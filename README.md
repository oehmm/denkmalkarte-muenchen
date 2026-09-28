# Denkmalkarte München

Interaktive Karte aller Münchner Baudenkmäler (Bayerische Denkmalliste, Stand 25.09.2026).

- Online (Artifact): https://claude.ai/artifact/7p4cYk64UHDjhrn5vQZ18c
- Lokal mit eingebautem Gemini-Chat:

```bash
python3 serve.py
```

Dann http://localhost:8765 öffnen. Der Server liest `GEMINI_API_KEY` aus der Umgebung,
aus `./.env` oder aus `~/debattier-coach-web/.env`. Modell über `GEMINI_MODEL` (Standard `gemini-3.8-flash`).
Im Artifact ist kein direkter API-Zugriff möglich; dort übergibt „Frag Gemini“ die Frage samt Listentext an gemini.google.com.

## Funktionen

- 6.911 Baudenkmäler + 87 Ensembles mit Listentext, Kategorie, Baujahr, Stadtbezirk
- Architekten-Verzeichnis, Baustil-Filter, Zeitreise-Animation, Glossar mit 66 Fachbegriffen
- 9 Themen-Rundgänge mit berechneter Route und Google-Maps-Navigation
- Merkliste und „schon besucht“ (im Artifact im privaten Konto-Speicher, sonst im Browser)
- Vergleich mit dem Listenstand 21.12.2024: neue, geänderte (mit Wort-Diff) und gestrichene Einträge

## Daten neu erzeugen

```
scripts/parse.py        PDF-Text (raw/d.txt, via pdftotext -layout) -> raw/entries.json
scripts/fetch.py        Koordinaten vom BLfD-WMS (einzeldenkmalO / bauensembleO)
scripts/build.py        -> dm.json (Titel, Adresse, Kategorie, Baujahr)
scripts/base.py         OSM-Basiskarte + Stadtbezirke -> data/basiskarte.json, data/denkmaeler.json
scripts/enrich.py       Architekten + Baustile
scripts/diff.py         Vergleich mit raw/entries_2024-12-21.json -> data/aenderungen.json
scripts/tours_build.py  Rundgänge (Stationen, Reihenfolge, Fußweg-Routing) -> data/rundgaenge.json
scripts/assemble.py     src.html + Daten -> site/
```
