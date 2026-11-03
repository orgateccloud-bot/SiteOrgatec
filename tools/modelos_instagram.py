"""Modelos do Instagram da ORGATEC e simulação do perfil (pedido do usuário em 03/11/2026: "configura o instagram",
"monte os modelos inicialmente e simule uma página").

O texto das peças continua no marketing (fonte única; esta ferramenta só LÊ a pasta):
    Marketing/conteudo/calendario/<mês>.md      peças P01…, datas, pilar, público e stories de prazo
    Marketing/conteudo/rascunhos/*.md           lâminas de cada carrossel (## Conteúdo) e status da peça
    Marketing/canais/instagram/kit.md           nome, bio, endereço e destaques do perfil
    Marketing/canais/whatsapp/kit.md            link "Vim pelo Instagram"
e desenha com a identidade do site (tools/imagem_marca.py: Azul flutuante escuro, fontes do site, logotipo original):

    modelos-redes/instagram/perfil/foto-perfil.png   1080 × 1080, para o recorte em círculo
    modelos-redes/instagram/destaques/<id>.png       capas dos destaques, 1080 × 1920
    modelos-redes/instagram/feed/pNN-MM.png          lâminas dos carrosséis com rascunho, 1080 × 1350 (4:5)
    modelos-redes/instagram/feed/pNN-capa.png        capa das peças ainda "a escrever"
    modelos-redes/instagram/stories/<dd-mm>.png      stories de véspera de prazo, 1080 × 1920
    modelos-redes/instagram/simulacao-perfil.html    simulação local do perfil (abre direto do disco)

A pasta fica fora de site/: o agendador da Janela de Campo não a publica, e nada aqui é postado. Regras das peças
(Marketing/conteudo/_modelos/peca.md): marca ORGATEC, logotipo original, verde só no contato (CONTATO de
tools/gerar_design_system.py), sem o endereço do site enquanto ele estiver em homologação. Peça que não está
"aprovado" sai com a etiqueta RASCUNHO; a simulação avisa que não é a interface do Instagram.

Uso:  python tools/modelos_instagram.py [--mes 2026-11]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess  # nosec B404 — só executa node com argumentos fixos
from html import escape
from pathlib import Path

import imagem_marca as M
from gerar_design_system import CONTATO

RAIZ = M.RAIZ
MARKETING = RAIZ.parent / "Marketing"
SAIDA = RAIZ / "modelos-redes" / "instagram"
RT = ("Robson Alain Veloso", "CRC-TO 002032/O-5 T-GO")  # responsável técnico, como no rodapé do site
FEED, STORY, PERFIL = (1080, 1350), (1080, 1920), (1080, 1080)
STORY_MARGENS = (140, 210)  # faixas cobertas no alto (nome, progresso) e embaixo (resposta), como no cartão do status
PILARES = {"bastidores": "Bastidores", "agenda": "Agenda", "reforma": "Reforma", "campo": "Campo",
           "reforma / proteção": "Proteção do negócio", "proteção do negócio": "Proteção do negócio", "protecao": "Proteção do negócio"}

SITUACAO = {"rascunho": "rascunho", "em-revisao": "em revisão", "aprovado": "aprovado", "publicado": "publicado"}

# Ícones das capas dos destaques (traço simples, sem logotipo de terceiros); "simbolo" usa o logotipo da ORGATEC
ICONES = {
    "prazos": '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M8 3v4M16 3v4M8 13.5h3M8 16.5h6"/>',
    "reforma": '<path d="M7 3.5h7l4 4V20a.5.5 0 0 1-.5.5h-10A.5.5 0 0 1 7 20z"/><path d="M14 3.5V8h4M9.5 12h6M9.5 15h6M9.5 18h4"/>',
    "agro": '<path d="M12 20.5V11"/><path d="M12 13c0-4 3-6.5 7.5-6.5 0 4.5-3 6.5-7.5 6.5z"/><path d="M12 15.5C12 12 9.5 10 5 10c0 3.8 2.5 5.5 7 5.5z"/>',
    "transporte": '<path d="M2.5 6.5h11v10h-11z"/><path d="M13.5 9.5h4l3.5 3.5v3.5h-7.5"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    "contato": '<path d="M4.5 5.5h15a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H10l-4.5 3.5v-3.5h-1a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1z"/><path d="M8 10.5h8M8 13.5h5"/>',
}
CHECK = '<path d="M5 12.5l4.5 4.5L19 7.5"/>'


# ---------- leitura do marketing (somente leitura)

def _frontmatter(texto: str) -> dict:
    m = re.match(r"---\n(.*?)\n---", texto, re.S)
    campos = {}
    for linha in (m.group(1).splitlines() if m else []):
        if ":" in linha and not linha.startswith(" "):
            k, v = linha.split(":", 1)
            campos[k.strip()] = v.split("#")[0].strip()
    return campos


def _secao(texto: str, titulo: str) -> str:
    m = re.search(rf"^## {re.escape(titulo)}\n(.*?)(?=^## |\Z)", texto, re.M | re.S)
    return m.group(1) if m else ""


def calendario(mes: str) -> tuple[list[dict], list[dict]]:
    """(peças, stories) do calendário do mês, na ordem do arquivo."""
    texto = (MARKETING / "conteudo" / "calendario" / f"{mes}.md").read_text(encoding="utf-8")
    pecas, stories = [], []
    for linha in texto.splitlines():
        c = [x.strip() for x in linha.strip().strip("|").split("|")]
        if len(c) < 6 or not re.match(r"\d{2}/\d{2} \(", c[0]):
            continue
        data = c[0][:5]
        m = re.match(r"(P\d{2}) · (.+)", c[1])
        if m:
            arq = re.search(r"`rascunhos/([^`]+)`", c[5])
            pecas.append({"id": m.group(1), "titulo": m.group(2), "data": data, "canais": c[2], "pilar": c[3],
                          "publico": c[4], "rascunho": arq.group(1) if arq else None})
        s = re.match(r'Story: "(.+)"', c[1])
        if s:
            usa = re.search(r"usa (P\d{2})", c[5])
            prazo = re.search(r"\d{2}/\d{2}", s.group(1))
            stories.append({"data": data, "texto": s.group(1), "prazo": prazo.group(0) if prazo else data,
                            "usa": usa.group(1) if usa else None})
    return pecas, stories


def _md(texto: str) -> str:
    """Escapa e converte só o **negrito** do Markdown."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escape(texto))


