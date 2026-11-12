# Changelog – Lina

Versionsnummer: `pyproject.toml` (Hauptversion.Funktion.Korrektur). Ablauf: `docs/DEPLOY.md`.
„LiveKit-Version“ = ID aus `lk agent status` (für `lk agent rollback`).

## 1.1.1 – für Staging vorbereitet, V3-Gesprächsrhythmus, 12.11.2026

- Nur V3-Voice-Prompt: natürliche, leicht variierende Satzmelodie statt flacher Melodie;
  Reaktionen nach Bedarf statt nach jeder Antwort; Smalltalk auf Initiative des Kandidaten;
  keine stereotypen Komplimente, keine obligatorischen Neugier-Fragen.
- Keine Wartefloskel bei jeder Speicherung; kurze Denkpausen zulassen; Begrüßung und
  Verabschiedung gekürzt. Widerspruch zwischen Familienkommentar und neutraler Kinderfrage
  im Stilteil entfernt.
- Backend-Anweisungen, fachlicher Ablauf, Modell, Stimme und V2 bleiben in diesem Patch
  unverändert. Vorhandene V3-Fachregeln sind damit nicht fachlich abgenommen.
- `scenarios-gpt-live.yaml`: bisherige Pflicht-Smalltalk-Erwartung korrigiert, drei
  Szenarien ergänzt. Übergabe und manuelle Hörprüfung: `docs/HOERTEST-V3.md`.
- Prüfung 12.11.2026: 115 Python-Tests bestanden, inklusive V2-Golden-Test; Ruff-Lint und
  Formatprüfung der geänderten Python-Dateien bestanden. Gesamtlauf: bestehender SIM117
  und acht Formatabweichungen, auch im unveränderten Basis-Repository bestätigt.
- Version 1.1.1 mit `uv lock` abgeglichen, keine Dependency-Upgrades. Sprachwechsel-Ausnahme
  im V3-Voice-Prompt entfernt; Abschiedstest akzeptiert Groß-/Kleinschreibung.
- Erster Audio-Lauf `SR_f74K3ow9UAVL`: 6/12 bestanden. Nachfragen trotz Zeitmangel und
  Abweisung von „Kako si?“ im Transkript erkannt; V3-Voice-Regeln gezielt nachgeschärft.
  Vollständiger Audio-Nachtest `SR_KcdVB2A8wAE3`: 5/12 bestanden, 7/12 fehlgeschlagen.
  Kurze Antworten bestehen, Smalltalk wird im Transkript warm beantwortet, der Fall endet
  aber mit 30 s Stille. Offen: Abschied vor Auflegen, Rückrufbestätigung, unbelegte
  Speicherbestätigung und Session-Ende-Fehler. Keine Audio-Abnahme, kein Deployment.
- Noch kein Commit, Push, Deployment oder manueller Hörvergleich. Downloads-Kopie besitzt
  kein eigenes Git; Übernahme in bestehendes Lina-Repository angefragt. Details: `docs/HOERTEST-V3.md`.
- `tools/deploy-v3-staging.sh`: erzeugt einen getrennten Dateistand, prüft Ruff und Pytest,
  committet nur die angegebenen Dateien auf einem neuen Arbeitsbranch, pusht und deployt
  den geprüften Stand nach staging. Bricht bei Fehlern ab. Kein Audio-Test im Skript;
  die hörbare Wirkung wird anschließend manuell geprüft.

## 1.1.0 – staging, 11.11.2026 (Branch `lina-3-prompt-v2`, Git-Tag `v1.1.0-rc.1` = Commit `847c444`, LiveKit-Version `mshPFHzUFdGr`, noch nicht abgenommen)
- Staging läuft ohne Secret mit v3 (`LIVEKIT_AGENT_DEPLOYMENT=staging`), production bleibt v2.
  Grund: LiveKit-Secrets gelten für alle Deployments eines Agents.
