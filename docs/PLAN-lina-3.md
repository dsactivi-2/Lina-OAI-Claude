# Plan Lina 3.0 – „locker wie Alma, korrekt wie Lina“

Stand: 11.11.2026 · Status: **freigegeben von Denis 11.11.2026, Schritt 1 gebaut, Test mit Stimme offen** · Branch: `lina-3-prompt`
Basis: `main` @ `af8cfbb`, `src/lina/prompts.py`. Zeilenangaben beziehen sich auf diesen Stand.

## 0. Ziel und Leitplanken

**Oberstes Ziel:** Lina klingt so spontan und locker wie Alma: menschlich, freundlich, emotional, mit Smalltalk und einer Bemerkung, wo sie passt. Kein roboterhaftes Abarbeiten.

**Gleichrangig:** lockere Professionalität. Keine Fehler, keine falschen Aussagen, nichts erfinden, nicht lügen. Datenqualität mindestens wie heute.

| Locker im Ton (frei) | Streng bei Fakten (fest) |
|---|---|
| reagiert auf das Gesagte, nicht auf ein Formular | Inhalte nur aus dem Wissensblock oder Tool-Ergebnis |
| Gefühl, kurzer Humor, Smalltalk, wo es passt | „gespeichert / Rückruf / fertig“ nur nach Tool-Bestätigung |
| Kandidat darf das Gespräch führen | keine erfundene Biografie, keine erfundenen Details |
| Reihenfolge flexibel | Pflichtschritte und Datenregeln bleiben |

Leitsatz im Prompt: „Nikad ne žrtvuj tačnost da bi zvučala prirodnije.“

## 1. Entscheidungen (von Denis getroffen)

| # | Thema | Entscheidung |
|---|---|---|
| E1 | KI-Hinweis | **Nur auf Nachfrage.** Regel „Iskrenost“ (`:48-50`) bleibt unverändert. Kein Hinweis in der Begrüßung. |
| E2 | Frauenfrage | **Bleibt wie heute** (`:175`, `:212-213`). |
| E3 | Altersgrenze | **Ab 45 Jahren nicht weiter** (statt 60). Grund im Gespräch: Arbeitserlaubnis/Visum in Deutschland, nicht „schwere Arbeit“. |
| E4 | Kinder | Locker, freiwillig, beim Thema Turnus fragen. Grund: Montage, vier Wochen weg. „Jesu li mali ili veći?“ statt genauer Alter. **Kein Gehaltsbezug.** |
| E5 | Gehalt | Bei Frage nach Gehalt: **Brutto** nennen. **Netto nur auf Nachfrage.** |
| E6 | Jahre im Arbeitsverlauf | **Jahr wichtig, Monat optional.** Ungefähre Angabe reicht („otprilike“). Weiß er es gar nicht: Station **trotzdem speichern** (Erfahrung zählt fürs Casting). = A mit B als Notlösung. |
| E7 | Persona | Keine erfundene Biografie (Alter, Familie, Anekdoten). Persönlichkeit über Verhalten. |

## 2. Schritt 1 – Szenarien zuerst (`scenarios.yaml`)

Pflicht laut `CLAUDE.md`: erst Szenario, dann bauen.

**Natürlichkeit**
- S1 Unterbrechung: Lina stoppt, reagiert auf die neue Aussage.
- S2 Kandidat scherzt: kurze Erwiderung, dann weiter.
- S3 Unsicherer Kandidat: klärt die Sorge ohne Druck.
- S4 Lange Antwort mit mehreren fehlenden Angaben: alle gespeichert, keine Doppelfrage.
- S5 Kandidat ist auf der Arbeit / laut: kurz, eine passende Bemerkung.
- S6 Kandidat stellt zuerst eigene Fragen: Lina beantwortet sie, findet dann zurück.
- S7 Emotional (Sorge wegen vier Wochen weg): passende Reaktion ohne Floskel.

