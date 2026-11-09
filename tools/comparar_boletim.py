"""Compara o boletim gerado no GitHub Actions com o que está no ar (fase "sombra" do boletim no Actions).

Só a estrutura decide o resultado: mesmo dia, mesmos polos, sem polo sem previsão a mais e todos os campos do painel.
Diferenças de previsão e de horário entre duas gerações são normais (a fonte atualiza) e só aparecem no relatório.

Uso:
    python tools/comparar_boletim.py AO_VIVO.json GERADO.json      imprime o relatório em Markdown; sai com 1 se a estrutura divergir
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

CAMPOS = ("id", "dia", "geradoEm", "resumo", "semDados", "regioes", "proximos", "tendencia", "criterios", "polos",
          "confianca", "fontes")


def _ids(boletim: dict) -> list[str]:
    return [p.get("id") for p in boletim.get("polos", [])]


def comparar(ao_vivo: dict, gerado: dict) -> tuple[list[str], list[str]]:
    """Devolve (problemas estruturais, observações). Sem problemas = a geração no Actions equivale à do Windows."""
    problemas: list[str] = []
    notas: list[str] = []
    faltam = [c for c in CAMPOS if c not in gerado]
    if faltam:
        problemas.append("campos ausentes no boletim gerado: " + ", ".join(faltam))
    if ao_vivo.get("dia") != gerado.get("dia"):
        problemas.append(f"dia diferente: no ar {ao_vivo.get('dia')}, gerado {gerado.get('dia')}")
    iv, ig = _ids(ao_vivo), _ids(gerado)
    if sorted(iv) != sorted(ig):
        problemas.append("polos diferentes: só no ar " + str(sorted(set(iv) - set(ig))) +
                         ", só no gerado " + str(sorted(set(ig) - set(iv))))
    sem = len(gerado.get("semDados", []))
    sem_vivo = len(ao_vivo.get("semDados", []))
    if sem > sem_vivo:
        problemas.append(f"polos sem previsão: {sem} no gerado contra {sem_vivo} no ar")
    try:
        d = abs((datetime.fromisoformat(gerado["geradoEm"]) - datetime.fromisoformat(ao_vivo["geradoEm"])).total_seconds()) / 60
        notas.append(f"horário de geração: {d:.0f} min de diferença entre as duas versões")
    except (KeyError, ValueError):
        notas.append("horário de geração não comparável")
    notas.append("resumo igual" if ao_vivo.get("resumo") == gerado.get("resumo") else "resumo diferente (normal: a previsão da fonte muda)")
    notas.append(f"alerta: no ar {ao_vivo.get('alerta')!r}, gerado {gerado.get('alerta')!r}")
    return problemas, notas


def relatorio(problemas: list[str], notas: list[str]) -> str:
    topo = "### Comparação com o boletim no ar (fase sombra, não publicado)\n"
    if problemas:
        return topo + "- **Estrutura divergente:**\n" + "\n".join(f"  - {p}" for p in problemas) + "\n" + \
            "\n".join(f"- {n}" for n in notas) + "\n"
    return topo + "- Estrutura equivalente à do boletim no ar\n" + "\n".join(f"- {n}" for n in notas) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    ao_vivo, gerado = (json.loads(Path(a).read_text(encoding="utf-8")) for a in args)
    problemas, notas = comparar(ao_vivo, gerado)
    print(relatorio(problemas, notas))
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