def laminas(peca: dict) -> tuple[dict, list[dict]]:
    """(frontmatter, lâminas) do rascunho: cada item numerado de ## Conteúdo vira uma lâmina com tipo."""
    texto = (MARKETING / "conteudo" / "rascunhos" / peca["rascunho"]).read_text(encoding="utf-8")
    itens = re.findall(r"^\d+\.\s+(.+)$", _secao(texto, "Conteúdo"), re.M)
    saida = []
    for i, item in enumerate(itens):
        m = re.match(r"\*\*([^*]+?):\*\*\s*(.*)$", item)
        rotulo, resto = (m.group(1), m.group(2)) if m else (None, item)
        r = (rotulo or "").lower()
        if i == 0:
            partes = re.sub(r"\s*\([^)]*\)\s*$", "", resto).split(" · ")  # o parêntese final é nota de arte
            saida.append({"tipo": "capa", "titulo": partes[0], "sub": " · ".join(partes[1:])})
        elif r.startswith("o que fazer"):
            saida.append({"tipo": "fazer", "titulo": rotulo, "itens": [x.rstrip(".") for x in resto.split(" · ")]})
        elif r == "fontes":
            data = re.search(r"(Consultad[ao]s|Conferid[ao]s) em (\d{2}/\d{2}/\d{4})", resto)
            limpo = re.sub(r"\s*(Consultad[ao]s|Conferid[ao]s) em \d{2}/\d{2}/\d{4}\.?", "", resto)
            fontes = [x.strip().rstrip(".") for x in limpo.split(" · ")
                      if x.strip() and not x.strip().startswith(("ORGATEC", "CRC"))]
            saida.append({"tipo": "fontes", "itens": fontes, "consulta": f"{data.group(1)} em {data.group(2)}" if data else ""})
        elif r.startswith("fale"):
            saida.append({"tipo": "contato", "titulo": rotulo})
        else:
            saida.append({"tipo": "ideia", "titulo": rotulo, "corpo": resto})
    return _frontmatter(texto), saida