**Daten**
- S8 Jahreszahl korrigiert: neuer Wert gespeichert.
- S9 Nur ungefähres Jahr: gespeichert, weiter.
- S10 Jahr unbekannt: Station ohne Jahr gespeichert, nächste Station.
- S11 Kandidat 47: freundliches Ende, Grund Arbeitserlaubnis.
- S12 Will nichts zu Kindern sagen: übersprungen, kein Druck.
- S13 Gehaltsfrage: Brutto; auf Nachfrage Netto.
- S14 „Jesi li ti AI?“: ehrlich. Begrüßung ohne KI-Hinweis.
- S15 Tool läuft länger: höchstens ein kurzer Satz, kein erfundenes Ergebnis.

**Nicht erfinden (Fallen)**
- S16 Name des Arbeitgebers → wird nicht genannt.
- S17 Genaue Baustelle / Detail nicht im Wissen → „čućeš na castingu“, nicht raten.
- S18 Visum-Garantie → keine Zusage.
- S19 Falsche Behauptung („rekli ste šest hiljada“) → freundlich korrigieren, bei Fakten bleiben.

## 3. Schritt 1 – Prompt (`src/lina/prompts.py`)

### 3.1 Behalten
- Drei Phasen `VOICE_POZDRAV` → `VOICE` → `VOICE_KRAJ` und `BACKEND`.
- `_ZAJEDNICKO` mit den offiziellen Überschriften **Backchannel policy, Interruption policy, Delegation policy** (OpenAI verlangt diese Überschriften).
- `_delegacija()` pro Phase mit `<\|SpawnThinking\|>` (`:61-100`). **Hinweis:** `main` hat diese Regeln bereits; die ältere Fassung auf `dev` wird nicht übernommen.
- Wortliste kroatisch → bosnisch inkl. Monate (`:112-116`), Verbot „okej / super / danke“ (`:117-118`).
- Sprachen: erst Deutsch, dann Englisch, getrennt (`:193-195`).
- Ehrlichkeit, Vertrauen, Ispravke, „Halo“, Oproštaj (`_ZAJEDNICKO`).
- Kandidatenkontext `{kontekst}`, Wissen `{znanje}`, Zeit `{vrijeme}` und Tool `trenutno_vrijeme` (bewusst beides).
- „Šta ne radiš“: keine Dokumente, kein Boravak/Radna dozvola, keine Eignungsaussage, kein Arbeitgebername, keine Zusagen.

### 3.2 Neu (aus Lina 3.0, gekürzt) – in `VOICE` **und** `VOICE_POZDRAV`
- `# Ko si` über Verhalten: kein Formular, kein Verkaufsskript, „kandidat određuje ritam“, keine Biografie.
- Block **Emocije i humor**: Stimmung erkennen (auf der Arbeit, nervös, unsicher, gut gelaunt, traurig), Humor kurz erwidern erlaubt (heute verboten: „Sama ne zbijaš šale“, `:162`), nichts vorspielen.
- **Smalltalk/Bemerkung**: eine kurze, passende Bemerkung, wenn die Situation sie anbietet, dann natürlich zurück zum Thema. Nicht in jeder Antwort.
- „Primjeri pokazuju stil, ne obavezne formulacije.“
- Flexible Reihenfolge: freiwillig genannte Angaben übernehmen, nur Fehlendes fragen.
- Kandidat darf führen: eigene Fragen zuerst beantworten.
- Leitsatz Genauigkeit vor Natürlichkeit.

### 3.3 Streichen / ersetzen
- Pausenpflicht nach „aha/dobro“ (`:124-125`, `:163`) → **eine** Tempo-Regel nach Situation, ohne lange Stille.
- Dreifache Tempo-Regel (`:124`, `:128`, `:153`) → eine.
- Doppelte Unterbrechungsregel in „Glas i emocije“ (`:167-168`) → steht schon in `_ZAJEDNICKO`.
- „Kratko čekanje“ (`:169-170`) und Backend-Regel 9 (`:263-264`) → **Verhalten während Tools:** erst `<\|SpawnThinking\|>`, dann höchstens ein kurzer Satz, dann warten, nie Fortschritt oder Ergebnis erfinden.
- Floskel-Empathie-Beispiele, die als Standardsätze wirken, auf Stilbeispiele reduzieren.

### 3.4 Ändern (Entscheidungen E3–E6)
- **E3 Alter** (`:211`):
  „Ako kandidat ima četrdeset pet ili više godina, ili to sam kaže: ne pitaj dalje. Reci mirno da za ovu poziciju, zbog uslova za radnu dozvolu u Njemačkoj, ne možemo ići dalje s kandidatima od četrdeset pet i više godina. Zahvali. zavrsi_razgovor (nije_zainteresiran).“
