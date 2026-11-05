"""Gera as máscaras do holograma da tela de abertura (site/assets/marca/holo/*.png e site/assets/js/holo-logos.js).

Uso:  python tools/gerar_holo_logos.py [--previa caminho.png]
Os originais ficam em fontes-marca/projecao/ (fora do site, não são publicados). Para cada logotipo:
recorte, máscara por cor ou brilho (separa a marca do fundo), corte justo e redução para LADO px no lado maior.
A máscara sai branca com a intensidade no canal alfa; abertura.js a transforma em pontos em linhas de varredura,
na cor do tema, e projeta em camadas (volume). A ordem da lista é a ordem do rodízio; o primeiro é o quadro fixo do
movimento reduzido. A assinatura "By Warley Veloso" não é imagem: abertura.js a escreve com a fonte do site.
"""

from __future__ import annotations

import argparse
import colorsys
import json
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
ORIGENS = RAIZ / "fontes-marca" / "projecao"
PASTA = RAIZ / "site" / "assets" / "marca" / "holo"
DESTINO = RAIZ / "site" / "assets" / "js" / "holo-logos.js"
LADO = 720      # lado maior da máscara publicada, em pixels
ANALISE = 1440  # lado maior usado para calcular a máscara: originais pequenos são ampliados antes, e o corte por
                # cor sai com borda firme

# id, legenda, arquivo, recorte (x0, y0, x1, y1) no original ou None, regra(h, s, v) → é marca?, exige
LOGOS = [
    ("simbolo", "ORGATEC", "orgatec-simbolo.png", None,
     lambda h, s, v: s > .25 and v > .2, None),
    ("servicos", "ORGATEC SERVIÇOS CONTÁBEIS", "orgatec-servicos-contabeis.jpg", None,
     lambda h, s, v: s > .25 or v < .5, None),
    # néon azul e laranja; fora o fundo "matrix" verde, o piso refletido e a marca d'água do gerador
    ("ia", "ORGATEC IA", "orgatec-ia.jpg", (36, 24, 478, 440),
     lambda h, s, v: v > .85 and not (.17 < h < .46), None),
    # só com a data de início comprovada em config.institucional (anos de atuação ≥ 50)
    ("50-anos", "ORGATEC 50 ANOS", "orgatec-50-anos.jpg", (420, 110, 960, 690),
     lambda h, s, v: v > .5 and (s > .35 or v > .8), "anos50"),
    ("parceiro", "ORGATEC · PARCEIRO FINANCEIRO", "orgatec-parceiro.jpg", (40, 220, 990, 600),
     lambda h, s, v: v > .45, None),
    ("audi-agro", "ORGATEC AUDI AGRO", "orgatec-audi-agro.jpg", (200, 240, 900, 610),
     lambda h, s, v: v < .5 or (s > .4 and v < .85), None),
    ("trilhum", "TRILHUM", "trilhum.jpg", None,
     lambda h, s, v: v > .35, None),
]


def mascara(arquivo: str, recorte, regra) -> Image.Image:
    im = Image.open(ORIGENS / arquivo)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fundo = Image.new("RGB", im.size, (255, 255, 255))
        fundo.paste(im, mask=im.split()[3])
        im = fundo
    im = im.convert("RGB")
    if recorte:
        im = im.crop(recorte)
    escala = ANALISE / max(im.size)
    im = im.resize((round(im.width * escala), round(im.height * escala)), Image.LANCZOS)
    w, h = im.size
    px = im.load()
    alfa = Image.new("L", (w, h), 0)
    pa = alfa.load()
    for y in range(h):
        for x in range(w):
            r, g, b = (c / 255 for c in px[x, y])
            hh, s, v = colorsys.rgb_to_hsv(r, g, b)
            if regra(hh, s, v):
                pa[x, y] = int(255 * (.55 + .45 * max(s, abs(v - .5) * 2)))  # contraste com o fundo, claro ou escuro
    caixa = alfa.getbbox()
    if not caixa:
        raise SystemExit(f"{arquivo}: máscara vazia; ajuste a regra ou o recorte")
    alfa = alfa.crop(caixa)
    alfa.thumbnail((LADO, LADO), Image.LANCZOS)
    alfa = alfa.point(lambda v: v // 17 * 17)  # 16 níveis bastam e reduzem bastante o PNG
    return Image.merge("LA", (Image.new("L", alfa.size, 255), alfa))


def previa(imagens: list[tuple[str, Image.Image]], caminho: Path) -> None:
    tela = Image.new("RGB", (len(imagens) * 380, 420), (8, 14, 28))
    d = ImageDraw.Draw(tela)
    for i, (nome, im) in enumerate(imagens):
        tela.paste(im.convert("RGBA"), (10 + i * 380, 40), im.convert("RGBA"))
        d.text((10 + i * 380, 10), nome, fill=(200, 210, 230))
    tela.save(caminho)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--previa", type=Path, help="salva uma imagem com as máscaras, para conferir")
    args = ap.parse_args()
    PASTA.mkdir(parents=True, exist_ok=True)
    logos, imagens = [], []
    for id_, nome, arquivo, recorte, regra, exige in LOGOS:
        im = mascara(arquivo, recorte, regra)
        im.save(PASTA / f"{id_}.png", optimize=True)
        lg = {"id": id_, "nome": nome, "arquivo": f"assets/marca/holo/{id_}.png", "largura": im.width, "altura": im.height}
        if exige:
            lg["exige"] = exige
        logos.append(lg)
        imagens.append((nome, im))
    dados = json.dumps(logos, ensure_ascii=False, indent=2)
    DESTINO.write_text(
        "/* Gerado por tools/gerar_holo_logos.py a partir de fontes-marca/projecao/ — não editar à mão.\n"
        "   Logotipos do holograma da tela de abertura, na ordem do rodízio: máscaras PNG brancas (intensidade no alfa).\n"
        "   `exige: 'anos50'`: só entra no rodízio com os anos de atuação comprovados (config.institucional). */\n"
        "(function (root) {\n"
        f"  (root.Orgatec = root.Orgatec || {{}}).holoLogos = {dados};\n"
        "})(this);\n", encoding="utf-8", newline="\n")
    total = sum((PASTA / f"{lg['id']}.png").stat().st_size for lg in logos)
    print(f"OK {len(logos)} máscaras em {PASTA.relative_to(RAIZ)} ({total // 1024} KB) e {DESTINO.relative_to(RAIZ)}")
    if args.previa:
        previa(imagens, args.previa)


if __name__ == "__main__":
    main()
