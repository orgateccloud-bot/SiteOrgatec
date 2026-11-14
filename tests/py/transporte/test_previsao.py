"""Previsão do MET Norway no mapa público da Janela do Transporte: leitura da série, chuva forte no Sul, cache e limite dos
pedidos, rota sem login e a CSP da página do mapa interativo."""
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.transporte import api
from backend.transporte.alertas import previsao, publico, rotina
from backend.transporte.alertas.envio import SISTEMA, Envio
from backend.transporte.erros import ErroProvedor
from backend.transporte.provedores.http import ClienteHttp
from backend.transporte.repositorio_transporte import RepositorioMemoria

RAIZ = Path(__file__).resolve().parents[3]
AGORA = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)  # 9h em Brasília
ENV = {"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_ALERTAS": "1"}


def _passo(t, simbolo, chuva, temp=25.0, vento=5.0, horas=1):
    d = {"instant": {"details": {"air_temperature": temp, "wind_speed": vento}}}
    d["next_1_hours" if horas == 1 else "next_6_hours"] = {"summary": {"symbol_code": simbolo}, "details": {"precipitation_amount": chuva}}
    return {"time": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "data": d}


def _serie(chuva_por_hora=None, h6=()):
    """60 h de passos de 1 h a partir de AGORA e, depois, passos de 6 h (como o MET manda)."""
    chuva_por_hora = chuva_por_hora or {}
    ts = [_passo(AGORA + timedelta(hours=i), "rain_day" if chuva_por_hora.get(i) else "cloudy", chuva_por_hora.get(i, 0.0), temp=20 + i % 10) for i in range(60)]
    ts += [_passo(AGORA + timedelta(hours=60 + 6 * i), "heavyrain", c, horas=6) for i, c in enumerate(h6)]
    return {"properties": {"meta": {"updated_at": "2026-11-13T09:00:00Z"}, "timeseries": ts}}


def test_categorias_dos_simbolos_do_met():
    assert previsao.categoria("heavyrainandthunder_day") == "trovoada"
    assert previsao.categoria("heavyrainshowers_night") == "chuva_forte"
    assert previsao.categoria("lightrain") == "chuva_fraca"
    assert previsao.categoria("rainshowers_polartwilight") == "chuva"
    assert previsao.categoria("clearsky_day") == "limpo" and previsao.categoria("fair_night") == "poucas_nuvens"
    assert previsao.categoria("sleet") == "neve" and previsao.categoria("") == ""


def test_resumo_por_hora_e_por_dia_em_horario_de_brasilia_sem_contar_duas_vezes():
    r = previsao.resumir(_serie({0: 2.0, 1: 3.0, 20: 1.0}, h6=(6.0, 4.0)), AGORA)
    assert len(r["horas"]) == 12 and r["horas"][0]["vento"] == 18 and r["horas"][0]["tempo"] == "chuva"  # 5 m/s = 18 km/h
    dias = {d["dia"]: d for d in r["dias"]}
    assert list(dias)[0] == "2026-11-13"  # 12h UTC = 9h em Brasília
    assert dias["2026-11-13"]["chuva"] == 5.0 and dias["2026-11-14"]["chuva"] == 1.0  # a hora 20 (8h UTC do dia 14) cai às 5h de Brasília do dia 14
    assert sum(d["chuva"] for d in r["dias"]) == 16.0  # os passos de 6 h entram uma vez só
    assert r["credito"].startswith("Dados do MET Norway") and r["rotulos"]["chuva_forte"] == "Chuva forte"


def test_chuva_forte_e_muito_forte_nas_proximas_48_h():
    assert previsao.risco(_serie({5: 4.0}), AGORA)["nivel"] == ""
    forte = previsao.risco(_serie({5: 4.0, 10: 12.0}), AGORA)
    assert forte["nivel"] == "forte" and forte["inicio"] == "2026-11-13T22:00:00+00:00" and forte["chuva_max"] == 12.0 and forte["chuva_total"] == 16.0
    assert previsao.risco(_serie({10: 12.0, 30: 25.0}), AGORA)["nivel"] == "muito_forte"
    assert previsao.risco(_serie({50: 40.0}), AGORA)["nivel"] == ""  # depois de 48 h não conta
    # por dia de Brasília: hora 10 = 13/11 19h, hora 30 = 14/11 15h, hora 40 = 15/11 01h
    dias = previsao.risco(_serie({10: 12.0, 30: 25.0, 40: 11.0}), AGORA)["dias"]
    assert dias == {"2026-11-13": "forte", "2026-11-14": "muito_forte", "2026-11-15": "forte"}
    assert previsao.risco(_serie({5: 4.0}), AGORA)["dias"] == {}


