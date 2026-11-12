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


def _resposta(codigo, saida):
    return subprocess.CompletedProcess(["firebase"], codigo, stdout=saida, stderr="")


@pytest.mark.parametrize("saida", ["Authentication Error: Your credentials are no longer valid. Please run firebase login --reauth",
                                   "Error: Assertion failed: resolving hosting target of a site with no site name or target name",
                                   "HTTP Error: 401, Request had invalid authentication credentials."])
def test_credencial_vencida_vira_aviso_claro(monkeypatch, saida):
    monkeypatch.setattr(P, "_firebase", lambda *a, **k: _resposta(1, saida))
    assert P.conferir_acesso() == P.AVISO_CREDENCIAL
    with pytest.raises(RuntimeError, match="firebase login --reauth"):
        P.implantar()


def test_erro_de_outro_tipo_mantem_a_mensagem_original(monkeypatch):
    monkeypatch.setattr(P, "_firebase", lambda *a, **k: _resposta(1, "Error: quota exceeded"))
    assert P.conferir_acesso() == "Error: quota exceeded"


def test_acesso_ok_nao_tem_motivo(monkeypatch):
    monkeypatch.setattr(P, "_firebase", lambda *a, **k: _resposta(0, "live"))
    assert P.conferir_acesso() is None


def test_credencial_vencida_para_antes_da_suite(monkeypatch, capsys):
    monkeypatch.setattr(P, "motivo_para_nao_publicar", lambda: None)
    monkeypatch.setattr(P, "motivo_remoto", lambda: None)  # sem isto o teste depende do git do ambiente (no GitHub a main local fica atrás)
    monkeypatch.setattr(P, "conferir_acesso", lambda: P.AVISO_CREDENCIAL)
    monkeypatch.setattr(P, "rodar_suite", lambda: pytest.fail("não deveria rodar a suíte"))
    assert P.main([]) == 1
    assert "firebase login --reauth" in capsys.readouterr().out


def test_trava_impede_duas_publicacoes_e_some_no_fim(tmp_path):
    with P.trava("sessão A", tmp_path):
        assert (tmp_path / P.TRAVA).exists()
        with pytest.raises(P.PublicacaoEmAndamento, match="sessão A"):
            with P.trava("sessão B", tmp_path):
                pass
    assert not (tmp_path / P.TRAVA).exists()


def test_trava_some_mesmo_com_erro(tmp_path):
    with pytest.raises(ValueError):
        with P.trava("sessão A", tmp_path):
            raise ValueError
    assert not (tmp_path / P.TRAVA).exists()


def test_trava_vencida_e_substituida(tmp_path):
    import os
    import time
    arq = tmp_path / P.TRAVA
    arq.write_text("processo morto", encoding="utf-8")
    velho = time.time() - P.TRAVA_VALIDADE_S - 10
    os.utime(arq, (velho, velho))
    with P.trava("sessão nova", tmp_path):
        assert "sessão nova" in arq.read_text(encoding="utf-8")


def test_codigo_novo_na_main_bloqueia_o_agendador(repo):
    assert "nenhuma versão publicada" in P.motivo_codigo_nao_publicado(repo)
    _git(repo, "tag", "publicado-20260101-0000")
    assert P.motivo_codigo_nao_publicado(repo) is None
    (repo / "b.txt").write_text("b", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "b")
    assert "1 commit(s) depois de publicado-20260101-0000" in P.motivo_codigo_nao_publicado(repo)


def test_estado_lista_o_que_falta(repo):
    _git(repo, "tag", "publicado-20260101-0000")
    _git(repo, "branch", "desenvolvimento")
    _git(repo, "checkout", "-q", "-b", "ideia/x")
    (repo / "c.txt").write_text("c", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "c")
    _git(repo, "checkout", "-q", "main")
    texto = "\n".join(P.estado(repo))
    assert "publicado-20260101-0000; main com 0" in texto
    assert "desenvolvimento: 0" in texto and "ideia/x: 1 commit(s)" in texto


