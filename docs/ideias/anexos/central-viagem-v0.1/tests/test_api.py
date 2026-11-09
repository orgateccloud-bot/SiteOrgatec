import asyncio
import json
import time
from decimal import Decimal

from fastapi.testclient import TestClient

from transporte.api.app import criar_app
from transporte.db.tabelas import Transportadora
from transporte.erros import ProvedorTimeout
from transporte.provedores.registro import FabricaProvedores
from transporte.telemetria import ingestao
from transporte.telemetria.seguranca import assinar

from .conftest import config

VEICULO = {
    "placa": "ABC1D23",
    "descricao": "Cavalo 6x2 + carreta",
    "eixos": 6,
    "consumo_km_l_carregado": "2.3",
    "consumo_km_l_vazio": "2.9",
    "tanque_l": "700",
}
ROTA = {
    "pontos": [{"nome": "Goiânia", "uf": "GO"}, {"nome": "Palmas", "uf": "TO"}],
    "partida_prevista": "2026-11-10T06:00:00-03:00",
    "carregado": True,
}


def _lancar(amb, papel="gestor", usuario="u-gestor"):
    cli, h = amb["cli"], amb["h"]
    vid = cli.post("/api/transporte/veiculos", json=VEICULO, headers=h()).json()["id"]
    r = cli.post("/api/transporte/viagens", json={**ROTA, "veiculo_id": vid}, headers=h(papel=papel, usuario=usuario))
    return vid, r


def test_sem_identificacao_ou_transportadora_inexistente_e_negado(ambiente):
    cli = ambiente["cli"]
    assert cli.get("/api/transporte/viagens").status_code == 403
    assert cli.get("/api/transporte/viagens", headers=ambiente["h"](tid="nao-existe")).status_code == 403


def test_lancar_rota_entrega_despesas_tempo_bloqueios_e_clima(ambiente):
    _, r = _lancar(ambiente)
    assert r.status_code == 201, r.text
    res = r.json()["resultado"]
    tipos = {i["tipo"] for i in res["despesas"]["itens"]}
    assert {"combustivel", "pedagio", "hospedagem", "alimentacao", "pneus", "borracharia"} <= tipos
    assert Decimal(res["despesas"]["total"]) > 0
    assert res["jornada"]["chegada_prevista"] and res["jornada"]["pernoites"] >= 1
    assert res["bloqueios"] and res["clima"]


def test_portal_leitura_ve_o_mesmo_e_nao_altera(ambiente):
    cli, h = ambiente["cli"], ambiente["h"]
    _, r = _lancar(ambiente)
    vid = r.json()["id"]
    portal = cli.get(f"/api/transporte/viagens/{vid}", headers=h(papel="leitura"))
    assert portal.status_code == 200 and portal.json()["resultado"] == r.json()["resultado"]
    assert cli.post("/api/transporte/viagens", json=ROTA, headers=h(papel="leitura")).status_code == 403
    assert (
        cli.put(
            f"/api/transporte/viagens/{vid}/despesas/pedagio", json={"valor": 1}, headers=h(papel="leitura")
        ).status_code
        == 403
    )


def test_isolamento_entre_transportadoras(ambiente):
    _, r = _lancar(ambiente)
    outra = ambiente["cli"].get(f"/api/transporte/viagens/{r.json()['id']}", headers=ambiente["h"](tid=ambiente["b"]))
    assert outra.status_code == 404
    assert ambiente["cli"].get("/api/transporte/viagens", headers=ambiente["h"](tid=ambiente["b"])).json() == []


def test_ajuste_manual_e_remocao(ambiente):
    cli, h = ambiente["cli"], ambiente["h"]
    _, r = _lancar(ambiente)
    vid, total = r.json()["id"], Decimal(r.json()["total_despesas"])
    aj = cli.put(f"/api/transporte/viagens/{vid}/despesas/hospedagem", json={"valor": "0"}, headers=h()).json()
    assert Decimal(aj["total_despesas"]) < total and aj["ajustes"] == {"hospedagem": "0"}
    volta = cli.put(f"/api/transporte/viagens/{vid}/despesas/hospedagem", json={"valor": None}, headers=h()).json()
    assert Decimal(volta["total_despesas"]) == total


def test_parametros_editaveis_mudam_o_recalculo(ambiente):
    cli, h = ambiente["cli"], ambiente["h"]
    _, r = _lancar(ambiente)
    vid = r.json()["id"]
    p = cli.get("/api/transporte/parametros", headers=h()).json()
    assert "fonte" in p["meta"]["direcao_continua_max_h"]
    novos = {**p["valores"], "diaria_hospedagem": "300.00"}
    assert cli.put("/api/transporte/parametros", json=novos, headers=h()).status_code == 200
    rec = cli.post(f"/api/transporte/viagens/{vid}/recalcular", headers=h()).json()
    assert Decimal(rec["total_despesas"]) > Decimal(r.json()["total_despesas"])
    assert cli.put("/api/transporte/parametros", json={**novos, "x": 1}, headers=h()).status_code == 422


