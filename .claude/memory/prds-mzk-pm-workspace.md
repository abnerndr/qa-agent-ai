---
name: prds-mzk-pm-workspace
description: "PRDs das tasks MZK ficam em pyxys-inteligencia-digital/mzk-pm-workspace/artefatos/prds, acesso por SSH"
metadata:
  type: reference
---

PRDs das tasks do Mundo ZeroKM: https://github.com/pyxys-inteligencia-digital/mzk-pm-workspace/tree/main/artefatos/prds (repo privado).

- A descrição da task no Slack traz o caminho do PRD; às vezes o link completo, às vezes só o caminho/nome → completar com a URL base acima.
- Critérios de aceite: na task; se não tiver, no PRD.
- Todo dev que usa o agente de QA precisa de chave SSH com acesso à org `pyxys-inteligencia-digital`.
- A skill busca com `scripts/buscar_prd.sh` (ver ADR-003).
