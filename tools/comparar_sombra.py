"""Compara o boletim gerado na SOMBRA (GitHub Actions, sem publicar) com o que está no ar (gerado pelo agendador do Windows).

Durante a semana de sombra os dois geram o mesmo boletim a poucos minutos de distância. Esta ferramenta diz se o GitHub
produz o mesmo formato e os mesmos polos e regiões; as diferenças de estado são esperadas (a previsão muda de uma rodada
para a outra) e só são contadas. Plano: docs/plano-ativacao-boletim-actions.md.

Uso (depois de gerar o boletim em site/dados):
    python tools/comparar_sombra.py                     compara site/dados com https://orgatec.io
    python tools/comparar_sombra.py --ao-vivo URL       outro site (só https)

Saída 0: mesmo formato (pode haver avisos). Saída 1: formato diferente ou boletim da sombra inválido.
No GitHub Actions o resultado também vai para o resumo da execução.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "site" / "dados"
AO_VIVO = "https://orgatec.io"
ESTADOS = {"ok", "atencao", "evitar"}
OPERACOES = ("pulv", "plantio", "colheita", "animais", "maquinas")
MAX_RESUMO = 90
LIMITE_DIFERENCA_MIN = 90  # a sombra roda perto da rodada do Windows; além disso, algo atrasou


def _ids(lista: object) -> list[str]:
    return sorted(x.get("id", "") for x in lista if isinstance(x, dict)) if isinstance(lista, list) else []


def comparar(sombra: dict, ao_vivo: dict) -> dict:
    """Cada lado tem as chaves "atual" (boletim), "noticias" e "historico" (dicts; podem faltar). Devolve falhas, avisos e info."""
    falhas: list[str] = []
    avisos: list[str] = []
    info: dict[str, object] = {}
    s, v = sombra.get("atual") or {}, ao_vivo.get("atual") or {}
    if not s:
        return {"falhas": ["a sombra não gerou o boletim (atual.json ausente ou vazio)"], "avisos": [], "info": {}}

    if v:
        faltam, sobram = sorted(set(v) - set(s)), sorted(set(s) - set(v))
        if faltam or sobram:
            falhas.append(f"chaves do boletim diferentes do que está no ar: faltam {faltam}, sobram {sobram}")
        if _ids(s.get("polos")) != _ids(v.get("polos")):
            falhas.append("os polos da sombra não são os mesmos do boletim no ar")
        if _ids(s.get("regioes")) != _ids(v.get("regioes")):
            falhas.append("as regiões da sombra não são as mesmas do boletim no ar")
    else:
        avisos.append("não foi possível ler o boletim no ar para comparar; só a validade da sombra foi conferida")

    for r in s.get("regioes", []):
        for op in OPERACOES:
            valor = (r.get("ops") or {}).get(op)
            if not valor or valor[0] not in ESTADOS or not valor[1]:
                falhas.append(f"região {r.get('id')}: operação {op} sem estado válido")
            elif len(valor[1]) > MAX_RESUMO and valor[1] != "Sem previsão para as horas úteis de hoje (05h às 20h).":
                falhas.append(f"região {r.get('id')}: resumo de {op} com {len(valor[1])} caracteres (limite {MAX_RESUMO})")
    if "semDados" not in s:
        falhas.append("o boletim da sombra não tem semDados: o código gerador está desatualizado")

    if v:
        mudaram = sum(
            1 for rs in s.get("regioes", []) for rv in v.get("regioes", []) if rs.get("id") == rv.get("id")
            for op in OPERACOES if (rs.get("ops") or {}).get(op, [None])[0] != (rv.get("ops") or {}).get(op, [None])[0])
        info["estados_diferentes"] = f"{mudaram} de {len(OPERACOES) * len(s.get('regioes', []))} (esperado: a previsão muda entre rodadas)"
        try:
            dif = abs((datetime.fromisoformat(s["geradoEm"]) - datetime.fromisoformat(v["geradoEm"])).total_seconds()) / 60
            info["geradoEm"] = f"sombra {s['geradoEm']}, no ar {v['geradoEm']} (diferença de {dif:.0f} min)"
            if dif > LIMITE_DIFERENCA_MIN:
                avisos.append(f"a sombra e o boletim no ar foram gerados com {dif:.0f} min de diferença (limite {LIMITE_DIFERENCA_MIN})")
        except (KeyError, ValueError):
            avisos.append("não foi possível comparar a hora de geração dos dois boletins")

    ns, nv = sombra.get("noticias") or {}, ao_vivo.get("noticias") or {}
    if not ns:
        falhas.append("a sombra não gerou o noticias.json")
    elif nv and set(ns) != set(nv):
        falhas.append(f"chaves do noticias.json diferentes do que está no ar: {sorted(set(ns) ^ set(nv))}")
    if ns:
        info["notícias com tema atendido"] = f"{sum(1 for x in (ns.get('atividades') or {}).values() if x)} de {len(ns.get('atividades') or {})}"
    hs, hv = len((sombra.get("historico") or {}).get("itens", [])), len((ao_vivo.get("historico") or {}).get("itens", []))
    info["histórico de notícias"] = f"sombra {hs} itens, no ar {hv}"
    if hv and hs < hv * 0.8:
        avisos.append("o histórico de notícias da sombra tem bem menos itens que o do ar: a restauração pode ter falhado")
    return {"falhas": falhas, "avisos": avisos, "info": info}


def _ler(base: Path) -> dict:
    def ler(rel: str) -> dict:
        try:
            return json.loads((base / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
    return {"atual": ler("campo/atual.json"), "noticias": ler("agro/noticias.json"), "historico": ler("agro/historico.json")}


def _baixar(base: str) -> dict:
    def baixar(rel: str) -> dict:
        try:
            r = httpx.get(f"{base.rstrip('/')}/dados/{rel}", timeout=30, headers={"User-Agent": "orgatec-boletim-sombra", "Cache-Control": "no-cache"})
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, ValueError):
            return {}
    return {"atual": baixar("campo/atual.json"), "noticias": baixar("agro/noticias.json"), "historico": baixar("agro/historico.json")}


def texto(res: dict) -> str:
    linhas = ["### Sombra do boletim: " + ("FORMATO DIFERENTE" if res["falhas"] else "mesmo formato do que está no ar")]
    linhas += [f"- FALHA: {f}" for f in res["falhas"]] + [f"- aviso: {a}" for a in res["avisos"]] + [f"- {k}: {v}" for k, v in res["info"].items()]
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ao-vivo", default=AO_VIVO)
    ap.add_argument("--dados", type=Path, default=DADOS)
    a = ap.parse_args(argv)
    if not a.ao_vivo.startswith("https://"):
        print("erro: --ao-vivo precisa começar com https://", file=sys.stderr)
        return 1
    res = comparar(_ler(a.dados), _baixar(a.ao_vivo))
    saida = texto(res)
    print(saida)
    resumo = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumo:
        with Path(resumo).open("a", encoding="utf-8") as f:
            f.write(saida + "\n")
    return 1 if res["falhas"] else 0


if __name__ == "__main__":
    sys.exit(main())
