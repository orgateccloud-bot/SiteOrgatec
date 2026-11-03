"""Trava de publicação e nome dos canais de prévia."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import previa as V  # noqa: E402
import publicar as P  # noqa: E402

pytestmark = pytest.mark.skipif(not shutil.which("git"), reason="git ausente")


def _git(pasta, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=pasta, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "a")
    return tmp_path


def test_main_limpa_pode_publicar(repo):
    assert P.motivo_para_nao_publicar(repo) is None


def test_outra_branch_nao_publica(repo):
    _git(repo, "checkout", "-q", "-b", "ideia/teste")
    assert "ideia/teste" in P.motivo_para_nao_publicar(repo)


@pytest.mark.parametrize("arquivo", ["a.txt", "novo.txt"])
def test_alteracao_pendente_nao_publica(repo, arquivo):
    (repo / arquivo).write_text("mudou", encoding="utf-8")
    assert "sem commit" in P.motivo_para_nao_publicar(repo)


def test_pasta_sem_git_nao_publica(tmp_path):
    assert P.motivo_para_nao_publicar(tmp_path)


def test_arquivo_ignorado_nao_bloqueia(repo):
    """Os dados do agendador ficam fora do git: gravá-los não pode travar a publicação do boletim."""
    (repo / ".gitignore").write_text("site/dados/\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "ignora")
    (repo / "site" / "dados").mkdir(parents=True)
    (repo / "site" / "dados" / "atual.json").write_text("{}", encoding="utf-8")
    assert P.motivo_para_nao_publicar(repo) is None


def test_boletim_nao_publica_com_a_pasta_travada(monkeypatch):
    import gerar_boletim_campo as G
    implantou = []
    monkeypatch.setattr(P, "motivo_para_nao_publicar", lambda: "branch errada")
    monkeypatch.setattr(P, "implantar", lambda: implantou.append(True))
    with pytest.raises(RuntimeError, match="branch errada"):
        G.publicar()
    assert not implantou


@pytest.mark.parametrize("branch, canal", [
    ("desenvolvimento", "dev"),
    ("ideia/novo-simulador", "ideia-novo-simulador"),
    ("ideia/Área do Cliente", "ideia-rea-do-cliente"),
    ("ideia/" + "x" * 80, "ideia-" + "x" * 30),
])
def test_canal_da_branch(branch, canal):
    assert V.canal_da_branch(branch) == canal
    assert len(V.canal_da_branch(branch)) <= 36


def test_copiar_dados_da_pasta_principal(tmp_path):
    principal, destino = tmp_path / "principal", tmp_path / "ideia"
    (principal / "site" / "dados" / "campo").mkdir(parents=True)
    (principal / "site" / "dados" / "campo" / "atual.json").write_text("{}", encoding="utf-8")
    V.copiar_dados(principal, destino)
    assert (destino / "site" / "dados" / "campo" / "atual.json").exists()
    V.copiar_dados(principal, principal)  # na própria pasta principal, não faz nada
