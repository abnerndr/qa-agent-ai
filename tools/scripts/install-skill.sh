#!/usr/bin/env bash
# tools/scripts/install-skill.sh
#
# Instala uma skill a partir DESTE checkout em ~/.claude/skills (escopo
# usuario), sem passar pelo GitHub. Util para testar mudancas locais na
# skill antes de dar push. A fonte da verdade e .claude/skills/<nome>/.
#
# Depois de copiar, roda scripts/setup.sh da skill (se existir) para criar
# o runtime de evidencias. Pule com QA_SKIP_SETUP=1.
#
# Uso:
#   ./tools/scripts/install-skill.sh                    # instala qa-validacao-tasks
#   ./tools/scripts/install-skill.sh <nome>             # instala uma skill especifica
#   ./tools/scripts/install-skill.sh --list             # lista as skills do repositorio

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_DIR="$ROOT_DIR/.claude/skills"

if [ "${1:-}" = "--list" ]; then
  ls -1 "$SKILLS_DIR"
  exit 0
fi

SKILL_NAME="${1:-qa-validacao-tasks}"
SRC="$SKILLS_DIR/$SKILL_NAME"
DEST="$HOME/.claude/skills/$SKILL_NAME"

if [ ! -f "$SRC/SKILL.md" ]; then
  echo "[erro] skill '$SKILL_NAME' nao encontrada em $SKILLS_DIR" >&2
  exit 1
fi

mkdir -p "$DEST"
# copia tudo menos o runtime local (.venv) e caches
tar -C "$SRC" --exclude=.venv --exclude=__pycache__ -cf - . | tar -C "$DEST" -xf -
echo "[ok] $SKILL_NAME instalada em $DEST"

if [ -f "$DEST/scripts/setup.sh" ] && [ "${QA_SKIP_SETUP:-0}" != "1" ]; then
  echo "[info] preparando runtime de evidencias (Playwright + Chromium) ..."
  bash "$DEST/scripts/setup.sh"
fi
