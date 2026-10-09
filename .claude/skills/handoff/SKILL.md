---
name: handoff
description: Atualiza o handoff.md do Work OS do Abner (assistente de QA) para que um agente novo ou um terceiro entenda o estado do projeto sem perguntar nada, e registra a sessão em docs/session-log.md. Use ao fim de uma sessão de trabalho, antes de trocar de agente/ferramenta, antes de uma apresentação (Demoday), ou quando o usuário disser "handoff", "/handoff", "passa o bastão", "atualiza o handoff" ou "fecha a sessão".
---

# Handoff do Work OS (agente de QA)

Objetivo: deixar `handoff.md` (raiz do projeto) fiel ao estado **atual** do repositório e registrar a sessão em `docs/session-log.md`. Quem ler só o handoff tem que saber o que existe, o que mudou, o que está em aberto e por onde continuar.

## Regras

- Só escreva o que dá para verificar no repositório (arquivos, `git log`, ADRs, memórias). Nada de métrica, prazo ou status inventado. O que não tiver como confirmar vira pergunta ao Abner ou fica marcado como `[a confirmar]`.
- Não apague nem renomeie arquivos. O handoff é reescrito com Edit/Write, nunca com `>` (o hook `guard.sh` bloqueia redirecionamentos em arquivos protegidos).
- Não exponha dado sensível (tokens, Basic Auth do staging, dados de cliente). Cite onde fica, não o valor.
- Commit só com o ok do Abner, seguindo o padrão de mensagem do histórico (`tipo(escopo): resumo` em pt-BR).

## Passo 1: levantar o estado

Leia, nesta ordem:

1. `handoff.md` atual, para saber o que já estava registrado e até qual commit.
2. `git log --format='%h %ad %s' --date=short` e `git status --short`: commits novos desde o último registrado no handoff e o que está pendente.
3. `README.md` e `CLAUDE.md`.
4. `.claude/memory/MEMORY.md` e `.claude/memory/adr-index.md`. Abra os ADRs novos.
5. `.claude/skills/*/SKILL.md` (cabeçalho e passos) e `ls` de `scripts/`.
6. `tasks/tasks-PRDSI1.md` (checkboxes), `docs/decision-log.md`, `docs/session-log.md`, `outputs/qa/`.

## Passo 2: reescrever o `handoff.md`

Mantenha estas seções, nesta ordem. Atualize o conteúdo; não acumule texto velho.

1. **Cabeçalho**: para que serve o arquivo, ordem de leitura e data/commit da última atualização.
2. **O que é este projeto**: 1 parágrafo.
3. **Estado atual em uma tela**: o que funciona hoje, o que está em aberto, próximo passo.
4. **Estrutura**: tabela das camadas (pasta → papel).
5. **Histórico real**: tabela de commits agrupados por marco (não precisa de um por linha quando vários tratam do mesmo assunto).
6. **Decisões (ADRs)**: uma linha por ADR, com o que mudou.
7. **Skills**: o que cada skill faz, scripts e como instalar.
8. **Memória**: contagem por tipo (`user`, `feedback`, `project`, `reference`) e apontador para o `MEMORY.md`.
9. **PRD e tasks**: fase, o que já foi coberto, divergências entre o PRD e o que foi construído.
10. **Hooks**: o que cada um faz.
11. **Particularidades de ambiente**.
12. **Regras que continuam valendo**: resumo do CLAUDE.md.
13. **Por onde continuar**: lista curta e ordenada.

## Passo 3: registrar a sessão

Adicione uma entrada no fim de `docs/session-log.md`:

```markdown
## AAAA-MM-DD — <título curto>
<o que foi feito, o que foi decidido, o que ficou em aberto; 3–6 linhas>
```

Se a sessão tomou uma decisão estrutural sem ADR, ou revelou fato/preferência sem memória, avise o Abner e proponha criar (regras do CLAUDE.md).

## Passo 4: conferir e reportar

- Toda afirmação do handoff bate com um arquivo ou commit?
- Contagens (memórias por tipo, ADRs, commits) conferem com `ls` e `git log`?
- Responda ao Abner com o que mudou no handoff, o que ficou `[a confirmar]` e se quer commitar.