def _transporte(contagem, status=200, expira=None):
    def responder(req):
        contagem.append(req)
        if status != 200:
            return httpx.Response(status)
        return httpx.Response(200, json=_serie({3: 11.0}), headers={"Expires": expira} if expira else {})
    return httpx.MockTransport(responder)


def test_cache_por_ponto_ate_o_expires_nunca_antes_de_3_h_e_limite_de_pedidos():
    pedidos, relogio = [], [AGORA.timestamp()]
    met = previsao.PrevisaoMet(ClienteHttp("met_norway", transporte=_transporte(pedidos, expira="Fri, 13 Nov 2026 12:30:00 GMT"), dormir=lambda s: None),
                               relogio=lambda: relogio[0], limite=2)
    a = met.ponto(-27.6123, -48.5512, AGORA)
    assert (a["lat"], a["lon"]) == (-27.6, -48.6) and len(pedidos) == 1
    assert pedidos[0].url.params["lat"] == "-27.6000" and pedidos[0].url.params["lon"] == "-48.6000"  # no máximo 4 casas
    met.ponto(-27.58, -48.62, AGORA)  # mesma célula de 0,1°
    relogio[0] += 2 * 3600  # passou do Expires (30 min), mas não de 3 h
    met.ponto(-27.6, -48.6, AGORA)
    assert len(pedidos) == 1
    relogio[0] += 3600 + 1
    met.ponto(-27.6, -48.6, AGORA)
    assert len(pedidos) == 2
    met.ponto(-10.0, -48.0, AGORA)
    with pytest.raises(ErroProvedor):  # 2 pedidos na janela de 10 min: o terceiro não sai
        met.ponto(-11.0, -48.0, AGORA)
    assert len(pedidos) == 3


def test_cliente_do_met_se_identifica():
    pedidos = []
    previsao.previsao_met(_transporte(pedidos)).buscar(-27.6, -48.6)
    assert pedidos[0].headers["user-agent"] == "orgatec.io/1.0 (https://orgatec.io)"
    assert str(pedidos[0].url).startswith("https://api.met.no/weatherapi/locationforecast/2.0/compact?")


def test_grade_do_sul_cai_dentro_de_pr_sc_e_rs():
    pontos = previsao.grade_sul()
    assert len(pontos) == 90 and {p[0] for p in pontos} == {"PR", "SC", "RS"}
    assert all(-34.0 < p[1] < -22.4 and -58.0 < p[2] < -47.9 for p in pontos)


def test_sul_renova_a_cada_3_h_e_guarda_o_anterior_se_o_met_cair():
    pedidos = []
    met = previsao.PrevisaoMet(ClienteHttp("met_norway", transporte=_transporte(pedidos), dormir=lambda s: None))
    novo = previsao.temporal_sul(None, met, AGORA)
    assert novo["estado"] == "ok" and len(novo["pontos"]) == 90 and len(pedidos) == 90
    assert novo["ufs"]["RS"]["nivel"] == "forte" and novo["ufs"]["RS"]["inicio"] == "2026-11-13T15:00:00+00:00"
    assert novo["ufs"]["RS"]["dias"] == {"2026-11-13": {"nivel": "forte", "pontos": novo["ufs"]["RS"]["pontos"]}}
    assert novo["pontos"][0][7] == {"2026-11-13": "forte"}
    assert previsao.temporal_sul(novo, None, AGORA + timedelta(hours=2)) is novo  # menos de 3 h: nem pede
    assert previsao.temporal_sul(None, None, AGORA) is None
    caindo = []
    fora = previsao.PrevisaoMet(ClienteHttp("met_norway", transporte=_transporte(caindo, status=500), dormir=lambda s: None, tentativas=1))
    velho = previsao.temporal_sul(novo, fora, AGORA + timedelta(hours=4))
    assert velho["estado"] == "indisponivel" and velho["pontos"] == novo["pontos"] and velho["atualizado_em"] == novo["atualizado_em"]
    assert len(caindo) < 20  # na primeira falha os outros pedidos não saem
    assert previsao.temporal_sul(None, fora, AGORA)["estado"] == "indisponivel"


