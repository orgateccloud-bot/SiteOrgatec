"""Gera as páginas do site organizadas em torno do eixo tributário, inclusive a página inicial.

Uso:  python tools/gerar_paginas.py

Cada página declara o objetivo que atende (captação, retenção, autoridade) em `data-objetivo`.
O conteúdo legal NÃO fica neste arquivo: blocos com data-itens, data-noticias, data-alertas e
data-linha-tempo são preenchidos no navegador por assets/js/paginas.js a partir de
reforma-itens.js, fontes.js e regras.js. Simulador, calendário, alertas regionais, demonstrações e
formulários são ligados por assets/js/app.js pelos mesmos IDs da página inicial antiga
(_legado/index-2026-10-31.html). Aqui só há estrutura, chamadas e textos institucionais.
"""

from __future__ import annotations

from pathlib import Path

import layout
from gerar_imagens_compartilhar import imagem_de  # og:image própria da página, quando gerada

RAIZ = Path(__file__).resolve().parent.parent
SITE = RAIZ / "site"
WHATS = 'href="https://wa.me/5562992949161" data-link="whatsapp" target="_blank" rel="noopener"'
MSG_DIAGNOSTICO = "Olá! Quero agendar um diagnóstico tributário da reforma com a ORGATEC."


# Páginas que descrevem um serviço da ORGATEC: ganham JSON-LD Service (nome do serviço)
SERVICOS_SCHEMA = {"tributario/index.html": "Consultoria tributária e reforma", "solucoes/index.html": "Soluções do escritório",
                   "solucoes/conciliacao.html": "Conciliação bancária", "solucoes/auditoria-rural.html": "Auditoria forense rural de NFA-e"}


def pagina(caminho: str, titulo: str, descricao: str, ativo: str | None, objetivo: str, corpo: str,
           indexar: bool = True, extra: list[str] | None = None, trilha: list | None = None,
           head_extra: str = "", barra: bool = True) -> None:
    p = "../" * caminho.count("/")
    if trilha:
        head_extra += layout.breadcrumb(trilha, caminho)
    if caminho in SERVICOS_SCHEMA:
        head_extra += layout.servico_jsonld(SERVICOS_SCHEMA[caminho], descricao, caminho)
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
{layout.head(titulo, descricao, p, caminho, indexar=indexar, extra=head_extra, imagem=imagem_de(caminho))}
</head>
<body class="text-ink font-sans antialiased{" com-barra-movel" if barra else ""}" data-layout="paginas">
{layout.cabecalho(p, ativo, caminho)}
    <!-- Objetivo: {objetivo} -->
    <main data-objetivo="{objetivo}">
{layout.trilha(p, trilha) if trilha else ""}
{corpo.replace("{p}", p)}
    </main>
{layout.rodape(p)}
{layout.barra_movel(p) if barra else ""}
{layout.scripts(p, extra)}
</body>
</html>
"""
    destino = SITE / caminho
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8", newline="\n")
    print("OK", caminho)


def hero(sobre: str, titulo: str, lead: str, ctas: str, compacto: bool = False) -> str:
    """Herói no design ORGATEC Trilha: sem faixa escura; o fundo é o da página (com brilho no estilo flutuante).
    compacto: no celular, menos espaço e título menor, para páginas que precisam mostrar conteúdo útil na primeira tela."""
    return f"""        <section class="{"py-6 sm:py-16 lg:py-24" if compacto else "py-16 lg:py-24"}" data-hero>
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="max-w-3xl">
                    <p class="eyebrow">{sobre}</p>
                    <h1 class="{"text-3xl sm:text-6xl my-3 sm:my-6" if compacto else "text-4xl sm:text-6xl my-6"} font-extrabold leading-[1.05] text-ink">{titulo}</h1>
                    <p class="text-lg text-muted {"mb-5 sm:mb-8 line-clamp-3 sm:line-clamp-none" if compacto else "mb-8"} leading-relaxed">{lead}</p>
                    <div class="flex flex-col sm:flex-row gap-3">{ctas}</div>
                </div>
            </div>
        </section>"""


def intro(sobre: str, titulo: str, texto: str = "", depois: str = "", compacto: bool = False) -> str:
    """Abertura curta das páginas internas (ferramentas, cliente, contato). compacto: no celular, sem o texto e com menos
    espaço, para a página que precisa mostrar a decisão na primeira tela (Janela de Campo)."""
    classe_texto = "text-tinta-suave max-w-3xl" + (" hidden sm:block" if compacto else "")
    paragrafo = f'\n                <p class="{classe_texto}">{texto}</p>' if texto else ""
    return f"""        <section class="{"py-4 sm:py-14" if compacto else "py-10 sm:py-14"} bg-superficie border-b border-linha" data-hero>
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <p class="eyebrow">{sobre}</p>
                <h1 class="text-3xl sm:text-4xl font-extrabold text-tinta tracking-tight mt-2 mb-4">{titulo}</h1>{paragrafo}
{depois}
            </div>
        </section>"""


def secao(sobre: str, titulo: str, corpo: str, fundo: str = "bg-fundo", id_: str = "", compacto: bool = False) -> str:
    """Seção com título. compacto: menos espaço vertical no celular (páginas que precisam ser curtas)."""
    ident = f' id="{id_}"' if id_ else ""
    return f"""        <section{ident} class="{"py-8 sm:py-16" if compacto else "py-16"} {fundo}">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <p class="eyebrow">{sobre}</p>
                <h2 class="text-3xl font-bold text-tinta mt-2 mb-6">{titulo}</h2>
{corpo}
            </div>
        </section>"""


def itens(destino: str | None = None, setor: str | None = None, limite: int = 0, filtros: bool = False,
          recolher: bool = False, temas: bool = False, inicial: int = 0) -> str:
    """Lista de itens da reforma. recolher: cada item abre sob demanda (<details>), com as fontes dentro; temas: chips por tema
    (campo opcional `tema` dos itens; os chips são montados no navegador só com os temas que têm item)."""
    attrs = "".join([f' data-destino="{destino}"' if destino else "", f' data-setor="{setor}"' if setor else "",
                     f' data-limite="{limite}"' if limite else "", " data-recolher" if recolher else "",
                     f' data-inicial="{inicial}"' if inicial else ""])
    seletores = ""
    if filtros:
        seletores = """                    <div class="flex flex-wrap items-end gap-3 mb-6">
                        <div class="og-campo"><label class="og-campo-rotulo" for="fSetor">Setor</label><select id="fSetor" class="og-campo-controle og-campo-md" data-filtro="setor"><option value="">Todos</option><option value="agro">Agro</option><option value="transporte">Transporte</option></select></div>
                        <div class="og-campo"><label class="og-campo-rotulo" for="fTributo">Tributo</label><select id="fTributo" class="og-campo-controle og-campo-md" data-filtro="tributo"><option value="">Todos</option><option value="cbs">CBS</option><option value="ibs">IBS</option><option value="is">Imposto Seletivo</option><option value="piscofins">PIS/Cofins</option><option value="icms">ICMS</option><option value="iss">ISS</option><option value="ipi">IPI</option><option value="irpf">IRPF</option></select></div>
                        <div class="og-campo"><label class="og-campo-rotulo" for="fStatus">Status</label><select id="fStatus" class="og-campo-controle og-campo-md" data-filtro="status"><option value="">Todos</option><option value="em_vigor">Em vigor</option><option value="vigencia_futura">Aprovado, vigência futura</option><option value="pendente_regulamentacao">Pendente de regulamentação</option><option value="incerto">Incerto</option></select></div>
                        <span class="text-sm text-tinta-fraca pb-2" data-contagem aria-live="polite"></span>
                    </div>
"""
    if temas:
        seletores += """                    <div class="campo-abas mb-3" role="group" aria-label="Tema" data-temas hidden></div>
                    <p class="text-sm text-tinta-fraca mb-3" data-contagem aria-live="polite"></p>
