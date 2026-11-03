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
from datetime import timedelta

import pytest

from backend.repositorio import Repositorio, agora_utc

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


def test_eliminar_apaga_dados_e_mantem_a_cadeia(banco):
    repo, _, ler = banco
    r1 = repo.inserir("lead", "novo", PAYLOAD, "200.1.1.1")
    r2 = repo.inserir("contato", "novo", {"nome": "João", "email": "j@ex.com"}, "200.1.1.2")
    r3 = repo.inserir("contato", "novo", {"nome": "Ana", "email": "a@ex.com"}, "200.1.1.3")
    assert repo.eliminar(r2["protocolo"], "titular") is True
    assert repo.eliminar(r2["protocolo"], "titular") is False  # só uma vez
    linha = ler(r2["protocolo"])
    assert linha["payload"] is None and linha["sal"] is None and linha["ip_hmac"] == ""
    assert linha["status"] == "eliminado" and linha["motivo_eliminacao"] == "titular" and linha["eliminado_em"]
    assert linha["audit_hash"] == r2["audit_hash"]
    assert repo.verificar_cadeia() is True
    assert ler(r3["protocolo"])["hash_ant"] == r2["audit_hash"] and r1["protocolo"] != r3["protocolo"]


def test_payload_sumido_sem_registro_de_eliminacao_e_adulteracao(banco):
    repo, adulterar, _ = banco
    r = repo.inserir("lead", "novo", PAYLOAD, "200.1.1.1")
    repo.eliminar(r["protocolo"], "retencao")
    assert repo.verificar_cadeia() is True
    r2 = repo.inserir("lead", "novo", PAYLOAD, "200.1.1.1")
    adulterar(r2["protocolo"])
    assert repo.verificar_cadeia() is False


def test_localizar_titular_por_email_ou_whatsapp(banco):
    repo, _, _ = banco
    r = repo.inserir("lead", "novo", {"nome": "Bia", "email": "bia@ex.com", "whatsapp": "62999990000"}, "200.1.1.1")
    repo.inserir("lead", "novo", {"nome": "Rui", "email": "rui@ex.com"}, "200.1.1.2")
    assert [a["protocolo"] for a in repo.localizar_titular(email=" BIA@ex.com ")] == [r["protocolo"]]
    assert [a["dados"]["nome"] for a in repo.localizar_titular(whatsapp="+55 (62) 99999-0000")] == ["Bia"]
    assert repo.localizar_titular(email="ninguem@ex.com") == []
    repo.eliminar(r["protocolo"], "titular")
    assert repo.localizar_titular(email="bia@ex.com") == []


def test_tokens_guardados_so_como_hash_e_descadastro(banco):
    repo, _, ler = banco
    r = repo.inserir("optin", "pendente_confirmacao", {"email": "a@b.com"}, "200.1.1.1", com_token=True)
    linha = ler(r["protocolo"])
    assert linha["token"] != r["token"] and linha["token_saida"] != r["token_saida"]
    assert repo.revogar_optin("token-que-nao-existe") is None
    assert repo.revogar_optin(r["token"]) is None  # o token de confirmação não cancela
    assert repo.revogar_optin(r["token_saida"]) == r["protocolo"]
    assert repo.revogar_optin(r["token_saida"]) is None
    assert ler(r["protocolo"])["status"] == "revogado" and ler(r["protocolo"])["payload"] is None
    assert repo.confirmar_optin(r["token"]) is None  # depois de cancelar, o link de confirmação não vale mais
    assert repo.verificar_cadeia() is True


def test_link_de_confirmacao_vence_e_o_prazo_vem_de_prazos(banco):
    repo, _, _ = banco
    r = repo.inserir("optin", "pendente_confirmacao", {"email": "a@b.com"}, "200.1.1.1", com_token=True)
    depois = agora_utc() + timedelta(days=repo.prazos.optin_pendente_dias + 1)
    assert repo.confirmar_optin(r["token"], agora=depois) is None
    assert repo.confirmar_optin(r["token"]) == r["protocolo"]


def test_vencidos_segue_os_prazos_por_tipo(banco):
    repo, _, _ = banco
    lead = repo.inserir("lead", "novo", PAYLOAD, "200.1.1.1")
    pendente = repo.inserir("optin", "pendente_confirmacao", {"email": "a@b.com"}, "200.1.1.1", com_token=True)
    confirmado = repo.inserir("optin", "pendente_confirmacao", {"email": "c@b.com"}, "200.1.1.1", com_token=True)
    repo.confirmar_optin(confirmado["token"])
    assert repo.vencidos() == []
    em_40_dias = agora_utc() + timedelta(days=40)
    assert [r["protocolo"] for r in repo.vencidos(em_40_dias)] == [pendente["protocolo"]]
    em_3_anos = agora_utc() + timedelta(days=1100)
    achados = {r["protocolo"] for r in repo.vencidos(em_3_anos)}
    assert achados == {lead["protocolo"], pendente["protocolo"]}  # opt-in confirmado não tem prazo
    repo.eliminar(lead["protocolo"], "retencao")
    assert lead["protocolo"] not in {r["protocolo"] for r in repo.vencidos(em_3_anos)}
