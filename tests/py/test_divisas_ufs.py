"""Divisas dos estados do mapa de satélite (tools/gerar_divisas_ufs.py), sem rede: o shapefile do teste é montado à mão.
O SVG que está no site vem do BR_UF_2025.zip do IBGE (licença compatível com CC BY 4.0; ver o cabeçalho da ferramenta)."""

import math
import re
import struct
import sys
import xml.dom.minidom
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import gerar_divisas_ufs as D  # noqa: E402

SVG = RAIZ / "site" / "assets" / "img" / "divisas-ufs.svg"
MAPA_JS = (RAIZ / "site" / "assets" / "js" / "campo-mapa.js").read_text(encoding="utf-8")


def shapefile(aneis):
    """Um shapefile de polígonos (tipo 5) com um registro por anel; o suficiente para o leitor."""
    registros = b""
    for n, anel in enumerate(aneis, 1):
        pts = b"".join(struct.pack("<dd", lon, lat) for lon, lat in anel)
        corpo = struct.pack("<i", 5) + struct.pack("<4d", 0, 0, 0, 0) + struct.pack("<ii", 1, len(anel)) + struct.pack("<i", 0) + pts
        registros += struct.pack(">ii", n, len(corpo) // 2) + corpo
    cabecalho = struct.pack(">i", 9994) + b"\0" * 20 + struct.pack(">i", (100 + len(registros)) // 2) + struct.pack("<ii", 1000, 5) + b"\0" * 64
    return cabecalho + registros


def test_recorte_igual_ao_do_mapa_javascript():
    caixa = re.search(r"CAIXA = \{ oeste: (-?\d+), leste: (-?\d+), norte: (-?\d+), sul: (-?\d+) \}", MAPA_JS)
    assert caixa and tuple(map(int, caixa.groups())) == (D.OESTE, D.LESTE, D.NORTE, D.SUL)
    assert re.search(r"var Z = 4, N = Math\.pow\(2, Z\), TAM = 256;", MAPA_JS) and (D.Z, D.TAM) == (4, 256)


def test_projecao_cantos_e_proporcao_do_recorte():
    assert D.projetar(D.OESTE, D.NORTE) == pytest.approx((0, 0), abs=1e-9)
    x, y = D.projetar(D.LESTE, D.SUL)
    assert x == pytest.approx(D.LARGURA_SVG) and y == pytest.approx(D.ALTURA_SVG)
    xg, yg = D.projetar(-49.25, -16.68)  # Goiânia fica dentro do recorte, mais para o centro
    assert 0 < xg < D.LARGURA_SVG and 0 < yg < D.ALTURA_SVG and 300 < xg < 700


def test_leitor_de_shapefile_devolve_os_aneis():
    quadrado = [(-50.0, -10.0), (-49.0, -10.0), (-49.0, -11.0), (-50.0, -11.0), (-50.0, -10.0)]
    assert D.ler_aneis(shapefile([quadrado, quadrado[:4] + [quadrado[0]]])) == [quadrado, quadrado]
    with pytest.raises(ValueError):
        D.ler_aneis(b"\0" * 120)


def test_simplificar_tira_pontos_alinhados_e_guarda_as_pontas():
    reta = [(0, 0), (1, 0.01), (2, 0), (3, -0.01), (4, 0)]
    assert D.simplificar(reta, 0.5) == [(0, 0), (4, 0)]
    quina = [(0, 0), (5, 0), (5, 5)]
    assert D.simplificar(quina, 0.5) == quina
    assert D.simplificar([(0, 0), (1, 1)], 1) == [(0, 0), (1, 1)]


def test_caminho_ignora_ilhotas_e_o_que_esta_fora_do_recorte():
    grande = [(-50.0, -10.0), (-45.0, -10.0), (-45.0, -15.0), (-50.0, -15.0), (-50.0, -10.0)]
    ilhota = [(-40.0, -10.0), (-39.99, -10.0), (-39.99, -10.01), (-40.0, -10.01), (-40.0, -10.0)]
    texto, total = D.caminho_svg([grande, ilhota], 0.8)
    assert texto.count("M") == 1 and total == 5  # o quadrado fechado (5 pontos, o primeiro repetido); a ilhota some
    assert D.caminho_svg([[(-10.0, -3.0), (-9.0, -3.0), (-9.0, -4.0), (-10.0, -3.0)]], 0.8) == ("", 0)  # longe do recorte


def test_svg_do_site_e_valido_leve_e_com_credito_e_aviso_de_generalizacao():
    texto = SVG.read_text(encoding="utf-8")
    doc = xml.dom.minidom.parseString(texto)
    raiz = doc.documentElement
    assert raiz.getAttribute("viewBox").startswith("0 0 1000 ") and raiz.getAttribute("preserveAspectRatio") == "none"
    assert len(texto) < 80_000
    desc = doc.getElementsByTagName("desc")[0].firstChild.data
    for obrigatorio in ("IBGE", "CC BY 4.0", "simplificadas", "ilustrativo"):
        assert obrigatorio in desc, obrigatorio
    assert len(doc.getElementsByTagName("use")) == 2 and len(doc.getElementsByTagName("path")) == 1
    assert "http" not in re.sub(r'xmlns="[^"]*"', "", texto.replace("</desc>", "")).split("<defs>")[1]  # nada externo nas linhas


def test_geometria_do_svg_bate_com_os_extremos_do_brasil():
    """Confere a orientação e a escala: o oeste (Acre) e o sul (Rio Grande do Sul) do desenho ficam onde devem."""
    caminho = re.search(r' d="([^"]+)"', SVG.read_text(encoding="utf-8")).group(1)
    pontos = [(float(a), float(b)) for a, b in re.findall(r"(-?\d+\.?\d*) (-?\d+\.?\d*)", caminho)]
    assert len(pontos) > 1500
    xs, ys = [p[0] for p in pontos], [p[1] for p in pontos]
    oeste_x = D.projetar(-73.99, 0)[0]          # ponto mais a oeste do Brasil (Serra do Divisor, AC)
    sul_y = D.projetar(0, -33.75)[1]            # ponto mais ao sul (Chuí, RS)
    assert min(xs) == pytest.approx(oeste_x, abs=4)
    assert max(ys) == pytest.approx(sul_y, abs=4)
    norte_y = D.projetar(0, 5.27)[1]            # Monte Caburaí, RR
    assert min(ys) == pytest.approx(norte_y, abs=4)
    assert math.isfinite(sum(xs) + sum(ys))
