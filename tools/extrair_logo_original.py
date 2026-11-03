"""Gera o símbolo ORGATEC a partir da imagem ORIGINAL do logotipo, sem redesenhar.

Entrada: fontes-marca/orgatec-logo-original.jpg (a imagem enviada pela ORGATEC, fundo branco).
Saídas (site/assets/marca/):
  orgatec-original.png         cores originais, fundo transparente (branco convertido em transparência)
  orgatec-original-branco.png  mesma silhueta em branco, para paletas escuras
  orgatec-original-512.png     cores originais em quadrado 512 px (avatar e imagem de destaque)

O branco vira transparência pelo método "cor para alfa": cada pixel perde a parte que é branco, e a cor
restante é recomposta. Assim os vãos entre as faixas ficam transparentes e as bordas continuam suaves.

Uso:  python tools/extrair_logo_original.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "fontes-marca" / "orgatec-logo-original.jpg"
DESTINO = RAIZ / "site" / "assets" / "marca"
RUIDO = 0.06  # abaixo disso é ruído de compressão JPG no fundo branco
OPACO = 0.45  # a partir daqui o pixel é parte da faixa, não borda


def cor_para_alfa(rgb: np.ndarray) -> np.ndarray:
    c = rgb.astype(np.float64) / 255.0
    alfa = (1.0 - c).max(axis=2)
    alfa = np.where(alfa < RUIDO, 0.0, alfa)
    seguro = np.where(alfa == 0, 1.0, alfa)[..., None]
    cor = 1.0 - (1.0 - c) / seguro
    # Miolo das faixas (alfa >= OPACO) fica opaco com a cor ORIGINAL, para que o degradê claro não fique
    # translúcido sobre fundos escuros; só as bordas junto aos vãos usam a cor recomposta e alfa suave.
    miolo = (alfa >= OPACO)[..., None]
    cor = np.where(miolo, c, cor)
    opacidade = np.clip(alfa / OPACO, 0.0, 1.0)
    rgba = np.dstack([np.clip(cor, 0, 1), opacidade])
    return (rgba * 255 + 0.5).astype(np.uint8)


def main() -> None:
    rgb = np.asarray(Image.open(ORIGEM).convert("RGB"))
    rgba = cor_para_alfa(rgb)
    colorido = Image.fromarray(rgba)
    colorido = colorido.crop(colorido.getbbox())  # remove a margem transparente
    colorido.save(DESTINO / "orgatec-original.png", optimize=True)

    branco = np.asarray(colorido).copy()
    branco[..., :3] = 255
    Image.fromarray(branco).save(DESTINO / "orgatec-original-branco.png", optimize=True)

    lado = 512
    quadro = Image.new("RGBA", (lado, lado), (255, 255, 255, 0))
    escala = (lado * 0.86) / max(colorido.size)
    menor = colorido.resize((round(colorido.width * escala), round(colorido.height * escala)), Image.LANCZOS)
    quadro.alpha_composite(menor, ((lado - menor.width) // 2, (lado - menor.height) // 2))
    quadro.save(DESTINO / "orgatec-original-512.png", optimize=True)

    # Ícones da aba e do iPhone a partir do original (o do iPhone precisa de fundo opaco)
    quadro.resize((32, 32), Image.LANCZOS).save(DESTINO / "favicon-32.png", optimize=True)
    iphone = Image.new("RGBA", (180, 180), (255, 255, 255, 255))
    iphone.alpha_composite(quadro.resize((180, 180), Image.LANCZOS))
    iphone.convert("RGB").save(DESTINO / "apple-touch-icon.png", optimize=True)
    print(f"gerado: orgatec-original.png {colorido.size}, orgatec-original-branco.png, orgatec-original-512.png, favicon-32.png, apple-touch-icon.png")


if __name__ == "__main__":
    main()
