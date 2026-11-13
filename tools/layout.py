"""Cabeçalho, navegação e rodapé comuns às páginas geradas (gerar_paginas.py e gerar_hub.py).

As cores vêm do design system: assets/js/tema-tailwind.js (Tailwind) e assets/css/orgatec.css
(tokens + componentes og-*), ambos gerados por tools/gerar_design_system.py a partir de
design-system/orgatec-template2/tokens.json.
"""

from __future__ import annotations

from html import escape

# (chave, rótulo, caminho a partir da raiz do site, subitens). Ordem = prioridade do eixo tributário.
# Com subitens, o item vira grupo: <details> no desktop e lista com título no menu ☰.
# A raiz (index.html) é a tela de abertura; "Início" no logotipo, na trilha e no rodapé leva à vitrine do site.
# Login do portal do cliente (Athenas Online). Troque por https://portal.orgatec.io quando o CNAME
# e o certificado estiverem no ar (pendência T5); config.js → portal.url faz o mesmo no navegador.
PORTAL_URL = "https://orgatec.athenas.online/Usuarios/login"
INICIO = "inicio.html"
# Menu do Modelo C (docs/ideias/modelo-c.md): a ferramenta leva ao diagnóstico e o diagnóstico leva à proposta.
DIAGNOSTICO_URL = "diagnostico-reforma.html"
PROPOSTA_URL = "proposta/index.html"
SIMULAR = [("Simulador tributário", "ferramentas/simulador.html"), ("Calculadoras da transição", "ferramentas/index.html"),
           ("Calendário fiscal", "ferramentas/calendario.html")]
DIAGNOSTICO = [("Diagnóstico de Impacto da Reforma", DIAGNOSTICO_URL), ("Solicitar proposta", PROPOSTA_URL),
               ("Consultoria tributária", "consultoria-tributaria.html")]
REFORMA = [("Central da Reforma", "reforma/index.html"), ("LC nº 214/2025", "reforma/lc-214-2025.html"), ("IBS", "reforma/ibs.html"),
           ("CBS", "reforma/cbs.html"), ("Split payment", "reforma/split-payment.html"), ("Simples Nacional: IBS e CBS fora do DAS", "reforma/simples-hibrido.html"),
           ("Alertas regionais GO, TO e PA", "reforma/alertas-regionais.html"), ("Fontes legais", "reforma/fontes.html")]
# Setores reúne o agro e o que antes era o grupo Empresarial (transporte, lucro real e a visão geral das empresas).
SETORES = [("Agro e produtor rural", "rural/index.html"), ("Janela de Campo (tempo no agro)", "rural/janela-de-campo.html"),
           ("Cotações e notícias do agro", "rural/cotacoes.html"), ("Transporte", "empresarial/transporte.html"),
           ("Central de Viagem (clientes)", "transporte/central.html"), ("Lucro real e presumido", "empresarial/lucro-real.html"),
           ("Empresas: visão geral", "empresarial/index.html"), ("Janela da semana", "empresarial/janela.html")]
# Área de Compliance (docs/plano-area-compliance.md; páginas em tools/paginas_compliance.py): visão geral, termômetro, score e as quatro frentes.
COMPLIANCE = [("Visão geral", "compliance/index.html"), ("Termômetro de conformidade", "compliance/termometro.html"),
              ("Score da empresa", "empresarial/score.html"), ("Por público", "compliance/publicos.html"),
              ("Conformidade tributária", "compliance/conformidade-tributaria.html"), ("Prevenção à lavagem de dinheiro", "compliance/prevencao-lavagem.html"),
              ("Proteção de dados (LGPD)", "compliance/protecao-de-dados.html"), ("Integridade e anticorrupção", "compliance/integridade.html")]
# Sistemas da ORGATEC (docs/plano-incorporacao-produtos.md): só páginas no site; o acesso a cada sistema é link
# para o subdomínio dele, controlado por config.solucoes. Gestão financeira (Mini e crédito do OrgCred, Fases 3 e 4) ainda fora.
SOLUCOES = [("Todas as soluções", "solucoes/index.html"), ("Conciliação bancária", "solucoes/conciliacao.html"),
            ("Auditoria forense rural (NFA-e)", "solucoes/auditoria-rural.html")]
