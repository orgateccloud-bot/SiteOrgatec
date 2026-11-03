"""Gera o símbolo ORGATEC e suas variantes (SVG + PNG) em site/assets/marca/.

Geometria medida no arquivo original do logotipo: contorno = elipse rotacionada;
cada faixa é limitada por duas parábolas x(y) (erro máximo de ajuste 1,3 px num
desenho de 314 x 347 px). Cores amostradas de cada faixa, de cima para baixo.

Uso:  python tools/gerar_logo.py           # SVGs
      python tools/gerar_logo.py --png     # SVGs + PNGs (favicon, apple-touch, og-image) via Playwright
"""

from __future__ import annotations

import argparse
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "site" / "assets" / "marca"

W, H = 314, 347
ELIPSE = dict(cx=160.0, cy=172.2, rx=160.0, ry=168.8, rot=8.08)

# Bordas das faixas: x(y) = a*y² + b*y + c
BORDAS = {
    1: (0.000877, -0.182031, 40.410374),
    2: (0.001354, -0.333842, 64.142549),
    3: (0.000632, -0.095347, 105.312585),
    4: (0.001332, -0.365034, 149.384103),
    5: (0.000141, 0.032583, 197.022629),
    6: (0.000811, -0.323936, 258.214150),
}

# (id, borda esquerda, borda direita, paradas do degradê vertical)
FAIXAS = [
    ("navy", None, 1, [(0, "#2F5591"), (0.30, "#244A86"), (0.45, "#183873"), (0.60, "#072563"), (1, "#021D5C")]),
    ("azul", 2, 3, [(0, "#4A81BA"), (0.15, "#4A81BA"), (0.40, "#3466A3"), (0.60, "#214C90"), (1, "#1E4B8E")]),
    ("medio", 4, 5, [(0, "#1984C8"), (0.26, "#3BA7D6"), (0.43, "#2690CC"), (0.55, "#167DBF"), (0.66, "#0A70B8"), (1, "#096FB7")]),
    ("ciano", 6, None, [(0, "#03AEE4"), (0.26, "#02C9F0"), (0.43, "#03DEFA"), (0.55, "#06CAF2"), (0.72, "#04AEE1"), (1, "#03A8DE")]),
]

PALETA = {
    "Navy ORGATEC": "#072563",
    "Azul ORGATEC": "#214C90",
    "Azul médio": "#0970B5",
    "Ciano ORGATEC": "#03AEE4",
    "Ciano luz": "#03DEFA",
    "Tinta (texto)": "#0F172A",
}

Y0, Y1 = -30.0, H + 30.0


def _x(borda: int, y: float) -> float:
    a, b, c = BORDAS[borda]
    return a * y * y + b * y + c


def _curva(borda: int, descendo: bool) -> str:
    """Parábola como Bézier quadrática exata (parametrizada linearmente em y)."""
    ya, yb = (Y0, Y1) if descendo else (Y1, Y0)
    ym = (Y0 + Y1) / 2
    xa, xb, xm = _x(borda, ya), _x(borda, yb), _x(borda, ym)
    xc = 2 * xm - (xa + xb) / 2
    return f"{xa:.2f},{ya:.2f} Q{xc:.2f},{ym:.2f} {xb:.2f},{yb:.2f}"


def _faixa_path(esq: int | None, dir_: int | None) -> str:
    if esq is None:
        ini = f"M-60,{Y0} L-60,{Y1}"
    else:
        ini = "M" + _curva(esq, True)
    if dir_ is None:
        fim = f"L{W + 60},{Y1} L{W + 60},{Y0}"
    else:
        fim = "L" + _curva(dir_, False)
    return f"{ini} {fim} Z"


