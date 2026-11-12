"""Alertas de clima e desastres na rota: fontes, cruzamento com a rota e a posição, rotina, envio com teto e API."""

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.transporte import api
from backend.transporte.alertas import cruzamento as cz
from backend.transporte.alertas import fontes, rotina
from backend.transporte.alertas.envio import Envio, SmsZenvia, WhatsAppCloud, id_comunicacao
from backend.transporte.erros import ErroProvedor, ProvedorRespostaInvalida, RecursoDesligado
from backend.transporte.provedores.http import ClienteHttp
from backend.transporte.repositorio_transporte import RepositorioMemoria

ENV = {"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_ALERTAS": "1", "ORGATEC_TRANSPORTE_WHATSAPP_VERIFICACAO": "verif-123",
       "ORGATEC_TRANSPORTE_WHATSAPP_APP_SEGREDO": "segredo-app"}
VEICULO = {"placa": "ABC1D23", "eixos": 5, "consumo_km_l_carregado": 2.5, "consumo_km_l_vazio": 3.2, "tanque_l": 600}
PONTOS = [{"nome": "Goiânia", "uf": "GO"}, {"nome": "Palmas", "uf": "TO"}]
AGORA = datetime.now(UTC).replace(microsecond=0)


# ---------- ambiente ----------
@pytest.fixture
def amb():
    repo = RepositorioMemoria()
    a, b = repo.criar_transportadora(), repo.criar_transportadora()
    app = FastAPI()
    assert api.instalar(app, ENV, repo=repo)
    cli = TestClient(app)

    def h(tid=a, papel="gestor", usuario="u-gestor"):
        return {"X-Transportadora-Id": tid, "X-Usuario-Papel": papel, "X-Usuario-Id": usuario}

    veiculo = cli.post("/api/transporte/veiculos", json=VEICULO, headers=h()).json()["id"]
    motorista = cli.post("/api/transporte/motoristas", json={"nome": "Motorista Um", "usuario_id": "u-mot"}, headers=h()).json()["id"]
    return {"cli": cli, "a": a, "b": b, "h": h, "repo": repo, "veiculo": veiculo, "motorista": motorista}


def _viagem(amb, partida, status=None):
    corpo = {"veiculo_id": amb["veiculo"], "motorista_id": amb["motorista"], "pontos": PONTOS, "partida_prevista": partida.isoformat(), "carregado": True}
    r = amb["cli"].post("/api/transporte/viagens", json=corpo, headers=amb["h"]())
    assert r.status_code == 201, r.text
    v = r.json()
    if status:
        amb["repo"].atualizar(amb["a"], "viagens", v["id"], {"status": status})
    return amb["repo"].obter(amb["a"], "viagens", v["id"])


def _consentir(amb, canais=("whatsapp", "sms")):
    corpo = {"telefone": "(62) 99999-1234", "canais": list(canais), "consentimento_do_motorista": True, "versao_termo": "alertas-rota-2026-11-11"}
    r = amb["cli"].put(f"/api/transporte/motoristas/{amb['motorista']}/contato", json=corpo, headers=amb["h"]())
    assert r.status_code == 200, r.text


def _quadrado(lat, lon, lado=0.3):
    return ((lat - lado, lon - lado), (lat - lado, lon + lado), (lat + lado, lon + lado), (lat + lado, lon - lado), (lat - lado, lon - lado))


def _aviso(v, km_frac=0.5, gravidade="perigo", inicio=None, fim=None, id_="inmet:1"):
    geo = v["resultado"]["rota"]["geometria"]
    lat, lon = geo[int(len(geo) * km_frac)]
    return fontes.AlertaExterno(id=id_, origem="inmet", fonte=fontes.INMET_CREDITO, tipo="tempestade", gravidade=gravidade,
                                titulo="Tempestade (Perigo)", inicio=inicio or AGORA - timedelta(hours=1), fim=fim or AGORA + timedelta(days=3),
                                poligonos=(_quadrado(lat, lon),), instrucoes="Evite enfrentar o mau tempo.", link="https://avisos.inmet.gov.br/1")


class FonteFalsa:
    def __init__(self, origem, alertas=None, focos=None, falha=False):
        self.origem, self.credito, self.alertas, self.focos, self.falha = origem, origem, alertas or [], focos or [], falha

    def buscar(self, *_a):
        if self.falha:
            raise ErroProvedor(self.origem, "fora do ar")
        return self.focos if self.origem != "inmet" else self.alertas


