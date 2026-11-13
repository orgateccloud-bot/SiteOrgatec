# Mapa público de alertas nas rodovias (Janela do Transporte)

Branch `ideia/mapa-alertas-publico`, pasta `D:\01_Projetos_Ativos\SiteOrgatec-mapa-alertas`. Pedido do usuário em 12/11/2026: "este mapa tem que ser integrado ao site". Escolhas dele: na Janela do Transporte, com as camadas de avisos do INMET, focos de fogo e rodovias principais; plano aprovado com "execute".

## O que entra

- Seção "Alertas nas rodovias de GO, TO e PA" em `empresarial/janela.html` (a página da Janela Empresarial e do Transporte, fora do menu e com noindex até a decisão R3).
- Mapa sem biblioteca, no padrão da Janela de Campo (`campo-mapa.js`):
  - fundo NASA Blue Marble (GIBS);
  - divisas do IBGE;
  - SVG com avisos do INMET, focos do FIRMS das últimas 24 h e o traçado da BR-153, BR-060, BR-010 e BR-230.
- Os avisos valendo agora são áreas cheias. Os dos próximos dias (o INMET publica os de amanhã e depois) aparecem só com contorno tracejado e numa lista à parte.
- Painel ao lado, que vira coluna única no celular:
  - estado de cada fonte e hora da verificação;
  - tabela por rodovia, com o aviso de agora, o próximo e os focos a até 5 km;
  - lista dos avisos com riscos, instruções e link para o INMET.
- Fonte fora do ar, verificação atrasada (mais de 40 min) ou sem verificação aparecem como aviso. O mapa nunca diz "sem risco" sem ter verificado.

Mudança em relação ao plano: o plano previa Leaflet com OpenStreetMap.
- A Janela de Campo já tinha um mapa próprio sobre a NASA GIBS, e a CSP do site já liberava esse endereço.
- Por isso não entrou biblioteca nova nem mudança de CSP.
- O custo continua zero e o mapa não usa nada do Google.

## Dados

| Camada | Fonte | Termos | Conferido |
|---|---|---|---|
| Avisos | INMET, `apiprevmet3.inmet.gov.br/avisos/ativos` (já usado nos alertas de rota) | dado público do governo federal, com crédito ao INMET | 11/11/2026 (alertas-rota) |
| Focos de fogo | NASA FIRMS, VIIRS NOAA-20 e NOAA-21 (o Suomi NPP parou em 02/11/2026) | CC0, crédito "NASA FIRMS" | 11/11/2026 |
| Rodovias | IBGE, BC250 2023, camada `rod_trecho_rodoviario_l`, simplificada por `tools/gerar_rodovias.py` | a documentação da BC250 não traz licença; vale a nota metodológica 01/2026 do IBGE (compatível com CC BY 4.0, com crédito e aviso de generalização) | **pendente: confirmar com o responsável se a nota cobre a BC250** |
| Divisas | IBGE, Malha Municipal 2025 (`divisas-ufs.svg`, já no ar) | nota 01/2026 do IBGE | 02/11/2026 |
| Fundo | NASA GIBS, Blue Marble | uso livre, com crédito à NASA | já no ar na Janela de Campo |

O traçado das rodovias **não** vem do Google. Os termos do Google Maps proíbem levar o conteúdo da Routes API a um mapa que não seja do Google.

## Como funciona

1. A rotina dos alertas (`tools/transporte_alertas.py`, job `orgatec-alertas` a cada 15 min) passou a buscar as fontes mesmo sem viagem ativa.
   - Ela grava `_sistema/alertas_publicos/atual` com `backend/transporte/alertas/publico.py`.
   - O FIRMS é pedido uma vez para a soma das rotas com a região do mapa (sul −19,6, oeste −56,5, norte −1,0, leste −45,5).
2. `GET /api/transporte/alertas-publicos` não pede login.
   - Só funciona com `ORGATEC_TRANSPORTE_ALERTAS=1`.
   - Devolve o resumo com `Cache-Control: public, max-age=60, s-maxage=300`, e a CDN do Firebase Hosting guarda por 5 min.
   - O `no-store` de toda a API (backend/app.py) ganhou uma única exceção, `API_PUBLICA_COM_CACHE`, testada.
3. O resumo não tem viagem, posição, transportadora nem motorista (teste). Os focos saem com 2 casas decimais (~1 km) e no máximo 4.000.
4. A página lê o resumo pela própria origem (CSP `connect-src 'self'`; `/api/**` é reescrito para o Cloud Run) e o atualiza a cada 5 min.

## Publicar