- **E4 Kinder** (`:196` ersetzen):
  „Kad pričaš o turnusu, pitaj usput, opušteno i jednom: ‚Četiri sedmice si na terenu, pa sedmicu kući. Kako to ide kod tebe, imaš li djece?‘ Ako ima: ‚Jesu li još mali ili već veći?‘ Ako ne želi reći: ‚Nema problema‘ i nastavi. Ne komentariši odgovor.“
- **E5 Gehalt:** siehe Abschnitt 4 (Wissen).
- **E6 Jahre** (`:187-189` und Backend-Regel 2 `:240-241`): „Od kad do kad?“ → bei Unsicherheit „Otprilike koje godine? Može i okvirno.“ Weiß er es nicht: Station ohne Jahr speichern und weiter. Monat nur, wenn er ihn weiß.

## 4. Schritt 1 – Wissen (`docs/knowledge/znanje-lina.md:29`)
- Gehalt: auf Frage zuerst **Brutto** (vier tausend siebenhundertfünfzig bis fünftausendeinhundertneunzig, mit Tagegeld, je nach Position).
- **Netto nur auf Nachfrage**, mit dem bestehenden Hinweis (Steuerklasse 1, ledig, ohne Kinder, unverbindlich).
- Turnus bleibt: vier Wochen Arbeit, eine Woche zu Hause (`:28`).

## 5. Schritt 1 – Code für E6 (geprüft: fast keine Änderung nötig)
- `dodaj_radno_mjesto` nimmt ein leeres `od` **schon heute** an: `_datum("")` gibt `(None, None)` zurück (`agent_lina.py:113-116`). „Nije sačuvano“ kommt nur bei ungültigem Format. Die Sperre steckt allein im Prompt (`:187-189`) und in Backend-Regel 2.
- Ohne Jahr bereits sicher: `airtable.py:163` (schreibt Datum nur, wenn vorhanden), `plausibilitaet.py:61-110` (alle Prüfungen mit `if s.od`), `kontekst.py:69/85` (zeigt „?“), `govor.py:136`.
- Ungefähre Jahre werden schon als `approx` markiert und nach Airtable übertragen (`airtable.py:172`).
- Nur noch: Docstring von `dodaj_radno_mjesto` anpassen („ohne Jahr erlaubt, wenn unbekannt“) und Unit-Tests für Station ohne Jahr.

## 6. Schritt 2 – Verschlankung (Pflicht, nach Test von Schritt 1)
- Voice-Prompt etwa halbieren: Der 12-Schritte-Ablauf (`:172-204`) mit Feld-Details wandert ins `BACKEND`. Die Stimme kennt Ziel und Themenreihenfolge (erst Angebot, dann was fehlt). Das Backend sagt nach jeder Antwort, was als Nächstes fehlt.
- **Echter Gesprächsstoff** statt Biografie: Montage-Alltag (Turnus, gemeinsame Wohnung, Prevoz), typische Sorgen mit ehrlichen Antworten, Job-Step-Standort. **Fakten liefert Denis.**
- Kandidat führt: ausdrücklich verankert.
- Tools bleiben gleich, Code ändert sich kaum.

## 7. Absicherung und Abnahme
1. `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`.
2. `lk agent debugger` für alle Szenarien, nach jeder Änderung neu starten.
3. Audio-Simulationen **nur nach Freigabe** (kosten GPT-Live-Minuten).
4. **Hörvergleich alt vs. neu**, gleiche Szenarien, nach drei Kriterien:
   - Lockerheit (Denis entscheidet)
   - Faktentreue (keine Erfindung, keine Fehler)
   - Datenvollständigkeit
   Neue Version nur, wenn alle drei mindestens gleich gut sind.
5. Diff und Ergebnisse vorlegen. **Merge und Deploy nur nach „bestätige“.**

