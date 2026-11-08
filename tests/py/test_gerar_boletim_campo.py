"""Gerador da Janela de Campo (tools/gerar_boletim_campo.py) sem rede: a previsão vem da resposta gravada do
MET Norway em tests/fixtures/campo. Precisa do Node.js (a montagem usa site/assets/js/campo-regras.js)."""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import gerar_boletim_campo as G  # noqa: E402

MET = json.loads((RAIZ / "tests" / "fixtures" / "campo" / "met-rio-verde.json").read_text(encoding="utf-8"))
AGORA = datetime(2026, 11, 2, 11, 2, tzinfo=G.BRASILIA)
pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="Node.js ausente")


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(G.time, "sleep", lambda s: None)


def amostra(polo, cliente, agora):
    return MET


def test_gera_boletim_valido_e_grava_atual_dia_e_indice(tmp_path):
    b = G.gerar(AGORA, buscar=amostra, destino=tmp_path)
    assert b["dia"] == "2026-11-02" and b["automatico"] is True
    assert b["geradoEm"] == "2026-11-02T11:02-03:00"
    assert b["proximaAtualizacao"] == "hoje às 17h"
    assert len(b["polos"]) == len(json.loads(G.POLOS.read_text(encoding="utf-8"))["polos"])
    assert json.loads((tmp_path / "atual.json").read_text(encoding="utf-8")) == b
    assert (tmp_path / "boletim-2026-11-02.json").exists()
    indice = json.loads((tmp_path / "indice.json").read_text(encoding="utf-8"))
    assert indice["boletins"][0] == {"id": "2026-11-02", "dia": "2026-11-02", "geradoEm": b["geradoEm"], "arquivo": "boletim-2026-11-02.json"}


def test_fonte_fora_do_ar_nao_grava_nada(tmp_path):
    def falha(polo, cliente, agora):
        raise G.FonteIndisponivel(f"MET Norway sem resposta para {polo['nome']}")
    with pytest.raises(G.FonteIndisponivel):
        G.gerar(AGORA, buscar=falha, destino=tmp_path)
    assert not list(tmp_path.iterdir())  # o boletim anterior publicado continua valendo


def test_main_devolve_erro_sem_publicar(monkeypatch, tmp_path):
    publicou = []
    monkeypatch.setattr(G, "configurar_log", lambda: None)
    monkeypatch.setattr(G, "atualizar_noticias", lambda: False)  # sem rede; notícias com falha também não publicam
    monkeypatch.setattr(G, "gerar", lambda: (_ for _ in ()).throw(G.FonteIndisponivel("fora do ar")))
    monkeypatch.setattr(G, "publicar", lambda: publicou.append(True))
    monkeypatch.setattr(G, "retirar_cartao_vencido", lambda: None)  # não mexe no cartão real (tests/py/test_cartao_campo.py)
    assert G.main(["--publicar"]) == 1
    assert not publicou


def test_indice_lista_no_maximo_30_dias(tmp_path):
    for d in range(1, 36):
        dia = f"2026-10-{d:02d}" if d <= 31 else f"2026-11-{d - 31:02d}"
        (tmp_path / f"boletim-{dia}.json").write_text(json.dumps({"id": dia, "dia": dia, "geradoEm": dia + "T05:00-03:00"}), encoding="utf-8")
    G.gravar({"id": "2026-11-05", "dia": "2026-11-05", "geradoEm": "2026-11-05T05:00-03:00"}, tmp_path)
    itens = json.loads((tmp_path / "indice.json").read_text(encoding="utf-8"))["boletins"]
    assert len(itens) == 30 and itens[0]["dia"] == "2026-11-05"
    assert len(list(tmp_path.glob("boletim-*.json"))) == 36  # arquivos antigos não são apagados


def test_proxima_atualizacao():
    assert G.proxima_atualizacao(datetime(2026, 11, 2, 4, 59, tzinfo=G.BRASILIA)) == "hoje às 05h"
    assert G.proxima_atualizacao(datetime(2026, 11, 2, 11, 0, tzinfo=G.BRASILIA)) == "hoje às 17h"
    assert G.proxima_atualizacao(datetime(2026, 11, 2, 17, 30, tzinfo=G.BRASILIA)) == "amanhã às 05h"


