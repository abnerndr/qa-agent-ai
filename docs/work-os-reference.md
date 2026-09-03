# Work OS — Referência Operacional

Conteúdo de apoio para decisões e execução. O CLAUDE.md aponta para cá — este arquivo pode crescer, o CLAUDE.md não.

## Fluxo de trabalho

Frame Goal → Load Context → Ask for Options → Choose with Criteria → Execute in Checkpoints → Verify with Evidence → Review Adversarially → Ship Artifact → Log Decisions → Promote Learning

Em 7 estágios: Objetivo → Contexto → Opções → Decisão → Execução → Verificação → Aprendizado.

## Antes de decidir ou executar — checklist de 12 perguntas

1. **Objetivo** — Que decisão ou artefato é necessário? → Definir sucesso em uma frase.
2. **Contexto** — Quais arquivos, dados e histórico importam? → Carregar só o contexto relevante.
3. **Confiança** — A fonte é oficial, de mercado, comunidade, externa ou desconhecida? → Classificar A/B/C/D/E (ver escala abaixo).
4. **Restrições** — O que limita tempo, orçamento, ferramentas, política ou escopo? → Deixar as restrições explícitas.
5. **Risco** — O que poderia causar uma decisão errada? → Explicitar premissas e modos de falha.
6. **Reversibilidade** — Dá para desfazer com segurança? → Pedir aprovação humana para movimentos irreversíveis.
7. **Evidência** — O que prova que a resposta está correta? → Exigir arquivos, cálculos, testes, fontes ou revisão.
8. **Opções** — Quais alternativas existem? → Comparar probabilidade, esforço, risco e verificação.
9. **Fronteira humana** — O que precisa ficar com o humano? → Manter julgamento, risco e aprovações com a pessoa.
10. **Prontidão para automação** — A regra é clara e repetível? → Só automatizar depois de validação manual.
11. **Segurança** — Toca dado sensível, permissão ou mensagem externa? → Parar, perguntar, registrar e proteger.
12. **Aprendizado** — Isso vai se repetir? → Promover a template, skill, hook ou runbook.

## Padrão de prompt

Ao formular um pedido para o Claude Code, preencher (mentalmente ou por escrito):

- **Contexto** — projeto, arquivos, situação
- **Objetivo** — decisão ou artefato que se quer produzir
- **Papel operacional** — identidade/perfil assumido
- **Pedido** — o que o Claude Code deve fazer
- **Opinião antes de executar** — premissas, riscos e dúvidas antes de agir
- **Critério de sucesso** — como saber que funcionou
- **Evidência necessária** — o que precisa provar que está certo
- **Limites** — o que não pode acontecer sem aprovação
- **Formato de saída** — markdown, tabela, plano, planilha, HTML, JSON etc.

## Fontes e nível de confiança

Pipeline: Coletar → Catalogar → Classificar Confiança → Processar → Pronto para Claude → Usar com Evidência.

Escala de confiança:
- **A** — Fonte oficial
- **B** — Mercado/paper/padrão forte
- **C** — Comunidade/artigo técnico de boa qualidade
- **D** — Coleta externa (impresso, transcrição, exportação)
- **E** — Origem desconhecida

Regra: **sem entrada no catálogo, a fonte não é confiável para decisão.**

Estados de um item de conhecimento: `collected` → `market_reference` / `processed` → `claude_ready`, ou `quarantine` se a origem não for clara.

## Quando usar cada camada

| Situação | Usar |
|---|---|
| A pessoa precisa do mapa do projeto | `README.md` |
| A regra precisa valer sempre, em toda sessão | `CLAUDE.md` |
| A informação precisa sobreviver à conversa | `docs/` |
| A entrada é uma fonte ou referência externa | `knowledge/` |
| O mesmo checklist se repete | `.claude/skills/` |
| A regra é determinística e não pode depender de lembrar | `.claude/hooks/` |
| A precisão precisa ser comprovada de novo a cada vez | `tools/` / `harnesses/` |
| O artefato está pronto para compartilhar ou revisar | `outputs/` |
| A decisão muda a estrutura do próprio projeto | `.claude/adr/` |
| O conhecimento precisa ser lembrado em sessões futuras | `.claude/memory/` |

## Aprovação humana obrigatória antes de:
- Apagar arquivos
- Mudar permissões
- Enviar mensagens externas
- Usar dados sensíveis
- Tomar decisão de negócio irreversível
- Compartilhar informação financeira, jurídica ou de cliente
- Tratar evidência fraca como fato

## Boas práticas
- Manter o CLAUDE.md curto e preciso.
- Mover contexto longo para arquivos Markdown.
- Pedir opções antes de escolher a execução.
- Exigir evidência antes de confiança.
- Usar checkpoints em trabalho arriscado.
- Separar dado-fonte de instrução de projeto.
- Tratar origem desconhecida como quarentena.
- Transformar trabalho repetido em skill.
- Usar hooks para controles determinísticos.
- Criar harnesses quando precisão importa.
- Revisar de forma adversarial antes de compartilhar.
- Registrar decisões e aprendizados a cada sessão.
