"""Rotinas de LGPD do banco dos formulários. Nada é apagado sem --confirmar.

Usa o mesmo banco e o mesmo segredo da API (ORGATEC_BANCO, ORGATEC_DB, ORGATEC_SEGREDO_IP): rode com as variáveis do
ambiente que quer atender. A tela nunca mostra dados pessoais, só protocolos; os dados saem apenas em --exportar.

  python tools/lgpd.py retencao                   lista o que passou do prazo (backend/retencao.py)
  python tools/lgpd.py retencao --confirmar       elimina esses dados
  python tools/lgpd.py titular --email x@y.com    localiza um titular (--whatsapp também aceito)
  python tools/lgpd.py titular --email x@y.com --exportar resposta.json          acesso e portabilidade (art. 18)
  python tools/lgpd.py titular --email x@y.com --eliminar [--protocolo LD-...]   mostra o que seria eliminado
  python tools/lgpd.py titular --email x@y.com --eliminar --confirmar            elimina
  python tools/lgpd.py trilha                     confere a trilha inteira (sai com erro se estiver quebrada)

Antes de eliminar a pedido do titular, confira se há obrigação legal de guardar (LGPD, art. 16). A eliminação apaga os
dados e deixa só protocolo, tipo, datas e hashes, para a trilha continuar íntegra.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("ORGATEC_SERVIR_SITE", "0")  # só o repositório interessa aqui

from backend.app import repo  # noqa: E402


def _trilha() -> int:
    if repo.verificar_cadeia():
        print(f"trilha íntegra: {repo.contar()} registros")
        return 0
    print("TRILHA QUEBRADA: há registro alterado ou apagado. Trate como possível incidente.", file=sys.stderr)
    return 1


def retencao(args) -> int:
    vencidos = repo.vencidos()
    for r in vencidos:
        print(f"{r['protocolo']}  {r['tipo']:8}{r['status']:22}{r['criado_em']}")
    print(f"{len(vencidos)} registro(s) fora do prazo")
    if not args.confirmar:
        print("Nada foi apagado. Para eliminar, repita com --confirmar.")
        return 0
    apagados = sum(repo.eliminar(r["protocolo"], "retencao") for r in vencidos)
    print(f"{apagados} eliminado(s)")
    _telemetria_vencida(confirmar=True)
    _coordenadas_google_vencidas()
    return _trilha()


def _telemetria_vencida(confirmar: bool) -> None:
    """Leituras de sensores da Central de Viagem fora do prazo (só quando ORGATEC_TRANSPORTE_BANCO é persistente)."""
    from datetime import timedelta

    from backend.repositorio import agora_utc
    from backend.retencao import prazos_do_ambiente
    from backend.transporte.repositorio_transporte import RepositorioMemoria, criar_repositorio

    rt = criar_repositorio()
    if isinstance(rt, RepositorioMemoria):
        return
    limite = agora_utc() - timedelta(days=prazos_do_ambiente().telemetria_dias)
    print(f"{rt.purgar_leituras(limite)} leitura(s) de sensor eliminada(s)" if confirmar else "")


def _coordenadas_google_vencidas() -> None:
    """Termos do Google Maps Platform: coordenadas da Routes e da Places só ficam guardadas por até 30 dias (Central de Viagem)."""
    from datetime import timedelta

    from backend.repositorio import agora_utc
    from backend.transporte.repositorio_transporte import RepositorioMemoria, criar_repositorio
    from backend.transporte.servicos.viagem import PRAZO_COORDENADAS_GOOGLE_DIAS

    rt = criar_repositorio()
    if isinstance(rt, RepositorioMemoria):
        return
    limite = agora_utc() - timedelta(days=PRAZO_COORDENADAS_GOOGLE_DIAS)
    print(f"{rt.expirar_coordenadas_google(limite)} viagem(ns) sem as coordenadas do Google vencidas")


def _exportar(registros: list[dict], destino: Path) -> None:
    destino = destino.resolve()
    if RAIZ / "site" in destino.parents:
        raise SystemExit("recusado: site/ é publicado; não grave dados de titular nessa pasta")
    if destino.exists():
        raise SystemExit(f"recusado: {destino} já existe")
    destino.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(registros)} registro(s) exportado(s) para {destino}. O arquivo tem dados pessoais: "
          "entregue ao titular por canal seguro e apague a cópia depois.")


def titular(args) -> int:
    if not args.email and not args.whatsapp:
        raise SystemExit("informe --email ou --whatsapp")
    registros = repo.localizar_titular(args.email, args.whatsapp)
    for r in registros:
        print(f"{r['protocolo']}  {r['tipo']:8}{r['status']:22}{r['criado_em']}")
    print(f"{len(registros)} registro(s) com esse contato")
    if args.exportar:
        _exportar(registros, Path(args.exportar))
    if not args.eliminar:
        return 0
    alvos = [r for r in registros if not args.protocolo or r["protocolo"] in args.protocolo]
    if not args.confirmar:
        print(f"{len(alvos)} seriam eliminado(s). Nada foi apagado. Para eliminar, repita com --confirmar.")
        return 0
    apagados = sum(repo.eliminar(r["protocolo"], "titular") for r in alvos)
    print(f"{apagados} eliminado(s)")
    return _trilha()


def principal() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="comando", required=True)
    r = sub.add_parser("retencao")
    r.add_argument("--confirmar", action="store_true")
    r.set_defaults(rodar=retencao)
    t = sub.add_parser("titular")
    t.add_argument("--email")
    t.add_argument("--whatsapp")
    t.add_argument("--exportar", metavar="ARQUIVO")
    t.add_argument("--eliminar", action="store_true")
    t.add_argument("--protocolo", action="append", help="limita a eliminação a este protocolo (pode repetir)")
    t.add_argument("--confirmar", action="store_true")
    t.set_defaults(rodar=titular)
    sub.add_parser("trilha").set_defaults(rodar=lambda _args: _trilha())
    args = p.parse_args()
    return args.rodar(args)


if __name__ == "__main__":
    sys.exit(principal())
