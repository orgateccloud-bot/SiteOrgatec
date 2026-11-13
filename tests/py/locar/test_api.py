"""API do painel LOCAR: isolamento entre grupos, papéis, entidade sensível, escrita só da equipe e trilha de auditoria."""

from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.locar import api
from backend.locar.erros import RecursoDesligado
from backend.locar.repositorio_locar import RepositorioMemoria

GA = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
GB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
ENV = {"ORGATEC_LOCAR": "1"}


def cab(grupo=GA, papel="equipe", uid="u-eq"):
    return {"X-Locar-Grupo": grupo, "X-Locar-Papel": papel, "X-Usuario-Id": uid}


def _ent(nome, tipo="pj", sensivel=False, titulares=()):
    return {"nome": nome, "tipo": tipo, "status": "ativa", "sucessora_id": None, "regime": "lucro_real", "regime_vigencia": None,
            "documento_mascarado": None, "sensivel": sensivel, "titulares": list(titulares)}


def _item(entidade, titulo, prazo=None, status="a_fazer", tipo="obrigacao"):
    return {"entidade_id": entidade, "tipo": tipo, "titulo": titulo, "prazo": prazo, "prazo_a_confirmar": False, "responsavel": "equipe",
            "status": status, "fonte_id": None, "modelo_id": None, "evidencia_ref": None}


@pytest.fixture
def amb():
    repo = RepositorioMemoria()
    repo.criar_grupo(GA, "Grupo A")
    repo.criar_grupo(GB, "Grupo B")
    repo.inserir(GA, "entidades", "e1", _ent("Empresa 1"))
    repo.inserir(GA, "entidades", "e2", _ent("Empresa 2"))
    repo.inserir(GA, "entidades", "pf", _ent("Produtor PF", "produtor_pf", True, ["u-tit"]))
    repo.inserir(GB, "entidades", "eb", _ent("Empresa B"))
    repo.inserir(GA, "itens", "ia1", _item("e1", "Item 1", "2026-12-01"))
    repo.inserir(GA, "itens", "ia2", _item("e2", "Item 2", "2026-12-02"))
    repo.inserir(GA, "itens", "ia3", _item(None, "Item do grupo", "2027-01-01", tipo="evento_reforma"))
    repo.inserir(GA, "itens", "ia4", _item("pf", "Item do produtor", "2026-12-03"))
    repo.inserir(GB, "itens", "ib1", _item("eb", "Item B", "2026-12-01"))
    repo.salvar_acesso(GA, "u-dir", "diretor", ["e1", "pf"])  # cita a entidade sensível, mas ele não é titular
    app = FastAPI()
    assert api.instalar(app, ENV, repo=repo)
    app.state.locar.hoje = lambda: date(2026, 11, 12)
    return TestClient(app), repo


def test_flag_desligada_nao_registra_nada():
    app = FastAPI()
    assert api.instalar(app, {}) is False
    assert TestClient(app).get("/api/locar/entrada").status_code == 404


def test_producao_recusa_o_modo_dev():
    with pytest.raises(RecursoDesligado):
        api.criar_servicos({"ORGATEC_LOCAR": "1", "ORGATEC_PRODUCAO": "1", "ORGATEC_LOCAR_AUTH": "dev"})


def test_entrada_sem_login_diz_o_modo_e_so_expoe_a_chave_publica_no_firebase():
    s = api.criar_servicos({"ORGATEC_LOCAR": "1", "ORGATEC_LOCAR_AUTH": "firebase", "ORGATEC_FIREBASE_PROJETO": "p",
                            "ORGATEC_TRANSPORTE_FIREBASE_WEB_KEY": "chave-web"}, repo=RepositorioMemoria())
    assert s.entrada == {"modo": "firebase", "chave_web": "chave-web"}
    assert api.criar_servicos({"ORGATEC_LOCAR": "1"}, repo=RepositorioMemoria()).entrada == {"modo": "dev"}


def test_equipe_ve_todas_as_entidades_e_itens_do_proprio_grupo(amb):
    c, _ = amb
    r = c.get("/api/locar/agenda", headers=cab()).json()
    assert r["hoje"] == "2026-11-12"
    assert {e["id"] for e in r["entidades"]} == {"e1", "e2", "pf"}
    assert {i["id"] for i in r["itens"]} == {"ia1", "ia2", "ia3", "ia4"}
    assert all("grupo_id" not in i for i in r["itens"]) and all("grupo_id" not in e for e in r["entidades"])
    assert [i["id"] for i in r["itens"]] == ["ia1", "ia2", "ia4", "ia3"]  # por prazo


