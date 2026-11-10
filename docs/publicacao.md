# Publicação do site ORGATEC

Preparado em 31/10/2026. Nada foi publicado ainda.

## O que é publicado

Um único serviço, montado pelo `Dockerfile`:
- o site estático (`site/`) em `/`;
- a API dos formulários (lead, opt-in e contato) em `/api`, gravando em SQLite.

## Testado localmente com Docker em 31/10/2026

- **Sem segredo:** a imagem se recusa a iniciar sem `ORGATEC_SEGREDO_IP`.
- **Saúde:** `/api/saude` responde `ok` sem tocar no banco. A trilha `audit_hash` se confere com `python tools/lgpd.py trilha`.
- **Cabeçalhos:** todas as respostas levam CSP, `X-Frame-Options: DENY`, `nosniff`, HSTS e `X-Robots-Tag: noindex`, este último por ser homologação.
- **Política de segurança:** as 10 páginas principais carregam sem nenhum bloqueio. O único aviso no navegador é o do Tailwind via CDN.
- **Código:** `tools/` e `backend/app.py` não ficam acessíveis pela web (404).
- **Dados:** um lead gravado continuou no banco depois de reiniciar o contêiner, com o volume em `/dados`.
- **Usuário:** o serviço roda como usuário sem privilégios (uid 10001).

## Modelo escolhido: tudo no Firebase, com dados em São Paulo

| Parte | Serviço | Região |
|---|---|---|
| Site (`site/`) | Firebase Hosting (CDN) | global |
| API dos formulários | Cloud Run, com o mesmo `Dockerfile` | `southamerica-east1` (São Paulo) |
| Banco (leads, opt-in, contato) | Firestore (`ORGATEC_BANCO=firestore`) | `southamerica-east1` (São Paulo) |

- **Mesmo endereço:** o Hosting encaminha `/api/**` para o Cloud Run (rewrite no `firebase.json`), então site e API ficam no mesmo endereço. Não há CORS, e a CSP fica só com `'self'`. No `config.js`, `api.publica: ''`.
- **Acesso ao banco:** o navegador não acessa o Firestore (`firestore.rules` nega tudo). Só a API grava, com a conta de serviço do Cloud Run.
- **Trilha de auditoria:** a trilha `audit_hash` é a mesma do SQLite. Cada envio entra numa transação, e dentro da instância os envios formam fila.
- **Retenção:** não ligue a política de TTL do Firestore, porque ela apaga o documento inteiro e quebra a trilha. A eliminação roda em `tools/lgpd.py`, que apaga só os dados pessoais. Ela vai na imagem da API: crie uma tarefa do Cloud Run com o comando `python tools/lgpd.py retencao --confirmar`, as mesmas variáveis e o mesmo segredo da API (`ORGATEC_BANCO`, `ORGATEC_SEGREDO_IP`), e dispare uma vez por dia pelo Cloud Scheduler. Sem isso, os prazos da política não se cumprem.
- **Testes:**
  - os testes de contrato passam no SQLite e no emulador do Firestore, incluindo 12 envios simultâneos;
  - a imagem Docker, apontada para o emulador, gravou lead e opt-in;
  - a confirmação do opt-in foi aceita uma única vez.

### O que a documentação do Google diz (consultada em 31/10/2026)

- **São Paulo:** o rewrite do Hosting para o Cloud Run funciona com `southamerica-east1`. O Firestore e o Cloud Run têm região em São Paulo. O Cloud Run de São Paulo fica na faixa de preço "Tier 2".
- **Plano:** usar o Cloud Run exige uma conta de faturamento ligada ao projeto, o que passa o projeto para o plano Blaze. Há cota gratuita; confira os valores na página do Google.
- **Disco efêmero:** o sistema de arquivos do Cloud Run fica em memória e é apagado quando a instância para. Por isso o banco é o Firestore.
- **Limites do Hosting:** respostas a POST nunca entram em cache, e o tempo máximo de uma requisição é 60 segundos.
- **IP do visitante:** não está documentado em que posição o IP chega ao Cloud Run pelo Hosting. Calibre na homologação com `ORGATEC_DIAGNOSTICO_IP=1` (veja o passo 7 abaixo).

### Passo a passo (contas e cobrança são da ORGATEC)

