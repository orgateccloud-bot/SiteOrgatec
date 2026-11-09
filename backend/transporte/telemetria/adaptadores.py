"""Adaptadores por fornecedor: convertem o corpo recebido em leituras normalizadas (LeituraEntrada).

Para integrar um fornecedor novo: escreva uma função `(dict) -> list[dict]` que devolva leituras no formato de
LeituraEntrada e registre em ADAPTADORES com o mesmo nome usado no campo `fornecedor` do sensor. Formatos de
fornecedores específicos não foram implementados porque não foram fornecidos nem verificados.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from backend.transporte.dominio import LeituraEntrada
from backend.transporte.erros import EntradaInvalida

MAX_LEITURAS = 500


def generico(corpo: dict[str, Any]) -> list[dict[str, Any]]:
    """Formato próprio da Central: {"leituras": [{id, ts, lat, lon, velocidade_kmh?, ignicao?, ...}]}."""
    leituras = corpo.get("leituras")
    if not isinstance(leituras, list):
        raise EntradaInvalida("Campo 'leituras' (lista) é obrigatório.")
    return leituras


ADAPTADORES: dict[str, Callable[[dict[str, Any]], list[dict[str, Any]]]] = {"generico": generico}


def normalizar(fornecedor: str, corpo: Any) -> list[LeituraEntrada]:
    if not isinstance(corpo, dict):
        raise EntradaInvalida("Corpo deve ser um objeto JSON.")
    adaptador = ADAPTADORES.get(fornecedor)
    if adaptador is None:
        raise EntradaInvalida(f"Fornecedor '{fornecedor}' sem adaptador registrado.")
    brutas = adaptador(corpo)
    if len(brutas) > MAX_LEITURAS:
        raise EntradaInvalida(f"Máximo de {MAX_LEITURAS} leituras por envio.")
    try:
        return [LeituraEntrada.model_validate(b) for b in brutas]
    except ValidationError as exc:
        raise EntradaInvalida(f"Leitura inválida: {exc.errors()[0]['loc']} {exc.errors()[0]['msg']}") from exc