"""
    mais = ('\n                    <p class="mt-4"><button type="button" class="og-btn og-btn-contorno og-btn-md" data-ver-todos hidden>Ver todos os pontos</button></p>'
            if inicial else "")
    return f"""                <div data-itens{attrs}>
{seletores}                    <div class="lista-itens grid grid-cols-1 md:grid-cols-2 gap-4"></div>{mais}
                </div>"""


def cartao(ref: str, titulo: str, texto: str, href: str) -> str:
    return f'<a href="{href}" class="og-cartao"><span class="og-cartao-ref">{ref}</span><h3 class="og-cartao-titulo">{titulo}</h3><p class="og-cartao-texto">{texto}</p></a>'


def grade(cartoes: list[str], colunas: str = "md:grid-cols-2 lg:grid-cols-4", base: str = "grid-cols-1") -> str:
    juntos = "\n                    ".join(cartoes)
    return f'                <div class="grid {base} {colunas} gap-4">\n                    {juntos}\n                </div>'


def faixa_cta(titulo: str, texto: str, compacto: bool = False) -> str:
    return f"""        <section class="{"py-8 sm:py-16" if compacto else "py-16"} bg-superficie border-t border-linha">
            <div class="max-w-3xl mx-auto px-4 sm:px-6 text-center">
                <h2 class="text-2xl font-bold text-tinta mb-3">{titulo}</h2>
                <p class="text-tinta-suave mb-6">{texto}</p>
                <div class="flex flex-col sm:flex-row gap-3 justify-center">
                    <a {WHATS} data-msg="{MSG_DIAGNOSTICO}" class="og-btn og-btn-contato og-btn-lg">Agendar Diagnóstico com Especialista</a>
                    <a href="{{p}}ferramentas/simulador.html" class="og-btn og-btn-primario og-btn-lg">Testar Simulador Tributário</a>
                </div>
                <p class="text-xs text-tinta-fraca mt-6 font-mono">{layout.AVISO_LEGAL}</p>
            </div>
        </section>"""


PROVA = """        <section class="bg-superficie border-b border-linha">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex flex-wrap gap-x-8 gap-y-2 text-sm text-tinta-suave items-center">
                <strong class="text-tinta" data-prova-anos hidden></strong>
                <span>Responsável técnico: <strong class="text-tinta">Robson Alain Veloso</strong>, <span class="font-mono text-link">CRC-TO 002032/O-5 T-GO</span></span>
                <span>Atuação em agro, transporte, lucro real e produtor rural</span>
                <span>Base legal citada em cada orientação</span>
            </div>
        </section>"""

# Cartões reaproveitados em mais de uma página (mesmo texto = mesma afirmação conferida)
C_SIMPLES = cartao("LC 214/2025, art. 41", "Simples Nacional: IBS e CBS fora do DAS", "Quando vale apurar IBS e CBS no regime regular para não perder o cliente PJ.", "{p}reforma/simples-hibrido.html")
C_REAL = cartao("Lucro real e presumido", "CBS no lugar de PIS e Cofins", "A CBS substitui PIS e Cofins a partir de 2027: o impacto no lucro presumido e no lucro real.", "{p}reforma/cbs.html")
C_AGRO = cartao("LC 214/2025, arts. 137, 138 e 164 a 168", "Agro e produtor rural", "Redução de 60%, produtor não contribuinte, crédito presumido de quem compra e LCDPR.", "{p}setores/agro.html")
C_TRANSPORTE = cartao("LC 214/2025, arts. 169, 172 a 180 e 284 a 287", "Transporte", "CT-e com IBS e CBS, crédito do diesel, frete de autônomo e passageiros.", "{p}setores/transporte.html")
C_SIMULADOR = cartao("27 UFs · setor · regime", "Simulador tributário", "Compare o cenário atual com o pós-reforma e receba o diagnóstico.", "{p}ferramentas/simulador.html")
C_CALENDARIO = cartao("Federal · trabalhista · estadual", "Calendário fiscal", "Vencimentos do mês por UF, com download para a agenda e alerta por e-mail.", "{p}ferramentas/calendario.html")
C_TRANSICAO = cartao("ADCT, arts. 125 a 129", "Transição ano a ano", "O que vale de CBS, IBS, PIS/Cofins, ICMS e ISS em cada ano de 2026 a 2033.", "{p}ferramentas/index.html#transicao")
C_PRODUTOR = cartao("LC 214/2025, arts. 164 e 165", "Produtor rural contribuinte?", "Verifique pela receita do ano se o produtor fica dentro ou fora do regime regular.", "{p}ferramentas/index.html#produtor")

MARCOS = """                <ol class="marcos" data-marcos>
                    <li class="marco"><span class="bola" aria-hidden="true">1</span><h3>Levantamento</h3><p>Regime, cadastro de produtos e serviços (NCM/NBS), fornecedores por regime e contratos.</p></li>
                    <li class="marco"><span class="bola" aria-hidden="true">2</span><h3>Simulação</h3><p>Cenários de 2027, da convivência de 2029 a 2032 e do regime pleno de 2033.</p></li>
                    <li class="marco"><span class="bola" aria-hidden="true">3</span><h3>Decisão com fonte</h3><p>Recomendação por escrito, com o dispositivo legal de cada ponto e o que ainda depende de regulamentação.</p></li>
                    <li class="marco"><span class="bola" aria-hidden="true">4</span><h3>Acompanhamento</h3><p>Calendário fiscal, documentos fiscais com IBS e CBS e programa de conformidade.</p></li>
                </ol>"""

JSONLD = """
    <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "AccountingService", "name": "ORGATEC", "logo": "https://orgatec.io/assets/marca/orgatec-app-512.png",
     "url": "https://orgatec.io", "taxID": "13.155.211/0001-45", "areaServed": "BR", "telephone": "+55-62-99294-9161",
     "address": {"@type": "PostalAddress", "streetAddress": "Av. Ministro Alfredo Nasser, 727, Centro", "addressLocality": "Formoso", "addressRegion": "GO", "addressCountry": "BR"}}
    </script>"""


def secao_folha(sobre: str, titulo: str, corpo: str, fundo: str = "bg-fundo", id_: str = "", lead: str = "") -> str:
    """Seção da página inicial em "folha": cantos superiores arredondados, sobreposta à anterior, título grande e centralizado."""
    ident = f' id="{id_}"' if id_ else ""
    paragrafo = f'\n                    <p class="text-lg text-tinta-suave mt-4">{lead}</p>' if lead else ""
    return f"""        <section{ident} class="folha py-16 sm:py-20 {fundo}">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-10">
                    <p class="eyebrow">{sobre}</p>
                    <h2 class="text-3xl sm:text-5xl font-extrabold text-tinta tracking-tight mt-3">{titulo}</h2>{paragrafo}
                </div>
{corpo}
            </div>
        </section>"""


# Prévias decorativas dos cartões de ferramentas (sem números inventados; a da transição segue o ADCT, arts. 125 a 129)
PREVIAS = {
    "simulador": '<svg viewBox="0 0 200 90"><rect class="pv-fraco" x="30" y="20" width="44" height="60" rx="6"/><rect class="pv-forte" x="118" y="38" width="44" height="42" rx="6"/><text x="52" y="14">hoje</text><text x="140" y="32">2033</text></svg>',
    "calendario": '<svg viewBox="0 0 200 90">' + "".join(
        f'<rect class="{"pv-forte" if (l, c) in ((1, 4), (3, 1)) else "pv-fraco"}" x="{18 + c * 24}" y="{8 + l * 20}" width="18" height="14" rx="3"/>'
        for l in range(4) for c in range(7)) + "</svg>",
    "transicao": '<svg viewBox="0 0 200 90">' + "".join(
        f'<rect class="{"pv-forte" if v < 100 else "pv-fraco"}" x="{14 + i * 22}" y="{80 - v * 0.62:.0f}" width="16" height="{max(v * 0.62, 2):.0f}" rx="3"/>'
        for i, v in enumerate([100, 100, 100, 90, 80, 70, 60, 0])) + "</svg>",
    "produtor": '<svg viewBox="0 0 200 90"><path class="pv-arco" d="M40 80 A60 60 0 0 1 160 80"/><path class="pv-arco-forte" d="M40 80 A60 60 0 0 1 100 20"/><circle class="pv-ponto" cx="100" cy="20" r="6"/></svg>',
}


VIDRO_HEAD = """
    <link rel="stylesheet" href="assets/css/vidro.css">
    <script src="assets/js/vidro.js"></script>"""


def inicio() -> None:
    """Página inicial (inspirada na estrutura do Adobe Firefly, no design ORGATEC Trilha):
    herói com a simulação em destaque e faixa de marcos, seções em "folha" com títulos centralizados,
    ferramentas em carrossel, painel escuro de fontes oficiais. As ferramentas completas ficam nas próprias páginas."""
    heroi = f"""        <section class="holo-vitrine pt-12 pb-16 sm:pt-16 sm:pb-24" data-hero>
            <!-- Nome ORGATEC em holograma, decorativo: acompanha o ponteiro (inicio.js), parado com movimento reduzido -->
            <div class="holo-nome" aria-hidden="true" data-holo-nome><span>ORGATEC</span></div>
            <div class="max-w-4xl mx-auto px-4 sm:px-6 text-center">
                <p class="eyebrow">EC 132/2023 • LC 214/2025 • Split Payment</p>
                <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.05] text-ink my-6">Contabilidade Estratégica e <mark class="marca-texto">Inteligência Tributária</mark> para a Nova Era Fiscal.</h1>
                <p class="text-lg sm:text-xl text-muted leading-relaxed">Preparamos sua empresa em Goiás, no Tocantins, no Pará e em todo o Brasil para a transição do IBS e da CBS, protegendo seu fluxo de caixa com rigor técnico e tecnologia.</p>
                <form class="caixa-sim text-left" action="{{p}}ferramentas/simulador.html" method="get" data-sim-rapida aria-label="Simulação rápida">
                    <p class="caixa-sim-rotulo">Simule o impacto da reforma · 27 UFs</p>
                    <div class="caixa-sim-campos">
                        <label class="caixa-campo caixa-campo-setor" for="rSetor"><span>Setor</span><select id="rSetor" name="setor"></select></label>
                        <label class="caixa-campo" for="rRegime"><span>Regime atual</span><select id="rRegime" name="regime">{REGIMES}</select></label>
                        <label class="caixa-campo" for="rFat"><span>Faturamento anual (R$)</span><input id="rFat" type="text" inputmode="decimal" placeholder="ex.: 2.400.000"></label>
                        <button type="submit" class="caixa-sim-enviar" aria-label="Ver o resultado da simulação"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg><span class="caixa-sim-texto">Ver o resultado</span></button>
                    </div>
                    <p class="caixa-sim-nota">O cálculo roda no seu navegador; o faturamento não vai para o endereço da página.</p>
                </form>
                <p class="mt-6 text-sm text-tinta-suave flex flex-wrap justify-center gap-x-4 gap-y-1">
                    <a {WHATS} data-msg="{MSG_DIAGNOSTICO}" class="og-link font-semibold">Prefere conversar? Agende um diagnóstico</a>
                    <strong class="text-tinta" data-prova-anos hidden></strong>
                    <span>Responsável técnico: <strong class="text-tinta">Robson Alain Veloso</strong>, <span class="font-mono text-link">CRC-TO 002032/O-5 T-GO</span></span>
                </p>
            </div>
            <!-- Faixa de marcos (itens da reforma com fonte; rola sozinha, pausa no botão, no foco e com movimento reduzido) -->
            <div class="faixa-marcos mt-12" data-faixa-marcos>
                <div class="faixa-janela"><ul class="faixa-trilho" data-faixa-trilho aria-label="Marcos da reforma tributária"></ul></div>
                <button type="button" class="faixa-pausa" data-faixa-pausa aria-pressed="false">Pausar</button>
            </div>
        </section>"""
    transicao = f"""        <section id="agora" class="folha py-16 sm:py-20 bg-superficie">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
                <!-- Painel da transição (exemplo interativo; dados do ADCT, arts. 125 a 129, via regras.js/calculadoras.js) -->
                <aside class="og-cartao painel-transicao" aria-labelledby="ptTitulo" data-painel-transicao>
                    <img class="painel-logo" src="{{p}}assets/marca/orgatec-original.png" alt="ORGATEC" width="88" height="97">
                    <div class="pr-24">
                        <p class="eyebrow">Exemplo interativo · EC 132/2023</p>
                        <h2 id="ptTitulo" class="text-xl font-bold text-ink mt-1">Onde estamos na transição</h2>
                    </div>
                    <div class="anel-wrap">
                        <svg class="anel-progresso" viewBox="0 0 100 100" role="img" aria-labelledby="ptAnelRotulo">
                            <circle class="trilho" cx="50" cy="50" r="42"/>
                            <circle class="valor" cx="50" cy="50" r="42" transform="rotate(-90 50 50)" stroke-dasharray="263.9" stroke-dashoffset="263.9" data-anel/>
                        </svg>
                        <div class="min-w-0">
                            <p class="anel-num" id="ptAnelRotulo"><span data-progresso>0%</span><span class="sr-only"> da transição de 2026 a 2033 já passou</span></p>
                            <p class="text-sm text-muted">da transição 2026–2033 já passou</p>
                            <p class="text-sm text-ink mt-2" data-contagem-cbs></p>
                        </div>
                    </div>
                    <div>
                        <p class="eyebrow mb-2">Escolha o ano</p>
                        <div class="chips" role="group" aria-label="Ano da transição" data-anos></div>
                    </div>
                    <dl class="linha-ano" aria-live="polite" data-linha-ano></dl>
                    <p class="text-xs text-muted">Fonte: <a class="og-link" href="https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm" target="_blank" rel="noopener">ADCT, arts. 125 a 129 (EC nº 132/2023)</a>. A barra mostra quanto resta das alíquotas atuais de ICMS e ISS.</p>
                </aside>
                <div class="min-w-0">
                    <p class="eyebrow">ORGATEC em números</p>
                    <h2 class="text-3xl sm:text-4xl font-extrabold text-tinta tracking-tight mt-3 mb-6">Acompanhamento com fonte, ponto a ponto</h2>
                    <div class="numeros" data-numeros>
                        <div class="numero"><b data-contador="itens">0</b><span>pontos da reforma acompanhados, cada um com fonte oficial</span></div>
                        <div class="numero"><b data-contador="fontes">0</b><span>dispositivos legais conferidos na fonte primária</span></div>
                        <div class="numero"><b data-contador="ufs">27</b><span>UFs no simulador e no calendário fiscal</span></div>
                        <div class="numero"><b data-contador="dias">0</b><span>dias para a CBS substituir PIS e Cofins (01/01/2027)</span></div>
                    </div>
                </div>
            </div>
        </section>"""
    # Os cartões são links (funcionam sem JS); inicio.js os transforma em seletor e abre o painel do caso.
    casos = [c.replace('class="og-cartao"', f'class="og-cartao" data-caso="{k}" aria-controls="painelCaso"', 1)
             for c, k in zip([C_SIMPLES, C_REAL, C_AGRO, C_TRANSPORTE], ["simples", "real", "agro", "transporte"])]
    painel = """                <p class="text-sm text-tinta-suave mt-4 text-center" data-caso-dica hidden>Toque em um caso para ver os pontos da reforma que mais pesam nele.</p>
                <div id="painelCaso" class="og-cartao caso-painel mt-6" data-caso-painel hidden aria-live="polite"></div>"""
    ferramentas_cartoes = [
        ("simulador", C_SIMULADOR), ("calendario", C_CALENDARIO), ("transicao", C_TRANSICAO), ("produtor", C_PRODUTOR)]
    carrossel = "\n".join(
        "                        " + c.replace('class="og-cartao">', f'class="og-cartao carrossel-cartao"><span class="previa" aria-hidden="true">{PREVIAS[k]}</span>', 1)
        for k, c in ferramentas_cartoes)
    ferramentas_home = f"""                <div class="carrossel" data-carrossel>
                    <div class="carrossel-trilho" data-carrossel-trilho tabindex="0" role="region" aria-label="Ferramentas (role para o lado)">
{carrossel}
                    </div>
                    <div class="carrossel-botoes">
                        <button type="button" class="carrossel-botao" data-carrossel-ant aria-label="Ferramenta anterior">←</button>
                        <button type="button" class="carrossel-botao" data-carrossel-prox aria-label="Próxima ferramenta">→</button>
                    </div>
                </div>
                <p class="text-center mt-6"><a href="{{p}}solucoes/index.html" class="og-link">Conheça também os sistemas do escritório: conciliação bancária e auditoria forense rural →</a></p>
                <p class="text-center mt-3"><a href="{{p}}compliance/termometro.html" class="og-link">Sua empresa está em dia? Faça o termômetro de conformidade →</a></p>"""
    ultimas = """                <ul class="grid grid-cols-1 md:grid-cols-3 gap-4" data-noticias="3" data-base="{p}"></ul>
                <p class="text-center mt-8"><a href="{p}reforma/index.html" class="og-link">Ver todos os itens na Central da Reforma →</a></p>"""
    fontes = """                <div class="grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4" data-fontes-orgaos></div>
                <p class="text-center text-sm text-tinta-suave mt-8">Citar um órgão como fonte não indica parceria nem endosso. <a href="{p}reforma/fontes.html" class="og-link">Ver todos os dispositivos citados →</a></p>"""
    perguntas = """                <div class="faq max-w-3xl mx-auto" data-faq data-limite="4"></div>
                <p class="text-sm text-muted mt-6 text-center">As respostas trazem só o que está na norma citada. Para o efeito na sua empresa, <a href="{p}contato/index.html" class="og-link">fale com a equipe</a> ou veja <a href="{p}reforma/index.html" class="og-link">todos os pontos na Central da Reforma</a>.</p>"""
    corpo = "\n".join([
        heroi, transicao,
        secao_folha("Qual é o seu caso?", "Comece pela situação da sua empresa", grade(casos) + "\n" + painel, "bg-fundo", "casos"),
        secao_folha("Central da Reforma", "Últimas da reforma", ultimas, "bg-superficie", "ultimas"),
        secao_folha("Ferramentas", "Simule antes de decidir", ferramentas_home, "bg-fundo", "ferramentas",
                    "Simulador, calendário e calculadoras com a regra legal de cada ponto."),
        secao_folha("Transparência", "Fontes oficiais citadas", fontes, "folha-escura", "fontes",
                    "Cada orientação do site aponta para o texto oficial. Estes são os órgãos de onde vêm as citações."),
        secao_folha("Perguntas frequentes", "O que os clientes mais perguntam sobre a reforma", perguntas, "bg-fundo", "perguntas"),
        faixa_cta("Comece pelo diagnóstico", "Em uma conversa, levantamos regime, setor e fornecedores e indicamos o que precisa de decisão ainda em 2026."),
    ])
    pagina(layout.INICIO, "Contabilidade Consultiva e Inteligência Tributária",
           "Contabilidade consultiva e transição para a Reforma Tributária (IBS, CBS e split payment), em GO, TO e PA. Resp. técnico: Robson Veloso, CRC-TO 002032/O-5.",
           None, "captação", corpo, extra=["inicio.js"],
           # Vitrine em vidro azul com a logo em holograma (ideia/vidro-azul): vale só na paleta Azul flutuante escuro
           head_extra=VIDRO_HEAD + JSONLD)


def tributario() -> None:
    servicos = [
        cartao("EC 132/2023 · LC 214/2025", "Diagnóstico da reforma", "Regime, fornecedores, NCM/NBS e preço: o impacto de 2027 a 2033 na sua empresa.", "{p}reforma/index.html"),
        C_SIMPLES,
        cartao("LC 214/2025, arts. 378 a 383", "Créditos de PIS e Cofins antes da extinção", "Levantamento e uso dos saldos que continuam válidos depois de 2027.", "{p}reforma/index.html#item-saldo-piscofins"),
        cartao("Lucro real", "Lucro real na transição", "Crédito amplo de IBS e CBS, estoque de 1º/01/2027 e margem no período de convivência.", "{p}reforma/index.html#item-nao-cumulatividade"),
        cartao("LC 214/2025, arts. 164 a 168", "Produtor rural e LCDPR", "Contribuinte ou não contribuinte, crédito presumido do comprador e o LCDPR do IRPF.", "{p}setores/agro.html"),
        cartao("LC 214/2025, arts. 31 a 35", "Split payment e capital de giro", "Preparar caixa, conciliação e cadastros para o recolhimento na liquidação.", "{p}reforma/split-payment.html"),
    ]
    corpo = "\n".join([
        hero("Consultoria tributária", 'Reforma tributária com <mark class="marca-texto">base legal</mark> em cada decisão.',
             "Do agro ao transporte, do lucro real ao produtor rural: a ORGATEC traduz a EC 132/2023 e a LC 214/2025 em números e prazos para a sua empresa.",
             f'<a {WHATS} data-msg="{MSG_DIAGNOSTICO}" class="og-btn og-btn-contato og-btn-lg">Agendar Diagnóstico com Especialista</a>'
             '<a href="{p}ferramentas/simulador.html" class="og-btn og-btn-sobre-palco og-btn-lg">Testar Simulador Tributário</a>'),
        PROVA,
        secao("Serviços", "O que a consultoria tributária entrega", grade(servicos, "md:grid-cols-2 lg:grid-cols-3")),
        secao("Como funciona", "Do diagnóstico à transição", MARCOS, "bg-superficie", "como-funciona"),
        secao("Reforma", "Pontos que mais afetam a sua decisão", itens(destino="tributario", limite=6) +
              '\n                <p class="mt-6"><a href="{p}reforma/index.html" class="og-link">Ver todos os itens na Central da Reforma →</a></p>'),
        faixa_cta("Comece pelo diagnóstico", "Em uma conversa, levantamos regime, setor e fornecedores e indicamos o que precisa de decisão ainda em 2026."),
    ])
    pagina("tributario/index.html", "Consultoria tributária e reforma", "Consultoria tributária para a reforma (EC 132/2023, LC 214/2025): diagnóstico, Simples, créditos de PIS/Cofins, lucro real, produtor rural e split payment.",
           "tributario", "captação + autoridade", corpo, extra=["inicio.js"], trilha=[("Consultoria", None)])


def reforma() -> None:
    legenda = """                <div class="flex flex-wrap gap-3 text-sm mb-2">
                    <span class="og-selo og-selo-definido">Em vigor</span>
                    <span class="og-selo og-selo-futuro">Aprovado, vigência futura</span>
                    <span class="og-selo og-selo-pendente">Pendente de regulamentação</span>
                    <span class="og-selo og-selo-pendente">Incerto: não verificado</span>
                </div>
                <p class="text-sm text-tinta-suave max-w-3xl">Cada item traz o fato com a fonte oficial, a data em que foi conferido e o status. Quando houver, a orientação da ORGATEC aparece separada e identificada como interpretação.</p>"""
    linha = """                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left min-w-[640px]">
                        <thead><tr class="text-xs uppercase text-tinta-fraca border-b border-linha"><th class="py-2 pr-4">Ano</th><th class="py-2 pr-4">CBS</th><th class="py-2 pr-4">IBS</th><th class="py-2 pr-4">PIS/Cofins</th><th class="py-2 pr-4">IPI</th><th class="py-2">ICMS e ISS</th></tr></thead>
                        <tbody data-linha-tempo></tbody>
                    </table>
                </div>
                <p class="text-xs text-tinta-fraca mt-3">Fonte: ADCT, arts. 125 a 129 (EC nº 132/2023).</p>"""
    artigos = [
        cartao("LC nº 214/2025", "A lei do IBS, da CBS e do IS", "Estrutura da lei e cronograma.", "lc-214-2025.html"),
        cartao("IBS", "O imposto que substitui ICMS e ISS", "Destino, transição e benefícios.", "ibs.html"),
        cartao("CBS", "A contribuição que substitui PIS e Cofins", "Impacto no presumido e no real.", "cbs.html"),
        cartao("Split Payment", "Tributo separado no pagamento", "Implantação gradual e caixa.", "split-payment.html"),
        cartao("LC 214/2025, art. 41", "IBS e CBS fora do DAS", "A opção do Simples Nacional.", "simples-hibrido.html"),
        cartao("Transparência", "Fontes legais", "Tudo o que o site cita.", "fontes.html"),
    ]
    corpo = "\n".join([
        intro("Central da Reforma", "O que já vale, o que vem e o que falta regulamentar", "",
              '                <p class="text-sm text-tinta-fraca font-mono mb-6">Levantamento de referência: 31/10/2026 · Responsável técnico: Robson Alain Veloso, CRC-TO 002032/O-5 T-GO</p>\n' + legenda),
        secao("Guias", "Os temas da reforma", grade(artigos, "md:grid-cols-3"), id_="guias"),
        secao("Cronograma", "Linha do tempo 2026–2033", linha, "bg-superficie"),
        secao("Itens", "Todos os pontos da reforma", itens(filtros=True), id_="itens"),
        secao("Notícias", "Últimas atualizações", '                <ul class="grid grid-cols-1 md:grid-cols-2 gap-4" data-noticias="8" data-base="{p}"></ul>', "bg-superficie", "noticias"),
        secao("Perguntas frequentes", "O que mais perguntam sobre a reforma", '                <div class="faq max-w-3xl" data-faq-itens="reforma"></div>', id_="perguntas"),
        faixa_cta("A reforma muda o preço do seu produto", "Transforme estes itens em decisões: regime, fornecedores, contratos e caixa."),
    ])
    pagina("reforma/index.html", "Central da Reforma Tributária", "Itens da reforma tributária com fonte oficial, data de consulta e status (em vigor, futuro, pendente). Linha do tempo 2026 a 2033 e notícias.",
           "reforma", "autoridade + retenção", corpo, trilha=[("Reforma", None)])


def subnav_setores(ativo: str) -> str:
    botoes = "".join(f'<a href="{arq}" class="og-btn og-btn-{"primario" if chave == ativo else "contorno"} og-btn-md">{rot}</a>'
                     for chave, rot, arq in [("agro", "Agro", "agro.html"), ("transporte", "Transporte", "transporte.html"),
                                             ("regional", "Alertas regionais", "regional.html"), ("campo", "Janela de Campo", "janela-de-campo.html"),
                                             ("mercado", "Cotações e notícias", "agro-mercado.html")]
                     # Sem alertas do setor, o botão leva a uma página vazia para o transporte (SETORES_REGIONAIS em regras.js)
                     if not (chave == "regional" and ativo == "transporte"))
    return f'        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-8 flex flex-nowrap sm:flex-wrap gap-3 overflow-x-auto" data-subnav-setores>{botoes}</div>'


# Página "Por público" da área de Compliance que corresponde ao setor (só as que já estão no ar)
COMPLIANCE_SETOR = {"transporte": "compliance/publico/transportador.html", "agro": "compliance/publico/produtor-rural.html"}


def compliance_do_setor(slug: str) -> str:
    if slug not in COMPLIANCE_SETOR:
        return ""
    return secao("Compliance", "O que o seu setor precisa cumprir",
                 '                <p class="text-tinta-suave max-w-3xl mb-6">Além do IBS e da CBS, o setor tem obrigações próprias, com prazo e penalidade. Elas estão reunidas, com a fonte oficial, na área de Compliance.</p>\n'
                 f'                <a href="{{p}}{COMPLIANCE_SETOR[slug]}" class="og-btn og-btn-primario og-btn-lg" data-compliance-setor>Ver o que o setor precisa cumprir</a>',
                 "bg-superficie", "compliance")


def caminho_agro(ref: str, titulo: str, texto: str, href: str) -> str:
    """Cartão de um caminho do produtor rural."""
    return (f'<article class="og-cartao" data-agro-caminho><span class="og-cartao-ref">{ref}</span>'
            f'<h3 class="og-cartao-titulo"><a href="{href}" class="hover:text-acao">{titulo}</a></h3>'
            f'<p class="og-cartao-texto hidden sm:block">{texto}</p></article>')


def caminhos_agro() -> str:
    """Entrada única do produtor rural: o que ele quer fazer, em 4 caminhos que reúnem o conteúdo antes espalhado."""
    return secao("Para o produtor rural", "O que você quer fazer hoje?", grade([
        caminho_agro("Tempo", "Janela de Campo", "A janela do dia por operação, os próximos 7 dias e o satélite.", "{p}setores/janela-de-campo.html"),
        caminho_agro("Mercado", "Cotações e notícias", "Indicador do CEPEA, notícias e legislação por atividade.", "{p}setores/agro-mercado.html"),
        caminho_agro("Tributos e obrigações", "Reforma, LCDPR e Funrural", "Os pontos da reforma, a calculadora do produtor, o compliance e os alertas do agro.", "#tributos"),
        caminho_agro("Serviços", "Auditoria rural e diagnóstico", "As notas do produtor conferidas uma a uma, com laudo.", "{p}solucoes/auditoria-rural.html"),
    ], "lg:grid-cols-4", "grid-cols-2"), "bg-fundo", compacto=True)


def hoje_agro() -> str:
    """Resumo do dia na região escolhida, preenchido por assets/js/agro-hoje.js com o boletim publicado da Janela de Campo.
    Sem JavaScript ou sem boletim válido, fica o texto fixo e o link (nenhum número é escrito aqui)."""
    return """        <section class="py-6" aria-labelledby="agroHojeTitulo" data-agro-hoje data-campo-dados="{p}dados/campo/">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="og-cartao grid gap-3">
                    <div><h2 id="agroHojeTitulo" class="eyebrow">Hoje na sua região<span class="sr-only">: <span data-agro-hoje-regiao>Janela de Campo</span></span></h2></div>
                    <div class="grid gap-3" data-agro-hoje-corpo>
                        <p class="og-cartao-texto">Veja se hoje dá para pulverizar, plantar, colher e fazer o manejo dos animais na sua região.</p>
                    </div>
                    <p><a href="janela-de-campo.html" class="og-btn og-btn-primario og-btn-md" data-agro-hoje-link>Abrir a Janela de Campo</a></p>
                </div>
            </div>
        </section>"""


def proximos_passos_agro() -> str:
    """Chamadas claras: a calculadora do produtor e a auditoria rural; e, em links, o compliance e os alertas do setor."""
    return secao("Próximos passos", "Do número ao laudo", f"""{grade([
        cartao("Calculadora", "O produtor é contribuinte?", "Veja, pela receita do ano, se o produtor fica dentro ou fora do regime regular de IBS e CBS.", "{p}ferramentas/index.html#produtor"),
        cartao("Serviço do escritório", "Auditoria forense rural (NFA-e)", "As notas do produtor conferidas uma a uma, com laudo.", "{p}solucoes/auditoria-rural.html"),
    ], "md:grid-cols-2")}
                <p class="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm">
                    <a href="{{p}}{COMPLIANCE_SETOR["agro"]}" class="og-link" data-compliance-setor>O que o produtor rural precisa cumprir (Compliance)</a>
                    <a href="regional.html?setor=agro" class="og-link" data-alertas-agro>Alertas do agro por estado: GO, TO e PA</a>
                    <a href="regional.html" class="og-link">Alertas de atacado e indústria</a>
                </p>""", "bg-superficie", "proximos-passos", compacto=True)


def setor_agro() -> None:
    """Página Agro: entrada do produtor rural. Resumo do dia, 4 caminhos, pontos da reforma recolhidos por tema e próximos passos."""
    titulo = "A reforma tributária no agronegócio e para o produtor rural."
    lead = ("Redução de 60% para in natura e insumos, produtor não contribuinte até R$ 3,6 milhões, crédito presumido de quem compra e LCDPR: "
            "o que muda no campo.")
    porque = ("O agro tem as maiores reduções da reforma, mas também as escolhas mais difíceis: ser ou não contribuinte de IBS e CBS muda o preço negociado "
              "com cooperativas, tradings e frigoríficos, e o fim gradual do ICMS reduz o valor dos incentivos estaduais de 2029 a 2032.")
    corpo = "\n".join([
        hero("Setor · Agro", titulo, lead,
             f'<a {WHATS} data-msg="Olá! Quero falar sobre a reforma tributária no setor de agro." class="og-btn og-btn-contato og-btn-lg">Agendar Diagnóstico com Especialista</a>'
             '<span class="hidden sm:contents"><a href="{p}ferramentas/index.html#produtor" class="og-btn og-btn-sobre-palco og-btn-lg">Usar a ferramenta do setor</a></span>', compacto=True),
        subnav_setores("agro"),
        hoje_agro(),
        caminhos_agro(),
        secao("Itens da reforma", "Pontos da reforma para o agro",
              f'                <details class="mb-4 max-w-3xl"><summary class="font-semibold cursor-pointer py-2">Por que importa para o agro</summary>'
              f'<p class="text-tinta-suave leading-relaxed mt-2">{porque}</p></details>\n'
              + itens(destino="setor-agro", setor="agro", recolher=True, temas=True, inicial=5), "bg-fundo", "tributos", compacto=True),
        proximos_passos_agro(),
        faixa_cta("Diagnóstico para agro", "Levantamos as operações, os fornecedores e os créditos e mostramos o efeito ano a ano.", compacto=True),
    ])
    pagina("setores/agro.html", "Reforma tributária no agro", lead, "setores", "captação + autoridade", corpo,
           extra=["campo.js", "agro-hoje.js"], trilha=[("Setores", None), ("Agro", None)])


def setor(slug: str, nome: str, titulo: str, lead: str, porque: str, ferramenta: str) -> None:
    corpo = "\n".join([
        hero(f"Setor · {nome}", titulo, lead,
             f'<a {WHATS} data-msg="Olá! Quero falar sobre a reforma tributária no setor de {nome.lower()}." class="og-btn og-btn-contato og-btn-lg">Agendar Diagnóstico com Especialista</a>'
             f'<a href="{ferramenta}" class="og-btn og-btn-sobre-palco og-btn-lg">Usar a ferramenta do setor</a>'),
        subnav_setores(slug),
        secao("Por que importa", f"A reforma no {nome.lower()}", f'                <p class="text-tinta-suave max-w-3xl leading-relaxed">{porque}</p>'),
        secao("Itens", f"Pontos da reforma para {nome.lower()}", itens(destino=f"setor-{slug}", setor=slug)),
        compliance_do_setor(slug),
        # Transporte: as obrigações do transportador (tabela 3.6 de docs/relatorio-publicos-reforma-compliance.md) aparecem aqui, com fonte e revisão
        (secao("Obrigações do transportador", "RNTRC, CIOT, piso de frete e vale-pedágio",
               '                <p class="text-tinta-suave max-w-3xl mb-6">Cada ponto traz a norma, a data de consulta e o status da revisão técnica. Não substitui a ANTT nem o parecer do contador.</p>\n'
               + itens(destino="publico-transportador", recolher=True, inicial=6), "bg-superficie", "obrigacoes") if slug == "transporte" else ""),
        faixa_cta(f"Diagnóstico para {nome.lower()}", "Levantamos as operações, os fornecedores e os créditos e mostramos o efeito ano a ano."),
    ])
    pagina(f"setores/{slug}.html", f"Reforma tributária no {nome.lower()}", lead, "setores", "captação + autoridade", corpo,
           extra=["compliance-itens.js"] if slug == "transporte" else None, trilha=[("Setores", None), (nome, None)])


# Cards por atividade (marca Orgatec Audi Agro): configuração única em tools/agro_fontes.json
AGRO = RAIZ / "tools" / "agro_fontes.json"
# Cores do widget do CEPEA: com a marca (verde #028227 medido na logo por tools/extrair_logo_audi_agro.py) ou neutras
# (cinza-azulado claro), que são as de hoje: a marca está desligada em agro_fontes.json (marca.exibir)
WIDGET_CORES_MARCA = {"corfundo": "e6f2e9", "cortexto": "111111", "corlinha": "f4faf5"}
WIDGET_CORES_NEUTRAS = {"corfundo": "eef2f7", "cortexto": "111111", "corlinha": "f7f9fc"}


def widgets_cepea(cfg: dict) -> None:
    """Uma página por card com o widget oficial do CEPEA (o único uso liberado sem autorização formal).
    Abertas pelos cards num iframe isolado; CSP própria em /cotacoes/ (backend/app.py e firebase.json)."""
    from html import escape
    from urllib.parse import urlencode
    destino = SITE / "cotacoes"  # sem "widget" no caminho: bloqueadores de anúncio barram endereços com essa palavra
    destino.mkdir(exist_ok=True)
    for a in cfg["atividades"]:
        if not a["cepea"]:
            continue
        cores = WIDGET_CORES_MARCA if cfg.get("marca", {}).get("exibir") else WIDGET_CORES_NEUTRAS
        params = urlencode([("fonte", "arial"), ("tamanho", "10"), ("largura", "100%")] + list(cores.items()) +
                           [("id_indicador[]", str(i)) for i in a["cepea"]])
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex">
    <title>Cotação CEPEA · {escape(a["nome"])}</title>
    <style>html,body{{margin:0;background:transparent;font-family:Arial,Helvetica,sans-serif}}.imagenet-widget-tabela{{width:100%!important}}</style>
</head>
<body data-atividade="{escape(a["id"])}">
    <!-- Widget oficial do CEPEA/Esalq: cotacoes exibidas como o CEPEA as publica (licenca dos dados CC BY-NC 4.0). -->
    <script src="{escape(cfg["cepea"]["widget"])}?{escape(params)}"></script>
    <script src="../assets/js/cotacao-cepea.js"></script>
</body>
</html>
"""
        (destino / f"{a['id']}.html").write_text(html, encoding="utf-8", newline="\n")
    print("OK cotacoes/*.html")