def test_agendador_tres_tarefas_com_publicar_e_simulacao(capsys):
    cmds = G.comandos_agendador()
    assert [c[c.index("/ST") + 1] for c in cmds] == ["05:00", "11:00", "17:00"]
    assert all(c[c.index("/TR") + 1].endswith("gerar_boletim_campo.py\" --publicar") for c in cmds)
    assert all(c[c.index("/TN") + 1].startswith("ORGATEC\\JanelaCampo") for c in cmds)
    assert [c[1] for c in G.comandos_agendador(remover=True)] == ["/Delete"] * 3
    G.agendador(remover=False, simular=True)  # só imprime; não cria tarefa
    assert capsys.readouterr().out.count("schtasks /Create") == 3


def test_cache_respeita_expires_sem_ir_a_rede(monkeypatch, tmp_path):
    monkeypatch.setattr(G, "CACHE", tmp_path)
    polo = {"id": "teste", "nome": "Teste", "lat": -17.79, "lon": -50.92}
    (tmp_path / "met-teste.json").write_text(json.dumps({"expira": AGORA.timestamp() + 600, "modificado": None, "corpo": {"ok": 1}}), encoding="utf-8")

    class SemRede:
        def get(self, *a, **k):
            raise AssertionError("não devia consultar o MET dentro do Expires")
    assert G.buscar_met(polo, SemRede(), AGORA) == {"ok": 1}


# ---- confiabilidade da fonte (MET Norway devolveu 502/503 em 04 e 05/11/2026)

POLO = {"id": "teste", "nome": "Teste", "lat": -17.79, "lon": -50.92}


class Resposta:
    def __init__(self, status, corpo=None, cabecalhos=None):
        self.status_code, self._corpo, self.headers = status, corpo, cabecalhos or {}

    def json(self):
        return self._corpo


class Cliente:
    def __init__(self, *respostas):
        self.respostas, self.chamadas = list(respostas), 0

    def get(self, *a, **k):
        self.chamadas += 1
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture
def esperas(monkeypatch, tmp_path):
    monkeypatch.setattr(G, "CACHE", tmp_path)
    dormiu = []
    monkeypatch.setattr(G.time, "sleep", dormiu.append)
    return dormiu


def test_tenta_de_novo_e_aceita_a_segunda_resposta(esperas):
    c = Cliente(Resposta(503), Resposta(200, {"ok": 2}))
    assert G.buscar_met(POLO, c, AGORA) == {"ok": 2}
    assert c.chamadas == 2 and esperas == [2]


def test_retry_after_da_fonte_vale_com_teto(esperas):
    c = Cliente(Resposta(429, cabecalhos={"retry-after": "500"}), Resposta(200, {"ok": 3}))
    G.buscar_met(POLO, c, AGORA)
    assert esperas == [G.ESPERA_MAXIMA]


def test_erro_4xx_que_nao_e_429_nao_insiste(esperas):
    c = Cliente(Resposta(403))
    with pytest.raises(G.FonteIndisponivel, match="403"):
        G.buscar_met(POLO, c, AGORA)
    assert c.chamadas == 1 and not esperas


def test_sem_resposta_depois_das_tres_tentativas(esperas):
    import httpx
    c = Cliente(httpx.ConnectError("x"), httpx.ConnectError("x"), httpx.ConnectError("x"))
    with pytest.raises(G.FonteIndisponivel, match="sem resposta"):
        G.buscar_met(POLO, c, AGORA)
    assert c.chamadas == 3 and esperas == [2, 6]


def test_previsao_guardada_ha_pouco_serve_quando_a_fonte_cai(esperas, tmp_path):
    arq = tmp_path / "met-teste.json"
    arq.write_text(json.dumps({"expira": AGORA.timestamp() - 60, "modificado": None, "corpo": {"velho": 1}}), encoding="utf-8")
    import os
    os.utime(arq, (AGORA.timestamp() - 3600, AGORA.timestamp() - 3600))  # guardada há 1 h
    assert G.buscar_met(POLO, Cliente(Resposta(503), Resposta(503), Resposta(503)), AGORA) == {"velho": 1}


