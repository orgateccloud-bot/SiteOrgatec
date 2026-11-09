"""Previsão de despesas da viagem. Decimal em todo cálculo; arredondamento só no valor final de cada item."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from transporte.dominio import ParametrosCusto

CENTAVO = Decimal("0.01")

ROTULOS = {
    "combustivel": "Combustível (diesel)",
    "arla": "ARLA 32",
    "pedagio": "Pedágio",
    "hospedagem": "Hospedagem / pernoite",
    "alimentacao": "Alimentação",
    "pneus": "Pneus",
    "manutencao": "Manutenção",
    "borracharia": "Borracharia (reserva)",
    "outros": "Outros custos da viagem",
    "reserva_imprevistos": "Reserva para imprevistos",
}


def q(v: Decimal) -> Decimal:
    return v.quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Insumos:
    """Tudo que o cálculo precisa, guardado na viagem para recalcular ajustes sem chamar as fontes de novo."""

    distancia_km: Decimal
    pernoites: int
    eixos: int
    consumo_km_l: Decimal
    preco_diesel: Decimal
    preco_diesel_fonte: str
    preco_diesel_estado: str
    tarifas_pracas: list[Decimal | None]
    pedagio_estado: str

    def como_dict(self) -> dict[str, Any]:
        return {
            "distancia_km": str(self.distancia_km),
            "pernoites": self.pernoites,
            "eixos": self.eixos,
            "consumo_km_l": str(self.consumo_km_l),
            "preco_diesel": str(self.preco_diesel),
            "preco_diesel_fonte": self.preco_diesel_fonte,
            "preco_diesel_estado": self.preco_diesel_estado,
            "tarifas_pracas": [None if t is None else str(t) for t in self.tarifas_pracas],
            "pedagio_estado": self.pedagio_estado,
        }

    @classmethod
    def de_dict(cls, d: dict[str, Any]) -> Insumos:
        return cls(
            distancia_km=Decimal(d["distancia_km"]),
            pernoites=int(d["pernoites"]),
            eixos=int(d["eixos"]),
            consumo_km_l=Decimal(d["consumo_km_l"]),
            preco_diesel=Decimal(d["preco_diesel"]),
            preco_diesel_fonte=d["preco_diesel_fonte"],
            preco_diesel_estado=d["preco_diesel_estado"],
            tarifas_pracas=[None if t is None else Decimal(t) for t in d["tarifas_pracas"]],
            pedagio_estado=d["pedagio_estado"],
        )


def _item(tipo: str, quantidade: Decimal, unidade: str, unitario: Decimal, fonte: str, estado: str = "ok") -> dict:
    return {
        "tipo": tipo,
        "rotulo": ROTULOS[tipo],
        "quantidade": str(quantidade),
        "unidade": unidade,
        "valor_unitario": str(unitario),
        "valor_calculado": str(q(quantidade * unitario)),
        "valor": str(q(quantidade * unitario)),
        "fonte": fonte,
        "estado": estado,
        "ajustado": False,
    }


def calcular(ins: Insumos, p: ParametrosCusto, ajustes: dict[str, str] | None = None) -> dict[str, Any]:
    ajustes = ajustes or {}
    km = ins.distancia_km
    param = "Parâmetro da transportadora"
    litros = (km / ins.consumo_km_l).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    itens = [
        _item("combustivel", litros, "l", ins.preco_diesel, ins.preco_diesel_fonte, ins.preco_diesel_estado),
        _item("arla", (litros * p.arla_pct_diesel).quantize(Decimal("0.1")), "l", p.preco_arla_l, param),
    ]
    tarifas = [t if t is not None else p.pedagio_tarifa_padrao_cat1 for t in ins.tarifas_pracas]
    fator_eixo = Decimal(ins.eixos) * p.pedagio_multiplicador_por_eixo
    soma_pedagio = sum((t * fator_eixo for t in tarifas), Decimal("0"))
    n = Decimal(len(tarifas))
    fonte_ped = "Praças: " + ("ANTT" if ins.pedagio_estado == "ok" else ins.pedagio_estado)
    if any(t is None for t in ins.tarifas_pracas):
        fonte_ped += "; tarifa: parâmetro da transportadora"
    ped = _item("pedagio", n, "praça(s)", q(soma_pedagio / n) if n else Decimal("0"), fonte_ped, ins.pedagio_estado)
    ped["valor_calculado"] = ped["valor"] = str(q(soma_pedagio))
    itens.append(ped)
    pernoites = Decimal(ins.pernoites)
    if p.pernoite_no_veiculo:
        itens.append(_item("hospedagem", pernoites, "noite(s)", Decimal("0"), "Pernoite na cabine (parâmetro)"))
    else:
        itens.append(_item("hospedagem", pernoites, "noite(s)", p.diaria_hospedagem, param))
    itens += [
        _item("alimentacao", pernoites + 1, "dia(s)", p.diaria_alimentacao, param),
        _item("pneus", km, "km", p.custo_pneus_km, param),
        _item("manutencao", km, "km", p.custo_manutencao_km, param),
        _item("borracharia", Decimal("1"), "viagem", p.reserva_borracharia_viagem, param),
        _item("outros", Decimal("1"), "viagem", p.outros_custos_viagem, param),
    ]
    for it in itens:
        _aplicar_ajuste(it, ajustes)
    subtotal = sum((Decimal(it["valor"]) for it in itens), Decimal("0"))
    reserva = _item("reserva_imprevistos", subtotal, "R$ base", p.reserva_imprevistos_pct, param)
    reserva["quantidade"] = str(q(subtotal))
    _aplicar_ajuste(reserva, ajustes)
    itens.append(reserva)
    total = q(subtotal + Decimal(reserva["valor"]))
    return {
        "itens": itens,
        "total": str(total),
        "custo_por_km": str(q(total / km)) if km else "0.00",
        "litros_diesel": str(litros),
    }


def _aplicar_ajuste(item: dict[str, Any], ajustes: dict[str, str]) -> None:
    valor = ajustes.get(item["tipo"])
    if valor is not None:
        item["valor"] = str(q(Decimal(valor)))
        item["ajustado"] = True
        item["fonte"] = f"Ajuste manual (calculado: R$ {item['valor_calculado']})"
