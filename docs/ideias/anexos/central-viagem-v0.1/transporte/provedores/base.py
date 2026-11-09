"""Contratos dos provedores de dados. Cada tipo tem uma implementação real e uma simulada (mesma interface)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from transporte.geo import Coord


@dataclass(frozen=True)
class RotaCalculada:
    distancia_km: float
    duracao_h: float
    geometria: list[Coord]
    fonte: str
    estado: str = "ok"


@dataclass(frozen=True)
class PrecoCombustivel:
    valor: Decimal
    referencia: str
    fonte: str
    estado: str = "ok"


@dataclass(frozen=True)
class PracaPedagio:
    nome: str
    lat: float
    lon: float
    km_na_rota: float
    tarifa_cat1: Decimal | None
    fonte: str


@dataclass(frozen=True)
class PrevisaoClima:
    previsto_para: datetime
    temperatura_c: float | None
    chuva_mm: float | None
    vento_ms: float | None
    condicao: str
    fonte: str


@dataclass(frozen=True)
class Bloqueio:
    tipo: str
    descricao: str
    lat: float
    lon: float
    km_na_rota: float
    fonte: str
    inicio: datetime | None = None
    fim: datetime | None = None
    extra: dict[str, str] = field(default_factory=dict)


class RotaProvider(Protocol):
    nome: str

    def geocodificar(self, texto: str, uf: str | None) -> Coord: ...

    def calcular(self, pontos: list[Coord], eixos: int) -> RotaCalculada: ...


class CombustivelProvider(Protocol):
    nome: str

    def preco_diesel(self, uf: str | None, municipio: str | None) -> PrecoCombustivel | None: ...


class PedagioProvider(Protocol):
    nome: str

    def pracas_na_rota(self, geometria: list[Coord]) -> list[PracaPedagio]: ...


class ClimaProvider(Protocol):
    nome: str

    def previsao(self, lat: float, lon: float, quando: datetime) -> PrevisaoClima | None: ...


class BloqueioProvider(Protocol):
    nome: str

    def na_rota(self, geometria: list[Coord], inicio: datetime, fim: datetime) -> list[Bloqueio]: ...
