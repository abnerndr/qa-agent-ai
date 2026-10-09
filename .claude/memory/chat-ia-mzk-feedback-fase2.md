---
name: chat-ia-mzk-feedback-fase2
description: "Onde está o código do chat IA do Mundo Zerokm (backend chat-ia-mzk + front staging-veezor) e o plano de QA da Fase 2 (feedback)"
metadata:
  type: project
---

- Backend: `/home/abner/www/pyxys/chat-ia-mzk` (Express, `mzk-chat-agent`), local em `http://localhost:3339`. Rotas `/chat`, `/chat/proactive`, `/feedback`; token por `?token=`; feedback inválido responde 200 `{ok:true}` sem gravar (degradação silenciosa por contrato). Persistência em arquivo (`CONVERSATIONS_DIR`).
- Front: `mundo-zero-km-nextjs`, branch `staging-veezor` — `src/components/common/Chat/` (`ChatWidget`, `MessageFeedback`, `useFeedbackToken`, `ContentOfferTrigger`) + `src/lib/redux/chat/chatSlice.ts`. A branch `#feature/chat-ia` é antiga, sem feedback.
- Plano de QA de 2026-10-07 com CA1–CA16 (ajustes pedidos pela Aline Goto, PM; dev Vinicius Rodrigues). Relatório anterior: 2026-10-02.

Ver [[mundozerokm-staging-assistente]] e [[qa-validacao-tasks]].
