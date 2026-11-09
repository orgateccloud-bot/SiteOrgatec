"""Área Empresarial (empresarial/): hub e página de lucro real e presumido (docs/ideias/reestruturacao-transporte.md, Fase 3).

Gerada por gerar_paginas.main(). O conteúdo jurídico NÃO fica aqui: os itens vêm de reforma-itens.js (destino
'empresarial-lucro-real') e são preenchidos no navegador por paginas.js, com fonte e status de revisão.
Transporte continua em setores/transporte.html até a decisão de mover páginas (anotada na ideia).
"""
from __future__ import annotations

import gerar_paginas as gp

MSG = "Olá! Quero falar com a ORGATEC sobre a reforma tributária na minha empresa."


def hub() -> None:
    cartoes = [
        gp.cartao("Transporte", "Transportadora, cooperativa e autônomo", "IBS e CBS no frete, crédito do diesel e as obrigações do transportador, com a fonte de cada ponto.", "{p}setores/transporte.html"),
        gp.cartao("Lucro real e presumido", "CBS no lugar de PIS e Cofins", "Créditos, saldos e a transição de 2027 a 2033 para quem não está no Simples.", "{p}empresarial/lucro-real.html"),
        gp.cartao("Simples Nacional", "IBS e CBS dentro ou fora do DAS", "Quando vale apurar IBS e CBS no regime regular e as janelas de opção.", "{p}reforma/simples-hibrido.html"),
        gp.cartao("Compliance", "O que cada público precisa cumprir", "Obrigações por público, com prazo e fonte, e o termômetro de conformidade.", "{p}compliance/publicos.html"),
    ]
    corpo = "\n".join([
        gp.hero("Área Empresarial", "Reforma tributária para a sua empresa ou transportadora.",
                "Transporte, lucro real e presumido e Simples em um lugar só, com a fonte oficial em cada orientação.",
                f'<a {gp.WHATS} data-msg="{MSG}" class="og-btn og-btn-contato og-btn-lg">Agendar Diagnóstico com Especialista</a>'
                '<a href="{p}ferramentas/simulador.html" class="og-btn og-btn-sobre-palco og-btn-lg">Testar Simulador Tributário</a>', compacto=True),
        gp.secao("Quem atendemos", "Por onde começar",
                 '                <p class="text-tinta-suave max-w-3xl mb-6">Escolha o caminho mais próximo da sua operação. Os textos orientam; a decisão do seu caso passa pelo contador responsável.</p>\n'
                 + gp.grade(cartoes), "bg-fundo", "caminhos", compacto=True),
        gp.faixa_cta("Comece pelo diagnóstico", "Em uma conversa, levantamos regime, atividade e fornecedores e indicamos o que precisa de decisão ainda em 2026.", compacto=True),
    ])
    gp.pagina("empresarial/index.html", "Área Empresarial: reforma tributária",
              "Reforma tributária para empresas e transportadoras: transporte, lucro real e presumido e Simples, com a fonte oficial em cada orientação.",
              "empresarial", "captação", corpo, trilha=[("Empresarial", None)])


