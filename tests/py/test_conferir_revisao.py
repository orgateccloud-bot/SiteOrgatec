"""Conferência do registro da revisão técnica (tools/conferir_revisao.py)."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import conferir_revisao as cr  # noqa: E402


def _registro():
    corpo = {"versao": 1, "responsavel": "Responsável Teste", "data": "2026-11-07",
             "decisoes": [{"id": "item:x", "tipo": "Ponto", "decisao": "aprovada", "nota": "", "conteudoHash": "a" * 64}]}
    corpo["audit_hash"] = hashlib.sha256(cr.canonico(corpo).encode("utf-8")).hexdigest()
    return corpo


def test_registro_integro():
    assert cr.conferir(_registro()) == []


def test_registro_alterado_e_apontado():
    r = _registro()
    r["decisoes"][0]["decisao"] = "ajustar"
    assert any("audit_hash" in e for e in cr.conferir(r))


def test_main(tmp_path):
    arq = tmp_path / "r.json"
    arq.write_text(json.dumps(_registro(), ensure_ascii=False), encoding="utf-8")
    assert cr.main([str(arq)]) == 0
