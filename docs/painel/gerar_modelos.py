"""Gera os três modelos do painel de compliance moderno (docs/painel/modelo-*.html).
Conteúdo e interação são os mesmos (painel.js); muda só o layout. Uso: python docs/painel/gerar_modelos.py"""
import pathlib

AQUI = pathlib.Path(__file__).parent

KPIS = [("38", "pontos com fonte", ""), ("43", "perguntas no termômetro", ""), ("9", "perfis de público", ""),
        ("0", "pontos aprovados na revisão técnica", "alerta"), ("43", "perguntas só de declaração", "alerta"), ("9", "frentes analisadas", "")]
ABAS = [("frentes", "Frentes"), ("termometro", "Termômetro"), ("evidencia", "Evidência"), ("plano", "Plano"), ("nao", "Não adotar")]


def kpis(classe):
    return "".join(f'<div class="{classe} {c}"><b>{n}</b><small>{t}</small></div>' for n, t, c in KPIS)


def abas(vertical=False):
    papel = ' aria-orientation="vertical"' if vertical else ""
    bts = "".join(f'<button class="btn" role="tab" data-aba="{a}" aria-pressed="{"true" if i == 0 else "false"}">{t}</button>'
                  for i, (a, t) in enumerate(ABAS))
    return f'<nav class="abas" role="tablist" aria-label="Seções do painel"{papel}>{bts}</nav>'


def paineis(classe):
    return f"""
<section class="{classe}" data-painel="frentes">
  <h2>As nove frentes</h2>
  <p class="nota">Clique em um cartão para ver o que muda no site e no serviço.</p>
  <div class="filtros" id="filtroClasse">
    <button class="btn" data-classe="todas" aria-pressed="true">Todas</button>
    <button class="btn" data-classe="A" aria-pressed="false">A · norma</button>
    <button class="btn" data-classe="B" aria-pressed="false">B · experimento</button>
    <button class="btn" data-classe="C" aria-pressed="false">C · observacional</button>
  </div>
  <div class="grade" id="frentes"></div>
</section>
<section class="{classe}" data-painel="termometro" hidden>
  <h2>Cobertura do termômetro</h2>
  <p class="nota">Quantas das 43 perguntas tocam cada eixo. Mapa do estudo, seção 4.</p>
  <div id="cobertura"></div>
  <h3 class="subtitulo">Camadas propostas</h3>
  <div class="camadas">
    <div class="camada"><b>Existe?</b>O controle está no papel</div>
    <div class="camada"><b>Funciona?</b>Foi usado no período, com que resultado</div>
    <div class="camada"><b>Como sabe?</b>Que registro mostra isso</div>
  </div>
</section>
<section class="{classe}" data-painel="evidencia" hidden>
  <h2>Estudos e normas</h2>
  <div class="tabela"><table><thead><tr><th>Fonte</th><th>Classe</th><th>Achado</th><th>Limite</th></tr></thead><tbody id="tabelaEvidencia"></tbody></table></div>
</section>
<section class="{classe}" data-painel="plano" hidden>
  <h2>Plano em três ondas</h2>
  <div class="onda" id="ondas"></div>
</section>
<section class="{classe}" data-painel="nao" hidden>
  <h2>O que não adotar</h2>
  <div class="tabela"><table><thead><tr><th>Ideia</th><th>Por quê</th></tr></thead><tbody id="tabelaNao"></tbody></table></div>
</section>"""


def pagina(arquivo, titulo, tema, css, corpo):
    html = f"""<!DOCTYPE html>
<html lang="pt-BR" data-tema="{tema}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{titulo}</title>
<link rel="stylesheet" href="base.css">
<style>{css}</style>
</head>
<body>
{corpo}
<script src="painel.js"></script>
</body>
</html>
"""
    (AQUI / arquivo).write_text(html, encoding="utf-8")


