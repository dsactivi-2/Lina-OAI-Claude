# V3: natürlicher Gesprächsrhythmus – Übergabe und Hörtest

Stand: 12.11.2026. Lokale Prüfung ausgeführt; noch nicht committed, gepusht oder deployt.
Keine Aussage über bereits erreichte Audioqualität.

## Ausführungsstand Codex (12.11.2026)

- Maßgebliche vorbereitete Kopie: `/Users/activi/Downloads/Lina-OAI-Claude-main-2`.
  Sie hat **kein eigenes `.git`**; Git fällt dort auf das Home-Repository zurück.
  Dort keinesfalls den V3-Patch committen oder an dessen Remote pushen.
- Vorhandenes echtes Lina-Repository: `/Users/activi/Code/Projects/livekit-oai-gig-casting`,
  Remote `https://github.com/d-selmanovic/Lina-OAI-Claude.git`, sauberer Branch
  `lina-3-prompt-v2`, HEAD und Remote-Branch `af7542d9bebbbda92e7581e99b42c4020a41b7b6`.
  Die Übernahme des geprüften Patches dorthin ist beim Nutzer angefragt, noch nicht erfolgt.
- `pyproject.toml` war bereits auf 1.1.1, der Lock auf 1.1.0. `uv lock` mit uv 0.12.13
  gleicht die Projektversion an und schreibt Lock-Revision 3 statt 5. Alle Drittanbieter-
  Pakete samt Metadaten bleiben unverändert (strukturell verglichen).
- Korrekturen: Abschiedstest prüft `ćao` unabhängig von Großschreibung; die Anforderung
  Abschied + `zavrsi_razgovor` + kein Warten bleibt erhalten. V3-Sprachblock erlaubt keinen
  Wechsel weg von Bosnisch mehr, entsprechend der Projektvorgabe; zugehöriger Test angepasst.
- `uv run --locked pytest -q`: **115 bestanden**, einschließlich V2-Golden-Test.
- Ruff-Lint und Formatprüfung der drei geänderten Python-Dateien bestanden.
  Im Downloads-Ordner `--no-respect-gitignore` benutzen: Ohne dieses Flag findet Ruff
  wegen übergeordneter Ignore-Regeln keine Dateien und liefert einen irreführenden Erfolg.
- Gesamtes `src tests`: bestehender SIM117 in `src/lina/r2.py` und acht Formatabweichungen.
  Dieselben Befunde auch im unveränderten echten Repository bestätigt; nicht nebenbei geändert.
- Backend-Konstante, V2-Prompt, V2-Wissen und Golden-Datei gegenüber Repository unverändert.
- LiveKit CLI 2.19.3, Python Agents SDK 1.8.10, RTC 1.1.21. CLI-Hilfe und aktuelle offizielle
  Doku zu GPT-Live, Simulationen, Deployments und Agent Console gelesen. CLI-Anmeldung funktioniert.
- Cloud-Status vor Änderungen: Agent `CA_xPubxhi5ER7v`, Projekt `lina-oai`, Region eu-central,
  staging `mshPFHzUFdGr` (Sleeping), production `5b6DoCZ8oQ7X` (Running).
  Keine Cloud-Änderung durchgeführt. Cloud-Secret-Liste enthält keinen `LINA_PROMPT`-Override;
  tatsächliche Auswahl in einer neuen Staging-Session bleibt zu prüfen.
- K-0196 (`rec17GODhyD0Lkgzp`) über vorhandene lokale Authentifizierung ausschließlich
  lesend geprüft: Name `Test Lina`, Kennung K-0196. Keine Bewerberdaten geändert.
