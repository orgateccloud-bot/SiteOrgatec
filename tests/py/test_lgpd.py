"""Direitos do titular na API e em tools/lgpd.py: descadastro, retenção, localização, exportação e eliminação."""

import importlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parents[2]
CONSENT = {"aceito": True, "versao_politica": "2026-10", "finalidade": "teste automatizado"}
OPTIN = {"email": "ana@ex.com", "ufs": ["GO"], "esferas": ["federal"], "consentimento": CONSENT}
CONTATO = {"nome": "Ana", "email": "ana@ex.com", "assunto": "outro", "mensagem": "mensagem de teste", "consentimento": CONSENT}


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("ORGATEC_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("ORGATEC_SEGREDO_IP", "segredo-de-teste")
    monkeypatch.setenv("ORGATEC_RATE_LIMIT", "50")
    monkeypatch.setenv("ORGATEC_SERVIR_SITE", "0")
    import backend.app as mod
    mod = importlib.reload(mod)
    tokens = []
    inserir = mod.repo.inserir

    def guardar(*a, **k):  # em produção os tokens só saem no link enviado ao titular (T2)
        r = inserir(*a, **k)
        tokens.append(r)
        return r

    monkeypatch.setattr(mod.repo, "inserir", guardar)
    return TestClient(mod.app), mod, tokens, tmp_path / "t.db"


def test_recibo_nunca_traz_os_tokens_e_o_banco_nao_guarda_em_claro(api):
    c, _, tokens, db = api
    r = c.post("/api/optin", json=OPTIN).json()
    assert "token" not in r and "token_saida" not in r
    linha = sqlite3.connect(db).execute("SELECT token, token_saida FROM registros").fetchone()
    assert tokens[0]["token"] not in linha and tokens[0]["token_saida"] not in linha


def test_get_do_link_nao_confirma_nem_cancela(api):
    """Robôs de e-mail abrem os links: só o clique no botão (POST) vale."""
    c, mod, tokens, _ = api
    c.post("/api/optin", json=OPTIN)
    t = tokens[0]
    for rota, valor in (("confirmar", t["token"]), ("sair", t["token_saida"])):
        r = c.get(f"/api/optin/{rota}", params={"token": valor})
        assert r.status_code == 200 and f'action="/api/optin/{rota}?token={valor}"' in r.text
        assert r.headers["referrer-policy"] == "no-referrer"
    assert mod.repo.localizar_titular("ana@ex.com")[0]["status"] == "pendente_confirmacao"


def test_link_com_token_malformado_nao_vira_html(api):
    c, _, _, _ = api
    assert c.get("/api/optin/sair", params={"token": '"><script>alert(1)</script>'}).status_code == 404


def test_descadastro_apaga_os_dados_e_a_trilha_continua_integra(api):
    c, mod, tokens, db = api
    c.post("/api/contato", json=CONTATO)
    c.post("/api/optin", json=OPTIN)
    c.post("/api/contato", json=CONTATO)
    assert c.post("/api/optin/confirmar", params={"token": tokens[1]["token"]}).status_code == 200
    r = c.post("/api/optin/sair", params={"token": tokens[1]["token_saida"]})
    assert r.status_code == 200 and "apagado" in r.text
    assert c.post("/api/optin/sair", params={"token": tokens[1]["token_saida"]}).status_code == 404  # uso único
    linha = sqlite3.connect(db).execute(
        "SELECT status, payload, sal, contatos, ip_hmac, motivo_eliminacao FROM registros WHERE tipo='optin'").fetchone()
    assert linha == ("revogado", None, None, "[]", "", "revogacao")
    assert mod.repo.verificar_cadeia() is True
    assert len(mod.repo.localizar_titular("ana@ex.com")) == 2  # os contatos seguem; só o opt-in saiu


def test_corpo_grande_recebe_413_com_cabecalhos_de_seguranca(api):
    c, mod, _, _ = api
    r = c.post("/api/contato", content=b"x" * 20_000, headers={"Content-Type": "application/json"})
    assert r.status_code == 413 and r.headers["cache-control"] == "no-store"
    assert "default-src" in r.headers["content-security-policy"]
    assert mod.repo.contar() == 0


def test_alerta_longo_e_recusado(api):
    c, _, _, _ = api
    sim = {"setor": "agro", "regime": "real", "perfil": "b2b", "uf": "TO", "alertas": ["x" * 81]}
    corpo = {"nome": "Ana", "email": "a@ex.com", "consentimento": CONSENT, "simulacao": sim}
    assert c.post("/api/leads", json=corpo).status_code == 422


def test_saude_nao_le_o_banco(api, monkeypatch):
    c, mod, _, _ = api
    monkeypatch.setattr(mod.repo, "verificar_cadeia", lambda: pytest.fail("/api/saude varreu o banco"))
    assert c.get("/api/saude").json() == {"ok": True}


def test_memoria_do_limite_por_ip_tem_teto(api, monkeypatch):
    c, mod, _, _ = api
    monkeypatch.setattr(mod, "_MAX_IPS", 3)
    mod._hits.clear()
    for i in range(3):
        mod._hits[f"10.0.0.{i}"].append(-10_000.0)  # já passaram da janela
    assert c.get("/api/optin/confirmar", params={"token": "x" * 32}).status_code == 200
    assert len(mod._hits) == 1


def test_banco_local_antigo_fica_guardado_de_lado(tmp_path):
    from backend.repositorio import Repositorio

    db = tmp_path / "velho.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE registros (id INTEGER PRIMARY KEY, protocolo TEXT, payload TEXT)")
    con.execute("INSERT INTO registros (protocolo, payload) VALUES ('LD-1', '{}')")
    con.commit()
    con.close()
    repo = Repositorio(db, "s")
    assert repo.contar() == 0
    assert sqlite3.connect(db).execute("SELECT protocolo FROM registros_antes_lgpd").fetchone() == ("LD-1",)


