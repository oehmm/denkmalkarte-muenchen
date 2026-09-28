#!/usr/bin/env python3
"""Lokaler Server für die Denkmalkarte mit Gemini-Chat.

Start:  python3 serve.py        ->  http://localhost:8765

Liefert die Seite aus site/ aus und leitet Chat-Anfragen an die Gemini-API weiter,
damit der API-Schlüssel nie im Browser landet. Schlüsselquelle (in dieser Reihenfolge):
  1. Umgebungsvariable GEMINI_API_KEY
  2. .env in diesem Ordner
  3. ~/debattier-coach-web/.env
Modell: GEMINI_MODEL (Standard: gemini-3.8-flash)
"""
import json, os, sys, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
PORT = int(os.environ.get("PORT", "8765"))
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")


def read_key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()
    for p in (ROOT / ".env", Path.home() / "debattier-coach-web" / ".env"):
        if p.exists():
            for line in p.read_text().splitlines():
                if line.strip().startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


KEY = read_key()

SYSTEM = (
    "Du bist ein kundiger Münchner Architektur- und Stadthistoriker und beantwortest Fragen "
    "zu einem einzelnen Baudenkmal aus der Bayerischen Denkmalliste. Antworte auf Deutsch, "
    "anschaulich und knapp (meist 80–200 Wörter), gern mit kurzen Absätzen oder Stichpunkten. "
    "Grundlage ist der amtliche Listentext im Kontext. Wenn du darüber hinausgehst, stütze dich "
    "auf verlässliches Wissen oder die Websuche und mache kenntlich, was nicht aus dem Listentext "
    "stammt. Erfinde keine Daten, Namen oder Jahreszahlen; sag offen, wenn du etwas nicht sicher weißt."
)


def gemini(contents, grounding=True):
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1200},
    }
    if grounding:
        body["tools"] = [{"google_search": {}}]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.load(r)
    cand = (data.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    sources = []
    for ch in (cand.get("groundingMetadata") or {}).get("groundingChunks", []) or []:
        w = ch.get("web") or {}
        if w.get("uri"):
            sources.append({"title": w.get("title") or w["uri"], "url": w["uri"]})
    return text.strip(), sources


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def log_message(self, fmt, *args):
        if args and "/api/" in str(args[0]):
            sys.stderr.write("%s\n" % (fmt % args))

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/status":
            return self._json(200, {"gemini": bool(KEY), "model": MODEL})
        if self.path in ("/", "/index.html") or self.path.startswith("/?") or self.path.startswith("/#"):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/gemini":
            return self._json(404, {"error": "not found"})
        if not KEY:
            return self._json(503, {"error": "Kein GEMINI_API_KEY gefunden."})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n) or b"{}")
            ctx = str(req.get("context", ""))[:8000]
            msgs = req.get("messages", [])[-12:]
            contents = []
            for i, m in enumerate(msgs):
                role = "model" if m.get("role") == "model" else "user"
                text = str(m.get("text", ""))[:4000]
                if i == 0 and role == "user":
                    text = "Kontext zum Denkmal:\n" + ctx + "\n\nFrage: " + text
                contents.append({"role": role, "parts": [{"text": text}]})
            if not contents or contents[-1]["role"] != "user":
                return self._json(400, {"error": "Keine Frage übergeben."})
            try:
                text, sources = gemini(contents, grounding=True)
            except urllib.error.HTTPError as e:
                if e.code == 400:   # Modell ohne Websuche: ohne Grounding erneut
                    text, sources = gemini(contents, grounding=False)
                else:
                    raise
            return self._json(200, {"text": text or "(keine Antwort)", "sources": sources[:6], "model": MODEL})
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            return self._json(502, {"error": f"Gemini-Fehler {e.code}", "detail": detail})
        except Exception as e:
            return self._json(500, {"error": str(e)})


if __name__ == "__main__":
    print(f"Denkmalkarte: http://localhost:{PORT}   Gemini: {'aktiv (' + MODEL + ')' if KEY else 'kein Schlüssel gefunden'}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