1. **Projeto.** No console do Firebase, crie o projeto e ative o faturamento (plano Blaze).
2. **Banco.** Crie o Firestore em modo nativo, na região **southamerica-east1 (São Paulo)**. A região não pode ser trocada depois.
3. **Ferramentas, uma vez por máquina.** `firebase login` (a ferramenta já está instalada aqui). Instale o Google Cloud CLI e rode `gcloud auth login` e `gcloud config set project <id>`.
4. **Segredo do HMAC no Secret Manager.** Ele é gerado uma vez e nunca trocado:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32), end='')" | gcloud secrets create orgatec-segredo-ip --data-file=-
   ```

5. **API no Cloud Run, em São Paulo.** Este comando compila o `Dockerfile` na nuvem:

   ```bash
   gcloud run deploy orgatec-api --source . --region southamerica-east1 --max-instances 1 --allow-unauthenticated --set-secrets ORGATEC_SEGREDO_IP=orgatec-segredo-ip:latest --set-env-vars ORGATEC_BANCO=firestore,ORGATEC_SERVIR_SITE=0,ORGATEC_PRODUCAO=1,ORGATEC_INDEXAR=0,ORGATEC_CABECALHO_IP=x-forwarded-for,ORGATEC_DIAGNOSTICO_IP=1,ORGATEC_ORIGENS=https://<id>.web.app
   ```

   - `--max-instances 1` mantém a cadeia de auditoria sem disputa; é folgado para o volume de formulários.
   - `--allow-unauthenticated` é necessário porque o site é público.
   - A conta de serviço do Cloud Run precisa do papel "Usuário do Cloud Datastore" no projeto para gravar no Firestore.

6. **Site e encaminhamento da API.**

   ```bash
   python tools/preparar_firebase.py --projeto <id> --cloud-run orgatec-api
   firebase deploy --only hosting,firestore:rules
   ```

7. **Calibrar o IP do visitante.**
   - Envie um contato de teste pelo site, de uma rede cujo IP você conheça.
   - Nos logs do Cloud Run, procure a linha `diagnostico-ip`, que mostra o `X-Forwarded-For` com o último bloco mascarado.
   - Veja em que posição está o seu IP e grave essa posição em `ORGATEC_IP_POSICAO`: `-2` para penúltimo, `0` para primeiro.
   - Depois, desligue o diagnóstico com `ORGATEC_DIAGNOSTICO_IP=0`.
8. **Conferir.** Abra `https://<id>.web.app/testes/index.html`: o autoteste deve passar. Envie um contato e confira se ele recebe protocolo.

### Ligar a Central de Viagem na API já publicada (módulo `backend/transporte/`)

O módulo nasce desligado. Para ligar no `orgatec-api`, **use `--update-env-vars`** (e não `--set-env-vars`, que apagaria as variáveis dos formulários):

```bash
firebase deploy --only firestore:indexes --project <id>
gcloud run deploy orgatec-api --source . --region southamerica-east1 --max-instances 1 --update-env-vars ORGATEC_TRANSPORTE=1,ORGATEC_TRANSPORTE_AUTH=firebase,ORGATEC_FIREBASE_PROJETO=<id>,ORGATEC_TRANSPORTE_BANCO=firestore,ORGATEC_TRANSPORTE_FIREBASE_WEB_KEY=<chave web>
gcloud run jobs update orgatec-retencao --region southamerica-east1 --image <imagem da API> --update-env-vars ORGATEC_TRANSPORTE_BANCO=firestore
```

- Antes: autorize o domínio do site em Authentication → Configurações → Domínios autorizados e restrinja a chave web ao referenciador `https://<domínio>/*`.
- Confira: `/api/transporte/contexto` deve sair de 404 para 200 e `/api/saude` seguir em 200.
- **Primeiro cliente:** crie a transportadora e dê acesso ao usuário (criado antes no Firebase Authentication).

  ```bash
  gcloud auth application-default login
  python tools/transporte_transportadora.py --projeto <id>
  python tools/transporte_usuario.py --projeto <id> --email <email> --transportadora <uuid impresso> --papel gestor
  ```

  O acesso vale no próximo login (até 1 hora). Para retirar: `transporte_usuario.py ... --revogar`.
- Sensores, rota, clima, combustível e pedágio reais seguem desligados até haver as flags `ORGATEC_TRANSPORTE_*` correspondentes. Combustível (ANP) e pedágio (ANTT): o `Dockerfile` baixa os arquivos na construção da imagem (estágio `dados`, `tools/transporte_dados_abertos.py`) e os deixa em `/app/dados-abertos`. Para usar: `--update-env-vars ORGATEC_TRANSPORTE_COMBUSTIVEL_REAL=1,ORGATEC_TRANSPORTE_PEDAGIO_REAL=1`. A ANP publica um arquivo por mês, então reimplante a API uma vez por mês para renovar o diesel. Se o gov.br estiver fora do ar na construção, a imagem sai sem os arquivos e só esses dois provedores ficam indisponíveis (a tela mostra o estado ao lado do dado). O pedágio da ANTT traz as praças, não a tarifa: o valor segue o parâmetro da transportadora.

