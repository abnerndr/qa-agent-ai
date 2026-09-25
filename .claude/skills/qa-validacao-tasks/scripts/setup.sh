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

if command -v uv >/dev/null 2>&1; then
  [ -x "$VENV/bin/python" ] || uv venv --quiet "$VENV"
  uv pip install --quiet --python "$VENV/bin/python" --upgrade playwright
elif python3 -m venv --help >/dev/null 2>&1; then
  if [ ! -x "$VENV/bin/pip" ]; then
    rm -rf "$VENV"
    python3 -m venv "$VENV" || {
      echo "[erro] python3 -m venv falhou. Instale uv (curl -LsSf https://astral.sh/uv/install.sh | sh)" >&2
      echo "       ou o pacote python3-venv (sudo apt install python3-venv) e rode de novo." >&2
      exit 1
    }
  fi
  "$VENV/bin/pip" install --quiet --upgrade playwright
else
  echo "[erro] precisa de uv ou python3 com venv" >&2
  exit 1
fi

"$VENV/bin/python" -m playwright install chromium

if command -v npx >/dev/null 2>&1; then
  npx -y lighthouse@12 --version >/dev/null 2>&1 && echo "[ok] lighthouse disponivel (npx lighthouse@12)"
else
  echo "[aviso] Node/npx nao encontrado: o subcomando 'lighthouse' nao vai funcionar (o resto funciona)" >&2
fi

echo "[ok] runtime pronto: $VENV/bin/python $SKILL_DIR/scripts/qa_evidencias.py --help"
