"""Branch lina-3-prompt-v2: Jezik-Block, Kraj ohne neue Session, Korrekturen an Airtable-Einträgen,
„Već imamo iz prijave“ im Kontext. Nach dem Testanruf vom 11.11.2026."""

import asyncio
from datetime import datetime

import pytest

from lina import mapa, prompts
from lina.agent_lina import LinaAgent
from lina.airtable import FakeStore, Paket, napravi_zapise
from lina.config import OB, RI, T_DOPUNE, D, P
from lina.kontekst import izracunaj
from lina.stanje import Stanje
from lina.zeit import TZ


@pytest.fixture
def v3(monkeypatch):
    monkeypatch.setenv("LINA_PROMPT", "v3")
    monkeypatch.setattr(mapa, "skola_u_gradu", lambda *a, **k: True)
    monkeypatch.setattr(mapa, "ulica_u_gradu", lambda *a, **k: True)


def run(c):
    return asyncio.run(c)


def _agent_mit_airtable():
    k = izracunaj(
        "recT",
        {P.TELEFON: "+387 61 000 000", P.DRZAVLJANSTVO: "BiH"},
        [],
        [{RI.POZICIJA: "Zidar", RI.POSLODAVAC: "A", RI.OD: "2010", RI.DO: "2015"}],
        [
            {
                OB.SKOLA: "Gimnazija",
                OB.ADRESA_SKOLE: "Bihać",
                OB.OD: "2005",
                OB.DO: "2009",
            }
        ],
    )
    st = Stanje(k, fiksno_vrijeme=datetime(2026, 11, 11, 10, 0, tzinfo=TZ))
    store = FakeStore(Paket({}, [], [], []))
    return LinaAgent(instructions="x", stanje=st, store=store), st


# ---------- Kontext ----------


def test_kontekst_vec_imamo_bez_vrijednosti(v3):
    _, st = _agent_mit_airtable()
    t = st.kontekst.za_instrukcije()
    assert "Već imamo iz prijave" in t
    assert "broj telefona" in t and "državljanstvo" in t
    assert "000 000" not in t  # nie Rohdaten
    assert "znanje njemačkog jezika" not in t.split("Već imamo")[1].split("\n")[0]


# ---------- Korrekturen über alle Einträge ----------


def test_nummerierung_zaehlt_airtable_zuerst(v3):
    a, _st = _agent_mit_airtable()
    r = run(a.dodaj_skolu(None, "Tehnička škola", "Bihać", "2009", "2012"))
    assert "škola broj 2" in r
    r = run(a.dodaj_radno_mjesto(None, "Vozač", "B", "2016", "2020"))
    assert "radno mjesto broj 2" in r


def test_ispravka_airtable_eintrag_wird_notiz(v3):
    a, st = _agent_mit_airtable()
    r = run(a.ispravi_skolu(None, 1, "skola", "Srednja tehnička škola"))
    assert "Zabilježeno" in r and "Ne dodaj" in r
    assert st.kontekst.skole[0].skola == "Gimnazija"  # Airtable bleibt unverändert
    assert st.nove_skole == []
    assert st.napomene_provjere["ISPRAVKA:skola:1"].endswith(
        "skola: Srednja tehnička škola"
    )
    r = run(a.ispravi_radno_mjesto(None, 1, "do", "2016"))
    assert "Zabilježeno" in r
    assert "ISPRAVKA:posao:1" in st.napomene_provjere
    notiz = napravi_zapise(st)[T_DOPUNE][0][D.OPIS]
    assert "Ispravka skola:1" in notiz and "Ispravka posao:1" in notiz


def test_ispravka_lina_eintrag_aendert(v3):
    a, st = _agent_mit_airtable()
    run(a.dodaj_skolu(None, "Tehnička", "Bihać", "2009", "2012"))
    r = run(a.ispravi_skolu(None, 2, "skola", "Tehnička škola Bihać"))
    assert r.startswith("Ispravljeno")
    assert st.nove_skole[0].skola == "Tehnička škola Bihać"
    assert "Nepostojeći redni broj" in run(a.ispravi_skolu(None, 3, "skola", "x"))
    assert "1–2" in run(a.ispravi_skolu(None, 9, "skola", "x"))


# ---------- Prompts ----------


def test_jezik_blok_in_allen_voice_prompts(v3):
    _, st = _agent_mit_airtable()
    k = st.kontekst
    for t in (
        prompts.voice(k, "x"),
        prompts.voice_pozdrav(k, "x"),
        prompts.voice_kraj(k, "x"),
    ):
        assert "# Jezik" in t
        assert "hiljada, ne tisuća" in t
        assert "akcenat iz Bihaća" in t
        assert "/dʒob step/" in t
        assert "siječanj" in t and "Nikad siječanj" in t
        assert "osim ako izričito traži drugi jezik" in t
    assert "{jezik}" not in prompts.voice(k, "x")


def test_tok_ponuda_nur_auf_wunsch_und_delegation_nach_jeder_antwort():
    v = prompts.VOICE
    assert "ne recituješ je" in v
    assert "SAMO ako kandidat pita" in v
    assert "Ne nabrajaš\n  ostatak ponude" in v
    assert "# Ritam razgovora" in v and "Reakcije" in v
    assert (
        "Četiri sedmice si na terenu" not in v
    )  # Kinder nicht mehr an Turnus/Plata gekoppelt
    assert "Odmah poslije SVAKOG odgovora" in prompts._DEL_PODACI
    assert "Već imamo iz prijave" in prompts.BACKEND
    assert (
        "same\n   session" in prompts.BACKEND
        or "same session" in prompts.BACKEND.replace("\n   ", " ")
    )


def test_kraj_prelaz_kurz():
    t = prompts.KRAJ_PRELAZ
    assert (
        "Ne pitaj nova polja" in t
        and "zavrsi_razgovor" in t
        and "<|SpawnThinking|>" in t
    )
    assert len(t) < 900  # append_instructions: ≤ 500 Tokens