NAV = [
    ("ferramentas", "Simular", "ferramentas/simulador.html", SIMULAR),
    ("diagnostico", "Diagnóstico", DIAGNOSTICO_URL, DIAGNOSTICO),
    ("reforma", "Reforma", "reforma/index.html", REFORMA),
    ("setores", "Setores", "rural/index.html", SETORES),
    ("compliance", "Compliance", "compliance/index.html", COMPLIANCE),
    ("solucoes", "Serviços", "solucoes/index.html", SOLUCOES),
]
# Chaves que as páginas ainda passam em `ativo` e o grupo que as recebe no menu novo.
ATIVO_GRUPO = {"tributario": "diagnostico", "empresarial": "setores"}
# A Central de Viagem (noindex, área de clientes) segue no menu, agora em Setores, ao lado de Transporte.
# "Escritório" segue fora do menu principal (decisão C3 provisória): rodapé ("O escritório") e grupo Atendimento do menu ☰.


def grupo_ativo(ativo: str | None, atual: str = "") -> str | None:
    """Grupo do menu a destacar: o que contém a página atual; sem isso, a chave da página (com as antigas convertidas)."""
    for chave, _rotulo, caminho, subs in NAV:
        if atual and (atual == caminho or any(u == atual for _r, u in subs)):
            return chave
    return ATIVO_GRUPO.get(ativo, ativo)

# Fontes servidas pelo próprio site (pendência T4): gerar com python tools/baixar_fontes.py.
FONTES = '<link rel="stylesheet" href="{p}assets/fontes/fontes.css">'
ICONE_INICIO = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                'stroke-linejoin="round" aria-hidden="true"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h5v-6h4v6h5V9.5"/></svg>')
ICONE_CORES = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">'
               '<circle cx="12" cy="12" r="9"/><circle cx="8" cy="10" r="1"/><circle cx="12" cy="7" r="1"/><circle cx="16" cy="10" r="1"/></svg>')


def tema(p: str) -> str:
    """Design ORGATEC Trilha: fontes, CSS dos componentes, paleta (tema.js no <head>, antes da pintura) e Tailwind compilado."""
    return f"""    {FONTES.format(p=p)}
    <link rel="stylesheet" href="{p}assets/css/orgatec.css">
    <script src="{p}assets/js/tema.js"></script>
    <link rel="stylesheet" href="{p}assets/css/tailwind.css">"""


def botao_cores() -> str:
    # Abaixo de 375 px o botão sai do cabeçalho (o nome ORGATEC encostava nele) e fica no menu ☰ (item_cores)
    return f'<button id="btnCores" type="button" class="tema-btn hidden min-[375px]:inline-flex" aria-label="Escolher cores">{ICONE_CORES}<span class="hidden md:inline xl:hidden">Cores</span></button>'


ITEM_CORES = '<button type="button" class="py-2 text-left min-[375px]:hidden" data-abrir-cores>Cores</button>'


SCRIPTS = ["config.js", "fontes.js", "ufs.js", "regras.js", "conteudo.js", "reforma-itens.js", "calculadoras.js", "paginas.js"]


def head(titulo: str, descricao: str, p: str, canonical: str, tipo: str = "website", indexar: bool = True, extra: str = "",
         imagem: str | None = None) -> str:
    """Bloco <head>. p = prefixo relativo até a raiz do site ('' ou '../'). extra = marcação adicional (ex.: JSON-LD).
    imagem = og:image própria da página (caminho a partir da raiz, tools/gerar_imagens_compartilhar.py); sem ela, a geral."""
    canonical = "" if canonical == "index.html" else canonical
    og_imagem = '    <meta property="og:image" content="https://orgatec.io/assets/marca/og-image.png">'
    if imagem:
        og_imagem = (f'    <meta property="og:image" content="https://orgatec.io/{imagem}">\n'
                     '    <meta property="og:image:width" content="1200">\n    <meta property="og:image:height" content="630">\n'
                     f'    <meta property="og:image:alt" content="{escape(titulo)}">')
    return f"""    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(titulo)} | ORGATEC</title>
    <meta name="description" content="{escape(descricao)}">{"" if indexar else chr(10) + '    <meta name="robots" content="noindex">'}
    <link rel="canonical" href="https://orgatec.io/{canonical}">
    <meta property="og:title" content="{escape(titulo)}">
    <meta property="og:description" content="{escape(descricao)}">
    <meta property="og:type" content="{tipo}">
{og_imagem}
    <link rel="icon" href="{p}assets/marca/favicon-32.png" sizes="32x32" type="image/png">
    <link rel="apple-touch-icon" href="{p}assets/marca/apple-touch-icon.png">
    <meta name="theme-color" content="#072563">
{tema(p)}{extra}"""


