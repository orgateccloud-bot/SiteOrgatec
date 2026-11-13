"""Login do LOCAR com Firebase: o servidor confere o token e exige locar_grupo e locar_papel. O Google é simulado."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.locar import api
from backend.locar.autenticacao import autenticador_firebase
from backend.locar.erros import RecursoDesligado
from backend.locar.repositorio_locar import RepositorioMemoria

PROJETO = "orgatec-site"
GA = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
GB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
ENV = {"ORGATEC_LOCAR": "1", "ORGATEC_LOCAR_AUTH": "firebase", "ORGATEC_FIREBASE_PROJETO": PROJETO, "ORGATEC_LOCAR_FIREBASE_WEB_KEY": "AIzaChavePublica",
       "ORGATEC_PRODUCAO": "1"}


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
    repo.criar_grupo(GA, "A")
    repo.criar_grupo(GB, "B")
    tokens = {
        "equipe-a": {"user_id": "u1", "locar_grupo": GA, "locar_papel": "equipe"},
        "diretor-a": {"user_id": "u2", "locar_grupo": GA, "locar_papel": "diretor"},
        "equipe-b": {"user_id": "u3", "locar_grupo": GB, "locar_papel": "equipe"},
        "so-transporte": {"user_id": "u4", "transportadora_id": GA, "papel": "gestor"},  # conta do Transporte não entra no LOCAR
        "sem-claims": {"user_id": "u5"},
        "papel-estranho": {"user_id": "u6", "locar_grupo": GA, "locar_papel": "admin"},
        "grupo-ruim": {"user_id": "u7", "locar_grupo": "../etc", "locar_papel": "equipe"},
        "grupo-inexistente": {"user_id": "u8", "locar_grupo": "cccccccc-cccc-4ccc-8ccc-cccccccccccc", "locar_papel": "equipe"},
        "sem-uid": {"locar_grupo": GA, "locar_papel": "equipe"},
    }
    app = FastAPI()
    api.instalar(app, ENV, autenticador=autenticador_firebase(PROJETO, _verificador_falso(tokens)), repo=repo)
    return TestClient(app)


def bearer(t):
    return {"Authorization": f"Bearer {t}"}


def test_equipe_entra_e_o_token_define_o_grupo(amb):
    r = amb.get("/api/locar/contexto", headers=bearer("equipe-a"))
    assert r.status_code == 200 and r.json()["papel"] == "equipe" and r.json()["grupo"]["id"] == GA and r.json()["ambiente"] == "producao"
    assert amb.get("/api/locar/contexto", headers=bearer("equipe-b")).json()["grupo"]["id"] == GB


def test_diretor_entra_mas_nao_escreve(amb):
    assert amb.get("/api/locar/contexto", headers=bearer("diretor-a")).status_code == 200
    assert amb.post("/api/locar/itens", headers=bearer("diretor-a"), json={"tipo": "obrigacao", "titulo": "x"}).status_code == 403


@pytest.mark.parametrize("token", ["so-transporte", "sem-claims", "papel-estranho", "grupo-ruim", "grupo-inexistente", "sem-uid", "token-falso"])
def test_sem_as_duas_declaracoes_validas_a_resposta_e_403(amb, token):
    r = amb.get("/api/locar/contexto", headers=bearer(token))
    assert r.status_code == 403 and r.json() == {"detail": "Acesso negado."}  # o motivo não vai ao cliente


def test_sem_cabecalho_ou_com_cabecalho_gigante_e_403(amb):
    assert amb.get("/api/locar/contexto").status_code == 403
    assert amb.get("/api/locar/contexto", headers={"Authorization": "Bearer " + "x" * 5000}).status_code == 403
    assert amb.get("/api/locar/contexto", headers={"Authorization": "Basic abc"}).status_code == 403


def test_em_producao_os_cabecalhos_de_desenvolvimento_nao_valem(amb):
    h = {"X-Locar-Grupo": GA, "X-Locar-Papel": "equipe", "X-Usuario-Id": "dev"}
    assert amb.get("/api/locar/contexto", headers=h).status_code == 403


def test_firebase_exige_o_projeto():
    with pytest.raises(RecursoDesligado):
        autenticador_firebase("")


def test_entrada_publica_traz_a_chave_web_so_no_modo_firebase(amb):
    assert amb.get("/api/locar/entrada").json() == {"modo": "firebase", "chave_web": "AIzaChavePublica"}
