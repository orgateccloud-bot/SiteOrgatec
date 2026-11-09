"""Dependências da API: configuração, sessão, contexto do usuário e serviços compartilhados."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from transporte.config import Config
from transporte.db.sessao import FabricaSessao
from transporte.db.tabelas import Transportadora
from transporte.dominio import Contexto, Papel
from transporte.erros import AcessoNegado, RecursoDesligado
from transporte.provedores.registro import FabricaProvedores
from transporte.telemetria.broker import Broker
from transporte.telemetria.ingestao import Limitador
from transporte.telemetria.seguranca import Cofre

# Autenticador do sistema hospedeiro: recebe a requisição e devolve o Contexto (ou levanta AcessoNegado).
Autenticador = Callable[[Request], Contexto]


@dataclass
class Servicos:
    config: Config
    sessoes: FabricaSessao
    provedores: FabricaProvedores
    broker: Broker
    limitador: Limitador
    autenticador: Autenticador
    cofre: Cofre | None

    def cofre_ativo(self) -> Cofre:
        if self.cofre is None:
            raise RecursoDesligado()
        return self.cofre


def autenticador_dev(request: Request) -> Contexto:
    """SOMENTE desenvolvimento/homologação. Recusado em produção pela validação da Config."""
    tid = request.headers.get("X-Transportadora-Id")
    papel = request.headers.get("X-Usuario-Papel", "gestor")
    if not tid or papel not in ("gestor", "motorista", "leitura"):
        raise AcessoNegado()
    return Contexto(transportadora_id=tid, usuario_id=request.headers.get("X-Usuario-Id", "dev"), papel=papel)  # type: ignore[arg-type]


def servicos(request: Request) -> Servicos:
    return request.app.state.servicos


def sessao(s: Servicos = Depends(servicos)) -> Iterator[Session]:  # noqa: B008
    yield from s.sessoes()


def contexto(request: Request, s: Servicos = Depends(servicos), db: Session = Depends(sessao)) -> Contexto:  # noqa: B008
    ctx = s.autenticador(request)
    if db.get(Transportadora, ctx.transportadora_id) is None:
        raise AcessoNegado()
    return ctx


def exigir(*papeis: Papel) -> Callable[[Contexto], Contexto]:
    def verificar(ctx: Contexto = Depends(contexto)) -> Contexto:  # noqa: B008
        if ctx.papel not in papeis:
            raise AcessoNegado()
        return ctx

    return verificar


def sensores_ligados(s: Servicos = Depends(servicos)) -> Servicos:  # noqa: B008
    if not s.config.sensores_ativo or s.cofre is None:
        raise RecursoDesligado()
    return s
