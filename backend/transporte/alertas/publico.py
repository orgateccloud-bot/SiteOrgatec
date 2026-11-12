"""Resumo público dos alertas para o mapa da Janela do Transporte (empresarial/janela.html).

Só dados de fontes públicas, sem viagem, posição, cliente ou motorista:
- avisos do INMET cuja área toca a região dos corredores (GO, TO e PA até a BR-230), com o polígono simplificado;
- focos de fogo do NASA FIRMS das últimas 24 h na região (coordenadas com 2 casas, ~1 km);
- por rodovia (BR-153, BR-060, BR-010 e BR-230, traçado do IBGE em site/assets/geo/rodovias-corredores.json): os avisos que
  cruzam o traçado e quantos focos estão a até 5 km dele.

A rotina dos alertas grava o resumo a cada execução em `_sistema/alertas_publicos/atual`; a API o devolve sem login.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.transporte.alertas.cruzamento import RAIO_FOGO_KM, dentro
from backend.transporte.alertas.fontes import AlertaExterno, Foco, ResultadoFonte, rank
from backend.transporte.geo import distancia_ponto_rota_km, simplificar

ARQUIVO_RODOVIAS = Path(__file__).resolve().parents[3] / "site" / "assets" / "geo" / "rodovias-corredores.json"
# (sul, oeste, norte, leste), no formato das caixas da rotina. Mesma região de tools/gerar_rodovias.py: um teste confere.
REGIAO = (-19.6, -56.5, -1.0, -45.5)
JANELA_FOCOS = timedelta(hours=24)
MAX_FOCOS = 4000  # o documento do Firestore tem limite de 1 MB; 4.000 focos ocupam ~100 KB
MAX_PONTOS_ANEL = 200


@lru_cache(maxsize=1)
def rodovias() -> tuple[tuple[str, tuple[tuple[tuple[float, float], ...], ...]], ...]:
    """(sigla, linhas de (lat, lon)). Arquivo ausente = sem resumo por rodovia (o mapa segue com avisos e focos)."""
    if not ARQUIVO_RODOVIAS.exists():
        return ()
    dados = json.loads(ARQUIVO_RODOVIAS.read_text(encoding="utf-8"))
    return tuple((r["sigla"], tuple(tuple((p[0], p[1]) for p in linha) for linha in r["linhas"])) for r in dados["rodovias"])


def _na_regiao(lat: float, lon: float) -> bool:
    s, w, n, e = REGIAO
    return s <= lat <= n and w <= lon <= e


def _toca_regiao(anel: tuple[tuple[float, float], ...]) -> bool:
    s, w, n, e = REGIAO
    lats, lons = [p[0] for p in anel], [p[1] for p in anel]
    return not (max(lats) < s or min(lats) > n or max(lons) < w or min(lons) > e)


def _aviso(a: AlertaExterno, agora: datetime) -> dict[str, Any]:
    aneis = [[[round(p[0], 3), round(p[1], 3)] for p in simplificar(list(anel), MAX_PONTOS_ANEL)] for anel in a.poligonos if _toca_regiao(anel)]
    return {"id": a.id, "tipo": a.tipo, "gravidade": a.gravidade, "titulo": a.titulo, "inicio": a.inicio.isoformat(), "fim": a.fim.isoformat(),
            "vigente": a.inicio <= agora,  # o INMET publica também os avisos dos próximos dias: o mapa os mostra à parte
            "riscos": a.riscos, "instrucoes": a.instrucoes, "link": a.link, "fonte": a.fonte, "poligonos": aneis}


PASSO_GRAUS = 0.05  # ~5 km: o traçado simplificado tem trechos retos longos, e o aviso pode cortar só o meio de um deles


def _amostras(linha: tuple[tuple[float, float], ...]) -> list[tuple[float, float]]:
    pontos = [linha[0]]
    for (la0, lo0), (la1, lo1) in zip(linha, linha[1:]):
        n = max(1, math.ceil(max(abs(la1 - la0), abs(lo1 - lo0)) / PASSO_GRAUS))
        pontos += [(la0 + (la1 - la0) * i / n, lo0 + (lo1 - lo0) * i / n) for i in range(1, n + 1)]
    return pontos


def _aviso_cruza(a: AlertaExterno, linhas: tuple[tuple[tuple[float, float], ...], ...]) -> bool:
    return any(dentro(p, anel) for anel in a.poligonos for linha in linhas for p in _amostras(linha))


def _focos_perto(focos: list[Foco], linhas: tuple[tuple[tuple[float, float], ...], ...]) -> int:
    folga = RAIO_FOGO_KM / 100.0 + 0.02
    caixas = [(min(p[0] for p in ln) - folga, min(p[1] for p in ln) - folga, max(p[0] for p in ln) + folga, max(p[1] for p in ln) + folga)
              for ln in linhas]
    n = 0
    for f in focos:
        for linha, (s, w, nn, e) in zip(linhas, caixas):
            if s <= f.lat <= nn and w <= f.lon <= e and distancia_ponto_rota_km((f.lat, f.lon), linha)[0] <= RAIO_FOGO_KM:
                n += 1
                break
    return n


def montar(fontes: dict[str, ResultadoFonte], agora: datetime) -> dict[str, Any]:
    """Resumo gravado pela rotina. Fonte fora do ar aparece como indisponível (o mapa avisa em vez de mostrar 'sem risco')."""
    avisos = [a for r in fontes.values() for a in r.alertas
              if a.origem == "inmet" and a.fim > agora and any(_toca_regiao(anel) for anel in a.poligonos)]
    avisos.sort(key=lambda a: (-rank(a.gravidade), a.inicio))
    focos = [f for r in fontes.values() for f in r.focos if f.origem == "firms" and f.quando >= agora - JANELA_FOCOS and _na_regiao(f.lat, f.lon)]
    focos.sort(key=lambda f: f.quando, reverse=True)
    focos = focos[:MAX_FOCOS]
    resumo = []
    for sigla, linhas in rodovias():
        cruzam = [a for a in avisos if _aviso_cruza(a, linhas)]
        ja = [a for a in cruzam if a.inicio <= agora]
        depois = [a for a in cruzam if a.inicio > agora]
        resumo.append({"sigla": sigla, "avisos": [a.id for a in cruzam],
                       "gravidade": max((a.gravidade for a in ja), key=rank, default=""),
                       "gravidade_proxima": max((a.gravidade for a in depois), key=rank, default=""),
                       "proximo_inicio": min(a.inicio for a in depois).isoformat() if depois else None,
                       "focos_5km": _focos_perto(focos, linhas)})
    return {
        "atualizado_em": agora.isoformat(),
        "regiao": dict(zip(("sul", "oeste", "norte", "leste"), REGIAO)),
        "fontes": {k: {"estado": r.estado, "credito": r.credito} for k, r in fontes.items() if k in ("inmet", "firms")},
        "avisos": [_aviso(a, agora) for a in avisos],
        "focos": [[round(f.lat, 2), round(f.lon, 2), f.quando.strftime("%Y-%m-%dT%H:%MZ")] for f in focos],
        "rodovias": resumo,
        "raio_fogo_km": RAIO_FOGO_KM,
    }
