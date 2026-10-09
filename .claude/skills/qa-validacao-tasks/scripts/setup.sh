#!/usr/bin/env bash
# scripts/setup.sh — prepara o runtime de captura de evidências da skill.
#
# Cria <skill>/.venv com Playwright para Python e baixa o Chromium (reaproveita
# o cache em ~/.cache/ms-playwright se a versão já estiver lá). Idempotente:
# rodar de novo só atualiza o Playwright.
#
# Usa uv quando disponível; senão, python3 -m venv (exige o pacote
# python3-venv no Debian/Ubuntu).

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$SKILL_DIR/.venv"

# Windows (Git Bash) usa .venv/Scripts/python.exe e "python" em vez de "python3".
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) VPY="$VENV/Scripts/python.exe" ;;
  *) VPY="$VENV/bin/python" ;;
esac
PY3=python3
command -v python3 >/dev/null 2>&1 && python3 -c 1 >/dev/null 2>&1 || PY3=python

if command -v uv >/dev/null 2>&1; then
  [ -x "$VPY" ] || uv venv --quiet "$VENV"
  uv pip install --quiet --python "$VPY" --upgrade playwright
elif "$PY3" -m venv --help >/dev/null 2>&1; then
  if [ ! -x "$VPY" ]; then
    rm -rf "$VENV"
    "$PY3" -m venv "$VENV" || {
      echo "[erro] python3 -m venv falhou. Instale uv (curl -LsSf https://astral.sh/uv/install.sh | sh)" >&2
      echo "       ou o pacote python3-venv (sudo apt install python3-venv) e rode de novo." >&2
      exit 1
    }
  fi
  "$VPY" -m pip install --quiet --upgrade playwright
else
  echo "[erro] precisa de uv ou python3 com venv" >&2
  exit 1
fi

"$VPY" -m playwright install chromium

if command -v npx >/dev/null 2>&1; then
  npx -y lighthouse@12 --version >/dev/null 2>&1 && echo "[ok] lighthouse disponivel (npx lighthouse@12)"
else
  echo "[aviso] Node/npx nao encontrado: o subcomando 'lighthouse' nao vai funcionar (o resto funciona)" >&2
fi

bash "$SKILL_DIR/scripts/buscar_prd.sh" --check 2>/dev/null \
  || echo "[aviso] sem acesso SSH ao mzk-pm-workspace: o modo automatico nao acha o PRD (o modo manual funciona)" >&2

echo "[ok] runtime pronto: $VPY $SKILL_DIR/scripts/qa_evidencias.py --help"
