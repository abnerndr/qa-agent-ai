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
# duplicar o .venv. Onde link nao funciona, copia e roda o setup de novo.
# Pule o setup com QA_SKIP_SETUP=1.
#
# Se a skill tiver agents/<agente>.md (ex.: qa-executor, usado na execucao
# com multiagentes), o agente e instalado no formato de cada IA que suporta
# agentes por arquivo: Claude Code e Cursor (.md) e Kiro (.json).
#
# No WSL, --windows instala tambem no perfil do Windows (C:\Users\<voce>),
# onde rodam Cursor, Kiro e Claude Desktop. La e sempre copia (o Windows nao
# segue link do WSL) e o runtime e o .venv que ja existir no lado Windows.
#
# Uso:
#   ./tools/scripts/install-skill.sh                          # qa-validacao-tasks no Claude
#   ./tools/scripts/install-skill.sh --ia claude,codex,kiro   # em varias IAs
#   ./tools/scripts/install-skill.sh --ia todas               # em toda IA instalada nesta maquina
#   ./tools/scripts/install-skill.sh --ia todas --windows     # idem, e tambem no lado Windows (WSL)
#   ./tools/scripts/install-skill.sh --dir ~/minha-ia/skills  # numa pasta qualquer
#   ./tools/scripts/install-skill.sh <nome> [--ia ...]        # outra skill
#   ./tools/scripts/install-skill.sh --list                   # lista skills e IAs conhecidas

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_DIR="$ROOT_DIR/.claude/skills"

# ia:pasta de skills relativa ao HOME. "agents" e a pasta compartilhada do padrao Agent Skills.
IAS="claude:.claude/skills
agents:.agents/skills
codex:.codex/skills
gemini:.gemini/skills
cursor:.cursor/skills
kiro:.kiro/skills
copilot:.copilot/skills
opencode:.config/opencode/skills"

SKILL_NAME="qa-validacao-tasks"
ALVOS=()        # "ia|pasta de skills"
IA_LISTA="claude"
WINDOWS=0

while [ $# -gt 0 ]; do
  case "$1" in
    --list)
      echo "skills:"; ls -1 "$SKILLS_DIR" | sed 's/^/  /'
      echo "ias (--ia):"; echo "$IAS" | sed 's/^/  /; s/:/ → ~\//'
      exit 0 ;;
    --ia) IA_LISTA="$2"; shift 2 ;;
    --dir) ALVOS+=("dir|$2"); IA_LISTA=""; shift 2 ;;
    --windows) WINDOWS=1; shift ;;
    -*) echo "[erro] opcao desconhecida: $1" >&2; exit 1 ;;
    *) SKILL_NAME="$1"; shift ;;
  esac
done

SRC="$SKILLS_DIR/$SKILL_NAME"
if [ ! -f "$SRC/SKILL.md" ]; then
  echo "[erro] skill '$SKILL_NAME' nao encontrada em $SKILLS_DIR" >&2
  exit 1
fi

