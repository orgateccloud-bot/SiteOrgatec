"""Montagem da API: `incluir_no_app(app_existente, ...)` acopla ao back-end atual; `criar_app()` sobe isolado."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from transporte.api import rotas, telemetria
from transporte.api.deps import Autenticador, Servicos, autenticador_dev
from transporte.config import Config, obter_config
from transporte.db.sessao import FabricaSessao, criar_engine
from transporte.db.tabelas import Base
from transporte.erros import ErroProvedor, ErroTransporte
from transporte.provedores.registro import FabricaProvedores
from transporte.telemetria.broker import Broker
from transporte.telemetria.ingestao import Limitador
from transporte.telemetria.seguranca import Cofre

log = logging.getLogger("transporte")
PASTA_WEB = Path(__file__).resolve().parents[2] / "web" / "transporte"


def montar_servicos(
    config: Config,
    autenticador: Autenticador | None = None,
    sessoes: FabricaSessao | None = None,
    provedores: FabricaProvedores | None = None,
) -> Servicos:
    if config.auth_modo == "externo" and autenticador is None:
        raise RuntimeError("TRANSPORTE_AUTH_MODO=externo exige passar o autenticador do sistema hospedeiro.")
    return Servicos(
        config=config,
        sessoes=sessoes or FabricaSessao(criar_engine(config.database_url)),
        provedores=provedores or FabricaProvedores(config),
        broker=Broker(),
        limitador=Limitador(),
        autenticador=autenticador or autenticador_dev,
        cofre=Cofre(config.chave_cripto) if config.sensores_ativo else None,
    )


def _tratar_erro(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ErroTransporte):  # o handler só é registrado para ErroTransporte
        return JSONResponse({"erro": "Erro interno."}, status_code=500)
    if exc.codigo_http >= 500 or isinstance(exc, ErroProvedor):
        log.warning("erro %s em %s: %s", type(exc).__name__, request.url.path, exc)
    corpo: dict[str, str] = {"erro": exc.mensagem_publica, "codigo": type(exc).__name__}
    if isinstance(exc, ErroProvedor):
        corpo["estado"] = exc.estado
    return JSONResponse(corpo, status_code=exc.codigo_http)


def incluir_no_app(app: FastAPI, servicos: Servicos) -> None:
    app.state.servicos = servicos
    app.add_exception_handler(ErroTransporte, _tratar_erro)
    app.include_router(rotas.router)
    app.include_router(telemetria.router)


def criar_app(
    config: Config | None = None,
    *,
    autenticador: Autenticador | None = None,
    servir_web: bool = True,
    criar_tabelas: bool = False,
    provedores: FabricaProvedores | None = None,
) -> FastAPI:
    config = config or obter_config()
    app = FastAPI(title="Central de Viagem — ORGATEC", version="0.1.0", docs_url="/api/transporte/docs")
    servicos = montar_servicos(config, autenticador, provedores=provedores)
    if criar_tabelas:
        Base.metadata.create_all(servicos.sessoes.engine)  # só desenvolvimento/teste; produção usa Alembic
    incluir_no_app(app, servicos)
    if servir_web and PASTA_WEB.is_dir():
        app.mount("/transporte", StaticFiles(directory=PASTA_WEB, html=True), name="web")

        @app.get("/", include_in_schema=False)
        def raiz() -> RedirectResponse:
            return RedirectResponse("/transporte/central.html")

    return app
