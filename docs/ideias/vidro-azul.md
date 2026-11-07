# Vitrine em vidro azul com a logo em holograma

- **Situação:** em prévia (dois modelos para a ORGATEC escolher)
- **Branch:** `ideia/vidro-azul`
- **Prévia:** modelo A https://orgatec-site--ideia-vidro-azul-lz7ujg2j.web.app/inicio.html?vidro=a e modelo B https://orgatec-site--ideia-vidro-azul-lz7ujg2j.web.app/inicio.html?vidro=b (expira em 06/12/2026)

## Problema

O usuário pediu dois modelos da página em vidro azul (glassmorphism), com a logo da ORGATEC ao fundo em holograma.

## Público

Quem chega à vitrine por orgatec.io, em computador e em celular.

## Proposta

Os dois modelos usam a vitrine real e não mudam a página padrão: só agem com `?vidro=a` ou `?vidro=b`. A logo é o símbolo ORGATEC (`orgatec-simbolo-branco.svg`) usado como máscara, fixa atrás da página, e os cartões de vidro desfocam a logo enquanto se rola. A logo inclina com o mouse ou o dedo e fica parada com movimento reduzido. Uma chave "Modelo: Original · A · B" no canto da página permite comparar (existe só nesta prévia e sai quando um modelo for escolhido).

- **A, Noturno:** vidro azul-fumê sobre azul-marinho. Logo em volume, centralizada atrás do título, com feixe de projetor, anéis e leve vibração de cor.
- **B, Cristal:** vidro claro sobre azul vivo. Logo à direita, com varredura de luz, órbita tracejada e cantos de mira; o texto fica à esquerda no computador. O vidro leva um azul escuro por baixo para segurar o texto branco onde a logo passa clara.

Código: `site/assets/css/vidro.css` e `site/assets/js/vidro.js`, ligados só à vitrine em `tools/gerar_paginas.py`.

## Referências

Só inspiração, sem copiar código. A técnica de vidro (fundo translúcido, desfoque do que está atrás e borda clara) vem de tutoriais abertos de glassmorphism. A distinção entre vidro (objeto) e holograma (luz: transparência alta, bordas brilhantes, linhas de varredura, um só tom) vem de um tutorial de botão holográfico em CSS (janeiro de 2026). Do próprio acervo: o vidro Aurora Blue do `OrgConc-landing`, os modelos de Instagram em vidro azul escuro desta pasta (`tools/modelos_instagram.py`) e o HUD do `jarvis`, cujo modo vidro já foi revertido uma vez, o que reforça cuidar da legibilidade.

## Desempenho (medido em 07/11/2026)

Medido no Chromium sem placa de vídeo (renderização por software), com a CPU emulada 4x mais lenta no computador e 6x no celular. Serve para comparar as versões entre si, não para prever um aparelho real. Tempo médio por quadro (16,7 ms = 60 quadros por segundo):

| | Original | Primeira versão | Versão atual |
|---|---|---|---|
| Computador, parado | 19 ms | 110–125 ms | 35 ms |
| Computador, rolando | 17 ms | 125–130 ms | 35 ms |
| Celular, parado | 17 ms | 50 ms | 17 ms |
| Celular, rolando | 17 ms | 53–62 ms | 17–18 ms |

- **O vidro em si não pesa.** Com as animações desligadas, o modelo A faz 60 quadros por segundo, rolando ou parado, com todos os desfoques ligados.
- **O que pesava era o fundo mudar a cada quadro:** todo cartão de vidro por cima refaz o desfoque. O piscar e a varredura de luz dentro do grupo da logo, que tinha `drop-shadow`, custavam mais; depois a flutuação.
- **Mudanças:** brilho estático em camada à parte, sem `mix-blend-mode`, sem piscar e sem flutuação. A varredura, os anéis (A) e a órbita (B) só se mexem numa parte do ciclo de 9 s.
- **Regras no código:** as animações desligam com a página rolada (a logo fica atrás dos cartões) e em aparelho lento, que o `vidro.js` detecta medindo os quadros duas vezes seguidas. Pausar custa mais que desligar. A inclinação pelo ponteiro continua.

## Fontes e validação

Sem regra, alíquota ou prazo. A logo vem do arquivo da marca já usado no site.

## Pronto quando

- A ORGATEC escolhe um modelo (ou pede ajustes).
- O escolhido vira padrão ou tema, e o outro é removido junto com a chave de comparação.
- Teste em aparelho real, de preferência um celular de entrada: as medições abaixo são em navegador sem placa de vídeo.
- A suíte passa nos três navegadores.
