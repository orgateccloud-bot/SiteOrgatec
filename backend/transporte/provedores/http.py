"""Cliente HTTP resiliente para integrações externas: timeout, nova tentativa com espera crescente em 429/5xx."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import httpx

from backend.transporte.erros import ProvedorLimiteExcedido, ProvedorRespostaInvalida, ProvedorTimeout

log = logging.getLogger(__name__)

REPETIVEIS = {429, 500, 502, 503, 504}


class ClienteHttp:
    def __init__(
        self,
        provedor: str,
        *,
        timeout: float = 10.0,
        tentativas: int = 3,
        cabecalhos: dict[str, str] | None = None,
        transporte: httpx.BaseTransport | None = None,
        dormir: Callable[[float], None] = time.sleep,
        espera_base: float = 0.5,
    ) -> None:
        self.provedor = provedor
        self.tentativas = tentativas
        self._dormir = dormir
        self._espera_base = espera_base
        self._cliente = httpx.Client(timeout=timeout, headers=cabecalhos or {}, transport=transporte)

    def requisitar(self, metodo: str, url: str, **kwargs: Any) -> Any:
        """Devolve o JSON da resposta. Levanta ErroProvedor tipado quando não há como completar."""
        return self._requisitar(metodo, url, True, **kwargs)

    def requisitar_texto(self, metodo: str, url: str, **kwargs: Any) -> str:
        """Igual a `requisitar`, mas devolve o corpo em texto (CSV, HTML de listagem)."""
        return self._requisitar(metodo, url, False, **kwargs)

    def _requisitar(self, metodo: str, url: str, como_json: bool, **kwargs: Any) -> Any:
        ultimo: httpx.Response | None = None
        for tentativa in range(1, self.tentativas + 1):
            try:
                resp = self._cliente.request(metodo, url, **kwargs)
            except httpx.TimeoutException as exc:
                if tentativa == self.tentativas:
                    raise ProvedorTimeout(self.provedor, "timeout") from exc
                self._esperar(tentativa, None)
                continue
            except httpx.HTTPError as exc:
                if tentativa == self.tentativas:
                    raise ProvedorTimeout(self.provedor, f"falha de conexão: {type(exc).__name__}") from exc
                self._esperar(tentativa, None)
                continue
            if resp.status_code in REPETIVEIS:
                ultimo = resp
                if tentativa < self.tentativas:
                    self._esperar(tentativa, resp.headers.get("Retry-After"))
                    continue
                break
            if resp.status_code >= 400:
                raise ProvedorRespostaInvalida(self.provedor, f"HTTP {resp.status_code}")
            if not como_json:
                return resp.text
            try:
                return resp.json()
            except ValueError as exc:
                raise ProvedorRespostaInvalida(self.provedor, "corpo não é JSON") from exc
        if ultimo is not None and ultimo.status_code == 429:
            raise ProvedorLimiteExcedido(self.provedor, "HTTP 429")
        raise ProvedorTimeout(self.provedor, f"HTTP {ultimo.status_code if ultimo else '?'} após tentativas")

    def _esperar(self, tentativa: int, retry_after: str | None) -> None:
        espera = self._espera_base * (2 ** (tentativa - 1))
        if retry_after and retry_after.isdigit():
            espera = min(float(retry_after), 30.0)
        log.warning("provedor=%s nova tentativa=%s espera=%.1fs", self.provedor, tentativa + 1, espera)
        self._dormir(espera)
