"""Mapa público de alertas da Janela do Transporte, Brasil inteiro: resumos nacional e por estado, rotas sem login com cache
e a malha rodoviária por estado (IBGE)."""
import json
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.transporte import api
from backend.transporte.alertas import fontes, publico, rotina
from backend.transporte.alertas.envio import SISTEMA, Envio
from backend.transporte.repositorio_transporte import RepositorioMemoria
from tools import gerar_rodovias

RAIZ = Path(__file__).resolve().parents[3]
GEO = RAIZ / "site" / "assets" / "geo"
AGORA = datetime(2026, 11, 12, 15, 0, tzinfo=UTC)
ENV = {"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_ALERTAS": "1"}
# Malha de teste: um trecho reto da BR-153 no Tocantins, uma estadual ao lado e a BR-116 no Rio Grande do Sul (lat, lon)
MALHA = {"TO": [("BR-153", (((-13.4, -49.15), (-11.7, -49.07)),)), ("TO-080", (((-10.2, -48.9), (-10.2, -48.3)),))],
         "RS": [("BR-116", (((-30.0, -51.2), (-29.2, -51.1)),))]}


def _malha(monkeypatch):
    monkeypatch.setattr(publico, "malha", lambda: publico.Malha.de(MALHA))


def _quadrado(lat, lon, lado=0.3):
    return ((lat - lado, lon - lado), (lat - lado, lon + lado), (lat + lado, lon + lado), (lat + lado, lon - lado), (lat - lado, lon - lado))


def _aviso(id_, lat, lon, gravidade="perigo", inicio=None, fim=None):
    return fontes.AlertaExterno(id=id_, origem="inmet", fonte=fontes.INMET_CREDITO, tipo="chuva", gravidade=gravidade, titulo="Chuvas Intensas",
                                inicio=inicio or AGORA - timedelta(hours=2), fim=fim or AGORA + timedelta(hours=10),
                                poligonos=(_quadrado(lat, lon),), riscos="Alagamentos.", instrucoes="Evite áreas de risco.", link="https://avisos.inmet.gov.br/1")


def _fontes(avisos=(), focos=(), estado_firms="ok"):
    inmet = fontes.ResultadoFonte("inmet", "ok", fontes.INMET_CREDITO, alertas=list(avisos))
    firms = fontes.ResultadoFonte("firms", estado_firms, fontes.FIRMS_CREDITO, focos=list(focos))
    return {"inmet": inmet, "firms": firms, "inpe": fontes.ResultadoFonte("inpe", "desligada", "inpe")}


def test_resumo_nacional_e_por_estado(monkeypatch):
    _malha(monkeypatch)
    avisos = [_aviso("inmet:agora", -12.5, -49.1, "perigo"),
              _aviso("inmet:amanha", -12.5, -49.1, "grande_perigo", inicio=AGORA + timedelta(hours=12), fim=AGORA + timedelta(hours=36)),
              _aviso("inmet:sul", -29.6, -51.15, "potencial"),
              _aviso("inmet:mar", -20.0, -20.0),  # no meio do Atlântico: fora do recorte do Brasil
              _aviso("inmet:vencido", -12.5, -49.1, fim=AGORA - timedelta(minutes=1))]
    focos = [fontes.Foco(-12.0, -49.10, AGORA - timedelta(hours=3), "firms"),   # a ~1 km da BR-153
             fontes.Foco(-12.0, -48.70, AGORA - timedelta(hours=3), "firms"),   # a ~40 km: entra na mancha, não na rodovia
             fontes.Foco(-10.21, -48.6, AGORA - timedelta(hours=1), "firms"),   # a ~1 km da TO-080
             fontes.Foco(-12.0, -49.10, AGORA - timedelta(hours=30), "firms"),  # mais de 24 h
             fontes.Foco(48.8, 2.3, AGORA, "firms"),                             # Paris: fora do recorte
             fontes.Foco(-12.0, -49.10, AGORA, "inpe")]                          # INPE não entra no mapa público
    r = publico.montar(_fontes(avisos, focos), AGORA)
    assert set(r) == {"atual", *publico.UFS}
    nac, to = r["atual"], r["TO"]
    assert [(a["id"], a["vigente"], a["ufs"]) for a in nac["avisos"]] == [("inmet:amanha", False, ["TO"]), ("inmet:agora", True, ["TO"]), ("inmet:sul", True, ["RS"])]
    assert nac["focos_total"] == 3 and sum(c[2] for c in nac["calor"]) == 3 and nac["passo_calor"] == 0.25
    assert [-12.0, -49.25, 1] in nac["calor"]  # célula de 0,25° que contém o foco junto à BR-153
    assert nac["ufs"]["TO"] == {"gravidade": "perigo", "gravidade_proxima": "grande_perigo", "focos_5km": 2, "rodovias": 2}
    assert nac["ufs"]["RS"] == {"gravidade": "potencial", "gravidade_proxima": "", "focos_5km": 0, "rodovias": 1}
    assert nac["ufs"]["GO"] == {"gravidade": "", "gravidade_proxima": "", "focos_5km": 0, "rodovias": 0}
    assert set(nac["fontes"]) == {"inmet", "firms"}
    assert to["rodovias"] == [
        {"sigla": "BR-153", "avisos": ["inmet:amanha", "inmet:agora"], "gravidade": "perigo", "gravidade_proxima": "grande_perigo",
         "proximo_inicio": (AGORA + timedelta(hours=12)).isoformat(), "focos_5km": 1},
        {"sigla": "TO-080", "avisos": [], "gravidade": "", "gravidade_proxima": "", "proximo_inicio": None, "focos_5km": 1}]
    assert sorted(to["focos_perto"]) == [[-12.0, -49.1], [-10.21, -48.6]] and to["focos_5km"] == 2
    assert r["GO"]["rodovias"] == [] and r["GO"]["focos_perto"] == []
    # nada de viagem, transportadora ou motorista nos resumos públicos
    texto = json.dumps(r)
    for proibido in ("viagem", "transportadora", "motorista", "km_ini", "telefone"):
        assert proibido not in texto


