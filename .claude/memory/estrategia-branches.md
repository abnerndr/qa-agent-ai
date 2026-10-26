---
name: estrategia-branches
description: "pyxys_version preserva a versão PYXYS; master e pyxys_version ficam intocadas; trabalho novo vai na branch project"
metadata:
  type: project
---

Em 2026-10-25 o Abner decidiu tornar o agente de QA genérico (qualquer aplicação, não só PYXYS/Mundo ZeroKM).

- `pyxys_version`: preserva a parte específica da PYXYS; depois será levada para outro repositório.
- `master` e `pyxys_version`: devem ficar neutras — não commitar nelas.
- `project`: branch criada a partir da `master` (81f61f3) onde as próximas mudanças serão feitas.

**Why:** separar o produto genérico da customização PYXYS sem perder esta última.
**How to apply:** antes de editar/commitar, confirmar que está na `project`; nunca alterar `master` nem `pyxys_version` sem pedido explícito. Ver [[perfil-abner]].
