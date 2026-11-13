"""Mapa público de alertas da Janela do Transporte: resumo da rotina, rota sem login com cache e traçado das rodovias (IBGE)."""
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
AGORA = datetime(2026, 11, 12, 15, 0, tzinfo=UTC)
ENV = {"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_ALERTAS": "1"}
# Trecho reto de teste na BR-153 entre Porangatu e Gurupi (lat, lon)
ESTRADA = (("BR-153", (((-13.4, -49.15), (-11.7, -49.07)),)),)


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


def test_resumo_publico_so_tem_a_regiao_e_separa_os_avisos_dos_proximos_dias(monkeypatch):
    monkeypatch.setattr(publico, "rodovias", lambda: ESTRADA)
    avisos = [_aviso("inmet:agora", -12.5, -49.1, "perigo"),
              _aviso("inmet:amanha", -12.5, -49.1, "grande_perigo", inicio=AGORA + timedelta(hours=12), fim=AGORA + timedelta(hours=36)),
              _aviso("inmet:sul", -29.0, -51.0),  # Rio Grande do Sul: fora da região
              _aviso("inmet:vencido", -12.5, -49.1, fim=AGORA - timedelta(minutes=1))]
    focos = [fontes.Foco(-12.0, -49.10, AGORA - timedelta(hours=3), "firms"),   # a ~1 km da estrada
             fontes.Foco(-12.0, -48.70, AGORA - timedelta(hours=3), "firms"),   # a ~40 km: conta no mapa, não na rodovia
             fontes.Foco(-12.0, -49.10, AGORA - timedelta(hours=30), "firms"),  # mais de 24 h
             fontes.Foco(-23.5, -46.6, AGORA, "firms"),                          # São Paulo: fora da região
             fontes.Foco(-12.0, -49.10, AGORA, "inpe")]                          # INPE não entra no mapa público
    r = publico.montar(_fontes(avisos, focos), AGORA)
    assert [a["id"] for a in r["avisos"]] == ["inmet:amanha", "inmet:agora"]  # mais grave primeiro
    assert {a["id"]: a["vigente"] for a in r["avisos"]} == {"inmet:amanha": False, "inmet:agora": True}
    assert len(r["focos"]) == 2 and all(len(f) == 3 for f in r["focos"])
    assert r["rodovias"] == [{"sigla": "BR-153", "avisos": ["inmet:amanha", "inmet:agora"], "gravidade": "perigo", "gravidade_proxima": "grande_perigo",
                              "proximo_inicio": (AGORA + timedelta(hours=12)).isoformat(), "focos_5km": 1}]
    assert set(r["fontes"]) == {"inmet", "firms"}
    # nada de viagem, transportadora ou motorista no resumo público
    texto = json.dumps(r)
    for proibido in ("viagem", "transportadora", "motorista", "km_ini", "telefone"):
        assert proibido not in texto


def test_resumo_publico_limita_os_focos_e_arredonda(monkeypatch):
    monkeypatch.setattr(publico, "rodovias", lambda: ())
    monkeypatch.setattr(publico, "MAX_FOCOS", 3)
    focos = [fontes.Foco(-10.123456, -48.987654, AGORA - timedelta(minutes=i), "firms") for i in range(5)]
    r = publico.montar(_fontes(focos=focos), AGORA)
    assert len(r["focos"]) == 3
    assert r["focos"][0] == [-10.12, -48.99, AGORA.strftime("%Y-%m-%dT%H:%MZ")]  # o mais recente primeiro, ~1 km


def test_rotina_grava_o_resumo_publico_mesmo_sem_viagem(monkeypatch):
    monkeypatch.setattr(publico, "rodovias", lambda: ESTRADA)
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
    (caixa,), = firms.caixas  # sem viagem, o FIRMS é pedido só para a região do mapa (com ~10 km de folga)
    assert all(abs(x - y) <= 0.1 + 1e-9 for x, y in zip(caixa, publico.REGIAO))
    reg = repo.listar(SISTEMA, "alertas_publicos")[0]
    assert reg["id"] == "atual" and reg["rodovias"][0]["gravidade"] == "perigo" and reg["rodovias"][0]["focos_5km"] == 1


