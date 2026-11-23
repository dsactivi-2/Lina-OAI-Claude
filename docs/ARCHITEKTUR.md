---
title: Architektur und öffentliche Schnittstellen
---

# Architektur und öffentliche Schnittstellen

Stand: Code auf `main` (Commit `3555ea6`, 16.11.2026). Lina entscheidet nichts über Eignung; der Code hält Zustand, Freigaben und Schreibzugriffe.

## Einstieg

`src/agent.py` ist der einzige LiveKit-Entrypoint (`AgentServer`, Agent-Name `livekit-oai-gig-casting`).

1. Kandidat bestimmen (`_record_id`): JSON-Metadaten `{"record_id":"rec…"}`, sonst `LINA_TEST_RECORD_ID`.
2. Langfuse optional (`src/lina/telemetrie.py`), Metadaten `lina.record_id` und `lina.prompt_verzija`.
3. Pre-Call-Fetch **vor** `session.start`. Fehler → `shutdown`, kein Gespräch.
4. `izracunaj()` in `src/lina/kontekst.py` baut die Zusammenfassung `vorhanden` / `nedostaje` (inkl. nicht verworfener `Dopune`).
5. GPT-Live (`openai/gpt-live-1`) + Silero-VAD + ai-coustics Rauschunterdrückung.
6. Start mit `PozdravAgent`. Nach dem Connect: AMD, außer in Simulationen.

Ohne `record_id` loggt der Entrypoint den Fehler und startet die Session nicht.

## Gesprächsphasen

| Phase | Klasse | Aufgabe | Tools |
|---|---|---|---|
| Pozdrav | `PozdravAgent` | Warten auf Halo, Identität, hat der Kandidat eine Minute | `nastavi_prikupljanje`, `zakazi_povratni_poziv`, `zavrsi_razgovor`, `end_call` |
| Prikupljanje | `LinaAgent` | Fehlende Angaben, Stationen, Schulen | alle Datentools plus Abschluss |
| Kraj | Abschluss | Danke, speichern, auflegen | `zavrsi_razgovor`, `end_call` |

Handoff Pozdrav → Lina: klassischer Agent-Wechsel, `chat_ctx` **ohne** alte Instruktionen (`exclude_instructions=True`). Sonst startet GPT-Live eine neue Modell-Session mit doppelten Tool-Namen.

Handoff Lina → Kraj hängt von der Prompt-Version ab (`src/lina/agent_lina.py`, `predji_na_kraj`):

- **v2:** echter Handoff auf `KrajAgent` (wie Produktion).
- **v3:** Session bleibt offen. `append_instructions` (Kraj-Regeln, ≤ 500 Tokens) + `update_tools` (Daten-Tools weg, `zavrsi_razgovor` und `end_call` bleiben). Grund: Hörtest 11.11.2026, 13 s Stille bei neuem Handoff.

40 s nach `predji_na_kraj` (v3) legt der Code auf, falls `zavrsi_razgovor` nicht kam. Gespeichert wird dann über den Shutdown-Callback mit `ishod_bez_kraja()`.

## Öffentliche Tools (`LinaAgent`)

Nur Zustand im Speicher. Geschrieben wird einmal in `zavrsi_razgovor` bzw. beim Session-Ende.

| Tool | Wirkung |
|---|---|
| `sacuvaj_podatak` | Eine Angabe, Werte aus `docs/feldwerte.md` / `werte.py`. Adresse → Nominatim-Check. Alter ≥ 45 in v3 → Gesprächsende. |
| `dodaj_radno_mjesto` / `ispravi_radno_mjesto` | Station anlegen bzw. korrigieren. Nummern zählen **alle** Einträge (Airtable zuerst, dann neu). Bewerbungs-Einträge werden nicht überschrieben, sondern als `ISPRAVKA:…` notiert. |
| `dodaj_skolu` / `ispravi_skolu` | analog, plus Schul-Check über Nominatim (`src/lina/mapa.py`) |
| `provjeri_podatke` | Plausibilität L1–L10, jede Auffälligkeit einmal |
| `zabiljezi_objasnjenje` | Antwort des Kandidaten zu einer Auffälligkeit |
| `trenutno_vrijeme` | Datum/Wochentag/Uhr in `Europe/Sarajevo` |
| `zakazi_povratni_poziv` | absoluter Termin, ISO, nicht in der Vergangenheit |
| `predji_na_kraj` | Phasenwechsel, keine neuen Felder danach |
| `zavrsi_razgovor` | `ishod` + `sazetak` + drei Fakten für den Status, dann `sacuvaj()` |

Zusätzlich `EndCallTool` (`end_call`) am Session-Objekt.

