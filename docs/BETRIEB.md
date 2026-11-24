---
title: Betrieb, Setup und Fallstricke
---

# Betrieb, Setup und Fallstricke

Stand: Code auf `main` (Commit `3555ea6`). Keine Secrets, keine Telefonnummern, keine echten Namen.

Schnellstart und Architektur: [`README.md`](../README.md), [`docs/ARCHITEKTUR.md`](ARCHITEKTUR.md).
Staging/Production: [`docs/DEPLOY.md`](DEPLOY.md). SIP: [`docs/TELEFONIE.md`](TELEFONIE.md).

## Lokales Setup

Python **3.10–3.14** (`pyproject.toml`). Pakete über `uv`; `yarl` ist auf `<1.24` beschränkt.

```bash
uv sync
cp .env.example .env.local   # Keys nur hier, Datei ist gitignored
uv run pytest -q && uv run ruff check src tests
```

LiveKit-CLI ab 2.18.8 (`lk --version`). Cloud-Auth: `lk cloud auth`, danach `lk app env --write --destination .env.local` für URL und API-Keys.

Read-only Bestandsaufnahme (ändert nichts, maskiert Keys):

```bash
bash tools/lk-audit.sh .
```

## Welche Umgebungsvariable macht was

Vier ähnlich benannte Variablen steuern **verschiedene** Dinge. Verwechslung ist der häufigste Betriebsfehler.

| Variable | Wirkung | Wer setzt sie |
|---|---|---|
| `LIVEKIT_AGENT_DEPLOYMENT` | Prompt-Wahl: Wert `staging` → v3, sonst v2 (`src/lina/verzija.py`) | LiveKit Cloud am Job |
| `LIVEKIT_DEPLOYMENT` / `LINA_OKRUZENJE` | `Pozivi Lina` → Okruženje und R2-Pfad-Prefix (`src/lina/airtable.py` `_okruzenje()`). Unbekannt oder leer → `staging` | optional; nicht dasselbe wie oben |
| `LINA_ENV` | Langfuse-Environment (`src/lina/telemetrie.py`). Sonst `LIVEKIT_AGENT_DEPLOYMENT`, sonst `production` | lokal setzen, sonst Tests als `production` |
| `LINA_PROMPT` | Erzwingt v2/v3 | **nur** `.env.local`. Nie als Cloud-Secret: Secrets gelten für alle Deployments |

Weitere:

| Variable | Default / Regel |
|---|---|
| `LINA_TEST_RECORD_ID` | Nur wenn **keine** Dispatch-Metadaten da sind. In der Cloud vor echten Anrufen entfernen. |
| `LINA_AMD_STT` | `deepgram/nova-3:bs`. Cartesia Ink-Whisper gibt es in eu-central nicht. |
| `LINA_VOICE` | `marin` (GPT-Live hat keine bosnische Stimme) |
| `LINA_BACKEND_MODEL` | `gpt-5.6-luna` |
| `LINA_BACKEND_REASONING` / `VERBOSITY` | v3: `low` / `low`. v2 ignoriert sie. |
| `LINA_BACKEND_MAX_TOKENS` | nur opt-in; zu klein bricht Tool-Aufrufe ab; keine Zahl → ignoriert |
| `LANGFUSE_INHALTE` | `1` = Gesprächsinhalte (Personendaten). `0` = nur Metadaten |
| `R2_*` | alle fünf oder keine; sonst bleibt die Pozivi-Zeile ohne Transkript-URL |

## Dispatch-Vertrag

Pro Kandidat ein Job. Metadaten **genau**:

```json
{"record_id": "rec…"}
```

`src/agent.py` `_record_id()`:

1. Nicht-leere Metadaten, gültiges JSON, `record_id` gesetzt → dieser Wert (auch wenn es eine Zahl ist, dann `str(...)`).
2. Metadaten da, aber kaputt (`{`, `[]`, `{"foo":1}`, leeres `record_id`) → **kein** Fallback auf `LINA_TEST_RECORD_ID`, Log `Dispatch-Metadaten ohne gültiges record_id`, Session startet nicht.
3. Metadaten leer oder fehlend → `LINA_TEST_RECORD_ID`, sonst Shutdown `no record_id`.

Lina wählt die Nummer nicht selbst. Outbound: [`docs/TELEFONIE.md`](TELEFONIE.md). n8n-Workflow ist noch nicht im Repo (Backlog).