def secao_agro(cfg: dict) -> str:
    """Seção de mercado do agro: um card por atividade com a cotação (widget do CEPEA) e as notícias
    (site/dados/agro/noticias.json, de tools/gerar_noticias_agro.py), preenchidas por assets/js/agro-cards.js.
    A marca Orgatec Audi Agro (selo, nome e cores) só aparece com marca.exibir = true em agro_fontes.json; desligada,
    a seção usa as cores do site."""
    from html import escape
    marca = cfg.get("marca", {})
    exibir_marca = bool(marca.get("exibir"))
    selo = (f'<span class="audi-agro-selo"><img src="{{p}}{marca["logo"]}" alt="{escape(marca["nome"])}" width="480" height="293"></span>'
            if exibir_marca else "")
    chamada = escape(marca["nome"]) if exibir_marca else "Mercado"
    cards = []
    for a in cfg["atividades"]:
        nome = escape(a["nome"])
        if a["cepea"]:
            cotacao = (f'<iframe class="audi-agro-widget" title="Cotação CEPEA/Esalq: {nome}" data-src="{{p}}cotacoes/{a["id"]}.html" '
                       f'sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox" height="96" data-agro-widget="{a["id"]}"></iframe>'
                       '<p class="audi-agro-aviso" data-agro-aviso hidden></p>'
                       '<p class="audi-agro-fonte">Fonte: CEPEA/Esalq, pelo widget oficial. Valor e data na tabela, atualizados pelo CEPEA nos dias úteis.</p>')
        else:
            cotacao = f'<p class="audi-agro-sem">{escape(a["semWidget"])}</p>'
        cards.append(f"""                    <article class="og-cartao audi-agro-card" data-agro-atividade="{a["id"]}" aria-labelledby="agro-{a["id"]}">
                        <div class="audi-agro-card-topo"><h3 id="agro-{a["id"]}">{nome}</h3><a class="og-link text-sm" href="{escape(a["referencia"])}" target="_blank" rel="noopener">Indicador no CEPEA</a></div>
                        <div class="audi-agro-cotacao">{cotacao}</div>
                        <div class="audi-agro-noticias"><p class="eyebrow">Notícias e legislação</p><ul data-agro-noticias><li class="og-cartao-texto">Carregando…</li></ul></div>
                        <p class="audi-agro-atualizado" data-agro-atualizado></p>
                    </article>""")
    # Fontes das notícias, agrupadas pelos termos que valem para elas (tools/agro_fontes.json): o nome leva ao portal e
    # "termos" leva à página onde a regra de reprodução foi lida
    grupos: dict[str, dict] = {}
    for x in cfg["feeds"]:
        grupos.setdefault(x["termos"], x)
    fontes = ", ".join(
        f'<a class="og-link" href="{escape(f["portal"])}" target="_blank" rel="noopener">{escape(cfg["termos"][k]["rotulo"])}</a> '
        f'(<a class="og-link" href="{escape(cfg["termos"][k]["url"])}" target="_blank" rel="noopener">termos</a>)' for k, f in grupos.items())
    conferido = max(t["conferidoEm"] for k, t in cfg["termos"].items() if not k.startswith("_"))
    conferido_br = "/".join(reversed(conferido.split("-")))
    oficiais = " · ".join(f'<a class="og-link" href="{escape(a["url"])}" target="_blank" rel="noopener">{escape(a["nome"])}</a>' for a in cfg["acompanhe"])
    return f"""        <section class="audi-agro{"" if exibir_marca else " audi-agro-neutro"} py-12" aria-labelledby="agroTitulo" data-agro>
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid gap-6">
                <div class="audi-agro-topo">
                    {selo}
                    <div>
                        <p class="eyebrow">{chamada}</p>
                        <h2 id="agroTitulo" class="text-3xl font-bold text-tinta mt-2">Mercado e notícias por atividade</h2>
                        <p class="text-tinta-suave mt-2 max-w-3xl">Cotações do CEPEA/Esalq pelo widget oficial e notícias e legislação das agências da Câmara e do Senado e da Receita Federal, coletadas três vezes por dia.</p>
                    </div>
                </div>
                <div class="og-cartao audi-agro-tributacao" aria-labelledby="agroTributacao">
                    <p class="eyebrow" id="agroTributacao">{escape(cfg["tributacao"]["nome"])}: LCDPR, Funrural, ITR, reforma e crédito rural</p>
                    <ul data-agro-tributacao><li class="og-cartao-texto">Carregando…</li></ul>
                </div>
                <div class="audi-agro-grade">
{chr(10).join(cards)}
                </div>
                <p class="text-xs text-tinta-fraca" data-agro-situacao></p>
                <p class="text-xs text-tinta-fraca">Cotações: CEPEA/Esalq (licença de uso dos dados CC BY-NC 4.0), exibidas pelo widget oficial, sem cópia pelo site; quando o CEPEA está fora do ar, o card avisa. Notícias: só título, data e link, de {fontes}, com os termos de reprodução conferidos em {conferido_br}; o histórico guarda 180 dias e o card mostra os últimos 90. A B3 não entra: a difusão das cotações dela exige contrato.</p>
                <p class="text-xs text-tinta-fraca" data-agro-oficiais>Para ver mais, acompanhe direto nas fontes oficiais: {oficiais}. O site não coleta nem copia essas páginas.</p>
            </div>
        </section>"""


