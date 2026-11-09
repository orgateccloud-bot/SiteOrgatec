"""Provedores simulados: deterministas, sem rede. Permitem rodar a Central de ponta a ponta sem chave nem contrato.

Tudo que sai daqui é marcado com estado "simulado" e aparece assim na tela.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import Decimal

from transporte.erros import EntradaInvalida
from transporte.geo import Coord, acumulado_km, distancia_ponto_rota_km, haversine_km, ponto_no_km
from transporte.provedores.base import Bloqueio, PracaPedagio, PrecoCombustivel, PrevisaoClima, RotaCalculada

FONTE = "Simulado (demonstração)"

# Coordenadas aproximadas de capitais/cidades conhecidas, só para demonstração do geocodificador simulado.
CIDADES_DEMO: dict[str, Coord] = {
    "goiania": (-16.6869, -49.2648),
    "anapolis": (-16.3281, -48.9534),
    "brasilia": (-15.7939, -47.8828),
    "palmas": (-10.1844, -48.3336),
    "sao paulo": (-23.5505, -46.6333),
    "belem": (-1.4558, -48.4902),
    "uruacu": (-14.5237, -49.1396),
    "porangatu": (-13.4409, -49.1488),
}

FATOR_SINUOSIDADE = 1.25
VELOCIDADE_MEDIA_KMH = 60.0


def _normalizar(texto: str) -> str:
    tabela = str.maketrans("áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ", "aaaaeeiooouc" + "aaaaeeiooouc")
    base = texto.split("-")[0].split(",")[0].split("/")[0]
    return base.translate(tabela).lower().strip()


def _sorteio(*partes: object) -> float:
    """Número estável em [0, 1) a partir das partes — mesma entrada, mesmo resultado."""
    dig = hashlib.sha256("|".join(map(str, partes)).encode()).hexdigest()
    return int(dig[:8], 16) / 0xFFFFFFFF


class RotaSimulada:
    nome = "rota_simulada"

    def geocodificar(self, texto: str, uf: str | None) -> Coord:
        coord = CIDADES_DEMO.get(_normalizar(texto))
        if coord is None:
            raise EntradaInvalida(
                f"Local '{texto}' não está na lista de demonstração. Informe latitude e longitude "
                f"ou ligue TRANSPORTE_ROTA_REAL. Disponíveis: {', '.join(sorted(CIDADES_DEMO))}."
            )
        return coord

    def calcular(self, pontos: list[Coord], eixos: int) -> RotaCalculada:
        geometria: list[Coord] = []
        for a, b in zip(pontos, pontos[1:], strict=False):
            passos = max(10, int(haversine_km(a, b) / 10))
            trecho = [(a[0] + (b[0] - a[0]) * i / passos, a[1] + (b[1] - a[1]) * i / passos) for i in range(passos)]
            geometria.extend(trecho)
        geometria.append(pontos[-1])
        distancia = acumulado_km(geometria)[-1] * FATOR_SINUOSIDADE
        return RotaCalculada(
            distancia_km=round(distancia, 1),
            duracao_h=round(distancia / VELOCIDADE_MEDIA_KMH, 2),
            geometria=geometria,
            fonte=f"{FONTE}: linha reta × {FATOR_SINUOSIDADE} a {VELOCIDADE_MEDIA_KMH:.0f} km/h",
            estado="simulado",
        )


class CombustivelSimulado:
    nome = "combustivel_simulado"

    def preco_diesel(self, uf: str | None, municipio: str | None) -> PrecoCombustivel | None:
        return PrecoCombustivel(Decimal("6.29"), "valor fixo de demonstração", FONTE, "simulado")


class PedagioSimulado:
    nome = "pedagio_simulado"
    intervalo_km = 180.0

    def pracas_na_rota(self, geometria: list[Coord]) -> list[PracaPedagio]:
        acc = acumulado_km(geometria)
        pracas: list[PracaPedagio] = []
        km = self.intervalo_km / 2
        n = 1
        while km < acc[-1]:
            lat, lon = ponto_no_km(geometria, km, acc)
            pracas.append(PracaPedagio(f"Praça simulada {n}", lat, lon, round(km, 1), Decimal("9.40"), FONTE))
            km += self.intervalo_km
            n += 1
        return pracas


class ClimaSimulado:
    nome = "clima_simulado"

    def previsao(self, lat: float, lon: float, quando: datetime) -> PrevisaoClima | None:
        s = _sorteio(round(lat, 1), round(lon, 1), quando.strftime("%Y%m%d%H"))
        chuva = round(max(0.0, (s - 0.6) * 20), 1)
        condicao = "chuva" if chuva > 2 else ("nublado" if s > 0.4 else "céu limpo")
        return PrevisaoClima(quando, round(20 + s * 12, 1), chuva, round(1 + s * 7, 1), condicao, FONTE)


class BloqueioSimulado:
    nome = "bloqueio_simulado"

    def na_rota(self, geometria: list[Coord], inicio: datetime, fim: datetime) -> list[Bloqueio]:
        acc = acumulado_km(geometria)
        if acc[-1] < 50:
            return []
        km = acc[-1] * 0.4
        lat, lon = ponto_no_km(geometria, km, acc)
        dist, km_rota = distancia_ponto_rota_km((lat, lon), geometria, acc)
        return [
            Bloqueio(
                "interdicao_parcial",
                "Interdição parcial simulada (obra em pista) — meia pista, pare e siga",
                lat,
                lon,
                round(km_rota, 1),
                FONTE,
            )
        ]
