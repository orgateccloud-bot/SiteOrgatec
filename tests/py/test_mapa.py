"""Mapa do site (tools/gerar_mapa.py): toda página indexável entra; páginas internas (noindex) ficam fora."""

import re
import sys
import xml.dom.minidom
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import gerar_mapa  # noqa: E402


def test_mapa_tem_as_paginas_indexaveis_e_nenhuma_interna():
    lista = gerar_mapa.paginas()
    enderecos = [u for u, _ in lista]
    assert enderecos[0] == "https://orgatec.io/"  # a raiz (tela de abertura) vem primeiro
    assert len(enderecos) == len(set(enderecos))
    for interna in ("testes/index.html", "marca.html", "orgatec-template2.html", "orgatec-trilha.html"):
        assert f"https://orgatec.io/{interna}" not in enderecos
    for pagina in ("inicio.html", "tributario/index.html", "reforma/index.html", "ferramentas/simulador.html"):
        assert f"https://orgatec.io/{pagina}" in enderecos
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) for _, d in lista)


def test_sitemap_xml_valido(tmp_path):
    destino = tmp_path / "sitemap.xml"  # testes não regravam o site: a pasta principal precisa continuar limpa
    gerar_mapa.main(destino)
    doc = xml.dom.minidom.parse(str(destino))
    assert len(doc.getElementsByTagName("url")) == len(gerar_mapa.paginas())


def test_robots_txt_aponta_o_sitemap_e_nao_bloqueia(tmp_path):
    gerar_mapa.main(tmp_path / "sitemap.xml")
    texto = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: https://orgatec.io/sitemap.xml" in texto
    assert "Disallow" not in texto
    assert "User-agent: *" in texto


def test_lastmod_vem_do_ultimo_commit_e_nao_da_gravacao(tmp_path, monkeypatch):
    arquivo = tmp_path / "x.html"
    arquivo.write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(gerar_mapa.shutil, "which", lambda _n: None)  # sem git: cai na data do arquivo, ainda no formato AAAA-MM-DD
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", gerar_mapa.data_da_pagina(arquivo))
