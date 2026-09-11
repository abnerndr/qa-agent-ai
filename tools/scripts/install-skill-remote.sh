#!/usr/bin/env bash
# tools/scripts/install-skill-remote.sh
#
# Instala uma skill deste repositorio em ~/.claude/skills (escopo usuario,
# funciona em qualquer projeto aberto com Claude Code), sem precisar clonar
# o repositorio inteiro nem colar o conteudo do SKILL.md manualmente.
#
# Usa "git clone --filter=blob:none --sparse" pra baixar so a pasta da
# skill dentro de um clone temporario, copia pra ~/.claude/skills e apaga
# o temporario. Sempre pega a versao mais recente do repositorio (branch
# padrao), entao rodar de novo depois de uma atualizacao so sobrescreve.
#
# Requisitos: git >= 2.25, acesso de leitura ao repositorio.
#
# Uso:
#   ./install-skill-remote.sh                    # instala qa-validacao-tasks (default)
#   ./install-skill-remote.sh qa-validacao-tasks  # instala uma skill especifica

set -euo pipefail

REPO_URL="https://github.com/abnerndr/qa-agent-ai.git"
SKILL_NAME="${1:-qa-validacao-tasks}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "[info] clonando so .claude/skills/$SKILL_NAME de $REPO_URL ..."
git clone --depth 1 --filter=blob:none --sparse "$REPO_URL" "$TMP_DIR" --quiet
git -C "$TMP_DIR" sparse-checkout set ".claude/skills/$SKILL_NAME" --quiet

SRC="$TMP_DIR/.claude/skills/$SKILL_NAME"
if [ ! -d "$SRC" ]; then
  echo "[erro] skill '$SKILL_NAME' nao encontrada em $REPO_URL" >&2
  exit 1
fi

DEST="$HOME/.claude/skills/$SKILL_NAME"
mkdir -p "$DEST"
cp -r "$SRC/." "$DEST/"

echo "[ok] $SKILL_NAME instalada em $DEST"