- Site: `python tools/publicar.py --com-desenvolvimento`, depois de juntar a ideia na desenvolvimento.
- API: `gcloud run deploy orgatec-api --source .` sem mudar variáveis. A imagem já copia `site/`, onde está o traçado.
- Atualizar a imagem dos jobs `orgatec-alertas` e `orgatec-retencao` para a mesma da API.
- Sem variável nova.

## Testado

- `tests/py/transporte/test_alertas_publico.py`: região e avisos dos próximos dias, limite e arredondamento dos focos, rotina sem viagem, rota pública sem login e com cache, desligada sem flag, exceção do no-store, mesma região em servidor, gerador e mapa, traçado do IBGE.
- `tests/js/janela-transporte-mapa.test.js`: estado da verificação, camadas, tabela por rodovia, aviso de fonte fora do ar, escape de texto e só link https.
- Prévia local com os avisos reais do INMET de 12/11/2026 e focos de **teste**: computador (duas colunas, 440 + 741 px), tela média e celular de 375 px sem rolagem lateral.

## Não testado

- Focos reais do FIRMS no mapa (a chave fica só no Secret Manager).
- A CDN do Firebase guardando a resposta de verdade.
- O job em produção gravando o resumo.

## No ar (12/11/2026)

- Site na tag `publicado-20261112-1405`, API `orgatec-api-00021-pdq`; os jobs `orgatec-alertas` e `orgatec-retencao` usam a mesma imagem.
- Primeira execução: 3 avisos do INMET na região (1 valendo agora e 2 dos próximos dias, todos "Perigo potencial" de tempestade) e 2.010 focos reais do FIRMS. Por rodovia, a BR-010 tinha 19 focos a até 5 km e a BR-230 tinha 53. A chave do FIRMS não aparece nos registros.
- `orgatec.io/api/transporte/alertas-publicos` responde com `X-Cache: HIT` (a CDN guarda por 5 min).
- Na página publicada, o mapa desenhou as 3 áreas, os 2.010 focos e as 4 rodovias, com as 12 imagens da NASA carregadas e sem rolagem lateral.

## Modernização visual (12/11/2026, branch `ideia/mapa-alertas-visual`)

Pedido do usuário: "modernize essa página". Só a página mudou; a API e o job seguem iguais, salvo as duas correções abaixo.

- **Veredito no topo**, acima do mapa (no celular, antes de tudo): aviso grave primeiro, depois a rodovia com mais focos (10 ou mais a até 5 km) e o aviso de perigo potencial. Com fonte fora do ar ou verificação atrasada, o veredito vira "Verificação incompleta" e nunca diz "sem alerta".
- **Dias**: Hoje, Amanhã e depois, no horário de Brasília. O mapa e a lista mostram só os avisos do dia escolhido.
- **Cartões por rodovia** no lugar da tabela: aviso do dia, início do que ainda não começou, focos em 24 h com barra. Tocar no cartão (ou na rodovia no mapa) destaca o traçado e filtra a lista.
- **Focos**: só os que estão a até 5 km de uma rodovia continuam como pontos; os demais viram manchas por célula de 0,25° (~27 km), calculadas no navegador.
- **Balão** ao tocar numa área de aviso, com tipo, gravidade, validade e instrução. Fecha no × ou com Esc.
- Camadas como botões de 44 px; mapa fixo ao lado do painel no computador.

Correções de dados feitas junto:
- **Zero foco à noite**: o pedido ao FIRMS cobria "1 dia", que na NASA é o dia corrente em UTC. Das 21h de Brasília em diante o mapa mostrava zero foco com a fonte "ok". Agora pede 2 dias; os filtros de 24 h (mapa) e 12 h (rota) já existiam.
- **Instruções do INMET com colchetes**: `riscos` e `instrucoes` vêm como lista de frases e apareciam como `['...', '...']` na tela (e iriam assim na mensagem ao motorista). Agora viram texto corrido.

As duas correções exigem subir a API e atualizar a imagem dos jobs.

## Brasil inteiro e toda a malha (12/11/2026, branch `ideia/mapa-alertas-brasil`)

Pedido do usuário: "tem que ser todo o Brasil e toda a malha rodoviária". Escolhas dele: todas as estradas, inclusive municipais, e navegação "Brasil e escolha do estado". Plano aprovado com "execute".