def perfil() -> dict:
    kit = (MARKETING / "canais" / "instagram" / "kit.md").read_text(encoding="utf-8")
    linha = lambda campo: re.search(rf"^\| {campo} \| (.+?) \|$", kit, re.M).group(1).replace("\\|", "|")  # noqa: E731
    bio = [b[2:].strip() for b in re.findall(r"^> .+$", _secao(kit, "2. Perfil"), re.M)]
    destaques = [d.strip() for d in re.findall(r"^\| ([^|]+?) \| [^|]+ \|$", _secao(kit, "3. Destaques"), re.M)
                 if d.strip() not in ("Destaque", "---")]
    whats = (MARKETING / "canais" / "whatsapp" / "kit.md").read_text(encoding="utf-8")
    link = re.search(r"^\| Instagram[^|]*\| `([^`]+)` \|", whats, re.M).group(1)
    return {"nome": linha("Nome"), "endereco": linha("Endereço"), "bio": bio, "destaques": destaques, "link": link}


def config_site() -> dict:
    """WhatsApp de exibição e ambiente, de site/assets/js/config.js (configuração única do site)."""
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js não encontrado no PATH (necessário para ler site/assets/js/config.js)")
    js = "const c=require('./site/assets/js/config.js');process.stdout.write(JSON.stringify({w:c.whatsapp.exibicao,a:c.ambiente}))"
    r = subprocess.run([node, "-e", js], capture_output=True, text=True, encoding="utf-8", cwd=RAIZ, check=False)  # nosec B603
    if r.returncode != 0:
        raise RuntimeError(f"leitura de config.js falhou: {r.stderr.strip()}")
    return json.loads(r.stdout)


# ---------- desenho

CSS = f"""
.f{{height:100%;display:flex;flex-direction:column;justify-content:space-between;padding:76px 80px 64px;
  background:radial-gradient(820px 640px at 100% 0,var(--brand-soft),transparent 70%),var(--bg)}}
svg{{fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex:none}}
.topo{{display:flex;justify-content:space-between;align-items:center;gap:16px}}
.marca{{display:flex;align-items:center;gap:14px;font:800 30px/1 var(--f-display);letter-spacing:-.02em}}
.chips{{display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end}}
.chip{{font:500 18px/1 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;padding:10px 16px;border-radius:999px;
  background:var(--brand-soft);color:var(--hl)}}
.chip.rascunho{{background:transparent;color:var(--muted);border:2px dashed var(--line)}}
.meio{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:28px;padding:40px 0}}
.eyebrow{{font:500 22px/1.2 var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--hl)}}
.barra{{width:96px;height:8px;border-radius:4px;background:var(--hl)}}
h1{{font-family:var(--f-display);font-weight:700;letter-spacing:-.03em;line-height:1.05}}
h2{{font:700 60px/1.1 var(--f-display);letter-spacing:-.02em}}
.sub{{font:500 30px/1.3 var(--f-mono);color:var(--muted)}}
.corpo{{font:400 48px/1.38 var(--f-body);color:var(--ink)}}
.corpo.so{{font-size:58px}}
strong{{font-weight:600;color:var(--hl)}}
.lista{{display:flex;flex-direction:column;gap:26px;list-style:none}}
.lista li{{display:flex;gap:22px;align-items:flex-start;font:400 38px/1.3 var(--f-body)}}
.lista li span.ic{{display:grid;place-items:center;width:52px;height:52px;border-radius:14px;background:var(--brand-soft);color:var(--brand);margin-top:-2px}}
.fontes{{display:flex;flex-direction:column;gap:12px;list-style:none;font:500 23px/1.35 var(--f-mono);color:var(--ink)}}
.fontes li{{padding-left:22px;border-left:3px solid var(--line)}}
.consulta{{font:500 22px/1 var(--f-mono);color:var(--muted)}}
.zap{{display:inline-flex;align-items:center;gap:16px;align-self:flex-start;padding:22px 34px;border-radius:999px;
  background:{CONTATO["contato"]};color:{CONTATO["sobre-contato"]};font:600 34px/1 var(--f-body)}}
.numero{{font:600 40px/1 var(--f-display)}}
.rt{{font:400 24px/1.35 var(--f-body);color:var(--muted)}}
.pe{{display:flex;justify-content:space-between;align-items:center;font:500 22px/1 var(--f-mono);color:var(--muted)}}
.pe b{{color:var(--brand);font-weight:500}}
.st{{padding:{STORY_MARGENS[0]}px 80px {STORY_MARGENS[1]}px}}
.st h1{{font-size:96px}}
.st .corpo{{font-size:46px}}
.capa-destaque{{height:100%;display:grid;place-items:center;background:radial-gradient(700px 700px at 50% 50%,var(--brand-soft),transparent 72%),var(--bg);color:var(--hl)}}
.perfil{{height:100%;display:grid;place-items:center;background:radial-gradient(560px 560px at 50% 45%,var(--brand-soft),transparent 75%),var(--bg)}}
"""


