# ADR-001 — Adoção do Work OS Pessoal

**Status:** Aceito
**Data:** 2026-09-03
**Contexto:** Sessão de setup inicial do Claude Code nesta pasta, parte do treinamento de profissionais da PYXYS no uso do Claude Code como assistente pessoal.

---

## Decisão

Adotar a estrutura completa de Work OS nesta pasta: mapa (`README.md`), memória ativa (`CLAUDE.md`), decisão (`docs/`), evidência (`knowledge/`), reuso (`.claude/skills/`), guardrail (`.claude/hooks/`), verificação (`tools/`+`harnesses/`), entrega (`outputs/`), decisão arquitetural (`.claude/adr/`) e memória acumulada (`.claude/memory/`).

---

## Contexto

Pasta criada para uso pessoal de Claude Code na PYXYS, sem estrutura prévia. Sem um sistema assim, cada sessão nova reconstrói contexto do zero, decisões não ficam registradas, e não há separação entre fonte confiável e não verificada.

---

## Alternativas Consideradas

### 1. Pasta mínima, só README + CLAUDE.md — descartada

Resolve o mapa e a memória ativa, mas não dá histórico de decisão, controle de confiança de fonte, nem trava automática contra ação arriscada.

### 2. Seguir sem nenhuma estrutura — descartada

Custo de retrabalho crescente a cada sessão nova; nenhum registro do que já foi decidido ou por quê.

---

## Consequências

**Positivo:**
- CLAUDE.md carrega automaticamente identidade e regras em toda sessão nova.
- Decisões ficam registradas com o motivo, evitando decidir a mesma coisa duas vezes.
- Fontes ficam classificadas por confiança antes de entrar numa decisão.
- Hooks bloqueiam ações destrutivas por engano.

**Negativo / riscos aceitos:**
- Mais pastas e arquivos para manter do que uma pasta solta.
- Exige manter `.claude/memory/` e `docs/decision-log.md` atualizados — sem isso, as camadas ficam vazias e perdem utilidade.
