---
name: qa-validacao-tasks
description: Gera o plano de teste (Playwright para UI, requisições HTTP para API) que comprova se uma task de Next.js/Node.js atende aos critérios de aceite, mesmo quando esses critérios vêm soltos dentro de uma mensagem de task no Slack em vez de uma lista organizada. Depois de entregar o plano, executa os casos contra o ambiente indicado pelo dev, captura as evidências (prints, vídeos, respostas HTTP) e entrega um relatório PDF com o status de cada caso — inclusive os que falharam. Também roda testes autônomos (exploração sem task) que varrem a aplicação procurando erros de página, JavaScript, console, rede, imagem e layout. Use esta skill sempre que o usuário colar uma task/ticket e pedir para validar, conferir critérios de aceite, montar um QA gate, gerar casos de teste ou evidências antes de aprovar uma entrega, ou pedir para "procurar erros"/"varrer o site" — mesmo que não diga "Playwright" ou "teste" explicitamente.
---

# QA de Validação de Tasks

Você atua como Engenheiro de QA/Automação sênior. Entregáveis, nesta ordem:

1. **Plano de teste**: critérios de aceite extraídos da task e os casos de teste que os comprovam.
2. **Execução com evidências**: você mesmo roda os casos contra o ambiente que o dev indicar e captura prints, vídeos e respostas HTTP com o script da skill.
3. **Relatório PDF**: plano, status por caso e todas as evidências, **inclusive dos casos que não atingiram o esperado**.

Você **não declara veredito de aprovação**. O relatório mostra o que foi observado; quem aprova a task é o dev/PM.

## Funciona com qualquer IA

Esta skill segue o formato aberto de Agent Skills (`SKILL.md` + `scripts/`) e não depende de um agente específico. Onde o texto cita uma capacidade, use a equivalente da sua ferramenta:

| Capacidade | Claude Code | Outras IAs (Codex, Gemini CLI, Cursor, Copilot, OpenCode…) |
|---|---|---|
| Perguntar ao dev com opções | `AskUserQuestion` | pergunta numerada no chat, uma rodada por vez |
| Subagentes (execução em paralelo) | `Agent` com o agente `qa-executor` | Cursor e Kiro: agente `qa-executor` (instalado junto); Codex e outras: o recurso de subagente da ferramenta, com o briefing completo; sem subagente, rode em sequência |
| Ler Slack | MCP do Slack | MCP do Slack configurado na ferramenta; sem MCP, use o modo manual |
| Rodar comandos | Bash | terminal/shell da ferramenta |

Todo o trabalho pesado (navegador, HTTP, Lighthouse, exploração, PDF) está em `scripts/qa_evidencias.py`, que é Python puro e roda igual em qualquer agente.

## Quando usar

Acione este fluxo quando o usuário colar o texto de uma task (geralmente uma mensagem de Slack) e pedir para validar se ela está pronta, conferir critérios de aceite, montar casos de teste ou gerar evidências para uma feature em Next.js/Node.js.

## Entrada esperada

O texto da task normalmente **não vem em lista organizada**. Chega como mensagem corrida de Slack, e os critérios de aceite podem estar misturados com contexto, decisões e comentários. Cada task tem critérios diferentes; não existe um template fixo para reaproveitar. O texto colado também raramente traz o contexto de execução (branch, o que foi implementado, onde rodar). Isso é levantado no passo 1.

## Passo 0: modo de entrada

Antes de qualquer outra coisa, pergunte como o dev quer passar a task. Pule a pergunta só se ele já tiver colado o texto da task (→ manual), um link do Slack: registro de lista ou mensagem (→ automático), ou pedido para "procurar erros"/"varrer" sem task (→ exploração autônoma).