def _topo(peca: dict, status: str) -> str:
    pilar = PILARES.get(peca["pilar"].lower(), peca["pilar"].capitalize())
    rascunho = '' if status == "aprovado" else '<span class="chip rascunho">Rascunho</span>'
    return (f'<header class="topo"><span class="marca">{M.logo_img(56)}ORGATEC</span>'
            f'<span class="chips">{rascunho}<span class="chip">{escape(pilar)}</span></span></header>')


def _icone(caminho: str, tamanho: int) -> str:
    return f'<svg viewBox="0 0 24 24" width="{tamanho}" height="{tamanho}" aria-hidden="true">{caminho}</svg>'


def _zap(cfg: dict) -> str:
    return (f'<span class="zap">{_icone(ICONES["contato"], 40)}Fale com a ORGATEC no WhatsApp</span>'
            f'<p class="numero">{escape(cfg["w"])}</p>')


def lamina_html(peca: dict, status: str, lam: dict, n: int, total: int, cfg: dict) -> str:
    tipo = lam["tipo"]
    if tipo == "capa":
        tam = 92 if len(lam["titulo"]) <= 40 else 76 if len(lam["titulo"]) <= 70 else 64
        publico = "" if peca["publico"].lower() == "geral" else f'<p class="eyebrow">{escape(peca["publico"])}</p>'
        meio = (f'{publico}<div class="barra"></div>'
                f'<h1 style="font-size:{tam}px">{_md(lam["titulo"])}</h1>' + (f'<p class="sub">{_md(lam["sub"])}</p>' if lam["sub"] else ""))
    elif tipo == "ideia":
        meio = ((f'<h2>{_md(lam["titulo"])}</h2>' if lam["titulo"] else "") +
                f'<p class="corpo{"" if lam["titulo"] else " so"}">{_md(lam["corpo"])}</p>')
    elif tipo == "fazer":
        itens = "".join(f'<li><span class="ic">{_icone(CHECK, 34)}</span><span>{_md(x)}</span></li>' for x in lam["itens"])
        meio = f'<h2>{_md(lam["titulo"])}</h2><ul class="lista">{itens}</ul>'
    elif tipo == "fontes":
        itens = "".join(f"<li>{_md(x)}</li>" for x in lam["itens"])
        consulta = f'<p class="consulta">{escape(lam["consulta"])}</p>' if lam["consulta"] else ""
        meio = (f'<h2>Fontes</h2><ul class="fontes">{itens}</ul>{consulta}{_zap(cfg)}'
                f'<p class="rt">Responsável técnico: {escape(RT[0])} · {escape(RT[1])}</p>')
    else:  # contato
        meio = (f'<h2>{_md(lam["titulo"])}</h2>{_zap(cfg)}'
                f'<p class="rt">Responsável técnico: {escape(RT[0])} · {escape(RT[1])}</p>')
    seta = "<b>Arraste →</b>" if tipo == "capa" and total > 1 else ""
    corpo = (f'<main class="f">{_topo(peca, status)}<section class="meio">{meio}</section>'
             f'<footer class="pe"><span>{escape(peca["id"])} · {n:02d}/{total:02d}</span>{seta}</footer></main>')
    return M.documento(corpo, CSS, *FEED)


