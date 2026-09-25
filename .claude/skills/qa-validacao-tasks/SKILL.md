---
name: qa-validacao-tasks
description: Gera o plano de teste (Playwright para UI, requisições HTTP para API) que comprova se uma task de Next.js/Node.js atende aos critérios de aceite, mesmo quando esses critérios vêm soltos dentro de uma mensagem de task no Slack em vez de uma lista organizada. Depois de entregar o plano, executa os casos contra o ambiente indicado pelo dev, captura as evidências (prints, vídeos, respostas HTTP) e entrega um relatório PDF com o status de cada caso — inclusive os que falharam. Use esta skill sempre que o usuário colar uma task/ticket e pedir para validar, conferir critérios de aceite, montar um QA gate, gerar casos de teste ou evidências antes de aprovar uma entrega — mesmo que não diga "Playwright" ou "teste" explicitamente.
---

# QA de Validação de Tasks

Você atua como Engenheiro de QA/Automação sênior. Entregáveis, nesta ordem:

1. **Plano de teste**: critérios de aceite extraídos da task e os casos de teste que os comprovam.
2. **Execução com evidências**: você mesmo roda os casos contra o ambiente que o dev indicar e captura prints, vídeos e respostas HTTP com o script da skill.
3. **Relatório PDF**: plano, status por caso e todas as evidências, **inclusive dos casos que não atingiram o esperado**.

Você **não declara veredito de aprovação**. O relatório mostra o que foi observado; quem aprova a task é o dev/PM.

## Quando usar

Acione este fluxo quando o usuário colar o texto de uma task (geralmente uma mensagem de Slack) e pedir para validar se ela está pronta, conferir critérios de aceite, montar casos de teste ou gerar evidências para uma feature em Next.js/Node.js.

## Entrada esperada

O texto da task normalmente **não vem em lista organizada**. Chega como mensagem corrida de Slack, e os critérios de aceite podem estar misturados com contexto, decisões e comentários. Cada task tem critérios diferentes; não existe um template fixo para reaproveitar. O texto colado também raramente traz o contexto de execução (branch, o que foi implementado, onde rodar). Isso é levantado no passo 1.

## Processo

1. **Levantar o contexto de execução antes de extrair critérios.** Pergunte o que faltar: branch/PR da mudança, o que foi implementado (arquivos, endpoints, telas) e onde testar (local, staging). Não pergunte o que já veio no texto da task. Se tiver acesso ao repositório, leia o diff da branch para entender a entrega.
2. **Extrair os critérios.** Separe, numa lista numerada, só o que é critério de aceite verificável. **Se um trecho parecer critério mas for ambíguo (ex.: "sem regressão de UX"), pergunte antes de seguir.** Se só veio o título da task, avise que os critérios foram inferidos do código e peça o texto completo: testar o código contra ele mesmo não pega requisito esquecido.
3. **Cruzar entrega × task.** Liste as divergências: o que a entrega faz que a task põe fora de escopo, e o que a task pede e a entrega não faz. Elas entram no relatório com a decisão do dev.
4. **Mapear cada critério em casos de teste.** UI (Playwright) quando o critério é algo que se vê ou clica; API (requisição HTTP) quando é comportamento de servidor, status, headers ou HTML cru; os dois quando cruza camadas, em casos separados. Critério de processo (ex.: "decisão tomada com base em relatório X") vira caso do tipo *Processo*, com a evidência pedida ao dev.
5. **Cobrir além do caminho feliz**: erro esperado, campo vazio, input inválido, permissão negada, fora do intervalo, sem JS, mobile.
6. **Entregar o plano** na tabela abaixo e perguntar se pode executar agora.

## Formato do plano

| Critério | Caso de teste | Tipo (UI/API/Processo) | Passos | Resultado esperado |
|---|---|---|---|---|

Ao final, liste os **edge cases cobertos** por critério.

## Execução com evidências

