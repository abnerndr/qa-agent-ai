#!/bin/bash
# PreToolUse hook (matcher: Write) — lembrete não-bloqueante antes de gravar em outputs/.

input=$(cat)

if echo "$input" | grep -Eq '"file_path"[^}]*outputs/'; then
  echo "Lembrete: antes de gravar em outputs/, confira se há evidência suficiente (pergunta 7 do checklist em docs/work-os-reference.md)."
fi

exit 0