def cabecalho(p: str, ativo: str | None, atual: str = "") -> str:
    """atual = caminho da página (marca o subitem com aria-current)."""
    ativo = grupo_ativo(ativo, atual)
    def sub(rotulo: str, caminho: str, cls: str) -> str:
        marca = ' aria-current="page"' if caminho == atual else ""
        return f'<a href="{p}{caminho}" class="{cls}"{marca}>{rotulo}</a>'

    def item(chave: str, rotulo: str, caminho: str, subs: list) -> str:
        destaque = " text-acao font-semibold" if chave == ativo else ""
        if subs:
            links = "".join(sub(r, u, "") for r, u in subs)
            return f'<details class="nav-grupo" data-nav-grupo><summary class="hover:text-acao transition{destaque}">{rotulo}</summary><div class="nav-sub">{links}</div></details>'
        marca = ' aria-current="page"' if chave == ativo else ""
        return f'<a href="{p}{caminho}" class="hover:text-acao transition{destaque}"{marca}>{rotulo}</a>'

    def item_movel(chave: str, rotulo: str, caminho: str, subs: list) -> str:
        if subs:
            return f'<p class="nav-titulo">{rotulo}</p>' + "".join(sub(r, u, "py-2 pl-3") for r, u in subs)
        marca = ' aria-current="page"' if chave == ativo else ""
        return f'<a href="{p}{caminho}" class="py-2{" text-acao font-semibold" if chave == ativo else ""}"{marca}>{rotulo}</a>'

    # "Início" (vitrine): ícone de casa no desktop, em qualquer largura, para o cabeçalho caber na caixa de 1280 px (max-w-7xl)
    # sem cobrir o logotipo nem sair pela direita; o texto fica só para leitor de tela e no title. No menu ☰ é o primeiro item, escrito.
    na_vitrine = atual == INICIO
    marca_ini = ' aria-current="page"' if na_vitrine else ""
    destaque_ini = " text-acao font-semibold" if na_vitrine else ""
    inicio = (f'<a href="{p}{INICIO}" class="hover:text-acao transition inline-flex items-center gap-1.5{destaque_ini}" title="Início"{marca_ini}>'
              f'{ICONE_INICIO}<span class="sr-only">Início</span></a>')
    inicio_movel = f'<a href="{p}{INICIO}" class="py-2{destaque_ini}"{marca_ini}>Início</a>'
    nav = "\n                ".join([inicio] + [item(*n) for n in NAV])
    nav_movel = "\n                ".join([inicio_movel] + [item_movel(*n) for n in NAV])
    return f"""    <div id="faixaHomologacao" hidden class="bg-aviso-fundo border-b border-aviso-borda text-aviso-texto text-xs">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2"><strong>Ambiente de homologação.</strong> Itens da reforma marcados "em revisão técnica" ainda não foram aprovados pelo responsável técnico e não aparecem em produção. <a href="{p}testes/index.html" class="underline font-semibold">Painel de testes e pendências →</a></div>
    </div>
    <header class="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-linha">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-3">
            <a href="{p}{INICIO}" class="flex items-center gap-3 shrink-0" aria-label="ORGATEC — início">
                <img src="{p}assets/marca/orgatec-original.png" alt="" width="40" height="44" class="h-9 w-8 sm:h-11 sm:w-10 shrink-0">
                <div class="min-w-0">
                    <span class="block text-lg sm:text-xl font-display font-extrabold tracking-tight text-tinta leading-none whitespace-nowrap">ORGATEC</span>
                    <span class="hidden sm:block text-[10px] text-descritor uppercase tracking-widest mt-1 whitespace-nowrap">Inteligência Tributária</span>
                </div>
            </a>
            <nav class="hidden xl:flex items-center gap-3 text-sm font-medium text-tinta-suave whitespace-nowrap" aria-label="Principal">
                {nav}
            </nav>
            <div class="flex items-center gap-2 sm:gap-3">
                <a href="{p}{DIAGNOSTICO_URL}" class="hidden xl:inline-flex og-btn og-btn-primario og-btn-md whitespace-nowrap" data-cta-diagnostico>Solicitar diagnóstico</a>
                <a href="{p}cliente/index.html" class="hidden sm:inline-flex items-center whitespace-nowrap text-sm font-medium text-tinta-texto hover:text-acao px-4 py-2 rounded-lg border border-linha-campo hover:border-acao transition">Área do cliente</a>
                {botao_cores()}
                <a href="https://wa.me/5562992949161" data-link="whatsapp" target="_blank" rel="noopener" class="og-btn og-btn-contato og-btn-md"><span class="sm:hidden xl:inline">WhatsApp</span><span class="hidden sm:inline xl:hidden">Falar no WhatsApp</span></a>
                <button id="btnMenu" type="button" class="xl:hidden p-2 rounded-lg border border-linha-campo text-tinta-texto" aria-controls="menuMobile" aria-expanded="false" aria-label="Abrir menu">☰</button>
            </div>
        </div>
        <nav id="menuMobile" hidden class="xl:hidden border-t border-linha bg-white" aria-label="Menu móvel">
            <div class="px-4 py-3 grid gap-1 text-sm font-medium text-tinta-texto">
                {nav_movel}
                <p class="nav-titulo">Atendimento</p>
                <a href="{p}{DIAGNOSTICO_URL}" class="py-2 pl-3 font-semibold text-acao">Solicitar diagnóstico</a>
                <a href="{p}quem-somos.html" class="py-2 pl-3">O escritório</a>
                <a href="{p}cliente/index.html" class="py-2 pl-3">Área do cliente</a>
                <a href="{p}contato/index.html" class="py-2 pl-3">Contato</a>
                {ITEM_CORES}
            </div>
        </nav>
    </header>"""