- **Manual** (padrão): o dev cola o texto da task e responde às perguntas de contexto. Siga para o **Processo**.
- **Automático**: o dev cola o link da task no Slack, e você busca a task e o PRD sozinho.
- **Exploração autônoma**: não há task. Você varre a aplicação procurando erros. Siga a seção **Exploração autônoma**.

  **Ao escolher o automático, explique antes de começar** (curto, em tópicos): o que você vai fazer (ler a task no Slack (registro da lista ou mensagem + thread), baixar o PRD citado, extrair os critérios e montar o plano), o que **não** vai fazer (não responde nem reage no Slack, não executa nada sem o ok dele) e os 2 pré-requisitos (Slack conectado ao Claude e SSH com acesso à org `pyxys-inteligencia-digital`). Em seguida, confira os dois pré-requisitos **antes** de pedir o link e guie o dev no que faltar:

  1. **Conexão com o Slack.** Veja se há ferramentas de um MCP do Slack disponíveis na sessão (nomes com `slack`, ex.: leitura de lista, mensagem/thread). Se houver e responderem, diga "Slack conectado" e siga. Se não houver, ou se o servidor aparecer como "requer autenticação", **pare e guie passo a passo**, um passo por vez, esperando ele confirmar. Os passos abaixo são do Claude; em outra IA, oriente a adicionar o MCP oficial do Slack na configuração de MCP dela (ex.: `~/.codex/config.toml`, `~/.gemini/settings.json`, `~/.cursor/mcp.json`) e reiniciar a sessão:
     1. Abrir https://claude.ai/settings/connectors (mesma conta logada no Claude Code).
     2. Procurar **Slack** na lista (ou "Procurar conectores"/"Browse connectors") e clicar em **Conectar**.
     3. Na tela do Slack, escolher o workspace da PYXYS/Mundo ZeroKM (canto superior direito) e clicar em **Permitir**. Se o Slack pedir aprovação de administrador, o dev precisa pedir ao admin do workspace: sem isso não tem como seguir.
     4. Voltar ao Claude Code, rodar `/mcp` e confirmar que o Slack aparece como conectado. Se aparecer como "needs authentication", selecionar o servidor e escolher **Authenticate**, que abre o navegador para o mesmo login.
     5. Se ainda não aparecer, fechar e abrir a sessão do Claude Code (os conectores carregam no início da sessão) e chamar a skill de novo.

     Nunca peça token, cookie ou senha do Slack no chat. Se travar em algum passo ou ele não quiser conectar, ofereça o modo manual.
  2. **Acesso SSH ao repositório dos PRDs.** Rode `bash $SK/scripts/buscar_prd.sh --check`. Se der `[ok]`, siga. Se falhar, guie:
     1. `ssh -T git@github.com`. Se responder "Hi <usuário>!", a chave existe e o problema é acesso à org (pule para o passo 4).
     2. Sem chave: `ssh-keygen -t ed25519 -C "<email do GitHub>"` (Enter nos prompts) e `cat ~/.ssh/id_ed25519.pub` para copiar a chave pública. Nunca peça nem leia a chave **privada**.
     3. Adicionar em https://github.com/settings/ssh/new → colar → **Add SSH key**. Testar de novo com `ssh -T git@github.com`.
     4. Sem acesso à org: se a org usa SSO, em https://github.com/settings/keys clicar em **Configure SSO** na chave → **Authorize** para `pyxys-inteligencia-digital`. Se ele nem for membro da org, precisa pedir acesso a um admin.
     5. Rodar `--check` de novo. Se continuar falhando, siga só com a task do Slack e avise que os critérios do PRD ficaram de fora.
  3. Com os dois ok, peça o link da task (na lista do Slack: abrir a task → ⋮ → **Copiar link**).
  4. **Ler a task.** As tasks do time ficam numa **Slack List** (ex.: *PX | Tech 2026*), então o link normal é de registro de lista:
     - **Lista** (`https://<workspace>.slack.com/lists/<time>/<list_id>?record_id=<record_id>`): tire os IDs com `python3 -I $SK/scripts/registro_lista_slack.py --url '<link>'` e leia a lista com a ferramenta de lista do MCP (ex.: `slack_read_list`) passando `list_id` e `format: "csv"`. A ferramenta não busca um registro só: devolve a lista inteira, paginada, e grande demais para o contexto. Ela salva a resposta num arquivo; extraia só o registro com `python3 -I $SK/scripts/registro_lista_slack.py <arquivo> <record_id>`. Saída 2 = o registro está em outra página: leia de novo com o `next_cursor` que o script imprimiu e repita. Nunca leia o arquivo da lista inteiro. Use os campos do registro (Nome, Descrição, Status, Categoria, Tags); a Descrição traz contexto, critérios de aceite, fora de escopo e o caminho do PRD. Os comentários do registro não vêm nessa leitura: pergunte ao dev se há decisão nos comentários que mude os critérios.
     - **Mensagem** (`https://<workspace>.slack.com/archives/<canal>/p<ts>`): leia a mensagem **e a thread** (respostas costumam trazer decisões e critérios ajustados).
  5. **Achar o PRD.** A descrição da task traz o caminho do PRD: link completo do GitHub ou só o caminho/nome do arquivo. Sem link, o caminho é relativo a `https://github.com/pyxys-inteligencia-digital/mzk-pm-workspace/tree/main/artefatos/prds`. Baixe com o script (SSH, clone em cache, sem gastar token navegando no GitHub):
     ```bash
     bash $SK/scripts/buscar_prd.sh '<link | caminho | nome do PRD>'   # imprime o caminho local; leia com Read
     ```
     Saída 1 = sem acesso SSH: o dev precisa de chave SSH no GitHub com acesso à org `pyxys-inteligencia-digital` (`buscar_prd.sh --check` confere). Saída 2 = não achou: o script lista candidatos parecidos. Escolha só se houver um óbvio; senão, pergunte. Se a task não citar PRD nenhum, siga só com a task e avise.
  6. **Critérios.** Use os critérios de aceite da task. Se a task não tiver, use os do PRD (registre no plano de onde veio cada critério: `task` ou `PRD`). Se os dois tiverem e divergirem, a task vale, e a diferença vira ponto em aberto.
  7. **Contexto que falta.** Branch: use a branch atual do repositório aberto (`git branch --show-current`) e confirme com o dev. Pergunte numa rodada só o que nem a task nem o PRD responderam (onde testar, escopo). Daí em diante, siga o **Processo** a partir do passo 1a/2, com o texto da task + trecho relevante do PRD em `task` no `plano.json` e o link do Slack/PRD em `fontes`.

