"""Restauração do histórico do site no ar (tools/restaurar_dados_do_site.py), sem rede: o site é simulado."""

import json
import sys
from pathlib import Path

import httpx
import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import restaurar_dados_do_site as R  # noqa: E402

BASE = "https://exemplo.test"


def _site(arquivos: dict[str, object]) -> httpx.Client:
    def tratar(req: httpx.Request) -> httpx.Response:
        caminho = req.url.path.removeprefix("/dados/")
        if caminho in arquivos:
            return httpx.Response(200, json=arquivos[caminho])
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(tratar))


INDICE = {"boletins": [{"arquivo": "boletim-2026-11-06.json"}, {"arquivo": "boletim-2026-11-05.json"}]}
SITE = {
    "campo/indice.json": INDICE,
    "campo/atual.json": {"dia": "2026-11-06"},
    "campo/boletim-2026-11-06.json": {"dia": "2026-11-06"},
    "campo/boletim-2026-11-05.json": {"dia": "2026-11-05"},
    "agro/noticias.json": {"itens": []},
}


def test_restaura_indice_boletins_atual_e_noticias(tmp_path):
    feitos = R.restaurar(BASE, tmp_path, _site(SITE))
    assert sorted(feitos) == sorted(SITE)
    assert json.loads((tmp_path / "campo" / "boletim-2026-11-05.json").read_text(encoding="utf-8")) == {"dia": "2026-11-05"}


def test_so_aceita_nome_de_boletim_no_formato_esperado():
    indice = {"boletins": [{"arquivo": "boletim-2026-11-06.json"}, {"arquivo": "../../segredo.json"},
                           {"arquivo": "boletim-x.json"}, {"arquivo": "boletim-2026-11-06.json"}, "lixo", {"arquivo": 7}]}
    assert R.nomes_do_indice(indice) == ["campo/boletim-2026-11-06.json"]


def test_nome_malicioso_no_indice_nao_sai_da_pasta(tmp_path):
    site = {**SITE, "campo/indice.json": {"boletins": [{"arquivo": "../../x.json"}]}}
    R.restaurar(BASE, tmp_path / "dados", _site(site))
    assert not (tmp_path / "x.json").exists()
    assert not list(tmp_path.rglob("x.json"))


def test_falha_quando_o_boletim_atual_nao_vem(tmp_path):
    site = {k: v for k, v in SITE.items() if k != "campo/atual.json"}
    with pytest.raises(RuntimeError, match="atual.json"):
        R.restaurar(BASE, tmp_path, _site(site))


def test_noticias_ou_boletim_antigo_ausentes_so_geram_aviso(tmp_path, capsys):
    site = {k: v for k, v in SITE.items() if k not in ("agro/noticias.json", "campo/boletim-2026-11-05.json")}
    feitos = R.restaurar(BASE, tmp_path, _site(site))
    assert "agro/noticias.json" not in feitos and "campo/boletim-2026-11-05.json" not in feitos
    assert "aviso" in capsys.readouterr().err


def test_base_precisa_ser_https(tmp_path):
    with pytest.raises(ValueError, match="https"):
        R.restaurar("http://exemplo.test", tmp_path, _site(SITE))
