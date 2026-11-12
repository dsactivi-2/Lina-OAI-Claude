"""Einstieg: Lina – Outbound-Recruiting-Agent (Anruf 1: Datenerfassung).

Ablauf: Kandidat bestimmen → Pre-Call-Fetch aus Airtable (vor dem Sessionstart) →
Instruktionen mit Kontext bauen → GPT-Live-Session → am Ende einmalig zurückschreiben.

Kandidat: Dispatch-Metadaten `{"record_id": "rec..."}`. Nur zum lokalen Testen ohne Metadaten
gilt `LINA_TEST_RECORD_ID` (Test-Kandidat K-0196).
LINA_PREVIEW=1: Browser-Hörtest mit fiktiven Daten und FakeStore, ohne Airtable oder AMD.
"""

import asyncio
import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from livekit.agents import (
    AMD,
    AgentServer,
    AgentSession,
    CloseEvent,
    ConversationItemAddedEvent,
    JobContext,
    SimulationContext,
    cli,
    inference,
    room_io,
)
from livekit.agents.beta import EndCallTool
from livekit.plugins import ai_coustics

from lina import jezik, prompts, verzija
from lina.agent_lina import PozdravAgent
from lina.airtable import AirtableStore, FakeStore, Store, sacuvaj
from lina.dialog import DialogProtokoll
from lina.kontekst import izracunaj
from lina.simulacija import paket_iz_userdata, razlike
from lina.stanje import Stanje
from lina.telemetrie import setup_langfuse, umgebung
from lina.zeit import TZ, opis

logger = logging.getLogger("agent")

load_dotenv(".env.local")

AGENT_NAME = os.getenv("LINA_AGENT_NAME", "livekit-oai-gig-casting")


def _record_id(ctx: JobContext) -> str | None:
    meta = (ctx.job.metadata or "").strip()
    if meta:
        try:
            rid = json.loads(meta).get("record_id")
        except (ValueError, AttributeError):
            rid = None
        if rid:
            return str(rid)
        logger.error("Dispatch-Metadaten ohne gültiges record_id")
        return None
    return os.getenv("LINA_TEST_RECORD_ID") or None


def _initial_call_data(ctx: JobContext):
    """Simulation, isolierter Browser-Hörtest oder regulärer Airtable-Pfad."""
    if sim := ctx.simulation_context():
        ud = sim.userdata()
        fixed = None
        if ud.get("sada"):
            fixed = datetime.fromisoformat(ud["sada"]).replace(tzinfo=TZ)
        return FakeStore(paket_iz_userdata(ud)), "recSIMULACIJA00001", fixed
    if os.getenv("LINA_PREVIEW") == "1":
        # Pro Gespräch frischer Speicher. Dispatch-Metadaten werden hier nicht gelesen.
        paket = paket_iz_userdata(
            {
                "kandidat": {
                    "ime": "Emir",
                    "datum_rodjenja": "15.03.1992",
                    "drzavljanstvo": "BiH",
                    "vozacka": "B",
                    "mjesto_rodjenja": "Bihać",
                    "adresa": "Testna 1, 77000 Bihać",
                    "email": "emir@example.com",
                }
            }
        )
        return FakeStore(paket), "recPREVIEW00000001", None
    record_id = _record_id(ctx)
    if not record_id:
        return None
    return AirtableStore(), record_id, None


async def on_simulation_end(sim: SimulationContext) -> None:
    expected = sim.userdata().get("expected_state")
    if not expected:
        return
    session = sim.job_context.primary_session
    if session is None:
        sim.fail(reason="Session wurde nicht gestartet")
        return
    stanje: Stanje = session.userdata
    # GPT-Live delegiert asynchron: Die Simulation endet oft mit Linas Abschiedssatz, bevor das
    # Backend die letzten Angaben gespeichert hat. Kurz warten, bis der Abschluss gemeldet ist.
    for _ in range(20):
        if stanje.ishod is not None:
            break
        await asyncio.sleep(0.5)
    await asyncio.sleep(1.0)
    if fehler := razlike(stanje, expected):
        sim.fail(reason="; ".join(fehler))


def _tekst_iz_historije(history) -> str:
    items = getattr(history, "items", None)
    if items is None and isinstance(history, list):
        items = history
    linije = []
    for item in items or []:
        role = getattr(item, "role", None)
        if role not in ("user", "assistant"):
            continue
        tekst = getattr(item, "text_content", None)
        if not tekst:
            sadrzaj = getattr(item, "content", "")
            if isinstance(sadrzaj, list):
                tekst = " ".join(str(c) for c in sadrzaj if isinstance(c, str))
            else:
                tekst = str(sadrzaj or "")
        tekst = (tekst or "").strip()
        if not tekst:
            continue
        linije.append(("Kandidat: " if role == "user" else "Lina: ") + tekst)
    return "\n".join(linije)