def lucro_real() -> None:
    corpo = "\n".join([
        gp.hero("Empresarial · Lucro real e presumido", "CBS no lugar de PIS e Cofins, créditos e transição.",
                "Os pontos da reforma que mais pesam para quem apura pelo lucro real ou presumido, com fonte, data de consulta e status.",
                f'<a {gp.WHATS} data-msg="{MSG}" class="og-btn og-btn-contato og-btn-lg">Agendar Diagnóstico com Especialista</a>'
                '<a href="{p}ferramentas/simulador.html" class="og-btn og-btn-sobre-palco og-btn-lg">Testar Simulador Tributário</a>', compacto=True),
        gp.secao("Itens da reforma", "Pontos que mais afetam a decisão",
                 '                <p class="text-tinta-suave max-w-3xl mb-6">Cada item abre com o texto, a norma e a data em que a fonte foi consultada. Itens ainda sem revisão técnica trazem o selo "em revisão técnica".</p>\n'
                 + gp.itens(destino="empresarial-lucro-real", recolher=True, inicial=6), "bg-fundo", "itens", compacto=True),
        gp.secao("Compliance", "O que a empresa precisa cumprir",
                 '                <a href="{p}compliance/publico/comercio-industria.html" class="og-btn og-btn-primario og-btn-lg">Comércio e indústria</a> '
                 '<a href="{p}compliance/publico/servicos.html" class="og-btn og-btn-contorno og-btn-lg">Prestador de serviço</a>', "bg-superficie", "compliance", compacto=True),
        gp.faixa_cta("Diagnóstico para lucro real e presumido", "Levantamos créditos, saldos e fornecedores e mostramos o efeito ano a ano.", compacto=True),
    ])
    gp.pagina("empresarial/lucro-real.html", "Lucro real e presumido na reforma",
              "CBS no lugar de PIS e Cofins, créditos e transição para quem apura pelo lucro real ou presumido, com a fonte oficial de cada ponto.",
              "empresarial", "captação + autoridade", corpo, trilha=[("Empresarial", "empresarial/index.html"), ("Lucro real e presumido", None)])


def janela() -> None:
    """Janela Empresarial e do Transporte. Fica FORA do menu, do hub e do mapa do site (noindex) até a decisão R3 e a semana de sombra."""
    publicos = [("", "Escolha"), ("transportador", "Transportador de cargas"), ("comercio", "Comércio e indústria"),
                ("servicos", "Prestador de serviço"), ("simples", "Simples Nacional")]
    opcoes_pub = "".join(f'<option value="{v}">{r}</option>' for v, r in publicos)
    regimes = "".join(f'<option value="{v}"{" selected" if v == "real" else ""}>{r}</option>' for v, r in
                      (("simples", "Simples Nacional"), ("presumido", "Lucro presumido"), ("real", "Lucro real")))
    ufs = "".join(f'<option value="{u}">{u}</option>' for u in ("GO", "TO", "PA"))
    controles = ('<div class="flex flex-wrap items-end gap-3 mb-4">'
                 f'<div class="og-campo"><label class="og-campo-rotulo" for="jAtividade">Minha atividade</label><select id="jAtividade" class="og-campo-controle og-campo-md" data-filtro-janela="atividade">{opcoes_pub}</select></div>'
                 f'<div class="og-campo"><label class="og-campo-rotulo" for="jRegime">Regime</label><select id="jRegime" class="og-campo-controle og-campo-md" data-filtro-janela="regime">{regimes}</select></div>'
                 f'<div class="og-campo"><label class="og-campo-rotulo" for="jUf">UF</label><select id="jUf" class="og-campo-controle og-campo-md" data-filtro-janela="uf">{ufs}</select></div></div>')
    corpo = "\n".join([
        gp.hero("Empresarial · Janela", "O que importa para a sua empresa esta semana.",
                "Prazos dos próximos 7 dias, mudanças na reforma e, para o transportador, as obrigações do setor. Cada cartão mostra a fonte, a hora da coleta e o estado.",
                f'<a {gp.WHATS} data-msg="{MSG}" class="og-btn og-btn-contato og-btn-lg">Falar com o escritório</a>', compacto=True),
        gp.secao("Janela", "Seu painel", controles + '\n                <div data-janela-empresarial data-origem="{p}dados/empresarial/atual.json">'
                 '<div data-janela-lista aria-live="polite"><p class="og-cartao-texto">Carregando a janela…</p></div></div>', "bg-fundo", "janela", compacto=True),
    ])
    gp.pagina("empresarial/janela.html", "Janela Empresarial e do Transporte",
              "Prazos, mudanças da reforma e obrigações do transportador, com fonte, hora da coleta e estado de cada cartão.",
              "empresarial", "retenção", corpo, indexar=False, extra=["janela-empresarial.js"],
              trilha=[("Empresarial", "empresarial/index.html"), ("Janela", None)])


def gerar() -> None:
    hub()
    lucro_real()
    janela()
