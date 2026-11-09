"""Monta a viagem completa a partir dos pontos: rota, jornada, despesas, bloqueios e clima.

Regra de falha: sem rota não há viagem (erro explícito). Qualquer outra fonte que falhe vira estado na tela e o
cálculo segue com o parâmetro da transportadora quando existir.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from transporte.dominio import ParametrosCusto, Ponto
from transporte.erros import EntradaInvalida, ErroProvedor
from transporte.geo import Coord, acumulado_km, distancia_ponto_rota_km, ponto_no_km, simplificar
from transporte.provedores.base import BloqueioProvider
from transporte.provedores.registro import Provedores
from transporte.servicos import despesas, jornada

log = logging.getLogger(__name__)

INTERVALO_CLIMA_KM = 150.0
MAX_PONTOS_CLIMA = 12


def _fonte(estado: str, fonte: str, detalhe: str = "") -> dict[str, str]:
    return {"estado": estado, "fonte": fonte, "detalhe": detalhe}


def montar(
    pontos: list[Ponto],
    *,
    eixos: int,
    consumo_km_l: Decimal,
    partida: datetime,
    parametros: ParametrosCusto,
    parametros_vigencia: str,
    provedores: Provedores,
    bloqueios: BloqueioProvider,
    ajustes: dict[str, str] | None = None,
) -> dict[str, Any]:
    fontes: dict[str, dict[str, str]] = {}

    coords: list[Coord] = []
    for pt in pontos:
        if pt.lat is not None and pt.lon is not None:
            coords.append((pt.lat, pt.lon))
        elif pt.lat is None and pt.lon is None:
            coords.append(provedores.rota.geocodificar(pt.nome, pt.uf))
        else:
            raise EntradaInvalida(f"Informe latitude e longitude juntas para '{pt.nome}'.")

    rota = provedores.rota.calcular(coords, eixos)
    if rota.distancia_km <= 0 or not rota.geometria:
        raise EntradaInvalida("A rota calculada está vazia. Confira os pontos.")
    fontes["rota"] = _fonte(rota.estado, rota.fonte)
    acc = acumulado_km(rota.geometria)
    escala = rota.distancia_km / acc[-1] if acc[-1] else 1.0

    km_pontos = [0.0]
    for c in coords[1:-1]:
        km_pontos.append(distancia_ponto_rota_km(c, rota.geometria, acc)[1] * escala)
    km_pontos.append(rota.distancia_km)
    km_pontos = [max(a, b) for a, b in zip(km_pontos, [0.0, *km_pontos[:-1]], strict=False)]  # garante ordem
    trechos = []
    for a, b in zip(km_pontos, km_pontos[1:], strict=False):
        dist = b - a
        trechos.append((dist, rota.duracao_h * dist / rota.distancia_km))
    plano = jornada.planejar(trechos, partida, parametros)

    origem = pontos[0]
    preco, preco_fonte, preco_estado = parametros.preco_diesel_padrao, "Parâmetro da transportadora", "parametro"
    try:
        pc = provedores.combustivel.preco_diesel(origem.uf, origem.nome.split("-")[0].strip())
        if pc is not None:
            preco, preco_fonte, preco_estado = pc.valor, f"{pc.fonte} ({pc.referencia})", pc.estado
        fontes["combustivel"] = _fonte(preco_estado, preco_fonte)
    except ErroProvedor as exc:
        log.warning("combustivel indisponivel: %s", exc)
        fontes["combustivel"] = _fonte(exc.estado, provedores.combustivel.nome, "usando parâmetro da transportadora")

    try:
        pracas = provedores.pedagio.pracas_na_rota(rota.geometria)
        estado_ped = "simulado" if "Simulado" in (pracas[0].fonte if pracas else "") else "ok"
        fontes["pedagio"] = _fonte(estado_ped, provedores.pedagio.nome)
    except ErroProvedor as exc:
        log.warning("pedagio indisponivel: %s", exc)
        pracas, estado_ped = [], exc.estado
        fontes["pedagio"] = _fonte(exc.estado, provedores.pedagio.nome, "pedágio fora da estimativa")

    insumos = despesas.Insumos(
        distancia_km=Decimal(str(rota.distancia_km)),
        pernoites=plano.contar("pernoite"),
        eixos=eixos,
        consumo_km_l=consumo_km_l,
        preco_diesel=preco,
        preco_diesel_fonte=preco_fonte,
        preco_diesel_estado=preco_estado,
        tarifas_pracas=[p.tarifa_cat1 for p in pracas],
        pedagio_estado=estado_ped,
    )

    lista_bloqueios: list[dict[str, Any]] = []
    try:
        for b in bloqueios.na_rota(rota.geometria, plano.partida, plano.chegada):
            km = b.km_na_rota * escala
            lista_bloqueios.append(
                {
                    "tipo": b.tipo,
                    "descricao": b.descricao,
                    "lat": b.lat,
                    "lon": b.lon,
                    "km": round(km, 1),
                    "passagem_prevista": plano.tempo_no_km(km).isoformat(),
                    "fonte": b.fonte,
                }
            )
        fontes["bloqueios"] = _fonte("simulado" if bloqueios.nome.endswith("simulado") else "ok", bloqueios.nome)
    except ErroProvedor as exc:
        fontes["bloqueios"] = _fonte(exc.estado, bloqueios.nome)

    fontes["clima"], lista_clima = _clima(provedores, rota.geometria, acc, escala, rota.distancia_km, plano)

    return {
        "pontos": [
            {"nome": pt.nome, "uf": pt.uf, "lat": c[0], "lon": c[1], "km": round(k, 1)}
            for pt, c, k in zip(pontos, coords, km_pontos, strict=False)
        ],
        "rota": {
            "distancia_km": rota.distancia_km,
            "duracao_direcao_h": rota.duracao_h,
            "geometria": [[round(a, 5), round(b, 5)] for a, b in simplificar(rota.geometria, 400)],
        },
        "jornada": plano.resumo(),
        "pedagios": [
            {"nome": p.nome, "km": round(p.km_na_rota * escala, 1), "lat": p.lat, "lon": p.lon} for p in pracas
        ],
        "insumos": insumos.como_dict(),
        "despesas": despesas.calcular(insumos, parametros, ajustes),
        "bloqueios": lista_bloqueios,
        "clima": lista_clima,
        "fontes": fontes,
        "parametros": parametros.model_dump(mode="json"),
        "parametros_vigencia": parametros_vigencia,
        "calculado_em": datetime.now(UTC).isoformat(),
    }


def _clima(
    provedores: Provedores,
    geometria: list[Coord],
    acc: list[float],
    escala: float,
    distancia_km: float,
    plano: jornada.PlanoJornada,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    marcos = [0.0]
    km = INTERVALO_CLIMA_KM
    while km < distancia_km and len(marcos) < MAX_PONTOS_CLIMA - 1:
        marcos.append(km)
        km += INTERVALO_CLIMA_KM
    marcos += [e.km_inicio for e in plano.eventos if e.tipo == "pernoite"]
    marcos.append(distancia_km)
    saida: list[dict[str, Any]] = []
    for km_rel in sorted(set(round(m, 1) for m in marcos))[:MAX_PONTOS_CLIMA]:
        lat, lon = ponto_no_km(geometria, km_rel / escala, acc)
        quando = plano.tempo_no_km(km_rel)
        try:
            prev = provedores.clima.previsao(lat, lon, quando)
        except ErroProvedor as exc:
            log.warning("clima indisponivel: %s", exc)
            return _fonte(exc.estado, provedores.clima.nome), saida
        item: dict[str, Any] = {
            "km": km_rel,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "passagem": quando.isoformat(),
        }
        if prev is None:
            item.update({"condicao": "fora do horizonte da previsão", "temperatura_c": None, "chuva_mm": None})
        else:
            item.update(
                {
                    "condicao": prev.condicao,
                    "temperatura_c": prev.temperatura_c,
                    "chuva_mm": prev.chuva_mm,
                    "vento_ms": prev.vento_ms,
                }
            )
        saida.append(item)
    estado = "simulado" if provedores.clima.nome.endswith("simulado") else "ok"
    return _fonte(estado, provedores.clima.nome), saida


def recalcular_despesas(resultado: dict[str, Any], ajustes: dict[str, str]) -> dict[str, Any]:
    insumos = despesas.Insumos.de_dict(resultado["insumos"])
    parametros = ParametrosCusto.model_validate(resultado["parametros"])
    return despesas.calcular(insumos, parametros, ajustes)
