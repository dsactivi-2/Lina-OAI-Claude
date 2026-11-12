# Eigener Lina-V3-Testagent

## Aktuelles Ziel

Dieser Ablauf ersetzt den bisherigen Plan, den vorhandenen Agenten auf staging zu aktualisieren.
Ziel ist ein eigener LiveKit-Agent im vorhandenen Projekt lina-oai, Region eu-central.
Technischer Aufrufname: `lina-v3-test`.
Das Standard-Deployment dieses NEUEN Agenten heißt `production`.
Das ist keine Aktualisierung des bisherigen Produktionsagenten.

Repository: https://github.com/dsactivi-2/Lina-OAI-Claude
Ausgangskopie: `/Users/activi/Downloads/Lina-OAI-Claude-main-2`
Neuer Git-Clone: daneben als `Lina-OAI-Claude-v3-test`.

## Start

Im normalen Terminal, nicht im Codex-Eingabefeld:

```bash
cd '/Users/activi/Downloads/Lina-OAI-Claude-main-2' && bash -n tools/create-v3-agent.sh && bash tools/create-v3-agent.sh
```

Voraussetzungen: git, uv, LiveKit CLI, vorhandene Anmeldung für GitHub-Push und LiveKit.
Das Skript nutzt bestehende Anmeldungen. Es führt keine fremden Anmeldungen aus.

## Ablauf

1. Fork klonen und eigenen Branch anlegen.
2. Explizit benannte lokale Änderungen inklusive der Codex-Testkorrekturen übernehmen.
3. Im NEUEN Clone die alte LiveKit-Agent-ID durch eine reine Projektkonfiguration ersetzen.
4. Abhängigkeiten installieren, geänderte Python-Dateien formatieren und linten, gesamte
   Python-Testsuite ausführen. Der alte SIM117 in r2.py gehört nicht zu diesem Patch;
   vollständiger projektweiter Lint wird damit nicht als bestanden behauptet.
5. Commit und Push ausschließlich zum Fork dsactivi-2.
6. Neuen Agenten mit `lk agent create` anlegen. Die alte ID CA_xPubxhi5ER7v ist gesperrt.
7. Neue LiveKit-ID im neuen Clone committen und pushen; Status ausgeben.

Bei Fehlern stoppt das Skript. Es kann Schritte davor bereits erledigt haben.
Ein unterbrochener create-Versuch ohne gespeicherte ID wird nicht blind wiederholt.
Bitte dann die Ausgabe teilen, damit ein möglicherweise bereits angelegter Agent geprüft wird.

## Hörtestmodus

Neue Umgebungsvariablen:
- `LINA_AGENT_NAME`: technischer Aufrufname; Standard bleibt livekit-oai-gig-casting.
- `LINA_PREVIEW=1`: synthetische Browser-Gespräche mit einem neuen FakeStore pro Session.
- Für den neuen Agenten zusätzlich: `LINA_PROMPT=v3`, `LINA_ENV=preview`,
  `LINA_VOICE=marin`.

Fiktiver Bewerber: Emir, geboren am 15.03.1992, aus Bihać.
Arbeitserfahrung und Ausbildung können im Gespräch frei als Testdaten angegeben werden.
Jede neue Session beginnt wieder mit denselben Ausgangsdaten.
Im Preview-Modus werden Kandidaten-IDs aus Dispatch-Metadaten ignoriert.
AirtableStore wird nicht initialisiert; Antworten bleiben im Arbeitsspeicher.
Die Anrufbeantworter-Erkennung wird für den Browser-Hörtest ausgelassen.
Simulationen haben Vorrang und behalten ihre Szenario-Daten.

Für diesen Agenten werden keine Airtable-, Langfuse- oder R2-Zugangsdaten übernommen.
LiveKit stellt die eigenen Projektzugangsdaten im Cloud-Agenten bereit.
Modell-Inferenz läuft weiterhin über die vorhandene GPT-Live-/LiveKit-Anbindung und
verursacht Nutzungskosten. Dieser Modus testet keine produktive Airtable-Integration.

## Anhören

LiveKit Agent Console öffnen und den NEUEN Agenten auswählen.
Aufrufname: lina-v3-test; Deployment: production.
Mikrofon freigeben, Session starten und zuerst „Halo“ sagen.
Es wird kein ausgehender Telefonanruf gestartet.

Prüffälle und erwartete Reaktionen stehen in docs/HOERTEST-V3.md.
Zum Test gehören kurze Antworten, Smalltalk, Denkpausen, Korrekturen, Unterbrechungen
und ein respektiertes Gesprächsende.

## Verifikation und Grenzen

Der vorherige Codex-Bericht dokumentiert 115 bestandene Tests des früheren Prompt-Patches.
Die Änderungen für den eigenen Testagenten kamen DANACH hinzu und sind damit noch nicht
durch diese 115 Tests abgedeckt. Das Startskript führt die Suite einschließlich der neuen
tests/test_preview.py erneut aus. Diese Chat-Sitzung konnte sie nicht selbst ausführen.

Nicht behaupten: neuer Agent bereits angelegt, Push abgeschlossen, neue Tests bestanden
oder Audioqualität verbessert. Dafür muss die tatsächliche Terminalausgabe bzw. der
Hörtest vorliegen.

Das ist ein Browser-Testagent. Produktive Daten, Telefonie und Langfuse werden in einem
separaten Schritt anhand der tatsächlichen Konfiguration angebunden.

Quellen:
- https://docs.livekit.io/reference/developer-tools/livekit-cli/agent/deployment/
- https://docs.livekit.io/agents/server/agent-dispatch/
- https://docs.livekit.io/deploy/agents/secrets/