def test_com_desenvolvimento_so_avanca_direto(repo):
    _git(repo, "checkout", "-q", "-b", "desenvolvimento")
    (repo / "d.txt").write_text("d", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "d")
    _git(repo, "checkout", "-q", "main")
    assert P.trazer_desenvolvimento(repo) == P.commit_atual(repo)
    assert (repo / "d.txt").exists()
    (repo / "e.txt").write_text("e", encoding="utf-8")  # main diverge da desenvolvimento
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "e")
    _git(repo, "checkout", "-q", "desenvolvimento")
    (repo / "f.txt").write_text("f", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "f")
    _git(repo, "checkout", "-q", "main")
    with pytest.raises(RuntimeError, match="não avança direto"):
        P.trazer_desenvolvimento(repo)


def test_main_mudou_durante_a_suite_nao_publica(monkeypatch, tmp_path, capsys):
    commits = iter(["aaa", "bbb"])
    monkeypatch.setattr(P, "RAIZ", tmp_path)
    for nome in ("motivo_para_nao_publicar", "motivo_remoto", "conferir_acesso"):
        monkeypatch.setattr(P, nome, lambda: None)
    monkeypatch.setattr(P, "commit_atual", lambda: next(commits))
    monkeypatch.setattr(P, "rodar_suite", lambda: None)
    trava_original = P.trava
    monkeypatch.setattr(P, "trava", lambda quem: trava_original(quem, tmp_path))
    monkeypatch.setattr(P, "implantar", lambda: pytest.fail("não deveria implantar"))
    assert P.main([]) == 1
    assert "mudou durante a suíte" in capsys.readouterr().out


def test_publicacao_prepara_os_dados_antes_do_deploy(monkeypatch, tmp_path, capsys):
    ordem = []
    monkeypatch.setattr(P, "RAIZ", tmp_path)
    for nome in ("motivo_para_nao_publicar", "motivo_remoto", "conferir_acesso"):
        monkeypatch.setattr(P, nome, lambda: None)
    monkeypatch.setattr(P, "commit_atual", lambda: "aaa")
    monkeypatch.setattr(P, "rodar_suite", lambda: None)
    trava_original = P.trava
    monkeypatch.setattr(P, "trava", lambda quem: trava_original(quem, tmp_path))
    monkeypatch.setattr(P, "preparar_dados", lambda: ordem.append("dados"))
    monkeypatch.setattr(P, "implantar", lambda: ordem.append("deploy"))
    monkeypatch.setattr(P, "git", lambda *a, **k: "")
    assert P.main([]) == 0
    assert ordem == ["dados", "deploy"]


def test_agendador_tambem_prepara_os_dados(monkeypatch, tmp_path):
    import gerar_boletim_campo as G
    ordem = []
    monkeypatch.setattr(P, "motivo_para_nao_publicar", lambda: None)
    monkeypatch.setattr(P, "motivo_codigo_nao_publicado", lambda: None)
    trava_original = P.trava
    monkeypatch.setattr(P, "trava", lambda quem: trava_original(quem, tmp_path))
    monkeypatch.setattr(P, "preparar_dados", lambda: ordem.append("dados"))
    monkeypatch.setattr(P, "implantar", lambda: ordem.append("deploy"))
    G.publicar()
    assert ordem == ["dados", "deploy"]


def test_falha_nos_dados_nao_derruba_a_publicacao(monkeypatch, capsys):
    import gerar_janela_empresarial as J
    monkeypatch.setattr(J, "gerar", lambda: (_ for _ in ()).throw(OSError("disco cheio")))
    P.preparar_dados()
    assert "Janela Empresarial não atualizada" in capsys.readouterr().out


def test_boletim_nao_publica_codigo_sem_suite(monkeypatch):
    import gerar_boletim_campo as G
    monkeypatch.setattr(P, "motivo_para_nao_publicar", lambda: None)
    monkeypatch.setattr(P, "motivo_codigo_nao_publicado", lambda: "a main tem 2 commit(s) depois de publicado-x")
    monkeypatch.setattr(P, "implantar", lambda: pytest.fail("não deveria implantar"))
    with pytest.raises(RuntimeError, match="2 commit"):
        G.publicar()


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
