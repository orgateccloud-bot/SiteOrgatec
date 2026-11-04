"""Publica o site em orgatec.io: só da branch main, sem alterações pendentes e com a suíte passando.

Uso: python tools/publicar.py            (confere, roda JS + bandit + pytest, publica e marca a versão com uma tag)
     python tools/publicar.py --simular  (só diz se a pasta pode publicar)

O agendador do boletim (tools/gerar_boletim_campo.py) usa a mesma trava, sem rodar a suíte: ele só troca os
dados de site/dados, que ficam fora do git. Trabalho novo vai para uma prévia: python tools/previa.py.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404 — só executa git, node, python e firebase com argumentos fixos
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROJETO = "orgatec-site"
CONTA = "orgatec@orgatec.io"  # conta do Workspace; a Gmail fica como proprietária de reserva do projeto
BRANCH = "main"


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


def implantar(raiz: Path = RAIZ) -> None:
    firebase = shutil.which("firebase")
    if not firebase:
        raise RuntimeError("Firebase CLI não encontrado no PATH")
    cmd = [firebase, "deploy", "--only", "hosting", "--project", PROJETO, "--account", CONTA]
    r = subprocess.run(cmd, cwd=raiz, capture_output=True, text=True, encoding="utf-8", check=False)  # nosec B603 — argumentos fixos
    if r.returncode != 0:
        raise RuntimeError(f"publicação falhou: {r.stderr.strip() or r.stdout.strip()}")


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
    a = ap.parse_args(argv)
    motivo = motivo_para_nao_publicar()
    if motivo:
        print(f"não publicado: {motivo}")
        return 1
    if a.simular:
        print("a pasta pode publicar")
        return 0
    rodar_suite()
    implantar()
    tag = datetime.now().strftime("publicado-%Y%m%d-%H%M")
    git("tag", tag)
    git("push", "origin", BRANCH, tag)
    print(f"publicado: https://orgatec.io (tag {tag})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