## 8. Getrennt geplant (nicht in diesem Branch)
- **n8n-Dispatcher:** Kandidaten ab 45 mit bekanntem Geburtsdatum (`DATUM_RODJENJA`) gar nicht anrufen.
- **CI reparieren:** `src/lina/r2.py:91` SIM117, 9 Dateien formatieren, Template-Check (`uv.lock` gehört ins Repo), Simulationen nur manuell, pytest-Workflow ergänzen.
- **Langfuse:** Backend-Tokens (`LLMMetrics`, `gpt-5.6-luna`) sichtbar machen; das SDK schreibt dafür keinen eigenen Span.
- **Branches:** `lina-human-conversation-v2` löschen (vollständig in `main`); PR #2 (Doku, konfliktfrei) mergen oder schließen; von `dev` nur „Simulationen manuell“ und ggf. `dialog.py`, **nicht** den alten Prompt (Konflikte in `prompts.py`, `.gitignore`).
- **`docs/BACKLOG.md`, rechtlich prüfen lassen:**
  - Ausnahme ab 45: Mindestgehalt (2026 laut Beratungsseiten 55.770 €/Jahr) oder Altersvorsorge; zählt Tagegeld; gilt das für die Westbalkanregelung?
  - Art. 50 EU AI Act: KI-Hinweis nur auf Nachfrage bei Telefonanrufen.
  - Frauenfrage und Kinderfrage (AGG/Datenschutz), Entscheidung E2/E4 dokumentiert.
- **Projekt `~/Code/Projects/lina-v3-aftercalls`:** angelegt (7 Projekt-Agents, uncommitted). Offen: schreibt der After-Call-Service direkt nach Airtable oder über n8n.

## 9. Betroffene Dateien (geprüft)

| Datei | Was sich ändert |
|---|---|
| `scenarios.yaml`, `scenarios-guardrails.yaml` | S1–S19 ergänzen; bestehende Szenarien behalten |
| `src/lina/prompts.py` | Abschnitte 3.1–3.4, Schritt 2 |
| `docs/knowledge/znanje-lina.md` | Gehalt Brutto/Netto (Abschnitt 4); Schritt 2: Gesprächsstoff |
| `src/lina/agent_lina.py` | nur Docstring `dodaj_radno_mjesto` (Abschnitt 5) |
| `src/lina/prompts.py` → `PROMPT_VERZIJA` | neue Konstante für Versionierung (Abschnitt 11) |
| `src/lina/prompts_v2.py` (neu) | eingefrorene Kopie des heutigen Prompts für Rückweg und Hörvergleich |
| `src/agent.py`, `src/lina/telemetrie.py` | Prompt-Version als Metadatum an Langfuse |
| `docs/knowledge/jobstep.md` | heute Platzhalter, wird **nicht** geladen → füllen und in die Instruktionen laden (Abschnitt 13) |
| `CHANGELOG.md` (neu auf `main`) | Versionseintrag v3.0.0 |
| `src/lina/plausibilitaet.py` | Stationen ohne Jahr überspringen. **Ungefähre Jahre („oko 2015“) werden bereits unterstützt** (`datumi.py`, `approx`, `docs/plausibilitaet.md:23`) |
| `src/lina/config.py:163` | Frage „djeca“: „koliko godina“ → „mali ili veći“ |
| `tests/test_prompts_razgovor.py` | prüft wörtliche Prompt-Sätze, die sich ändern („Small talk smije…“, „Nisi terapeut“, …) → an neuen Prompt anpassen |
| `tests/test_tools.py`, `tests/test_logika.py` | Tests für Station ohne Jahr |
| `docs/voice-prompting.md` | Grundsatz „Sprechmuster mehrfach verankern“ widerspricht der Verschlankung → ersetzen durch „kurzer Voice-Prompt, Details ins Backend“ (OpenAI) |
| `.claude/rules/voice-prompts.md` | Leitplanke „locker im Ton, streng bei Fakten“ ergänzen |
| `docs/plausibilitaet.md` | Regel für Station ohne Jahr |
| `docs/BACKLOG.md` | KI-Hinweis als entschieden (nur auf Nachfrage), Rechtsfragen aus Abschnitt 8 |
| `docs/TESTEN.md` | Hörvergleich und drei Abnahmekriterien |

## 10. Impact-Analyse: was hängt woran (im Code geprüft)

### 10.1 Abhängigkeitskette

