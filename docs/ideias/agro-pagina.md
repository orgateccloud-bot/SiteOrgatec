# Página Agro: começa pelo dia do produtor, e os pontos da reforma abrem sob demanda (Fase 4)

- **Situação:** em desenvolvimento (código e testes prontos; falta a prévia e a sua aprovação)
- **Branch:** `ideia/agro-pagina` (parte de `ideia/campo-layout`, que junta as Fases 0 a 3)
- **Prévia:** ainda não gerada

## Problema

`setores/agro.html` tinha 11.505 px no celular, e 5.240 px eram os pontos da reforma, todos abertos, com fato, orientação e fontes de uma vez. A Fase 2 deu à página os quatro caminhos e tirou os alertas (10.149 px), mas ela ainda abria com a introdução, não com o que o produtor precisa saber hoje, e não tinha uma chamada clara para a calculadora e para a auditoria rural.

## Público

Produtor rural, no celular.

## O que esta branch muda

Ordem no celular:

1. **Introdução** mais curta (título menor, texto em até 3 linhas, um botão a menos).
2. **Hoje na sua região:** o estado das 5 operações na região que o produtor escolheu na Janela de Campo, lido do boletim publicado (`assets/js/agro-hoje.js`). A região é a mesma da Janela (chave `orgatec.campo`, só neste navegador); trocar aqui troca lá. Sem boletim válido, ou com o boletim vencido ou com mais de 18 horas, a seção fica só com o texto fixo e o link da Janela: nenhum número é escrito sem boletim vigente.
3. **Os quatro caminhos** da Fase 2, em duas colunas no celular, só com o título.
4. **Pontos da reforma para o agro**, recolhidos:
   - Cada ponto mostra a referência (tributos), o status e o título; o fato, a orientação, as fontes e a data de consulta ficam dentro e abrem com o toque ou com Enter. Nada foi omitido.
   - Chips de tema (**Alíquotas e reduções**, **Contribuinte ou não**, **Crédito e insumos**, **Obrigações e transição**), só com os temas que têm item.
   - Sem filtro, os 5 primeiros pontos e o botão "Ver todos os 10 pontos".
   - "Por que importa para o agro" virou um item recolhido acima da lista.
5. **Próximos passos:** a calculadora do produtor ("O produtor é contribuinte?") e a auditoria forense rural, em dois cartões; abaixo, os links do compliance do produtor rural e dos alertas do agro.
6. Faixa final de diagnóstico, com menos espaço no celular.

Mudanças de código:

- `conteudo.js`: campo opcional `tema` nos itens (validado), filtro por tema e `renderItem(item, fontes, { recolhido: true })`. Sem a opção, o HTML dos itens é exatamente o de antes.
- `reforma-itens.js`: o `tema` dos 10 itens do agro. **O agrupamento é editorial**, para organizar a leitura, e vai para revisão do responsável técnico junto com os itens (todos continuam com revisão pendente).
- `gerar_paginas.py`: `setor_agro()` própria; `hero`, `secao` e `faixa_cta` ganharam o modo compacto.

## Medição (Playwright, 375 x 812 e 1280 x 900, ambiente de homologação)

| | Antes | Agora |
|---|---|---|
| Página Agro no celular | 11.505 px | 4.779 px |
| Página Agro no desktop | 5.601 px | 3.498 px |
| Rolagem horizontal | nenhuma | nenhuma |

Com 10 itens do agro e o boletim do dia; com o botão "Ver todos os 10 pontos" apertado, a página cresce em cerca de 600 px. Em produção só aparecem os itens com revisão técnica aprovada; hoje nenhum está aprovado, então a lista fica vazia lá, como já acontecia.

## Fora desta fase

Fases 5 e 6 (satélite, notícias e cotações), a busca por município e a marca Audi Agro (decisão sua, na Fase 2).

## Fontes e validação

Nenhuma regra legal nova: os itens, as fontes e as datas são os mesmos de `reforma-itens.js`. O resumo do dia usa o boletim da Janela de Campo, com as fontes e os limites dela (V20 continua pendente).

## Pronto quando

- Os testes novos passam: item recolhido (JS), tema e filtro, resumo do dia com e sem boletim e com boletim vencido, lista recolhida por tema com fontes, página de até 5.000 px no celular.
- A suíte completa (JS, pytest, e2e) e o bandit estão verdes.
- Prévia aberta em 375 px e 1280 px e aprovada pelo usuário.
