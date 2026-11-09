"""Recebe leituras de sensores: valida assinatura, normaliza, grava sem duplicar, liga à viagem e publica."""

from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from transporte.db.tabelas import LeituraTelemetria, Sensor, Viagem
from transporte.dominio import utc
from transporte.erros import AcessoNegado, EntradaInvalida, ErroTransporte
from transporte.geo import acumulado_km, distancia_ponto_rota_km
from transporte.telemetria.adaptadores import normalizar
from transporte.telemetria.broker import Broker
from transporte.telemetria.seguranca import Cofre, verificar_assinatura

TAMANHO_MAX_CORPO = 256 * 1024
DESVIO_ALERTA_KM = 5.0


class LimiteExcedido(ErroTransporte):
    codigo_http = 429
    mensagem_publica = "Muitas requisições deste sensor. Aguarde."


class Limitador:
    """Janela deslizante por sensor (em memória, por instância)."""

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


def viagem_ativa(sessao: Session, sensor: Sensor, ts: datetime) -> Viagem | None:
    return sessao.scalars(
        select(Viagem)
        .where(
            Viagem.transportadora_id == sensor.transportadora_id,
            Viagem.veiculo_id == sensor.veiculo_id,
            Viagem.status.in_(["planejada", "em_andamento"]),
            Viagem.deleted_at.is_(None),
            Viagem.partida_prevista <= utc(ts) + timedelta(hours=12),
        )
        .order_by(Viagem.partida_prevista.desc())
        .limit(1)
    ).first()


def receber(
    sessao: Session,
    cofre: Cofre,
    broker: Broker,
    limitador: Limitador,
    sensor_id: str,
    corpo: bytes,
    timestamp: str | None,
    assinatura: str | None,
) -> dict[str, Any]:
    if len(corpo) > TAMANHO_MAX_CORPO:
        raise EntradaInvalida("Corpo acima de 256 KB.")
    sensor = sessao.get(Sensor, sensor_id)
    if sensor is None or not sensor.ativo:
        raise AcessoNegado()  # não revela se o sensor existe
    verificar_assinatura(cofre.decifrar(sensor.segredo_cifrado), timestamp, assinatura, corpo)
    limitador.registrar(sensor_id)
    try:
        bruto = json.loads(corpo)
    except ValueError as exc:
        raise EntradaInvalida("Corpo não é JSON válido.") from exc
    leituras = sorted(normalizar(sensor.fornecedor, bruto), key=lambda leitura: leitura.ts)
    ja_vistas = set(
        sessao.scalars(
            select(LeituraTelemetria.leitura_id).where(
                LeituraTelemetria.sensor_id == sensor.id,
                LeituraTelemetria.leitura_id.in_([leitura.id for leitura in leituras]),
            )
        )
    )
    gravadas, eventos = 0, []
    for le in leituras:
        if le.id in ja_vistas:
            continue
        ja_vistas.add(le.id)
        viagem = viagem_ativa(sessao, sensor, le.ts)
        sessao.add(
            LeituraTelemetria(
                transportadora_id=sensor.transportadora_id,
                sensor_id=sensor.id,
                viagem_id=viagem.id if viagem else None,
                leitura_id=le.id,
                ts=utc(le.ts),
                lat=le.lat,
                lon=le.lon,
                velocidade_kmh=le.velocidade_kmh,
                ignicao=le.ignicao,
                temperatura_c=le.temperatura_c,
                combustivel_pct=le.combustivel_pct,
                evento=le.evento,
            )
        )
        gravadas += 1
        if viagem is not None:
            if viagem.status == "planejada":
                viagem.status = "em_andamento"
            eventos.append((viagem, le))
    sessao.flush()
    if leituras:
        ultimo = utc(leituras[-1].ts)
        if sensor.ultimo_sinal_em is None or ultimo > utc(sensor.ultimo_sinal_em):
            sensor.ultimo_sinal_em = ultimo
    sessao.commit()
    for viagem, le in eventos:
        broker.publicar(viagem.id, evento_posicao(viagem, sensor.nome, le))
    return {"recebidas": len(leituras), "gravadas": gravadas, "duplicadas": len(leituras) - gravadas}


def evento_posicao(viagem: Viagem, sensor_nome: str, le: Any) -> dict[str, Any]:
    geo = [tuple(p) for p in viagem.resultado["rota"]["geometria"]]
    desvio, km = distancia_ponto_rota_km((le.lat, le.lon), geo)  # type: ignore[arg-type]
    total_geo = viagem.resultado["rota"]["distancia_km"]
    acc = acumulado_km(geo)  # type: ignore[arg-type]
    escala = total_geo / acc[-1] if acc[-1] else 1.0
    ts = le.ts if isinstance(le.ts, datetime) else datetime.fromisoformat(str(le.ts))
    return {
        "tipo": "posicao",
        "viagem_id": viagem.id,
        "status": viagem.status,
        "sensor": sensor_nome,
        "ts": utc(ts).isoformat(),
        "lat": le.lat,
        "lon": le.lon,
        "velocidade_kmh": le.velocidade_kmh,
        "ignicao": le.ignicao,
        "temperatura_c": le.temperatura_c,
        "combustivel_pct": le.combustivel_pct,
        "evento": le.evento,
        "km_percorrido": round(km * escala, 1),
        "desvio_km": round(desvio, 1),
        "fora_da_rota": desvio > DESVIO_ALERTA_KM,
    }
