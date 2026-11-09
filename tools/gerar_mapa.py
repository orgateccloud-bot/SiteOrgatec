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
import shutil
import subprocess  # nosec B404 — só executa git com argumentos fixos
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape  # nosec B406 - só escapa texto ao escrever o sitemap; não lê XML

RAIZ = Path(__file__).resolve().parent.parent
SITE = RAIZ / "site"
CANONICAL = re.compile(r'<link rel="canonical" href="([^"]+)"')
NOINDEX = re.compile(r'<meta name="robots" content="noindex', re.I)


def data_da_pagina(arquivo: Path) -> str:
    """Data do último commit da página: regerar o site muda a data do arquivo, mesmo com o conteúdo igual."""
    git = shutil.which("git")
    if git:
        r = subprocess.run([git, "log", "-1", "--format=%cs", "--", str(arquivo)], cwd=RAIZ, capture_output=True, text=True, check=False)  # nosec B603
        if r.stdout.strip():
            return r.stdout.strip()
    return datetime.fromtimestamp(arquivo.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")


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
        saida.append((canonico.group(1), data_da_pagina(arquivo)))
    saida.sort(key=lambda p: (p[0].split("://", 1)[1].rstrip("/").count("/"), p[0]))  # raiz, páginas da raiz, depois seções
    return saida


def main(destino: Path = SITE / "sitemap.xml") -> None:
    lista = paginas()
    urls = "\n".join(f"  <url><loc>{escape(u)}</loc><lastmod>{d}</lastmod></url>" for u, d in lista)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Gerado por tools/gerar_mapa.py. Não edite à mão. -->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""
    destino.write_text(xml, encoding="utf-8", newline="\n")
    print(f"gerado: {destino.name} ({len(lista)} páginas)")
    robots(destino.parent / "robots.txt")


def robots(destino: Path = SITE / "robots.txt") -> None:
    """robots.txt com a linha Sitemap. Libera o rastreio: quem impede a indexação, enquanto o site está em homologação,
    é o cabeçalho X-Robots-Tag (noindex), que o buscador só lê se puder abrir a página. O noindex sai na virada (T9)."""
    destino.write_text("# Gerado por tools/gerar_mapa.py. Não edite à mão.\nUser-agent: *\nAllow: /\n\nSitemap: https://orgatec.io/sitemap.xml\n",
                       encoding="utf-8", newline="\n")
    print(f"gerado: {destino.name}")


if __name__ == "__main__":
    main()
