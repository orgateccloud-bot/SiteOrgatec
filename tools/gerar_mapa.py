"""Gera site/sitemap.xml (mapa do site para buscadores) a partir das páginas que estão em site/.

Uso:  python tools/gerar_mapa.py

- Entra toda página .html com <link rel="canonical">, exceto as marcadas com <meta name="robots" content="noindex">
  (painel de testes, manual da marca e páginas de design system).
- O endereço publicado é o do canonical (https://orgatec.io/...); a data é a da última gravação do arquivo.
- Rode depois de gerar as páginas (gerar_paginas.py, gerar_hub.py). Enquanto o site estiver em homologação,
  os buscadores continuam bloqueados pelo cabeçalho X-Robots-Tag (backend/app.py e firebase.json).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape  # nosec B406 - só escapa texto ao escrever o sitemap; não lê XML

RAIZ = Path(__file__).resolve().parent.parent
SITE = RAIZ / "site"
CANONICAL = re.compile(r'<link rel="canonical" href="([^"]+)"')
NOINDEX = re.compile(r'<meta name="robots" content="noindex', re.I)


def paginas() -> list[tuple[str, str]]:
    """[(endereço canônico, AAAA-MM-DD)] das páginas indexáveis, a raiz primeiro e o resto em ordem alfabética."""
    saida = []
    for arquivo in sorted(SITE.rglob("*.html")):
        if "assets" in arquivo.relative_to(SITE).parts:
            continue
        html = arquivo.read_text(encoding="utf-8")
        canonico = CANONICAL.search(html)
        if not canonico or NOINDEX.search(html):
            continue
        data = datetime.fromtimestamp(arquivo.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
        saida.append((canonico.group(1), data))
    saida.sort(key=lambda p: (p[0].split("://", 1)[1].rstrip("/").count("/"), p[0]))  # raiz, páginas da raiz, depois seções
    return saida


def main() -> None:
    lista = paginas()
    urls = "\n".join(f"  <url><loc>{escape(u)}</loc><lastmod>{d}</lastmod></url>" for u, d in lista)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Gerado por tools/gerar_mapa.py. Não edite à mão. -->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""
    (SITE / "sitemap.xml").write_text(xml, encoding="utf-8", newline="\n")
    print(f"gerado: site/sitemap.xml ({len(lista)} páginas)")


if __name__ == "__main__":
    main()