def test_um_grupo_nao_ve_o_outro(amb):
    c, _ = amb
    r = c.get("/api/locar/agenda", headers=cab(GB)).json()
    assert {e["id"] for e in r["entidades"]} == {"eb"} and {i["id"] for i in r["itens"]} == {"ib1"}
    assert c.patch("/api/locar/itens/ia1", headers=cab(GB), json={"status": "entregue"}).status_code == 404
    assert c.patch("/api/locar/entidades/e1", headers=cab(GB), json={"status": "extinta"}).status_code == 404


def test_grupo_inexistente_ou_malformado_leva_403(amb):
    c, _ = amb
    assert c.get("/api/locar/agenda", headers=cab("cccccccc-cccc-4ccc-8ccc-cccccccccccc")).status_code == 403
    assert c.get("/api/locar/agenda", headers=cab("../etc")).status_code == 403
    assert c.get("/api/locar/agenda", headers=cab(papel="admin")).status_code == 403
    assert c.get("/api/locar/agenda").status_code == 403


def test_diretor_ve_so_as_entidades_do_acesso_e_a_sensivel_some(amb):
    c, _ = amb
    r = c.get("/api/locar/agenda", headers=cab(papel="diretor", uid="u-dir")).json()
    assert {e["id"] for e in r["entidades"]} == {"e1"}  # e2 não está no acesso; pf é sensível e ele não é titular
    assert {i["id"] for i in r["itens"]} == {"ia1", "ia3"}  # o item da entidade e2 e o do produtor não aparecem; o do grupo aparece


def test_titular_ve_a_propria_entidade_sensivel_e_nao_ve_os_titulares(amb):
    c, _ = amb
    r = c.get("/api/locar/agenda", headers=cab(papel="leitura", uid="u-tit")).json()
    assert {e["id"] for e in r["entidades"]} == {"pf"}
    assert all("titulares" not in e for e in r["entidades"])
    equipe = c.get("/api/locar/entidades", headers=cab()).json()
    assert next(e for e in equipe if e["id"] == "pf")["titulares"] == ["u-tit"]


def test_usuario_sem_acesso_cadastrado_ve_so_o_que_e_do_grupo(amb):
    c, _ = amb
    r = c.get("/api/locar/agenda", headers=cab(papel="leitura", uid="u-novo")).json()
    assert r["entidades"] == [] and [i["id"] for i in r["itens"]] == ["ia3"]


@pytest.mark.parametrize("papel", ["diretor", "leitura"])
def test_so_a_equipe_escreve(amb, papel):
    c, _ = amb
    h = cab(papel=papel, uid="u-dir")
    assert c.post("/api/locar/itens", headers=h, json={"tipo": "obrigacao", "titulo": "x"}).status_code == 403
    assert c.patch("/api/locar/itens/ia1", headers=h, json={"status": "entregue"}).status_code == 403
    assert c.patch("/api/locar/entidades/e1", headers=h, json={"status": "extinta"}).status_code == 403
    assert c.get("/api/locar/auditoria", headers=h).status_code == 403
    assert c.get("/api/locar/auditoria/verificar", headers=h).status_code == 403


def test_criar_item_valida_a_entidade_o_id_e_a_evidencia(amb):
    c, _ = amb
    base = {"tipo": "obrigacao", "titulo": "Novo item"}
    assert c.post("/api/locar/itens", headers=cab(), json={**base, "entidade_id": "inexistente"}).status_code == 422
    assert c.post("/api/locar/itens", headers=cab(), json={**base, "entidade_id": "eb"}).status_code == 422  # entidade de outro grupo
    assert c.post("/api/locar/itens", headers=cab(), json={**base, "id": "ia1"}).status_code == 422  # id repetido
    assert c.post("/api/locar/itens", headers=cab(), json={**base, "evidencia_ref": "javascript:alert(1)"}).status_code == 422
    assert c.post("/api/locar/itens", headers=cab(), json={**base, "campo_estranho": 1}).status_code == 422
    ok = c.post("/api/locar/itens", headers=cab(), json={**base, "entidade_id": "e1", "prazo": "2026-12-31", "evidencia_ref": "https://exemplo.com/doc"})
    assert ok.status_code == 201 and ok.json()["id"].startswith("i-") and "grupo_id" not in ok.json()


