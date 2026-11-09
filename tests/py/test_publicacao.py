"""Configuração da publicação Firebase (site) + Railway (API): tools/preparar_firebase.py."""

import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("preparar_firebase", RAIZ / "tools" / "preparar_firebase.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)


def test_endereco_da_api_normalizado_e_validado():
    assert pf.origem_api("https://Orgatec-API.up.railway.app/") == "https://orgatec-api.up.railway.app"
    assert pf.origem_api(None) is None
    for ruim in ["http://a.com", "https://a.com/api", "https://a.com?x=1", "ftp://a.com", "a.com"]:
        with pytest.raises(SystemExit):
            pf.origem_api(ruim)


def test_id_do_projeto_firebase():
    assert pf.projeto_valido("orgatec-site") == "orgatec-site"
    for ruim in ["Orgatec", "org", "orgatec_site", "-orgatec", "a" * 31]:
        with pytest.raises(SystemExit):
            pf.projeto_valido(ruim)


def test_firebase_json_homologacao_libera_so_a_api_e_bloqueia_buscadores():
    cfg = pf.firebase_json("https://orgatec-api.up.railway.app", indexar=False)
    h = cfg["hosting"]
    assert h["public"] == "site"
    cab = {c["key"]: c["value"] for c in h["headers"][0]["headers"]}
    assert "connect-src 'self' https://orgatec-api.up.railway.app" in cab["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in cab["Content-Security-Policy"]
    assert cab["X-Robots-Tag"] == "noindex, nofollow"
    assert cab["X-Frame-Options"] == "DENY"
    prod = pf.firebase_json(None, indexar=True)
    cab2 = {c["key"]: c["value"] for c in prod["hosting"]["headers"][0]["headers"]}
    assert "X-Robots-Tag" not in cab2 and cab2["Content-Security-Policy"].count("connect-src 'self';") == 1


def test_csp_igual_a_do_backend_exceto_connect_src():
    import backend.app as app
    assert pf.csp(None) == app.CSP


def test_firebase_json_versionado_esta_em_homologacao_sem_api():
    cfg = json.loads((RAIZ / "firebase.json").read_text(encoding="utf-8"))
    cab = {c["key"]: c["value"] for c in cfg["hosting"]["headers"][0]["headers"]}
    assert cab["X-Robots-Tag"] == "noindex, nofollow"
    assert "connect-src 'self';" in cab["Content-Security-Policy"]


def test_modo_cloud_run_encaminha_api_em_sao_paulo_com_regras_fechadas():
    cfg = pf.firebase_json(None, indexar=False, cloud_run="orgatec-api")
    assert cfg["hosting"]["rewrites"] == [{"source": "/api/**", "run": {"serviceId": "orgatec-api", "region": "southamerica-east1"}}]
    assert cfg["firestore"] == {"rules": "firestore.rules"}
    cab = {c["key"]: c["value"] for c in cfg["hosting"]["headers"][0]["headers"]}
    assert "connect-src 'self';" in cab["Content-Security-Policy"]  # mesma origem: nada além de 'self'
    assert "rewrites" not in pf.firebase_json(None, indexar=False)["hosting"]
    for ruim in ["Orgatec-API", "-api", "api_1", "a" * 60]:
        with pytest.raises(SystemExit):
            pf.servico_valido(ruim)


def test_regras_do_firestore_negam_acesso_pelo_navegador():
    regras = (RAIZ / "firestore.rules").read_text(encoding="utf-8")
    assert "allow read, write: if false;" in regras
    assert "allow read, write: if true" not in regras


def test_respostas_da_api_sem_cache(tmp_path, monkeypatch):
    import importlib

    from fastapi.testclient import TestClient
    monkeypatch.setenv("ORGATEC_DB", str(tmp_path / "c.db"))
    monkeypatch.setenv("ORGATEC_SERVIR_SITE", "0")
    import backend.app as app
    app = importlib.reload(app)
    assert TestClient(app.app).get("/api/saude").headers["cache-control"] == "no-store"


def test_paginas_movidas_respondem_301_direto_para_o_destino():
    cfg = pf.firebase_json(None, False, "orgatec-api", pf.REGIAO_PADRAO)
    r = {x["source"]: x for x in cfg["hosting"]["redirects"]}
    assert r["/setores/transporte.html"] == {"source": "/setores/transporte.html", "destination": "/empresarial/transporte.html", "type": 301}
    destinos = {x["destination"] for x in r.values()}
    assert not destinos & set(r), "redirecionamento em cadeia"
    assert cfg["hosting"]["rewrites"][0]["source"] == "/api/**"


def test_nenhum_link_do_site_aponta_para_pagina_antiga():
    """Nada some sem 301, mas o próprio site não deve mais apontar para os endereços antigos (Fase 2)."""
    antigos = [de.lstrip("/") for de, _ in pf.REDIRECIONAMENTOS]
    achados = []
    for f in (RAIZ / "site").rglob("*"):
        if f.suffix in (".html", ".js", ".xml", ".txt") and "dados" not in f.parts and "homologacao.js" != f.name:
            texto = f.read_text(encoding="utf-8", errors="ignore")
            achados += [(f.name, a) for a in antigos if a in texto]
    assert not achados, achados[:5]
    for de, _ in pf.REDIRECIONAMENTOS:
        assert not (RAIZ / "site" / de.lstrip("/")).exists(), f"{de} ainda existe em site/"
