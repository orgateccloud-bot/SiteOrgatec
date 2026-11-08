# Logo do Noturno igual à do Cristal

- **Situação:** em prévia (pedido do usuário em 08/11/2026)
- **Branch:** `ideia/vidro-logo-cristal`
- **Prévia:** a gerar com `python tools/previa.py`

## Problema

A vitrine em vidro azul (modelo A, Noturno) já está no ar, com a logo centralizada atrás do título, feixe de projetor e anéis sob a esfera. O usuário preferiu a logo do modelo Cristal (B) e pediu: "eu quero que a logo no noturno fique que nem a do cristal".

## Público

Quem chega à vitrine por orgatec.io, em computador e em celular.

## Proposta

A logo do Noturno passa a ter a composição e o acabamento da do Cristal, mantendo o fundo azul-marinho e o vidro escuro:

- **Posição e tamanho:** esfera grande à direita (centro a 77% da largura, `min(80vmin, 720px)`); no celular, 150vw, cortada à direita.
- **Acabamento:** degradê de branco a ciano (`#FFFFFF`, `#BAE6FD`, `#38BDF8`), linhas de varredura em azul, brilho mais claro e varredura de luz.
- **Elementos:** órbita tracejada que avança em passos e cantos de mira. Saem o feixe de projetor e os anéis.
- **Texto:** no computador (1024 px ou mais), o herói fica alinhado à esquerda, como no Cristal, para a logo ocupar a direita. No tablet e no celular continua centralizado.
- **Legibilidade:** o registro no CRC passa para um azul mais claro, porque cai sobre a parte clara da esfera.

O código está em `site/assets/css/vidro.css` e `site/assets/js/vidro.js`. As regras de desempenho continuam: animações desligadas com a página rolada e em aparelho lento.

## Fontes e validação

Sem regra, alíquota ou prazo.

## Desempenho (medido em 08/11/2026)

Mesmo método da ideia `vidro-azul` (Chromium sem placa de vídeo, CPU 4x mais lenta no computador e 6x no celular). Tempo médio por quadro, parado no herói:

| | Antes (logo centralizada) | Agora |
|---|---|---|
| Computador | 35 ms | 46 ms |
| Celular | 17 ms | 17 ms |

A órbita e a varredura de luz somam cerca de 14 ms no computador emulado. Só existem no herói: com a página rolada ou em aparelho lento, as animações desligam.

## Pronto quando

- A ORGATEC confere a logo no computador, no tablet e no celular.
- A suíte passa.
- Aprovada, integra na `desenvolvimento` e vai ao ar pelo `tools/publicar.py`, com autorização.