def test_previsao_guardada_ha_muito_tempo_nao_serve(esperas, tmp_path):
    arq = tmp_path / "met-teste.json"
    arq.write_text(json.dumps({"expira": AGORA.timestamp() - 60, "modificado": None, "corpo": {"velho": 1}}), encoding="utf-8")
    import os
    os.utime(arq, (AGORA.timestamp() - 5 * 3600, AGORA.timestamp() - 5 * 3600))  # guardada há 5 h
    with pytest.raises(G.FonteIndisponivel):
        G.buscar_met(POLO, Cliente(Resposta(503), Resposta(503), Resposta(503)), AGORA)


def test_polo_sem_previsao_fica_de_fora_e_o_boletim_avisa(tmp_path):
    cfg = G.carregar_polos()
    ausente = cfg["regioes"][0]["polos"][0]

    def sem_um(polo, cliente, agora):
        if polo["id"] == ausente:
            raise G.FonteIndisponivel(f"MET Norway respondeu 503 para {polo['nome']}")
        return MET
    b = G.gerar(AGORA, buscar=sem_um, destino=tmp_path)
    assert [p["id"] for p in b["semDados"]] == [ausente]
    assert ausente not in [p["id"] for p in b["polos"]] and len(b["polos"]) == len(cfg["polos"]) - 1
    assert any("Sem previsão" in c["rotulo"] for c in b["confianca"])
    assert "1 sem previsão" in b["resumo"]


def test_boletim_inteiro_sem_falha_nao_traz_aviso(tmp_path):
    b = G.gerar(AGORA, buscar=amostra, destino=tmp_path)
    assert b["semDados"] == [] and not any("Sem previsão" in c["rotulo"] for c in b["confianca"])


def test_regiao_precisa_manter_pelo_menos_metade_dos_polos():
    cfg = G.carregar_polos()
    reg = next(r for r in cfg["regioes"] if len(r["polos"]) == 4)
    por_id = {p["id"]: p for p in cfg["polos"]}
    G.conferir_cobertura(cfg, [por_id[i] for i in reg["polos"][:2]])  # 2 de 4 ficam: é a metade, passa
    with pytest.raises(G.FonteIndisponivel, match=reg["nome"]):
        G.conferir_cobertura(cfg, [por_id[i] for i in reg["polos"][:3]])  # fica 1 de 4


def test_falhas_espalhadas_em_regioes_diferentes_nao_derrubam_o_boletim(tmp_path):
    cfg = G.carregar_polos()
    ausentes = {r["polos"][0] for r in cfg["regioes"]}  # 1 polo de cada região, nunca 3 seguidos

    def sem_alguns(polo, cliente, agora):
        if polo["id"] in ausentes:
            raise G.FonteIndisponivel("503")
        return MET
    b = G.gerar(AGORA, buscar=sem_alguns, destino=tmp_path)
    assert {p["id"] for p in b["semDados"]} == ausentes


def test_tres_polos_seguidos_sem_previsao_encerram_a_busca(tmp_path):
    chamados = []

    def cai(polo, cliente, agora):
        chamados.append(polo["id"])
        raise G.FonteIndisponivel("503")
    with pytest.raises(G.FonteIndisponivel, match="fora do ar"):
        G.gerar(AGORA, buscar=cai, destino=tmp_path)
    assert len(chamados) == G.FALHAS_SEGUIDAS


def test_indice_registra_os_dias_sem_boletim(tmp_path):
    for dia in ("2026-11-02", "2026-11-03", "2026-11-05"):
        (tmp_path / f"boletim-{dia}.json").write_text(json.dumps({"id": dia, "dia": dia, "geradoEm": dia + "T05:00-03:00"}), encoding="utf-8")
    G.gravar({"id": "2026-11-06", "dia": "2026-11-06", "geradoEm": "2026-11-06T05:00-03:00"}, tmp_path)
    indice = json.loads((tmp_path / "indice.json").read_text(encoding="utf-8"))
    assert indice["lacunas"] == ["2026-11-04"]
    assert [i["dia"] for i in indice["boletins"]] == ["2026-11-06", "2026-11-05", "2026-11-03", "2026-11-02"]


def test_sem_lacunas_quando_o_arquivo_e_continuo():
    assert G.lacunas(["2026-11-03", "2026-11-02"]) == [] and G.lacunas(["2026-11-02"]) == []
