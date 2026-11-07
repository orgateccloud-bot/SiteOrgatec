"""Testes da API de formulários (leads, opt-in, contato)."""

import importlib
import sqlite3

import pytest
from fastapi.testclient import TestClient

CONSENT = {"aceito": True, "versao_politica": "2026-10", "finalidade": "teste automatizado"}
SIM = {"setor": "agro", "regime": "real", "perfil": "b2b", "uf": "TO", "faturamento_anual": 5_000_000, "alertas": ["x"]}


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGATEC_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("ORGATEC_SEGREDO_IP", "segredo-de-teste")
    monkeypatch.setenv("ORGATEC_RATE_LIMIT", "5")
    monkeypatch.setenv("ORGATEC_SERVIR_SITE", "0")
    import backend.app as mod
    mod = importlib.reload(mod)
    return TestClient(mod.app), mod, tmp_path / "t.db"


def test_lead_valido_retorna_protocolo_e_hash(cliente):
    c, _, _ = cliente
    r = c.post("/api/leads", json={"nome": "Maria", "whatsapp": "(62) 99999-0000", "consentimento": CONSENT, "simulacao": SIM})
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["protocolo"].startswith("LD-") and len(j["audit_hash"]) == 64
    assert "token" not in j


@pytest.mark.parametrize("ajuste", [
    {"consentimento": {**CONSENT, "aceito": False}},  # sem consentimento
    {"whatsapp": None, "email": None},                # sem canal de retorno
    {"email": "invalido@", "whatsapp": None},
    {"whatsapp": "6233334444"},                       # fixo, não celular
    {"website": "http://spam"},                       # honeypot preenchido
    {"campo_extra": 1},                               # extra=forbid
])
def test_lead_invalido_422(cliente, ajuste):
    c, _, _ = cliente
    corpo = {"nome": "Maria", "whatsapp": "62999990000", "consentimento": CONSENT, "simulacao": SIM, **ajuste}
    assert c.post("/api/leads", json=corpo).status_code == 422


def test_lead_uf_inexistente_422(cliente):
    c, _, _ = cliente
    corpo = {"nome": "Maria", "email": "m@ex.com", "consentimento": CONSENT, "simulacao": {**SIM, "uf": "XX"}}
    assert c.post("/api/leads", json=corpo).status_code == 422


def test_optin_double_optin(cliente):
    c, mod, db = cliente
    tokens = []
    inserir = mod.repo.inserir
    mod.repo.inserir = lambda *a, **k: tokens.append(inserir(*a, **k)) or tokens[-1]
    r = c.post("/api/optin", json={"email": "a@b.com.br", "ufs": ["GO", "TO", "PA"], "esferas": ["federal", "estadual"], "consentimento": CONSENT})
    assert r.status_code == 201 and r.json()["status"] == "pendente_confirmacao"
    token = tokens[0]["token"]
    assert c.post("/api/optin/confirmar", params={"token": token}).status_code == 200
    assert c.post("/api/optin/confirmar", params={"token": token}).status_code == 404  # uso único
    assert sqlite3.connect(db).execute("SELECT status FROM registros WHERE tipo='optin'").fetchone()[0] == "confirmado"


def test_optin_sem_uf_422(cliente):
    c, _, _ = cliente
    assert c.post("/api/optin", json={"email": "a@b.com", "ufs": [], "esferas": ["federal"], "consentimento": CONSENT}).status_code == 422


def test_contato_e_ip_nao_gravado_em_claro(cliente):
    c, _, db = cliente
    r = c.post("/api/contato", json={"nome": "João", "email": "j@ex.com", "assunto": "lgpd", "mensagem": "Quero acessar meus dados.", "consentimento": CONSENT})
    assert r.status_code == 201
    linha = sqlite3.connect(db).execute("SELECT ip_hmac, payload FROM registros").fetchone()
    assert "testclient" not in linha[0] and len(linha[0]) == 16
    assert "website" not in linha[1]


def test_cadeia_de_auditoria_detecta_adulteracao(cliente):
    c, mod, db = cliente
    for i in range(3):
        c.post("/api/contato", json={"nome": f"P{i}", "email": f"p{i}@ex.com", "assunto": "outro", "mensagem": "mensagem de teste", "consentimento": CONSENT})
    assert mod.repo.verificar_cadeia() is True
    con = sqlite3.connect(db)
    con.execute("UPDATE registros SET payload = replace(payload, 'P1', 'PX') WHERE id = 2")
    con.commit()
    assert mod.repo.verificar_cadeia() is False


def test_rate_limit_429(cliente):
    c, _, _ = cliente
    corpo = {"nome": "Rate", "email": "r@ex.com", "assunto": "outro", "mensagem": "mensagem de teste", "consentimento": CONSENT}
    codigos = [c.post("/api/contato", json=corpo).status_code for _ in range(7)]
    assert codigos[:5] == [201] * 5 and 429 in codigos[5:]


