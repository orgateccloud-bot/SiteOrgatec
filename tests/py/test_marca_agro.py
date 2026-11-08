"""Interruptor da marca Orgatec Audi Agro nos cards de cotações e notícias (tools/agro_fontes.json, marca.exibir).
Decisão de 07/11/2026: a marca sai das páginas por enquanto; a realocação fica para depois. Ligar o interruptor devolve tudo."""

import copy
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import gerar_paginas as P  # noqa: E402

CFG = json.loads((RAIZ / "tools" / "agro_fontes.json").read_text(encoding="utf-8"))


def com_marca(exibir: bool) -> dict:
    cfg = copy.deepcopy(CFG)
    cfg["marca"]["exibir"] = exibir
    return cfg


def test_marca_desligada_por_padrao():
    assert CFG["marca"]["exibir"] is False
    assert CFG["marca"]["logo"] == "assets/marca/orgatec-audi-agro.png"
    assert (RAIZ / "site" / CFG["marca"]["logo"]).exists()  # o arquivo continua no site, pronto para a realocação


def test_secao_sem_a_marca_usa_as_cores_do_site():
    html = P.secao_agro(com_marca(False))
    assert "audi-agro-selo" not in html and "orgatec-audi-agro.png" not in html
    assert "Orgatec Audi Agro" not in html
    assert '<p class="eyebrow">Mercado</p>' in html
    assert 'class="audi-agro audi-agro-neutro ' in html
    assert html.count("data-agro-atividade=") == len(CFG["atividades"])  # os cards e os avisos continuam
    assert "Tributação rural" in html


def test_secao_com_a_marca_ligada_volta_o_selo_o_nome_e_as_cores():
    html = P.secao_agro(com_marca(True))
    assert 'class="audi-agro-selo"' in html and "{p}assets/marca/orgatec-audi-agro.png" in html
    assert 'alt="Orgatec Audi Agro"' in html and '<p class="eyebrow">Orgatec Audi Agro</p>' in html
    assert "audi-agro-neutro" not in html


def test_cores_do_widget_do_cepea_seguem_o_interruptor(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "SITE", tmp_path)
    ativ = next(a for a in CFG["atividades"] if a["cepea"])
    P.widgets_cepea(com_marca(False))
    neutro = (tmp_path / "cotacoes" / f"{ativ['id']}.html").read_text(encoding="utf-8")
    assert "corfundo=eef2f7" in neutro and "e6f2e9" not in neutro
    P.widgets_cepea(com_marca(True))
    marca = (tmp_path / "cotacoes" / f"{ativ['id']}.html").read_text(encoding="utf-8")
    assert "corfundo=e6f2e9" in marca
