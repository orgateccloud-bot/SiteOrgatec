# Agro: uma entrada única para o produtor rural (Fase 2)

- **Situação:** aprovada em 07/11/2026 e publicada: no ar desde 08/11/2026 (tag `publicado-20261108-0650`); branch mantida até o lançamento definitivo
- **Branch:** `ideia/agro-hub` (parte de `desenvolvimento`; independente das branches `ideia/campo-confiabilidade` e `ideia/campo-qualidade`)
- **Prévia:** [link](https://orgatec-site--ideia-agro-hub-kk86piet.web.app/setores/agro.html) (expira em 07/12/2026)

## Problema

O conteúdo para o produtor rural está espalhado em sete lugares, sem um caminho entre eles: `setores/agro.html`, `setores/regional.html`, a Janela de Campo, a calculadora (`ferramentas/index.html#produtor`), `compliance/publico/produtor-rural.html`, `solucoes/auditoria-rural.html` e os itens da reforma. Além disso:

- Os alertas do agro apareciam duas vezes, em `agro.html` (com seletor de estado) e em `regional.html`.
- Os cards por atividade (cotações e notícias) ocupavam 4.916 px, 35% da Janela de Campo no celular, e empurravam o contato para baixo.
- A marca Orgatec Audi Agro só aparecia no fim da Janela de Campo.

## Público

Produtor rural, que hoje não sabe por onde começar, e a equipe, que quer levá-lo do tempo e do preço ao diagnóstico.

## O que esta branch muda

1. **`setores/agro.html` vira a entrada do produtor.** Logo depois da subnavegação, quatro caminhos:
   - **Tempo:** Janela de Campo.
   - **Mercado:** Cotações e notícias (página nova).
   - **Tributos e obrigações:** a lista de pontos da reforma da própria página, a calculadora do produtor, o compliance do produtor rural e os alertas regionais do agro.
   - **Serviços:** auditoria forense rural e o contato.
2. **Página nova `setores/agro-mercado.html`** (Cotações e notícias). Os cards por atividade saíram da Janela de Campo, com os mesmos widgets do CEPEA e os mesmos avisos de falha (a marca foi retirada, ver abaixo). `tools/gerar_paginas.py` passa a ter `agro_mercado()`.
3. **A Janela de Campo fica só com o boletim** e um bloco com o link para as cotações e notícias. No celular, a página caiu de 14.092 px para 9.772 px (a meta final, de até 5.000 px, é da Fase 3, que reorganiza o boletim).
4. **Alertas do agro numa página só.** `agro.html` perde a lista e o seletor e ganha o botão "Ver os alertas do agro por estado", que abre `regional.html?setor=agro`. `regional.html` agora entende `?setor=` e `?uf=` (valores inválidos voltam ao padrão, Goiás e Agronegócio). Nenhum conteúdo foi apagado: os alertas continuam em `regional.html`, com a mesma fonte legal de cada ponto.
5. **Subnavegação e menu.** "Cotações e notícias" entra na subnavegação dos setores, no menu "Setores" e no mapa do site.

Nenhum endereço antigo deixou de existir, então não há redirecionamento a fazer. Só mudou o conteúdo de `agro.html` (sem a lista de alertas) e de `janela-de-campo.html` (sem os cards). Quem tinha `janela-de-campo.html#agroTitulo` salvo cai no topo da Janela; não encontrei esse tipo de link no site.

## Decidido em 07/11/2026: a marca sai por enquanto

Você pediu para tirar a marca Orgatec Audi Agro e decidir depois onde ela entra. A proposta de realocação que estava aqui fica suspensa. O que foi feito:

- **Página de cotações e notícias:** sem o selo, sem o nome e sem o verde e o preto da marca. A seção abre com "Mercado" e usa as cores do site; as cores do widget do CEPEA também ficaram neutras.
- **Interruptor:** `tools/agro_fontes.json` ganhou `marca.exibir` (hoje `false`). Para a marca voltar, basta mudar para `true` e rodar `python tools/gerar_paginas.py`: o selo, o nome e as cores voltam. O arquivo do logotipo (`site/assets/marca/orgatec-audi-agro.png`) continua no site. Isso é testado em `tests/py/test_marca_agro.py`.
- **Ainda mostra a marca:** o rodízio de logotipos do holograma da abertura (`abertura`), que é outra coisa e não foi mexido. Os nomes internos das classes CSS (`audi-agro-*`) ficaram como estão, para a volta ser simples.

## Fontes e validação

Nada de regra legal ou de dado novo: os alertas, os itens da reforma, o compliance e os cards são os mesmos, só em outros lugares. Os links para fontes oficiais seguem como estavam.

## Pronto quando

- Os testes e2e novos e alterados passam: quatro caminhos com os links esperados, alertas só em `regional.html` e abrindo no setor e no estado do link, Janela sem os cards e com o link, subnavegação com a página nova, cards na página de mercado.
- A suíte completa (JS, pytest, e2e) e o bandit estão verdes.
- Prévia aberta no celular e aprovada pelo usuário.
- Decisão sobre a marca.
