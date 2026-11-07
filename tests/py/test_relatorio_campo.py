"""Relatório da distribuição de estados da Janela de Campo (tools/relatorio_campo.py), com boletins mínimos montados à mão."""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import relatorio_campo as R  # noqa: E402


def boletim(dia, estado_pulv, horas=range(5, 21), regioes=("co", "sul")):
    por_hora = {str(h): estado_pulv for h in horas}
    ops = {op: {"estado": "ok", "motivo": None, "porHora": {str(h): "ok" for h in horas}} for op in R.OPERACOES}
    ops["pulv"] = {"estado": estado_pulv, "motivo": "vento forte (deriva)" if estado_pulv != "ok" else None, "porHora": por_hora}
    return {"id": dia, "dia": dia, "geradoEm": dia + "T17:00-03:00",
            "polos": [{"id": "a", "ops": ops}],
            "regioes": [{"id": r, "ops": {op: [ops[op]["estado"], "x"] for op in R.OPERACOES}} for r in regioes]}


def gravar(pasta, *boletins):
    for b in boletins:
        (pasta / f"boletim-{b['dia']}.json").write_text(json.dumps(b), encoding="utf-8")


def test_mede_estados_por_hora_dia_e_regiao(tmp_path):
    gravar(tmp_path, boletim("2026-11-02", "atencao"), boletim("2026-11-03", "ok"))
    rel = R.medir(R.carregar(tmp_path))
    p = rel["operacoes"]["pulv"]
    assert rel["boletins"] == 2 and p["horas_pct"] == {"ok": 50.0, "atencao": 50.0}
    assert p["regiao_dia"] == {"atencao": 2, "ok": 2} and p["dia_polo"] == {"atencao": 1, "ok": 1}
    assert p["motivos"] == [("vento forte (deriva)", 1)]
    assert not p["pouca_variacao"]


def test_aponta_operacao_que_quase_nao_varia(tmp_path):
    gravar(tmp_path, *(boletim(f"2026-11-0{d}", "atencao") for d in range(1, 6)))
    rel = R.medir(R.carregar(tmp_path))
    assert rel["operacoes"]["pulv"]["pouca_variacao"] and rel["operacoes"]["plantio"]["pouca_variacao"]
    assert "[POUCA VARIAÇÃO]" in R.texto(rel)


def test_lista_boletins_com_horas_faltando(tmp_path):
    gravar(tmp_path, boletim("2026-11-02", "ok", horas=range(10, 21)), boletim("2026-11-03", "ok"))
    rel = R.medir(R.carregar(tmp_path))
    assert rel["boletins_com_horas_faltando"] == [{"dia": "2026-11-02", "geradoEm": "2026-11-02T17:00-03:00", "polos": 1}]


def test_main_sem_boletins_devolve_erro(tmp_path, capsys):
    assert R.main(["--pasta", str(tmp_path)]) == 1
    assert "Nenhum boletim" in capsys.readouterr().err


def test_main_json(tmp_path, capsys):
    gravar(tmp_path, boletim("2026-11-02", "ok"))
    assert R.main(["--pasta", str(tmp_path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["boletins"] == 1
