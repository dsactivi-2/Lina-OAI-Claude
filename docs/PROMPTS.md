---
title: Prompt-Versionen und Wissensdateien
---

# Prompt-Versionen und Wissensdateien

Stand: Code auf `main`. Umschalten in `src/lina/verzija.py`. Beide Prompt-Sätze leben parallel: `prompts_v2.py` (eingefroren) und `prompts.py` (v3).

## Welche Version läuft?

```text
LINA_PROMPT gesetzt? ──ja──► v3 nur bei Wert „v3“, sonst v2
         │
         nein
         ▼
LIVEKIT_AGENT_DEPLOYMENT == "staging" ──► v3
sonst (production, lokal, leer)        ──► v2
```

LiveKit-Cloud-Secrets gelten für **alle** Deployments eines Agents. Ein Secret `LINA_PROMPT=v3` würde also auch Production umschalten. Deshalb wählt der Code selbst: Staging ohne Secret = v3, Production ohne Secret = v2.

| Umgebung | Prompt | Alter-Grenze | Wissen | Sprachkorrektur | Backend reasoning/verbosity |
|---|---|---|---|---|---|
| production (Secret leer) | v2 (`2.0.0`) | 60, im Code ohne Abbruch | `znanje-lina-v2.md` | aus | OpenAI-Standard |
| staging (Secret leer) | v3 (`3.0.0`) | 45 → Gesprächsende | `znanje-lina.md` + `jobstep.md` | `jezik.py`, max. 2× | Standard `low` / `low` |
| lokal `LINA_PROMPT=v2` | v2 | wie production | v2-Datei | aus | Standard |
| lokal `LINA_PROMPT=v3` | v3 | wie staging | v3-Dateien | an | `LINA_BACKEND_*` |

Langfuse-Metadatum: `lina.prompt_verzija`. v2-Prompts sind zeichengleich gegen Tag `lina-v2.0-prod` geprüft (`tests/test_v2_eingefroren.py`). Nicht an `prompts_v2.py` oder `znanje-lina-v2.md` drehen, außer für den eingefrorenen Stand.

## Wissensdateien

Pfad: `docs/knowledge/`. Der Prompt lädt den Dateiinhalt in **alle** Voice- und Backend-Instruktionen der jeweiligen Version (`_znanje()`).

| Datei | v2 | v3 | Rolle |
|---|---|---|---|
| `znanje-lina-v2.md` | ja | nein | eingefrorenes Produktionswissen |
| `znanje-lina.md` | nein | ja | Positionen, Gehalt, Turnus |
| `jobstep.md` | nein | ja | Agentur-Fakten, nur auf Nachfrage |
| `job-angebot.md` | nein | nein | Entwurf, wird **nicht** geladen |

`job-angebot.md` ist nur Doku. Lina sagt im Anruf nichts daraus.

## Fallstrick: YAML-Frontmatter im Anruf

Die Knowledge-Seiten haben YAML-Frontmatter für das Doku-Hosting (`title: …` zwischen `---`). `_znanje()` auf `main` liest die Datei **roh**. Damit stehen z. B. `title: Znanje za Linu v3` und die Trennstriche im GPT-Live-Prompt.

Das ist unbeabsichtigt: Frontmatter ist Navigations-Metadaten, kein Wissen fürs Gespräch.

- Branch `test/znanje-frontmatter` (23.11.2026) enthält `src/lina/znanje.py` (`ohne_yaml_frontmatter`) plus Tests — **nicht** auf `main`.
- Bis das gemergt ist: Frontmatter klein halten, keine Fakten nur in `title:` ablegen.
- `docs/knowledge/*.md` ändern = Prompt ändern. Danach `uv run pytest tests/test_lina3.py tests/test_v2_eingefroren.py` und ein Debugger-Turn.

## Backend hinter GPT-Live

`responses_options` in `src/agent.py` → `_responses_options()`:

- Modell: `LINA_BACKEND_MODEL`, Standard `gpt-5.6-luna`.
- Stimme: `LINA_VOICE`, Standard `marin` (GPT-Live hat keine bosnische Stimme; Kombination Stimme + Jezik-Block anhören).
- v3: `LINA_BACKEND_REASONING` / `LINA_BACKEND_VERBOSITY` (Standard `low`). `LINA_BACKEND_MAX_TOKENS` nur setzen, wenn nötig — zu klein bricht Tool-Aufrufe ab.
- v2: diese Optionen werden **nicht** gesetzt.

Hörtest 11.11.2026: Standard-Reasoning bei 8–18k Input-Tokens → 4–6 s Pause.

## Abschluss in v3 ohne neue Session

`predji_na_kraj` hängt Kraj-Regeln an und entzieht Datentools. `KrajAgent.on_enter` (Zahvala per `generate_reply`) gilt nur im klassischen Handoff-Pfad, den v3 im Anruf nicht mehr nimmt. Sicherheitsnetz: 40 s-Timer plus Shutdown-`sacuvaj()`.

## Szenarien je Version

| Datei | Zweck |
|---|---|
| `scenarios.yaml` | Kernfluss Anruf 1 |
| `scenarios-guardrails.yaml` | Opt-out, falsche Person, Abbruch |
| `scenarios-neu.yaml` | Scherz, E-Mail, Smalltalk (0.2.2) |
| `scenarios-lina3.yaml` | v3: S1–S19, P1–P3 |
| `scenarios-gpt-live.yaml` | GPT-Live-spezifisch, u. a. Abschied/Auflegen |

Lokal: `lk agent simulate audio --scenarios <datei>`. CI führt nur die ersten zwei Dateien aus und nur manuell.