def janela_de_campo() -> None:
    """Janela de Campo: boletim agrometeorológico para o produtor rural (retenção do público agro).
    Dados em assets/js/boletins-campo.js; tela em assets/js/campo.js. Boletim vencido continua como arquivo, marcado.
    Os cards por atividade (Orgatec Audi Agro) moraram aqui; agora estão em agro_mercado()."""
    import json
    from html import escape
    atividades = json.loads(AGRO.read_text(encoding="utf-8"))["atividades"]
    opcoes_atividades = "".join(f'<option value="{a["id"]}">{escape(a["nome"])}</option>' for a in atividades)
    corpo = "\n".join([
        intro("Setor · Agro", "Janela de Campo",
              "Boletim automático três vezes ao dia, por região e operação.", compacto=True),
        subnav_setores("campo"),
        """        <section class="py-5 sm:py-12">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid gap-4 sm:gap-8" data-campo data-campo-divisas="{p}assets/img/divisas-ufs.svg">
                <p class="og-cartao-texto">Carregando o boletim. Se nada aparecer, ative o JavaScript ou consulte os avisos do INMET em <a class="og-link" href="https://alertas2.inmet.gov.br" target="_blank" rel="noopener">alertas2.inmet.gov.br</a>.</p>
            </div>
            <p class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-10 text-xs text-tinta-fraca font-mono">Boletim informativo gerado automaticamente a partir das fontes listadas (previsão: MET Norway, CC BY 4.0; satélite: NASA/NOAA). Não substitui os avisos oficiais do <a class="og-link" href="https://alertas2.inmet.gov.br" target="_blank" rel="noopener">INMET</a> e da Defesa Civil do seu município, nem a bula dos produtos.</p>
        </section>""",
        secao("Mercado", "Minha atividade", f"""                <p class="text-tinta-suave max-w-3xl mb-6">Escolha a sua atividade: o indicador do CEPEA, as notícias e a legislação dela estão na página de cotações e notícias.</p>
                <div class="og-campo max-w-xs mb-6"><label class="og-campo-rotulo" for="minhaAtividade">Minha atividade</label><select id="minhaAtividade" class="og-campo-controle og-campo-md" data-minha-atividade><option value="">Todas as atividades</option>{opcoes_atividades}</select></div>
                <a href="agro-mercado.html" class="og-btn og-btn-primario og-btn-lg" data-agro-mercado>Ver cotações e notícias</a>""", "bg-superficie"),
        faixa_cta("O clima também mexe no caixa", "Safra frustrada, colheita atrasada e perda de insumos mudam a receita e a despesa do ano, e com elas o planejamento tributário do produtor. Converse com a equipe."),
    ])
    pagina("setores/janela-de-campo.html", "Janela de Campo: boletim para o produtor rural",
           "Boletim agrometeorológico para o produtor rural: janela do dia por região e operação (pulverização, plantio, colheita, animais e máquinas), com as fontes.",
           "setores", "retenção", corpo, extra=["boletins-campo.js", "campo-mapa.js", "campo.js"], trilha=[("Setores", None), ("Janela de Campo", None)])


def agro_mercado() -> None:
    """Cotações e notícias por atividade: cards de secao_agro, preenchidos por assets/js/agro-cards.js.
    Tinham sido incluídos na Janela de Campo; a página própria deixa o boletim leve e dá ao produtor um endereço para o mercado."""
    import json
    cfg_agro = json.loads(AGRO.read_text(encoding="utf-8"))
    widgets_cepea(cfg_agro)
    corpo = "\n".join([
        intro("Setor · Agro · Mercado", "Cotações e notícias do agro por atividade",
              "Para cada atividade, o indicador do CEPEA, as notícias e a legislação do setor, com a fonte e a data de cada item."),
        subnav_setores("mercado"),
        secao_agro(cfg_agro),
        faixa_cta("O preço mexe no imposto", "Variação de preço, mudança de regime e crédito presumido do comprador alteram o resultado do produtor. Converse com a equipe."),
    ])
    pagina("setores/agro-mercado.html", "Cotações e notícias do agro por atividade",
           "Cotações do CEPEA/Esalq e notícias e legislação por atividade do agro (soja, milho, boi, leite e outras), com a fonte e a data de cada item.",
           "setores", "retenção", corpo, extra=["agro-cards.js"], trilha=[("Setores", None), ("Cotações e notícias", None)])


def regional() -> None:
    """Alertas regionais GO, TO e PA por setor (antes na página inicial; ligados por app.js: tabsUf, tabsSetor, listaRegional)."""
    corpo = "\n".join([
        intro("Eixo GO-TO-PA", "Alertas regionais por setor",
              "Pontos de atenção para agronegócio, comércio atacadista e indústria em Goiás, no Tocantins e no Pará. Para as demais UFs, use o simulador."),
        subnav_setores("regional"),
        """        <section id="regional" class="py-12">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex flex-wrap gap-2 mb-3" role="tablist" aria-label="UF" id="tabsUf"></div>
                <div class="flex flex-wrap gap-2 mb-6" role="tablist" aria-label="Setor" id="tabsSetor"></div>
                <ul id="listaRegional" class="grid grid-cols-1 md:grid-cols-2 gap-4"></ul>
            </div>
        </section>""",
        faixa_cta("O alerta vale para a sua operação?", "No diagnóstico, cruzamos os alertas do estado com as suas notas, os seus fornecedores e os benefícios que você usa hoje."),
    ])
    pagina("setores/regional.html", "Alertas regionais da reforma em GO, TO e PA", "Alertas da reforma tributária por setor (agro, atacado, indústria) em Goiás, Tocantins e Pará, com a fonte legal de cada ponto.",
           "setores", "autoridade", corpo, extra=["app.js"], trilha=[("Setores", None), ("Alertas regionais", None)])


def ferramentas() -> None:
    anos = "".join(f'<option value="{a}"{" selected" if a == 2027 else ""}>{a}</option>' for a in range(2026, 2034))
    corpo = "\n".join([
        intro("Ferramentas", "Simuladores e calculadoras da reforma", "",
              grade([C_SIMULADOR, C_CALENDARIO, C_TRANSICAO, C_PRODUTOR,
                     cartao("Compliance · 16 perguntas", "Termômetro de conformidade", "Conformidade tributária, lavagem de dinheiro, LGPD e integridade, com a fonte de cada pergunta.", "{p}compliance/termometro.html")],
                    "md:grid-cols-2 lg:grid-cols-3")),
        secao("Calculadora", "O que vale em cada ano da transição", f"""                <form id="formTransicao" class="og-cartao grid grid-cols-1 gap-4 max-w-2xl" novalidate>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div class="og-campo"><label class="og-campo-rotulo" for="tAno">Ano</label><select id="tAno" class="og-campo-controle og-campo-lg">{anos}</select></div>
                        <div class="og-campo"><label class="og-campo-rotulo" for="tIcms">ICMS + ISS pagos hoje por ano (R$, opcional)</label><input id="tIcms" type="text" inputmode="decimal" placeholder="ex.: 1.200.000" class="og-campo-controle og-campo-lg"></div>
                    </div>
                    <button type="submit" class="og-btn og-btn-primario og-btn-lg">Calcular</button>
                    <div id="tResultado" hidden aria-live="polite"></div>
                </form>""", id_="transicao"),
        secao("Calculadora", "Produtor rural: contribuinte ou não de IBS e CBS?", """                <form id="formProdutor" class="og-cartao grid grid-cols-1 gap-4 max-w-2xl" novalidate>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div class="og-campo"><label class="og-campo-rotulo" for="pReceita">Receita do ano-calendário (R$)</label><input id="pReceita" type="text" inputmode="decimal" placeholder="ex.: 3.200.000" class="og-campo-controle og-campo-lg"><p class="og-campo-ajuda">Some a receita das empresas agropecuárias em que tem participação.</p></div>
                        <div class="og-campo"><label class="og-campo-rotulo" for="pMeses">Meses de atividade no ano</label><input id="pMeses" type="number" min="1" max="12" value="12" class="og-campo-controle og-campo-lg"><p class="og-campo-ajuda">Menos de 12 só no ano de início da atividade.</p></div>
                        <div class="og-campo"><label class="og-campo-rotulo" for="pMesExcesso">Mês em que passou do limite (se passou)</label><input id="pMesExcesso" type="number" min="1" max="12" placeholder="1 a 12" class="og-campo-controle og-campo-lg"></div>
                    </div>
                    <label class="og-consentimento"><input id="pIntegrado" type="checkbox"><span>Sou produtor integrado (contrato de integração vertical com agroindústria)</span></label>
                    <label class="og-consentimento"><input id="pOptou" type="checkbox"><span>Já pedi inscrição no regime regular de IBS e CBS</span></label>
                    <button type="submit" class="og-btn og-btn-primario og-btn-lg">Verificar</button>
                    <div id="pResultado" hidden aria-live="polite"></div>
                </form>""", "bg-superficie", "produtor"),
        faixa_cta("Os números da sua empresa", "As calculadoras usam só a regra legal. O diagnóstico leva em conta preços, fornecedores e contratos."),
    ])
    pagina("ferramentas/index.html", "Simuladores e calculadoras da reforma", "Simulador tributário, calendário fiscal, calculadora da transição 2026–2033 e verificação do produtor rural contribuinte de IBS e CBS.",
           "ferramentas", "captação", corpo, trilha=[("Ferramentas", None)])


