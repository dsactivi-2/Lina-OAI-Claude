"""Pre-Call-Kontext: Was ist schon bekannt, was fehlt?

Regel (docs/airtable.md): Eine Angabe wird nur abgefragt, wenn sie
(a) abgefragt werden soll UND (b) leer ist – in `Prijave (test)` UND in allen
offenen `Dopune`-Einträgen (Status ≠ „Odbačeno“).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import (
    DOPUNE_ODBACENO,
    OB,
    PITANJA,
    RI,
    D,
    P,
)
from .datumi import Datum, parse_datum
from .verzija import granica_godina, je_v3

Fields = dict[str, Any]

PLATZHALTER_LEER = {"", "-", "?", "–"}


def _skola_ok(naziv: str) -> bool:
    import unicodedata

    s = unicodedata.normalize("NFKD", naziv or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return any(
        w in s for w in ("skol", "gimnaz", "fakultet", "univerzitet", "akademij")
    )


def prazno(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() in PLATZHALTER_LEER
    if isinstance(v, (list, tuple, dict, set)):
        return len(v) == 0
    return False


def _tekst(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, dict):  # singleSelect u nekim API odgovorima
        return str(v.get("name", ""))
    return str(v).strip()


@dataclass
class Stanica:
    """Eine Berufsstation (aus Airtable oder vom Kandidaten)."""

    pozicija: str
    poslodavac: str
    od: Datum | None
    do: Datum | None
    aktuelno: bool = False
    grad: str = ""
    drzava: str = ""
    opis: str = ""
    izvor: str = "airtable"  # airtable | lina

    def kratko(self) -> str:
        od = self.od.datum.year if self.od else "?"
        do = "danas" if self.aktuelno else (self.do.datum.year if self.do else "?")
        return f"{self.pozicija or '?'} – {self.poslodavac or '?'} ({od}–{do})"


@dataclass
class Skola:
    skola: str
    adresa: str
    od: Datum | None
    do: Datum | None
    smjer: str = ""
    stepen: str = ""
    izvor: str = "airtable"

    def kratko(self) -> str:
        od = self.od.datum.year if self.od else "?"
        do = self.do.datum.year if self.do else "?"
        smjer = f", {self.smjer}" if self.smjer else ""
        return f"{self.skola or '?'}{smjer} ({od}–{do})"


@dataclass
class Kontekst:
    record_id: str
    sifra: str
    ime: str
    nedostaje: list[str]
    poznato_iskustvo: list[str] = field(default_factory=list)
    poznato_obrazovanje: list[str] = field(default_factory=list)
    stanice: list[Stanica] = field(default_factory=list)
    skole: list[Skola] = field(default_factory=list)
    datum_rodjenja: Datum | None = None
    poznata_polja: list[str] = field(default_factory=list)  # oznake, bez vrijednosti

    def za_instrukcije(self) -> str:
        """Bosnischer Block für die Instruktionen. Enthält keine Rohdaten aus Airtable."""
        lab = {p.key: p.label for p in PITANJA}
        nedostaje = (
            "\n".join(f"- {lab[k]}" for k in self.nedostaje)
            or "- ništa (svi podaci su već upisani)"
        )
        linije = [
            f"Ime kandidata: {self.ime or 'nepoznato'}",
            "Podaci koji NEDOSTAJU (pitaj samo ovo, ovim redom):",
            nedostaje,
        ]
        if self.poznata_polja and je_v3():  # v2 bleibt wie in Produktion
            linije.append(
                "Već imamo iz prijave (NE pitaj, NE čitaj naglas, ne traži potvrdu): "
                + ", ".join(self.poznata_polja)
                + ". Ako kandidat to sam spomene ili ponudi: „To već imamo iz prijave, hvala.“"
            )
        if self.poznato_iskustvo:
            linije.append(
                "Već upisano radno iskustvo (NE pitaj ponovo; samo jednom pitaj ima li još nešto):\n"
                + "\n".join(f"- {s}" for s in self.poznato_iskustvo)
            )
        if self.poznato_obrazovanje:
            linije.append(
                "Već upisano školovanje (NE pitaj ponovo; samo jednom pitaj ima li još nešto):\n"
                + "\n".join(f"- {s}" for s in self.poznato_obrazovanje)
            )
        if self.datum_rodjenja:
            from datetime import date

            d = self.datum_rodjenja.datum
            danas = date.today()
            godine = danas.year - d.year - ((danas.month, danas.day) < (d.month, d.day))
            if godine >= granica_godina():
                linije.append(
                    "Godine: četrdeset pet ili više. Ne pitaj dalje. Reci da zbog uslova za radnu dozvolu u Njemačkoj ne možemo dalje i završi poziv (nije_zainteresiran)."
                    if granica_godina() == 45
                    else "Godine: šezdeset ili više. Ne pitaj dalje. Reci da je posao težak fizički rad napolju i završi poziv."
                )
        sumnjive = [s.skola for s in self.skole if s.skola and not _skola_ok(s.skola)]
        if sumnjive:
            linije.append(
                "Škola je upisana, ali naziv ne liči na školu ("
                + ", ".join(sumnjive)
                + "). Pitaj jednom, čim dođe školovanje: „Samo da provjerim — ta škola je u tom gradu?“"
            )
        return "\n".join(linije)


def _stanica_iz_ri(f: Fields) -> Stanica:
    return Stanica(
        pozicija=_tekst(f.get(RI.POZICIJA)),
        poslodavac=_tekst(f.get(RI.POSLODAVAC)),
        od=parse_datum(f.get(RI.OD), kraj=False),
        do=parse_datum(f.get(RI.DO), kraj=True),
        aktuelno=bool(f.get(RI.AKTUELNO)),
        grad=_tekst(f.get(RI.GRAD)),
        drzava=_tekst(f.get(RI.DRZAVA)),
    )


def _skola_iz_ob(f: Fields) -> Skola:
    return Skola(
        skola=_tekst(f.get(OB.SKOLA)),
        adresa=_tekst(f.get(OB.ADRESA_SKOLE)),
        od=parse_datum(f.get(OB.OD), kraj=False),
        do=parse_datum(f.get(OB.DO), kraj=True),
    )


def izracunaj(
    record_id: str,
    kandidat: Fields,
    dopune: list[Fields],
    radno_iskustvo: list[Fields],
    obrazovanje: list[Fields],
) -> Kontekst:
    """Berechnet den Kontext. Alle Listen enthalten Felddicts (Field-ID → Wert)."""
    otvorene = [
        d for d in dopune if _tekst(d.get(D.STATUS_PREGLEDA)) != DOPUNE_ODBACENO
    ]

    stanice = [_stanica_iz_ri(f) for f in radno_iskustvo]
    od_flat = parse_datum(_tekst(kandidat.get(P.RI_OD)), kraj=False)
    do_flat = parse_datum(_tekst(kandidat.get(P.RI_DO)), kraj=True)
    if od_flat and do_flat and not prazno(kandidat.get(P.RADNO_MJESTO)):
        stanice.append(
            Stanica(
                _tekst(kandidat.get(P.RADNO_MJESTO)),
                _tekst(kandidat.get(P.KOMPANIJA)),
                od_flat,
                do_flat,
                izvor="prijava",
            )
        )
    skole = [_skola_iz_ob(f) for f in obrazovanje]

    poznato_iskustvo = [s.kratko() for s in stanice]
    if not stanice and not prazno(kandidat.get(P.RADNO_MJESTO)):
        poznato_iskustvo.append(
            f"{_tekst(kandidat.get(P.RADNO_MJESTO))} – {_tekst(kandidat.get(P.KOMPANIJA)) or '?'} (iz prijave)"
        )
    for d in otvorene:
        if not prazno(d.get(D.RI1_RADNO_MJESTO)):
            poznato_iskustvo.append(
                f"{_tekst(d.get(D.RI1_RADNO_MJESTO))} (iz dopune, čeka pregled)"
            )

    poznato_obrazovanje = [s.kratko() for s in skole]
    if not skole and not prazno(kandidat.get(P.SKOLA_TXT)):
        struka = _tekst(kandidat.get(P.STRUKA_TXT))
        poznato_obrazovanje.append(
            f"{_tekst(kandidat.get(P.SKOLA_TXT))}{', ' + struka if struka else ''} (iz prijave)"
        )
    for d in otvorene:
        if not prazno(d.get(D.SKOLA)):
            poznato_obrazovanje.append(
                f"{_tekst(d.get(D.SKOLA))} (iz dopune, čeka pregled)"
            )

    nedostaje: list[str] = []
    for p in PITANJA:
        if not p.abfragen:
            continue
        if p.key == "radno_iskustvo":
            vorhanden = bool(poznato_iskustvo)
        elif p.key == "obrazovanje":
            vorhanden = bool(poznato_obrazovanje)
        else:
            vorhanden = any(not prazno(kandidat.get(fid)) for fid in p.prijave) or (
                p.dopune is not None
                and any(not prazno(d.get(p.dopune)) for d in otvorene)
            )
        if not vorhanden:
            nedostaje.append(p.key)

    # Was schon da ist, nur als Bezeichnung: der Prompt soll „das haben wir schon“ sagen können,
    # ohne Rohdaten zu sehen. Telefon gehört dazu, obwohl es nie abgefragt wird.
    poznata_polja: list[str] = []
    if not prazno(kandidat.get(P.TELEFON)):
        poznata_polja.append("broj telefona")
    for p in PITANJA:
        if p.key in ("radno_iskustvo", "obrazovanje") or not p.abfragen:
            continue
        if p.key not in nedostaje:
            poznata_polja.append(p.label)

    dr = parse_datum(
        _tekst(kandidat.get(P.DATUM_RODJENJA_DATE)), kraj=False
    ) or parse_datum(_tekst(kandidat.get(P.DATUM_RODJENJA_TXT)), kraj=False)

    return Kontekst(
        record_id=record_id,
        sifra=_tekst(kandidat.get(P.SIFRA)),
        ime=_tekst(kandidat.get(P.IME)),
        nedostaje=nedostaje,
        poznato_iskustvo=poznato_iskustvo,
        poznato_obrazovanje=poznato_obrazovanje,
        stanice=stanice,
        skole=skole,
        datum_rodjenja=dr,
        poznata_polja=poznata_polja,
    )
