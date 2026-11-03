"""Gera o design system "ORGATEC Trilha": o design do projeto Trilha com o nome trocado para ORGATEC.

Fonte: D:\\01_Projetos_Ativos\\Trilha\\DESIGN-SYSTEM.md (texto) e trilha.html (PRESETS e applyTheme, os
valores de verdade). Saídas:
  design-system/orgatec-trilha/DESIGN-SYSTEM.md   documento adaptado
  design-system/orgatec-trilha/tokens.json        7 paletas no formato do design system (cores derivadas como no applyTheme)
  site/orgatec-trilha.html                        demonstração com seletor de cores e estilo flutuante

Uso:  python design-system/gerar_trilha.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = Path(r"D:\01_Projetos_Ativos\Trilha\DESIGN-SYSTEM.md")
SAIDA = RAIZ / "design-system" / "orgatec-trilha"
PAGINA = RAIZ / "site" / "orgatec-trilha.html"
e = html.escape


def externalizar_script(pagina: str, destino: Path, src: str) -> str:
    """Grava o script embutido da página num arquivo e troca por <script src> (a CSP do site não permite script embutido)."""
    ini = pagina.rindex("<script>\n")
    fim = pagina.index("</script>", ini)
    destino.write_text("/* Gerado junto com a página. Não edite à mão. */\n" + pagina[ini + len("<script>\n"):fim].strip() + "\n",
                       encoding="utf-8", newline="\n")
    return pagina[:ini] + f'<script src="{src}"></script>' + pagina[fim + len("</script>"):]

# trilha.html, const PRESETS (31/10/2026). 'auto' segue o sistema: Verde no claro, Noturno no escuro.
PRESETS = [
    dict(id="verde", nome="Verde Toga", p="#1F4D40", h="#F2C14E", ink="#18211E", a="#9A5212", s="#DCE7E1", bg="#F3F5F2"),
    dict(id="azul", nome="Azul Tribunal", p="#1D3F6E", h="#F5C451", ink="#131A26", a="#A4471C", s="#DDE5F0", bg="#F2F4F7"),
    dict(id="vinho", nome="Vinho Toga", p="#6B1E2E", h="#F0C04A", ink="#1E1416", a="#8A5A10", s="#EEDFE2", bg="#F6F2F2"),
    dict(id="ciano", nome="Grafite e Ciano", p="#155E6B", h="#F4D35E", ink="#161B1E", a="#9B4A12", s="#D9ECEF", bg="#F2F5F6"),
    dict(id="noite", nome="Noturno", p="#8FC7B2", h="#F2C14E", ink="#E6ECE8", a="#E3A961", s="#22322C", bg="#111916"),
    dict(id="azul-fl", nome="Azul flutuante", p="#1D5FD6", h="#4B8FE0", ink="#0C1A33", a="#B03A0A", s="#E3ECFB", bg="#EAF1FB", fl=1),
    dict(id="azul-fl-esc", nome="Azul flutuante escuro", p="#6EA8FF", h="#9CC3FF", ink="#E6EEFB", a="#FF8A4C", s="#12233F", bg="#08111F", fl=1),
]
FOCO = {"claro": "#2B6CB0", "escuro": "#7FB3F2", "azul-fl-esc": "#9CC3FF"}  # :root, tema escuro e inicio.html


def hx(c):
    n = int(c[1:], 16)
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255]


def mx(a, b, t):  # trilha.html: const mx
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(hx(a), hx(b)))


def lum(c):  # trilha.html: const lum
    v = [x / 255 for x in hx(c)]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def derivar(p):
    """Mesma derivação do applyTheme do Trilha."""
    escuro = lum(p["bg"]) < 0.2
    return {
        "bg": p["bg"], "surface": mx(p["bg"], "#FFFFFF", 0.06) if escuro else "#FFFFFF", "surface2": mx(p["bg"], p["ink"], 0.07),
        "ink": p["ink"], "muted": mx(p["ink"], p["bg"], 0.36), "line": mx(p["bg"], p["ink"], 0.16),
        "brand": p["p"], "brand-ink": "#18211E" if lum(p["p"]) > 0.35 else "#F3F5F2", "brand-soft": p["s"],
        "hl": p["h"], "hl-ink": "#06142b" if p.get("fl") else "#18211E", "hl-soft": mx(p["bg"], p["h"], 0.22 if escuro else 0.3),
        "warn": p["a"], "warn-soft": mx(p["bg"], p["a"], 0.16),
        "focus": FOCO.get(p["id"], FOCO["escuro"] if escuro else FOCO["claro"]),
    }


USOS = {
    "bg": "Fundo da página.", "surface": "Cartões.", "surface2": "Áreas internas de cartões.",
    "ink": "Texto principal, sobre bg e surface (contraste ≥ 4,5:1).", "muted": "Texto secundário e legendas, sobre bg e surface.",
    "line": "Bordas de 1 px.", "brand": "Títulos, links, aba ativa, bloco de teoria.", "brand-ink": "Texto sobre brand.",
    "brand-soft": "Etiquetas neutras e fundo de ícone.", "hl": "Marca-texto: hoje, meta, concluído, botão principal. Só marca; nunca texto corrido nem área grande.",
    "hl-ink": "Texto sobre hl.", "hl-soft": "Fundo de bloco concluído e do dia de hoje.", "warn": "Âmbar de prazo: só alerta.",
    "warn-soft": "Fundo de aviso.", "focus": "Anel de foco e bloco de áudio.",
}


# Paletas com tokens completos escritos à mão no Trilha (":root" e tema escuro de trilha.html; inicio.html para o
# Azul flutuante escuro), conforme a seção "Tokens completos" do documento. Prevalecem sobre a derivação.
TOKENS_COMPLETOS = {
    "verde": {"bg": "#F3F5F2", "surface": "#FFFFFF", "surface2": "#E9EEEA", "ink": "#18211E", "muted": "#4F5C56", "line": "#D5DDD8",
              "brand": "#1F4D40", "brand-ink": "#F3F5F2", "brand-soft": "#DCE7E1", "hl": "#F2C14E", "hl-ink": "#18211E", "hl-soft": "#FBEFC9",
              "warn": "#9A5212", "warn-soft": "#F6E6D3", "focus": "#2B6CB0"},
    "noite": {"bg": "#111916", "surface": "#18221E", "surface2": "#1F2B26", "ink": "#E6ECE8", "muted": "#9AA8A1", "line": "#2C3833",
              "brand": "#8FC7B2", "brand-ink": "#111916", "brand-soft": "#1F3029", "hl": "#F2C14E", "hl-ink": "#18211E", "hl-soft": "#3A3218",
              "warn": "#E3A961", "warn-soft": "#33281A", "focus": "#7FB3F2"},
    "azul-fl-esc": {"bg": "#08111F", "surface": "#171F2C", "surface2": "#1D2737", "ink": "#E6EEFB", "muted": "#969EAC", "line": "#2B3442",
                    "brand": "#6EA8FF", "brand-ink": "#08111F", "brand-soft": "#12233F", "hl": "#9CC3FF", "hl-ink": "#06142B", "hl-soft": "#293850",
                    "warn": "#FF8A4C", "warn-soft": "#302426", "focus": "#9CC3FF"},
}


def gerar_tokens():
    temas = [{"id": p["id"], "name": p["nome"]} for p in PRESETS]
    vals = {p["id"]: TOKENS_COMPLETOS.get(p["id"]) or derivar(p) for p in PRESETS}
    tokens = [{"name": k, "value": {t: vals[t][k] for t in vals}, "usage": USOS[k]} for k in USOS]
    dados = {
        "name": "ORGATEC Trilha", "version": 1,
        "meta": {"source": "Projeto Trilha: DESIGN-SYSTEM.md e trilha.html (PRESETS, applyTheme), 31/10/2026; nome trocado para ORGATEC", "nota": "Verde, Noturno e Azul flutuante escuro usam os tokens completos do documento; as demais paletas usam a derivação do applyTheme."},
        "color": {"themes": temas, "tokens": tokens},
        "type": {"fonts": [], "families": {
            "display": "\"Bricolage Grotesque\", \"Segoe UI\", system-ui, sans-serif",
            "body": "\"Source Sans 3\", \"Segoe UI\", system-ui, sans-serif",
            "display-flutuante": "Sora, \"Segoe UI\", system-ui, sans-serif",
            "body-flutuante": "\"IBM Plex Sans\", \"Segoe UI\", system-ui, sans-serif",
            "mono": "\"IBM Plex Mono\", ui-monospace, Consolas, monospace"},
            "groups": [
                {"name": "Títulos", "family": "display", "styles": [
                    {"name": "assinatura", "fontSize": "24px", "lineHeight": 1, "fontWeight": 800, "letterSpacing": "-0.03em", "sample": "ORGATEC", "usage": "Nome ao lado do símbolo."},
                    {"name": "titulo-grande", "fontSize": "44px", "lineHeight": 1.05, "fontWeight": 800, "letterSpacing": "-0.035em", "sample": "Reforma tributária, passo a passo", "usage": "Herói."},
                    {"name": "kpi", "fontSize": "30px", "lineHeight": 1.1, "fontWeight": 700, "sample": "27 de 31", "usage": "Valor de cartão de indicador."}]},
                {"name": "Texto", "family": "body", "styles": [
                    {"name": "corpo", "fontSize": "16px", "lineHeight": 1.55, "fontWeight": 400, "sample": "O próximo passo aparece antes do detalhe.", "usage": "Corpo, botões e formulários; leitura de 65–70 caracteres."}]},
                {"name": "Dados", "family": "mono", "styles": [
                    {"name": "eyebrow", "fontSize": "12px", "lineHeight": "16px", "fontWeight": 500, "letterSpacing": "0.08em", "sample": "PRÓXIMO PASSO", "usage": "Rótulo de seção, caixa alta, cor hl (flutuante) ou muted."},
                    {"name": "dado", "fontSize": "14px", "lineHeight": "20px", "fontWeight": 400, "sample": "LC 214/2025, art. 41", "usage": "Artigos de lei, datas e horários."}]}]},
        "radius": {"note": "6–10 px no clássico, 14 px no flutuante; pílula em botões da página inicial.", "tokens": [
            {"name": "r-classico", "value": "10px", "usage": "Cartões e botões no estilo clássico."},
            {"name": "r-flutuante", "value": "14px", "usage": "Cartões no estilo flutuante."},
            {"name": "r-pilula", "value": "999px", "usage": "Botões da página inicial, cabeçalho de vidro, toast."}]},
        "shadow": {"note": "Só no estilo flutuante; o clássico não usa sombra.", "tokens": [
            {"name": "sombra-flutuante", "value": {**{p["id"]: "none" for p in PRESETS},
                                                   "azul-fl": "0 1px 2px rgba(15,40,90,.06), 0 8px 24px -8px rgba(15,40,90,.16)",
                                                   "azul-fl-esc": "0 1px 2px rgba(0,0,0,.4), 0 10px 28px -10px rgba(0,0,0,.6)"}, "usage": "Cartões no estilo flutuante."}]},
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "tokens.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def gerar_documento():
    t = ORIGEM.read_text(encoding="utf-8")
    troca = [
        ("# Trilhum · design system\n\nIdentidade visual e regras de interface do Trilhum: app (`trilha.html`), página inicial (`inicio.html`),\naviso de privacidade (`privacidade.html`) e materiais de estudo da mesma família (Quadro, Placar).\nVersão de 31/10/2026. A fonte da verdade dos valores é o código; este documento descreve e explica.",
         "# ORGATEC Trilha · design system\n\nAdaptação do design system do projeto Trilha (DESIGN-SYSTEM.md de 31/10/2026) com o nome trocado para\n**ORGATEC**. Gerado por `design-system/gerar_trilha.py`; os valores das paletas vêm do código do Trilha\n(`PRESETS` e `applyTheme` em `trilha.html`) e estão em `design-system/orgatec-trilha/tokens.json`.\nDemonstração: `site/orgatec-trilha.html`. Este design ainda **não** está aplicado ao site: a escolha entre\nele e o `orgatec-template2` é a pendência D6 do painel de testes."),
        ("**Trilhum** (marca visível). Internamente o código ainda usa `trilha` (pasta, chaves `trilha.*` do\nnavegador, funções `trilha_sync_*`): isso é intencional e não aparece para a pessoa.",
         "**ORGATEC**, sempre em maiúsculas (regra da marca de 30/10/2026). No código do modelo original, os nomes\ninternos `trilha.*` continuam; eles não aparecem para a pessoa."),
        ('<svg viewBox="0 0 64 64" role="img" aria-label="Trilhum">', '<svg viewBox="0 0 64 64" role="img" aria-label="ORGATEC">'),
        ("- Tamanho mínimo: **20 px**.",
         "- Na ORGATEC já existe um símbolo oficial: a esfera de quatro faixas (`site/assets/marca/orgatec-original.png`, extraído da imagem original por `tools/extrair_logo_original.py`).\n  Decisão de 31/10/2026: com este design, a ORGATEC usa o logotipo original, sempre com as cores originais,\n  inclusive nas paletas escuras. O símbolo do modelo Trilha fica só como referência.\n- Tamanho mínimo: **20 px**."),
        ("Símbolo + palavra **trilhum** em minúsculas, fonte de títulos peso 800, `letter-spacing: -.03em`.",
         "Símbolo + palavra **ORGATEC** em maiúsculas (o modelo original usava minúsculas), fonte de títulos peso 800, `letter-spacing: -.03em`."),
        ('"Desenvolvido por Warley Moreira Veloso", junto da versão. Materiais de estudo **não** levam logo nem nome\nda ORGATEC. Nunca creditar ferramentas de IA.',
         '"Desenvolvido por Warley Moreira Veloso", junto da versão. Nunca creditar ferramentas de IA.\nNo modelo original, materiais de estudo não levavam o nome da ORGATEC; nesta adaptação o design passa a ser\nda ORGATEC, e o rodapé segue a regra do site (CNPJ, responsável técnico com CRC, LGPD, NBC PG 01).'),
    ]
    for a, b in troca:
        if a not in t:
            raise SystemExit(f"trecho não encontrado no documento de origem: {a[:60]!r}")
        t = t.replace(a, b)
    t = t.replace("Trilhum", "ORGATEC")
    ini = t.index("## 13. Onde está no código")
    t = t[:ini] + """## 13. Onde está no código