def campo(id_: str, rotulo: str, controle: str, ajuda: str = "") -> str:
    texto_ajuda = f'<p class="og-campo-ajuda">{ajuda}</p>' if ajuda else ""
    return f'<div class="og-campo"><label class="og-campo-rotulo" for="{id_}">{rotulo}</label>{controle}{texto_ajuda}</div>'


CTRL = "og-campo-controle og-campo-lg"
HONEYPOT = '<div class="hp" aria-hidden="true"><label>Website<input name="website" tabindex="-1" autocomplete="off"></label></div>'
REGIMES = '<option value="simples">Simples Nacional</option><option value="presumido">Lucro Presumido</option><option value="real">Lucro Real</option>'
ESFERAS = ('<label><input type="checkbox" name="{n}" value="federal" checked> Federal</label>'
           '<label><input type="checkbox" name="{n}" value="trabalhista" checked> Trabalhista</label>'
           '<label><input type="checkbox" name="{n}" value="estadual" checked> Estadual</label>')


def simulador() -> None:
    """Simulador e captação do lead (antes na página inicial; mesmos IDs, ligados por app.js)."""
    form = "\n".join([
        '                <form id="taxSimulatorForm" class="og-cartao grid grid-cols-1 gap-6" novalidate>',
        '                    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">',
        "                        " + campo("simSector", "1. Setor de atuação principal", f'<select id="simSector" class="{CTRL}"></select>'),
        "                        " + campo("simRegime", "2. Regime tributário atual", f'<select id="simRegime" class="{CTRL}">{REGIMES}</select>'),
        "                        " + campo("simClient", "3. Perfil predominante de clientes", f'<select id="simClient" class="{CTRL}"><option value="b2b">Mais de 50% Empresas (B2B)</option><option value="b2c">Mais de 50% Consumidor Final (B2C)</option></select>'),
        "                        " + campo("simUf", "4. UF principal de operação", f'<select id="simUf" class="{CTRL}"></select>'),
        "                        " + campo("simFaturamento", "5. Faturamento anual (R$)", f'<input id="simFaturamento" type="text" inputmode="decimal" placeholder="ex.: 2.400.000" class="{CTRL}">', "Receita bruta dos últimos 12 meses."),
        "                        " + campo("simCompras", "6. Compras com direito a crédito (% do faturamento)", f'<input id="simCompras" type="number" min="0" max="100" step="1" class="{CTRL}">',
                                          "Mercadorias, insumos e serviços de fornecedores do regime regular. Preenchido com uma premissa do setor; ajuste se souber o seu."),
        "                    </div>",
        '                    <p id="simErro" class="og-campo-erro" role="alert" hidden></p>',
        '                    <div><button id="btnSimular" type="submit" class="og-btn og-btn-primario og-btn-lg w-full sm:w-auto">Gerar Diagnóstico Tributário Imediato</button></div>',
        "                </form>",
    ])
    resultado = f"""                <div id="simResult" class="hidden mt-8 grid grid-cols-1 gap-6" aria-live="polite">
                    <div class="og-cartao">
                        <h2 class="og-cartao-titulo text-xl">Relatório preliminar de impacto fiscal</h2>
                        <p id="resultText" class="og-cartao-texto mb-4"></p>
                        <div id="resultEstimativa" class="mb-4"></div>
                        <ul id="resultAlertas" class="space-y-3 mb-4"></ul>
                        <p class="text-xs text-tinta-fraca font-mono">⚠️ Aviso Legal: Simulação orientativa baseada na EC nº 132/2023 e LC nº 214/2025. Não substitui parecer técnico emitido pelo contador responsável.</p>
                    </div>
                    <form id="leadForm" class="og-cartao grid grid-cols-1 gap-4" novalidate>
                        <h2 class="og-cartao-titulo">Receba a análise completa do seu CNPJ</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {campo("leadNome", "Nome", f'<input id="leadNome" name="nome" autocomplete="name" class="{CTRL}">')}
                            {campo("leadEmpresa", "Empresa (opcional)", f'<input id="leadEmpresa" name="empresa" autocomplete="organization" class="{CTRL}">')}
                            {campo("leadWhats", "WhatsApp", f'<input id="leadWhats" name="whatsapp" type="tel" autocomplete="tel" placeholder="(62) 9 0000-0000" class="{CTRL}">')}
                            {campo("leadEmail", "E-mail", f'<input id="leadEmail" name="email" type="email" autocomplete="email" class="{CTRL}">')}
                        </div>
                        {HONEYPOT}
                        <label class="og-consentimento"><input id="leadConsent" type="checkbox"><span>Autorizo a ORGATEC a usar estes dados e o resultado da simulação para entrar em contato sobre o diagnóstico tributário, conforme a <a href="{{p}}privacidade.html">Política de Privacidade</a> (LGPD, Lei nº 13.709/2018). Posso revogar a qualquer momento.</span></label>
                        <p id="leadMsg" class="text-sm" role="status"></p>
                        <div class="flex flex-col sm:flex-row gap-3">
                            <button type="submit" class="og-btn og-btn-primario og-btn-lg">Enviar para análise</button>
                            <a id="ctaWhatsSim" href="https://wa.me/5562992949161" target="_blank" rel="noopener" class="og-btn og-btn-contato og-btn-lg">Solicitar Análise Detalhada com os Especialistas</a>
                        </div>
                    </form>
                </div>"""
    corpo = "\n".join([
        intro("Ferramentas · 27 UFs", "Simulador de Impacto da Reforma Tributária",
              "Simule em segundos os reflexos da transição do IBS, da CBS e do Split Payment no seu modelo de negócio, em qualquer uma das 27 UFs."),
        f"""        <section id="simulador" class="py-12">
            <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
{form}
{resultado}
            </div>
        </section>""",
        secao("Outras ferramentas", "Continue a análise", grade([C_CALENDARIO, C_TRANSICAO, C_PRODUTOR], "md:grid-cols-3"), "bg-superficie"),
    ])
    pagina("ferramentas/simulador.html", "Simulador de impacto da reforma tributária", "Simulador da reforma tributária para as 27 UFs: setor, regime, perfil de clientes e faturamento, com alertas e a fonte legal de cada ponto.",
           "ferramentas", "captação", corpo, extra=["validadores.js", "app.js"], trilha=[("Ferramentas", "ferramentas/index.html"), ("Simulador", None)])


def calendario() -> None:
    """Calendário fiscal multiestado, .ics e opt-in de alertas (antes na página inicial; mesmos IDs, ligados por app.js)."""
    pequeno = "og-campo-controle og-campo-md"
    corpo = "\n".join([
        intro("Calendário Fiscal Multiestado", "Vencimentos federais, trabalhistas e estaduais",
              "Escolha o mês, a UF e o regime. As datas já consideram fins de semana e feriados nacionais; feriados estaduais e municipais não estão incluídos."),
        f"""        <section id="calendario" class="py-12">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 og-cartao min-w-0">
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                        {campo("calMes", "Mês", f'<input id="calMes" type="month" class="{pequeno}">')}
                        {campo("calUf", "UF", f'<select id="calUf" class="{pequeno}"></select>')}
                        {campo("calRegime", "Regime", f'<select id="calRegime" class="{pequeno}">{REGIMES}</select>')}
                        <fieldset class="sm:col-span-2 md:col-span-1"><legend class="og-campo-rotulo">Esferas</legend><div class="flex flex-wrap gap-x-3 text-sm">{ESFERAS.format(n="calEsfera")}<label><input type="checkbox" name="calEsfera" value="compliance" checked> Compliance</label></div></fieldset>
                    </div>
                    <ul id="calLista" class="divide-y divide-linha text-sm"></ul>
                    <div class="mt-4 flex flex-wrap gap-3 items-center">
                        <button id="btnIcs" type="button" class="og-btn og-btn-contorno og-btn-md">Baixar mês (.ics)</button>
                        <span id="calGuia" class="text-xs text-tinta-fraca"></span>
                    </div>
                </div>
                <form id="optinForm" class="og-cartao grid grid-cols-1 gap-4 content-start min-w-0" novalidate>
                    <h2 class="og-cartao-titulo text-lg">Receba os alertas de vencimento</h2>
                    <p class="og-cartao-texto">Avisos mensais das obrigações das UFs escolhidas. Você confirma a inscrição pelo link que enviaremos e pode cancelar quando quiser.</p>
                    {campo("optEmail", "E-mail", f'<input id="optEmail" type="email" autocomplete="email" class="{pequeno}">')}
                    {campo("optWhats", "WhatsApp", f'<input id="optWhats" type="tel" autocomplete="tel" placeholder="(62) 9 0000-0000" class="{pequeno}">')}
                    {campo("optUfs", "UFs (segure Ctrl/⌘ para várias)", f'<select id="optUfs" multiple size="4" class="{pequeno}"></select>')}
                    <fieldset><legend class="og-campo-rotulo">Esferas</legend><div class="flex flex-wrap gap-x-3 text-sm">{ESFERAS.format(n="optEsfera")}</div></fieldset>
                    {HONEYPOT}
                    <label class="og-consentimento"><input id="optConsent" type="checkbox"><span>Aceito receber os alertas do Calendário Fiscal, conforme a <a href="{{p}}privacidade.html">Política de Privacidade</a>.</span></label>
                    <p id="optMsg" class="text-sm" role="status"></p>
                    <button type="submit" class="og-btn og-btn-contato og-btn-lg w-full">Quero receber</button>
                </form>
            </div>
        </section>""",
        secao("Outras ferramentas", "Continue a análise", grade([C_SIMULADOR, C_TRANSICAO, C_PRODUTOR], "md:grid-cols-3"), "bg-superficie"),
    ])
    pagina("ferramentas/calendario.html", "Calendário fiscal multiestado", "Vencimentos federais, trabalhistas e estaduais do mês por UF e regime, com download para a agenda (.ics) e alertas por e-mail.",
           "ferramentas", "retenção", corpo, extra=["calendario.js", "validadores.js", "app.js"],
           trilha=[("Ferramentas", "ferramentas/index.html"), ("Calendário fiscal", None)])