- Nach dem Testanruf vom 11.11.2026 (andere Claude-Sitzung, Punkte 1–8 und 10 der Analyse,
  Sprachpunkte 1–3 und 6):
  - Abschluss ohne neue GPT-Live-Session (`append_instructions` + `update_tools`), sonst Handoff
    mit `KrajAgent.on_enter`.
  - Backend `reasoning`/`verbosity` = low (`LINA_BACKEND_REASONING`, `LINA_BACKEND_VERBOSITY`,
    `LINA_BACKEND_MAX_TOKENS` opt-in).
  - v3-Prompt: Ponuda nur auf Wunsch, „nur das Gefragte beantworten“, Kinderfrage ohne Turnus,
    Speichern nach jeder Antwort, gemeinsamer Sprachblock (Akzent Bihać, IPA, Wortliste).
  - „Već imamo iz prijave“ im Kontext (nur Feldnamen, keine Werte).
  - Korrekturen an Stationen/Schulen über alle Einträge; Einträge aus der Bewerbung werden nicht
    geändert, sondern als „Ispravka …“ in Dopune vermerkt.
  - Kartenabfragen in einem Thread; `jezik.py` korrigiert kroatische/ekavische Wörter im Gespräch.
  - 4 Szenarien in `scenarios-gpt-live.yaml`.
- Hörtest 11.11.2026: Lina verabschiedete sich nicht und legte nicht auf. Jetzt: warmer Abschied
  mit „ćao“ in derselben Antwort, und 40 s nach `predji_na_kraj` legt der Code auf, falls
  `zavrsi_razgovor` nicht kam (gespeichert wird dann über `ishod_bez_kraja()`).
- v2 eingefroren: Kontextzeile „Već imamo“, Abschluss ohne Session, `KrajAgent.on_enter`, Backend
  low, Sprachkorrektur und der neue Text von `zavrsi_razgovor` wirken nur in v3.
  `tests/test_v2_eingefroren.py` prüft die v2-Prompts zeichengleich gegen `lina-v2.0-prod`.
  Für v2 wirken mit Absicht: Nummerierung der Korrekturen über alle Einträge (Fehlerkorrektur,
  die Tool-Beschreibungen gelten für beide), Kartenabfragen im Thread, Tool-Beschreibungen.
- v3-Prompt: Abschnitt „Ritam razgovora“ mit kurzem menschlichem Einstieg, Reaktion vor jeder
  nächsten Frage, einer Neugier-Frage pro Station, Übergängen und Reaktionsbausteinen (nach Alma).
- Sprachkorrektur zählt Hinweise statt Wörter; `on_enter` prüft das Ergebnis von `generate_reply`.
- 2 Szenarien: Abschied mit Auflegen, Gesprächsrhythmus.
- Offen: Unterbrechungsschwellen (Hörtest), Stimmenwahl per Anhören, Beispielsätze aus Bihać.

## 3.0.0 – in Arbeit (Branch `lina-3-prompt`, noch nicht abgenommen)
- Umschaltbar über `LINA_PROMPT` (`v2` Standard, `v3` neu); Langfuse-Metadatum `lina.prompt_verzija`.
- `prompts_v2.py` + `docs/knowledge/znanje-lina-v2.md`: eingefrorener Produktions-Prompt (geprüft zeichengleich mit `af8cfbb`).
- Prompt v3: Persona als Mensch (Iskrenost bleibt), Emotion/Humor/Smalltalk, eine Tempo-Regel,
  Verhalten während Tools, die fünf Regeln aus 0.2.2, Alter ab 45 (Grund Arbeitserlaubnis),
  Kinder „mali ili veći“, Jahre ungefähr/ohne Jahr, Gehalt brutto zuerst.
- Wissen: `jobstep.md` geladen (nur v3), auch in der Abschlussphase; Fahrer arbeitet auf der Baustelle mit.
- Code: 45+ beendet in v3 mit Vermerk „Dob 45+ – ne ispunjava uslov.“ im Sažetak (Ishod bleibt
  `nije_zainteresiran`); `dob_djece` nimmt auch „mala“, „veća“, „mala i veća“.
- Szenarien: `scenarios-lina3.yaml` (S1–S19, P1–P3).

