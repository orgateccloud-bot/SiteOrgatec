"""App Traccar Client (celular como rastreador, para teste de telemetria): adaptador do protocolo OsmAnd nas duas formas
(JSON e parâmetros), identificador do dispositivo = segredo do sensor, flag ORGATEC_TRANSPORTE_TRACCAR e caminho comum de gravação."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.transporte import api
from backend.transporte.erros import EntradaInvalida
from backend.transporte.repositorio_transporte import RepositorioMemoria
from backend.transporte.telemetria.adaptadores import traccar_client

ENV = {"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_SENSORES": "1", "ORGATEC_TRANSPORTE_CHAVE": "k" * 40,
       "ORGATEC_TRANSPORTE_TRACCAR": "1"}
VEICULO = {"placa": "ABC1D23", "eixos": 5, "consumo_km_l_carregado": 2.5, "consumo_km_l_vazio": 3.2, "tanque_l": 600}


def _amb(env=ENV):
    repo = RepositorioMemoria()
    tid = repo.criar_transportadora()
    app = FastAPI()
    assert api.instalar(app, env, repo=repo)
    cli = TestClient(app)
    h = {"X-Transportadora-Id": tid, "X-Usuario-Papel": "gestor", "X-Usuario-Id": "u-gestor"}
    vid = cli.post("/api/transporte/veiculos", json=VEICULO, headers=h).json()["id"]
    partida = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    viagem = cli.post("/api/transporte/viagens", headers=h, json={"veiculo_id": vid, "partida_prevista": partida, "carregado": True,
                                                                   "pontos": [{"nome": "Goiânia", "uf": "GO"}, {"nome": "Palmas", "uf": "TO"}]}).json()
    sensor = cli.post("/api/transporte/sensores", json={"veiculo_id": vid, "nome": "Celular do teste", "fornecedor": "traccar_client"},
                      headers=h).json()
    return cli, h, viagem, sensor


def _json(segredo, lat=-16.6, lon=-49.25, ts=None, speed=20.0):
    return {"device_id": segredo, "location": {"timestamp": ts or datetime.now(UTC).isoformat(), "event": "motionchange",
                                               "coords": {"latitude": lat, "longitude": lon, "speed": speed, "heading": 10,
                                                          "accuracy": 5, "altitude": 700}}}


def test_adaptador_json_converte_m_s_para_km_h():
    le = traccar_client(_json("x", ts="2026-11-10T20:00:00+00:00", speed=20.0))[0]
    assert (le["lat"], le["lon"], le["velocidade_kmh"], le["evento"]) == (-16.6, -49.25, 72.0, "motionchange")
    assert le["id"] == "tc-2026-11-10T20:00:00+00:00"


def test_adaptador_parametros_converte_nos_e_epoca():
    le = traccar_client({"id": "x", "lat": "-16.6", "lon": "-49.25", "timestamp": "1794340800", "speed": "10"})[0]
    assert le["velocidade_kmh"] == 18.5 and le["ts"].startswith("2026-")
    em_ms = traccar_client({"lat": "-16.6", "lon": "-49.25", "timestamp": "1794340800000", "speed": "-1"})[0]
    assert em_ms["ts"] == le["ts"] and em_ms["velocidade_kmh"] is None  # velocidade negativa = desconhecida


def test_adaptador_sem_coordenada_recusa():
    with pytest.raises(EntradaInvalida):
        traccar_client({"id": "x", "timestamp": "1794340800"})


def test_celular_envia_json_e_a_posicao_aparece_na_viagem():
    cli, h, viagem, sensor = _amb()
    assert sensor["endpoint"].endswith("/traccar") and "identificador do dispositivo" in sensor["aviso"]
    lat, lon = viagem["resultado"]["rota"]["geometria"][3]
    r = cli.post(sensor["endpoint"], json=_json(sensor["segredo"], lat, lon))
    assert r.status_code == 200 and r.json()["gravadas"] == 1
    pos = cli.get(f"/api/transporte/viagens/{viagem['id']}/posicoes", headers=h).json()
    assert len(pos) == 1 and pos[0]["velocidade_kmh"] == 72.0 and pos[0]["sensor"] == "Celular do teste"
    assert cli.get(f"/api/transporte/viagens/{viagem['id']}", headers=h).json()["status"] == "em_andamento"


def test_celular_envia_parametros_na_url_e_no_formulario():
    cli, _, _, sensor = _amb()
    ts = int(datetime.now(UTC).timestamp())
    r = cli.get(sensor["endpoint"], params={"id": sensor["segredo"], "lat": -16.6, "lon": -49.25, "timestamp": ts, "speed": 10})
    assert r.status_code == 200 and r.json()["gravadas"] == 1
    r = cli.post(sensor["endpoint"], data={"id": sensor["segredo"], "lat": -16.61, "lon": -49.25, "timestamp": ts + 10})
    assert r.status_code == 200 and r.json()["gravadas"] == 1


def test_identificador_errado_ou_sensor_de_outro_tipo_da_403():
    cli, h, _, sensor = _amb()
    assert cli.post(sensor["endpoint"], json=_json("errado")).status_code == 403
    assert cli.post(sensor["endpoint"], json=_json("")).status_code == 403
    vid = cli.get("/api/transporte/veiculos", headers=h).json()[0]["id"]
    comum = cli.post("/api/transporte/sensores", json={"veiculo_id": vid, "nome": "Rastreador"}, headers=h).json()
    assert cli.post(f"/api/telemetria/{comum['id']}/traccar", json=_json(comum["segredo"])).status_code == 403


def test_sem_a_flag_o_endereco_do_app_fica_desligado():
    env = {k: v for k, v in ENV.items() if k != "ORGATEC_TRANSPORTE_TRACCAR"}
    cli, _, _, sensor = _amb(env)
    assert cli.post(sensor["endpoint"], json=_json(sensor["segredo"])).status_code != 200
