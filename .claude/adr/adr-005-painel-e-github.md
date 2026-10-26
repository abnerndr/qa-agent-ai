# ADR-005 — Painel estático e issues/PR no GitHub a partir do relatório

**Status:** Aceito
**Data:** 2026-10-25
**Contexto:** Com exploração autônoma e várias aplicações (ADR-004), o usuário precisa ver o que foi testado em cada aplicação sem abrir PDF por PDF. O Abner também pediu que o agente crie issues e PR no GitHub a partir do que o relatório devolver, com o acesso aos repositórios configurado num `.env`.

---

## Decisão

1. **`qa painel`** gera um `index.html` estático em `$QA_REPORTS_DIR`, lendo os `run.json` das execuções e agrupando por aplicação (`projeto`, ou o host do ambiente). O painel mostra status por caso, ambientes, links do PDF, das issues e do PR, além de busca e filtros. Não tem servidor, banco nem dependência.
2. **`qa github check | issues | pr`** usa a API REST do GitHub com token de `~/.config/qa-agent/.env` (`QA_GITHUB_TOKEN`, mapa `QA_GITHUB_REPOS=projeto=dono/repo`, `QA_GITHUB_REPO`, `QA_GITHUB_LABELS`, `QA_GITHUB_API`). Sem token, cai no `gh auth token`. Sem repositório configurado, usa o `git remote` da pasta atual.
   - Uma issue por caso divergente, com rótulo e marcador HTML que evitam duplicar. O link é gravado de volta no caso.
   - O PR sai de uma branch já enviada, como rascunho por padrão, com a tabela dos achados e `Closes #n`.
   - **Sem `--criar`, só mostra a prévia.** A skill exige o ok do dev antes de `--criar` e de `git push` (regra de aprovação humana para envio externo do CLAUDE.md).
   - O script recusa corpo que pareça conter credencial, e o corpo não leva caminho absoluto da máquina.

---

## Alternativas Consideradas

### 1. Painel web com servidor (gerenciar testes e ambientes) (adiada)
Exige login, guarda de credenciais dos ambientes e hospedagem. O painel estático cobre a visualização agora; o servidor volta à mesa quando outras pessoas usarem ou a exploração rodar agendada todo dia.

### 2. Só `gh` CLI (descartada)
Nem toda IA ou máquina tem `gh` logado, e o pedido foi configurar por `.env`. O `gh` virou fallback.

### 3. `.env` dentro da pasta da skill (descartada)
O instalador sobrescreve a pasta e ela é copiada/linkada para várias IAs. Com o arquivo em `~/.config/qa-agent/`, o token fica fora de qualquer repositório.

### 4. Criar issues automaticamente ao fim da execução (descartada)
Publicaria achado não triado (e possivelmente dado de cliente) sem revisão. A prévia seguida de confirmação mantém o gate humano.

---

## Consequências

**Positivo:**
- Uma página mostra o histórico de QA de todas as aplicações.
- Achados viram issues rastreáveis sem copiar e colar, e o PR da correção já fecha as issues.

**Negativo / riscos aceitos:**
- As imagens de evidência não sobem pela API; a issue lista os arquivos e o dev anexa à mão se quiser.
- O token fine-grained precisa ser renovado e autorizado por SSO quando a org exigir.
- O painel precisa ser regenerado (`qa painel`) depois de cada execução; a skill faz isso no passo 7.
