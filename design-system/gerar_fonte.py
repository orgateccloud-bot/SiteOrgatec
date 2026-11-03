"""Gera a fonte do design system orgatec-template2 (design-system/orgatec-template2/) a partir de site/marca.html e do site."""
import json
import datetime
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"
OUT = Path(__file__).parent / "orgatec-template2"
AGORA = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
FONTES_LINK = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap">'


def w(rel, txt):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt, encoding="utf-8", newline="\n")


def c(nome, claro, escuro=None, uso=""):
    return {"name": nome, "value": claro if escuro is None else {"claro": claro, "escuro": escuro}, "usage": uso}


# ---------------------------------------------------------------- tokens
cores = [
    c("fundo", "#f8fafc", "#0f172a", "Fundo da página (lightBg). No escuro, a Tinta do hero e do rodapé."),
    c("superficie", "#ffffff", "rgba(255,255,255,0.06)", "Cartões, formulários, cabeçalho."),
    c("linha", "#e2e8f0", "rgba(255,255,255,0.12)", "Bordas de cartões e divisórias (slate-200)."),
    c("linha-campo", "#cbd5e1", "rgba(255,255,255,0.24)", "Borda de campos e do botão contorno (slate-300). Fica em 1,5:1 sobre branco, abaixo do 3:1 para bordas de controle: valor do site mantido, ver Acessibilidade."),
    c("tinta", "#0f172a", "#ffffff", "Títulos e o nome ORGATEC, sobre fundo e superficie."),
    c("tinta-texto", "#1e293b", "#e2e8f0", "Texto corrido (slate-800), sobre fundo e superficie."),
    c("tinta-suave", "#475569", "#cbd5e1", "Parágrafos de apoio e legendas (slate-600; slate-300 no hero), sobre fundo e superficie."),
    c("tinta-fraca", "#64748b", "#94a3b8", "Metadados, CNPJ, notas de rodapé (slate-500 / slate-400), sobre fundo e superficie."),
    c("acao", "#2563eb", "#2563eb", "Preenchimento do botão primário e da aba ativa; anel de foco (brandBlue). Como texto, use link."),
    c("acao-hover", "#1d4ed8", "#1d4ed8", "Hover do botão primário (blue-700)."),
    c("sobre-acao", "#ffffff", "#ffffff", "Texto sobre acao: 5,2:1."),
    c("link", "#2563eb", "#0ea5e9", "Links. Claro: brandBlue sobre fundo/superficie. Escuro: brandCyan, como no rodapé (6,4:1 sobre Tinta)."),
    c("contato", "#10b981", "#10b981", "Exclusivo dos botões de contato (WhatsApp). Nunca em outro elemento."),
    c("contato-hover", "#059669", "#059669", "Hover do botão de contato (emerald-600)."),
    c("sobre-contato", "#ffffff", "#ffffff", "Texto do botão de contato. Branco sobre contato dá 2,5:1, abaixo de 4,5:1: valor do site mantido, ver Acessibilidade."),
    c("marca-navy", "#072563", None, "Faixa 1 do símbolo. Não usar como texto ou preenchimento sobre fundo escuro."),
    c("marca-azul", "#214c90", None, "Faixa 2 do símbolo."),
    c("marca-azul-medio", "#0970b5", None, "Faixa 3 do símbolo; descritor Inteligência Tributária sobre branco (5,3:1)."),
    c("marca-ciano", "#03aee4", None, "Faixa 4 do símbolo. Não usar como texto sobre claro (2,6:1)."),
    c("marca-ciano-luz", "#03defa", None, "Brilho da faixa ciano; descritor sobre fundo escuro."),
    c("marca-tinta", "#0f172a", None, "Tinta fixa da marca: nome ORGATEC sobre branco e fundo do hero/rodapé em qualquer tema."),
    c("marca-branco", "#ffffff", None, "Nome e símbolo negativos sobre marca-tinta ou marca-navy."),
    c("faixa-1", "{marca-navy}", "{marca-azul}", "Primeira faixa em peças gráficas (capa, divisórias). No escuro sobe um tom para não sumir no fundo."),
    c("faixa-2", "{marca-azul}", "{marca-azul-medio}", "Segunda faixa em peças gráficas."),
    c("faixa-3", "{marca-azul-medio}", "{marca-ciano}", "Terceira faixa em peças gráficas."),
    c("faixa-4", "{marca-ciano}", "{marca-ciano-luz}", "Quarta faixa em peças gráficas."),
    c("descritor", "#0970b5", "#03defa", "Linha Inteligência Tributária sob o nome: azul médio no claro, ciano luz no escuro."),
    c("palco", "#0f172a", "#0f172a", "Hero e rodapé (bg-dark), escuros nos dois temas."),
    c("palco-texto", "#cbd5e1", "#cbd5e1", "Parágrafo sobre palco (slate-300, 12:1)."),
    c("palco-ponto", "#38bdf8", "#38bdf8", "Grade de pontos do hero, a 16 px de passo e 10% de opacidade."),
    c("pendente-fundo", "#fef3c7", None, "Fundo do selo pendente de validação (amber-100)."),
    c("pendente-texto", "#92400e", None, "Texto do selo pendente, sobre pendente-fundo (6,4:1)."),
    c("pendente-borda", "#fcd34d", None, "Borda do selo pendente."),
    c("definido-fundo", "#d1fae5", None, "Fundo do selo de item definido ou validado (emerald-100)."),
    c("definido-texto", "#065f46", None, "Texto do selo definido, sobre definido-fundo (6,8:1)."),
    c("aviso-fundo", "#fffbeb", None, "Faixa de homologação no topo (amber-50)."),
    c("aviso-texto", "#78350f", None, "Texto da faixa de homologação, sobre aviso-fundo (8,7:1)."),
    c("aviso-borda", "#fde68a", None, "Borda inferior da faixa de homologação."),
]

