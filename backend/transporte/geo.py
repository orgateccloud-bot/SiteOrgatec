"""Cálculos geográficos simples sobre a geometria da rota (lista de (lat, lon))."""

from __future__ import annotations

import math
from collections.abc import Sequence

Coord = tuple[float, float]
RAIO_TERRA_KM = 6371.0


def haversine_km(a: Coord, b: Coord) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(h))


def acumulado_km(geometria: Sequence[Coord]) -> list[float]:
    acc = [0.0]
    for i in range(1, len(geometria)):
        acc.append(acc[-1] + haversine_km(geometria[i - 1], geometria[i]))
    return acc


def ponto_no_km(geometria: Sequence[Coord], km: float, acumulado: list[float] | None = None) -> Coord:
    acc = acumulado or acumulado_km(geometria)
    if km <= 0:
        return geometria[0]
    if km >= acc[-1]:
        return geometria[-1]
    for i in range(1, len(acc)):
        if acc[i] >= km:
            seg = acc[i] - acc[i - 1] or 1e-9
            f = (km - acc[i - 1]) / seg
            a, b = geometria[i - 1], geometria[i]
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
    return geometria[-1]


def _projetar(p: Coord, ref_lat: float) -> tuple[float, float]:
    k = math.cos(math.radians(ref_lat))
    return (p[1] * 111.32 * k, p[0] * 110.574)


def distancia_ponto_rota_km(
    ponto: Coord, geometria: Sequence[Coord], acumulado: list[float] | None = None
) -> tuple[float, float]:
    """Devolve (distância mínima do ponto à rota em km, km da rota onde ocorre). Aproximação plana por segmento."""
    acc = acumulado or acumulado_km(geometria)
    melhor = (float("inf"), 0.0)
    px, py = _projetar(ponto, ponto[0])
    for i in range(1, len(geometria)):
        ax, ay = _projetar(geometria[i - 1], ponto[0])
        bx, by = _projetar(geometria[i], ponto[0])
        dx, dy = bx - ax, by - ay
        comp2 = dx * dx + dy * dy
        t = 0.0 if comp2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / comp2))
        cx, cy = ax + t * dx, ay + t * dy
        d = math.hypot(px - cx, py - cy)
        if d < melhor[0]:
            melhor = (d, acc[i - 1] + t * (acc[i] - acc[i - 1]))
    return melhor


def simplificar(geometria: Sequence[Coord], maximo: int = 400) -> list[Coord]:
    """Reduz pontos para armazenar/exibir, mantendo início e fim."""
    if len(geometria) <= maximo:
        return list(geometria)
    passo = (len(geometria) - 1) / (maximo - 1)
    return [geometria[round(i * passo)] for i in range(maximo)]