Pre-Call-Fetch schlägt fehl → Shutdown `pre-call fetch failed`, kein Gespräch.

## AMD (Anrufbeantworter)

Nach `ctx.connect()`, nicht in Simulationen.

- STT: `LINA_AMD_STT`, Standard `deepgram/nova-3:bs` (EU + Bosnisch).
- Default von LiveKit (Cartesia Ink-Whisper) **nicht** nutzen: ohne Transkript endet AMD immer `UNCERTAIN`.
- `ivr_detection=False`.
- `machine-vm`: kurze Bosnisch-Nachricht, `ishod=prekinuto`, Shutdown `voicemail`.
- `machine-unavailable`: `ishod=prekinuto`, keine Ansage.
- Ausnahme im AMD: Log, Gespräch läuft weiter wie Mensch.

Unit-Tests dazu liegen auf Branch `test/amd-stt-und-dispatch` (nicht auf `main`). Verhalten auf `main` ist dasselbe.

## Fragenkatalog vs. Doku

Quelle der Wahrheit: `PITANJA` in `src/lina/config.py`. Reihenfolge = Gesprächsreihenfolge. `abfragen=False` schaltet die Frage ab, ohne den Key zu löschen.

Aktuell **aus** (`abfragen=False`): `status_boravka`, `radna_dozvola`.
Aktuell **an**, entgegen älterer Entwurfsdoku: Adresse, Geburtsdatum, Geburtsort, Familienstand, Kinder, E-Mail, Staatsangehörigkeit, Englisch.

Details: [`docs/airtable.md`](airtable.md).

## Häufige Symptome

| Symptom | Ursache | Was tun |
|---|---|---|
| Session startet nicht, Log `Kein Kandidat` | keine Metadaten und kein `LINA_TEST_RECORD_ID` | lokal die Test-ID setzen; in der Cloud Metadaten prüfen |
| Session startet nicht trotz Test-ID | Metadaten vorhanden, aber ungültig | JSON und Key `record_id` prüfen; Test-ID gilt dann **nicht** |
| Log `pre-call fetch failed` | Airtable-Token, Base, Record-ID, Netz, 429 | Token-Scopes, `AIRTABLE_BASE_ID`, Record-ID; 4 Retries mit Backoff sind schon im Code |
| AMD immer unsicher / Mailbox falsch | STT ohne EU-Endpunkt | `LINA_AMD_STT=deepgram/nova-3:bs` |
| Staging klingt wie v2 oder Production wie v3 | `LINA_PROMPT` als Cloud-Secret | Secret entfernen; Staging wählt v3 allein über `LIVEKIT_AGENT_DEPLOYMENT` |
| Cloud-Build bricht bei `uv sync --locked` | Version in `pyproject.toml` ohne `uv lock` | `uv lock` committen, siehe [`docs/DEPLOY.md`](DEPLOY.md) |
| Testanruf landet in Production | `--deployment` / `--agent-deployment staging` fehlt | immer explizit Staging |
| Debugger-Gespräch in Airtable | `zavrsi_razgovor` / Abbruch schreibt Dopune an K-0196 | Testdatensätze löschen oder `Odbačeno` |
| Lina liest `title: …` und `---` vor | Knowledge-Frontmatter geht roh in den Prompt | Frontmatter klein halten; Stripper auf Branch `test/znanje-frontmatter` |
| Langfuse-Trace unter `production` | `LINA_ENV` lokal nicht gesetzt | `LINA_ENV=lokal` in `.env.local` |
| Pozivi-Okruženje `staging` in Production | `_okruzenje()` liest `LIVEKIT_DEPLOYMENT`, nicht `LIVEKIT_AGENT_DEPLOYMENT` | `LIVEKIT_DEPLOYMENT=production` oder `LINA_OKRUZENJE` |
| `lk agent delete` ohne Flag | löscht das Original | nur mit `--deployment staging` |

## Was der Debugger schreibt

`lk agent debugger` und `lk agent dev` ohne Dispatch-Metadaten nutzen K-0196. Endet das Gespräch, legt `sacuvaj()` Zeilen in `Dopune` / `Radno iskustvo` / `Obrazovanje` / `Pozivi Lina` an. Danach in Airtable aufräumen. Details: [`docs/TESTEN.md`](TESTEN.md).
