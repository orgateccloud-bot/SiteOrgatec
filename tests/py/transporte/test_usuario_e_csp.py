"""Ferramenta que dá acesso a um usuário (declarações do Firebase) e a CSP que deixa só /transporte/ falar com o Google."""

import importlib.util
import json
from pathlib import Path

import httpx
import pytest

RAIZ = Path(__file__).resolve().parents[3]


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "tools" / f"{nome}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


usuario = _carregar("transporte_usuario")
firebase = _carregar("preparar_firebase")
TID = "00000000-0000-4000-8000-000000000001"


def _cliente(encontra=True, vistos=None):
    def h(req):
        corpo = json.loads(req.content)
        (vistos if vistos is not None else []).append((req.url.path, corpo))
        if req.url.path.endswith(":lookup"):
            return httpx.Response(200, json={"users": [{"localId": "uid-1"}] if encontra else {}})
        return httpx.Response(200, json={})
    return httpx.Client(transport=httpx.MockTransport(h))


def test_concede_acesso_gravando_as_duas_declaracoes():
    vistos = []
    frase = usuario.definir_acesso(_cliente(vistos=vistos), "orgatec-site", "a@b.com", TID, "gestor")
    assert "concedido" in frase
    atualizar = [c for p, c in vistos if p.endswith(":update")][0]
    assert atualizar["localId"] == "uid-1" and json.loads(atualizar["customAttributes"]) == {"transportadora_id": TID, "papel": "gestor"}


def test_revoga_acesso_limpando_as_declaracoes_e_recusa_usuario_inexistente():
    vistos = []
    assert "removido" in usuario.definir_acesso(_cliente(vistos=vistos), "p", "a@b.com", None, None)
    assert json.loads([c for p, c in vistos if p.endswith(":update")][0]["customAttributes"]) == {}
    with pytest.raises(SystemExit):
        usuario.definir_acesso(_cliente(encontra=False), "p", "x@y.com", TID, "leitura")


def test_so_transporte_fala_com_o_google_no_firebase_json():
    cfg = firebase.firebase_json(None, False, "orgatec-api", firebase.REGIAO_PADRAO)
    regras = {h["source"]: {x["key"]: x["value"] for x in h["headers"]} for h in cfg["hosting"]["headers"]}
    assert "identitytoolkit.googleapis.com" in regras["/transporte/**"]["Content-Security-Policy"]
    assert "googleapis" not in regras["**"]["Content-Security-Policy"]  # o resto do site continua só com 'self'


def test_so_transporte_fala_com_o_google_no_servidor():
    from backend import app as servidor
    assert "securetoken.googleapis.com" in servidor.CSP_TRANSPORTE and "googleapis" not in servidor.CSP
