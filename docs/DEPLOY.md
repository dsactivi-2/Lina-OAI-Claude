---
title: Deploy auf LiveKit Cloud
---

# Deploy auf LiveKit Cloud

Projekt `lina-oai` (`p_40xj9wk3r8d`), Agent-Name `livekit-oai-gig-casting`, Region **eu-central** (EU).

## 1. Secrets-Datei anlegen (nicht committen)
`LIVEKIT_URL`, `LIVEKIT_API_KEY` und `LIVEKIT_API_SECRET` setzt LiveKit Cloud **selbst**. Sie dürfen
nicht als Secret mitgegeben werden. Deshalb eine eigene Datei `.env.cloud` anlegen
(sie ist über `.env.*` in `.gitignore` ausgeschlossen):

```text
AIRTABLE_API_KEY=pat...
AIRTABLE_BASE_ID=appz3VFomHaWhuILV
AIRTABLE_TABLE=tbl7WHRtBkRX7tGxt
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_INHALTE=1
# NUR für die Testphase: Agent Console ohne Metadaten → Test-Kandidat K-0196.
# Vor echten Anrufen ENTFERNEN (sonst landen Tests ohne Kandidat bei K-0196).
LINA_TEST_RECORD_ID=rec17GODhyD0Lkgzp
# Optional: Transkript nach R2 (alle fünf oder keine). Fehlt etwas, bleibt die Pozivi-Zeile.
# R2_BUCKET=
# R2_PUBLIC_BASE=
# R2_ENDPOINT=
# R2_ACCESS_KEY_ID=
# R2_SECRET_ACCESS_KEY=
```

Kein `LINA_PROMPT` als Cloud-Secret setzen: Secrets gelten für **alle** Deployments.
Staging nimmt v3, Production v2 (`src/lina/verzija.py`, `docs/PROMPTS.md`).

## 2. Erstes Deploy
```bash
lk agent create --region eu-central --secrets-file .env.cloud
```
Legt `livekit.toml` mit der Agent-ID an (die Datei committen, sie enthält keine Secrets).

## 3. Weitere Versionen
```bash
lk agent deploy
lk agent status
lk agent logs
```
Secrets ändern: `lk agent update-secrets --secrets-file .env.cloud` (Befehl vorher mit
`lk agent --help` prüfen).

## 4. Testen in der Cloud
- **Agent Console** im LiveKit-Dashboard → Agent `livekit-oai-gig-casting` → sprechen. Dort hörst
  du Lina und siehst Transkript, Tool-Aufrufe und Zeiten.
- **Audio-Simulationen gegen den deployten Agent:**
  ```bash
  lk agent simulate audio --agent-name livekit-oai-gig-casting --scenarios scenarios.yaml
  ```
- **Langfuse:** Traces unter dem Raumnamen (`langfuse.session.id`).

## Ablauf bei jeder Änderung (production = Original, staging = Tester)
1. **Ändern auf `dev`**: `git switch dev`, Tests: `uv run pytest -q && uv run ruff check src tests`.
2. **Version hochzählen** in `pyproject.toml` UND `uv lock` ausführen (sonst bricht der Cloud-Build
   wegen `uv sync --locked` ab), Eintrag in `CHANGELOG.md`, committen, `git push`.
3. **Auf den Tester**: `lk agent deploy --deployment staging`. Prüfen: Testanruf mit
   `--deployment staging`, Simulation, Langfuse (Environment `staging`, Release = Version).
4. **Freigabe nur nach „bestätige“**:
   ```bash
   git switch main && git merge dev && git push
   git tag -a vX.Y.Z -m "…" && git push origin vX.Y.Z
   lk agent promote --deployment staging
   ```
5. **Notieren**: LiveKit-Version aus `lk agent status` in `CHANGELOG.md` eintragen.

Wichtig:
- Befehle einzeln ausführen, nie als Block einfügen (sonst läuft `promote` ungewollt mit).
- `lk agent delete` nie ohne `--deployment staging` (sonst ist das Original weg).
- Testanrufe ohne `--deployment` gehen an das Original.
- Den LiveKit-Starter-Workflow `template-check.yml` nicht wieder anlegen:
  `uv.lock` und `livekit.toml` gehören in dieses Repo.

## Rollback
Ship-Plan: `lk agent rollback` (Optionen mit `lk agent rollback --help` prüfen; Versions-IDs in `CHANGELOG.md`).
Notfalls älteren Git-Tag auschecken und `lk agent deploy`.