RODAPE_CONSULTORIA = [("Consultoria tributária", "consultoria-tributaria.html"), ("Diagnóstico da reforma", DIAGNOSTICO_URL), ("Simulador tributário", "ferramentas/simulador.html"),
                      ("Calendário fiscal", "ferramentas/calendario.html"), ("Agro e produtor rural", "rural/index.html"),
                      ("Transporte", "empresarial/transporte.html"), ("Soluções do escritório", "solucoes/index.html"),
                      ("O escritório", "quem-somos.html")]
RODAPE_REFORMA = [("Central da Reforma", "reforma/index.html"), ("LC nº 214/2025", "reforma/lc-214-2025.html"), ("IBS", "reforma/ibs.html"),
                  ("CBS", "reforma/cbs.html"), ("Split payment", "reforma/split-payment.html"), ("Fontes legais", "reforma/fontes.html")]


def rodape(p: str) -> str:
    def coluna(titulo: str, links: list) -> str:
        itens = "".join(f'<li><a href="{p}{u}" class="hover:text-brand hover:underline">{r}</a></li>' for r, u in links)
        return f'<nav aria-label="{titulo}"><span class="text-ink font-bold text-base block mb-2">{titulo}</span><ul class="grid gap-1.5">{itens}</ul></nav>'

    return f"""    <footer class="bg-surface2 text-muted py-12 border-t border-line">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 text-sm">
            <div>
                <span class="flex items-center gap-2 mb-3"><img src="{p}assets/marca/orgatec-original.png" alt="" width="26" height="29" class="h-7 w-auto"><span class="text-ink font-display font-extrabold text-lg tracking-tight">ORGATEC</span></span>
                <p class="mb-4">Contabilidade Consultiva e Inteligência Tributária. Atendimento digital em todo o Brasil com forte atuação no eixo GO, TO e PA.</p>
                <p class="text-xs text-muted">CNPJ: 13.155.211/0001-45</p>
                <p class="text-xs text-muted mt-2">Sede: Av. Ministro Alfredo Nasser, nº 727, Centro, Formoso-GO</p>
            </div>
            {coluna("Consultoria", RODAPE_CONSULTORIA)}
            {coluna("Reforma", RODAPE_REFORMA)}
            <div>
                <span class="text-ink font-bold text-base block mb-2">Responsabilidade Técnica</span>
                <p>Robson Alain Veloso</p>
                <p class="text-brand font-mono">CRC-TO 002032/O-5 T-GO</p>
                <span class="text-ink font-bold text-base block mt-4 mb-2">Canais Oficiais</span>
                <p>WhatsApp / Telefone: <span data-texto="whatsapp">+55 (62) 99294-9161</span></p>
                <p class="mt-2"><a href="{PORTAL_URL}" data-link="portal" target="_blank" rel="noopener" class="text-brand hover:underline">Portal do cliente</a></p>
                <p class="mt-2 text-xs" id="rodapeEmails" data-contato="{p}contato/index.html"></p>
            </div>
        </div>
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 pt-6 border-t border-line text-xs flex flex-wrap gap-x-4 gap-y-2 justify-between">
            <p><a href="{p}{INICIO}" class="hover:underline">Início</a> · <a href="{p}privacidade.html" class="hover:underline">Política de Privacidade (LGPD)</a> · <a href="{p}marca.html" class="hover:underline">Marca</a> · <a href="{p}contato/index.html" class="hover:underline">Contato</a></p>
            <p>© 2026 ORGATEC. Todos os direitos reservados. Em conformidade com a LGPD e o Código de Ética do CFC (NBC PG 01).</p>
        </div>
    </footer>"""


