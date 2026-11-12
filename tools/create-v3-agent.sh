#!/usr/bin/env bash
# Eigener Testagent aus dem Fork. Keine Befehle gegen die alte Agent-ID.
set -Eeuo pipefail
trap 'printf "\nAbgebrochen in Zeile %s. Bitte die letzte Ausgabe im Chat teilen.\n" "$LINENO" >&2' ERR

lina_source="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
lina_target="$(dirname "$lina_source")/Lina-OAI-Claude-v3-test"
lina_remote="https://github.com/dsactivi-2/Lina-OAI-Claude.git"

for lina_cmd in git uv lk; do
  command -v "$lina_cmd" >/dev/null || {
    printf 'Befehl fehlt: %s\n' "$lina_cmd" >&2
    exit 1
  }
done

if [ ! -e "$lina_target" ]; then
  git clone --branch main "$lina_remote" "$lina_target"
  cd "$lina_target"
  git switch -c "lina-v3-test-$(date -u +%Y%m%d-%H%M%S)"
  # Die übernommene alte Agent-ID wird NUR im neuen Clone ersetzt.
  printf '[project]\n  subdomain = "lina-oai-kk6g8p5z"\n' > livekit.toml
  printf 'lina-v3-test\n' > .git/lina-preview-workspace
else
  test -f "$lina_target/.git/lina-preview-workspace" || {
    printf 'Zielordner existiert bereits und wurde nicht von diesem Skript vorbereitet: %s\n' "$lina_target" >&2
    exit 1
  }
  cd "$lina_target"
fi
test "$(git remote get-url origin)" = "$lina_remote"
case "$(git branch --show-current)" in
  lina-v3-test-*) ;;
  *) printf 'Unerwarteter Branch im Test-Clone; angehalten.\n' >&2; exit 1 ;;
esac
git diff --cached --quiet || {
  printf 'Bereits vorgemerkte Änderungen im Test-Clone. Bitte git status dort teilen.\n' >&2
  exit 1
}

lina_files=(
  src/agent.py
  src/lina/prompts.py
  tests/test_preview.py
  tests/test_prompt_v2_kraj_ispravke.py
  tests/test_staging_kraj.py
  scenarios-gpt-live.yaml
  docs/HOERTEST-V3.md
  docs/NEUER-TESTAGENT.md
  CHANGELOG.md
  pyproject.toml
  uv.lock
  tools/create-v3-agent.sh
)
for lina_file in "${lina_files[@]}"; do
  mkdir -p "$(dirname "$lina_file")"
  cp "$lina_source/$lina_file" "$lina_file"
done

# Keine .env-Dateien aus der bestehenden Installation übernehmen.
export UV_PROJECT_ENVIRONMENT="$lina_target/.venv"
uv lock
UV_GIT_LFS=1 uv sync --locked --dev
uv run --locked ruff format src/agent.py src/lina/prompts.py tests/test_preview.py tests/test_prompt_v2_kraj_ispravke.py tests/test_staging_kraj.py
uv run --locked ruff check --no-respect-gitignore src/agent.py src/lina/prompts.py tests/test_preview.py tests/test_prompt_v2_kraj_ispravke.py tests/test_staging_kraj.py
(
  export LINA_PROMPT=v2
  export LINA_PREVIEW=0
  export LIVEKIT_AGENT_DEPLOYMENT=""
  uv run --locked pytest -q
)
git diff --check
git add -- "${lina_files[@]}" livekit.toml
if ! git diff --cached --quiet; then
  git commit -m "feat: eigener Lina V3 Hörtestagent mit fiktiven Daten"
fi
git push --set-upstream origin "$(git branch --show-current)"

# Die neue Agent-ID wird nach create in livekit.toml eingetragen.
lina_agent_id="$(uv run --locked python -c 'import pathlib, tomllib; print(tomllib.loads(pathlib.Path("livekit.toml").read_text()).get("agent", {}).get("id", ""))')"
if [ "$lina_agent_id" = "CA_xPubxhi5ER7v" ]; then
  printf 'Alte Agent-ID entdeckt; kein Cloud-Befehl ausgeführt.\n' >&2
  exit 1
fi

if [ -z "$lina_agent_id" ]; then
  if [ -f .git/lina-preview-create-started ]; then
    printf 'Ein create-Versuch wurde bereits gestartet, aber es fehlt die neue Agent-ID. Bitte Ausgabe teilen; kein zweiter Agent wird automatisch erzeugt.\n' >&2
    exit 1
  fi
  touch .git/lina-preview-create-started
  lk agent create --region eu-central \
    --secrets LINA_AGENT_NAME=lina-v3-test \
    --secrets LINA_PROMPT=v3 \
    --secrets LINA_PREVIEW=1 \
    --secrets LINA_ENV=preview \
    --secrets LINA_VOICE=marin
else
  # Wiederholter Aufruf aktualisiert nur den zuvor hier angelegten Testagenten.
  test -f .git/lina-preview-create-started
  lk agent deploy \
    --secrets LINA_AGENT_NAME=lina-v3-test \
    --secrets LINA_PROMPT=v3 \
    --secrets LINA_PREVIEW=1 \
    --secrets LINA_ENV=preview \
    --secrets LINA_VOICE=marin
fi

lina_agent_id="$(uv run --locked python -c 'import pathlib, tomllib; print(tomllib.loads(pathlib.Path("livekit.toml").read_text()).get("agent", {}).get("id", ""))')"
test -n "$lina_agent_id"
test "$lina_agent_id" != "CA_xPubxhi5ER7v"
git add -- livekit.toml
if ! git diff --cached --quiet; then
  git commit -m "chore: LiveKit-ID des neuen Lina-Testagenten speichern"
  git push
fi
lk agent status
printf '\nNeuer Testagent: %s\nAufrufname: lina-v3-test\nOrdner: %s\n' "$lina_agent_id" "$lina_target"
printf 'Agent Console: neuen Agenten auswählen, Deployment production, Mikrofon starten und Halo sagen.\n'
printf 'Fiktiver Bewerber: Emir, geboren am 15.03.1992. Keine Airtable-Schreibzugriffe.\n'
git log -1 --format='Commit: %h %s'