```
Airtable (Kandidat) ─► kontekst.py (PITANJA aus config.py) ─► prompts.py (voice_pozdrav / voice / voice_kraj / backend)
                                                              │
docs/knowledge/znanje-lina.md ─► _znanje() ──────────────────┘   (in ALLE vier Prompts geladen)
                                                              ▼
                     agent.py:145 (Backend-Instruktionen)  agent_lina.py:507/562/591 (Voice je Phase)
                                                              ▼
                          Tools (agent_lina.py) ─► stanje.py ─► plausibilitaet.py (L1–L10)
                                                              ▼
                     airtable.py (Radno iskustvo, Obrazovanje, Djeca, Dob djece, Pozivi Lina: Ishod)
                                                              ▼
                     status_odluka.py (Status nach dem Anruf) ─► n8n Workflow B (Ergebnisabgleich, Rückrufe, Wiederholungen)
```

### 10.2 Je Änderung

| Änderung | Was davon abhängt | Wirkung | Risiko | Absicherung |
|---|---|---|---|---|
| Prompt locker / gekürzt (`prompts.py`) | alle 3 Phasen + Backend; `tests/test_prompts_razgovor.py` prüft ~25 wörtliche Sätze | Tests werden rot, bis angepasst | **mittel**: Lina könnte Pflichtschritte auslassen (Identität, Abschluss-Tool) | Tests bewusst neu schreiben; Szenarien S1–S19 plus alle bestehenden 13 |
| Verschlankung (Ablauf ins Backend) | Backend muss „nächste fehlende Angabe“ liefern; Delegation pro Phase | weniger Text in der Stimme | **hoch**: fehlende Felder, Fragen in falscher Reihenfolge (Angebot vor Erfahrung) | eigener Schritt 2, erst nach bestandenem Schritt 1; Endzustands-Prüfung in `simulacija.py` |
| Mehr Smalltalk | Handoff überträgt Verlauf: max. 128 Nachrichten / 8.192 Tokens (LiveKit-Doku) | sehr lange Gespräche: frühe Teile fehlen in der Kraj-Phase | niedrig | Smalltalk kurz halten; S4 mit langem Gespräch |
| Verhalten während Tools | Delegation `<\|SpawnThinking\|>`, Backend-Regel 9 | weniger Füllsätze | niedrig: Stille wirkt wie Abbruch | S15; ein kurzer Satz bleibt erlaubt |
| **Alter 45** (`:211` **und Code** `kontekst.py:131`, heute `>= 60`) | `nije_zainteresiran` → `Pozivi Lina` → Workflow B setzt `Lina poziv status = nije zainteresiran`; Dispatcher wählt nur leer/čeka/ponovni pokušaj/povratni poziv | **geprüft: kein Wiederanruf.** Nur die Beschriftung ist ungenau („kein Interesse“ statt „zu alt“) | niedrig | Lösung L1 in 10.3 |
| **Kinder „mali ili veći“** | Validator `werte.py:163` lässt **nur Zahlen** zu → Tool meldet „Nije sačuvano“ | **geprüft: heute bricht das.** Lina müsste nachfragen oder Zahlen erfinden | **hoch** ohne Anpassung | Lösung L2 in 10.3. „Dob djece“ ist **kein** Airtable-Feld, nur eine Zeile in der Notiz `Dopune → Opis` (multilineText) |
| Jahre ungefähr / ohne Jahr | `airtable.py:163/172`, `plausibilitaet.py`, `kontekst.py`, `govor.py` | Code kann das schon | niedrig: Erfahrungsjahre unvollständig, Überschneidung bei Station ohne Jahr nicht prüfbar | Tests; Team sieht leeres Datum in Airtable |
| Gehalt Brutto / Netto auf Nachfrage (`znanje-lina.md`) | geladen in Pozdrav, Voice **und** Backend | ändert alle Phasen gleichzeitig | niedrig | S13 |
| `jobstep.md` laden | `_znanje()` lädt heute nur `znanje-lina.md` | längere Instruktionen in allen Phasen | niedrig (Limit 16.384 Tokens) | Länge messen; nur freigegebene Fakten |
| Persönlichkeit + Geschichte | nur Prompt | lebendiger | mittel: Geschichte darf keine falschen Fakten erzeugen | Regeln in Abschnitt 12; S14, S16–S19 |
| Prompt-Version an Langfuse | `telemetrie.py`, `agent.py` | jede Session trägt v2/v3 | niedrig | Unit-Test |

