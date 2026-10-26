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

Também tem **exploração autônoma**: sem task, varre a aplicação seguindo links e registra erros de página, JavaScript, console, rede, imagem e layout. Roda até sem IA (cron/CI).

Por baixo, é distribuído como skill no formato aberto de Agent Skills (`qa-validacao-tasks`): instruções em `SKILL.md` + runtime próprio em `scripts/`. Funciona com **qualquer IA** que leia skills (Claude Code, Codex, Gemini CLI, Cursor, Copilot, OpenCode). Racional: [ADR-002](.claude/adr/adr-002-captura-de-evidencias-pelo-agente.md) (execução pelo agente) e [ADR-004](.claude/adr/adr-004-multiagentes-multi-ia-exploracao.md) (multiagentes, qualquer IA, exploração autônoma).

### Instalar

**Pré-requisitos:** uma IA com suporte a skills (Claude Code, Codex, Gemini CLI, Cursor…), `git`, [`uv`](https://docs.astral.sh/uv/) (ou `python3-venv`) e Node/`npx` (para o Lighthouse). Funciona em Linux, macOS e WSL.

Para o **modo automático** (task pelo link do Slack), também:
- **Slack conectado à sua IA**: no Claude, claude.ai → Configurações → Conectores → Slack (ou `/mcp` no Claude Code); em outras IAs, o MCP do Slack na configuração de MCP dela.
- **Chave SSH no GitHub com acesso à org `pyxys-inteligencia-digital`**: o agente baixa o PRD do `mzk-pm-workspace` por SSH. Confira com `bash ~/.claude/skills/qa-validacao-tasks/scripts/buscar_prd.sh --check`.

**Qualquer dev, direto do GitHub** (precisa de acesso de leitura ao repo):

```bash
curl -fsSL https://raw.githubusercontent.com/abnerndr/qa-agent-ai/master/tools/scripts/install-skill-remote.sh | bash
```

**A partir deste checkout** (pra testar uma mudança local antes do push):

```bash
./tools/scripts/install-skill.sh
```

Por padrão, as duas formas instalam no Claude (`~/.claude/skills/qa-validacao-tasks/`). Para outras IAs, passe `--ia` (`claude`, `agents`, `codex`, `gemini`, `cursor`, `copilot`, `opencode` ou `todas`) ou `--dir <pasta de skills>`; no remoto, `curl … | bash -s -- --ia todas`. A primeira pasta recebe a cópia real; as outras, um link para ela. Confira com `--list` e ajuste `--dir` se a sua IA usar outra pasta. É escopo de usuário: o agente fica disponível em **qualquer projeto** e rodam `scripts/setup.sh`. Esse setup cria um `.venv` próprio com Playwright + Chromium (~115 MB na primeira vez) e pré-carrega o Lighthouse. O projeto testado não recebe nenhuma dependência. Pule o setup com `QA_SKIP_SETUP=1`.

**Windows (Claude Desktop, aba Code):** o Claude Desktop lê as skills de `C:\Users\<você>\.claude\skills\`. Copie a pasta da skill para lá e rode o setup pelo Git Bash do Windows (precisa de Python e Node no Windows):

```bash
# no WSL, a partir deste checkout
W=/mnt/c/Users/<você>/.claude/skills/qa-validacao-tasks; mkdir -p $W
tar -C .claude/skills/qa-validacao-tasks --exclude=.venv --exclude=__pycache__ -cf - . | tar -C $W -xf -
# no Git Bash do Windows
bash ~/.claude/skills/qa-validacao-tasks/scripts/setup.sh
```

Se o download do Chromium der timeout no Windows (rede bloqueando `cdn.playwright.dev`), baixe os zips pelo WSL (`playwright install --dry-run chromium` no Windows lista URLs e destinos em `%LOCALAPPDATA%\ms-playwright`), extraia e crie `INSTALLATION_COMPLETE` e `DEPENDENCIES_VALIDATED` em cada pasta.

**Atualizar:** rode o mesmo comando de novo.

**Opcional:** defina onde ficam os relatórios (padrão `~/qa-relatorios`):

```bash
echo 'export QA_REPORTS_DIR="$HOME/qa-relatorios"' >> ~/.zshrc
```

### Usar

1. Suba a aplicação na branch da task (ex.: `localhost:3000`).
2. Abra a sua IA (Claude Code, Codex, Gemini CLI…) **no repositório do projeto testado**, pra o agente conseguir ler o diff.
3. Peça a validação. O agente pergunta primeiro o **modo**:
   - **Manual** (padrão): você cola o texto da task e responde ao formulário de contexto.
   - **Exploração autônoma**: sem task. Você passa a URL e os limites, e ele procura erros sozinho.
   - **Automático**: você cola só o link da task no Slack (registro da lista, ex.: `https://pyxys.slack.com/lists/…?record_id=Rec…`, ou link de mensagem). Ele confere a conexão com o Slack, lê o registro (ou a mensagem e a thread), acha o PRD citado na task (link do GitHub ou caminho relativo a `mzk-pm-workspace/artefatos/prds`) e usa os critérios da task, ou os do PRD quando a task não tiver. Pergunta só o que faltar (onde testar, confirmar a branch).

   Exemplo no modo manual:

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

0. **Modo:** manual (texto colado) ou automático (link do Slack → task + PRD).
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

**Multiagentes:** com 6 casos ou mais e uma IA com subagentes, o agente divide os casos em lotes (por página/fluxo, até 4 agentes) que gravam na mesma execução em paralelo. O Lighthouse roda sozinho no fim, porque CPU disputada distorce a nota.

**Exploração autônoma:** `qa_evidencias.py explorar <pasta> <url>` navega só por links (GET, sem clicar em botão nem enviar formulário) e gera os casos `EX01`–`EX07`. Com `--falhar`, sai com código 1 quando acha erro, para agendar no cron/CI e chamar a IA só para triar.

**Painel:** `qa_evidencias.py painel` gera `~/qa-relatorios/index.html`, com todas as execuções agrupadas por aplicação: o que foi testado, status de cada caso, ambiente e links do PDF, das issues e do PR. Tem busca e filtro por aplicação e status. É um arquivo estático: abra no navegador, sem servidor.

**GitHub (issues e PR):** configure uma vez `~/.config/qa-agent/.env` a partir do [`.env.example`](.claude/skills/qa-validacao-tasks/.env.example) (token fine-grained com Issues e Pull requests em leitura/escrita, mapa `projeto=dono/repo`). Sem token, usa o login do `gh`. Confira com `qa_evidencias.py github check <pasta>`. Depois do relatório, o agente mostra a prévia das issues (uma por caso divergente) e só cria com o seu ok. Se você pedir a correção, ele corrige numa branch nova e abre um PR rascunho com `Closes #n`. Nada é publicado sem confirmação.

**Economia de tokens:** o script faz o trabalho pesado e devolve poucas linhas; a IA lê `status`, resumos e `grep` no log, nunca o JSON ou o HTML inteiro.

**Limites do agente:**
- só leitura, só no ambiente que você indicou
- produção só com autorização explícita
- nunca envia formulário que crie dado real (lead, pedido, pagamento) sem aprovação por caso
- não declara task aprovada/reprovada
- não cria issue, não faz push nem abre PR sem a sua confirmação

**O que versionar:** neste repo, as execuções ficam em `outputs/qa/`. Entram no git só `plano.json`, `run.json` e `relatorio.pdf`. As `evidencias/` (vídeos, prints, relatórios Lighthouse) e o `relatorio.html` ficam locais (ver `.gitignore`).

Exemplo real: validação da PR #516 do `mundo-zero-km-nextjs` em [outputs/qa/mundo-zero-km-pr-516/](outputs/qa/mundo-zero-km-pr-516/).
