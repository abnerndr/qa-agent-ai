# ADR-003 — Modo automático de entrada: task pelo Slack e PRD pelo GitHub

**Status:** Aceito
**Data:** 2026-10-09
**Contexto:** No fluxo atual, o dev copia o texto da task do Slack e preenche o formulário de contexto. As tasks do time Mundo ZeroKM citam o PRD na descrição (link do GitHub ou só o caminho em `mzk-pm-workspace/artefatos/prds`), e às vezes os critérios de aceite estão só no PRD. O Abner pediu que o agente pergunte, antes de rodar, se o dev prefere o modo manual (atual) ou um modo automático que lê a task e o PRD sozinho.

---

## Decisão

A skill `qa-validacao-tasks` ganha um **passo 0**: perguntar o modo de entrada.

- **Manual** (padrão): fluxo atual, sem mudança.
- **Automático**: o dev cola o link da task no Slack. O agente:
  1. confere se há um MCP do Slack conectado; sem ele, orienta a conexão (claude.ai → Conectores, ou `/mcp`) e para;
  2. lê a task (só leitura, sem responder nem editar no Slack): normalmente um registro da Slack List *PX | Tech 2026* (`/lists/<time>/<lista>?record_id=Rec…`), extraído com `scripts/registro_lista_slack.py` porque a ferramenta de lista devolve a lista inteira; ou, se o link for de mensagem, a mensagem e a thread;
  3. baixa o PRD com `scripts/buscar_prd.sh`, que mantém um clone raso e esparso de `pyxys-inteligencia-digital/mzk-pm-workspace` via **SSH** em `~/.cache/qa-validacao-tasks/` e completa caminhos relativos com `artefatos/prds`;
  4. usa os critérios da task, ou os do PRD quando a task não tiver (com a fonte de cada critério registrada no plano).

Os gates continuam iguais: critério ambíguo vira pergunta e nada executa sem o ok do dev no plano. O relatório mostra os links do Slack e do PRD (`fontes` no `plano.json`).

---

## Alternativas Consideradas

### 1. Ler o PRD pela web (WebFetch / `gh api`) (descartada)
O repositório é privado: WebFetch não autentica, e `gh` exige login extra que nem todo dev tem. Navegar no GitHub também gasta mais tokens que ler um arquivo local.

### 2. Clone completo do `mzk-pm-workspace` (descartada)
Desnecessário: só `artefatos/` interessa. Clone raso + esparso + `blob:none` é rápido e o `pull` a cada chamada mantém o PRD atualizado.

### 3. Modo automático como padrão (descartada)
Depende de Slack conectado e SSH na org. Manual continua padrão para não quebrar quem não tem essas configurações.

---

## Consequências

**Positivo:**
- O dev cola um link em vez de texto + formulário; critérios do PRD entram sem cópia manual.
- Rastreabilidade: o relatório aponta para a task e o PRD de origem.

**Negativo / riscos aceitos:**
- Pré-requisitos novos para o modo automático: Slack conectado ao Claude e chave SSH com acesso à org `pyxys-inteligencia-digital`. O `setup.sh` avisa se o SSH falhar.
- Nomes das ferramentas do MCP do Slack variam entre conectores; a skill descreve a capacidade (ler mensagem/thread), não um nome fixo.
- A task no Slack pode conter dado de cliente. A skill já instrui a não registrar dados pessoais nas evidências.
