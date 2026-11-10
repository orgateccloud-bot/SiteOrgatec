"""Tarifas de pedágio oficiais por praça e concessionária (categoria 1, que é a tarifa por eixo: o caminhão paga tarifa × eixos).

O arquivo da ANTT (dados abertos) traz as praças, mas não o valor. Esta tabela vem das tabelas que a própria concessionária publica
e é conferida à mão. Cada concessionária tem fonte, vigência e data de conferência; praça fora da tabela segue com o parâmetro da
transportadora e o selo "estimado". Rever a cada reajuste (Ecovias do Araguaia: data-base em outubro).

Para acrescentar uma concessionária: uma entrada em TARIFAS (chave = nome como no arquivo da ANTT, em maiúsculas e sem acento, e o
código da praça antes do " - ") e uma em CONCESSIONARIAS com a fonte.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FonteTarifa:
    concessionaria: str
    url: str
    vigencia: str
    conferido_em: str


CONCESSIONARIAS: dict[str, FonteTarifa] = {
    "ECOVIAS DO ARAGUAIA": FonteTarifa(
        "Ecovias do Araguaia",
        "https://www.ecoviasaraguaia.com.br/servicos/tarifas-de-pedagio",
        "valores da página oficial; coincidem com o reajuste de 03/10/2025 (a página não informa a vigência)",
        "2026-11-09",
    ),
}

# Categoria 1 (automóvel, 2 eixos, multiplicador 1,0), R$. Categoria 8 (6 eixos) = 6,0 × este valor.
TARIFAS: dict[str, dict[str, Decimal]] = {
    "ECOVIAS DO ARAGUAIA": {
        "P1": Decimal("9.50"),   # Aliança do Tocantins/TO, BR-153
        "P2": Decimal("12.40"),  # Alvorada/TO, BR-153
        "P3": Decimal("12.00"),  # Porangatu/GO, BR-153
        "P4": Decimal("11.50"),  # Estrela do Norte/GO, BR-153
        "P5": Decimal("14.30"),  # Campinorte/GO, BR-153
        "P6": Decimal("14.30"),  # Hidrolina/GO, BR-153
        "P7": Decimal("15.60"),  # Jaraguá/GO, BR-153
        "P8": Decimal("14.30"),  # Santa Rita do Novo Destino/GO, BR-080
        "P9": Decimal("14.30"),  # Corumbá de Goiás/GO, BR-414
    },
}

_CODIGO = re.compile(r"^\s*(P\d+)\b", re.IGNORECASE)


def _normalizar(txt: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn").upper().strip()


def tarifa_cat1(concessionaria: str, praca: str) -> tuple[Decimal, FonteTarifa] | None:
    """Tarifa categoria 1 da praça (ex.: 'P5 - Campinorte') na concessionária, ou None se não estiver na tabela."""
    chave = _normalizar(concessionaria)
    m = _CODIGO.match(praca or "")
    valor = TARIFAS.get(chave, {}).get(m.group(1).upper()) if m else None
    return (valor, CONCESSIONARIAS[chave]) if valor is not None else None


def rotulo_fonte(f: FonteTarifa) -> str:
    return f"tabela oficial {f.concessionaria}, conferida em {f.conferido_em[8:]}/{f.conferido_em[5:7]}/{f.conferido_em[:4]}"
