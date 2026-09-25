# ADR-002 — Captura de evidências e relatório PDF pelo agente de QA

**Status:** Aceito
**Data:** 2026-09-25
**Contexto:** Primeira validação real da skill `qa-validacao-tasks`, na PR #516 do `mundo-zero-km-nextjs` (padronização de paginação). O plano de teste saiu com 17 casos, 9 deles de requisição HTTP. Conduzir o dev caso a caso, com ele colando cada saída de `curl` e cada print, tornou-se o gargalo. O Abner decidiu que a busca de evidências passa a ser do agente e que toda execução termina num relatório PDF.

---

## Decisão

A skill `qa-validacao-tasks` passa a:

1. **Executar os casos** contra o ambiente indicado pelo dev e capturar evidências com um script Python próprio (`scripts/qa_evidencias.py`, Playwright). O script cobre requisições HTTP sem seguir redirect, prints (desktop/mobile, com e sem JS) e fluxos de clique com vídeo.
2. **Gerar um relatório PDF** com o plano, as divergências entre entrega e task, o status por caso e todas as evidências, **inclusive dos casos que falharam ou ficaram pendentes**.
3. **Continuar sem veredito**: o relatório mostra o observado, e a aprovação da task segue com o dev/PM.

A skill leva o próprio runtime (`scripts/setup.sh` cria `.venv` com Playwright + Chromium), instalado pelos scripts de instalação local e remota.

Isso antecipa parte do **V2** do `docs/PRDSI1.md` (executar testes e gerar evidência), que estava marcado como "não aprovado até uso real".

---

## Alternativas Consideradas

### 1. Manter o V1: o dev executa e cola as evidências (descartada)

Não depende de runtime. Mas o uso real na PR #516 mostrou que o custo de ida e volta por caso inviabiliza planos com mais de 10 casos. Também não havia um artefato final compartilhável.

### 2. Subagente dedicado (`.claude/agents/qa-executor.md`) (adiada)

Isolaria o contexto pesado da execução. Por outro lado, perde a portabilidade da instalação via `install-skill-remote.sh` e ainda não há volume que justifique. Deve ser revisitado se as execuções começarem a estourar o contexto.

### 3. Runtime em Node (`npx playwright`) (descartada)

O repositório alvo nem sempre tem Playwright, e scripts ESM não resolvem módulos instalados via `npx -p`. Python com venv próprio da skill isola o runtime do projeto testado. Pedido explícito do Abner por Python.

---

## Consequências

**Positivo:**
- A execução de um plano inteiro acontece numa sessão, sem o dev colar saídas.
- O PDF vira evidência única e compartilhável da task, com falhas incluídas.
- O runtime é isolado do projeto testado, que não recebe nenhuma dependência nova.

**Negativo / riscos aceitos:**
- O agente passa a agir sobre o ambiente. Mitigação na própria skill: só leitura, só no ambiente indicado, nunca produção sem autorização, nunca enviar formulário que crie dado real (lead, pedido, pagamento) sem aprovação por caso.
- Instalação mais pesada (~115 MB do Chromium) e exige `uv` ou `python3-venv`.
- Evidências podem capturar dados sensíveis (headers, prints logados). A skill instrui a avisar e mascarar antes de compartilhar.
- As perguntas em aberto do PRD sobre o V2 (onde roda, CI, custo) continuam em aberto. Esta decisão cobre só a execução local, conduzida pelo dev.
