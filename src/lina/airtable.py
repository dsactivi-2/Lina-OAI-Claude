"""Airtable-Zugriff: Pre-Call-Fetch und Zurückschreiben.

Regeln (.claude/rules/airtable.md):
- Lina schreibt Personendaten nie als neue Zeile in `Prijave (test)`. Einmal, am Ende,
  darf sie nur `Status kandidata` setzen. Personendaten → neue `Dopune` (Status „Novo“),
  Stationen → neue Datensätze in `Radno iskustvo` / `Obrazovanje`, Rückruf → `Termini i zadaci`.
- Es werden nur neue Datensätze angelegt. Der einzige Patch ist `Status kandidata`, einmal.
- Keine Personendaten in Logs, nur Record-IDs.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

import aiohttp

from . import r2
from .config import (
    BASE_ID,
    DOPUNE_NOVO,
    OB,
    PZ,
    RI,
    T_DOPUNE,
    T_OBRAZOVANJE,
    T_POZIVI,
    T_PRIJAVE,
    T_RADNO_ISKUSTVO,
    T_TERMINI,
    TZ,
    D,
    P,
)
from .stanje import Stanje
from .status_odluka import dokumenti, licni_popunjeni, odluka, trenutni_status

logger = logging.getLogger("lina.airtable")

Fields = dict[str, Any]

# Werte ohne eigenes Airtable-Feld (noch nicht angelegt) → Notiz in Dopune
_DOPUNE_ZIEL = {
    "status_boravka": D.STATUS_BORAVKA,
    "radna_dozvola": D.RADNA_DOZVOLA,
    "vozacka": D.VOZACKA,
    "drzavljanstvo": D.DRZAVLJANSTVO,
    "datum_rodjenja": D.DATUM_RODJENJA,
    "mjesto_rodjenja": D.MJESTO_RODJENJA,
    "adresa": D.ADRESA,
    "bracno_stanje": D.BRACNO_STANJE,
    "email": D.EMAIL,
    "vjestine": D.VJESTINE,
}
_NOTIZ_LABEL = {
    "njemacki": "Njemački – nivo (samoprocjena)",
    "engleski": "Engleski – nivo (samoprocjena)",
    "djeca": "Djeca",
    "broj_djece": "Broj djece",
    "dob_djece": "Dob djece",
}


@dataclass
class Paket:
    """Alles, was der Pre-Call-Fetch liefert (Felddicts: Field-ID → Wert)."""

    kandidat: Fields
    dopune: list[Fields]
    radno_iskustvo: list[Fields]
    obrazovanje: list[Fields]


class Store(Protocol):
    async def ucitaj(self, record_id: str) -> Paket: ...
    async def kreiraj(self, table: str, records: list[Fields]) -> list[str]: ...
    async def azuriraj(self, table: str, record_id: str, fields: Fields) -> None: ...


def _ima_podatke(stanje: Stanje) -> bool:
    return bool(
        stanje.podaci
        or stanje.nove_stanice
        or stanje.nove_skole
        or stanje.napomene_provjere
        or stanje.povratni_poziv
    )


def _okruzenje() -> str:
    v = os.getenv("LIVEKIT_DEPLOYMENT") or os.getenv("LINA_OKRUZENJE") or "staging"
    return v if v in ("staging", "production") else "staging"


def napravi_zapise(stanje: Stanje) -> dict[str, list[Fields]]:
    """Baut die neuen Datensätze aus dem Gesprächszustand (rein, gut testbar)."""
    k = stanje.kontekst
    rid = k.record_id
    zapisi: dict[str, list[Fields]] = {
        T_DOPUNE: [],
        T_RADNO_ISKUSTVO: [],
        T_OBRAZOVANJE: [],
        T_TERMINI: [],
        T_POZIVI: [],
    }
    kada = stanje.sada()
    oznaka = f"{k.sifra or rid} {kada.strftime('%Y-%m-%d %H:%M')}"
    sazetak = (stanje.sazetak or "").strip()
    if not sazetak and stanje.transkript.strip():
        sazetak = stanje.transkript.strip().replace("\n", " ")[:240]
    if not sazetak:
        sazetak = "Poziv prekinut, nema teksta."
    if stanje.ishod == "nije_zainteresiran" and stanje.dob_iznad_granice():
        sazetak = f"Dob 45+ – ne ispunjava uslov. {sazetak}"
    poziv: Fields = {
        PZ.OZNAKA: oznaka,
        PZ.DATUM: kada.isoformat(timespec="seconds"),
        PZ.SAZETAK: sazetak,
        PZ.ISHOD: stanje.ishod or "prekinuto",
        PZ.OKRUZENJE: _okruzenje(),
        PZ.KANDIDAT: [rid],
    }
    zapisi[T_POZIVI].append(poziv)

    if not _ima_podatke(stanje):
        return zapisi

    notiz = [f"Lina (poziv 1) – ishod: {stanje.ishod or 'prekinuto'}"]
    if stanje.sazetak:
        notiz.append(f"Sažetak: {stanje.sazetak}")
    for key, label in _NOTIZ_LABEL.items():
        if key in stanje.podaci:
            notiz.append(f"{label}: {stanje.podaci[key]}")
    for sk in stanje.nove_skole:
        if sk.smjer or sk.stepen:
            notiz.append(
                f"Škola '{sk.skola}': smjer {sk.smjer or '?'}, stepen {sk.stepen or '?'}"
            )
    for kljuc, odgovor in stanje.napomene_provjere.items():
        if kljuc.startswith("ISPRAVKA:"):
            notiz.append(f"Ispravka {kljuc[len('ISPRAVKA:') :]}: {odgovor}")
        else:
            notiz.append(f"Provjera {kljuc}: {odgovor}")

    dop: Fields = {
        D.KANDIDAT: [rid],
        D.STATUS_PREGLEDA: DOPUNE_NOVO,
        D.OPIS: "\n".join(notiz),
    }
    if k.sifra:
        dop[D.SIFRA] = k.sifra
    for key, fid in _DOPUNE_ZIEL.items():
        if key in stanje.podaci:
            dop[fid] = stanje.podaci[key]
    zapisi[T_DOPUNE].append(dop)

    for s in stanje.nove_stanice:
        f: Fields = {
            RI.KANDIDAT: [rid],
            RI.ISKUSTVO: f"{s.pozicija} – {s.poslodavac}".strip(" –"),
            RI.POZICIJA: s.pozicija,
            RI.POSLODAVAC: s.poslodavac,
            RI.AKTUELNO: s.aktuelno,
        }
        if s.od:
            f[RI.OD] = s.od.datum.isoformat()
        if s.do:
            f[RI.DO] = s.do.datum.isoformat()
        if s.grad:
            f[RI.GRAD] = s.grad
        if s.drzava:
            f[RI.DRZAVA] = s.drzava
        opis = [s.opis] if s.opis else []
        if (s.od and s.od.approx) or (s.do and s.do.approx):
            opis.append("Datum približan (kandidat naveo samo godinu/mjesec).")
        if opis:
            f[RI.OPIS] = "\n".join(opis)
        zapisi[T_RADNO_ISKUSTVO].append(f)

    for sk in stanje.nove_skole:
        f = {OB.KANDIDAT: [rid], OB.SKOLA: sk.skola}
        if sk.adresa:
            f[OB.ADRESA_SKOLE] = sk.adresa
        if sk.od:
            f[OB.OD] = sk.od.datum.isoformat()
        if sk.do:
            f[OB.DO] = sk.do.datum.isoformat()
        zapisi[T_OBRAZOVANJE].append(f)

    if stanje.povratni_poziv:
        zapisi[T_TERMINI].append(
            {
                TZ.NAME: f"Povratni poziv (Lina) – {k.sifra or rid}",
                TZ.DATUM: stanje.povratni_poziv.isoformat(),
                TZ.KANDIDAT: [rid],
                TZ.STATUS: "Todo",
                TZ.NOTES: stanje.povratni_poziv_napomena
                or "Kandidat traži povratni poziv.",
            }
        )
    return zapisi


async def _status_einmal(store: Store, stanje: Stanje) -> None:
    if "status" in stanje.zapisane_tabele:
        return
    diploma, pasos, foto = dokumenti(stanje.polja)
    javio_se = stanje.ishod not in (None, "prekinuto") or "Kandidat:" in (
        stanje.transkript or ""
    )
    novi = odluka(
        javio_se=javio_se,
        zainteresiran=stanje.zainteresiran,
        negativan_komentar=stanje.negativan_komentar,
        iskustvo_u_poslu=stanje.iskustvo_u_poslu,
        licni_popunjeni=licni_popunjeni(stanje.polja, stanje.podaci),
        diploma=diploma,
        pasos=pasos,
        foto=foto,
        trenutni_status=trenutni_status(stanje.polja),
    )
    if novi:
        await store.azuriraj(
            T_PRIJAVE,
            stanje.kontekst.record_id,
            {P.STATUS_KANDIDATA: novi},
        )
    stanje.zapisane_tabele.add("status")


async def sacuvaj(store: Store, stanje: Stanje) -> dict[str, list[str]]:
    """Schreibt jede Tabelle genau einmal. Schlägt eine fehl, kann ein späterer Aufruf
    (z. B. beim Sitzungsende) nur die fehlenden Tabellen nachholen – ohne Duplikate."""
    if stanje.sacuvano or stanje.sprema_u_toku:
        return {}
    stanje.sprema_u_toku = True
    rezultat: dict[str, list[str]] = {}
    try:
        for table, records in napravi_zapise(stanje).items():
            if records and table not in stanje.zapisane_tabele:
                ids = await store.kreiraj(table, records)
                rezultat[table] = ids
                stanje.zapisane_tabele.add(table)
                if table == T_POZIVI and ids and stanje.transkript.strip():
                    key = f"{_okruzenje()}/{stanje.kontekst.record_id}/{ids[0]}.txt"
                    url = await r2.stavi(key, stanje.transkript)
                    if url:
                        await store.azuriraj(table, ids[0], {PZ.LINK: url})
        await _status_einmal(store, stanje)
        stanje.sacuvano = True
    finally:
        stanje.sprema_u_toku = False
    logger.info(
        "gespeichert für %s: %s",
        stanje.kontekst.record_id,
        {t: len(ids) for t, ids in rezultat.items()},
    )
    return rezultat


class AirtableStore:
    """Echter Zugriff über die Airtable REST-API (Field-IDs, keine Namen)."""

    def __init__(
        self, token: str | None = None, base_id: str = BASE_ID, timeout: float = 8.0
    ) -> None:
        self._token = token or os.environ["AIRTABLE_API_KEY"]
        self._base = base_id
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _req(self, method: str, url: str, **kw: Any) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._token}"}
        for pokusaj in range(4):
            async with (
                aiohttp.ClientSession(timeout=self._timeout, headers=headers) as s,
                s.request(method, url, **kw) as r,
            ):
                if r.status == 429 and pokusaj < 3:
                    await asyncio.sleep(1.5 * (pokusaj + 1))
                    continue
                if r.status >= 400:
                    # Nur den Fehlertyp loggen: Airtable-Meldungen können Feldwerte enthalten.
                    try:
                        err = (await r.json()).get("error", {})
                        typ = err.get("type", err) if isinstance(err, dict) else err
                    except (ValueError, aiohttp.ContentTypeError):
                        typ = "unbekannt"
                    raise RuntimeError(f"Airtable {method} {r.status}: {typ}")
                return await r.json()
        raise RuntimeError("Airtable: zu viele 429-Antworten")

    def _url(self, table: str, record_id: str = "") -> str:
        return f"https://api.airtable.com/v0/{self._base}/{table}" + (
            f"/{record_id}" if record_id else ""
        )

    async def _po_id(self, table: str, ids: list[str]) -> list[Fields]:
        out: list[Fields] = []
        for i in range(0, len(ids), 40):
            dio = ids[i : i + 40]
            formula = "OR(" + ",".join(f"RECORD_ID()='{x}'" for x in dio) + ")"
            params = {
                "filterByFormula": formula,
                "returnFieldsByFieldId": "true",
                "pageSize": "100",
            }
            data = await self._req("GET", self._url(table), params=params)
            out.extend(r.get("fields", {}) for r in data.get("records", []))
        return out

    async def ucitaj(self, record_id: str) -> Paket:
        rec = await self._req(
            "GET",
            self._url(T_PRIJAVE, record_id),
            params={"returnFieldsByFieldId": "true"},
        )
        k: Fields = rec.get("fields", {})
        dopune, ri, ob = await asyncio.gather(
            self._po_id(T_DOPUNE, k.get(P.L_DOPUNE, [])),
            self._po_id(T_RADNO_ISKUSTVO, k.get(P.L_RADNO_ISKUSTVO, [])),
            self._po_id(T_OBRAZOVANJE, k.get(P.L_OBRAZOVANJE, [])),
        )
        return Paket(k, dopune, ri, ob)

    async def kreiraj(self, table: str, records: list[Fields]) -> list[str]:
        ids: list[str] = []
        for i in range(0, len(records), 10):
            body = {"records": [{"fields": f} for f in records[i : i + 10]]}
            data = await self._req("POST", self._url(table), json=body)
            ids.extend(r["id"] for r in data.get("records", []))
        return ids

    async def azuriraj(self, table: str, record_id: str, fields: Fields) -> None:
        await self._req(
            "PATCH", self._url(table, record_id), json={"fields": fields}
        )


@dataclass
class FakeStore:
    """Für Simulationen und Tests: In-Memory, gleiche Schnittstelle wie AirtableStore."""

    paket: Paket
    geschrieben: dict[str, list[Fields]] = field(default_factory=dict)

    async def ucitaj(self, record_id: str) -> Paket:
        return self.paket

    async def kreiraj(self, table: str, records: list[Fields]) -> list[str]:
        self.geschrieben.setdefault(table, []).extend(records)
        return [
            f"recFAKE{len(self.geschrieben[table]) - len(records) + i:010d}"
            for i in range(len(records))
        ]

    async def azuriraj(self, table: str, record_id: str, fields: Fields) -> None:
        self.geschrieben.setdefault("patch", []).append(
            {"table": table, "id": record_id, "fields": fields}
        )


__all__ = ["AirtableStore", "FakeStore", "Paket", "Store", "napravi_zapise", "sacuvaj"]
