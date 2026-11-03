"""Gerador da Janela de Campo (tools/gerar_boletim_campo.py) sem rede: a previsão vem da resposta gravada do
MET Norway em tests/fixtures/campo. Precisa do Node.js (a montagem usa site/assets/js/campo-regras.js)."""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import gerar_boletim_campo as G  # noqa: E402

MET = json.loads((RAIZ / "tests" / "fixtures" / "campo" / "met-rio-verde.json").read_text(encoding="utf-8"))
AGORA = datetime(2026, 11, 2, 11, 2, tzinfo=G.BRASILIA)
pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="Node.js ausente")


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(G.time, "sleep", lambda s: None)


def amostra(polo, cliente, agora):
    return MET


def test_gera_boletim_valido_e_grava_atual_dia_e_indice(tmp_path):
    b = G.gerar(AGORA, buscar=amostra, destino=tmp_path)
    assert b["dia"] == "2026-11-02" and b["automatico"] is True
    assert b["geradoEm"] == "2026-11-02T11:02-03:00"
    assert b["proximaAtualizacao"] == "hoje às 17h"
    assert len(b["polos"]) == len(json.loads(G.POLOS.read_text(encoding="utf-8"))["polos"])
    assert json.loads((tmp_path / "atual.json").read_text(encoding="utf-8")) == b
    assert (tmp_path / "boletim-2026-11-02.json").exists()
    indice = json.loads((tmp_path / "indice.json").read_text(encoding="utf-8"))
    assert indice["boletins"][0] == {"id": "2026-11-02", "dia": "2026-11-02", "geradoEm": b["geradoEm"], "arquivo": "boletim-2026-11-02.json"}


def test_fonte_fora_do_ar_nao_grava_nada(tmp_path):
    def falha(polo, cliente, agora):
        raise G.FonteIndisponivel(f"MET Norway sem resposta para {polo['nome']}")
    with pytest.raises(G.FonteIndisponivel):
        G.gerar(AGORA, buscar=falha, destino=tmp_path)
    assert not list(tmp_path.iterdir())  # o boletim anterior publicado continua valendo


def test_main_devolve_erro_sem_publicar(monkeypatch, tmp_path):
    publicou = []
    monkeypatch.setattr(G, "configurar_log", lambda: None)
    monkeypatch.setattr(G, "atualizar_noticias", lambda: False)  # sem rede; notícias com falha também não publicam
    monkeypatch.setattr(G, "gerar", lambda: (_ for _ in ()).throw(G.FonteIndisponivel("fora do ar")))
    monkeypatch.setattr(G, "publicar", lambda: publicou.append(True))
    monkeypatch.setattr(G, "retirar_cartao_vencido", lambda: None)  # não mexe no cartão real (tests/py/test_cartao_campo.py)
    assert G.main(["--publicar"]) == 1
    assert not publicou


def test_indice_lista_no_maximo_30_dias(tmp_path):
    for d in range(1, 36):
        dia = f"2026-10-{d:02d}" if d <= 31 else f"2026-11-{d - 31:02d}"
        (tmp_path / f"boletim-{dia}.json").write_text(json.dumps({"id": dia, "dia": dia, "geradoEm": dia + "T05:00-03:00"}), encoding="utf-8")
    G.gravar({"id": "2026-11-05", "dia": "2026-11-05", "geradoEm": "2026-11-05T05:00-03:00"}, tmp_path)
    itens = json.loads((tmp_path / "indice.json").read_text(encoding="utf-8"))["boletins"]
    assert len(itens) == 30 and itens[0]["dia"] == "2026-11-05"
    assert len(list(tmp_path.glob("boletim-*.json"))) == 36  # arquivos antigos não são apagados


def test_proxima_atualizacao():
    assert G.proxima_atualizacao(datetime(2026, 11, 2, 4, 59, tzinfo=G.BRASILIA)) == "hoje às 05h"
    assert G.proxima_atualizacao(datetime(2026, 11, 2, 11, 0, tzinfo=G.BRASILIA)) == "hoje às 17h"
    assert G.proxima_atualizacao(datetime(2026, 11, 2, 17, 30, tzinfo=G.BRASILIA)) == "amanhã às 05h"


def test_agendador_tres_tarefas_com_publicar_e_simulacao(capsys):
    cmds = G.comandos_agendador()
    assert [c[c.index("/ST") + 1] for c in cmds] == ["05:00", "11:00", "17:00"]
    assert all(c[c.index("/TR") + 1].endswith("gerar_boletim_campo.py\" --publicar") for c in cmds)
    assert all(c[c.index("/TN") + 1].startswith("ORGATEC\\JanelaCampo") for c in cmds)
    assert [c[1] for c in G.comandos_agendador(remover=True)] == ["/Delete"] * 3
    G.agendador(remover=False, simular=True)  # só imprime; não cria tarefa
    assert capsys.readouterr().out.count("schtasks /Create") == 3


def test_cache_respeita_expires_sem_ir_a_rede(monkeypatch, tmp_path):
    monkeypatch.setattr(G, "CACHE", tmp_path)
    polo = {"id": "teste", "nome": "Teste", "lat": -17.79, "lon": -50.92}
    (tmp_path / "met-teste.json").write_text(json.dumps({"expira": AGORA.timestamp() + 600, "modificado": None, "corpo": {"ok": 1}}), encoding="utf-8")

    class SemRede:
        def get(self, *a, **k):
            raise AssertionError("não devia consultar o MET dentro do Expires")
    assert G.buscar_met(polo, SemRede(), AGORA) == {"ok": 1}
