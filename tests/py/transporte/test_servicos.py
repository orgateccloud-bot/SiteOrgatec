from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from backend.transporte.dominio import ParametrosCusto, Ponto
from backend.transporte.erros import EntradaInvalida, ProvedorLimiteExcedido, ProvedorTimeout
from backend.transporte.provedores.registro import Provedores
from backend.transporte.provedores.simulados import (
    BloqueioSimulado,
    ClimaSimulado,
    CombustivelSimulado,
    PedagioSimulado,
    RotaSimulada,
)
from backend.transporte.servicos import despesas, jornada, viagem

BRT = timezone(timedelta(hours=-3))
P = ParametrosCusto()


def test_jornada_caso_de_referencia_1200km_20h():
    # Conferido à mão: 5,5 dir + 1 refeição + 4,5 dir + 11 descanso + 5,5 dir + 1 refeição + 4,5 dir = 33 h.
    plano = jornada.planejar([(1200.0, 20.0)], datetime(2026, 11, 10, 6, tzinfo=BRT), P)
    r = plano.resumo()
    assert r["pernoites"] == 1 and r["pausas"] == 2 and r["direcao_h"] == 20.0
    assert plano.chegada == datetime(2026, 11, 11, 15, tzinfo=BRT)
    assert [e.tipo for e in plano.eventos] == [
        "direcao",
        "refeicao",
        "direcao",
        "pernoite",
        "direcao",
        "refeicao",
        "direcao",
        "chegada",
    ]
    assert plano.tempo_no_km(330.0) == datetime(2026, 11, 10, 11, 30, tzinfo=BRT)


def test_jornada_curta_sem_pausa_e_parada_intermediaria_zera_direcao_continua():
    plano = jornada.planejar([(200.0, 3.0), (200.0, 3.0)], datetime(2026, 11, 10, 6, tzinfo=BRT), P)
    assert [e.tipo for e in plano.eventos] == ["direcao", "parada", "direcao", "chegada"]


def test_jornada_parametros_editaveis_mudam_resultado():
    p = ParametrosCusto(jornada_direcao_max_h=Decimal("8"))
    assert jornada.planejar([(900.0, 15.0)], datetime(2026, 11, 10, tzinfo=BRT), p).contar("pernoite") == 1
    p2 = ParametrosCusto(jornada_direcao_max_h=Decimal("16"), direcao_continua_max_h=Decimal("8"))
    assert jornada.planejar([(900.0, 15.0)], datetime(2026, 11, 10, tzinfo=BRT), p2).contar("pernoite") == 0


def _insumos(**kw):
    base = dict(
        distancia_km=Decimal("1000"),
        pernoites=1,
        eixos=6,
        consumo_km_l=Decimal("2.5"),
        preco_diesel=Decimal("6.00"),
        preco_diesel_fonte="ANP",
        preco_diesel_estado="ok",
        tarifas_pracas=[Decimal("10"), None, Decimal("8")],
        pedagio_estado="ok",
    )
    base.update(kw)
    return despesas.Insumos(**base)


def test_despesas_caso_de_referencia():
    # Conferido à mão: 2400 + 80 + 156 + 120 + 180 + 120 + 250 + 50 = 3356; reserva 5% = 167,80; total 3523,80.
    r = despesas.calcular(_insumos(), P)
    valores = {i["tipo"]: i["valor"] for i in r["itens"]}
    assert valores == {
        "combustivel": "2400.00",
        "arla": "80.00",
        "pedagio": "156.00",
        "hospedagem": "120.00",
        "alimentacao": "180.00",
        "pneus": "120.00",
        "manutencao": "250.00",
        "borracharia": "50.00",
        "outros": "0.00",
        "reserva_imprevistos": "167.80",
    }
    assert (r["total"], r["custo_por_km"], r["litros_diesel"]) == ("3523.80", "3.52", "400.0")


def test_despesas_ajuste_manual_recalcula_reserva_e_total():
    r = despesas.calcular(_insumos(), P, {"combustivel": "2000"})
    comb = next(i for i in r["itens"] if i["tipo"] == "combustivel")
    assert comb["ajustado"] and comb["valor_calculado"] == "2400.00"
    assert r["total"] == "3103.80"


