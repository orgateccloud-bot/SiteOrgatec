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
- **Retenção:** não ligue a política de TTL do Firestore, porque ela apaga o documento inteiro e quebra a trilha. A eliminação roda em `tools/lgpd.py`, que apaga só os dados pessoais. Agende `python tools/lgpd.py retencao --confirmar` uma vez por dia, com as mesmas variáveis da API (`ORGATEC_BANCO`, `ORGATEC_SEGREDO_IP`).
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
