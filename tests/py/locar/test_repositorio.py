"""Contrato dos repositórios do LOCAR: memória, SQLite e Firestore se comportam igual.

Firestore: firebase emulators:exec --only firestore --project demo-orgatec "python -m pytest tests/py/locar/test_repositorio.py"
Sem FIRESTORE_EMULATOR_HOST os casos do Firestore são pulados.
"""

import os
import threading
import uuid

import pytest

from backend.locar.erros import NaoEncontrado
from backend.locar.repositorio_locar import RepositorioFirestore, RepositorioMemoria, RepositorioSQLite, criar_repositorio

GA = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
GB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


@pytest.fixture(params=["memoria", "sqlite", "firestore"])
def repo(request, tmp_path):
    if request.param == "memoria":
        return RepositorioMemoria()
    if request.param == "sqlite":
        return RepositorioSQLite(tmp_path / "locar.db")
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        pytest.skip("emulador do Firestore não está rodando")
    return RepositorioFirestore(projeto="demo-orgatec", prefixo=f"t{uuid.uuid4().hex[:8]}_")


def test_isolamento_entre_grupos(repo):
    repo.criar_grupo(GA, "A")
    repo.criar_grupo(GB, "B")
    repo.inserir(GA, "entidades", "e1", {"nome": "Empresa A"})
    assert repo.obter(GA, "entidades", "e1")["nome"] == "Empresa A"
    with pytest.raises(NaoEncontrado):
        repo.obter(GB, "entidades", "e1")
    assert repo.listar(GB, "entidades") == [] and not repo.existe(GB, "entidades", "e1")
    assert repo.existe_grupo(GA) and not repo.existe_grupo("cccccccc-cccc-4ccc-8ccc-cccccccccccc")


def test_criar_grupo_repetido_nao_perde_a_data_de_criacao(repo):
    repo.criar_grupo(GA, "A")
    primeira = repo.obter_grupo(GA)["criado_em"]
    repo.criar_grupo(GA, "A renomeado")
    g = repo.obter_grupo(GA)
    assert g["criado_em"] == primeira and g["nome"] == "A renomeado"


def test_atualizar_mescla_e_nao_cria(repo):
    repo.criar_grupo(GA, "A")
    repo.inserir(GA, "itens", "i1", {"titulo": "x", "status": "a_fazer"})
    novo = repo.atualizar(GA, "itens", "i1", {"status": "entregue"})
    assert novo["titulo"] == "x" and novo["status"] == "entregue" and novo["grupo_id"] == GA
    with pytest.raises(NaoEncontrado):
        repo.atualizar(GA, "itens", "nao-existe", {"status": "x"})


def test_acesso_do_usuario_guarda_entidades_sem_repeticao(repo):
    repo.criar_grupo(GA, "A")
    repo.salvar_acesso(GA, "u1", "diretor", ["e2", "e1", "e1"])
    assert repo.obter_acesso(GA, "u1")["entidades"] == ["e1", "e2"]
    assert repo.obter_acesso(GA, "outro") is None and repo.obter_acesso(GB, "u1") is None


def test_trilha_encadeada_e_adulteracao_detectada(repo):
    repo.criar_grupo(GA, "A")
    assert repo.verificar_cadeia(GA) == (True, 0)
    for i in range(3):
        repo.anexar_auditoria(GA, "u1", "item.atualizar", "item", f"i{i}")
    assert repo.verificar_cadeia(GA) == (True, 3)
    assert [e["seq"] for e in repo.auditoria(GA, 2)] == [3, 2]  # mais novo primeiro
    elo = repo.obter(GA, "auditoria", "0000000002")
    repo._gravar(GA, "auditoria", "0000000002", {**elo, "usuario_id": "intruso"})  # adultera um elo no meio
    assert repo.verificar_cadeia(GA)[0] is False


def test_trilha_nao_guarda_o_conteudo_do_pedido(repo):
    repo.criar_grupo(GA, "A")
    elo = repo.anexar_auditoria(GA, "u1", "item.atualizar", "item", "i1")
    assert set(elo) == {"id", "grupo_id", "seq", "quando", "usuario_id", "acao", "recurso", "recurso_id", "payload_hash", "hash_ant", "audit_hash"}


def test_trilhas_de_grupos_diferentes_sao_independentes(repo):
    repo.criar_grupo(GA, "A")
    repo.criar_grupo(GB, "B")
    repo.anexar_auditoria(GA, "u1", "a", "r", "1")
    repo.anexar_auditoria(GA, "u1", "a", "r", "2")
    repo.anexar_auditoria(GB, "u2", "a", "r", "1")
    assert repo.verificar_cadeia(GA) == (True, 2) and repo.verificar_cadeia(GB) == (True, 1)


def test_escritas_simultaneas_nao_bifurcam_a_cadeia(repo):
    repo.criar_grupo(GA, "A")

    def escrever(n):
        for i in range(4):
            repo.anexar_auditoria(GA, f"u{n}", "item.atualizar", "item", f"{n}-{i}")

    fios = [threading.Thread(target=escrever, args=(n,)) for n in range(6)]
    for f in fios:
        f.start()
    for f in fios:
        f.join()
    assert repo.verificar_cadeia(GA) == (True, 24)


def test_escolha_do_banco_pela_variavel(tmp_path):
    assert isinstance(criar_repositorio({}), RepositorioMemoria)
    assert isinstance(criar_repositorio({"ORGATEC_LOCAR_BANCO": "sqlite", "ORGATEC_LOCAR_DB": str(tmp_path / "x.db")}), RepositorioSQLite)
    with pytest.raises(RuntimeError):
        criar_repositorio({"ORGATEC_LOCAR_BANCO": "excel"})
