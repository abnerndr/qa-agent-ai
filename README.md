# Abner André Ananias — Assistente Pessoal (Work OS)

Mapa deste projeto. Ponto de partida de toda sessão nova.

## Objetivo atual
Estruturar o Work OS pessoal e preparar as bases do assistente de QA — apoiar o dev a testar features, fixes, bugfixes e refactors, gerando evidências (prints, vídeos de navegador).

## Como navegar
- `CLAUDE.md` — quem sou eu, minhas regras e limites (lido automaticamente em toda sessão)
- `docs/` — decisões em aberto, log de decisões, log de sessões, referência operacional
- `knowledge/` — fontes e material de apoio, organizados por nível de confiança
- `.claude/skills/` — procedimentos que se repetem
- `.claude/hooks/` — travas automáticas
- `.claude/adr/` — decisões estruturais, com alternativas consideradas
- `.claude/memory/` — conhecimento acumulado ao longo do tempo
- `tools/` — scripts e checklists de verificação
- `outputs/` — entregas finais

## Como começar uma sessão
Abra o Claude Code nesta pasta. O CLAUDE.md é lido automaticamente. Para uma decisão nova, comece por `docs/runbooks/como-registrar-uma-decisao.md`.

## Skills

### Instalar a skill `qa-validacao-tasks`

Essa skill vive na conta do Claude (Cowork), não no repositório — por isso o projeto mantém uma cópia versionada do `SKILL.md` e um script que a grava em `.claude/skills/`.

```bash
# instala todas as skills conhecidas pelo script
./tools/scripts/install-skill.sh

# instala só essa skill
./tools/scripts/install-skill.sh qa-validacao-tasks

# lista as skills que o script sabe instalar
./tools/scripts/install-skill.sh --list
```

O script grava `.claude/skills/qa-validacao-tasks/SKILL.md`. A partir daí o Claude Code, rodando nesta pasta, já reconhece a skill sem depender de sync externo.

### Usar a skill `qa-validacao-tasks`

Cole o texto da task (geralmente uma mensagem corrida de Slack, com critérios de aceite misturados a contexto) e peça para validar — não precisa mencionar "Playwright" ou "teste" explicitamente, frases como "confere se isso está pronto" ou "monta o QA gate" já acionam a skill. Também dá para chamar direto:

```
/qa-validacao-tasks
```

A skill entrega um **plano de teste** (não executa nada nem declara aprovado/reprovado):
1. Extrai os critérios de aceite verificáveis do texto da task, perguntando antes de seguir se algum critério estiver ambíguo.
2. Mapeia cada critério em casos de teste — UI (Playwright) quando o critério é algo que se vê/clica, API (requisição HTTP) quando é comportamento de backend.
3. Cobre além do caminho feliz (erro esperado, campo vazio, input inválido, permissão negada).
4. Entrega tudo na tabela `Critério | Caso de teste | Tipo (UI/API) | Passos | Resultado esperado`, com os edge cases listados à parte.
