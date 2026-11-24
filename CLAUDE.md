@AGENTS.md

# Projekt: Lina – Outbound-Recruiting-Agent (Job-Step)

## Ziel und Prozess
Zweistufiger Outbound-Prozess:
1. **Anruf 1 (aktueller Bau): Datenabfrage.** Lina ruft Bewerber an, bedankt sich für die Bewerbung und fragt **nur die fehlenden, für die Eignung relevanten Angaben** ab. **Sie fordert in diesem Anruf keine Unterlagen an.** Fragen zu Job-Step und zum Jobangebot beantwortet sie aus der Wissensbasis.
2. **Eignungsprüfung:** passiert außerhalb des Gesprächs (Team bzw. Code). Lina entscheidet nicht über die Eignung und kündigt sie nicht an.
3. **Anruf 2 (später): Unterlagen anfordern**, nur bei geeigneten Kandidaten.
- **Auslöser:** statusfrei beim Dispatch. Manueller Start oder per n8n mit Record-IDs, ein Job pro Kandidat. Nach dem Gespräch setzt `src/lina/status_odluka.py` einmal `Status kandidata`, und nur wenn der Wert noch leer, `New Lead` oder `NE JAVLJA SE` ist.
- Später folgt ein eigener Agent für Inbound auf derselben Basis.

## Fixe Vorgaben
- **Sprache: ausschließlich Bosnisch (ijekavski), Anrede „ti“.** Kein Deutsch, kein Englisch im Gespräch. Kandidaten sitzen in BiH.
- **Stack:** LiveKit Agents (Python) und LiveKit Cloud-Projekt `lina-oai`, Agent-Name `livekit-oai-gig-casting`.
- **Modell:** OpenAI GPT-Live 1. Regeln dazu in `.claude/rules/gpt-live.md`.
- **Datenquelle:** ausschließlich Airtable. Regeln in `.claude/rules/airtable.md`, Schema in `docs/airtable.md`.

## Architektur-Leitplanken
- **Pre-Call-Fetch im Code, nicht im Modell:** Vor dem Gesprächsstart lädt der Entrypoint den Kandidaten-Datensatz aus Airtable und berechnet daraus `vorhanden` und `fehlt`. Nur diese Zusammenfassung geht an die Instruktionen, keine Rohdaten.
- **Das Modell interpretiert, der Code entscheidet:** Zustand, Freigaben und Airtable-Schreibzugriffe liegen im Code bzw. in Tools.
- **Zurückschreiben** nur über `sacuvaj()` (Tool `zavrsi_razgovor` oder Shutdown), nur Felder mit Inhalt, Ishod aus `stanje.py` (`zavrseno`, `djelimicno`, `povratni_poziv`, …).
- **Drei Gesprächsphasen:** Pozdrav → Prikupljanje → Kraj. Tools nur in der Phase. GPT-Live startet pro klassischem Handoff eine neue Modell-Session; `chat_ctx` ohne alte Instruktionen mitgeben. In **v3** ist Kraj kein Handoff, sondern `append_instructions` + `update_tools` (siehe `docs/PROMPTS.md`).
- **Wissen** liegt in `docs/knowledge/` und wird von dort in die Instruktionen geladen, nicht im Code dupliziert. v2 liest nur `znanje-lina-v2.md`, v3 `znanje-lina.md` + `jobstep.md`. `job-angebot.md` wird nicht geladen. YAML-Frontmatter dieser Dateien landet auf `main` derzeit mit im Prompt.

## Datum und Zeit
- Zeitzone **`Europe/Sarajevo`** (MEZ/MESZ, Sommerzeit automatisch). **Nie fest „UTC+1“ setzen.**
- Der Entrypoint gibt beim Start das aktuelle Datum, den Wochentag und die Uhrzeit in `Europe/Sarajevo` an die Instruktionen. Zusätzlich gibt es das Tool `trenutno_vrijeme` für lange Gespräche, Rückrufe und relative Angaben wie „sutra“ oder „za dvije sedmice“.
- Rückruftermine immer als absolutes Datum mit Uhrzeit speichern und dem Kandidaten auf Bosnisch bestätigen.

## Datenerfassung
- Berufserfahrung und Ausbildung sind **mehrfach**: Station für Station, neueste zuerst, bis keine weitere kommt.
- **Plausibilität** prüft der Code (Tool `provjeri_podatke`), nicht das Modell. Regeln in `docs/plausibilitaet.md`. Pro Auffälligkeit genau einmal nachfragen.
- **Bestätigung nur bei Unsicherheit oder langem Eintrag**, eine kurze Parafrase, nicht nach jeder Station. Nie mehrere Stationen auf einmal vorlesen.
- **Auswahl statt Freitext:** Schreib-Tools akzeptieren nur Werte aus `docs/feldwerte.md`.
- **Airtable-Schutz:** Bestehende Felder und Daten werden nie umgebaut, überschrieben oder gelöscht. Neue Felder nur nach Freigabe.
- **Fragenkatalog:** Reihenfolge und Schalter stehen in `PITANJA` (`src/lina/config.py`), nicht in älterer Entwurfsdoku. `status_boravka` und `radna_dozvola` sind `abfragen=False`. Adresse, Geburt, Familie, E-Mail und Staatsangehörigkeit **werden** gefragt, wenn leer. Siehe `docs/airtable.md`.
- Keine Sprach-Kontrollfragen auf Deutsch oder Englisch. Sprachniveau ist eine Selbsteinschätzung.