### Mapa real, postos e lançamentos da Central de Viagem

O mapa da Central e do Portal é o **Google Maps** (satélite com rótulos, com troca para ruas e relevo). A escolha segue os termos do
Google Maps Platform, conferidos em 10/11/2026: a rota (Routes API) e os postos (Places API) **não podem aparecer em mapa de outro
provedor** (termos gerais 3.2.3(e); Service Specific Terms 19.2 e 14.2). Sem chave, ou se o Google recusar a chave, a tela volta ao
diagrama SVG do traçado, o que os termos permitem (19.1 e 14.1).

**1. Chave do mapa (navegador).** Em Console › APIs e serviços › Credenciais, crie uma chave nova só para o mapa:
- Restrições de aplicativo: **Referenciadores HTTP**, `https://orgatec.io/*` (e o endereço de prévia, se for testar nele).
- Restrições de API: só **Maps JavaScript API** (ative a API antes em Biblioteca).
- Opcional, recomendado: em Gerenciamento de mapas, crie um **Map ID** (tipo JavaScript, raster). Com ele, os marcadores usam
  `AdvancedMarkerElement`; sem ele, usam `google.maps.Marker`, que o Google marcou como obsoleto (sem data de desligamento, com aviso de 12 meses).

A chave fica numa variável de ambiente do Cloud Run e só é entregue à tela depois do login (`/api/transporte/contexto`):

```bash
gcloud run services update orgatec-api --region southamerica-east1 --update-env-vars ORGATEC_TRANSPORTE_MAPS_CHAVE_WEB=<chave do mapa>,ORGATEC_TRANSPORTE_MAPS_ID=<map id>
```

**2. Postos ao longo da rota (servidor).** Ative a **Places API (New)** no projeto e acrescente-a às APIs permitidas da chave do
servidor (o segredo `orgatec-google-chave`, que já atende Routes e Geocoding). Depois:

```bash
gcloud run services update orgatec-api --region southamerica-east1 --update-env-vars ORGATEC_TRANSPORTE_POSTOS_REAL=1
```

Uma busca "ao longo da rota" (Text Search Pro, até 20 postos a até 3 km do traçado) por cálculo ou recálculo de viagem; abrir a viagem
não consulta de novo. O preço exibido é a **média da ANP no município do posto** (ou na UF), rotulada como média; nunca o preço do posto.

**3. Teto de gasto.** Orçamento só avisa. O corte real é a cota diária por API em Console › APIs e serviços › Cotas
(fonte: developers.google.com/maps/billing-and-pricing/manage-costs). Para ficar na faixa gratuita mensal, divida a cota mensal por 31:

| API (SKU) | Gratuito por mês | Acima disso, por 1.000 | Cota diária sugerida |
|---|---|---|---|
| Maps JavaScript API, Dynamic Maps | 10.000 carregamentos | US$ 7,00 | 322 |
| Places API (New), Text Search Pro | 5.000 | US$ 32,00 | 161 |
| Routes API, Compute Routes Essentials | 10.000 | US$ 5,00 | 322 |
| Geocoding API | 10.000 | US$ 5,00 | 322 |

Valores da tabela oficial (developers.google.com/maps/billing-and-pricing/pricing), lidos em 10/11/2026. A página não diz se o modo
satélite do mapa JavaScript entra no mesmo SKU de Dynamic Maps; confira no relatório de faturamento no primeiro mês.
A tela cria o mapa uma vez por página aberta e o reaproveita nas atualizações, então cada abertura da Central conta um carregamento.

**4. Prazo de 30 dias.** Os termos (19.3 e 14.3) só permitem guardar latitude e longitude da Routes e da Places por 30 dias. O job
`orgatec-retencao` (`tools/lgpd.py retencao --confirmar`) apaga, depois de 29 dias, o traçado, os pontos geocodificados, os pontos de
clima e as coordenadas dos postos. Distâncias, tempos, valores, praças da ANTT e pontos digitados ficam. A tela avisa e o gestor pode
recalcular a viagem. Reimplante o job com a imagem nova para valer:
`gcloud run jobs update orgatec-retencao --region southamerica-east1 --image <imagem da API>`.

