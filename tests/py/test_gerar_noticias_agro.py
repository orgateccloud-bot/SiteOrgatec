"""Notícias dos cards Orgatec Audi Agro (tools/gerar_noticias_agro.py) sem rede: feeds gravados em tests/fixtures/agro
(Agência Câmara · Agropecuária, Agência Senado e Receita Federal, coletados em 02/11/2026)."""

import json
import sys
from datetime import datetime
from pathlib import Path

import httpx
import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import gerar_noticias_agro as N  # noqa: E402

AMOSTRAS = RAIZ / "tests" / "fixtures" / "agro"
AGORA = datetime(2026, 11, 2, 12, 40, tzinfo=N.BRASILIA)
CFG = json.loads(N.CONFIG.read_text(encoding="utf-8"))


def amostra(feed, cliente):
    return (AMOSTRAS / f"{feed['id']}.xml").read_bytes()


def test_le_os_feeds_com_titulo_link_e_data():
    for feed in CFG["feeds"]:
        itens = N.ler_feed(amostra(feed, None), feed, "2026-11-02T12:40-03:00")
        assert itens, feed["id"]
        for i in itens:
            assert i["titulo"] and i["link"].startswith("http") and i["fonte"] == feed["id"]
    senado = N.ler_feed(amostra(CFG["feeds"][1], None), CFG["feeds"][1], "x")
    assert all("senado.leg.br" in i["link"] for i in senado)  # o Senado não manda <link>: o endereço vem do <guid>


def test_palavra_chave_so_no_comeco_da_palavra():
    item = {"_filtro": N.normalizar("Projeto protege empregado rural e trata de graves crises; suínos e bovinos")}
    assert not N.casa(item, ["gado"])   # "empregado" não é gado
    assert not N.casa(item, ["aves"])   # "graves" não é aves
    assert N.casa(item, ["suín"]) and N.casa(item, ["bovin"])
    assert N.casa({"_filtro": N.normalizar("Café e cafeicultura")}, ["cafe"])  # sem acento casa com acento


def test_classifica_por_atividade_ordena_e_descarta_antigos():
    itens = [i for f in CFG["feeds"] for i in N.ler_feed(amostra(f, None), f, "x")]
    atividades, tributacao = N.classificar(itens, CFG, AGORA)
    assert set(atividades) == {a["id"] for a in CFG["atividades"]}
    for lista in list(atividades.values()) + [tributacao]:
        datas = [i["data"] for i in lista]
        assert datas == sorted(datas, reverse=True)
        assert all(d >= "2026-08-04" for d in datas)  # nada com mais de 90 dias (a Receita mistura itens de 2022)
        assert all("_filtro" not in i for i in lista)
    assert any("rastreabilidade bovina" in i["titulo"].lower() for i in atividades["corte"])
    assert len(atividades["corte"]) <= N.POR_ATIVIDADE


def test_gera_json_com_fontes_e_data(tmp_path):
    destino = tmp_path / "noticias.json"
    d = N.gerar(AGORA, baixar=amostra, destino=destino)
    assert d["geradoEm"] == "2026-11-02T12:40-03:00"
    assert [f["ok"] for f in d["fontes"]] == [True] * len(CFG["feeds"])
    assert json.loads(destino.read_text(encoding="utf-8")) == d
    assert all(f["portal"].startswith("https://") for f in d["fontes"])
    # os itens brutos (com o texto do filtro) ficam no histórico, não no arquivo que o visitante baixa
    texto = destino.read_text(encoding="utf-8")
    assert "_filtro" not in texto and '"itens":[' not in texto
    hist = json.loads((tmp_path / "historico.json").read_text(encoding="utf-8"))
    assert len(hist["itens"]) > 20 and all("_filtro" in i for i in hist["itens"])
    assert d["janelaDias"] == 90 and [x["nome"] for x in d["acompanhe"]] == [x["nome"] for x in CFG["acompanhe"]]


