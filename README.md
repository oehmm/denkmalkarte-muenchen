# Denkmalkarte München

Interaktive Karte aller Münchner Baudenkmäler (Bayerische Denkmalliste, Stand 25.09.2026).

- Handy-App (GitHub Pages, installierbar): https://oehmm.github.io/denkmalkarte-muenchen/
- Online (Artifact): https://claude.ai/artifact/7p4cYk64UHDjhrn5vQZ18c
- Lokal mit eingebautem Gemini-Chat:

```bash
python3 serve.py
```

Dann http://localhost:8765 öffnen. Der Server liest `GEMINI_API_KEY` aus der Umgebung,
aus `./.env` oder aus `~/debattier-coach-web/.env`. Modell über `GEMINI_MODEL` (Standard `gemini-3.8-flash`).
Im Artifact ist kein direkter API-Zugriff möglich; dort übergibt „Frag Gemini“ die Frage samt Listentext an gemini.google.com.

## Varianten

| | Artifact | Handy-App (GitHub Pages) | Lokal (`serve.py`) |
|---|---|---|---|
| Commons-Fotos | eingebettete Vorschaubilder | groß, direkt von Commons | groß, direkt von Commons |
| In der Nähe (GPS) | – (vom Artifact gesperrt) | ✓ | ✓ (nur localhost) |
| Eigene Fotos | Artifact-Speicher (Konto) | auf dem Gerät (IndexedDB) | im Browser (IndexedDB) |
| Merkliste | Claude-Konto | auf dem Gerät | im Browser |
| Frag Gemini | Übergabe an gemini.google.com | eigener API-Schlüssel (nur auf dem Gerät) | über Server-Schlüssel |
| Offline | – | ✓ (Service Worker) | – |

Auf dem iPhone: Seite in Safari öffnen → Teilen → „Zum Home-Bildschirm“. Android/Chrome: Menü → „App installieren“.

## Veröffentlichen

```bash
scripts/deploy.sh
```

baut `docs/` neu, committet und pusht; GitHub Pages ist nach 1–2 Minuten aktualisiert.

## Funktionen

- 6.911 Baudenkmäler + 87 Ensembles mit Listentext, Kategorie, Baujahr, Stadtbezirk
- Architekten-Verzeichnis, Baustil-Filter, Zeitreise-Animation, Glossar mit 66 Fachbegriffen
- 9 Themen-Rundgänge mit berechneter Route und Google-Maps-Navigation
- Merkliste und „schon besucht“ (im Artifact im privaten Konto-Speicher, sonst im Browser)
- Vergleich mit dem Listenstand 21.12.2024: neue, geänderte (mit Wort-Diff) und gestrichene Einträge
- Commons-Fotos (über Wikidata, BLfD-Aktennummer P4244) mit Urheber und Lizenz
- Eigene Fotos je Denkmal
- Ebenen: 819 Bodendenkmäler, 542 Baudenkmäler im Umland (Dachau, Gauting, Pullach …)
- „In der Nähe“ per GPS

## Daten neu erzeugen

```
scripts/parse.py        PDF-Text (raw/d.txt, via pdftotext -layout) -> raw/entries.json
scripts/fetch.py        Koordinaten vom BLfD-WMS (einzeldenkmalO / bauensembleO)
scripts/build.py        -> dm.json (Titel, Adresse, Kategorie, Baujahr)
scripts/base.py         OSM-Basiskarte + Stadtbezirke -> data/basiskarte.json, data/denkmaeler.json
scripts/enrich.py       Architekten + Baustile
scripts/diff.py         Vergleich mit raw/entries_2024-12-21.json -> data/aenderungen.json
scripts/tours_build.py  Rundgänge (Stationen, Reihenfolge, Fußweg-Routing) -> data/rundgaenge.json
scripts/extra_layers.py Umland (Gemeinden via Wikidata-AGS) + Bodendenkmäler
scripts/photos.py       Commons-Fotos: Metadaten + Vorschaubilder (raw/thumbs)
scripts/pack_thumbs.py  Vorschaubilder für das Artifact bündeln -> site/thumbs
scripts/assemble.py     src.html + Daten -> site/ (Artifact, lokal) und docs/ (GitHub Pages)
```
