"""Planejamento de tempo: direção, pausas, refeição, pernoites e paradas intermediárias.

Os limites vêm de ParametrosCusto (padrões baseados no CTB art. 67-C, redação da Lei 13.103/2015). A regra é
parâmetro e não lei embutida: a revisão jurídica dos padrões está pendente (ver README).
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from transporte.dominio import ParametrosCusto

EPS = 1e-9


@dataclass
class Evento:
    tipo: str  # direcao | pausa | refeicao | pernoite | parada | chegada
    inicio: datetime
    fim: datetime
    km_inicio: float
    km_fim: float

    def como_dict(self) -> dict[str, object]:
        return {
            "tipo": self.tipo,
            "inicio": self.inicio.isoformat(),
            "fim": self.fim.isoformat(),
            "km_inicio": round(self.km_inicio, 1),
            "km_fim": round(self.km_fim, 1),
            "duracao_h": round((self.fim - self.inicio).total_seconds() / 3600, 2),
        }


@dataclass
class PlanoJornada:
    eventos: list[Evento] = field(default_factory=list)

    @property
    def chegada(self) -> datetime:
        return self.eventos[-1].fim

    @property
    def partida(self) -> datetime:
        return self.eventos[0].inicio

    def contar(self, tipo: str) -> int:
        return sum(1 for e in self.eventos if e.tipo == tipo)

    def horas(self, tipo: str) -> float:
        return sum((e.fim - e.inicio).total_seconds() for e in self.eventos if e.tipo == tipo) / 3600

    def tempo_no_km(self, km: float) -> datetime:
        """Momento previsto de passagem no km (interpolado nos trechos de direção)."""
        trechos = [e for e in self.eventos if e.tipo == "direcao"]
        if not trechos:
            return self.partida
        fins = [e.km_fim for e in trechos]
        i = min(bisect_left(fins, km - EPS), len(trechos) - 1)
        e = trechos[i]
        if e.km_fim - e.km_inicio < EPS:
            return e.fim
        f = max(0.0, min(1.0, (km - e.km_inicio) / (e.km_fim - e.km_inicio)))
        return e.inicio + (e.fim - e.inicio) * f

    def resumo(self) -> dict[str, object]:
        total = (self.chegada - self.partida).total_seconds() / 3600
        return {
            "partida": self.partida.isoformat(),
            "chegada_prevista": self.chegada.isoformat(),
            "duracao_total_h": round(total, 2),
            "direcao_h": round(self.horas("direcao"), 2),
            "pausas": self.contar("pausa") + self.contar("refeicao"),
            "pernoites": self.contar("pernoite"),
            "paradas": self.contar("parada"),
            "eventos": [e.como_dict() for e in self.eventos],
        }


def planejar(trechos: list[tuple[float, float]], partida: datetime, p: ParametrosCusto) -> PlanoJornada:
    """trechos: lista de (distancia_km, duracao_direcao_h) entre pontos consecutivos."""
    lim_continua = float(p.direcao_continua_max_h)
    lim_dia = float(p.jornada_direcao_max_h)
    plano = PlanoJornada()
    t, km = partida, 0.0
    continua = dia = 0.0
    refeicao_feita = False

    def add(tipo: str, horas: float, km_fim: float | None = None) -> None:
        nonlocal t, km
        fim = t + timedelta(hours=horas)
        plano.eventos.append(Evento(tipo, t, fim, km, km if km_fim is None else km_fim))
        t = fim
        if km_fim is not None:
            km = km_fim

    for indice, (dist, dur) in enumerate(trechos):
        restante = dur
        vel = dist / dur if dur > EPS else 0.0
        while restante > EPS:
            bloco = min(restante, lim_continua - continua, lim_dia - dia)
            if bloco > EPS:
                add("direcao", bloco, km + bloco * vel)
                restante -= bloco
                continua += bloco
                dia += bloco
            if restante <= EPS:
                break
            if dia >= lim_dia - EPS:
                add("pernoite", float(p.descanso_diario_h))
                continua = dia = 0.0
                refeicao_feita = False
            elif continua >= lim_continua - EPS:
                if not refeicao_feita and p.refeicao_min:
                    add("refeicao", max(p.refeicao_min, p.pausa_min) / 60)
                    refeicao_feita = True
                else:
                    add("pausa", p.pausa_min / 60)
                continua = 0.0
        if indice < len(trechos) - 1 and p.tempo_parada_intermediaria_h > 0:
            horas_parada = float(p.tempo_parada_intermediaria_h)
            add("parada", horas_parada)
            if horas_parada * 60 >= p.pausa_min:
                continua = 0.0
    plano.eventos.append(Evento("chegada", t, t, km, km))
    return plano
