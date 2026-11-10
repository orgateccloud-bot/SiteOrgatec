"""Mapa real da Central de Viagem: lançamentos manuais, postos ao longo da rota (Google Places), valor de cada pedágio, prazo de 30 dias
das coordenadas do Google (termos do Google Maps Platform) e a CSP que libera o mapa só em /transporte/."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.transporte import api
from backend.transporte.dominio import ParametrosCusto, Ponto
from backend.transporte.provedores.base import Posto, PrecoCombustivel
from backend.transporte.provedores.cache import Cache
from backend.transporte.provedores.http import ClienteHttp
from backend.transporte.provedores.reais import PostosGoogle, _decodificar_polilinha, codificar_polilinha
from backend.transporte.provedores.registro import Provedores, provedores_do_ambiente
from backend.transporte.provedores.simulados import BloqueioSimulado, ClimaSimulado, PedagioSimulado, RotaSimulada
from backend.transporte.repositorio_transporte import RepositorioMemoria, RepositorioSQLite
from backend.transporte.servicos import viagem

ENV = {"ORGATEC_TRANSPORTE": "1"}
VEICULO = {"placa": "ABC1D23", "eixos": 6, "consumo_km_l_carregado": 2.4, "consumo_km_l_vazio": 3.0, "tanque_l": 700}
PONTOS = [{"nome": "Goiânia", "uf": "GO"}, {"nome": "Palmas", "uf": "TO"}]


@pytest.fixture
def amb():
    repo = RepositorioMemoria()
    a, b = repo.criar_transportadora(), repo.criar_transportadora()
    app = FastAPI()
    assert api.instalar(app, ENV, repo=repo)
    cli = TestClient(app)

    def h(tid=a, papel="gestor", usuario="u-gestor"):
        return {"X-Transportadora-Id": tid, "X-Usuario-Papel": papel, "X-Usuario-Id": usuario}

    vid = cli.post("/api/transporte/veiculos", json=VEICULO, headers=h()).json()["id"]
    corpo = {"veiculo_id": vid, "pontos": PONTOS, "partida_prevista": (datetime.now(UTC) + timedelta(hours=1)).isoformat()}
    viagem_id = cli.post("/api/transporte/viagens", json=corpo, headers=h()).json()["id"]
    return {"cli": cli, "a": a, "b": b, "h": h, "repo": repo, "viagem": viagem_id}


def _lanc(**extra):
    return {"tipo": "abastecimento", "ts": (datetime.now(UTC) - timedelta(minutes=5)).isoformat(), "local": "Posto Km 120",
            "valor": "1500.00", "litros": "250", "preco_l": "6.00", **extra}


# ---------- lançamentos manuais ----------
def test_lancamento_grava_com_fonte_manual_e_aparece_na_lista(amb):
    url = f"/api/transporte/viagens/{amb['viagem']}/lancamentos"
    r = amb["cli"].post(url, json=_lanc(lat=-15.9, lon=-49.2), headers=amb["h"]())
    assert r.status_code == 201, r.text
    criado = r.json()
    assert criado["fonte"] == "informado manualmente" and criado["autor_id"] == "u-gestor" and criado["valor"] == "1500.00"
    lista = amb["cli"].get(url, headers=amb["h"](papel="leitura")).json()  # o portal (leitura) vê
    assert [x["id"] for x in lista] == [criado["id"]]


def test_lancamento_isolado_por_transportadora_e_papel(amb):
    url = f"/api/transporte/viagens/{amb['viagem']}/lancamentos"
    assert amb["cli"].post(url, json=_lanc(), headers=amb["h"](tid=amb["b"])).status_code == 404  # outra transportadora
    assert amb["cli"].get(url, headers=amb["h"](tid=amb["b"])).status_code == 404
    assert amb["cli"].post(url, json=_lanc(), headers=amb["h"](papel="leitura")).status_code == 403


@pytest.mark.parametrize("corpo", [
    {"tipo": "posicao_manual", "ts": datetime.now(UTC).isoformat()},  # posição sem coordenada
    _lanc(lat=-15.9),  # só latitude
    {**_lanc(), "tipo": "parada"},  # litros fora de abastecimento
    _lanc(ts=(datetime.now(UTC) + timedelta(days=1)).isoformat()),  # futuro
    _lanc(valor="-1"),
    _lanc(extra="campo desconhecido"),
])
def test_lancamento_invalido_e_recusado(amb, corpo):
    r = amb["cli"].post(f"/api/transporte/viagens/{amb['viagem']}/lancamentos", json=corpo, headers=amb["h"]())
    assert r.status_code == 422, r.text


def test_remocao_logica_e_motorista_so_remove_o_proprio(amb):
    url = f"/api/transporte/viagens/{amb['viagem']}/lancamentos"
    lid = amb["cli"].post(url, json=_lanc(), headers=amb["h"]()).json()["id"]
    # motorista sem vínculo com a viagem não a enxerga
    assert amb["cli"].delete(f"{url}/{lid}", headers=amb["h"](papel="motorista", usuario="u-mot")).status_code == 404
    assert amb["cli"].delete(f"{url}/{lid}", headers=amb["h"]()).status_code == 200
    assert amb["cli"].get(url, headers=amb["h"]()).json() == []
    reg = amb["repo"].obter(amb["a"], "lancamentos", lid)
    assert reg["removido"] and reg["removido_por"] == "u-gestor"  # fica registrado quem removeu
    assert amb["cli"].delete(f"{url}/{lid}", headers=amb["h"]()).status_code == 404


def test_contexto_entrega_a_chave_do_mapa_so_quando_configurada(amb):
    assert amb["cli"].get("/api/transporte/contexto", headers=amb["h"]()).json()["mapa"] is None
    repo = RepositorioMemoria()
    tid = repo.criar_transportadora()
    app = FastAPI()
    api.instalar(app, {**ENV, "ORGATEC_TRANSPORTE_MAPS_CHAVE_WEB": "AIza-teste", "ORGATEC_TRANSPORTE_MAPS_ID": "abc123"}, repo=repo)
    cli = TestClient(app)
    c = cli.get("/api/transporte/contexto", headers={"X-Transportadora-Id": tid}).json()
    assert c["mapa"] == {"provedor": "google", "chave": "AIza-teste", "map_id": "abc123"} and c["usuario_id"] == "dev"
    assert "AIza" not in cli.get("/api/transporte/entrada").text  # sem login, a chave do mapa não aparece


# ---------- pedágio por praça e postos ----------
P = ParametrosCusto()


def _montar(postos=None, combustivel=None):
    prov = Provedores(RotaSimulada(), combustivel or _Combustivel(), PedagioSimulado(), ClimaSimulado())
    if postos is not None:
        prov.postos = postos
    return viagem.montar([Ponto(nome="Goiânia", uf="GO"), Ponto(nome="Palmas", uf="TO")], eixos=6, consumo_km_l=Decimal("2.4"),
                         partida=datetime(2026, 11, 10, 9, tzinfo=UTC), parametros=P, parametros_vigencia="teste", provedores=prov,
                         bloqueios=BloqueioSimulado())


class _Combustivel:  # nome sem "Simulado": conta como fonte real (ANP)
    nome = "anp_teste"

    def __init__(self):
        self.pedidos = []

    def preco_diesel(self, uf, municipio):
        self.pedidos.append((uf, municipio))
        return PrecoCombustivel(Decimal("7.261"), f"{municipio}/{uf}, coleta até 2026-10-30", "ANP") if municipio == "Porangatu" else None


class _Postos:
    nome = "google_places"

    def postos_na_rota(self, geometria):
        lat, lon = geometria[len(geometria) // 2]
        return [Posto("Posto Exemplo", lat, lon, 400.0, "BR-153, km 10", "Porangatu", "GO", "Google Places", "ChIJ1"),
                Posto("Posto Sem ANP", lat, lon, 500.0, "BR-153", "Talismã", "TO", "Google Places", "ChIJ2"),
                Posto("Posto Também em Porangatu", lat, lon, 410.0, "BR-153", "Porangatu", "GO", "Google Places", "ChIJ3")]


def test_praca_sem_tarifa_usa_o_parametro_e_fica_estimada():
    from backend.transporte.provedores.base import PracaPedagio
    ps = viagem._pedagios([PracaPedagio("P1 - X (ECOVIAS DO ARAGUAIA, BR-153)", -12.0, -48.9, 10.0, Decimal("9.50"), "ANTT; tarifa: tabela oficial"),
                           PracaPedagio("Outra", -12.5, -48.9, 60.0, None, "ANTT, dados abertos (CC BY)")], 1.0, 6, P)
    assert (ps[0]["valor"], ps[0]["tarifa_oficial"]) == ("57.00", True)
    assert ps[1]["valor"] == str((P.pedagio_tarifa_padrao_cat1 * 6).quantize(Decimal("0.01"))) and not ps[1]["tarifa_oficial"]
    assert "estimada" in ps[1]["fonte"]


def test_cada_pedagio_traz_o_valor_para_os_eixos_do_veiculo():
    r = _montar()
    assert r["pedagios"]
    for p in r["pedagios"]:
        assert Decimal(p["valor"]) == Decimal(p["tarifa_cat1"]) * 6 and p["eixos"] == 6
        assert not p["tarifa_oficial"] and p["fonte"].startswith("Simulado")  # simulado nunca passa por tarifa oficial


def test_postos_com_media_anp_rotulada_e_sem_preco_inventado():
    comb = _Combustivel()
    r = _montar(_Postos(), comb)
    assert r["fontes"]["postos"]["estado"] == "ok"
    exemplo, sem, tambem = r["postos"]  # ordem do provedor (já vem por km)
    assert exemplo["preco_diesel_referencia"] == "7.261" and "não é o preço deste posto" in exemplo["preco_fonte"]
    assert sem["preco_diesel_referencia"] is None and "não disponível" in sem["preco_fonte"]
    assert tambem["preco_diesel_referencia"] == "7.261"
    assert comb.pedidos.count(("GO", "Porangatu")) == 1  # a média é consultada uma vez por município


def test_postos_sem_anp_real_ficam_sem_preco():
    class Simulado(_Combustivel):
        pass
    Simulado.__name__ = "CombustivelSimulado"
    r = _montar(_Postos(), Simulado())
    assert all(p["preco_diesel_referencia"] is None for p in r["postos"])


def test_polilinha_codificada_ida_e_volta():
    pts = [(-16.68, -49.25), (-16.5, -49.3), (-10.18, -48.33), (-10.18001, -48.33002)]
    assert _decodificar_polilinha(codificar_polilinha(pts)) == pts
    assert codificar_polilinha([(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]) == "_p~iF~ps|U_ulLnnqC_mqNvxq`@"  # exemplo do Google


def test_postos_google_chama_search_along_route_e_filtra_longe_da_rota():
    vistos = []

    def responder(req):
        vistos.append(req)
        return httpx.Response(200, json={"places": [
            {"id": "a", "displayName": {"text": "Posto Perto"}, "location": {"latitude": -13.0, "longitude": -49.0},
             "formattedAddress": "BR-153, Porangatu - GO", "addressComponents": [
                 {"longText": "Porangatu", "types": ["administrative_area_level_2", "political"]},
                 {"longText": "Goiás", "shortText": "GO", "types": ["administrative_area_level_1", "political"]}]},
            {"id": "b", "displayName": {"text": "Posto Longe"}, "location": {"latitude": -13.0, "longitude": -48.0}},
            {"id": "c", "displayName": {"text": "Sem local"}},
        ]})

    geo = [(-16.0, -49.0), (-13.0, -49.0), (-10.0, -49.0)]
    prov = PostosGoogle(ClienteHttp("google_places", transporte=httpx.MockTransport(responder)), "chave-teste", Cache(), 60)
    achados = prov.postos_na_rota(geo)
    assert [p.nome for p in achados] == ["Posto Perto"]
    assert (achados[0].municipio, achados[0].uf, achados[0].fonte) == ("Porangatu", "GO", "Google Places")
    corpo = json.loads(vistos[0].content)
    assert vistos[0].headers["X-Goog-Api-Key"] == "chave-teste" and "places.location" in vistos[0].headers["X-Goog-FieldMask"]
    assert corpo["includedType"] == "gas_station" and _decodificar_polilinha(corpo["searchAlongRouteParameters"]["polyline"]["encodedPolyline"]) == geo
    prov.postos_na_rota(geo)
    assert len(vistos) == 1  # mesma rota: vem do cache


def test_postos_real_exige_chave_e_desligado_nao_inventa():
    from backend.transporte.erros import RecursoDesligado
    with pytest.raises(RecursoDesligado):
        provedores_do_ambiente({"ORGATEC_TRANSPORTE_POSTOS_REAL": "1"})
    p = provedores_do_ambiente({"ORGATEC_TRANSPORTE_POSTOS_REAL": "1", "ORGATEC_TRANSPORTE_GOOGLE_CHAVE": "x"})
    assert isinstance(p.postos, PostosGoogle) and "postos" in p.reais()
    assert provedores_do_ambiente({}).postos.postos_na_rota([(0, 0), (1, 1)]) is None


# ---------- prazo de 30 dias das coordenadas do Google ----------
def _viagem_google(dias_atras, lat_informada=None):
    calc = (datetime.now(UTC) - timedelta(days=dias_atras)).isoformat()
    return {"id": "v1", "pontos": [{"nome": "A", "lat": None, "lon": None}, {"nome": "B", "lat": lat_informada, "lon": -48.3 if lat_informada else None}],
            "resultado": {"calculado_em": calc, "fontes": {"rota": {"fonte": "Google Routes API (veículo de passeio)"}},
                          "rota": {"distancia_km": 800, "geometria": [[-16.6, -49.2], [-10.1, -48.3]]},
                          "pontos": [{"nome": "A", "lat": -16.6, "lon": -49.2}, {"nome": "B", "lat": -10.1, "lon": -48.3}],
                          "pedagios": [{"nome": "P1", "lat": -12.0, "lon": -48.9}], "clima": [{"km": 0, "lat": -16.6, "lon": -49.2}],
                          "postos": [{"nome": "X", "lat": -13.0, "lon": -49.0, "id_externo": "ChIJ"}], "bloqueios": []}}


def test_expira_coordenadas_do_google_depois_do_prazo():
    limite = datetime.now(UTC) - timedelta(days=viagem.PRAZO_COORDENADAS_GOOGLE_DIAS)
    assert viagem.expirar_coordenadas(_viagem_google(10), limite) is None  # dentro do prazo
    novo = viagem.expirar_coordenadas(_viagem_google(31, lat_informada=-10.1), limite)
    assert novo["rota"]["geometria"] == [] and novo["coordenadas_expiradas"]
    assert novo["pontos"][0]["lat"] is None and novo["pontos"][1]["lat"] == -10.1  # o que o usuário digitou fica
    assert novo["pedagios"][0]["lat"] == -12.0  # ANTT não é do Google
    assert novo["clima"][0]["lat"] is None and novo["postos"][0]["lat"] is None and novo["postos"][0]["id_externo"] == "ChIJ"
    assert novo["rota"]["distancia_km"] == 800
    assert viagem.expirar_coordenadas({**_viagem_google(31), "resultado": novo}, limite) is None  # uma vez só


def test_rota_que_nao_e_do_google_e_sem_postos_nao_muda():
    v = _viagem_google(40)
    v["resultado"]["fontes"]["rota"]["fonte"] = "OpenRouteService"
    v["resultado"]["postos"] = []
    assert viagem.expirar_coordenadas(v, datetime.now(UTC)) is None


@pytest.mark.parametrize("fabrica", [RepositorioMemoria, lambda tmp: RepositorioSQLite(tmp / "t.db")])
def test_repositorio_expira_em_todas_as_transportadoras(fabrica, tmp_path):
    repo = fabrica() if fabrica is RepositorioMemoria else fabrica(tmp_path)
    a, b = repo.criar_transportadora(), repo.criar_transportadora()
    for tid, dias in ((a, 31), (b, 31), (b, 2)):
        v = _viagem_google(dias)
        repo.inserir(tid, "viagens", {k: v[k] for k in ("pontos", "resultado")})
    limite = datetime.now(UTC) - timedelta(days=viagem.PRAZO_COORDENADAS_GOOGLE_DIAS)
    assert repo.expirar_coordenadas_google(limite) == 2
    assert repo.expirar_coordenadas_google(limite) == 0
    restantes = [v["resultado"]["rota"]["geometria"] for v in repo.listar(b, "viagens")]
    assert sorted(len(g) for g in restantes) == [0, 2]


def test_posicoes_com_tracado_expirado_nao_quebram(amb):
    repo = amb["repo"]
    v = repo.obter(amb["a"], "viagens", amb["viagem"])
    v["resultado"]["rota"]["geometria"] = []
    repo.atualizar(amb["a"], "viagens", v["id"], {"resultado": v["resultado"]})
    r = amb["cli"].get(f"/api/transporte/viagens/{amb['viagem']}", headers=amb["h"]())
    assert r.status_code == 200 and r.json()["resultado"]["rota"]["geometria"] == []


# ---------- CSP ----------
def test_csp_do_mapa_so_em_transporte_e_igual_no_servidor_e_no_firebase():
    import importlib.util
    from pathlib import Path

    from backend import app as servidor
    caminho = Path(__file__).resolve().parents[3] / "tools" / "preparar_firebase.py"
    spec = importlib.util.spec_from_file_location("preparar_firebase_t", caminho)
    pf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pf)
    assert pf.csp_transporte(None) == servidor.CSP_TRANSPORTE
    assert "script-src 'self' https://maps.googleapis.com https://maps.gstatic.com;" in servidor.CSP_TRANSPORTE
    assert "unsafe-inline" not in servidor.CSP_TRANSPORTE.split("script-src")[1].split(";")[0]
    assert "*.googleapis.com" not in servidor.CSP_TRANSPORTE.split("script-src")[1].split(";")[0]  # curinga incluiria o Cloud Storage
    assert "maps.googleapis.com" not in servidor.CSP and "maps.googleapis.com" not in pf.csp(None)
