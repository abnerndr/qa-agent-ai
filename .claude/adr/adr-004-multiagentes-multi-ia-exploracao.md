# ADR-004 — Multiagentes, qualquer IA e exploração autônoma

**Status:** Aceito
**Data:** 2026-10-25
**Contexto:** Na branch `project`, o Abner quer tornar o agente de QA genérico (qualquer aplicação, não só PYXYS). Ele pediu três coisas: testar com multiagentes, a skill funcionar com qualquer IA e uma opção de testes autônomos para encontrar erros. Também pediu que tudo gaste menos tokens, porque a execução fica mais longa e deve poder rodar sozinha.

---

## Decisão

1. **Qualquer IA.** A skill segue o formato aberto de Agent Skills (`SKILL.md` + `scripts/`). O `SKILL.md` descreve capacidades (perguntar ao dev, subagentes, MCP do Slack) com a tabela de equivalência por ferramenta e acha a própria pasta (`SK`) em qualquer diretório de skills. O `install-skill.sh` ganha `--ia` (claude, agents, codex, gemini, cursor, copilot, opencode, todas) e `--dir`. A primeira pasta recebe a cópia e o `.venv`; as outras recebem um link para ela. O remoto delega ao local.
2. **Multiagentes.** O `run.json` passa a ser gravado com trava de arquivo (`fcntl`/`msvcrt`) e troca atômica, e os nomes de evidência são reservados com criação exclusiva. Assim vários agentes usam a mesma pasta de execução. O orquestrador mantém os gates (critérios, plano, ok do dev), divide os casos em lotes por página/fluxo (até 4 agentes, a partir de 6 casos) e consolida com o novo `qa status`. O Lighthouse roda sozinho no fim.
3. **Exploração autônoma.** Novo `qa explorar`: BFS só por links da mesma origem (GET, sem clicar nem enviar formulário, ignora logout/exclusão), com seis checks por página (status/link, exceção JS, console.error, rede da própria origem, imagem quebrada, rolagem horizontal) e um sétimo informativo para terceiros. Gera um caso por check (mesmo check em N páginas = um caso). `--falhar` devolve código 1 para cron/CI.
4. **Economia de tokens como regra.** O script trabalha e devolve poucas linhas; a IA lê `status`, resumos e `grep`, e só gasta tokens na triagem dos divergentes.

---

## Alternativas Consideradas

### 1. Crawler/explorador conduzido pela IA (MCP de navegador) (descartada)
Cada página lida pelo modelo custa milhares de tokens; a varredura sem IA custa zero e é reproduzível. A IA entra só na triagem.

### 2. Exploração clicando em botões e preenchendo formulários (descartada por ora)
Risco de criar dado real ou mudar estado no ambiente. Contraria os limites da execução. Interação continua no `fluxo`, com plano e ok do dev.

### 3. Um `run.json` por agente, mesclado no fim (descartada)
Mais um passo e mais chance de perder caso. A trava de arquivo resolve com menos código e mantém o `relatorio` igual.

### 4. Cópia completa da skill (com `.venv`) para cada IA (descartada)
Duplicaria ~115 MB por IA. Link simbólico para a primeira instalação, com cópia só onde link não funciona.

---

## Consequências

**Positivo:**
- O mesmo pacote roda em Claude Code, Codex, Gemini CLI, Cursor, Copilot e OpenCode.
- Planos grandes executam em paralelo sem conflito de escrita.
- Erros fora dos critérios (exceção JS, link quebrado) aparecem sem custo de tokens, e a exploração pode ser agendada.

**Negativo / riscos aceitos:**
- As pastas de skills de outras IAs mudam com o tempo; `--dir` cobre o caso de uma pasta diferente.
- Subagentes recebem só o briefing: se ele for incompleto, o lote volta `pendente`. A consolidação com `status` deixa isso visível.
- A exploração não testa áreas atrás de login nem fluxos interativos.
- O modo automático (Slack + PRD por SSH) continua específico da PYXYS nesta branch.

---

## Adendo (2026-10-25): Kiro, Windows e agente `qa-executor`

- O instalador ganhou o alvo `kiro` (`~/.kiro/skills`) e `--windows`, que no WSL copia a skill para o perfil do Windows, onde rodam Cursor e Kiro. Lá é sempre cópia, porque o Windows não segue link do WSL. A SKILL.md escolhe a primeira instalação com `.venv`, então as cópias do Windows usam o runtime que já existir naquele lado.
- O lote dos multiagentes ganhou um agente próprio, `qa-executor` (`agents/qa-executor.md` na skill), instalado no formato de cada IA: Claude Code e Cursor em `.md` (modelo Haiku/`fast`) e Kiro em `.json`. Ele já traz runtime, regras e formato de resposta, então o briefing fica só com pasta, ambiente e casos. No Codex e nas outras IAs, o subagente da ferramenta recebe o briefing completo.
- Verificado nos binários instalados: o Codex lê `~/.agents/skills` e `~/.codex/skills`; o Cursor lê `~/.cursor/skills`, `~/.claude/skills`, `~/.agents/skills` e `~/.cursor/agents`; o Kiro lê `~/.kiro/skills`, `.agents/skills` e `.claude/skills`, e agentes de usuário em `~/.kiro/agents`. O formato JSON do agente no Kiro IDE não foi validado.