tokens = {
    "name": "orgatec-template2",
    "version": 1,
    "meta": {"source": "site/marca.html + site/index.html (ORGATEC)"},
    "color": {"themes": [{"id": "claro", "name": "Claro"}, {"id": "escuro", "name": "Escuro"}], "tokens": cores},
    "type": {
        "fonts": [],
        "families": {
            "sans": "Inter, ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", sans-serif",
            "mono": "\"JetBrains Mono\", ui-monospace, Menlo, monospace",
        },
        "groups": [
            {"name": "Marca", "family": "sans", "note": "Assinatura: Inter ExtraBold com +4% de espaçamento; descritor em SemiBold caixa-alta com +32%.",
             "styles": [
                 {"name": "nome-marca", "fontSize": "48px", "lineHeight": 1, "fontWeight": 800, "letterSpacing": "0.04em", "sample": "ORGATEC", "usage": "O nome, sempre em maiúsculas."},
                 {"name": "descritor", "fontSize": "11px", "lineHeight": "16px", "fontWeight": 600, "letterSpacing": "0.32em", "sample": "INTELIGÊNCIA TRIBUTÁRIA", "usage": "Linha sob o nome, em caixa-alta, cor descritor."},
             ]},
            {"name": "Títulos", "family": "sans",
             "styles": [
                 {"name": "titulo-hero", "fontSize": "60px", "lineHeight": 1.25, "fontWeight": 800, "letterSpacing": "-0.025em", "sample": "Contabilidade Estratégica e Inteligência Tributária para a Nova Era Fiscal.", "usage": "Só o H1 do hero, sobre palco (36px no celular, 48px no tablet)."},
                 {"name": "titulo-secao", "fontSize": "30px", "lineHeight": "36px", "fontWeight": 700, "sample": "Hub da Reforma Tributária", "usage": "H2 de cada seção."},
                 {"name": "titulo-cartao", "fontSize": "16px", "lineHeight": "24px", "fontWeight": 700, "sample": "A lei do IBS, da CBS e do IS", "usage": "Título de cartão e de bloco de formulário."},
             ]},
            {"name": "Texto", "family": "sans",
             "styles": [
                 {"name": "lead", "fontSize": "20px", "lineHeight": "28px", "fontWeight": 400, "sample": "Preparamos sua empresa para a transição do IBS e da CBS.", "usage": "Parágrafo de abertura do hero."},
                 {"name": "corpo", "fontSize": "16px", "lineHeight": "24px", "fontWeight": 400, "sample": "Conteúdo técnico com a base legal citada em cada ponto.", "usage": "Texto corrido."},
                 {"name": "pequeno", "fontSize": "14px", "lineHeight": "20px", "fontWeight": 400, "sample": "Estrutura da lei, cronograma de transição e o que já vale em 2026.", "usage": "Texto de cartão, legendas, rodapé."},
                 {"name": "rotulo", "fontSize": "14px", "lineHeight": "20px", "fontWeight": 600, "sample": "Faturamento anual (R$)", "usage": "Rótulo de campo."},
                 {"name": "sobretitulo", "fontSize": "12px", "lineHeight": "16px", "fontWeight": 600, "letterSpacing": "0.1em", "sample": "REFORMA TRIBUTÁRIA", "usage": "Acima do H2, em caixa-alta, cor link."},
                 {"name": "selo", "fontSize": "10px", "lineHeight": "15px", "fontWeight": 600, "sample": "pendente de validação", "usage": "Texto dos selos, em minúsculas."},
             ]},
            {"name": "Dados", "family": "mono", "note": "JetBrains Mono para números, normas e códigos.",
             "styles": [
                 {"name": "referencia", "fontSize": "12px", "lineHeight": "16px", "fontWeight": 400, "sample": "LC 214/2025 · art. 41", "usage": "Referência legal em cartões e listas, cor link."},
                 {"name": "dado", "fontSize": "14px", "lineHeight": "20px", "fontWeight": 600, "sample": "CRC-TO 002032/O-5 T-GO", "usage": "Registros, protocolos e valores."},
             ]},
        ],
    },
    "spacing": {"note": "Base de 4 px (escala do Tailwind usada no site).", "tokens": [
        {"name": "espaco-1", "value": "4px", "usage": "Selo: respiro vertical; ícone e rótulo."},
        {"name": "espaco-2", "value": "8px", "usage": "Rótulo e campo; selo: respiro horizontal."},
        {"name": "espaco-3", "value": "12px", "usage": "Símbolo e nome na assinatura; campo pequeno."},
        {"name": "espaco-4", "value": "16px", "usage": "Grade entre cartões; margem lateral no celular; passo da grade de pontos."},
        {"name": "espaco-5", "value": "20px", "usage": "Padding do cartão do Hub."},
        {"name": "espaco-6", "value": "24px", "usage": "Padding de blocos; margem lateral no tablet."},
        {"name": "espaco-8", "value": "32px", "usage": "Padding lateral do CTA grande; margem lateral no desktop."},
        {"name": "espaco-10", "value": "40px", "usage": "Entre o lead e os CTAs do hero."},
        {"name": "espaco-20", "value": "80px", "usage": "Padding vertical de cada seção."},
    ]},
    "radius": {"note": "Cantos suaves; pílula só em selos.", "tokens": [
        {"name": "raio-lg", "value": "8px", "usage": "Campos pequenos e botões do cabeçalho."},
        {"name": "raio-xl", "value": "12px", "usage": "CTAs e campos do simulador."},
        {"name": "raio-2xl", "value": "16px", "usage": "Cartões e painéis."},
        {"name": "raio-icone", "value": "24px", "usage": "Ícone de app de 112 px (proporção iOS)."},
        {"name": "raio-pilula", "value": "9999px", "usage": "Selos e o chip de normas do hero."},
    ]},
    "shadow": {"note": "Sombras do Tailwind usadas no site; foco é anel sólido de 2 px.", "tokens": [
        {"name": "sombra-sm", "value": "0 1px 2px 0 #0000000d", "usage": "Botão de contato em repouso."},
        {"name": "sombra-lg", "value": "0 10px 15px -3px #0000001a, 0 4px 6px -4px #0000001a", "usage": "Cartão em hover, CTA do hero."},
        {"name": "foco", "value": {"claro": "0 0 0 2px #2563eb", "escuro": "0 0 0 2px #0ea5e9"}, "usage": "Anel de foco de teclado em campos e botões (focus:ring-2 brandBlue)."},
    ]},
}
w("tokens.json", json.dumps(tokens, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- tokens.css (primeiro, depois a página assume)
def css_val(v, tema):
    v = v if isinstance(v, str) else v.get(tema, v.get("claro"))
    return f"var(--{v[1:-1]})" if v.startswith("{") else v

linhas = ["/* orgatec-template2 — generated from tokens.json */"]
corpo = [f"  --{t['name']}: {css_val(t['value'],'claro')};" for t in cores] + [f"  --{t['name']}: {css_val(t['value'],'claro')};" for t in tokens["shadow"]["tokens"]]
linhas += [':root, [data-theme="claro"] {'] + corpo + ["}"]
esc = [f"  --{t['name']}: {css_val(t['value'], 'escuro')};" for t in cores + tokens["shadow"]["tokens"] if isinstance(t["value"], dict)]
linhas += ['[data-theme="escuro"] {'] + esc + ["}"]
fixos = [f"  --{t['name']}: {t['value']};" for t in tokens["spacing"]["tokens"] + tokens["radius"]["tokens"]]
fixos += [f"  --font-{k}: {v};" for k, v in tokens["type"]["families"].items()]
linhas += [":root {"] + fixos + ["}"]
for g in tokens["type"]["groups"]:
    for s in g["styles"]:
        fam = s.get("family", g["family"])
        decl = [f"font-family: var(--font-{fam})", f"font-size: {s['fontSize']}", f"line-height: {s['lineHeight']}", f"font-weight: {s['fontWeight']}"]
        if "letterSpacing" in s:
            decl.append(f"letter-spacing: {s['letterSpacing']}")
        linhas.append(f".{s['name']} {{ {'; '.join(decl)}; }}")
w("tokens.css", "\n".join(linhas) + "\n")


# ---------------------------------------------------------------- bundle
simbolo = (SITE / "assets/marca/orgatec-simbolo.svg").read_text(encoding="utf-8").strip()
branco = (SITE / "assets/marca/orgatec-simbolo-branco.svg").read_text(encoding="utf-8").strip()
nomes = ["Assinatura", "Botao", "Selo", "CitacaoFonte", "CartaoHub", "Campo", "Consentimento"]
cabecalho = {"format": 4, "namespace": "OrgatecUI", "components": [{"name": n} for n in nomes]}

bundle = "/* @ds-bundle: " + json.dumps(cabecalho) + " */\n" + r"""(function () {
  var React = window.React, h = React.createElement;
  var SIMBOLO = %s, SIMBOLO_BRANCO = %s;
  function cx() { return Array.prototype.filter.call(arguments, Boolean).join(' '); }

  function Simbolo(p) {
    return h('span', { className: cx('og-simbolo', p.className), 'aria-hidden': 'true', style: { height: p.altura, width: p.altura * 314 / 347 },
      dangerouslySetInnerHTML: { __html: p.branco ? SIMBOLO_BRANCO : SIMBOLO } });
  }

  function Assinatura(p) {
    var variante = p.variante || 'horizontal', tom = p.tom || 'claro';
    var descritor = p.descritor !== false && variante !== 'reduzida';
    var alt = { horizontal: 64, vertical: 80, reduzida: 32 }[variante];
    return h('span', { className: cx('og-assinatura', 'og-assinatura-' + variante, 'og-tom-' + tom, p.className), role: 'img', 'aria-label': 'ORGATEC' },
      h(Simbolo, { altura: p.altura || alt, branco: tom === 'escuro' }),
      h('span', { className: 'og-assinatura-texto' },
        h('span', { className: 'og-nome' }, 'ORGATEC'),
        descritor ? h('span', { className: 'og-descritor' }, 'Inteligência Tributária') : null));
  }

  function Botao(p) {
    var r = Object.assign({}, p); delete r.variante; delete r.tamanho; delete r.className; delete r.children;
    var cls = cx('og-btn', 'og-btn-' + (p.variante || 'primario'), 'og-btn-' + (p.tamanho || 'md'), p.className);
    if (p.href) { if (/^https?:/.test(p.href)) { r.target = r.target || '_blank'; r.rel = r.rel || 'noopener'; } return h('a', Object.assign(r, { className: cls }), p.children); }
    return h('button', Object.assign({ type: 'button' }, r, { className: cls }), p.children);
  }

  var TEXTO_SELO = { pendente: 'pendente de validação', definido: 'definido', futuro: 'vigência futura', norma: '' };
  function Selo(p) {
    var tom = p.tom || 'pendente';
    return h('span', { className: cx('og-selo', 'og-selo-' + tom, p.className) }, p.children || TEXTO_SELO[tom]);
  }

  function CitacaoFonte(p) {
    return h('span', { className: cx('og-citacao', p.className) },
      p.url ? h('a', { href: p.url, target: '_blank', rel: 'noopener', className: 'og-link' }, p.rotulo) : h('span', null, p.rotulo),
      p.validado ? null : h(Selo, { tom: 'pendente' }));
  }

  function CartaoHub(p) {
    return h(p.href ? 'a' : 'div', { href: p.href, className: cx('og-cartao', p.className) },
      p.referencia ? h('span', { className: 'og-cartao-ref' }, p.referencia) : null,
      h('h3', { className: 'og-cartao-titulo' }, p.titulo, p.pendente ? h(Selo, { tom: 'pendente' }) : null),
      p.children ? h('p', { className: 'og-cartao-texto' }, p.children) : null);
  }

  function Campo(p) {
    var r = Object.assign({}, p); ['rotulo', 'ajuda', 'erro', 'tamanho', 'opcoes', 'className'].forEach(function (k) { delete r[k]; });
    var cls = cx('og-campo-controle', 'og-campo-' + (p.tamanho || 'md'), p.erro ? 'og-campo-invalido' : '');
    var desc = p.erro || p.ajuda ? p.id + '-desc' : undefined;
    var ctrl = p.opcoes
      ? h('select', Object.assign(r, { className: cls, 'aria-describedby': desc }), p.opcoes.map(function (o) { return h('option', { key: o.valor, value: o.valor }, o.rotulo); }))
      : h('input', Object.assign({ type: 'text' }, r, { className: cls, 'aria-describedby': desc, 'aria-invalid': p.erro ? 'true' : undefined }));
    return h('div', { className: cx('og-campo', p.className) },
      h('label', { htmlFor: p.id, className: 'og-campo-rotulo' }, p.rotulo), ctrl,
      p.erro ? h('p', { id: desc, className: 'og-campo-erro', role: 'alert' }, p.erro)
        : p.ajuda ? h('p', { id: desc, className: 'og-campo-ajuda' }, p.ajuda) : null);
  }

  function Consentimento(p) {
    var r = Object.assign({}, p); delete r.children; delete r.className;
    return h('label', { className: cx('og-consentimento', p.className) },
      h('input', Object.assign({ type: 'checkbox' }, r)), h('span', null, p.children));
  }

  window.OrgatecUI = Object.assign(window.OrgatecUI || {}, { Assinatura: Assinatura, Botao: Botao, Selo: Selo, CitacaoFonte: CitacaoFonte, CartaoHub: CartaoHub, Campo: Campo, Consentimento: Consentimento });
})();
""" % (json.dumps(simbolo), json.dumps(branco))
if "</script" in bundle.lower() or "<!--" in bundle:
    raise SystemExit("bundle.js não pode conter </script nem <!-- (é embutido em <script>)")
w("components/bundle.js", bundle)

w("components/bundle.css", """/* OrgatecUI — componentes do site ORGATEC. Valores vêm de tokens.css. */
body { margin: 0; font-family: var(--font-sans); background: var(--fundo); color: var(--tinta-texto); -webkit-font-smoothing: antialiased; }
.og-linha { display: flex; flex-wrap: wrap; gap: var(--espaco-3); align-items: center; padding: var(--espaco-4); }
.og-pilha { display: grid; gap: var(--espaco-4); padding: var(--espaco-4); }
.og-palco { background: var(--palco); color: var(--marca-branco); border-radius: var(--raio-2xl); padding: var(--espaco-6); }
.og-painel-branco { background: var(--marca-branco); border-radius: var(--raio-2xl); padding: var(--espaco-6); }

.og-simbolo { display: inline-block; flex-shrink: 0; }
.og-simbolo svg { display: block; width: 100%; height: 100%; }
.og-assinatura { display: inline-flex; align-items: center; gap: var(--espaco-4); }
.og-assinatura-reduzida { gap: var(--espaco-3); }
.og-assinatura-vertical { flex-direction: column; text-align: center; gap: var(--espaco-4); }
.og-assinatura-texto { display: flex; flex-direction: column; }
.og-nome { font-family: var(--font-sans); font-weight: 800; letter-spacing: .04em; line-height: 1; font-size: 48px; }
.og-assinatura-reduzida .og-nome { font-size: 24px; }
.og-assinatura-vertical .og-nome { font-size: 36px; }
.og-descritor { font-weight: 600; letter-spacing: .32em; text-transform: uppercase; font-size: 11px; line-height: 16px; margin-top: var(--espaco-2); }
.og-tom-claro .og-nome { color: var(--marca-tinta); }
.og-tom-claro .og-descritor { color: var(--marca-azul-medio); }
.og-tom-escuro .og-nome { color: var(--marca-branco); }
.og-tom-escuro .og-descritor { color: var(--marca-ciano-luz); }

.og-btn { display: inline-flex; align-items: center; justify-content: center; gap: var(--espaco-2); font: inherit; font-weight: 600; text-decoration: none; cursor: pointer; border: 1px solid transparent; white-space: nowrap; transition: background-color .15s, border-color .15s, color .15s; }
.og-btn:focus-visible { outline: 2px solid transparent; box-shadow: var(--foco); }
.og-btn-md { font-size: 14px; line-height: 20px; padding: 10px var(--espaco-5); border-radius: var(--raio-lg); }
.og-btn-lg { font-size: 16px; line-height: 24px; padding: var(--espaco-4) var(--espaco-8); border-radius: var(--raio-xl); }
.og-btn-primario { background: var(--acao); color: var(--sobre-acao); }
.og-btn-primario:hover { background: var(--acao-hover); }
.og-btn-lg.og-btn-primario { box-shadow: var(--sombra-lg); }
.og-btn-contato { background: var(--contato); color: var(--sobre-contato); box-shadow: var(--sombra-sm); }
.og-btn-contato:hover { background: var(--contato-hover); }
.og-btn-contorno { background: transparent; color: var(--tinta-texto); border-color: var(--linha-campo); font-weight: 500; }
.og-btn-contorno:hover { color: var(--link); border-color: var(--acao); }
.og-btn-sobre-palco { background: rgba(255,255,255,0.1); color: var(--marca-branco); border-color: rgba(255,255,255,0.2); }
.og-btn-sobre-palco:hover { background: rgba(255,255,255,0.2); }

.og-selo { display: inline-flex; align-items: center; font-size: 10px; line-height: 15px; font-weight: 600; padding: 2px var(--espaco-2); border-radius: var(--raio-pilula); border: 1px solid transparent; white-space: nowrap; vertical-align: middle; }
.og-selo-pendente { background: var(--pendente-fundo); color: var(--pendente-texto); border-color: var(--pendente-borda); }
.og-selo-definido { background: var(--definido-fundo); color: var(--definido-texto); }
.og-selo-futuro { background: var(--superficie); color: var(--link); border-color: var(--acao); }
.og-selo-norma { font-size: 12px; line-height: 16px; letter-spacing: .05em; text-transform: uppercase; padding: var(--espaco-1) var(--espaco-3); background: rgba(37,99,235,0.2); color: #67e8f9; border-color: rgba(37,99,235,0.3); }

.og-citacao { display: inline-flex; flex-wrap: wrap; align-items: center; gap: var(--espaco-2); font-size: 14px; line-height: 20px; }
.og-link { color: var(--link); text-decoration: underline; text-underline-offset: 2px; }
.og-link:focus-visible { outline: none; box-shadow: var(--foco); border-radius: 2px; }

.og-cartao { display: block; background: var(--superficie); border: 1px solid var(--linha); border-radius: var(--raio-2xl); padding: var(--espaco-5); text-decoration: none; color: inherit; transition: border-color .15s, box-shadow .15s; }
a.og-cartao:hover { border-color: var(--acao); box-shadow: var(--sombra-lg); }
a.og-cartao:focus-visible { outline: none; box-shadow: var(--foco); }
.og-cartao-ref { font-family: var(--font-mono); font-size: 12px; line-height: 16px; color: var(--link); }
.og-cartao-titulo { font-size: 16px; line-height: 24px; font-weight: 700; color: var(--tinta); margin: var(--espaco-2) 0; display: flex; flex-wrap: wrap; gap: var(--espaco-2); align-items: center; }
a.og-cartao:hover .og-cartao-titulo { color: var(--link); }
.og-cartao-texto { font-size: 14px; line-height: 20px; color: var(--tinta-suave); margin: 0; }
.og-item { display: grid; gap: var(--espaco-3); align-content: start; }
.og-item .og-cartao-titulo { margin: 0; }
.og-item-orientacao { border-top: 1px solid var(--linha); padding-top: var(--espaco-3); font-size: 14px; line-height: 20px; color: var(--tinta-texto); }
.og-item-orientacao p { margin: var(--espaco-1) 0 0; }
.og-item-rotulo { font-size: 12px; line-height: 16px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--tinta-fraca); }
.og-item-fontes { display: grid; gap: var(--espaco-1); font-size: 12px; }
.og-item-fontes .og-citacao { font-size: 12px; line-height: 16px; }
.og-item-meta { margin: 0; font-family: var(--font-mono); font-size: 12px; line-height: 16px; color: var(--tinta-fraca); }

.og-campo { display: grid; gap: var(--espaco-2); }
.og-campo-rotulo { font-size: 14px; line-height: 20px; font-weight: 600; color: var(--tinta-texto); }
.og-campo-controle { font: inherit; color: var(--tinta-texto); background: var(--superficie); border: 1px solid var(--linha-campo); width: 100%; box-sizing: border-box; }
.og-campo-controle:focus { outline: none; box-shadow: var(--foco); }
.og-campo-md { font-size: 14px; padding: var(--espaco-2) var(--espaco-3); border-radius: var(--raio-lg); }
.og-campo-lg { font-size: 16px; padding: var(--espaco-3) var(--espaco-4); border-radius: var(--raio-xl); }
.og-campo-invalido { border-color: var(--pendente-texto); }
.og-campo-ajuda { margin: 0; font-size: 12px; line-height: 16px; color: var(--tinta-fraca); }
.og-campo-erro { margin: 0; font-size: 14px; line-height: 20px; color: var(--pendente-texto); }

.og-consentimento { display: flex; align-items: flex-start; gap: var(--espaco-2); font-size: 12px; line-height: 16px; color: var(--tinta-suave); }
.og-consentimento input { margin-top: 2px; accent-color: var(--acao); }
.og-consentimento a { color: var(--link); }
""")

w("components/index.d.ts", """import type * as React from 'react';
/** Logotipo ORGATEC: símbolo de 4 faixas + nome. Fundo claro: tom 'claro'. Fundo escuro: tom 'escuro' (símbolo branco). */
export interface AssinaturaProps { variante?: 'horizontal' | 'vertical' | 'reduzida'; tom?: 'claro' | 'escuro'; descritor?: boolean; altura?: number; className?: string }
export declare function Assinatura(props: AssinaturaProps): React.ReactElement;
/** Botão ou link (com href). 'contato' é exclusivo do WhatsApp; 'sobre-palco' só sobre o hero escuro. */
export interface BotaoProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { variante?: 'primario' | 'contato' | 'contorno' | 'sobre-palco'; tamanho?: 'md' | 'lg'; href?: string; children?: React.ReactNode }
export declare function Botao(props: BotaoProps): React.ReactElement;
/** Selo de estado. Sem children, 'pendente' escreve "pendente de validação". */
export interface SeloProps { tom?: 'pendente' | 'definido' | 'futuro' | 'norma'; children?: React.ReactNode; className?: string }
export declare function Selo(props: SeloProps): React.ReactElement;
/** Citação de norma com link oficial; validado=false acrescenta o selo pendente. */
export interface CitacaoFonteProps { rotulo: string; url?: string; validado?: boolean; className?: string }
export declare function CitacaoFonte(props: CitacaoFonteProps): React.ReactElement;
/** Cartão do Hub: referência legal em mono, título e resumo. */
export interface CartaoHubProps { referencia?: string; titulo: string; href?: string; pendente?: boolean; children?: React.ReactNode; className?: string }
export declare function CartaoHub(props: CartaoHubProps): React.ReactElement;
/** Rótulo + campo (input, ou select com opcoes) + ajuda ou erro. id é obrigatório. */
export interface CampoProps extends React.InputHTMLAttributes<HTMLInputElement> { id: string; rotulo: string; ajuda?: string; erro?: string; tamanho?: 'md' | 'lg'; opcoes?: { valor: string; rotulo: string }[] }
export declare function Campo(props: CampoProps): React.ReactElement;
/** Caixa de consentimento LGPD. Nunca pré-marcada. */
export interface ConsentimentoProps extends React.InputHTMLAttributes<HTMLInputElement> { children: React.ReactNode }
export declare function Consentimento(props: ConsentimentoProps): React.ReactElement;
declare global { interface Window { OrgatecUI: { Assinatura: typeof Assinatura; Botao: typeof Botao; Selo: typeof Selo; CitacaoFonte: typeof CitacaoFonte; CartaoHub: typeof CartaoHub; Campo: typeof Campo; Consentimento: typeof Consentimento } } }
""")


# ---------------------------------------------------------------- previews
def preview(nome, grupo, altura, raiz_cls, render):
    w(f"components/{nome}/preview.html", f"""<!-- @dsCard group="{grupo}" height={altura} -->
<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>{nome} — prévia</title>{FONTES_LINK}</head>
<body>
<div id="root" class="{raiz_cls}"></div>
<script>
  var O = window.OrgatecUI, h = React.createElement;
  ReactDOM.createRoot(document.getElementById('root')).render({render});
</script>
</body>
</html>
""")

preview("Assinatura", "Marca", 360, "og-pilha",
        "h(React.Fragment, null, h('div', { className: 'og-painel-branco' }, h(O.Assinatura, null)), "
        "h('div', { className: 'og-palco' }, h(O.Assinatura, { tom: 'escuro' })), "
        "h('div', { className: 'og-painel-branco', style: { display: 'flex', gap: 48, alignItems: 'center', flexWrap: 'wrap' } }, h(O.Assinatura, { variante: 'vertical' }), h(O.Assinatura, { variante: 'reduzida' })))")
preview("Botao", "Ações", 200, "og-pilha",
        "h(React.Fragment, null, h('div', { className: 'og-linha', style: { padding: 0 } }, h(O.Botao, { tamanho: 'lg' }, 'Testar Simulador Tributário'), h(O.Botao, { variante: 'contato', href: 'https://wa.me/5562992949161' }, 'Falar no WhatsApp'), h(O.Botao, { variante: 'contorno', href: 'https://portal.orgatec.io' }, 'Portal do Cliente')), "
        "h('div', { className: 'og-palco og-linha' }, h(O.Botao, { tamanho: 'lg' }, 'Testar Simulador Tributário'), h(O.Botao, { variante: 'sobre-palco', tamanho: 'lg' }, 'Agendar Diagnóstico com Especialista')))")
preview("Selo", "Estado", 120, "og-pilha",
        "h(React.Fragment, null, h('div', { className: 'og-linha', style: { padding: 0 } }, h(O.Selo), h(O.Selo, { tom: 'definido' }, 'Integração: Sieg'), h(O.Selo, { tom: 'pendente' }, 'ERP do portal: pendente de definição'), h(O.Selo, { tom: 'futuro' })), "
        "h('div', { className: 'og-palco' }, h(O.Selo, { tom: 'norma' }, 'EC 132/2023 • LC 214/2025 • Split Payment')))")
preview("CitacaoFonte", "Fontes legais", 120, "og-pilha",
        "h(React.Fragment, null, h(O.CitacaoFonte, { rotulo: 'LC 214/2025, art. 41, §§ 3º e 4º', url: 'https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm', validado: true }), "
        "h(O.CitacaoFonte, { rotulo: 'Lei 6.489/2002 (PA)', validado: false }))")
preview("CartaoHub", "Conteúdo", 220, "og-pilha",
        "h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 } }, "
        "h(O.CartaoHub, { href: '#', referencia: 'LC 214/2025', titulo: 'A lei do IBS, da CBS e do IS' }, 'Estrutura da lei, cronograma de transição e o que já vale em 2026.'), "
        "h(O.CartaoHub, { href: '#', referencia: 'LC 214/2025 · art. 41', titulo: 'Simples Híbrido' }, 'Quando vale recolher IBS e CBS fora do DAS e a janela de opção.'), "
        "h(O.CartaoHub, { referencia: 'Calendário estadual', titulo: 'ICMS no Pará', pendente: true }, 'Dia de vencimento a confirmar na SEFAZ-PA.'))")
preview("Campo", "Formulários", 260, "og-pilha",
        "h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 } }, "
        "h(O.Campo, { id: 'faturamento', rotulo: 'Faturamento anual (R$)', tamanho: 'lg', placeholder: 'ex.: 2.400.000', inputMode: 'decimal' }), "
        "h(O.Campo, { id: 'uf', rotulo: 'UF', tamanho: 'lg', opcoes: [{ valor: 'GO', rotulo: 'Goiás' }, { valor: 'TO', rotulo: 'Tocantins' }, { valor: 'PA', rotulo: 'Pará' }] }), "
        "h(O.Campo, { id: 'email', rotulo: 'E-mail', type: 'email', defaultValue: 'email-invalido', erro: 'E-mail inválido.' }), "
        "h(O.Campo, { id: 'whats', rotulo: 'WhatsApp', placeholder: '(62) 99999-0000', ajuda: 'Só para retorno do diagnóstico.' }))")
preview("Consentimento", "Formulários", 120, "og-pilha",
        "h(O.Consentimento, { id: 'consent' }, 'Autorizo a ORGATEC a usar estes dados e o resultado da simulação para entrar em contato sobre o diagnóstico tributário, conforme a ', h('a', { href: '#' }, 'Política de Privacidade'), ' (LGPD, Lei nº 13.709/2018). Posso revogar a qualquer momento.')")

# ---------------------------------------------------------------- guidelines
READMES = {
    "Assinatura": """# Assinatura

O logotipo ORGATEC: o símbolo de quatro faixas e o nome em Inter ExtraBold. Use `horizontal` em cabeçalhos, propostas e assinatura de e-mail, `vertical` em capas de laudo e peças quadradas, e `reduzida` (sem descritor) abaixo de 160 px de largura.

- O consumidor fornece o fundo. `tom="claro"` vai sobre branco ou `fundo`; `tom="escuro"` vai sobre `palco` ou `marca-navy` e troca o símbolo pelo branco.
- Respiro: metade da altura do símbolo em volta. Mínimo: 16 px de símbolo e 160 px de assinatura com descritor.
- Não distorça, não gire, não troque as cores das faixas, não aplique sombra e não escreva "Orgatec.IO". O nome é sempre ORGATEC.
- O nome é texto vivo em Inter. Carregue a Inter do Google Fonts na página, ou use os PNG do grupo Assinaturas.
""",
    "Botao": """# Botao

Um botão ou link de ação. Com `href`, vira `<a>`, e link externo abre em nova aba. Use frases com verbo ("Testar Simulador Tributário", "Falar no WhatsApp").

- `primario` (`acao`): uma ação principal por bloco.
- `contato` (`contato`): só WhatsApp e telefone. O verde não aparece em nenhum outro elemento.
- `contorno`: ações secundárias do cabeçalho, como o Portal do Cliente.
- `sobre-palco`: botão translúcido, só sobre o hero escuro (`palco`).
- `tamanho="lg"` (`raio-xl`) para os CTAs do hero e do simulador. `md` (`raio-lg`) para o cabeçalho.
- O link de WhatsApp leva só uma mensagem padrão, nunca nome, e-mail ou telefone do visitante na URL.
""",
    "Selo": """# Selo

Marca o estado de uma informação. `pendente` ("pendente de validação") é obrigatório em toda regra, alíquota ou data que ainda não foi confirmada na fonte oficial.

- `pendente`: `pendente-fundo`, `pendente-texto`, `pendente-borda`. Também serve para pendências do Plano Diretor ("pendente de definição").
- `definido`: o item foi escolhido ou validado (`definido-fundo`, `definido-texto`).
- `futuro`: lei aprovada com vigência futura (borda `acao`, texto `link`); usado no status dos itens da reforma.
- `norma`: chip das normas no hero, só sobre `palco`.
- Escreva em minúsculas e não use o selo como enfeite.
""",
    "CitacaoFonte": """# CitacaoFonte

Cita a base legal com link para a fonte oficial (Planalto, DOU, SEFAZ). Com `validado=false`, acrescenta o selo pendente.

- O consumidor fornece `rotulo` (norma e dispositivo, ex.: "LC 214/2025, art. 41, §§ 3º e 4º"), `url` oficial e `validado`.
- Toda afirmação tributária exibida precisa de uma citação. Sem fonte confirmada, `validado=false`.
""",
    "CartaoHub": """# CartaoHub

Cartão de conteúdo do Hub da Reforma: referência legal em mono, título e resumo de uma linha.

- `referencia` usa o estilo `referencia` (JetBrains Mono, cor `link`).
- Com `href`, o cartão inteiro é o link, e no hover ganha borda `acao` e `sombra-lg`.
- `pendente` põe o selo ao lado do título quando o conteúdo depende de fonte não confirmada.
- Em grade, use `espaco-4` entre cartões e cinco colunas no desktop.
""",
    "Campo": """# Campo

Rótulo, campo e linha de ajuda ou erro. `id` é obrigatório e liga o rótulo ao campo.

- `tamanho="lg"` (`raio-xl`) no simulador; `md` (`raio-lg`) nos formulários de lead, opt-in e contato.
- `opcoes` troca o input por um select (setor, regime, UF).
- `erro` diz o que corrigir ("E-mail inválido.", "Escreva pelo menos 10 caracteres.") e é anunciado ao leitor de tela.
- Valores em reais aceitam o formato brasileiro ("2.400.000"); use `inputMode="decimal"`.
""",
    "Consentimento": """# Consentimento

Caixa de consentimento LGPD para leads, opt-in e contato. O envio é bloqueado sem ela.

- Nunca venha marcada.
- O texto diz para que o dado será usado, liga para a Política de Privacidade, cita a Lei nº 13.709/2018 e diz que o titular pode revogar.
""",
}
for n, t in READMES.items():
    w(f"components/{n}/README.md", t)

# ---------------------------------------------------------------- asset groups
w("assets/Simbolo/README.md", """# Símbolo

- `orgatec-simbolo.svg`: colorido, uso preferencial sobre fundos claros.
- `orgatec-simbolo-mono.svg`: uma cor, `marca-navy`. Impressão em 1 cor, carimbos e documentos.
- `orgatec-simbolo-branco.svg`: negativo, `marca-branco`. Fundos escuros e fotos.

O vetor foi reconstruído a partir da imagem original do logotipo (contorno e curvas medidos).
""")
w("assets/Assinaturas/README.md", """# Assinaturas

- `orgatec-horizontal`: símbolo + nome + descritor, sobre claro. SVG e PNG.
- `orgatec-horizontal-negativo`: símbolo branco, nome branco, descritor `marca-ciano-luz`, sobre `palco`. SVG e PNG.
- `orgatec-horizontal-mono.svg`: tudo em `marca-navy`.
- `orgatec-vertical`: símbolo sobre o nome. SVG e PNG.

Nos SVG o nome é texto em Inter: sem a fonte instalada, aparece outra no lugar. Para gráfica e documentos, use os PNG.
""")
w("assets/Icones/README.md", """# Ícones e redes

- `orgatec-app.svg` / `orgatec-app-512.png`: avatar claro, símbolo colorido sobre branco.
- `orgatec-app-escuro.svg` / `orgatec-app-escuro-512.png`: avatar escuro, símbolo branco sobre `marca-navy`.
- `favicon.svg` e `favicon-32.png`: aba do navegador.
- `apple-touch-icon.png`: atalho no iPhone (180 px, fundo opaco).
- `og-image.png`: imagem de compartilhamento, 1200 × 630.
""")

# ---------------------------------------------------------------- README (brand book)
w("README.md", """ORGATEC é um escritório de contabilidade consultiva e inteligência tributária, com responsável técnico com CRC ativo e atuação no eixo GO, TO e PA. O site vende diagnóstico tributário da Reforma (EC 132/2023, LC 214/2025). Cada número exibido carrega a fonte legal.

## Voz e conteúdo

- Escreva em português do Brasil, direto e técnico, falando com o empresário por "você" e "sua empresa". A ORGATEC fala de si como "nós" ("Preparamos sua empresa...").
- O nome é sempre **ORGATEC**, em maiúsculas. Nunca "Orgatec.IO" nem "Orgatec". Os domínios continuam `orgatec.io` e `portal.orgatec.io`.
- Toda regra, alíquota, percentual de incentivo ou prazo cita a norma e o dispositivo ("LC 214/2025, art. 41, §§ 3º e 4º") com `CitacaoFonte`. O que não foi confirmado leva o `Selo` "pendente de validação". Nunca apresente suposição como fato.
- Use normas como sobretítulo, no formato "EC 132/2023 • LC 214/2025 • Split Payment".
- Os CTAs são fixos: "Testar Simulador Tributário", "Agendar Diagnóstico com Especialista", "Falar no WhatsApp" ("WhatsApp" no celular).
- Todo resultado de simulação traz o aviso: "Simulação orientativa baseada na EC nº 132/2023 e LC nº 214/2025. Não substitui parecer técnico emitido pelo contador responsável."
- Emoji: nenhum, salvo o 🔒 de "Portal do Cliente" e o ⚠️ do aviso legal, que já existem no site.

## Cor

- Página em `fundo` e blocos em `superficie`, com borda `linha`. Títulos em `tinta`, texto em `tinta-texto`, apoio em `tinta-suave` e metadados em `tinta-fraca`.
- O hero e o rodapé são `palco` nos dois temas, com texto `marca-branco` e parágrafo `palco-texto`. A grade de pontos do hero usa `palco-ponto` a 16 px de passo (`espaco-4`) e 10% de opacidade.
- `acao` preenche o botão primário e a aba ativa e desenha o foco. Texto clicável, sobretítulos e referências legais usam `link`, que no escuro vira ciano.
- `contato` (verde) é exclusivo dos botões de WhatsApp e telefone.
- As cinco cores `marca-*` são as faixas do símbolo, do navy ao ciano. Use-as em peças de marca e capas, não em texto corrido. `marca-ciano` nunca vai como texto sobre claro.
- Estados: `pendente-*` para o que falta validar ou definir, `definido-*` para o que foi confirmado, `aviso-*` para a faixa de homologação.

## Tipografia

- Inter para tudo, JetBrains Mono para normas, registros, protocolos e valores (`referencia`, `dado`).
- O nome usa `nome-marca` (ExtraBold, +4%) e o descritor `descritor` (SemiBold, caixa-alta, +32%).
- Hierarquia: `titulo-hero` só no H1 do hero; `titulo-secao` em cada H2, com `sobretitulo` acima em `link`; `titulo-cartao` em cartões; `lead`, `corpo`, `pequeno` para texto; `rotulo` em campos; `selo` nos selos.
- Carregue as duas famílias do Google Fonts (pesos 400, 600, 700, 800 e 400, 600). Em produção, sirva os arquivos localmente.

## Espaço, forma e sombra

- Escala de 4 px: `espaco-4` entre cartões, `espaco-5` dentro do cartão do Hub, `espaco-20` no padding vertical de cada seção. Margem lateral: `espaco-4` no celular, `espaco-6` no tablet, `espaco-8` no desktop. Largura máxima de 1280 px.
- Cantos: `raio-lg` em campos pequenos e botões do cabeçalho, `raio-xl` em CTAs e campos do simulador, `raio-2xl` em cartões, `raio-pilula` só em selos.
- Sombra só em hover de cartão e no CTA do hero (`sombra-lg`) e no botão de contato (`sombra-sm`). O foco de teclado é `foco`, anel sólido de 2 px.
- O cabeçalho é fixo, branco a 90% com desfoque e borda `linha`. A navegação completa aparece a partir de 1280 px; abaixo, menu ☰.

## Marca

- Use `Assinatura` ou os arquivos dos grupos Símbolo, Assinaturas e Ícones. Não redesenhe o símbolo.
- Use o símbolo sempre com as cores originais, em fundo claro ou escuro (decisão da ORGATEC de 31/10/2026). A versão branca fica só para usos em uma cor, como carimbo ou gravação.
- Respiro: metade da altura do símbolo. Mínimo: 16 px ou 6 mm de símbolo, 160 px ou 40 mm de assinatura com descritor.
- Não distorça, não gire, não troque as cores, não aplique sombra ou efeito.

## Iconografia

O site não tem biblioteca de ícones: usa texto e dois glifos (🔒 no Portal do Cliente, ☰ no menu móvel). Ao precisar de ícones, escolha um conjunto de traço simples e registre aqui antes de usar.

## Acessibilidade

- Texto em `tinta`, `tinta-texto`, `tinta-suave` e `tinta-fraca` passa de 4,5:1 sobre `fundo` e `superficie` nos dois temas.
- Dois pares vêm do site e ficam abaixo do mínimo, mantidos por serem a identidade atual: branco sobre `contato` (2,5:1) e a borda `linha-campo` sobre branco (1,5:1). Se quiser corrigir, troque `contato` por #047857 (5,5:1) e `linha-campo` por #64748b (4,8:1).
- Todo campo tem rótulo visível; erros saem com `role="alert"`; o resultado do simulador é anunciado com `aria-live`.

## Rodapé obrigatório

Toda página termina com: CNPJ 13.155.211/0001-45; responsável técnico Robson Alain Veloso, `CRC-TO 002032/O-5 T-GO` em `dado` e `link`; sede na Av. Ministro Alfredo Nasser, nº 727, Centro, Formoso-GO; links para a Política de Privacidade (LGPD), as Fontes legais e a Marca; e a linha "Em conformidade com a LGPD e o Código de Ética do CFC (NBC PG 01)."
""")

# ---------------------------------------------------------------- cover
w("components/Cover/preview.html", """<!-- @dsCard height=288 -->
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>ORGATEC</title>
""" + FONTES_LINK + """
<style>
  html, body { margin:0; height:100%; }
  body { background:var(--fundo); color:var(--tinta); font-family:var(--font-sans); overflow:hidden; }
  .cover { position:relative; height:288px; overflow:hidden; }
  .art { position:absolute; top:0; left:480px; width:480px; height:288px; overflow:hidden; }
  .art svg { display:block; width:480px; height:288px; }
  .navy { fill:var(--faixa-1); }
  .azul { fill:var(--faixa-2); }
  .medio { fill:var(--faixa-3); }
  .ciano { fill:var(--faixa-4); }
  .ponto { fill:var(--marca-ciano-luz); }
  .faixa { rx:var(--raio-2xl); }
  .words { position:absolute; left:var(--espaco-8); bottom:var(--espaco-8); max-width:440px; }
  .name { margin:0; font-size:84px; line-height:.92; font-weight:800; letter-spacing:.04em; color:var(--tinta); }
  .tag { margin:var(--espaco-3) 0 0 4px; font-size:13px; line-height:20px; font-weight:600; letter-spacing:.32em; text-transform:uppercase; color:var(--tinta-suave); }
</style>
</head>
<body>
<div class="cover">
<div class="art" aria-hidden="true">
<svg viewBox="0 0 480 288" width="480" height="288">
<!--
  blocos      faixa-1 (marca-navy) 144x288, sangra no topo, o maior · faixa-2 (marca-azul) 112x232 · faixa-3 (marca-azul-medio) 88x192 · faixa-4 (marca-ciano) 64x152; no escuro sobem um tom, nesta ordem, como as faixas do símbolo; cerca de 34% de 960x288
  arranjo     faixa de blocos desiguais, da esquerda para a direita, base comum espaco-6 acima da borda, vãos espaco-2 no fundo (os vãos brancos do símbolo), topos em degrau
  padrão      grade de pontos, da linha "grade de pontos do hero a 16 px": 5x8 pontos marca-ciano-luz a passo espaco-4 sobre o bloco navy, como o hero do site
  escalas     larguras em múltiplos de espaco-2; vãos espaco-2; passo espaco-4; cantos raio-2xl; ponto de raio 1.5
-->
<rect class="navy faixa" x="40" y="-24" width="144" height="288" rx="16"/>
<rect class="azul faixa" x="192" y="32" width="112" height="232" rx="16"/>
<rect class="medio faixa" x="312" y="72" width="88" height="192" rx="16"/>
<rect class="ciano faixa" x="408" y="112" width="64" height="152" rx="16"/>
""" + "\n".join(f'<circle class="ponto" cx="{80 + 16 * i}" cy="{120 + 16 * j}" r="1.5"/>' for i in range(5) for j in range(8)) + """
</svg>
</div>
<div class="words">
<h1 class="name">ORGATEC</h1>
<p class="tag">Inteligência Tributária</p>
</div>
</div>
</body>
</html>
""")

# ---------------------------------------------------------------- index
ids = {
    "Simbolo": [("orgatec-simbolo.svg", "f5d49cdbb2b2d5d984107bfd6adc1cb1", 2213, "image/svg+xml"),
                ("orgatec-simbolo-mono.svg", "d21f8f51926a41a782c75dd2bcadf421", 737, "image/svg+xml"),
                ("orgatec-simbolo-branco.svg", "f9ef51cb15fcca2471163c2cc6ab2464", 737, "image/svg+xml")],
    "Assinaturas": [("orgatec-horizontal.svg", "6ace5ccc1f54f284116ea2a4a7e2701f", 2652, "image/svg+xml"),
                    ("orgatec-horizontal.png", "331103ebeb64f9c60166a08146a36c4c", 51801, "image/png"),
                    ("orgatec-horizontal-negativo.svg", "002005400b4cc8d76e5293ed9b45859a", 2652, "image/svg+xml"),
                    ("orgatec-horizontal-negativo.png", "53739955ac9491e4ebf02f1b06d08b13", 45377, "image/png"),
                    ("orgatec-horizontal-mono.svg", "23476d126a8d689a04553b4e49465f6e", 1178, "image/svg+xml"),
                    ("orgatec-vertical.svg", "bdce24d36e82a0e4dbe9a1c86e624d7c", 2729, "image/svg+xml"),
                    ("orgatec-vertical.png", "a42e2c15140f113f772a06205c35a9ba", 45244, "image/png")],
    "Icones": [("orgatec-app.svg", "b218dc8a4a1c4795d7b08be0a27b6f98", 2332, "image/svg+xml"),
               ("orgatec-app-512.png", "ba46f87b22f9dc495840125b4ca15d89", 26311, "image/png"),
               ("orgatec-app-escuro.svg", "17223995f5ae3ca77d2c54f92d1ee96e", 1037, "image/svg+xml"),
               ("orgatec-app-escuro-512.png", "892be8db52b03747145ecfa197a75f2f", 103230, "image/png"),
               ("favicon.svg", "6c6e375f5b1870dea3ec935fdfe46c96", 2265, "image/svg+xml"),
               ("favicon-32.png", "3ccb93e46c4fc2d5b0ea2b845610132f", 1633, "image/png"),
               ("apple-touch-icon.png", "c75e11c871522bf032804559037783c0", 7120, "image/png"),
               ("og-image.png", "99805a29cc6878707b1e45bbe3392eca", 255875, "image/png")],
}
tiles = {"Simbolo": "m", "Assinaturas": "l", "Icones": "s"}
indice = {
    "v": 3, "layout": "files",
    "createdOnFiles": {"v": 1, "at": AGORA},
    "title": "orgatec-template2",
    "namespace": "OrgatecUI",
    "libraries": [{"name": "react", "version": "18"}, {"name": "react-dom", "version": "18"}],
    "sections": {},
    "groups": list(ids),
    "assetGroups": {g: {"name": g, "tile": tiles[g], "order": [f[0] for f in fs],
                        "files": {f[0]: {"name": f[0], "blob": f[1], "size": f[2], "type": f[3]} for f in fs}} for g, fs in ids.items()},
    "blobs": {},
    "docs": {"readme": "project/README.md", "sections": []},
    "lastChange": {"by": "Claude", "via": "Claude Code", "at": AGORA, "note": "Criado a partir de site/marca.html e do site ORGATEC."},
}
w("design-system.json", json.dumps(indice, ensure_ascii=False, indent=2))

print("\n".join(str(p.relative_to(OUT.parent)).replace("\\", "/") for p in sorted(OUT.rglob("*")) if p.is_file()))
