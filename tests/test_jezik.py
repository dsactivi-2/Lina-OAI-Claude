"""Jezička korektura (src/lina/jezik.py): hrvatske riječi, ekavica, njemački/engleski uzvici."""

from lina import jezik


def test_hrvatske_rijeci_i_mjeseci():
    n = jezik.nalazi(
        "Plata je četiri tisuće eura, a kući ideš svaki peti tjedan, u rujnu."
    )
    assert [x.zamjena for x in n] == ["hiljada", "sedmica", "septembar"]
    assert n[0].rijec == "tisuće"


def test_bosanski_tekst_bez_nalaza():
    t = "Plata je četiri hiljade sedamsto pedeset eura bruto, sedmica kući, od septembra. Tako, tačno."
    assert jezik.nalazi(t) == []
    # „ko“ u sredini riječi i „neko“ nisu hrvatski
    assert jezik.nalazi("Neko ko radi, kao i tko god… ne, ko god.")[0].zamjena == "ko"
    assert jezik.nalazi("Mislio sam nekoga drugog, u redu.") == []


def test_uzvici_i_ekavica():
    assert [x.zamjena for x in jezik.nalazi("Okej, super, danke.")] == [
        "u redu",
        "odlično",
        "hvala",
    ]
    assert jezik.nalazi("Lepo, vreme je.")[0].zamjena.startswith("ijekavica")
    assert jezik.nalazi("Vrijeme je lijepo, mjesto je ovdje.") == []


def test_napomena_kratka_i_bosanska():
    n = jezik.nalazi("tisuću, tjedan, okej")
    t = jezik.napomena(n)
    assert "hiljada" in t and "sedmica" in t and "u redu" in t
    assert len(t) < 600  # weit unter 500 Tokens (append_instructions-Grenze)