**5. Lançamentos manuais (Firestore).** Coleção `transporte_lancamentos`, no mesmo formato das outras (documento
`<transportadora>__<id>` com `tid`, `id` e `doc`). Campos do registro: `tipo` (`abastecimento`, `pedagio_pago`, `parada`, `ocorrencia`
ou `posicao_manual`), `ts`, `local`, `lat` e `lon` (opcionais; obrigatórios na posição), `valor`, `litros` e `preco_l` (só
abastecimento), `observacao`, `viagem_id`, `autor_id`, `criado_em`, `fonte` = "informado manualmente" e a remoção lógica
(`removido`, `removido_por`, `removido_em`). As regras do Firestore não mudam: o navegador continua sem acesso; só a API lê e grava.
A posição informada à mão é dado pessoal do motorista, como a telemetria (ver `docs/lgpd/transporte-monitoramento.md`).

**Atualização da tela.** A Central consulta viagem, lançamentos e posição a cada 15 s com a aba visível e redesenha só o que mudou,
sem apagar o que estiver sendo digitado. Não há listener do Firestore no navegador, porque isso exigiria abrir as regras do banco.

### Testar localmente com o emulador

```bash
firebase emulators:exec --only firestore --project demo-orgatec "python -m pytest tests/py/test_repositorio_contrato.py"
```

## Alternativa mantida: Firebase Hosting (site) + Railway (API)

O mesmo `Dockerfile` roda na Railway com SQLite e volume em `/dados`. Para ligar os dois lados, rode `python tools/preparar_firebase.py --projeto <id> --api https://<api>.up.railway.app`.

Pontos da documentação da Railway (31/10/2026):
- o `railway.json` foi descontinuado e deixa de ser lido em 01/12/2026;
- não há região no Brasil;
- o IP do visitante chega em `X-Real-IP`, então use `ORGATEC_CABECALHO_IP=x-real-ip`.

## Outras plataformas com Docker (referência)

O site continua em modo teste (`config.ambiente = 'homologacao'`) e fora dos buscadores.

### Em qualquer plataforma com Docker

1. Crie um serviço a partir deste repositório. A plataforma detecta o `Dockerfile`.
2. Cadastre as variáveis do `.env.example`:
   - `ORGATEC_SEGREDO_IP`: gere uma vez com `python -c "import secrets; print(secrets.token_hex(32))"` e não troque mais;
   - `ORGATEC_ORIGENS`: o endereço de homologação que a plataforma der, por exemplo `https://orgatec-homologacao.up.railway.app`;
   - `ORGATEC_PROXY_IPS`: o IP ou faixa do proxy da plataforma. `*` só serve se o contêiner não aceitar tráfego direto;
   - `ORGATEC_INDEXAR=0`.
3. Monte um **volume persistente em `/dados`**. Sem ele, os leads somem a cada nova versão.
4. Configure a verificação de saúde em `/api/saude`.
5. Abra o endereço e rode o painel `/testes/index.html`: o autoteste deve passar inteiro.

### Railway, se for a escolha

O projeto tem as ferramentas da Railway disponíveis. Com a sua autorização:
- criar o projeto e o serviço;
- cadastrar as variáveis e o volume `/dados`;
- gerar o domínio de homologação.

O segredo é gerado na hora e cadastrado direto na plataforma. Ele nunca é escrito no repositório.

## Antes da produção (painel de testes)

Só troque `ORGATEC_INDEXAR=1` e `config.ambiente = 'producao'` quando o painel de testes não tiver mais bloqueios. Os principais:

| Pendência | O que falta |
|---|---|
| V1 | Revisão técnica dos itens da reforma (em produção, só os aprovados aparecem) |
| V6 | Aprovar os prazos de retenção da política de privacidade |
| C4 e C5 | E-mail do encarregado de dados ativo; WhatsApp validado |
| C2, D2 e T5 | Sistema do portal do cliente, CNAME de `portal.orgatec.io` e certificado |
| T2 | Envio real do e-mail de confirmação do opt-in |
| T3 | Tailwind compilado no lugar do CDN; depois disso, tirar `'unsafe-inline'` do `script-src` |

## Domínio

- Aponte `orgatec.io` (ou `www`) para o serviço com o CNAME ou A indicado pela plataforma. O HTTPS vem da plataforma.
- Ajuste `ORGATEC_ORIGENS=https://orgatec.io,https://www.orgatec.io`.
- Mudar o DNS do domínio principal tira o site atual do ar: faça isso só na virada para produção.

## Backup e LGPD

- O banco tem dados pessoais de leads e contatos. Faça backup do volume `/dados` com acesso restrito.
- Os prazos de retenção valem só depois da aprovação da pendência V6.
- O segredo `ORGATEC_SEGREDO_IP` também precisa de backup em local seguro. Se ele se perder, os IPs gravados deixam de ser comparáveis.
