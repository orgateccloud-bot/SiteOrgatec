"""Provedores reais com a rede simulada (httpx.MockTransport) e CSVs no formato oficial da ANP e da ANTT (conferido em 09/11/2026)."""

from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from backend.transporte.erros import (
    EntradaInvalida,
    ErroProvedor,
    ProvedorLimiteExcedido,
    ProvedorRespostaInvalida,
    ProvedorTimeout,
    RecursoDesligado,
)
from backend.transporte.provedores.cache import Cache
from backend.transporte.provedores.http import ClienteHttp
from backend.transporte.provedores.reais import ClimaMetNo, CombustivelANP, PedagioANTT, RotaORS
from backend.transporte.provedores.registro import provedores_do_ambiente

GOI, PMW = (-16.6869, -49.2648), (-10.1844, -48.3336)


def _http(handler, tentativas=3):
    return ClienteHttp("t", transporte=httpx.MockTransport(handler), dormir=lambda s: None, tentativas=tentativas)


def test_ors_converte_resposta_usa_cache_e_manda_a_chave_no_cabecalho():
    chamadas = []

    def h(req):
        chamadas.append(req)
        return httpx.Response(200, json={"features": [{"properties": {"summary": {"distance": 934000, "duration": 41000}},
                                                       "geometry": {"coordinates": [[-49.26, -16.68], [-48.33, -10.18]]}}]})

    r = RotaORS(_http(h), "https://ors.exemplo", "CHAVE-TESTE", Cache(), 60)
    a, b = r.calcular([GOI, PMW], 6), r.calcular([GOI, PMW], 6)
    assert a.distancia_km == 934.0 and a.duracao_h == 11.39 and "driving-hgv" in a.fonte and a == b
    assert len(chamadas) == 1 and chamadas[0].headers["Authorization"] == "CHAVE-TESTE" and "CHAVE-TESTE" not in str(chamadas[0].url)


def test_ors_geocodifica_e_recusa_local_inexistente():
    def h(req):
        achou = "Goiânia" in req.url.params["text"]
        return httpx.Response(200, json={"features": [{"geometry": {"coordinates": [-49.26, -16.68]}}] if achou else []})

    r = RotaORS(_http(h), "https://ors.exemplo", "k", Cache(), 60)
    assert r.geocodificar("Goiânia", "GO") == (-16.68, -49.26)
    with pytest.raises(EntradaInvalida):
        r.geocodificar("Lugar Nenhum", None)


def test_falhas_de_rede_viram_erros_tipados():
    with pytest.raises(ProvedorLimiteExcedido):
        RotaORS(_http(lambda q: httpx.Response(429), 2), "https://x", "k", Cache(), 1).calcular([GOI, PMW], 6)

    def estoura(q):
        raise httpx.ReadTimeout("lento")

    with pytest.raises(ProvedorTimeout):
        RotaORS(_http(estoura, 2), "https://x", "k", Cache(), 1).calcular([GOI, PMW], 6)
    with pytest.raises(ProvedorRespostaInvalida):
        RotaORS(_http(lambda q: httpx.Response(200, json={"x": 1})), "https://x", "k", Cache(), 1).calcular([GOI, PMW], 6)
    with pytest.raises(ProvedorRespostaInvalida):
        RotaORS(_http(lambda q: httpx.Response(403)), "https://x", "k", Cache(), 1).calcular([GOI, PMW], 6)


def test_metno_escolhe_o_horario_mais_proximo_e_recusa_fora_do_horizonte():
    serie = {"properties": {"timeseries": [{"time": "2026-11-10T12:00:00Z", "data": {
        "instant": {"details": {"air_temperature": 31.5, "wind_speed": 3.2}},
        "next_1_hours": {"summary": {"symbol_code": "rain"}, "details": {"precipitation_amount": 2.4}}}}]}}
    c = ClimaMetNo(_http(lambda q: httpx.Response(200, json=serie)), "https://met.exemplo", Cache(), 60)
    p = c.previsao(-16.7, -49.3, datetime(2026, 11, 10, 13, tzinfo=UTC))
    assert p.temperatura_c == 31.5 and p.chuva_mm == 2.4 and p.condicao == "rain" and "CC BY" in p.fonte
    assert c.previsao(-16.7, -49.3, datetime(2026, 11, 20, tzinfo=UTC)) is None