def test_aviso_que_corta_so_o_meio_de_um_trecho_reto_conta(monkeypatch):
    _malha(monkeypatch)
    r = publico.montar(_fontes([_aviso("inmet:meio", -12.55, -49.11)]), AGORA)  # longe das duas pontas do trecho
    assert r["TO"]["rodovias"][0]["sigla"] == "BR-153" and r["atual"]["avisos"][0]["ufs"] == ["TO"]


def test_focos_por_estado_tem_limite_mas_a_contagem_usa_todos(monkeypatch):
    _malha(monkeypatch)
    monkeypatch.setattr(publico, "MAX_FOCOS_UF", 3)
    focos = [fontes.Foco(-12.0 - i * 0.001, -49.10, AGORA - timedelta(minutes=i), "firms") for i in range(8)]
    r = publico.montar(_fontes(focos=focos), AGORA)
    assert len(r["TO"]["focos_perto"]) == 3 and r["TO"]["focos_perto"][0] == [-12.0, -49.1]  # os mais recentes
    assert r["TO"]["focos_5km"] == 8 and r["TO"]["rodovias"][0]["focos_5km"] == 8 and r["atual"]["ufs"]["TO"]["focos_5km"] == 8


def test_rotina_grava_os_resumos_mesmo_sem_viagem(monkeypatch):
    _malha(monkeypatch)
    repo = RepositorioMemoria()

    class Fonte:
        def __init__(self, origem, itens):
            self.origem, self.credito, self.itens, self.caixas = origem, origem, itens, []

        def buscar(self, *a):
            self.caixas.append(a)
            return self.itens

    inmet = Fonte("inmet", [_aviso("inmet:1", -12.5, -49.1)])
    firms = Fonte("firms", [fontes.Foco(-12.0, -49.1, AGORA, "firms")])
    cfg = rotina.Configuracao(inmet, firms, None, Envio(repo, None, None, Decimal("50")), {"inpe": "desligada"})
    resumo = rotina.executar(repo, cfg, AGORA)
    assert resumo["viagens"] == 0 and resumo["publico"] == {"avisos": 1, "focos": 1}
    (caixa,), = firms.caixas  # sem viagem, o FIRMS é pedido para o Brasil (com ~10 km de folga)
    assert all(abs(x - y) <= 0.1 + 1e-9 for x, y in zip(caixa, publico.REGIAO))
    assert repo.obter(SISTEMA, "alertas_publicos", "atual")["ufs"]["TO"]["gravidade"] == "perigo"
    assert repo.obter(SISTEMA, "alertas_publicos", "TO")["rodovias"][0]["focos_5km"] == 1
    assert len(repo.listar(SISTEMA, "alertas_publicos")) == 28  # nacional + 27 estados


