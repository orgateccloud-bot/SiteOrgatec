"""Login do módulo LOCAR com Firebase Authentication, no desenho de backend/transporte/autenticacao.py.

O navegador entra com e-mail e senha direto no Firebase e envia o ID token em `Authorization: Bearer`. O servidor confere
assinatura, validade, emissor e público do token e lê DUAS declarações próprias (custom claims), gravadas pelo escritório com
tools/locar_usuario.py:
  locar_grupo   a qual grupo o usuário pertence (UUID)
  locar_papel   equipe | diretor | leitura
As chaves têm prefixo próprio para não colidir com as da Central de Viagem (`transportadora_id`, `papel`): a mesma conta pode ter
as duas. Sem as duas declarações o token vale como login, mas a API responde 403: ninguém entra só por ter conta.

Ligar: ORGATEC_LOCAR_AUTH=firebase, ORGATEC_FIREBASE_PROJETO=<id do projeto> e, para a tela de entrada,
ORGATEC_LOCAR_FIREBASE_WEB_KEY (ou a mesma ORGATEC_TRANSPORTE_FIREBASE_WEB_KEY, que é do mesmo projeto e é pública por desenho).
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from fastapi import Request

from backend.locar.dominio import PAPEIS, Contexto, grupo_valido, uid_valido
from backend.locar.erros import AcessoNegado, RecursoDesligado
from backend.transporte.autenticacao import Verificador, verificador_google

log = logging.getLogger("orgatec.locar")
Autenticador = Callable[[Request], Contexto]


def autenticador_dev(request: Request) -> Contexto:
    """SOMENTE fora de produção: o contexto vem de cabeçalhos. Em produção, `criar_servicos` recusa este modo."""
    grupo = request.headers.get("X-Locar-Grupo", "")
    papel = request.headers.get("X-Locar-Papel", "equipe")
    usuario = request.headers.get("X-Usuario-Id", "dev")
    if not grupo_valido(grupo) or papel not in PAPEIS or not uid_valido(usuario):
        raise AcessoNegado()
    return Contexto(grupo_id=grupo, usuario_id=usuario, papel=papel)  # type: ignore[arg-type]


def autenticador_recusa_tudo(_request: Request) -> Contexto:
    raise AcessoNegado()


def autenticador_firebase(projeto: str, verificador: Verificador | None = None) -> Autenticador:
    if not projeto:
        raise RecursoDesligado("login Firebase exige ORGATEC_FIREBASE_PROJETO")
    verificar = verificador or verificador_google

    def autenticar(request: Request) -> Contexto:
        cab = request.headers.get("Authorization", "")
        if not cab.startswith("Bearer ") or len(cab) > 4096:
            raise AcessoNegado()
        try:
            dados = verificar(cab[7:].strip(), projeto)
        except Exception as exc:  # noqa: BLE001 - qualquer falha do token é 403; o motivo não vai ao cliente nem ao log
            log.info("token recusado: %s", type(exc).__name__)
            raise AcessoNegado() from exc
        grupo, papel, uid = dados.get("locar_grupo"), dados.get("locar_papel"), dados.get("user_id") or dados.get("sub")
        if not isinstance(grupo, str) or not grupo_valido(grupo) or papel not in PAPEIS or not isinstance(uid, str) or not uid_valido(uid):
            raise AcessoNegado()
        return Contexto(grupo_id=grupo, usuario_id=uid, papel=papel)

    return autenticar
