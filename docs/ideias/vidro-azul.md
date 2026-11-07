# Vitrine em vidro azul com a logo em holograma

- **Situação:** em prévia (dois modelos para a ORGATEC escolher)
- **Branch:** `ideia/vidro-azul`
- **Prévia:** modelo A com `inicio.html?vidro=a` e modelo B com `inicio.html?vidro=b` (endereço da prévia no registro de ideias)

## Problema

O usuário pediu dois modelos da página em vidro azul (glassmorphism), com a logo da ORGATEC ao fundo em holograma.

## Público

Quem chega à vitrine por orgatec.io, em computador e em celular.

## Proposta

Os dois modelos usam a vitrine real e não mudam a página padrão: só agem com `?vidro=a` ou `?vidro=b`. A logo é o símbolo ORGATEC (`orgatec-simbolo-branco.svg`) usado como máscara, fixa atrás da página, e os cartões de vidro desfocam a logo enquanto se rola. A logo inclina com o mouse ou o dedo e fica parada com movimento reduzido.

- **A, Noturno:** vidro azul-fumê sobre azul-marinho. Logo em volume, centralizada atrás do título, com feixe de projetor, anéis e leve vibração de cor.
- **B, Cristal:** vidro claro sobre azul vivo. Logo à direita, com varredura de luz, órbita tracejada e cantos de mira; o texto fica à esquerda no computador. O vidro leva um azul escuro por baixo para segurar o texto branco onde a logo passa clara.

Código: `site/assets/css/vidro.css` e `site/assets/js/vidro.js`, ligados só à vitrine em `tools/gerar_paginas.py`.

## Referências

Só inspiração, sem copiar código. A técnica de vidro (fundo translúcido, desfoque do que está atrás e borda clara) vem de tutoriais abertos de glassmorphism. A distinção entre vidro (objeto) e holograma (luz: transparência alta, bordas brilhantes, linhas de varredura, um só tom) vem de um tutorial de botão holográfico em CSS (janeiro de 2026). Do próprio acervo: o vidro Aurora Blue do `OrgConc-landing`, os modelos de Instagram em vidro azul escuro desta pasta (`tools/modelos_instagram.py`) e o HUD do `jarvis`, cujo modo vidro já foi revertido uma vez, o que reforça cuidar da legibilidade.

## Fontes e validação

Sem regra, alíquota ou prazo. A logo vem do arquivo da marca já usado no site.

## Pronto quando

- A ORGATEC escolhe um modelo (ou pede ajustes).
- O escolhido vira padrão ou tema, e o outro é removido. Antes disso, medir o custo do desfoque em celular de entrada: são cerca de 30 elementos com `backdrop-filter` sobre uma camada animada.
- A suíte passa nos três navegadores.