def cliente() -> None:
    tabela = lambda id_, colunas: f"""                    <div class="overflow-x-auto">
                        <table class="w-full text-sm min-w-[760px]">
                            <thead class="text-xs uppercase text-tinta-fraca border-b border-linha text-left"><tr>{"".join(f'<th class="py-2 pr-3">{c}</th>' for c in colunas)}</tr></thead>
                            <tbody id="{id_}" class="divide-y divide-linha"></tbody>
                        </table>
                    </div>"""
    demos = f"""                <p class="text-tinta-suave max-w-3xl mb-6">Demonstração com os modelos de homologação do Plano Diretor (dados fictícios).</p>
                <div class="og-cartao mb-6 min-w-0">
                    <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
                        <h3 class="og-cartao-titulo">1. Captura de NF-e, NFS-e e CT-e (multiestado)</h3>
                        <span id="xmlFerramenta" class="text-xs px-2 py-1 rounded-full"></span>
                    </div>
                    <p class="og-cartao-texto mb-4">Varredura diária, com certificado digital A1/A3, dos documentos emitidos contra o CNPJ do cliente em qualquer SEFAZ. Cada documento passa por validação estrutural antes de entrar na apuração.</p>
{tabela("xmlTabela", ["ID", "Emitente", "UF", "Tipo", "Valor", "Emissão", "Status captura", "Validação"])}
                </div>
                <div class="og-cartao min-w-0">
                    <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
                        <h3 class="og-cartao-titulo">2. Portal do cliente — atendimento com SLA e trilha de auditoria</h3>
                        <span id="portalErp" class="text-xs px-2 py-1 rounded-full"></span>
                    </div>
                    <p class="og-cartao-texto mb-4">Guias, balancetes e solicitações no <a href="{layout.PORTAL_URL}" data-link="portal" target="_blank" rel="noopener" class="og-link">portal do cliente (Athenas Online)</a>. O exemplo abaixo usa dados fictícios, com IPs mascarados (LGPD).</p>
{tabela("portalTabela", ["Protocolo", "UF", "Departamento", "Solicitação", "Competência", "Status", "SLA", "Auditoria"])}
                    <p class="mt-6"><a href="{{p}}contato/index.html" class="og-link">Problemas de acesso? Fale conosco →</a></p>
                </div>"""
    portal = f"""                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
                    <div>
                        <p class="text-tinta-suave mb-6">O acesso é feito no portal do sistema contábil do escritório, com login individual. Este site não guarda documentos nem dados de clientes.</p>
                        <div class="flex flex-wrap gap-3 items-center">
                            <a href="{layout.PORTAL_URL}" data-link="portal" target="_blank" rel="noopener" class="og-btn og-btn-primario og-btn-lg">Entrar no portal</a>
                            <span data-portal-erp class="og-selo og-selo-pendente">ERP do portal: pendente de definição</span>
                        </div>
                    </div>
                    <div class="og-cartao">
                        <h2 class="og-cartao-titulo">No portal você encontra</h2>
                        <ul class="list-disc pl-5 text-sm text-tinta-suave space-y-1">
                            <li>Guias de impostos e de folha do mês</li>
                            <li>Documentos e relatórios contábeis</li>
                            <li>Protocolo de envio e recebimento de documentos</li>
                        </ul>
                        <p class="text-xs text-tinta-fraca mt-3">As funções exatas dependem do sistema escolhido para o portal.</p>
                    </div>
                </div>"""
    acessos = grade([
        '<div class="og-cartao"><span class="og-cartao-ref">Exclusivo</span><h3 class="og-cartao-titulo">Módulo LOCAR</h3>'
        '<p class="og-cartao-texto mb-3">Espaço do Grupo LOCAR, com agenda, obrigações e reforma por empresa.</p><p class="flex flex-wrap items-center gap-3">'
        '<a href="{p}cliente/locar.html" class="og-btn og-btn-primario og-btn-md">Abrir módulo</a><span class="og-selo og-selo-pendente">em implantação</span></p></div>',
        f'<div class="og-cartao"><span class="og-cartao-ref">Sistema próprio</span><h3 class="og-cartao-titulo">Conciliação bancária</h3>'
        f'<p class="og-cartao-texto mb-3">Extratos conferidos com a contabilidade e laudo das divergências.</p><p class="flex flex-wrap items-center gap-3">{acesso("conciliacao", "og-btn og-btn-primario og-btn-md")}'
        f'<a href="{{p}}solucoes/conciliacao.html" class="og-link text-sm">Saiba mais</a></p></div>',
        f'<div class="og-cartao"><span class="og-cartao-ref">Para empresas</span><h3 class="og-cartao-titulo">Gestão financeira</h3>'
        f'<p class="og-cartao-texto mb-3">Lançamentos, extratos, notas e projeção de CBS e IBS por empresa. O acompanhamento de crédito entra aqui quando a operação começar; ainda não há oferta de crédito.</p><p class="flex flex-wrap items-center gap-3">{acesso("gestaoFinanceira", "og-btn og-btn-primario og-btn-md")}'
        f'<a href="{{p}}solucoes/index.html" class="og-link text-sm">Saiba mais</a></p></div>',
    ], "md:grid-cols-2 lg:grid-cols-3")
    corpo = "\n".join([
        intro("Área do cliente", "Documentos, guias e relatórios no portal", "", portal),
        secao("Acessos", "Outros sistemas da ORGATEC", acessos + '\n                <p class="text-sm text-tinta-suave mt-4">Cada sistema tem endereço e login próprios. O botão “Entrar” aparece quando o acesso estiver liberado para clientes.</p>', id_="acessos"),
        secao("Em 2026", "O que acompanhar agora", itens(destino="cliente")),
        secao("Calendário", "Vencimentos e alertas", grade([C_CALENDARIO,
              cartao("Central da Reforma", "Últimas atualizações", "Atos, regulamentos e prazos novos, com a fonte oficial.", "{p}reforma/index.html#noticias")], "md:grid-cols-2"), "bg-superficie"),
        secao("Soluções", "Captura automática de documentos e portal do cliente", demos, id_="servicos"),
        secao("Suporte", "Precisa de ajuda?", f'                <a {WHATS} data-msg="Olá! Sou cliente da ORGATEC e preciso de ajuda com o portal." class="og-btn og-btn-contato og-btn-lg">Falar com o atendimento</a>', "bg-superficie"),
    ])
    pagina("cliente/index.html", "Área do cliente", "Acesso ao portal do cliente ORGATEC (documentos, guias e relatórios), calendário fiscal, atualizações da reforma e captura automática de documentos.",
           None, "retenção", corpo, extra=["validadores.js", "demo-dados.js", "app.js"], trilha=[("Área do cliente", None)])


def escritorio() -> None:
    corpo = "\n".join([
        intro("O escritório", "Experiência no agro e no transporte aplicada à reforma tributária", "",
              """                <p class="text-xl font-bold text-tinta mb-4" data-prova-anos hidden></p>
                <p class="text-tinta-suave leading-relaxed max-w-3xl">A ORGATEC atende há anos empresas do agronegócio e do transporte, inclusive no lucro real, e produtores rurais com LCDPR. Esse conhecimento das operações de cada cliente é a base da consultoria para a reforma tributária.</p>"""),
        secao("Responsabilidade técnica", "Quem assina", """                <div class="og-cartao max-w-xl">
                    <h3 class="og-cartao-titulo">Robson Alain Veloso</h3>
                    <p class="font-mono text-link">CRC-TO 002032/O-5 T-GO</p>
                    <p class="og-cartao-texto mt-2">Contador responsável técnico. Toda orientação publicada passa por revisão técnica antes de ir ao ar.</p>
                </div>"""),
        secao("Serviços", "Contabilidade que sustenta a decisão tributária", """                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="og-cartao"><h3 class="og-cartao-titulo">Contábil</h3><p class="og-cartao-texto">Escrituração e demonstrações que dão base às apurações e aos créditos.</p></div>
                    <div class="og-cartao"><h3 class="og-cartao-titulo">Fiscal</h3><p class="og-cartao-texto">Apuração, obrigações acessórias e documentos fiscais com IBS e CBS.</p></div>
                    <div class="og-cartao"><h3 class="og-cartao-titulo">Pessoal</h3><p class="og-cartao-texto">Folha, eSocial e obrigações trabalhistas.</p></div>
                </div>
                <p class="mt-6"><a href="{p}tributario/index.html" class="og-link">Conheça a consultoria tributária →</a></p>
                <p class="mt-2"><a href="{p}compliance/index.html" class="og-link">Conheça a área de compliance: conformidade tributária, lavagem de dinheiro, LGPD e integridade →</a></p>""", "bg-superficie"),
        secao("Conformidade", "Como a ORGATEC cumpre as próprias obrigações", """                <div class="grid grid-cols-1 md:grid-cols-3 gap-4" data-obrigacoes-proprias>
                    <div class="og-cartao"><span class="og-cartao-ref">Res. CFC nº 1.721/2024</span><h3 class="og-cartao-titulo">Prevenção à lavagem de dinheiro</h3>
                        <p class="og-cartao-texto">Como organização contábil, o escritório segue a resolução nos serviços que ela alcança: cadastro dos contratantes, comunicação ao COAF das operações previstas e, sem ocorrência no ano, declaração de não ocorrência ao CFC até 31 de janeiro. Por isso, em algumas operações, pedimos documentos de identificação e de origem dos recursos.</p>
                        <p class="mt-3"><a href="{p}compliance/prevencao-lavagem.html#item-pld-profissionais-contabilidade" class="og-link text-sm">Ver a regra →</a></p></div>
                    <div class="og-cartao"><span class="og-cartao-ref">Lei nº 13.709/2018</span><h3 class="og-cartao-titulo">Proteção de dados</h3>
                        <p class="og-cartao-texto">O escritório trata dados pessoais de clientes, dos empregados deles (folha e eSocial) e de fornecedores conforme a LGPD. Como esses dados são usados e protegidos está na <a href="{p}privacidade.html" class="og-link">Política de Privacidade</a>.</p>
                        <p class="og-cartao-texto mt-3" data-dpo>Encarregado de dados (DPO): canal em ativação. Enquanto isso, use o <a href="{p}contato/index.html?assunto=lgpd" class="og-link">formulário de contato</a> com o assunto "Meus dados pessoais (LGPD)".</p></div>
                    <div class="og-cartao"><span class="og-cartao-ref">NBC PG 01</span><h3 class="og-cartao-titulo">Ética profissional</h3>
                        <p class="og-cartao-texto">Atuação conforme o Código de Ética Profissional do Contador. O escritório faz o diagnóstico e organiza documentos e rotinas; não emite parecer jurídico.</p></div>
                </div>"""),
    ])
    pagina("escritorio/index.html", "O escritório", "ORGATEC: contabilidade consultiva com experiência no agro e no transporte, responsável técnico com CRC e foco em reforma tributária.",
           "escritorio", "autoridade", corpo, trilha=[("O escritório", None)])


def contato() -> None:
    """Agendamento pelo WhatsApp e formulário de contato (antes na página inicial; mesmos IDs, ligados por app.js)."""
    form = f"""                <form id="contatoForm" class="og-cartao grid grid-cols-1 gap-4 min-w-0" novalidate>
                    <h2 class="og-cartao-titulo">Prefere escrever?</h2>
                    {campo("ctNome", "Nome", f'<input id="ctNome" autocomplete="name" class="{CTRL}">')}
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {campo("ctWhats", "WhatsApp", f'<input id="ctWhats" type="tel" autocomplete="tel" class="{CTRL}">')}
                        {campo("ctEmail", "E-mail", f'<input id="ctEmail" type="email" autocomplete="email" class="{CTRL}">')}
                    </div>
                    {campo("ctAssunto", "Assunto", f'<select id="ctAssunto" class="{CTRL}"><option value="diagnostico">Diagnóstico tributário</option><option value="portal">Acesso ao portal</option><option value="lgpd">Meus dados pessoais (LGPD)</option><option value="outro">Outro</option></select>')}
                    {campo("ctMensagem", "Mensagem", f'<textarea id="ctMensagem" rows="4" class="{CTRL}"></textarea>')}
                    {HONEYPOT}
                    <label class="og-consentimento"><input id="ctConsent" type="checkbox"><span>Autorizo o uso destes dados para responder a esta mensagem, conforme a <a href="{{p}}privacidade.html">Política de Privacidade</a>.</span></label>
                    <p id="ctMsg" class="text-sm" role="status"></p>
                    <button type="submit" class="og-btn og-btn-primario og-btn-lg w-full sm:w-auto">Enviar mensagem</button>
                </form>"""
    corpo = "\n".join([
        f"""        <section id="contato" class="py-10 sm:py-14 bg-superficie border-b border-linha" data-hero>
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
                <div>
                    <p class="eyebrow">Contato</p>
                    <h1 class="text-3xl sm:text-4xl font-extrabold text-tinta tracking-tight mt-2 mb-4">Agende o diagnóstico tributário</h1>
                    <p class="text-tinta-suave mb-6">O agendamento é feito pelo WhatsApp oficial. A mensagem já vai pronta, sem nenhum dado seu na conversa até você escrever. O formulário serve para diagnóstico, acesso ao portal ou pedidos sobre os seus dados pessoais.</p>
                    <a {WHATS} data-msg="{MSG_DIAGNOSTICO}" class="og-btn og-btn-contato og-btn-lg">Agendar pelo WhatsApp</a>
                    <p class="text-sm text-tinta-suave mt-4">WhatsApp / telefone: <span data-texto="whatsapp" class="font-mono">+55 (62) 99294-9161</span></p>
                    <p class="mt-2 text-sm text-tinta-suave" id="contatoEmailLinha"></p>
                    <p class="text-xs text-tinta-fraca mt-4">Sede: Av. Ministro Alfredo Nasser, nº 727, Centro, Formoso-GO</p>
                </div>
{form}
            </div>
        </section>""",
    ])
    pagina("contato/index.html", "Contato e agendamento", "Agende o diagnóstico tributário com a ORGATEC pelo WhatsApp ou pelo formulário de contato.",
           None, "captação", corpo, extra=["validadores.js", "app.js"], trilha=[("Contato", None)])


# ---------- Soluções (sistemas da ORGATEC) — docs/plano-incorporacao-produtos.md, Fase 1
# Só páginas no site. O acesso ao sistema é um link para o subdomínio dele, criado por paginas.js quando
# config.solucoes.<id>.situacao = 'disponivel' (e com url https). Nada de embed, bundle ou chamada à API do sistema.
# Os textos descrevem só o que existe e foi conferido nos repositórios; nenhum dado de cliente.

def modulo_locar() -> None:
    """Módulo exclusivo do Grupo LOCAR. Em implantação: página sem dados do grupo e fora do mapa do site.
    O portal com login será uma aplicação separada; aqui só entram textos gerais (docs/ideias/modulo-locar.md)."""
    item = lambda ref, titulo, texto: f'<div class="og-cartao"><span class="og-cartao-ref">{ref}</span><h3 class="og-cartao-titulo">{titulo}</h3><p class="og-cartao-texto">{texto}</p></div>'
    acoes = f"""                <div class="flex flex-wrap gap-3 items-center mt-6">
                    <a href="{layout.PORTAL_URL}" data-link="portal" target="_blank" rel="noopener" class="og-btn og-btn-primario og-btn-lg">Entrar no portal</a>
                    <a {WHATS} data-msg="Olá! Sou do Grupo LOCAR e preciso de atendimento." class="og-btn og-btn-contato og-btn-lg">Falar com o atendimento</a>
                    <span class="og-selo og-selo-pendente">em implantação</span>
                </div>"""
    conteudo = grade([
        item("Prazos", "Agenda da transição", "Prazos da reforma e das obrigações, por empresa, com responsável e evidência."),
        item("Empresas", "Obrigações por empresa", "Situação de cada entrega fiscal, contábil e trabalhista do grupo."),
        item("Transporte", "Operação de transporte", "CT-e e MDF-e, frete, créditos de IBS e CBS e transportadores."),
        item("Agro", "Operação rural", "Fazendas, produtores rurais, livro caixa, LCDPR, Funrural e rebanho."),
        item("Documentos", "Guias e relatórios", "Continuam no portal do cliente; o módulo aponta para eles."),
        item("Compliance", "Evidências de conformidade", "Pacote datado para compartilhar, com autorização do grupo."),
    ], "md:grid-cols-2 lg:grid-cols-3")
    acesso_txt = """                <div class="max-w-3xl space-y-3 text-tinta-suave">
                    <p>O acesso será individual, com permissão por empresa e por pessoa. Os dados de cada produtor rural pessoa física ficarão separados dos dados das empresas.</p>
                    <p>Até a liberação, nenhum dado do grupo fica nesta página. Documentos e guias seguem no portal do cliente.</p>
                </div>"""
    corpo = "\n".join([
        intro("Área do cliente · Exclusivo", "Módulo LOCAR", "Espaço exclusivo do Grupo LOCAR na ORGATEC, em implantação.", acoes),
        secao("O que o módulo vai reunir", "Do prazo à evidência, por empresa", conteudo),
        secao("Acesso", "Dados separados por empresa e por pessoa", acesso_txt, "bg-superficie"),
    ])
    pagina("cliente/locar.html", "Módulo LOCAR", "Espaço exclusivo do Grupo LOCAR na ORGATEC, em implantação.", None, "retenção", corpo,
           indexar=False, trilha=[("Área do cliente", "cliente/index.html"), ("Módulo LOCAR", None)])