def test_fonte_fora_do_ar_mantem_itens_anteriores_com_a_data_da_coleta(tmp_path):
    destino = tmp_path / "noticias.json"
    N.gerar(AGORA, baixar=amostra, destino=destino)

    def camara_fora(feed, cliente):
        if feed["id"] == "camara-agro":
            raise httpx.ConnectError("sem conexão")
        return amostra(feed, cliente)

    depois = datetime(2026, 11, 2, 17, 0, tzinfo=N.BRASILIA)
    d = N.gerar(depois, baixar=camara_fora, destino=destino)
    camara = [f for f in d["fontes"] if f["id"] == "camara-agro"][0]
    assert camara["ok"] is False and "sem conexão" in camara["erro"]
    assert camara["ultimaColetaValida"] == "2026-11-02T12:40-03:00"
    assert camara["itens"] > 0
    assert any(i["fonte"] == "camara-agro" and i["coletadoEm"] == "2026-11-02T12:40-03:00" for i in d["atividades"]["corte"])


def test_xml_invalido_conta_como_falha(tmp_path):
    def quebrado(feed, cliente):
        return b"<rss><channel><item><title>sem fim"
    d = N.gerar(AGORA, baixar=quebrado, destino=tmp_path / "n.json")
    assert all(not f["ok"] for f in d["fontes"])
    assert d["atividades"]["soja"] == []  # sem dado anterior: lista vazia, nada inventado


@pytest.mark.parametrize("bruta,esperada", [
    ("Tue, 27 Oct 2026 21:19:00 GMT", "2026-10-27T18:19-03:00"),
    ("Fri, 30 Oct 2026 20:10:23 -0300", "2026-10-30T20:10-03:00"),
    ("2026-10-29T10:00:00Z", "2026-10-29T07:00-03:00"),
    ("data ruim", None),
])
def test_data_em_brasilia(bruta, esperada):
    assert N.data_iso(bruta) == esperada


# ---- Fase 6: histórico acumulado, última notícia, título inteiro


def rss(*itens):
    corpo = "".join(f"<item><title>{t}</title><link>{l}</link><pubDate>{d}</pubDate><description>{t}</description></item>" for t, l, d in itens)
    return f"<?xml version='1.0'?><rss version='2.0'><channel><title>x</title>{corpo}</channel></rss>".encode("utf-8")


def so_um_feed(xml):
    """baixar() que devolve o mesmo XML para o primeiro feed da configuração e um feed vazio para os outros."""
    def baixar(feed, cliente):
        return xml if feed["id"] == CFG["feeds"][0]["id"] else rss()
    return baixar


def test_historico_acumula_o_que_saiu_do_feed(tmp_path):
    destino = tmp_path / "noticias.json"
    ontem = ("Soja: governo anuncia nova regra", "https://exemplo.gov.br/soja", "Mon, 02 Nov 2026 09:00:00 -0300")
    hoje = ("Milho tem novo programa", "https://exemplo.gov.br/milho", "Tue, 03 Nov 2026 09:00:00 -0300")
    d1 = N.gerar(AGORA, baixar=so_um_feed(rss(ontem)), destino=destino)
    assert [i["titulo"] for i in d1["atividades"]["soja"]] == ["Soja: governo anuncia nova regra"]
    # na rodada seguinte o feed já não traz a notícia da soja, mas ela continua valendo (dentro dos 90 dias)
    d2 = N.gerar(datetime(2026, 11, 3, 12, 0, tzinfo=N.BRASILIA), baixar=so_um_feed(rss(hoje)), destino=destino)
    assert [i["titulo"] for i in d2["atividades"]["soja"]] == ["Soja: governo anuncia nova regra"]
    assert [i["titulo"] for i in d2["atividades"]["milho"]] == ["Milho tem novo programa"]
    primeiro = d2["fontes"][0]
    assert primeiro["ok"] and primeiro["itens"] == 1 and primeiro["acumulados"] == 1
    # a notícia que continua no feed não é duplicada
    d3 = N.gerar(datetime(2026, 11, 3, 17, 0, tzinfo=N.BRASILIA), baixar=so_um_feed(rss(hoje, ontem)), destino=destino)
    assert [i["link"] for i in d3["atividades"]["soja"]] == ["https://exemplo.gov.br/soja"]


