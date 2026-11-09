"""Comparação do boletim gerado no Actions com o que está no ar (tools/comparar_boletim.py)."""

import copy
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import comparar_boletim as C  # noqa: E402

BASE = {"id": "b1", "dia": "2026-11-09", "geradoEm": "2026-11-09T05:00-03:00", "resumo": "ok", "alerta": None,
        "semDados": [], "regioes": [], "proximos": {}, "tendencia": [], "criterios": [], "confianca": [], "fontes": [],
        "polos": [{"id": "sorriso"}, {"id": "rio-verde"}]}


def test_boletins_equivalentes_nao_tem_problema():
    gerado = copy.deepcopy(BASE)
    gerado["geradoEm"] = "2026-11-09T05:20-03:00"
    gerado["resumo"] = "outro texto"
    problemas, notas = C.comparar(BASE, gerado)
    assert problemas == []
    assert any("20 min" in n for n in notas) and any("resumo diferente" in n for n in notas)


def test_dia_polos_e_campos_divergentes_sao_problemas():
    gerado = copy.deepcopy(BASE)
    gerado["dia"] = "2026-11-08"
    gerado["polos"] = [{"id": "sorriso"}]
    del gerado["fontes"]
    problemas, _ = C.comparar(BASE, gerado)
    texto = " | ".join(problemas)
    assert "dia diferente" in texto and "rio-verde" in texto and "fontes" in texto


def test_mais_polos_sem_previsao_que_no_ar_e_problema():
    gerado = copy.deepcopy(BASE)
    gerado["semDados"] = [{"id": "sorriso"}]
    problemas, _ = C.comparar(BASE, gerado)
    assert any("sem previsão" in p for p in problemas)


def test_main_devolve_codigo_de_saida(tmp_path, capsys):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(BASE), encoding="utf-8")
    b.write_text(json.dumps(BASE), encoding="utf-8")
    assert C.main([str(a), str(b)]) == 0
    assert "equivalente" in capsys.readouterr().out
    ruim = copy.deepcopy(BASE)
    ruim["polos"] = []
    b.write_text(json.dumps(ruim), encoding="utf-8")
    assert C.main([str(a), str(b)]) == 1
    assert C.main([str(a)]) == 2
