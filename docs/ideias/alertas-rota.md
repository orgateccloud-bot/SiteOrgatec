# Alertas de clima e desastres na rota (Central de Viagem): plano

Situação: decisões tomadas em 11/11/2026; implementado na branch `ideia/alertas-rota`, tudo desligado por flag. Falta a configuração fora do código (seção 9).
Fontes conferidas por pesquisa em 11/11/2026. O que não foi confirmado está marcado como **não verificado**.

## 1. O que existe hoje (lido no código)

- Servidor Python (FastAPI) no Cloud Run, Firestore pela conta de serviço. As regras do Firestore negam tudo ao navegador e continuam assim.
- Coleção `alertas` por transportadora (bloqueio, interdição parcial, obra, outro), lançada à mão, com posição, raio e fonte. Ela entra no cálculo da rota como "Bloqueios" e aparece no mapa.
- Clima por ponto da rota com o MET Norway, a cada 150 km.
- Telemetria (Traccar e sensores) liga cada leitura à viagem certa do veículo.
- Motorista tem só nome e usuário. **Não há telefone nem app do motorista** (não existe PWA nem manifest no site).
- Não há rotina periódica no transporte. Os alertas precisam de um job agendado.

## 2. Os eventos nas rotas atendidas

| Evento | Ocorre? | Época | Onde | Fonte |
|---|---|---|---|---|
| Furacão e tempestade tropical | Não. O único caso no Atlântico Sul foi o Catarina (2004), no litoral de SC/RS | — | nenhuma rota | [NOAA](https://www.aoml.noaa.gov/es/hurricane_blog/10th-anniversary-of-cyclone-catarina) |
| Chuva forte, enchente, cratera | Sim, é o principal risco climático | out a abr | BR-153 no TO, BR-230 no PA | [INMET](https://portal.inmet.gov.br/noticias/balan%C3%A7o-palmas-to-teve-chuva-e-temperaturas-acima-da-m%C3%A9dia-em-mar%C3%A7o-2024) |
| Deslizamento | Raro (relevo plano); aparece como erosão de aterro | chuvas | BR-153 perto de Colinas (TO), 2017 | notícia regional, não oficial |
| Queimada e fumaça | Sim. PA lidera focos; BR-153 fechada por fumaça em Uruaçu (GO) em set/2024 | jul a out | GO, TO, PA | [INPE Infoqueima](https://dataserver-coids.inpe.br/queimadas/queimadas/Infoqueima/2024/2024_08_infoqueima.pdf); fechamento: notícia, página não abriu |
| Neblina | Ocasional, madrugadas de inverno | mai a ago | GO, SP | não verificado |
| Geada | Só na saída de SP e no sudoeste de GO | jun a ago | trecho paulista | aviso de geada do [INMET](https://avisos.inmet.gov.br/54434) |
| Vento forte, granizo | Sim, nos avisos de tempestade do INMET | set a dez | GO, TO | notícia citando aviso do INMET |
| Tornado | Raro; corredor vai do interior de SP ao RS | primavera e verão | trecho paulista | [estudo UFPE](https://periodicos.ufpe.br/revistas/rbgfe/article/download/246023/38145/189264) |
| Interdição de rodovia | Sim, é o maior risco operacional: atoleiros na BR-230, ponte do Araguaia (PA/TO) interditada | dez a mai | BR-230/PA | [DNIT](https://www.gov.br/dnit/pt-br/dnit-executa-obras-de-manutencao-em-diversos-pontos-da-br-230-pa-a-transamazonica) |
| Extra opcional: calor extremo | Sim, alerta vermelho do INMET no TO em nov/2023 | ago a out | GO, TO, PA | [INMET](https://portal.inmet.gov.br/noticias/calor-pode-superar-40-c-em-oito-estados-até-quarta-feira-30) |

## 3. Fontes

| Fonte | Cobre | Acesso | Custo e termos | Recomendação |
|---|---|---|---|---|
| INMET, avisos meteorológicos | tempestade, chuva intensa, vendaval, granizo, geada, onda de calor, baixa umidade | `https://apiprevmet3.inmet.gov.br/avisos/ativos` (JSON com polígono GeoJSON e municípios; conferido em 11/11/2026) e CAP 1.2 por aviso ([manual](https://portal.inmet.gov.br/manual)) | Sem token. Licença e limites: **não verificado** | **Principal** |
| NASA FIRMS | focos de fogo (VIIRS e MODIS) | `api/area/csv/{chave}/...`, chave gratuita, 5.000 transações a cada 10 min ([doc](https://firms.modaps.eosdis.nasa.gov/api/area/)) | Grátis, CC0, crédito "NASA FIRMS", sem sugerir endosso ([termos](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance)). Latência < 3 h | **Principal para fogo** |
| INPE Queimadas | focos de fogo, a cada 10 min | CSV aberto ([dados](https://data.inpe.br/queimadas/dados-abertos/)) | Grátis, pede citação ([FAQ](https://data.inpe.br/queimadas/portal/faq/)). Uso comercial: **não verificado** | Segunda fonte de fogo, só depois de confirmar a licença |
| MET Norway (já em uso) | previsão por ponto; tem rajada, neblina e probabilidade de trovoada | Locationforecast `complete` | CC BY 4.0 ([licença](https://api.met.no/doc/License)). Não traz alertas para o Brasil | Complemento: rajada, trovoada e neblina no horário de passagem |
| Cemaden | deslizamento e risco hidrológico | só painel web ([painel](https://painelalertas.cemaden.gov.br)); API **não encontrada** | — | Fora por ora (lacuna) |
| IDAP / Defesa Civil | alertas públicos | CSV mensal com 1 mês de atraso ([dados](https://dadosabertos.mdr.gov.br/dataset/idap-interface-de-divulgacao-de-alertas-publicos)); feed CAP **não encontrado** | CC BY | Fora (histórico) |
| CPTEC/INPE | previsão por município | XML | Proíbe uso comercial sem autorização ([página](http://servicos.cptec.inpe.br/XML/)) | Fora |
| PRF, DNIT, ANTT | acidentes e interdições | PRF: CSV mensal ([dados](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf)); DNIT e ANTT: só notícias e PDF | — | **Não há feed oficial de interdição em tempo real.** Interdição segue manual |
| DETER, PRODES, MapBiomas | desmatamento e uso do solo | — | — | Fora: não é risco imediato de rota |
| Open-Meteo | previsão | API | Grátis só não comercial ([termos](https://open-meteo.com/en/terms)) | Fora |

**Lacunas que a tela vai declarar:** interdição de rodovia (só manual e lançamento do motorista), deslizamento e enchente (só o aviso de chuva do INMET), tornado (só o aviso de tempestade), fumaça como visibilidade (só indireto: foco perto da rota e neblina do MET).

## 4. Canais

| Canal | Custo | Pontos fortes | Limites |
|---|---|---|---|
| WhatsApp Cloud API, direto da Meta | utility no Brasil ≈ US$ 0,0068 por mensagem entregue, exemplo da [página de preços](https://developers.facebook.com/docs/whatsapp/pricing) (tabela completa não aberta) | recibo de entrega e leitura; motorista já usa | template aprovado, opt-in, 250 destinatários por dia até verificar a empresa ([limites](https://developers.facebook.com/docs/whatsapp/messaging-limits)); precisa de dados móveis |
| SMS (Zenvia) | R$ 0,07 a 0,10 por SMS, por pacote ([preços](https://zenvia.com/precos/)) | chega sem dados móveis | Oi sem recibo, acentos trocados ([Twilio BR](https://www.twilio.com/en-us/guidelines/br/sms)); cadastro de remetente na Anatel em implantação (texto oficial **não verificado**) |
| SMS (Twilio) | US$ 0,0599 por segmento ([preços](https://www.twilio.com/en-us/sms/pricing/br)) | API simples | mais caro |
| App do motorista (PWA + Firebase Cloud Messaging) | grátis ([preços](https://firebase.google.com/pricing)) | fila de até 28 dias; substitui alerta velho pelo novo | **o app não existe**; no iPhone só com o app na Tela de Início, iOS 16.4+ ([WebKit](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/)) |

Recomendação: WhatsApp como principal; SMS como reserva só para alerta grave sem confirmação de entrega em 15 min; app do motorista depois, como fase própria. A central recebe no painel (lista e mapa, com som opcional) e, se quiser, um resumo por WhatsApp ao plantonista.

## 5. Quem recebe o quê (proposta)

- **No trajeto:** viagem `em_andamento`. Usa a última posição da telemetria (ou o plano, sem telemetria) para achar o trecho que falta e a hora estimada de chegada a cada ponto. Recebe se a área do alerta cruza o trecho que falta dentro da validade do alerta.
- **Vai viajar:** viagem `planejada` com partida nas próximas 72 h. Mesmo cruzamento, com o horário do plano.
- **Gravidade:** INMET "Perigo potencial" só no painel; "Perigo" no painel e WhatsApp; "Grande perigo" no painel, WhatsApp e SMS de reserva. Foco de fogo a até 5 km do trecho que falta, nas próximas 6 h: painel e WhatsApp.
- **Sem repetição:** cada par alerta e viagem gera uma mensagem; nova só se a gravidade subir.
- **Mensagem:** risco, trecho (km e cidade), quando chega lá, validade, o que fazer e a fonte.

## 6. Dados novos (Firestore, só pelo servidor)

- `transporte_alertas_externos` (global): fonte, id externo, tipo, gravidade, início, fim, área simplificada, texto, instruções, link, capturado em.
- `alertas_viagem` (por transportadora): viagem, alerta, trecho, hora estimada, estado (novo, visto).
- `comunicacoes` (por transportadora): motorista, canal, enviada em, estado (enviada, entregue, lida, falhou), id no provedor, texto.
- `motoristas`: telefone e consentimento (data e versão do texto aceito). Prazo de guarda pela rotina de retenção já existente.

## 7. Entrega em fases (tudo atrás de flag, desligado por padrão)

1. Fontes INMET e FIRMS, job a cada 15 min, cruzamento com as viagens, cartão e camadas no mapa da Central, fonte e "fonte indisponível" visíveis. Sem envio de mensagem.
2. Histórico de comunicações e tela de consentimento e telefone do motorista.
3. WhatsApp (depende de conta Meta, número e template aprovado, feitos pelo usuário).
4. SMS de reserva.
5. App do motorista com notificação (fase própria).

## 8. Custo mensal estimado (exemplo: 20 caminhões, 300 mensagens)

- Fontes: R$ 0 (INMET, FIRMS, MET Norway).
- Job no Cloud Scheduler: US$ 0,10 ([preços](https://cloud.google.com/scheduler/pricing)); execuções no Cloud Run dentro da cota gratuita (estimativa, não medida).
- WhatsApp: 300 × US$ 0,0068 ≈ US$ 2,04 (≈ R$ 12).
- SMS de reserva: 30 × R$ 0,10 = R$ 3, mais o pacote mínimo da Zenvia (valor mínimo **não verificado**).

## Decisões do usuário (11/11/2026)

| Ponto | Decisão |
|---|---|
| Fontes | INMET + NASA FIRMS + INPE. O INPE fica desligado (`ORGATEC_TRANSPORTE_ALERTAS_INPE`) até confirmar com o INPE o uso comercial |
| Canal do motorista | WhatsApp (Cloud API, direto da Meta) + SMS de reserva (Zenvia) |
| Teto mensal | R$ 50 para as mensagens; ao chegar no teto, nada mais é enviado e o painel mostra "bloqueada pelo teto" |
| Regra de envio | Painel recebe tudo; motorista recebe "Perigo" e "Grande perigo" do INMET e fogo a até 5 km do trecho que falta (passagem nas próximas 6 h); viagens planejadas entram se partem nas próximas 72 h |

## 9. Configuração (fora do código)

Tudo fica desligado até `ORGATEC_TRANSPORTE_ALERTAS=1` na API e no job.

| Variável | Para quê | Onde |
|---|---|---|
| `ORGATEC_TRANSPORTE_ALERTAS=1` | liga a API dos alertas e a rotina | env da API e do job |
| `ORGATEC_TRANSPORTE_FIRMS_CHAVE` | chave gratuita do NASA FIRMS ([pedido](https://firms.modaps.eosdis.nasa.gov/api/map_key/)) | Secret Manager, `--update-secrets` no job |
| `ORGATEC_TRANSPORTE_ALERTAS_INPE=1` | liga o INPE depois da confirmação da licença | env do job |
| `ORGATEC_TRANSPORTE_WHATSAPP=1`, `_WHATSAPP_TOKEN`, `_WHATSAPP_NUMERO_ID`, `_WHATSAPP_TEMPLATE`, `_WHATSAPP_VERSAO` (padrão v27.0) | envio pelo WhatsApp | token no Secret Manager; o resto em env do job |
| `ORGATEC_TRANSPORTE_WHATSAPP_VERIFICACAO`, `_WHATSAPP_APP_SEGREDO` | webhook de status `https://orgatec.io/api/transporte/whatsapp/webhook` | Secret Manager, `--update-secrets` na API |
| `ORGATEC_TRANSPORTE_SMS=1`, `_ZENVIA_TOKEN`, `_ZENVIA_REMETENTE` | SMS de reserva | token no Secret Manager; env do job |
| `ORGATEC_TRANSPORTE_ALERTAS_TETO_BRL` (50), `_CUSTO_WHATSAPP_BRL` (0,05), `_CUSTO_SMS_BRL` (0,10) | teto e custo estimado por mensagem | env do job |

Template do WhatsApp a criar na Meta (categoria **utility**, idioma pt_BR, 5 variáveis):
"Alerta ORGATEC na sua rota: {{1}}. Onde: {{2}}. Quando: {{3}}. O que fazer: {{4}}. Fonte: {{5}}."

Job a cada 15 min (mesma imagem da API; o comando muda):

```bash
gcloud run jobs create orgatec-alertas --region southamerica-east1 --image <imagem da API> --command python --args tools/transporte_alertas.py,--confirmar --update-env-vars ORGATEC_TRANSPORTE_BANCO=firestore,ORGATEC_TRANSPORTE_ALERTAS=1
gcloud scheduler jobs create http orgatec-alertas-15min --location southamerica-east1 --schedule "*/15 * * * *" --uri <URL de execução do job> --oauth-service-account-email <conta de serviço>
```

Sem `--confirmar`, o job só atualiza o painel e não envia mensagem: serve para a semana de observação.

Custo: o Scheduler é o 5º job da conta (US$ 0,10/mês acima dos 3 gratuitos, [preços](https://cloud.google.com/scheduler/pricing)). As execuções de 15 em 15 min usam a cota gratuita do Cloud Run jobs (estimativa, não medida). A rotina lê `alertas_rota` e `comunicacoes` de cada transportadora com viagem ativa a cada execução.

## 10. O que foi testado e o que não foi

Testado:
- 23 testes Python (`tests/py/transporte/test_alertas.py`): leitura do INMET, do FIRMS e do INPE, cruzamento com a rota e a telemetria, fogo por faixa, rotina sem mensagem repetida, gravidade que sobe, teto, falta de consentimento, fonte fora do ar que não encerra alerta, SMS de reserva, retenção, montagem dos pedidos do WhatsApp e da Zenvia, API (isolamento, papel do motorista, consentimento, revogação, webhook assinado).
- 1 teste JS nas camadas do mapa.
- Fontes reais em 11/11/2026: o INMET devolveu 9 avisos com polígono; o INPE, 1.819 focos em 12 arquivos. O servidor do INMET derruba a conexão com o User-Agent padrão do httpx e do curl; com o User-Agent da ORGATEC responde.
- Prévia local: cartão, chips das fontes, área e marcador no diagrama do mapa, formulário de telefone com aceite obrigatório, tela de 375 px sem rolagem lateral.

Não testado:
- NASA FIRMS ao vivo (falta a chave).
- WhatsApp e Zenvia de verdade (falta conta, número, template aprovado e token). Os formatos seguem a documentação oficial citada em `backend/transporte/alertas/envio.py`.
- Webhook real da Meta, job no Cloud Run e Scheduler, Firestore real (só memória e SQLite).
- Desenho das áreas no Google Maps (a prévia local não tem chave do mapa; foi visto só o diagrama SVG).
