"""API do painel do grupo LOCAR (APIRouter incluído em backend/app.py, atrás da flag ORGATEC_LOCAR=1).

Sem a flag, nada é registrado e as rotas respondem 404. Em produção a API só aceita login Firebase com as declarações
`locar_grupo` e `locar_papel`; o modo `dev` (cabeçalhos X-Locar-*) é recusado. Toda escrita e toda leitura de entidade sensível
entram na trilha de auditoria do grupo. Visibilidade: ver backend/locar/dominio.py.
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from backend.locar.autenticacao import Autenticador, autenticador_dev, autenticador_firebase, autenticador_recusa_tudo
from backend.locar.dominio import Contexto, EntidadePatch, ItemEntrada, ItemPatch, entidade_publica, entidade_visivel, item_visivel
from backend.locar.erros import AcessoNegado, EntradaInvalida, ErroLocar, LimiteExcedido, NaoEncontrado, RecursoDesligado
from backend.locar.repositorio_locar import RepositorioBase, criar_repositorio

log = logging.getLogger("orgatec.locar")
# O Brasil não tem horário de verão desde 2019 (Decreto 9.772/2019): o deslocamento fixo dispensa o banco de fusos (a imagem slim não traz).
FUSO_BRASILIA = timezone(timedelta(hours=-3))


def ligado(env: dict[str, str] | None = None) -> bool:
    return (env if env is not None else os.environ).get("ORGATEC_LOCAR", "0") == "1"


class Limitador:
    """Janela deslizante por usuário (em memória, por instância)."""

    def __init__(self, maximo: int = 600, janela_s: float = 60.0) -> None:
        self._maximo, self._janela = maximo, janela_s
        self._hist: dict[str, deque[float]] = defaultdict(deque)
        self._trava = threading.Lock()

    def registrar(self, chave: str) -> None:
        agora = time.monotonic()
        with self._trava:
            h = self._hist[chave]
            while h and h[0] < agora - self._janela:
                h.popleft()
            if len(h) >= self._maximo:
                raise LimiteExcedido()
            h.append(agora)


def hoje_brasilia() -> date:
    return datetime.now(FUSO_BRASILIA).date()


@dataclass
class Servicos:
    repo: RepositorioBase
    autenticador: Autenticador
    producao: bool
    entrada: dict[str, Any] = field(default_factory=dict)  # o que a tela precisa para entrar (modo e chave web pública)
    limite_ip: Callable[[Request], Any] | None = None  # limite por IP do site: só tentativas de acesso NEGADAS gastam dele
    limitador_usuario: Limitador = field(default_factory=Limitador)
    hoje: Callable[[], date] = hoje_brasilia


def criar_servicos(env: dict[str, str] | None = None, autenticador: Autenticador | None = None, repo: RepositorioBase | None = None,
                   limite_ip: Callable[[Request], Any] | None = None) -> Servicos:
    e = env if env is not None else dict(os.environ)
    producao = e.get("ORGATEC_PRODUCAO", "0") == "1"
    modo = e.get("ORGATEC_LOCAR_AUTH", "dev")
    if autenticador is None:
        if modo == "dev":
            if producao:
                raise RecursoDesligado("ORGATEC_LOCAR_AUTH=dev não é permitido em produção")
            autenticador = autenticador_dev
        elif modo == "firebase":
            autenticador = autenticador_firebase(e.get("ORGATEC_FIREBASE_PROJETO", "").strip())
        else:
            autenticador = autenticador_recusa_tudo
    repo = repo or criar_repositorio(e)
    if e.get("ORGATEC_LOCAR_DEMO", "0") == "1" and not producao:
        from backend.locar import demo

        demo.carregar(repo)  # só desenvolvimento: grupo fictício para experimentar a tela
    chave_web = (e.get("ORGATEC_LOCAR_FIREBASE_WEB_KEY") or e.get("ORGATEC_TRANSPORTE_FIREBASE_WEB_KEY") or "").strip()
    entrada = {"modo": modo, **({"chave_web": chave_web} if modo == "firebase" and chave_web else {})}
    return Servicos(repo, autenticador, producao, entrada=entrada, limite_ip=limite_ip)


def servicos(request: Request) -> Servicos:
    return request.app.state.locar


def contexto(request: Request, s: Servicos = Depends(servicos)) -> Contexto:  # noqa: B008
    try:
        ctx = s.autenticador(request)
        if not s.repo.existe_grupo(ctx.grupo_id):
            raise AcessoNegado()
    except AcessoNegado:
        if s.limite_ip:
            s.limite_ip(request)  # quem erra o acesso repetidamente leva 429 pelo limite por IP do site
        raise
    s.limitador_usuario.registrar(f"{ctx.grupo_id}:{ctx.usuario_id}")
    return ctx


def exigir(*papeis: str) -> Callable[..., Contexto]:
    def verificar(ctx: Contexto = Depends(contexto)) -> Contexto:  # noqa: B008
        if ctx.papel not in papeis:
            raise AcessoNegado()
        return ctx
    return verificar


EQUIPE = exigir("equipe")
router = APIRouter(prefix="/api/locar", tags=["locar"])


def tratar_erro(_request: Request, exc: ErroLocar) -> JSONResponse:
    if exc.codigo_http >= 500:
        log.error("erro no módulo LOCAR: %s", type(exc).__name__)  # sem dado do grupo no log
    return JSONResponse(status_code=exc.codigo_http, content={"detail": exc.mensagem_publica})


# ---------------------------------------------------------------- leitura com visibilidade

def _visiveis(s: Servicos, ctx: Contexto) -> list[dict[str, Any]]:
    acesso = s.repo.obter_acesso(ctx.grupo_id, ctx.usuario_id)
    return [e for e in s.repo.listar(ctx.grupo_id, "entidades") if entidade_visivel(ctx, e, acesso)]


def _registrar_leitura_sensivel(s: Servicos, ctx: Contexto, entidades: list[dict[str, Any]]) -> None:
    ids = sorted(e["id"] for e in entidades if e.get("sensivel"))
    if ids:
        s.repo.anexar_auditoria(ctx.grupo_id, ctx.usuario_id, "leitura.sensivel", "entidades", ",".join(ids)[:200])


def _itens_visiveis(s: Servicos, ctx: Contexto, entidades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = {e["id"] for e in entidades}
    itens = [i for i in s.repo.listar(ctx.grupo_id, "itens") if item_visivel(i, ids)]
    return [{k: v for k, v in i.items() if k != "grupo_id"} for i in sorted(itens, key=lambda i: (i.get("prazo") is None, i.get("prazo") or "", i["id"]))]


@router.get("/entrada")
def como_entrar(s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    """Sem login: a tela pergunta se mostra o painel de desenvolvimento ou o formulário de entrada (a chave web é pública)."""
    return s.entrada


@router.get("/contexto")
def ver_contexto(ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    grupo = s.repo.obter_grupo(ctx.grupo_id) or {}
    return {"papel": ctx.papel, "usuario_id": ctx.usuario_id, "grupo": {"id": ctx.grupo_id, "nome": grupo.get("nome", ""), "polos": grupo.get("polos", [])},
            "ambiente": "producao" if s.producao else "desenvolvimento", "entrada": s.entrada.get("modo")}


@router.get("/agenda")
def agenda(ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    """Tudo o que o painel precisa numa chamada: a data de hoje (a do servidor, em Brasília), as entidades e os itens que o usuário vê."""
    entidades = _visiveis(s, ctx)
    _registrar_leitura_sensivel(s, ctx, entidades)
    return {"hoje": s.hoje().isoformat(), "entidades": [entidade_publica(ctx, e) for e in entidades], "itens": _itens_visiveis(s, ctx, entidades)}


@router.get("/entidades")
def listar_entidades(ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> list[dict[str, Any]]:  # noqa: B008
    entidades = _visiveis(s, ctx)
    _registrar_leitura_sensivel(s, ctx, entidades)
    return [entidade_publica(ctx, e) for e in entidades]


@router.get("/itens")
def listar_itens(entidade_id: str | None = None, status: str | None = None, ctx: Contexto = Depends(contexto),  # noqa: B008
                 s: Servicos = Depends(servicos)) -> list[dict[str, Any]]:  # noqa: B008
    entidades = _visiveis(s, ctx)
    _registrar_leitura_sensivel(s, ctx, entidades)
    itens = _itens_visiveis(s, ctx, entidades)
    if entidade_id is not None:
        itens = [i for i in itens if i.get("entidade_id") == entidade_id]
    if status is not None:
        itens = [i for i in itens if i["status"] == status]
    return itens


# ---------------------------------------------------------------- escrita (só a equipe)

@router.patch("/entidades/{entidade_id}")
def atualizar_entidade(entidade_id: str, entrada: EntidadePatch, ctx: Contexto = Depends(EQUIPE), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    mudancas = entrada.model_dump(mode="json", exclude_unset=True)
    if not mudancas:
        raise EntradaInvalida("Nada para atualizar.")
    atual = s.repo.obter(ctx.grupo_id, "entidades", entidade_id)  # de outro grupo: NaoEncontrado
    sucessora = mudancas.get("sucessora_id")
    if sucessora is not None and (sucessora == entidade_id or not s.repo.existe(ctx.grupo_id, "entidades", sucessora)):
        raise EntradaInvalida("A sucessora deve ser outra entidade do grupo.")
    novo = s.repo.atualizar(ctx.grupo_id, "entidades", entidade_id, mudancas)
    s.repo.anexar_auditoria(ctx.grupo_id, ctx.usuario_id, "entidade.atualizar", "entidade", atual["id"])
    return entidade_publica(ctx, novo)


@router.post("/itens", status_code=201)
def criar_item(entrada: ItemEntrada, ctx: Contexto = Depends(EQUIPE), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    if entrada.entidade_id is not None and not s.repo.existe(ctx.grupo_id, "entidades", entrada.entidade_id):
        raise EntradaInvalida("Entidade inexistente neste grupo.")
    rid = entrada.id or f"i-{uuid.uuid4().hex[:12]}"
    if s.repo.existe(ctx.grupo_id, "itens", rid):
        raise EntradaInvalida("Já existe um item com esse id.")
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    reg = entrada.model_dump(mode="json", exclude={"id"}) | {"criado_em": agora, "atualizado_em": agora, "atualizado_por": ctx.usuario_id}
    item = s.repo.inserir(ctx.grupo_id, "itens", rid, reg)
    s.repo.anexar_auditoria(ctx.grupo_id, ctx.usuario_id, "item.criar", "item", rid)
    return {k: v for k, v in item.items() if k != "grupo_id"}


@router.patch("/itens/{item_id}")
def atualizar_item(item_id: str, entrada: ItemPatch, ctx: Contexto = Depends(EQUIPE), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    mudancas = entrada.model_dump(mode="json", exclude_unset=True)
    if not mudancas:
        raise EntradaInvalida("Nada para atualizar.")
    s.repo.obter(ctx.grupo_id, "itens", item_id)  # de outro grupo: NaoEncontrado
    mudancas |= {"atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"), "atualizado_por": ctx.usuario_id}
    item = s.repo.atualizar(ctx.grupo_id, "itens", item_id, mudancas)
    s.repo.anexar_auditoria(ctx.grupo_id, ctx.usuario_id, "item.atualizar", "item", item_id)
    return {k: v for k, v in item.items() if k != "grupo_id"}


@router.get("/auditoria")
def ver_auditoria(limite: int = 100, ctx: Contexto = Depends(EQUIPE), s: Servicos = Depends(servicos)) -> list[dict[str, Any]]:  # noqa: B008
    if not 1 <= limite <= 500:
        raise EntradaInvalida("O limite deve ficar entre 1 e 500.")
    return [{k: e[k] for k in ("seq", "quando", "usuario_id", "acao", "recurso", "recurso_id", "audit_hash")} for e in s.repo.auditoria(ctx.grupo_id, limite)]


@router.get("/auditoria/verificar")
def verificar_auditoria(ctx: Contexto = Depends(EQUIPE), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    integra, elos = s.repo.verificar_cadeia(ctx.grupo_id)
    return {"integra": integra, "elos": elos}


def instalar(app: Any, env: dict[str, str] | None = None, autenticador: Autenticador | None = None, repo: RepositorioBase | None = None,
             limite_ip: Any = None) -> bool:
    """Chamado por backend/app.py. Com a flag desligada não registra nada e devolve False."""
    if not ligado(env):
        return False
    app.state.locar = criar_servicos(env, autenticador, repo, limite_ip)
    app.add_exception_handler(ErroLocar, tratar_erro)
    app.include_router(router)
    return True


__all__ = ["instalar", "ligado", "criar_servicos", "router", "NaoEncontrado"]
