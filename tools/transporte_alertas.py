"""Rotina dos alertas de clima e desastres na rota (Central de Viagem). Roda como job do Cloud Run a cada 15 min.

  python tools/transporte_alertas.py            busca as fontes, cruza com as viagens, grava e envia (precisa de --confirmar para enviar)
  python tools/transporte_alertas.py --confirmar idem, com envio de mensagens
Sem --confirmar os canais ficam desligados nesta execução: nada sai para o motorista, mas o painel é atualizado.

Usa o mesmo banco da API (ORGATEC_TRANSPORTE_BANCO etc.) e exige ORGATEC_TRANSPORTE_ALERTAS=1. Configuração completa em
docs/ideias/alertas-rota.md, seção "Configuração".
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from backend.transporte.alertas import rotina  # noqa: E402
from backend.transporte.repositorio_transporte import criar_repositorio  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--confirmar", action="store_true", help="envia as mensagens (sem isto, só atualiza o painel)")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    # O httpx registra a URL de cada chamada em INFO, e a URL do FIRMS leva a chave: no Cloud Logging, só avisos e erros dele.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    env = dict(os.environ)
    if not rotina.ligado(env):
        print("alertas desligados (ORGATEC_TRANSPORTE_ALERTAS=1 liga)")
        return 0
    repo = criar_repositorio(env)
    cfg = rotina.configurar(env, repo)
    if not args.confirmar and cfg.envio is not None:
        cfg.envio.whatsapp = cfg.envio.sms = None
    print(json.dumps(rotina.executar(repo, cfg), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
