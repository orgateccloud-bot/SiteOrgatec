"""Confere o registro da revisão técnica gerado por docs/revisao/revisao-tecnica.html.

Recalcula o audit_hash (SHA-256 do JSON canônico do registro sem o próprio hash) e diz se o arquivo
foi alterado depois de gerado. Uso: python tools/conferir_revisao.py revisao-AAAA-MM-DD-xxxxxxxx.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def canonico(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def conferir(registro: dict) -> list[str]:
    erros = []
    corpo = {k: v for k, v in registro.items() if k != "audit_hash"}
    if not registro.get("responsavel"):
        erros.append("sem responsável")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(registro.get("data", ""))):
        erros.append("data inválida")
    for d in registro.get("decisoes", []):
        if d.get("decisao") not in ("aprovada", "ajustar"):
            erros.append(f"decisão inválida: {d.get('id')}")
        if not HEX64.match(str(d.get("conteudoHash", ""))):
            erros.append(f"hash do conteúdo inválido: {d.get('id')}")
    esperado = hashlib.sha256(canonico(corpo).encode("utf-8")).hexdigest()
    if registro.get("audit_hash") != esperado:
        erros.append("audit_hash não confere: o registro foi alterado depois de gerado")
    return erros


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("arquivo", type=Path)
    a = ap.parse_args(argv)
    erros = conferir(json.loads(a.arquivo.read_text(encoding="utf-8")))
    if erros:
        print("\n".join(erros))
        return 1
    print("Registro íntegro.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
