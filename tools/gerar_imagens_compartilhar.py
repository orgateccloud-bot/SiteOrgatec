"""Imagens de compartilhamento por página (og:image 1200 × 630; pedido S3 do marketing, 02/11/2026): o link enviado no
WhatsApp mostra o assunto da página em vez da imagem geral da marca (assets/marca/og-image.png).

Páginas com imagem própria: a Central da Reforma, a página "Compliance por público" e cada página de público pronta
(PUBLICOS e PUBLICOS_PRONTOS em tools/paginas_compliance.py, fonte única dos nomes e textos dos públicos).
Cores de design-system/orgatec-trilha/tokens.json e fontes do site (tools/imagem_marca.py). As imagens não mudam o
visual das páginas: só o <head> passa a apontar para elas (layout.head, via imagem_de).

Uso (antes de tools/gerar_paginas.py, que só aponta para a imagem que já existe):
    python tools/gerar_imagens_compartilhar.py
"""

from __future__ import annotations

from html import escape

import imagem_marca as M

SITE = M.RAIZ / "site"
PASTA = "assets/compartilhar"
LARGURA, ALTURA = 1200, 630

# Páginas além das de público: (caminho, sobre, título, texto)
EXTRAS = [
    ("reforma/index.html", "Reforma tributária", "Central da Reforma",
     "O que já vale, o que vem e o que falta regulamentar, com a fonte oficial e a data de consulta de cada ponto."),
    ("compliance/publicos.html", "Compliance", "Compliance por público",
     "O que cada público precisa cumprir: transportador, produtor rural, MEI, autônomo, Simples, serviços, comércio e indústria e imóveis."),
]

CSS = """
.c{height:100%;display:flex;flex-direction:column;justify-content:space-between;padding:56px 80px 52px;
  background:radial-gradient(760px 520px at 100% 0,var(--brand-soft),transparent 70%),var(--bg)}
.topo{display:flex;align-items:center;gap:18px}
.marca{font:800 34px/1 var(--f-display);letter-spacing:-.02em}
.sub{font:500 13px/1 var(--f-mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-top:8px}
.sobre{display:flex;align-items:center;gap:14px;font:500 20px/1 var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--hl)}
.sobre i{display:block;width:40px;height:4px;border-radius:2px;background:var(--hl)}
h1{font-family:var(--f-display);font-weight:700;letter-spacing:-.03em;line-height:1.04;margin-top:18px;max-width:1040px}
.texto{font:400 27px/1.38 var(--f-body);color:var(--muted);margin-top:18px;max-width:1000px}
.pe{font:500 20px/1 var(--f-mono);color:var(--brand)}
"""


def arquivo(caminho: str) -> str:
    """Imagem de uma página, a partir da raiz do site: compliance/publico/mei.html → assets/compartilhar/compliance-publico-mei.png."""
    return f"{PASTA}/{caminho.removesuffix('.html').replace('/', '-')}.png"


def imagem_de(caminho: str) -> str | None:
    """A imagem própria da página, se já foi gerada; senão None (a página fica com a og-image.png geral)."""
    rel = arquivo(caminho)
    return rel if (SITE / rel).is_file() else None


def paginas() -> list[dict]:
    import paginas_compliance as pc  # tardio: paginas_compliance importa gerar_paginas, que importa este módulo

    itens = [{"caminho": c, "sobre": s, "titulo": t, "texto": x} for c, s, t, x in EXTRAS]
    itens += [{"caminho": f"compliance/publico/{arq}", "sobre": "Compliance · Por público", "titulo": titulo, "texto": texto}
              for chave, arq, titulo, texto in pc.PUBLICOS if chave in pc.PUBLICOS_PRONTOS]
    return itens


def montar_html(item: dict) -> str:
    n = len(item["titulo"])
    tamanho = 96 if n <= 16 else 72 if n <= 24 else 62
    corpo = f"""<main class="c">
<header class="topo">{M.logo_img(66)}<div><p class="marca">ORGATEC</p><p class="sub">Inteligência Tributária</p></div></header>
<section><p class="sobre"><i></i>{escape(item["sobre"])}</p><h1 style="font-size:{tamanho}px">{escape(item["titulo"])}</h1>
<p class="texto">{escape(item["texto"])}</p></section>
<footer class="pe">orgatec.io</footer>
</main>"""
    return M.documento(corpo, CSS, LARGURA, ALTURA)


def gerar() -> list[str]:
    itens = paginas()
    M.renderizar([(montar_html(i), LARGURA, ALTURA, SITE / arquivo(i["caminho"])) for i in itens])
    return [arquivo(i["caminho"]) for i in itens]


if __name__ == "__main__":
    for rel in gerar():
        print("OK", rel)