## AMD (Anrufbeantworter)

Nach `ctx.connect()`, nicht in Simulationen (`src/agent.py`).

- STT: `LINA_AMD_STT`, Standard `deepgram/nova-3:bs` (EU; Cartesia Ink-Whisper gibt es in eu-central nicht).
- `ivr_detection=False`.
- `machine-vm`: kurze Bosnisch-Nachricht, `ishod=prekinuto`, Shutdown `voicemail`.
- `machine-unavailable`: `ishod=prekinuto`, Shutdown ohne Ansage.
- Fehler im AMD: Log, Gespräch läuft weiter wie Mensch.

## Schreiben nach dem Gespräch

`src/lina/airtable.py` → `sacuvaj()`. Jede Tabelle höchstens einmal; ein späterer Shutdown holt nur fehlende Tabellen nach.

| Tabelle | Wann | Inhalt |
|---|---|---|
| `Pozivi Lina` (`tblXnTENm7kts7wwT`) | immer | Oznaka, Datum, Sažetak, Ishod, Okruženje, Link auf Kandidat |
| `Dopune` | nur wenn Angaben erfasst wurden | Status pregleda = Novo, Opis, Feldwerte |
| `Radno iskustvo` / `Obrazovanje` | neue Stationen/Schulen | neue Datensätze, nie Patch auf bestehende |
| `Termini i zadaci` | Rückruf vereinbart | Status Todo |
| `Prijave (test)` | einmal, optional | nur `Status kandidata` |

`Prijave` wird **nicht** mit Personendaten beschrieben. Der einzige Patch ist der Status, und nur wenn der aktuelle Wert in `{leer, New Lead, NE JAVLJA SE}` liegt (`src/lina/status_odluka.py`). Spätere Stapel bleiben unangetastet.

Ishod-Werte im Code (`src/lina/stanje.py`): `zavrseno`, `djelimicno`, `povratni_poziv`, `nije_zainteresiran`, `ne_zovite_vise`, `pogresna_osoba`, `prekinuto`. Gesprächsende ohne `zavrsi_razgovor` → `ishod_bez_kraja()` (Rückruf oder Teilangaben zählen nicht als Abbruch).

Status-Namen setzt der Code aus Fakten, nicht das Modell:

| Bedingung | Status |
|---|---|
| nicht gemeldet | `NE JAVLJA SE` |
| negativ + kein Interesse + keine Erfahrung | `Odustao` |
| Interesse, Unterlagen vollständig | `Pre-casting` |
| Interesse, Teil der Unterlagen oder persönliche Daten | `Zeleni / obrada` |
| Interesse, sonst | `Zainteresiran` |
| Interesse ≠ da | kein Schreibzugriff |

## Transkript nach R2 (optional)

Nach dem `Pozivi`-Datensatz versucht `r2.stavi()` einen Upload. Fehlen Secrets oder schlägt PUT fehl, bleibt die Pozivi-Zeile trotzdem stehen.

Schlüssel: `{staging|production}/{record_id}/{pozivi_id}.txt`. Öffentliche URL landet in `Pozivi Lina` → Link (`fld1cRL36FOnMHXRT`).

Benötigte Variablen (alle oder keine): `R2_BUCKET`, `R2_PUBLIC_BASE`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`. Nicht in Logs schreiben.

Umgebung für Pozivi/`_okruzenje()`: `LIVEKIT_DEPLOYMENT` oder `LINA_OKRUZENJE`, sonst `staging`. Das ist **nicht** dasselbe wie `LIVEKIT_AGENT_DEPLOYMENT` (Prompt-Wahl, siehe `docs/PROMPTS.md`).

## Laufzeit-Helfer (kein LLM)

| Modul | Rolle |
|---|---|
| `govor.py` | Pflichtnachfragen aus dem Gesagten (Schule, Jahres-Überlappung, Behauptung ohne Station in der Bewerbung), ohne auf ein Tool zu warten |
| `jezik.py` | v3: kroatische/ekavische Wörter und DE/EN-Floskeln in Linas Text → `append_instructions`, max. 2 Hinweise pro Anruf |
| `mapa.py` | Nominatim (nur `countrycodes=ba`). `None` = Netz weg, nicht nachfragen. `False` = kein Treffer, einmal nachfragen |
| `plausibilitaet.py` | L1–L10 |
| `dialog.py` | Gespräch beider Seiten für Langfuse, Telefonnummern/Secrets maskiert |

## Dispatch / n8n

Pro Kandidat ein Job. Metadaten genau `{"record_id":"<Airtable-Record-ID>"}`. Lina wählt die Nummer nicht selbst; Outbound läuft über SIP (`docs/TELEFONIE.md`).
