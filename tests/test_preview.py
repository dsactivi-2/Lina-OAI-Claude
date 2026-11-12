"""Hörtestmodus: keine Airtable-Ausführung, eigener Zustand pro Gespräch."""

from types import SimpleNamespace

import pytest

import agent
from lina.airtable import FakeStore
from lina.config import P


def _ctx(metadata="", userdata=None):
    simulation = (
        SimpleNamespace(userdata=lambda: userdata) if userdata is not None else None
    )
    return SimpleNamespace(
        job=SimpleNamespace(metadata=metadata),
        simulation_context=lambda: simulation,
    )


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("LINA_PREVIEW", raising=False)
    monkeypatch.delenv("LINA_TEST_RECORD_ID", raising=False)


def test_preview_ignoriert_echte_dispatch_id_und_airtable(monkeypatch):
    monkeypatch.setenv("LINA_PREVIEW", "1")

    def forbidden():
        pytest.fail("Airtable darf im Hörtestmodus nicht initialisiert werden")

    monkeypatch.setattr(agent, "AirtableStore", forbidden)
    store, record_id, fixed = agent._initial_call_data(
        _ctx('{"record_id": "recECHTERKANDIDAT"}')
    )
    assert isinstance(store, FakeStore)
    assert record_id == "recPREVIEW00000001"
    assert store.paket.kandidat[P.IME] == "Emir"
    assert fixed is None


def test_preview_zustand_ist_pro_gespraech_neu(monkeypatch):
    monkeypatch.setenv("LINA_PREVIEW", "1")
    first, _, _ = agent._initial_call_data(_ctx())
    second, _, _ = agent._initial_call_data(_ctx())
    first.geschrieben["test"] = [{"wert": "nur erstes Gespräch"}]
    first.paket.kandidat[P.IME] = "Geändert"
    assert second.geschrieben == {}
    assert second.paket.kandidat[P.IME] == "Emir"


def test_simulation_behaelt_eigene_daten_auch_im_preview(monkeypatch):
    monkeypatch.setenv("LINA_PREVIEW", "1")
    store, record_id, fixed = agent._initial_call_data(
        _ctx(userdata={"kandidat": {"ime": "Testperson"}, "sada": "2026-11-12T10:00"})
    )
    assert store.paket.kandidat[P.IME] == "Testperson"
    assert record_id == "recSIMULACIJA00001"
    assert fixed.year == 2026
    assert fixed.tzinfo is not None


def test_regulaerer_betrieb_verwendet_airtable(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(agent, "AirtableStore", lambda: sentinel)
    store, record_id, fixed = agent._initial_call_data(
        _ctx('{"record_id": "recREGULAER"}')
    )
    assert store is sentinel
    assert record_id == "recREGULAER"
    assert fixed is None


def test_regulaerer_betrieb_ohne_kandidat_startet_nicht(monkeypatch):
    def forbidden():
        pytest.fail("Ohne Kandidat soll kein AirtableStore entstehen")

    monkeypatch.setattr(agent, "AirtableStore", forbidden)
    assert agent._initial_call_data(_ctx()) is None