def acesso(id_: str, classe: str = "og-btn og-btn-contorno og-btn-lg") -> str:
    """Selo de situação + lugar do botão "Entrar" (preenchidos por paginas.js a partir de config.solucoes)."""
    return (f'<span class="inline-flex flex-wrap items-center gap-3" data-solucao="{id_}">'
            f'<span class="og-selo og-selo-pendente" data-solucao-selo>situação em config.js</span>'
            f'<span data-solucao-entrar data-classe="{classe}" hidden></span></span>')


def lista(itens: list[tuple[str, str]], colunas: str = "md:grid-cols-2 lg:grid-cols-4") -> str:
    """Grade de cartões sem link: (título, texto)."""
    return grade([f'<div class="og-cartao"><h3 class="og-cartao-titulo">{t}</h3><p class="og-cartao-texto">{x}</p></div>' for t, x in itens], colunas)


def marcos(passos: list[tuple[str, str]]) -> str:
    li = "\n".join(f'                    <li class="marco"><span class="bola" aria-hidden="true">{i}</span><h3>{t}</h3><p>{x}</p></li>'
                   for i, (t, x) in enumerate(passos, 1))
    return f'                <ol class="marcos" data-marcos>\n{li}\n                </ol>'


def faixa_solucao(titulo: str, texto: str, msg: str, botao: str = "Solicitar demonstração") -> str:
    return f"""        <section class="py-16 bg-superficie border-t border-linha">
            <div class="max-w-3xl mx-auto px-4 sm:px-6 text-center">
                <h2 class="text-2xl font-bold text-tinta mb-3">{titulo}</h2>
                <p class="text-tinta-suave mb-6">{texto}</p>
                <div class="flex flex-col sm:flex-row gap-3 justify-center"><a {WHATS} data-msg="{msg}" class="og-btn og-btn-contato og-btn-lg">{botao}</a></div>
                <p class="text-xs text-tinta-fraca mt-6">Este site não recebe extratos, notas nem documentos: o envio acontece só dentro do sistema, com login, ou diretamente com a equipe.</p>
            </div>
        </section>"""


SEGURANCA_COMUM = ("Este site não recebe seus dados", "Extratos, notas e documentos são enviados só dentro do sistema, com login, ou diretamente à equipe. O site só leva você até lá.")


def solucoes_vitrine() -> None:
    cartoes = [
        f'<div class="og-cartao"><span class="og-cartao-ref">Sistema próprio · extratos e contabilidade</span>'
        f'<h3 class="og-cartao-titulo"><a href="{{p}}solucoes/conciliacao.html" class="hover:text-acao">Conciliação bancária</a></h3><p class="og-cartao-texto">Extratos conferidos com a contabilidade, divergências por severidade e laudo do que ficou pendente.</p>'
        f'<p class="mt-3 flex flex-wrap items-center gap-3">{acesso("conciliacao", "og-btn og-btn-contorno og-btn-md")}<a href="{{p}}solucoes/conciliacao.html" class="og-link text-sm">Conhecer a solução →</a></p></div>',
        f'<div class="og-cartao"><span class="og-cartao-ref">Serviço do escritório · SEFAZ-GO</span>'
        f'<h3 class="og-cartao-titulo"><a href="{{p}}solucoes/auditoria-rural.html" class="hover:text-acao">Auditoria forense rural (NFA-e)</a></h3><p class="og-cartao-texto">As notas avulsas do produtor rural conferidas uma a uma, com score de risco, Funrural, IRPF rural e laudo.</p>'
        f'<p class="mt-3 flex flex-wrap items-center gap-3">{acesso("auditoriaRural", "og-btn og-btn-contorno og-btn-md")}<a href="{{p}}solucoes/auditoria-rural.html" class="og-link text-sm">Conhecer o serviço →</a></p></div>',
        f'<div class="og-cartao"><span class="og-cartao-ref">Para empresas · em preparação</span>'
        f'<h3 class="og-cartao-titulo">Gestão financeira para empresas</h3><p class="og-cartao-texto">Lançamentos, importação de extratos e notas e projeção de CBS e IBS num painel por empresa. O acompanhamento de crédito entra neste módulo quando a operação começar; ainda não há oferta de crédito.</p>'
        f'<p class="mt-3 flex flex-wrap items-center gap-3">{acesso("gestaoFinanceira")}'
        f'<a {WHATS} data-msg="Olá! Quero ser avisado quando a gestão financeira da ORGATEC estiver disponível." class="og-link text-sm">Quero ser avisado</a></p></div>',
    ]
    corpo = "\n".join([
        intro("Soluções", "Sistemas da ORGATEC a serviço da sua contabilidade",
              "Além da consultoria, o escritório usa sistemas próprios para conferir extratos, auditar notas fiscais e acompanhar a reforma. Aqui está o que cada um faz e como pedir acesso."),
        secao("Soluções", "O que o escritório oferece", grade(cartoes, "md:grid-cols-3")),
        secao("Como funciona o acesso", "Cada sistema tem endereço e login próprios", lista([
            SEGURANCA_COMUM,
            ("Login separado por sistema", "Quando um sistema estiver disponível para você, o botão “Entrar” aparece aqui e na Área do cliente."),
            ("Demonstração com a equipe", "Antes de qualquer acesso, a equipe mostra o sistema com dados fictícios e combina o que será enviado."),
        ], "md:grid-cols-3"), "bg-superficie"),
        faixa_solucao("Qual solução faz sentido para a sua empresa?", "Em uma conversa, a equipe indica o sistema ou o serviço adequado ao seu caso.",
                      "Olá! Quero saber qual solução da ORGATEC faz sentido para a minha empresa.", "Falar com a equipe"),
    ])
    pagina("solucoes/index.html", "Soluções do escritório", "Sistemas próprios da ORGATEC: conciliação bancária, auditoria forense rural de NFA-e e gestão financeira para empresas.",
           "solucoes", "captação", corpo, trilha=[("Soluções", None)])


SITUACAO_CONTROLE = {"no sistema": "og-selo-definido", "em parte": "og-selo-futuro", "a definir": "og-selo-pendente"}


def controles(itens: list[tuple[str, str, str]], nota: str) -> str:
    """Bloco de confiança: (controle, o que ele faz e o limite dele, situação). Situação em SITUACAO_CONTROLE.
    Só entra o que foi conferido no código do sistema; a evidência fica em docs/conciliacao-confianca-evidencias.md."""
    cartoes = [f'<div class="og-cartao" data-controle><span class="og-selo {SITUACAO_CONTROLE[s]} mb-3">{s}</span>'
               f'<h3 class="og-cartao-titulo">{t}</h3><p class="og-cartao-texto">{x}</p></div>' for t, x, s in itens]
    return grade(cartoes, "md:grid-cols-2 lg:grid-cols-3") + f'\n                <p class="text-sm text-tinta-fraca mt-6 max-w-3xl" data-controles-nota>{nota}</p>'


# Conferido no código do OrgConc (branch main) em 07/11/2026. Antes de mudar uma frase, confira a evidência no doc.
CONFIANCA_CONCILIACAO = controles([
    ("Um escritório não vê o outro",
     "Nas tabelas de clientes, conciliações e lançamentos, a separação por escritório é uma regra do próprio banco de dados, "
     "não só da tela. Os arquivos de cada conciliação ainda não estão sob essa regra: o sistema os separa por usuário.", "em parte"),
    ("Trilha de auditoria encadeada",
     "Cada ação registrada leva o código (hash) da ação anterior e uma assinatura. O registro não aceita alteração nem exclusão, "
     "e o sistema confere a cadeia inteira de uma vez.", "no sistema"),
    ("Inteligência artificial desligada",
     "Vem desligada e só é ligada se o escritório decidir. Antes de qualquer envio, CPF, CNPJ e e-mail são mascarados. "
     "Nomes digitados no histórico do banco, como num PIX, ainda não são; por isso ela fica desligada.", "no sistema"),
    ("Segundo fator de login",
     "Aplicativo autenticador disponível para todos e exigido nas funções de administração do escritório. "
     "A chave de acesso (passkey) existe no sistema, mas depende de um domínio próprio, ainda não configurado.", "em parte"),
    ("Arquivos cifrados",
     "Os arquivos das conciliações e os segredos do segundo fator ficam cifrados no armazenamento. Senhas são guardadas só como hash.", "no sistema"),
    ("Hospedagem, guarda e exclusão",
     "A região de hospedagem, o prazo de guarda dos dados e a exclusão completa a pedido do cliente serão publicados aqui "
     "antes da abertura do sistema. Hoje o cadastro do cliente pode ser anonimizado a pedido.", "a definir"),
], "O sistema não tem certificação ISO 27001 nem SOC 2, e esta página não afirma que tenha. Uma revisão de segurança "
   "está em andamento antes da abertura do acesso; até lá, o uso é por demonstração com a equipe. "
   "Este site não recebe extratos, notas nem documentos.")


def solucao_conciliacao() -> None:
    msg = "Olá! Quero conhecer a conciliação bancária da ORGATEC."
    corpo = "\n".join([
        hero("Soluções · Sistema próprio", 'Conciliação bancária com <mark class="marca-texto">trilha</mark> de cada divergência.',
             "Extratos em OFX, PDF ou CSV conferidos com a contabilidade da empresa: o que bate, o que falta e o que precisa de explicação, com laudo das divergências por severidade.",
             f'<a {WHATS} data-msg="{msg}" class="og-btn og-btn-contato og-btn-lg">Solicitar demonstração</a>{acesso("conciliacao")}'),
        secao("Para quem", "Quando a conciliação deixa de caber na planilha", lista([
            ("Várias contas e bancos", "Muitos lançamentos por mês, pagamentos recorrentes e mais de uma instituição."),
            ("Lucro real", "Conciliação mensal que sustenta a apuração e a revisão dos créditos."),
            ("Transporte", "Volume alto de pagamentos de frete, combustível, pedágio e manutenção."),
            ("Antes de uma fiscalização", "Revisão de um período fechado para encontrar e explicar divergências antes de alguém perguntar."),
        ])),
        secao("Como funciona", "Do extrato ao laudo", marcos([
            ("Envio", "Extratos (OFX, PDF ou CSV) e razão contábil do período, dentro do sistema."),
            ("Conferência", "Cada lançamento do banco é cruzado com a contabilidade; as diferenças ganham severidade."),
            ("Revisão", "A equipe confere os apontamentos e registra a explicação de cada divergência."),
            ("Laudo", "Relatório em tela, planilha e PDF com o que foi conciliado e o que ficou pendente."),
        ]), "bg-superficie", "como-funciona"),
        secao("O que entrega", "Recursos do sistema", lista([
            ("Leitura de extratos", "OFX, PDF, XML e CSV de diferentes bancos, sem redigitação."),
            ("Divergências por severidade", "Lançamentos sem par, valores diferentes e padrões fora do comum separados por gravidade."),
            ("Contrapartes", "Consulta do CNPJ de quem paga e de quem recebe em base pública."),
            ("Reforma tributária", "Projeção de CBS e IBS sobre as operações para acompanhar a transição de 2026 a 2033."),
        ])),
        secao("Segurança e LGPD", "O que o sistema faz hoje, e o que ainda não faz", CONFIANCA_CONCILIACAO, "bg-superficie", "confianca"),
        faixa_solucao("Veja a conciliação com dados fictícios", "Na demonstração, a equipe mostra o sistema com um período de exemplo e explica o que seria enviado no seu caso.", msg),
    ])
    pagina("solucoes/conciliacao.html", "Conciliação bancária", "Conciliação bancária da ORGATEC: extratos OFX, PDF e CSV conferidos com a contabilidade, divergências por severidade e laudo.",
           "solucoes", "captação", corpo, extra=["inicio.js"], trilha=[("Soluções", "solucoes/index.html"), ("Conciliação bancária", None)])


LAUDO_EXEMPLO = """                <figure class="og-cartao max-w-3xl" data-laudo-exemplo>
                    <div class="flex flex-wrap items-start justify-between gap-3 border-b border-linha pb-4 mb-4">
                        <div>
                            <p class="eyebrow">Laudo de auditoria · NFA-e</p>
                            <p class="og-cartao-titulo">Produtor Exemplo (dados fictícios)</p>
                            <p class="text-sm text-tinta-suave font-mono">CPF ***.***.***-** · período: jan. a dez. (fictício)</p>
                        </div>
                        <span class="og-selo og-selo-pendente">EXEMPLO · DADOS FICTÍCIOS</span>
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-[auto_minmax(0,1fr)] gap-6 items-center">
                        <div class="text-center">
                            <p class="text-5xl font-extrabold text-tinta font-display">64</p>
                            <p class="text-xs text-tinta-suave">score de risco (0 a 100)</p>
                            <span class="og-selo og-selo-futuro mt-2">atenção</span>
                        </div>
                        <ul class="grid gap-3 text-sm">
                            <li class="flex gap-3 items-start"><span class="og-selo og-selo-pendente">alto</span><span>Notas de valor logo abaixo de uma faixa de atenção emitidas em dias próximos para o mesmo destinatário (possível fracionamento).</span></li>
                            <li class="flex gap-3 items-start"><span class="og-selo og-selo-futuro">médio</span><span>Produto vendido sem correspondência com a atividade cadastrada.</span></li>
                            <li class="flex gap-3 items-start"><span class="og-selo og-selo-definido">baixo</span><span>Diferença entre o total das notas do ano e a receita registrada no livro-caixa (LCDPR).</span></li>
                        </ul>
                    </div>
                    <figcaption class="text-xs text-tinta-fraca mt-5">Ilustração do formato do laudo. Produtor, valores e achados são fictícios; o laudo real é entregue só ao cliente, com a apuração e as recomendações do escritório.</figcaption>
                </figure>"""