def test_cabecalhos_de_seguranca_e_noindex_na_homologacao(cliente):
    c, _, _ = cliente
    r = c.get("/api/saude")
    h = r.headers
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert "default-src 'self'" in h["content-security-policy"]
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert h["x-robots-tag"] == "noindex, nofollow"  # homologação fora dos buscadores
    assert "strict-transport-security" not in h      # HSTS só com ORGATEC_PRODUCAO=1


def test_producao_exige_segredo_forte(tmp_path, monkeypatch):
    import backend.app as mod
    monkeypatch.setenv("ORGATEC_DB", str(tmp_path / "p.db"))
    monkeypatch.setenv("ORGATEC_SERVIR_SITE", "0")
    monkeypatch.setenv("ORGATEC_PRODUCAO", "1")
    monkeypatch.delenv("ORGATEC_SEGREDO_IP", raising=False)
    with pytest.raises(RuntimeError, match="obrigatório"):
        importlib.reload(mod)
    monkeypatch.setenv("ORGATEC_SEGREDO_IP", "curto")
    with pytest.raises(RuntimeError, match="32 caracteres"):
        importlib.reload(mod)
    monkeypatch.setenv("ORGATEC_SEGREDO_IP", "s" * 40)
    monkeypatch.setenv("ORGATEC_INDEXAR", "1")
    mod = importlib.reload(mod)
    h = TestClient(mod.app).get("/api/saude").headers
    assert h["strict-transport-security"].startswith("max-age=")
    assert "x-robots-tag" not in h


def test_ip_real_pelo_cabecalho_do_proxy(tmp_path, monkeypatch):
    """Na Railway o proxy informa o IP do visitante em X-Real-IP: cada visitante tem o próprio limite."""
    import backend.app as mod
    monkeypatch.setenv("ORGATEC_DB", str(tmp_path / "ip.db"))
    monkeypatch.setenv("ORGATEC_SEGREDO_IP", "segredo-de-teste")
    monkeypatch.setenv("ORGATEC_RATE_LIMIT", "2")
    monkeypatch.setenv("ORGATEC_SERVIR_SITE", "0")
    monkeypatch.setenv("ORGATEC_CABECALHO_IP", "X-Real-IP")
    mod = importlib.reload(mod)
    c = TestClient(mod.app)
    corpo = {"nome": "Ana", "email": "ana@ex.com", "assunto": "diagnostico", "mensagem": "Quero um diagnóstico tributário.", "consentimento": CONSENT}
    for _ in range(2):
        assert c.post("/api/contato", json=corpo, headers={"X-Real-IP": "200.1.1.1"}).status_code == 201
    assert c.post("/api/contato", json=corpo, headers={"X-Real-IP": "200.1.1.1"}).status_code == 429
    assert c.post("/api/contato", json=corpo, headers={"X-Real-IP": "200.2.2.2"}).status_code == 201  # outro visitante


def test_ip_por_posicao_no_x_forwarded_for(tmp_path, monkeypatch, caplog):
    """Atrás do Hosting/Cloud Run: a posição do IP real é configurável; valores fora da lista caem no IP da conexão."""
    import backend.app as mod
    monkeypatch.setenv("ORGATEC_DB", str(tmp_path / "pos.db"))
    monkeypatch.setenv("ORGATEC_SEGREDO_IP", "segredo-de-teste")
    monkeypatch.setenv("ORGATEC_RATE_LIMIT", "1")
    monkeypatch.setenv("ORGATEC_SERVIR_SITE", "0")
    monkeypatch.setenv("ORGATEC_CABECALHO_IP", "x-forwarded-for")
    monkeypatch.setenv("ORGATEC_IP_POSICAO", "-2")  # penúltimo: o que o proxy acrescentou antes do próprio IP
    monkeypatch.setenv("ORGATEC_DIAGNOSTICO_IP", "1")
    mod = importlib.reload(mod)
    c = TestClient(mod.app)
    corpo = {"nome": "Ana", "email": "ana@ex.com", "assunto": "diagnostico", "mensagem": "Quero um diagnóstico tributário.", "consentimento": CONSENT}
    # visitante forja o primeiro valor; o penúltimo (real) é o mesmo nas duas: a segunda é barrada
    assert c.post("/api/contato", json=corpo, headers={"X-Forwarded-For": "1.1.1.1, 200.9.9.9, 35.1.1.1"}).status_code == 201
    with caplog.at_level("WARNING", logger="orgatec.api"):
        assert c.post("/api/contato", json=corpo, headers={"X-Forwarded-For": "8.8.8.8, 200.9.9.9, 35.1.1.1"}).status_code == 429
    assert "200.9.9.x" in caplog.text and "200.9.9.9" not in caplog.text  # diagnóstico sem o IP inteiro
    assert mod.mascarar_ip("2804:14c::1") == "2804:14c::x" and mod.mascarar_ip("") == ""


def test_esquema_da_api_nao_fica_publico(cliente):
    c, _, _ = cliente
    for caminho in ("/docs", "/redoc", "/openapi.json"):
        assert c.get(caminho).status_code == 404, caminho