## Merge dev → main – 11.11.2026 (Commit `988e23a`)
- Aus dev übernommen: Langfuse-Dialog beider Seiten (`src/lina/dialog.py`), Version und
  Environment in Langfuse, Simulationen nur manuell, Wartezeit am Simulationsende,
  `testanruf*.json` ignoriert (zusätzlich bleibt `allowlist-testanruf.json`), DEPLOY-Ablauf,
  Szenarien-Anpassungen und `scenarios-neu.yaml`.
- Nicht übernommen: `prompts.py` aus 0.2.2 (main ist neuer), Version und `uv.lock` aus dev.
  Die Prompt-Regeln aus 0.2.2 (Scherz, Beleidigungen, Rückruf mit Wochentag, „schon in der
  Bewerbung“, E-Mail-Bestätigung) kommen erst mit dem Lina-3-Prompt.
- Korrektur: Langfuse-Abschluss nutzt `stanje.ishod or stanje.ishod_bez_kraja()`, wie beim Speichern.

## 1.0.0 – production, 10.11.2026 (Commit `af8cfbb`, Git-Tag `lina-v2.0-prod`, LiveKit-Version `5b6DoCZ8oQ7X`)
- Stand von main vor Lina 3: AMD mit EU-fähigem STT, Handoffs Pozdrav → Lina → Kraj ohne
  doppelte Tools, Status nach dem Anruf aus den Fakten, Gesprächsende ohne Abschluss über
  `ishod_bez_kraja()`. Einzelheiten in `git log 44cbd65..af8cfbb`.

## 0.2.2 – dev, nur teilweise nach main übernommen
- Stimmen-Prompt nach OpenAI-Leitfaden „Prompting GPT-Live“: Delegation policy mit
  `<|SpawnThinking|>` und `Backend tools:`, Backchannel policy, Interruption policy;
  nicht raten beim Warten, Bestätigung erst nach Backend-Ergebnis.
- Ablauf-Schritte nur für fehlende Angaben; „schon in der Bewerbung“ sofort akzeptieren.
- E-Mail buchstabiert zurücklesen und bestätigen lassen, erst dann speichern.
- Scherz/Unglaubwürdiges: einmal mit Humor ernst nachfragen; Backend speichert keine Scherze
  und keine beleidigenden Begriffe.
- Smalltalk kurz und menschlich; weniger gleichförmige Bestätigungen.
- Rückruf: Wochentag, Datum, Uhrzeit vom Backend; Widerspruch erst klären.
- Simulation: Endprüfung wartet auf den Gesprächsabschluss (asynchrone Delegation).
- Szenarien: Erwartungen präzisiert, Opt-out-Persona Kroatisch (Simulator lehnte „bos“ ab),
  neu `scenarios-neu.yaml` (Scherzantwort, E-Mail, Smalltalk).

## 0.2.1 – dev (Commit `de4dc06`)
- Versionsnummer in Langfuse (`langfuse.release`, `lina.version`).
- GitHub-Simulationen nur noch manuell (keine automatischen Kosten bei Push auf main).
- `testanruf*.json` von Git ausgeschlossen.

## 0.2.0 – staging, 06.11.2026 (Git-Tag `v0.2.0`, Commit `4fa39a8`)
- Langfuse: Gespräch beider Seiten (Kandidat + Lina) pro `agent_turn` und als ganzer Dialog
  am `agent_session`-Span; Telefonnummern/Secrets maskiert; Environment production/staging/lokal.
- Status: auf staging, Abnahme offen (Testanruf staging hatte Rauschen, Ursache offen).

## 0.1.0 – production, 05./06.11.2026 (Commit `44cbd65`, LiveKit-Version `iV8VZbkKehaz`)
- Erste Cloud-Version: Anruf 1 (Datenerfassung), Airtable, Langfuse (nur Linas Seite),
  Stimme/Emotionen, Telefonie über FusionPBX → TG400. Vorherige LiveKit-Version: `HFgDwp9SRJ9w`
  (gleicher Code).