def test_rota_publica_sem_login_com_cache_e_desligada_sem_flag():
    repo = RepositorioMemoria()
    app = FastAPI()
    assert api.instalar(app, ENV, repo=repo)
    cli = TestClient(app)
    r = cli.get("/api/transporte/alertas-publicos")  # sem cabeçalho de transportadora nem token
    assert r.status_code == 200 and r.json()["atualizado_em"] is None and r.json()["avisos"] == []
    assert r.headers["cache-control"] == "public, max-age=60, s-maxage=300"
    repo.inserir(SISTEMA, "alertas_publicos", {"atualizado_em": AGORA.isoformat(), "avisos": [], "focos": [[-12.0, -49.1, "x"]], "rodovias": [], "fontes": {}},
                 id_="atual")
    corpo = cli.get("/api/transporte/alertas-publicos").json()
    assert corpo["focos"] == [[-12.0, -49.1, "x"]] and "id" not in corpo and "transportadora_id" not in corpo
    desligada = FastAPI()
    api.instalar(desligada, {"ORGATEC_TRANSPORTE": "1"}, repo=repo)
    assert TestClient(desligada).get("/api/transporte/alertas-publicos").status_code == 404


def test_so_a_rota_publica_escapa_do_no_store_da_api():
    """backend/app.py manda no-store em toda a API; a exceção é só o resumo público (sem dado pessoal)."""
    from backend import app as aplicacao
    assert aplicacao.API_PUBLICA_COM_CACHE == frozenset({"/api/transporte/alertas-publicos"})


def test_mesma_regiao_no_servidor_no_gerador_e_no_mapa():
    s, w, n, e = publico.REGIAO
    assert (gerar_rodovias.SUL, gerar_rodovias.OESTE, gerar_rodovias.NORTE, gerar_rodovias.LESTE) == (s, w, n, e)
    js = (RAIZ / "site" / "assets" / "js" / "janela-transporte-mapa.js").read_text(encoding="utf-8")
    caixa = re.search(r"var CAIXA = \{ oeste: ([-\d.]+), leste: ([-\d.]+), norte: ([-\d.]+), sul: ([-\d.]+) \}", js)
    assert tuple(float(x) for x in caixa.groups()) == (w, e, n, s)


def test_tracado_das_rodovias_do_ibge_no_repositorio():
    dados = json.loads(publico.ARQUIVO_RODOVIAS.read_text(encoding="utf-8"))
    assert [r["sigla"] for r in dados["rodovias"]] == list(gerar_rodovias.RODOVIAS)
    assert "IBGE" in dados["fonte"] and "BC250" in dados["fonte"] and "simplificado" in dados["aviso"]
    s, w, n, e = publico.REGIAO
    for r in dados["rodovias"]:
        assert r["linhas"], r["sigla"]
        for linha in r["linhas"]:
            assert len(linha) >= 2 and all(s <= p[0] <= n and w <= p[1] <= e for p in linha)
    assert publico.ARQUIVO_RODOVIAS.stat().st_size < 60_000  # vai para o navegador do visitante
    assert [sigla for sigla, _ in publico.rodovias()] == list(gerar_rodovias.RODOVIAS)


def test_gerador_das_rodovias_separa_siglas_e_junta_trechos():
    assert gerar_rodovias.siglas_da("BR-153;BR-060") == {"BR-153", "BR-060"}
    assert gerar_rodovias.siglas_da("BR-153/BR-414 ") == {"BR-153", "BR-414"}
    partes = [[(0.0, 0.0), (1.0, 0.0)], [(2.0, 0.0), (1.0, 0.0)], [(5.0, 5.0), (6.0, 6.0)]]
    linhas = sorted(gerar_rodovias.juntar(partes), key=len)
    assert linhas[0] == [(5.0, 5.0), (6.0, 6.0)]
    assert sorted(linhas[1]) == [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]


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
