---
name: tasks-slack-list-px-tech
description: "Tasks do time ficam na Slack List 'PX | Tech 2026' (F0AJ2PGQD4J); link é de registro de lista, não de mensagem"
metadata:
  type: reference
---

As tasks do time Mundo ZeroKM/PYXYS ficam na Slack List **PX | Tech 2026** (list_id `F0AJ2PGQD4J`, time `TC63D2PUJ`). O link de uma task tem o formato `https://pyxys.slack.com/lists/TC63D2PUJ/F0AJ2PGQD4J?record_id=Rec…`, não `/archives/<canal>/p<ts>`.

Colunas úteis: Nome, Status (Backlog → A fazer → Em andamento → Revisão → Em aprovação → Concluído), Projeto, Categoria, Tags, Descrição. A Descrição traz Contexto, O que fazer, Critérios de aceite, Fora de escopo e `*PRD:*` com o caminho em `artefatos/prds/…` (ver [[prds-mzk-pm-workspace]]).

`slack_read_list` não lê um registro só: devolve a lista inteira paginada (~190k caracteres por página de 100), salva em arquivo. Extrair o registro com `scripts/registro_lista_slack.py` da skill qa-validacao-tasks. Comentários do registro não vêm nessa leitura.
