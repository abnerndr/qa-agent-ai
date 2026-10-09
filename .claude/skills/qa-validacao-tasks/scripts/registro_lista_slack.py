#!/usr/bin/env python3
"""scripts/registro_lista_slack.py — extrai um registro de uma Slack List lida pelo MCP do Slack.

Uso:
  registro_lista_slack.py --url '<link da task>'      # imprime list_id e record_id
  registro_lista_slack.py <arquivo> <record_id>       # imprime o registro (campo: valor)

O link de uma task em lista tem o formato
  https://<workspace>.slack.com/lists/<time>/<list_id>?record_id=<record_id>

<arquivo> é a saída de slack_read_list em CSV: o arquivo salvo pela ferramenta quando a
resposta é grande demais, ou um texto colado. Aceita o JSON da ferramenta ({"result": ...})
ou o CSV puro.

Saída 2: registro não está nesta página (leia a próxima com o next_cursor impresso no stderr).
"""
import csv
import io
import json
import re
import sys
from urllib.parse import parse_qs, urlparse


def parse_url(url):
    u = urlparse(url)
    m = re.search(r"/lists/[^/]+/([^/?#]+)", u.path)
    rec = parse_qs(u.query).get("record_id", [None])[0]
    if not m or not rec:
        sys.exit("link não é de um registro de Slack List (esperado /lists/<time>/<lista>?record_id=Rec…)")
    print(f"list_id={m.group(1)}")
    print(f"record_id={rec}")


def extrair(arquivo, record_id):
    raw = open(arquivo, encoding="utf-8").read()
    cursor = ""
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            cursor = data.get("next_cursor") or ""
            raw = data.get("result", raw)
    except json.JSONDecodeError:
        pass
    for row in csv.DictReader(io.StringIO(raw)):
        if row.get("Record ID") == record_id:
            for campo, valor in row.items():
                if valor:
                    print(f"## {campo}\n{valor}\n")
            return
    print(f"registro {record_id} não está nesta página", file=sys.stderr)
    if cursor:
        print(f"next_cursor={cursor}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--url":
        parse_url(sys.argv[2])
    elif len(sys.argv) == 3:
        extrair(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
