"""Gera um link de prévia da branch atual num canal do Firebase Hosting, sem tocar em orgatec.io.

Uso: python tools/previa.py            (canal com o nome da branch; a desenvolvimento usa o canal dev)
     python tools/previa.py --simular  (só mostra o canal e o comando)

O link expira sozinho. Como site/dados fica fora do git, os dados são copiados da pasta principal antes de publicar.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess  # nosec B404 — só executa git e firebase com argumentos fixos
import sys
from pathlib import Path

import publicar as P

VALIDADE = "30d"


def canal_da_branch(branch: str) -> str:
    """ideia/Novo Simulador → ideia-novo-simulador. O limite evita passar do tamanho de um nome de domínio."""
    if branch == "desenvolvimento":
        return "dev"
    return re.sub(r"[^a-z0-9]+", "-", branch.lower()).strip("-")[:36].strip("-")


def pasta_principal() -> Path:
    """A primeira pasta listada pelo git é a principal, onde o agendador grava os dados."""
    return Path(P.git("worktree", "list", "--porcelain").splitlines()[0].removeprefix("worktree ").strip())


def copiar_dados(principal: Path, destino: Path = P.RAIZ) -> None:
    origem = principal / "site" / "dados"
    if origem.is_dir() and principal.resolve() != destino.resolve():
        shutil.copytree(origem, destino / "site" / "dados", dirs_exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--simular", action="store_true", help="só mostra o canal e o comando")
    a = ap.parse_args(argv)
    branch = P.git("branch", "--show-current")
    if not branch or branch == P.BRANCH:
        print(f"prévia é para branches de trabalho; a {P.BRANCH} já é o site no ar")
        return 1
    canal = canal_da_branch(branch)
    firebase = shutil.which("firebase") or "firebase"
    cmd = [firebase, "hosting:channel:deploy", canal, "--expires", VALIDADE, "--project", P.PROJETO, "--account", P.CONTA]
    if a.simular:
        print(" ".join(cmd))
        return 0
    copiar_dados(pasta_principal())
    return subprocess.run(cmd, cwd=P.RAIZ, check=False).returncode  # nosec B603 — argumentos fixos


if __name__ == "__main__":
    sys.exit(main())