COMUM = """.grade{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.filtros{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 16px}
.camadas{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px}
.camada{padding:14px;border-radius:14px;border:1px dashed var(--line);text-align:center;color:var(--muted);font-size:14px}
.camada b{display:block;color:var(--ink);font:700 20px var(--f-display)}
.subtitulo{margin-top:22px;font-size:17px}
.tabela{overflow-x:auto}
@media (max-width:640px){.camadas{grid-template-columns:1fr}}"""

TOPO = """<div class="marca"><span class="logo" aria-hidden="true"></span><span>ORGATEC</span></div>"""

# ---------- Modelo 1: navegação lateral, Azul flutuante escuro (padrão do site)
pagina("modelo-1-lateral.html", "Painel Compliance · Lateral", "escuro", COMUM + """
.casca{display:grid;grid-template-columns:250px 1fr;min-height:100vh}
aside{background:var(--surface);border-right:1px solid var(--line);padding:22px 16px;position:sticky;top:0;height:100vh;display:flex;flex-direction:column;gap:18px}
.marca{display:flex;align-items:center;gap:10px;font:800 18px var(--f-display);letter-spacing:.04em}
.logo{width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,var(--brand),var(--hl))}
aside .abas{display:grid;gap:6px}
aside .abas .btn{text-align:left;border-radius:10px;border-color:transparent;background:transparent}
aside .abas .btn[aria-pressed="true"]{background:var(--brand-soft);color:var(--ink);border-color:var(--brand)}
aside .rodape{margin-top:auto}
main{padding:28px clamp(16px,3vw,40px) 60px;max-width:1100px}
.cab h1{font-size:clamp(24px,3vw,34px)}
.cab p{color:var(--muted);margin:6px 0 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px;border-left:4px solid var(--brand)}
.kpi b{display:block;font:700 28px var(--f-mono)}
.kpi small{color:var(--muted)}
.kpi.alerta{border-left-color:var(--warn)} .kpi.alerta b{color:var(--warn)}
.bloco{background:var(--surface);border:1px solid var(--line);border-radius:var(--raio);padding:20px 22px}
.bloco .cartao{background:var(--surface2)}
@media (max-width:860px){.casca{grid-template-columns:1fr}aside{position:static;height:auto}aside .abas{grid-template-columns:repeat(auto-fit,minmax(120px,1fr))}}""",
       f"""<div class="casca">
<aside>{TOPO}{abas(vertical=True)}<div class="rodape"><button class="btn" id="tema" type="button">Tema claro/escuro</button><p class="nota">Estudo de 07/11/2026 · sem dados de clientes</p></div></aside>
<main>
  <header class="cab"><p class="nota">Compliance · estudo</p><h1>Compliance moderno na área do site</h1><p>Da pergunta "o que a lei exige" para "o controle funciona, e como você sabe".</p></header>
  <div class="kpis">{kpis("kpi")}</div>
  {paineis("bloco")}
</main>
</div>""")