def test_atualizar_item_registra_quem_e_audita(amb):
    c, repo = amb
    r = c.patch("/api/locar/itens/ia1", headers=cab(uid="u-ana"), json={"status": "entregue", "evidencia_ref": "Protocolo 123"})
    assert r.status_code == 200 and r.json()["status"] == "entregue" and r.json()["atualizado_por"] == "u-ana"
    assert c.patch("/api/locar/itens/ia1", headers=cab(), json={}).status_code == 422  # nada para atualizar
    assert c.patch("/api/locar/itens/ia1", headers=cab(), json={"status": "inventado"}).status_code == 422
    assert c.patch("/api/locar/itens/nao-existe", headers=cab(), json={"status": "entregue"}).status_code == 404
    elos = c.get("/api/locar/auditoria", headers=cab()).json()
    assert elos[0]["acao"] == "item.atualizar" and elos[0]["recurso_id"] == "ia1" and elos[0]["usuario_id"] == "u-ana"
    assert c.get("/api/locar/auditoria/verificar", headers=cab()).json() == {"integra": True, "elos": 1}


def test_atualizar_entidade_exige_sucessora_do_grupo(amb):
    c, _ = amb
    assert c.patch("/api/locar/entidades/e1", headers=cab(), json={"status": "em_incorporacao", "sucessora_id": "e1"}).status_code == 422
    assert c.patch("/api/locar/entidades/e1", headers=cab(), json={"status": "em_incorporacao", "sucessora_id": "eb"}).status_code == 422
    r = c.patch("/api/locar/entidades/e1", headers=cab(), json={"status": "em_incorporacao", "sucessora_id": "e2"})
    assert r.status_code == 200 and r.json()["sucessora_id"] == "e2"
    assert c.patch("/api/locar/entidades/e1", headers=cab(), json={"nome": "Outro nome"}).status_code == 422  # o nome não muda por aqui


def test_leitura_de_entidade_sensivel_entra_na_trilha(amb):
    c, _ = amb
    c.get("/api/locar/agenda", headers=cab(papel="leitura", uid="u-tit"))
    c.get("/api/locar/agenda", headers=cab(papel="diretor", uid="u-dir"))  # não vê a sensível: não gera registro
    elos = c.get("/api/locar/auditoria", headers=cab()).json()
    assert [(e["acao"], e["usuario_id"], e["recurso_id"]) for e in elos] == [("leitura.sensivel", "u-tit", "pf")]


def test_trilha_adulterada_e_detectada(amb):
    c, repo = amb
    c.patch("/api/locar/itens/ia1", headers=cab(), json={"status": "entregue"})
    c.patch("/api/locar/itens/ia2", headers=cab(), json={"status": "entregue"})
    elo = repo.obter(GA, "auditoria", "0000000001")
    repo._gravar(GA, "auditoria", "0000000001", {**elo, "recurso_id": "outro"})
    assert c.get("/api/locar/auditoria/verificar", headers=cab()).json()["integra"] is False


def test_limite_por_usuario(amb):
    c, _ = amb
    c.app.state.locar.limitador_usuario = api.Limitador(maximo=3)
    assert [c.get("/api/locar/contexto", headers=cab()).status_code for _ in range(4)] == [200, 200, 200, 429]


def test_contexto_mostra_papel_e_nome_do_grupo_sem_chave(amb):
    c, _ = amb
    r = c.get("/api/locar/contexto", headers=cab(papel="diretor", uid="u-dir")).json()
    assert r["papel"] == "diretor" and r["grupo"] == {"id": GA, "nome": "Grupo A"} and r["ambiente"] == "desenvolvimento"
    assert "chave_web" not in r


def test_filtros_de_itens(amb):
    c, _ = amb
    assert [i["id"] for i in c.get("/api/locar/itens?entidade_id=e1", headers=cab()).json()] == ["ia1"]
    c.patch("/api/locar/itens/ia2", headers=cab(), json={"status": "entregue"})
    assert [i["id"] for i in c.get("/api/locar/itens?status=entregue", headers=cab()).json()] == ["ia2"]
    assert c.get("/api/locar/auditoria?limite=0", headers=cab()).status_code == 422


def test_demo_carrega_o_grupo_ficticio_so_fora_de_producao():
    s = api.criar_servicos({"ORGATEC_LOCAR": "1", "ORGATEC_LOCAR_DEMO": "1"})
    from backend.locar.demo import GRUPO_DEMO

    assert s.repo.existe_grupo(GRUPO_DEMO) and len(s.repo.listar(GRUPO_DEMO, "entidades")) == 4
    producao = api.criar_servicos({"ORGATEC_LOCAR": "1", "ORGATEC_LOCAR_DEMO": "1", "ORGATEC_PRODUCAO": "1", "ORGATEC_LOCAR_AUTH": "firebase",
                                   "ORGATEC_FIREBASE_PROJETO": "p"})
    assert not producao.repo.existe_grupo(GRUPO_DEMO)
