# Handoff — Assistente de QA (Work OS do Abner)

Este arquivo existe para que **qualquer agente novo** (Claude Code em outra sessão, outra ferramenta de IA, ou você mesmo revisitando o projeto depois de um tempo) entenda rápido o que já existe aqui e o que falta, sem precisar reconstruir contexto do zero.

Ordem de leitura recomendada para um agente novo: `README.md` → `CLAUDE.md` (carregado automaticamente pelo Claude Code) → este arquivo → `docs/work-os-reference.md` se precisar do método completo.

## O que é este projeto

Work OS pessoal do Abner (dev full stack no time Mundo ZeroKM / PYXYS), criado para sustentar a evolução de uma ideia específica: um **assistente de QA** que ajuda a validar tasks de dev — hoje coladas em texto corrido do Slack, sem padrão — extraindo critérios de aceite e gerando plano de teste (Playwright para UI, requisição HTTP para API).

## Estrutura (10 camadas)

| Pasta | Papel |
|---|---|
| `README.md` | Mapa do projeto — ponto de partida |
| `CLAUDE.md` | Memória ativa — identidade, regras, limites (lido automaticamente pelo Claude Code) |
| `docs/` | Decisões: briefs, matriz de opções, log de decisões, log de sessões, referência operacional |
| `knowledge/` | Fontes e evidências, organizadas por nível de confiança (A–E) |
| `.claude/skills/` | Procedimentos reutilizáveis (skills) |
| `.claude/hooks/` | Travas automáticas (guardrails) |
| `.claude/adr/` | Decisões arquiteturais, com alternativas consideradas |
| `.claude/memory/` | Conhecimento acumulado entre sessões |
| `tools/` | Scripts e harnesses de verificação |
| `outputs/` | Entregas finais |

Racional completo da adoção dessa estrutura: `.claude/adr/adr-001-adocao-do-work-os.md`.

## Histórico real (por commit)

| Commit | O que entrou |
|---|---|
| `03d22cb` | Setup inicial do Work OS — as 10 camadas, hooks testados, ADR-001 |
| `310c4c4` | `docs/PRDSI1.md` (PRD do Sistema de QA Automático) + `tasks/tasks-PRDSI1.md` (task list da fase atual) |
| `260bf51` | `tools/scripts/install-skill.sh` — instala a skill `qa-validacao-tasks` neste projeto |
| `8e075be` | Seção no `README.md` documentando como instalar e usar a skill |

Confira `git log --oneline` para ver se já existem commits mais recentes que este arquivo não capturou.

## O PRD e a task list ativa

`docs/PRDSI1.md` é uma cópia do PRD "Sistema de QA Automático para Validação de Tasks de Dev" (status: Draft — Planning Review). Ele descreve 3 fases:

- **V1 — já existe:** a skill `qa-validacao-tasks` (instalada neste projeto). Só gera o plano de teste, não executa nada.
- **V2 — futura, não aprovada:** executar os testes de verdade e gerar evidência (print/vídeo). Só entra em pauta se o time confirmar, em uso real, que o plano sozinho não basta.
- **V3 — visão, não comprometida:** onde isso roda de forma fixa (o próprio Work OS? Electron? site?) — decisão futura.

`tasks/tasks-PRDSI1.md` foi gerado deliberadamente **só para a fase atual** (validar o V1, expandir para o time, resolver as perguntas em aberto do PRD) — nenhuma task de construção do V2 foi incluída, porque o próprio PRD marca isso como Não-Objetivo até a decisão de avançar ser tomada. São 5 parent tasks e 26 sub-tasks, todas ainda não marcadas como feitas:

1. Validar o V1 em mais tasks reais (uso individual do Abner)
2. Expandir o piloto para 1–2 devs do time e coletar feedback
3. Levantar as métricas e baseline pendentes (Seção 6 do PRD, campos `[NEED]`)
4. Resolver as decisões técnicas em aberto (Seção 8 do PRD, campos `[NEED]`)
5. Consolidar o critério de avanço para o V2 e registrar a decisão (ADR-002, só se for o caso)

Nenhum valor `[NEED]` foi inventado — essas tasks existem justamente para produzir esses números com dados reais.

## Skill instalada: `qa-validacao-tasks`

A skill em si vive na conta do Claude (Cowork), não no repositório. Este projeto mantém uma cópia versionada do `SKILL.md` dentro de `.claude/skills/qa-validacao-tasks/`, gravada por `tools/scripts/install-skill.sh` (testado com diff byte a byte contra o original antes de ser commitado). Se a skill mudar na conta do Cowork, o script precisa ser atualizado manualmente com o novo conteúdo — ele não sincroniza sozinho.

## Hooks (guardrails)

Três hooks configurados em `.claude/settings.json`:

- `guard.sh` (bloqueante, `PreToolUse` em `Bash`) — impede comandos destrutivos (`rm`, `mv`, `shred`, `truncate`, `dd`, redirecionamento `>`) sobre arquivos protegidos (`CLAUDE.md`, `.claude/adr/`, `.claude/memory/`, `docs/decision-log.md`). Testado ao vivo: bloqueia `rm CLAUDE.md`, deixa passar comandos inofensivos e comandos compostos onde verbo e alvo estão em trechos separados por `;`/`&&`/`||` (limitação conhecida e documentada).
- `remind.sh` (não bloqueante, `PreToolUse` em `Write` para `outputs/`) — lembrete de validação.
- `remind.sh` (não bloqueante, `Stop`) — lembrete para atualizar o log de sessão.

## Particularidade de ambiente (só relevante para agentes rodando via bridge remota)

Quando esta pasta é acessada por um agente em sandbox via ponte remota (não um terminal comum do Windows), `rm`/`unlink` retornam "Operation not permitted" — o git não consegue limpar seus próprios arquivos `.lock` depois de operações. Sintoma: `fatal: cannot lock ref 'HEAD'` ou `Unable to create '.../index.lock'` em commits subsequentes. Workaround usado (funciona porque renomear não é bloqueado): mover o lock para um nome `.stale.<timestamp>` antes de cada `git add`/`git commit`. Não é um problema do repositório em si — um terminal normal no Windows não deveria ter essa restrição.

## Regras que continuam valendo (de `CLAUDE.md`)

- Nunca inventar dado, sempre perguntar quando algo for ambíguo.
- Aprovação humana obrigatória antes de: apagar arquivos, mudar permissões, enviar mensagem externa, usar dado sensível, decisão de negócio irreversível, compartilhar informação financeira/jurídica/de cliente, tratar evidência fraca como fato.
- Decisão estrutural nova → ADR em `.claude/adr/`, registrado em `.claude/memory/adr-index.md`.
- Fato novo, preferência revelada, ou correção de forma de trabalhar → memória nova em `.claude/memory/`, indexada em `.claude/memory/MEMORY.md` (esse índice ainda está vazio — nenhuma memória foi registrada até agora).

## Por onde continuar

O próximo passo natural é a task **1.0** de `tasks/tasks-PRDSI1.md`: rodar a skill `qa-validacao-tasks` em 3–5 tasks reais do Abner e cronometrar o processo. É trabalho que depende de tasks reais do Slack e do julgamento do Abner — um agente não deve simular isso ou inventar os números de tempo/qualidade. Ao fechar cada bloco de trabalho, atualizar `docs/session-log.md` (novo agente = nova entrada) e marcar os checkboxes correspondentes em `tasks/tasks-PRDSI1.md`.
