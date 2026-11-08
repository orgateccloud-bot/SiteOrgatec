"""Vigia do boletim (tools/vigiar_boletim.py): sem rede, com o horário e o boletim montados no teste."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import vigiar_boletim as V  # noqa: E402

BRASILIA = timezone(timedelta(hours=-3))
AGORA = datetime(2026, 11, 8, 16, 0, tzinfo=BRASILIA)


def boletim(horas_atras: float) -> dict:
    return {"geradoEm": (AGORA - timedelta(hours=horas_atras)).isoformat(timespec="minutes")}


@pytest.mark.parametrize("horas,em_dia", [(0.5, True), (6, True), (12, True), (13.9, True), (14.5, False), (20, False)])
def test_limite_de_horas(horas, em_dia):
    ok, msg = V.avaliar(boletim(horas), AGORA)
    assert ok is em_dia
    assert ("em dia" in msg.lower()) is em_dia and ("limite de 14 h" in msg)


def test_mensagem_de_atraso_diz_o_que_olhar():
    ok, msg = V.avaliar(boletim(17), AGORA)
    assert not ok and "há 17 h" in msg and "campo.log" in msg and "credencial do Firebase" in msg


def test_o_maior_intervalo_normal_das_rodadas_cabe_no_limite():
    # 17h de um dia e 05h do outro: 12 h; com 1 h de atraso do agendador ainda passa
    assert V.avaliar(boletim(13), AGORA)[0] is True


@pytest.mark.parametrize("ruim", [None, [], {}, {"geradoEm": ""}, {"geradoEm": "ontem"}, {"geradoEm": "2026-11-08T10:00"}, "texto"])
def test_boletim_ilegivel_ou_sem_fuso_conta_como_alerta(ruim):
    ok, msg = V.avaliar(ruim, AGORA)
    assert not ok and msg


def test_data_no_futuro_e_alerta_mas_pequena_diferenca_de_relogio_passa():
    assert V.avaliar({"geradoEm": (AGORA + timedelta(minutes=20)).isoformat()}, AGORA)[0] is True
    ok, msg = V.avaliar({"geradoEm": (AGORA + timedelta(hours=5)).isoformat()}, AGORA)
    assert not ok and "futuro" in msg


def test_limite_pode_ser_mudado():
    assert V.avaliar(boletim(10), AGORA, limite_horas=8)[0] is False
    assert V.avaliar(boletim(10), AGORA, limite_horas=18)[0] is True


def test_main_devolve_codigo_de_saida(monkeypatch, capsys):
    monkeypatch.setattr(V, "baixar", lambda url: boletim(3))
    assert V.main([], agora=AGORA) == 0 and capsys.readouterr().out.startswith("OK: ")
    monkeypatch.setattr(V, "baixar", lambda url: boletim(30))
    assert V.main([], agora=AGORA) == 1 and capsys.readouterr().out.startswith("ALERTA: ")


def test_site_fora_do_ar_ou_json_invalido_e_alerta(monkeypatch, capsys):
    def fora(url):
        raise httpx.ConnectError("sem conexão")

    def invalido(url):
        raise ValueError("Expecting value")
    for falha in (fora, invalido):
        monkeypatch.setattr(V, "baixar", falha)
        assert V.main(["--url", "https://exemplo.test/atual.json"], agora=AGORA) == 1
        saida = capsys.readouterr().out
        assert saida.startswith("ALERTA: Não foi possível ler o boletim no ar em https://exemplo.test/atual.json")


def test_resumo_da_execucao_do_github(monkeypatch, tmp_path):
    resumo = tmp_path / "resumo.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumo))
    monkeypatch.setattr(V, "baixar", lambda url: boletim(30))
    assert V.main([], agora=AGORA) == 1
    assert "**ALERTA**" in resumo.read_text(encoding="utf-8")