class CanalFalso:
    def __init__(self, nome, custo="0.05", falha=False):
        self.nome, self.custo_brl, self.falha, self.enviadas = nome, Decimal(custo), falha, []

    def enviar(self, telefone, partes, texto):
        if self.falha:
            raise ErroProvedor(self.nome, "recusado")
        self.enviadas.append((telefone, partes, texto))
        return f"wamid.{self.nome}.{len(self.enviadas)}"


def _cfg(repo, inmet=None, firms=None, whatsapp=None, sms=None, teto="50"):
    return rotina.Configuracao(inmet or FonteFalsa("inmet"), firms, None, Envio(repo, whatsapp, sms, Decimal(teto)), {"inpe": "desligada"})


# ---------- fontes ----------
INMET_JSON = {"hoje": [
    {"id": 10, "descricao": "Tempestade", "severidade": "Perigo", "inicio": "2026-11-12 00:01", "fim": "2026-11-12 23:59", "encerrado": False,
     "poligono": json.dumps({"type": "Polygon", "coordinates": [[[-49.5, -16.9], [-49.0, -16.9], [-49.0, -16.4], [-49.5, -16.4], [-49.5, -16.9]]]}),
     "riscos": "Ventos de 60 km/h.", "instrucoes": "Evite o mau tempo."},
    {"id": 11, "descricao": "Geada", "severidade": "Grande Perigo", "inicio": "2026-11-12 00:01", "fim": "2026-11-12 08:00", "encerrado": True,
     "poligono": "{}"}],
    "futuro": [{"id": 12, "descricao": "Acumulado de Chuva", "severidade": "Perigo Potencial", "inicio": "2026-11-13 00:01", "fim": "2026-11-13 23:59",
                "poligono": {"type": "MultiPolygon", "coordinates": [[[[-48, -10], [-47, -10], [-47, -9], [-48, -10]]],
                                                                     [[[-46, -8], [-45, -8], [-45, -7], [-46, -8]]]]}}]}


def test_inmet_normaliza_area_hora_tipo_e_gravidade():
    avisos = fontes.interpretar_inmet(INMET_JSON)
    assert [a.id for a in avisos] == ["inmet:10", "inmet:12"]  # o encerrado fica de fora
    t = avisos[0]
    assert (t.tipo, t.gravidade, t.link) == ("tempestade", "perigo", "https://avisos.inmet.gov.br/10")
    assert t.inicio == datetime(2026, 11, 12, 3, 1, tzinfo=UTC)  # horário de Brasília convertido para UTC
    assert t.poligonos[0][0] == (-16.9, -49.5)  # GeoJSON (lon, lat) virou (lat, lon)
    assert avisos[1].tipo == "chuva" and avisos[1].gravidade == "potencial" and len(avisos[1].poligonos) == 2


def test_inmet_formato_inesperado_vira_erro_de_fonte():
    with pytest.raises(ProvedorRespostaInvalida):
        fontes.interpretar_inmet(["nada"])


def test_firms_le_csv_e_recusa_chave_invalida():
    csv = "latitude,longitude,bright_ti4,acq_date,acq_time,satellite\n-10.1,-48.3,330,2026-11-11,1342,N20\n"
    f = fontes.interpretar_firms(csv)[0]
    assert (f.lat, f.lon, f.quando, f.origem) == (-10.1, -48.3, datetime(2026, 11, 11, 13, 42, tzinfo=UTC), "firms")
    with pytest.raises(ProvedorRespostaInvalida):
        fontes.interpretar_firms("Invalid MAP_KEY.")


def test_inpe_le_so_os_arquivos_novos():
    listagem = '<a href="focos_10min_20261111_2300.csv">x</a><a href="focos_10min_20261111_2310.csv">y</a>'
    corpo = "lat,lon,satelite,data\n -10.5, -48.2,AQUA_M-T,2026-11-11 20:29:00\n"
    pedidos = []

    def responder(req):
        pedidos.append(str(req.url))
        return httpx.Response(200, text=listagem if req.url.path.endswith("/10min/") else corpo)

    inpe = fontes.FocosInpe(ClienteHttp("inpe", transporte=httpx.MockTransport(responder)))
    focos, marca = inpe.buscar("focos_10min_20261111_2300.csv")
    assert marca == "focos_10min_20261111_2310.csv" and len(focos) == 1 and focos[0].quando.hour == 20
    assert not any(p.endswith("2300.csv") for p in pedidos)


