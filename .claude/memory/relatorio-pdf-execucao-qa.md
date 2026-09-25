---
name: relatorio-pdf-execucao-qa
description: "Toda execução guiada de QA termina num relatório PDF com plano + evidências, inclusive de casos que falharam"
metadata:
  type: feedback
---

Ao final da execução guiada da skill `qa-validacao-tasks`, gerar um relatório PDF com o plano de teste, o status de cada caso e as evidências coletadas — **mesmo quando o caso não atinge o resultado esperado** (divergente/pendente também entra, com a evidência do que foi observado).

**Why:** Abner precisa de um artefato único e compartilhável que prove o que foi testado na task, não só o que passou. Pedido feito em 2026-09-25, validando a PR #516 (paginação) do mundo-zero-km-nextjs.

**How to apply:**
- Desde 2026-09-25 (ADR-002) quem executa e captura evidência é o agente, via `scripts/qa_evidencias.py` da skill. Continua sem veredito automático.
- Status por caso: confirmado / divergente / pendente / pulado. Sem veredito geral de "aprovado".
- Incluir as divergências PR × task e os pontos em aberto levantados no plano.
- Evidências e PDF em `${QA_REPORTS_DIR:-~/qa-relatorios}/<projeto>-<pr>/`. Para o Abner, usar `QA_REPORTS_DIR=/home/abner/www/abnerndr/qa-agent-ai/outputs/qa`.
- PDF gerado por `qa_evidencias.py relatorio` (HTML → PDF via Playwright/Chromium). Runtime em `~/.claude/skills/qa-validacao-tasks/.venv`, criado por `scripts/setup.sh` com `uv` (a máquina não tem pip nem ensurepip no sistema).