def _responses_options(kontekst, vrijeme: str) -> dict:
    """Backend-Modell hinter GPT-Live (responses_options, Doku /agents/models/realtime/gpt-live).

    Im Testanruf vom 11.11.2026 dauerten Backend-Antworten mit Standard-Reasoning und 8–18k
    Input-Tokens 4–6 s, hörbar als Pausen. LiveKit reicht reasoning, text und max_output_tokens
    durch (gpt_live.py, _build_delegation). Leere Umgebungsvariable = Option weglassen.
    """
    opts: dict = {
        "model": os.getenv("LINA_BACKEND_MODEL", "gpt-5.6-luna"),
        "instructions": prompts.backend(kontekst, vrijeme),
    }
    if not verzija.je_v3():  # v2 bleibt wie in Produktion (OpenAI-Standard)
        return opts
    if effort := os.getenv("LINA_BACKEND_REASONING", "low").strip():
        opts["reasoning"] = {"effort": effort}
    if verbosity := os.getenv("LINA_BACKEND_VERBOSITY", "low").strip():
        opts["text"] = {"verbosity": verbosity}
    # Reasoning-Tokens zählen mit; ein zu kleines Limit bricht Tool-Aufrufe ab. Darum nur opt-in.
    if max_tokens := os.getenv("LINA_BACKEND_MAX_TOKENS", "").strip():
        try:
            opts["max_output_tokens"] = max(16, int(max_tokens))
        except ValueError:
            logger.warning("LINA_BACKEND_MAX_TOKENS ist keine Zahl, wird ignoriert")
    return opts


