"""Wissensdateien für den Anruf: YAML-Frontmatter bleibt in der Doku, nicht im Prompt."""

from __future__ import annotations

from pathlib import Path

_FALLBACK = "Nemaš dodatnih informacija o poslu. Na pitanja o poslu reci da ćeš zabilježiti pitanje."


def ohne_yaml_frontmatter(text: str) -> str:
    """Entfernt einen führenden YAML-Block (`--- … ---`). Sonst unverändert.

    Ohne schließendes `---` bleibt der Text stehen, damit Wissen nicht
    verschluckt wird, wenn die Datei kaputt ist.
    """
    if text.startswith("---\r\n"):
        nl = "\r\n"
    elif text.startswith("---\n"):
        nl = "\n"
    else:
        return text
    rest = text[len("---" + nl) :]
    closer = nl + "---" + nl
    idx = rest.find(closer)
    if idx < 0:
        return text
    return rest[idx + len(closer) :].lstrip("\n\r")


def citaj_znanje(path: Path, *, fallback: str | None = None) -> str:
    """Liest eine Wissensdatei und entfernt Doku-Metadaten."""
    try:
        return ohne_yaml_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        return _FALLBACK if fallback is None else fallback