def solucao_auditoria_rural() -> None:
    msg = "Olá! Quero saber sobre a auditoria das NFA-e do produtor rural com a ORGATEC."
    corpo = "\n".join([
        hero("Soluções · Serviço do escritório", 'Auditoria forense das <mark class="marca-texto">NFA-e</mark> do produtor rural.',
             "Para o produtor rural em Goiás: as notas fiscais avulsas emitidas pela SEFAZ-GO conferidas uma a uma, com score de risco, apuração do Funrural e do IRPF rural e laudo técnico do escritório.",
             f'<a {WHATS} data-msg="{msg}" class="og-btn og-btn-contato og-btn-lg">Falar com o escritório</a>{acesso("auditoriaRural")}'),
        secao("Para quem", "Quem mais se beneficia", lista([
            ("Produtor pessoa física", "Quem declara a atividade rural no IRPF e mantém o livro-caixa (LCDPR)."),
            ("Produtor pessoa jurídica", "Empresas rurais que emitem notas avulsas pela SEFAZ-GO."),
            ("Antes de uma fiscalização", "Revisão preventiva de um ano inteiro de notas, para encontrar e explicar inconsistências."),
        ], "md:grid-cols-3")),
        secao("Como funciona", "Das notas ao laudo", marcos([
            ("Coleta", "Relatório das NFA-e do período, obtido na SEFAZ-GO."),
            ("Leitura", "Cada nota é lida e classificada automaticamente por operação, produto e destinatário."),
            ("Análise de risco", "Score de 0 a 100 e tipologias de risco documentadas, como o fracionamento de notas."),
            ("Laudo", "PDF com os achados por severidade, a apuração do Funrural e do IRPF rural e as recomendações."),
        ]), "bg-superficie", "como-funciona"),
        secao("Exemplo", "Como o laudo apresenta os achados", LAUDO_EXEMPLO, id_="exemplo"),
        secao("Privacidade", "Dados fiscais do produtor tratados com cuidado", lista([
            ("Identidade protegida na análise", "Antes de qualquer etapa com inteligência artificial, CPF, CNPJ e nomes são substituídos por códigos."),
            ("Sistema interno do escritório", "A auditoria roda num sistema de uso interno da equipe; o produtor recebe o laudo, sem acesso ao sistema."),
            SEGURANCA_COMUM,
        ], "md:grid-cols-3"), "bg-superficie"),
        secao("Relacionado", "Agro na reforma tributária", grade([C_AGRO,
              cartao("LCDPR", "LCDPR e IBS/CBS do produtor pessoa física", "O livro-caixa do produtor na transição da reforma.", "{p}reforma/index.html#item-lcdpr"),
              C_PRODUTOR], "md:grid-cols-3")),
        faixa_solucao("Quer revisar as notas do seu ano?", "Em uma conversa, o escritório explica o que é preciso enviar e o prazo do laudo.", msg, "Falar com o escritório"),
    ])
    pagina("solucoes/auditoria-rural.html", "Auditoria forense rural de NFA-e", "Auditoria das NFA-e do produtor rural (SEFAZ-GO) pela ORGATEC: score de risco, apuração do Funrural e do IRPF rural e laudo técnico.",
           "solucoes", "captação + autoridade", corpo, extra=["inicio.js"], trilha=[("Soluções", "solucoes/index.html"), ("Auditoria forense rural", None)])


def abertura() -> None:
    """Tela de abertura, na raiz do site (index.html), no modelo do trilhum.io: texto direto no fundo, à esquerda, e a
    projeção holográfica à direita (canvas: projetor, feixe e os logotipos da ORGATEC em camadas, em rodízio, terminando
    em "By Warley Veloso"; máscaras de tools/gerar_holo_logos.py). Sem caixa de vidro nem cards de marcos (02/11/2026).
    Sem menu nem rodapé do layout comum, de propósito: o holograma se forma, o texto surge em cascata e o botão
    "Entrar no site" leva à vitrine (inicio.html); os atalhos levam direto às áreas. A sequência roda uma vez por aba
    (abertura-intro.js marca a primeira visita antes da pintura) e some com movimento reduzido.
    Destinos em config.abertura; anos de atuação só com comprovação (config.institucional)."""
    seta = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
{layout.head("Reforma tributária com base legal", "Consultoria tributária para lucro real, transporte e produtor rural, com a fonte oficial em cada orientação sobre a reforma (EC 132/2023, LC 214/2025).", "", "index.html", extra=JSONLD)}
    <link rel="stylesheet" href="assets/css/abertura.css">
    <script src="assets/js/abertura-intro.js"></script>
</head>
<body class="abertura folha-escura">
    <canvas class="holo-canvas" data-holo aria-hidden="true"></canvas>
    <div class="holo-grade" aria-hidden="true"></div>
    <main class="abertura-palco" data-objetivo="captação: tela de abertura">
        <section class="abertura-texto" data-abertura-texto aria-labelledby="abTitulo">
            <div class="holo-marca">
                <img src="assets/marca/orgatec-original.png" alt="Símbolo da ORGATEC" width="46" height="51">
                <div><span class="holo-marca-nome">ORGATEC</span><span class="holo-sub">Contabilidade Consultiva e Inteligência Tributária</span></div>
            </div>
            <p class="holo-eyebrow">Reforma tributária · EC 132/2023 · LC 214/2025</p>
            <h1 id="abTitulo">Reforma tributária com <span class="holo-destaque">base legal</span> em cada decisão.</h1>
            <p class="holo-lead">Consultoria tributária para empresas do lucro real, transportadoras e produtores rurais com LCDPR. Cada orientação cita o dispositivo oficial e a data em que foi conferido.</p>
            <ul class="holo-publicos" aria-label="Para quem">
                <li>Lucro real</li><li>Transporte</li><li>Agro e LCDPR</li>
            </ul>
            <p class="holo-trajetoria" data-prova-anos hidden></p>
            <a class="holo-entrar" href="{layout.INICIO}" data-destino="entrada" data-entrar>Entrar no site {seta}</a>
            <p class="holo-rt">Responsável técnico: <b>Robson Alain Veloso</b> · <span class="font-mono">CRC-TO 002032/O-5 T-GO</span></p>
            <nav class="holo-atalhos" aria-label="Atalhos">
                <a href="tributario/index.html" data-destino="tributario">Área tributária</a>
                <a href="cliente/index.html" data-destino="areaCliente">Área do cliente</a>
                <a href="cliente/locar.html" data-destino="locar">Módulo LOCAR</a>
                <a href="ferramentas/index.html" data-destino="simuladores">Simuladores</a>
                <a href="solucoes/index.html" data-destino="solucoes">Soluções</a>
                <a href="reforma/index.html#noticias" data-destino="noticias">Central da Reforma</a>
                <a href="https://wa.me/5562992949161" data-link="whatsapp" data-msg="{MSG_DIAGNOSTICO}" target="_blank" rel="noopener">WhatsApp</a>
            </nav>
        </section>
        <div class="holo-ancora" data-holo-ancora aria-hidden="true">
            <span class="holo-legenda holo-legenda-topo">ORGATEC · Projeção</span>
            <span class="holo-legenda holo-legenda-base" data-holo-legenda>ORGATEC</span>
        </div>
    </main>
    <a class="holo-entrar holo-entrar-fixo" href="{layout.INICIO}" data-destino="entrada" data-entrar data-entrar-fixo tabindex="-1" aria-hidden="true">Entrar no site {seta}</a>
    <footer class="abertura-rodape">
        <p>© 2026 ORGATEC · CNPJ 13.155.211/0001-45 · <a href="privacidade.html">Política de Privacidade</a><span data-homologacao hidden> · Ambiente de homologação: <a href="testes/index.html">painel de testes</a></span></p>
        <button type="button" class="holo-movimento" data-movimento aria-pressed="false">Reduzir animação</button>
    </footer>
    <script src="assets/js/config.js"></script>
    <script src="assets/js/conteudo.js"></script>
    <script src="assets/js/holo-logos.js"></script>
    <script src="assets/js/abertura.js"></script>
</body>
</html>
"""
    (SITE / "index.html").write_text(html, encoding="utf-8", newline="\n")
    print("OK index.html (tela de abertura)")


MAPA = [  # (página, objetivo) — conferido pelo painel de testes
    ("index.html", "captação: tela de abertura"), ("inicio.html", "captação"), ("tributario/index.html", "captação + autoridade"), ("reforma/index.html", "autoridade + retenção"),
    ("setores/agro.html", "captação + autoridade"), ("setores/transporte.html", "captação + autoridade"), ("setores/regional.html", "autoridade"), ("setores/janela-de-campo.html", "retenção"),
    ("setores/agro-mercado.html", "retenção"),
    ("ferramentas/index.html", "captação"), ("ferramentas/simulador.html", "captação"), ("ferramentas/calendario.html", "retenção"),
    ("solucoes/index.html", "captação"), ("solucoes/conciliacao.html", "captação"), ("solucoes/auditoria-rural.html", "captação + autoridade"),
    ("compliance/index.html", "captação + autoridade"), ("compliance/termometro.html", "captação"), ("compliance/conformidade-tributaria.html", "captação + autoridade"),
    ("compliance/prevencao-lavagem.html", "autoridade"), ("compliance/protecao-de-dados.html", "autoridade"), ("compliance/integridade.html", "autoridade"),
    ("compliance/publicos.html", "captação"), ("compliance/publico/transportador.html", "captação + autoridade"),
    ("compliance/publico/produtor-rural.html", "captação + autoridade"), ("compliance/publico/mei.html", "captação + autoridade"),
    ("compliance/publico/autonomo.html", "captação + autoridade"), ("compliance/publico/simples.html", "captação + autoridade"),
    ("compliance/publico/comercio-industria.html", "captação + autoridade"), ("compliance/publico/servicos.html", "captação + autoridade"),
    ("compliance/publico/imoveis.html", "captação + autoridade"),
    ("cliente/index.html", "retenção"), ("cliente/locar.html", "retenção"), ("escritorio/index.html", "autoridade"),
    ("contato/index.html", "captação"), ("reforma/fontes.html", "autoridade"), ("privacidade.html", "conformidade (LGPD)"),
    ("marca.html", "interno: marca"), ("orgatec-template2.html", "interno: design system atual"),
    ("orgatec-trilha.html", "interno: design ORGATEC Trilha (demonstração)"),
]


def testes() -> None:
    mapa = "\n".join(f'                        <tr class="border-b border-linha"><td class="py-2 pr-4"><a class="og-link" href="{{p}}{c}">{c}</a></td><td class="py-2">{o}</td></tr>' for c, o in MAPA)
    corpo = "\n".join([
        """        <section class="py-14 bg-superficie border-b border-linha">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <p class="eyebrow">Fase de testes</p>
                <h1 class="text-3xl sm:text-4xl font-extrabold text-tinta tracking-tight mt-2 mb-4">Painel de testes e pendências</h1>
                <p class="text-tinta-suave max-w-3xl mb-6">Página interna da homologação (não aparece no Google nem no menu). Mostra o que precisa ser resolvido na próxima fase e roda um autoteste dos simuladores, do conteúdo e da configuração. O status das pendências automáticas muda sozinho quando a configuração ou os dados mudam.</p>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4" data-resumo-testes>
                    <div class="og-cartao"><span class="og-cartao-ref">Ambiente</span><p class="text-2xl font-bold text-tinta mt-1" data-resumo="ambiente">—</p></div>
                    <div class="og-cartao"><span class="og-cartao-ref">Pendências abertas</span><p class="text-2xl font-bold text-tinta mt-1 font-mono" data-resumo="abertas">—</p></div>
                    <div class="og-cartao"><span class="og-cartao-ref">Bloqueiam a produção</span><p class="text-2xl font-bold text-tinta mt-1 font-mono" data-resumo="bloqueios">—</p></div>
                    <div class="og-cartao"><span class="og-cartao-ref">Autoteste</span><p class="text-2xl font-bold text-tinta mt-1 font-mono" data-resumo="autoteste">—</p></div>
                </div>
            </div>
        </section>""",
        secao("Autoteste", "Os módulos respondem como esperado?", """                <ul class="grid grid-cols-1 md:grid-cols-2 gap-3" data-autoteste></ul>
                <p class="text-xs text-tinta-fraca mt-4">Os mesmos casos rodam no Node (tests/js/homologacao.test.js). A suíte completa está em tests/ROTEIRO-QA.md.</p>"""),
        secao("Próxima fase", "Pendências a resolver", """                <div class="flex flex-wrap items-end gap-3 mb-6">
                    <div class="og-campo"><label class="og-campo-rotulo" for="pdStatus">Status</label><select id="pdStatus" class="og-campo-controle og-campo-md"><option value="aberta">Abertas</option><option value="">Todas</option><option value="resolvida">Resolvidas</option></select></div>
                    <div class="og-campo"><label class="og-campo-rotulo" for="pdResp">Responsável</label><select id="pdResp" class="og-campo-controle og-campo-md"><option value="">Todos</option><option value="orgatec">ORGATEC (direção)</option><option value="rt">Responsável técnico</option><option value="dev">Desenvolvimento</option></select></div>
                    <label class="og-consentimento pb-2"><input id="pdBloqueia" type="checkbox"><span>Só as que bloqueiam a produção</span></label>
                    <button type="button" id="btnCopiarPendencias" class="og-btn og-btn-contorno og-btn-md">Copiar lista (Markdown)</button>
                    <span class="text-sm text-tinta-fraca pb-2" id="pdContagem" aria-live="polite"></span>
                </div>
                <div data-pendencias class="grid gap-8"></div>
                <textarea id="pdTexto" class="sr-only" aria-hidden="true" tabindex="-1"></textarea>""", "bg-superficie", "pendencias"),
        secao("Mapa", "Páginas do site e objetivo de cada uma", f"""                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left min-w-[480px]">
                        <thead><tr class="text-xs uppercase text-tinta-fraca border-b border-linha"><th class="py-2 pr-4">Página</th><th class="py-2">Objetivo</th></tr></thead>
                        <tbody>
{mapa}
                        </tbody>
                    </table>
                </div>"""),
    ])
    pagina("testes/index.html", "Painel de testes", "Painel interno da fase de testes do site ORGATEC: pendências da próxima fase e autoteste.",
           None, "interno: homologação", corpo, indexar=False, extra=["calendario.js", "validadores.js", "compliance-itens.js", "homologacao.js"], barra=False)


def main() -> None:
    inicio()
    abertura()
    tributario()
    reforma()
    setor_agro()
    setor("transporte", "Transporte", "A reforma tributária no transporte de cargas e de passageiros.",
          "CT-e com IBS e CBS desde agosto de 2026, crédito do diesel, frete de autônomo com crédito presumido e caminhões fora do Imposto Seletivo.",
          "O transporte de cargas fica na regra geral de IBS e CBS, sem redução de alíquota, mas passa a creditar o que hoje é custo, como combustível, peças e manutenção. Os documentos fiscais do setor já exigem os novos campos, e o split payment muda o caixa de quem trabalha com margem curta.",
          "{p}ferramentas/simulador.html?setor=transporte")
    regional()
    janela_de_campo()
    agro_mercado()
    ferramentas()
    simulador()
    calendario()
    solucoes_vitrine()
    solucao_conciliacao()
    solucao_auditoria_rural()
    cliente()
    modulo_locar()
    escritorio()
    contato()
    import paginas_compliance  # área de Compliance, gerada à parte (docs/plano-area-compliance.md)
    paginas_compliance.gerar()
    import paginas_empresarial  # área Empresarial (Fase 3 de docs/ideias/reestruturacao-transporte.md)
    paginas_empresarial.gerar()
    testes()


if __name__ == "__main__":
    main()