# ---------- tools/lgpd.py

def _lgpd(db, *args):
    env = {**os.environ, "ORGATEC_DB": str(db), "ORGATEC_SEGREDO_IP": "segredo-da-ferramenta", "ORGATEC_SERVIR_SITE": "0",
           "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, str(RAIZ / "tools" / "lgpd.py"), *args], capture_output=True, text=True,
                          encoding="utf-8", env=env, cwd=RAIZ, check=False)


@pytest.fixture()
def banco(tmp_path):
    from backend.repositorio import Repositorio

    db = tmp_path / "f.db"
    repo = Repositorio(db, "segredo-da-ferramenta")
    novo = repo.inserir("contato", "novo", {"nome": "Bia", "email": "bia@ex.com", "whatsapp": "62999990000"}, "200.1.1.1")["protocolo"]
    velho = repo.inserir("lead", "novo", {"nome": "Rui", "email": "rui@ex.com"}, "200.1.1.2")["protocolo"]
    con = sqlite3.connect(db)
    # Envelhece um registro: criado_em entra no hash, então estes casos conferem a eliminação, não a trilha.
    con.execute("UPDATE registros SET criado_em='2020-01-01T00:00:00+00:00' WHERE protocolo=?", (velho,))
    con.commit()
    con.close()
    return db, novo, velho


def test_retencao_so_elimina_com_confirmar(banco):
    db, novo, velho = banco
    r = _lgpd(db, "retencao")
    assert r.returncode == 0 and velho in r.stdout and novo not in r.stdout and "Nada foi apagado" in r.stdout
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM registros WHERE payload IS NULL").fetchone()[0] == 0
    r = _lgpd(db, "retencao", "--confirmar")
    assert "1 eliminado(s)" in r.stdout
    linha = sqlite3.connect(db).execute("SELECT payload, motivo_eliminacao FROM registros WHERE protocolo=?", (velho,)).fetchone()
    assert linha == (None, "retencao")


def test_titular_localiza_exporta_e_elimina(banco, tmp_path):
    db, novo, _ = banco
    r = _lgpd(db, "titular", "--whatsapp", "+55 (62) 99999-0000")
    assert novo in r.stdout and "bia@ex.com" not in r.stdout  # a tela não mostra dados pessoais
    arq = tmp_path / "resposta.json"
    r = _lgpd(db, "titular", "--email", "BIA@ex.com", "--exportar", str(arq))
    assert json.loads(arq.read_text(encoding="utf-8"))[0]["dados"]["nome"] == "Bia"
    assert _lgpd(db, "titular", "--email", "bia@ex.com", "--exportar", str(arq)).returncode != 0  # não sobrescreve
    assert "Nada foi apagado" in _lgpd(db, "titular", "--email", "bia@ex.com", "--eliminar").stdout
    assert "1 eliminado(s)" in _lgpd(db, "titular", "--email", "bia@ex.com", "--eliminar", "--confirmar").stdout
    assert "0 registro(s)" in _lgpd(db, "titular", "--email", "bia@ex.com").stdout


def test_exportacao_recusa_a_pasta_publicada(banco):
    db, _, _ = banco
    r = _lgpd(db, "titular", "--email", "bia@ex.com", "--exportar", str(RAIZ / "site" / "vazou.json"))
    assert r.returncode != 0 and "site/" in r.stderr
    assert not (RAIZ / "site" / "vazou.json").exists()


def test_trilha_quebrada_sai_com_erro(tmp_path):
    from backend.repositorio import Repositorio

    db = tmp_path / "t.db"
    repo = Repositorio(db, "segredo-da-ferramenta")
    repo.inserir("contato", "novo", {"nome": "Bia", "email": "bia@ex.com"}, "200.1.1.1")
    assert _lgpd(db, "trilha").returncode == 0
    con = sqlite3.connect(db)
    con.execute("UPDATE registros SET payload='{}'")
    con.commit()
    con.close()
    r = _lgpd(db, "trilha")
    assert r.returncode == 1 and "QUEBRADA" in r.stderr


def test_imagem_do_servidor_leva_a_rotina_de_retencao():
    docker = (RAIZ / "Dockerfile").read_text(encoding="utf-8")
    ignorar = (RAIZ / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert "COPY tools/lgpd.py tools/lgpd.py" in docker
    assert ignorar.index("!tools/lgpd.py") > ignorar.index("tools")  # a exceção precisa vir depois da regra


def test_site_usa_o_nome_atual_da_anpd():
    """Lei nº 15.352/2026: a ANPD passou de Autoridade para Agência Nacional de Proteção de Dados."""
    for arq in (RAIZ / "site").rglob("*.html"):
        assert "Autoridade Nacional de Proteção" not in arq.read_text(encoding="utf-8"), arq.name
