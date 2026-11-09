"""Limites da API do módulo: por usuário logado (o painel consulta a cada 15 s) e por IP só para acessos negados."""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.transporte import api
from backend.transporte.dominio import Contexto
from backend.transporte.erros import AcessoNegado
from backend.transporte.repositorio_transporte import RepositorioMemoria
from backend.transporte.telemetria.ingestao import Limitador

ENV = {"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_AUTH": "dev"}


def _app(limite_ip=None):
    repo = RepositorioMemoria()
    tid = repo.criar_transportadora()
    app = FastAPI()
    api.instalar(app, ENV, repo=repo, limite_ip=limite_ip)
    return app, TestClient(app), {"X-Transportadora-Id": tid, "X-Usuario-Papel": "gestor", "X-Usuario-Id": "u1"}


def test_painel_que_consulta_a_cada_15_s_nao_leva_429_do_limite_de_formularios():
    chamadas = []
    app, cli, h = _app(limite_ip=lambda req: chamadas.append(1))
    for _ in range(100):  # bem acima dos 20 por 10 minutos do limite por IP dos formulários
        assert cli.get("/api/transporte/contexto", headers=h).status_code == 200
    assert chamadas == []  # acesso autorizado não gasta o limite por IP


def test_limite_por_usuario_responde_429_e_nao_afeta_outro_usuario():
    app, cli, h = _app()
    app.state.transporte.limitador_usuario = Limitador(maximo=3, janela_s=60)
    codigos = [cli.get("/api/transporte/contexto", headers=h).status_code for _ in range(5)]
    assert codigos[:3] == [200, 200, 200] and 429 in codigos[3:]
    assert cli.get("/api/transporte/contexto", headers={**h, "X-Usuario-Id": "u2"}).status_code == 200


def test_acesso_negado_gasta_o_limite_por_ip():
    def limite(_req):
        raise HTTPException(status_code=429, detail="muitas requisições")

    _, cli, _ = _app(limite_ip=limite)
    assert cli.get("/api/transporte/contexto", headers={"X-Usuario-Papel": "gestor"}).status_code == 429  # sem transportadora: negado, vai ao limite


def test_tipos_importados_existem():
    assert Contexto and AcessoNegado
