# Proposta: pré-renderizar itens da reforma, alertas e compliance no HTML

Situação: **proposta, não implementada** (Fase 1, item 6 do prompt). Depende de aprovação.

## Problema (fato verificado)

`paginas.js` preenche, no navegador, os blocos `data-itens`, `data-alertas`, `data-noticias` e `data-linha-tempo` a partir de `reforma-itens.js`, `compliance-itens.js`, `fontes.js` e `regras.js`. No HTML gerado só ficam os blocos vazios. A página de transporte tem 529 palavras no HTML, e a de alertas regionais, perto de 114. Um buscador que não executa JavaScript, ou executa tarde, não vê os itens.

## Proposta

1. O gerador (`gerar_paginas.py` e `paginas_compliance.py`) lê os mesmos arquivos de dados e escreve, dentro de cada `data-itens`, o HTML dos itens que o navegador escreveria hoje. Os blocos de itens usam `<details>`, então o texto fica no HTML sem JavaScript.
2. A regra de "só item aprovado em produção" vai para o gerador: com `ambiente = 'producao'` o gerador não escreve item com revisão pendente. Em homologação escreve todos, com o selo "em revisão técnica".
3. O navegador continua hidratando: `conteudo.js` troca o instantâneo pelo conteúdo vivo (filtros, chips de tema, selos). Sem JavaScript, a página já tem o texto.
4. Alertas regionais dependem de UF e setor escolhidos pelo usuário: o gerador escreve um instantâneo por setor coberto (hoje agro, atacado e indústria) com a UF padrão, e o restante continua no navegador.

## Como evitar duas fontes de verdade

Os dados são arquivos JavaScript no formato de módulo do navegador. Para o Python ler, há duas saídas:

- **A (recomendada):** um passo `node tools/exportar_itens.js` grava `tools/dados/itens.json` a partir dos `.js`, e o gerador lê o JSON. O JSON é derivado e vai ao git para o teste conferir que não está defasado. É o mesmo padrão de `exportar_pendencias.js`.
- **B:** reescrever os itens em JSON e gerar o `.js` a partir dele. Mais limpo, mas muda o fluxo de quem edita os itens.

## Impacto nos testes

- Testes JS de `conteudo.js` e `paginas.js` continuam valendo.
- Novo teste Python: cada página com `data-itens` traz no HTML pelo menos o título de um item conhecido; em modo produção, nenhum item pendente aparece.
- Novo teste: o JSON exportado bate com o `.js` (falha se alguém editar só um dos dois).
- Testes e2e que contam elementos de `[data-itens]` precisam esperar a hidratação, não a criação dos itens; o risco é de contagem duplicada se a hidratação não trocar o instantâneo.

## Riscos e opinião

- **Risco:** conteúdo jurídico duplicado no HTML e no JS. Mitigação: a opção A, com teste de consistência.
- **Opinião (confiança média):** vale mais do que a maioria das mudanças de menu, porque é a única que muda o que o buscador vê. Só tem efeito depois da virada, quando o `noindex` sair.
- **Bloqueio real:** hoje nenhum item está aprovado (V1). Em produção, o gerador escreveria páginas sem itens até a revisão técnica acontecer.
