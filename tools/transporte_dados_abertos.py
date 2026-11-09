"""Baixa os dados abertos usados pelos provedores reais da Central de Viagem (backend/transporte/provedores/reais.py).

  python tools/transporte_dados_abertos.py                 baixa o mês mais recente da ANP e as praças da ANTT
  python tools/transporte_dados_abertos.py --destino PASTA (padrão: backend/dados/transporte, fora do git)

Imprime as variáveis de ambiente para ligar os provedores. Só lê dados públicos (ANP: série histórica de preços de combustíveis;
ANTT: dados abertos de praças de pedágio, licença CC BY). Não envia nada a ninguém.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parents[1]
ANP_PAGINA = "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis"
ANTT = "https://dados.antt.gov.br/api/3/action/package_show?id=praca-de-pedagio"
AGENTE = {"User-Agent": "orgatec.io dados-abertos (contato: orgatec.cloud@gmail.com)"}


def _baixar(cliente: httpx.Client, url: str, destino: Path) -> bool:
    r = cliente.get(url, follow_redirects=True)
    if r.status_code != 200 or len(r.content) < 200:
        return False
    destino.write_bytes(r.content)
    return True


def mais_recente_diesel(html: str) -> str | None:
    """A ANP muda o nome dos arquivos de um ano para o outro; por isso o link é lido da página, não montado."""
    achados = {}
    for m in re.finditer(r"https://www\.gov\.br/anp/[^\"\s]*?/dsan/(\d{4})/([^\"\s/]*diesel[^\"\s/]*\.csv)", html):
        mes = re.search(r"(?<!\d)(\d{2})(?!\d)", m.group(2).replace("2026", "").replace("2025", "").replace("2024", "").replace("2023", ""))
        if mes:
            achados[(int(m.group(1)), int(mes.group(1)))] = m.group(0)
    return achados[max(achados)] if achados else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--destino", default=str(RAIZ / "backend" / "dados" / "transporte"))
    a = ap.parse_args(argv)
    pasta = Path(a.destino)
    pasta.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=60, headers=AGENTE) as c:
        anp = pasta / "anp-diesel.csv"
        url = mais_recente_diesel(c.get(ANP_PAGINA, follow_redirects=True).text)
        if not url or not _baixar(c, url, anp):
            print("ANP: não achei ou não consegui baixar o arquivo de diesel mais recente", file=sys.stderr)
            return 1
        print(f"ANP: {url.rsplit('/', 2)[-2]}/{url.rsplit('/', 1)[-1]} salvo em {anp}")
        meta = c.get(ANTT).json()
        csv_url = next(r["url"] for r in meta["result"]["resources"] if r.get("format", "").upper() == "CSV")
        antt = pasta / "antt-pracas.csv"
        if not _baixar(c, csv_url, antt):
            print("ANTT: não consegui baixar o CSV de praças", file=sys.stderr)
            return 1
        print(f"ANTT: salvo em {antt}")
    print("\nPara ligar:\n"
          f"  ORGATEC_TRANSPORTE_COMBUSTIVEL_REAL=1 ORGATEC_TRANSPORTE_ANP_ARQUIVO={anp}\n"
          f"  ORGATEC_TRANSPORTE_PEDAGIO_REAL=1 ORGATEC_TRANSPORTE_ANTT_ARQUIVO={antt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
