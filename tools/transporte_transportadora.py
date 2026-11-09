"""Cria uma transportadora (tenant) da Central de Viagem e imprime o UUID, para usar em transporte_usuario.py.

  python tools/transporte_transportadora.py --projeto orgatec-site                     cria com um UUID novo
  python tools/transporte_transportadora.py --projeto orgatec-site --uuid <uuid>       cria com o UUID dado (idempotente)
  python tools/transporte_transportadora.py --projeto orgatec-site --conferir <uuid>   só diz se existe

Grava no mesmo Firestore da API (coleção transporte_tenants, banco padrão). Credenciais: `gcloud auth application-default login`
com uma conta que escreva no Firestore do projeto; nada é gravado em arquivo. Criar de novo o mesmo UUID não muda nada.
Só é preciso uma vez por cliente; sem o documento da transportadora, toda chamada da API responde "acesso negado".
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def criar(repo, uuid: str | None = None) -> tuple[str, bool]:
    """Cria a transportadora no repositório. Devolve (uuid, já_existia). Sem efeito se já existir."""
    if uuid is not None and not UUID.fullmatch(uuid):
        raise SystemExit("O UUID da transportadora deve ter o formato 8-4-4-4-12 (36 caracteres).")
    if uuid is not None and repo.existe_transportadora(uuid):
        return uuid, True
    return repo.criar_transportadora(uuid), False


def main(argv: list[str] | None = None, repo=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--projeto", required=True, help="projeto do Google (ex.: orgatec-site)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--uuid", help="UUID a usar em vez de gerar um novo")
    g.add_argument("--conferir", metavar="UUID", help="só confere se a transportadora existe")
    a = ap.parse_args(argv)
    if repo is None:
        from backend.transporte.repositorio_transporte import RepositorioFirestore

        repo = RepositorioFirestore(projeto=a.projeto)
    if a.conferir:
        if not UUID.fullmatch(a.conferir):
            raise SystemExit("O UUID da transportadora deve ter o formato 8-4-4-4-12 (36 caracteres).")
        existe = repo.existe_transportadora(a.conferir)
        print(f"{a.conferir}: {'existe' if existe else 'não existe'}")
        return 0 if existe else 1
    tid, existia = criar(repo, a.uuid)
    print(f"{tid}: {'já existia' if existia else 'criada'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