def test_motorista_lanca_e_ve_so_as_proprias(ambiente):
    cli, h = ambiente["cli"], ambiente["h"]
    _, r = _lancar(ambiente, papel="motorista", usuario="u-motorista")
    assert r.status_code == 201 and r.json()["motorista_id"]
    cli.post("/api/transporte/viagens", json={**ROTA, "veiculo_id": r.json()["veiculo_id"]}, headers=h())
    assert len(cli.get("/api/transporte/viagens", headers=h(papel="motorista", usuario="u-motorista")).json()) == 1
    assert len(cli.get("/api/transporte/viagens", headers=h()).json()) == 2
    assert cli.get("/api/transporte/viagens", headers=h(papel="motorista", usuario="outro")).json() == []


def test_local_desconhecido_no_simulado_da_422_com_mensagem(ambiente):
    cli, h = ambiente["cli"], ambiente["h"]
    vid = cli.post("/api/transporte/veiculos", json=VEICULO, headers=h()).json()["id"]
    r = cli.post(
        "/api/transporte/viagens",
        headers=h(),
        json={**ROTA, "veiculo_id": vid, "pontos": [{"nome": "Lugar Nenhum"}, {"nome": "Palmas"}]},
    )
    assert r.status_code == 422 and "demonstração" in r.json()["erro"]


def test_falha_da_rota_real_vira_503_com_estado():
    cfg = config()
    fab = FabricaProvedores(cfg)

    class Falha:
        nome = "openrouteservice"

        def geocodificar(self, *a):
            raise ProvedorTimeout("ors", "x")

        calcular = geocodificar

    fab._rota = Falha()
    app = criar_app(cfg, criar_tabelas=True, servir_web=False, provedores=fab)
    s = app.state.servicos.sessoes.nova()
    t = Transportadora(nome="T")
    s.add(t)
    s.commit()
    cli = TestClient(app)
    h = {"X-Transportadora-Id": t.id}
    vid = cli.post("/api/transporte/veiculos", json=VEICULO, headers=h).json()["id"]
    r = cli.post("/api/transporte/viagens", json={**ROTA, "veiculo_id": vid}, headers=h)
    assert r.status_code == 503 and r.json()["estado"] == "timeout"


# ---------------- Sensores e telemetria ----------------
def _sensor(amb, vid):
    r = amb["cli"].post(
        "/api/transporte/sensores", json={"veiculo_id": vid, "nome": "Rastreador 1"}, headers=amb["h"]()
    )
    assert r.status_code == 201, r.text
    return r.json()


def _enviar(cli, sensor, leituras, ts=None, segredo=None):
    corpo = json.dumps({"leituras": leituras}).encode()
    ts = ts or str(int(time.time()))
    sig = assinar(segredo or sensor["segredo"], ts, corpo)
    return cli.post(
        f"/api/telemetria/{sensor['id']}",
        content=corpo,
        headers={"X-Timestamp": ts, "X-Assinatura": sig, "Content-Type": "application/json"},
    )


def test_sensores_desligados_por_flag():
    app = criar_app(config(sensores_ativo=False), criar_tabelas=True, servir_web=False)
    s = app.state.servicos.sessoes.nova()
    t = Transportadora(nome="T")
    s.add(t)
    s.commit()
    cli = TestClient(app)
    assert cli.get("/api/transporte/sensores", headers={"X-Transportadora-Id": t.id}).status_code == 404
    assert cli.post("/api/telemetria/qualquer", content=b"{}").status_code == 404


def test_sensor_via_api_atualiza_posicao_e_status(ambiente):
    cli, h = ambiente["cli"], ambiente["h"]
    vid, r = _lancar(ambiente)
    viagem = r.json()
    sensor = _sensor(ambiente, vid)
    lat, lon = viagem["resultado"]["rota"]["geometria"][40]
    leitura = {
        "id": "L1",
        "ts": "2026-11-10T08:00:00-03:00",
        "lat": lat,
        "lon": lon,
        "velocidade_kmh": 72,
        "ignicao": True,
    }
    resp = _enviar(cli, sensor, [leitura])
    assert resp.status_code == 200 and resp.json() == {"recebidas": 1, "gravadas": 1, "duplicadas": 0}
    assert _enviar(cli, sensor, [leitura]).json()["duplicadas"] == 1
    det = cli.get(f"/api/transporte/viagens/{viagem['id']}", headers=h(papel="leitura")).json()
    assert det["status"] == "em_andamento"
    pos = cli.get(f"/api/transporte/viagens/{viagem['id']}/posicoes", headers=h(papel="leitura")).json()
    assert len(pos) == 1 and pos[0]["km_percorrido"] > 0 and not pos[0]["fora_da_rota"]
    sensores = cli.get("/api/transporte/sensores", headers=h()).json()
    assert sensores[0]["ultimo_sinal_em"] and "segredo" not in sensores[0]