def test_despesas_pernoite_na_cabine_zera_hospedagem():
    r = despesas.calcular(_insumos(), ParametrosCusto(pernoite_no_veiculo=True))
    assert next(i for i in r["itens"] if i["tipo"] == "hospedagem")["valor"] == "0.00"


def test_insumos_ida_e_volta_em_dict():
    ins = _insumos()
    assert despesas.Insumos.de_dict(ins.como_dict()) == ins


def _prov(**trocar):
    base = dict(
        rota=RotaSimulada(), combustivel=CombustivelSimulado(), pedagio=PedagioSimulado(), clima=ClimaSimulado()
    )
    base.update(trocar)
    return Provedores(**base)


def _montar(prov=None, bloq=None, pontos=None):
    return viagem.montar(
        pontos or [Ponto(nome="Goiânia", uf="GO"), Ponto(nome="Palmas", uf="TO")],
        eixos=6,
        consumo_km_l=Decimal("2.4"),
        partida=datetime(2026, 11, 10, 6, tzinfo=BRT),
        parametros=P,
        parametros_vigencia="2026-11-09",
        provedores=prov or _prov(),
        bloqueios=bloq or BloqueioSimulado(),
    )


def test_viagem_completa_com_simulados():
    r = _montar()
    assert r["rota"]["distancia_km"] > 800
    assert r["jornada"]["pernoites"] >= 1
    assert Decimal(r["despesas"]["total"]) > 0
    assert len(r["bloqueios"]) == 1 and r["bloqueios"][0]["passagem_prevista"]
    assert len(r["clima"]) >= 5
    assert {f["estado"] for f in r["fontes"].values()} == {"simulado"}


def test_viagem_com_parada_intermediaria_coordenada():
    pts = [Ponto(nome="Goiânia"), Ponto(nome="Uruaçu", lat=-14.5237, lon=-49.1396), Ponto(nome="Palmas")]
    r = _montar(pontos=pts)
    assert r["jornada"]["paradas"] == 1
    assert 0 < r["pontos"][1]["km"] < r["rota"]["distancia_km"]


class _Falha:
    def __init__(self, nome, exc):
        self.nome, self.exc = nome, exc

    def __getattr__(self, item):
        def f(*a, **k):
            raise self.exc

        return f


def test_falha_de_combustivel_usa_parametro_e_marca_estado():
    r = _montar(_prov(combustivel=_Falha("anp", ProvedorTimeout("anp", "x"))))
    comb = next(i for i in r["despesas"]["itens"] if i["tipo"] == "combustivel")
    assert comb["valor_unitario"] == "6.50" and r["fontes"]["combustivel"]["estado"] == "timeout"


def test_falha_de_clima_e_pedagio_nao_derruba_a_viagem():
    r = _montar(
        _prov(
            clima=_Falha("met", ProvedorLimiteExcedido("met", "429")),
            pedagio=_Falha("antt", ProvedorTimeout("antt", "x")),
        )
    )
    assert r["fontes"]["clima"]["estado"] == "limite_excedido" and r["clima"] == []
    assert r["fontes"]["pedagio"]["estado"] == "timeout"
    assert next(i for i in r["despesas"]["itens"] if i["tipo"] == "pedagio")["valor"] == "0.00"


def test_falha_de_rota_interrompe_com_erro_tipado():
    with pytest.raises(ProvedorTimeout):
        _montar(_prov(rota=_Falha("ors", ProvedorTimeout("ors", "x"))))


def test_coordenada_incompleta_e_recusada():
    with pytest.raises(EntradaInvalida):
        _montar(pontos=[Ponto(nome="Fazenda", lat=-16.0), Ponto(nome="Palmas")])


def test_recalcular_despesas_usa_insumos_e_parametros_guardados():
    r = _montar()
    novo = viagem.recalcular_despesas(r, {"pedagio": "0"})
    assert Decimal(novo["total"]) < Decimal(r["despesas"]["total"])