**Malha (tools/gerar_rodovias.py, 56 arquivos, 3,7 MB no total, o maior com 394 KB):**
- `assets/geo/ufs.json`: contorno e retângulo dos 27 estados (IBGE, Malha Municipal 2025). Ilhas oceânicas distantes (Trindade, Fernando de Noronha) ficam fora do recorte.
- `assets/geo/rodovias/BR.json`: as 149 rodovias federais, bem simplificadas, para a visão do país.
- `assets/geo/rodovias/<UF>.json`: rodovias com sigla (federais e estaduais) do estado, cerca de 3.000 no país.
- `assets/geo/rodovias/<UF>-locais.json`: estradas sem sigla (municipais e vicinais), só desenho, carregadas a pedido.
- A base do IBGE (BC250 2023) tem 130 mil trechos. Cada trecho vai para o estado onde cai o seu ponto do meio. Saem os abandonados, destruídos, planejados, em construção e os não operacionais.
- A sigla é lida em vários formatos: `BR-153;BR-060`, `BR-430 BA-464`, `Rodovia MG-403`, `LMG 628` e o código do SNV (`156BAP0170` = BR-156 no Amapá).

**Servidor (publico.py):**
- O FIRMS passa a ser pedido para o Brasil inteiro.
- A rotina grava 28 registros a cada execução: `alertas_publicos/atual` (avisos com os estados em que cruzam rodovia, focos agrupados em células de 0,25° e o resumo por estado) e um por estado (rodovias com aviso ou foco e até 1.500 focos junto a rodovias).
- Índice espacial dos trechos por célula de 0,1°. Medido em 12/11/2026: 60 mil focos contra 3.002 rodovias em 1,5 s; registro nacional com 128 KB e o maior estadual com 76 KB (o limite do Firestore é 1 MB).
- API: `/alertas-publicos` e `/alertas-publicos/<UF>`, as duas sem login e com cache de 5 min. UF inválida devolve 404. São as únicas exceções ao `no-store` (`_publica_com_cache` em backend/app.py, testada).
- Custo no Firestore: 28 gravações a cada 15 min, cerca de 2.700 por dia, dentro da cota gratuita de 20 mil.

**Página:**
- Abre no Brasil: estados clicáveis, federais, avisos do dia e manchas de fogo. Veredito nacional, cartões dos estados com aviso ou foco e lista para escolher qualquer estado.
- No estado: imagem de satélite mais nítida (zoom 5 a 8, conforme o tamanho), rodovias federais e estaduais com alvo de toque, focos junto a rodovias, veredito do estado, cartões das rodovias com aviso ou foco e busca pela sigla em todas as rodovias dali.
- Botão "Estradas locais" (só no estado, desligado por padrão): desenha a malha sem sigla num canvas.
- Estradas locais não têm nome na base e não entram no cruzamento com avisos e focos.

**Limites:**
- A escala da base é 1:250.000: a malha local é incompleta. O crédito avisa que não serve de guia de rota.
- Falta conferir os focos reais do FIRMS no país inteiro (a chave fica só no Secret Manager) e o tempo do job em produção.

## Mapa interativo, previsão e chuva forte no Sul (13/11/2026, branch `ideia/mapa-alertas-interativo`)

Pedido do usuário: mapas realistas, previsão do tempo, tornados no Sul, dinamismo e interatividade. Modelo aprovado ("Aprovado, siga") e três fases aprovadas ("Execute as 3 fases"). Parte da branch `ideia/mapa-alertas-brasil` e leva junto as correções dela (FIRMS "/2" e texto do INMET).

**Fontes conferidas em 13/11/2026:**
- MET Norway (Locationforecast 2.0): dados CC BY 4.0, cobre o Brasil, 9 dias, atualiza a cada 6 h fora da Escandinávia. Termos: User-Agent com o site, coordenada com até 4 casas, sem repetir o mesmo pedido antes de 3 h, menos de 20 pedidos/s, navegador não chama direto (proxy com cache). Os termos pedem que "uma pessoa com autoridade" os leia e aceite: **o usuário precisa ler https://api.met.no/doc/TermsOfService antes de ligar a previsão em produção.**
- **A série do MET para o Brasil não traz trovoada nem rajada.** Em 16 pontos tropicais (Brasil, Bangkok, Singapura, Jacarta, Houston), num dia de aviso de tempestade do INMET, nenhum símbolo "thunder" apareceu. Por isso a camada do Sul é de **chuva forte prevista** (10 mm em 1 h ou 30 mm em 6 h) e **muito forte** (20 mm em 1 h ou 50 mm em 6 h), e não de "temporal" nem "trovoada".
- RainViewer (radar): API gratuita só para uso pessoal e educacional. Fora.
- Open-Meteo: API gratuita proíbe uso comercial; plano pago tem CAPE e rajada. Fora até o usuário decidir o preço.
- PREVOTS (tempo severo no Sul): só imagem diária, sem licença; os registros são só para uso acadêmico. Fora; pedir autorização por e-mail se quiser.

