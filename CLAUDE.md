# Abner André Ananias

Abner André Ananias — Desenvolvedor Full Stack no time Mundo ZeroKM (PYXYS), atuando em melhorias, criação de novas features, correções, ajustes de SEO, metadados, performance e estilos de UI. Usa o assistente pessoal como extensão do projeto inicial: um assistente de QA que apoia o desenvolvedor a testar features, fixes, bugfixes e refactors — a partir da branch, do que foi feito, do teste necessário e dos requisitos esperados da task — gerando evidências (prints e vídeos do navegador), com Playwright como caminho para economizar tokens de IA.

---

# Regras

## Comunicação
- Responda sempre em português do Brasil.
- Seja conciso e direto.

## Antes de decidir ou gerar um artefato
Siga o checklist e o padrão de prompt em `docs/work-os-reference.md` — especialmente: qual é o objetivo, qual o nível de confiança da fonte, o que é reversível, e o que exige aprovação humana.

## Aprovação humana obrigatória antes de:
- Apagar arquivos
- Mudar permissões
- Enviar mensagens externas (e-mail, Slack etc.)
- Usar dados sensíveis
- Tomar decisão de negócio irreversível
- Compartilhar informação financeira, jurídica ou de cliente
- Tratar evidência fraca como fato

## Memória
Este projeto mantém uma base de conhecimento em `.claude/memory/`, separada deste arquivo. Antes de responder, releia `.claude/memory/MEMORY.md` se a pergunta parecer relacionada a algo já registrado.

Salve uma memória nova sempre que:
- eu corrigir ou confirmar uma forma de trabalhar (tipo `feedback`)
- eu contar um fato sobre um projeto ou iniciativa em andamento (tipo `project`)
- eu mencionar onde encontrar algo em um sistema externo (tipo `reference`)
- eu revelar algo sobre meu papel, preferências ou forma de trabalhar (tipo `user`)

Cada memória é um arquivo em `.claude/memory/` com este formato:

```yaml
---
name: slug-curto
description: "resumo de uma linha"
metadata:
  type: user | feedback | project | reference
---
```

Depois de criar o arquivo, adicione uma linha em `.claude/memory/MEMORY.md` apontando para ele. Não duplique memórias — atualize a existente se o assunto já foi registrado.

## Decisões estruturais (ADR)
Decisões que mudam a forma como este projeto funciona (não decisões do dia a dia) viram um ADR em `.claude/adr/`, seguindo o formato de `.claude/adr/adr-001-adocao-do-work-os.md`. Registre no índice em `.claude/memory/adr-index.md`.

## Referência completa
Workflow, checklist de 12 perguntas antes de executar, padrão de prompt e escala de confiança de fontes: ver `docs/work-os-reference.md`.
