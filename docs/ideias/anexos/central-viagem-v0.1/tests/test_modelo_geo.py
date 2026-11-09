from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from transporte.db.sessao import FabricaSessao, criar_engine
from transporte.db.tabelas import Base, Transportadora, Veiculo
from transporte.dominio import ParametrosCusto, VeiculoEntrada
from transporte.geo import acumulado_km, distancia_ponto_rota_km, haversine_km, ponto_no_km


def test_tabelas_e_placa_unica_por_transportadora():
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = FabricaSessao(engine).nova()
    t1, t2 = Transportadora(nome="A"), Transportadora(nome="B")
    s.add_all([t1, t2])
    s.flush()
    kw = dict(
        placa="ABC1D23",
        eixos=6,
        consumo_km_l_carregado=Decimal("2.2"),
        consumo_km_l_vazio=Decimal("2.8"),
        tanque_l=Decimal("600"),
    )
    s.add_all([Veiculo(transportadora_id=t1.id, **kw), Veiculo(transportadora_id=t2.id, **kw)])
    s.flush()
    s.add(Veiculo(transportadora_id=t1.id, **kw))
    with pytest.raises(IntegrityError):
        s.flush()


def test_placa_mercosul_e_antiga_normalizadas():
    v = VeiculoEntrada(placa="abc-1d23", eixos=3, consumo_km_l_carregado=3, consumo_km_l_vazio=4, tanque_l=300)
    assert v.placa == "ABC1D23"
    assert VeiculoEntrada(placa="ABC1234", eixos=3, consumo_km_l_carregado=3, consumo_km_l_vazio=4, tanque_l=300)


def test_parametros_rejeitam_campo_desconhecido_e_negativo():
    with pytest.raises(ValueError):
        ParametrosCusto(desconhecido=1)
    with pytest.raises(ValueError):
        ParametrosCusto(diaria_hospedagem=-1)


def test_haversine_goiania_brasilia_ordem_de_grandeza():
    d = haversine_km((-16.6869, -49.2648), (-15.7939, -47.8828))
    assert 170 < d < 180


def test_ponto_no_km_e_distancia_a_rota():
    geo = [(0.0, -48.0), (0.0, -47.0)]
    total = acumulado_km(geo)[-1]
    meio = ponto_no_km(geo, total / 2)
    assert meio[1] == pytest.approx(-47.5, abs=1e-6)
    dist, km = distancia_ponto_rota_km((0.01, -47.5), geo)
    assert dist == pytest.approx(1.1, abs=0.1)
    assert km == pytest.approx(total / 2, rel=0.01)
