"""Gera site/orgatec-template2.html: o design system ORGATEC em uma página estática.

Lê os tokens e o CSS dos componentes de design-system/orgatec-template2/ (a mesma fonte do
artifact publicado) e monta a página sem React, com a marcação que os componentes produzem.

Executar:  python tools/gerar_design_system.py
"""
import base64
import html
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DS = RAIZ / "design-system" / "orgatec-template2"
SAIDA = RAIZ / "site" / "orgatec-template2.html"
SAIDA_AVULSA = RAIZ / "dist" / "orgatec-template2.html"
e = html.escape


def externalizar_script(pagina: str, destino: Path, src: str) -> str:
    """Grava o script embutido da página num arquivo e troca por <script src> (a CSP do site não permite script embutido)."""
    ini = pagina.rindex("<script>\n")
    fim = pagina.index("</script>", ini)
    destino.write_text("/* Gerado junto com a página. Não edite à mão. */\n" + pagina[ini + len("<script>\n"):fim].strip() + "\n",
                       encoding="utf-8", newline="\n")
    return pagina[:ini] + f'<script src="{src}"></script>' + pagina[fim + len("</script>"):]


def valor(v, tema):
    return v if isinstance(v, str) else v.get(tema, v.get("claro"))


def selo(tom="pendente", texto=None):
    texto = texto or {"pendente": "pendente de validação", "definido": "definido"}.get(tom, "")
    return f'<span class="og-selo og-selo-{tom}">{e(texto)}</span>'


def assinatura(variante="horizontal", tom="claro"):
    alt = {"horizontal": 64, "vertical": 80, "reduzida": 32}[variante]
    img = "orgatec-simbolo-branco.svg" if tom == "escuro" else "orgatec-simbolo.svg"
    desc = "" if variante == "reduzida" else '<span class="og-descritor">Inteligência Tributária</span>'
    return (f'<span class="og-assinatura og-assinatura-{variante} og-tom-{tom}" role="img" aria-label="ORGATEC">'
            f'<img class="og-simbolo" src="assets/marca/{img}" alt="" style="height:{alt}px;width:{round(alt * 314 / 347)}px">'
            f'<span class="og-assinatura-texto"><span class="og-nome">ORGATEC</span>{desc}</span></span>')


def botao(texto, variante="primario", tamanho="md", href=None):
    cls = f"og-btn og-btn-{variante} og-btn-{tamanho}"
    if href:
        return f'<a class="{cls}" href="{e(href)}" target="_blank" rel="noopener">{e(texto)}</a>'
    return f'<button type="button" class="{cls}">{e(texto)}</button>'


def citacao(rotulo, url=None, validado=True):
    alvo = f'<a class="og-link" href="{e(url)}" target="_blank" rel="noopener">{e(rotulo)}</a>' if url else f"<span>{e(rotulo)}</span>"
    return f'<span class="og-citacao">{alvo}{"" if validado else selo()}</span>'


def cartao(ref, titulo, texto, href="#", pendente=False):
    tag = "a" if href else "div"
    attr = f' href="{e(href)}"' if href else ""
    return (f'<{tag} class="og-cartao"{attr}><span class="og-cartao-ref">{e(ref)}</span>'
            f'<h3 class="og-cartao-titulo">{e(titulo)}{selo() if pendente else ""}</h3>'
            f'<p class="og-cartao-texto">{e(texto)}</p></{tag}>')


def campo(id_, rotulo, tamanho="md", placeholder="", ajuda=None, erro=None, opcoes=None, tipo="text", valor_=""):
    cls = f"og-campo-controle og-campo-{tamanho}" + (" og-campo-invalido" if erro else "")
    desc = f' aria-describedby="{id_}-desc"' if (erro or ajuda) else ""
    if opcoes:
        ctrl = f'<select id="{id_}" class="{cls}"{desc}>' + "".join(f'<option value="{v}">{e(r)}</option>' for v, r in opcoes) + "</select>"
    else:
        extra = ' aria-invalid="true"' if erro else ""
        ctrl = f'<input id="{id_}" type="{tipo}" class="{cls}" placeholder="{e(placeholder)}" value="{e(valor_)}"{desc}{extra}>'
    nota = (f'<p id="{id_}-desc" class="og-campo-erro" role="alert">{e(erro)}</p>' if erro
            else f'<p id="{id_}-desc" class="og-campo-ajuda">{e(ajuda)}</p>' if ajuda else "")
    return f'<div class="og-campo"><label for="{id_}" class="og-campo-rotulo">{e(rotulo)}</label>{ctrl}{nota}</div>'


def codigo(txt):
    return f'<pre class="ds-codigo"><code>{e(txt)}</code></pre>'


def md_inline(txt):
    """Markdown mínimo do manual: `código` e **negrito**."""
    import re
    t = e(txt)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)


def manual(md):
    """README.md → HTML (parágrafos, ## seções e listas)."""
    out, lista = [], False
    for linha in md.splitlines():
        if linha.startswith("- "):
            if not lista:
                out.append("<ul>"); lista = True
            out.append(f"<li>{md_inline(linha[2:])}</li>")
            continue
        if lista:
            out.append("</ul>"); lista = False
        if linha.startswith("## "):
            out.append(f"<h3>{e(linha[3:])}</h3>")
        elif linha.strip():
            out.append(f"<p>{md_inline(linha)}</p>")
    if lista:
        out.append("</ul>")
    return "\n".join(out)


