"""Credencial HMAC dos sensores, sem guardar segredo.

Diferença deliberada do módulo de referência (que cifrava o segredo de cada sensor com Fernet, da biblioteca
`cryptography`, dependência não aprovada para o servidor): o segredo do sensor é DERIVADO,
    segredo = HMAC-SHA256(chave_mestra, "sensor|<id do sensor>|<versão>")
Ele é exibido uma só vez, na criação. O servidor o recalcula para conferir a assinatura de cada leitura, então não há segredo
em repouso para vazar. Rotacionar = subir a versão do sensor (a credencial antiga deixa de valer). Sem a chave mestra
(variável ORGATEC_TRANSPORTE_CHAVE, longa e aleatória) nada funciona: o recurso fica desligado.
"""

from __future__ import annotations

import hashlib
import hmac
import time

from backend.transporte.erros import AcessoNegado, RecursoDesligado

JANELA_RELOGIO_S = 300
CHAVE_MINIMA = 32


class Cofre:
    def __init__(self, chave_mestra: str) -> None:
        if len(chave_mestra or "") < CHAVE_MINIMA:
            raise RecursoDesligado("chave mestra do transporte ausente ou curta (mínimo de 32 caracteres)")
        self._chave = chave_mestra.encode()

    def segredo_do_sensor(self, sensor_id: str, versao: int = 1) -> str:
        return hmac.new(self._chave, f"sensor|{sensor_id}|{versao}".encode(), hashlib.sha256).hexdigest()


def assinar(segredo: str, timestamp: str, corpo: bytes) -> str:
    return hmac.new(segredo.encode(), timestamp.encode() + b"." + corpo, hashlib.sha256).hexdigest()


def verificar_assinatura(segredo: str, timestamp: str | None, assinatura: str | None, corpo: bytes, agora: float | None = None) -> None:
    """Levanta AcessoNegado (sem dizer o motivo) se faltar algo, o relógio estiver fora da janela ou a assinatura não bater."""
    if not timestamp or not assinatura or not timestamp.isdigit():
        raise AcessoNegado()
    if abs((agora if agora is not None else time.time()) - int(timestamp)) > JANELA_RELOGIO_S:
        raise AcessoNegado()
    if not hmac.compare_digest(assinar(segredo, timestamp, corpo), assinatura):
        raise AcessoNegado()
