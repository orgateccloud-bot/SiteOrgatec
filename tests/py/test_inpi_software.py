"""Pacote do registro de software no INPI (tools/inpi_software.py): reproduzível, só código próprio, fora do git."""
import hashlib
import sys
import tarfile
import io
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import inpi_software as S  # noqa: E402

REF = "HEAD"


def test_selecao_inclui_codigo_proprio_e_exclui_terceiros():
    assert S.entra("backend/app.py") and S.entra("tools/publicar.py") and S.entra("site/assets/js/app.js")
    assert S.entra("site/assets/css/orgatec.css") and S.entra("Dockerfile")
    assert not S.entra("site/assets/vendor/maplibre-gl-4.7.1/maplibre-gl-csp.js")
    assert not S.entra("site/assets/fontes/inter.woff2")
    assert not S.entra("site/assets/css/tailwind.css")
    assert not S.entra("site/inicio.html") and not S.entra("docs/inpi/mapa-registros-inpi.md")
    assert not S.entra("site/dados/campo.json")


def test_pacote_reproduzivel_e_igual_ao_manifesto():
    p1, m1 = S.montar(REF)
    p2, _ = S.montar(REF)
    assert hashlib.sha512(p1).hexdigest() == hashlib.sha512(p2).hexdigest()
    with tarfile.open(fileobj=io.BytesIO(p1)) as tar:
        nomes = [i.name for i in tar.getmembers()]
        assert all(i.uid == 0 and i.mode == 0o644 for i in tar.getmembers())
    assert nomes == [f"{S.NOME}/{m['arquivo']}" for m in m1]
    assert any(n.endswith("backend/app.py") for n in nomes)
    assert not any("vendor" in n or "/fontes/" in n for n in nomes)


def test_recusa_gravar_dentro_do_repositorio(tmp_path):
    with pytest.raises(SystemExit):
        S.gerar(REF, S.RAIZ / "dist" / "inpi")


def test_gera_pacote_hash_e_manifesto_fora_do_repositorio(tmp_path):
    r = S.gerar(REF, tmp_path)
    tar = next(tmp_path.glob("*.tar"))
    assert hashlib.sha512(tar.read_bytes()).hexdigest() == r["sha512"]
    assert r["sha512"] in next(tmp_path.glob("*.sha512")).read_text(encoding="utf-8")
    assert (tmp_path / f"{S.NOME}-{REF}.manifesto.csv").read_text(encoding="utf-8").startswith("arquivo,bytes,sha256")
