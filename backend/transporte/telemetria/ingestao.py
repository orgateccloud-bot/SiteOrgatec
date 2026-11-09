"""Recebe leituras de sensores: confere a assinatura, normaliza, grava sem duplicar (idempotente) e liga à viagem.

Falhas de segurança respondem sempre 403 sem dizer o motivo (sensor inexistente, inativo, assinatura ou relógio inválidos).
O tempo real da v1 é por consulta: a tela chama /posicoes a cada 15 segundos (sem canal aberto: o Cloud Run escala em várias instâncias).
"""

from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Any

from backend.transporte.dominio import utc
from backend.transporte.erros import AcessoNegado, EntradaInvalida, ErroTransporte
from backend.transporte.geo import acumulado_km, distancia_ponto_rota_km
from backend.transporte.repositorio_transporte import RepositorioMemoria
from backend.transporte.telemetria.adaptadores import normalizar
from backend.transporte.telemetria.seguranca import Cofre, verificar_assinatura

TAMANHO_MAX_CORPO = 256 * 1024
DESVIO_ALERTA_KM = 5.0


class LimiteExcedido(ErroTransporte):
    codigo_http = 429
    mensagem_publica = "Muitas requisições deste sensor. Aguarde."


class Limitador:
    """Janela deslizante por sensor (em memória, por instância: com várias instâncias o limite é por instância)."""

    def __init__(self, maximo: int = 120, janela_s: float = 60.0) -> None:
        self._maximo, self._janela = maximo, janela_s
        self._hist: dict[str, deque[float]] = defaultdict(deque)
        self._trava = threading.Lock()

    def registrar(self, chave: str) -> None:
        agora = time.monotonic()
        with self._trava:
            h = self._hist[chave]
            while h and h[0] < agora - self._janela:
                h.popleft()
            if len(h) >= self._maximo:
                raise LimiteExcedido()
            h.append(agora)


def receber(repo: RepositorioMemoria, cofre: Cofre, limitador: Limitador, sensor_id: str, corpo: bytes,
            timestamp: str | None, assinatura: str | None) -> dict[str, Any]:
    if len(corpo) > TAMANHO_MAX_CORPO:
        raise EntradaInvalida("Corpo acima de 256 KB.")
    sensor = repo.sensor_global(sensor_id)
    if sensor is None or not sensor["ativo"]:
        raise AcessoNegado()
    verificar_assinatura(cofre.segredo_do_sensor(sensor["id"], sensor["versao"]), timestamp, assinatura, corpo)
    limitador.registrar(sensor_id)
    try:
        bruto = json.loads(corpo)
    except ValueError as exc:
        raise EntradaInvalida("Corpo não é JSON válido.") from exc
    tid = sensor["transportadora_id"]
    leituras = sorted(normalizar(sensor["fornecedor"], bruto), key=lambda le: le.ts)
    gravadas = 0
    for le in leituras:
        if repo.leitura_ja_vista(tid, sensor["id"], le.id):
            continue
        viagem = repo.viagem_ativa(tid, sensor["veiculo_id"], le.ts)
        repo.inserir(tid, "leituras", {
            "sensor_id": sensor["id"], "viagem_id": viagem["id"] if viagem else None, "leitura_id": le.id, "ts": utc(le.ts),
            "lat": le.lat, "lon": le.lon, "velocidade_kmh": le.velocidade_kmh, "ignicao": le.ignicao,
            "temperatura_c": le.temperatura_c, "combustivel_pct": le.combustivel_pct, "evento": le.evento})
        gravadas += 1
        if viagem and viagem["status"] == "planejada":
            repo.atualizar(tid, "viagens", viagem["id"], {"status": "em_andamento"})
    if leituras:
        ultimo = utc(leituras[-1].ts)
        anterior = sensor.get("ultimo_sinal_em")
        if anterior is None or ultimo > utc(anterior):
            repo.atualizar(tid, "sensores", sensor["id"], {"ultimo_sinal_em": ultimo})
    return {"recebidas": len(leituras), "gravadas": gravadas, "duplicadas": len(leituras) - gravadas}


def evento_posicao(viagem: dict[str, Any], sensor_nome: str, le: dict[str, Any]) -> dict[str, Any]:
    """Posição de uma leitura em relação à rota da viagem: km percorrido e desvio. Só coordenadas; nada de dado pessoal."""
    geo = [tuple(p) for p in viagem["resultado"]["rota"]["geometria"]]
    desvio, km = distancia_ponto_rota_km((le["lat"], le["lon"]), geo)  # type: ignore[arg-type]
    total = viagem["resultado"]["rota"]["distancia_km"]
    acc = acumulado_km(geo)  # type: ignore[arg-type]
    escala = total / acc[-1] if acc[-1] else 1.0
    ts = le["ts"] if isinstance(le["ts"], datetime) else datetime.fromisoformat(str(le["ts"]))
    return {"tipo": "posicao", "viagem_id": viagem["id"], "status": viagem["status"], "sensor": sensor_nome, "ts": utc(ts).isoformat(),
            "lat": le["lat"], "lon": le["lon"], "velocidade_kmh": le.get("velocidade_kmh"), "ignicao": le.get("ignicao"),
            "temperatura_c": le.get("temperatura_c"), "combustivel_pct": le.get("combustivel_pct"), "evento": le.get("evento"),
            "km_percorrido": round(km * escala, 1), "desvio_km": round(desvio, 1), "fora_da_rota": desvio > DESVIO_ALERTA_KM}