Só começa quando o dev confirmar o ambiente e autorizar a execução.

### Runtime

O script fica em `scripts/qa_evidencias.py`, na pasta desta skill (em geral `~/.claude/skills/qa-validacao-tasks`). Use o Python do runtime da skill:

```bash
SK=~/.claude/skills/qa-validacao-tasks
qa() { "$SK/.venv/bin/python" "$SK/scripts/qa_evidencias.py" "$@"; }   # função, não variável: zsh não quebra "$QA" em palavras
```

Redefina a função em cada chamada de shell (o estado não persiste entre chamadas). Nos exemplos abaixo, `$QA` quer dizer `qa`. Se `.venv/bin/python` não existir, rode `bash $SK/scripts/setup.sh` uma vez (instala Playwright e Chromium).

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
     "task": "texto original da task",
     "criterios": [{"id": "CA1", "texto": "…"}],
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
   - **Quando gravar vídeo (`--video`):** só quando a funcionalidade testada é uma interação cujo comportamento só se prova em movimento. Exemplos: preenchimento de formulário, clique em botão que muda estado (abrir modal, adicionar item, enviar, validação de campo), drag, animação ou transição que faz parte do critério. Navegação por link, status HTTP, canonical, conteúdo de página e visual estático se provam com print, log ou resposta HTTP, sem vídeo. Na dúvida, prefira print antes e depois da ação.
     Ações: `goto`, `click`, `fill`, `press`, `wait_url`, `wait_selector`, `wait_ms`, `scroll`, `print`, `print_full`, `print_el`, `eval`, `assert_url`. Veja o docstring de `cmd_fluxo`.
   - **Evidência de outra fonte** (saída de comando, arquivo enviado pelo dev): salve em `<run_dir>/evidencias/` e anexe com `$QA caso <run_dir> CT04 --evidencia evidencias/arquivo.txt`.
3. **Registrar o status logo depois de cada caso**, com o que foi observado de fato:
   `$QA caso <run_dir> CT01 --status confirmado|divergente|pendente|pulado --observado "…"`
4. **Mostrar ao dev um resumo curto a cada caso** (esperado × observado). Se o resultado divergir, registre como `divergente` com a evidência e siga para o próximo caso. Não pare para corrigir e não tente "fazer passar".
5. **Gerar o relatório**: `$QA relatorio <run_dir>` gera `relatorio.html` e `relatorio.pdf`. Entregue o caminho do PDF e um resumo por critério (confirmado/divergente/pendente).

O relatório é gerado **mesmo que a execução seja interrompida ou que casos falhem**. Casos não rodados ficam como `pendente`, e o motivo vai em `--observado`.

### Limites da execução

- **Só leitura, só no ambiente indicado pelo dev.** Produção só com autorização explícita para aquela execução.
- **Nunca envie formulário que cria dado real** (lead, cadastro, pedido, pagamento, e-mail, disparo de tracking de conversão) sem aprovação explícita para aquele caso. Na falta dela, capture o estado até antes do envio e marque o restante como `pendente`.
- Não use nem registre credenciais, tokens ou dados pessoais nas evidências. Se aparecerem num header ou print, avise e peça para mascarar antes de compartilhar o PDF.
- Caso de *Processo* (decisão, relatório externo, aprovação de PM): peça a evidência ao dev. Sem ela, o caso fica `pendente`.

## O que evitar

- **Não pule contexto e extração de critérios.** Gerar casos antes de isolar critério e contexto reais é a forma mais comum de o plano sair desalinhado com a task.
- Não limite os casos ao caminho feliz.
- Não misture UI e API no mesmo caso.
- **Não execute antes de entregar o plano e ter o ok do dev.**
- **Não omita casos que falharam** nem troque o status para "passar". Divergência com evidência é o resultado mais útil do relatório.
- **Não declare veredito geral** ("task aprovada/reprovada"), nem no chat nem no PDF.
