"""Monta a viagem completa a partir dos pontos: rota, jornada, despesas, bloqueios e clima.

Regra de falha: sem rota não há viagem (erro explícito). Qualquer outra fonte que falhe vira estado na tela e o
cálculo segue com o parâmetro da transportadora quando existir.
"""

from __future__ import annotations

import copy
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from backend.transporte.dominio import ParametrosCusto, Ponto
from backend.transporte.erros import EntradaInvalida, ErroProvedor
from backend.transporte.geo import Coord, acumulado_km, distancia_ponto_rota_km, ponto_no_km, simplificar
from backend.transporte.provedores.base import BloqueioProvider
from backend.transporte.provedores.registro import Provedores
from backend.transporte.servicos import despesas, jornada

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

    fontes["postos"], lista_postos = _postos(provedores, rota.geometria, escala)

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
        "pedagios": _pedagios(pracas, escala, eixos, parametros),
        "postos": lista_postos,
        "insumos": insumos.como_dict(),
        "despesas": despesas.calcular(insumos, parametros, ajustes),
        "bloqueios": lista_bloqueios,
        "clima": lista_clima,
        "fontes": fontes,
        "parametros": parametros.model_dump(mode="json"),
        "parametros_vigencia": parametros_vigencia,
        "calculado_em": datetime.now(UTC).isoformat(),
    }


def _pedagios(pracas: list[Any], escala: float, eixos: int, parametros: ParametrosCusto) -> list[dict[str, Any]]:
    """Cada praça com o valor para este veículo: tarifa da categoria 1 x eixos x multiplicador. Sem tarifa oficial, o valor sai do
    parâmetro da transportadora e a praça fica marcada como estimada."""
    fator = Decimal(eixos) * parametros.pedagio_multiplicador_por_eixo
    saida = []
    for p in pracas:
        tem_tarifa = p.tarifa_cat1 is not None
        tarifa = p.tarifa_cat1 if tem_tarifa else parametros.pedagio_tarifa_padrao_cat1
        saida.append({"nome": p.nome, "km": round(p.km_na_rota * escala, 1), "lat": p.lat, "lon": p.lon,
                      "tarifa_cat1": str(tarifa), "valor": str((tarifa * fator).quantize(Decimal("0.01"))), "eixos": eixos,
                      "tarifa_oficial": tem_tarifa and not p.fonte.startswith("Simulado"),
                      "fonte": p.fonte if tem_tarifa else f"{p.fonte}; tarifa: parâmetro da transportadora (estimada)"})
    return saida


def _postos(provedores: Provedores, geometria: list[Coord], escala: float) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Postos ao longo da rota. O preço é a média da ANP no município do posto (ou na UF), nunca o preço do posto, e só quando o
    combustível real (ANP) está ligado. Sem provedor de postos, a fonte fica 'indisponivel' e a lista vazia."""
    try:
        achados = provedores.postos.postos_na_rota(geometria)
    except ErroProvedor as exc:
        log.warning("postos indisponiveis: %s", exc)
        return _fonte(exc.estado, provedores.postos.nome, "busca de postos falhou"), []
    if achados is None:
        return _fonte("indisponivel", "Busca de postos desligada", "não configurada nesta instalação"), []
    anp_real = "combustivel" in provedores.reais()
    precos: dict[tuple[str | None, str | None], Any] = {}
    saida = []
    for p in achados:
        chave = (p.uf, p.municipio)
        if chave not in precos:
            try:
                precos[chave] = provedores.combustivel.preco_diesel(p.uf, p.municipio) if anp_real and p.uf else None
            except ErroProvedor:
                precos[chave] = None
        pc = precos[chave]
        saida.append({"nome": p.nome, "lat": p.lat, "lon": p.lon, "km": round(p.km_na_rota * escala, 1), "endereco": p.endereco,
                      "municipio": p.municipio, "uf": p.uf, "id_externo": p.id_externo, "fonte": p.fonte,
                      "preco_diesel_referencia": str(pc.valor) if pc else None,
                      "preco_fonte": (f"média ANP ({pc.referencia}), não é o preço deste posto" if pc
                                      else "preço não disponível (sem dado da ANP para o local)")})
    return _fonte("ok", provedores.postos.nome, f"{len(saida)} posto(s) a até 3 km da rota"), saida


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


# Termos do Google Maps Platform (Service Specific Terms 19.3 e 14.3): latitude e longitude vindas da Routes API e da Places API só
# podem ficar guardadas por até 30 dias corridos. O job de retenção (tools/lgpd.py) usa 29 para ter folga de um dia.
PRAZO_COORDENADAS_GOOGLE_DIAS = 29


def expirar_coordenadas(viagem: dict[str, Any], antes_de: datetime) -> dict[str, Any] | None:
    """Novo `resultado` sem as coordenadas do Google, ou None se nada precisa mudar. Mantém distâncias, tempos, valores e as coordenadas
    que não vieram do Google (pedágios da ANTT, bloqueios e pontos informados pelo usuário). A viagem pode ser recalculada depois."""
    r = viagem.get("resultado") or {}
    if r.get("coordenadas_expiradas") or not r.get("calculado_em"):
        return None
    if datetime.fromisoformat(r["calculado_em"]) >= antes_de:
        return None
    rota_google = "Google" in r.get("fontes", {}).get("rota", {}).get("fonte", "")
    postos = r.get("postos") or []
    if not rota_google and not postos:
        return None
    novo = copy.deepcopy(r)
    if rota_google:
        novo["rota"]["geometria"] = []
        for ponto, informado in zip(novo.get("pontos", []), viagem.get("pontos", []), strict=False):
            if informado.get("lat") is None:  # veio da geocodificação do Google
                ponto["lat"] = ponto["lon"] = None
        for c in novo.get("clima", []):
            c["lat"] = c["lon"] = None  # pontos tirados do traçado
    for p in novo.get("postos", []):
        p["lat"] = p["lon"] = None
    novo["coordenadas_expiradas"] = datetime.now(UTC).isoformat()
    return novo
