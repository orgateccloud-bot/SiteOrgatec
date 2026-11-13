"""Malha rodoviária do Brasil para o mapa público de alertas da Janela do Transporte, recortada por estado.

Grava em site/assets/geo/:
    ufs.json                      contorno simplificado e retângulo de cada UF (mapa do Brasil e aproximação no estado)
    rodovias/BR.json              rodovias federais do país, bem simplificadas (visão do Brasil)
    rodovias/<UF>.json            rodovias com sigla (federais e estaduais) do estado: mapa, cartões e cruzamento com os alertas
    rodovias/<UF>-locais.json     estradas sem sigla (municipais e vicinais) do estado: só desenho, carregadas a pedido

Fontes (IBGE):
- Base Cartográfica Contínua do Brasil 1:250.000 (BC250), versão 2023, camada rod_trecho_rodoviario_l (130 mil trechos). O zip
  completo tem 806 MB; o gerador lê só essa camada por pedido parcial (HTTP Range).
- Malha Municipal Digital 2025, limites das UFs (BR_UF_2025.zip), a mesma das divisas (tools/gerar_divisas_ufs.py).
Licença: a documentação da BC250 2023 não traz licença própria; vale a nota metodológica 01/2026 do IBGE ("Informações técnicas e
legais para a utilização dos dados publicados"): compatível com CC BY 4.0, com crédito ao IBGE e aviso de que a geometria foi
generalizada. Pendência: confirmar com o responsável se a nota cobre a BC250 (docs/ideias/mapa-alertas-publico.md).
A escala é 1:250.000: a malha local é incompleta e sem nome. Serve de contexto, não de guia de rota.

Não usa o Google: os termos do Google Maps proíbem levar a rota dele a um mapa que não seja do Google.

Uso:
    python tools/gerar_rodovias.py                      baixa as duas fontes do IBGE e grava tudo
    python tools/gerar_rodovias.py --pasta CAMINHO      usa rod_trecho_rodoviario_l.shp/.dbf já extraídos
    python tools/gerar_rodovias.py --ufs CAMINHO.zip    usa um BR_UF_2025.zip já baixado

Só a biblioteca padrão. Os JSON ficam no repositório; os shapefiles não.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
import tempfile
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from tools.gerar_divisas_ufs import URL as URL_UFS  # noqa: E402
from tools.gerar_divisas_ufs import simplificar  # noqa: E402

SAIDA = RAIZ / "site" / "assets" / "geo"
URL = ("https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2023/shapefile/"
       "bc250_shapefile._2023_11_23.zip")
CAMADA = "rod_trecho_rodoviario_l"
FONTE = "IBGE, Base Cartográfica Contínua do Brasil 1:250.000 (BC250) 2023, trechos rodoviários"
FONTE_UFS = "IBGE, Malha Municipal Digital e Áreas Territoriais 2025 (limites das Unidades da Federação)"
LICENCA = "nota metodológica 01/2026 do IBGE (compatível com CC BY 4.0, com crédito ao IBGE)"
AVISO = "Traçado simplificado a partir da BC250 do IBGE (geometria generalizada; ilustrativo, não serve para navegação)."
USER_AGENT = "orgatec.io/1.0 (https://orgatec.io)"

UFS = ("AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR",
       "RS", "SC", "SE", "SP", "TO")
# Tolerâncias da simplificação, em graus (0,01 ≈ 1 km)
TOL_BRASIL, TOL_UF, TOL_LOCAL, TOL_CONTORNO = 0.03, 0.006, 0.01, 0.02
MENOR_KM = {"brasil": 15.0, "uf": 2.0, "local": 3.0}  # linhas menores que isso saem (sobras de cruzamentos e acessos)
ILHA_LONGE = 1.5  # graus além do retângulo do continente
FORA_DE_USO = ("Abandonada", "Destruída", "Planejada", "Em construção")

Ponto = tuple[float, float]  # (lon, lat), como no shapefile


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


def baixar_rodovias() -> tuple[bytes, bytes]:
    print(f"lendo {CAMADA} de {URL} (só a camada, por HTTP Range)", file=sys.stderr)
    with zipfile.ZipFile(ZipRemoto(URL)) as z:  # type: ignore[arg-type]
        return z.read(f"{CAMADA}.shp"), z.read(f"{CAMADA}.dbf")


def abrir_ufs(caminho: Path | None) -> tuple[bytes, bytes]:
    if caminho is None:
        caminho = Path(tempfile.gettempdir()) / "BR_UF_2025.zip"
        if not caminho.exists():
            print(f"baixando {URL_UFS}", file=sys.stderr)
            urllib.request.urlretrieve(URL_UFS, caminho)  # nosec B310 — URL fixa (https) do IBGE
    with zipfile.ZipFile(caminho) as z:
        nomes = {n.lower().rsplit(".", 1)[-1]: n for n in z.namelist()}
        return z.read(nomes["shp"]), z.read(nomes["dbf"])


def ler_formas(shp: bytes, tipo_esperado: int) -> list[list[list[Ponto]]]:
    """Por registro, as partes (lista de pontos lon, lat) de um shapefile de linhas (tipo 3) ou de polígonos (tipo 5)."""
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
        if tipo != tipo_esperado:
            raise ValueError(f"tipo de forma {tipo} não suportado (esperado {tipo_esperado})")
        n_partes, n_pontos = struct.unpack("<ii", corpo[36:44])
        partes = list(struct.unpack(f"<{n_partes}i", corpo[44:44 + 4 * n_partes])) + [n_pontos]
        base = 44 + 4 * n_partes
        pontos = list(struct.iter_unpack("<dd", corpo[base:base + 16 * n_pontos]))
        registros.append([pontos[a:b] for a, b in zip(partes, partes[1:])])
    return registros


def ler_linhas(shp: bytes) -> list[list[list[Ponto]]]:
    return ler_formas(shp, 3)


def ler_colunas(dbf: bytes, *nomes: str) -> list[tuple[str, ...]]:
    """Colunas de texto de cada registro do .dbf (UTF-8, conforme o .cpg do IBGE). O nome da coluna não diferencia maiúsculas."""
    n, cabecalho, tam_registro = struct.unpack("<IHH", dbf[4:12])
    campos, pos, inicio = {}, 32, 1
    while dbf[pos] != 0x0D:
        nome, tam = dbf[pos:pos + 11].split(b"\0")[0].decode("ascii").lower(), dbf[pos + 16]
        campos[nome] = (inicio, tam)
        inicio += tam
        pos += 32
    faltam = [c for c in nomes if c.lower() not in campos]
    if faltam:
        raise ValueError(f"o .dbf não tem a(s) coluna(s) {', '.join(faltam)}")
    cortes = [campos[c.lower()] for c in nomes]
    saida = []
    for i in range(n):
        base = cabecalho + i * tam_registro
        saida.append(tuple(dbf[base + a:base + a + t].decode("utf-8", "replace").strip() for a, t in cortes))
    return saida


_SIGLA = re.compile(r"(?<![A-Z])([A-Z]{2,3})[- ]?(\d{3})(?!\d)")
_SNV = re.compile(r"^(\d{3})([BE])([A-Z]{2})\d{4}$")  # código do SNV/DNIT: 156BAP0170 = BR-156 no AP; 170EMG0280 = MG-170


def siglas_da(texto: str) -> set[str]:
    """Siglas de rodovia de um trecho, no formato 'XX-000': 'BR-153;BR-060', 'BR-430 BA-464', 'Rodovia MG-403', 'LMG 628' e o
    código do SNV. Trecho com sobreposição devolve as duas; nome por extenso ou código solto devolve vazio (vira estrada local)."""
    t = texto.strip().upper()
    snv = _SNV.match(t)
    if snv:
        return {("BR" if snv[2] == "B" else snv[3]) + "-" + snv[1]}
    return {f"{prefixo}-{numero}" for prefixo, numero in _SIGLA.findall(t)}


def juntar(partes: list[list[Ponto]], casas: int = 5) -> list[list[Ponto]]:
    """Encadeia partes que se tocam pelas pontas (os trechos da BC250 são curtos): menos linhas e menos pontos no JSON.
    Índice pelas pontas arredondadas, para a malha local (dezenas de milhares de partes por estado)."""
    def chave(p: Ponto) -> tuple[float, float]:
        return (round(p[0], casas), round(p[1], casas))

    restantes = {i: p for i, p in enumerate(partes) if len(p) >= 2}
    pontas: dict[tuple[float, float], set[int]] = {}
    for i, p in restantes.items():
        pontas.setdefault(chave(p[0]), set()).add(i)
        pontas.setdefault(chave(p[-1]), set()).add(i)

    def tirar(i: int) -> list[Ponto]:
        p = restantes.pop(i)
        pontas[chave(p[0])].discard(i)
        pontas[chave(p[-1])].discard(i)
        return p

    linhas = []
    while restantes:
        linha = list(tirar(next(iter(restantes))))
        for no_fim in (True, False):
            while True:
                ponta = linha[-1] if no_fim else linha[0]
                vizinhos = pontas.get(chave(ponta))
                if not vizinhos:
                    break
                p = list(tirar(next(iter(vizinhos))))
                if no_fim:
                    linha += (p if chave(p[0]) == chave(ponta) else p[::-1])[1:]
                else:
                    linha = (p if chave(p[-1]) == chave(ponta) else p[::-1])[:-1] + linha
        linhas.append(linha)
    return linhas


def _km(linha: list[Ponto]) -> float:
    return sum(math.hypot((b[0] - a[0]) * math.cos(math.radians(a[1])), b[1] - a[1]) for a, b in zip(linha, linha[1:])) * 111.2


def enxugar(partes: list[list[Ponto]], tol: float, menor_km: float, casas: int) -> list[list[list[float]]]:
    """Junta, simplifica, descarta as sobras e devolve as linhas como [[lat, lon], ...] (a ordem dos alertas)."""
    linhas = []
    for linha in juntar(partes):
        if _km(linha) < menor_km:
            continue
        linhas.append([[round(lat, casas), round(lon, casas)] for lon, lat in simplificar(linha, tol)])
    linhas.sort(key=len, reverse=True)
    return linhas


# ---------- estados ----------
def _dentro(p: Ponto, anel: list[Ponto]) -> bool:
    x, y = p
    dentro, j = False, len(anel) - 1
    for i in range(len(anel)):
        (xi, yi), (xj, yj) = anel[i], anel[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            dentro = not dentro
        j = i
    return dentro


class Estados:
    """Limites das UFs para dizer em que estado cai cada trecho (pelo ponto do meio)."""

    def __init__(self, shp: bytes, dbf: bytes) -> None:
        self.itens = []
        for partes, (sigla, nome) in zip(ler_formas(shp, 5), ler_colunas(dbf, "SIGLA_UF", "NM_UF")):
            aneis = [simplificar(a, 0.004) for a in partes if math.hypot(max(p[0] for p in a) - min(p[0] for p in a),
                                                                         max(p[1] for p in a) - min(p[1] for p in a)) > 0.05]
            caixas = [(min(p[0] for p in a), min(p[1] for p in a), max(p[0] for p in a), max(p[1] for p in a)) for a in aneis]
            # Ilhas oceânicas distantes (Trindade, Fernando de Noronha, São Pedro e São Paulo) ficam fora: esticariam o recorte do
            # estado por centenas de quilômetros de mar, e não têm rodovia na base.
            pw, ps, pl, pn = max(caixas, key=lambda c: (c[2] - c[0]) * (c[3] - c[1]))
            perto = [i for i, c in enumerate(caixas) if c[0] <= pl + ILHA_LONGE and c[2] >= pw - ILHA_LONGE and c[1] <= pn + ILHA_LONGE and c[3] >= ps - ILHA_LONGE]
            aneis, caixas = [aneis[i] for i in perto], [caixas[i] for i in perto]
            lons, lats = [p[0] for a in aneis for p in a], [p[1] for a in aneis for p in a]
            self.itens.append({"uf": sigla, "nome": nome, "aneis": aneis, "caixas": caixas, "caixa": (min(lons), min(lats), max(lons), max(lats))})
        self.itens.sort(key=lambda e: e["uf"])

    def uf_de(self, p: Ponto) -> str | None:
        perto = None
        for e in self.itens:
            w, s, l, n = e["caixa"]
            if not (w - 0.05 <= p[0] <= l + 0.05 and s - 0.05 <= p[1] <= n + 0.05):
                continue
            perto = perto or e["uf"]
            dentro = False
            for anel, (aw, as_, al, an) in zip(e["aneis"], e["caixas"]):
                if aw <= p[0] <= al and as_ <= p[1] <= an and _dentro(p, anel):
                    dentro = not dentro  # anel interno (buraco) inverte
            if dentro:
                return e["uf"]
        return perto  # trecho na divisa ou no litoral, fora do contorno simplificado: fica com o primeiro estado do retângulo

    def contornos(self) -> list[dict]:
        saida = []
        for e in self.itens:
            aneis = []
            for a in e["aneis"]:
                s = simplificar(a, TOL_CONTORNO)
                if len(s) >= 4:
                    aneis.append([[round(lat, 3), round(lon, 3)] for lon, lat in s])
            w, s_, l, n = e["caixa"]
            saida.append({"uf": e["uf"], "nome": e["nome"], "caixa": [round(s_, 3), round(w, 3), round(n, 3), round(l, 3)], "aneis": aneis})
        return saida


def separar(shp: bytes, dbf: bytes, estados: Estados) -> tuple[dict[str, dict[str, list]], dict[str, list], dict[str, list]]:
    """(com sigla por UF e rodovia, locais por UF, federais do país por rodovia)."""
    registros = ler_linhas(shp)
    atributos = ler_colunas(dbf, "sigla", "situacaofi", "operaciona")
    if len(registros) != len(atributos):
        raise ValueError(f"{len(registros)} formas e {len(atributos)} registros no .dbf")
    nomeadas: dict[str, dict[str, list]] = {uf: {} for uf in UFS}
    locais: dict[str, list] = {uf: [] for uf in UFS}
    federais: dict[str, list] = {}
    for partes, (sigla, situacao, operacional) in zip(registros, atributos):
        if situacao in FORA_DE_USO or operacional == "Não":
            continue
        siglas = siglas_da(sigla)
        for parte in partes:
            if len(parte) < 2:
                continue
            uf = estados.uf_de(parte[len(parte) // 2])
            if uf is None:
                continue
            if not siglas:
                locais[uf].append(parte)
                continue
            for s in siglas:
                nomeadas[uf].setdefault(s, []).append(parte)
                if s.startswith("BR-"):
                    federais.setdefault(s, []).append(parte)
    return nomeadas, locais, federais


def _gravar(caminho: Path, dados: dict) -> int:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return caminho.stat().st_size


def _ordem(sigla: str) -> tuple[int, str]:
    return (0 if sigla.startswith("BR-") else 1, sigla)


def gerar(shp: bytes, dbf: bytes, estados: Estados, saida: Path = SAIDA) -> dict[str, int]:
    nomeadas, locais, federais = separar(shp, dbf, estados)
    base = {"fonte": FONTE, "licenca": LICENCA, "aviso": AVISO, "gerado_em": date.today().isoformat()}
    tamanhos = {"ufs.json": _gravar(saida / "ufs.json", {"fonte": FONTE_UFS, "licenca": LICENCA,
                                                        "aviso": "Contornos simplificados; o IBGE não define os limites, e o desenho é ilustrativo.",
                                                        "gerado_em": base["gerado_em"], "ufs": estados.contornos()})}
    brasil = [{"sigla": s, "linhas": enxugar(federais[s], TOL_BRASIL, MENOR_KM["brasil"], 3)} for s in sorted(federais)]
    tamanhos["rodovias/BR.json"] = _gravar(saida / "rodovias" / "BR.json", {**base, "rodovias": [r for r in brasil if r["linhas"]]})
    for uf in UFS:
        rodovias = [{"sigla": s, "linhas": enxugar(nomeadas[uf][s], TOL_UF, MENOR_KM["uf"], 4)} for s in sorted(nomeadas[uf], key=_ordem)]
        tamanhos[f"rodovias/{uf}.json"] = _gravar(saida / "rodovias" / f"{uf}.json", {**base, "uf": uf, "rodovias": [r for r in rodovias if r["linhas"]]})
        tamanhos[f"rodovias/{uf}-locais.json"] = _gravar(saida / "rodovias" / f"{uf}-locais.json",
                                                         {**base, "uf": uf, "linhas": enxugar(locais[uf], TOL_LOCAL, MENOR_KM["local"], 3)})
    return tamanhos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pasta", type=Path, help="pasta com rod_trecho_rodoviario_l.shp e .dbf já extraídos")
    ap.add_argument("--ufs", type=Path, help="BR_UF_2025.zip já baixado")
    args = ap.parse_args(argv)
    if args.pasta:
        shp, dbf = (args.pasta / f"{CAMADA}.shp").read_bytes(), (args.pasta / f"{CAMADA}.dbf").read_bytes()
    else:
        shp, dbf = baixar_rodovias()
    tamanhos = gerar(shp, dbf, Estados(*abrir_ufs(args.ufs)))
    total = sum(tamanhos.values())
    maiores = sorted(tamanhos.items(), key=lambda kv: -kv[1])[:6]
    print(f"{len(tamanhos)} arquivos em {SAIDA.relative_to(RAIZ)}, {total / 1e6:.1f} MB no total; maiores: " +
          ", ".join(f"{k} {v // 1024} KB" for k, v in maiores))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
