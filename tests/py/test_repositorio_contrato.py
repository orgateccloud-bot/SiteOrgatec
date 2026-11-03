"""Contrato dos repositórios: SQLite (local, Docker) e Firestore (Cloud Run) se comportam igual.

O Firestore roda no emulador. Para incluí-lo:
    firebase emulators:exec --only firestore --project demo-orgatec "python -m pytest tests/py/test_repositorio_contrato.py"
Sem o emulador (FIRESTORE_EMULATOR_HOST ausente), os casos do Firestore são pulados com aviso.
"""

import json
import os
import sqlite3
import threading
import uuid

import pytest

from backend.repositorio import Repositorio

SEGREDO = "segredo-de-contrato"


def _sqlite(tmp_path):
    db = tmp_path / "contrato.db"
    repo = Repositorio(db, SEGREDO)

    def adulterar(protocolo):
        with sqlite3.connect(db) as c:
            c.execute("UPDATE registros SET payload = ? WHERE protocolo = ?", ('{"nome":"Outro"}', protocolo))

    def ler(protocolo):
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        return dict(con.execute("SELECT * FROM registros WHERE protocolo = ?", (protocolo,)).fetchone())

    return repo, adulterar, ler


def _firestore(_tmp_path):
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        pytest.skip("emulador do Firestore não está rodando (veja o cabeçalho deste arquivo)")
    from google.cloud import firestore

    from backend.repositorio_firestore import RepositorioFirestore

    cliente = firestore.Client(project=os.environ.get("GCLOUD_PROJECT", "demo-orgatec"))
    prefixo = f"t{uuid.uuid4().hex[:8]}_"  # coleções isoladas por teste
    repo = RepositorioFirestore(SEGREDO, cliente=cliente, prefixo=prefixo)

    def adulterar(protocolo):
        cliente.collection(f"{prefixo}registros").document(protocolo).update({"payload": '{"nome":"Outro"}'})

    def ler(protocolo):
        return cliente.collection(f"{prefixo}registros").document(protocolo).get().to_dict()

    return repo, adulterar, ler


@pytest.fixture(params=["sqlite", "firestore"])
def banco(request, tmp_path):
    return (_sqlite if request.param == "sqlite" else _firestore)(tmp_path)


PAYLOAD = {"nome": "Maria", "whatsapp": "62999990000", "consentimento": {"aceito": True}}


def test_insercao_com_protocolo_hash_e_cadeia_integra(banco):
    repo, _, ler = banco
    r1 = repo.inserir("lead", "novo", PAYLOAD, "200.1.1.1")
    r2 = repo.inserir("contato", "novo", {"nome": "João"}, "200.1.1.2")
    assert r1["protocolo"].startswith("LD-") and r2["protocolo"].startswith("CT-")
    assert len(r1["audit_hash"]) == 64 and r1["token"] is None
    assert ler(r2["protocolo"])["hash_ant"] == r1["audit_hash"]  # encadeado ao anterior
    assert repo.verificar_cadeia() is True


def test_adulteracao_retroativa_quebra_a_cadeia(banco):
    repo, adulterar, _ = banco
    r1 = repo.inserir("lead", "novo", PAYLOAD, "200.1.1.1")
    repo.inserir("lead", "novo", PAYLOAD, "200.1.1.1")
    adulterar(r1["protocolo"])
    assert repo.verificar_cadeia() is False


def test_ip_so_em_hmac_e_payload_canonico(banco):
    repo, _, ler = banco
    r = repo.inserir("lead", "novo", PAYLOAD, "200.123.45.67")
    linha = ler(r["protocolo"])
    assert "200.123.45.67" not in json.dumps(linha, default=str)
    assert len(linha["ip_hmac"]) == 16
    assert json.loads(linha["payload"]) == PAYLOAD


def test_optin_confirmado_uma_unica_vez(banco):
    repo, _, ler = banco
    r = repo.inserir("optin", "pendente_confirmacao", {"email": "a@b.com"}, "200.1.1.1", com_token=True)
    assert r["token"] and len(r["token"]) >= 24
    assert repo.confirmar_optin("token-que-nao-existe") is None
    assert repo.confirmar_optin(r["token"]) == r["protocolo"]
    assert repo.confirmar_optin(r["token"]) is None  # link já usado
    linha = ler(r["protocolo"])
    assert linha["status"] == "confirmado" and linha["token"] is None
    assert repo.verificar_cadeia() is True  # confirmar não mexe no hash


def test_contagem_por_tipo(banco):
    repo, _, _ = banco
    for t in ["lead", "lead", "contato"]:
        repo.inserir(t, "novo", {"n": t}, "200.1.1.1")
    assert repo.contar() == 3 and repo.contar("lead") == 2 and repo.contar("optin") == 0


def test_insercoes_simultaneas_nao_quebram_a_cadeia(banco):
    repo, _, _ = banco
    erros = []

    def envia(i):
        try:
            repo.inserir("lead", "novo", {"i": i}, f"200.1.1.{i}")
        except Exception as e:  # noqa: BLE001 - o teste registra qualquer falha
            erros.append(e)

    fios = [threading.Thread(target=envia, args=(i,)) for i in range(12)]
    for f in fios:
        f.start()
    for f in fios:
        f.join()
    assert not erros, erros
    assert repo.contar() == 12
    assert repo.verificar_cadeia() is True