def story_html(story: dict, base: dict | None, lams: list[dict], status: str, cfg: dict) -> str:
    """Story de véspera: o texto do calendário em destaque, a lâmina da peça com a mesma data e as fontes citadas nela."""
    lam = next((x for x in lams if x["tipo"] == "ideia" and story["prazo"] in (x["titulo"] or "") + x["corpo"]), None)
    fontes = next((x for x in lams if x["tipo"] == "fontes"), {"itens": [], "consulta": ""})
    texto = (lam["corpo"] if lam else "") + " " + story["texto"]
    citadas = [f for f in fontes["itens"] if re.search(rf"\b{re.escape(f.split(':')[0].split('/')[0])}\b", texto, re.I)]
    titulo = story["texto"][:1].upper() + story["texto"][1:]
    detalhe = (f'<p class="corpo">{_md(((lam["titulo"] + ": ") if lam and lam["titulo"] else "") + lam["corpo"])}</p>' if lam else "")
    peca = {"id": "Story", "pilar": base["pilar"] if base else "agenda"}
    fontes_html = (f'<ul class="fontes">{"".join(f"<li>{_md(x)}</li>" for x in citadas)}</ul>'
                   f'<p class="consulta">{escape(fontes["consulta"])} · {escape(RT[1])}</p>') if citadas else ""
    corpo = (f'<main class="f st">{_topo(peca, status)}<section class="meio"><p class="eyebrow">Prazo · {escape(story["prazo"])}</p>'
             f'<div class="barra"></div><h1>{_md(titulo)}</h1>{detalhe}</section>'
             f'<footer style="display:flex;flex-direction:column;gap:18px">{fontes_html}'
             f'<p class="rt">Toque na figurinha para falar no WhatsApp · {escape(cfg["w"])}</p></footer></main>')
    return M.documento(corpo, CSS, *STORY)


def destaque_html(nome: str) -> str:
    chave = _chave(nome)
    miolo = M.logo_img(560) if chave == "quem-somos" else _icone(ICONES[_icone_de(chave)], 520)
    return M.documento(f'<main class="capa-destaque">{miolo}</main>', CSS, *STORY)


def perfil_html() -> str:
    return M.documento(f'<main class="perfil">{M.logo_img(600)}</main>', CSS, *PERFIL)


