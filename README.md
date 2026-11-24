# Lina – Outbound-Recruiting-Agent (Job-Step)

Bosnischer Voice-Agent für **Anruf 1**: Lina ruft Bewerber in BiH an, bedankt sich für die Bewerbung und fragt nur die **fehlenden, für die Eignung relevanten Angaben** ab. Unterlagen fordert sie in diesem Anruf nicht an. Eignung entscheidet das Team bzw. der Code nach dem Gespräch.

Das Repository startete als [LiveKit Agents Python-Starter](https://github.com/livekit-examples/agent-starter-python). Der produktive Agent heißt **`livekit-oai-gig-casting`** im Cloud-Projekt **`lina-oai`** (Region eu-central).

| | |
|---|---|
| Sprache im Gespräch | ausschließlich Bosnisch (ijekavski), Anrede „ti“ |
| Modell | OpenAI GPT-Live 1 über LiveKit Inference (`openai/gpt-live-1`) |
| Daten | Airtable-Base GIG Casting, Pre-Call-Fetch vor Sessionstart |
| Zeitzone | `Europe/Sarajevo` |
| Version | `1.1.0` in `pyproject.toml` · Prompt v2 Produktion, v3 Staging |

## Schnellstart

```bash
uv sync
cp .env.example .env.local   # Keys nur lokal, nie committen
uv run pytest -q && uv run ruff check src tests
lk agent debugger start src/agent.py --audio
```

Lokaler Dev-Agent an LiveKit Cloud: `lk agent dev`. Produktionsstart: `uv run src/agent.py start`.

Dispatch übergibt den Kandidaten als Job-Metadaten:

```json
{"record_id": "rec…"}
```

Ohne Metadaten gilt nur lokal `LINA_TEST_RECORD_ID` (Testkarte K-0196). Fehlt beides, startet die Session nicht.

## Architektur in einem Blick

```text
Dispatch {record_id}
        │
        ▼
src/agent.py  ─ Pre-Call-Fetch Airtable ─► Kontext (vorhanden / fehlt)
        │
        ▼
GPT-Live-Session
  PozdravAgent  --nastavi_prikupljanje-->  LinaAgent  --predji_na_kraj-->  Abschluss
        │
        ▼
sacuvaj()  →  Dopune / Radno iskustvo / Obrazovanje / Termini / Pozivi Lina
           →  einmal Status kandidata (nur wenn die Karte noch in der Anruf-Schlange ist)
           →  optional Transkript nach R2
```

Details: [`docs/ARCHITEKTUR.md`](docs/ARCHITEKTUR.md). Prompt-Versionen und Wissensdateien: [`docs/PROMPTS.md`](docs/PROMPTS.md).

## Tests und Betrieb

- Unit-Tests, Debugger, Console, Langfuse: [`docs/TESTEN.md`](docs/TESTEN.md)
- Setup, Umgebungsvariablen, Dispatch, Fallstricke: [`docs/BETRIEB.md`](docs/BETRIEB.md)
- Staging/Production, Secrets, Rollback: [`docs/DEPLOY.md`](docs/DEPLOY.md)
- SIP-Pfad LiveKit → FusionPBX → TG400: [`docs/TELEFONIE.md`](docs/TELEFONIE.md)
- Coding-Agenten (Cursor/Claude): [`CLAUDE.md`](CLAUDE.md), LiveKit-Workflows in [`AGENTS.md`](AGENTS.md)

Simulationen sind **audio-only** (GPT-Live) und kosten Inferenz. CI startet sie nur manuell (`.github/workflows/simulations.yml`).

## Doku-Index

| Thema | Datei |
|---|---|
| Airtable-Schema, Fetch, Schreiben | [`docs/airtable.md`](docs/airtable.md) |
| Erlaubte Feldwerte | [`docs/feldwerte.md`](docs/feldwerte.md) |
| Plausibilität L1–L10 | [`docs/plausibilitaet.md`](docs/plausibilitaet.md) |
| Voice-Prompt-Prinzipien | [`docs/voice-prompting.md`](docs/voice-prompting.md) |
| Wissen, das Lina sagen darf | [`docs/knowledge/`](docs/knowledge/) |
| Lina-3-Plan | [`docs/PLAN-lina-3.md`](docs/PLAN-lina-3.md) |
| Versionshistorie | [`CHANGELOG.md`](CHANGELOG.md) |

Keine Secrets, keine Telefonnummern, keine echten Kandidatennamen in Docs oder Logs — nur Record-IDs.
