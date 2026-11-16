"""Dispatch-Kandidat, EU-AMD-STT und Transkript: ohne Tests landet der Anruf falsch."""

from types import SimpleNamespace

import agent
from lina.kontekst import izracunaj

VRIJEME = "srijeda, 11. novembar 2026, 10:00"


def _ctx(metadata):
    return SimpleNamespace(job=SimpleNamespace(metadata=metadata))


def test_amd_stt_eu_default_nicht_cartesia(monkeypatch):
    monkeypatch.delenv("LINA_AMD_STT", raising=False)
    stt = agent._amd_stt()
    assert stt == "deepgram/nova-3:bs"
    assert not stt.startswith("cartesia/")


def test_amd_stt_umgebung_ueberschreibt(monkeypatch):
    monkeypatch.setenv("LINA_AMD_STT", "deepgram/nova-3:en")
    assert agent._amd_stt() == "deepgram/nova-3:en"


def test_record_id_aus_dispatch_json():
    assert agent._record_id(_ctx('{"record_id": "recABC"}')) == "recABC"
    assert agent._record_id(_ctx('{"record_id": 123}')) == "123"


def test_record_id_ungueltige_metadaten_kein_test_fallback(monkeypatch):
    monkeypatch.setenv("LINA_TEST_RECORD_ID", "recTEST")
    assert agent._record_id(_ctx("{")) is None
    assert agent._record_id(_ctx("[]")) is None
    assert agent._record_id(_ctx('{"foo": 1}')) is None
    assert agent._record_id(_ctx('{"record_id": ""}')) is None


def test_record_id_ohne_metadaten_nimmt_test_id(monkeypatch):
    monkeypatch.setenv("LINA_TEST_RECORD_ID", "recTEST")
    assert agent._record_id(_ctx("")) == "recTEST"
    assert agent._record_id(_ctx("   ")) == "recTEST"
    assert agent._record_id(_ctx(None)) == "recTEST"
    monkeypatch.delenv("LINA_TEST_RECORD_ID", raising=False)
    assert agent._record_id(_ctx("")) is None


def test_transkript_nur_kandidat_und_lina():
    history = SimpleNamespace(
        items=[
            SimpleNamespace(role="system", text_content="ignore"),
            SimpleNamespace(role="user", text_content=" Halo "),
            SimpleNamespace(role="assistant", text_content="Pozdrav"),
            SimpleNamespace(role="user", content=["da", "ne"]),
            SimpleNamespace(role="tool", text_content="skip"),
            SimpleNamespace(role="assistant", text_content="   "),
        ]
    )
    assert agent._tekst_iz_historije(history) == (
        "Kandidat: Halo\nLina: Pozdrav\nKandidat: da ne"
    )


def test_transkript_aus_liste_ohne_items():
    assert (
        agent._tekst_iz_historije([SimpleNamespace(role="user", text_content="da")])
        == "Kandidat: da"
    )


def test_ungueltige_max_tokens_werden_ignoriert(monkeypatch):
    monkeypatch.delenv("LINA_PROMPT", raising=False)
    monkeypatch.setenv("LIVEKIT_AGENT_DEPLOYMENT", "staging")
    monkeypatch.setenv("LINA_BACKEND_MAX_TOKENS", "nicht-zahl")
    opts = agent._responses_options(izracunaj("recX", {}, [], [], []), VRIJEME)
    assert "max_output_tokens" not in opts


def test_max_tokens_mindestens_16(monkeypatch):
    monkeypatch.delenv("LINA_PROMPT", raising=False)
    monkeypatch.setenv("LIVEKIT_AGENT_DEPLOYMENT", "staging")
    monkeypatch.setenv("LINA_BACKEND_MAX_TOKENS", "1")
    opts = agent._responses_options(izracunaj("recX", {}, [], [], []), VRIJEME)
    assert opts["max_output_tokens"] == 16
