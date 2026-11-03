"""Converte orgatec_io_modelos_testes.xlsx em site/assets/js/demo-dados.js.

Uso:
    python tools/gerar_demo.py            # gera o arquivo
    python tools/gerar_demo.py --dry-run  # apenas imprime o JSON

Os IPs do log de auditoria são mascarados aqui (localmente), antes de qualquer
publicação: endereço IP é dado pessoal (LGPD, art. 5º, I). O arquivo gerado
guarda apenas o IP mascarado e um hash SHA-256 truncado para correlação.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parent.parent
XLSX = RAIZ / "orgatec_io_modelos_testes.xlsx"
SAIDA = RAIZ / "site" / "assets" / "js" / "demo-dados.js"

# Salt fixo apenas para o hash de correlação dos dados de DEMONSTRAÇÃO.
SALT_DEMO = "orgatec-demo"

COLS_XML = ["id", "cnpj", "emitente", "uf", "chave", "tipo", "valor", "data", "status", "lgpd"]
COLS_PORTAL = ["protocolo", "cnpj", "uf", "departamento", "solicitacao", "competencia",
               "status", "sla", "log", "acao"]


def mascarar_log(log: str) -> dict:
    """'177.18.22.90 (MFA OK)' -> {'ip': '177.18.***.***', 'ipHash': 'ab12cd34', 'mfa': True}"""
    m = re.match(r"\s*(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\s*(?:\((.*)\))?", log or "")
    if not m:
        return {"ip": "***", "ipHash": None, "mfa": False, "bruto": None}
    ip = ".".join(m.group(i) for i in range(1, 5))
    detalhe = (m.group(5) or "").upper()
    return {
        "ip": f"{m.group(1)}.{m.group(2)}.***.***",
        "ipHash": hashlib.sha256(f"{SALT_DEMO}:{ip}".encode()).hexdigest()[:8],
        "mfa": "MFA OK" in detalhe or "2FA OK" in detalhe,
    }


def ler_aba(ws, colunas: list[str]) -> list[dict]:
    linhas = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not any(c is not None for c in row):
            continue
        reg = dict(zip(colunas, row))
        for k, v in reg.items():
            if isinstance(v, (dt.date, dt.datetime)):
                reg[k] = v.strftime("%Y-%m-%d")
        linhas.append(reg)
    return linhas


def gerar() -> dict:
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    xml = ler_aba(wb["Modelo_Captura_XML"], COLS_XML)
    for r in xml:
        r["chave"] = str(r["chave"])
        r["valor"] = float(r["valor"])
    portal = ler_aba(wb["Modelo_Portal_Cliente"], COLS_PORTAL)
    for r in portal:
        r["auditoria"] = mascarar_log(r.pop("log"))
        r["sla"] = str(r["sla"])
    return {"origem": XLSX.name, "capturaXml": xml, "protocolos": portal}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dados = gerar()
    js = json.dumps(dados, ensure_ascii=False, indent=2)
    if args.dry_run:
        print(js)
        return 0
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(
        "/* GERADO por tools/gerar_demo.py a partir de orgatec_io_modelos_testes.xlsx — não edite à mão.\n"
        "   Dados FICTÍCIOS de homologação; IPs mascarados (LGPD). */\n"
        "(function (root) {\n"
        "  var dados = " + js.replace("\n", "\n  ") + ";\n"
        "  if (typeof module === 'object' && module.exports) module.exports = dados;\n"
        "  else (root.Orgatec = root.Orgatec || {}).demo = dados;\n"
        "})(this);\n",
        encoding="utf-8",
    )
    print(f"OK: {SAIDA.relative_to(RAIZ)} ({len(dados['capturaXml'])} XML, {len(dados['protocolos'])} protocolos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
