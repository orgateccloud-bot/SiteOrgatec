"""Restaura em site/dados/ o histórico que já está no ar (protótipo do boletim no GitHub Actions).

`site/dados/` fica fora do git e é regravado três vezes ao dia. Um runner novo começa sem ele, e a publicação do
Hosting troca o site inteiro: sem este passo, cada execução apagaria os boletins anteriores e perderia o boletim do dia
que o gerador compara para marcar o que mudou. O que é restaurado:

    dados/campo/indice.json e os boletins que ele lista (os 30 dias mais recentes)
    dados/campo/atual.json
    dados/agro/noticias.json

Boletins mais antigos que os 30 do índice não têm como ser listados pela web e não voltam.

Uso:
    python tools/restaurar_dados_do_site.py                  restaura de https://orgatec.io em site/dados
    python tools/restaurar_dados_do_site.py --base URL       outro site (só https)

O conteúdo vem da rede: nomes de arquivo só são aceitos no formato boletim-AAAA-MM-DD.json, e todo arquivo precisa ser
um JSON válido antes de ser gravado.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parent.parent
BASE = "https://orgatec.io"
DESTINO = RAIZ / "site" / "dados"
FIXOS = ("campo/indice.json", "campo/atual.json", "agro/noticias.json")
NOME_BOLETIM = re.compile(r"^boletim-\d{4}-\d{2}-\d{2}\.json$")
USER_AGENT = "orgatec-boletim-actions"


def nomes_do_indice(indice: dict) -> list[str]:
    """Arquivos de boletim listados no índice, sem repetição e só com nome no formato esperado."""
    saida: list[str] = []
    for item in indice.get("boletins", []):
        nome = item.get("arquivo") if isinstance(item, dict) else None
        if isinstance(nome, str) and NOME_BOLETIM.match(nome) and f"campo/{nome}" not in saida:
            saida.append(f"campo/{nome}")
    return saida


def _baixar(cliente: httpx.Client, base: str, caminho: str) -> dict:
    r = cliente.get(f"{base}/dados/{caminho}", timeout=30)
    r.raise_for_status()
    return r.json()


def restaurar(base: str = BASE, destino: Path = DESTINO, cliente: httpx.Client | None = None) -> list[str]:
    """Baixa e grava os arquivos. Devolve os caminhos restaurados. Falha se o índice ou o boletim atual não vierem."""
    if not base.startswith("https://"):
        raise ValueError("a base precisa começar com https://")
    base = base.rstrip("/")
    proprio = cliente is None
    cliente = cliente or httpx.Client(headers={"User-Agent": USER_AGENT})
    feitos: list[str] = []
    try:
        indice = _baixar(cliente, base, "campo/indice.json")
        caminhos = list(FIXOS) + nomes_do_indice(indice)
        for caminho in dict.fromkeys(caminhos):
            try:
                conteudo = indice if caminho == "campo/indice.json" else _baixar(cliente, base, caminho)
            except (httpx.HTTPError, ValueError) as erro:
                if caminho in ("campo/indice.json", "campo/atual.json"):
                    raise RuntimeError(f"não foi possível restaurar {caminho}: {erro}") from erro
                print(f"aviso: {caminho} não restaurado ({erro})", file=sys.stderr)
                continue
            alvo = destino / caminho
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text(json.dumps(conteudo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            feitos.append(caminho)
    finally:
        if proprio:
            cliente.close()
    return feitos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default=BASE, help="endereço do site (só https)")
    a = ap.parse_args(argv)
    try:
        feitos = restaurar(a.base)
    except (RuntimeError, ValueError, httpx.HTTPError) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1
    print(f"restaurados {len(feitos)} arquivos em {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
