---
name: mundozerokm-staging-assistente
description: "Staging do Mundo ZeroKM usa HTTP Basic Auth (Cloudflare); backend do Assistente ZeroKM é um Express público em easypanel"
metadata:
  type: reference
---

- `https://staging.mundozerokm.com.br/` responde 401 `WWW-Authenticate: Basic realm="Staging Area"` — não é login por JS. O `qa_evidencias.py` **não** suporta Basic Auth (não lê `QA_HTTP_USER` e grava headers na evidência): para UI no staging, usar Playwright próprio com `http_credentials` **sem** `origin` (com `origin` deu 401). Credencial em `~/qa-relatorios/mundozerokm-assistente/.credenciais` (600, valores **entre aspas** — remover ao ler); uso autorizado pelo Abner em 2026-10-07. Nunca vai para evidência nem memória.
- Home e notícias abrem um modal de lead (botão `aria-label="Fechar"`) que trava a rolagem: fechar antes de rolar/clicar em links. `networkidle` nunca chega (ads/analytics); usar `domcontentloaded` + espera.
- Assistente ZeroKM (botão flutuante `aria-label="Abrir assistente virtual"` na home) chama `POST https://sistemas-chat-ia-mzk.7seoan.easypanel.host/chat` com `{message, history}` → `{reply, links}`. O histórico vem do cliente.
- Não chamar backends de terceiros com a env de Basic Auth carregada (o header iria para outro host).

Primeira validação: 2026-10-02, relatório em `~/qa-relatorios/mundozerokm-assistente/`. Ver [[qa-validacao-tasks]].
