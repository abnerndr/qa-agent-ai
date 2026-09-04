# Tasks — PRDSI1: Sistema de QA Automático para Validação de Tasks de Dev

> Gerado a partir de `docs/PRDSI1.md` (Status: Draft — Planning Review). Escopo: apenas a fase atual do rollout (Seção 7) e o levantamento das questões em aberto (Seções 6 e 8). Nenhuma task de build do V2 (execução real de testes, captura de evidência, escolha de Electron/site) está incluída — o próprio PRD marca isso como Não-Objetivo até o time confirmar, em uso real, que o V1 (só o plano de teste) não é suficiente.

## Relevant Files

- `docs/PRDSI1.md` - Cópia do PRD original; Seções 6 e 8 são atualizadas conforme os `[NEED]` forem resolvidos (tasks 3.5 e 4.6).
- `tasks/tasks-PRDSI1.md` - Esta própria task list; marcar os itens como concluídos (`[x]`) conforme forem feitos.
- `knowledge/03_processado/piloto-v1-abner.md` - Resultado consolidado das rodadas de validação individuais do Abner (task 1.5).
- `knowledge/01_coletas_externas/feedback-piloto-devs.md` - Feedback bruto coletado dos devs no piloto (task 2.4), ainda sem avaliação — promover para `knowledge/03_processado/` depois de revisado.
- `docs/problem-brief.md` - Atualizado com o resultado desta fase de validação (task 5.2).
- `docs/option-matrix.md` - Atualizado com a avaliação do critério de avanço (task 5.2).
- `docs/decision-log.md` - Nova linha registrando a decisão de avançar (ou não) para o V2 (task 5.3).
- `.claude/adr/adr-002-*.md` - Novo ADR, criado somente se a decisão for avançar para o V2 (task 5.4) — segue o formato de `adr-001-adocao-do-work-os.md`.
- `.claude/memory/adr-index.md` - Atualizado com a entrada do ADR-002, se ele for criado.

### Notes

- Esta fase é de validação/decisão, não de construção de software — por isso não há arquivos de código nem testes automatizados para parear (diferente do formato padrão desta task list). Quando o V2 for aprovado, um novo PRD + task list cobre a implementação em si, com seus arquivos de produção e de teste.
- Nenhum valor dos campos `[NEED]` foi inventado nesta task list — são as próprias tasks 3.x e 4.x que existem para produzir esses números com dados reais.

## Tasks

- [ ] 1.0 Validar o V1 (skill Cowork `qa-validacao-tasks`) em mais tasks reais — uso individual (Abner)
  - [ ] 1.1 Selecionar 3–5 tasks reais recentes do Slack, variando o tipo (UI, API, mista)
  - [ ] 1.2 Para cada task, colar o texto bruto na skill `qa-validacao-tasks` e gerar o plano de teste
  - [ ] 1.3 Cronometrar, em cada rodada, o tempo do "colar o texto" até o "plano pronto"
  - [ ] 1.4 Anotar qualquer critério de aceite que a skill não extraiu corretamente, e a hipótese do porquê
  - [ ] 1.5 Consolidar as 3–5 rodadas em `knowledge/03_processado/piloto-v1-abner.md` (tempos, acertos, falhas de extração)

- [ ] 2.0 Expandir o piloto para 1–2 devs do time e coletar feedback de uso real
  - [ ] 2.1 Escolher 1–2 devs com perfis de task diferentes (ex.: um mais front-end, um mais back-end)
  - [ ] 2.2 Explicar a cada dev o uso da skill (colar o texto da task → receber o plano de teste)
  - [ ] 2.3 Pedir que cada dev rode a skill em pelo menos 2 tasks reais próprias
  - [ ] 2.4 Coletar feedback qualitativo de cada dev por escrito (o plano cobriu o que testariam manualmente? faltou algo?) em `knowledge/01_coletas_externas/feedback-piloto-devs.md`
  - [ ] 2.5 Revisar esse feedback e promover para `knowledge/03_processado/` quando estiver processado

- [ ] 3.0 Levantar as métricas e baseline pendentes da Seção 6 do PRD (marcadas `[NEED]`)
  - [ ] 3.1 Medir o tempo médio hoje gasto validando uma task manualmente, usando uma amostra de 3–5 tasks recentes validadas do jeito antigo (baseline real, não estimado)
  - [ ] 3.2 A partir do resultado de 1.0 e 2.0, definir a meta de redução percentual (%) e documentar o racional da escolha
  - [ ] 3.3 Definir o prazo para atingir essa meta
  - [ ] 3.4 Definir a meta de adoção do time (quantas tasks ou pessoas usando o sistema em quanto tempo)
  - [ ] 3.5 Atualizar a tabela da Seção 6 em `docs/PRDSI1.md`, substituindo os `[NEED]` pelos valores levantados

- [ ] 4.0 Resolver as decisões técnicas em aberto da Seção 8 do PRD (marcadas `[NEED]`, Owner: Abner)
  - [ ] 4.1 Decidir onde o V2 vai rodar (Work OS atual / app Electron / site) e registrar o racional
  - [ ] 4.2 Decidir a ferramenta de captura de evidência (nativa do Playwright ou outra)
  - [ ] 4.3 Quantificar o esforço atual gasto validando tasks manualmente (pode reaproveitar os dados da task 3.1)
  - [ ] 4.4 Definir quantos devs/QA vão usar o sistema, para dimensionar o rollout
  - [ ] 4.5 Definir onde o histórico de evidências (prints/vídeos) vai ficar armazenado
  - [ ] 4.6 Atualizar a Seção 8 em `docs/PRDSI1.md` com as respostas, marcando cada uma como resolvida

- [ ] 5.0 Consolidar o critério de avanço para o V2 e registrar a decisão no Work OS
  - [ ] 5.1 Revisar, com os dados de 1.0–4.0, se o critério de avanço do PRD foi atingido (time confirmar que o plano sozinho não basta)
  - [ ] 5.2 Atualizar `docs/problem-brief.md` e `docs/option-matrix.md` com o resultado desta fase
  - [ ] 5.3 Registrar uma linha em `docs/decision-log.md` com a decisão tomada (avançar para V2, ou não, e por quê)
  - [ ] 5.4 Se a decisão for avançar: criar `.claude/adr/adr-002-*.md` formalizando escopo, tooling e onde o V2 roda, seguindo `docs/runbooks/como-registrar-uma-decisao.md`, e registrar no `.claude/memory/adr-index.md`
  - [ ] 5.5 Se a decisão for não avançar: registrar o motivo em `docs/decision-log.md` e manter o V1 como está
