---
name: instalacao-wsl-windows
description: "Agente de QA instalado no WSL e no Windows (Claude Desktop); rede do Windows bloqueia cdn.playwright.dev"
metadata:
  type: project
---

Em 2026-10-02 a skill `qa-validacao-tasks` foi instalada em dois lugares: `~/.claude/skills/` no WSL (cópia real; o symlink antigo para `/home/abner/www/skills` foi movido para `~/.claude/backups/`) e `C:\Users\abner\.claude\skills\` no Windows, para o Claude Desktop (aba Code, que roda no Git Bash).

A rede do lado Windows dá timeout em `cdn.playwright.dev`; o WSL baixa normalmente. Os browsers do Windows foram baixados pelo WSL e extraídos em `%LOCALAPPDATA%\ms-playwright`.

**Why:** reinstalar pelo `setup.sh` no Windows falha no `playwright install`.
**How to apply:** ao atualizar a skill, sincronize as duas cópias; se o Playwright mudar de versão, repita o download pelo WSL (ver README, seção Windows).