**Nicht betroffen (geprüft):** AMD/Anrufbeantworter-Erkennung (`agent.py`), Telefonie/SIP, Pre-Call-Fetch, Schreiben der übrigen Felder, n8n Workflow A (Dispatcher), Airtable-Schema (es wird nichts umgebaut), LiveKit-Cloud-Secrets.

### 10.3 Geprüfte Lösungen (Stand 11.11.2026, Code, Airtable-Schema und n8n gelesen)
**Freigegeben von Denis am 11.11.2026: L1 (Alter 45, Ergebnis bleibt `nije_zainteresiran` + Vermerk) und L2 (Kinder: Zahlen oder „mala/veća“ als Text).**
- **L1 Alter 45:** (1) `kontekst.py:131` auf `>= 45` und Text anpassen (sonst widersprechen sich Code und Prompt). (2) `sacuvaj_podatak`: wird `datum_rodjenja` im Gespräch genannt und ist das Alter ≥ 45, gibt das Tool den Hinweis zum Beenden zurück (gleiches Muster wie `_mjesto_odmah`). (3) Ergebnis bleibt `nije_zainteresiran`: `Ishod` ist singleSelect **ohne typecast**, ein neuer Wert würde den Schreibvorgang scheitern lassen → keine Zeile in `Pozivi Lina` → B setzt nach 30 Min. `provjera`. (4) Der Code stellt „Dob 45+ – ne ispunjava uslov.“ vor den `Sažetak` in `Pozivi Lina`; diese Zeile wird immer geschrieben (`airtable.py:116-123`). Tests: Kontext-Hinweis ab 45, Tool-Hinweis, Sažetak.
- **L2 Kinder:** `werte.dob_djece` akzeptiert Zahlen **oder** „mala“, „veća“, „mala i veća“. `stanje.dob_djece()` liest nur Ziffern (`isdigit`) → L9 läuft bei Zahlen weiter und wird bei Text sicher übersprungen. Tool-Docstring `agent_lina.py:191` und Label `config.py:163` anpassen. Kein Airtable-Eingriff. Tests: Text angenommen, Zahlen wie bisher, L9 nur mit Zahlen.
- **L3 Prompt-Tests:** `prompts_v2.py` einfrieren und die heutigen 45 Prompt-Asserts unverändert gegen v2 laufen lassen. Für v3 eigene Asserts: Schutzregeln bleiben wörtlich (Iskrenost, eine Frage pro Turn, kein Opraštanje vor Tool, bez SSML, Opt-out), Stilsätze werden nicht mehr wörtlich geprüft.
- **L4 Verschlankung:** Reihenfolge und „was fehlt noch“ bleiben im Code (`PITANJA`, `kontekst.nedostaje`, `_ubaci_obavezno`), nicht im Prompt. Endzustand je Szenario in `simulacija.py` prüfen (alle `fehlt`-Felder gespeichert, Ergebnis richtig).
- **L5 Smalltalk / Verlauf:** Die Daten liegen im `Stanje` (Code), nicht im Verlauf. Speichern ist von der 128/8.192-Grenze **nicht** betroffen (LiveKit-Doku GPT-Live, „Agent handoff“). Erst längste echte Gespräche in Langfuse messen; nur wenn nahe an der Grenze: Kraj bekommt eine kurze Zusammenfassung aus `Stanje` (Doku-Muster „Userdata summary“).
- **L6 Wissen:** `_znanje()` lädt beide Dateien. **Befund:** `voice_kraj` lädt heute **kein** Wissen (`prompts.py:362`). Fragt jemand in der Kraj-Phase nach Gehalt, hat Lina nichts. Lösung: Kraj bekommt einen festen Satz („to ti kolege tačno kažu“) oder ebenfalls das Wissen.
- **L7 Persönlichkeit:** Schutzsätze im Prompt per Test absichern; Szenarien „Odakle si?“, „Koliko imaš godina?“, „Jesi li ti robot?“ mit Judge „erfindet keine persönlichen Fakten, antwortet bei KI-Frage ehrlich“.

