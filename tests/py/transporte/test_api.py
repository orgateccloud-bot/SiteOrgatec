"""API da Central de Viagem: flag, isolamento entre transportadoras, papéis, portal em leitura, sensores com HMAC e idempotência."""

import json
import time
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.transporte import api
from backend.transporte.erros import RecursoDesligado
from backend.transporte.repositorio_transporte import RepositorioMemoria
from backend.transporte.telemetria.seguranca import Cofre, assinar

CHAVE = "k" * 40
ENV = {"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_SENSORES": "1", "ORGATEC_TRANSPORTE_CHAVE": CHAVE}
VEICULO = {"placa": "ABC1D23", "eixos": 5, "consumo_km_l_carregado": 2.5, "consumo_km_l_vazio": 3.2, "tanque_l": 600}
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
    return {"cli": cli, "a": a, "b": b, "h": h, "repo": repo, "app": app}


def _veiculo(amb, tid=None):
    r = amb["cli"].post("/api/transporte/veiculos", json=VEICULO, headers=amb["h"](tid or amb["a"]))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _viagem(amb, veiculo_id, partida=None, papel="gestor"):
    partida = partida or (datetime.now(UTC) + timedelta(hours=1))
    corpo = {"veiculo_id": veiculo_id, "pontos": PONTOS, "partida_prevista": partida.isoformat(), "carregado": True}
    return amb["cli"].post("/api/transporte/viagens", json=corpo, headers=amb["h"](papel=papel))


def test_flag_desligada_nao_registra_rota_nenhuma():
    app = FastAPI()
    assert api.instalar(app, {}) is False and not [r for r in app.routes if "transporte" in getattr(r, "path", "")]


def test_modo_dev_e_recusado_em_producao():
    with pytest.raises(RecursoDesligado):
        api.criar_servicos({**ENV, "ORGATEC_PRODUCAO": "1"})  # auth dev em produção


def test_producao_sem_login_real_responde_403_em_tudo():
    repo = RepositorioMemoria()
    tid = repo.criar_transportadora()
    app = FastAPI()
    api.instalar(app, {**ENV, "ORGATEC_PRODUCAO": "1", "ORGATEC_TRANSPORTE_AUTH": "externo"}, repo=repo)
    r = TestClient(app).get("/api/transporte/veiculos", headers={"X-Transportadora-Id": tid})
    assert r.status_code == 403


def test_provedor_real_e_recusado_enquanto_nao_existe():
    with pytest.raises(RecursoDesligado):
        api.criar_servicos({**ENV, "ORGATEC_TRANSPORTE_ROTA_REAL": "1"})


def test_rota_de_teste_mostra_despesas_tempo_bloqueios_e_clima(amb):
    v = _viagem(amb, _veiculo(amb))
    assert v.status_code == 201, v.text
    res = v.json()["resultado"]
    assert res["despesas"]["total"] and {i["tipo"] for i in res["despesas"]["itens"]} >= {"combustivel", "pedagio", "hospedagem", "reserva_imprevistos"}
    assert res["jornada"]["chegada_prevista"] and res["rota"]["distancia_km"] > 500
    assert "bloqueios" in res and "clima" in res