def test_tema_sem_noticia_recente_mostra_a_ultima_que_houver(tmp_path):
    destino = tmp_path / "noticias.json"
    antiga = ("Café: regras da safra", "https://exemplo.gov.br/cafe", "Mon, 06 Jul 2026 09:00:00 -0300")      # 119 dias antes de AGORA
    muito_antiga = ("Arroz: levantamento", "https://exemplo.gov.br/arroz", "Mon, 06 Apr 2026 09:00:00 -0300")  # 210 dias: fora da retenção
    recente = ("Soja em alta", "https://exemplo.gov.br/soja", "Mon, 02 Nov 2026 09:00:00 -0300")
    d = N.gerar(AGORA, baixar=so_um_feed(rss(antiga, muito_antiga, recente)), destino=destino)
    assert d["atividades"]["cafe"] == [] and d["ultimas"]["cafe"]["titulo"] == "Café: regras da safra"
    assert d["ultimas"]["cafe"]["data"].startswith("2026-07-06") and "_filtro" not in d["ultimas"]["cafe"]
    assert d["atividades"]["arroz"] == [] and d["ultimas"]["arroz"] is None   # passou da retenção de 180 dias
    assert d["ultimas"]["soja"] is None                                        # tem notícia recente: o card mostra a lista
    assert d["ultimas"]["milho"] is None and set(d["ultimas"]) == {a["id"] for a in CFG["atividades"]} | {"tributacao"}


def test_noticia_acumulada_some_depois_da_retencao(tmp_path):
    destino = tmp_path / "noticias.json"
    N.gerar(datetime(2026, 5, 1, 12, 0, tzinfo=N.BRASILIA), baixar=so_um_feed(rss(("Soja: abril", "https://exemplo.gov.br/s", "Fri, 01 May 2026 08:00:00 -0300"))), destino=destino)
    N.gerar(datetime(2026, 11, 5, 12, 0, tzinfo=N.BRASILIA), baixar=so_um_feed(rss()), destino=destino)  # 188 dias depois
    hist = json.loads((tmp_path / "historico.json").read_text(encoding="utf-8"))
    assert hist["itens"] == []


def test_titulo_nao_e_cortado_e_o_longo_demais_nao_e_listado():
    ok = "S" * (N.TITULO_MAX - 5) + " soja"   # exatamente TITULO_MAX caracteres
    longo = ok + "!"
    feed = CFG["feeds"][0]
    itens = N.ler_feed(rss((ok, "https://e.gov.br/1", "Mon, 02 Nov 2026 09:00:00 -0300"), (longo, "https://e.gov.br/2", "Mon, 02 Nov 2026 09:00:00 -0300")), feed, "x")
    assert [i["titulo"] for i in itens] == [ok] and len(itens[0]["titulo"]) == N.TITULO_MAX


def test_noticias_json_antigo_com_itens_vale_como_historico(tmp_path):
    destino = tmp_path / "noticias.json"
    f = CFG["feeds"][0]
    item = {"titulo": "Soja: regra antiga", "link": "https://e.gov.br/antigo", "data": "2026-10-20T10:00-03:00", "fonte": f["id"],
            "fonteNome": f["nome"], "coletadoEm": "2026-10-20T12:00-03:00", "_filtro": "soja: regra antiga"}
    destino.write_text(json.dumps({"geradoEm": "x", "itens": [item]}), encoding="utf-8")
    d = N.gerar(AGORA, baixar=so_um_feed(rss()), destino=destino)
    assert [i["link"] for i in d["atividades"]["soja"]] == ["https://e.gov.br/antigo"]
    assert "itens" not in json.loads(destino.read_text(encoding="utf-8"))  # na mudança, os itens saem do arquivo público