# alvos de um HOME: as IAs pedidas, ou (todas) as que ja tem pasta de configuracao nele
alvos_do_home() {
  local home="$1" ia rel
  if [ "$IA_LISTA" = "todas" ]; then
    while IFS=: read -r ia rel; do
      [ -d "$home/$(dirname "$rel")" ] && echo "$ia|$home/$rel"
    done <<< "$IAS"
  elif [ -n "$IA_LISTA" ]; then
    for ia in ${IA_LISTA//,/ }; do
      rel="$(echo "$IAS" | awk -F: -v ia="$ia" '$1 == ia { print $2 }')"
      [ -n "$rel" ] || { echo "[erro] IA desconhecida: $ia (veja --list ou use --dir)" >&2; exit 1; }
      echo "$ia|$home/$rel"
    done
  fi
}

while IFS= read -r linha; do [ -n "$linha" ] && ALVOS+=("$linha"); done < <(alvos_do_home "$HOME")
[ ${#ALVOS[@]} -gt 0 ] || { echo "[erro] nenhuma pasta de destino" >&2; exit 1; }

WIN_HOME=""
if [ "$WINDOWS" = "1" ]; then
  command -v wslpath >/dev/null 2>&1 || { echo "[erro] --windows so funciona dentro do WSL" >&2; exit 1; }
  WIN_HOME="$(wslpath "$(cmd.exe /c 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r')")"
  [ -d "$WIN_HOME" ] || { echo "[erro] perfil do Windows nao encontrado" >&2; exit 1; }
fi

setup() {
  if [ -f "$1/scripts/setup.sh" ] && [ "${QA_SKIP_SETUP:-0}" != "1" ]; then
    echo "[info] preparando runtime de evidencias (Playwright + Chromium) em $1 ..."
    bash "$1/scripts/setup.sh"
  fi
}

copiar() {  # copia tudo menos o runtime local (.venv) e caches; preserva o .venv que ja existir
  mkdir -p "$1"
  tar -C "$SRC" --exclude=.venv --exclude=__pycache__ -cf - . | tar -C "$1" -xf -
}

# agents/<nome>.md da skill → formato de cada IA que define agentes por arquivo
instalar_agentes() {
  local ia="$1" home="$2" arq nome
  [ -d "$SRC/agents" ] || return 0
  for arq in "$SRC"/agents/*.md; do
    [ -f "$arq" ] || continue
    nome="$(basename "$arq" .md)"
    case "$ia" in
      claude|cursor|kiro) ;;
      *) continue ;;
    esac
    mkdir -p "$home/.$ia/agents"
    python3 - "$ia" "$nome" "$arq" "$home/.$ia/agents" <<'PY'
import json, sys
from pathlib import Path
ia, nome, origem, destino = sys.argv[1:]
corpo = Path(origem).read_text(encoding="utf-8")
descricao = ("Executa um lote de casos de teste já aprovados da skill qa-validacao-tasks e registra o "
             "resultado de cada caso. Use só quando o orquestrador da skill despachar um lote.")
if ia == "kiro":
    agente = {"name": nome, "description": descricao, "prompt": corpo,
              "tools": ["execute_bash", "fs_read", "fs_write", "grep", "glob"],
              "allowedTools": ["fs_read", "grep", "glob"], "resources": []}
    Path(destino, f"{nome}.json").write_text(json.dumps(agente, ensure_ascii=False, indent=2), encoding="utf-8")
else:
    # modelo mais barato: o lote e execucao mecanica de um plano ja aprovado
    extra = "tools: Bash, Read, Grep, Glob, Write\nmodel: haiku" if ia == "claude" else "model: fast"
    Path(destino, f"{nome}.md").write_text(
        f"---\nname: {nome}\ndescription: {descricao}\n{extra}\n---\n\n{corpo}", encoding="utf-8")
PY
    echo "[ok] agente $nome → $home/.$ia/agents"
  done
}

PRINCIPAL=""
for alvo in "${ALVOS[@]}"; do
  ia="${alvo%%|*}"; pasta="${alvo#*|}"
  DEST="$pasta/$SKILL_NAME"
  mkdir -p "$pasta"
  if [ -z "$PRINCIPAL" ]; then
    [ -L "$DEST" ] && rm "$DEST"   # era link de uma instalacao anterior: vira copia real
    copiar "$DEST"
    PRINCIPAL="$DEST"
    echo "[ok] $SKILL_NAME instalada em $DEST"
    setup "$DEST"
  elif [ -e "$DEST" ] && [ ! -L "$DEST" ]; then
    copiar "$DEST"   # copia real de outra instalacao: atualiza no lugar em vez de apagar
    echo "[ok] $SKILL_NAME atualizada em $DEST"
    setup "$DEST"
  else
    [ -L "$DEST" ] && rm "$DEST"
    if ln -s "$PRINCIPAL" "$DEST" 2>/dev/null && [ -f "$DEST/SKILL.md" ]; then
      echo "[ok] $DEST → $PRINCIPAL (link)"
    else
      rm -f "$DEST" 2>/dev/null || true
      copiar "$DEST"
      echo "[ok] $SKILL_NAME copiada em $DEST (link indisponivel)"
      setup "$DEST"
    fi
  fi
  instalar_agentes "$ia" "$HOME"
done

if [ -n "$WIN_HOME" ]; then
  while IFS= read -r alvo; do
    [ -n "$alvo" ] || continue
    ia="${alvo%%|*}"; DEST="${alvo#*|}/$SKILL_NAME"
    [ -L "$DEST" ] && rm "$DEST"
    copiar "$DEST"
    echo "[ok] $SKILL_NAME copiada no Windows: $DEST"
    instalar_agentes "$ia" "$WIN_HOME"
  done < <(alvos_do_home "$WIN_HOME")
  # no Windows o runtime e o .venv de qualquer copia (a SKILL.md procura a primeira que tiver)
  if ! ls "$WIN_HOME"/.*/skills/"$SKILL_NAME"/.venv/Scripts/python.exe >/dev/null 2>&1; then
    echo "[aviso] sem runtime no lado Windows: no Git Bash do Windows rode" >&2
    echo "        bash ~/.claude/skills/$SKILL_NAME/scripts/setup.sh" >&2
  fi
fi