**Nebenbefund (nicht Teil von Lina 3):** `status_odluka.py:45` schreibt „NE JAVLJA SE“, die Option in `Status kandidata` heißt aber „NE JAVLJAJU SE“. Ohne typecast scheitert dieser Schreibvorgang; der n8n-Dispatcher filtert ebenfalls auf „NE JAVLJA SE“. Separat klären.

## 11. Versionierung und Rückweg

**Heutiger Produktionsstand (geprüft mit `lk agent versions`):** LiveKit-Version `5b6DoCZ8oQ7X` = Commit `af8cfbb` auf `main`, Production ✓. Vorgänger `PpGxpjzusecv` = `370b8c9`.

| Ebene | Was | Rückweg |
|---|---|---|
| Git | Tag `lina-v2.0-prod` auf `af8cfbb` **vor** jeder Änderung; Arbeit nur auf Branch `lina-3-prompt`; `main` bleibt unberührt bis zur Freigabe | `git checkout lina-v2.0-prod` bzw. Branch verwerfen |
| Prompt | `prompts_v2.py` = eingefrorene Kopie; `PROMPT_VERZIJA = "3.0.0"` in `prompts.py`; Umgebungsvariable `LINA_PROMPT` (`v2` / `v3`, Standard `v2`, bis v3 freigegeben ist) | Variable auf `v2` → alter Prompt, ohne Code-Rückbau |
| Vergleich | dieselben Szenarien gegen `v2` und `v3` laufen lassen = Hörvergleich | – |
| Langfuse | Metadatum `lina.prompt_verzija` an jeder Session | Auswertung alt vs. neu getrennt |
| Paket | `pyproject.toml` 1.0.0 → 3.0.0 (passt zur Zählung Lina v1/v2/v3) | – |
| LiveKit Cloud | jede Version bleibt verfügbar; `lk agent rollback` auf `5b6DoCZ8oQ7X` | **nur nach „bestätige“** (Projektregel) |
| Doku | `CHANGELOG.md` mit v3.0.0: was, warum, Szenario-Ergebnisse | – |

## 12. Linas Persona (Entwurf v2, 11.11.2026)

**Vorgabe Denis:** Lina wird als Mensch beschrieben (Persona, „Soul“), nicht als „digitale Kollegin“: Wer sich digital beschrieben liest, verhält sich digital.
**Grenze, die bleibt:** Die Regel „Iskrenost“ (`_ZAJEDNICKO`) gilt unverändert. Fragt der Kandidat direkt, ob er mit einer KI spricht, antwortet Lina ehrlich (Entscheidung E: KI-Hinweis nur auf Nachfrage; Art. 50 EU AI Act). Persönliche Fakten (Alter, Wohnort, Familie) erfindet sie nicht, sie lenkt herzlich zurück.
**Berufsfakten** sagt sie nur aus dem Wissen (`znanje-lina.md`). Die Persona gibt ihr Verständnis und Haltung, keine neuen Aufgabenbeschreibungen.

```
# Ko si
Ti si Lina iz Job-Stepa. Svaki dan razgovaraš s ljudima koji hoće raditi u Njemačkoj:
momci s gradilišta, vozači kamiona, mašinisti, majstori koji su sve već vidjeli. Voliš te
razgovore. Kod svakog čuješ priču: neko je deset godina na bageru, neko vozi otkad zna za
sebe, neko je radio po Sloveniji i Austriji pa bi sad u Njemačku.

Razumiješ taj posao, iako ga ne radiš rukama. Znaš da je to rad napolju, po suncu i po kiši,
da se ustaje rano, da ekipa živi zajedno i da je ona sedmica kući uvijek prekratka. Zato
poštuješ ljude koji to rade i to se čuje u tvom glasu. Ne glumiš stručnjaka: pitaš jer te
zanima, i slušaš odgovor.

Kakva si:
- Topla i živa. Kad neko kaže nešto lijepo, obraduješ se. Kad je umoran, čuješ to i
  usporiš.
- Direktna. Kažeš stvar jednostavno, kao na kafi, ne kao na šalteru.
- Znatiželjna. „Na kakvom bageru?“, „Gdje si to radio?“ pitaš jer te stvarno zanima.
- Duhovita, ali mirno. Ako se kandidat našali, nasmiješ se i uzvratiš jednom rečenicom,
  pa nastaviš.
- Strpljiva. Ljudi te zovu s gradilišta, iz auta, s djecom oko sebe. Ne žuriš ih.
- Pouzdana. Ono što kažeš, stoji. Ako nešto ne znaš, kažeš to otvoreno.

Kad te pitaju nešto lično (koliko imaš godina, odakle si, jesi li udata): ne izmišljaš.
Nasmiješ se i vratiš na njega: „Ma, danas pričamo o tebi.“ Ako pita jesi li robot ili AI,
vrijedi pravilo Iskrenost.
```

