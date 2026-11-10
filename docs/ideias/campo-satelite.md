# Janela de Campo: satélite com divisas, hora em cada imagem e aviso quando a NASA falha (Fase 5)

- **Situação:** aprovada em 07/11/2026 e publicada: no ar desde 08/11/2026 (tag `publicado-20261108-0650`); branch mantida até o lançamento definitivo
- **Branch:** `ideia/campo-satelite` (parte de `desenvolvimento`, que já tem as Fases 0 a 4)
- **Prévia:** [link](https://orgatec-site--ideia-campo-satelite-20z856ne.web.app/setores/janela-de-campo.html) (expira em 07/12/2026). Conferida em 375 px e 1280 px com as imagens reais da NASA, em 07/11/2026 às 22h: celular sem pedido à NASA antes de abrir a aba; cor real às 21h20 (infravermelho às 21h30); chuva IMERG de 06/11; sem erros nem rolagem lateral.

## Problema

O mapa de satélite tinha quatro limitações:

- Sem divisas dos estados (só o litoral), o produtor não situava o próprio estado.
- A falha da NASA GIBS aparecia só como um texto pequeno na legenda da imagem, sem dizer que a previsão não depende dela e sem como tentar de novo.
- Só o infravermelho tinha hora. A cor real dizia "imagem mais recente" e a chuva dizia "de ontem", sem data.
- No celular, o controle de tempo era uma barra sem horas legíveis, e a legenda era uma frase de 12 px (que falava só em "nuvem branca", enquanto o mapa também mostra amarelo e vermelho). As imagens da chuva eram pedidas mesmo escondidas.

## O que esta branch muda

1. **Divisas dos estados** (opção "Divisas dos estados", ligada por padrão). A NASA GIBS não tem divisas dos estados brasileiros (confirmado nas capacidades da API em 07/11/2026: só litoral, fronteiras entre países e referências). Elas vêm do IBGE, como um SVG estático do próprio site (`site/assets/img/divisas-ufs.svg`, 44 KB), gerado por `tools/gerar_divisas_ufs.py` a partir do shapefile oficial `BR_UF_2025.zip`. Nada externo é carregado.
2. **Aviso claro quando a NASA falha**, com o botão "Tentar de novo":
   - Sem nenhuma imagem: "Não foi possível carregar a imagem de satélite: a NASA (GIBS) não respondeu agora. A previsão e os polos continuam valendo".
   - Imagem parcial (alguns quadrados não vieram, nem na segunda tentativa): "Parte da imagem de satélite não carregou".
   - Chuva: aviso próprio.
3. **Hora de cada imagem.** Infravermelho com a hora de cada quadro; cor real com a hora (a página pede o horário do infravermelho, ou até 1 hora antes, em vez de "a mais recente"); chuva com o dia ("chuva IMERG de 06/11"), descoberto ao ligar a camada.
4. **Celular.**
   - O controle de tempo ganhou as horas das pontas e a da imagem escolhida, em uma área de toque de 44 px; o leitor de tela recebe a hora no valor da barra.
   - Legendas de cor com barra (temperatura do topo da nuvem em °C; chuva em mm/h) e frase em 14 px.
   - Os créditos ficam num bloco recolhível.
5. **Só carrega quando aparece.** No celular, as imagens da NASA só são pedidas quando a aba Satélite é aberta; no desktop, quando o painel chega a 300 px da tela. A chuva só é pedida quando o visitante a liga. Antes, as duas camadas eram pedidas na abertura.

## Fontes e licenças (conferidas em 07/11/2026)

- **Divisas: IBGE, Malha Municipal Digital e Áreas Territoriais 2025.** A nota metodológica 01/2026 do IBGE ("Informações técnicas e legais para a utilização dos dados publicados", [biblioteca.ibge.gov.br, item 2102268](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102268.pdf)) diz que a MMD e os produtos derivados saem "sob licença compatível com Creative Commons BY 4.0", que permite adaptar, "mesmo para fins comerciais", com crédito ao IBGE. A mesma nota exige que, ao generalizar a malha, o usuário final seja avisado de que ela passou por processamento que alterou as características originais: o crédito do mapa diz que as divisas foram simplificadas. O IBGE também informa que não é legalmente responsável pela definição dos limites; por isso o crédito diz que o desenho é ilustrativo. O arquivo vem de `geoftp.ibge.gov.br` (`BR_UF_2025.zip`); a página de malhas do IBGE bloqueia download automático (403) e não foi contornada.
- **Escalas de cor:** colormaps oficiais da NASA GIBS (`Clean_Longwave_Infrared_Window_Band.xml`, em °C, de −92 a mais de 57; `GPM_Precipitation_Rate.xml`, em mm/h, o colormap que a própria API da NASA indica para a camada IMERG). Preferi barras de cor leves às legendas SVG oficiais (350 a 540 KB cada). A frase explicativa sob a barra ("topos cada vez mais frios e altos") é minha, de meteorologia geral, e não texto da NASA.
- **Horários:** as capacidades da API (`Default` de cada camada) mostram passos de 10 minutos para o infravermelho e a cor real, com horários padrão diferentes (23h30 e 23h20 UTC no momento da consulta), e passo de 1 dia para o IMERG.

## O que não foi mudado

- Zoom 4 (3 × 3 imagens): o mapa continua de baixa resolução; aumentar o zoom quadruplica as imagens.
- Nenhum dado novo de previsão, nem as regras de decisão (V20).
- O aviso do satélite não altera o status do boletim: a previsão não depende das imagens.

## Pronto quando

- Testes novos passam: geometria das divisas (extremos do Brasil, recorte igual ao do JavaScript, SVG válido e com crédito), escalas de cor, divisas com crédito do IBGE, hora de cada imagem e legendas, aviso total e parcial com "Tentar de novo", carga sob demanda no desktop e no celular, controle de tempo no celular.
- A suíte completa (JS, pytest, e2e) e o bandit estão verdes.
- Prévia aberta em 375 px e 1280 px e aprovada pelo usuário.
