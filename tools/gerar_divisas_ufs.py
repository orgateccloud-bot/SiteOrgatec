"""Divisas dos estados para o mapa de satélite da Janela de Campo: lê os limites estaduais do IBGE (shapefile oficial),
projeta no mesmo recorte do mapa (campo-mapa.js: Web Mercator, zoom 4) e grava site/assets/img/divisas-ufs.svg.

Fonte: IBGE, Malha Municipal Digital e Áreas Territoriais 2025 (arquivo BR_UF_2025.zip). Licença, conferida na nota
metodológica 01/2026 do IBGE ("Informações técnicas e legais para a utilização dos dados publicados", item 2102268 da
Biblioteca do IBGE): a MMD e os produtos derivados saem sob licença compatível com Creative Commons BY 4.0, inclusive para
fins comerciais, com crédito ao IBGE. A mesma nota exige que, ao generalizar a malha (simplificar vetores para uma escala),
o usuário final seja avisado de que ela passou por processamento que alterou as características originais: o mapa traz esse
aviso. O IBGE informa que não é responsável legal pela definição dos limites; o desenho é ilustrativo.

Uso:
    python tools/gerar_divisas_ufs.py                       baixa o BR_UF_2025.zip do IBGE e grava o SVG
    python tools/gerar_divisas_ufs.py --zip CAMINHO.zip     usa um arquivo já baixado
    python tools/gerar_divisas_ufs.py --tolerancia 0.8      tolerância da simplificação, em unidades do SVG (largura 1000)

Só a biblioteca padrão. O SVG gerado fica no repositório; o shapefile (14 MB) não.
"""

from __future__ import annotations

import argparse
import io
import math
import struct
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "site" / "assets" / "img" / "divisas-ufs.svg"
URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_UF_2025.zip"
FONTE = "IBGE, Malha Municipal Digital e Áreas Territoriais 2025 (limites das Unidades da Federação), licença compatível com CC BY 4.0"

# Mesmo recorte de site/assets/js/campo-mapa.js (CAIXA, Z e TAM): um teste confere que os números não se afastam.
OESTE, LESTE, NORTE, SUL = -75.0, -33.0, 6.0, -34.0
Z, TAM = 4, 256
LARGURA_SVG = 1000.0
MENOR_ANEL = 6.0  # diagonal mínima de um anel, em unidades do SVG


def _px(lon: float) -> float:
    return (lon + 180) / 360 * TAM * 2 ** Z


def _py(lat: float) -> float:
    r = math.radians(lat)
    return (1 - math.log(math.tan(math.pi / 4 + r / 2)) / math.pi) / 2 * TAM * 2 ** Z


X0, X1, Y0, Y1 = _px(OESTE), _px(LESTE), _py(NORTE), _py(SUL)
ESCALA = LARGURA_SVG / (X1 - X0)
ALTURA_SVG = (Y1 - Y0) * ESCALA


def projetar(lon: float, lat: float) -> tuple[float, float]:
    """Longitude e latitude (graus) para as coordenadas do SVG, no recorte do mapa."""
    return (_px(lon) - X0) * ESCALA, (_py(lat) - Y0) * ESCALA


def ler_aneis(shp: bytes) -> list[list[tuple[float, float]]]:
    """Anéis (lista de pontos lon, lat) de um shapefile de polígonos. Só o formato que o IBGE publica (tipo 5)."""
    if struct.unpack(">i", shp[0:4])[0] != 9994:
        raise ValueError("não é um shapefile")
    aneis, pos = [], 100
    while pos + 8 <= len(shp):
        tamanho = struct.unpack(">i", shp[pos + 4:pos + 8])[0] * 2
        corpo = shp[pos + 8:pos + 8 + tamanho]
        pos += 8 + tamanho
        tipo = struct.unpack("<i", corpo[0:4])[0]
        if tipo == 0:
            continue
        if tipo != 5:
            raise ValueError(f"tipo de forma {tipo} não suportado (esperado 5, polígono)")
        n_partes, n_pontos = struct.unpack("<ii", corpo[36:44])
        partes = list(struct.unpack(f"<{n_partes}i", corpo[44:44 + 4 * n_partes])) + [n_pontos]
        base = 44 + 4 * n_partes
        pontos = [struct.unpack("<dd", corpo[base + 16 * i:base + 16 * i + 16]) for i in range(n_pontos)]
        for a, b in zip(partes, partes[1:]):
            aneis.append(pontos[a:b])
    return aneis