def main():
    tokens = json.loads((DS / "tokens.json").read_text(encoding="utf-8"))
    css_tokens = (DS / "tokens.css").read_text(encoding="utf-8")
    css_comp = (DS / "components" / "bundle.css").read_text(encoding="utf-8").replace("body {", ".ds-body-og {", 1)
    readme = (DS / "README.md").read_text(encoding="utf-8")
    cores = tokens["color"]["tokens"]

    def resolve(nome, tema):
        t = next(c for c in cores if c["name"] == nome)
        v = valor(t["value"], tema)
        return resolve(v[1:-1], tema) if v.startswith("{") else v

    amostras = "".join(
        f'<div class="ds-cor"><div class="ds-cor-bloco" style="background:var(--{c["name"]})"></div>'
        f'<div class="ds-cor-info"><b>{c["name"]}</b><span class="ds-mono">{e(resolve(c["name"], "claro"))}'
        + (f' · {e(resolve(c["name"], "escuro"))}' if resolve(c["name"], "escuro") != resolve(c["name"], "claro") else "")
        + f'</span><small>{e(c["usage"])}</small></div></div>' for c in cores)

    tipos = []
    for g in tokens["type"]["groups"]:
        tipos.append(f'<h3 class="ds-h3">{e(g["name"])}</h3>')
        for s in g["styles"]:
            esp = f' · {s["letterSpacing"]}' if "letterSpacing" in s else ""
            tipos.append(f'<div class="ds-tipo"><div class="ds-tipo-meta"><b>{s["name"]}</b><span class="ds-mono">{s["fontSize"]} / {s["lineHeight"]} · {s["fontWeight"]}{esp}</span>'
                         f'<small>{e(s.get("usage", ""))}</small></div><div class="{s["name"]} ds-tipo-amostra">{e(s["sample"])}</div></div>')

    espacos = "".join(f'<div class="ds-medida"><span class="ds-barra" style="width:var(--{t["name"]})"></span><b>{t["name"]}</b><span class="ds-mono">{t["value"]}</span><small>{e(t["usage"])}</small></div>'
                      for t in tokens["spacing"]["tokens"])
    raios = "".join(f'<div class="ds-raio"><div class="ds-raio-caixa" style="border-radius:var(--{t["name"]})"></div><b>{t["name"]}</b><span class="ds-mono">{t["value"]}</span><small>{e(t["usage"])}</small></div>'
                    for t in tokens["radius"]["tokens"])
    sombras = "".join(f'<div class="ds-raio"><div class="ds-raio-caixa ds-sombra" style="box-shadow:var(--{t["name"]})"></div><b>{t["name"]}</b><small>{e(t["usage"])}</small></div>'
                      for t in tokens["shadow"]["tokens"])

    arquivos = [("Símbolo", ["orgatec-simbolo.svg", "orgatec-simbolo-mono.svg", "orgatec-simbolo-branco.svg"]),
                ("Assinaturas", ["orgatec-horizontal.svg", "orgatec-horizontal-negativo.svg", "orgatec-horizontal-mono.svg", "orgatec-vertical.svg"]),
                ("Ícones", ["orgatec-app.svg", "orgatec-app-escuro.svg", "favicon.svg", "og-image.png"])]
    logos = "".join(
        f'<h3 class="ds-h3">{g}</h3><div class="ds-grade-arquivos">' + "".join(
            f'<figure class="ds-arquivo{" ds-arquivo-escuro" if ("branco" in a or "negativo" in a) else ""}"><img src="assets/marca/{a}" alt="{a}"><figcaption><a class="og-link" href="assets/marca/{a}" download>{a}</a></figcaption></figure>'
            for a in fs) + "</div>" for g, fs in arquivos)

    componentes = [
        ("Assinatura", "Logotipo: símbolo de quatro faixas + nome. Fundo claro: tom claro; fundo escuro: tom escuro.",
         f'<div class="og-painel-branco">{assinatura()}</div><div class="og-palco">{assinatura(tom="escuro")}</div>'
         f'<div class="og-painel-branco ds-linha-solta">{assinatura("vertical")}{assinatura("reduzida")}</div>',
         'h(OrgatecUI.Assinatura, { variante: "horizontal", tom: "claro" })'),
        ("Botao", "Ação ou link. Verde só no WhatsApp; translúcido só sobre o hero.",
         f'<div class="og-linha ds-sem-pad">{botao("Testar Simulador Tributário", tamanho="lg")}{botao("Falar no WhatsApp", "contato", href="https://wa.me/5562992949161")}{botao("Portal do Cliente", "contorno", href="https://portal.orgatec.io")}</div>'
         f'<div class="og-palco og-linha">{botao("Testar Simulador Tributário", tamanho="lg")}{botao("Agendar Diagnóstico com Especialista", "sobre-palco", "lg")}</div>',
         'h(OrgatecUI.Botao, { variante: "contato", href: "https://wa.me/5562992949161" }, "Falar no WhatsApp")'),
        ("Selo", "Estado da informação. \"pendente de validação\" em toda regra ainda não confirmada.",
         f'<div class="og-linha ds-sem-pad">{selo()}{selo("definido", "Integração: Sieg")}{selo("pendente", "ERP do portal: pendente de definição")}</div>'
         f'<div class="og-palco">{selo("norma", "EC 132/2023 • LC 214/2025 • Split Payment")}</div>',
         'h(OrgatecUI.Selo, { tom: "pendente" })'),
        ("CitacaoFonte", "Norma e dispositivo com link oficial; sem confirmação, ganha o selo pendente.",
         f'<div class="og-pilha ds-sem-pad">{citacao("LC 214/2025, art. 41, §§ 3º e 4º", "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm")}{citacao("Lei 6.489/2002 (PA)", validado=False)}</div>',
         'h(OrgatecUI.CitacaoFonte, { rotulo: "LC 214/2025, art. 41", url: "https://www.planalto.gov.br/...", validado: true })'),
        ("CartaoHub", "Cartão do Hub da Reforma: referência legal em mono, título e resumo.",
         '<div class="ds-grade-cartoes">' + cartao("LC 214/2025", "A lei do IBS, da CBS e do IS", "Estrutura da lei, cronograma de transição e o que já vale em 2026.")
         + cartao("LC 214/2025 · art. 41", "Simples Híbrido", "Quando vale recolher IBS e CBS fora do DAS e a janela de opção.")
         + cartao("Calendário estadual", "ICMS no Pará", "Dia de vencimento a confirmar na SEFAZ-PA.", href=None, pendente=True) + "</div>",
         'h(OrgatecUI.CartaoHub, { referencia: "LC 214/2025", titulo: "A lei do IBS, da CBS e do IS", href: "reforma/lc-214-2025.html" }, "Resumo")'),
        ("Campo", "Rótulo + campo + ajuda ou erro. id obrigatório; opcoes vira select.",
         '<div class="ds-grade-cartoes">' + campo("dsFat", "Faturamento anual (R$)", "lg", "ex.: 2.400.000")
         + campo("dsUf", "UF", "lg", opcoes=[("GO", "Goiás"), ("TO", "Tocantins"), ("PA", "Pará")])
         + campo("dsEmail", "E-mail", tipo="email", valor_="email-invalido", erro="E-mail inválido.")
         + campo("dsWhats", "WhatsApp", placeholder="(62) 99999-0000", ajuda="Só para retorno do diagnóstico.") + "</div>",
         'h(OrgatecUI.Campo, { id: "faturamento", rotulo: "Faturamento anual (R$)", tamanho: "lg", inputMode: "decimal" })'),
        ("Consentimento", "Caixa LGPD, nunca pré-marcada; sem ela o envio é bloqueado.",
         '<label class="og-consentimento"><input id="dsConsent" type="checkbox"><span>Autorizo a ORGATEC a usar estes dados e o resultado da simulação para entrar em contato sobre o diagnóstico tributário, conforme a <a href="privacidade.html">Política de Privacidade</a> (LGPD, Lei nº 13.709/2018). Posso revogar a qualquer momento.</span></label>',
         'h(OrgatecUI.Consentimento, { id: "consent" }, "Autorizo a ORGATEC ...")'),
    ]
    comps = "".join(
        f'<article class="ds-comp" id="comp-{n}"><header><h3 class="ds-h3">{n}</h3><p>{e(d)}</p></header>'
        f'<div class="ds-comp-palco">{demo}</div>{codigo(uso)}</article>' for n, d, demo, uso in componentes)

    pontos = "".join(f'<circle class="ponto" cx="{80 + 16 * i}" cy="{120 + 16 * j}" r="1.5"/>' for i in range(5) for j in range(8))
    nav = [("capa", "Capa"), ("manual", "Manual"), ("cores", "Cores"), ("tipografia", "Tipografia"), ("medidas", "Medidas"), ("logotipos", "Logotipos"), ("componentes", "Componentes")]

    pagina = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>orgatec-template2 | Design system ORGATEC</title>
    <meta name="description" content="Design system ORGATEC (orgatec-template2): cores, tipografia, medidas, logotipos e componentes do site.">
    <meta name="robots" content="noindex">
    <link rel="icon" href="assets/marca/favicon.svg" type="image/svg+xml">
    <link rel="icon" href="assets/marca/favicon-32.png" sizes="32x32" type="image/png">
    <link rel="apple-touch-icon" href="assets/marca/apple-touch-icon.png">
    <meta name="theme-color" content="#072563">
    <link href="assets/fontes/fontes.css" rel="stylesheet">
    <!-- Gerado por tools/gerar_design_system.py a partir de design-system/orgatec-template2/. Não edite à mão. -->
    <style>
{css_tokens}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="claro"]) {{ {" ".join(f"--{t['name']}: {valor(t['value'], 'escuro') if not valor(t['value'], 'escuro').startswith('{') else 'var(--' + valor(t['value'], 'escuro')[1:-1] + ')'};" for t in cores + tokens["shadow"]["tokens"] if isinstance(t["value"], dict))} color-scheme: dark; }} }}
[data-theme="escuro"] {{ color-scheme: dark; }}
{css_comp}
html {{ scroll-behavior: smooth; }}
body {{ margin: 0; font-family: var(--font-sans); background: var(--fundo); color: var(--tinta-texto); -webkit-font-smoothing: antialiased; }}
.ds-topo {{ position: sticky; top: 0; z-index: 20; background: var(--fundo); border-bottom: 1px solid var(--linha); }}
.ds-topo-in {{ max-width: 1200px; margin: 0 auto; padding: 0 var(--espaco-4); height: 64px; display: flex; align-items: center; justify-content: space-between; gap: var(--espaco-4); }}
.ds-marca {{ display: flex; align-items: center; gap: var(--espaco-2); text-decoration: none; color: var(--tinta); font-weight: 800; letter-spacing: .04em; font-size: 18px; white-space: nowrap; }}
.ds-marca small {{ font-family: var(--font-mono); font-weight: 400; letter-spacing: 0; font-size: 12px; color: var(--tinta-fraca); }}
.ds-nav {{ display: none; gap: var(--espaco-5); font-size: 14px; }}
.ds-nav a {{ color: var(--tinta-suave); text-decoration: none; }}
.ds-nav a:hover {{ color: var(--link); }}
@media (min-width: 1024px) {{ .ds-nav {{ display: flex; }} }}
.ds-tema {{ font: inherit; font-size: 13px; padding: 6px var(--espaco-3); border-radius: var(--raio-lg); border: 1px solid var(--linha-campo); background: transparent; color: var(--tinta-texto); cursor: pointer; white-space: nowrap; }}
.ds-tema:focus-visible {{ outline: none; box-shadow: var(--foco); }}
main {{ max-width: 1200px; margin: 0 auto; padding: var(--espaco-10) var(--espaco-4) var(--espaco-20); display: grid; gap: var(--espaco-20); }}
section {{ scroll-margin-top: 80px; min-width: 0; }}
.ds-sobre {{ font-size: 12px; line-height: 16px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--link); margin: 0 0 var(--espaco-2); }}
.ds-h2 {{ font-size: 30px; line-height: 36px; font-weight: 700; color: var(--tinta); margin: 0 0 var(--espaco-6); text-wrap: balance; }}
.ds-h3 {{ font-size: 16px; line-height: 24px; font-weight: 700; color: var(--tinta); margin: var(--espaco-6) 0 var(--espaco-3); }}
.ds-mono {{ font-family: var(--font-mono); font-size: 12px; color: var(--tinta-suave); }}
.ds-capa {{ position: relative; height: 288px; border-radius: var(--raio-2xl); overflow: hidden; background: var(--superficie); border: 1px solid var(--linha); }}
.ds-capa svg {{ position: absolute; right: 0; top: 0; height: 288px; width: 480px; }}
.ds-capa .navy {{ fill: var(--faixa-1); }} .ds-capa .azul {{ fill: var(--faixa-2); }} .ds-capa .medio {{ fill: var(--faixa-3); }} .ds-capa .ciano {{ fill: var(--faixa-4); }} .ds-capa .ponto {{ fill: var(--marca-ciano-luz); }}
.ds-capa-txt {{ position: absolute; left: var(--espaco-8); bottom: var(--espaco-8); }}
.ds-capa-txt h1 {{ margin: 0; font-size: 84px; line-height: .92; font-weight: 800; letter-spacing: .04em; color: var(--tinta); }}
.ds-capa-txt p {{ margin: var(--espaco-3) 0 0 4px; font-size: 13px; font-weight: 600; letter-spacing: .32em; text-transform: uppercase; color: var(--tinta-suave); }}
@media (max-width: 760px) {{
  .ds-capa {{ height: 320px; }}
  .ds-capa svg {{ width: 100%; height: 160px; }}
  .ds-capa-txt {{ left: var(--espaco-5); bottom: var(--espaco-5); }}
  .ds-capa-txt h1 {{ font-size: 52px; }}
  .ds-capa-txt p {{ font-size: 11px; letter-spacing: .24em; }}
}}
.ds-manual {{ max-width: 72ch; font-size: 16px; line-height: 26px; color: var(--tinta-texto); }}
.ds-manual h3 {{ font-size: 20px; line-height: 28px; color: var(--tinta); margin: var(--espaco-8) 0 var(--espaco-2); }}
.ds-manual ul {{ padding-left: 1.2em; margin: 0; display: grid; gap: var(--espaco-2); }}
.ds-manual code, .ds-cor-info small code {{ font-family: var(--font-mono); font-size: .85em; background: var(--linha); padding: 1px 5px; border-radius: 4px; }}
.ds-grade-cores {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--espaco-3); }}
.ds-cor {{ background: var(--superficie); border: 1px solid var(--linha); border-radius: var(--raio-xl); overflow: hidden; display: flex; flex-direction: column; }}
.ds-cor-bloco {{ height: 64px; border-bottom: 1px solid var(--linha); }}
.ds-cor-info {{ padding: var(--espaco-3); display: grid; gap: 2px; min-width: 0; }}
.ds-cor-info b {{ color: var(--tinta); font-size: 14px; }}
.ds-cor-info small, .ds-tipo small, .ds-medida small, .ds-raio small {{ color: var(--tinta-suave); font-size: 12px; line-height: 17px; }}
.ds-tipo {{ display: grid; grid-template-columns: 240px 1fr; gap: var(--espaco-6); padding: var(--espaco-4) 0; border-top: 1px solid var(--linha); align-items: baseline; }}
.ds-tipo-meta {{ display: grid; gap: 2px; }}
.ds-tipo-meta b {{ color: var(--tinta); font-size: 14px; }}
.ds-tipo-amostra {{ color: var(--tinta); min-width: 0; overflow-wrap: anywhere; }}
.titulo-hero.ds-tipo-amostra {{ font-size: clamp(32px, 5vw, 60px); }}
@media (max-width: 760px) {{ .ds-tipo {{ grid-template-columns: 1fr; gap: var(--espaco-2); }} }}
.ds-medidas {{ display: grid; gap: var(--espaco-2); }}
.ds-medida {{ display: grid; grid-template-columns: 96px 110px 56px 1fr; gap: var(--espaco-3); align-items: center; }}
.ds-barra {{ height: 12px; background: var(--acao); border-radius: 2px; max-width: 96px; }}
.ds-medida b, .ds-raio b {{ color: var(--tinta); font-size: 14px; }}
@media (max-width: 760px) {{ .ds-medida {{ grid-template-columns: 96px 1fr; }} .ds-medida small {{ grid-column: 1 / -1; }} }}
.ds-grade-raios {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: var(--espaco-4); }}
.ds-raio {{ display: grid; gap: 4px; }}
.ds-raio-caixa {{ height: 72px; background: var(--superficie); border: 2px solid var(--acao); margin-bottom: var(--espaco-2); }}
.ds-sombra {{ border-color: var(--linha); border-radius: var(--raio-xl); }}
.ds-grade-arquivos {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--espaco-3); }}
.ds-arquivo {{ margin: 0; background: #ffffff; border: 1px solid var(--linha); border-radius: var(--raio-xl); padding: var(--espaco-4); display: grid; gap: var(--espaco-3); justify-items: center; }}
.ds-arquivo-escuro {{ background: var(--palco); }}
.ds-arquivo img {{ height: 88px; width: 100%; object-fit: contain; }}
.ds-arquivo figcaption {{ font-size: 12px; overflow-wrap: anywhere; text-align: center; }}
.ds-arquivo-escuro .og-link {{ color: #0ea5e9; }}
.ds-comps {{ display: grid; gap: var(--espaco-6); }}
.ds-comp {{ background: var(--superficie); border: 1px solid var(--linha); border-radius: var(--raio-2xl); padding: var(--espaco-6); min-width: 0; }}
.ds-comp header p {{ margin: 0 0 var(--espaco-4); color: var(--tinta-suave); font-size: 14px; }}
.ds-comp .ds-h3 {{ margin-top: 0; font-family: var(--font-mono); }}
.ds-comp-palco {{ display: grid; gap: var(--espaco-4); }}
.ds-comp-palco > * {{ min-width: 0; }}
.ds-sem-pad {{ padding: 0; }}
.ds-linha-solta {{ display: flex; flex-wrap: wrap; gap: var(--espaco-10); align-items: center; }}
.ds-grade-cartoes {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--espaco-4); }}
.ds-codigo {{ margin: var(--espaco-4) 0 0; padding: var(--espaco-3) var(--espaco-4); background: var(--palco); color: var(--palco-texto); border-radius: var(--raio-lg); font-family: var(--font-mono); font-size: 12px; line-height: 18px; overflow-x: auto; }}
.og-palco .og-assinatura, .og-painel-branco .og-assinatura {{ max-width: 100%; }}
@media (max-width: 480px) {{ .ds-marca small {{ display: none; }} .og-selo-norma {{ white-space: normal; }} .ds-comp {{ padding: var(--espaco-4); }} .og-palco {{ padding: var(--espaco-4); }} }}
@media (max-width: 480px) {{ .og-assinatura-horizontal .og-nome {{ font-size: 34px; }} .og-assinatura-horizontal .og-simbolo {{ height: 48px !important; width: 43px !important; }} .og-descritor {{ letter-spacing: .2em; }} .og-btn {{ white-space: normal; text-align: center; }} }}
footer {{ background: var(--palco); color: var(--palco-texto); font-size: 14px; }}
footer div {{ max-width: 1200px; margin: 0 auto; padding: var(--espaco-8) var(--espaco-4); display: flex; flex-wrap: wrap; gap: var(--espaco-3) var(--espaco-8); justify-content: space-between; align-items: center; }}
footer .ds-mono {{ color: #0ea5e9; }}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} * {{ transition: none !important; }} }}
    </style>
</head>
<body>
    <header class="ds-topo">
        <div class="ds-topo-in">
            <a href="index.html" class="ds-marca"><img src="assets/marca/orgatec-original.png" alt="" width="29" height="32">ORGATEC <small>orgatec-template2</small></a>
            <nav class="ds-nav" aria-label="Seções">{"".join(f'<a href="#{i}">{t}</a>' for i, t in nav[1:])}</nav>
            <button type="button" class="ds-tema" id="btnTema" aria-label="Alternar tema claro e escuro">Tema: automático</button>
        </div>
    </header>

    <main>
        <section id="capa" aria-label="Capa">
            <div class="ds-capa">
                <svg viewBox="0 0 480 288" aria-hidden="true">
                    <rect class="navy" x="40" y="-24" width="144" height="288" rx="16"/>
                    <rect class="azul" x="192" y="32" width="112" height="232" rx="16"/>
                    <rect class="medio" x="312" y="72" width="88" height="192" rx="16"/>
                    <rect class="ciano" x="408" y="112" width="64" height="152" rx="16"/>
                    {pontos}
                </svg>
                <div class="ds-capa-txt"><h1>ORGATEC</h1><p>Inteligência Tributária</p></div>
            </div>
        </section>

        <section id="manual">
            <p class="ds-sobre">Design system · orgatec-template2</p>
            <h2 class="ds-h2">Manual</h2>
            <div class="ds-manual">
{manual(readme)}
            </div>
        </section>

        <section id="cores">
            <p class="ds-sobre">{len(cores)} tokens · temas claro e escuro</p>
            <h2 class="ds-h2">Cores</h2>
            <div class="ds-grade-cores">{amostras}</div>
        </section>

        <section id="tipografia">
            <p class="ds-sobre">Inter · JetBrains Mono</p>
            <h2 class="ds-h2">Tipografia</h2>
            {"".join(tipos)}
        </section>

        <section id="medidas">
            <p class="ds-sobre">Base de 4 px</p>
            <h2 class="ds-h2">Espaço, cantos e sombras</h2>
            <h3 class="ds-h3">Espaçamento</h3>
            <div class="ds-medidas">{espacos}</div>
            <h3 class="ds-h3">Cantos</h3>
            <div class="ds-grade-raios">{raios}</div>
            <h3 class="ds-h3">Sombras e foco</h3>
            <div class="ds-grade-raios">{sombras}</div>
        </section>

        <section id="logotipos">
            <p class="ds-sobre">assets/marca</p>
            <h2 class="ds-h2">Logotipos</h2>
            {logos}
        </section>

        <section id="componentes">
            <p class="ds-sobre">OrgatecUI · {len(componentes)} componentes</p>
            <h2 class="ds-h2">Componentes</h2>
            <div class="ds-comps">{comps}</div>
        </section>
    </main>

    <footer>
        <div>
            <span>ORGATEC · CNPJ 13.155.211/0001-45 · Resp. técnico: Robson Alain Veloso · <span class="ds-mono">CRC-TO 002032/O-5 T-GO</span></span>
            <span><a class="og-link" href="marca.html">Marca</a> · <a class="og-link" href="privacidade.html">Política de Privacidade (LGPD)</a> · NBC PG 01</span>
        </div>
    </footer>

    <script>
    (function () {{
        var ordem = ['auto', 'claro', 'escuro'], nomes = {{ auto: 'automático', claro: 'claro', escuro: 'escuro' }};
        var btn = document.getElementById('btnTema'), atual = 'auto';
        try {{ atual = localStorage.getItem('og-tema') || 'auto'; }} catch (e) {{}}
        function aplica() {{
            if (atual === 'auto') document.documentElement.removeAttribute('data-theme');
            else document.documentElement.setAttribute('data-theme', atual);
            btn.textContent = 'Tema: ' + nomes[atual];
        }}
        btn.addEventListener('click', function () {{
            atual = ordem[(ordem.indexOf(atual) + 1) % ordem.length];
            try {{ localStorage.setItem('og-tema', atual); }} catch (e) {{}}
            aplica();
        }});
        aplica();
    }})();
    </script>
</body>
</html>
"""
    pagina_site = externalizar_script(pagina, RAIZ / "site" / "assets" / "js" / "ds-template2.js", "assets/js/ds-template2.js")
    SAIDA.write_text(pagina_site, encoding="utf-8", newline="\n")  # a versão avulsa (dist) mantém o script embutido
    print(f"gerado: {SAIDA.relative_to(RAIZ)} ({len(pagina) // 1024} KB)")

    # Versão avulsa para download: logotipos embutidos como data URI, links do site apontando para o domínio.
    avulsa = pagina
    for arq in sorted(a for a in (RAIZ / "site" / "assets" / "marca").iterdir() if a.is_file()):  # marca/holo/ é pasta
        tipo = "image/svg+xml" if arq.suffix == ".svg" else "image/png"
        uri = f"data:{tipo};base64,{base64.b64encode(arq.read_bytes()).decode()}"
        avulsa = avulsa.replace(f'href="assets/marca/{arq.name}" download', f'href="{uri}" download="{arq.name}"')
        avulsa = avulsa.replace(f"assets/marca/{arq.name}", uri)
    # Arquivo único: sem a pasta assets/fontes, as fontes voltam a vir do Google Fonts.
    avulsa = avulsa.replace('<link href="assets/fontes/fontes.css" rel="stylesheet">',
                            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">')
    for pag in ("index.html", "marca.html", "privacidade.html"):
        avulsa = avulsa.replace(f'href="{pag}"', f'href="https://orgatec.io/{pag}"')
    if "assets/marca/" in avulsa:
        raise SystemExit("versão avulsa ainda aponta para assets/marca/: arquivo da marca não embutido")
    SAIDA_AVULSA.parent.mkdir(exist_ok=True)
    SAIDA_AVULSA.write_text(avulsa, encoding="utf-8", newline="\n")
    print(f"gerado: {SAIDA_AVULSA.relative_to(RAIZ)} ({len(avulsa) // 1024} KB, arquivo único)")
    gerar_tema_site(tokens, css_tokens)


# ---------------------------------------------------------------------------------------------
# TEMA DO SITE: design ORGATEC Trilha (decisão D6, 31/10/2026: "Aplicar ao site").
# Cores, fontes e estilo flutuante vêm de design-system/orgatec-trilha/tokens.json (7 paletas);
# os componentes og-* e as medidas (espaços, raios) continuam do orgatec-template2, agora lendo as
# cores do Trilha por apelidos (--fundo → --bg, --acao → --brand ...).
# Saídas: site/assets/js/tema.js (paletas + seletor "Cores"), site/assets/css/orgatec.css e
# site/assets/js/tema-tailwind.js (classes do Tailwind, inclusive white/slate/brandBlue, ligadas às variáveis).
# ---------------------------------------------------------------------------------------------
TRILHA = RAIZ / "design-system" / "orgatec-trilha" / "tokens.json"
PADRAO = "azul-fl-esc"          # paleta padrão do site: Azul flutuante escuro (escolha da ORGATEC em 02/11/2026; antes, Azul flutuante)
ESCURA = "azul-fl-esc"          # paleta do painel escuro da página inicial (.folha-escura)
AUTO = ("verde", "noite")       # "Automático": claro e escuro do sistema
CORES_TRILHA = ["bg", "surface", "surface2", "ink", "muted", "line", "brand", "brand-ink", "brand-soft",
                "hl", "hl-ink", "hl-soft", "warn", "warn-soft", "focus"]
CONTATO = {"contato": "#10b981", "contato-hover": "#059669", "sobre-contato": "#ffffff"}  # verde reservado ao WhatsApp

# Nomes do orgatec-template2 usados pelos componentes og-* e pelas páginas → cor do Trilha
APELIDOS = {
    "fundo": "bg", "superficie": "surface", "linha": "line", "linha-campo": "line", "tinta": "ink", "tinta-texto": "ink",
    "tinta-suave": "muted", "tinta-fraca": "muted", "acao": "brand", "acao-hover": "brand", "sobre-acao": "brand-ink",
    "link": "brand", "descritor": "brand", "palco": "surface2", "palco-texto": "muted", "palco-ponto": "hl",
    "pendente-fundo": "warn-soft", "pendente-texto": "warn", "pendente-borda": "warn",
    "definido-fundo": "brand-soft", "definido-texto": "brand", "aviso-fundo": "warn-soft", "aviso-texto": "warn", "aviso-borda": "warn",
    "faixa-1": "brand", "faixa-2": "brand", "faixa-3": "hl", "faixa-4": "hl",
}
# Classes antigas do Tailwind (primeira versão do site, app.js, Hub) → cor do Trilha, para não reescrever cada página
PALETA_TAILWIND = {
    "white": "surface", "black": "ink", "dark": "ink", "lightBg": "bg", "brandBlue": "brand", "brandCyan": "brand", "navy": "brand",
    "slate": {50: "bg", 100: "line", 200: "line", 300: "line", 400: "muted", 500: "muted", 600: "muted", 700: "ink", 800: "ink", 900: "ink"},
    "blue": {50: "brand-soft", 100: "brand-soft", 200: "line", 700: "brand", 800: "brand"},
    "sky": {300: "hl"},
    "cyan": {100: "brand-soft", 300: "hl", 800: "brand"},
    "emerald": {50: "brand-soft", 100: "brand-soft", 200: "line", 300: "hl", 700: "brand", 800: "brand"},
    "amber": {50: "warn-soft", 100: "warn-soft", 200: "warn-soft", 500: "warn", 700: "warn", 800: "warn", 900: "warn"},
    "red": {50: "warn-soft", 200: "warn-soft", 600: "warn", 700: "warn"},
}


def _rgb(h):
    h = h.lstrip("#")
    return " ".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def _lum(h):
    v = [int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def gerar_tema_site(tokens_t2, css_tokens):
    tri = json.loads(TRILHA.read_text(encoding="utf-8"))
    cores = {t["name"]: t["value"] for t in tri["color"]["tokens"]}
    temas = {}
    for th in tri["color"]["themes"]:
        vals = {k: cores[k][th["id"]] for k in CORES_TRILHA}
        temas[th["id"]] = {"nome": th["name"], "escuro": _lum(vals["bg"]) < 0.2, "flutuante": th["id"].startswith("azul-fl"), "cores": vals}

    def bloco(vals):
        return "".join(f"--{k}:{v};--{k}-rgb:{_rgb(v)};" for k, v in vals.items())

    # ---- tema.js: aplica a paleta antes de desenhar a página (carregar no <head>, sem defer)
    js = f"""/* Gerado por tools/gerar_design_system.py a partir de design-system/orgatec-trilha/tokens.json. Não edite à mão.
   Paletas do design ORGATEC Trilha. Carregue no <head>, depois de orgatec.css: aplica a paleta salva antes da pintura
   (sem piscar) e liga o botão "Cores" (#btnCores) quando a página termina de carregar. */
(function (root, factory) {{
  if (typeof module === 'object' && module.exports) module.exports = factory(null);
  else (root.Orgatec = root.Orgatec || {{}}).tema = factory(root);
}})(this, function (win) {{
  'use strict';
  var TEMAS = {json.dumps(temas, ensure_ascii=False)};
  var PADRAO = '{PADRAO}', AUTO = {json.dumps(list(AUTO))}, CHAVE = 'orgatec.tema';
  var ORDEM = ['auto'].concat(Object.keys(TEMAS));
  function rgb(h) {{ var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255].join(' '); }}
  function escuroDoSistema() {{ return !!(win && win.matchMedia && win.matchMedia('(prefers-color-scheme: dark)').matches); }}
  /* 'auto' → Verde Toga ou Noturno, conforme o sistema; id desconhecido → padrão. */
  function resolver(id, escuro) {{ if (id === 'auto') return escuro ? AUTO[1] : AUTO[0]; return TEMAS[id] ? id : PADRAO; }}
  function nome(id) {{ return id === 'auto' ? 'Automático' : (TEMAS[id] ? TEMAS[id].nome : TEMAS[PADRAO].nome); }}
  var atual = PADRAO;

  function aplicar(id) {{
    if (!win) return null;
    var doc = win.document, r = doc.documentElement, efetivo = resolver(id, escuroDoSistema()), t = TEMAS[efetivo];
    Object.keys(t.cores).forEach(function (k) {{ r.style.setProperty('--' + k, t.cores[k]); r.style.setProperty('--' + k + '-rgb', rgb(t.cores[k])); }});
    r.style.setProperty('color-scheme', t.escuro ? 'dark' : 'light');
    if (t.flutuante) r.setAttribute('data-float', t.escuro ? 'dark' : 'light'); else r.removeAttribute('data-float');
    r.setAttribute('data-tema', efetivo);
    r.setAttribute('data-escuro', t.escuro ? 'sim' : 'nao');
    atual = TEMAS[id] || id === 'auto' ? id : PADRAO;
    // O símbolo não muda com a paleta: fica sempre com as cores originais (decisão da ORGATEC, 31/10/2026).
    return efetivo;
  }}

  function salvo() {{ try {{ return win.localStorage.getItem(CHAVE) || PADRAO; }} catch (e) {{ return PADRAO; }} }}
  function escolher(id) {{ aplicar(id); try {{ win.localStorage.setItem(CHAVE, id); }} catch (e) {{}} }}

  function montarSeletor() {{
    // #btnCores no cabeçalho e, em telas estreitas, o item "Cores" do menu (data-abrir-cores)
    var doc = win.document, botoes = Array.prototype.slice.call(doc.querySelectorAll('#btnCores, [data-abrir-cores]')), btn = botoes[0];
    if (!btn) return;
    var pop = doc.createElement('div');
    pop.id = 'temaPop'; pop.className = 'tema-pop'; pop.hidden = true; pop.setAttribute('role', 'dialog'); pop.setAttribute('aria-label', 'Escolher cores');
    var toast = doc.createElement('div'); toast.className = 'tema-toast'; toast.setAttribute('role', 'status'); toast.setAttribute('aria-live', 'polite');
    doc.body.appendChild(pop); doc.body.appendChild(toast);
    var tt;
    function desenhar() {{
      pop.innerHTML = '<p class="tema-pop-titulo">Cores</p>' + ORDEM.map(function (id) {{
        var c = id === 'auto' ? [TEMAS[AUTO[0]].cores, TEMAS[AUTO[1]].cores] : [TEMAS[id].cores];
        var sw = id === 'auto' ? [c[0].brand, c[0].hl, c[0].bg, c[1].bg] : [c[0].brand, c[0].hl, c[0].ink, c[0].bg];
        return '<button type="button" class="tema-opcao" data-tema-id="' + id + '" aria-pressed="' + (id === atual) + '"><span class="tema-sw">' +
          sw.map(function (x) {{ return '<i style="background:' + x + '"></i>'; }}).join('') + '</span>' + nome(id) + '</button>';
      }}).join('');
    }}
    function fechar() {{ pop.hidden = true; botoes.forEach(function (b) {{ b.setAttribute('aria-expanded', 'false'); }}); }}
    botoes.forEach(function (b) {{
      b.setAttribute('aria-controls', 'temaPop'); b.setAttribute('aria-expanded', 'false');
      b.addEventListener('click', function (ev) {{
        ev.stopPropagation(); desenhar(); btn = b;
        var r = b.getBoundingClientRect();
        pop.style.top = (r.bottom + 8) + 'px';
        pop.style.right = Math.max(8, doc.documentElement.clientWidth - r.right) + 'px';
        pop.hidden = !pop.hidden; b.setAttribute('aria-expanded', String(!pop.hidden));
      }});
    }});
    pop.addEventListener('click', function (ev) {{
      ev.stopPropagation();  // a lista é redesenhada: sem isso, o clique chega ao documento como "fora" e fecha o seletor
      var o = ev.target.closest('[data-tema-id]'); if (!o) return;
      var id = o.getAttribute('data-tema-id'); escolher(id); desenhar();
      toast.textContent = 'Cores: ' + nome(id); toast.classList.add('on');
      clearTimeout(tt); tt = setTimeout(function () {{ toast.classList.remove('on'); }}, 1800);
    }});
    doc.addEventListener('click', function (ev) {{ if (!pop.hidden && !pop.contains(ev.target) && botoes.indexOf(ev.target) < 0) fechar(); }});
    doc.addEventListener('keydown', function (ev) {{ if (ev.key === 'Escape' && !pop.hidden) {{ fechar(); btn.focus(); }} }});
  }}

  if (win) {{
    aplicar(salvo());
    if (win.matchMedia) {{
      var mq = win.matchMedia('(prefers-color-scheme: dark)');
      var mudou = function () {{ if (atual === 'auto') aplicar('auto'); }};
      if (mq.addEventListener) mq.addEventListener('change', mudou);
    }}
    var pronto = function () {{ aplicar(atual); montarSeletor(); }};
    if (win.document.readyState === 'loading') win.document.addEventListener('DOMContentLoaded', pronto); else pronto();
  }}
  return {{ TEMAS: TEMAS, PADRAO: PADRAO, AUTO: AUTO, ORDEM: ORDEM, resolver: resolver, nome: nome, aplicar: aplicar, escolher: escolher,
    atual: function () {{ return atual; }} }};
}});
"""
    (RAIZ / "site" / "assets" / "js" / "tema.js").write_text(js, encoding="utf-8", newline="\n")

    # ---- tema-tailwind.js: toda cor como rgb(var(--x-rgb) / alpha) para seguir a paleta e aceitar /10, /90 ...
    def c(nome):
        return f"rgb(var(--{nome}-rgb) / <alpha-value>)"

    cores_tw = {k: c(k) for k in CORES_TRILHA}
    cores_tw.update({k: c(v) for k, v in APELIDOS.items()})
    for nome, alvo in PALETA_TAILWIND.items():
        cores_tw[nome] = {str(n): c(a) for n, a in alvo.items()} if isinstance(alvo, dict) else c(alvo)
    cores_tw["emerald"]["600"] = CONTATO["contato-hover"]  # hover do botão de WhatsApp continua verde
    cores_tw.update({"accentGreen": CONTATO["contato"], "contato": CONTATO["contato"], "contato-hover": CONTATO["contato-hover"]})
    marca = {t["name"]: t["value"] for t in tokens_t2["color"]["tokens"] if t["name"].startswith("marca-")}
    cores_tw.update(marca)  # cores fixas do logotipo
    config = {"theme": {"extend": {"colors": cores_tw, "fontFamily": {
        "sans": ["var(--f-body)"], "display": ["var(--f-display)"], "mono": ["var(--f-mono)"]}}}}
    # Configuração do Tailwind compilado (pendência T3: sem o CDN de teste). O CSS final sai de
    #   npx tailwindcss@3.4.17 -c tailwind.config.js -i tools/tailwind-entrada.css -o site/assets/css/tailwind.css --minify
    # (tools/compilar_css.py faz isso). As classes são lidas das páginas e dos scripts do site.
    config["content"] = ["./site/**/*.html", "./site/assets/js/**/*.js"]
    (RAIZ / "tailwind.config.js").write_text(
        "/* Gerado por tools/gerar_design_system.py (design ORGATEC Trilha). Não edite à mão. */\n"
        f"module.exports = {json.dumps(config, ensure_ascii=False, indent=2)};\n", encoding="utf-8", newline="\n")
    antigo = RAIZ / "site" / "assets" / "js" / "tema-tailwind.js"
    if antigo.exists():
        antigo.unlink()  # era a configuração do Tailwind via CDN; o site agora usa o CSS compilado

    # ---- orgatec.css
    padrao = temas[PADRAO]["cores"]
    fixos = css_tokens[css_tokens.index(":root {", css_tokens.index('[data-theme="escuro"]')):]
    fixos = "\n".join(l for l in fixos.splitlines() if not l.startswith(".") and "--font-" not in l)  # só espaços e raios (fontes vêm do Trilha)
    marca_css = "".join(f"--{k}:{v};" for k, v in marca.items())
    apelidos_css = "".join(f"--{k}:var(--{v});--{k}-rgb:var(--{v}-rgb);" for k, v in APELIDOS.items())
    contato_css = "".join(f"--{k}:{v};--{k}-rgb:{_rgb(v)};" for k, v in CONTATO.items())
    comp = (DS / "components" / "bundle.css").read_text(encoding="utf-8")
    comp = "\n".join(l for l in comp.splitlines() if not l.startswith("body {"))
    css = f"""/* Gerado por tools/gerar_design_system.py. Não edite à mão.
   Design ORGATEC Trilha: cores de design-system/orgatec-trilha/tokens.json (tema.js troca a paleta em tempo real);
   componentes og-* e medidas de design-system/orgatec-template2/. Padrão: {temas[PADRAO]["nome"]}. */
:root{{{bloco(padrao)}color-scheme:{"dark" if temas[PADRAO]["escuro"] else "light"};
  {contato_css}{marca_css}
  --f-display:"Bricolage Grotesque","Segoe UI",system-ui,sans-serif;--f-body:"Source Sans 3","Segoe UI",system-ui,sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
  --r:10px;--shadow:none;--shadow-up:none;--glow1:transparent;--glow2:transparent;
  {apelidos_css}
  --foco:0 0 0 3px var(--focus);--sombra-sm:var(--shadow);--sombra-lg:var(--shadow-up);--font-sans:var(--f-body);--font-mono:var(--f-mono)}}
:root[data-float]{{--f-display:"Sora","Segoe UI",system-ui,sans-serif;--f-body:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;--r:14px;
  --shadow:0 1px 2px rgba(15,40,90,.06),0 8px 24px -8px rgba(15,40,90,.16);--shadow-up:0 2px 4px rgba(15,40,90,.08),0 18px 40px -12px rgba(29,95,214,.32);--glow1:rgba(59,130,246,.22);--glow2:rgba(14,165,233,.18)}}
:root[data-float="dark"]{{--shadow:0 1px 2px rgba(0,0,0,.4),0 10px 28px -10px rgba(0,0,0,.6);--shadow-up:0 2px 6px rgba(0,0,0,.45),0 20px 44px -12px rgba(59,130,246,.35);--glow1:rgba(59,130,246,.20);--glow2:rgba(14,165,233,.14)}}
{fixos}
body{{background:var(--bg);color:var(--ink);font-family:var(--f-body);-webkit-font-smoothing:antialiased}}
:root[data-float] body{{background-image:radial-gradient(900px 520px at 8% -6%,var(--glow1),transparent 60%),radial-gradient(760px 480px at 100% 18%,var(--glow2),transparent 60%);background-attachment:fixed}}
h1,h2,h3,h4,.font-display{{font-family:var(--f-display)}}
h1,h2{{letter-spacing:-.03em;text-wrap:balance}}
:focus-visible{{outline:3px solid var(--focus);outline-offset:2px}}
mark.marca-texto{{background:linear-gradient(var(--hl),var(--hl)) no-repeat 0 0/100% 100%;color:var(--hl-ink);border-radius:4px;padding:0 .15em;-webkit-box-decoration-break:clone;box-decoration-break:clone;animation:og-risca .9s .35s cubic-bezier(.2,.7,.2,1) both}}
@keyframes og-risca{{from{{background-size:0 100%;color:inherit}}}}
.eyebrow{{font-family:var(--f-mono);font-size:12px;line-height:16px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
:root[data-float] .eyebrow{{color:var(--hl)}}
/* Estilo flutuante: sombra, subir no hover e cabeçalho de vidro */
:root[data-float] .og-cartao,:root[data-float] main .rounded-2xl.border,:root[data-float] main form.rounded-2xl{{box-shadow:var(--shadow);transition:transform .2s ease,box-shadow .2s ease}}
:root[data-float] a.og-cartao:hover,:root[data-float] main a.rounded-2xl:hover{{transform:translateY(-3px);box-shadow:var(--shadow-up)}}
:root[data-float] body>header.sticky{{background:color-mix(in srgb,var(--surface) 74%,transparent);-webkit-backdrop-filter:blur(14px) saturate(1.4);backdrop-filter:blur(14px) saturate(1.4)}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important;animation:none!important}}:root[data-float] a.og-cartao:hover,:root[data-float] main a.rounded-2xl:hover{{transform:none}}}}
/* Seletor de cores */
.tema-btn{{display:inline-flex;align-items:center;gap:6px;min-height:40px;padding:0 12px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--ink);font:600 14px var(--f-body);cursor:pointer;white-space:nowrap}}
.tema-btn svg{{width:18px;height:18px}}
.tema-pop{{position:fixed;z-index:60;width:min(300px,calc(100vw - 16px));max-height:min(70vh,520px);overflow:auto;padding:10px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);box-shadow:0 18px 40px -12px rgba(0,0,0,.45);display:grid;gap:4px}}
.tema-pop[hidden]{{display:none}}
.tema-pop-titulo{{margin:2px 6px 6px;font:500 12px var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.tema-opcao{{display:flex;align-items:center;gap:10px;min-height:44px;padding:6px 10px;border:1px solid transparent;border-radius:10px;background:transparent;color:var(--ink);font:500 14px var(--f-body);text-align:left;cursor:pointer}}
.tema-opcao:hover{{background:var(--surface2)}}
.tema-opcao[aria-pressed="true"]{{border-color:var(--brand);background:var(--brand-soft)}}
.tema-sw{{display:inline-flex}} .tema-sw i{{width:14px;height:14px;border-radius:50%;margin-left:-4px;border:1px solid rgba(0,0,0,.2)}} .tema-sw i:first-child{{margin-left:0}}
.tema-toast{{position:fixed;left:50%;bottom:calc(20px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:70;background:var(--ink);color:var(--bg);padding:10px 18px;border-radius:999px;font-weight:600;opacity:0;pointer-events:none;transition:opacity .2s}}
.tema-toast.on{{opacity:1}}
/* Página inicial interativa: painel da transição, números, marcos e perguntas */
.painel-transicao{{position:relative;display:grid;gap:18px;padding:24px}}
.painel-logo{{width:88px;height:auto;position:absolute;top:-28px;right:20px;filter:drop-shadow(0 10px 18px rgba(0,0,0,.18));animation:og-flutua 6s ease-in-out infinite}}
@keyframes og-flutua{{50%{{transform:translateY(-6px)}}}}
.anel-wrap{{display:flex;align-items:center;gap:18px}}
.anel-progresso{{width:96px;height:96px;flex:none}}
.anel-progresso circle{{fill:none;stroke-width:9}}
.anel-progresso .trilho{{stroke:var(--line)}}
.anel-progresso .valor{{stroke:var(--hl);stroke-linecap:round;transition:stroke-dashoffset 1.2s cubic-bezier(.2,.7,.2,1)}}
.anel-num{{font:700 30px/1 var(--f-display);font-variant-numeric:tabular-nums}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{min-height:36px;min-width:52px;padding:0 10px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--ink);font:500 13px var(--f-mono);cursor:pointer;transition:background .15s,border-color .15s}}
.chip:hover{{border-color:var(--brand)}}
.chip[aria-pressed="true"]{{background:var(--brand);border-color:var(--brand);color:var(--brand-ink)}}
.linha-ano{{display:grid;grid-template-columns:96px 1fr;gap:6px 12px;align-items:center;font-size:14px}}
.linha-ano dt{{color:var(--muted)}}
.linha-ano dd{{margin:0;min-width:0}}
.barra{{display:block;height:6px;border-radius:999px;background:var(--line);margin-top:4px;overflow:hidden}}
.barra>i{{display:block;height:100%;background:var(--warn);border-radius:inherit;transition:width .6s cubic-bezier(.2,.7,.2,1)}}
.numeros{{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}}
.numero{{padding:20px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface)}}
.numero b{{display:block;font:800 40px/1.05 var(--f-display);letter-spacing:-.03em;font-variant-numeric:tabular-nums;color:var(--brand)}}
.numero span{{color:var(--muted);font-size:14px}}
:root[data-float] .numero{{box-shadow:var(--shadow)}}
.marcos{{list-style:none;margin:0;padding:0;display:grid;gap:16px;grid-template-columns:repeat(4,minmax(0,1fr));position:relative}}
.marcos::before{{content:"";position:absolute;left:28px;right:28px;top:27px;border-top:2px dashed var(--line)}}
.marco{{position:relative;display:grid;gap:8px;align-content:start}}
.marco .bola{{width:56px;height:56px;border-radius:50%;display:grid;place-items:center;background:var(--surface);border:2px solid var(--line);font:700 20px var(--f-display);color:var(--muted);transition:background .4s,border-color .4s,color .4s,box-shadow .4s}}
.marco.aceso .bola{{background:var(--hl);border-color:var(--hl);color:var(--hl-ink);box-shadow:0 0 0 6px var(--hl-soft)}}
.marco h3{{margin:0;font-size:17px}}
.marco p{{margin:0;color:var(--muted);font-size:14px}}
@media (max-width:760px){{.marcos{{grid-template-columns:1fr}}.marcos::before{{left:27px;right:auto;top:28px;bottom:28px;border-top:0;border-left:2px dashed var(--line)}}.marco{{grid-template-columns:56px 1fr;column-gap:14px}}.marco .bola{{grid-row:span 2}}}}
.faq{{display:grid;gap:10px}}
.faq details{{border:1px solid var(--line);border-radius:var(--r);background:var(--surface)}}
:root[data-float] .faq details{{box-shadow:var(--shadow)}}
.faq summary{{cursor:pointer;list-style:none;display:flex;justify-content:space-between;gap:12px;align-items:center;padding:16px 18px;font:600 17px var(--f-display);color:var(--ink)}}
.faq summary::-webkit-details-marker{{display:none}}
.faq summary::after{{content:"+";font:500 22px var(--f-mono);color:var(--brand);transition:transform .2s}}
.faq details[open] summary::after{{transform:rotate(45deg)}}
.faq .resposta{{padding:0 18px 18px;display:grid;gap:10px}}
@media (prefers-reduced-motion:reduce){{mark.marca-texto,.painel-logo{{animation:none}}.anel-progresso .valor,.barra>i,.marco .bola{{transition:none}}}}
/* Layout comum (tools/layout.py): menu com grupos, trilha, barra fixa do celular e utilitários dos formulários */
html{{scroll-behavior:smooth}}
[hidden]{{display:none!important}}
.badge-pendente{{background:var(--warn-soft);color:var(--warn);border:1px solid var(--warn)}}
.tab-ativa{{background:var(--brand);color:var(--brand-ink);border-color:var(--brand)}}
.hp{{position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden}}
.nav-grupo{{position:relative}}
.nav-grupo>summary{{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:4px}}
.nav-grupo>summary::-webkit-details-marker{{display:none}}
.nav-grupo>summary::after{{content:"";width:6px;height:6px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:translateY(-2px) rotate(45deg);transition:transform .15s}}
.nav-grupo[open]>summary::after{{transform:translateY(1px) rotate(-135deg)}}
.nav-sub{{position:absolute;left:-12px;top:calc(100% + 12px);min-width:240px;display:grid;gap:2px;padding:8px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);box-shadow:0 18px 40px -12px rgba(0,0,0,.3);z-index:55}}
.nav-sub a{{display:block;padding:8px 10px;border-radius:8px;color:var(--ink)}}
.nav-sub a:hover,.nav-sub a[aria-current]{{background:var(--surface2);color:var(--brand)}}
.nav-titulo{{margin:10px 0 2px;font:500 11px var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.trilha ol{{display:flex;flex-wrap:wrap;gap:6px;list-style:none;margin:0;padding:0;font-size:13px;color:var(--muted)}}
.trilha li+li::before{{content:"›";margin-right:6px}}
.trilha a{{color:var(--link)}}
.trilha a:hover{{text-decoration:underline}}
/* Interações da página inicial: caso selecionado, painel do caso e blocos que surgem ao rolar (só com JS) */
a.og-cartao[aria-pressed="true"]{{border-color:var(--brand);box-shadow:0 0 0 2px var(--brand)}}
a.og-cartao[data-caso]{{cursor:pointer}}
.caso-painel{{animation:og-surge .35s cubic-bezier(.2,.7,.2,1) both}}
@keyframes og-surge{{from{{opacity:0;transform:translateY(10px)}}}}
:root[data-tema] .revelar{{opacity:0;transform:translateY(18px);transition:opacity .55s ease,transform .55s cubic-bezier(.2,.7,.2,1),box-shadow .2s ease}}
:root[data-tema] .revelar.visivel{{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){{.caso-painel{{animation:none}}:root[data-tema] .revelar{{opacity:1;transform:none}}}}
/* Página inicial (estrutura inspirada no Adobe Firefly): caixa de simulação no herói, faixa de marcos,
   seções em "folha", carrossel de ferramentas e painel escuro. O painel escuro usa a paleta {temas[ESCURA]["nome"]}
   e redeclara os apelidos (--tinta etc.), que no :root já chegam resolvidos com as cores claras. */
.caixa-sim{{margin:32px auto 0;max-width:820px;padding:14px;border-radius:24px;background:var(--ink);color:var(--bg);box-shadow:0 24px 60px -24px rgba(8,17,31,.55)}}
.caixa-sim-rotulo{{margin:2px 6px 10px;font:500 12px var(--f-mono);letter-spacing:.06em;text-transform:uppercase;opacity:.75}}
.caixa-sim-campos{{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr) minmax(0,1fr) auto;gap:8px;align-items:end}}
.caixa-campo{{display:grid;gap:4px;font-size:12px;min-width:0}}
.caixa-campo>span{{opacity:.75;padding-left:6px}}
.caixa-campo select,.caixa-campo input{{width:100%;min-height:48px;padding:0 12px;border-radius:14px;border:1px solid color-mix(in srgb,var(--bg) 24%,transparent);background:color-mix(in srgb,var(--bg) 10%,transparent);color:inherit;font:inherit;font-size:15px}}
.caixa-campo option{{color:#0C1A33;background:#fff}}
.caixa-campo input::placeholder{{color:inherit;opacity:.55}}
.caixa-sim-enviar{{width:48px;height:48px;border:0;border-radius:50%;background:var(--brand);color:var(--brand-ink);display:inline-flex;align-items:center;justify-content:center;gap:8px;cursor:pointer;font:600 15px var(--f-body);transition:transform .15s,filter .15s}}
.caixa-sim-enviar:hover{{filter:brightness(1.1);transform:translateX(2px)}}
.caixa-sim-enviar svg{{width:22px;height:22px;flex:none}}
.caixa-sim-texto{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}
.caixa-sim-nota{{margin:10px 6px 2px;font-size:12px;opacity:.7}}
@media (max-width:767px){{
  .caixa-sim-campos{{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}
  .caixa-campo-setor{{grid-column:1/-1}}
  .caixa-sim-enviar{{grid-column:1/-1;width:100%;border-radius:14px}}
  .caixa-sim-texto{{position:static;width:auto;height:auto;clip:auto}}
}}
.faixa-marcos{{position:relative;display:flex;align-items:center;gap:8px;padding:0 16px}}
.faixa-janela{{flex:1;min-width:0;overflow:hidden;-webkit-mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent);mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent)}}
.faixa-trilho{{display:flex;width:max-content;list-style:none;margin:0;padding:4px 0;animation:og-faixa 48s linear infinite}}
.faixa-trilho li{{margin-right:12px}}
.faixa-trilho a{{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:0 16px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--ink);font-size:14px;white-space:nowrap}}
.faixa-trilho a:hover{{border-color:var(--brand);color:var(--brand)}}
.faixa-trilho .og-selo{{font-size:11px}}
.faixa-marcos.pausada .faixa-trilho,.faixa-janela:hover .faixa-trilho,.faixa-janela:focus-within .faixa-trilho{{animation-play-state:paused}}
@keyframes og-faixa{{to{{transform:translateX(-50%)}}}}
.faixa-pausa{{flex:none;min-height:40px;padding:0 14px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--ink);font:600 13px var(--f-body);cursor:pointer}}
@media (prefers-reduced-motion:reduce){{.faixa-trilho{{animation:none}}.faixa-janela{{overflow-x:auto}}.faixa-trilho [aria-hidden="true"],.faixa-pausa{{display:none}}}}
.folha{{position:relative;border-radius:32px 32px 0 0;margin-top:-32px;box-shadow:0 -1px 0 var(--line)}}
@media (max-width:639px){{.folha{{border-radius:22px 22px 0 0;margin-top:-22px}}}}
.folha-escura{{{bloco(temas[ESCURA]["cores"])}{apelidos_css}color-scheme:dark;background:var(--bg);color:var(--ink)}}
/* Página já escura (padrão Azul flutuante escuro): o painel escuro troca o fundo para continuar se destacando. */
html[data-escuro="sim"] section.folha-escura{{background:var(--brand-soft)}}
@media (max-width:639px){{[data-orgao]{{padding:14px}}[data-orgao] .og-cartao-texto{{display:none}}[data-orgao] .og-cartao-titulo{{font-size:14px;line-height:20px;margin-bottom:0}}}}
[data-pendencias] article{{min-width:0;overflow-wrap:anywhere}}
/* Vitrine: nome ORGATEC em holograma atrás do título. Só CSS e duas variáveis (--hx, --hy, de -1 a 1) que o inicio.js
   atualiza no máximo uma vez por quadro; sem canvas. Contorno e brilho vêm das cores da paleta (--hl, --brand). */
.holo-vitrine{{position:relative;overflow:hidden;isolation:isolate}}
.holo-nome{{position:absolute;left:0;right:0;top:clamp(4px,3vw,32px);display:flex;justify-content:center;pointer-events:none;z-index:-1;perspective:900px;user-select:none}}
.holo-nome span{{font:800 clamp(52px,13vw,200px)/1 var(--f-display);letter-spacing:.06em;color:transparent;-webkit-text-stroke:1px rgb(var(--hl-rgb)/.5);
  background:linear-gradient(105deg,transparent 30%,rgb(var(--hl-rgb)/.6) 45%,rgb(var(--brand-rgb)/.4) 55%,transparent 70%) no-repeat;background-size:250% 100%;
  background-position:calc(50% + var(--hx,0) * 45%) 0;-webkit-background-clip:text;background-clip:text;opacity:.2;
  transform:rotateX(calc(var(--hy,0) * -9deg)) rotateY(calc(var(--hx,0) * 14deg));transition:transform .5s ease-out,background-position .5s ease-out;
  -webkit-mask-image:repeating-linear-gradient(to bottom,#000 0 2px,rgb(0 0 0/.45) 2px 4px);mask-image:repeating-linear-gradient(to bottom,#000 0 2px,rgb(0 0 0/.45) 2px 4px);
  animation:holo-pulso 7s ease-in-out infinite}}
[data-escuro="sim"] .holo-nome span{{opacity:.28}}
@keyframes holo-pulso{{0%,100%{{filter:none}}50%{{filter:drop-shadow(0 0 18px rgb(var(--hl-rgb)/.35))}}}}
@media (prefers-reduced-motion:reduce){{.holo-nome span{{animation:none;transition:none;transform:none}}}}
.carrossel{{position:relative}}
.carrossel-trilho{{display:grid;grid-auto-flow:column;grid-auto-columns:min(82%,360px);gap:16px;overflow-x:auto;overflow-y:hidden;scroll-snap-type:x mandatory;scroll-padding-inline:4px;padding:4px 4px 16px;scrollbar-width:thin;scroll-behavior:smooth}}
.carrossel-trilho:focus-visible{{outline-offset:4px}}
.carrossel-cartao{{scroll-snap-align:start;display:grid;align-content:start}}
.previa{{display:block;margin:-4px -4px 14px;padding:12px;border-radius:calc(var(--r) - 2px);background:var(--surface2)}}
.previa svg{{display:block;width:100%;height:96px}}
.previa text{{font:500 11px var(--f-mono);fill:var(--muted);text-anchor:middle}}
.pv-fraco{{fill:color-mix(in srgb,var(--muted) 30%,transparent)}}
.pv-forte{{fill:var(--brand)}}
.pv-arco,.pv-arco-forte{{fill:none;stroke-width:12;stroke-linecap:round}}
.pv-arco{{stroke:color-mix(in srgb,var(--muted) 30%,transparent)}}
.pv-arco-forte{{stroke:var(--brand)}}
.pv-ponto{{fill:var(--hl)}}
.carrossel-botoes{{display:flex;justify-content:center;gap:10px;margin-top:8px}}
.carrossel-botao{{width:44px;height:44px;border-radius:50%;border:1px solid var(--line);background:var(--surface);color:var(--ink);font-size:18px;cursor:pointer}}
.carrossel-botao:hover{{border-color:var(--brand);color:var(--brand)}}
.carrossel-botao:disabled{{opacity:.4;cursor:default}}
/* Janela de Campo (setores/janela-de-campo.html, campo.js): três estados com cor, ícone e texto.
   Sem verde/vermelho próprios: o verde é reservado ao WhatsApp; "evitar" usa o tom de aviso cheio. */
.campo-selo{{display:inline-flex;align-items:center;gap:6px;padding:3px 10px 3px 8px;border-radius:999px;font-size:13px;font-weight:600;white-space:nowrap;border:1px solid transparent}}
.campo-selo i{{font-style:normal;font-family:var(--f-mono);width:1.1em;text-align:center}}
.campo-ok{{background:var(--brand-soft);color:var(--brand)}}
.campo-atencao{{background:var(--warn-soft);color:var(--warn);border-color:var(--warn)}}
.campo-evitar{{background:var(--warn);color:var(--surface)}}
.campo-situacao{{padding:12px 16px;border-radius:var(--r);border:1px solid var(--line);font-size:15px}}
.campo-situacao-vigente{{background:var(--brand-soft);border-color:var(--brand)}}
.campo-situacao-vencido{{background:var(--warn-soft);border-color:var(--warn);color:var(--ink)}}
.campo-situacao a{{color:var(--link);font-weight:600}}
.campo-alerta{{display:grid;gap:6px;padding:14px 16px;border:1px solid var(--warn);border-radius:var(--r);background:var(--warn-soft)}}
.campo-alerta strong{{font:700 17px var(--f-display);letter-spacing:.02em;text-transform:uppercase;color:var(--warn)}}
.campo-alerta ul,.campo-lista{{margin:0;padding-left:1.1em;display:grid;gap:6px;list-style:disc}}
.campo-matriz-rolagem{{overflow-x:auto;border:1px solid var(--line);border-radius:var(--r);background:var(--surface)}}
.campo-matriz{{border-collapse:collapse;width:100%;min-width:680px}}
.campo-matriz th,.campo-matriz td{{padding:0;border-bottom:1px solid var(--line);text-align:left}}
.campo-matriz thead th{{padding:10px;font:500 11px var(--f-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}}
.campo-matriz tbody tr:last-child>*{{border-bottom:0}}
.campo-matriz tbody th{{padding:10px 12px;font-weight:600;white-space:nowrap}}
.campo-matriz tbody th small{{display:block;font-weight:400;font-size:12px;color:var(--muted)}}
.campo-matriz tbody tr.selecionada th{{box-shadow:inset 4px 0 0 var(--brand)}}
.campo-celula{{width:100%;min-height:52px;padding:6px 8px;display:flex;align-items:center;border:0;background:transparent;font:inherit;color:inherit;cursor:pointer}}
.campo-celula.ativa .campo-selo{{outline:2px solid var(--ink);outline-offset:1px}}
/* Página Agro: resumo do dia (agro-hoje.js) e itens da reforma recolhidos (conteudo.renderItem com recolhido) */
.campo-hoje-mini{{list-style:none;margin:0;padding:0;display:grid;gap:8px}}
.campo-hoje-mini li{{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:4px 0;border-bottom:1px solid var(--line)}}
.campo-hoje-mini li:last-child{{border-bottom:0}}
.og-cartao.og-item-recolhivel{{display:block;padding:0}}
.og-item-resumo{{list-style:none;cursor:pointer;display:grid;gap:6px;padding:14px 44px 14px 16px;position:relative}}
.og-item-linha{{display:flex;flex-wrap:wrap;align-items:center;gap:8px}}
.og-item-resumo::-webkit-details-marker{{display:none}}
.og-item-resumo::after{{content:"+";position:absolute;right:16px;top:14px;font:600 22px/1 var(--f-mono);color:var(--muted)}}
.og-item-recolhivel[open]>.og-item-resumo::after{{content:"\2212"}}
.og-item-resumo:focus-visible{{outline:2px solid var(--focus);outline-offset:-2px;border-radius:var(--r)}}
.og-item-resumo .og-cartao-titulo{{margin:0}}
.og-item-corpo{{display:grid;gap:12px;padding:0 16px 16px}}
/* Janela de Campo, nova ordem: seletor, "Hoje na minha região", abas e, no desktop, duas colunas com o satélite sempre à vista */
.campo-grade{{display:grid;gap:24px;min-width:0}}
.campo-esq,.campo-dir{{display:grid;grid-template-columns:minmax(0,1fr);gap:20px;align-content:start;min-width:0}}
@media (min-width:1024px){{
  .campo-grade{{grid-template-columns:minmax(0,5fr) minmax(0,7fr);align-items:start}}
  .campo-dir{{display:flex;flex-direction:column;gap:20px}}
  .campo-paineis{{display:contents}}
  .campo-abas-painel{{order:1}}
  .campo-painel{{order:2}}
  .campo-painel[data-painel="satelite"]{{display:grid !important;order:0}}
  .campo-aba-painel[data-aba="satelite"]{{display:none}}
}}
.campo-seletor{{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;min-width:0}}
.campo-seletor>div{{min-width:0}}
.campo-seletor .campo-abas{{position:relative;flex-wrap:nowrap;overflow-x:auto;scroll-snap-type:x proximity;padding-bottom:4px}}
.campo-seletor .campo-aba{{flex:none;scroll-snap-align:start;white-space:nowrap}}
@media (min-width:1024px){{.campo-seletor .campo-abas{{flex-wrap:wrap;overflow:visible}}}}
.campo-hoje{{list-style:none;margin:0;padding:0;display:grid;gap:8px}}
.campo-op{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 10px;align-items:center;width:100%;min-height:56px;padding:10px 12px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);color:var(--ink);font:inherit;text-align:left;cursor:pointer}}
.campo-op[aria-pressed="true"]{{border-color:var(--brand);box-shadow:inset 4px 0 0 var(--brand)}}
.campo-op:focus-visible{{outline:2px solid var(--focus);outline-offset:2px}}
.campo-op-nome{{font-weight:700}}
.campo-op-txt{{grid-column:1/-1;font-size:14px;color:var(--muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.campo-op-txt:empty{{display:none}}
.campo-comparar>summary{{cursor:pointer;font-weight:600;padding:10px 0}}
.campo-comparar>summary:focus-visible{{outline:2px solid var(--focus);outline-offset:2px}}
.campo-abas-painel{{display:flex;gap:4px;border-bottom:1px solid var(--line);overflow-x:auto}}
.campo-aba-painel{{flex:none;padding:10px 14px;border:0;border-bottom:3px solid transparent;background:transparent;color:var(--muted);font:600 15px var(--f-body);white-space:nowrap;cursor:pointer}}
.campo-aba-painel[aria-selected="true"]{{color:var(--ink);border-bottom-color:var(--brand)}}
.campo-aba-painel:focus-visible,.campo-painel:focus-visible{{outline:2px solid var(--focus);outline-offset:-2px}}
.campo-painel{{display:grid;grid-template-columns:minmax(0,1fr);gap:16px;align-content:start;padding-top:16px;min-width:0}}
.campo-painel[hidden]{{display:none}}
.campo-abas{{display:flex;flex-wrap:wrap;gap:6px}}
.campo-aba{{padding:6px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:500 14px var(--f-body);cursor:pointer}}
.campo-aba[aria-pressed="true"]{{background:var(--brand);border-color:var(--brand);color:var(--brand-ink)}}
.campo-fatos{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:8px;overflow:hidden}}
@media (max-width:480px){{.campo-fatos{{grid-template-columns:minmax(0,1fr)}}}}
.campo-fato{{display:grid;gap:2px;padding:10px 12px;background:var(--surface);min-width:0}}
.campo-dia,.campo-horas{{display:grid;grid-template-columns:6fr 4fr 2fr 3fr 3fr 6fr}}
.campo-dia{{height:44px;border:1px solid var(--line);border-radius:8px;overflow:hidden}}
.campo-dia>div{{display:flex;align-items:center;justify-content:center;font:600 14px var(--f-mono)}}
.campo-horas{{font:400 11px var(--f-mono);color:var(--muted)}}
.campo-horas>span:last-child{{display:flex;justify-content:space-between}}
.campo-recomendacao{{display:grid;gap:8px;padding:14px 16px;border-left:4px solid var(--brand);border-radius:0 8px 8px 0;background:var(--brand-soft)}}
.campo-tendencia{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}
@media (max-width:719px){{.campo-tendencia{{grid-template-columns:minmax(0,1fr)}}}}
.campo-tendencia article{{display:grid;gap:4px;padding-top:10px;border-top:3px solid var(--line)}}
.campo-tendencia article.agora{{border-top-color:var(--brand)}}
.campo-celula:focus-visible,.campo-aba:focus-visible{{outline:2px solid var(--focus);outline-offset:-2px}}
.campo-passado{{background:var(--surface2);color:var(--muted)}}
/* Cards por atividade da Janela de Campo, marca Orgatec Audi Agro. Verde e preto medidos na logo
   (tools/extrair_logo_audi_agro.py) e válidos só nesta seção; o resto segue a paleta do site. */
.audi-agro{{--aa-verde:#028227;--aa-preto:#000000;--aa-verde-suave:color-mix(in srgb,var(--aa-verde) 12%,var(--surface))}}
/* sem a marca (agro_fontes.json, marca.exibir = false): a seção usa as cores do site, não o verde e o preto da marca */
.audi-agro-neutro{{--aa-verde:var(--brand);--aa-preto:var(--ink)}}
.audi-agro-topo{{display:flex;flex-wrap:wrap;align-items:center;gap:20px}}
.audi-agro-selo{{flex:none;display:inline-flex;padding:10px 14px;border-radius:16px;background:#fff;border:1px solid color-mix(in srgb,var(--aa-verde) 30%,transparent);box-shadow:0 8px 24px -16px rgba(0,0,0,.4)}}
.audi-agro-selo img{{display:block;width:132px;height:auto}}
.audi-agro .eyebrow{{color:var(--aa-verde)}}
:root[data-float="dark"] .audi-agro .eyebrow,:root[data-tema$="esc"] .audi-agro .eyebrow{{color:color-mix(in srgb,var(--aa-verde) 55%,#fff)}}
.audi-agro-grade{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:16px}}
.audi-agro-card{{display:grid;gap:12px;align-content:start;border-top:4px solid var(--aa-verde)}}
.audi-agro-card-topo{{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:6px 12px}}
.audi-agro-card-topo h3{{margin:0;font:700 19px var(--f-display);color:var(--ink)}}
.audi-agro-cotacao{{display:grid;gap:6px;padding:10px;border-radius:10px;background:var(--aa-verde-suave)}}
.audi-agro-widget{{display:block;width:100%;border:0;min-height:72px;background:transparent}}
.audi-agro-fonte,.audi-agro-atualizado{{margin:0;font-size:12px;color:var(--muted)}}
.audi-agro-aviso{{margin:0;padding:8px 10px;border-radius:8px;border:1px solid var(--warn);background:var(--warn-soft);color:var(--ink);font-size:13px}}
.audi-agro-sem{{margin:0;font-size:13px;color:var(--muted)}}
.audi-agro-noticias ul,.audi-agro-tributacao ul{{list-style:none;margin:6px 0 0;padding:0;display:grid;gap:8px}}
.audi-agro-item a{{color:var(--ink);font-weight:600;text-decoration:none}}
.audi-agro-item a:hover{{color:var(--aa-verde);text-decoration:underline}}
.audi-agro-meta{{display:block;font-size:12px;color:var(--muted)}}
.audi-agro-tributacao{{border-left:4px solid var(--aa-preto)}}
:root[data-float="dark"] .audi-agro-tributacao,:root[data-tema$="esc"] .audi-agro-tributacao{{border-left-color:var(--aa-verde)}}
.campo-horaria{{display:grid;grid-template-columns:repeat(24,minmax(0,1fr));gap:2px;height:28px}}
.campo-horaria>div{{border-radius:3px}}
.campo-horaria-rotulos{{display:flex;justify-content:space-between;font:400 11px var(--f-mono);color:var(--muted)}}
.campo-semana{{min-width:760px}}
.campo-semana thead th small{{display:block;font-size:11px;letter-spacing:0;text-transform:none}}
.campo-semana td{{padding:8px 10px;vertical-align:top;font-size:13px}}
.campo-semana td>span{{display:block}}
.campo-tempo{{font-weight:600}}
.campo-tempo-trovoada,.campo-tempo-chuva-forte{{color:var(--warn)}}
.campo-tempo-chuva{{color:var(--brand)}}
.campo-temp{{font:600 14px var(--f-mono)}}
.campo-temp small{{font-weight:400;color:var(--muted)}}
.campo-mm{{color:var(--muted);font-size:12px}}
.campo-criterios{{margin:0;padding-left:1.1em;display:grid;gap:8px;list-style:disc}}
.mapa-controles{{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px}}
.mapa-satelite{{position:relative;margin:0;width:100%;max-width:760px;justify-self:center;overflow:hidden;border-radius:var(--r);border:1px solid var(--line);background:#0b1220}}
.mapa-palco,.mapa-pontos{{position:absolute;inset:0}}
.mapa-camada{{position:absolute;inset:0}}
.mapa-camada img{{position:absolute;display:block;max-width:none;image-rendering:auto}}
.mapa-chuva img{{opacity:.85}}
.mapa-polo{{position:absolute;width:20px;height:20px;margin:-10px 0 0 -10px;padding:0;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 2px rgba(0,0,0,.45);cursor:pointer;display:grid;place-items:center;font:700 11px var(--f-mono);line-height:1}}
.mapa-polo i{{font-style:normal}}
.mapa-polo-ok{{background:var(--brand);color:var(--brand-ink)}}
.mapa-polo-atencao{{background:var(--warn-soft);color:var(--warn);border-color:var(--warn)}}
.mapa-polo-evitar{{background:var(--warn);color:#fff}}
.mapa-polo:focus-visible{{outline:3px solid var(--focus);outline-offset:2px}}
.mapa-polo-nome{{position:absolute;left:14px;top:-4px;padding:1px 6px;border-radius:6px;background:rgba(8,17,31,.78);color:#fff;font:600 11px var(--f-body);white-space:nowrap;pointer-events:none;opacity:0;transition:opacity .15s}}
.mapa-polo:hover .mapa-polo-nome,.mapa-polo:focus-visible .mapa-polo-nome{{opacity:1}}
.mapa-hora{{position:absolute;left:10px;bottom:10px;padding:4px 10px;border-radius:999px;background:rgba(8,17,31,.78);color:#fff;font:500 12px var(--f-mono)}}
.mapa-tempo{{display:flex;flex-wrap:wrap;align-items:center;gap:12px;max-width:760px;width:100%;justify-self:center}}
.mapa-tempo input[type=range]{{flex:1;min-width:160px;accent-color:var(--brand)}}
/* Termômetro de conformidade: respostas como chips (rádio acessível por teclado) */
.chip-opcao{{position:relative;display:inline-flex}}
.chip-opcao input{{position:absolute;opacity:0;width:1px;height:1px}}
.chip-opcao span{{display:inline-flex;align-items:center;min-height:40px;padding:0 14px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--ink);font:500 14px var(--f-body);cursor:pointer;transition:background .15s,border-color .15s}}
.chip-opcao span:hover{{border-color:var(--brand)}}
.chip-opcao input:checked+span{{background:var(--brand);border-color:var(--brand);color:var(--brand-ink)}}
.chip-opcao input:focus-visible+span{{outline:3px solid var(--focus);outline-offset:2px}}
.pergunta+.pergunta{{border-top:1px solid var(--line);padding-top:18px}}
.camadas-prova{{border-left:3px solid var(--brand);padding:4px 0 4px 14px;display:grid;gap:10px}}
.termometro-resultado{{position:sticky;top:96px}}
.termometro-resumo{{display:none}}
.relatorio-impressao{{display:none}}
/* Impressão: na página do termômetro sai só o relatório; nas demais, sem cabeçalho, rodapé e barras. Sempre claro. */
@media print{{
  html,body{{background:#fff!important;color:#111!important}}
  header,footer,nav,.barra-movel,.termometro-resumo,#faixaHomologacao{{display:none!important}}
  body:has([data-termometro-relatorio]) main>*:not([data-termometro]),[data-termometro]>*:not([data-termometro-relatorio]){{display:none!important}}
  .relatorio-impressao{{display:block!important;font:12pt/1.45 var(--f-body);color:#111}}
  .relatorio-impressao h1{{font:700 18pt var(--f-display);margin:0 0 6pt}}
  .relatorio-impressao h2{{font:700 13pt var(--f-display);margin:14pt 0 4pt}}
  .relatorio-impressao ol,.relatorio-impressao ul{{padding-left:18pt}}
  .relatorio-impressao li{{margin:0 0 6pt;break-inside:avoid}}
  .relatorio-impressao small{{color:#444}}
  .relatorio-nivel{{font-size:15pt;font-weight:700}}
  .relatorio-aviso{{margin-top:16pt;font-size:9pt;color:#444;border-top:1px solid #999;padding-top:6pt}}
}}
@media (max-width:1023px){{
  .termometro-resumo.fora{{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:45;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 14px;border:1px solid var(--line);border-radius:14px;background:var(--surface);color:var(--ink);box-shadow:0 12px 30px -12px rgba(0,0,0,.45);font-size:14px;text-decoration:none}}
  .termometro-resumo-ver{{color:var(--link);font-weight:600;white-space:nowrap}}
}}
.barra-movel{{display:none}}
@media (max-width:639px){{
  .barra-movel{{display:grid;grid-template-columns:1fr 1fr;gap:8px;position:fixed;left:0;right:0;bottom:0;z-index:45;padding:8px 12px calc(8px + env(safe-area-inset-bottom,0px));background:var(--surface);border-top:1px solid var(--line);transition:transform .2s}}
  .barra-movel.recolhida{{transform:translateY(110%)}}
  body.com-barra-movel{{padding-bottom:72px}}
}}
/* Componentes og-* (orgatec-template2), agora com as cores do Trilha */
{comp}
.og-selo-norma{{background:var(--brand-soft);color:var(--brand);border-color:var(--line)}}
.og-btn-sobre-palco{{background:var(--surface);color:var(--ink);border-color:var(--line)}}
.og-btn-sobre-palco:hover{{background:var(--surface2)}}
.og-btn-primario:hover{{filter:brightness(1.08)}}
.og-btn-contato{{color:var(--sobre-contato)}}
"""
    destino = RAIZ / "site" / "assets" / "css" / "orgatec.css"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(css, encoding="utf-8", newline="\n")
    print("gerado: site/assets/js/tema.js, site/assets/css/orgatec.css e tailwind.config.js (design ORGATEC Trilha)")


if __name__ == "__main__":
    main()
