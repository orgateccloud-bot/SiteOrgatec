"""Baixa as fontes do site uma vez e grava em site/assets/fontes/ (pendência T4).

Com as fontes servidas pelo próprio domínio, o navegador do visitante não contata o Google
(fonts.googleapis.com / fonts.gstatic.com), e a CSP deixa de liberar esses dois hosts.

Uso: python tools/baixar_fontes.py   (só é preciso rodar de novo se mudar a lista FAMILIAS)
Saída: site/assets/fontes/*.woff2 e site/assets/fontes/fontes.css (com @font-face locais).
Só o subconjunto "latin" é baixado: cobre o português (ç, ã, é, º, ª, €, aspas e travessões).
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "site" / "assets" / "fontes"

# Design ORGATEC Trilha (páginas do site) + Inter e JetBrains Mono (marca.html e orgatec-template2.html).
FAMILIAS = {
    "Bricolage Grotesque": "500;700;800",
    "Sora": "500;600;700",
    "Source Sans 3": "400;600;700",
    "IBM Plex Sans": "400;500;600",
    "IBM Plex Mono": "400;500",
    "Inter": "400;500;600;700;800",
    "JetBrains Mono": "400;600",
}
API = "https://fonts.googleapis.com/css2?{familias}&display=swap"
# O Google só entrega woff2 a navegadores que o aceitam; sem isso, devolve TTF.
AGENTE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def baixar(url: str) -> bytes:
    if not url.startswith(("https://fonts.googleapis.com/", "https://fonts.gstatic.com/")):
        raise SystemExit(f"endereço fora do Google Fonts: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=30) as r:  # nosec B310 - só https do Google Fonts (checado acima)
        return r.read()


def nome_arquivo(familia: str, peso: str, estilo: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", familia.lower()).strip("-")
    return f"{base}-{peso}{'-italico' if estilo == 'italic' else ''}.woff2"


def main() -> None:
    familias = "&".join(f"family={f.replace(' ', '+')}:wght@{p}" for f, p in FAMILIAS.items())
    css = baixar(API.format(familias=familias)).decode("utf-8")
    # Cada bloco vem precedido de um comentário com o subconjunto: /* latin */ @font-face { ... }
    blocos = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", css)
    latin = []
    for subconjunto, bloco in blocos:
        if subconjunto == "latin":
            latin.append((bloco, re.search(r"font-family:\s*'([^']+)'", bloco).group(1),
                          re.search(r"font-weight:\s*(\d+)", bloco).group(1),
                          re.search(r"font-style:\s*(\w+)", bloco).group(1),
                          re.search(r"url\((https://[^)]+)\)", bloco).group(1)))
    # Fonte variável: o Google usa o mesmo arquivo para todos os pesos; aí o nome não leva o peso.
    urls_por_familia: dict[str, set[str]] = {}
    for _, familia, _, _, url in latin:
        urls_por_familia.setdefault(familia, set()).add(url)
    DESTINO.mkdir(parents=True, exist_ok=True)
    for antigo in DESTINO.glob("*.woff2"):
        antigo.unlink()
    saida, baixados = [], {}
    for bloco, familia, peso, estilo, url in latin:
        if url not in baixados:
            variavel = len(urls_por_familia[familia]) == 1
            arquivo = nome_arquivo(familia, "" if variavel else peso, estilo).replace("-.woff2", ".woff2")
            (DESTINO / arquivo).write_bytes(baixar(url))
            baixados[url] = arquivo
        saida.append(bloco.replace(url, baixados[url]))
    if len(saida) < sum(len(p.split(";")) for p in FAMILIAS.values()):
        raise SystemExit(f"esperava um bloco latin por peso; vieram {len(saida)}")
    cabecalho = ("/* Gerado por tools/baixar_fontes.py a partir do Google Fonts (licença SIL Open Font License 1.1).\n"
                 "   Servido pelo próprio site: o navegador do visitante não contata o Google. Não edite à mão. */\n")
    (DESTINO / "fontes.css").write_text(cabecalho + "\n".join(saida) + "\n", encoding="utf-8", newline="\n")
    total = sum((DESTINO / a).stat().st_size for a in set(baixados.values()))
    print(f"fontes: {len(saida)} @font-face, {len(set(baixados.values()))} arquivos, {total // 1024} KB em {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
