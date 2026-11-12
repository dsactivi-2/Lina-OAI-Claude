"""Welche Lina-Version läuft: v2 (eingefroren, Standard) oder v3 (LINA_PROMPT=v3).

Eigenes Modul, damit prompts.py, kontekst.py und die Tools dieselbe Entscheidung lesen,
ohne sich gegenseitig zu importieren.
"""

from __future__ import annotations

import os

V2 = "2.0.0"
V3 = "3.0.0"


def _wunsch() -> str:
    """LINA_PROMPT, sonst Standard je Deployment.

    LiveKit-Cloud-Secrets gelten für alle Deployments eines Agents (Doku „Non-production
    deployments“, Stand 11.11.2026). Ein Secret LINA_PROMPT=v3 würde also auch production
    umschalten. Deshalb wählt der Code selbst: LIVEKIT_AGENT_DEPLOYMENT setzt LiveKit Cloud,
    „staging“ auf dem Tester, leer auf production. Staging = v3, production = v2.
    """
    wert = os.getenv("LINA_PROMPT", "").strip().lower()
    if wert:
        return wert
    return (
        "v3" if os.getenv("LIVEKIT_AGENT_DEPLOYMENT", "").strip() == "staging" else "v2"
    )


def aktivna_verzija() -> str:
    """Prompt-Version dieser Session: V3 bei LINA_PROMPT=v3 oder auf staging, sonst V2."""
    return V3 if _wunsch() == "v3" else V2


def je_v3() -> bool:
    return aktivna_verzija() == V3


def granica_godina() -> int:
    """Ab diesem Alter endet das Gespräch: v3 ab 45 (Entscheidung E3), v2 ab 60."""
    return 45 if je_v3() else 60
