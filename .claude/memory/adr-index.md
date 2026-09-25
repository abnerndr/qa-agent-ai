# ADR Index — Decisões Arquiteturais

Índice de Architecture Decision Records. Todos os ADRs vivem em `.claude/adr/`.

---

## ADRs Aceitos

| ID | Título | Data | Resumo |
|---|---|---|---|
| [ADR-001](../adr/adr-001-adocao-do-work-os.md) | Adoção do Work OS Pessoal | 2026-09-03 | Estrutura completa de 10 camadas adotada nesta pasta em vez de pasta mínima ou ausência de estrutura — dá histórico de decisão, controle de confiança de fonte e travas automáticas. |
| [ADR-002](../adr/adr-002-captura-de-evidencias-pelo-agente.md) | Captura de evidências e relatório PDF pelo agente de QA | 2026-09-25 | A skill `qa-validacao-tasks` passa a executar os casos, capturar evidências (script Python + Playwright) e gerar PDF com falhas incluídas, sem veredito. Antecipa parte do V2 do PRDSI1. |

---

## ADRs Pendentes (planejados)

| ID | Título | Trigger |
|---|---|---|
| — | — | — |

---

## Convenções

- **Status possíveis:** Proposto · Em Review · Aceito · Depreciado · Substituído
- **Numeração:** sequencial, sem gaps — ADR-001, ADR-002, ...
- **Substituição:** ADR depreciado referencia o ADR que o substitui no campo Status
- **Contexto obrigatório:** todo ADR referencia o que motivou a decisão