| O quê | Arquivo |
|---|---|
| Paletas, tokens e documento adaptado | `design-system/orgatec-trilha/` (gerado por `design-system/gerar_trilha.py`) |
| Demonstração com seletor de cores | `site/orgatec-trilha.html` |
| Código de origem (referência) | `D:\\01_Projetos_Ativos\\Trilha\\trilha.html` (`PRESETS`, `applyTheme`) e `inicio.html` |
| Design atual do site, para comparar | `design-system/orgatec-template2/` e `site/orgatec-template2.html` |
"""
    (SAIDA / "DESIGN-SYSTEM.md").write_text(t, encoding="utf-8", newline="\n")
    if "rilhum" in t:
        raise SystemExit("ainda há 'Trilhum' no documento adaptado")


ICONES = {  # traço 2 px, pontas arredondadas, currentColor
    "book": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/>',
    "pen": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "audio": '<path d="M3 14v-2a9 9 0 0 1 18 0v2"/><path d="M21 15a2 2 0 0 1-2 2h-1v-5h3zM3 15a2 2 0 0 0 2 2h1v-5H3z"/>',
    "video": '<rect x="2" y="5" width="15" height="14" rx="2"/><path d="m17 10 5-3v10l-5-3"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
    "flag": '<path d="M4 22V4"/><path d="M4 4h12l-2 4 2 4H4"/>',
    "check": '<path d="m5 12 5 5L20 7"/>',
    "palette": '<circle cx="12" cy="12" r="9"/><circle cx="8" cy="10" r="1"/><circle cx="12" cy="7" r="1"/><circle cx="16" cy="10" r="1"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "cal": '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/>',
}


def ico(nome):
    return f'<svg class="ico" aria-hidden="true"><use href="#i-{nome}"/></svg>'


def gerar_pagina():
    sprite = "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{v}</symbol>' for k, v in ICONES.items())
    presets_js = json.dumps([{"id": "auto", "name": "Automático"}] + [{**{k: v for k, v in p.items() if k != "nome"}, "name": p["nome"]} for p in PRESETS], ensure_ascii=False)
    blocos = [("t", "Teoria / Lei seca", "book", "08:00", "LC 214/2025", "Livro I, Título IV: regimes diferenciados", False),
              ("l", "Leitura", "list", "09:30", "ADCT", "Arts. 125 a 129: transição", False),
              ("q", "Questões", "pen", "10:30", "Simples Nacional", "Opção pelo regime regular (art. 41)", False),
              ("a", "Áudio", "audio", "12:00", "Split payment", "Resumo em áudio", False),
              ("x", "Videoaula", "video", "14:00", "Produtor rural", "Arts. 164 a 168", False),
              ("v", "Revisão", "refresh", "16:00", "CBS e IBS", "Revisão da semana", True)]
    html_blocos = "".join(
        f'<article class="blk {c}{" done" if feito else ""}"><div class="blk-top"><span class="tipo">{ico(i)}{e(n)}</span>'
        f'<label class="feito"><input type="checkbox"{" checked" if feito else ""} aria-label="Feito: {e(d)}"> Feito?</label></div>'
        f'<span class="mono">{h}</span><strong>{e(d)}</strong><span class="muted">{e(tp)}</span></article>'
        for c, n, i, h, d, tp, feito in blocos)
    marcos = [("Cadastro", "feito"), ("Diagnóstico", "feito"), ("Plano", "atual"), ("Implantação", ""), ("2027", "")]
    html_marcos = "".join(f'<li class="marco {s}"><span class="bola">{ico("check") if s == "feito" else ""}</span><span>{e(n)}</span></li>' for n, s in marcos)

    pagina = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ORGATEC Trilha | Design system</title>
<meta name="description" content="Design system ORGATEC Trilha: 8 paletas, estilo flutuante, tipografia e componentes, adaptado do projeto Trilha.">
<meta name="robots" content="noindex">
<link rel="stylesheet" href="assets/fontes/fontes.css">
<!-- Gerado por design-system/gerar_trilha.py. Não edite à mão. -->
<style>
/* Tokens do Trilha (Verde Toga no claro, Noturno no escuro); o seletor aplica as outras paletas por variáveis inline, como no applyTheme. */
:root{{--bg:#F3F5F2;--surface:#FFFFFF;--surface2:#E9EEEA;--ink:#18211E;--muted:#4F5C56;--line:#D5DDD8;--brand:#1F4D40;--brand-ink:#F3F5F2;--brand-soft:#DCE7E1;
  --hl:#F2C14E;--hl-ink:#18211E;--hl-soft:#FBEFC9;--warn:#9A5212;--warn-soft:#F6E6D3;--focus:#2B6CB0;--r:10px;--shadow:none;--shadow-up:none;
  --f-display:"Bricolage Grotesque","Segoe UI",system-ui,sans-serif;--f-body:"Source Sans 3","Segoe UI",system-ui,sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,Consolas,monospace}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#111916;--surface:#18221E;--surface2:#1F2B26;--ink:#E6ECE8;--muted:#9AA8A1;--line:#2C3833;--brand:#8FC7B2;--brand-ink:#111916;--brand-soft:#1F3029;
  --hl:#F2C14E;--hl-ink:#18211E;--hl-soft:#3A3218;--warn:#E3A961;--warn-soft:#33281A;--focus:#7FB3F2;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#111916;--surface:#18221E;--surface2:#1F2B26;--ink:#E6ECE8;--muted:#9AA8A1;--line:#2C3833;--brand:#8FC7B2;--brand-ink:#111916;--brand-soft:#1F3029;
  --hl:#F2C14E;--hl-ink:#18211E;--hl-soft:#3A3218;--warn:#E3A961;--warn-soft:#33281A;--focus:#7FB3F2;color-scheme:dark}}
:root[data-float]{{--f-display:"Sora","Segoe UI",system-ui,sans-serif;--f-body:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;--r:14px;
  --shadow:0 1px 2px rgba(15,40,90,.06),0 8px 24px -8px rgba(15,40,90,.16);--shadow-up:0 2px 4px rgba(15,40,90,.08),0 18px 40px -12px rgba(29,95,214,.32);--glow1:rgba(59,130,246,.22);--glow2:rgba(14,165,233,.18)}}
:root[data-float="dark"]{{--shadow:0 1px 2px rgba(0,0,0,.4),0 10px 28px -10px rgba(0,0,0,.6);--shadow-up:0 2px 6px rgba(0,0,0,.45),0 20px 44px -12px rgba(59,130,246,.35);--glow1:rgba(59,130,246,.20);--glow2:rgba(14,165,233,.14)}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--f-body);-webkit-font-smoothing:antialiased}}
:root[data-float] body{{background-image:radial-gradient(900px 520px at 8% -6%,var(--glow1),transparent 60%),radial-gradient(760px 480px at 100% 18%,var(--glow2),transparent 60%);background-attachment:fixed}}
.ico{{width:20px;height:20px;flex:none}}
.wrap{{max-width:1120px;margin:0 auto;padding-inline:max(16px,env(safe-area-inset-left,0px)) max(16px,env(safe-area-inset-right,0px))}}
header.top{{position:sticky;top:0;z-index:10;background:var(--bg);border-bottom:2px solid var(--ink)}}
:root[data-float] header.top{{border-bottom:0;background:transparent;padding-top:8px}}
:root[data-float] header.top .wrap>div{{border:1px solid var(--line);border-radius:999px;background:color-mix(in srgb,var(--surface) 74%,transparent);-webkit-backdrop-filter:blur(14px) saturate(1.4);backdrop-filter:blur(14px) saturate(1.4);box-shadow:var(--shadow-up);padding-inline:16px}}
.top .wrap>div{{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:64px}}
.assin{{display:flex;align-items:center;gap:10px;font:800 24px/1 var(--f-display);letter-spacing:-.03em;color:var(--ink);text-decoration:none}}
.assin img,.assin svg{{width:32px;height:32px}}
main{{display:grid;gap:56px;padding-block:40px 80px}}
section{{display:grid;gap:16px;min-width:0}}
.eyebrow{{font:500 12px/16px var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0}}
:root[data-float] .eyebrow{{color:var(--hl)}}
h1,h2,h3{{font-family:var(--f-display);margin:0;text-wrap:balance}}
h1{{font-size:clamp(32px,6vw,52px);line-height:1.05;letter-spacing:-.035em;font-weight:800}}
h2{{font-size:28px;letter-spacing:-.03em;font-weight:700;color:var(--brand)}}
h3{{font-size:18px;font-weight:700}}
p{{margin:0;max-width:68ch}}
.muted{{color:var(--muted)}} .mono{{font-family:var(--f-mono);font-size:14px;font-variant-numeric:tabular-nums}}
mark.hl{{background:linear-gradient(transparent 55%,var(--hl) 55%);color:inherit;padding:0 .1em}}
.grade{{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}}
.card,.kpi,.blk,.marco .bola{{background:var(--surface);border:1px solid var(--line);border-radius:var(--r)}}
.card,.kpi{{padding:20px}}
:root[data-float] .card,:root[data-float] .kpi,:root[data-float] .blk{{box-shadow:var(--shadow);transition:transform .2s ease,box-shadow .2s ease}}
:root[data-float] .card:hover,:root[data-float] .kpi:hover,:root[data-float] .blk:hover{{transform:translateY(-3px);box-shadow:var(--shadow-up)}}
.btn{{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:0 18px;font:600 16px var(--f-body);border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:8px;cursor:pointer;text-decoration:none}}
:root[data-float] .btn{{border-radius:10px}}
.btn.principal{{background:var(--hl);color:var(--hl-ink);border-color:var(--hl)}}
.btn.marca{{background:var(--brand);color:var(--brand-ink);border-color:var(--brand);border-radius:999px}}
.btn:focus-visible,input:focus-visible,select:focus-visible{{outline:3px solid var(--focus);outline-offset:2px}}
.paletas{{display:flex;flex-wrap:wrap;gap:8px}}
.pre{{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:6px 12px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--ink);font:500 14px var(--f-body);cursor:pointer}}
.pre[aria-pressed="true"]{{border-color:var(--brand);box-shadow:0 0 0 2px var(--brand)}}
.sw{{display:inline-flex}} .sw i{{width:14px;height:14px;border-radius:50%;margin-left:-4px;border:1px solid rgba(0,0,0,.15)}} .sw i:first-child{{margin-left:0}}
.kpi .rot{{display:flex;align-items:center;gap:6px;font:500 12px var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.kpi .val{{font:700 30px/1.1 var(--f-display);margin-top:8px;font-variant-numeric:tabular-nums}}
.kpi.hoje{{background:var(--hl-soft)}}
.anel{{display:flex;align-items:center;gap:16px}}
.anel circle{{fill:none;stroke-width:8}}
.blks{{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}}
.blk{{display:grid;gap:4px;padding:14px 16px;border-left-width:4px}}
.blk.t{{border-left-color:var(--brand)}} .blk.l{{border-left-color:var(--muted)}} .blk.q{{border-left-color:var(--warn)}} .blk.a{{border-left-color:var(--focus)}}
.blk.x{{border-left:5px double var(--brand)}} .blk.v{{border-left-color:var(--hl)}}
.blk.done{{background:var(--hl-soft);border-color:var(--hl)}}
.blk-top{{display:flex;justify-content:space-between;align-items:center;gap:8px}}
.tipo{{display:inline-flex;align-items:center;gap:6px;font:500 12px var(--f-mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}
.feito{{font-size:14px;display:inline-flex;gap:6px;align-items:center}}
.trilha{{list-style:none;margin:0;padding:0;display:flex;justify-content:space-between;position:relative;gap:8px}}
.trilha::before{{content:"";position:absolute;left:24px;right:24px;top:22px;border-top:2px dashed var(--line)}}
.marco{{position:relative;display:grid;justify-items:center;gap:6px;font-size:14px;text-align:center;flex:1}}
.marco .bola{{width:44px;height:44px;display:grid;place-items:center;border-radius:50%}}
.marco.feito .bola{{background:var(--brand);color:var(--brand-ink);border-color:var(--brand)}}
.marco.atual .bola{{background:var(--hl);border-color:var(--hl);box-shadow:0 0 0 6px var(--hl-soft)}}
@media (max-width:560px){{.trilha{{flex-direction:column}}.trilha::before{{left:22px;right:auto;top:22px;bottom:22px;border-top:0;border-left:2px dashed var(--line)}}.marco{{grid-template-columns:44px 1fr;justify-items:start;text-align:left;align-items:center}}}}
.tags{{display:flex;flex-wrap:wrap;gap:8px}}
.tag{{font:500 11.5px var(--f-mono);padding:3px 8px;border-radius:6px;background:var(--brand-soft);color:var(--brand)}}
.tag.w{{background:var(--warn-soft);color:var(--warn)}} .tag.x{{background:var(--hl);color:var(--hl-ink)}}
.aviso{{border-left:4px solid var(--warn);background:var(--warn-soft);padding:12px 16px;border-radius:0 var(--r) var(--r) 0}}
.aviso.ok{{border-left-color:var(--brand);background:var(--brand-soft)}}
.toast{{position:fixed;left:50%;bottom:calc(20px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:10px 18px;border-radius:999px;font-weight:600;opacity:0;pointer-events:none;transition:opacity .2s}}
.toast.on{{opacity:1}}
.tbl{{overflow-x:auto;border:1px solid var(--line);border-radius:var(--r);background:var(--surface)}}
table{{border-collapse:collapse;width:100%;min-width:560px;font-size:14px}} th,td{{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line)}} th{{font:500 12px var(--f-mono);text-transform:uppercase;color:var(--muted)}}
.amostra{{display:inline-block;width:18px;height:18px;border-radius:4px;vertical-align:middle;border:1px solid var(--line);margin-right:6px}}
footer{{border-top:1px solid var(--line);padding-block:24px;font-size:14px;color:var(--muted)}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}:root[data-float] .card:hover,:root[data-float] .kpi:hover,:root[data-float] .blk:hover{{transform:none}}}}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">{sprite}</svg>
<header class="top"><div class="wrap"><div>
  <a class="assin" href="index.html"><img src="assets/marca/orgatec-original.png" alt="">ORGATEC</a>
  <button class="btn" type="button" id="btnCores">{ico("palette")}Cores</button>
</div></div></header>
<main class="wrap">
  <section>
    <p class="eyebrow">Design system · ORGATEC Trilha</p>
    <h1>O próximo passo da <mark class="hl">reforma</mark>, primeiro.</h1>
    <p class="muted">Design do projeto Trilha com o nome trocado para ORGATEC. Esta página é demonstração da fase de testes: o site ainda usa o design atual (orgatec-template2), e a escolha entre os dois é a pendência D6 do <a href="testes/index.html" style="color:var(--brand)">painel de testes</a>.</p>
    <div style="display:flex;flex-wrap:wrap;gap:12px"><a class="btn marca" href="testes/index.html">Ver painel de testes</a><a class="btn principal" href="#cores">Escolher paleta</a><a class="btn" href="orgatec-template2.html">Comparar com o design atual</a></div>
  </section>

  <section id="cores">
    <p class="eyebrow">Cor</p><h2>Paletas do seletor de cores</h2>
    <p class="muted">A escolha vale na hora e fica salva neste navegador. As paletas "flutuante" ligam sombra, brilho de fundo, cabeçalho de vidro, cantos de 14 px e as fontes Sora e IBM Plex Sans.</p>
    <div class="paletas" id="paletas" role="group" aria-label="Paletas"></div>
    <div class="tbl"><table><thead><tr><th>Token</th><th>Valor na paleta ativa</th><th>Papel</th></tr></thead><tbody id="tabTokens"></tbody></table></div>
  </section>

  <section>
    <p class="eyebrow">Marca</p><h2>Símbolo</h2>
    <div class="grade">
      <div class="card" style="display:flex;align-items:center;gap:16px"><img src="assets/marca/orgatec-original.png" alt="Símbolo oficial ORGATEC" width="56" height="62"><div><h3>Símbolo oficial</h3><p class="muted">Logotipo original, sempre com as cores originais, em qualquer paleta.</p></div></div>
      <div class="card" style="display:flex;align-items:center;gap:16px">
        <svg viewBox="0 0 64 64" width="56" height="56" role="img" aria-label="ORGATEC"><rect x="5" y="5" width="54" height="54" rx="12" fill="none" stroke="var(--brand)" stroke-width="5"/><rect x="14" y="34" width="36" height="11" rx="2" fill="var(--hl)"/><path d="M19 33 L28 42 L46 21" fill="none" stroke="var(--ink)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <div><h3>Símbolo do modelo Trilha</h3><p class="muted">Página, marca-texto e visto. Só referência: a ORGATEC usa o logotipo original.</p></div></div>
    </div>
  </section>

  <section>
    <p class="eyebrow">Tipografia</p><h2>Títulos, texto e dados</h2>
    <div class="grade">
      <div class="card"><p class="eyebrow">Títulos · --f-display</p><p style="font:800 32px/1.1 var(--f-display);letter-spacing:-.03em">ORGATEC</p></div>
      <div class="card"><p class="eyebrow">Texto · --f-body</p><p>Rótulos dizem o que acontece: "Salvar e ir para o cronograma".</p></div>
      <div class="card"><p class="eyebrow">Dados · --f-mono</p><p class="mono">LC 214/2025, art. 41 · 31/10/2026 · 08:00</p></div>
    </div>
  </section>

  <section>
    <p class="eyebrow">Componentes</p><h2>Indicadores</h2>
    <div class="grade">
      <div class="kpi hoje"><span class="rot">{ico("target")}Hoje</span><div class="val">3 de 6</div><p class="muted">blocos feitos</p></div>
      <div class="kpi"><span class="rot">{ico("cal")}Semana</span><div class="anel"><svg width="64" height="64" viewBox="0 0 64 64" aria-label="58% da semana"><circle cx="32" cy="32" r="26" stroke="var(--line)"/><circle cx="32" cy="32" r="26" stroke="var(--hl)" stroke-dasharray="94.8 163.4" transform="rotate(-90 32 32)" stroke-linecap="round"/></svg><div class="val">58%</div></div></div>
      <div class="kpi"><span class="rot">{ico("clock")}Prazo</span><div class="val">61 dias</div><p class="muted">até 01/01/2027</p></div>
    </div>
  </section>

  <section>
    <p class="eyebrow">Componentes</p><h2>Blocos por tipo</h2>
    <div class="blks">{html_blocos}</div>
  </section>

  <section>
    <p class="eyebrow">Componentes</p><h2>Trilha das fases</h2>
    <ol class="trilha">{html_marcos}</ol>
  </section>

  <section>
    <p class="eyebrow">Componentes</p><h2>Botões, etiquetas e avisos</h2>
    <div style="display:flex;flex-wrap:wrap;gap:12px"><button class="btn principal" type="button" data-toast="Bloco feito">Marcar como feito</button><button class="btn" type="button" data-toast="Sincronizado">Sincronizar</button><button class="btn" type="button" id="btnApagar">Apagar exemplo</button></div>
    <div class="tags"><span class="tag">fato</span><span class="tag">fonte secundária</span><span class="tag w">inferência</span><span class="tag w">Desatualizado</span><span class="tag x">2×</span><span class="tag">Novo</span></div>
    <div class="aviso">Âmbar de prazo: a opção do Simples para o semestre de janeiro é feita em setembro.</div>
    <div class="aviso ok">Versão positiva: plano salvo neste aparelho.</div>
  </section>
</main>
<footer><div class="wrap">ORGATEC · CNPJ 13.155.211/0001-45 · Resp. técnico: Robson Alain Veloso, <span class="mono">CRC-TO 002032/O-5 T-GO</span> · LGPD · NBC PG 01 · Design adaptado do projeto Trilha.</div></footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>
(function () {{
  'use strict';
  var PRESETS = {presets_js};
  var USOS = {json.dumps(USOS, ensure_ascii=False)};
  var FOCO = {json.dumps(FOCO)};
  var hx = function (h) {{ var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }};
  var mx = function (a, b, t) {{ var x = hx(a), y = hx(b); return '#' + x.map(function (v, i) {{ return Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0'); }}).join(''); }};
  var lum = function (h) {{ var c = hx(h).map(function (v) {{ v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }}); return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; }};
  var CHAVES = ['--bg', '--surface', '--surface2', '--ink', '--muted', '--line', '--brand', '--brand-ink', '--brand-soft', '--hl', '--hl-ink', '--hl-soft', '--warn', '--warn-soft', '--focus', 'color-scheme'];
  var r = document.documentElement, tema = 'auto', toastT;
  function toast(m) {{ var t = document.getElementById('toast'); t.textContent = m; t.classList.add('on'); clearTimeout(toastT); toastT = setTimeout(function () {{ t.classList.remove('on'); }}, 1800); }}
  // Mesma regra do applyTheme do Trilha (trilha.html)
  function aplicar(id) {{
    delete r.dataset.float; CHAVES.forEach(function (k) {{ r.style.removeProperty(k); }});
    var P = PRESETS.filter(function (p) {{ return p.id === id; }})[0];
    if (P && id !== 'auto') {{
      var dark = lum(P.bg) < .2;
      var v = {{ '--bg': P.bg, '--surface': dark ? mx(P.bg, '#FFFFFF', .06) : '#FFFFFF', '--surface2': mx(P.bg, P.ink, .07), '--ink': P.ink, '--muted': mx(P.ink, P.bg, .36), '--line': mx(P.bg, P.ink, .16),
        '--brand': P.p, '--brand-ink': lum(P.p) > .35 ? '#18211E' : '#F3F5F2', '--brand-soft': P.s, '--hl': P.h, '--hl-ink': P.fl ? '#06142b' : '#18211E', '--hl-soft': mx(P.bg, P.h, dark ? .22 : .3),
        '--warn': P.a, '--warn-soft': mx(P.bg, P.a, .16), '--focus': FOCO[P.id] || (dark ? FOCO.escuro : FOCO.claro) }};
      Object.keys(v).forEach(function (k) {{ r.style.setProperty(k, v[k]); }});
      r.style.setProperty('color-scheme', dark ? 'dark' : 'light');
      if (P.fl) r.dataset.float = dark ? 'dark' : 'light';
    }}
    tema = id; desenhar();
  }}
  function desenhar() {{
    document.getElementById('paletas').innerHTML = PRESETS.map(function (p) {{
      var sw = p.id === 'auto' ? ['#1F4D40', '#F2C14E', '#F3F5F2', '#111916'] : [p.p, p.h, p.ink, p.bg];
      return '<button class="pre" type="button" data-t="' + p.id + '" aria-pressed="' + (p.id === tema) + '"><span class="sw">' + sw.map(function (c) {{ return '<i style="background:' + c + '"></i>'; }}).join('') + '</span>' + p.name + '</button>';
    }}).join('');
    var cs = getComputedStyle(r);
    document.getElementById('tabTokens').innerHTML = Object.keys(USOS).map(function (k) {{
      var v = cs.getPropertyValue('--' + k).trim();
      return '<tr><td class="mono">--' + k + '</td><td class="mono"><span class="amostra" style="background:var(--' + k + ')"></span>' + v + '</td><td>' + USOS[k] + '</td></tr>';
    }}).join('');
  }}
  document.getElementById('paletas').addEventListener('click', function (ev) {{
    var b = ev.target.closest('[data-t]'); if (!b) return;
    aplicar(b.getAttribute('data-t'));
    try {{ localStorage.setItem('orgatec.trilha.tema', tema); }} catch (e) {{}}
    toast('Cores: ' + PRESETS.filter(function (p) {{ return p.id === tema; }})[0].name);
  }});
  document.getElementById('btnCores').addEventListener('click', function () {{ document.getElementById('cores').scrollIntoView({{ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }}); }});
  Array.prototype.forEach.call(document.querySelectorAll('[data-toast]'), function (b) {{ b.addEventListener('click', function () {{ toast(b.getAttribute('data-toast')); }}); }});
  // Ação destrutiva: o 1º clique arma o botão por 6 s; nunca confirm() do navegador
  var apagar = document.getElementById('btnApagar'), armado = null;
  apagar.addEventListener('click', function () {{
    if (armado) {{ clearTimeout(armado); armado = null; apagar.textContent = 'Apagar exemplo'; toast('Exemplo apagado'); return; }}
    apagar.textContent = 'Confirmar: apagar exemplo';
    armado = setTimeout(function () {{ armado = null; apagar.textContent = 'Apagar exemplo'; }}, 6000);
  }});
  Array.prototype.forEach.call(document.querySelectorAll('.blk input'), function (c) {{
    c.addEventListener('change', function () {{ c.closest('.blk').classList.toggle('done', c.checked); if (c.checked) toast('Bloco feito'); }});
  }});
  var salvo = 'azul-fl';
  try {{ salvo = localStorage.getItem('orgatec.trilha.tema') || salvo; }} catch (e) {{}}
  aplicar(PRESETS.some(function (p) {{ return p.id === salvo; }}) ? salvo : 'auto');
}})();
</script>
</body>
</html>
"""
    pagina = externalizar_script(pagina, RAIZ / "site" / "assets" / "js" / "ds-trilha.js", "assets/js/ds-trilha.js")
    PAGINA.write_text(pagina, encoding="utf-8", newline="\n")


def main():
    gerar_tokens()
    gerar_documento()
    gerar_pagina()
    print("gerado: design-system/orgatec-trilha/ (DESIGN-SYSTEM.md, tokens.json) e site/orgatec-trilha.html")


if __name__ == "__main__":
    main()
