"""Itens da reforma e do compliance escritos no HTML (tools/prerenderizar_itens.js), para quem não executa JavaScript."""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node não instalado")


def test_instantaneos_em_dia():
    r = subprocess.run(["node", "tools/prerenderizar_itens.js", "--conferir"], cwd=RAIZ, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_pagina_da_reforma_traz_itens_no_html():
    html = (RAIZ / "site/reforma/index.html").read_text(encoding="utf-8")
    bloco = html.split("<!--pre-->", 1)[1].split("<!--/pre-->", 1)[0]
    assert "CBS substitui PIS e Cofins em 2027" in bloco


def test_nenhum_item_pendente_em_producao():
    """Com ambiente = producao, só item com revisão aprovada é publicável (mesma regra que o instantâneo usa)."""
    script = (
        "const K=require('./site/assets/js/conteudo.js'),F=require('./site/assets/js/fontes.js'),"
        "I=require('./site/assets/js/reforma-itens.js').concat(require('./site/assets/js/compliance-itens.js'));"
        "const r=K.publicaveis(I,F.porId,'producao');"
        "console.log(r.itens.filter(i=>i.revisao.status!=='aprovada').length)"
    )
    r = subprocess.run(["node", "-e", script], cwd=RAIZ, capture_output=True, text=True)
    assert r.stdout.strip() == "0", r.stderr
