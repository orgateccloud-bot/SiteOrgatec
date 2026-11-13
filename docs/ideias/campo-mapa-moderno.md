# Janela de Campo: mapa de satélite com visual novo

- **Situação:** aprovada em 12/11/2026 e junta na `desenvolvimento` (mapa novo e modelo 3D de vidro do mapa); **lançada em 12/11/2026** (`publicado-20261112-2106`). Os cartões das operações em vidro 3D foram feitos e desfeitos a pedido ("mantém o formato anterior"); ficaram guardados no stash do git "cartoes das operacoes em vidro 3D".
- **Branch:** `ideia/campo-mapa-moderno` (removida depois do merge)
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

## Modelo 3D de vidro (chave "3D")

Pedido em 12/11/2026: "monte um modelo em 3d interativo vidro". O mapa abre plano, como sempre, e a chave **3D** (ao lado de "Chuva" e "Divisas") transforma a imagem num modelo que dá para girar:

- **Placa de vidro com espessura.** A imagem do satélite vira a face de cima de uma placa inclinada, com as quatro bordas em vidro azul, um brilho embaixo e um piso em grade.
- **Folha de vidro com as divisas.** As divisas dos estados sobem para uma folha transparente 20 px acima da imagem; ao girar, as duas camadas se deslocam uma em relação à outra.
- **Polos como pinos.** Cada polo vira um pino com haste, que sempre encara quem olha. A altura cresce com a restrição (favorável mais baixo, com restrição no meio, evitar mais alto), além do glifo, que continua igual. O polo escolhido fica maior.
- **Giro.** Arrastar com o mouse gira e inclina (entre 28° e 70°; a volta é livre). No celular, arrastar para os lados gira e o arrasto vertical continua rolando a página. Com o mapa em foco, as setas do teclado fazem o mesmo. Desligar a chave volta ao mapa plano e ao ângulo inicial.
- **O que fica parado.** A contagem por estado e a hora da imagem ficam fora da placa, sempre de frente. A animação das 2 horas, a chuva, a troca de camada e o clique nos polos funcionam igual nos dois modos.

Sem biblioteca: só transformações 3D de CSS e cerca de 40 linhas de JavaScript para o giro. Com "movimento reduzido" ligado no aparelho, o modelo liga sem a transição de entrada.

**Limites do 3D:** a placa ocupa cerca de 70% da largura do mapa para caber girada em qualquer ângulo, então a imagem fica menor que no modo plano; os polos próximos se sobrepõem mais; o nome do polo escolhido pode ser cortado na borda em alguns ângulos. Por isso o modo plano continua sendo o padrão e o 3D não é lembrado entre visitas (nenhuma chave nova no aparelho).

## O que não muda

Fontes e horários das imagens (NASA GIBS, GOES-East, IMERG), o recorte do Brasil, as divisas do IBGE e o crédito, a hora de cada imagem, o aviso de falha da NASA com "Tentar de novo", a chuva só pedida quando ligada, o carregamento só quando o mapa aparece, o clique no polo abrindo a região, o formato do boletim, as regras de estado (sem verde e sem vermelho; nunca só por cor) e a política de privacidade. Nenhuma biblioteca nova e nenhum pedido de rede novo.

## Limites conhecidos

- As cores do infravermelho são da própria imagem da NASA (escala oficial); não dá para trocá-las pela paleta do site.
- No celular, os polos do Sudeste continuam se encostando (o mapa tem 343 px de largura para 20 polos); o toque continua funcionando e a lista de regiões e polos fica na folha do local.

## Testes

- Unitário (+1): contagem dos polos por estado.
- E2E (+3): cartão com controle segmentado e chaves, glifo em cada polo, contagem que soma os 20 polos e muda com a operação, destaque do polo escolhido, nomes dentro do mapa; animação por transição com um quadro à vista por vez e rótulo do botão; no celular, cartão dentro da tela e botões com 44 px.
- Modelo 3D: unitário (+1, giro com limites e volta completa) e E2E (+2): a chave liga a placa em 3D, arrastar e as setas giram, os pinos continuam abrindo a região, desligar volta ao plano; no celular, o arrasto vertical continua rolando a página e nada sai da tela.
- Os testes do satélite que já existiam (divisas, hora e legendas, falha da NASA, imagem parcial, carregamento adiado, celular) continuam verdes sem mudança.

## Pronto quando

Suíte completa e bandit verdes; prévia vista no desktop e no celular, nas paletas escura e clara (botão "Ao sol"), e aprovada.
