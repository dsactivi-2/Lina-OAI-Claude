---
title: Lina testen
---

# Lina testen

Reihenfolge: erst Unit-Tests, dann Debugger, dann Console, dann Simulationen.
**GPT-Live ist audio-only:** Debugger und Simulationen laufen im **Audio-Modus**.

## 0. Einmalig
In `.env.local` steht der Test-Kandidat (K-0196, kein echter Bewerber):
```text
LINA_TEST_RECORD_ID=rec17GODhyD0Lkgzp
```
Er gilt nur, wenn ein Job **ohne** Dispatch-Metadaten startet (lokale Tests). Echte Anrufe
übergeben `{"record_id": "rec..."}` als Metadaten.

## 1. Unit-Tests (kein Netz, keine Kosten)
```bash
uv run pytest
uv run ruff check src tests
```

## 2. Pre-Call-Fetch gegen Airtable (nur lesen)
```bash
uv run python -c "import asyncio, dotenv; dotenv.load_dotenv('.env.local'); \
from lina.airtable import AirtableStore; from lina.kontekst import izracunaj; \
p=asyncio.run(AirtableStore().ucitaj('rec17GODhyD0Lkgzp')); \
print(izracunaj('rec17GODhyD0Lkgzp',p.kandidat,p.dopune,p.radno_iskustvo,p.obrazovanje).nedostaje)"
```
Erwartet: Liste der fehlenden Angaben, **ohne** `drzavljanstvo` (bei K-0196 eingetragen).

## 3. Agent-Debugger (Audio, nur Text-Ausgabe)
Der Debugger spricht deinen Text ein, du **hörst aber nichts**: Er zeigt nur Transkript und Tools.
Zum Hören Schritt 4 nutzen.
```bash
lk agent debugger start src/agent.py --audio
lk agent debugger say "Halo?"
lk agent debugger say "Da, imam vremena."
lk agent debugger say "Radim kao zidar u firmi Hidrogradnja od dvije hiljade osamnaeste."
lk agent debugger stop --chat-history
```
Achte auf: bosnische Antworten, eine Frage pro Turn, zuerst `nastavi_prikupljanje`,
dann `sacuvaj_podatak` / `dodaj_radno_mjesto`, am Ende `predji_na_kraj`. Nach Codeänderungen: `lk agent debugger restart`.

**Achtung:** Endet das Gespräch mit `zavrsi_razgovor` oder bricht ab, schreibt Lina einen
neuen Eintrag in `Dopune` (und ggf. `Radno iskustvo` / `Obrazovanje`) – verknüpft mit dem
Test-Kandidaten K-0196. Diese Testeinträge danach in Airtable löschen oder auf „Odbačeno“ setzen.

## 4. Mit Lina sprechen (Mikrofon, Browser – hier hörst du sie)
```bash
lk agent dev
```
Den ausgegebenen Agent-Console-Link öffnen, Mikrofon erlauben und sprechen.
Nach dem Deploy geht das auch direkt in der Agent Console der Cloud (siehe `docs/DEPLOY.md`).

## 4a. Langfuse prüfen
Mit gesetzten `LANGFUSE_*`-Variablen erscheint pro Gespräch ein Trace (Session = Raumname,
Metadaten `lina.record_id`, Environment `production` / `staging` / `lokal`).
Entscheidung (05.11.2026): **alles inkl. Gesprächsinhalte** (`LANGFUSE_INHALTE=1`).

Was Langfuse bekommt (`src/lina/dialog.py`):
- **agent_turn**: Input = Kandidatenaussage(n) seit dem letzten Turn + Linas vorherige Frage,
  Output = Linas Antwort + `unterbrochen`.
- **agent_session** (Wurzel): Output = ganzer Dialog in Reihenfolge (`rolle` kandidat/lina,
  `role` user/assistant, Text, Zeit, unterbrochen) + Ergebnis (`ishod`, `sazetak`).
  Auch als `langfuse.trace.output` für ältere Trace-Evaluatoren.
- Telefonnummern (Ziffern) und Secrets sind maskiert. Gesprochene Zahlwörter nicht.

Prüfen nach einem Testanruf: Langfuse → Traces → Environment filtern → Trace öffnen →
`agent_session` Output (ganzer Dialog) und einzelne `agent_turn` (Input/Output).

Lokal: `LINA_ENV=lokal` in `.env.local`, damit Tests nicht als `production` erscheinen.

## 5. Simulationen (kosten Inferenz)
```bash
lk agent simulate audio --scenarios scenarios.yaml
lk agent simulate audio --scenarios scenarios-guardrails.yaml
lk agent simulate audio --scenarios scenarios-neu.yaml
lk agent simulate audio --scenarios scenarios-lina3.yaml      # Prompt v3
lk agent simulate audio --scenarios scenarios-gpt-live.yaml   # Abschied, Auflegen, GPT-Live
lk agent simulate list
```
Simulationen nutzen **keinen** Airtable-Zugriff: Kandidaten kommen aus `userdata`
(`src/lina/simulacija.py`), der Endzustand wird in `on_simulation_end` geprüft.
CI (`.github/workflows/simulations.yml`) startet nur manuell und nur die ersten zwei Dateien.

Welche Datei zu v2/v3 gehört: `docs/PROMPTS.md`. Lokal `LINA_PROMPT` setzen, sonst gilt wie in der Cloud: Staging = v3, sonst v2.
