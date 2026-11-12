# Janela de Campo: mapa de satélite com visual novo

- **Situação:** implementada em 12/11/2026 na branch `ideia/campo-mapa-moderno`; **aguarda a sua aprovação da prévia**. Não publicada.
- **Branch:** `ideia/campo-mapa-moderno` (parte da `desenvolvimento`)
- **Prévia:** [link](https://orgatec-site--ideia-campo-mapa-moderno-weu5fxse.web.app/rural/janela-de-campo.html) (expira em 12/12/2026). Usa o boletim real do ar.

## Problema

O mapa de satélite da Janela de Campo ("Satélite e polos agrícolas") tinha a cara da Fase 5: botões e caixas de marcar soltos acima da imagem, polos como bolinhas de 20 px com um caractere dentro, botão "Animar 2 h" retangular, controle de horário padrão do navegador e legenda com um parágrafo. Funcionava, mas destoava dos cartões, glifos e da barra do local que a Janela de Campo 2 (V1 a V4) trouxe.

## O que muda (só no mapa; `site/assets/js/campo-mapa.js` e o CSS dele)

1. **Um cartão só.** Controles, imagem, linha do tempo e legenda ficam dentro de um cartão de vidro (borda fina, cantos de 20 px, desfoque do fundo), como o resto do site no tema Azul flutuante.
2. **Camada em controle segmentado** ("Nuvens" e "Cor real") e **chuva e divisas em chaves** de ligar e desligar. Continuam sendo dois botões com `aria-pressed` e duas caixas de marcar para leitor de tela e teclado; o nome completo ("Nuvens (infravermelho)", "Chuva estimada (NASA IMERG)") fica no `title` e no texto para leitor de tela.
3. **Polos com os glifos da página.** Cada polo usa o mesmo desenho dos cartões e da grade das regiões: cheio com ✓, vazado com !, cheio com ✕, pontilhado com –, sobre um disco branco com sombra para ler em cima de qualquer cor da imagem. De 20 para 28 px no desktop e 22 px no celular.
4. **Polo escolhido em destaque.** O polo da barra do local ("Sorriso · MT") aparece maior, com um anel que pulsa e o nome sempre à vista. Os outros mostram o nome ao passar o mouse ou focar; na metade direita do mapa o nome abre para a esquerda, para não sair da imagem.
5. **Contagem por estado sobre a imagem.** No canto do mapa: quantos polos estão favoráveis, com restrição, a evitar ou sem previsão para a operação escolhida (glifo, número e texto; no celular, glifo e número, com o texto para leitor de tela). Muda ao trocar a operação.
6. **Linha do tempo nova.** Botão redondo de tocar e pausar (com rótulo "Animar as últimas 2 horas" e "Pausar a animação"), trilho com o trecho já percorrido preenchido, 12 marcas (uma por imagem) e a hora da imagem em destaque.
7. **Troca suave entre as imagens.** Os 12 quadros ficam empilhados e o da vez sobe em 0,35 s por cima do anterior, sem piscar. Com "movimento reduzido" ligado no aparelho não há transição nem animação (regra geral do site).
8. **Carregamento.** Enquanto a NASA não responde, a área do mapa mostra um brilho de carregamento no lugar do retângulo escuro parado.
9. **Legenda enxuta.** A barra de temperatura fica mais fina e o parágrafo vira duas legendas nas pontas ("Do ciano ao vermelho: topos mais frios e altos, nuvens de grande desenvolvimento" e "Cinza: nuvens baixas e a superfície").

## O que não muda

Fontes e horários das imagens (NASA GIBS, GOES-East, IMERG), o recorte do Brasil, as divisas do IBGE e o crédito, a hora de cada imagem, o aviso de falha da NASA com "Tentar de novo", a chuva só pedida quando ligada, o carregamento só quando o mapa aparece, o clique no polo abrindo a região, o formato do boletim, as regras de estado (sem verde e sem vermelho; nunca só por cor) e a política de privacidade. Nenhuma biblioteca nova e nenhum pedido de rede novo.

## Limites conhecidos

- As cores do infravermelho são da própria imagem da NASA (escala oficial); não dá para trocá-las pela paleta do site.
- No celular, os polos do Sudeste continuam se encostando (o mapa tem 343 px de largura para 20 polos); o toque continua funcionando e a lista de regiões e polos fica na folha do local.

## Testes

- Unitário (+1): contagem dos polos por estado.
- E2E (+3): cartão com controle segmentado e chaves, glifo em cada polo, contagem que soma os 20 polos e muda com a operação, destaque do polo escolhido, nomes dentro do mapa; animação por transição com um quadro à vista por vez e rótulo do botão; no celular, cartão dentro da tela e botões com 44 px.
- Os testes do satélite que já existiam (divisas, hora e legendas, falha da NASA, imagem parcial, carregamento adiado, celular) continuam verdes sem mudança.

## Pronto quando

Suíte completa e bandit verdes; prévia vista no desktop e no celular, nas paletas escura e clara (botão "Ao sol"), e aprovada.
