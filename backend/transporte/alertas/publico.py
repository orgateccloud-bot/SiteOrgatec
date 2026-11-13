"""Resumo público dos alertas para o mapa da Janela do Transporte (empresarial/janela.html), Brasil inteiro.

Só dados de fontes públicas, sem viagem, posição, cliente ou motorista. A rotina dos alertas grava, a cada execução:

- `_sistema/alertas_publicos/atual` (nacional): avisos do INMET com o polígono simplificado e os estados em que cruzam rodovia,
  focos de fogo do NASA FIRMS das últimas 24 h agrupados em células de 0,25° (o país passa de dezenas de milhares de focos por dia
  na seca: ponto a ponto não cabe no registro nem no navegador) e o resumo por estado;
- `_sistema/alertas_publicos/<UF>` (um por estado): as rodovias com sigla que têm aviso no traçado ou foco a até 5 km, e os focos
  junto a rodovias (limitados), para o mapa aproximado no estado.

A malha vem de site/assets/geo/rodovias/<UF>.json (IBGE BC250, tools/gerar_rodovias.py): federais e estaduais com sigla.
As estradas locais sem sigla só são desenhadas pela página; não entram no cruzamento. A API devolve os resumos sem login.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.transporte.alertas.cruzamento import RAIO_FOGO_KM, dentro
from backend.transporte.alertas.fontes import AlertaExterno, Foco, ResultadoFonte, rank
from backend.transporte.geo import simplificar

PASTA_RODOVIAS = Path(__file__).resolve().parents[3] / "site" / "assets" / "geo" / "rodovias"
UFS = ("AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR",
       "RS", "SC", "SE", "SP", "TO")
# Brasil com folga: (sul, oeste, norte, leste), no formato das caixas da rotina. Mesmo recorte do mapa (um teste confere).
REGIAO = (-34.0, -74.5, 5.5, -34.5)
JANELA_FOCOS = timedelta(hours=24)
PASSO_CALOR = 0.25  # célula da mancha de fogo, em graus (~27 km)
PASSO_INDICE = 0.1  # célula do índice espacial dos trechos (~11 km, maior que o raio de 5 km: basta olhar as vizinhas)
PASSO_AMOSTRA = 0.05  # ~5 km: o traçado simplificado tem trechos retos longos, e o aviso pode cortar só o meio de um deles
MAX_FOCOS_UF = 1500  # focos junto a rodovias enviados por estado (os mais recentes); a contagem por rodovia usa todos
MAX_PONTOS_ANEL = 200

Coord = tuple[float, float]  # (lat, lon)


@dataclass
class Rodovia:
    uf: str
    sigla: str
    linhas: tuple[tuple[Coord, ...], ...]
    caixa: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # (sul, oeste, norte, leste)
    amostras: list[Coord] = field(default_factory=list)

    def __post_init__(self) -> None:
        lats = [p[0] for ln in self.linhas for p in ln]
        lons = [p[1] for ln in self.linhas for p in ln]
        self.caixa = (min(lats), min(lons), max(lats), max(lons))
        for linha in self.linhas:
            self.amostras.append(linha[0])
            for (la0, lo0), (la1, lo1) in zip(linha, linha[1:]):
                n = max(1, math.ceil(max(abs(la1 - la0), abs(lo1 - lo0)) / PASSO_AMOSTRA))
                self.amostras += [(la0 + (la1 - la0) * i / n, lo0 + (lo1 - lo0) * i / n) for i in range(1, n + 1)]


class Malha:
    """Rodovias com sigla de todos os estados e um índice dos trechos por célula, para achar o que está a até 5 km de um foco."""

    def __init__(self, rodovias: list[Rodovia]) -> None:
        self.rodovias = rodovias
        self.indice: dict[tuple[int, int], list[tuple[int, Coord, Coord]]] = {}
        for i, r in enumerate(rodovias):
            for linha in r.linhas:
                for a, b in zip(linha, linha[1:]):
                    for ci in range(_celula(min(a[0], b[0])), _celula(max(a[0], b[0])) + 1):
                        for cj in range(_celula(min(a[1], b[1])), _celula(max(a[1], b[1])) + 1):
                            self.indice.setdefault((ci, cj), []).append((i, a, b))

    @classmethod
    def de(cls, por_uf: dict[str, list[tuple[str, tuple[tuple[Coord, ...], ...]]]]) -> Malha:
        return cls([Rodovia(uf, sigla, linhas) for uf, lista in por_uf.items() for sigla, linhas in lista])

    def perto(self, lat: float, lon: float, raio_km: float) -> set[int]:
        """Índices das rodovias com algum trecho a até raio_km do ponto."""
        ci, cj, achadas = _celula(lat), _celula(lon), set()
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for i, a, b in self.indice.get((ci + di, cj + dj), ()):
                    if i not in achadas and _dist_km((lat, lon), a, b) <= raio_km:
                        achadas.add(i)
        return achadas


def _celula(v: float) -> int:
    return math.floor(v / PASSO_INDICE)


def _dist_km(p: Coord, a: Coord, b: Coord) -> float:
    """Distância do ponto ao segmento, em km (aproximação plana, boa para poucos quilômetros)."""
    k = math.cos(math.radians(p[0]))
    ax, ay, bx, by = (a[1] - p[1]) * k, a[0] - p[0], (b[1] - p[1]) * k, b[0] - p[0]
    dx, dy = bx - ax, by - ay
    c = dx * dx + dy * dy
    t = max(0.0, min(1.0, -(ax * dx + ay * dy) / c)) if c else 0.0
    return math.hypot(ax + t * dx, ay + t * dy) * 111.2


@lru_cache(maxsize=1)
def malha() -> Malha:
    """Lê os arquivos por estado. Estado sem arquivo fica sem resumo por rodovia (o mapa segue com avisos e manchas)."""
    rodovias = []
    for uf in UFS:
        arquivo = PASTA_RODOVIAS / f"{uf}.json"
        if not arquivo.exists():
            continue
        for r in json.loads(arquivo.read_text(encoding="utf-8"))["rodovias"]:
            rodovias.append(Rodovia(uf, r["sigla"], tuple(tuple((p[0], p[1]) for p in linha) for linha in r["linhas"])))
    return Malha(rodovias)


def _na_regiao(lat: float, lon: float) -> bool:
    s, w, n, e = REGIAO
    return s <= lat <= n and w <= lon <= e


def _caixa_anel(anel: tuple[Coord, ...]) -> tuple[float, float, float, float]:
    lats, lons = [p[0] for p in anel], [p[1] for p in anel]
    return (min(lats), min(lons), max(lats), max(lons))


def _sobrepoe(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _aviso(a: AlertaExterno, agora: datetime, ufs: list[str]) -> dict[str, Any]:
    aneis = [[[round(p[0], 3), round(p[1], 3)] for p in simplificar(list(anel), MAX_PONTOS_ANEL)] for anel in a.poligonos if _sobrepoe(_caixa_anel(anel), REGIAO)]
    return {"id": a.id, "tipo": a.tipo, "gravidade": a.gravidade, "titulo": a.titulo, "inicio": a.inicio.isoformat(), "fim": a.fim.isoformat(),
            "vigente": a.inicio <= agora,  # o INMET publica também os avisos dos próximos dias: o mapa os mostra à parte
            "riscos": a.riscos, "instrucoes": a.instrucoes, "link": a.link, "fonte": a.fonte, "ufs": ufs, "poligonos": aneis}


def _cruzar_avisos(avisos: list[AlertaExterno], m: Malha) -> dict[int, list[AlertaExterno]]:
    """Por rodovia (índice na malha), os avisos cuja área contém algum ponto do traçado."""
    saida: dict[int, list[AlertaExterno]] = {}
    for a in avisos:
        aneis = [(anel, _caixa_anel(anel)) for anel in a.poligonos]
        for i, r in enumerate(m.rodovias):
            for anel, caixa in aneis:
                if _sobrepoe(r.caixa, caixa) and any(caixa[0] <= p[0] <= caixa[2] and caixa[1] <= p[1] <= caixa[3] and dentro(p, anel) for p in r.amostras):
                    saida.setdefault(i, []).append(a)
                    break
    return saida


def _pior(avisos: list[AlertaExterno]) -> str:
    return max((a.gravidade for a in avisos), key=rank, default="")


def montar(fontes: dict[str, ResultadoFonte], agora: datetime) -> dict[str, dict[str, Any]]:
    """Resumos gravados pela rotina: {"atual": nacional, "AC": ..., "TO": ...}.
    Fonte fora do ar aparece como indisponível (o mapa avisa em vez de mostrar 'sem risco')."""
    m = malha()
    avisos = [a for r in fontes.values() for a in r.alertas
              if a.origem == "inmet" and a.fim > agora and any(_sobrepoe(_caixa_anel(anel), REGIAO) for anel in a.poligonos)]
    avisos.sort(key=lambda a: (-rank(a.gravidade), a.inicio))
    focos = [f for r in fontes.values() for f in r.focos if f.origem == "firms" and f.quando >= agora - JANELA_FOCOS and _na_regiao(f.lat, f.lon)]
    focos.sort(key=lambda f: f.quando, reverse=True)

    por_rodovia = _cruzar_avisos(avisos, m)
    focos_rodovia: dict[int, int] = {}
    focos_uf: dict[str, list[list[float]]] = {uf: [] for uf in UFS}
    focos_uf_total: dict[str, int] = dict.fromkeys(UFS, 0)
    calor: dict[tuple[int, int], int] = {}
    for f in focos:
        celula = (math.floor(f.lat / PASSO_CALOR), math.floor(f.lon / PASSO_CALOR))
        calor[celula] = calor.get(celula, 0) + 1
        achadas = m.perto(f.lat, f.lon, RAIO_FOGO_KM)
        for i in achadas:
            focos_rodovia[i] = focos_rodovia.get(i, 0) + 1
        for uf in {m.rodovias[i].uf for i in achadas}:
            focos_uf_total[uf] += 1
            if len(focos_uf[uf]) < MAX_FOCOS_UF:
                focos_uf[uf].append([round(f.lat, 3), round(f.lon, 3)])

    por_uf: dict[str, list[dict[str, Any]]] = {uf: [] for uf in UFS}
    ufs_do_aviso: dict[str, set[str]] = {a.id: set() for a in avisos}
    for i, r in enumerate(m.rodovias):
        cruzam, n_focos = por_rodovia.get(i, []), focos_rodovia.get(i, 0)
        if not cruzam and not n_focos:
            continue
        ja, depois = [a for a in cruzam if a.inicio <= agora], [a for a in cruzam if a.inicio > agora]
        for a in cruzam:
            ufs_do_aviso[a.id].add(r.uf)
        por_uf.setdefault(r.uf, []).append({
            "sigla": r.sigla, "avisos": [a.id for a in cruzam], "gravidade": _pior(ja), "gravidade_proxima": _pior(depois),
            "proximo_inicio": min(a.inicio for a in depois).isoformat() if depois else None, "focos_5km": n_focos})

    estados = {}
    for uf in UFS:
        linhas = por_uf.get(uf, [])
        estados[uf] = {"gravidade": max((x["gravidade"] for x in linhas), key=rank, default=""),
                       "gravidade_proxima": max((x["gravidade_proxima"] for x in linhas), key=rank, default=""),
                       "focos_5km": focos_uf_total.get(uf, 0),
                       "rodovias": sum(1 for x in linhas if x["gravidade"] or x["focos_5km"])}
    estado_fontes = {k: {"estado": r.estado, "credito": r.credito} for k, r in fontes.items() if k in ("inmet", "firms")}
    saida: dict[str, dict[str, Any]] = {"atual": {
        "atualizado_em": agora.isoformat(),
        "regiao": dict(zip(("sul", "oeste", "norte", "leste"), REGIAO)),
        "fontes": estado_fontes,
        "avisos": [_aviso(a, agora, sorted(ufs_do_aviso[a.id])) for a in avisos],
        "calor": [[round(i * PASSO_CALOR, 2), round(j * PASSO_CALOR, 2), n] for (i, j), n in sorted(calor.items())],
        "passo_calor": PASSO_CALOR,
        "focos_total": len(focos),
        "ufs": estados,
        "raio_fogo_km": RAIO_FOGO_KM,
    }}
    for uf in UFS:
        linhas = sorted(por_uf.get(uf, []), key=lambda x: (-rank(x["gravidade"]), -x["focos_5km"], x["sigla"]))
        saida[uf] = {"atualizado_em": agora.isoformat(), "uf": uf, "fontes": estado_fontes, "rodovias": linhas,
                     "focos_perto": focos_uf.get(uf, []), "focos_5km": focos_uf_total.get(uf, 0), "raio_fogo_km": RAIO_FOGO_KM}
    return saida