def test_telemetria_recusa_assinatura_errada_relogio_e_corpo_invalido(ambiente):
    cli = ambiente["cli"]
    vid, _ = _lancar(ambiente)
    sensor = _sensor(ambiente, vid)
    leitura = [{"id": "x", "ts": "2026-11-10T08:00:00Z", "lat": -16, "lon": -49}]
    assert _enviar(cli, sensor, leitura, segredo="errado").status_code == 403
    assert _enviar(cli, sensor, leitura, ts=str(int(time.time()) - 3600)).status_code == 403
    assert _enviar(cli, sensor, [{"id": "x", "ts": "sem-data", "lat": 0, "lon": 0}]).status_code == 422
    assert cli.post("/api/telemetria/inexistente", content=b"{}").status_code == 403
    cli.delete(f"/api/transporte/sensores/{sensor['id']}", headers=ambiente["h"]())
    assert _enviar(cli, sensor, leitura).status_code == 403


def test_sensor_simulado_pelo_endpoint(ambiente):
    cli, h = ambiente["cli"], ambiente["h"]
    vid, r = _lancar(ambiente)
    sensor = _sensor(ambiente, vid)
    viagem_id = r.json()["id"]
    res = cli.post(
        f"/api/transporte/viagens/{viagem_id}/simular-sensor",
        json={"sensor_id": sensor["id"], "leituras": 5},
        headers=h(),
    )
    assert res.status_code == 200 and res.json()["gravadas"] == 5
    seg = cli.post(
        f"/api/transporte/viagens/{viagem_id}/simular-sensor",
        json={"sensor_id": sensor["id"], "leituras": 3},
        headers=h(),
    ).json()
    assert seg["gravadas"] == 3
    pos = cli.get(f"/api/transporte/viagens/{viagem_id}/posicoes", headers=h()).json()
    assert len(pos) == 8 and pos[0]["km_percorrido"] > pos[-1]["km_percorrido"]


def test_ingestao_publica_no_broker_em_tempo_real(ambiente):
    cli = ambiente["cli"]
    vid, r = _lancar(ambiente)
    sensor = _sensor(ambiente, vid)
    viagem_id = r.json()["id"]
    serv = ambiente["app"].state.servicos
    lat, lon = r.json()["resultado"]["rota"]["geometria"][10]
    corpo = json.dumps({"leituras": [{"id": "rt1", "ts": "2026-11-10T07:00:00Z", "lat": lat, "lon": lon}]}).encode()

    async def cenario():
        fila = serv.broker.assinar(viagem_id)
        ts = str(int(time.time()))

        def enviar():
            with serv.sessoes.nova() as db:
                return ingestao.receber(
                    db,
                    serv.cofre,
                    serv.broker,
                    serv.limitador,
                    sensor["id"],
                    corpo,
                    ts,
                    assinar(sensor["segredo"], ts, corpo),
                )

        await asyncio.to_thread(enviar)
        evento = await asyncio.wait_for(fila.get(), 2)
        serv.broker.cancelar(viagem_id, fila)
        return evento

    evento = asyncio.run(cenario())
    assert evento["tipo"] == "posicao" and evento["viagem_id"] == viagem_id and evento["status"] == "em_andamento"
    token = cli.post(f"/api/transporte/viagens/{viagem_id}/stream-token", headers=ambiente["h"](papel="leitura")).json()
    assert token["token"]
    assert cli.get(f"/api/transporte/viagens/{viagem_id}/stream?token=falso").status_code == 403
    assert cli.get(f"/api/transporte/viagens/outra/stream?token={token['token']}").status_code == 403


def test_limitador_por_sensor():
    lim = ingestao.Limitador(maximo=2, janela_s=60)
    lim.registrar("s")
    lim.registrar("s")
    try:
        lim.registrar("s")
        raise AssertionError("deveria limitar")
    except ingestao.LimiteExcedido:
        pass


def test_partida_volta_com_o_mesmo_instante_mesmo_no_sqlite(ambiente):
    _, r = _lancar(ambiente)
    det = ambiente["cli"].get(f"/api/transporte/viagens/{r.json()['id']}", headers=ambiente["h"]()).json()
    from datetime import datetime

    assert datetime.fromisoformat(det["partida_prevista"]) == datetime.fromisoformat(ROTA["partida_prevista"])
