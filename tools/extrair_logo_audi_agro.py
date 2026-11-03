"""Gera a logo Orgatec Audi Agro do site a partir da imagem ORIGINAL, sem redesenhar.

Entrada: fontes-marca/orgatec-audi-agro-original.jpg (enviada pela ORGATEC: "OA" preto, planta verde no "O" e
"ORGATEC AUDI AGRO" em verde, fundo branco).
Saída: site/assets/marca/orgatec-audi-agro.png — recortada nas margens brancas, fundo branco mantido (no site
ela fica sobre um selo branco, para manter as cores originais também nas paletas escuras; sem o branco, o "OA"
preto sumiria no fundo escuro).

Também imprime o verde e o preto medidos na imagem (mediana dos pixels da marca), usados nas variáveis
--aa-verde e --aa-preto da seção (tools/gerar_design_system.py).

Uso:  python tools/extrair_logo_audi_agro.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "fontes-marca" / "orgatec-audi-agro-original.jpg"
DESTINO = RAIZ / "site" / "assets" / "marca" / "orgatec-audi-agro.png"
MARGEM = 24  # px de respiro em volta do desenho
LARGURA = 480


def medir_cores(rgb: np.ndarray) -> tuple[str, str]:
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    verde = (g > r + 40) & (g > b + 40)
    preto = (r < 60) & (g < 60) & (b < 60)
    hexa = lambda m: "#%02x%02x%02x" % tuple(int(np.median(rgb[..., i][m])) for i in range(3))
    return hexa(verde), hexa(preto)


def main() -> None:
    im = Image.open(ORIGEM).convert("RGB")
    rgb = np.asarray(im)
    desenho = (rgb < 235).any(axis=2)  # tudo o que não é fundo branco (ruído de JPG incluído no limiar)
    ys, xs = np.where(desenho)
    caixa = (max(xs.min() - MARGEM, 0), max(ys.min() - MARGEM, 0), min(xs.max() + MARGEM, im.width), min(ys.max() + MARGEM, im.height))
    recorte = im.crop(caixa)
    alto = round(recorte.height * LARGURA / recorte.width)
    recorte.resize((LARGURA, alto), Image.LANCZOS).save(DESTINO, optimize=True)
    verde, preto = medir_cores(rgb)
    print(f"gerado: {DESTINO.relative_to(RAIZ)} ({LARGURA}x{alto}) · verde {verde} · preto {preto}")


if __name__ == "__main__":
    main()