CAB_ANP = ("Regiao - Sigla;Estado - Sigla;Municipio;Revenda;CNPJ da Revenda;Nome da Rua;Numero Rua;Complemento;Bairro;Cep;Produto;"
           "Data da Coleta;Valor de Venda;Valor de Compra;Unidade de Medida;Bandeira\n")


def _linha(mun, prod, data, valor, posto="POSTO"):
    return f"CO;GO;{mun};{posto}; 11.111.111/0001-11;RUA A;1;;B;74000-000;{prod};{data};{valor};;R$ / litro;BRANCA\n"


ANP = (CAB_ANP + _linha("GOIANIA", "DIESEL S10", "01/12/2025", "6,00") + _linha("GOIANIA", "DIESEL S10", "02/12/2025", "6,20")
       + _linha("ANAPOLIS", "DIESEL S10", "02/12/2025", "5,80") + _linha("GOIANIA", "DIESEL", "02/12/2025", "9,99")
       + _linha("GOIANIA", "DIESEL S10", "20/11/2025", "9,00") + _linha("GOIANIA", "GASOLINA", "02/12/2025", "1,00"))


def test_anp_media_da_ultima_semana_por_municipio_e_por_uf(tmp_path):
    arq = tmp_path / "anp.csv"
    arq.write_bytes(b"\xef\xbb\xbf" + ANP.replace("\n", "\r\n").encode())
    c = CombustivelANP(str(arq))
    g = c.preco_diesel("GO", "Goiânia")  # com acento e minúsculas, como o usuário digita
    assert g.valor == Decimal("6.100") and g.referencia.startswith("Goiânia/GO") and "ANP" in g.fonte  # S10 da última semana; ignora S500, outro mês e gasolina
    u = c.preco_diesel("GO", "Cidade Sem Dado")
    assert u.valor == Decimal("6.000") and "média de GO" in u.referencia  # (6,00 + 6,20 + 5,80) / 3
    assert c.preco_diesel("SP", None) is None and c.preco_diesel(None, None) is None
    assert "CNPJ" not in repr(g) and "POSTO" not in repr(g)


def test_arquivo_ausente_e_erro_de_provedor(tmp_path):
    with pytest.raises(ErroProvedor):
        CombustivelANP(str(tmp_path / "nao-existe.csv")).preco_diesel("GO", None)


ANTT = ("concessionaria;praca_de_pedagio;ano_do_pnv_snv;rodovia;uf;km_m;municipal;tipo_de_pista;sentido;situacao;data_da_inativacao;latitude;longitude\n"
        "ECO 050;Perdizes;2014;BR-050;MG;100.0;Perdizes;Principal;Crescente;Ativo;;-16.0000;-48.9000\n"
        "ECO 050;Perdizes;2014;BR-050;MG;100.0;Perdizes;Principal;Decrescente;Ativo;;-16.0000;-48.9000\n"
        "OUTRA;Inativa;2010;BR-060;GO;5.0;X;Principal;Crescente;Inativo;01/01/2020;-15.0000;-48.5000\n"
        "OUTRA;Longe;2010;BR-116;SP;5.0;X;Principal;Crescente;Ativo;;-23.5000;-46.6000\n")


def test_antt_acha_pracas_na_rota_sem_duplicar_por_sentido(tmp_path):
    arq = tmp_path / "antt.csv"
    arq.write_text(ANTT, encoding="utf-8")
    rota = [(-16.6869, -49.2648), (-16.0, -48.9), (-10.1844, -48.3336)]
    pracas = PedagioANTT(str(arq)).pracas_na_rota(rota)
    arq.write_bytes(ANTT.replace("Perdizes;2014", "Perdizes;2014").replace("Principal", "Prínc").encode("cp1252"))
    assert [p.nome.split(" (")[0] for p in PedagioANTT(str(arq)).pracas_na_rota(rota)] == ["Perdizes"]  # Windows-1252 também lê
    assert [p.nome.split(" (")[0] for p in pracas] == ["Perdizes"] and pracas[0].tarifa_cat1 is None and "ANTT" in pracas[0].fonte


