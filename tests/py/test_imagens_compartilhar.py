"""Imagens de compartilhamento por página (tools/gerar_imagens_compartilhar.py): cada página da lista tem a sua
imagem 1200 × 630 e o <head> aponta para ela com URL absoluta; as demais continuam com a og-image.png geral."""

import re
import sys
from html import unescape
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
SITE = RAIZ / "site"
sys.path.insert(0, str(RAIZ / "tools"))
import gerar_imagens_compartilhar as G  # noqa: E402


def meta(html: str, prop: str) -> str | None:
    m = re.search(rf'<meta (?:property|name)="{re.escape(prop)}" content="([^"]*)">', html)
    return unescape(m.group(1)) if m else None


def test_lista_cobre_central_da_reforma_publicos_e_cada_publico_pronto():
    import paginas_compliance as pc
    caminhos = [i["caminho"] for i in G.paginas()]
    assert "reforma/index.html" in caminhos and "compliance/publicos.html" in caminhos
    assert {f"compliance/publico/{a}" for c, a, _, _ in pc.PUBLICOS if c in pc.PUBLICOS_PRONTOS} <= set(caminhos)
    assert len(caminhos) == len(set(caminhos))
    nomes = {i["caminho"]: i["titulo"] for i in G.paginas()}
    assert nomes["compliance/publico/mei.html"] == "MEI"


def test_cada_pagina_aponta_para_a_propria_imagem_1200x630():
    for item in G.paginas():
        rel = G.arquivo(item["caminho"])
        assert Image.open(SITE / rel).size == (1200, 630), rel
        html = (SITE / item["caminho"]).read_text(encoding="utf-8")
        assert meta(html, "og:image") == f"https://orgatec.io/{rel}"
        assert meta(html, "og:image:width") == "1200" and meta(html, "og:image:height") == "630"
        titulo = re.search(r"<title>(.*) \| ORGATEC</title>", html).group(1)
        assert meta(html, "og:title") == unescape(titulo) == meta(html, "og:image:alt")
        assert meta(html, "og:description") == meta(html, "description") and len(meta(html, "og:description")) > 60


def test_titulos_e_descricoes_proprios_em_cada_pagina():
    vistos = set()
    for item in G.paginas():
        html = (SITE / item["caminho"]).read_text(encoding="utf-8")
        par = (meta(html, "og:title"), meta(html, "og:description"))
        assert par not in vistos, item["caminho"]
        vistos.add(par)


def test_demais_paginas_mantem_a_imagem_geral_e_toda_og_image_existe():
    proprias = {i["caminho"] for i in G.paginas()}
    for pagina in SITE.rglob("*.html"):
        html = pagina.read_text(encoding="utf-8")
        url = meta(html, "og:image")
        if url is None:
            continue
        assert url.startswith("https://orgatec.io/"), pagina
        assert (SITE / url.removeprefix("https://orgatec.io/")).is_file(), url
        if pagina.relative_to(SITE).as_posix() not in proprias:
            assert url == "https://orgatec.io/assets/marca/og-image.png", pagina


def test_nome_da_imagem_e_imagem_de():
    assert G.arquivo("compliance/publico/mei.html") == "assets/compartilhar/compliance-publico-mei.png"
    assert G.arquivo("reforma/index.html") == "assets/compartilhar/reforma-index.png"
    assert G.imagem_de("compliance/publico/mei.html") == "assets/compartilhar/compliance-publico-mei.png"
    assert G.imagem_de("inicio.html") is None  # sem imagem gerada: a página fica com a geral


def test_html_das_imagens_sem_rede():
    for item in G.paginas():
        html = G.montar_html(item)
        assert "http://" not in html and "https://" not in html and "<script" not in html
        assert item["titulo"].split()[0] in html
