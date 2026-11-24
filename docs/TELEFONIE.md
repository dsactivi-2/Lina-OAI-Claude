---
title: "Telefonie: LiveKit → FusionPBX → TG400 → SIM"
---

# Telefonie: LiveKit → FusionPBX → TG400 → SIM

Stand 08.11.2026. Keine Passwörter in dieser Datei.

## Weg eines Anrufs
```text
LiveKit Cloud (Lina, Agent livekit-oai-gig-casting)
  │  Outbound-Trunk ST_pN6ccnMf26NY „FusionPBX Outbound (Lina)“
  ▼
FusionPBX fusion.activi.io:5060 (Profil internal, UDP, Login als Nebenstelle 300)
  │  Ausgehende Route „TG400_Outbound“ (Reihenfolge 100)
  ▼
Gateway „TG400“ (ID 5e889af0-e082-488f-b96f-f247b88725cc, Profil internal, ohne Registrierung)
  ▼
Yeastar TG400 (Bihać, LAN 192.168.31.150, öffentlich 213.91.103.192) → SIM 1 m:tel → Handy
```
Der Angerufene sieht die Nummer der SIM 1 (m:tel).

## LiveKit-Trunk (Dashboard → Telephony → Trunks)
- address `fusion.activi.io:5060`, transport UDP, numbers `["300"]`, auth_username `300`
- from_host `fusion.activi.io` (FusionPBX ordnet den Anruf so der Domain zu)
- Passwort = Passwort von Nebenstelle 300 (nur im Dashboard, nirgends sonst)

## FusionPBX
- Nebenstelle **300**: wird vom TG400 (Anmeldung) und von LiveKit (Anruf mit Login) genutzt.
- Route **call_direction-outbound** (22): setzt nur `call_direction=outbound`, nicht ändern.
- Route **TG400_Outbound** (100): Muster `^(?:\+|00)?([1-9]\d{7,14})$`,
  bridge in der Tabellenansicht `sofia/gateway/TG400/00$1` (FusionPBX setzt intern die ID ein).
  Änderungen nur in der Tabellenansicht, der XML-Editor wird aus der Tabelle neu erzeugt.
- Nach Änderungen: SIP Status → Cache leeren.
- Zurück auf sipgate: bridge `sofia/gateway/sipgate-Trunk/$1`.

## TG400
- Trunk „fusion“: Register-Trunk zu fusion.activi.io, Benutzer 300, UDP 5060.
- Codecs nur a-law, u-law, GSM (kein G722).
- Firewall an, keine IP gesperrt. Nichts öffnen, was nicht nötig ist.

## Testanruf
Lina wählt **nicht** selbst. Allowlist + CLI. Staging:

```bash
lk sip participant create --project lina-oai --trunk ST_pN6ccnMf26NY \
  --to +387… --agent-name livekit-oai-gig-casting --agent-deployment staging \
  --agent-metadata '{"record_id":"rec…"}' --timeout 50s --wait -y
```

Ohne `--agent-deployment staging` trifft **Production**.

## AMD
Nach `ctx.connect()`, nicht in Simulationen (`src/agent.py`). Mensch vs. Mailbox, `ivr_detection=False`.

- STT: `LINA_AMD_STT`, Standard `deepgram/nova-3:bs`. Cartesia Ink-Whisper (LiveKit-Default) gibt es in eu-central nicht; ohne Transkript endet AMD immer `UNCERTAIN`.
- `machine-vm`: kurze Bosnisch-Nachricht, `ishod=prekinuto`, Shutdown `voicemail`.
- `machine-unavailable`: `ishod=prekinuto`, keine Ansage.
- AMD-Fehler: Log, Gespräch läuft weiter wie Mensch.

Dispatch-Metadaten und STT-Fallstricke: [`docs/BETRIEB.md`](BETRIEB.md).

## Fehlerbilder
- 480 und `last_arg` mit Gateway `5c24281b…`: Anruf ging an sipgate (Route falsch).
- 484 Address Incomplete: Nummer passt nicht, `last_arg` im FusionPBX-Anrufprotokoll prüfen.
- Kein Eintrag in TG400 → Call Logs: Anruf erreicht den TG400 nicht.
- AMD immer unsicher: STT prüfen (`LINA_AMD_STT`), nicht Cartesia in der EU.

## Offen
- Feste öffentliche IP des TG400-Standorts klären (Gateway nutzt 213.91.103.192).
- Eigene Nebenstelle für LiveKit statt 300 (Trennung von TG400).
- Inbound (Kandidat ruft uns) nicht eingerichtet.