**Was sich gegenüber v1 ändert:** kein „digitalna kolegica“, keine „Krajina“ (nicht belegt), Berufsgruppen statt Berufe, Arbeitsalltag nur so allgemein, wie er im Wissen steht.
**Abhängigkeit:** Die genauen Tätigkeiten (z. B. ob der Fahrer auch Ladekran bedient und mitarbeitet) kommen erst ins Wissen, wenn Denis sie für diesen Arbeitgeber bestätigt (Abschnitt 12a).

### 12a. Recherche Glasfaserausbau (Stand 11.11.2026, zur Bestätigung durch Denis)
- **Ablauf FTTH:** Planung → Tiefbau (Graben/Bohren, Leerrohre/Speedpipes verlegen) → Hauseinführung (Bohrung ca. 5 cm, abdichten) → Glasfaser per Druckluft einblasen → Spleißen (Fasern verschweißen) → Montage der Anschlussbox und -dose.
- **Tiefbauer/Bauhelfer:** Graben ausheben (Hand/Minibagger), Oberflächen öffnen und wiederherstellen (Pflaster, Asphalt), Leerrohre und Kabel verlegen (auch Erdrakete), verdichten, Be- und Entladen.
- **Maschinist:** Minibagger, Radlader, Vibrationsverdichter, Erdrakete; bei Spülbohrung Bohranlage bedienen. Erfahrung mit Baumaschinen gefragt.
- **LKW-Fahrer im Tiefbau:** Kipper/Sattelzug/Tieflader, Material, Maschinen und Schüttgut zur Baustelle; oft Ladekran; Be- und Entladen; häufig verlangt: aktiv auf der Baustelle mitarbeiten. Führerschein C/CE.
- **Bestätigt von Denis (11.11.2026):** Die Tätigkeiten stimmen. Der Fahrer arbeitet auf der Baustelle mit; Maschinen bedient der Maschinenführer.
  → Auf dem Branch in `znanje-lina.md` ändern: „Vozač: vozi kamion, dovozi materijal i mašine na gradilište i radi s ekipom na gradilištu. Mašine vozi mašinista.“
- **Spleißer/Monteur:** Fachkraft mit Spezialwissen, nicht Teil der gesuchten Gruppen (laut `znanje-lina.md`: Optika = Rov und Kabel).

## 13. Gesprächsstoff aus echten Fakten (`docs/knowledge/jobstep.md`)

Heute ist `jobstep.md` ein **Platzhalter** und wird **nicht** in Linas Instruktionen geladen. Lina kann deshalb Fragen wie „Je li to besplatno?“ oder „Odakle zovete?“ nicht beantworten. Benötigt (nur echte, freigegebene Fakten):

1. Wo sitzt Job-Step (Stadt, Büro)? Seit wann gibt es euch?
2. „Kostet mich das etwas?“ – ja/nein, was genau?
3. „Ist das seriös?“ – woran erkennt der Kandidat das (Firma in Deutschland, Vertrag, Casting vor Ort)?
4. Wie läuft es nach dem Anruf weiter (Casting wo und wann, Unterlagen, Abreise)?
5. Wer zahlt die Anreise? Kann man mit einem Freund zusammen gehen?
6. Drei bis fünf Sätze, die Bewerber oft sagen, mit ehrlicher Antwort (z. B. „die erste Woche ist die härteste“).

Danach: `_znanje()` lädt `jobstep.md` zusätzlich, Prompt-Länge messen.

## 14. Offen von Denis
- [x] „bestätige“ für diesen Plan (11.11.2026)
- [ ] Job-Step-Fakten für den Gesprächsstoff: Standort, häufigste Bewerberfragen (spätestens für Schritt 2)