def test_rotina_grava_a_chuva_do_sul_no_resumo_nacional(monkeypatch):
    monkeypatch.setattr(publico, "malha", lambda: publico.Malha.de({}))
    repo = RepositorioMemoria()
    pedidos = []

    class Inmet:
        origem = credito = "inmet"

        def buscar(self, *a):
            return []

    met = previsao.PrevisaoMet(ClienteHttp("met_norway", transporte=_transporte(pedidos), dormir=lambda s: None))
    cfg = rotina.Configuracao(Inmet(), None, None, Envio(repo, None, None, Decimal("50")), {}, met)
    rotina.executar(repo, cfg, AGORA)
    atual = repo.obter(SISTEMA, "alertas_publicos", "atual")
    assert atual["temporal"]["ufs"]["PR"]["nivel"] == "forte" and len(pedidos) == 90
    rotina.executar(repo, cfg, AGORA + timedelta(minutes=15))  # 15 min depois: reaproveita, sem pedir de novo
    assert len(pedidos) == 90 and repo.obter(SISTEMA, "alertas_publicos", "atual")["temporal"]["atualizado_em"] == AGORA.isoformat()
    assert rotina.configurar({}, repo).met is None and rotina.configurar({"ORGATEC_TRANSPORTE_PREVISAO": "1"}, repo).met is not None


def test_rota_da_previsao_sem_login_com_cache_so_no_brasil():
    pedidos = []
    app = FastAPI()
    api.instalar(app, ENV, repo=RepositorioMemoria())
    cli = TestClient(app)
    assert cli.get("/api/transporte/previsao?lat=-27.6&lon=-48.6").status_code == 404  # desligada sem ORGATEC_TRANSPORTE_PREVISAO
    app.state.transporte.previsao = previsao.PrevisaoMet(ClienteHttp("met_norway", transporte=_transporte(pedidos), dormir=lambda s: None))
    r = cli.get("/api/transporte/previsao?lat=-27.61&lon=-48.58")
    assert r.status_code == 200 and r.headers["cache-control"] == "public, max-age=600, s-maxage=3600"
    assert r.json()["lat"] == -27.6 and r.json()["dias"] and r.json()["credito"].startswith("Dados do MET Norway")
    for lat, lon in (("48.8", "2.3"), ("-27.6", "-20.0"), ("nan", "-48.6")):
        assert cli.get(f"/api/transporte/previsao?lat={lat}&lon={lon}").status_code == 422
    assert len(pedidos) == 1
    app.state.transporte.previsao = previsao.PrevisaoMet(ClienteHttp("met_norway", transporte=_transporte([], status=503), dormir=lambda s: None, tentativas=1))
    caiu = cli.get("/api/transporte/previsao?lat=-20&lon=-45")
    assert caiu.status_code == 503 and caiu.headers["cache-control"] == "no-store"
    assert api.criar_servicos({**ENV, "ORGATEC_TRANSPORTE_PREVISAO": "1"}, repo=RepositorioMemoria()).previsao is not None


def test_previsao_escapa_do_no_store_da_api_so_quando_da_certo():
    from backend import app as servidor
    assert servidor._publica_com_cache("/api/transporte/previsao")
    assert not servidor._publica_com_cache("/api/transporte/previsao/x") and not servidor._publica_com_cache("/api/transporte/previsaox")


def test_so_a_pagina_da_janela_baixa_imagens_da_nasa_por_fetch():
    from backend import app as servidor
    from tools import preparar_firebase as pf
    cfg = pf.firebase_json(None, False, "orgatec-api", pf.REGIAO_PADRAO)
    regras = {h["source"]: {x["key"]: x["value"] for x in h["headers"]} for h in cfg["hosting"]["headers"]}
    janela = regras["/empresarial/janela.html"]["Content-Security-Policy"]
    assert janela == servidor.CSP_JANELA
    assert "connect-src 'self' https://gibs.earthdata.nasa.gov;" in janela and "blob:" in janela and "script-src 'self';" in janela
    assert "unsafe-eval" not in janela and "worker-src" not in janela
    assert "connect-src 'self';" in regras["**"]["Content-Security-Policy"]  # o resto do site não muda
    assert regras["/assets/vendor/**"]["Cache-Control"] == "public, max-age=31536000, immutable"
    versionado = json.loads((RAIZ / "firebase.json").read_text(encoding="utf-8"))
    assert any(h["source"] == "/empresarial/janela.html" for h in versionado["hosting"]["headers"])


def test_biblioteca_do_mapa_hospedada_no_site_sem_cdn():
    pasta = RAIZ / "site" / "assets" / "vendor" / "maplibre-gl-4.7.1"
    assert {p.name for p in pasta.iterdir()} >= {"maplibre-gl-csp.js", "maplibre-gl-csp-worker.js", "maplibre-gl.css", "LICENSE.txt"}
    pagina = (RAIZ / "site" / "empresarial" / "janela.html").read_text(encoding="utf-8")
    assert 'data-gl="../assets/vendor/maplibre-gl-4.7.1/"' in pagina and 'data-previsao="/api/transporte/previsao"' in pagina
    assert "unpkg.com" not in pagina and "jsdelivr" not in pagina
