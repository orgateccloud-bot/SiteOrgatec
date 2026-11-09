"""Escolhe os provedores. Nesta versão só os SIMULADOS existem: os reais (OpenRouteService, MET Norway, ANP e ANTT por CSV)
dependem de um cliente HTTP no servidor (httpx), dependência que ainda não foi aprovada. Pedir um provedor real levanta
RecursoDesligado em vez de cair em dado simulado sem aviso. Ver docs/ideias/reestruturacao-transporte-fase5.md."""

from __future__ import annotations

from dataclasses import dataclass

from backend.transporte.erros import RecursoDesligado
from backend.transporte.provedores.base import (
    BloqueioProvider,
    ClimaProvider,
    CombustivelProvider,
    PedagioProvider,
    RotaProvider,
)
from backend.transporte.provedores.simulados import (
    BloqueioSimulado,
    ClimaSimulado,
    CombustivelSimulado,
    PedagioSimulado,
    RotaSimulada,
)


@dataclass
class Provedores:
    rota: RotaProvider
    combustivel: CombustivelProvider
    pedagio: PedagioProvider
    clima: ClimaProvider


def provedores_simulados() -> Provedores:
    return Provedores(RotaSimulada(), CombustivelSimulado(), PedagioSimulado(), ClimaSimulado())


def bloqueio_simulado() -> BloqueioProvider:
    return BloqueioSimulado()


def provedores_do_ambiente(env: dict[str, str]) -> Provedores:
    """Flags TRANSPORTE_*_REAL: enquanto os provedores reais não forem aprovados e implementados, ligar uma flag é recusado."""
    for flag in ("ROTA", "CLIMA", "COMBUSTIVEL", "PEDAGIO"):
        if env.get(f"ORGATEC_TRANSPORTE_{flag}_REAL", "0") == "1":
            raise RecursoDesligado(f"provedor real de {flag.lower()} ainda não implementado")
    return provedores_simulados()
