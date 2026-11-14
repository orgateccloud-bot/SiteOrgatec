"""Página "Como os sistemas são construídos": o mapa vai a público só no nível de módulo."""

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PAGINA = RAIZ / "site" / "solucoes" / "plataforma.html"
DADOS = RAIZ / "tools" / "plataforma_grafo.json"


def test_dados_so_tem_campos_publicos():
    dados = json.loads(DADOS.read_text(encoding="utf-8"))
    for s in dados["sistemas"].values():
        assert set(s) == {"nome", "pagina", "modulos", "ligacoes"}
        for m in s["modulos"]:
            assert set(m) == {"id", "nome", "camada", "texto", "arquivos", "simbolos"}
        ids = {m["id"] for m in s["modulos"]}
        for e in s["ligacoes"]:
            assert set(e) == {"de", "para", "total", "lidas"}
            assert e["de"] in ids and e["para"] in ids and 0 <= e["lidas"] <= e["total"]


def test_pagina_sem_nome_de_arquivo_nem_caminho_de_codigo():
    html = PAGINA.read_text(encoding="utf-8")
    assert not re.search(r"\.(py|ts|tsx|js|sql|yaml|env)\b(?![\"'])", re.sub(r'(src|href)="[^"]*"', "", html))
    for termo in ("api/", "nfa_extractor", "pdf_engine", "_legacy", "routers", "matchers"):
        assert termo not in html, termo


def test_so_sistemas_publicos_vao_a_pagina():
    """O OrgAudi é de uso interno (decisão de 13/11/2026): fica no curador, mas não no JSON nem na página."""
    import sys
    sys.path.insert(0, str(RAIZ / "tools"))
    import plataforma_curar
    publicos = {k for k, cfg in plataforma_curar.SISTEMAS.items() if cfg["publico"]}
    dados = json.loads(DADOS.read_text(encoding="utf-8"))
    assert set(dados["sistemas"]) == publicos
    assert "orgaudi" not in publicos
    html = PAGINA.read_text(encoding="utf-8")
    for chave in set(plataforma_curar.SISTEMAS) - publicos:
        assert f"mapa-{chave}" not in html and f'data-mapa-plataforma="{chave}"' not in html, chave
    for texto in ("Leitura de NFA-e", "Motor do laudo PDF", "Banco e integração com IA", "auditoria forense rural)"):
        assert texto not in html, texto


def test_pagina_sem_script_externo():
    html = PAGINA.read_text(encoding="utf-8")
    assert not re.search(r'<script[^>]+src="https?://', html)


def test_pagina_no_menu_de_solucoes():
    import sys
    sys.path.insert(0, str(RAIZ / "tools"))
    import layout
    assert ("Como os sistemas são construídos", "solucoes/plataforma.html") in layout.SOLUCOES
