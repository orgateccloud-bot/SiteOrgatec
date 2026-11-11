"""Cruza alertas com a rota real e a posição de cada caminhão: quem será afetado, em que trecho e quando chega lá.

Regras aprovadas pelo usuário em 11/11/2026 (docs/ideias/alertas-rota.md, seção 5):
- No trajeto: viagem em andamento. O trecho que falta começa no km da última leitura de telemetria (sem telemetria, no km previsto
  para agora pelo plano). A hora de chegada a cada km é a do plano, deslocada pelo atraso ou adiantamento medido na última leitura.
- Vai viajar: viagem planejada com partida nas próximas 72 h.
- Área (INMET): o alerta vale se o trecho que falta passa dentro do polígono enquanto o aviso está valendo.
- Fogo: focos a até 5 km do trecho que falta, onde o caminhão passa nas próximas 6 h. Os focos viram um alerta por faixa de 25 km.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from backend.transporte.alertas.fontes import AlertaExterno, Foco, rank
from backend.transporte.dominio import utc
from backend.transporte.geo import Coord, acumulado_km, distancia_ponto_rota_km
from backend.transporte.servicos.jornada import Evento, PlanoJornada

HORIZONTE_PLANEJADA = timedelta(hours=72)
RAIO_FOGO_KM = 5.0
HORIZONTE_FOGO = timedelta(hours=6)
FAIXA_FOGO_KM = 25.0
VALIDADE_FOCO = timedelta(hours=12)
GRAVIDADE_MINIMA_MOTORISTA = "perigo"  # "Perigo potencial" fica só no painel


@dataclass
class RotaViagem:
    tid: str
    viagem: dict[str, Any]
    geo: list[Coord]
    acc: list[float]
    escala: float  # km de estrada por km do traçado simplificado
    plano: PlanoJornada
    km_atual: float  # km de estrada já percorrido (0 para planejada)
    atraso: timedelta
    grupo: str  # trajeto | planejada
    posicao_fonte: str  # telemetria | plano

    @property
    def caixa(self) -> tuple[float, float, float, float]:
        lats, lons = [p[0] for p in self.geo], [p[1] for p in self.geo]
        return (min(lats), min(lons), max(lats), max(lons))

    def hora_no_km(self, km: float) -> datetime:
        return self.plano.tempo_no_km(km) + self.atraso


def _plano(resultado: dict[str, Any]) -> PlanoJornada | None:
    eventos = (resultado.get("jornada") or {}).get("eventos") or []
    if not eventos:
        return None
    return PlanoJornada([Evento(e["tipo"], datetime.fromisoformat(e["inicio"]), datetime.fromisoformat(e["fim"]), e["km_inicio"], e["km_fim"])
                         for e in eventos])


def preparar(tid: str, viagem: dict[str, Any], ultima_leitura: dict[str, Any] | None, agora: datetime) -> RotaViagem | None:
    """None quando a viagem não entra no cruzamento: status, prazo, traçado apagado (30 dias, termos do Google) ou sem plano."""
    status, r = viagem.get("status"), viagem.get("resultado") or {}
    geo = [tuple(p) for p in ((r.get("rota") or {}).get("geometria") or [])]
    plano = _plano(r)
    if len(geo) < 2 or plano is None:
        return None
    if status == "planejada":
        if not (agora - timedelta(hours=12) <= utc(viagem["partida_prevista"]) <= agora + HORIZONTE_PLANEJADA):
            return None
        grupo = "planejada"
    elif status == "em_andamento":
        if plano.chegada + timedelta(hours=24) < agora:
            return None  # esquecida "em andamento" muito depois da chegada
        grupo = "trajeto"
    else:
        return None
    acc = acumulado_km(geo)  # type: ignore[arg-type]
    escala = r["rota"]["distancia_km"] / acc[-1] if acc[-1] else 1.0
    km_atual, atraso, fonte = 0.0, timedelta(0), "plano"
    if ultima_leitura is not None:
        _, km_tracado = distancia_ponto_rota_km((ultima_leitura["lat"], ultima_leitura["lon"]), geo, acc)  # type: ignore[arg-type]
        km_atual = km_tracado * escala
        atraso = utc(ultima_leitura["ts"]) - plano.tempo_no_km(km_atual)
        fonte = "telemetria"
    elif grupo == "trajeto":
        km_atual = _km_previsto(plano, agora)
    return RotaViagem(tid, viagem, geo, acc, escala, plano, km_atual, atraso, grupo, fonte)  # type: ignore[arg-type]


def _km_previsto(plano: PlanoJornada, agora: datetime) -> float:
    for e in plano.eventos:
        if e.inicio <= agora <= e.fim:
            if e.tipo != "direcao" or e.fim == e.inicio:
                return e.km_inicio
            return e.km_inicio + (e.km_fim - e.km_inicio) * (agora - e.inicio) / (e.fim - e.inicio)
    return plano.eventos[-1].km_fim if agora > plano.chegada else 0.0


def dentro(p: Coord, anel: tuple[Coord, ...]) -> bool:
    """Ponto no polígono (raio cruzando), em graus: suficiente para áreas de aviso."""
    lat, lon = p
    dentro_ = False
    j = len(anel) - 1
    for i in range(len(anel)):
        (la_i, lo_i), (la_j, lo_j) = anel[i], anel[j]
        if (lo_i > lon) != (lo_j > lon) and lat < (la_j - la_i) * (lon - lo_i) / ((lo_j - lo_i) or 1e-12) + la_i:
            dentro_ = not dentro_
        j = i
    return dentro_


def _caixa_anel(anel: tuple[Coord, ...]) -> tuple[float, float, float, float]:
    return (min(p[0] for p in anel), min(p[1] for p in anel), max(p[0] for p in anel), max(p[1] for p in anel))


def _sobrepoe(a: tuple[float, float, float, float], b: tuple[float, float, float, float], folga: float = 0.0) -> bool:
    return not (a[2] + folga < b[0] or b[2] + folga < a[0] or a[3] + folga < b[1] or b[3] + folga < a[1])


def _afetacao(rota: RotaViagem, alerta: dict[str, Any], km_ini: float, km_fim: float, local: Coord) -> dict[str, Any]:
    chegada = rota.hora_no_km(km_ini)
    avisar = rank(alerta["gravidade"]) >= rank(GRAVIDADE_MINIMA_MOTORISTA)
    return {"viagem_id": rota.viagem["id"], "alerta": alerta, "km_ini": round(km_ini, 1), "km_fim": round(km_fim, 1),
            "chegada_prevista": chegada.isoformat(), "lat": round(local[0], 4), "lon": round(local[1], 4), "grupo": rota.grupo,
            "posicao_fonte": rota.posicao_fonte, "avisar_motorista": avisar}


def cruzar_area(rota: RotaViagem, alerta: AlertaExterno) -> dict[str, Any] | None:
    caixa = rota.caixa
    trechos: list[tuple[float, Coord]] = []
    for anel in alerta.poligonos:
        if not _sobrepoe(caixa, _caixa_anel(anel)):
            continue
        for i, p in enumerate(rota.geo):
            km = rota.acc[i] * rota.escala
            if km >= rota.km_atual - 0.5 and dentro(p, anel):
                trechos.append((km, p))
    if not trechos:
        return None
    trechos.sort()
    km_ini, km_fim = trechos[0][0], trechos[-1][0]
    if rota.hora_no_km(km_fim) < alerta.inicio or rota.hora_no_km(km_ini) > alerta.fim:
        return None  # passa pela área fora da validade do aviso
    d = alerta.como_dict()
    d.pop("pontos")
    return _afetacao(rota, d, km_ini, km_fim, trechos[0][1])


def cruzar_focos(rota: RotaViagem, focos: list[Foco], agora: datetime) -> list[dict[str, Any]]:
    """Focos recentes (até 12 h) a até 5 km do trecho que falta, alcançado nas próximas 6 h. Um alerta por faixa de 25 km."""
    s, w, n, e = rota.caixa
    folga = RAIO_FOGO_KM / 100.0 + 0.02
    faixas: dict[int, list[tuple[float, Foco]]] = {}
    for f in focos:
        if f.quando < agora - VALIDADE_FOCO or not (s - folga <= f.lat <= n + folga and w - folga <= f.lon <= e + folga):
            continue
        dist, km_tracado = distancia_ponto_rota_km((f.lat, f.lon), rota.geo, rota.acc)
        km = km_tracado * rota.escala
        if dist > RAIO_FOGO_KM or km < rota.km_atual - 0.5 or rota.hora_no_km(km) > agora + HORIZONTE_FOGO:
            continue
        faixas.setdefault(int(km // FAIXA_FOGO_KM), []).append((km, f))
    saida = []
    for faixa, itens in sorted(faixas.items()):
        itens.sort(key=lambda x: x[0])
        kms = [k for k, _ in itens]
        quando = [f.quando for _, f in itens]
        origens = sorted({f.origem for _, f in itens})
        credito = " e ".join({"firms": "NASA FIRMS", "inpe": "INPE Queimadas"}[o] for o in origens) + " (focos de fogo por satélite)"
        alerta = {"id": f"fogo:{faixa}", "origem": "+".join(origens), "fonte": credito, "tipo": "fogo", "gravidade": "perigo",
                  "titulo": f"{len(itens)} foco(s) de fogo a até {RAIO_FOGO_KM:.0f} km da rota", "inicio": min(quando).isoformat(),
                  "fim": (max(quando) + VALIDADE_FOCO).isoformat(), "poligonos": [],
                  "pontos": [[round(f.lat, 4), round(f.lon, 4)] for _, f in itens[:30]],
                  "riscos": "Fumaça pode reduzir a visibilidade e levar à interdição da pista.",
                  "instrucoes": "Reduza a velocidade, acenda os faróis e não pare no acostamento sob fumaça. Siga a orientação da PRF.",
                  "link": ""}
        saida.append(_afetacao(rota, alerta, kms[0], kms[-1], (itens[0][1].lat, itens[0][1].lon)))
    return saida


def chave(viagem_id: str, alerta_id: str) -> str:
    return f"{viagem_id}__{hashlib.sha256(alerta_id.encode()).hexdigest()[:16]}"
