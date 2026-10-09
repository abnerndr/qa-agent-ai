# Handoff — Assistente de QA (Work OS do Abner)

Este arquivo existe para que **qualquer agente novo** (Claude Code em outra sessão, outra ferramenta de IA) ou **um terceiro** (ex.: banca do Demoday) entenda o que existe aqui e o que falta, sem precisar perguntar nada.

Ordem de leitura: `README.md` → `CLAUDE.md` (carregado automaticamente pelo Claude Code) → este arquivo → `docs/work-os-reference.md` se precisar do método completo.

**Última atualização:** 2026-10-09, gerada pela skill `/handoff` (`.claude/skills/handoff/`), cobrindo até o commit `7562344` mais a sessão que criou a própria skill.

## O que é este projeto

Work OS pessoal do Abner (dev full stack no time Mundo ZeroKM / PYXYS) que sustenta um **agente de QA**: recebe uma task de dev do jeito que ela chega (mensagem corrida do Slack ou link de registro da Slack List), extrai os critérios de aceite, monta o plano de teste, **executa os testes** (Playwright para UI, requisição HTTP para API, Lighthouse) contra o ambiente indicado e entrega um **relatório PDF com evidências**, inclusive das falhas. Ele não aprova a task: quem aprova é o dev/PM.

## Estado atual em uma tela

| | |
|---|---|
| **Funciona hoje** | Skill `qa-validacao-tasks` completa: plano → execução → PDF. Modo manual (cola o texto) e automático (link do Slack + PRD por SSH). Instalação local e remota. |
| **Uso real** | PR #516 do `mundo-zero-km-nextjs` (`outputs/qa/mundo-zero-km-pr-516/`) e Chat IA MZK Fase 2 (plano CA1–CA16, ver memória `chat-ia-mzk-feedback-fase2`). |
| **Em aberto** | Métricas e baseline do PRD (`[NEED]`), piloto com outros devs, onde o V2 roda de forma fixa. |
| **Próximo passo** | Ver "Por onde continuar" no fim deste arquivo. |

## Estrutura (10 camadas)

| Pasta | Papel |
|---|---|
| `README.md` | Mapa do projeto e guia de instalação/uso do agente de QA |
| `CLAUDE.md` | Memória ativa: identidade, regras, limites (lido automaticamente) |
| `docs/` | PRD, briefs, matriz de opções, log de decisões, log de sessões, referência operacional |
| `knowledge/` | Fontes e evidências por nível de confiança (A–E) |
| `.claude/skills/` | `qa-validacao-tasks` (agente de QA) e `handoff` (este procedimento) |
| `.claude/hooks/` | Travas automáticas (guardrails) |
| `.claude/adr/` | Decisões estruturais, com alternativas consideradas |
| `.claude/memory/` | Conhecimento acumulado entre sessões, por tipo |
| `tools/` | Scripts de instalação e harnesses |
| `outputs/` | Entregas finais (relatórios do agente em `outputs/qa/`) |

## Histórico real (por marco)

