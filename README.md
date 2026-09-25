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

A fonte da verdade é `.claude/skills/qa-validacao-tasks/`, neste repositório: `SKILL.md` + `scripts/` (captura de evidências e relatório PDF). A instalação vai pro escopo de usuário (`~/.claude/skills/`), então a skill funciona em qualquer projeto aberto no Claude Code.

**Qualquer dev, direto do GitHub** (precisa de `git` e acesso de leitura ao repo):

```bash
curl -fsSL https://raw.githubusercontent.com/abnerndr/qa-agent-ai/master/tools/scripts/install-skill-remote.sh | bash
```

**A partir deste checkout** (pra testar mudança local antes do push):

```bash
./tools/scripts/install-skill.sh            # qa-validacao-tasks
./tools/scripts/install-skill.sh --list     # skills do repositório
```

As duas formas copiam a skill e rodam `scripts/setup.sh`, que cria `~/.claude/skills/qa-validacao-tasks/.venv` com Playwright + Chromium (~115 MB na primeira vez). Esse runtime precisa de [`uv`](https://docs.astral.sh/uv/) ou `python3-venv`. Pule o setup com `QA_SKIP_SETUP=1`. Rodar de novo atualiza a skill e o Playwright.

Opcional: defina onde ficam os relatórios (padrão `~/qa-relatorios`):

```bash
echo 'export QA_REPORTS_DIR="$HOME/qa-relatorios"' >> ~/.zshrc
```

### Usar a skill `qa-validacao-tasks`

Cole o texto da task (geralmente a mensagem do Slack, com critérios misturados a contexto) e peça pra validar. Frases como "confere se isso está pronto" ou "monta o QA gate" já acionam a skill. Também dá pra chamar direto com `/qa-validacao-tasks`.

1. **Contexto**: pergunta o que faltar (branch/PR, o que foi feito, onde testar) e lê o diff quando tem acesso ao repositório.
2. **Critérios**: extrai os critérios de aceite verificáveis e pergunta antes de seguir se algum estiver ambíguo.
3. **Entrega × task**: lista as divergências (o que a entrega faz fora do escopo, e o que falta).
4. **Plano**: tabela `Critério | Caso | Tipo (UI/API/Processo) | Passos | Esperado`, com os edge cases à parte.
5. **Execução** (depois do seu ok): o agente roda os casos no ambiente indicado e captura prints, vídeos e respostas HTTP com `scripts/qa_evidencias.py`. Só leitura, e nunca envia formulário que crie dado real sem aprovação.
6. **Relatório PDF** em `$QA_REPORTS_DIR/<projeto>-<pr>/relatorio.pdf`: resumo por critério, divergências, status e evidências de cada caso, **inclusive os que falharam**. Sem veredito: quem aprova é o dev/PM.

Racional da execução pelo agente: [ADR-002](.claude/adr/adr-002-captura-de-evidencias-pelo-agente.md).
