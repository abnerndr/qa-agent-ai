**Título:** Sistema de QA Automático para Validação de Tasks de Dev
**Autor:** Abner
**Data:** 04/09/2026
**Status:** Draft — Planning Review (alinhamento de escopo, antes de comprometer tempo de dev)

---

## 1. Hipótese

Acreditamos que automatizar a extração de critérios de aceite de uma task (hoje colados em texto corrido do Slack) e a geração do plano de teste correspondente vai reduzir a inconsistência na validação de entregas do time, medido por `[NEED: tempo médio hoje gasto validando uma task manualmente]` e pela redução de bugs que escapam por critério mal coberto.

Já existe uma primeira validação: a skill `qa-validacao-tasks`, rodando no Cowork, foi testada e teve feedback positivo em uso individual — a hipótese deste PRD é que vale a pena evoluir isso de skill pontual para um sistema que o time todo usa.

## 2. Problema

**Quem:** Abner hoje, e o time de devs/QA como público-alvo seguinte.

**Como o problema se manifesta:** cada task chega com critérios de aceite diferentes, geralmente soltos dentro de uma mensagem de Slack — sem lista organizada, sem padrão. A validação hoje depende de alguém ler a task, decidir o que testar e testar manualmente, sem registro de evidência de que o critério foi de fato verificado.

**Workaround atual:** validação manual, ad-hoc, sem rastro — o que já é, por si só, sinal de que falta uma ferramenta.

**O que já se provou funcionar:** o piloto (skill no Cowork) extrai os critérios do texto bruto e gera um plano de teste (Playwright para UI, requisição HTTP para API) cobrindo caminho feliz + edge cases, com feedback positivo no uso real.

**O que falta:** o piloto só gera o plano — não executa os testes nem produz evidência (print/vídeo) de que o critério passou. É aqui que mora a decisão deste PRD: vale a pena evoluir para isso, e onde.

**Se não resolvermos:** a aprovação de tasks continua dependendo de julgamento manual não documentado, sem evidência auditável.

## 3. Estratégia / Por que agora

O V1 (skill) já validou a abordagem central — extrair critério + gerar plano de teste — com custo de desenvolvimento baixo. O próximo passo natural é decidir se isso vira um sistema que o time usa de verdade, com execução real e evidência, e onde ele mora.

Alternativas consideradas:
- **Manter só como skill:** simples, mas depende do Cowork estar aberto e de alguém colar a task manualmente — não escala pro time sem fricção.
- **Sistema standalone (Electron ou site):** mais robusto, permite execução real + evidência centralizada, mas exige decidir tooling (Playwright ou outro) e onde ficam prints/vídeos — ainda em aberto.

Trade-off assumido: este PRD **não** resolve essas decisões de tooling agora — o objetivo aqui é alinhar o escopo em fases antes de comprometer tempo de build.

## 4. Solução (em fases)

**V1 — já existe (skill Cowork `qa-validacao-tasks`):**
Dev/QA cola o texto da task → skill extrai critérios de aceite do texto corrido → gera plano de teste (tabela: critério | caso de teste | tipo UI/API | passos | resultado esperado) + edge cases cobertos. Não executa, não gera evidência, não dá veredito.

**V2 — próxima fase (ainda sem tooling definido):**
O sistema passa a executar de fato os testes do plano (ex: Playwright) e gerar evidência da execução — print automático nos passos críticos, vídeo nos fluxos multi-step que exigem — e fecha com veredito por critério: Válido / Inválido, com a evidência anexada.

**V3 — visão, não comprometida ainda:**
Onde isso roda deixa de ser "colar na skill" e passa a ter um lugar fixo. Abner já tem um "Work OS" pessoal na área de trabalho e pretende começar testando o fluxo por ali; a ideia de um app Electron ou um site é cogitada como destino futuro, mas nenhuma dessas decisões está tomada.

**Exemplo de comportamento esperado (V1, já em produção):**
```
Input: "task: no cadastro de concessionária, o campo CNPJ precisa validar
formato e não deixar salvar duplicado. Slack, colado sem formatação."

Output (resumo):
| Critério | Caso de teste | Tipo | Passos | Resultado esperado |
|---|---|---|---|---|
| CNPJ formato válido | Rejeitar CNPJ malformado | UI | Preencher CNPJ inválido, tentar salvar | Erro de validação exibido, não salva |
| CNPJ duplicado | Bloquear duplicidade | API | POST com CNPJ já existente | Retorna erro 409, não cria registro |
Edge cases cobertos: CNPJ vazio, CNPJ com máscara errada, duplicidade com espaços/formatação diferente.
```

## 5. Não-Objetivos (nesta fase)

- V1 **não** executa testes de verdade nem gera evidência — só o plano. Já decidido, não é escopo desta fase.
- V1 **não** se integra a CI/pipeline — uso é manual, colando o texto da task.
- **Não** estamos decidindo neste PRD qual framework de captura de vídeo/print, nem se o destino final é Electron, site, ou o "Work OS" atual — isso fica para uma decisão técnica separada, depois do alinhamento de escopo.
- **Não** estamos substituindo o board de tasks (Slack/Work OS) — o sistema só valida, não gerencia backlog.

## 6. Métricas de Sucesso

| Métrica | Tipo | Baseline | Meta | Prazo |
|---|---|---|---|---|
| Tempo médio de validação manual por task | Primária | `[NEED: medir hoje]` | Reduzir em X% | `[NEED: definir prazo]` |
| Tasks validadas via sistema (adoção no time) | Secundária | 0 | `[NEED: meta de adoção]` | — |
| Critérios cobertos por task (incl. edge cases) | Secundária | — | 100% dos critérios extraídos com pelo menos 1 edge case | — |

**Guardrail:** nenhum aumento de bugs pós-entrega atribuídos a critério marcado como "testado" mas mal coberto.

**Critério para avançar do V1 para o V2:** o time confirmar, em uso real, que o plano de teste sozinho não é suficiente (ainda depende de alguém rodar manualmente) — isso é o sinal de que vale investir em execução real + evidência.

## 7. Plano de Rollout

1. Abner valida a skill em mais tasks reais (uso individual, atual).
2. 1–2 devs do time experimentam a skill em tasks reais deles.
3. Time todo adota como etapa padrão antes de aprovar uma task.
4. Só então se decide o V2 (execução real) e onde ele roda.

**Rollback:** o sistema é aditivo — se não pegar tração, o time simplesmente volta ao processo manual atual, sem custo de migração.

## 8. Questões Em Aberto

- `[NEED: onde o V2 vai rodar de fato — dentro do "Work OS" atual, um app Electron, ou um site?]` — Owner: Abner
- `[NEED: ferramenta de captura de evidência — screenshot/vídeo nativo do Playwright ou outra ferramenta?]` — Owner: Abner
- `[NEED: quantificar tempo/esforço atual gasto validando tasks manualmente]` — pré-requisito pra medir ganho real
- `[NEED: quantos devs/QA vão usar isso, pra dimensionar o rollout]`
- `[NEED: onde o histórico de evidências (prints/vídeos) vai ficar armazenado]`

---

### Checklist — Planning Stage
- [x] Problema definido com segmento de usuário claro
- [x] Estado atual documentado (como o problema é tratado hoje)
- [ ] Métricas de negócio com baseline real — pendente `[NEED]`
- [x] Evidência qualitativa incluída (piloto com feedback positivo)
- [x] Lacunas de conhecimento identificadas com owner
- [ ] Panorama competitivo — não avaliado (ferramenta interna, sem concorrência direta mapeada)