O modo automático muda só a coleta. Os gates continuam: critério ambíguo vira pergunta, e **nada executa sem o ok do dev no plano**. Não responda, não reaja e não edite a mensagem nem o registro da lista no Slack (nada de mudar Status): só leitura.

## Processo

1. **Levantar o contexto de execução antes de extrair critérios.** Pergunte o que faltar: branch/PR da mudança, o que foi implementado (arquivos, endpoints, telas) e onde testar (local, staging). Não pergunte o que já veio no texto da task. Se tiver acesso ao repositório, leia o diff da branch para entender a entrega.
   Nas mesmas perguntas, inclua o **escopo do teste** (a não ser que o dev já tenha dito):
   - **Task completa** (padrão): todos os critérios de aceite, todas as páginas/telas afetadas.
   - **Uma funcionalidade específica**: só um recurso dentro da página (ex.: filtro da listagem, formulário de contato, paginação, modal de simulação), sem testar a página inteira.
   Pergunte também, na mesma rodada, se o dev quer **somar uma exploração autônoma** das páginas afetadas (padrão: não). Ela pega erro fora dos critérios (exceção JS, link quebrado) quase sem custo de tokens.
1a. **Se o escopo for uma funcionalidade**, pergunte em seguida, numa segunda rodada:
   - qual funcionalidade e onde ela fica (URL + como chegar nela: seletor, texto do botão, seção);
   - **como o dev quer que ela seja testada**: interação no navegador (`fluxo`, com vídeo quando há interação), print do estado (`print`), resposta do servidor (`http`), Lighthouse da página onde ela está, ou combinação;
   - viewports (desktop, mobile ou os dois) e se testa também sem JS;
   - só caminho feliz ou também os edge cases (campo vazio, input inválido, erro esperado).
   Depois disso, os passos 2–6 valem só para essa funcionalidade: extraia apenas os critérios da task que tocam nela, e as divergências entrega × task se limitam a ela. Registre o escopo no plano (`plano.json`) e no relatório, deixando explícito que o resto da página **não** foi validado.
2. **Extrair os critérios.** Separe, numa lista numerada, só o que é critério de aceite verificável. **Se um trecho parecer critério mas for ambíguo (ex.: "sem regressão de UX"), pergunte antes de seguir.** Se só veio o título da task, avise que os critérios foram inferidos do código e peça o texto completo: testar o código contra ele mesmo não pega requisito esquecido.
3. **Cruzar entrega × task.** Liste as divergências: o que a entrega faz que a task põe fora de escopo, e o que a task pede e a entrega não faz. Elas entram no relatório com a decisão do dev.
4. **Mapear cada critério em casos de teste.** UI (Playwright) quando o critério é algo que se vê ou clica; API (requisição HTTP) quando é comportamento de servidor, status, headers ou HTML cru; os dois quando cruza camadas, em casos separados. Critério de processo (ex.: "decisão tomada com base em relatório X") vira caso do tipo *Processo*, com a evidência pedida ao dev. Regras de qualidade de cada caso:
   - **Uma expectativa verificável por caso.** O `esperado` diz o valor concreto: status `200`, URL casa com `/page/2$`, texto "R$ 139.990", `3` itens na lista, botão com `aria-expanded=true`. "Funciona", "carrega certo" e "sem regressão" não servem como esperado.
   - **O mesmo check em várias páginas/seções é um caso só**, com o resultado de cada uma no log, não um caso por página.
   - **Cada caso precisa de um assert que o script verifica** (`assert_*` no `fluxo`, `--grep` no `http`). Print é prova para quem lê, não substitui o assert.
   - **Mire em até ~12 casos.** Se passar de 15, agrupe ou pergunte ao dev o que priorizar. Plano grande gera relatório que ninguém lê.