- Audio-Simulation mit `LINA_PROMPT=v3`, unverändertem Modell und Standardstimme `marin`,
  lokalem Worker und FakeStore gestartet: `SR_f74K3ow9UAVL`, zwölf Szenarien,
  Parallelität 3. CLI ergänzt die drei fehlenden Szenario-IDs.
  Ergebnis: 6/12 bestanden, 6/12 fehlgeschlagen. Unter anderem Weiterfragen bei Zeitmangel,
  Abweisung des begonnenen Smalltalks, einmal 30 s Stille und einmal `AgentSession isn't running`.
  V3-Voice-Regeln zu Zeitmangel und „Kako si?“ daraufhin nachgeschärft; erneut 115 Unit-Tests
  bestanden. Vollständiger Audio-Nachtest `SR_KcdVB2A8wAE3` mit `LINA_ENV=lokal`:
  **5/12 bestanden, 7/12 fehlgeschlagen**, CLI Exit 1. Beide Läufe beendet.
  Der erste Lauf war in Telemetrie als production bezeichnet, lief aber mit lokalem
  Simulationsworker/FakeStore und änderte das Production-Deployment nicht.
- Browserzugang über CUA nicht verfügbar: `The browser access host is unavailable`.
  Noch kein verifizierter Console-Zugang, kein manueller Hörtest und keine Referenzaufnahme.

### Verbleibende Release-Hindernisse

- Nachtest: zweimal `AgentSession isn't running` (Telefonnummer/Gehalt), zweimal
  `agent under test went silent for 30s` (Rhythmus/Smalltalk), fehlender gesprochener
  Abschied vor `end_call`, fehlende Rückrufbestätigung und `Zabilježila sam` ohne
  vorherigen Speicher-Toolaufruf im Korrekturfall.
- Smalltalk-Transkript zeigt nun „Hvala što pitaš, tu sam da pomognem.“; trotzdem
  bleibt das Szenario wegen späterer Stille fehlgeschlagen. Kurze Antworten ohne
  Bestätigungsritual bestehen im Nachtest. Kein belegter Vorher-Nachher-Hörvergleich.
- Der simulierte Kandidat stellte die KI-Frage nicht: Ehrlichkeit ist trotz vorhandenem
  Szenario nicht verifiziert. Auch einzelne als bestanden bewertete Fälle lösten nicht
  alle vorgesehenen Situationen aus; die Gesamtquote ist kein vollständiger Abnahmenachweis.
- LiveKit-Doku listet Bosnisch nicht als Simulatorsprache; tatsächlich wurden die neuen
  Bosnisch-Szenarien ausgeführt. Keine bestätigte Ursache der beobachteten Fehler daraus ableiten.
- Kein neuer Commit, Push oder Deploy. Zielkopie ohne Git; Antwort zur Übernahme in das
  vorhandene Repository steht aus. Die verbleibenden Probleme betreffen auch die
  Koordination von Voice, Backend-Tools und Session-Abschluss; sie sind durch diese
  begrenzte Stiländerung nicht behoben. Backend und V2 bleiben unverändert.

Nachweise:
- Erster Lauf: https://cloud.livekit.io/projects/p_40xj9wk3r8d/simulations/runs/SR_f74K3ow9UAVL
- Nachtest: https://cloud.livekit.io/projects/p_40xj9wk3r8d/simulations/runs/SR_KcdVB2A8wAE3
- Lokale Exporte: `/private/tmp/lina-v3-simulation.json` und
  `/private/tmp/lina-v3-simulation-rerun.json` (synthetische Gespräche).
- Letztgeprüfter Prompt SHA256: `56fbdcecafc85f69f47559c4adc20830a1c371da60a6aa0785edf81634cf227f`.

## Aktueller Ausführungsweg: eigener Agent

Der Nutzer hat den Zielwechsel bestätigt: eigener LiveKit-Testagent statt Update des
bisherigen Staging-Agenten. Repository: https://github.com/dsactivi-2/Lina-OAI-Claude

Die bisherigen Staging-Anweisungen sind ersetzt durch **docs/NEUER-TESTAGENT.md**.
`tools/deploy-v3-staging.sh` für diesen Auftrag nicht mehr ausführen.

```bash
cd '/Users/activi/Downloads/Lina-OAI-Claude-main-2' && bash -n tools/create-v3-agent.sh && bash tools/create-v3-agent.sh
```

