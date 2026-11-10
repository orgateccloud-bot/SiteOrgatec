# Velocidade média do caminhão (parâmetro da transportadora): a rota de caminhão do Google (Large Vehicle Routing) só atende
# EUA e Japão (conferido em 10/11/2026), então o tempo de carro da Routes API é corrigido por um parâmetro informado.
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from backend.transporte.dominio import PARAMETROS_META, ParametrosCusto, Ponto
from backend.transporte.provedores.registro import Provedores
from backend.transporte.provedores.simulados import (
    BloqueioSimulado,
    ClimaSimulado,
    CombustivelSimulado,
    PedagioSimulado,
    RotaSimulada,
)
from backend.transporte.servicos import viagem

BRT = timezone(timedelta(hours=-3))


def _montar(parametros):
    return viagem.montar(
        [Ponto(nome="Goiânia", uf="GO"), Ponto(nome="Palmas", uf="TO")],
        eixos=6,
        consumo_km_l=Decimal("2.4"),
        partida=datetime(2026, 11, 10, 6, tzinfo=BRT),
        parametros=parametros,
        parametros_vigencia="2026-11-10",
        provedores=Provedores(rota=RotaSimulada(), combustivel=CombustivelSimulado(), pedagio=PedagioSimulado(),
                              clima=ClimaSimulado()),
        bloqueios=BloqueioSimulado(),
    )


def test_sem_parametro_nada_muda_e_a_tela_avisa_que_e_tempo_de_carro():
    p = ParametrosCusto()
    assert p.velocidade_media_caminhao_kmh is None  # sem valor padrão inventado
    r = _montar(p)
    assert r["rota"]["duracao_direcao_h"] == pytest.approx(r["rota"]["duracao_direcao_provedor_h"], abs=0.01)
    assert r["fontes"]["tempo"]["estado"] == r["fontes"]["rota"]["estado"]
    assert "tempo de carro" in r["fontes"]["tempo"]["detalhe"]


def test_velocidade_informada_alonga_a_direcao_e_a_chegada():
    base = _montar(ParametrosCusto())
    r = _montar(ParametrosCusto(velocidade_media_caminhao_kmh=Decimal("55")))
    dist = r["rota"]["distancia_km"]
    assert r["rota"]["duracao_direcao_h"] == pytest.approx(dist / 55, abs=0.02)
    assert r["jornada"]["direcao_h"] == pytest.approx(dist / 55, abs=0.02)
    assert r["jornada"]["chegada_prevista"] > base["jornada"]["chegada_prevista"]
    assert r["fontes"]["tempo"]["estado"] == "parametro"
    assert "55 km/h" in r["fontes"]["tempo"]["fonte"]


def test_caminhao_nunca_fica_mais_rapido_que_a_rota():
    # Velocidade acima da média da rota: vale o tempo do provedor em cada trecho.
    trechos = viagem.tempos_de_direcao([0.0, 100.0, 300.0], 5.0, 300.0, Decimal("90"))
    assert trechos == [(100.0, pytest.approx(5.0 / 3)), (200.0, pytest.approx(10.0 / 3))]
    lentos = viagem.tempos_de_direcao([0.0, 100.0, 300.0], 5.0, 300.0, Decimal("50"))
    assert [h for _, h in lentos] == [pytest.approx(2.0), pytest.approx(4.0)]


@pytest.mark.parametrize("valor", ["0", "19", "91"])
def test_valores_fora_da_faixa_sao_recusados(valor):
    with pytest.raises(ValidationError):
        ParametrosCusto(velocidade_media_caminhao_kmh=Decimal(valor))


def test_parametro_tem_rotulo_e_fonte_na_tela():
    meta = PARAMETROS_META["velocidade_media_caminhao_kmh"]
    assert meta["rotulo"] and "Parâmetro da transportadora" in meta["fonte"]
