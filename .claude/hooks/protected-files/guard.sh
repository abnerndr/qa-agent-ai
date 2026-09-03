#!/bin/bash
# PreToolUse (matcher: Bash) — bloqueia comandos destrutivos sobre arquivos-chave do Work OS.
input=$(cat)

# Isola SOMENTE o valor de "command" (evita casar com "description"/"cwd"/paths do payload)
cmd=$(printf '%s' "$input" \
  | sed -e 's/.*"command"[[:space:]]*:[[:space:]]*"//' -e 's/"[[:space:]]*[,}].*$//')

PROTECTED='CLAUDE\.md|\.claude/adr|\.claude/memory|docs/decision-log\.md'
DESTRUTIVO='(^|[;&|[:space:]])(rm|mv|shred|truncate|dd)([[:space:]]|$)|>[[:space:]]*[^>]*(CLAUDE\.md|decision-log\.md)'

# Avalia por trecho (separado por ; && || |), não o comando inteiro de uma vez --
# evita bloquear comando composto onde o verbo destrutivo e o nome protegido
# aparecem em partes independentes (ex: "echo sobre CLAUDE.md; rm outra_coisa").
bloqueado=0
while IFS= read -r trecho; do
  [ -z "$trecho" ] && continue
  if printf '%s' "$trecho" | grep -Eq "$DESTRUTIVO" && printf '%s' "$trecho" | grep -Eq "$PROTECTED"; then
    bloqueado=1
    break
  fi
done < <(printf '%s\n' "$cmd" | sed -E 's/(&&|\|\|)/\n/g' | tr ';|' '\n\n')

if [ "$bloqueado" -eq 1 ]; then
  echo "Bloqueado: este comando parece apagar ou sobrescrever um arquivo protegido do Work OS (CLAUDE.md, .claude/adr/, .claude/memory/ ou docs/decision-log.md). Confirme com a pessoa antes de continuar." >&2
  exit 2
fi
exit 0
