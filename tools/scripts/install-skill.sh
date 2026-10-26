#!/usr/bin/env bash
# tools/scripts/install-skill.sh
#
# Instala uma skill a partir DESTE checkout na pasta de skills de uma ou mais
# IAs (escopo usuario), sem passar pelo GitHub. A fonte da verdade e
# .claude/skills/<nome>/. A skill segue o formato aberto de Agent Skills
# (SKILL.md + scripts/), entao a mesma pasta serve para qualquer agente.
#
# A primeira IA recebe a copia real e o runtime (scripts/setup.sh: .venv com
# Playwright + Chromium). As demais recebem um link simbolico para ela, sem
# duplicar o .venv. Onde link nao funciona (Windows/Git Bash), copia e roda o
# setup de novo. Pule o setup com QA_SKIP_SETUP=1.
#
# Uso:
#   ./tools/scripts/install-skill.sh                          # qa-validacao-tasks no Claude
#   ./tools/scripts/install-skill.sh --ia claude,codex,gemini # em varias IAs
#   ./tools/scripts/install-skill.sh --ia todas               # em toda IA instalada nesta maquina
#   ./tools/scripts/install-skill.sh --dir ~/minha-ia/skills  # numa pasta qualquer
#   ./tools/scripts/install-skill.sh <nome> [--ia ...]        # outra skill
#   ./tools/scripts/install-skill.sh --list                   # lista skills e IAs conhecidas

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_DIR="$ROOT_DIR/.claude/skills"

# ia:pasta de skills de usuario. "agents" e a pasta compartilhada do padrao Agent Skills.
IAS="claude:$HOME/.claude/skills
agents:$HOME/.agents/skills
codex:$HOME/.codex/skills
gemini:$HOME/.gemini/skills
cursor:$HOME/.cursor/skills
copilot:$HOME/.copilot/skills
opencode:$HOME/.config/opencode/skills"

SKILL_NAME="qa-validacao-tasks"
ALVOS=()
IA_LISTA="claude"

while [ $# -gt 0 ]; do
  case "$1" in
    --list)
      echo "skills:"; ls -1 "$SKILLS_DIR" | sed 's/^/  /'
      echo "ias (--ia):"; echo "$IAS" | sed 's/^/  /; s/:/ → /'
      exit 0 ;;
    --ia) IA_LISTA="$2"; shift 2 ;;
    --dir) ALVOS+=("$2"); IA_LISTA=""; shift 2 ;;
    -*) echo "[erro] opcao desconhecida: $1" >&2; exit 1 ;;
    *) SKILL_NAME="$1"; shift ;;
  esac
done

SRC="$SKILLS_DIR/$SKILL_NAME"
if [ ! -f "$SRC/SKILL.md" ]; then
  echo "[erro] skill '$SKILL_NAME' nao encontrada em $SKILLS_DIR" >&2
  exit 1
fi

if [ "$IA_LISTA" = "todas" ]; then
  # so as IAs cuja pasta de configuracao ja existe nesta maquina
  while IFS=: read -r ia pasta; do
    [ -d "$(dirname "$pasta")" ] && ALVOS+=("$pasta")
  done <<< "$IAS"
elif [ -n "$IA_LISTA" ]; then
  for ia in ${IA_LISTA//,/ }; do
    pasta="$(echo "$IAS" | awk -F: -v ia="$ia" '$1 == ia { print $2 }')"
    [ -n "$pasta" ] || { echo "[erro] IA desconhecida: $ia (veja --list ou use --dir)" >&2; exit 1; }
    ALVOS+=("$pasta")
  done
fi
[ ${#ALVOS[@]} -gt 0 ] || { echo "[erro] nenhuma pasta de destino" >&2; exit 1; }

setup() {
  if [ -f "$1/scripts/setup.sh" ] && [ "${QA_SKIP_SETUP:-0}" != "1" ]; then
    echo "[info] preparando runtime de evidencias (Playwright + Chromium) em $1 ..."
    bash "$1/scripts/setup.sh"
  fi
}

PRINCIPAL=""
for pasta in "${ALVOS[@]}"; do
  DEST="$pasta/$SKILL_NAME"
  mkdir -p "$pasta"
  if [ -z "$PRINCIPAL" ]; then
    [ -L "$DEST" ] && rm "$DEST"   # era link de uma instalacao anterior: vira copia real
    mkdir -p "$DEST"
    # copia tudo menos o runtime local (.venv) e caches
    tar -C "$SRC" --exclude=.venv --exclude=__pycache__ -cf - . | tar -C "$DEST" -xf -
    PRINCIPAL="$DEST"
    echo "[ok] $SKILL_NAME instalada em $DEST"
    setup "$DEST"
  elif [ -e "$DEST" ] && [ ! -L "$DEST" ]; then
    # copia real de outra instalacao: atualiza no lugar em vez de apagar
    tar -C "$SRC" --exclude=.venv --exclude=__pycache__ -cf - . | tar -C "$DEST" -xf -
    echo "[ok] $SKILL_NAME atualizada em $DEST"
    setup "$DEST"
  else
    [ -L "$DEST" ] && rm "$DEST"
    if ln -s "$PRINCIPAL" "$DEST" 2>/dev/null && [ -f "$DEST/SKILL.md" ]; then
      echo "[ok] $DEST → $PRINCIPAL (link)"
    else
      rm -f "$DEST" 2>/dev/null || true
      mkdir -p "$DEST"
      tar -C "$SRC" --exclude=.venv --exclude=__pycache__ -cf - . | tar -C "$DEST" -xf -
      echo "[ok] $SKILL_NAME copiada em $DEST (link indisponivel)"
      setup "$DEST"
    fi
  fi
done