def test_rotas_publicas_sem_login_com_cache_e_desligadas_sem_flag():
    repo = RepositorioMemoria()
    app = FastAPI()
    assert api.instalar(app, ENV, repo=repo)
    cli = TestClient(app)
    r = cli.get("/api/transporte/alertas-publicos")  # sem cabeçalho de transportadora nem token
    assert r.status_code == 200 and r.json()["atualizado_em"] is None and r.json()["avisos"] == []
    assert r.headers["cache-control"] == "public, max-age=60, s-maxage=300"
    vazio = cli.get("/api/transporte/alertas-publicos/GO")
    assert vazio.status_code == 200 and vazio.json() == {"atualizado_em": None, "uf": "GO", "rodovias": [], "focos_perto": [], "fontes": {}}
    repo.inserir(SISTEMA, "alertas_publicos", {"atualizado_em": AGORA.isoformat(), "avisos": [], "calor": [[-12.0, -49.25, 1]], "ufs": {}, "fontes": {}}, id_="atual")
    repo.inserir(SISTEMA, "alertas_publicos", {"atualizado_em": AGORA.isoformat(), "uf": "GO", "rodovias": [{"sigla": "BR-153"}], "focos_perto": []}, id_="GO")
    corpo = cli.get("/api/transporte/alertas-publicos").json()
    assert corpo["calor"] == [[-12.0, -49.25, 1]] and "id" not in corpo and "transportadora_id" not in corpo
    go = cli.get("/api/transporte/alertas-publicos/GO")
    assert go.json()["rodovias"] == [{"sigla": "BR-153"}] and "id" not in go.json() and go.headers["cache-control"] == "public, max-age=60, s-maxage=300"
    for invalido in ("XX", "go", "atual", "_sistema"):
        assert cli.get(f"/api/transporte/alertas-publicos/{invalido}").status_code == 404
    desligada = FastAPI()
    api.instalar(desligada, {"ORGATEC_TRANSPORTE": "1"}, repo=repo)
    assert TestClient(desligada).get("/api/transporte/alertas-publicos").status_code == 404
    assert TestClient(desligada).get("/api/transporte/alertas-publicos/GO").status_code == 404


def test_so_as_rotas_publicas_escapam_do_no_store_da_api():
    """backend/app.py manda no-store em toda a API; a exceção é só o resumo público (sem dado pessoal), nacional e por estado."""
    from backend import app as aplicacao
    assert aplicacao._publica_com_cache("/api/transporte/alertas-publicos")
    assert aplicacao._publica_com_cache("/api/transporte/alertas-publicos/GO")
    for outro in ("/api/transporte/alertas-publicos/go", "/api/transporte/alertas-publicos/GO/x", "/api/transporte/alertas-publicosX",
                  "/api/transporte/alertas-rota", "/api/transporte/viagens", "/api/transporte/alertas-publicos/"):
        assert not aplicacao._publica_com_cache(outro), outro


def test_mesmo_recorte_do_brasil_no_servidor_e_no_mapa():
    s, w, n, e = publico.REGIAO
    js = (RAIZ / "site" / "assets" / "js" / "janela-transporte-mapa.js").read_text(encoding="utf-8")
    caixa = re.search(r"var BRASIL = \{ oeste: ([-\d.]+), leste: ([-\d.]+), norte: ([-\d.]+), sul: ([-\d.]+) \}", js)
    assert tuple(float(x) for x in caixa.groups()) == (w, e, n, s)
    assert publico.UFS == gerar_rodovias.UFS and len(publico.UFS) == 27


