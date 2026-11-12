"""Simulationen: deterministischer Kandidat aus `userdata` der Szenarien und Endzustands-Prüfung.

`userdata` eines Szenarios (Schlüssel exakt wie in scenarios.yaml):

    sada: "2026-11-05T10:00"              # optional, fixiert die Uhr
    kandidat: {ime: Amir, drzavljanstvo: BiH, vozacka: "B", ...}   # leer/fehlend = fehlt
    radno_iskustvo: [{pozicija, poslodavac, od, do}]
    obrazovanje: [{skola, od, do}]
    dopune: [{status_pregleda: Novo, status_boravka: BiH}]
    expected_state:
      sacuvano: [status_boravka, ...]     # muss erfasst sein
      nije_sacuvano: [drzavljanstvo, ...] # darf NICHT erfasst sein (war schon da)
      broj_novih_radnih_mjesta: 3
      broj_novih_skola: 1
      povratni_poziv: true
      ishod: zavrseno
"""

from __future__ import annotations

from typing import Any

from .airtable import Paket
from .config import OB, RI, D, P
from .stanje import Stanje

_P = {
    "ime": P.IME,
    "sifra": P.SIFRA,
    "telefon": P.TELEFON,
    "drzavljanstvo": P.DRZAVLJANSTVO,
    "vozacka": P.VOZACKA,
    "status_boravka": P.STATUS_BORAVKA,
    "radna_dozvola": P.RADNA_DOZVOLA,
    "datum_rodjenja": P.DATUM_RODJENJA_TXT,
    "mjesto_rodjenja": P.MJESTO_RODJENJA,
    "adresa": P.ADRESA,
    "bracno_stanje": P.BRACNO_STANJE,
    "email": P.EMAIL,
    "vjestine": P.VJESTINE,
    "njemacki": P.NJEMACKI_TXT,
    "radno_mjesto": P.RADNO_MJESTO,
    "kompanija": P.KOMPANIJA,
    "skola": P.SKOLA_TXT,
}
_D = {
    "status_pregleda": D.STATUS_PREGLEDA,
    "status_boravka": D.STATUS_BORAVKA,
    "radna_dozvola": D.RADNA_DOZVOLA,
    "vozacka": D.VOZACKA,
    "drzavljanstvo": D.DRZAVLJANSTVO,
    "datum_rodjenja": D.DATUM_RODJENJA,
    "email": D.EMAIL,
    "adresa": D.ADRESA,
}
_RI = {
    "pozicija": RI.POZICIJA,
    "poslodavac": RI.POSLODAVAC,
    "od": RI.OD,
    "do": RI.DO,
    "aktuelno": RI.AKTUELNO,
}
_OB = {"skola": OB.SKOLA, "adresa_skole": OB.ADRESA_SKOLE, "od": OB.OD, "do": OB.DO}


def _map(d: dict[str, Any], m: dict[str, str]) -> dict[str, Any]:
    return {m[k]: v for k, v in (d or {}).items() if k in m}


def paket_iz_userdata(ud: dict[str, Any]) -> Paket:
    return Paket(
        kandidat=_map(ud.get("kandidat", {}), _P),
        dopune=[_map(x, _D) for x in ud.get("dopune", [])],
        radno_iskustvo=[_map(x, _RI) for x in ud.get("radno_iskustvo", [])],
        obrazovanje=[_map(x, _OB) for x in ud.get("obrazovanje", [])],
    )


def razlike(stanje: Stanje, expected: dict[str, Any]) -> list[str]:
    """Liefert Abweichungen vom erwarteten Endzustand (leer = alles korrekt)."""
    f: list[str] = []
    for k in expected.get("sacuvano", []):
        if k not in stanje.podaci:
            f.append(f"'{k}' wurde nicht erfasst")
    for k in expected.get("nije_sacuvano", []):
        if k in stanje.podaci:
            f.append(f"'{k}' wurde erfasst, obwohl es schon vorhanden war")
    if (
        "broj_novih_radnih_mjesta" in expected
        and len(stanje.nove_stanice) != expected["broj_novih_radnih_mjesta"]
    ):
        f.append(
            f"{len(stanje.nove_stanice)} statt {expected['broj_novih_radnih_mjesta']} Berufsstationen"
        )
    if (
        "broj_novih_skola" in expected
        and len(stanje.nove_skole) != expected["broj_novih_skola"]
    ):
        f.append(
            f"{len(stanje.nove_skole)} statt {expected['broj_novih_skola']} Schulen"
        )
    if expected.get("povratni_poziv") and stanje.povratni_poziv is None:
        f.append("kein Rückruftermin gespeichert")
    if "ishod" in expected and stanje.ishod != expected["ishod"]:
        f.append(f"Ergebnis '{stanje.ishod}' statt '{expected['ishod']}'")
    if expected.get("bez_napomena_provjere") and stanje.napomene_provjere:
        f.append("unerwartete Plausibilitäts-Rückfrage")
    if expected.get("napomena_provjere") and not any(
        k.startswith(expected["napomena_provjere"]) for k in stanje.napomene_provjere
    ):
        f.append(f"keine Erklärung zu {expected['napomena_provjere']} gespeichert")
    return f
