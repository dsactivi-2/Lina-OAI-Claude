---
title: Backlog – Lina Outbound
---

# Backlog – Lina Outbound

## Offene Entscheidungen
- [ ] **ADR 0001:** GPT-Live über LiveKit Inference (Vorschlag) oder OpenAI-Plugin — im Code läuft Inference, ADR bleibt „Vorschlag“
- [ ] **Airtable-Schema:** echte Felder auslesen, Pflichtunterlagen und „vorhanden“-Felder festlegen (`docs/airtable.md`)
- [ ] **Jobbeschreibung** in `docs/knowledge/job-angebot.md` (Entwurf, **wird nicht geladen**; geladenes Wissen steht in `znanje-lina.md` / `jobstep.md`)
- [x] **Job-Step-Wissen** in `docs/knowledge/jobstep.md` (v3, Stand 11.11.2026)
- [x] **KI-Hinweis:** nur auf Nachfrage (Plan Lina 3, E1)
- [ ] **Aufzeichnung:** ja oder nein, Einwilligungsformulierung
- [ ] **Eignungskriterien** festlegen (wer geht in Anruf 2?)
- [ ] **Anruf 2 (Unterlagen):** später, eigener Ablauf, nutzt `Kratki link za dopunu`
- [ ] **Trigger:** n8n-Workflow oder manuelles Skript, das eine Liste von Record-IDs dispatcht
- [x] **Status-Logik:** `src/lina/status_odluka.py` schreibt einmal `Status kandidata` (nur leer / New Lead / NE JAVLJA SE)
- [x] **Telefonie:** SIP-Pfad dokumentiert (`docs/TELEFONIE.md`); Inbound und eigene LiveKit-Nebenstelle offen
- [ ] **Anrufzeiten** und Wiederholversuche
- [ ] **YAML-Frontmatter** aus Knowledge-Dateien vor dem Prompt strippen (Branch `test/znanje-frontmatter`, nicht auf `main`)
- [ ] **AMD/Dispatch-Tests** mergen (Branch `test/amd-stt-und-dispatch`; Verhalten auf `main` ist schon da, Tests noch nicht)

## Entschieden (05.11.2026)
- Mehrfache Erfahrung und Ausbildung: Option B (direkt in `Radno iskustvo` / `Obrazovanje`)
- Vorerst NICHT: berechnete Berufsjahre, Markierung „nije provjereno“
- Alle Plausibilitätsregeln L1–L10 inklusive Lücken-Regel
- Keine Sprach-Kontrollfrage
- Zeitzone `Europe/Sarajevo`

## Aufgaben (Reihenfolge)
0. [ ] Neue Airtable-Felder anlegen (Liste in `docs/airtable.md`), **nach Freigabe**
1. [ ] Airtable-Schema über den Connector auslesen → `docs/airtable.md` aktualisieren
2. [x] Szenarien: `scenarios.yaml` (7, mit Endzustand) und `scenarios-guardrails.yaml` (6)
3. [x] Pre-Call-Fetch, Write-Tools, `provjeri_podatke`, `trenutno_vrijeme` – Fetch gegen K-0196 getestet (nur lesend), Schreiben nur mit Fake-Store getestet
4. [x] Erster Entwurf der Instruktionen (Voice bosnisch, Backend englisch), GPT-Live per Inference
5. [ ] Test mit `lk agent debugger --audio` und `lk agent dev` (Console) – siehe `docs/TESTEN.md`
5a. [ ] Erster echter Schreibtest gegen Airtable (K-0196), danach Testeinträge aufräumen
6. [ ] Feinschliff Persona, Wissen und Einwände
7. [ ] SIP-Outbound
8. [ ] Später: Inbound-Agent
