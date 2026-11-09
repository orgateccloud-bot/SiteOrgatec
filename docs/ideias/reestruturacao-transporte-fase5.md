# Fase 5: Central de Viagem e portal do cliente com sensores

Situação: **implementada atrás de flag desligada.** A persistência existe (SQLite e Firestore, por `ORGATEC_TRANSPORTE_BANCO`; padrão `memoria`), mas o Firestore só foi testado no contrato com o emulador, que não rodou aqui (casos pulados). Em produção a API segue recusando tudo sem login real (R4). O que depende de aprovação está na seção "Aprovações pendentes".

## O que existe

| Parte | Onde | Observação |
|---|---|---|
| Domínio, jornada, despesas, rota e geografia | `backend/transporte/dominio.py`, `servicos/`, `geo.py` | Reaproveitado do módulo de referência. Os casos de referência conferidos à mão (jornada de 1.200 km em 33 h e as despesas) passam como testes. |
| Provedores simulados | `backend/transporte/provedores/` | Rota, clima, combustível, pedágio e bloqueio. Os reais **não existem** (ver pendências). |
| Telemetria | `backend/transporte/telemetria/` | Assinatura HMAC, adaptadores por fornecedor, ingestão idempotente e limitador por sensor. |
| Persistência | `backend/transporte/repositorio_transporte.py` | Memória, SQLite (`transporte_docs`) e Firestore (`transporte_<coleção>`). Padrão: memória. Prazo de guarda das leituras aplicado por `python tools/lgpd.py retencao --confirmar`. |
| API | `backend/transporte/api.py`, incluída em `backend/app.py` | `APIRouter` com documentação automática desligada, o limite por IP do app e o mesmo tratamento de IP. |
| Telas | `site/transporte/central.html` e `portal.html` (gerador `tools/paginas_transporte.py`) | `noindex`, fora do menu, do hub e do mapa. Usam `orgatec.css` e os tokens (tema claro e escuro). |
| Testes | `tests/py/transporte/` (36 testes) | Isolamento entre transportadoras, papéis, portal em leitura, sensor, idempotência, 403 sem motivo, limite, produção recusa o modo dev. |

## Como ligar (somente desenvolvimento)

```bash
ORGATEC_TRANSPORTE=1 ORGATEC_TRANSPORTE_SENSORES=1 ORGATEC_TRANSPORTE_DEMO=1 \
ORGATEC_TRANSPORTE_CHAVE=<texto aleatório com 32 caracteres ou mais> \
python -m uvicorn backend.app:app --port 8000
```

Abra `http://localhost:8000/transporte/central.html`. No painel amarelo, informe a transportadora de demonstração `00000000-0000-4000-8000-000000000001`. Para um sensor externo: `POST /api/telemetria/<id>` com `X-Timestamp` e `X-Assinatura` (HMAC-SHA256 de `timestamp.corpo`).

Flags (todas desligadas por padrão): `ORGATEC_TRANSPORTE`, `ORGATEC_TRANSPORTE_SENSORES`, `ORGATEC_TRANSPORTE_DEMO`, `ORGATEC_TRANSPORTE_AUTH` (`dev` ou `externo`), `ORGATEC_TRANSPORTE_*_REAL` (recusadas hoje).

## Diferenças em relação ao módulo de referência (e o porquê)

- **Banco:** SQLAlchemy, Alembic e PostgreSQL saíram. Entrou o repositório em memória.
- **Segredo do sensor sem biblioteca nova:** o módulo de referência cifrava o segredo com Fernet (`cryptography`). Aqui o segredo é derivado, `HMAC(chave mestra, "sensor|id|versão")`, exibido uma vez e recalculado na conferência. Não há segredo em repouso. Rotacionar = subir a versão do sensor.
- **Tempo real:** sem SSE (o Cloud Run escala em várias instâncias). A tela consulta `/posicoes` a cada 15 segundos.
- **Configuração:** variáveis `ORGATEC_*` no lugar de `pydantic-settings`.
- **Dependências novas no servidor:** nenhuma.

## Requisitos do briefing: situação

| Requisito | Situação |
|---|---|
| Ao lançar a rota: despesas, tempo, bloqueios e clima | Feito, **com dados simulados**. Testado na API e na tela. |
| Parâmetros ajustáveis pela transportadora | Feito (`PUT /parametros`, tela de parâmetros). Teste de que mudar a diária muda o total. |
| Frota pequena, média e grande | Sem limite fixo no código; **não medido** com carga. |
| Portal em modo leitura | Feito (papel `leitura` só lê; testado). |
| Sensor com credencial HMAC exibida uma vez | Feito. |
| Qualquer fornecedor por adaptador | Mecanismo pronto (`telemetria/adaptadores.py`); só o formato `generico` existe. |
| Leituras idempotentes e posição em tempo real | Feito, por consulta a cada 15 s. |
| Sensor simulado atualiza posição e status | Feito (`/simular-sensor`, recusado em produção). |
| Testes de falha, timeout e limite nas integrações | **Parcial:** serviços testam `ProvedorTimeout` e `ProvedorLimiteExcedido` e a ingestão testa 429. Os testes de HTTP e cache dos provedores reais não foram portados, porque os provedores reais não existem. |
| Documentação de uso e configuração | Este arquivo. |

## Aprovações pendentes (parei antes de decidir)

1. **Persistência (implementada; falta rodar o contrato no emulador do Firestore e criar as coleções em produção).** Proposta de coleções no Firestore (e tabelas equivalentes no SQLite), todas com `transportadora_id` e consultas sempre filtradas por ele: `transporte_veiculos`, `transporte_motoristas` (só nome e vínculo de usuário), `transporte_viagens` (com o resultado calculado), `transporte_alertas`, `transporte_sensores` (sem segredo) e `transporte_leituras` (com prazo de guarda). O contrato é o de `RepositorioMemoria`; o teste de contrato seguiria o padrão de `tests/py/test_repositorio_contrato.py`, com o emulador. Criar coleção é decisão do escritório.
2. **Provedores reais.** OpenRouteService (precisa de chave, sem SLA, 2.000 rotas por dia), MET Norway (User-Agent identificado, uso comercial a confirmar nos termos), ANP (falta o conversor do arquivo oficial) e pedágio ANTT (tarifa em formato aberto não confirmada). Precisam de um cliente HTTP no servidor, que é dependência nova (`httpx`), além de chave e termos conferidos. Sem aprovação ficam recusados.
3. **Login e área do cliente (R4/D2).** Sem autenticador real, em produção toda chamada responde 403. Não ativei o Firebase Authentication.
4. **Base legal do monitoramento de motoristas.** Rascunho em `docs/lgpd/transporte-monitoramento.md`, para revisão do responsável técnico e do encarregado.
5. **Remover `docs/ideias/anexos/central-viagem-v0.1/`.** O prompt manda apagar ao terminar a Fase 5. **Não apaguei**: restam nele os provedores reais e seus testes, a migração de banco e o `scripts/sensor_simulado.py`. Apagar depois dos itens 1 e 2.
