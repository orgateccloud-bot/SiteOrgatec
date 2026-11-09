"""Janela Empresarial (tools/gerar_janela_empresarial.py): regras de cada cartão e fontes sem termos conferidos."""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import gerar_janela_empresarial as J  # noqa: E402

AGORA = datetime(2026, 11, 9, 9, 0, tzinfo=timezone(timedelta(hours=-3)))


def _falso(_hoje):
    return {"perfis": {p["id"]: [{"id": "das", "data": "2026-11-20", "esfera": "federal", "titulo": "DAS", "ajustada": False, "aConfirmar": False}] for p in J.PERFIS},
            "mudou": []}


def test_fonte_externa_sem_termos_conferidos_fica_indisponivel_e_sem_dados(tmp_path):
    janela = J.gerar(AGORA, tmp_path, _falso)
    externos = [c for c in janela["cartoes"] if c["id"] in ("E2", "E3", "E5", "T2", "T3", "T5", "T6")]
    assert externos and all(c["estado"] == "indisponivel" and "dados" not in c and c["coletadoEm"] is None for c in externos)


def test_todo_cartao_traz_fonte_estado_e_validade(tmp_path):
    janela = J.gerar(AGORA, tmp_path, _falso)
    for c in janela["cartoes"]:
        assert c["fonte"] and c["estado"] in ("ok", "atrasado", "indisponivel") and c["validadeHoras"] >= 0
        assert (c["coletadoEm"] is None) == (c["estado"] == "indisponivel")
    assert json.loads((tmp_path / "atual.json").read_text(encoding="utf-8"))["geradoEm"] == janela["geradoEm"]


def test_piso_de_frete_so_entra_com_revisao_humana_completa():
    fonte = J.carregar_fontes()["T1"]
    assert J.cartao_piso(fonte, AGORA, {"pisoFrete": None})["estado"] == "indisponivel"
    assert J.cartao_piso(fonte, AGORA, {"pisoFrete": {"resolucao": "Res. X"}})["estado"] == "indisponivel"
    completo = {k: "x" for k in ("resolucao", "publicadaEm", "vigenciaEm", "url", "revisadoPor", "revisadoEm")}
    assert J.cartao_piso(fonte, AGORA, {"pisoFrete": completo})["estado"] == "ok"


def test_o_gerador_nao_publica_nada():
    texto = (RAIZ / "tools" / "gerar_janela_empresarial.py").read_text(encoding="utf-8")
    assert "publicar" not in texto.split('"""')[2]  # fora da docstring, nenhuma chamada de publicação
    assert "firebase" not in texto.lower().replace("nunca publica", "")


def test_gerar_com_o_calendario_real_traz_os_prazos_e_o_aviso(tmp_path):
    janela = J.gerar(AGORA, tmp_path)
    e1 = next(c for c in janela["cartoes"] if c["id"] == "E1")
    assert set(e1["dados"]["porPerfil"]) == {p["id"] for p in J.PERFIS}
    assert "SEFAZ" in janela["aviso"] and "ANTT" in janela["aviso"]
