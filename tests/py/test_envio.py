"""Envio da confirmação do opt-in (backend/envio.py, pendência T2)."""
import importlib
import logging

import pytest
from fastapi.testclient import TestClient

from backend import envio

CONSENT = {"aceito": True, "versao_politica": "2026-11", "finalidade": "teste automatizado"}
OPTIN = {"email": "pessoa@exemplo.com.br", "ufs": ["GO", "TO"], "esferas": ["federal", "estadual"], "consentimento": CONSENT}


class Memoria:
    nome = "memoria"

    def __init__(self, falhar=False):
        self.enviadas, self.falhar = [], falhar

    def enviar(self, msg):
        if self.falhar:
            raise ConnectionError("smtp fora do ar")
        self.enviadas.append(msg)


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGATEC_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("ORGATEC_SEGREDO_IP", "segredo-de-teste")
    monkeypatch.setenv("ORGATEC_SERVIR_SITE", "0")
    monkeypatch.delenv("ORGATEC_EMAIL", raising=False)
    import backend.app as mod
    mod = importlib.reload(mod)
    return TestClient(mod.app), mod


def test_mensagem_traz_os_dois_links_e_o_descadastro_de_um_clique():
    m = envio.confirmacao_optin("p@ex.com", "tok-conf_123", "tok-sair_456", ["GO"], ["federal"], 30, base="https://orgatec.io")
    assert "https://orgatec.io/api/optin/confirmar?token=tok-conf_123" in m.texto
    assert "https://orgatec.io/api/optin/sair?token=tok-sair_456" in m.texto
    assert m.descadastro == "https://orgatec.io/api/optin/sair?token=tok-sair_456"
    assert "30 dias" in m.texto and "GO" in m.texto
    e = envio.EnviadorSMTP("h", 587, "u", "s", "contato@orgatec.io").montar(m)
    assert e["List-Unsubscribe"] == "<https://orgatec.io/api/optin/sair?token=tok-sair_456>"
    assert e["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert e["From"] == "ORGATEC <contato@orgatec.io>" and e["To"] == "p@ex.com"


def test_descadastro_precisa_ser_https():
    with pytest.raises(ValueError):
        envio.confirmacao_optin("p@ex.com", "a" * 10, "b" * 10, ["GO"], ["federal"], 30, base="http://orgatec.io")


def test_padrao_e_desligado(monkeypatch):
    monkeypatch.delenv("ORGATEC_EMAIL", raising=False)
    assert isinstance(envio.enviador_do_ambiente(), envio.EnviadorDesligado)


def test_smtp_sem_credencial_nao_sobe(monkeypatch):
    monkeypatch.setenv("ORGATEC_EMAIL", "smtp")
    monkeypatch.delenv("ORGATEC_SMTP_SENHA", raising=False)
    monkeypatch.setenv("ORGATEC_SMTP_USUARIO", "contato@orgatec.io")
    with pytest.raises(RuntimeError, match="ORGATEC_SMTP_SENHA"):
        envio.enviador_do_ambiente()
    monkeypatch.setenv("ORGATEC_EMAIL", "outro")
    with pytest.raises(RuntimeError, match="inválido"):
        envio.enviador_do_ambiente()


def test_smtp_usa_starttls_antes_do_login(monkeypatch):
    passos = []

    class SMTPFalso:
        def __init__(self, host, porta, timeout):
            passos.append(("conecta", host, porta))

        def __enter__(self):
            return self

        def __exit__(self, *a):
            passos.append(("fecha",))

        def starttls(self, context):
            passos.append(("starttls",))

        def login(self, u, s):
            passos.append(("login", u))

        def send_message(self, m):
            passos.append(("envia", m["To"]))

    monkeypatch.setattr(envio.smtplib, "SMTP", SMTPFalso)
    monkeypatch.setenv("ORGATEC_EMAIL", "smtp")
    monkeypatch.setenv("ORGATEC_SMTP_USUARIO", "contato@orgatec.io")
    monkeypatch.setenv("ORGATEC_SMTP_SENHA", "senha-de-app-falsa")
    e = envio.enviador_do_ambiente(producao=True)
    e.enviar(envio.confirmacao_optin("p@ex.com", "a" * 10, "b" * 10, ["GO"], ["federal"], 30))
    assert [p[0] for p in passos] == ["conecta", "starttls", "login", "envia", "fecha"]
    assert passos[0][1:] == ("smtp.gmail.com", 587)


def test_optin_envia_a_confirmacao_e_a_resposta_nao_traz_token(api):
    c, mod = api
    mod.enviador = Memoria()
    r = c.post("/api/optin", json=OPTIN)
    assert r.status_code == 201 and "token" not in r.json()
    (m,) = mod.enviador.enviadas
    assert m.para == "pessoa@exemplo.com.br"
    token = m.texto.split("confirmar?token=")[1].split()[0]
    assert c.post("/api/optin/confirmar", params={"token": token}).status_code == 200  # o link da mensagem confirma


def test_falha_no_envio_nao_derruba_o_cadastro_nem_vaza_o_email(api, caplog):
    c, mod = api
    mod.enviador = Memoria(falhar=True)
    with caplog.at_level(logging.ERROR, logger="orgatec.api"):
        r = c.post("/api/optin", json=OPTIN)
    assert r.status_code == 201
    assert "ConnectionError" in caplog.text and "pessoa@exemplo" not in caplog.text


def test_optin_so_com_whatsapp_nao_tenta_email(api):
    c, mod = api
    mod.enviador = Memoria()
    r = c.post("/api/optin", json={**OPTIN, "email": None, "whatsapp": "62999990000"})
    assert r.status_code == 201 and mod.enviador.enviadas == []
