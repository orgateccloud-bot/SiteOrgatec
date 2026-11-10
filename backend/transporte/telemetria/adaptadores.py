"""Adaptadores por fornecedor: convertem o corpo recebido em leituras normalizadas (LeituraEntrada).

Para integrar um fornecedor novo: escreva uma função `(dict) -> list[dict]` que devolva leituras no formato de
LeituraEntrada e registre em ADAPTADORES com o mesmo nome usado no campo `fornecedor` do sensor. Formatos de
fornecedores específicos não foram implementados porque não foram fornecidos nem verificados.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from backend.transporte.dominio import LeituraEntrada
from backend.transporte.erros import EntradaInvalida

MAX_LEITURAS = 500


def generico(corpo: dict[str, Any]) -> list[dict[str, Any]]:
    """Formato próprio da Central: {"leituras": [{id, ts, lat, lon, velocidade_kmh?, ignicao?, ...}]}."""
    leituras = corpo.get("leituras")
    if not isinstance(leituras, list):
        raise EntradaInvalida("Campo 'leituras' (lista) é obrigatório.")
    return leituras


def _numero(v: Any) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _instante(v: Any) -> str:
    """Traccar Client manda ISO 8601 (JSON) ou época em segundos ou milissegundos (parâmetros)."""
    n = _numero(v)
    if n is not None:
        return datetime.fromtimestamp(n / 1000 if n > 1e11 else n, UTC).isoformat()
    if isinstance(v, str) and v:
        return v
    raise EntradaInvalida("Leitura sem horário.")


def traccar_client(corpo: dict[str, Any]) -> list[dict[str, Any]]:
    """App Traccar Client (protocolo OsmAnd, https://www.traccar.org/osmand/). Aceita as duas formas do protocolo:
    JSON {"device_id", "location": {"timestamp", "coords": {"latitude", "longitude", "speed" em m/s}}} e parâmetros
    {id, lat, lon, timestamp, speed em nós}. Velocidade negativa (desconhecida) vira vazia. Uma posição por envio."""
    loc = corpo.get("location")
    if isinstance(loc, dict):
        c = loc.get("coords") or {}
        lat, lon, vel, fator, ts = c.get("latitude"), c.get("longitude"), _numero(c.get("speed")), 3.6, loc.get("timestamp")
        evento = loc.get("event") if isinstance(loc.get("event"), str) else None
    else:
        lat, lon, vel, fator, ts, evento = corpo.get("lat"), corpo.get("lon"), _numero(corpo.get("speed")), 1.852, corpo.get("timestamp"), None
    if _numero(lat) is None or _numero(lon) is None:
        raise EntradaInvalida("Leitura sem latitude ou longitude.")
    instante = _instante(ts)
    return [{"id": "tc-" + instante, "ts": instante, "lat": _numero(lat), "lon": _numero(lon),
             "velocidade_kmh": round(vel * fator, 1) if vel is not None and vel >= 0 else None,
             "evento": evento[:40] if evento else None}]


ADAPTADORES: dict[str, Callable[[dict[str, Any]], list[dict[str, Any]]]] = {"generico": generico, "traccar_client": traccar_client}


def normalizar(fornecedor: str, corpo: Any) -> list[LeituraEntrada]:
    if not isinstance(corpo, dict):
        raise EntradaInvalida("Corpo deve ser um objeto JSON.")
    adaptador = ADAPTADORES.get(fornecedor)
    if adaptador is None:
        raise EntradaInvalida(f"Fornecedor '{fornecedor}' sem adaptador registrado.")
    brutas = adaptador(corpo)
    if len(brutas) > MAX_LEITURAS:
        raise EntradaInvalida(f"Máximo de {MAX_LEITURAS} leituras por envio.")
    try:
        return [LeituraEntrada.model_validate(b) for b in brutas]
    except ValidationError as exc:
        raise EntradaInvalida(f"Leitura inválida: {exc.errors()[0]['loc']} {exc.errors()[0]['msg']}") from exc
