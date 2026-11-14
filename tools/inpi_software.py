"""Pacote do código-fonte do site e da API para o registro de programa de computador no INPI (e-Software).

O INPI não recebe o código: recebe o resumo hash (SHA-512) de um arquivo que o titular guarda sem alterar. Este script
monta esse arquivo de forma reproduzível a partir de uma versão do git (uma tag `publicado-*`), só com o código próprio
da ORGATEC, e calcula o hash. Rodar de novo na mesma versão dá o mesmo hash, o que permite provar depois que o arquivo
guardado é o registrado.

Uso:
  python tools/inpi_software.py                       (resumo da versão no ar: quantos arquivos e o que fica de fora)
  python tools/inpi_software.py --listar              (lista os arquivos que entram)
  python tools/inpi_software.py --gerar               (grava pacote, hash e manifesto fora do repositório)
  python tools/inpi_software.py --ref <tag> --saida <pasta> --gerar

Saída padrão: D:/01_Projetos_Ativos/SiteOrgatec-dados-privados/inpi/ (fora do git). Ver docs/inpi/registro-software-site.md.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import subprocess  # nosec B404 — só executa git com argumentos fixos
import sys
import tarfile
from fnmatch import fnmatch
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA_PADRAO = RAIZ.parent / "SiteOrgatec-dados-privados" / "inpi"
NOME = "orgatec-io-site-api"

# Código próprio que entra no pacote
INCLUIR = ["backend/*", "tools/*", "site/assets/js/*", "site/assets/css/*",
           "Dockerfile", ".dockerignore", "firebase.json", "firestore.rules", "firestore.indexes.json", "tailwind.config.js"]
# Código e dados de terceiros, e arquivos gerados, que ficam de fora
EXCLUIR = ["site/assets/vendor/*",           # MapLibre (licença BSD), de terceiros
           "site/assets/fontes/*",           # fontes tipográficas de terceiros
           "site/assets/css/tailwind.css",   # CSS gerado pelo Tailwind (MIT) a partir de tools/tailwind-entrada.css
           "*/__pycache__/*", "*.pyc"]


def _git(*args: str, raiz: Path = RAIZ) -> bytes:
    return subprocess.run(["git", *args], cwd=raiz, check=True, capture_output=True).stdout  # nosec B603 B607


def entra(caminho: str) -> bool:
    return any(fnmatch(caminho, p) for p in INCLUIR) and not any(fnmatch(caminho, p) for p in EXCLUIR)


def ultima_publicada(raiz: Path = RAIZ) -> str:
    tags = _git("tag", "-l", "publicado-*", "--sort=-creatordate", raiz=raiz).decode().split()
    if not tags:
        raise SystemExit("nenhuma tag publicado-* encontrada")
    return tags[0]


def arquivos(ref: str, raiz: Path = RAIZ) -> list[tuple[str, str]]:
    """(caminho, id do blob) dos arquivos da versão que entram no pacote, em ordem."""
    saida = _git("ls-tree", "-r", "--full-tree", ref, raiz=raiz).decode("utf-8")
    itens = []
    for linha in saida.splitlines():
        meta, caminho = linha.split("\t", 1)
        _modo, tipo, blob = meta.split()
        if tipo == "blob" and entra(caminho):
            itens.append((caminho, blob))
    return sorted(itens)


def montar(ref: str, raiz: Path = RAIZ) -> tuple[bytes, list[dict]]:
    """Tar reproduzível (ordem fixa, data do commit, dono e permissões fixos) e o manifesto por arquivo."""
    data = int(_git("show", "-s", "--format=%ct", ref, raiz=raiz).decode().strip())
    buf = io.BytesIO()
    manifesto = []
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for caminho, blob in arquivos(ref, raiz):
            conteudo = _git("cat-file", "blob", blob, raiz=raiz)
            info = tarfile.TarInfo(f"{NOME}/{caminho}")
            info.size, info.mtime, info.mode = len(conteudo), data, 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(conteudo))
            manifesto.append({"arquivo": caminho, "bytes": len(conteudo), "sha256": hashlib.sha256(conteudo).hexdigest()})
    return buf.getvalue(), manifesto


def dentro_do_repositorio(pasta: Path, raiz: Path = RAIZ) -> bool:
    try:
        pasta.resolve().relative_to(raiz.resolve())
        return True
    except ValueError:
        return False


def gerar(ref: str, saida: Path, raiz: Path = RAIZ) -> dict:
    if dentro_do_repositorio(saida, raiz):
        raise SystemExit(f"recusado: {saida} fica dentro do repositório; o pacote precisa ficar fora do git")
    pacote, manifesto = montar(ref, raiz)
    sha512 = hashlib.sha512(pacote).hexdigest()
    commit = _git("rev-parse", f"{ref}^{{commit}}", raiz=raiz).decode().strip()
    base = saida / f"{NOME}-{ref}"
    saida.mkdir(parents=True, exist_ok=True)
    (base.with_suffix(".tar")).write_bytes(pacote)
    (base.with_suffix(".sha512")).write_text(f"{sha512}  {base.name}.tar\n", encoding="utf-8")
    with open(base.with_suffix(".manifesto.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["arquivo", "bytes", "sha256"])
        w.writeheader()
        w.writerows(manifesto)
    (base.with_suffix(".leia-me.txt")).write_text(
        f"Pacote do registro de programa de computador no INPI (e-Software)\n"
        f"Programa: ORGATEC.IO — site e API\nVersão (tag): {ref}\nCommit: {commit}\n"
        f"Arquivos: {len(manifesto)}\nSHA-512 do .tar: {sha512}\n\n"
        f"Guarde o .tar sem alterar: é a prova de que o código registrado é este.\n"
        f"Para conferir: python tools/inpi_software.py --ref {ref} (o hash deve ser o mesmo).\n",
        encoding="utf-8")
    return {"ref": ref, "commit": commit, "arquivos": len(manifesto), "bytes": len(pacote), "sha512": sha512, "pasta": str(saida)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ref", help="tag ou commit (padrão: a última publicado-*)")
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    ap.add_argument("--listar", action="store_true", help="lista os arquivos que entram")
    ap.add_argument("--gerar", action="store_true", help="grava pacote, hash e manifesto na pasta de saída")
    a = ap.parse_args(argv)
    ref = a.ref or ultima_publicada()
    if a.listar:
        for caminho, _ in arquivos(ref):
            print(caminho)
        return 0
    if a.gerar:
        r = gerar(ref, a.saida)
        print(f"gerado: {r['pasta']}\\{NOME}-{ref}.tar ({r['arquivos']} arquivos, {r['bytes'] // 1024} KB)")
        print(f"SHA-512: {r['sha512']}")
        return 0
    pacote, manifesto = montar(ref)
    print(f"versão {ref}: {len(manifesto)} arquivos, {len(pacote) // 1024} KB")
    print(f"SHA-512 (sem gravar): {hashlib.sha512(pacote).hexdigest()}")
    print("fora do pacote: " + ", ".join(EXCLUIR[:3]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
