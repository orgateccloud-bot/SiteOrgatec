# A linha "Clima" das fontes leva o crédito do provedor: a licença CC BY 4.0 do MET Norway exige atribuição visível.
from datetime import UTC, datetime
from decimal import Decimal

from backend.transporte.dominio import ParametrosCusto, Ponto
from backend.transporte.provedores.base import PrevisaoClima
from backend.transporte.provedores.registro import Provedores
from backend.transporte.provedores.simulados import BloqueioSimulado, CombustivelSimulado, PedagioSimulado, RotaSimulada
from backend.transporte.servicos import viagem

CREDITO = "MET Norway (api.met.no), licença CC BY 4.0"


class ClimaFalso:
    nome = "met_norway"

    def __init__(self, horizonte: bool = True) -> None:
        self.horizonte = horizonte

    def previsao(self, lat, lon, quando):
        return PrevisaoClima(quando, 25.0, 0.0, 3.0, "clearsky_day", CREDITO) if self.horizonte else None


def _montar(clima):
    return viagem.montar(
        [Ponto(nome="Goiânia", uf="GO"), Ponto(nome="Palmas", uf="TO")], eixos=6, consumo_km_l=Decimal("2.4"),
        partida=datetime(2026, 11, 11, 13, tzinfo=UTC), parametros=ParametrosCusto(), parametros_vigencia="2026-11-11",
        provedores=Provedores(rota=RotaSimulada(), combustivel=CombustivelSimulado(), pedagio=PedagioSimulado(), clima=clima),
        bloqueios=BloqueioSimulado())


def test_fonte_do_clima_traz_o_credito_da_licenca():
    f = _montar(ClimaFalso())["fontes"]["clima"]
    assert f["estado"] == "ok" and f["fonte"] == CREDITO


def test_sem_previsao_no_horizonte_fica_o_nome_do_provedor():
    assert _montar(ClimaFalso(horizonte=False))["fontes"]["clima"]["fonte"] == "met_norway"