def test_bloqueio_cadastrado_na_rota_aparece_no_calculo(amb):
    vid = _veiculo(amb)
    base = _viagem(amb, vid).json()
    meio = base["resultado"]["rota"]["geometria"][len(base["resultado"]["rota"]["geometria"]) // 2]
    agora = datetime.now(UTC)
    r = amb["cli"].post("/api/transporte/alertas", headers=amb["h"](), json={
        "tipo": "obra", "descricao": "Obra na pista", "lat": meio[0], "lon": meio[1], "raio_km": 5,
        "inicio": (agora - timedelta(days=1)).isoformat(), "fonte": "Cadastro da transportadora"})
    assert r.status_code == 201
    assert _viagem(amb, vid).json()["alertas"] == 1


def test_parametros_ajustaveis_mudam_as_despesas(amb):
    vid = _veiculo(amb)
    antes = _viagem(amb, vid).json()["total_despesas"]
    p = amb["cli"].get("/api/transporte/parametros", headers=amb["h"]()).json()["valores"]
    p["diaria_hospedagem"] = "999.00"
    assert amb["cli"].put("/api/transporte/parametros", json=p, headers=amb["h"]()).status_code == 200
    depois = _viagem(amb, vid).json()["total_despesas"]
    assert float(depois) > float(antes)


def test_isolamento_entre_transportadoras(amb):
    vid = _veiculo(amb)
    viagem = _viagem(amb, vid).json()
    outra = amb["cli"].get(f"/api/transporte/viagens/{viagem['id']}", headers=amb["h"](amb["b"]))
    assert outra.status_code == 404
    assert amb["cli"].get("/api/transporte/viagens", headers=amb["h"](amb["b"])).json() == []
    # veículo de A não pode ser usado por B
    corpo = {"veiculo_id": vid, "pontos": PONTOS, "partida_prevista": datetime.now(UTC).isoformat()}
    assert amb["cli"].post("/api/transporte/viagens", json=corpo, headers=amb["h"](amb["b"])).status_code == 404


def test_portal_em_modo_leitura_nao_escreve(amb):
    vid = _veiculo(amb)
    viagem = _viagem(amb, vid).json()
    leitor = amb["h"](papel="leitura", usuario="u-cliente")
    assert amb["cli"].get(f"/api/transporte/viagens/{viagem['id']}", headers=leitor).status_code == 200
    assert amb["cli"].post("/api/transporte/veiculos", json={**VEICULO, "placa": "XYZ9A87"}, headers=leitor).status_code == 403
    assert amb["cli"].post("/api/transporte/viagens", json={"veiculo_id": vid, "pontos": PONTOS, "partida_prevista": datetime.now(UTC).isoformat()}, headers=leitor).status_code == 403
    assert amb["cli"].post("/api/transporte/sensores", json={"veiculo_id": vid, "nome": "S"}, headers=leitor).status_code == 403


def test_motorista_so_ve_as_proprias_viagens(amb):
    vid = _veiculo(amb)
    m = amb["cli"].post("/api/transporte/motoristas", json={"nome": "João", "usuario_id": "u-mot"}, headers=amb["h"]()).json()
    corpo = {"veiculo_id": vid, "motorista_id": m["id"], "pontos": PONTOS, "partida_prevista": datetime.now(UTC).isoformat()}
    propria = amb["cli"].post("/api/transporte/viagens", json=corpo, headers=amb["h"]()).json()
    _viagem(amb, vid)  # outra, sem motorista
    mot = amb["h"](papel="motorista", usuario="u-mot")
    ids = [x["id"] for x in amb["cli"].get("/api/transporte/viagens", headers=mot).json()]
    assert ids == [propria["id"]]


def _sensor(amb, vid):
    r = amb["cli"].post("/api/transporte/sensores", json={"veiculo_id": vid, "nome": "Rastreador 1"}, headers=amb["h"]())
    assert r.status_code == 201, r.text
    return r.json()


def _enviar(amb, sensor, leituras, segredo=None, ts=None):
    corpo = json.dumps({"leituras": leituras}).encode()
    ts = ts or str(int(time.time()))
    assin = assinar(segredo or sensor["segredo"], ts, corpo)
    return amb["cli"].post(sensor["endpoint"], content=corpo, headers={"X-Timestamp": ts, "X-Assinatura": assin})


def _leitura(i, lat, lon, ts=None):
    return {"id": f"l{i}", "ts": (ts or datetime.now(UTC)).isoformat(), "lat": lat, "lon": lon, "velocidade_kmh": 70}


def test_sensor_atualiza_posicao_e_status_e_e_idempotente(amb):
    vid = _veiculo(amb)
    viagem = _viagem(amb, vid, partida=datetime.now(UTC) + timedelta(hours=1)).json()
    sensor = _sensor(amb, vid)
    assert "segredo" in sensor and "segredo" not in amb["cli"].get("/api/transporte/sensores", headers=amb["h"]()).json()[0]
    lat, lon = viagem["resultado"]["rota"]["geometria"][3]
    r = _enviar(amb, sensor, [_leitura(1, lat, lon), _leitura(2, lat, lon, datetime.now(UTC) + timedelta(seconds=5))])
    assert r.status_code == 200 and r.json() == {"recebidas": 2, "gravadas": 2, "duplicadas": 0}
    assert _enviar(amb, sensor, [_leitura(1, lat, lon)]).json()["duplicadas"] == 1  # reenvio não duplica
    assert amb["cli"].get(f"/api/transporte/viagens/{viagem['id']}", headers=amb["h"]()).json()["status"] == "em_andamento"
    pos = amb["cli"].get(f"/api/transporte/viagens/{viagem['id']}/posicoes", headers=amb["h"]()).json()
    assert len(pos) == 2 and pos[0]["fora_da_rota"] is False


def test_assinatura_errada_relogio_fora_e_sensor_inexistente_dao_403_sem_motivo(amb):
    vid = _veiculo(amb)
    _viagem(amb, vid)
    sensor = _sensor(amb, vid)
    assert _enviar(amb, sensor, [_leitura(1, -16.0, -49.0)], segredo="x" * 64).status_code == 403
    assert _enviar(amb, sensor, [_leitura(1, -16.0, -49.0)], ts=str(int(time.time()) - 3600)).status_code == 403
    r = amb["cli"].post("/api/telemetria/nao-existe", content=b"{}", headers={"X-Timestamp": str(int(time.time())), "X-Assinatura": "a"})
    assert r.status_code == 403 and r.json() == {"detail": "Acesso negado."}
    amb["cli"].delete(f"/api/transporte/sensores/{sensor['id']}", headers=amb["h"]())
    assert _enviar(amb, sensor, [_leitura(1, -16.0, -49.0)]).status_code == 403  # sensor desativado


def test_limite_de_uso_do_sensor_responde_429(amb):
    vid = _veiculo(amb)
    _viagem(amb, vid)
    sensor = _sensor(amb, vid)
    amb["app"].state.transporte.limitador = api.ingestao.Limitador(maximo=2, janela_s=60)
    codigos = [_enviar(amb, sensor, [_leitura(i, -16.0, -49.0)]).status_code for i in range(4)]
    assert codigos[:2] == [200, 200] and 429 in codigos[2:]


def test_corpo_invalido_e_fornecedor_sem_adaptador(amb):
    vid = _veiculo(amb)
    sensor = _sensor(amb, vid)
    ts = str(int(time.time()))
    corpo = b"isso nao e json"
    r = amb["cli"].post(sensor["endpoint"], content=corpo, headers={"X-Timestamp": ts, "X-Assinatura": assinar(sensor["segredo"], ts, corpo)})
    assert r.status_code == 422
    r = amb["cli"].post("/api/transporte/sensores", json={"veiculo_id": vid, "nome": "S", "fornecedor": "acme"}, headers=amb["h"]())
    assert r.status_code == 422


def test_sensor_simulado_pela_api_atualiza_posicao(amb):
    vid = _veiculo(amb)
    viagem = _viagem(amb, vid, partida=datetime.now(UTC) + timedelta(minutes=30)).json()
    sensor = _sensor(amb, vid)
    r = amb["cli"].post(f"/api/transporte/viagens/{viagem['id']}/simular-sensor", json={"sensor_id": sensor["id"], "leituras": 4}, headers=amb["h"]())
    assert r.status_code == 200 and r.json()["gravadas"] == 4
    pos = amb["cli"].get(f"/api/transporte/viagens/{viagem['id']}/posicoes", headers=amb["h"]()).json()
    assert len(pos) == 4 and max(p["km_percorrido"] for p in pos) > 0


def test_sem_chave_mestra_o_cofre_nao_abre():
    with pytest.raises(RecursoDesligado):
        Cofre("curta")


def test_segredo_derivado_nao_e_igual_entre_sensores_nem_versoes():
    c = Cofre(CHAVE)
    assert c.segredo_do_sensor("a") != c.segredo_do_sensor("b") and c.segredo_do_sensor("a", 1) != c.segredo_do_sensor("a", 2)


def test_purga_de_leituras_pelo_prazo_de_guarda(amb):
    vid = _veiculo(amb)
    _viagem(amb, vid)
    sensor = _sensor(amb, vid)
    _enviar(amb, sensor, [_leitura(1, -16.0, -49.0)])
    assert amb["repo"].purgar_leituras(datetime.now(UTC) + timedelta(days=1)) == 1