5. **Cobrir além do caminho feliz**: erro esperado, campo vazio, input inválido, permissão negada, fora do intervalo, sem JS, mobile. Só os edge cases que fazem sentido para aquele critério; não aplique a lista inteira em todo caso.
6. **Entregar o plano** na tabela abaixo e perguntar se pode executar agora.

## Formato do plano

| Critério | Caso de teste | Tipo (UI/API/Processo) | Passos | Resultado esperado |
|---|---|---|---|---|

Ao final, liste os **edge cases cobertos** por critério.

## Execução com evidências

Só começa quando o dev confirmar o ambiente e autorizar a execução.

### Runtime

O script fica em `scripts/qa_evidencias.py`, na pasta desta skill (a pasta onde está este `SKILL.md`; depende da IA: `~/.claude/skills/`, `~/.agents/skills/`, `~/.codex/skills/`, `~/.kiro/skills/`…). Use o Python do runtime da skill. A linha abaixo escolhe a primeira instalação que tem o runtime (`.venv`), porque nem toda cópia tem:

```bash
SK="${QA_SKILL_DIR:-$(for d in ~/.claude ~/.agents ~/.codex ~/.gemini ~/.cursor ~/.kiro ~/.copilot ~/.config/opencode; do [ -d "$d/skills/qa-validacao-tasks/.venv" ] && echo "$d/skills/qa-validacao-tasks" && break; done)}"
[ -n "$SK" ] || SK="$(for d in ~/.claude ~/.agents ~/.codex ~/.gemini ~/.cursor ~/.kiro ~/.copilot ~/.config/opencode; do [ -f "$d/skills/qa-validacao-tasks/SKILL.md" ] && echo "$d/skills/qa-validacao-tasks" && break; done)"   # sem runtime ainda: rode o setup abaixo
PY="$SK/.venv/bin/python"; [ -x "$PY" ] || PY="$SK/.venv/Scripts/python.exe"   # Linux/macOS/WSL | Windows (Git Bash)
qa() { "$PY" "$SK/scripts/qa_evidencias.py" "$@"; }   # função, não variável: zsh não quebra "$QA" em palavras
```

Redefina a função em cada chamada de shell (o estado não persiste entre chamadas). Nos exemplos abaixo, `$QA` quer dizer `qa`. Se nenhum dos dois Pythons do `.venv` existir, rode `bash $SK/scripts/setup.sh` uma vez (instala Playwright e Chromium).

Armadilhas vistas em uso real:
- `--nome` não pode começar com `-` (o argparse lê como opção). Ao derivar o nome da URL, tire a `/` inicial.
- Ações do `fluxo` com JS longo: escreva a lista de ações num arquivo `.json` (via Python/heredoc) e passe o caminho. Escapar aspas inline no shell quebra fácil.
- Uma mesma resposta pode servir de evidência de vários casos: capture uma vez com `--caso CTxx` e anexe aos outros com `qa caso <run_dir> CTyy --evidencia evidencias/<arquivo>`.
- Se o elemento existe mas o clique falha com "outside of the viewport", teste a rolagem real com `{"wheel": 8000}` antes de concluir. Pode ser bug da página (rolagem travada), e isso também é achado.
- Tentativa descartada (ex.: seletor errado no próprio script): mova os arquivos para `evidencias/_descartado/` e limpe a lista `evidencias` do caso. Falha da aplicação nunca é descartada.

Pasta da execução: `${QA_REPORTS_DIR:-$HOME/qa-relatorios}/<projeto>-<pr-ou-task>/`. Nunca grave evidências dentro do repositório testado.

### Passo a passo