server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME, on_simulation_end=on_simulation_end)
async def my_agent(ctx: JobContext):
    store: Store
    initial = _initial_call_data(ctx)
    if initial is None:
        logger.error("Kein Kandidat (record_id) – Session wird nicht gestartet")
        ctx.shutdown(reason="no record_id")
        return
    store, record_id, fiksno = initial

    ctx.log_context_fields = {"room": ctx.room.name, "record_id": record_id}

    # Langfuse (optional): vor dem Sessionstart, damit alle Spans ankommen.
    langfuse = setup_langfuse(
        metadata={
            "langfuse.session.id": ctx.room.name,
            "lina.record_id": record_id,
            "lina.prompt_verzija": prompts.aktivna_verzija(),
        }
    )
    trace_provider, dialog_prozessor = (
        langfuse if langfuse is not None else (None, None)
    )
    if trace_provider is not None:

        async def flush_trace() -> None:
            trace_provider.force_flush()

        ctx.add_shutdown_callback(flush_trace)

    # Pre-Call-Fetch: VOR dem Sessionstart. Ohne Kontext wird nicht telefoniert.
    try:
        paket = await store.ucitaj(record_id)
    except Exception:
        logger.exception("Pre-Call-Fetch fehlgeschlagen")
        ctx.shutdown(reason="pre-call fetch failed")
        return
    kontekst = izracunaj(
        record_id, paket.kandidat, paket.dopune, paket.radno_iskustvo, paket.obrazovanje
    )
    stanje = Stanje(kontekst, fiksno_vrijeme=fiksno)
    stanje.polja = dict(paket.kandidat)
    vrijeme = opis(stanje.sada())
    logger.info("Kontekst: %d Angaben fehlen", len(kontekst.nedostaje))

    session = AgentSession(
        llm=inference.DuplexModel(
            model="openai/gpt-live-1",
            # GPT-Live hat keine bosnische Stimme (Stand 11.11.2026); marin ist der Standard.
            # Vor einem Wechsel die Kombination Stimme + Jezik-Block anhören (OpenAI: „Audition
            # the actual combination of voice and instructions“).
            voice=os.getenv("LINA_VOICE", "marin"),
            extra_kwargs={"responses_options": _responses_options(kontekst, vrijeme)},
        ),
        # GPT-Live steuert Turns selbst; eine VAD ist nötig, damit Barge-in die Wiedergabe stoppt.
        vad=inference.VAD(model="silero"),
        userdata=stanje,
    )

    # Gesprächsverlauf beider Seiten für Langfuse (Kandidat + Lina), siehe lina/dialog.py
    protokoll = DialogProtokoll()
    if dialog_prozessor is not None:
        dialog_prozessor.binde(
            protokoll,
            {
                "record_id": record_id,
                "umgebung": umgebung(),
                "anzahl_fehlender_angaben": len(kontekst.nedostaje),
            },
        )

    @session.on("conversation_item_added")
    def _dialog_item(ev: ConversationItemAddedEvent) -> None:
        protokoll.dodaj(ev.item)

    # Jezička korektura: GPT-Live kroz LiveKit nema keyword biasing. Hrvatska riječ ili
    # njemački/engleski uzvik u Lininom tekstu → kratka napomena u instrukcije (≤ 500 Tokens),
    # najviše jezik.MAX_ISPRAVKI puta po pozivu. Geloggt werden nur die Ersatzwörter.
    ispravke_jezika: list[str] = []  # schon korrigierte Ersatzwörter
    napomene_jezika = [0]  # gesendete Hinweise, höchstens jezik.MAX_ISPRAVKI

    @session.on("conversation_item_added")
    def _jezik_item(ev: ConversationItemAddedEvent) -> None:
        item = ev.item
        if getattr(item, "role", None) != "assistant" or not verzija.je_v3():
            return
        if napomene_jezika[0] >= jezik.MAX_ISPRAVKI:
            return
        novi = [
            n
            for n in jezik.nalazi(getattr(item, "text_content", "") or "")
            if n.zamjena not in ispravke_jezika
        ]
        if not novi:
            return
        try:
            session.current_agent.duplex_session.append_instructions(
                jezik.napomena(novi)
            )
        except Exception:
            logger.debug("jezička napomena nije poslana", exc_info=True)
            return
        ispravke_jezika.extend(n.zamjena for n in novi)
        napomene_jezika[0] += 1
        logger.info("jezička korektura: %s", ", ".join(n.zamjena for n in novi))

    @session.on("close")
    def _dialog_kraj(ev: CloseEvent) -> None:
        # läuft vor dem Ende des agent_session-Spans, der den ganzen Dialog bekommt
        protokoll.abschluss = {
            "ishod": stanje.ishod or stanje.ishod_bez_kraja(),
            "sazetak": stanje.sazetak,
            "razlog_kraja": str(getattr(ev, "reason", "") or ""),
        }
        protokoll.beendet = True

    async def spremi_na_kraju() -> None:
        if stanje.sacuvano:
            return
        stanje.transkript = _tekst_iz_historije(session.history)
        if not stanje.sazetak and stanje.transkript:
            stanje.sazetak = stanje.transkript.replace("\n", " ")[:240]
        stanje.ishod = stanje.ishod or stanje.ishod_bez_kraja()
        try:
            await sacuvaj(store, stanje)
        except Exception:
            logger.exception("Speichern beim Sitzungsende fehlgeschlagen")

    ctx.add_shutdown_callback(spremi_na_kraju)

    extra = [EndCallTool(end_instructions=None, ignore_on_enter=True)]
    agent = PozdravAgent(
        stanje=stanje,
        store=store,
        kontekst=kontekst,
        vrijeme=vrijeme,
        tools=extra,
    )

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                ),
            ),
        ),
    )
    await ctx.connect()
    # Nicht sofort reden: warten, bis der Angerufene sich meldet (Halo / Da?).
    if ctx.simulation_context() or os.getenv("LINA_PREVIEW") == "1":
        return
    try:
        # Default-STT von AMD (cartesia/ink-whisper) gibt es in der EU-Region nicht;
        # ohne Transkript endet AMD immer mit UNCERTAIN. Nova-3 hat EU-Endpunkt und Bosnisch.
        async with AMD(
            session,
            stt=os.getenv("LINA_AMD_STT", "deepgram/nova-3:bs"),
            ivr_detection=False,
        ) as detector:
            amd = await detector.execute()
        logger.info("AMD category=%s", amd.category)
        if amd.category == "machine-vm":
            handle = session.generate_reply(
                instructions=(
                    "Govori bosanski, kratko, bez tagova. Reci da je Lina iz Job-Stepa "
                    "zvala i da ćemo se javiti. Onda šuti."
                )
            )
            await handle.wait_for_playout()
            stanje.ishod = stanje.ishod or "prekinuto"
            ctx.shutdown(reason="voicemail")
            return
        if amd.category == "machine-unavailable":
            stanje.ishod = stanje.ishod or "prekinuto"
            ctx.shutdown(reason="mailbox unavailable")
            return
    except Exception:
        logger.exception("AMD fehlgeschlagen – weiter wie Mensch")


if __name__ == "__main__":
    cli.run_app(server)
