"""Publica o site em orgatec.io: só da branch main, sem alterações pendentes e com a suíte passando.

Uso: python tools/publicar.py                       (confere, roda JS + bandit + pytest, publica e marca a versão com uma tag)
     python tools/publicar.py --com-desenvolvimento  (antes, avança a main até a desenvolvimento, sem merge)
     python tools/publicar.py --simular              (só diz se a pasta pode publicar)
     python tools/publicar.py --estado               (o que falta publicar: main, desenvolvimento, ideias e pastas)

Uma publicação por vez: a trava .publicando.lock (fora do git) vale para este script e para o agendador do boletim.
O agendador (tools/gerar_boletim_campo.py) não roda a suíte; por isso só publica quando a main é exatamente a última
versão publicada (tag publicado-*). Código novo na main só vai ao ar por este script, com a suíte passando.
Trabalho novo vai para uma prévia: python tools/previa.py.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404 — só executa git, node, python e firebase com argumentos fixos
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

RAIZ = Path(__file__).resolve().parent.parent
PROJETO = "orgatec-site"
CONTA = "orgatec@orgatec.io"  # proprietária do projeto; vale também para o boletim agendado e para as prévias
BRANCH = "main"
# Sinais de credencial vencida na saída do Firebase CLI. "resolving hosting target" aparece no deploy quando ele não
# consegue consultar o site padrão do projeto. firebase login:list não serve de teste: só lista as contas salvas.
SINAIS_CREDENCIAL = ("credentials are no longer valid", "invalid authentication credentials", "resolving hosting target")
AVISO_CREDENCIAL = f"credencial do Firebase vencida: rode firebase login --reauth e entre com {CONTA}"
TRAVA = ".publicando.lock"
TRAVA_VALIDADE_S = 60 * 60  # a suíte leva ~12 min; trava mais velha que 1 h é de um processo que morreu
DESENVOLVIMENTO = "desenvolvimento"


def git(*args: str, raiz: Path = RAIZ) -> str:
    executavel = shutil.which("git")
    if not executavel:
        raise RuntimeError("git não encontrado no PATH")
    r = subprocess.run([executavel, *args], cwd=raiz, capture_output=True, text=True, encoding="utf-8", check=False)  # nosec B603
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falhou: {r.stderr.strip()}")
    return r.stdout.strip()


def motivo_para_nao_publicar(raiz: Path = RAIZ) -> str | None:
    """Devolve o motivo do bloqueio ou None. Vale para quem publica à mão e para o agendador."""
    try:
        branch = git("branch", "--show-current", raiz=raiz)
        if branch != BRANCH:
            return f"a pasta está na branch {branch or '(sem branch)'}; só a {BRANCH} publica"
        pendentes = git("status", "--porcelain", raiz=raiz)
    except RuntimeError as erro:
        return str(erro)
    if pendentes:
        return f"há alterações sem commit na pasta ({len(pendentes.splitlines())} arquivos)"
    return None


class PublicacaoEmAndamento(RuntimeError):
    pass


@contextmanager
def trava(quem: str, raiz: Path = RAIZ) -> Iterator[None]:
    """Uma publicação por vez na pasta. Criação exclusiva do arquivo: duas sessões (ou sessão e agendador) não entram juntas."""
    arq = raiz / TRAVA
    for _ in range(2):
        try:
            fd = os.open(arq, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                idade = time.time() - arq.stat().st_mtime
                dono = arq.read_text(encoding="utf-8").strip()
            except OSError:
                continue  # sumiu entre as duas chamadas: tenta de novo
            if idade < TRAVA_VALIDADE_S:
                raise PublicacaoEmAndamento(f"outra publicação em andamento ({dono}); espere ela terminar") from None
            arq.unlink(missing_ok=True)  # vencida
    else:
        raise PublicacaoEmAndamento("não foi possível criar a trava de publicação")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(f"{quem}, pid {os.getpid()}, desde {datetime.now():%d/%m/%Y %H:%M}")
    try:
        yield
    finally:
        arq.unlink(missing_ok=True)


def commit_atual(raiz: Path = RAIZ) -> str:
    return git("rev-parse", "HEAD", raiz=raiz)


def ultima_publicada(raiz: Path = RAIZ) -> str | None:
    """Tag publicado-* mais recente alcançável pela HEAD, ou None."""
    try:
        return git("describe", "--tags", "--abbrev=0", "--match", "publicado-*", raiz=raiz)
    except RuntimeError:
        return None


def motivo_codigo_nao_publicado(raiz: Path = RAIZ) -> str | None:
    """Para o agendador: a main tem commits que ainda não passaram pela suíte de uma publicação?"""
    tag = ultima_publicada(raiz)
    if tag is None:
        return "nenhuma versão publicada (tag publicado-*) na main"
    novos = git("rev-list", "--count", f"{tag}..HEAD", raiz=raiz)
    if novos != "0":
        return f"a main tem {novos} commit(s) depois de {tag} ainda sem publicação; rode python tools/publicar.py"
    return None


def motivo_remoto(raiz: Path = RAIZ) -> str | None:
    """A main local não pode estar atrás do GitHub: o push do fim falharia depois de publicar."""
    try:
        git("fetch", "-q", "origin", BRANCH, raiz=raiz)
        git("merge-base", "--is-ancestor", f"origin/{BRANCH}", "HEAD", raiz=raiz)
    except RuntimeError:
        return f"a {BRANCH} local está atrás de origin/{BRANCH} (ou o GitHub não respondeu): traga o que falta antes"
    return None


def trazer_desenvolvimento(raiz: Path = RAIZ) -> str:
    """Avança a main até a desenvolvimento, só por avanço direto (sem merge e sem conflito na pasta principal)."""
    try:
        git("merge", "--ff-only", DESENVOLVIMENTO, raiz=raiz)
    except RuntimeError as erro:
        raise RuntimeError(f"a {BRANCH} não avança direto até a {DESENVOLVIMENTO}: integre na {DESENVOLVIMENTO} primeiro ({erro})") from None
    return commit_atual(raiz)


def estado(raiz: Path = RAIZ) -> list[str]:
    """Resumo do que falta publicar, para qualquer sessão conferir antes de mexer."""
    linhas = []
    tag = ultima_publicada(raiz)
    novos = git("rev-list", "--count", f"{tag}..{BRANCH}", raiz=raiz) if tag else "?"
    linhas.append(f"no ar: {tag or 'nenhuma tag'}; main com {novos} commit(s) depois dela")
    try:
        frente = git("rev-list", "--count", f"{BRANCH}..{DESENVOLVIMENTO}", raiz=raiz)
        linhas.append(f"desenvolvimento: {frente} commit(s) fora da main")
    except RuntimeError:
        linhas.append("desenvolvimento: branch não encontrada")
    for ref in git("for-each-ref", "--format=%(refname:short)", "refs/heads/ideia", raiz=raiz).splitlines():
        n = git("rev-list", "--count", f"{BRANCH}..{ref}", raiz=raiz)
        if n != "0":
            linhas.append(f"{ref}: {n} commit(s) fora da main")
    for linha in git("worktree", "list", "--porcelain", raiz=raiz).splitlines():
        if linha.startswith("worktree "):
            pasta = Path(linha[9:])
            try:
                sujos = git("status", "--porcelain", raiz=pasta)
            except RuntimeError:
                continue
            if sujos:
                linhas.append(f"pasta {pasta}: {len(sujos.splitlines())} arquivo(s) sem commit")
    arq = raiz / TRAVA
    if arq.exists():
        linhas.append(f"trava: {arq.read_text(encoding='utf-8').strip()}")
    return linhas


def _firebase(*args: str, raiz: Path = RAIZ) -> subprocess.CompletedProcess:
    firebase = shutil.which("firebase")
    if not firebase:
        raise RuntimeError("Firebase CLI não encontrado no PATH")
    cmd = [firebase, *args, "--project", PROJETO, "--account", CONTA]
    return subprocess.run(cmd, cwd=raiz, capture_output=True, text=True, encoding="utf-8", check=False)  # nosec B603 — argumentos fixos


def explicar_falha(r: subprocess.CompletedProcess) -> str:
    saida = " ".join(filter(None, (r.stderr, r.stdout))).strip()
    if any(sinal in saida for sinal in SINAIS_CREDENCIAL):
        return AVISO_CREDENCIAL
    return saida


def conferir_acesso(raiz: Path = RAIZ) -> str | None:
    """Devolve o motivo se o Firebase não responder. Consulta real, para falhar antes dos minutos da suíte."""
    r = _firebase("hosting:channel:list", raiz=raiz)
    return None if r.returncode == 0 else explicar_falha(r)


def implantar(raiz: Path = RAIZ) -> None:
    r = _firebase("deploy", "--only", "hosting", raiz=raiz)
    if r.returncode != 0:
        raise RuntimeError(f"publicação falhou: {explicar_falha(r)}")


def suite(raiz: Path = RAIZ) -> list[tuple[str, list[str]]]:
    py = sys.executable
    return [("JS", [shutil.which("node") or "node", "--test", *map(str, sorted((raiz / "tests" / "js").glob("*.test.js")))]),
            ("bandit", [py, "-m", "bandit", "-q", "-r", "backend", "tools"]),
            ("pytest", [py, "-m", "pytest", "tests/py", "tests/e2e", "-q", "-p", "no:cacheprovider"])]


def rodar_suite(raiz: Path = RAIZ) -> None:
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    for nome, cmd in suite(raiz):
        print(f"testes: {nome}...", flush=True)
        r = subprocess.run(cmd, cwd=raiz, env=env, check=False)  # nosec B603 — argumentos fixos
        if r.returncode != 0:
            raise SystemExit(f"{nome} falhou: nada foi publicado")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--simular", action="store_true", help="só confere se a pasta pode publicar")
    ap.add_argument("--com-desenvolvimento", action="store_true", help="avança a main até a desenvolvimento antes da suíte")
    ap.add_argument("--estado", action="store_true", help="mostra o que falta publicar e sai")
    a = ap.parse_args(argv)
    if a.estado:
        print("\n".join(estado()))
        return 0
    for conferir in (motivo_para_nao_publicar, motivo_remoto, conferir_acesso):
        motivo = conferir()
        if motivo:
            print(f"não publicado: {motivo}")
            return 1
    if a.simular:
        print("a pasta pode publicar")
        return 0
    try:
        with trava("tools/publicar.py"):
            if a.com_desenvolvimento:
                print(f"main avançada até {trazer_desenvolvimento()[:7]}", flush=True)
            testado = commit_atual()
            rodar_suite()
            # Outra sessão pode ter mexido na main durante os minutos da suíte: só publica o que foi testado.
            if commit_atual() != testado or motivo_para_nao_publicar():
                print("não publicado: a main mudou durante a suíte; rode de novo")
                return 1
            implantar()
            tag = datetime.now().strftime("publicado-%Y%m%d-%H%M")
            git("tag", tag)
            git("push", "origin", BRANCH, tag)
    except RuntimeError as erro:
        print(f"não publicado: {erro}")
        return 1
    print(f"publicado: https://orgatec.io (tag {tag})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