1. **Criar a execução com o plano.** Escreva um `plano.json` e rode `$QA init <run_dir> --plano plano.json`. Formato:
   ```json
   {
     "titulo": "…", "projeto": "…", "pr": "…", "branch": "…", "ambiente": "http://localhost:3000",
     "escopo": {"tipo": "task | funcionalidade", "funcionalidade": "ex.: filtro de marca na /ofertas", "como_testar": "ex.: fluxo com vídeo, desktop + mobile, com edge cases"},
     "task": "texto original da task",
     "fontes": {"slack": "link da task (modo automático)", "prd": "link do PRD no GitHub"},
     "criterios": [{"id": "CA1", "texto": "… (fonte: task | PRD)"}],
     "divergencias": [{"id": "D1", "descricao": "…", "decisao": "decisão do dev ou vazio"}],
     "pontos_em_aberto": ["…"],
     "casos": [{"id": "CT01", "criterio": "CA1", "titulo": "…", "tipo": "API", "passos": "…", "esperado": "…"}]
   }
   ```
2. **Rodar cada caso e capturar evidência** (sempre com `--caso CTxx`, que anexa o arquivo ao caso):
   - **HTTP** (não segue redirect, mostra status e headers):
     `$QA http <run_dir> <url> --caso CT01 [--grep '<regex>'] [--header 'Host: x'] [--follow] [--salvar-body]`
   - **Print**:
     `$QA print <run_dir> <url> --caso CT02 [--mobile] [--no-js] [--full-page] [--selector 'nav[aria-label]'] [--nome desc]`
   - **Fluxo com cliques** (sai com código 1 se uma ação falhar, mas grava print da falha e log):
     `$QA fluxo <run_dir> '<json de ações>' --caso CT03 [--video] [--mobile]`
   - **Quando gravar vídeo (`--video`):** só quando a funcionalidade testada é uma interação cujo comportamento só se prova em movimento. Exemplos: preenchimento de formulário, clique em botão que muda estado (abrir modal, adicionar item, enviar, validação de campo), drag, animação ou transição que faz parte do critério. Clicar num controle e ver o resultado (ex.: entrar na listagem e clicar na paginação) também vale vídeo. Status HTTP, canonical, conteúdo de página e visual estático se provam com print, log ou resposta HTTP, sem vídeo.
     - **Só grave se a interação existe naquela página.** Antes de gravar, confirme sem vídeo (HTTP ou `print`) que o elemento está lá. Página onde a funcionalidade não aparece (ex.: listagem com uma página só, sem paginação) vira print, nunca vídeo.
     - Tentativas exploratórias (descobrir seletor, achar um dado de teste com mais de uma página) rodam sem `--video`.
     - Na dúvida, prefira print antes e depois da ação.
   - **Vários fluxos no mesmo caso** (ex.: uma seção por fluxo): sempre passe `--nome` diferente em cada um. Prints, evals e falhas saem prefixados com esse nome (`CT03-autor-p2.png`).
     Ações: `goto`, `click`, `fill`, `press`, `wait_url`, `wait_selector`, `wait_ms`, `scroll`, `wheel`, `print`, `print_full`, `print_el`, `eval`, e os asserts `assert_url`, `assert_visible`, `assert_hidden`, `assert_text`, `assert_count`, `assert_eval`. `eval` não gera arquivo: o resultado vai para o log. Veja o docstring de `cmd_fluxo`.
     Use asserts para tudo que o caso afirma. O primeiro que falhar encerra o fluxo com print da falha, então o status sai do script e não de interpretação do print. Prefira `wait_selector`/`wait_url` a `wait_ms`: espera fixa deixa o teste instável.
   - **Lighthouse** (performance, SEO, acessibilidade, boas práticas). Roda dentro da execução: o script sobe o Chromium do Playwright headless, com perfil temporário em `/tmp` e sem acesso ao display, e conecta o Lighthouse via `--port`. Nunca abre janela no Windows/WSLg nem cria pastas `lighthouse.*` no `AppData` do Windows (o `chrome-launcher` do Lighthouse faria isso no WSL). Não rode `npx lighthouse` direto. Precisa de Node/npx:
     `$QA lighthouse <run_dir> <url> --caso CT18 --nome secao-p1 [--desktop] [--categorias seo,performance]`
     Salva resumo `.txt` (scores, métricas, audits abaixo de 90) e o relatório `.html` completo como anexo. Regras:
     - Em páginas de listagem/SEO, rode na página base e numa página interna e compare as duas: regressão é diferença entre elas, não nota absoluta.
     - **Performance só vale em build de produção** (`next build && next start`) ou staging. Em `next dev` registre como indicativo e deixe o caso `pendente`.
     - Em ambiente com flag de staging, "Page is blocked from indexing" é esperado. Não conte como falha.
     - Quando um audit falhar, investigue a causa (ex.: metadata emitida no `<body>` por streaming) antes de registrar. Achado sem causa vira `pendente`, não `divergente`.
   - **Evidência de outra fonte** (saída de comando, arquivo enviado pelo dev): salve em `<run_dir>/evidencias/` e anexe com `$QA caso <run_dir> CT04 --evidencia evidencias/arquivo.txt`.
