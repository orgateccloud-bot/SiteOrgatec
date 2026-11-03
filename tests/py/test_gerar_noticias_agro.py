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


def test_le_os_tres_feeds_com_titulo_link_e_data():
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
    assert [f["ok"] for f in d["fontes"]] == [True, True, True]
    assert json.loads(destino.read_text(encoding="utf-8")) == d


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
