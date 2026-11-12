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