3. **Registrar o status logo depois de cada caso**, com o que foi observado de fato:
   `$QA caso <run_dir> CT01 --status confirmado|divergente|pendente|pulado --resumo "…" --observado "…" --destaque evidencias/CT01-x.png`
   - `--resumo` (obrigatório): **uma linha** com esperado × observado, ex.: `"Esperado 404; veio 200 com página vazia"`. É o que aparece na tabela do PDF. Em divergente, o resumo fala da divergência, não da parte que passou.
   - `--observado`: o detalhe, em até 3–4 frases. Hipótese de causa vai marcada como hipótese.
   - `--destaque`: **1 evidência** (máx. 2) que prova o resultado sozinha. Só ela aparece no PDF; o resto fica listado e na pasta.
4. **Divergência: reproduza uma vez antes de registrar.** Rode de novo sem vídeo. Se repetir, registre `divergente` e anote "reproduzido 2/2". Se não repetir, registre `pendente` como instável ("1/2"), com as duas evidências. Não pare para corrigir e não tente "fazer passar".
5. **No chat, uma linha por caso**: `CT03 ✗ divergente: esperado /page/2, URL ficou na base`. Sem repetir o log nem o plano.
6. **Gerar o relatório**: `$QA relatorio <run_dir>` gera `relatorio.html` e `relatorio.pdf` no formato enxuto: resumo por critério, achados (divergentes e pendentes) com detalhe, tabela de casos com uma linha cada, e só as evidências de destaque. `--completo` gera `relatorio-completo.pdf` com todas as evidências, passos e o texto da task. Use só se o dev pedir. Antes de entregar, resolva os `[aviso]` que o comando imprime (caso sem resumo, sem evidência, excesso de arquivos). Entregue o caminho do PDF e o resumo por critério.
7. **Atualizar o painel**: `$QA painel` regenera `${QA_REPORTS_DIR:-~/qa-relatorios}/index.html`, que mostra todas as execuções agrupadas por aplicação (status de cada caso, ambiente, links do PDF, issues e PR). Informe o caminho ao dev.
8. **Oferecer issues/PR** quando houver divergentes: veja **GitHub**.

### Orçamento de evidências

Evidência é o mínimo que prova o resultado. Mais arquivo não deixa o teste mais confiável, só deixa o relatório mais difícil de ler.

| Tipo de caso | Capture | Não capture |
|---|---|---|
| HTTP (status, header, canonical) | 1 saída do `http` com `--grep` no que importa | print da página, body inteiro sem motivo |
| Visual estático | 1 `print_el` do elemento (ou `print` da viewport) | `print_full` sem necessidade, print antes de cada passo |
| Interação | 1 vídeo **ou** print antes + depois, com asserts no log | vídeo **e** print de cada etapa |
| Mesmo check em N páginas | asserts de todas no log + 1 print/vídeo representativo | 1 print/vídeo por página |
| Divergência | evidência da falha + no máx. 1 diagnóstico | toda a investigação exploratória |

- Rodada exploratória (achar seletor, descobrir dado de teste, investigar causa) roda **sem `--caso`**, na pasta `_explora/`. Só anexe ao caso o que entra como prova.
- Mais de ~8 arquivos num caso quase sempre indica caso grande demais ou captura repetida. O `relatorio` avisa.

O relatório é gerado **mesmo que a execução seja interrompida ou que casos falhem**. Casos não rodados ficam como `pendente`, e o motivo vai em `--observado`.

### Limites da execução

