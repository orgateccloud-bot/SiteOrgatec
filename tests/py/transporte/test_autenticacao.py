"""Login com Firebase: o servidor confere o token e exige as declarações transportadora_id e papel. O Google é simulado."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.transporte import api
from backend.transporte.autenticacao import autenticador_firebase
from backend.transporte.erros import RecursoDesligado
from backend.transporte.repositorio_transporte import RepositorioMemoria

PROJETO = "orgatec-site"
ENV = {"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_AUTH": "firebase", "ORGATEC_FIREBASE_PROJETO": PROJETO,
       "ORGATEC_TRANSPORTE_FIREBASE_WEB_KEY": "AIzaChavePublicaDeTeste", "ORGATEC_PRODUCAO": "1"}


def _verificador_falso(tokens: dict):
    def verificar(token, projeto):
        assert projeto == PROJETO
        if token not in tokens:
            raise ValueError("token inválido")
        return tokens[token]
    return verificar


@pytest.fixture
def amb():
    repo = RepositorioMemoria()
    a, b = repo.criar_transportadora(), repo.criar_transportadora()
    tokens = {
        "gestor-a": {"user_id": "u1", "transportadora_id": a, "papel": "gestor"},
        "leitura-a": {"user_id": "u2", "transportadora_id": a, "papel": "leitura"},
        "gestor-b": {"user_id": "u3", "transportadora_id": b, "papel": "gestor"},
        "sem-claims": {"user_id": "u4"},
        "papel-estranho": {"user_id": "u5", "transportadora_id": a, "papel": "admin"},
        "tenant-ruim": {"user_id": "u6", "transportadora_id": "../etc", "papel": "gestor"},
    }
    app = FastAPI()
    api.instalar(app, ENV, autenticador=autenticador_firebase(PROJETO, _verificador_falso(tokens)), repo=repo)
    return TestClient(app), a, b


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_token_valido_com_declaracoes_entra_e_enxerga_so_a_propria_transportadora(amb):
    cli, a, b = amb
    assert cli.post("/api/transporte/veiculos", headers=_h("gestor-a"), json={"placa": "ABC1D23", "eixos": 5, "consumo_km_l_carregado": 2.5,
                                                                              "consumo_km_l_vazio": 3.2, "tanque_l": 600}).status_code == 201
    assert len(cli.get("/api/transporte/veiculos", headers=_h("gestor-a")).json()) == 1
    assert cli.get("/api/transporte/veiculos", headers=_h("gestor-b")).json() == []  # outro cliente não vê
    assert cli.get("/api/transporte/contexto", headers=_h("leitura-a")).json()["papel"] == "leitura"


def test_leitura_nao_escreve(amb):
    cli, _, _ = amb
    r = cli.post("/api/transporte/veiculos", headers=_h("leitura-a"), json={"placa": "ABC1D23", "eixos": 5, "consumo_km_l_carregado": 2.5,
                                                                            "consumo_km_l_vazio": 3.2, "tanque_l": 600})
    assert r.status_code == 403


@pytest.mark.parametrize("cab", [{}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer"}, _h("falso"), _h("sem-claims"), _h("papel-estranho"), _h("tenant-ruim")])
def test_tudo_que_nao_e_login_completo_responde_403_sem_dizer_o_motivo(amb, cab):
    cli, _, _ = amb
    r = cli.get("/api/transporte/veiculos", headers=cab)
    assert r.status_code == 403 and "token" not in r.text.lower() and "claim" not in r.text.lower()


def test_cabecalhos_de_desenvolvimento_nao_valem_com_login_firebase(amb):
    cli, a, _ = amb
    assert cli.get("/api/transporte/veiculos", headers={"X-Transportadora-Id": a, "X-Usuario-Papel": "gestor"}).status_code == 403


def test_tela_descobre_como_entrar_sem_login(amb):
    cli, _, _ = amb
    r = cli.get("/api/transporte/entrada")
    assert r.status_code == 200 and r.json() == {"modo": "firebase", "chave_web": "AIzaChavePublicaDeTeste"}


def test_projeto_obrigatorio_e_dev_continua_recusado_em_producao():
    with pytest.raises(RecursoDesligado):
        autenticador_firebase("")
    with pytest.raises(RecursoDesligado):
        api.criar_servicos({"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_AUTH": "firebase"})
    with pytest.raises(RecursoDesligado):
        api.criar_servicos({"ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_AUTH": "dev", "ORGATEC_PRODUCAO": "1"})
