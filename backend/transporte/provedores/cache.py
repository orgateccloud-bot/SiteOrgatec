"""Cache em memória com validade. Interface simples para trocar por Redis com várias instâncias."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable
from typing import Any


class Cache:
    def __init__(self, relogio: Callable[[], float] = time.monotonic, maximo: int = 5000) -> None:
        self._dados: dict[str, tuple[float, Any]] = {}
        self._trava = threading.Lock()
        self._relogio = relogio
        self._maximo = maximo

    @staticmethod
    def chave(*partes: Any) -> str:
        bruto = json.dumps(partes, sort_keys=True, default=str)
        return hashlib.sha256(bruto.encode()).hexdigest()

    def obter(self, chave: str) -> Any | None:
        with self._trava:
            item = self._dados.get(chave)
            if item is None:
                return None
            expira, valor = item
            if expira < self._relogio():
                del self._dados[chave]
                return None
            return valor

    def gravar(self, chave: str, valor: Any, ttl: int) -> None:
        if ttl <= 0:
            return
        with self._trava:
            if len(self._dados) >= self._maximo:
                self._dados.pop(next(iter(self._dados)))
            self._dados[chave] = (self._relogio() + ttl, valor)

    def obter_ou_calcular(self, chave: str, ttl: int, calcular: Callable[[], Any]) -> Any:
        valor = self.obter(chave)
        if valor is None:
            valor = calcular()
            self.gravar(chave, valor, ttl)
        return valor