- **Só leitura, só no ambiente indicado pelo dev.** Produção só com autorização explícita para aquela execução.
- **Nunca envie formulário que cria dado real** (lead, cadastro, pedido, pagamento, e-mail, disparo de tracking de conversão) sem aprovação explícita para aquele caso. Na falta dela, capture o estado até antes do envio e marque o restante como `pendente`.
- Não use nem registre credenciais, tokens ou dados pessoais nas evidências. Se aparecerem num header ou print, avise e peça para mascarar antes de compartilhar o PDF.
- Caso de *Processo* (decisão, relatório externo, aprovação de PM): peça a evidência ao dev. Sem ela, o caso fica `pendente`.

## GitHub: issues e PR

O agente transforma achados em issues e abre o PR da correção. **Publicar no GitHub é ação externa**: nada é enviado sem o ok explícito do dev para aquela execução.

- **Configuração** (uma vez): `~/.config/qa-agent/.env`, a partir do `.env.example` da skill (token fine-grained, mapa `projeto=dono/repo`, rótulos). Sem token, usa o login do `gh`. Confira com `$QA github check <run_dir>`. Nunca peça nem leia o token no chat: o dev preenche o arquivo.
- **Issues**: `$QA github issues <run_dir>` mostra a prévia (uma linha por divergente; `--mostrar` traz o corpo). Mostre a lista ao dev, pergunte quais viram issue e só então rode com `--criar [--casos CT03 CT07]`. Uma issue por caso, com rótulo `qa-agent` e marcador que evita duplicar; o link volta para o caso no `run.json` e aparece no painel. Pendente só com `--incluir-pendentes`. O GitHub não recebe as imagens pela API: o corpo lista os arquivos de evidência para o dev anexar se quiser.
- **PR**: só quando o dev pedir que você corrija. Corrija numa branch nova (nunca na padrão), mostre o diff, faça commit e `git push` com o ok dele e depois `$QA github pr <run_dir> --head <branch>` (prévia) → `--criar`. Abre como rascunho (`--pronto` para revisão), com a tabela dos achados e `Closes #n` das issues. Depois do merge, rode a validação de novo.
- O script recusa enviar corpo que pareça conter credencial (`Authorization`, token, senha, cookie). Mascare o caso e rode de novo. Dado de cliente nas evidências também precisa de ok antes de virar issue.

## Execução com multiagentes

Use quando o plano tiver **6 casos ou mais** e a sua IA tiver subagentes. Com menos casos, o custo de explicar o contexto a cada agente passa do ganho. Sem subagentes, rode em sequência; o resultado é o mesmo.

O `run.json` aceita escrita paralela (trava de arquivo, nomes de evidência reservados), então todos os agentes usam **a mesma `<run_dir>`**.

1. **Você é o orquestrador.** Contexto, critérios, plano e ok do dev continuam com você, exatamente como no **Processo**. Depois do ok, rode `$QA init` uma vez.
2. **Divida os casos em lotes** de 3 a 5, agrupados pela página ou pelo fluxo (mesma página = mesmo agente, que reaproveita seletor e dado de teste). No máximo 4 agentes ao mesmo tempo.
3. **Lighthouse fica fora dos lotes.** Rode depois que os outros terminarem, um por vez: CPU disputada derruba a nota de performance e gera falso achado.
4. **Despache cada lote.** Se a IA tiver o agente **`qa-executor`** (Claude Code, Cursor, Kiro; o instalador cria), use-o: ele já traz o runtime, as regras e o formato de resposta, e roda num modelo mais barato. O briefing fica só com: `<run_dir>`, ambiente, os casos do lote copiados do plano (`id`, `criterio`, `passos`, `esperado`) e qualquer autorização específica (ex.: "pode enviar o formulário do CT05").
   Sem `qa-executor` (Codex e outras), o briefing é o único contexto do subagente. Inclua também:
   - o bloco **Runtime** desta skill (como definir `SK`/`qa`);
   - as regras: só os casos do lote; `--caso` e `--nome` em toda captura; registrar status com `$QA caso` logo após cada caso (com `--resumo`, `--observado`, `--destaque`); reproduzir divergência uma vez; seguir o orçamento de evidências e os limites da execução; **não** rodar `relatorio`, `painel` nem `github`, e não mexer em caso de outro lote;
   - a resposta esperada: **uma linha por caso** (`CT03 ✗ divergente: …`), nada mais;
   - se a ferramenta permitir escolher o modelo do subagente, um modelo mais barato: o lote é execução mecânica de um plano já decidido.
