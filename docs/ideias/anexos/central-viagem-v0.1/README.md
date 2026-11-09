# Central de Viagem — módulo de Transporte (ORGATEC)

Autoria: Warley Moreira Veloso · Versão 0.1.0 · 09/11/2026

Quando o motorista ou o gestor lança uma rota, a Central devolve:

- distância e tempo;
- jornada com pausas, pernoites e paradas;
- despesas previstas (combustível, ARLA, pedágio, hospedagem, alimentação, pneus, manutenção, borracharia, outros custos e reserva);
- bloqueios no trajeto;
- previsão do tempo por trecho.

O **Portal do cliente** mostra as mesmas informações em modo leitura. Nele o gestor conecta **sensores via API** (rastreador, telemetria, temperatura) para acompanhar a viagem em tempo real.

> **Situação da integração.** Este módulo foi escrito **sem acesso ao código do sistema**: o repositório não pôde ser anexado na sessão. A stack segue o padrão do documento de desenvolvimento do projeto: Python + FastAPI + SQLAlchemy + Alembic e PostgreSQL no back-end, front em JavaScript puro como o site orgatec.io. Antes de copiar para o projeto, confira a seção [Como integrar](#como-integrar).

## Requisitos

- Python 3.11 ou superior. Foi desenvolvido e testado com 3.13.
- PostgreSQL em produção. SQLite só para teste local.

## Instalação (Windows, PowerShell)

```powershell
cd D:\01_Projetos_Ativos\<projeto>\central-transporte
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,postgres]" uvicorn
Copy-Item .env.example .env   # preencha as variáveis
```

## Rodar em desenvolvimento (tudo simulado, sem chave de API)

```powershell
$env:TRANSPORTE_SENSORES_ATIVO = "true"
$env:TRANSPORTE_CHAVE_CRIPTO = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
$env:TRANSPORTE_CHAVE_STREAM = "troque-por-um-texto-aleatorio-longo"
uvicorn transporte.dev:app --reload
```

1. Abra `http://localhost:8000/transporte/central.html`.
2. No painel amarelo, informe a transportadora de demonstração `00000000-0000-4000-8000-000000000001`.
3. Lance a rota Goiânia (GO) → Palmas (TO).

O geocodificador simulado só conhece algumas cidades (Goiânia, Anápolis, Brasília, Palmas, São Paulo, Belém, Uruaçu, Porangatu). Para qualquer outro local, informe latitude e longitude.

Portal: `http://localhost:8000/transporte/portal.html`.
- Com o papel `gestor`: em "Conectar sensor via API", gere a credencial; ao abrir a viagem, use "Simular leituras do sensor".
- Com o papel `leitura`: é a visão do cliente.

Para acompanhar ao vivo com um sensor externo, a viagem precisa partir em até 12 horas a partir da leitura:

```powershell
python scripts\sensor_simulado.py --url http://localhost:8000 --sensor <id> --segredo <segredo> --de=-15.79,-47.88 --para=-16.68,-49.26 --passos 20 --intervalo 2
```

## Testes e qualidade

```powershell
pytest            # 56 testes
ruff check .      # lint
bandit -r transporte
```

## Configuração (`.env.example`)

| Variável | Padrão | Efeito |
|---|---|---|
| `TRANSPORTE_AMBIENTE` | desenvolvimento | Em `producao`, o modo de login `dev` e o sensor simulado são recusados |
| `TRANSPORTE_DATABASE_URL` | sqlite local | PostgreSQL em produção (`postgresql+psycopg://...`) |
| `TRANSPORTE_AUTH_MODO` | dev | `externo` = passar o autenticador do sistema hospedeiro |
| `TRANSPORTE_ROTA_REAL` | **false** | OpenRouteService (exige `TRANSPORTE_ORS_CHAVE`) |
| `TRANSPORTE_CLIMA_REAL` | **false** | MET Norway (exige `TRANSPORTE_METNO_USER_AGENT`) |
| `TRANSPORTE_COMBUSTIVEL_REAL` | **false** | CSV normalizado da ANP |
| `TRANSPORTE_PEDAGIO_REAL` | **false** | CSV normalizado das praças da ANTT |
| `TRANSPORTE_BLOQUEIO_MANUAL` | **false** | Bloqueios cadastrados pela transportadora, em vez dos simulados |
| `TRANSPORTE_SENSORES_ATIVO` | **false** | Sensores, telemetria e tempo real (exige as chaves de cripto e de stream) |

- Flag desligada significa provedor simulado. Tudo que vem de simulação aparece com o selo "simulado" na tela.
- A configuração é validada na subida: flag ligada sem a chave correspondente impede o app de iniciar.

## Fontes de dados

Verificação feita em 08 e 09/11/2026. Nenhuma API real foi chamada nesta entrega: os provedores reais foram testados só com respostas simuladas no formato documentado.

| Dado | Fonte padrão | Custo e limites | Situação |
|---|---|---|---|
| Rota, distância e tempo | OpenRouteService, perfil `driving-hgv` | Plano gratuito: 2.000 rotas/dia e 40/min (openrouteservice.org/plans). Sem SLA. Sem trânsito em tempo real | **Depende de chave.** Alternativa sem limite: servidor próprio do OpenRouteService ou do OSRM com o mapa do Brasil. O servidor público de demonstração do OSRM é proibido para uso comercial |
| Clima | MET Norway Locationforecast 2.0 (compact) | Gratuito. Exige User-Agent com nome do app e contato, e respeito ao cache | **Depende do User-Agent.** O uso comercial dentro do uso justo foi confirmado só em fonte secundária: conferir os termos em api.met.no/doc/TermsOfService. A Open-Meteo **não** é padrão porque o plano gratuito é só para uso não comercial |
| Diesel | ANP, Levantamento de Preços (semanal, CSV) | Gratuito, dados abertos | **Depende de conversor.** O provedor lê o CSV normalizado `uf;municipio;produto;preco_medio;data_referencia`. A rotina que converte o arquivo oficial **não está incluída**. Sem dado, usa o parâmetro da transportadora |
| Pedágio | ANTT, dados abertos "Praças de Pedágio" (lat/lon, situação) | Gratuito | **Depende de conversor e de validação.** CSV normalizado `concessionaria;praca;lat;lon;situacao;tarifa_cat1`. Só cobre concessões federais. **Tarifa em formato aberto não foi confirmada**; sem tarifa, usa o parâmetro da transportadora × eixos |
| Bloqueios e interdições | **Sem API aberta confirmada** (DNIT, PRF e ANTT só publicam painéis, aplicativos e notícias) | — | Cadastro manual pela transportadora (`/alertas`), com raio, validade e fonte. Uma API real pode entrar como novo provedor sem mudar o resto |
| Hospedagem, alimentação, pneus, manutenção, borracharia, ARLA | Sem fonte | — | Parâmetros por transportadora, versionados por vigência e editáveis na tela |
| Jornada | CTB art. 67-C (redação da Lei 13.103/2015) | — | Padrões: 5,5 h contínuas, 30 min de pausa, 11 h de descanso e 10 h de direção por dia. **Revisão jurídica pendente** (STF, ADI 5322) |

Robustez: as integrações têm timeout, até 3 tentativas com espera crescente (respeitando `Retry-After`), cache com validade e erros tipados.
- Sem rota, a viagem não é calculada e a API responde 503 informando qual fonte falhou.
- Falha de combustível, pedágio, clima ou bloqueio não derruba a viagem: o item afetado aparece com o estado da falha (`timeout`, `limite_excedido`, `indisponivel`).

## API

Prefixo `/api/transporte`. A documentação interativa fica em `/api/transporte/docs`.

| Método | Caminho | Papel |
|---|---|---|
| GET | `/contexto` | todos |
| GET / PUT | `/parametros` | todos / gestor |
| GET / POST | `/veiculos` | todos / gestor |
| GET / POST | `/motoristas` | gestor |
| POST | `/viagens` (lança a rota) | gestor, motorista |
| GET | `/viagens`, `/viagens/{id}` | todos (o motorista vê só as próprias) |
| PUT | `/viagens/{id}/despesas/{tipo}` (`{"valor": null}` desfaz o ajuste) | gestor |
| POST | `/viagens/{id}/recalcular`, `/viagens/{id}/status` | gestor / gestor, motorista |
| GET / POST | `/alertas` (bloqueios manuais) | todos / gestor, motorista |
| GET / POST / DELETE | `/sensores` (o segredo aparece uma vez só) | gestor · flag de sensores |
| GET | `/viagens/{id}/posicoes` | todos · flag de sensores |
| POST + GET | `/viagens/{id}/stream-token` + `/viagens/{id}/stream?token=` (SSE) | todos · flag de sensores |
| POST | `/viagens/{id}/simular-sensor` (fora de produção) | gestor · flag de sensores |
| POST | `/api/telemetria/{sensor_id}` | o sensor, por HMAC |

### Telemetria (qualquer fornecedor)

```
POST /api/telemetria/{sensor_id}
X-Timestamp: <segundos Unix>          # até 5 min de diferença do relógio do servidor
X-Assinatura: hex(HMAC-SHA256(segredo, "<timestamp>." + corpo))
{"leituras": [{"id": "único-por-sensor", "ts": "2026-11-10T08:00:00-03:00", "lat": -16.6, "lon": -49.2,
               "velocidade_kmh": 72, "ignicao": true, "temperatura_c": 4.1, "combustivel_pct": 63, "evento": null}]}
```

Regras de recebimento:
- Leitura repetida (mesmo `id`) é ignorada.
- Até 500 leituras e 256 KB por envio.
- Até 120 envios por minuto por sensor.
- A leitura se liga à viagem planejada ou em andamento do veículo que parta em até 12 horas a partir da leitura. A primeira leitura passa a viagem para "em andamento".

**Fornecedor novo:** escreva um adaptador em `transporte/telemetria/adaptadores.py`, que converte o formato do fornecedor para o formato acima, e registre-o no campo `fornecedor` do sensor. Nenhum formato de fornecedor específico foi implementado: nenhum foi fornecido nem verificado.

## Como integrar

1. **Back-end.** Confirme que o `backend/app.py` do site é FastAPI. O código público do site mostra Python atrás de `/api/**` no Cloud Run, mas não o framework. Se for, faça assim:
   ```python
   from transporte.api.app import incluir_no_app, montar_servicos
   from transporte.config import obter_config

   incluir_no_app(app, montar_servicos(obter_config(), autenticador=meu_autenticador))
   ```
   `meu_autenticador(request) -> Contexto` vem do login do sistema e devolve transportadora, usuário e papel. Se o back-end for Flask, a API precisa subir como serviço separado, atrás do mesmo rewrite do Firebase (`/api/transporte/**` e `/api/telemetria/**`).
2. **Banco.** `alembic upgrade head` com `TRANSPORTE_DATABASE_URL` apontando para o PostgreSQL. As tabelas têm o prefixo `tr_`.
3. **Front.** Copie `web/transporte/` para o site. As páginas respeitam a política de segurança atual (`script-src 'self'`, `connect-src 'self'`): sem script inline e sem recursos externos. O mapa é desenhado em SVG, sem imagens de fundo, porque a política bloqueia mapas de terceiros.
4. **Tempo real com mais de uma instância.** O distribuidor de eventos é em memória. No Cloud Run com escalonamento, troque por Redis Pub/Sub ou Firestore, mantendo a mesma interface (`telemetria/broker.py`). O limitador por sensor também é por instância.

## LGPD

- A posição do veículo identifica o motorista e é dado pessoal.
- O cadastro de motorista guarda só o nome e o vínculo de usuário: sem CPF, telefone ou endereço.
- As coordenadas não vão para log.
- O acesso fica restrito à transportadora; o motorista vê só as próprias viagens.
- Para as APIs estrangeiras (OpenRouteService, MET Norway) vão apenas coordenadas, sem nome.
- **Pendente:** definir a base legal do monitoramento, o prazo de guarda das leituras (a tabela `tr_leitura_telemetria` ainda não tem rotina de expurgo) e o aviso ao motorista.

## Estrutura

```
transporte/
  config.py, erros.py, dominio.py (esquemas e parâmetros), geo.py
  db/        tabelas.py (modelo), sessao.py, repositorios.py (isolamento por transportadora)
  provedores/ base.py (interfaces), simulados.py, reais.py, registro.py (flags), http.py, cache.py
  servicos/  jornada.py, despesas.py, viagem.py (montagem da viagem)
  telemetria/ seguranca.py (HMAC, cripto, token), adaptadores.py, ingestao.py, broker.py (SSE)
  api/       deps.py, rotas.py, telemetria.py, app.py
  dev.py     servidor de desenvolvimento com dados fictícios
migrations/  Alembic (0001)
web/transporte/  central.html, portal.html, comum.js, viagem-view.js, central.js, portal.js, transporte.css
scripts/sensor_simulado.py
tests/       56 testes
```
