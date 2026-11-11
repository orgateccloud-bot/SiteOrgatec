"""Área Empresarial (empresarial/): hub e página de lucro real e presumido (docs/ideias/reestruturacao-transporte.md, Fase 3).

Gerada por gerar_paginas.main(). O conteúdo jurídico NÃO fica aqui: os itens vêm de reforma-itens.js (destino
'empresarial-lucro-real') e são preenchidos no navegador por paginas.js, com fonte e status de revisão.
Transporte fica em empresarial/transporte.html; setores/transporte.html redireciona (301, tools/preparar_firebase.py).
"""
from __future__ import annotations

import gerar_paginas as gp

MSG = "Olá! Quero falar com a ORGATEC sobre a reforma tributária na minha empresa."


def hub() -> None:
    cartoes = [
        gp.cartao("Transporte", "Transportadora, cooperativa e autônomo", "IBS e CBS no frete, crédito do diesel e as obrigações do transportador, com a fonte de cada ponto.", "{p}empresarial/transporte.html"),
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


# "Minha atividade" da Janela e da janela do score: cada valor tem perfil em termometro.ATIVIDADE_PERFIL (vazio = geral)
ATIVIDADES = [("", "Escolha"), ("transportador", "Transportador de cargas"), ("comercio", "Comércio e indústria"),
              ("servicos", "Prestador de serviço"), ("simples", "Simples Nacional")]


def janela() -> None:
    """Janela Empresarial e do Transporte. Fica FORA do menu, do hub e do mapa do site (noindex) até a decisão R3 e a semana de sombra."""
    opcoes_pub = "".join(f'<option value="{v}">{r}</option>' for v, r in ATIVIDADES)
    regimes = "".join(f'<option value="{v}"{" selected" if v == "real" else ""}>{r}</option>' for v, r in
                      (("simples", "Simples Nacional"), ("presumido", "Lucro presumido"), ("real", "Lucro real")))
    ufs = "".join(f'<option value="{u}">{u}</option>' for u in ("GO", "TO", "PA"))
    controles = ('<div class="flex flex-wrap items-end gap-3 mb-4">'
                 f'<div class="og-campo"><label class="og-campo-rotulo" for="jAtividade">Minha atividade</label><select id="jAtividade" class="og-campo-controle og-campo-md" data-filtro-janela="atividade">{opcoes_pub}</select></div>'
                 f'<div class="og-campo"><label class="og-campo-rotulo" for="jRegime">Regime</label><select id="jRegime" class="og-campo-controle og-campo-md" data-filtro-janela="regime">{regimes}</select></div>'
                 f'<div class="og-campo"><label class="og-campo-rotulo" for="jUf">UF</label><select id="jUf" class="og-campo-controle og-campo-md" data-filtro-janela="uf">{ufs}</select></div></div>')
    corpo = "\n".join([
        gp.hero("Empresarial · Janela", "O que importa para a sua empresa esta semana.",
                "O score de compliance da sua empresa, prazos dos próximos 7 dias, mudanças na reforma e, para o transportador, as obrigações do setor. "
                "Cada cartão mostra a fonte, a hora da coleta e o estado.",
                f'<a {gp.WHATS} data-msg="{MSG}" class="og-btn og-btn-contato og-btn-lg">Falar com o escritório</a>', compacto=True),
        # O score (janela-empresarial.js → termometro.js) é calculado no navegador e não depende do atual.json
        gp.secao("Janela", "Seu painel", controles + '\n                <div data-janela-score aria-live="polite" class="mb-4"></div>'
                 '\n                <div data-janela-empresarial data-origem="{p}dados/empresarial/atual.json">'
                 '<div data-janela-lista aria-live="polite"><p class="og-cartao-texto">Carregando a janela…</p></div></div>', "bg-fundo", "janela", compacto=True),
    ])
    gp.pagina("empresarial/janela.html", "Janela Empresarial e do Transporte",
              "Score de compliance, prazos, mudanças da reforma e obrigações do transportador, com fonte, hora da coleta e estado de cada cartão.",
              "empresarial", "retenção", corpo, indexar=False, extra=["termometro.js", "janela-empresarial.js"],
              trilha=[("Empresarial", "empresarial/index.html"), ("Janela", None)])


def score() -> None:
    """Janela do score da empresa: medidor, evolução das notas registradas e alertas (site/assets/js/score-empresa.js).
    Fora do menu e noindex, como a Janela; aberta pelo cartão do score da Janela (score.html#perfil-<id>)."""
    opcoes = "".join(f'<option value="{v}">{"Qualquer empresa" if not v else r}</option>' for v, r in ATIVIDADES)
    controles = ('<div class="flex flex-wrap items-end gap-3 mb-4">'
                 f'<div class="og-campo"><label class="og-campo-rotulo" for="sAtividade">Minha atividade</label>'
                 f'<select id="sAtividade" class="og-campo-controle og-campo-md" data-score-atividade>{opcoes}</select></div>'
                 '<p class="text-sm text-tinta-suave pb-2">Perfil: <strong data-score-perfil>Qualquer empresa</strong></p></div>')
    painel = (controles +
              '\n                <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">'
              '<article class="og-cartao min-w-0"><span class="og-cartao-ref">Nota geral</span><div data-score-medidor></div></article>'
              '<article class="og-cartao min-w-0"><span class="og-cartao-ref">Evolução da nota</span><div data-score-evolucao></div>'
              '<div class="flex flex-wrap gap-3 mt-3"><button type="button" class="og-btn og-btn-primario og-btn-md" data-score-registrar hidden>Registrar a nota de hoje</button>'
              '<button type="button" class="og-btn og-btn-contorno og-btn-md" data-score-apagar hidden>Apagar histórico</button></div></article></div>'
              '\n                <article class="og-cartao mt-4"><div class="flex flex-wrap items-center justify-between gap-3 mb-3"><span class="og-cartao-ref">Alertas</span>'
              '<button type="button" class="og-btn og-btn-contorno og-btn-md" data-score-ics hidden>Adicionar prazos à agenda (.ics)</button></div>'
              '<div data-score-alertas aria-live="polite"></div></article>'
              '\n                <p class="text-sm text-tinta-suave mt-3" data-score-status role="status"></p>'
              '\n                <p class="text-xs text-tinta-fraca mt-2">Calculado só no seu navegador, com as respostas do termômetro. O histórico guarda só as notas, neste navegador, '
              'e só quando você registra. Não é parecer nem probabilidade de autuação. Pesos e faixas em revisão técnica.</p>')
    corpo = "\n".join([
        gp.hero("Empresarial · Score", "O score de compliance da sua empresa.",
                "A nota de 0 a 100 nas regras de compliance do seu perfil, como ela evolui e os alertas de prazo e de frente em risco, com a fonte de cada ponto.",
                f'<a {gp.WHATS} data-msg="{MSG}" class="og-btn og-btn-contato og-btn-lg">Falar com o escritório</a>'
                '<a href="{p}compliance/termometro.html" class="og-btn og-btn-sobre-palco og-btn-lg">Responder o termômetro</a>', compacto=True),
        gp.secao("Score", "Sua janela do score", '                <div data-score-empresa>' + painel + '</div>', "bg-fundo", "score", compacto=True),
    ])
    gp.pagina("empresarial/score.html", "Score de compliance da empresa",
              "Nota de compliance de 0 a 100, evolução e alertas de prazo e de frente em risco, calculados no navegador.",
              "empresarial", "retenção", corpo, indexar=False,
              extra=["compliance-itens.js", "calendario.js", "termometro.js", "score-empresa.js"],
              trilha=[("Empresarial", "empresarial/index.html"), ("Janela", "empresarial/janela.html"), ("Score", None)])


def gerar() -> None:
    hub()
    lucro_real()
    janela()
    score()
