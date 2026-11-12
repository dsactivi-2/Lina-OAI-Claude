"""v2 bleibt zeichengleich mit Produktion (Git-Tag lina-v2.0-prod, Commit af8cfbb).

tests/data/v2_prompts_prod.txt wurde am 11.11.2026 aus dem Tag erzeugt, mit genau diesem
Kandidaten. Schlägt der Test fehl, hat eine Änderung v2 verändert: hinter verzija.je_v3() legen.
"""

from pathlib import Path

import pytest

import agent  # lädt .env.local einmal, bevor die Fixtures LINA_PROMPT entfernen
from lina import prompts
from lina.config import OB, RI, P
from lina.kontekst import izracunaj

GOLDEN = Path(__file__).parent / "data" / "v2_prompts_prod.txt"
VRIJEME = "srijeda, 11. novembar 2026, 10:00"


@pytest.fixture
def v2(monkeypatch):
    monkeypatch.delenv("LINA_PROMPT", raising=False)
    monkeypatch.delenv("LIVEKIT_AGENT_DEPLOYMENT", raising=False)


def _render() -> str:
    k = izracunaj(
        "recGolden",
        {P.IME: "Amir", P.TELEFON: "+387 61 000 000", P.DRZAVLJANSTVO: "BiH"},
        [],
        [
            {
                RI.POZICIJA: "Zidar",
                RI.POSLODAVAC: "Firma A",
                RI.OD: "2010",
                RI.DO: "2015",
            }
        ],
        [
            {
                OB.SKOLA: "Gimnazija",
                OB.ADRESA_SKOLE: "Bihać",
                OB.OD: "2005",
                OB.DO: "2009",
            }
        ],
    )
    teile = [
        f"===== {n}\n{f(k, VRIJEME)}"
        for n, f in (
            ("voice", prompts.voice),
            ("pozdrav", prompts.voice_pozdrav),
            ("kraj", prompts.voice_kraj),
            ("backend", prompts.backend),
        )
    ]
    return "\n".join(teile)


def test_v2_prompts_wie_produktion(v2):
    assert _render() == GOLDEN.read_text()


def test_v2_backend_ohne_reasoning(v2):
    k = izracunaj("recGolden", {}, [], [], [])
    opts = agent._responses_options(k, VRIJEME)
    assert set(opts) == {"model", "instructions"}


def test_staging_v3_backend_low(monkeypatch):
    monkeypatch.delenv("LINA_PROMPT", raising=False)
    monkeypatch.setenv("LIVEKIT_AGENT_DEPLOYMENT", "staging")
    k = izracunaj("recGolden", {}, [], [], [])
    opts = agent._responses_options(k, VRIJEME)
    assert opts["reasoning"] == {"effort": "low"} and opts["text"] == {
        "verbosity": "low"
    }