def test_registro_exige_configuracao_e_monta_reais(tmp_path):
    with pytest.raises(RecursoDesligado):
        provedores_do_ambiente({"ORGATEC_TRANSPORTE_ROTA_REAL": "1"})
    with pytest.raises(RecursoDesligado):
        provedores_do_ambiente({"ORGATEC_TRANSPORTE_CLIMA_REAL": "1"})
    assert provedores_do_ambiente({}).reais() == []
    a = tmp_path / "a.csv"
    a.write_text(ANP, encoding="utf-8")
    p = provedores_do_ambiente({"ORGATEC_TRANSPORTE_ROTA_REAL": "1", "ORGATEC_TRANSPORTE_ORS_CHAVE": "k", "ORGATEC_TRANSPORTE_CLIMA_REAL": "1",
                                "ORGATEC_TRANSPORTE_METNO_CONTATO": "contato@orgatec.io", "ORGATEC_TRANSPORTE_COMBUSTIVEL_REAL": "1",
                                "ORGATEC_TRANSPORTE_ANP_ARQUIVO": str(a)}, cache=Cache())
    assert p.reais() == ["rota", "combustivel", "clima"]


# --- Google Routes API (alternativa licenciada ao OpenRouteService) ---
def test_polilinha_do_google_decodifica():
    from backend.transporte.provedores.reais import _decodificar_polilinha

    pts = _decodificar_polilinha("_p~iF~ps|U_ulLnnqC_mqNvxq`@")  # exemplo da documentação do Google
    assert [(round(a, 5), round(b, 5)) for a, b in pts] == [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
    with pytest.raises(ValueError):
        _decodificar_polilinha("_p~iF~ps|U_ulLnnqC_mqNvxq`")  # truncada


def test_google_calcula_rota_com_chave_no_cabecalho_e_cache():
    from backend.transporte.provedores.reais import RotaGoogle

    chamadas = []

    def h(req):
        chamadas.append(req)
        return httpx.Response(200, json={"routes": [{"distanceMeters": 934000, "duration": "41000s",
                                                     "polyline": {"encodedPolyline": "_p~iF~ps|U_ulLnnqC_mqNvxq`@"}}]})

    r = RotaGoogle(_http(h), "CHAVE-G", Cache(), 60)
    a, b = r.calcular([GOI, PMW], 6), r.calcular([GOI, PMW], 6)
    assert a.distancia_km == 934.0 and a.duracao_h == 11.39 and "Google" in a.fonte and a == b
    assert len(chamadas) == 1 and chamadas[0].headers["X-Goog-Api-Key"] == "CHAVE-G" and "CHAVE-G" not in str(chamadas[0].url)
    assert "routes.polyline" in chamadas[0].headers["X-Goog-FieldMask"]


def test_google_geocodifica_recusa_e_formato_invalido():
    from backend.transporte.provedores.reais import RotaGoogle

    def h(req):
        if "Goiânia" in req.url.params["address"]:
            return httpx.Response(200, json={"status": "OK", "results": [{"geometry": {"location": {"lat": -16.68, "lng": -49.26}}}]})
        return httpx.Response(200, json={"status": "ZERO_RESULTS", "results": []})

    r = RotaGoogle(_http(h), "k", Cache(), 60)
    assert r.geocodificar("Goiânia", "GO") == (-16.68, -49.26)
    with pytest.raises(EntradaInvalida):
        r.geocodificar("Lugar Nenhum", None)
    with pytest.raises(ProvedorRespostaInvalida):
        RotaGoogle(_http(lambda q: httpx.Response(200, json={"routes": []})), "k", Cache(), 1).calcular([GOI, PMW], 6)


def test_registro_escolhe_google_so_com_flag_e_chave():
    with pytest.raises(RecursoDesligado):
        provedores_do_ambiente({"ORGATEC_TRANSPORTE_ROTA_REAL": "1", "ORGATEC_TRANSPORTE_ROTA_FONTE": "google"})
    p = provedores_do_ambiente({"ORGATEC_TRANSPORTE_ROTA_REAL": "1", "ORGATEC_TRANSPORTE_ROTA_FONTE": "google",
                                "ORGATEC_TRANSPORTE_GOOGLE_CHAVE": "k"}, cache=Cache())
    assert type(p.rota).__name__ == "RotaGoogle" and p.reais() == ["rota"]


# --- tarifas oficiais de pedágio (Ecovias do Araguaia) ---
def test_tabela_de_tarifas_confere_com_a_pagina_oficial():
    from decimal import Decimal

    from backend.transporte.provedores.tarifas_pedagio import tarifa_cat1

    valor, fonte = tarifa_cat1("ECOVIAS DO ARAGUAIA", "P5 - Campinorte")
    assert valor == Decimal("14.30") and "ecoviasaraguaia.com.br" in fonte.url
    assert Decimal("6") * valor == Decimal("85.80")  # categoria 8 (6 eixos) na tabela oficial
    assert tarifa_cat1("Ecovias do Araguaia", "p1 - Aliança do Tocantins")[0] == Decimal("9.50")  # maiúsculas e acento não importam
    assert tarifa_cat1("ECO 050", "P1 - Perdizes") is None and tarifa_cat1("ECOVIAS DO ARAGUAIA", "Sem código") is None


ANTT_ECOVIAS = ("concessionaria;praca_de_pedagio;ano_do_pnv_snv;rodovia;uf;km_m;municipal;tipo_de_pista;sentido;situacao;data_da_inativacao;latitude;longitude\n"
                "ECOVIAS DO ARAGUAIA;P5 - Campinorte;2021;BR-153;GO;182.0;Campinorte;Principal;Crescente/Decrescente;Ativo;;-14.372969;-49.158264\n"
                "ECOVIAS DO ARAGUAIA;P3 - Porangatu;2021;BR-153;GO;12.5;Porangatu;Principal;Crescente/Decrescente;Ativo;;-12.943414;-49.133122\n"
                "OUTRA;Meio;2010;BR-153;GO;5.0;X;Principal;Crescente;Ativo;;-13.500000;-49.150000\n")


def test_antt_traz_a_tarifa_oficial_e_a_despesa_soma_por_eixo(tmp_path):
    from decimal import Decimal

    from backend.transporte.dominio import ParametrosCusto
    from backend.transporte.servicos import despesas

    arq = tmp_path / "antt.csv"
    arq.write_text(ANTT_ECOVIAS, encoding="utf-8")
    rota = [(-16.6869, -49.2648), (-14.372969, -49.158264), (-13.5, -49.15), (-12.943414, -49.133122), (-10.1844, -48.3336)]
    pracas = PedagioANTT(str(arq)).pracas_na_rota(rota)
    por_nome = {p.nome.split(" (")[0]: p for p in pracas}
    assert por_nome["P5 - Campinorte"].tarifa_cat1 == Decimal("14.30") and "tabela oficial Ecovias do Araguaia" in por_nome["P5 - Campinorte"].fonte
    assert por_nome["Meio"].tarifa_cat1 is None and "tabela oficial" not in por_nome["Meio"].fonte  # concessionária fora da tabela

    p = ParametrosCusto()
    ins = despesas.Insumos(distancia_km=Decimal("800"), pernoites=1, eixos=6, consumo_km_l=Decimal("2.3"), preco_diesel=Decimal("7"),
                           preco_diesel_fonte="t", preco_diesel_estado="ok", tarifas_pracas=[Decimal("14.30"), Decimal("12.00")], pedagio_estado="ok")
    ped = next(i for i in despesas.calcular(ins, p)["itens"] if i["tipo"] == "pedagio")
    assert Decimal(ped["valor"]) == Decimal("157.80") and "tabela oficial da concessionária" in ped["fonte"]
    misto = despesas.Insumos(**{**ins.__dict__, "tarifas_pracas": [Decimal("14.30"), None]})
    assert "1 de 2 praças" in next(i for i in despesas.calcular(misto, p)["itens"] if i["tipo"] == "pedagio")["fonte"]
