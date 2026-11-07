# Janela de Campo: a decisão do dia na primeira tela (Fase 3)

- **Situação:** em desenvolvimento (código e testes prontos; falta a prévia e a sua aprovação)
- **Branch:** `ideia/campo-layout` (junta as Fases 0, 1 e 2: `ideia/campo-qualidade` e `ideia/agro-hub`)
- **Prévia:** [link](https://orgatec-site--ideia-campo-layout-xu3bh1tl.web.app/setores/janela-de-campo.html) (expira em 07/12/2026). Usa um boletim real gerado com o código das Fases 0 e 1, em 07/11/2026 às 20h22.

## Problema

No celular, a Janela de Campo tinha 14.092 px (17 telas). A primeira decisão (o painel por região e operação) só aparecia em 2.068 px, depois do mapa, e os critérios, a confiança e as fontes vinham sempre abertos. A Fase 2 tirou os cards (9.772 px), mas a ordem continuava a de um relatório, não a de quem quer saber se pode trabalhar hoje.

## Público

Produtor rural, no celular, no campo.

## O que esta branch muda

Ordem no celular:

1. Título curto e uma linha de status (atualizado às, próxima atualização, polos sem previsão, link do INMET). O texto da introdução só aparece a partir de telas médias.
2. A data do boletim.
3. Seletor de **região** e de **polo**, em chips com rolagem lateral. A escolha fica lembrada só neste navegador.
4. **Hoje na minha região**: as 5 operações, cada uma com estado (ícone, texto e cor), resumo de até 90 caracteres e janela. Tocar numa operação mostra a orientação de segurança dela logo abaixo.
5. Alerta de trovoada, só quando houver.
6. Abas: **Horas** (condição do dia, polo hora a hora), **7 dias** (previsão e resumo da semana), **Satélite** e **Como decidimos** (resumo, critérios, confiança, fontes e o seletor de boletins anteriores).
7. **Comparar as regiões** (a matriz de antes), recolhida no celular.
8. **Minha atividade**: escolhe a atividade e o botão leva ao card dela na página de cotações e notícias. A escolha fica lembrada só neste navegador.
9. Contato (a faixa de diagnóstico que já existia).

No desktop (a partir de 1024 px): duas colunas. À esquerda, o seletor e "Hoje na minha região". À direita, o satélite sempre à vista e, abaixo dele, as abas Horas, 7 dias e Como decidimos. A comparação das regiões ocupa a largura toda, aberta.

Outras mudanças:

- **O satélite só carrega quando aparece.** No celular, as imagens da NASA só são pedidas quando a aba Satélite é aberta; antes, carregavam na abertura da página.
- **Teclado.** As abas seguem o padrão WAI-ARIA: setas, Home e End movem entre elas.
- **Subnavegação dos setores** em uma fileira com rolagem lateral no celular.
- **O que não muda na interface:** estados sempre com ícone, texto e cor; movimento reduzido respeitado; o mapa e seus controles são os mesmos.

## Medição (Playwright na prévia, com dados reais, 375 x 812 e 1280 x 900)

| | Antes | Agora |
|---|---|---|
| Janela no celular | 14.092 px | 4.376 px |
| Primeira decisão no celular (topo da primeira operação) | 2.068 px | 718 px |
| Janela no desktop | 7.606 px | 3.982 px |
| Rolagem horizontal | nenhuma | nenhuma |

A medição foi feita com a faixa de homologação do topo (cerca de 80 px), que não aparece em produção; sem ela, a primeira operação começa em torno de 640 px. Com a faixa, parte da primeira operação fica sob a barra fixa de contato do rodapé do celular. Na prévia o satélite não carrega no celular até a aba ser aberta (0 imagens), e carrega no desktop (27).

## Fora desta fase

- **Resumo da atividade com dados.** "Minha atividade" só leva ao card da atividade. Mostrar cotação ou notícia dentro da Janela exige juntar o `noticias.json` e o widget do CEPEA numa visão compacta, e fica para a Fase 6 (fontes, licença e estados vazios).
- **Busca por município e satélite.** Fases posteriores.
- **Limites agronômicos.** Não mudaram (V20).

## Fontes e validação

Nada de regra nova nem de dado novo: o conteúdo é o mesmo boletim, em outra ordem. A fonte de cada critério continua na aba "Como decidimos".

## Pronto quando

- Testes e2e novos e alterados passam: primeira operação até 812 px no celular, página de até 5.000 px, satélite sob demanda, abas por teclado, desktop em duas colunas com o satélite à vista, aviso de polo sem previsão com polo escolhido, "minha atividade".
- A suíte completa (JS, pytest, e2e) e o bandit estão verdes.
- Prévia aberta em 375 px e 1280 px e aprovada pelo usuário.