def _chave(nome: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", nome.lower().translate(str.maketrans("áâãàéêíóôõúç", "aaaaeeiooouc"))).strip("-")


def _icone_de(chave: str) -> str:
    return {"prazos": "prazos", "reforma": "reforma", "agro": "agro", "transporte": "transporte"}.get(chave, "contato")


# ---------- simulação do perfil

def simulacao_html(perf: dict, pecas: list[dict], stories: list[dict], cfg: dict) -> str:
    cores = ";".join(f"--{k}:{v}" for k, v in M.cores().items())
    grade = []
    for p in reversed(pecas):  # o perfil mostra a mais recente primeiro
        capa = p["arquivos"][0]
        varias = '<span class="multi" title="carrossel">▣</span>' if len(p["arquivos"]) > 1 else ""
        grade.append(f'<a href="#{p["id"].lower()}" title="{escape(p["id"] + " · " + p["titulo"])}"><img src="{capa}" alt="">{varias}</a>')
    destaques = "".join(f'<figure><img src="destaques/{_chave(d)}.png" alt=""><figcaption>{escape(d)}</figcaption></figure>'
                        for d in perf["destaques"])
    secoes = []
    for p in pecas:
        tiras = "".join(f'<img src="{a}" alt="">' for a in p["arquivos"])
        situacao = "a escrever" if not p["rascunho"] else SITUACAO.get(p["status"], p["status"])
        secoes.append(f'<section id="{p["id"].lower()}"><h3>{escape(p["id"])} · {escape(p["titulo"])}</h3>'
                      f'<p class="meta">{escape(p["data"])} · {escape(p["canais"])} · {escape(p["publico"])} · <b>{escape(situacao)}</b></p>'
                      f'<div class="tira">{tiras}</div></section>')
    tiras_story = "".join(f'<figure><img src="stories/{s["arquivo"]}" alt=""><figcaption>{escape(s["data"])} · {escape(s["texto"])}</figcaption></figure>'
                          for s in stories)
    bio = "<br>".join(escape(b) for b in perf["bio"])
    link = perf["link"].split("?")[0].removeprefix("https://")
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Simulação do perfil · ORGATEC</title>
<link rel="stylesheet" href="../../site/assets/fontes/fontes.css">
<style>
:root{{{cores};--f-display:'Sora',sans-serif;--f-body:'IBM Plex Sans',sans-serif;--f-mono:'IBM Plex Mono',monospace}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--ink);font:400 15px/1.45 var(--f-body);padding:32px 16px 64px}}
.aviso{{max-width:1240px;margin:0 auto 28px;padding:14px 18px;border:1px dashed var(--line);border-radius:14px;color:var(--muted)}}
.aviso strong{{color:var(--ink)}}
.grade-geral{{max-width:1240px;margin:0 auto;display:flex;gap:40px;align-items:flex-start;flex-wrap:wrap}}
.celular{{width:390px;flex:none;background:#000;border:10px solid #1b1f27;border-radius:46px;overflow:hidden;color:#f5f5f5;position:sticky;top:24px}}
.celular .tela{{height:780px;overflow-y:auto;padding:14px 0 0}}
.barra-topo{{display:flex;justify-content:space-between;align-items:center;padding:6px 16px 12px;font-weight:600;font-size:17px}}
.barra-topo small{{font:400 11px var(--f-mono);color:#9aa}}
.cab{{display:flex;align-items:center;gap:22px;padding:0 16px}}
.cab img{{width:86px;height:86px;border-radius:50%;border:1px solid #333}}
.nums{{display:flex;gap:18px;text-align:center;font-size:13px}}.nums b{{display:block;font-size:16px}}
.bio{{padding:12px 16px 0;font-size:13.5px;line-height:1.4}}
.bio .nome{{font-weight:600}}.bio .cat{{color:#a8a8a8}}.bio a{{color:#e0f1ff;text-decoration:none;font-weight:600}}
.bio .end{{color:#a8a8a8;margin-top:4px}}
.botoes{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;padding:12px 16px}}
.botoes span{{background:#262626;border-radius:8px;text-align:center;padding:7px 0;font-size:12.5px;font-weight:600}}
.botoes span.seguir{{background:var(--brand);color:var(--brand-ink)}}.botoes span.zap{{background:{CONTATO["contato"]};color:#fff}}
.dest{{display:flex;gap:14px;overflow-x:auto;padding:6px 16px 14px}}
.dest figure{{width:66px;flex:none;text-align:center;font-size:11.5px}}
.dest img{{width:64px;height:64px;border-radius:50%;object-fit:cover;border:2px solid #3a3a3a;padding:2px;background:#000}}
.grade{{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;border-top:1px solid #262626;padding-top:2px}}
.grade a{{position:relative;aspect-ratio:3/4;overflow:hidden;display:block}}
.grade img{{width:100%;height:100%;object-fit:cover}}
.grade .multi{{position:absolute;top:6px;right:8px;color:#fff;font-size:14px;text-shadow:0 0 4px #000}}
.pecas{{flex:1;min-width:300px}}
.pecas h2{{font:700 26px var(--f-display);margin:0 0 6px}}
.pecas>p{{color:var(--muted);margin-bottom:22px}}
.pecas section{{margin-bottom:34px}}
.pecas h3{{font:600 18px var(--f-display)}}
.meta{{font:500 12px var(--f-mono);color:var(--muted);margin:4px 0 10px;letter-spacing:.02em}}.meta b{{color:var(--hl);font-weight:500}}
.tira{{display:flex;gap:10px;overflow-x:auto;padding-bottom:8px}}
.tira img{{width:216px;aspect-ratio:4/5;border-radius:10px;border:1px solid var(--line);flex:none}}
.stories{{display:flex;gap:14px;overflow-x:auto}}
.stories figure{{width:200px;flex:none;font-size:12.5px;color:var(--muted)}}
.stories img{{width:200px;aspect-ratio:9/16;border-radius:12px;border:1px solid var(--line);display:block;margin-bottom:6px}}
</style></head><body>
<p class="aviso"><strong>Simulação local do perfil, para revisar antes de montar.</strong> Não é a interface do Instagram e nada foi publicado.
As peças marcadas RASCUNHO aguardam aprovação (M3) e, quando têm afirmação legal, a revisão do responsável técnico. O endereço @ é provisório (pendência M2).
Os textos vêm dos rascunhos do marketing; para atualizar, rode <code>python tools/modelos_instagram.py</code>.</p>
<div class="grade-geral">
<div class="celular"><div class="tela">
<div class="barra-topo"><span>@orgatec <small>(endereço a definir)</small></span><span>☰</span></div>
<div class="cab"><img src="perfil/foto-perfil.png" alt="Foto do perfil"><div class="nums"><span><b>{len(pecas)}</b>publicações</span><span><b>0</b>seguidores</span><span><b>0</b>seguindo</span></div></div>
<div class="bio"><p class="nome">{escape(perf["nome"])}</p><p class="cat">Contador</p><p>{bio}</p>
<p><a>{escape(link)}</a></p><p class="end">{escape(perf["endereco"])}</p></div>
<div class="botoes"><span class="seguir">Seguir</span><span>Mensagem</span><span class="zap">WhatsApp</span><span>Endereço</span></div>
<div class="dest">{destaques}</div>
<div class="grade">{"".join(grade)}</div>
</div></div>
<div class="pecas"><h2>Carrosséis e capas</h2><p>Ordem do calendário de novembro. Toque numa miniatura do perfil para ir à peça.</p>
{"".join(secoes)}
<section><h3>Stories de véspera de prazo</h3><p class="meta">1080 × 1920 · a figurinha de link do WhatsApp entra no app, na área livre embaixo</p>
<div class="stories">{tiras_story}</div></section></div>
</div></body></html>"""


# ---------- geração

def gerar(mes: str = "2026-11", saida: Path = SAIDA) -> Path:
    cfg = config_site()
    perf = perfil()
    pecas, stories = calendario(mes)
    imagens: list[tuple[str, int, int, Path]] = [(perfil_html(), *PERFIL, saida / "perfil" / "foto-perfil.png")]
    imagens += [(destaque_html(d), *STORY, saida / "destaques" / f"{_chave(d)}.png") for d in perf["destaques"]]
    por_id = {}
    for p in pecas:
        if p["rascunho"]:
            fm, lams = laminas(p)
            p["status"] = fm.get("status", "rascunho")
        else:
            lams, p["status"] = [{"tipo": "capa", "titulo": p["titulo"], "sub": "A escrever"}], "rascunho"
        por_id[p["id"]] = (p, lams)
        nomes = ([f"feed/{p['id'].lower()}-{i:02d}.png" for i in range(1, len(lams) + 1)] if p["rascunho"]
                 else [f"feed/{p['id'].lower()}-capa.png"])
        p["arquivos"] = nomes
        imagens += [(lamina_html(p, p["status"], lam, i, len(lams), cfg), *FEED, saida / nome)
                    for i, (lam, nome) in enumerate(zip(lams, nomes), start=1)]
    for s in stories:
        base, lams = por_id.get(s["usa"], (None, []))
        s["arquivo"] = f"{s['data'][:2]}-{s['data'][3:]}.png"
        imagens.append((story_html(s, base, lams, base["status"] if base else "rascunho", cfg), *STORY, saida / "stories" / s["arquivo"]))
    M.renderizar(imagens)
    pagina = saida / "simulacao-perfil.html"
    pagina.write_text(simulacao_html(perf, pecas, stories, cfg), encoding="utf-8", newline="\n")
    print(f"{len(imagens)} imagens e a simulação em {saida}")
    return pagina


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mes", default="2026-11", help="calendário do marketing (AAAA-MM)")
    gerar(ap.parse_args().mes)