def simbolo(prefixo: str = "o", cor: str | None = None) -> str:
    """Grupo <g> do símbolo em coordenadas 0..W x 0..H. `cor` = versão chapada (mono/branco)."""
    e = ELIPSE
    defs = [f'<clipPath id="{prefixo}-clip"><ellipse cx="{e["cx"]}" cy="{e["cy"]}" rx="{e["rx"]}" ry="{e["ry"]}" '
            f'transform="rotate({e["rot"]} {e["cx"]} {e["cy"]})"/></clipPath>']
    corpos = []
    for nome, esq, dir_, paradas in FAIXAS:
        if cor:
            fill = cor
        else:
            stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in paradas)
            defs.append(f'<linearGradient id="{prefixo}-{nome}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{H}">{stops}</linearGradient>')
            fill = f"url(#{prefixo}-{nome})"
        corpos.append(f'<path d="{_faixa_path(esq, dir_)}" fill="{fill}"/>')
    return (f'<defs>{"".join(defs)}</defs>'
            f'<g clip-path="url(#{prefixo}-clip)">{"".join(corpos)}</g>')


FONTE = "Inter, 'Helvetica Neue', Arial, sans-serif"


def svg(largura: float, altura: float, corpo: str, titulo: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura:g} {altura:g}" role="img" aria-label="{titulo}">'
            f'<title>{titulo}</title>{corpo}</svg>\n')


def variantes() -> dict[str, str]:
    v: dict[str, str] = {}
    v["orgatec-simbolo.svg"] = svg(W, H, simbolo(), "ORGATEC")
    v["orgatec-simbolo-mono.svg"] = svg(W, H, simbolo("m", "#072563"), "ORGATEC")
    v["orgatec-simbolo-branco.svg"] = svg(W, H, simbolo("b", "#FFFFFF"), "ORGATEC")

    # Horizontal: símbolo com altura 347 → wordmark ao lado (altura das maiúsculas ≈ 46% do símbolo)
    def horizontal(cor_txt: str, cor_sub: str, pref: str, mono: str | None = None) -> str:
        return (f'{simbolo(pref, mono)}'
                f'<text x="372" y="214" font-family="{FONTE}" font-weight="800" font-size="168" letter-spacing="6" textLength="853" lengthAdjust="spacingAndGlyphs" fill="{cor_txt}">ORGATEC</text>'
                f'<text x="376" y="292" font-family="{FONTE}" font-weight="600" font-size="39" letter-spacing="14" textLength="845" lengthAdjust="spacingAndGlyphs" fill="{cor_sub}">INTELIGÊNCIA TRIBUTÁRIA</text>')
    v["orgatec-horizontal.svg"] = svg(1250, H, horizontal("#0F172A", "#0970B5", "h"), "ORGATEC")
    v["orgatec-horizontal-negativo.svg"] = svg(1250, H, horizontal("#FFFFFF", "#03DEFA", "n"), "ORGATEC")
    v["orgatec-horizontal-mono.svg"] = svg(1250, H, horizontal("#072563", "#072563", "hm", "#072563"), "ORGATEC")

    # Vertical (empilhada)
    vert = (f'<g transform="translate(193 0)">{simbolo("v")}</g>'
            f'<text x="350" y="500" text-anchor="middle" font-family="{FONTE}" font-weight="800" font-size="128" letter-spacing="5" textLength="652" lengthAdjust="spacingAndGlyphs" fill="#0F172A">ORGATEC</text>'
            f'<text x="350" y="562" text-anchor="middle" font-family="{FONTE}" font-weight="600" font-size="30" letter-spacing="11" textLength="646" lengthAdjust="spacingAndGlyphs" fill="#0970B5">INTELIGÊNCIA TRIBUTÁRIA</text>')
    v["orgatec-vertical.svg"] = svg(700, 590, vert, "ORGATEC")

    # Ícones de aplicativo / avatar (512 px). Claro: símbolo colorido sobre branco.
    # Escuro: símbolo branco sobre navy (a faixa navy colorida sumiria no fundo escuro).
    s = 512 * 0.62 / H
    pos = f'translate({(512 - W * s) / 2:.2f} {(512 - H * s) / 2:.2f}) scale({s:.4f})'
    v["orgatec-app.svg"] = svg(512, 512, f'<rect width="512" height="512" rx="112" fill="#FFFFFF"/><g transform="{pos}">{simbolo("a")}</g>', "ORGATEC")
    v["orgatec-app-escuro.svg"] = svg(512, 512,
        '<defs><linearGradient id="ae-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0B2E73"/><stop offset="1" stop-color="#051B4D"/></linearGradient></defs>'
        f'<rect width="512" height="512" rx="112" fill="url(#ae-bg)"/><g transform="{pos}">{simbolo("ae", "#FFFFFF")}</g>', "ORGATEC")

    # Favicon: símbolo colorido com pequena margem, quadrado
    sf = 0.94 * 64 / H
    fav = f'<g transform="translate({(64 - W * sf) / 2:.2f} {(64 - H * sf) / 2:.2f}) scale({sf:.4f})">{simbolo("f")}</g>'
    v["favicon.svg"] = svg(64, 64, fav, "ORGATEC")
    return v