5. **Consolide** com `$QA status <run_dir>` (uma linha por caso; não leia o `run.json` inteiro). Caso que ficou `pendente` sem motivo vira nova rodada ou pergunta ao dev. Depois, `$QA relatorio`.

A exploração autônoma também divide bem: um agente por área, cada um com `--semente` e `--prefixo-url` próprios e `--prefixo` diferente (`EXA`, `EXB`…).

## Exploração autônoma

Teste sem task: o script navega a aplicação sozinho, seguindo só links (GET), e registra o que quebrar. **Não clica em botão nem envia formulário**, e ignora URLs de logout/exclusão (`--ignorar`). Toda a varredura roda sem IA: você só lê o resumo no final.

1. Pergunte, numa rodada só, o que faltar: URL base, limites (padrão 30 páginas, profundidade 2), área (`--prefixo-url`, ex.: `/ofertas`), viewport (desktop, mobile ou os dois). Produção só com autorização explícita. Confirme antes de rodar.
2. Rode:
   ```bash
   $QA explorar <run_dir> <url> [--semente <url>] [--prefixo-url /area] [--max-paginas 30] [--profundidade 2] [--mobile] [--prefixo EX]
   ```
   Para mobile e desktop, rode duas vezes com `--prefixo` diferente (`EXD`, `EXM`).
3. A saída é uma linha por check, e cada check vira um caso (`EX01`…`EX06`): páginas e links internos com erro, exceção JS, `console.error`, requisição da própria origem com erro, imagem quebrada, rolagem horizontal. Erro em domínio de terceiros vira `EX07` informativo (`pendente`). O detalhe por página fica em `evidencias/<prefixo>-explorar-log.txt`. Abra o log **só** para os casos `divergente`, e com `grep` no trecho que importa.
4. **Triagem de cada divergente** (é aqui que a IA agrega valor): reproduza uma vez a página citada com `print` ou `fluxo` sem vídeo, investigue a causa provável (hipótese marcada como hipótese) e atualize o caso com `$QA caso` (`--observado`, `--destaque`). Falso positivo comprovado (ex.: erro esperado do ambiente de staging) vira `pulado` com o motivo, nunca `confirmado`.
5. `$QA relatorio <run_dir>`. Sem task, o relatório mostra o escopo "Exploração autônoma".

**Rodar sem ninguém olhando (cron/CI):** `explorar` não precisa de IA. Com `--falhar`, sai com código 1 quando acha erro; agende o comando e chame a IA só para triar quando o código for 1:

```bash
"$PY" "$SK/scripts/qa_evidencias.py" explorar "$QA_REPORTS_DIR/explora-$(date +%F)" https://staging.exemplo.com --falhar \
  || echo "achou erro: abrir a IA e pedir a triagem desta pasta"
```

## Economia de tokens

A regra geral: **o script trabalha, a IA decide**. O que custa token é a IA ler saída longa, não o navegador rodar.

- Use os comandos do script em vez de navegar com ferramentas de browser da IA (MCP de navegador, leitura de página inteira). Uma chamada do script devolve poucas linhas.
- Nunca leia `run.json`, `explorar.json`, HTML salvo ou o log inteiro. Use `$QA status`, a saída curta dos comandos e `grep` no log.
- `--grep` no `http` em vez do body; asserts no `fluxo` em vez de olhar o print. Abra imagem só quando o assert não bastar para entender uma divergência.
- Agrupe ações num fluxo só (arquivo `.json`) em vez de várias chamadas.
- Exploração autônoma primeiro, IA depois: a varredura é de graça; gaste tokens só na triagem dos divergentes.
- Em multiagentes, briefing curto e resposta de uma linha por caso; modelo mais barato nos subagentes quando der.

## O que evitar

- **Não pule contexto e extração de critérios.** Gerar casos antes de isolar critério e contexto reais é a forma mais comum de o plano sair desalinhado com a task.
- Não limite os casos ao caminho feliz.
- Não misture UI e API no mesmo caso.
- **Não execute antes de entregar o plano e ter o ok do dev.**
- **Não rode `github ... --criar` nem `git push` sem o ok do dev** para aquela execução.
- **Não omita casos que falharam** nem troque o status para "passar". Divergência com evidência é o resultado mais útil do relatório.
- **Não declare veredito geral** ("task aprovada/reprovada"), nem no chat nem no PDF.
- Não capture evidência "por garantia": siga o orçamento de evidências.
- Não registre caso sem assert: "parece certo no print" não é resultado.