| Data | Commits | O que entrou |
|---|---|---|
| 2026-09-03 | `03d22cb` | Setup do Work OS: 10 camadas, hooks testados, ADR-001 |
| 2026-09-04 | `310c4c4` `260bf51` `8e075be` | PRDSI1 + task list da fase de validação; `install-skill.sh`; README de instalação |
| 2026-09-11 | `17af6b7` `836b3ff` `b161c4b` | Primeiro handoff; distribuição da skill; `install-skill-remote.sh` (sparse clone) |
| 2026-09-25 | `ff452ab` | Execução + evidências + PDF pelo agente (`qa_evidencias.py`), ADR-002 |
| 2026-09-25 | `8a30e39` `fe7f461` `718e47d` `c7376cc` | Ajustes da 1ª execução real (PR #516); regras de vídeo e nomes de evidência |
| 2026-09-25 | `522546a` `25abcdf` | Auditoria Lighthouse na execução; correção de pastas no AppData (WSL) |
| 2026-09-25 | `f1dc1f1` | README reescrito apresentando o agente |
| 2026-10-09 | `7562344` | Modo automático: `buscar_prd.sh`, `registro_lista_slack.py`, ADR-003 |
| 2026-10-09 | *(sessão do handoff)* | Skill `/handoff`, memória `user`, handoff/session-log/decision-log atualizados |

Confira `git log --oneline` para commits mais novos que este arquivo.

## Decisões (ADRs)

Índice: `.claude/memory/adr-index.md`. Log resumido: `docs/decision-log.md`.

- **ADR-001** (2026-09-03): adoção do Work OS completo de 10 camadas.
- **ADR-002** (2026-09-25): o agente executa os casos, captura evidências (Python + Playwright, venv próprio) e gera o PDF com falhas incluídas, sem veredito. **Antecipa parte do V2 do PRDSI1.**
- **ADR-003** (2026-10-09): passo 0 pergunta manual × automático; no automático, lê a task pelo MCP do Slack e o PRD do `mzk-pm-workspace` por SSH.

## Skills

### `qa-validacao-tasks` (o agente de QA)
- `SKILL.md`: passo 0 (modo de entrada) → contexto → plano → ok do dev → execução → PDF.
- `scripts/setup.sh`: cria `.venv` com Playwright + Chromium.
- `scripts/qa_evidencias.py`: HTTP sem seguir redirect, prints desktop/mobile, fluxos com vídeo, Lighthouse, PDF.
- `scripts/buscar_prd.sh`: clone raso/esparso do `mzk-pm-workspace` via SSH em `~/.cache/qa-validacao-tasks/`.
- `scripts/registro_lista_slack.py`: extrai um registro da Slack List *PX | Tech 2026*.
- Instalação: `tools/scripts/install-skill.sh` (local) ou `install-skill-remote.sh` (curl, ver README). A cópia em uso fica em `~/.claude/skills/` no WSL e no Windows (memória `instalacao-wsl-windows`).

### `handoff`
Procedimento para regenerar este arquivo e registrar a sessão em `docs/session-log.md`. Rodar com `/handoff` ao fim de cada sessão relevante. Vive só neste projeto (`.claude/skills/handoff/`).

## Memória (`.claude/memory/`)

Índice: `.claude/memory/MEMORY.md`. Oito memórias, cobrindo os quatro tipos:

| Tipo | Qtd | Exemplos |
|---|---|---|
| `user` | 1 | `perfil-abner`: papel, ambiente, preferências |
| `feedback` | 2 | `relatorio-qa-enxuto`, `relatorio-pdf-execucao-qa` |
| `project` | 2 | `chat-ia-mzk-feedback-fase2`, `instalacao-wsl-windows` |
| `reference` | 3 | `mundozerokm-staging-assistente`, `prds-mzk-pm-workspace`, `tasks-slack-list-px-tech` |

## PRD e tasks

`docs/PRDSI1.md` (Draft — Planning Review) previa V1 (só plano), V2 (executar e gerar evidência, "não aprovado") e V3 (onde roda de forma fixa).

**Divergência importante:** o V2 foi antecipado pelo ADR-002 depois do uso real na PR #516. O PRD e o `tasks/tasks-PRDSI1.md` ainda descrevem o cenário anterior (só V1) e não foram reescritos.

Na task list, foram marcadas só as tasks com evidência no repositório (4.2: ferramenta de captura; 5.4: ADR-002). As demais dependem de dados reais que ainda não foram levantados (tempos, baseline, feedback de outros devs) e **não devem ser inventadas**.

## Hooks (guardrails)

Configurados em `.claude/settings.json`:

- `protected-files/guard.sh` (bloqueante, `PreToolUse` em `Bash`): impede `rm`, `mv`, `shred`, `truncate`, `dd` e redirecionamento `>` sobre `CLAUDE.md`, `.claude/adr/`, `.claude/memory/` e `docs/decision-log.md`. Limitação conhecida: verbo e alvo em trechos separados por `;`/`&&`/`||` passam.
- `validation-reminder/remind.sh` (não bloqueante, `PreToolUse` em `Write`): lembrete de validação ao escrever em `outputs/`.
- `session-log-reminder/remind.sh` (não bloqueante, `Stop`): lembrete de atualizar `docs/session-log.md`.

## Particularidades de ambiente

- **WSL × Windows:** a rede do Windows dá timeout em `cdn.playwright.dev`; os browsers são baixados pelo WSL (memória `instalacao-wsl-windows`, README seção Windows).
- **Staging do Mundo ZeroKM** usa Basic Auth (memória `mundozerokm-staging-assistente`); credenciais nunca vão para o repositório.
- **Bridge remota em sandbox:** se `rm`/`unlink` derem "Operation not permitted", o git não limpa os `.lock` (`fatal: cannot lock ref 'HEAD'`). Workaround: renomear o lock para `.stale.<timestamp>` antes de `git add`/`git commit`. Num terminal normal isso não acontece.

## Regras que continuam valendo (de `CLAUDE.md`)

- Português do Brasil, conciso. Nunca inventar dado; perguntar quando algo for ambíguo.
- Aprovação humana antes de: apagar arquivos, mudar permissões, enviar mensagem externa, usar dado sensível, decisão de negócio irreversível, compartilhar informação financeira/jurídica/de cliente, tratar evidência fraca como fato.
- Decisão estrutural → ADR em `.claude/adr/` + `.claude/memory/adr-index.md`.
- Fato, preferência ou correção de forma de trabalhar → memória em `.claude/memory/` + `MEMORY.md`.

## Por onde continuar

1. Reescrever `docs/PRDSI1.md` e `tasks/tasks-PRDSI1.md` para refletir o ADR-002 (V2 local já existe), ou registrar um PRD novo da fase atual.
2. Consolidar as execuções reais (PR #516, Chat IA Fase 2) em `knowledge/03_processado/piloto-v1-abner.md`, com tempos medidos pelo Abner.
3. Piloto com 1–2 devs do time usando o modo automático.
4. Registrar o relatório da PR #516 em `outputs/INDEX.md` (hoje a tabela está vazia).
5. Ao fim de cada sessão: `/handoff`.
