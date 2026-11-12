"""Jezička korektura u toku poziva: hrvatske riječi, ekavica i njemački/engleski uzvici u
Lininom tekstu.

GPT-Live kroz LiveKit Inference nema keyword biasing, a bosanski nije među jezicima s vlastitim
glasom (OpenAI: „non-native accent or gaps in fluency“ moguće). Zato je ovo jedina korektura
koja djeluje u toku poziva: kad se u Lininoj rečenici pojavi zabranjena riječ, agent.py doda
kratku napomenu u instrukcije (duplex_session.append_instructions, najviše 500 tokena).
Napomena ide najviše MAX_ISPRAVKI puta po pozivu i samo za nove riječi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_ISPRAVKI = 2

# (regex bez granica riječi, bosanska zamjena)
_PRAVILA: tuple[tuple[str, str], ...] = (
    (r"tisuć\w*", "hiljada"),
    (r"tjedan|tjedn\w*", "sedmica"),
    (r"tko", "ko"),
    (r"netko", "neko"),
    (r"nitko", "niko"),
    (r"vlak(?:om|a|u|ovi|ove)?", "voz"),
    (r"kruh\w*", "hljeb"),
    (r"uvjet\w*", "uslov"),
    (r"točn\w*", "tačno"),
    (r"točk\w*", "tačka"),
    (r"sveučilišt\w*", "univerzitet"),
    (r"prijevoz\w*", "prevoz"),
    (r"utjecaj\w*", "uticaj"),
    (r"računal\w*", "kompjuter"),
    (r"iskaznic\w*", "lična karta"),
    (r"siječ(?:anj|nja|nju)", "januar"),
    (r"veljač\w*", "februar"),
    (r"ožuj(?:ak|ka|ku)", "mart"),
    (r"travanj|travnj\w*", "april"),
    (r"svib(?:anj|nja|nju)", "maj"),
    (r"lipanj|lipnj\w*", "juni"),
    (r"srpanj|srpnj\w*", "juli"),
    (r"kolovoz\w*", "august"),
    (r"rujan|rujn\w*", "septembar"),
    (r"listopad\w*", "oktobar"),
    (r"studen(?:i|og|om|oga)", "novembar"),
    (r"prosin(?:ac|ca|cu)", "decembar"),
    (
        r"lepo|vreme|mesto|ovde|gde|dete|deca",
        "ijekavica (lijepo, vrijeme, mjesto, ovdje, gdje, dijete, djeca)",
    ),
    (r"ok|okej|okay", "u redu"),
    (r"super", "odlično"),
    (r"danke", "hvala"),
    (r"bitte", "molim"),
    (r"sorry", "izvini"),
)
_REGEX = [(re.compile(rf"(?i)(?<!\w)(?:{p})(?!\w)"), z) for p, z in _PRAVILA]


@dataclass(frozen=True)
class Nalaz:
    rijec: str  # kako je Lina rekla
    zamjena: str  # bosanski oblik


def nalazi(tekst: str) -> list[Nalaz]:
    """Zabranjene riječi u Lininom tekstu, jedna po zamjeni, redom pojavljivanja."""
    out: list[Nalaz] = []
    vidjeno: set[str] = set()
    for rx, zamjena in _REGEX:
        m = rx.search(tekst or "")
        if m and zamjena not in vidjeno:
            vidjeno.add(zamjena)
            out.append(Nalaz(m.group(0), zamjena))
    return out


def napomena(n: list[Nalaz]) -> str:
    """Kratka napomena za append_instructions (daleko ispod 500 tokena)."""
    parovi = "; ".join(f"„{x.rijec}“ → {x.zamjena}" for x in n[:4])
    return (
        f"Jezik: upravo si rekla {parovi}. To nije bosanski. "
        "Od sada isključivo bosanski, ijekavica: hiljada, sedmica, ko, plata, uslov, tačno, "
        "januar…decembar, „u redu“, „odlično“, „hvala ti“. Ne ispravljaj se naglas, samo nastavi."
    )