## Arbeitsregeln
- LiveKit entwickelt sich schnell: APIs, CLI-Flags, Modelle und Preise immer zuerst prüfen (Skill `reading-livekit-docs` bzw. `lk docs`), nie aus dem Gedächtnis antworten.
- Belegte Fakten, Schlussfolgerungen und Annahmen trennen. Unsicherheit benennen.
- Verhaltensänderung → zuerst ein Szenario in `scenarios.yaml`, dann bauen, dann `lk agent debugger`.
- **Kein Deploy, kein Rollback, keine Änderung an Cloud- oder Airtable-Daten ohne meine ausdrückliche Bestätigung.** Bei mehrstufigen Änderungen erst den Plan zeigen und auf „bestätige“ warten.
- Gegen Airtable nur mit **Test-Datensätzen** entwickeln, bis ich die Produktivtabelle freigebe.

## Datenschutz und Secrets
- Kandidatendaten sind personenbezogen: keine Namen, Telefonnummern oder Dokumentinhalte in Logs. Nur Record-IDs loggen.
- Ausnahme mit Absicht: Langfuse speichert vollständige Gespräche (`LANGFUSE_INHALTE=1`, Entscheidung Denis 05.11.2026) zur Absicherung.
  Beide Seiten (Kandidat + Lina) über `src/lina/dialog.py`; Telefonnummern und Secrets werden vor dem Export maskiert.
- Keys nur in `.env.local` (gitignored). Nie in Code, Commits oder Chat.

## Code-Struktur
- `src/agent.py`: Einstieg, AMD (kein Simulation), Start mit PozdravAgent, Sprachkorrektur-Hook (nur v3)
- `src/lina/verzija.py`: v2/v3 aus `LINA_PROMPT` bzw. `LIVEKIT_AGENT_DEPLOYMENT`
- `src/lina/config.py`: alle Airtable-IDs und der Fragenkatalog `PITANJA` (Reihenfolge, `abfragen=False` schaltet eine Frage ab)
- `src/lina/kontekst.py`: „nur wenn leer“ inkl. Dopune · `plausibilitaet.py`: L1–L10 · `werte.py`: erlaubte Werte
- `src/lina/agent_lina.py`: PozdravAgent, LinaAgent, KrajAgent
- `src/lina/prompts_v2.py`: eingefrorener Produktions-Prompt · `prompts.py`: v3
- `src/lina/airtable.py`: Lesen, Schreiben, einmal Status · `status_odluka.py`: Statusname aus Fakten
- `src/lina/r2.py`: optionales Transkript nach R2 · `dialog.py` / `telemetrie.py`: Langfuse
- `src/lina/govor.py`: Pflichtfragen aus dem Gesagten · `jezik.py`: ijekavica-Korrektur · `mapa.py`: Nominatim BA
- `src/lina/simulacija.py`: Szenarien-Daten und Endzustands-Prüfung

## Projektdokumente
- `docs/ARCHITEKTUR.md`: Phasen, Tools, Schreibpfad, AMD, Dispatch
- `docs/PROMPTS.md`: v2/v3, Wissen, Frontmatter-Fallstrick
- `docs/BETRIEB.md`: Setup, Umgebungsvariablen, Dispatch-Vertrag, Fallstricke
- `docs/TESTEN.md`: Tests, Debugger, Console, Simulationen
- `docs/DEPLOY.md`: Staging/Production, Secrets, Rollback
- `docs/knowledge/znanje-lina.md` (v3) / `znanje-lina-v2.md` (v2): Wissen, das Lina sagen darf
- `docs/knowledge/jobstep.md`: nur v3, nur auf Nachfrage · `job-angebot.md`: Entwurf, nicht geladen
- `docs/airtable.md`: Felder, Pflichtunterlagen, Pre-Call-Fetch-Vertrag
- `docs/voice-prompting.md`: Prompt-Prinzipien
- `docs/plausibilitaet.md`: Logikprüfungen
- `docs/feldwerte.md`: erlaubte Werte je Feld
- `docs/legacy-lina-v2.md`: Was aus dem Gemini-Projekt übernommen wird
- `docs/adr/`: Architekturentscheidungen
- `docs/BACKLOG.md`: offene Entscheidungen und Aufgaben
