"""Comparação da sombra do boletim com o que está no ar (tools/comparar_sombra.py), sem rede: os boletins são montados no teste."""

import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import comparar_sombra as C  # noqa: E402

REGIOES = ["co", "norte", "sul"]


def atual(gerado="2026-11-08T11:00-03:00", estado="atencao"):
    return {"id": "2026-11-08", "dia": "2026-11-08", "geradoEm": gerado, "semDados": [],
            "polos": [{"id": "rio-verde"}, {"id": "palmas"}],
            "regioes": [{"id": r, "ops": {op: [estado, "Com restrição · janela comum 05h às 09h", "orientação"] for op in C.OPERACOES}} for r in REGIOES]}


def lado(a=None, noticias=None, historico=None):
    return {"atual": a if a is not None else atual(), "noticias": noticias if noticias is not None else {"geradoEm": "x", "atividades": {"soja": [{"titulo": "t"}], "milho": []}, "tributacao": []},
            "historico": historico if historico is not None else {"itens": [{}] * 40}}


def test_mesmo_formato_nao_falha_e_conta_as_diferencas_de_estado():
    res = C.comparar(lado(atual("2026-11-08T11:07-03:00", "ok")), lado())
    assert res["falhas"] == []
    assert res["info"]["estados_diferentes"].startswith("15 de 15")
    assert "7 min" in res["info"]["geradoEm"]
    assert res["info"]["notícias com tema atendido"] == "1 de 2"
    assert C.texto(res).startswith("### Sombra do boletim: mesmo formato")


def test_sombra_sem_boletim_falha_de_cara():
    res = C.comparar({"atual": {}}, lado())
    assert res["falhas"] and "atual.json" in res["falhas"][0]


def test_formato_diferente_falha():
    sombra = atual(); sombra["extra"] = 1; sombra["polos"] = sombra["polos"][:1]
    falhas = C.comparar(lado(sombra), lado())["falhas"]
    assert any("chaves do boletim" in f and "extra" in f for f in falhas)
    assert any("polos da sombra" in f for f in falhas)
    sombra2 = atual(); sombra2["regioes"] = sombra2["regioes"][:2]
    assert any("regiões da sombra" in f for f in C.comparar(lado(sombra2), lado())["falhas"])


def test_operacao_invalida_resumo_longo_e_codigo_antigo_falham():
    s = atual(); s["regioes"][0]["ops"]["pulv"] = ["talvez", "x"]; s["regioes"][1]["ops"]["plantio"] = ["ok", "x" * 91]
    falhas = C.comparar(lado(s), lado())["falhas"]
    assert any("co" in f and "pulv" in f for f in falhas) and any("norte" in f and "91 caracteres" in f for f in falhas)
    velho = atual(); del velho["semDados"]
    antigo = atual(); del antigo["semDados"]
    assert any("semDados" in f for f in C.comparar(lado(velho), lado(antigo))["falhas"])


def test_texto_de_sem_previsao_longo_demais_nao_conta_como_erro():
    s = atual(); s["regioes"][0]["ops"]["pulv"] = ["atencao", "Sem previsão para as horas úteis de hoje (05h às 20h).", "x"]
    assert C.comparar(lado(s), lado())["falhas"] == []


def test_noticias_ausentes_ou_com_chaves_diferentes_falham():
    sombra = lado(); sombra["noticias"] = {}
    assert any("noticias.json" in f for f in C.comparar(sombra, lado())["falhas"])
    outra = lado(noticias={"geradoEm": "x", "atividades": {}})
    assert any("chaves do noticias.json" in f for f in C.comparar(outra, lado())["falhas"])


def test_avisos_horas_longe_e_historico_pequeno_nao_falham():
    res = C.comparar(lado(atual("2026-11-08T14:00-03:00"), historico={"itens": [{}] * 10}), lado())
    assert res["falhas"] == [] and any("180 min" in a for a in res["avisos"]) and any("histórico" in a for a in res["avisos"])


def test_sem_boletim_no_ar_so_confere_a_validade_da_sombra():
    res = C.comparar(lado(), {"atual": {}, "noticias": {}, "historico": {}})
    assert res["falhas"] == [] and any("não foi possível ler o boletim no ar" in a for a in res["avisos"])


def test_main_le_a_pasta_local_e_o_site(monkeypatch, tmp_path, capsys):
    (tmp_path / "campo").mkdir(); (tmp_path / "agro").mkdir()
    (tmp_path / "campo" / "atual.json").write_text(json.dumps(atual()), encoding="utf-8")
    (tmp_path / "agro" / "noticias.json").write_text(json.dumps(lado()["noticias"]), encoding="utf-8")
    monkeypatch.setattr(C, "_baixar", lambda base: lado())
    assert C.main(["--dados", str(tmp_path)]) == 0
    assert "mesmo formato" in capsys.readouterr().out
    quebrado = atual(); quebrado["polos"] = []
    (tmp_path / "campo" / "atual.json").write_text(json.dumps(quebrado), encoding="utf-8")
    assert C.main(["--dados", str(tmp_path)]) == 1


def test_so_aceita_https_e_escreve_o_resumo_do_github(monkeypatch, tmp_path, capsys):
    assert C.main(["--ao-vivo", "http://exemplo.test"]) == 1 and "https" in capsys.readouterr().err
    resumo = tmp_path / "r.md"; monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumo))
    monkeypatch.setattr(C, "_baixar", lambda base: lado()); monkeypatch.setattr(C, "_ler", lambda base: lado())
    assert C.main([]) == 0 and "Sombra do boletim" in resumo.read_text(encoding="utf-8")
