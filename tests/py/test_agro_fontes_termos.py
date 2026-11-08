"""Registro do que cada fonte dos cards do agro permite (tools/agro_fontes.json: termos, acompanhe e descartadas).
Cada fonte coletada precisa de termos conferidos (página, texto e data); cada link só-link e cada fonte descartada,
de um motivo. As regras do CEPEA (D21) e da B3 (D22) e a ausência de cotação do leite não mudam sem decisão."""

import json
import re
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CFG = json.loads((RAIZ / "tools" / "agro_fontes.json").read_text(encoding="utf-8"))
DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def https(u):
    return isinstance(u, str) and u.startswith("https://")


def test_toda_fonte_coletada_tem_portal_e_termos_conferidos():
    termos = {k: v for k, v in CFG["termos"].items() if not k.startswith("_")}
    ids = [f["id"] for f in CFG["feeds"]]
    assert len(ids) == len(set(ids)) and len(ids) >= 5
    for f in CFG["feeds"]:
        assert https(f["url"]) and https(f["portal"]), f["id"]
        assert f["termos"] in termos, f"{f['id']}: termos '{f['termos']}' não registrados"
    for chave, t in termos.items():
        assert https(t["url"]) and t["rotulo"] and DATA.match(t["conferidoEm"]), chave
        assert date.fromisoformat(t["conferidoEm"]) <= date.today()
        for campo in ("permite", "uso", "cuidado"):
            assert len(t[campo]) > 20, f"{chave}.{campo}"
    assert {f["termos"] for f in CFG["feeds"]} == set(termos)  # nenhum termo órfão


def test_termos_citam_o_texto_lido_na_fonte():
    t = CFG["termos"]
    assert "desde que citada a fonte" in t["camara"]["permite"]
    assert "citação da Agência Senado e do autor" in t["senado"]["permite"] and "autor" in t["senado"]["cuidado"]
    assert "Atribuição-SemDerivações 3.0" in t["govbr"]["permite"] and t["govbr"]["licenca"] == "CC BY-ND 3.0"
    for k in ("camara", "senado", "govbr"):
        assert "nenhum texto" in t[k]["uso"] or "Só " in t[k]["uso"] or "Título" in t[k]["uso"]  # o uso é título, data e link


def test_links_oficiais_e_fontes_descartadas_trazem_o_motivo():
    assert [a["nome"] for a in CFG["acompanhe"]] == ["Ministério da Agricultura", "Conab", "Embrapa", "IBGE"]
    for a in CFG["acompanhe"]:
        assert https(a["url"]) and len(a["motivo"]) > 15 and DATA.match(a["conferidoEm"]), a["nome"]
    assert "www.conab.gov.br" not in " ".join(a["url"] for a in CFG["acompanhe"])  # certificado inválido: nunca linkar
    nomes = " | ".join(d["nome"] for d in CFG["descartadas"])
    for esperado in ("Agência Brasil", "CEPEA", "B3"):
        assert esperado in nomes, esperado
    for d in CFG["descartadas"]:
        assert len(d["motivo"]) > 15 and DATA.match(d["conferidoEm"]), d["nome"]
    ebc = next(d for d in CFG["descartadas"] if "EBC" in d["nome"])
    assert "não comerciais" in ebc["motivo"]


def test_cepea_b3_e_leite_seguem_como_estavam():
    assert CFG["cepea"]["autorizacao"] is None  # D21: sem autorização formal, só o widget oficial
    assert CFG["cepea"]["widget"].startswith("https://www.cepea.org.br/")
    assert not any("cepea" in f["url"] or "b3" in f["url"].lower() for f in CFG["feeds"])  # nenhum RSS do CEPEA, nenhuma cotação da B3
    leite = next(a for a in CFG["atividades"] if a["id"] == "leite")
    assert leite["cepea"] == [] and "não está disponível no widget" in leite["semWidget"]
    assert CFG["marca"]["exibir"] is False  # a marca continua suspensa (decisão de 07/11/2026)
