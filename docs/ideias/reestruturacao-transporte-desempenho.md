# Central de Viagem: desempenho de 10 a 100 caminhões

Medido em 09/11/2026 com `python tools/transporte_carga.py` (servidor local, um processo uvicorn, máquina de desenvolvimento). A ferramenta é repetível e sai com erro quando um cenário passa dos limites de aceite: p95 da leitura ≤ 250 ms, p95 das posições ≤ 1.000 ms, erros ≤ 0,5%.

## O que a carga faz

- Cada caminhão envia uma leitura de posição assinada (HMAC) a cada N segundos.
- Um painel por 5 caminhões consulta as posições a cada 15 s, com um usuário por painel.
- O gestor lança uma viagem por caminhão no início (cálculo de rota e de despesas).

## Resultado no ritmo real (uma leitura a cada 10 s, 45 s de tráfego)

| Caminhões | Banco | Leitura p50 | Leitura p95 | Posições p95 | Erros |
|---|---|---|---|---|---|
| 10 | SQLite | 21 ms | 32 ms | 25 ms | 0% |
| 20 | SQLite | 14 ms | 35 ms | 23 ms | 0% |
| 30 | SQLite | 16 ms | 34 ms | 40 ms | 0% |
| 50 | SQLite | 18 ms | 33 ms | 34 ms | 0% |
| 100 | SQLite | 15 ms | 37 ms | 109 ms | 0% |
| 100 | memória | 17 ms | 34 ms | 44 ms | 0% |

O lançamento de uma viagem (rota e despesas simuladas) leva cerca de 8 ms.

## Teste de estresse (uma leitura por segundo por caminhão, 10 vezes o ritmo real)

| Caminhões | Banco | Antes das correções, p95 | Depois, p95 |
|---|---|---|---|
| 50 | memória | 54 ms | 11 ms |
| 100 | memória | 585 ms (reprovado) | 72 ms |
| 10 | SQLite | 245 ms | 15 ms |
| 20 | SQLite | 1.032 ms (reprovado) | 19 ms |
| 50 | SQLite | 4.063 ms (reprovado) | 20 ms |
| 100 | SQLite | 26.285 ms (reprovado) | 328 ms (reprovado por pouco; 100 requisições por segundo em um processo) |

## O que estava errado e foi corrigido

1. **Limite por IP dos formulários valendo para toda a API.** Eram 20 requisições a cada 10 minutos, e o painel consulta 4 vezes por minuto. Agora o limite é por usuário logado (600 por minuto); o limite por IP só conta acessos negados.
2. **Idempotência varrendo todas as leituras do cliente.** Agora é uma busca direta pela chave `sensor:leitura`.
3. **Posições carregando todas as leituras de todas as viagens.** Agora é uma consulta indexada (`leituras_da_viagem`, 200 mais recentes), e a geometria da rota é preparada uma vez por pedido.
4. **Viagem ativa relida a cada leitura.** Cache de 15 s por veículo, desfeito quando o status muda.
5. **Uma escrita a mais por leitura** (`último sinal`). Agora no máximo uma a cada 30 s por sensor.
6. **SQLite abrindo uma conexão por operação.** Agora uma conexão por thread, com WAL e `synchronous=NORMAL`, e índices por viagem, veículo e data.

## Limites que continuam e o que fazer quando chegarem

| Situação | Sinal | Mudança mapeada |
|---|---|---|
| Mais de uma instância no Cloud Run | limite por sensor e cache da viagem ativa passam a valer por instância | Redis (ou Memorystore) para o limitador e o cache; ou `--max-instances=1` enquanto a frota for pequena |
| Mais de ~100 leituras por segundo em um processo | p95 da leitura acima de 250 ms | mais de um processo (workers) e fila de gravação em lote; aceitar lotes de leituras do rastreador, que já são suportados (até 500 por envio) |
| Volume de dados | 100 caminhões a cada 10 s são 864 mil leituras por dia e cerca de 26 milhões com a guarda de 30 dias | pedir ao rastreador envio a cada 30 s (8,6 milhões), guardar só uma leitura por minuto fora da viagem em andamento, ou mover as leituras para armazenamento de séries (BigQuery) |
| Custo no Firestore | cada leitura é uma escrita | 864 mil escritas por dia custam na ordem de US$ 1,5 por dia a preços de tabela (conferir a tabela vigente); agrupar leituras reduz o custo |
| Lista de viagens e de veículos grandes | `GET /viagens` lê todas as viagens do cliente e devolve as 50 mais recentes | consulta paginada e indexada por data de partida no SQLite e no Firestore |
| Índice composto no Firestore | consulta de posições falha em produção sem ele | `firestore.indexes.json` já traz o índice; ele precisa ser publicado junto com as regras |

## Como repetir

```bash
python tools/transporte_carga.py --frota 10 20 30 50 100 --banco memoria sqlite --duracao 45 --intervalo 10
python tools/transporte_carga.py --frota 100 --banco sqlite --duracao 30 --intervalo 1     # estresse
```

Não foi medido: Firestore real (latência de rede e custo), várias instâncias e rastreadores de fornecedores reais.
