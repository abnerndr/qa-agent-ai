---
name: relatorio-qa-enxuto
description: "Relatório de QA deve ser curto e legível: poucas evidências por caso, asserts objetivos, resumo de uma linha"
metadata:
  type: feedback
---

Abner achou o relatório da skill `qa-validacao-tasks` extenso e difícil de ler, com evidências desnecessárias, e pediu mais consistência e qualidade nos testes (2026-10-07). Execuções anteriores tinham 19–24 casos, 160–180 evidências e PDF de 82 páginas/18 MB.

**Why:** o PDF serve para o dev/PM decidir rápido; volume de evidência esconde os achados e não aumenta a confiança.

**How to apply:**
- PDF enxuto por padrão: resumo por critério → achados (divergentes/pendentes) → tabela de casos com uma linha → só evidências `--destaque`. `--completo` só quando ele pedir.
- Todo caso com `--resumo` de uma linha (esperado × observado) e 1 destaque (máx. 2).
- Seguir o orçamento de evidências do SKILL.md; exploração roda sem `--caso`.
- Cada caso com assert verificado pelo script (`assert_*` / `--grep`), esperado com valor concreto, ~12 casos no máximo.
- Divergência reproduzida 2x antes de registrar.
- Relacionado: [[relatorio-pdf-execucao-qa]].
