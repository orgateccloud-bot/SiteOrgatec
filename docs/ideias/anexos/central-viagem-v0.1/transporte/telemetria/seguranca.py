"""Segredos de sensor (cifrados em repouso), assinatura HMAC das leituras e tokens curtos do canal em tempo real."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from cryptography.fernet import Fernet, InvalidToken

from transporte.erros import AcessoNegado, ErroTransporte

JANELA_RELOGIO_S = 300
VALIDADE_TOKEN_STREAM_S = 300


class Cofre:
    def __init__(self, chave: str) -> None:
        if not chave:
            raise ErroTransporte("TRANSPORTE_CHAVE_CRIPTO não configurada")
        self._f = Fernet(chave.encode())

    @staticmethod
    def novo_segredo() -> str:
        return secrets.token_urlsafe(32)

    def cifrar(self, segredo: str) -> str:
        return self._f.encrypt(segredo.encode()).decode()

    def decifrar(self, cifrado: str) -> str:
        try:
            return self._f.decrypt(cifrado.encode()).decode()
        except InvalidToken as exc:
            raise ErroTransporte("segredo do sensor não pôde ser lido (chave trocada?)") from exc


def assinar(segredo: str, timestamp: str, corpo: bytes) -> str:
    return hmac.new(segredo.encode(), timestamp.encode() + b"." + corpo, hashlib.sha256).hexdigest()


def verificar_assinatura(segredo: str, timestamp: str | None, assinatura: str | None, corpo: bytes) -> None:
    if not timestamp or not assinatura or not timestamp.isdigit():
        raise AcessoNegado()
    if abs(time.time() - int(timestamp)) > JANELA_RELOGIO_S:
        raise AcessoNegado()
    if not hmac.compare_digest(assinar(segredo, timestamp, corpo), assinatura):
        raise AcessoNegado()


def gerar_token_stream(chave: str, viagem_id: str, transportadora_id: str, agora: float | None = None) -> str:
    exp = int((agora or time.time()) + VALIDADE_TOKEN_STREAM_S)
    sig = hmac.new(chave.encode(), f"{viagem_id}|{transportadora_id}|{exp}".encode(), hashlib.sha256).hexdigest()
    return f"{exp}.{transportadora_id}.{sig}"


def verificar_token_stream(chave: str, viagem_id: str, token: str) -> str:
    """Devolve a transportadora do token válido; levanta AcessoNegado caso contrário."""
    try:
        exp_txt, transportadora_id, sig = token.split(".", 2)
        exp = int(exp_txt)
    except ValueError as exc:
        raise AcessoNegado() from exc
    esperado = hmac.new(chave.encode(), f"{viagem_id}|{transportadora_id}|{exp}".encode(), hashlib.sha256).hexdigest()
    if exp < time.time() or not hmac.compare_digest(esperado, sig):
        raise AcessoNegado()
    return transportadora_id