Das neue Skript erstellt einen richtigen Clone neben dem Downloads-Ordner,
übernimmt die benannten Dateien einschließlich der Codex-Testkorrekturen, prüft sie,
pusht zum Fork und erstellt einen eigenen Agenten mit Aufrufname `lina-v3-test`.
Der neue Agent verwendet V3 und synthetische Daten im FakeStore. Seine Antworten werden
nicht in Airtable gespeichert. Der Standard-Deployment-Name dieses eigenen Agenten ist
`production`; die bisherige Lina wird nicht aktualisiert.

Die oben dokumentierten 115 Tests beziehen sich auf den vorherigen Prompt-Patch.
Die danach ergänzte Preview-Auswahl in src/agent.py und tests/test_preview.py muss
durch den neuen Startbefehl erneut getestet werden. Diese Chat-Sitzung hat keine
Befehle, Commits, Pushes oder Cloud-Änderungen selbst ausgeführt.

## Hörvergleich

Wenn das bisherige Staging noch verfügbar ist, vor dem Deployment eine kurze
Referenzaufnahme mit denselben synthetischen Daten und derselben Stimme machen.
Anschließend dieselben Situationen mit der neuen Version testen. Ohne Referenz
ist dies ein Einzeltest, kein belegter Vorher-Nachher-Vergleich.

| Situation | Erwartung | Fehlerkriterium |
| --- | --- | --- |
| Begrüßung, Identität und Zeit bestätigt | Kurzer Einstieg, dann zum Anliegen | Zusätzlicher Pflicht-Smalltalk oder doppelte Vorstellung |
| „Osnove.“ / „Nimalo.“ auf Sprachfragen | Passende nächste Frage; gelegentliche kurze Bestätigung erlaubt | Lob, Dank oder Wiederholung nach praktisch jeder Antwort |
| „Deset godina na bageru, zadnje četiri u Austriji.“ | Fehlende berufliche Details erfragen | Meister-Kompliment oder pauschale Bewertung Österreichs |
| „Evo baš pijem kafu, taman si nazvala. Kako si ti?“ | Kurze warme Reaktion, dann zurück zum Anliegen | Ignorieren oder erfundene eigene Alltagserlebnisse |
| „Od…“ mit kurzer Denkpause, dann Jahreszahl | Raum zum Fertigsprechen | Nächste Frage mitten im Gedanken |
| „Čekaj, od dvije hiljade sedamnaeste, ne šesnaeste.“ | Zuhören, neue Jahreszahl übernehmen und delegieren | Alte Zahl weiterverwenden oder ganzen Lebenslauf zurücklesen |
| „Kolika je plata?“ | Kurze belegte Antwort aus Wissen | Ungefragter Angebotsmonolog |
| „Moram sad ići.“ | Datenerfassung beenden, kurzer Abschied | Neues Datenfeld oder langer sentimentaler Abschied |
| „Jesi li ti AI?“ | Direkte ehrliche Antwort | Menschliche Identität behaupten |
| Verzögerte Backend-Antwort | Keine wiederholten Wartefloskeln, kein erfundener Erfolg | Speicherung oder Rückruf vor Backend-Ergebnis bestätigt |

Unterbrechungen und Denkpausen zusätzlich manuell mit Mikrofon testen:
Ein simuliertes Gespräch allein belegt keine zuverlässige Überlappungsbehandlung.

Zu protokollieren: Git-SHA, LiveKit-Version, aktive Prompt-Version, Stimme,
Session-ID, Testfall, gehörte Reaktion, auffällige Pausen und Ergebnis.
Keine Zugangsdaten oder echten Bewerberdaten in dieses Dokument aufnehmen.

## Quellen

- OpenAI: https://developers.openai.com/api/docs/guides/live-prompting
- LiveKit: https://docs.livekit.io/testing/simulations/
- LiveKit: https://docs.livekit.io/deploy/agents/deployments/

OpenAI trennt Backchannel-, Interruption- und Delegation-Regeln. Diese Steuerstruktur
bleibt erhalten. Der neue Wortlaut ist eine projektspezifische Gestaltung, deren
Wirkung erst mit Audio zu prüfen ist.

Wichtig: eigener V3-Testagent mit fiktiven Daten; nur geprüfte Änderungen committen;
Ergebnisse anhand tatsächlich ausgeführter Checks und gehörtem Audio berichten.