OG_HTML = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@600;800&display=swap" rel="stylesheet">
<style>body{margin:0}#c{width:1200px;height:630px;background:radial-gradient(circle at 85% 20%,#0B3A8C 0,#0F172A 55%);display:flex;align-items:center;padding:0 90px;box-sizing:border-box;font-family:Inter,sans-serif;color:#fff;gap:56px}
img{height:300px}h1{font-size:96px;font-weight:800;letter-spacing:4px;margin:0}p{font-size:30px;margin:14px 0 0;color:#CBD5E1;font-weight:600;line-height:1.35}span{color:#03DEFA}</style></head>
<body><div id="c"><img src="orgatec-simbolo.svg"><div><h1>ORGATEC</h1><p>Contabilidade consultiva e<br><span>inteligência tributária</span> para a Reforma</p></div></div></body></html>"""


def gerar_png() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for nome, tam, saida in (("favicon.svg", 32, "favicon-32.png"), ("orgatec-app.svg", 180, "apple-touch-icon.png"),
                                  ("orgatec-app.svg", 512, "orgatec-app-512.png"), ("orgatec-app-escuro.svg", 512, "orgatec-app-escuro-512.png")):
            pg.set_viewport_size({"width": tam, "height": tam})
            pg.goto((DESTINO / nome).as_uri())
            pg.screenshot(path=str(DESTINO / saida), omit_background=saida != "apple-touch-icon.png",  # iOS aplica a própria máscara: fundo opaco
                          clip={"x": 0, "y": 0, "width": tam, "height": tam})
        # PNGs das assinaturas com a fonte Inter carregada (para uso fora da web)
        for nome, fundo in (("orgatec-horizontal.svg", "transparent"), ("orgatec-horizontal-negativo.svg", "#0F172A"), ("orgatec-vertical.svg", "transparent")):
            html = (f'<html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@600;800&display=swap" rel="stylesheet">'
                    f'<style>body{{margin:0;background:{fundo}}}</style></head><body>{(DESTINO / nome).read_text(encoding="utf-8")}</body></html>')
            tmp = DESTINO / "_tmp.html"
            tmp.write_text(html, encoding="utf-8")
            vb = [float(x) for x in html.split('viewBox="')[1].split('"')[0].split()]
            pg.set_viewport_size({"width": int(vb[2]), "height": int(vb[3])})
            pg.goto(tmp.as_uri())
            pg.wait_for_timeout(800)
            pg.screenshot(path=str(DESTINO / nome.replace(".svg", ".png")), omit_background=fundo == "transparent",
                          clip={"x": 0, "y": 0, "width": vb[2], "height": vb[3]})
            tmp.unlink()
        tmp = DESTINO / "_og.html"
        tmp.write_text(OG_HTML, encoding="utf-8")
        pg.set_viewport_size({"width": 1200, "height": 630})
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(DESTINO / "og-image.png"), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
        tmp.unlink()
        b.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", action="store_true")
    args = ap.parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nome, conteudo in variantes().items():
        (DESTINO / nome).write_text(conteudo, encoding="utf-8")
        print("OK", nome)
    if args.png:
        gerar_png()
        print("OK PNGs")


if __name__ == "__main__":
    main()