# ---------- Modelo 2: relatório editorial, Azul flutuante claro
pagina("modelo-2-relatorio.html", "Painel Compliance · Relatório", "claro", COMUM + """
:root{--f-display:"Sora","Segoe UI",system-ui,sans-serif;--f-body:"Source Sans 3","Segoe UI",system-ui,sans-serif}
body{font-size:16px}
.faixa{background:var(--brand);color:var(--brand-ink)}
.faixa .dentro{max-width:980px;margin:0 auto;padding:16px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.marca{display:flex;align-items:center;gap:10px;font:700 17px var(--f-display);letter-spacing:.05em}
.logo{width:24px;height:24px;border-radius:50%;border:3px solid var(--brand-ink)}
.faixa .btn{background:transparent;color:var(--brand-ink);border-color:rgba(255,255,255,.5)}
.capa{max-width:980px;margin:0 auto;padding:44px 16px 18px}
.capa .eyebrow{font:600 12px var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--brand)}
.capa h1{font-size:clamp(28px,4.4vw,48px);line-height:1.08;margin-top:10px}
.capa p{font-size:19px;color:var(--muted);max-width:720px}
.numeros{max-width:980px;margin:0 auto;padding:0 16px;display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));border-top:2px solid var(--ink);border-bottom:1px solid var(--line)}
.num{padding:16px 12px;border-right:1px solid var(--line)}
.num:last-child{border-right:0}
.num b{display:block;font:700 34px var(--f-display);color:var(--brand)}
.num.alerta b{color:var(--warn)}
.num small{color:var(--muted)}
.conteudo{max-width:980px;margin:0 auto;padding:22px 16px 64px}
.conteudo .abas{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}
.secao h2{font-size:26px;margin-bottom:6px}
.secao .cartao{box-shadow:0 1px 2px rgba(12,26,51,.06)}""",
       f"""<div class="faixa"><div class="dentro">{TOPO}<button class="btn" id="tema" type="button">Tema</button></div></div>
<header class="capa"><span class="eyebrow">Estudo · 07/11/2026</span><h1>O controle existe. Mas funciona?</h1><p>Diagnóstico da área de Compliance do site e o que normas e estudos dizem sobre compliance moderno.</p></header>
<div class="numeros">{kpis("num")}</div>
<main class="conteudo">{abas()}{paineis("secao")}<p class="nota">Não é parecer jurídico nem probabilidade de autuação. Detalhes: docs/estudo-compliance-moderno.md.</p></main>""")

# ---------- Modelo 3: bento em folhas, Azul flutuante escuro, denso
pagina("modelo-3-bento.html", "Painel Compliance · Bento", "escuro", COMUM + """
:root{--raio:22px}
.pagina{max-width:1200px;margin:0 auto;padding:22px 16px 60px}
.topo{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:16px}
.marca{display:flex;align-items:center;gap:10px;font:800 18px var(--f-display)}
.logo{width:26px;height:26px;border-radius:7px;background:conic-gradient(var(--brand),var(--hl),var(--brand))}
.bento{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}
.folha{background:var(--surface);border:1px solid var(--line);border-radius:var(--raio);padding:18px}
.titulo{grid-column:span 4;background:linear-gradient(140deg,var(--brand-soft),var(--surface));}
.titulo h1{font-size:clamp(24px,3.2vw,38px)}
.titulo p{color:var(--muted);margin:8px 0 0}
.lacuna{grid-column:span 2;border-color:var(--warn);background:var(--warn-soft)}
.lacuna b{display:block;font:700 44px var(--f-mono);color:var(--warn)}
.cel{grid-column:span 1;padding:14px}
.cel b{display:block;font:700 26px var(--f-mono)}
.cel small{color:var(--muted);font-size:12px}
.cel.alerta b{color:var(--warn)}
.abas-folha{grid-column:span 6;display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between}
.abas-folha .abas{display:flex;flex-wrap:wrap;gap:8px}
.area{grid-column:span 6}
.area .cartao{background:var(--surface2);border-radius:16px}
@media (max-width:900px){.bento{grid-template-columns:repeat(2,1fr)}.titulo,.lacuna,.abas-folha,.area{grid-column:span 2}}""",
       f"""<div class="pagina">
<div class="topo">{TOPO}<button class="btn" id="tema" type="button">Tema</button></div>
<div class="bento">
  <div class="folha titulo"><p class="nota">Compliance moderno · 07/11/2026</p><h1>Da regra à prova de que funciona</h1><p>Nove frentes, evidência classificada e um plano em três ondas.</p></div>
  <div class="folha lacuna"><b>0/43</b>perguntas do termômetro pedem prova de que o controle funciona</div>
  {kpis("folha cel")}
  <div class="folha abas-folha">{abas()}<span class="nota">Classe A norma · B experimento · C observacional</span></div>
  <div class="area">{paineis("folha")}</div>
</div>
</div>""")
print("ok")
