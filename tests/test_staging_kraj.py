"""Staging wählt v3 ohne Secret; Abschluss: Abschied und Auflegen auch ohne zavrsi_razgovor."""

import asyncio

import pytest

from lina import agent_lina, prompts, verzija


@pytest.fixture
def ohne_schalter(monkeypatch):
    monkeypatch.delenv("LINA_PROMPT", raising=False)
    monkeypatch.delenv("LIVEKIT_AGENT_DEPLOYMENT", raising=False)
    return monkeypatch


def test_production_bleibt_v2(ohne_schalter):
    assert verzija.aktivna_verzija() == verzija.V2
    ohne_schalter.setenv(
        "LIVEKIT_AGENT_DEPLOYMENT", ""
    )  # so setzt es LiveKit auf production
    assert verzija.aktivna_verzija() == verzija.V2


def test_staging_ist_v3(ohne_schalter):
    ohne_schalter.setenv("LIVEKIT_AGENT_DEPLOYMENT", "staging")
    assert verzija.aktivna_verzija() == verzija.V3


def test_lina_prompt_hat_vorrang(ohne_schalter):
    ohne_schalter.setenv("LIVEKIT_AGENT_DEPLOYMENT", "staging")
    ohne_schalter.setenv("LINA_PROMPT", "v2")
    assert verzija.aktivna_verzija() == verzija.V2
    ohne_schalter.delenv("LIVEKIT_AGENT_DEPLOYMENT")
    ohne_schalter.setenv("LINA_PROMPT", "v3")
    assert verzija.aktivna_verzija() == verzija.V3


def test_kraj_prelaz_mit_abschied():
    t = prompts.KRAJ_PRELAZ
    assert "ćao" in t and "zavrsi_razgovor" in t and "Ne čekaš kandidata" in t
    assert len(t) < 1200  # append_instructions: ≤ 500 Tokens


def test_v2_antwort_von_zavrsi_unveraendert(ohne_schalter):
    assert agent_lina._poruka_sacuvano() == (
        "Sačuvano. Zahvali se u jednoj rečenici i pozovi end_call. Poziv se prekida sam."
    )
    ohne_schalter.setenv("LINA_PROMPT", "v3")
    assert "ćao" in agent_lina._poruka_sacuvano()


class _Sess:
    def __init__(self):
        self.zu = 0

    def shutdown(self, drain=True):
        self.zu += 1


class _Ctx:
    def __init__(self):
        self.session = _Sess()


def test_rezerva_legt_auf_wenn_kein_abschluss():
    async def lauf(ishod):
        ctx = _Ctx()
        agent_lina.zakazi_prekid(ctx, sekunde=0.01, samo_ako=lambda: ishod is None)
        await asyncio.sleep(0.05)
        return ctx.session.zu

    assert asyncio.run(lauf(None)) == 1
    assert (
        asyncio.run(lauf("zavrseno")) == 0
    )  # zavrsi_razgovor lief, eigener Timer legt auf