BASE_URL = "https://orgatec.io/"
# Primeiro passo da trilha sem endereço próprio: a migalha estruturada precisa de um destino (hoje, a primeira página do grupo).
MIGALHA_GRUPO = {"Setores": "rural/index.html", "Consultoria": "consultoria-tributaria.html", "Reforma": "reforma/index.html",
                 "Soluções": "solucoes/index.html", "Compliance": "compliance/index.html", "Empresarial": "empresarial/index.html", "Ferramentas": "ferramentas/index.html",
                 "Diagnóstico": DIAGNOSTICO_URL}


def breadcrumb(passos: list, caminho: str) -> str:
    """JSON-LD BreadcrumbList da trilha: Início e cada passo. A última migalha é a própria página."""
    import json
    lista = [{"@type": "ListItem", "position": 1, "name": "Início", "item": BASE_URL + INICIO}]
    for i, (rotulo, url) in enumerate(passos, start=2):
        ultimo = i == len(passos) + 1
        destino = url or (caminho if ultimo else MIGALHA_GRUPO.get(rotulo))
        item = {"@type": "ListItem", "position": i, "name": rotulo}
        if destino:
            item["item"] = BASE_URL + destino
        lista.append(item)
    dados = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": lista}
    return '\n    <script type="application/ld+json">' + json.dumps(dados, ensure_ascii=False) + "</script>"


def servico_jsonld(nome: str, descricao: str, caminho: str) -> str:
    """JSON-LD Service (consultoria e soluções) com o prestador ORGATEC."""
    import json
    dados = {"@context": "https://schema.org", "@type": "Service", "name": nome, "description": descricao, "areaServed": "BR",
             "url": BASE_URL + caminho, "provider": {"@type": "AccountingService", "name": "ORGATEC", "url": BASE_URL.rstrip("/")}}
    return '\n    <script type="application/ld+json">' + json.dumps(dados, ensure_ascii=False) + "</script>"


def trilha(p: str, passos: list, largura: str = "max-w-7xl") -> str:
    """Trilha de navegação das páginas internas: [(rótulo, caminho ou None para a página atual)]."""
    itens = [f'<li><a href="{p}{INICIO}">Início</a></li>'] + [
        f'<li><a href="{p}{u}">{r}</a></li>' if u else f'<li aria-current="page">{r}</li>' for r, u in passos]
    return f"""        <nav class="trilha {largura} mx-auto px-4 sm:px-6 lg:px-8 pt-6" aria-label="Trilha de navegação"><ol>{"".join(itens)}</ol></nav>"""


def barra_movel(p: str) -> str:
    """Atalhos fixos no rodapé da tela abaixo de 640 px: simular e pedir o diagnóstico (o WhatsApp fica no cabeçalho). paginas.js recolhe a barra enquanto o herói está visível."""
    return f"""    <div class="barra-movel" data-barra-movel>
        <a href="{p}ferramentas/simulador.html" class="og-btn og-btn-primario og-btn-md">Simular impacto</a>
        <a href="{p}{DIAGNOSTICO_URL}" class="og-btn og-btn-contorno og-btn-md">Solicitar diagnóstico</a>
    </div>"""


def scripts(p: str, extra: list[str] | None = None) -> str:
    ordem = SCRIPTS[:-1] + (extra or []) + SCRIPTS[-1:]  # extras antes de paginas.js, que usa os módulos
    return "\n".join(f'    <script src="{p}assets/js/{s}"></script>' for s in ordem)


AVISO_LEGAL = ("⚠️ Aviso Legal: Conteúdo orientativo baseado na EC nº 132/2023 e na LC nº 214/2025. Não substitui parecer técnico "
               "emitido pelo contador responsável. Itens marcados como \"pendente de validação\" ainda não foram conferidos na fonte primária.")
