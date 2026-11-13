# Mapa dos sistemas (Graphify)

- **Situação:** implementada em 12/11/2026; suíte verde em 13/11/2026; prévia conferida em celular (390 px) e desktop (1366 px), sem rolagem horizontal da página; textos dos módulos aprovados sem alteração em 13/11/2026; aguarda a decisão sobre o OrgAudi
- **Branch:** `ideia/plataforma-grafo` (pasta `SiteOrgatec-plataforma-grafo`), movida da `SiteOrgatec-dev` em 13/11/2026
- **Prévia:** https://orgatec-site--ideia-plataforma-grafo-i1gf2pty.web.app/solucoes/plataforma.html

## Problema

A página de Soluções diz o que cada sistema faz, mas não mostra que por trás há software próprio, organizado e revisável.

## Público

Escritórios e empresas avaliando a conciliação bancária e a auditoria rural; quem quer saber se o sistema é "de verdade".

## Proposta

Nova página `solucoes/plataforma.html` ("Como os sistemas são construídos"), no menu Serviços. Um mapa por sistema
(OrgConc e OrgAudi), módulo por módulo, com as ligações entre eles, desenhado em SVG estático (sem script, compatível com a CSP).

- `tools/plataforma_curar.py` reduz o `graph.json` do Graphify ao nível de módulo e grava `tools/plataforma_grafo.json`.
  Só passa o que está mapeado em `SISTEMAS`; nomes de arquivo, função, tabela e comentários ficam de fora.
- `tools/paginas_plataforma.py` gera a página a partir desse JSON (chamado por `gerar_paginas.py`).
- `tests/py/test_plataforma.py` barra campos extras no JSON e nome de arquivo ou caminho de código na página.

Atualizar o mapa:

```bash
# em cada repositório (OrgConc e OrgAudi), só código, sem IA:
GRAPHIFY_BACKEND=none GRAPHIFY_QUERY_LOG_DISABLE=1 graphify extract . --code-only --no-viz
# no site:
python tools/plataforma_curar.py --orgconc ../OrgConc/graphify-out/graph.json --orgaudi ../OrgAudi/graphify-out/graph.json
python tools/gerar_paginas.py && python tools/compilar_css.py
```

No Windows (PowerShell), defina as variáveis com `$env:GRAPHIFY_BACKEND="none"` antes do comando.

## Fontes e validação

- Grafo gerado com Graphify 0.9.108 em 12/11/2026, a partir do código de `OrgConc/api` e de `OrgAudi/api`, `nfa_extractor` e `pdf_engine`
  (sem `_legacy`, scripts avulsos, `.env` ou laudos).
- Os textos de cada módulo (em `SISTEMAS`, no curador) foram escritos a partir dos nomes das pastas e revisados pelo usuário em
  13/11/2026, que os aprovou como estavam (decisão D6 do plano de incorporação). Os `graph.json` não ficaram nas pastas dos sistemas:
  para mudar um texto sem gerar o grafo de novo, altere `SISTEMAS` e `tools/plataforma_grafo.json` juntos.
- Limite conhecido do Graphify (testado em 12/11/2026): chamadas a métodos herdados, feitas pela instância, não são capturadas.
  A página avisa isso.

## Pronto quando

- Textos dos módulos revisados. **Feito em 13/11/2026.**
- Decidido se mostrar a arquitetura do OrgAudi em público é aceitável enquanto ele é só de uso interno.
- `python tools/gerar_paginas.py`, `compilar_css.py` e a suíte passando; prévia conferida em celular e desktop.