**Fase 1, mapa interativo (`site/assets/js/janela-transporte-gl.js`):**
- MapLibre GL JS 4.7.1 hospedado em `site/assets/vendor/maplibre-gl-4.7.1/`, versão "csp" (sem `eval`, worker do próprio site). Integridade do pacote do npm conferida (`LEIA-ME.md` da pasta). Cache de 1 ano (`/assets/vendor/**`).
- Só carrega com WebGL e quando o mapa chega a 1.200 px da tela. Sem WebGL, ou se a biblioteca falhar, fica o mapa em SVG (testado).
- CSP só da página `/empresarial/janela.html` (`CSP_JANELA` em backend/app.py e `csp_janela` em tools/preparar_firebase.py, testadas iguais): `connect-src` + `https://gibs.earthdata.nasa.gov` (o MapLibre baixa as imagens por fetch) e `img-src` + `blob:`. O resto do site não muda.
- Zoom livre (Ctrl + rolagem ou dois dedos, para não prender a rolagem da página), satélite GOES-East ao vivo (cor real ou nuvens) com animação das últimas 2 h (os 11 quadros antigos só baixam quando a pessoa anima), chuva por satélite (IMERG de anteontem), avisos, manchas e focos, estados clicáveis, rodovias com sigla e estradas locais.
- O painel de cartões, o veredito, os dias e a busca continuam os mesmos, para o mapa e para quem usa leitor de tela.

**Fase 2, previsão por ponto (`backend/transporte/alertas/previsao.py`):**
- `GET /api/transporte/previsao?lat=&lon=`: sem login, só dentro do recorte do Brasil (422 fora), ponto arredondado a 0,1°, cache de até 3 h no processo e de 1 h na CDN, no máximo 600 pedidos ao MET a cada 10 min por instância. Erro sai com `no-store`.
- Balão do mapa (toque num ponto do estado): avisos do INMET ali, chuva forte prevista, próximas horas e 4 dias, com crédito e "não é aviso oficial".

**Fase 3, chuva forte no Sul:**
- A rotina dos alertas consulta 90 pontos (grade de 0,75° em PR, SC e RS), 4 de cada vez, no máximo a cada 3 h, e grava em `alertas_publicos/temporal_sul`; o resumo nacional leva o resultado em `temporal`. Medido: 90 pedidos em 8 s. Na primeira falha do MET os outros pedidos não saem e o mapa avisa que a previsão está atrasada.
- Painel: cartões de PR, SC e RS; veredito do Brasil cita só a chuva **muito forte**, sempre como "modelo do MET Norway, não é aviso oficial".

**Para ligar em produção:** `ORGATEC_TRANSPORTE_PREVISAO=1` na API (balão) e no job `orgatec-alertas` (Sul), com `--update-env-vars`. Site e API sobem juntos; atualizar a imagem dos jobs `orgatec-alertas` e `orgatec-retencao`. Sem a variável, o balão mostra só os avisos e o painel não mostra o Sul.

**Testado (13/11/2026):** 13 testes Python novos (`tests/py/transporte/test_previsao.py`) e 10 de JavaScript (`tests/js/janela-transporte-gl.test.js`); navegador de teste (Chromium com SwiftShader) com o servidor local: sem erro de CSP ou de script, Brasil, estado, balão com previsão real do MET, rodovia marcada, estradas locais, animação, nuvens e chuva, celular de 390 px sem rolagem lateral e o SVG sem WebGL. A camada do Sul foi conferida com dados de teste (hoje não há chuva forte prevista no Sul).

**Não testado:** em produção (CDN, Cloud Run, Firestore); celulares reais e GPU real; o job com a variável ligada.

### Revisão do mapa interativo (13/11/2026, tarde)

Pedida pelo usuário depois da análise ("Alta e média"):

- **Chuva por satélite:** era o IMERG diário de anteontem, sem data na tela. Agora é o `IMERG_Precipitation_Rate_30min` da GIBS, no horário mais novo publicado (lido da lista de domínios da GIBS ao ligar a camada; atraso medido de cerca de 5 a 6 h). Embaixo do mapa: "estimativa de DD/MM HH:MM, cerca de N h atrás. Não é o radar de agora."
- **Balão:** a chuva forte do Sul diz "na região", "em algum ponto da área de uns 80 km ao redor" e que o ponto exato pode ter menos chuva. O mapa anda para o balão caber inteiro quando a previsão chega.
- **Fogo em magenta** (manchas, pontos e barras do painel), para não confundir com amarelo, laranja e vermelho dos avisos do INMET.
- **Rótulos sem colisão:** siglas que encostam somem até aproximar (estados maiores e a rodovia marcada têm prioridade).
- **Malha discreta de longe;** chuva forte do Sul como mancha contínua (heatmap) em vez de quadrados; créditos sempre recolhidos no ⓘ; horário do primeiro e do último quadro na barra da animação; legenda só com as camadas ligadas; no desktop o mapa encolhe para a coluna fixa caber na tela.
