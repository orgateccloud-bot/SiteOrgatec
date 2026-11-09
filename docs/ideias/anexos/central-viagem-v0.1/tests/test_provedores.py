from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest

from transporte.db.sessao import FabricaSessao, criar_engine
from transporte.db.tabelas import AlertaRota, Base, Transportadora
from transporte.erros import EntradaInvalida, ErroProvedor, ProvedorRespostaInvalida
from transporte.provedores.cache import Cache
from transporte.provedores.http import ClienteHttp
from transporte.provedores.reais import BloqueioManual, ClimaMetNo, CombustivelArquivoANP, PedagioArquivoANTT, RotaORS
from transporte.provedores.simulados import (
    BloqueioSimulado,
    ClimaSimulado,
    PedagioSimulado,
    RotaSimulada,
)

GOI, PMW = (-16.6869, -49.2648), (-10.1844, -48.3336)


def _http(handler):
    return ClienteHttp("t", transporte=httpx.MockTransport(handler), dormir=lambda s: None)


def test_rota_simulada_determinista_e_marcada():
    r = RotaSimulada()
    a, b = r.calcular([GOI, PMW], 6), r.calcular([GOI, PMW], 6)
    assert a == b and a.estado == "simulado"
    assert 800 < a.distancia_km < 1000
    assert a.duracao_h == pytest.approx(a.distancia_km / 60, rel=0.01)


def test_geocodificador_simulado_aceita_acento_e_uf_e_recusa_desconhecido():
    r = RotaSimulada()
    assert r.geocodificar("Goiânia-GO", "GO") == GOI
    with pytest.raises(EntradaInvalida):
        r.geocodificar("Cidade Inexistente", None)


def test_pedagio_e_bloqueio_simulados_ao_longo_da_rota():
    rota = RotaSimulada().calcular([GOI, PMW], 6)
    pracas = PedagioSimulado().pracas_na_rota(rota.geometria)
    assert len(pracas) >= 3 and pracas == sorted(pracas, key=lambda p: p.km_na_rota)
    agora = datetime.now(UTC)
    bloqueios = BloqueioSimulado().na_rota(rota.geometria, agora, agora + timedelta(days=1))
    assert len(bloqueios) == 1


def test_clima_simulado_determinista():
    q = datetime(2026, 11, 10, 12, tzinfo=UTC)
    assert ClimaSimulado().previsao(-16.7, -49.3, q) == ClimaSimulado().previsao(-16.7, -49.3, q)


def test_ors_converte_resposta_e_usa_cache():
    chamadas = []

    def h(req):
        chamadas.append(req.url.path)
        assert req.headers["Authorization"] == "chave"
        return httpx.Response(
            200,
            json={
                "features": [
                    {
                        "properties": {"summary": {"distance": 900000.0, "duration": 54000.0}},
                        "geometry": {"coordinates": [[-49.26, -16.68], [-48.33, -10.18]]},
                    }
                ]
            },
        )

    ors = RotaORS(_http(h), "https://ors.test", "chave", Cache(), 3600)
    r = ors.calcular([GOI, PMW], 6)
    ors.calcular([GOI, PMW], 6)
    assert (r.distancia_km, r.duracao_h, r.geometria[0]) == (900.0, 15.0, (-16.68, -49.26))
    assert chamadas == ["/v2/directions/driving-hgv/geojson"]


def test_ors_resposta_fora_do_formato():
    ors = RotaORS(_http(lambda req: httpx.Response(200, json={"x": 1})), "https://ors.test", "k", Cache(), 0)
    with pytest.raises(ProvedorRespostaInvalida):
        ors.calcular([GOI, PMW], 6)


def test_metno_escolhe_horario_mais_proximo_e_respeita_horizonte():
    corpo = {
        "properties": {
            "timeseries": [
                {
                    "time": "2026-11-10T12:00:00Z",
                    "data": {
                        "instant": {"details": {"air_temperature": 28.1, "wind_speed": 3.2}},
                        "next_1_hours": {"summary": {"symbol_code": "rain"}, "details": {"precipitation_amount": 4.5}},
                    },
                },
                {"time": "2026-11-10T13:00:00Z", "data": {"instant": {"details": {"air_temperature": 29.0}}}},
            ]
        }
    }
    met = ClimaMetNo(_http(lambda req: httpx.Response(200, json=corpo)), "https://met.test", Cache(), 60)
    p = met.previsao(-16.7, -49.3, datetime(2026, 11, 10, 12, 10, tzinfo=UTC))
    assert (p.temperatura_c, p.chuva_mm, p.condicao) == (28.1, 4.5, "rain")
    assert met.previsao(-16.7, -49.3, datetime(2026, 11, 20, tzinfo=UTC)) is None


def test_anp_municipio_depois_media_da_uf(tmp_path):
    arq = tmp_path / "anp.csv"
    arq.write_text(
        "uf;municipio;produto;preco_medio;data_referencia\n"
        "GO;GOIANIA;DIESEL S10;6,10;2026-11-01\nGO;ANAPOLIS;DIESEL S10;6,30;2026-11-01\n"
        "GO;GOIANIA;GASOLINA;6,90;2026-11-01\n",
        encoding="utf-8",
    )
    anp = CombustivelArquivoANP(str(arq))
    assert anp.preco_diesel("GO", "Goiania").valor == Decimal("6.100")
    assert anp.preco_diesel("GO", "Uruacu").valor == Decimal("6.200")
    assert anp.preco_diesel("TO", None) is None


def test_arquivo_ausente_vira_erro_de_provedor(tmp_path):
    with pytest.raises(ErroProvedor):
        CombustivelArquivoANP(str(tmp_path / "nao.csv")).preco_diesel("GO", None)


def test_antt_pracas_perto_da_rota_sem_duplicar_sentido(tmp_path):
    rota = RotaSimulada().calcular([GOI, PMW], 6)
    lat, lon = rota.geometria[50]
    arq = tmp_path / "antt.csv"
    arq.write_text(
        "concessionaria;praca;lat;lon;situacao;tarifa_cat1\n"
        f"X;P1;{lat};{lon};Ativa;10,50\nX;P1;{lat};{lon};Ativa;10,50\n"
        "X;Longe;-20;-40;Ativa;5\nX;Inativa;"
        f"{lat};{lon};Inativa;1\n",
        encoding="utf-8",
    )
    pracas = PedagioArquivoANTT(str(arq)).pracas_na_rota(rota.geometria)
    assert [p.nome for p in pracas] == ["P1 (X)"] and pracas[0].tarifa_cat1 == Decimal("10.50")


def test_bloqueio_manual_filtra_tenant_janela_e_raio():
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = FabricaSessao(engine).nova()
    t, outra = Transportadora(nome="A"), Transportadora(nome="B")
    s.add_all([t, outra])
    s.flush()
    rota = RotaSimulada().calcular([GOI, PMW], 6)
    lat, lon = rota.geometria[30]
    agora = datetime.now(UTC)
    base = dict(tipo="bloqueio", descricao="Ponte", lat=lat, lon=lon, raio_km=2, fonte="PRF (manual)")
    s.add_all(
        [
            AlertaRota(transportadora_id=t.id, inicio=agora - timedelta(hours=1), **base),
            AlertaRota(transportadora_id=outra.id, inicio=agora, **base),
            AlertaRota(transportadora_id=t.id, inicio=agora - timedelta(days=3), fim=agora - timedelta(days=2), **base),
        ]
    )
    s.flush()
    achados = BloqueioManual(s, t.id).na_rota(rota.geometria, agora, agora + timedelta(days=1))
    assert len(achados) == 1
