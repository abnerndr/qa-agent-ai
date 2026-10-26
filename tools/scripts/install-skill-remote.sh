#!/usr/bin/env bash
# tools/scripts/install-skill-remote.sh
#
# Instala uma skill deste repositorio na pasta de skills de uma ou mais IAs
# (escopo usuario: Claude Code, Codex, Gemini CLI, Cursor...), sem precisar clonar
# o repositorio inteiro nem colar o conteudo do SKILL.md manualmente.
#
# Usa "git clone --filter=blob:none --sparse" pra baixar so as skills e o
# instalador num clone temporario, instala e apaga
# o temporario. Sempre pega a versao mais recente do repositorio (branch
# padrao), entao rodar de novo depois de uma atualizacao so sobrescreve.
#
# Depois de copiar, roda scripts/setup.sh da skill (se existir), que cria o
# runtime Python com Playwright + Chromium usado para capturar evidencias e
# gerar o relatorio PDF. Pule com QA_SKIP_SETUP=1.
#
# Aceita as mesmas opcoes do install-skill.sh (--ia, --dir): baixa a skill e
# o instalador e delega para ele.
#
# Requisitos: git >= 2.25, acesso de leitura ao repositorio, uv ou
# python3-venv (para o runtime de evidencias).
#
# Uso:
#   ./install-skill-remote.sh                              # qa-validacao-tasks no Claude
#   ./install-skill-remote.sh --ia claude,codex,gemini     # em varias IAs
#   ./install-skill-remote.sh --ia todas                   # em toda IA instalada
#   curl -fsSL <raw>/install-skill-remote.sh | bash -s -- --ia todas
#   QA_REF=project ./install-skill-remote.sh               # outra branch

set -euo pipefail

REPO_URL="https://github.com/abnerndr/qa-agent-ai.git"
REF="${QA_REF:-}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "[info] clonando .claude/skills e o instalador de $REPO_URL ${REF:+(branch $REF)} ..."
git clone --depth 1 --filter=blob:none --sparse ${REF:+--branch "$REF"} "$REPO_URL" "$TMP_DIR" --quiet
git -C "$TMP_DIR" sparse-checkout set ".claude/skills" "tools/scripts" --quiet

bash "$TMP_DIR/tools/scripts/install-skill.sh" "$@"
