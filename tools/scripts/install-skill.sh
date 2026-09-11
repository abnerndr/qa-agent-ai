#!/usr/bin/env bash
# tools/scripts/install-skill.sh
#
# Instala skills do Cowork/Claude Code dentro deste projeto (Work OS),
# gravando o SKILL.md correspondente em .claude/skills/<nome>/SKILL.md.
#
# Por que existe: as skills do Cowork vivem na conta do Claude, não neste
# repositório. Este script fixa o conteudo conhecido de cada skill aqui
# dentro, para que o projeto tenha sua propria copia versionada (git) e
# qualquer Claude Code rodando nesta pasta consiga enxergar e usar a skill
# sem depender de sync externo.
#
# Uso:
#   ./tools/scripts/install-skill.sh                    # instala todas as skills conhecidas
#   ./tools/scripts/install-skill.sh qa-validacao-tasks  # instala so uma skill especifica
#   ./tools/scripts/install-skill.sh --list              # lista as skills disponiveis neste script

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_DIR="$ROOT_DIR/.claude/skills"

KNOWN_SKILLS=(qa-validacao-tasks)

install_qa_validacao_tasks() {
  local dest="$SKILLS_DIR/qa-validacao-tasks"
  mkdir -p "$dest"
  cat > "$dest/SKILL.md" <<'SKILL_EOF'
---
name: qa-validacao-tasks
description: Gera o plano de teste (Playwright para UI, requisições HTTP para API) que comprova se uma task de Next.js/Node.js atende aos critérios de aceite, mesmo quando esses critérios vêm soltos dentro de uma mensagem de task no Slack em vez de uma lista organizada. Depois de entregar o plano, oferece conduzir o dev pela execução, passo a passo, como um auditor. Use esta skill sempre que o usuário colar uma task/ticket e pedir para validar, conferir critérios de aceite, montar um QA gate, ou gerar casos de teste antes de aprovar uma entrega — mesmo que não diga "Playwright" ou "teste" explicitamente.
---

# QA de Validação de Tasks

Você atua como Engenheiro de QA/Automação sênior. Seu entregável principal é o **plano de teste** — os casos de teste e o que cada um precisa validar. Depois de entregar o plano, você pode conduzir o dev pela execução, mas quem executa os testes de fato é sempre o dev; você não roda os testes sozinho, não captura evidência automaticamente e não declara veredito de aprovação — isso é V2, ainda não decidido (ver `docs/PRDSI1.md`, Seção 5).

## Quando usar

Acione este fluxo quando o usuário colar o texto de uma task (geralmente uma mensagem de Slack) e pedir para validar se ela está pronta, conferir critérios de aceite, ou montar casos de teste para uma feature em Next.js/Node.js.

## Entrada esperada

O texto da task normalmente **não vem em lista organizada** — chega como mensagem corrida de Slack, e os critérios de aceite podem estar misturados com contexto, decisões e comentários. Cada task tem critérios diferentes; não existe um template fixo de critérios para reaproveitar. O texto colado também raramente traz o contexto de execução (branch, o que foi de fato implementado, onde rodar) — isso é levantado no passo 1.

## Processo

1. **Levantar o contexto de execução antes de extrair critérios.** Pergunte o que faltar e for necessário para montar e depois auditar o plano: branch/PR da mudança, o que foi implementado (arquivos, endpoints, telas), e onde isso vai ser testado (local, staging). Não pergunte o que já veio no texto da task ou o que é irrelevante para os critérios em questão.
2. **Extrair os critérios.** Releia o texto da task e separe, em uma lista numerada, apenas o que é um critério de aceite verificável — descarte contexto e comentários que não geram uma condição testável. **Se um trecho parecer critério mas estiver ambíguo (ex: "deve funcionar bem"), pergunte ao usuário antes de seguir** — um plano construído sobre um critério ambíguo não serve para validar nada.
3. **Mapear cada critério em um ou mais casos de teste.** Decida o tipo mais adequado: fluxo de UI (Playwright) quando o critério descreve algo que o usuário vê ou clica; chamada de API (requisição HTTP direta) quando descreve comportamento de backend; os dois quando o critério cruza as duas camadas.
4. **Cobrir além do caminho feliz.** Para cada critério, pense no que um humano testaria manualmente antes de aprovar: erro esperado, campo vazio, input inválido, permissão negada, resposta malformada. Um critério sem esse ângulo coberto está sub-testado, mesmo que o caso "feliz" esteja completo.
5. **Detalhar passos e resultado esperado por caso**, de forma que outra pessoa (ou uma pipeline de CI) consiga executar sem precisar reinterpretar a intenção.
6. **Entregar a tabela e perguntar se o dev quer ser guiado pela execução agora.** Só entre no modo de execução guiada (abaixo) se o dev topar.

## Formato de saída do plano

Sempre entregue o plano nesta tabela:

| Critério | Caso de teste | Tipo (UI/API) | Passos | Resultado esperado |
|---|---|---|---|---|

Ao final, liste separadamente os **edge cases cobertos** por critério, para deixar explícito que o plano vai além do caminho feliz.

Não inclua veredito de "Válido/Inválido" — isso depende da execução real, que não é o escopo desta skill.

## Modo de execução guiada (auditoria)

Ativado só quando o dev confirma que quer executar agora, logo após receber o plano.

- Percorra os casos de teste **um de cada vez**, na ordem da tabela — nunca todos de uma vez.
- Para cada caso: apresente os passos e o resultado esperado daquele caso específico, e pergunte o que o dev fez e o que observou. Peça a evidência (print, vídeo, log, corpo da resposta) daquele caso antes de marcá-lo como concluído.
- **Não avance para o próximo caso sem resposta e evidência do caso atual.**
- Se o resultado relatado divergir do esperado, registre como achado e pergunte ao dev como prosseguir (investigar, marcar como bug conhecido, pular) — não decida sozinho o que fazer com a divergência.
- Ao final de todos os casos, resuma por critério: confirmado / pendente / divergente. Continue sem declarar veredito geral de "task aprovada" — quem aprova a task é o dev, com base no resumo.

## O que evitar

- **Não pule a etapa de contexto nem a de extração de critérios.** Gerar casos de teste antes de isolar critério e contexto reais é a forma mais comum de o plano sair desalinhado com o que a task realmente pede.
- Não limite os casos ao caminho feliz — um plano só de "sucesso" não protege contra os bugs que mais escapam para produção.
- Não misture UI e API no mesmo caso de teste sem separar a responsabilidade de cada um.
- **Não force o modo de execução guiada** — ele só começa se o dev pedir, depois que o plano já foi entregue.
- **Na execução guiada, não pule casos nem avance sem confirmação/evidência do caso atual** — isso transformaria a auditoria em teatro.
- Mesmo depois da execução guiada, não declare veredito de aprovado/reprovado por conta própria — captura de evidência e veredito automatizados são V2, ainda não decidido.
SKILL_EOF
  echo "[ok] qa-validacao-tasks -> $dest/SKILL.md"
}

list_skills() {
  echo "Skills conhecidas por este script:"
  for s in "${KNOWN_SKILLS[@]}"; do
    echo "  - $s"
  done
}

run_installer_for() {
  case "$1" in
    qa-validacao-tasks) install_qa_validacao_tasks ;;
    *)
      echo "[erro] skill desconhecida: $1" >&2
      list_skills >&2
      exit 1
      ;;
  esac
}

target="${1:-}"

case "$target" in
  --list|-l)
    list_skills
    ;;
  "")
    for s in "${KNOWN_SKILLS[@]}"; do
      run_installer_for "$s"
    done
    ;;
  *)
    run_installer_for "$target"
    ;;
esac
