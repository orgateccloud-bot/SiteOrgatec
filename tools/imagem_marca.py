"""Base comum das imagens geradas fora do navegador do visitante: o cartão da Janela de Campo para o status do
WhatsApp e os stories (tools/cartao_campo.py) e as imagens de compartilhamento das páginas
(tools/gerar_imagens_compartilhar.py).

Cores de design-system/orgatec-trilha/tokens.json (paleta Azul flutuante escuro, a padrão do site), fontes do próprio
site (site/assets/fontes, embutidas no HTML) e o logotipo original nas cores originais. Renderiza com o Playwright,
o mesmo que tools/gerar_logo.py e os testes e2e já usam. Tudo local: a página renderizada não contata a rede.
"""

from __future__ import annotations

import base64
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TOKENS = RAIZ / "design-system" / "orgatec-trilha" / "tokens.json"
FONTES = RAIZ / "site" / "assets" / "fontes"
LOGO = RAIZ / "site" / "assets" / "marca" / "orgatec-original.png"
PALETA = "azul-fl-esc"  # Azul flutuante escuro (PADRAO em tools/gerar_design_system.py)

# Família do estilo flutuante (paletas azul-fl*): Sora nos títulos, IBM Plex Sans no texto, IBM Plex Mono nos dados.
ARQUIVOS_FONTE = [("Sora", "sora.woff2", "500 700"), ("IBM Plex Sans", "ibm-plex-sans.woff2", "400 600"),
                  ("IBM Plex Mono", "ibm-plex-mono-500.woff2", "500")]


def cores(paleta: str = PALETA) -> dict[str, str]:
    """{token: valor} da paleta, lido de tokens.json (bg, surface, ink, muted, brand, warn...)."""
    t = json.loads(TOKENS.read_text(encoding="utf-8"))
    return {tk["name"]: tk["value"][paleta] for tk in t["color"]["tokens"]}


def _dados(arq: Path, tipo: str) -> str:
    return f"data:{tipo};base64,{base64.b64encode(arq.read_bytes()).decode('ascii')}"


def css_base(paleta: str = PALETA) -> str:
    """@font-face embutidos + variáveis de cor da paleta (--bg, --ink...) + reset da folha."""
    faces = "".join(f"@font-face{{font-family:'{nome}';font-weight:{peso};src:url({_dados(FONTES / arq, 'font/woff2')}) format('woff2')}}"
                    for nome, arq, peso in ARQUIVOS_FONTE)
    variaveis = ";".join(f"--{k}:{v}" for k, v in cores(paleta).items())
    return (faces + f":root{{{variaveis};--f-display:'Sora',sans-serif;--f-body:'IBM Plex Sans',sans-serif;--f-mono:'IBM Plex Mono',monospace}}"
            "*{box-sizing:border-box;margin:0;padding:0}html,body{background:var(--bg);color:var(--ink);font-family:var(--f-body);"
            "-webkit-font-smoothing:antialiased}")


def logo_img(altura: int) -> str:
    """Logotipo original (PNG transparente), sempre nas cores originais, em qualquer paleta."""
    return f'<img src="{_dados(LOGO, "image/png")}" alt="" style="height:{altura}px;width:auto;display:block">'


def documento(corpo: str, css: str, largura: int, altura: int) -> str:
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{css_base()}'
            f"body{{width:{largura}px;height:{altura}px;overflow:hidden}}{css}</style></head><body>{corpo}</body></html>")


def renderizar(itens: list[tuple[str, int, int, Path]]) -> None:
    """[(html, largura, altura, saída.png)] numa única instância do Chromium. A página fica sem rede: só data: URIs.
    Roda numa thread própria: a API síncrona do Playwright não abre numa thread que já tem laço asyncio (ex.: suíte e2e)."""
    with ThreadPoolExecutor(max_workers=1) as ex:
        ex.submit(_renderizar, itens).result()  # repassa a exceção da thread a quem chamou


def _renderizar(itens: list[tuple[str, int, int, Path]]) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        nav = p.chromium.launch()
        try:
            pg = nav.new_context(device_scale_factor=1, offline=True).new_page()
            for html, largura, altura, saida in itens:
                pg.set_viewport_size({"width": largura, "height": altura})
                pg.set_content(html, wait_until="load")
                pg.evaluate("document.fonts.ready.then(() => document.fonts.size)")  # fontes carregadas antes da foto
                saida.parent.mkdir(parents=True, exist_ok=True)
                tmp = saida.with_name(saida.stem + ".tmp.png")
                pg.screenshot(path=str(tmp), clip={"x": 0, "y": 0, "width": largura, "height": altura})
                tmp.replace(saida)  # troca atômica: quem abre o arquivo nunca vê um PNG pela metade
        finally:
            nav.close()