# ---------- cruzamento ----------
def test_aviso_no_meio_da_rota_afeta_viagem_planejada_com_trecho_e_hora(amb):
    v = _viagem(amb, AGORA + timedelta(hours=2))
    rota = cz.preparar(amb["a"], v, None, AGORA)
    af = cz.cruzar_area(rota, _aviso(v))
    assert af and af["grupo"] == "planejada" and 0 < af["km_ini"] <= af["km_fim"] < v["resultado"]["rota"]["distancia_km"]
    assert datetime.fromisoformat(af["chegada_prevista"]) > AGORA + timedelta(hours=2) and af["avisar_motorista"]


def test_aviso_vencido_antes_da_passagem_nao_afeta(amb):
    v = _viagem(amb, AGORA + timedelta(hours=2))
    rota = cz.preparar(amb["a"], v, None, AGORA)
    assert cz.cruzar_area(rota, _aviso(v, fim=AGORA + timedelta(hours=1))) is None


def test_viagem_planejada_alem_de_72h_fica_fora(amb):
    v = _viagem(amb, AGORA + timedelta(hours=80))
    assert cz.preparar(amb["a"], v, None, AGORA) is None


def test_trecho_ja_percorrido_nao_gera_alerta_e_atraso_da_telemetria_desloca_a_hora(amb):
    v = _viagem(amb, AGORA - timedelta(hours=3), status="em_andamento")
    geo = v["resultado"]["rota"]["geometria"]
    meio = geo[len(geo) // 2]
    leitura = {"lat": meio[0], "lon": meio[1], "ts": AGORA}
    rota = cz.preparar(amb["a"], v, leitura, AGORA)
    assert rota.grupo == "trajeto" and rota.posicao_fonte == "telemetria"
    assert cz.cruzar_area(rota, _aviso(v, km_frac=0.2)) is None  # ficou para trás
    af = cz.cruzar_area(rota, _aviso(v, km_frac=0.8))
    previsto = rota.plano.tempo_no_km(af["km_ini"])
    assert rota.atraso < timedelta(0)  # o caminhão está adiantado em relação ao plano
    assert abs(datetime.fromisoformat(af["chegada_prevista"]) - (previsto + rota.atraso)) < timedelta(minutes=1)  # km arredondado


def test_focos_perto_da_rota_viram_um_alerta_por_faixa_e_focos_distantes_ou_velhos_ficam_de_fora(amb):
    v = _viagem(amb, AGORA - timedelta(minutes=30), status="em_andamento")
    rota = cz.preparar(amb["a"], v, None, AGORA)
    geo = v["resultado"]["rota"]["geometria"]
    p = geo[3]
    focos = [fontes.Foco(p[0] + 0.01, p[1], AGORA - timedelta(hours=1), "firms"), fontes.Foco(p[0], p[1] + 0.01, AGORA, "inpe"),
             fontes.Foco(p[0] + 1.0, p[1] + 1.0, AGORA, "firms"), fontes.Foco(p[0], p[1], AGORA - timedelta(hours=20), "firms")]
    afs = cz.cruzar_focos(rota, focos, AGORA)
    assert len(afs) == 1
    a = afs[0]["alerta"]
    assert a["tipo"] == "fogo" and a["titulo"].startswith("2 foco") and "NASA FIRMS" in a["fonte"] and "INPE" in a["fonte"]


# ---------- rotina e envio ----------
def test_rotina_avisa_uma_vez_e_de_novo_so_quando_a_gravidade_sobe(amb):
    repo = amb["repo"]
    _consentir(amb)
    v = _viagem(amb, AGORA + timedelta(hours=1))
    wa = CanalFalso("whatsapp")
    cfg = _cfg(repo, inmet=FonteFalsa("inmet", [_aviso(v)]), whatsapp=wa)
    r = rotina.executar(repo, cfg, AGORA)
    assert r["afetacoes"] == 1 and r["mensagens"] == 1 and wa.enviadas[0][0] == "+5562999991234"
    assert "Tempestade (perigo)" in wa.enviadas[0][1][0]
    rotina.executar(repo, cfg, AGORA + timedelta(minutes=15))
    assert len(wa.enviadas) == 1  # mesmo alerta, mesma gravidade: não repete
    cfg.inmet.alertas = [_aviso(v, gravidade="grande_perigo")]
    rotina.executar(repo, cfg, AGORA + timedelta(minutes=30))
    assert len(wa.enviadas) == 2
    com = repo.listar(amb["a"], "comunicacoes")
    assert {c["estado"] for c in com} == {"enviada"} and all(c["destino"].endswith("1234") and "99999" not in c["destino"] for c in com)


def test_potencial_fica_so_no_painel(amb):
    repo = amb["repo"]
    _consentir(amb)
    v = _viagem(amb, AGORA + timedelta(hours=1))
    wa = CanalFalso("whatsapp")
    rotina.executar(repo, _cfg(repo, inmet=FonteFalsa("inmet", [_aviso(v, gravidade="potencial")]), whatsapp=wa), AGORA)
    assert not wa.enviadas and repo.listar(amb["a"], "alertas_rota")[0]["estado"] == "ativo"


def test_sem_consentimento_nada_e_enviado_e_fica_registrado(amb):
    repo = amb["repo"]
    v = _viagem(amb, AGORA + timedelta(hours=1))
    wa = CanalFalso("whatsapp")
    rotina.executar(repo, _cfg(repo, inmet=FonteFalsa("inmet", [_aviso(v)]), whatsapp=wa), AGORA)
    assert not wa.enviadas and repo.listar(amb["a"], "comunicacoes")[0]["estado"] == "sem_consentimento"


def test_teto_mensal_bloqueia_o_envio(amb):
    repo = amb["repo"]
    _consentir(amb)
    v = _viagem(amb, AGORA + timedelta(hours=1))
    wa = CanalFalso("whatsapp", custo="0.05")
    rotina.executar(repo, _cfg(repo, inmet=FonteFalsa("inmet", [_aviso(v)]), whatsapp=wa, teto="0.04"), AGORA)
    assert not wa.enviadas and repo.listar(amb["a"], "comunicacoes")[0]["estado"] == "bloqueada_teto"


def test_fonte_fora_do_ar_nao_encerra_alerta_e_fonte_ok_sem_aviso_encerra(amb):
    repo = amb["repo"]
    v = _viagem(amb, AGORA + timedelta(hours=1))
    inmet = FonteFalsa("inmet", [_aviso(v)])
    cfg = _cfg(repo, inmet=inmet)
    rotina.executar(repo, cfg, AGORA)
    inmet.falha = True
    rotina.executar(repo, cfg, AGORA + timedelta(minutes=15))
    estado = repo.listar(amb["a"], "alertas_estado")[0]["fontes"]
    assert repo.listar(amb["a"], "alertas_rota")[0]["estado"] == "ativo" and estado["inmet"]["estado"] == "indisponivel"
    inmet.falha, inmet.alertas = False, []
    rotina.executar(repo, cfg, AGORA + timedelta(minutes=30))
    assert repo.listar(amb["a"], "alertas_rota")[0]["estado"] == "encerrado"


def test_sms_de_reserva_so_para_grande_perigo_sem_entrega_em_15_min(amb):
    repo = amb["repo"]
    _consentir(amb)
    v = _viagem(amb, AGORA + timedelta(hours=1))
    wa, sms = CanalFalso("whatsapp"), CanalFalso("sms", custo="0.10")
    cfg = _cfg(repo, inmet=FonteFalsa("inmet", [_aviso(v, gravidade="grande_perigo")]), whatsapp=wa, sms=sms)
    rotina.executar(repo, cfg, AGORA)
    rotina.executar(repo, cfg, AGORA + timedelta(minutes=10))
    assert not sms.enviadas
    rotina.executar(repo, cfg, AGORA + timedelta(minutes=16))
    assert len(sms.enviadas) == 1 and sms.enviadas[0][2].isascii()
    rotina.executar(repo, cfg, AGORA + timedelta(minutes=31))
    assert len(sms.enviadas) == 1  # uma reserva por mensagem


def test_whatsapp_entregue_dispensa_o_sms(amb):
    repo = amb["repo"]
    _consentir(amb)
    v = _viagem(amb, AGORA + timedelta(hours=1))
    wa, sms = CanalFalso("whatsapp"), CanalFalso("sms")
    cfg = _cfg(repo, inmet=FonteFalsa("inmet", [_aviso(v, gravidade="grande_perigo")]), whatsapp=wa, sms=sms)
    rotina.executar(repo, cfg, AGORA)
    com = repo.listar(amb["a"], "comunicacoes")[0]
    repo.atualizar(amb["a"], "comunicacoes", com["id"], {"estado": "entregue"})
    rotina.executar(repo, cfg, AGORA + timedelta(minutes=20))
    assert not sms.enviadas


def test_retencao_tira_coordenadas_e_anonimiza_comunicacoes_antigas(amb):
    repo = amb["repo"]
    _consentir(amb)
    v = _viagem(amb, AGORA + timedelta(hours=1))
    rotina.executar(repo, _cfg(repo, inmet=FonteFalsa("inmet", [_aviso(v)]), whatsapp=CanalFalso("whatsapp")), AGORA)
    rotina.reter(repo, amb["a"], AGORA + timedelta(days=181))
    a = repo.listar(amb["a"], "alertas_rota")[0]
    c = repo.listar(amb["a"], "comunicacoes")[0]
    assert a["lat"] is None and a["estado"] == "arquivado" and c["texto"] == "" and c["destino"] == "" and c["estado"] == "enviada"


def test_configurar_recusa_whatsapp_sem_token_e_desliga_firms_sem_chave():
    repo = RepositorioMemoria()
    with pytest.raises(RecursoDesligado):
        rotina.configurar({"ORGATEC_TRANSPORTE_WHATSAPP": "1"}, repo)
    cfg = rotina.configurar({}, repo)
    assert cfg.firms is None and "firms" in cfg.desligadas and "inpe" in cfg.desligadas and cfg.envio.whatsapp is None


def test_whatsapp_e_sms_montam_o_pedido_documentado():
    pedidos = []

    def responder(req):
        pedidos.append(req)
        if "graph.facebook.com" in str(req.url):
            return httpx.Response(200, json={"messages": [{"id": "wamid.ABC"}]})
        return httpx.Response(200, json={"id": "zen-1"})

    t = httpx.MockTransport(responder)
    wa = WhatsAppCloud(ClienteHttp("whatsapp", transporte=t), "tok", "123", "alerta_rota")
    assert wa.enviar("+5562999991234", ["a", "b"], "texto") == "wamid.ABC"
    corpo = json.loads(pedidos[0].content)
    assert str(pedidos[0].url) == "https://graph.facebook.com/v27.0/123/messages" and pedidos[0].headers["Authorization"] == "Bearer tok"
    assert corpo["to"] == "5562999991234" and corpo["template"]["language"]["code"] == "pt_BR"
    assert [p["text"] for p in corpo["template"]["components"][0]["parameters"]] == ["a", "b"]
    sms = SmsZenvia(ClienteHttp("sms", transporte=t), "ztok", "ORGATEC")
    assert sms.enviar("+5562999991234", [], "oi") == "zen-1"
    assert pedidos[1].headers["X-API-TOKEN"] == "ztok" and json.loads(pedidos[1].content)["contents"] == [{"type": "text", "text": "oi"}]


# ---------- API ----------
def test_api_desligada_sem_flag():
    repo = RepositorioMemoria()
    tid = repo.criar_transportadora()
    app = FastAPI()
    api.instalar(app, {"ORGATEC_TRANSPORTE": "1"}, repo=repo)
    r = TestClient(app).get("/api/transporte/alertas-rota", headers={"X-Transportadora-Id": tid, "X-Usuario-Papel": "gestor"})
    assert r.status_code == 404


def test_api_lista_alertas_com_fontes_e_respeita_motorista_e_transportadora(amb):
    repo = amb["repo"]
    v = _viagem(amb, AGORA + timedelta(hours=1))
    rotina.executar(repo, _cfg(repo, inmet=FonteFalsa("inmet", [_aviso(v)])), AGORA)
    cli, h = amb["cli"], amb["h"]
    r = cli.get(f"/api/transporte/alertas-rota?viagem_id={v['id']}", headers=h()).json()
    assert len(r["alertas"]) == 1 and r["fontes"]["inmet"]["estado"] == "ok" and r["fontes"]["inpe"]["estado"] == "desligada"
    assert cli.get("/api/transporte/alertas-rota", headers=h(papel="motorista", usuario="u-mot")).json()["alertas"]
    assert not cli.get("/api/transporte/alertas-rota", headers=h(papel="motorista", usuario="outro")).json()["alertas"]
    assert not cli.get("/api/transporte/alertas-rota", headers=h(tid=amb["b"])).json()["alertas"]
    assert cli.get(f"/api/transporte/alertas-rota?viagem_id={v['id']}", headers=h(tid=amb["b"])).status_code == 404
    aid = r["alertas"][0]["id"]
    assert cli.post(f"/api/transporte/alertas-rota/{aid}/visto", headers=h(papel="motorista", usuario="u-mot")).status_code == 403
    assert cli.post(f"/api/transporte/alertas-rota/{aid}/visto", headers=h()).json()["visto"] is True


def test_contato_exige_consentimento_e_revogacao_apaga_o_telefone(amb):
    cli, h, url = amb["cli"], amb["h"], f"/api/transporte/motoristas/{amb['motorista']}/contato"
    sem = {"telefone": "62999991234", "canais": ["whatsapp"], "consentimento_do_motorista": False, "versao_termo": "alertas-rota-2026-11-11"}
    assert cli.put(url, json=sem, headers=h()).status_code == 422
    assert cli.put(url, json={**sem, "consentimento_do_motorista": True, "telefone": "123"}, headers=h()).status_code == 422
    assert cli.put(url, json={**sem, "consentimento_do_motorista": True}, headers=h(papel="motorista", usuario="u-mot")).status_code == 403
    assert cli.put(url, json={**sem, "consentimento_do_motorista": True}, headers=h()).json()["alertas_canais"] == ["whatsapp"]
    assert amb["repo"].obter(amb["a"], "motoristas", amb["motorista"])["contato"]["telefone"] == "+5562999991234"
    assert cli.delete(url, headers=h()).status_code == 200
    m = amb["repo"].obter(amb["a"], "motoristas", amb["motorista"])
    assert m["contato"] is None and m["contato_revogado_em"]


def _assinado(corpo: bytes, segredo="segredo-app"):
    return {"X-Hub-Signature-256": "sha256=" + hmac.new(segredo.encode(), corpo, hashlib.sha256).hexdigest(), "Content-Type": "application/json"}


def test_webhook_whatsapp_verifica_token_assinatura_e_nao_regride_estado(amb):
    cli, repo = amb["cli"], amb["repo"]
    url = "/api/transporte/whatsapp/webhook"
    ok = cli.get(url, params={"hub.mode": "subscribe", "hub.verify_token": "verif-123", "hub.challenge": "42"})
    assert ok.status_code == 200 and ok.text == "42"
    assert cli.get(url, params={"hub.mode": "subscribe", "hub.verify_token": "errado", "hub.challenge": "42"}).status_code == 403
    _consentir(amb)
    v = _viagem(amb, AGORA + timedelta(hours=1))
    rotina.executar(repo, _cfg(repo, inmet=FonteFalsa("inmet", [_aviso(v)]), whatsapp=CanalFalso("whatsapp")), AGORA)

    def evento(status):
        return json.dumps({"entry": [{"changes": [{"value": {"statuses": [{"id": "wamid.whatsapp.1", "status": status, "timestamp": "1700000000"}]}}]}]}).encode()

    corpo = evento("read")
    assert cli.post(url, content=corpo, headers=_assinado(corpo, "outro")).status_code == 403
    assert cli.post(url, content=corpo, headers=_assinado(corpo)).json() == {"atualizados": 1}
    corpo = evento("delivered")
    cli.post(url, content=corpo, headers=_assinado(corpo))
    com = repo.obter(amb["a"], "comunicacoes", id_comunicacao("whatsapp", "wamid.whatsapp.1"))
    assert com["estado"] == "lida" and [x["estado"] for x in com["historico"]] == ["enviada", "lida", "entregue"]
    lista = cli.get(f"/api/transporte/comunicacoes?viagem_id={v['id']}", headers=amb["h"]()).json()
    assert lista[0]["estado"] == "lida" and "99999" not in json.dumps(lista)