def simplificar(pontos: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
    """Douglas-Peucker iterativo (sem recursão, para anéis com muitos pontos). Mantém o primeiro e o último ponto."""
    if len(pontos) < 3:
        return pontos[:]
    manter = [False] * len(pontos)
    manter[0] = manter[-1] = True
    pilha = [(0, len(pontos) - 1)]
    while pilha:
        i, j = pilha.pop()
        (ax, ay), (bx, by) = pontos[i], pontos[j]
        dx, dy = bx - ax, by - ay
        norma = math.hypot(dx, dy)
        maior, onde = -1.0, -1
        for k in range(i + 1, j):
            px_, py_ = pontos[k]
            d = math.hypot(px_ - ax, py_ - ay) if norma == 0 else abs(dy * (px_ - ax) - dx * (py_ - ay)) / norma
            if d > maior:
                maior, onde = d, k
        if maior > tol:
            manter[onde] = True
            pilha.append((i, onde))
            pilha.append((onde, j))
    return [p for p, m in zip(pontos, manter) if m]


def caminho_svg(aneis: list[list[tuple[float, float]]], tol: float) -> tuple[str, int]:
    """Comandos de caminho (M/L/Z) com os anéis projetados e simplificados. Devolve o texto e o total de pontos."""
    partes, total = [], 0
    for anel in aneis:
        pts = [projetar(lon, lat) for lon, lat in anel]
        # descarta pontos quase iguais antes do Douglas-Peucker (a malha de origem é muito detalhada)
        enxuto = [pts[0]]
        for p in pts[1:]:
            if math.hypot(p[0] - enxuto[-1][0], p[1] - enxuto[-1][1]) >= tol / 4:
                enxuto.append(p)
        simples = simplificar(enxuto, tol)
        if len(simples) < 3:
            continue
        # fora do recorte (por exemplo, Fernando de Noronha) o SVG corta sozinho; aqui só ignora o que está muito longe
        if all(x < -50 or x > LARGURA_SVG + 50 or y < -50 or y > ALTURA_SVG + 50 for x, y in simples):
            continue
        # ilhotas e ilhas menores que uns 4 pixels do mapa só enfeitam e pesam
        xs, ys = [p[0] for p in simples], [p[1] for p in simples]
        if math.hypot(max(xs) - min(xs), max(ys) - min(ys)) < MENOR_ANEL:
            continue
        total += len(simples)
        partes.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in simples) + "Z")
    return "".join(partes), total


def montar_svg(caminho: str) -> str:
    h = f"{ALTURA_SVG:.1f}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGURA_SVG:.0f} {h}" preserveAspectRatio="none">'
            f"<title>Divisas dos estados do Brasil</title>"
            f"<desc>Fonte: {FONTE}. Linhas simplificadas para o mapa de satélite da Janela de Campo (generalização cartográfica: "
            f"não são as características originais da malha). Desenho ilustrativo; o IBGE não define os limites estaduais.</desc>"
            f'<defs><path id="d" d="{caminho}" fill="none" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></defs>'
            f'<use href="#d" stroke="#0b1220" stroke-opacity=".55" stroke-width="2.6"/>'
            f'<use href="#d" stroke="#ffffff" stroke-opacity=".9" stroke-width="1"/>'
            f"</svg>\n")


def abrir_zip(caminho: Path | None) -> bytes:
    """Bytes do .shp dentro do zip do IBGE (baixa o arquivo oficial quando nenhum é indicado)."""
    if caminho is None:
        destino = Path(tempfile.gettempdir()) / "BR_UF_2025.zip"
        if not destino.exists():
            print(f"baixando {URL}", file=sys.stderr)
            urllib.request.urlretrieve(URL, destino)  # nosec B310 — URL fixa (https) do IBGE
        caminho = destino
    with zipfile.ZipFile(caminho) as z:
        nome = next(n for n in z.namelist() if n.lower().endswith(".shp"))
        return z.read(nome)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip", type=Path, help="BR_UF_2025.zip já baixado")
    ap.add_argument("--tolerancia", type=float, default=0.8, help="tolerância da simplificação (unidades do SVG, largura 1000)")
    ap.add_argument("--saida", type=Path, default=SAIDA)
    a = ap.parse_args(argv)
    aneis = ler_aneis(abrir_zip(a.zip))
    caminho, total = caminho_svg(aneis, a.tolerancia)
    svg = montar_svg(caminho)
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_text(svg, encoding="utf-8", newline="\n")
    print(f"gravado {a.saida} ({len(svg) // 1024} KB, {len(aneis)} anéis de origem, {total} pontos depois de simplificar)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
