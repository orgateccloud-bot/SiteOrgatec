"""Login da Central de Viagem com Firebase Authentication (decisão R4, autorizada em 09/11/2026).

O navegador entra com e-mail e senha direto no Firebase (Identity Toolkit) e envia o ID token em `Authorization: Bearer`.
O servidor confere assinatura, validade, emissor e público do token com as chaves públicas do Google e lê DUAS declarações
próprias (custom claims) gravadas pelo escritório com `tools/transporte_usuario.py`:
  transportadora_id  qual cliente o usuário pertence
  papel              gestor | motorista | leitura
Sem as duas declarações o token vale como login, mas a API responde 403: ninguém entra só por ter conta.

Ligar: ORGATEC_TRANSPORTE_AUTH=firebase, ORGATEC_FIREBASE_PROJETO=<id do projeto> e, para a tela de entrada,
ORGATEC_TRANSPORTE_FIREBASE_WEB_KEY=<chave de API web do projeto> (é pública por desenho; restrinja por domínio no Google Cloud).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import Any

from fastapi import Request

from backend.transporte.dominio import Contexto
from backend.transporte.erros import AcessoNegado, RecursoDesligado

log = logging.getLogger("orgatec.transporte")
PAPEIS = ("gestor", "motorista", "leitura")
_UUID = re.compile(r"^[0-9a-fA-F-]{36}$")
Verificador = Callable[[str, str], dict[str, Any]]


def verificador_google(token: str, projeto: str) -> dict[str, Any]:
    """Confere o ID token do Firebase (assinatura, exp, iss e aud). Usa as chaves públicas do Google, em cache."""
    from google.auth.transport import requests as grequests
    from google.oauth2 import id_token

    return id_token.verify_firebase_token(token, grequests.Request(), audience=projeto)


def autenticador_firebase(projeto: str, verificador: Verificador | None = None) -> Callable[[Request], Contexto]:
    if not projeto:
        raise RecursoDesligado("login Firebase exige ORGATEC_FIREBASE_PROJETO")
    verificar = verificador or verificador_google

    def autenticar(request: Request) -> Contexto:
        cab = request.headers.get("Authorization", "")
        if not cab.startswith("Bearer ") or len(cab) > 4096:
            raise AcessoNegado()
        try:
            dados = verificar(cab[7:].strip(), projeto)
        except Exception as exc:  # noqa: BLE001 - qualquer falha do token é 403; o motivo não vai ao cliente nem ao log (sem dado pessoal)
            log.info("token recusado: %s", type(exc).__name__)
            raise AcessoNegado() from exc
        tid, papel, uid = dados.get("transportadora_id"), dados.get("papel"), dados.get("user_id") or dados.get("sub")
        if not isinstance(tid, str) or not _UUID.match(tid) or papel not in PAPEIS or not uid:
            raise AcessoNegado()
        return Contexto(transportadora_id=tid, usuario_id=str(uid), papel=papel)

    return autenticar
