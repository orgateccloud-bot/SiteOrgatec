"""Relatório da distribuição dos estados da Janela de Campo no arquivo de boletins (site/dados/campo/boletim-*.json).

Serve para saber se as regras discriminam: se uma operação fica no mesmo estado em quase todos os dias e regiões, ou o
limite não combina com o que a fonte entrega ou a regra olha pouca coisa. O relatório só mede; não altera nenhuma regra
(os limites aguardam validação técnica, pendência V20).

Uso:
    python tools/relatorio_campo.py                 tabela no terminal
    python tools/relatorio_campo.py --json          o mesmo, em JSON
    python tools/relatorio_campo.py --pasta CAMINHO outra pasta de boletins
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "site" / "dados" / "campo"
OPERACOES = ("pulv", "plantio", "colheita", "animais", "maquinas")
NOMES = {"pulv": "Pulverização", "plantio": "Plantio", "colheita": "Colheita", "animais": "Manejo de animais", "maquinas": "Máquinas e insumos"}
ESTADOS = ("ok", "atencao", "evitar")
LIMIAR_POUCA_VARIACAO = 0.9  # um estado em 90% ou mais das combinações de região e dia
HORAS_UTEIS = 16  # 05h às 20h


def carregar(pasta: Path) -> list[dict]:
    return [json.loads(a.read_text(encoding="utf-8")) for a in sorted(pasta.glob("boletim-*.json"))]


def pct(cont: Counter) -> dict[str, float]:
    total = sum(cont.values()) or 1
    return {e: round(100 * cont[e] / total, 1) for e in ESTADOS if cont[e]}


def medir(boletins: list[dict]) -> dict:
    ops = {}
    for op in OPERACOES:
        horas, dia_polo, regiao_dia, motivos = Counter(), Counter(), Counter(), Counter()
        for b in boletins:
            for r in b.get("regioes", []):
                if op in r.get("ops", {}):
                    regiao_dia[r["ops"][op][0]] += 1
            for p in b.get("polos", []):
                o = p.get("ops", {}).get(op)
                if not o:
                    continue
                dia_polo[o["estado"]] += 1
                if o.get("motivo") and o["estado"] != "ok":
                    motivos[o["motivo"]] += 1
                for h, e in (o.get("porHora") or {}).items():
                    if 5 <= int(h) <= 20:
                        horas[e] += 1
        dominante = max(regiao_dia.values(), default=0) / (sum(regiao_dia.values()) or 1)
        ops[op] = {"nome": NOMES[op], "horas_pct": pct(horas), "dia_polo": dict(dia_polo), "regiao_dia": dict(regiao_dia),
                   "motivos": motivos.most_common(3), "pouca_variacao": dominante >= LIMIAR_POUCA_VARIACAO and sum(regiao_dia.values()) > 0}
    parciais = []
    for b in boletins:
        faltam = [p["id"] for p in b.get("polos", [])
                  if any(sum(1 for h in (o.get("porHora") or {}) if 5 <= int(h) <= 20) < HORAS_UTEIS for o in p.get("ops", {}).values())]
        if faltam:
            parciais.append({"dia": b["dia"], "geradoEm": b.get("geradoEm"), "polos": len(faltam)})
    return {"boletins": len(boletins), "dias": [b["dia"] for b in boletins], "operacoes": ops, "boletins_com_horas_faltando": parciais}


def texto(rel: dict) -> str:
    linhas = [f"Boletins no arquivo: {rel['boletins']} ({', '.join(rel['dias'])})", ""]
    for op in OPERACOES:
        o = rel["operacoes"][op]
        linhas.append(f"{o['nome']}{'  [POUCA VARIAÇÃO]' if o['pouca_variacao'] else ''}")
        linhas.append(f"  região x dia: {o['regiao_dia']}   polo x dia: {o['dia_polo']}")
        linhas.append(f"  horas 05h–20h: {o['horas_pct']}")
        linhas.append(f"  motivos mais comuns: {o['motivos']}")
    if rel["boletins_com_horas_faltando"]:
        linhas += ["", "Boletins finais com menos de 16 horas úteis de previsão (estado calculado com dado parcial):"]
        linhas += [f"  {x['dia']} (gerado {x['geradoEm']}): {x['polos']} polos" for x in rel["boletins_com_horas_faltando"]]
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pasta", type=Path, default=PASTA)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    boletins = carregar(a.pasta)
    if not boletins:
        print(f"Nenhum boletim em {a.pasta}", file=sys.stderr)
        return 1
    rel = medir(boletins)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(rel, ensure_ascii=False, indent=1) if a.json else texto(rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
