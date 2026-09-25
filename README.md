# Abner André Ananias — Assistente Pessoal (Work OS)

Mapa deste projeto. Ponto de partida de toda sessão nova.

## Objetivo atual
Manter o Work OS pessoal e evoluir o **agente de QA**, que valida features, fixes, bugfixes e refactors contra os critérios de aceite da task, executa os testes e entrega um relatório PDF com as evidências.

## Como navegar
- `CLAUDE.md` — quem sou eu, minhas regras e limites (lido automaticamente em toda sessão)
- `docs/` — decisões em aberto, log de decisões, log de sessões, referência operacional
- `knowledge/` — fontes e material de apoio, organizados por nível de confiança
- `.claude/skills/` — procedimentos que se repetem (inclui o agente de QA, em `qa-validacao-tasks/`)
- `.claude/hooks/` — travas automáticas
- `.claude/adr/` — decisões estruturais, com alternativas consideradas
- `.claude/memory/` — conhecimento acumulado ao longo do tempo
- `tools/` — scripts e checklists de verificação
- `outputs/` — entregas finais (relatórios do agente de QA em `outputs/qa/`)

## Como começar uma sessão
Abra o Claude Code nesta pasta. O CLAUDE.md é lido automaticamente. Para uma decisão nova, comece por `docs/runbooks/como-registrar-uma-decisao.md`.

## Agente de QA

Agente que recebe uma task (do jeito que ela chega, geralmente uma mensagem de Slack), monta o plano de teste a partir dos critérios de aceite, **executa os testes sozinho** contra o ambiente que você indicar e entrega um **relatório PDF com as evidências**: prints, vídeos, respostas HTTP e Lighthouse, incluindo o que falhou. Ele não aprova a task. Quem aprova é o dev/PM, com base no relatório.

Por baixo, é distribuído como skill do Claude Code (`qa-validacao-tasks`): instruções em `SKILL.md` + runtime próprio em `scripts/`. Racional da execução pelo agente: [ADR-002](.claude/adr/adr-002-captura-de-evidencias-pelo-agente.md).

### Instalar

**Pré-requisitos:** Claude Code, `git`, [`uv`](https://docs.astral.sh/uv/) (ou `python3-venv`) e Node/`npx` (para o Lighthouse). Funciona em Linux, macOS e WSL.

**Qualquer dev, direto do GitHub** (precisa de acesso de leitura ao repo):

```bash
curl -fsSL https://raw.githubusercontent.com/abnerndr/qa-agent-ai/master/tools/scripts/install-skill-remote.sh | bash
```

**A partir deste checkout** (pra testar uma mudança local antes do push):

```bash
./tools/scripts/install-skill.sh
```

As duas formas instalam em `~/.claude/skills/qa-validacao-tasks/` (escopo de usuário, então o agente fica disponível em **qualquer projeto** aberto no Claude Code) e rodam `scripts/setup.sh`. Esse setup cria um `.venv` próprio com Playwright + Chromium (~115 MB na primeira vez) e pré-carrega o Lighthouse. O projeto testado não recebe nenhuma dependência. Pule o setup com `QA_SKIP_SETUP=1`.

**Atualizar:** rode o mesmo comando de novo.

**Opcional:** defina onde ficam os relatórios (padrão `~/qa-relatorios`):

```bash
echo 'export QA_REPORTS_DIR="$HOME/qa-relatorios"' >> ~/.zshrc
```

### Usar

1. Suba a aplicação na branch da task (ex.: `localhost:3000`).
2. Abra o Claude Code **no repositório do projeto testado**, pra o agente conseguir ler o diff.
3. Cole a task e peça a validação, com o contexto que tiver:

   ```
   valida essa task pra mim
   <texto da task, colado do Slack>
   PR: https://github.com/org/repo/pull/123
   o que fiz: <resumo curto>
   onde testar: localhost:3000
   ```

   Frases como "confere se isso está pronto" ou "monta o QA gate" já acionam o agente. Também dá pra chamar direto com `/qa-validacao-tasks`.
4. Responda o que ele perguntar (critério ambíguo, dado que falta) e decida sobre as divergências que ele apontar.
5. Dê o ok pra execução. No final ele informa o caminho do PDF.

### Como funciona

1. **Contexto:** pergunta o que faltar (branch/PR, o que foi feito, onde testar) e lê o diff da branch.
2. **Critérios:** extrai os critérios de aceite verificáveis do texto da task e pergunta antes de seguir se algum estiver ambíguo. Se vier só o título, avisa que os critérios foram inferidos do código.
3. **Entrega × task:** lista as divergências, ou seja, o que a entrega faz fora do escopo e o que a task pede e não foi feito.
4. **Plano:** tabela `Critério | Caso | Tipo (UI/API/Processo) | Passos | Esperado`, com os edge cases à parte.
5. **Execução** (só depois do seu ok): roda os casos com `scripts/qa_evidencias.py`:
   - `http`: status, headers, canonical, trechos do HTML do servidor (sem JS)
   - `print`: screenshot desktop/mobile, com ou sem JS
   - `fluxo`: cliques e preenchimentos no navegador. **Vídeo só em interação** (formulário, botão que muda estado, clicar na paginação), nunca em página estática ou onde a funcionalidade não aparece
   - `lighthouse`: performance, SEO, acessibilidade e boas práticas. Roda headless, dentro do WSL/Linux, sem abrir nada no Windows. Performance só vale em build de produção
6. **Relatório PDF** em `$QA_REPORTS_DIR/<projeto>-<pr>/relatorio.pdf`: resumo por critério, divergências e decisões, pontos em aberto, status de cada caso (confirmado / divergente / pendente / pulado) e as evidências, **inclusive dos casos que falharam**.

**Limites do agente:**
- só leitura, só no ambiente que você indicou
- produção só com autorização explícita
- nunca envia formulário que crie dado real (lead, pedido, pagamento) sem aprovação por caso
- não declara task aprovada/reprovada

**O que versionar:** neste repo, as execuções ficam em `outputs/qa/`. Entram no git só `plano.json`, `run.json` e `relatorio.pdf`. As `evidencias/` (vídeos, prints, relatórios Lighthouse) e o `relatorio.html` ficam locais (ver `.gitignore`).

Exemplo real: validação da PR #516 do `mundo-zero-km-nextjs` em [outputs/qa/mundo-zero-km-pr-516/](outputs/qa/mundo-zero-km-pr-516/).
