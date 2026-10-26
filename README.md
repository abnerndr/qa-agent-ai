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

Sem task, ele também faz **exploração autônoma**: varre a aplicação e registra erros de página, JavaScript, console, rede, imagem e layout.

É distribuído como skill no formato aberto de Agent Skills (`qa-validacao-tasks`): instruções em `SKILL.md` + runtime próprio em `scripts/`. Funciona com **qualquer IA** que leia skills (Claude Code, Codex, Gemini CLI, Cursor, Copilot, OpenCode).

### Novidades

Na branch `project` (2026-10-25). Racional em [ADR-004](.claude/adr/adr-004-multiagentes-multi-ia-exploracao.md) e [ADR-005](.claude/adr/adr-005-painel-e-github.md).

| O quê | Como usar |
|---|---|
| **Qualquer IA** | A instalação aceita `--ia codex,cursor,kiro,…`, `--ia todas` e `--windows` (Cursor/Kiro no Windows). A skill descreve capacidades, não ferramentas de uma IA só. Veja a seção 1. |
| **Multiagentes** | Automático: com 6 casos ou mais, o agente divide o plano entre até 4 subagentes que gravam na mesma execução. No Claude, Cursor e Kiro, os lotes vão para o agente `qa-executor` (modelo mais barato). Sem subagentes, roda em sequência. |
| **Exploração autônoma** | Peça "procura erros em <url>" ou rode `qa explorar`. Navega só por links, sem IA, e gera os casos `EX01`–`EX07`. |
| **Painel** | `qa painel` gera um `index.html` com o que foi testado em cada aplicação. |
| **Issues e PR no GitHub** | Depois do relatório, o agente mostra a prévia das issues e cria com o seu ok. Se você pedir a correção, abre um PR rascunho. |
| **Menos tokens** | O script faz o trabalho pesado e devolve poucas linhas. A IA só decide e faz a triagem do que falhou. |

### 1. Instalar

A instalação copia a skill para a pasta de skills de cada IA, cria o runtime (Python + Playwright + Chromium) e, nas IAs que aceitam agentes por arquivo, instala o agente `qa-executor`, usado na execução com multiagentes. O projeto testado não recebe nenhuma dependência.

#### 1.1 Pré-requisitos