def test_malha_do_ibge_no_repositorio_cobre_os_27_estados():
    ufs = json.loads((GEO / "ufs.json").read_text(encoding="utf-8"))
    assert [e["uf"] for e in ufs["ufs"]] == list(publico.UFS) and "IBGE" in ufs["fonte"]
    s, w, n, e = publico.REGIAO
    for est in ufs["ufs"]:
        cs, cw, cn, ce = est["caixa"]
        assert s <= cs < cn <= n and w <= cw < ce <= e and est["aneis"] and est["nome"], est["uf"]
    total = 0
    for uf in publico.UFS:
        dados = json.loads((GEO / "rodovias" / f"{uf}.json").read_text(encoding="utf-8"))
        assert dados["uf"] == uf and "BC250" in dados["fonte"] and "simplificado" in dados["aviso"]
        assert any(r["sigla"].startswith("BR-") for r in dados["rodovias"]), uf
        for r in dados["rodovias"]:
            assert re.fullmatch(r"[A-Z]{2,3}-\d{3}", r["sigla"]), r["sigla"]
            assert all(len(linha) >= 2 for linha in r["linhas"])
        locais = GEO / "rodovias" / f"{uf}-locais.json"
        assert json.loads(locais.read_text(encoding="utf-8"))["uf"] == uf
        for arquivo in (GEO / "rodovias" / f"{uf}.json", locais):
            assert arquivo.stat().st_size < 600_000, arquivo.name  # vai para o navegador do visitante, um estado por vez
            total += arquivo.stat().st_size
    federais = json.loads((GEO / "rodovias" / "BR.json").read_text(encoding="utf-8"))
    assert len(federais["rodovias"]) > 100 and (GEO / "rodovias" / "BR.json").stat().st_size < 150_000
    assert (GEO / "ufs.json").stat().st_size < 200_000 and total < 6_000_000
    go = json.loads((GEO / "rodovias" / "GO.json").read_text(encoding="utf-8"))
    assert {"BR-153", "BR-060"} <= {r["sigla"] for r in go["rodovias"]}
    m = publico.malha.__wrapped__()
    assert len(m.rodovias) > 2500 and {r.uf for r in m.rodovias} == set(publico.UFS)


def test_gerador_das_rodovias_separa_siglas_e_junta_trechos():
    assert gerar_rodovias.siglas_da("BR-153;BR-060") == {"BR-153", "BR-060"}
    assert gerar_rodovias.siglas_da("BR-153/go-414 ") == {"BR-153", "GO-414"}
    assert gerar_rodovias.siglas_da("156BAP0170") == {"BR-156"} and gerar_rodovias.siglas_da("170EMG0280") == {"MG-170"}  # código do SNV
    assert gerar_rodovias.siglas_da("BR-430 BA-464") == {"BR-430", "BA-464"} and gerar_rodovias.siglas_da("Rodovia MG-403") == {"MG-403"}
    assert gerar_rodovias.siglas_da("LMG 628") == {"LMG-628"} and gerar_rodovias.siglas_da("MG132") == {"MG-132"} and gerar_rodovias.siglas_da("900AMG2040") == set()
    assert gerar_rodovias.siglas_da("Rodovia dos Bandeirantes") == set() and gerar_rodovias.siglas_da("900") == set() and gerar_rodovias.siglas_da("") == set()
    partes = [[(0.0, 0.0), (1.0, 0.0)], [(2.0, 0.0), (1.0, 0.0)], [(5.0, 5.0), (6.0, 6.0)], [(2.0, 0.0), (3.0, 0.0)]]
    linhas = sorted(gerar_rodovias.juntar(partes), key=len)
    assert linhas[0] in ([(5.0, 5.0), (6.0, 6.0)], [(6.0, 6.0), (5.0, 5.0)])
    assert linhas[1] in ([(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)], [(3.0, 0.0), (2.0, 0.0), (1.0, 0.0), (0.0, 0.0)])


def test_firms_pede_dois_dias_para_nao_zerar_na_virada_do_dia_utc():
    """No FIRMS, 1 dia é só o dia corrente em UTC: às 21h de Brasília o mapa ficava sem nenhum foco, com a fonte "ok"."""
    assert fontes.FIRMS_URL.endswith("/2")


def test_inmet_manda_riscos_e_instrucoes_como_lista_de_frases():
    """Formato real de apiprevmet3 (conferido em 12/11/2026): a tela e a mensagem ao motorista mostravam "['...', '...']"."""
    bruto = {"hoje": [{"id": 1, "descricao": "Tempestade", "severidade": "Perigo Potencial", "inicio": "2026-11-12 08:50", "fim": "2026-11-12 23:59",
                       "encerrado": False, "poligono": '{"type":"Polygon","coordinates":[[[-49,-12],[-48,-12],[-48,-11],[-49,-12]]]}',
                       "riscos": ["Chuva de até 50 mm/dia. ", "Ventos de 40 a 60 km/h."], "instrucoes": ["Não se abrigue debaixo de árvores. ", "Ligue 199."]}],
             "futuro": []}
    aviso = fontes.interpretar_inmet(bruto)[0]
    assert aviso.riscos == "Chuva de até 50 mm/dia. Ventos de 40 a 60 km/h."
    assert aviso.instrucoes == "Não se abrigue debaixo de árvores. Ligue 199."
