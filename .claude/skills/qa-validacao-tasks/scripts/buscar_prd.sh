#!/usr/bin/env bash
# scripts/buscar_prd.sh — baixa um PRD do mzk-pm-workspace (via SSH) e imprime o caminho local.
#
# Uso:
#   buscar_prd.sh --check                 # só confere o acesso SSH ao repositório
#   buscar_prd.sh <url|caminho|nome>      # imprime o caminho local do PRD
#
# Aceita:
#   - link do GitHub (…/mzk-pm-workspace/tree/main/artefatos/prds/x ou …/blob/main/…/x.md)
#   - caminho a partir da raiz do repo (artefatos/prds/x.md)
#   - caminho/nome relativo a artefatos/prds (x.md, pasta/x.md, x)
#
# Mantém um clone raso e esparso (só artefatos/) em
# ${XDG_CACHE_HOME:-~/.cache}/qa-validacao-tasks/mzk-pm-workspace e faz pull a cada chamada.
# Exige chave SSH com acesso à org pyxys-inteligencia-digital no GitHub.
#
# Saída: caminho(s) absoluto(s) no stdout. Pasta → lista os arquivos dela.
# Código 2: PRD não encontrado (candidatos parecidos vão no stderr).

set -euo pipefail

REPO_SSH="git@github.com:pyxys-inteligencia-digital/mzk-pm-workspace.git"
PRDS_DIR="artefatos/prds"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/qa-validacao-tasks/mzk-pm-workspace"

erro_ssh() {
  echo "[erro] sem acesso SSH a $REPO_SSH" >&2
  echo "       Confira se sua chave SSH está no GitHub e se você tem acesso à org" >&2
  echo "       pyxys-inteligencia-digital: ssh -T git@github.com" >&2
  exit 1
}

[ $# -ge 1 ] || { sed -n '4,8p' "$0" >&2; exit 1; }

if [ "$1" = "--check" ]; then
  GIT_SSH_COMMAND="ssh -o BatchMode=yes" git ls-remote --heads "$REPO_SSH" >/dev/null 2>&1 || erro_ssh
  echo "[ok] acesso SSH ao mzk-pm-workspace"
  exit 0
fi

export GIT_SSH_COMMAND="ssh -o BatchMode=yes"
if [ -d "$CACHE/.git" ]; then
  git -C "$CACHE" pull --quiet --ff-only >/dev/null 2>&1 \
    || echo "[aviso] pull falhou, usando a cópia local do PRD (pode estar desatualizada)" >&2
else
  mkdir -p "$(dirname "$CACHE")"
  git clone --quiet --depth 1 --filter=blob:none --sparse "$REPO_SSH" "$CACHE" 2>/dev/null || erro_ssh
  git -C "$CACHE" sparse-checkout set artefatos
fi

# Normaliza a entrada para um caminho relativo à raiz do repo.
ref="$1"
ref="${ref%%\?*}"; ref="${ref%%#*}"; ref="${ref%/}"
ref="$(printf '%b' "${ref//%/\\x}")"   # decodifica %20 etc.
case "$ref" in
  http*://github.com/*/mzk-pm-workspace/tree/*|http*://github.com/*/mzk-pm-workspace/blob/*)
    rest="${ref#*/mzk-pm-workspace/}"; rest="${rest#*/}"   # tira "tree|blob"
    branch="${rest%%/*}"; rel="${rest#*/}"
    [ "$branch" = "main" ] || echo "[aviso] link aponta para '$branch'; usando main" >&2 ;;
  http*://*)
    echo "[erro] link não é do mzk-pm-workspace: $ref" >&2; exit 1 ;;
  artefatos/*) rel="$ref" ;;
  *) rel="$PRDS_DIR/${ref#/}" ;;
esac

alvo="$CACHE/$rel"
for c in "$alvo" "$alvo.md"; do
  if [ -f "$c" ]; then echo "$c"; exit 0; fi
  if [ -d "$c" ]; then find "$c" -type f -name '*.md' | sort; exit 0; fi
done

nome="$(basename "$rel")"; nome="${nome%.md}"
echo "[erro] PRD não encontrado: $rel" >&2
echo "       candidatos em $PRDS_DIR com '$nome' no nome:" >&2
find "$CACHE/$PRDS_DIR" -iname "*$nome*" 2>/dev/null | sed "s|^$CACHE/|         |" | head -10 >&2
exit 2