| O quê | Para quê | Conferir |
|---|---|---|
| Uma IA com suporte a skills | Claude Code, Codex, Gemini CLI, Cursor, Kiro, Copilot, OpenCode | — |
| `git` ≥ 2.25 | baixar a skill | `git --version` |
| [`uv`](https://docs.astral.sh/uv/) ou `python3-venv` | criar o runtime | `uv --version` ou `python3 -m venv --help` |
| `python3` | gerar os arquivos do agente `qa-executor` | `python3 --version` |
| Node/`npx` (opcional) | só para o Lighthouse | `npx --version` |

Funciona em Linux, macOS e WSL. No Windows nativo, veja a seção 1.5.

#### 1.2 Instalar (escolha uma forma)

**Direto do GitHub**, sem clonar o repositório (precisa de acesso de leitura ao repo):

```bash
# versão estável (master), só no Claude
curl -fsSL https://raw.githubusercontent.com/abnerndr/qa-agent-ai/master/tools/scripts/install-skill-remote.sh | bash

# versão com as novidades (branch project), em todas as IAs instaladas na máquina
curl -fsSL https://raw.githubusercontent.com/abnerndr/qa-agent-ai/project/tools/scripts/install-skill-remote.sh | QA_REF=project bash -s -- --ia todas
```

No segundo comando, o `project` da URL escolhe a versão do instalador e o `QA_REF=project`, a versão da skill. As opções depois de `bash -s --` são as mesmas da instalação local.

**A partir de um clone deste repositório** (também serve para testar uma mudança antes do push):

```bash
git clone git@github.com:abnerndr/qa-agent-ai.git && cd qa-agent-ai
git switch project                                      # opcional: versão com as novidades
./tools/scripts/install-skill.sh --ia todas
```

#### 1.3 Escolher as IAs

| Opção | O que faz |
|---|---|
| *(nenhuma)* | instala só no Claude |
| `--ia claude,codex,kiro` | instala nas IAs listadas |
| `--ia todas` | instala em toda IA cuja pasta de configuração já existe na máquina |
| `--windows` | no WSL: instala também no perfil do Windows (`C:\Users\<você>`), onde rodam Cursor, Kiro e Claude Desktop |
| `--dir <pasta>` | instala numa pasta de skills qualquer (IA que não está na tabela) |
| `--list` | mostra as IAs conhecidas e as pastas |

| `--ia` | Pasta da skill | Agente `qa-executor` |
|---|---|---|
| `claude` | `~/.claude/skills` | `~/.claude/agents/qa-executor.md` (modelo Haiku) |
| `agents` | `~/.agents/skills` (pasta compartilhada do padrão Agent Skills; o Codex também lê) | — |
| `codex` | `~/.codex/skills` | — (o Codex usa o subagente dele, com o briefing completo) |
| `gemini` | `~/.gemini/skills` | — |
| `cursor` | `~/.cursor/skills` | `~/.cursor/agents/qa-executor.md` (modelo `fast`) |
| `kiro` | `~/.kiro/skills` | `~/.kiro/agents/qa-executor.json` |
| `copilot` | `~/.copilot/skills` | — |
| `opencode` | `~/.config/opencode/skills` | — |

A primeira pasta recebe a cópia real e roda o `scripts/setup.sh`, que cria um `.venv` próprio com Playwright + Chromium (~115 MB na primeira vez) e pré-carrega o Lighthouse. As demais recebem um link para ela, sem duplicar o `.venv`. Para pular o setup, use `QA_SKIP_SETUP=1`.

Exemplos:

```bash
./tools/scripts/install-skill.sh --ia codex                 # só Codex
./tools/scripts/install-skill.sh --ia claude,cursor,kiro    # três IAs
./tools/scripts/install-skill.sh --ia todas --windows       # WSL + Windows (Cursor/Kiro no Windows)
```

#### 1.4 Conferir

```bash
SK=~/.claude/skills/qa-validacao-tasks            # ou a pasta da sua IA
"$SK/.venv/bin/python" "$SK/scripts/qa_evidencias.py" --help | head -3
```

Depois, **abra uma sessão nova da IA**: as skills são carregadas no início da sessão. Peça algo como "procura erros em http://localhost:3000" e confira se ela aciona a skill. No Claude Code, `/qa-validacao-tasks` chama direto.

#### 1.5 Windows (Cursor, Kiro, Claude Desktop)

Cursor, Kiro e Claude Desktop instalados no Windows leem as skills do perfil do Windows (`C:\Users\<você>\.<ia>\skills`), não do WSL.

1. No WSL, rode o instalador com `--windows`. Ele copia a skill e o agente para o perfil do Windows (cópia, porque o Windows não segue link do WSL):
   ```bash
   ./tools/scripts/install-skill.sh --ia todas --windows
   ```
2. Se ele avisar "sem runtime no lado Windows", crie o runtime uma vez pelo **Git Bash do Windows** (precisa de Python e Node instalados no Windows):
   ```bash
   bash ~/.claude/skills/qa-validacao-tasks/scripts/setup.sh
   ```
   Todas as cópias do Windows usam esse runtime: a skill procura a primeira instalação que tem `.venv`.
3. Se a IA abrir o projeto **dentro do WSL** (Cursor com WSL remoto), ela usa a instalação do WSL e o passo 2 não é necessário.

Se o download do Chromium der timeout no Windows (rede bloqueando `cdn.playwright.dev`), baixe os zips pelo WSL (`playwright install --dry-run chromium` no Windows lista URLs e destinos em `%LOCALAPPDATA%\ms-playwright`), extraia e crie `INSTALLATION_COMPLETE` e `DEPENDENCIES_VALIDATED` em cada pasta.

#### 1.6 Atualizar e desinstalar

- **Atualizar:** rode o mesmo comando de instalação de novo. O `.venv` e a configuração (`~/.config/qa-agent/.env`) são mantidos.
- **Desinstalar:** apague `qa-validacao-tasks` das pastas de skills (`~/.<ia>/skills/`) e o `qa-executor.*` das pastas de agentes (`~/.<ia>/agents/`). Os relatórios em `~/qa-relatorios` e o `.env` ficam, até você apagar.

#### 1.7 Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| A IA não aciona a skill | Sessão aberta antes da instalação: abra uma nova. Confira se a pasta da sua IA está na tabela da seção 1.3; se não estiver, use `--dir`. |
| `python3 -m venv falhou` | Instale `uv` (`curl -LsSf https://astral.sh/uv/install.sh \| sh`) ou `sudo apt install python3-venv` e rode de novo. |
| `[aviso] Node/npx nao encontrado` | Só o Lighthouse fica indisponível. Instale o Node se precisar dele. |
| `[aviso] sem acesso SSH ao mzk-pm-workspace` | Só afeta o modo automático da PYXYS (seção 2.3). |
| O agente `qa-executor` não aparece no Kiro | O arquivo segue o formato JSON dos agentes que já existem em `~/.kiro/agents`, mas não foi validado no Kiro IDE. Sem ele, a skill despacha os lotes com o briefing completo. |

### 2. Configurar

O agente funciona sem configurar nada além da instalação. Cada item abaixo liga um recurso opcional.

Para rodar os comandos à mão, defina o atalho `qa` (troque `~/.claude` pela pasta da sua IA, se for outra):

```bash
SK=~/.claude/skills/qa-validacao-tasks
qa() { "$SK/.venv/bin/python" "$SK/scripts/qa_evidencias.py" "$@"; }
```

#### 2.1 Pasta dos relatórios (opcional)

Padrão: `~/qa-relatorios`. Cada execução vira `<pasta>/<projeto>-<pr>/` e o painel fica em `<pasta>/index.html`.

```bash
echo 'export QA_REPORTS_DIR="$HOME/qa-relatorios"' >> ~/.zshrc   # ou ~/.bashrc
```

#### 2.2 GitHub: issues e PR (opcional)

1. **Crie o arquivo de configuração** a partir do exemplo. Ele fica fora da skill e de qualquer repositório:

   ```bash
   mkdir -p ~/.config/qa-agent
   cp "$SK/.env.example" ~/.config/qa-agent/.env
   chmod 600 ~/.config/qa-agent/.env
   ```

2. **Gere um token fine-grained** em GitHub → Settings → Developer settings → [Fine-grained tokens](https://github.com/settings/personal-access-tokens/new):
   - *Resource owner*: você ou a org dos projetos.
   - *Repository access*: **Only select repositories**, só os que o agente pode tocar.
   - *Permissions → Repository*: **Issues: Read and write**, **Pull requests: Read and write**, **Contents: Read** (Metadata: Read vem junto).
   - Se a org usa SSO: em [Settings → Tokens](https://github.com/settings/tokens), **Configure SSO → Authorize** para a org.

   Já tem o GitHub CLI logado (`gh auth status`)? Pode deixar `QA_GITHUB_TOKEN` vazio: o agente usa o token do `gh`.

3. **Preencha o `.env`:**

   ```bash
   QA_GITHUB_TOKEN=github_pat_...
   # campo "projeto" do plano = dono/repo, separados por vírgula
   QA_GITHUB_REPOS=minha-loja=minha-org/minha-loja-web,api-pedidos=minha-org/api-pedidos
   # usado quando o projeto não está no mapa (sem ele, vale o git remote da pasta atual)
   QA_GITHUB_REPO=
   QA_GITHUB_LABELS=qa-agent
   # GitHub Enterprise: QA_GITHUB_API=https://<host>/api/v3
   ```

   Variáveis exportadas no shell têm prioridade sobre o arquivo. Para usar outro arquivo, defina `QA_ENV_FILE`.

4. **Confira o acesso** (só leitura, não cria nada):

   ```bash
   qa github check <pasta de uma execução>           # repo resolvido pelo projeto da execução
   qa github check <pasta> --repo minha-org/minha-loja-web
   ```

   Esperado: `[ok] dono/repo · branch padrão main · push=True · issues=on`. Os erros dizem a causa: `401` = token inválido, `403` = sem permissão ou SSO não autorizado, `404` = token sem acesso ao repo.

Nunca cole o token no chat da IA: o agente lê do arquivo.

#### 2.3 Modo automático: task pelo Slack + PRD (opcional, PYXYS)

- **Slack conectado à sua IA**: no Claude, claude.ai → Configurações → Conectores → Slack (ou `/mcp` no Claude Code). Em outras IAs, adicione o MCP do Slack na configuração de MCP dela (ex.: `~/.codex/config.toml`, `~/.gemini/settings.json`, `~/.cursor/mcp.json`) e reinicie a sessão.
- **Chave SSH no GitHub com acesso à org `pyxys-inteligencia-digital`**: o agente baixa o PRD do `mzk-pm-workspace` por SSH. Confira com `bash "$SK/scripts/buscar_prd.sh" --check`.

#### 2.4 Exploração agendada (opcional, cron/CI)

A exploração não usa IA, então dá para agendar. Com `--falhar`, o comando sai com código 1 quando acha erro: só aí vale abrir a IA para a triagem.

```bash
# crontab -e → todo dia às 7h, no staging
0 7 * * * SK=$HOME/.claude/skills/qa-validacao-tasks; D=$HOME/qa-relatorios/explora-$(date +\%F); "$SK/.venv/bin/python" "$SK/scripts/qa_evidencias.py" explorar "$D" https://staging.exemplo.com --falhar; "$SK/.venv/bin/python" "$SK/scripts/qa_evidencias.py" relatorio "$D"; "$SK/.venv/bin/python" "$SK/scripts/qa_evidencias.py" painel
```

Em CI, o mesmo comando com `--falhar` quebra o job quando aparece erro novo.

### 3. Usar

1. Suba a aplicação na branch da task (ex.: `localhost:3000`).
2. Abra a sua IA **no repositório do projeto testado**, para o agente conseguir ler o diff.
3. Peça a validação. O agente pergunta primeiro o **modo**:
   - **Manual** (padrão): você cola o texto da task e responde ao formulário de contexto.
   - **Exploração autônoma**: sem task. Você passa a URL e os limites (páginas, profundidade, área, desktop/mobile), e ele procura erros sozinho.
   - **Automático** (PYXYS): você cola só o link da task no Slack (registro da lista, ex.: `https://pyxys.slack.com/lists/…?record_id=Rec…`, ou link de mensagem). Ele lê a task, acha o PRD citado e usa os critérios da task, ou os do PRD quando a task não tiver.

   Exemplos:

   ```
   valida essa task pra mim
   <texto da task, colado do Slack>
   PR: https://github.com/org/repo/pull/123
   o que fiz: <resumo curto>
   onde testar: localhost:3000
   ```

   ```
   procura erros em https://staging.minha-loja.com, só na área /ofertas, desktop e mobile
   ```

   Frases como "confere se isso está pronto", "monta o QA gate" ou "varre o site" já acionam o agente. No Claude Code também dá para chamar direto com `/qa-validacao-tasks`.
4. Responda o que ele perguntar (critério ambíguo, dado que falta) e decida sobre as divergências que ele apontar.
5. Dê o ok para a execução. No fim ele informa o caminho do PDF e atualiza o painel.
6. Se houver casos divergentes, ele oferece as issues: mostra a prévia, você escolhe quais criar. Se pedir a correção, ele trabalha numa branch nova, mostra o diff e só faz push e abre o PR rascunho com o seu ok.

**Ver o painel:** abra `~/qa-relatorios/index.html` no navegador (no WSL: `explorer.exe "$(wslpath -w ~/qa-relatorios/index.html)"`). Para regenerar à mão, use `qa painel`.

### Comandos do runtime

A IA chama estes comandos sozinha. Eles também funcionam à mão, com o atalho `qa` da seção 2:

| Comando | Para quê |
|---|---|
| `qa init <pasta> --plano plano.json` | cria a execução a partir do plano |
| `qa http <pasta> <url> --caso CT01 --grep '<regex>'` | status, headers e trechos do HTML do servidor |
| `qa print <pasta> <url> --caso CT02 [--mobile] [--no-js]` | screenshot |
| `qa fluxo <pasta> acoes.json --caso CT03 [--video]` | cliques, preenchimentos e asserts no navegador |
| `qa lighthouse <pasta> <url> --caso CT04` | performance, SEO, acessibilidade, boas práticas |
| `qa explorar <pasta> <url> [--prefixo-url /area] [--mobile] [--falhar]` | exploração autônoma (só links, sem IA) |
| `qa caso <pasta> CT01 --status … --resumo …` | registra o resultado de um caso |
| `qa status <pasta>` | uma linha por caso + contagem |
| `qa relatorio <pasta> [--completo]` | `relatorio.pdf` (enxuto) ou completo |
| `qa painel` | `index.html` com todas as execuções por aplicação |
| `qa github check\|issues\|pr <pasta>` | acesso ao repo, issues dos achados, PR da correção (prévia; envia só com `--criar`) |

`qa <comando> --help` mostra todas as opções.

### Como funciona

0. **Modo:** manual (texto colado), automático (link do Slack → task + PRD) ou exploração autônoma (sem task).
1. **Contexto:** pergunta o que faltar (branch/PR, o que foi feito, onde testar) e lê o diff da branch.
2. **Critérios:** extrai os critérios de aceite verificáveis do texto da task e pergunta antes de seguir se algum estiver ambíguo. Se vier só o título, avisa que os critérios foram inferidos do código.
3. **Entrega × task:** lista as divergências, ou seja, o que a entrega faz fora do escopo e o que a task pede e não foi feito.
4. **Plano:** tabela `Critério | Caso | Tipo (UI/API/Processo) | Passos | Esperado`, com os edge cases à parte.
5. **Execução** (só depois do seu ok), com `scripts/qa_evidencias.py`:
   - `http`: status, headers, canonical, trechos do HTML do servidor (sem JS)
   - `print`: screenshot desktop/mobile, com ou sem JS
   - `fluxo`: cliques e preenchimentos no navegador. **Vídeo só em interação** (formulário, botão que muda estado, clicar na paginação), nunca em página estática ou onde a funcionalidade não aparece
   - `lighthouse`: roda headless dentro do WSL/Linux, sem abrir nada no Windows. Performance só vale em build de produção
   - **Multiagentes:** com 6 casos ou mais e uma IA com subagentes, os casos são divididos em lotes por página/fluxo (até 4 agentes) que gravam na mesma execução. O Lighthouse roda sozinho no fim, porque CPU disputada distorce a nota.
6. **Relatório PDF** em `$QA_REPORTS_DIR/<projeto>-<pr>/relatorio.pdf`: resumo por critério, divergências e decisões, pontos em aberto, status de cada caso (confirmado / divergente / pendente / pulado) e as evidências, **inclusive dos casos que falharam**.
7. **Painel** atualizado com a execução.
8. **GitHub** (opcional, com o seu ok): uma issue por caso divergente; PR rascunho da correção com `Closes #n`.

**Exploração autônoma, em detalhe:** segue só links da mesma origem (GET), sem clicar em botão nem enviar formulário, e nunca abre URLs de logout/exclusão. Em cada página verifica: página ou link com erro (`EX01`), exceção JavaScript (`EX02`), `console.error` (`EX03`), requisição da própria origem com erro (`EX04`), imagem quebrada (`EX05`) e rolagem horizontal (`EX06`). Erro de domínio de terceiros vira `EX07`, informativo. Não entra em área que exige login.

**Economia de tokens:** a IA não navega no site nem lê arquivo grande. O script faz o trabalho e devolve poucas linhas, e a IA lê `status`, resumos e `grep` no log. A exploração roda sem IA, que só entra para a triagem do que falhou.

**Limites do agente:**
- só leitura, só no ambiente que você indicou
- produção só com autorização explícita
- nunca envia formulário que crie dado real (lead, pedido, pagamento) sem aprovação por caso
- não declara task aprovada/reprovada
- não cria issue, não faz push nem abre PR sem a sua confirmação; recusa enviar texto que pareça conter credencial

**O que versionar:** neste repo, as execuções ficam em `outputs/qa/`. Entram no git só `plano.json`, `run.json` e `relatorio.pdf`. As `evidencias/` (vídeos, prints, relatórios Lighthouse) e o `relatorio.html` ficam locais (ver `.gitignore`).

Exemplo real: validação da PR #516 do `mundo-zero-km-nextjs` em [outputs/qa/mundo-zero-km-pr-516/](outputs/qa/mundo-zero-km-pr-516/).
