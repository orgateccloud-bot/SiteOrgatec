"""Traçado das rodovias federais dos corredores da ORGATEC (BR-153, BR-060, BR-010 e BR-230 em GO, TO e PA) para o mapa
público de alertas da Janela do Transporte. Grava site/assets/geo/rodovias-corredores.json, lido pela página e pela rotina
dos alertas (o resumo por rodovia).

Fonte: IBGE, Base Cartográfica Contínua do Brasil 1:250.000 (BC250), versão 2023, camada rod_trecho_rodoviario_l. O arquivo
completo tem 806 MB; o gerador lê só os membros da camada de rodovias pelo pedido parcial (HTTP Range) do zip oficial.
Licença: a documentação técnica da BC250 2023 não traz licença própria; vale a nota metodológica 01/2026 do IBGE
("Informações técnicas e legais para a utilização dos dados publicados"), a mesma das divisas (tools/gerar_divisas_ufs.py):
licença compatível com CC BY 4.0, com crédito ao IBGE e aviso de que a geometria foi generalizada. Pendência: conferir com o
responsável se a nota cobre a BC250 (docs/ideias/mapa-alertas-publico.md).

Não usa o Google: os termos do Google Maps proíbem levar a rota dele a um mapa que não seja do Google.

Uso:
    python tools/gerar_rodovias.py                      baixa só a camada de rodovias do zip do IBGE e grava o JSON
    python tools/gerar_rodovias.py --pasta CAMINHO      usa rod_trecho_rodoviario_l.shp/.dbf já extraídos
    python tools/gerar_rodovias.py --tolerancia 0.01    tolerância da simplificação, em graus (padrão 0,01 ≈ 1 km)

Só a biblioteca padrão. O JSON fica no repositório; o shapefile não.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from tools.gerar_divisas_ufs import simplificar  # noqa: E402

SAIDA = RAIZ / "site" / "assets" / "geo" / "rodovias-corredores.json"
URL = ("https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2023/shapefile/"
       "bc250_shapefile._2023_11_23.zip")
CAMADA = "rod_trecho_rodoviario_l"
FONTE = "IBGE, Base Cartográfica Contínua do Brasil 1:250.000 (BC250) 2023, trechos rodoviários"
AVISO = "Traçado simplificado a partir da BC250 do IBGE (geometria generalizada; ilustrativo, não serve para navegação)."
USER_AGENT = "orgatec.io/1.0 (https://orgatec.io)"

# Mesma região de backend/transporte/alertas/publico.py (REGIAO): GO, TO e PA até a BR-230. Um teste confere.
OESTE, LESTE, NORTE, SUL = -56.5, -45.5, -1.0, -19.6
RODOVIAS = ("BR-153", "BR-060", "BR-010", "BR-230")


class ZipRemoto:
    """Arquivo somente leitura sobre HTTP Range: o zipfile lê o diretório central e só os membros pedidos."""

    def __init__(self, url: str, bloco: int = 1 << 20) -> None:
        self.url, self.pos, self.bloco = url, 0, bloco
        pedido = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(pedido, timeout=60) as r:  # nosec B310 — URL fixa (https) do IBGE
            self.tamanho = int(r.headers["Content-Length"])
        self._cache: tuple[int, bytes] = (0, b"")

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, deslocamento: int, de_onde: int = 0) -> int:
        self.pos = {0: deslocamento, 1: self.pos + deslocamento, 2: self.tamanho + deslocamento}[de_onde]
        return self.pos

    def read(self, n: int | None = -1) -> bytes:
        if n is None or n < 0:
            n = self.tamanho - self.pos
        if n == 0 or self.pos >= self.tamanho:
            return b""
        ini, dados = self._cache
        if not (ini <= self.pos and self.pos + n <= ini + len(dados)):
            fim = min(self.tamanho, self.pos + max(n, self.bloco)) - 1
            pedido = urllib.request.Request(self.url, headers={"User-Agent": USER_AGENT, "Range": f"bytes={self.pos}-{fim}"})
            with urllib.request.urlopen(pedido, timeout=120) as r:  # nosec B310 — URL fixa (https) do IBGE
                self._cache = (self.pos, r.read())
            ini, dados = self._cache
        parte = dados[self.pos - ini:self.pos - ini + n]
        self.pos += len(parte)
        return parte


def baixar() -> tuple[bytes, bytes]:
    print(f"lendo {CAMADA} de {URL} (só a camada, por HTTP Range)", file=sys.stderr)
    with zipfile.ZipFile(ZipRemoto(URL)) as z:  # type: ignore[arg-type]
        return z.read(f"{CAMADA}.shp"), z.read(f"{CAMADA}.dbf")


def ler_linhas(shp: bytes) -> list[list[list[tuple[float, float]]]]:
    """Por registro, as partes (lista de pontos lon, lat) de um shapefile de linhas (tipo 3)."""
    if struct.unpack(">i", shp[0:4])[0] != 9994:
        raise ValueError("não é um shapefile")
    registros, pos = [], 100
    while pos + 8 <= len(shp):
        tamanho = struct.unpack(">i", shp[pos + 4:pos + 8])[0] * 2
        corpo = shp[pos + 8:pos + 8 + tamanho]
        pos += 8 + tamanho
        tipo = struct.unpack("<i", corpo[0:4])[0]
        if tipo == 0:
            registros.append([])
            continue
        if tipo != 3:
            raise ValueError(f"tipo de forma {tipo} não suportado (esperado 3, linha)")
        n_partes, n_pontos = struct.unpack("<ii", corpo[36:44])
        partes = list(struct.unpack(f"<{n_partes}i", corpo[44:44 + 4 * n_partes])) + [n_pontos]
        base = 44 + 4 * n_partes
        pontos = [struct.unpack("<dd", corpo[base + 16 * i:base + 16 * i + 16]) for i in range(n_pontos)]
        registros.append([pontos[a:b] for a, b in zip(partes, partes[1:])])
    return registros


def ler_siglas(dbf: bytes) -> list[str]:
    """Coluna `sigla` de cada registro do .dbf (UTF-8, conforme o .cpg do IBGE)."""
    n, cabecalho, tam_registro = struct.unpack("<IHH", dbf[4:12])
    campos, pos = [], 32
    while dbf[pos] != 0x0D:
        campos.append((dbf[pos:pos + 11].split(b"\0")[0].decode("ascii"), dbf[pos + 16]))
        pos += 32
    inicio = 1
    for nome, tam in campos:
        if nome == "sigla":
            break
        inicio += tam
    else:
        raise ValueError("o .dbf não tem a coluna sigla")
    tam_sigla = dict(campos)["sigla"]
    return [dbf[cabecalho + i * tam_registro + inicio:cabecalho + i * tam_registro + inicio + tam_sigla].decode("utf-8", "replace").strip()
            for i in range(n)]


def siglas_da(texto: str) -> set[str]:
    """'BR-153;BR-060' ou 'BR-153/BR-060' → {'BR-153', 'BR-060'} (trechos com sobreposição de rodovias)."""
    return {s.strip().upper().replace(" ", "") for s in texto.replace("/", ";").replace(",", ";").split(";") if s.strip()}


def dentro(p: tuple[float, float]) -> bool:
    return OESTE <= p[0] <= LESTE and SUL <= p[1] <= NORTE


def juntar(partes: list[list[tuple[float, float]]], folga: float = 1e-6) -> list[list[tuple[float, float]]]:
    """Encadeia partes que se tocam pelas pontas (os trechos da BC250 são curtos): menos linhas e menos pontos no JSON."""
    restantes = [p[:] for p in partes if len(p) >= 2]
    linhas = []

    def igual(a: tuple[float, float], b: tuple[float, float]) -> bool:
        return abs(a[0] - b[0]) <= folga and abs(a[1] - b[1]) <= folga

    while restantes:
        linha = restantes.pop()
        mudou = True
        while mudou:
            mudou = False
            for i, p in enumerate(restantes):
                if igual(linha[-1], p[0]):
                    linha += p[1:]
                elif igual(linha[-1], p[-1]):
                    linha += p[::-1][1:]
                elif igual(linha[0], p[-1]):
                    linha = p[:-1] + linha
                elif igual(linha[0], p[0]):
                    linha = p[::-1][:-1] + linha
                else:
                    continue
                restantes.pop(i)
                mudou = True
                break
        linhas.append(linha)
    return linhas


def montar(shp: bytes, dbf: bytes, tol: float) -> dict:
    registros, siglas = ler_linhas(shp), ler_siglas(dbf)
    if len(registros) != len(siglas):
        raise ValueError(f"{len(registros)} formas e {len(siglas)} registros no .dbf")
    por_rodovia: dict[str, list[list[tuple[float, float]]]] = {r: [] for r in RODOVIAS}
    for partes, sigla in zip(registros, siglas):
        alvo = siglas_da(sigla) & set(RODOVIAS)
        for parte in partes:
            pontos = [p for p in parte if dentro(p)]
            if len(pontos) < 2:
                continue
            for r in alvo:
                por_rodovia[r].append(pontos)
    saida = []
    for r in RODOVIAS:
        linhas = []
        for linha in juntar(por_rodovia[r]):
            simples = simplificar(linha, tol)
            km = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(simples, simples[1:])) * 111
            if km < 2:  # sobras de cruzamentos e acessos
                continue
            linhas.append([[round(lat, 4), round(lon, 4)] for lon, lat in simples])  # (lat, lon), como os alertas
        saida.append({"sigla": r, "linhas": linhas})
    return {"fonte": FONTE, "licenca": "nota metodológica 01/2026 do IBGE (compatível com CC BY 4.0, com crédito ao IBGE)",
            "aviso": AVISO, "url": URL, "gerado_em": date.today().isoformat(), "tolerancia_graus": tol,
            "regiao": {"oeste": OESTE, "leste": LESTE, "norte": NORTE, "sul": SUL}, "rodovias": saida}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pasta", type=Path, help="pasta com rod_trecho_rodoviario_l.shp e .dbf já extraídos")
    ap.add_argument("--tolerancia", type=float, default=0.01)
    args = ap.parse_args(argv)
    if args.pasta:
        shp, dbf = (args.pasta / f"{CAMADA}.shp").read_bytes(), (args.pasta / f"{CAMADA}.dbf").read_bytes()
    else:
        shp, dbf = baixar()
    dados = montar(shp, dbf, args.tolerancia)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    pontos = sum(len(linha) for r in dados["rodovias"] for linha in r["linhas"])
    resumo = ", ".join(f'{r["sigla"]} {len(r["linhas"])} linha(s)' for r in dados["rodovias"])
    print(f"{SAIDA.relative_to(RAIZ)}: {pontos} pontos ({resumo}), {SAIDA.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
