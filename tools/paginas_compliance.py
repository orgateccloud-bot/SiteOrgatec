"""Área de Compliance (docs/plano-area-compliance.md), gerada à parte para não colidir com as outras frentes do site.

Uso: chamado por tools/gerar_paginas.py (main → paginas_compliance.gerar()).
Reaproveita os blocos de gerar_paginas (pagina, hero, intro, secao, itens, grade, marcos, lista, faixa_solucao).
O conteúdo legal NÃO fica aqui: os pontos vêm de compliance-itens.js e reforma-itens.js (destinos 'compliance*'),
renderizados por paginas.js com fonte, status e revisão técnica; as perguntas do termômetro vêm de termometro.js.
Aqui só há estrutura e textos institucionais.

Fases A a D: visão geral, as quatro frentes (conformidade tributária, PLD/FT, LGPD, integridade) e o termômetro.
Fase 2 (docs/relatorio-publicos-reforma-compliance.md): seção "Por público", com uma página por público
(destino 'publico-<id>' dos itens) e o perfil do público no termômetro.
"""

from __future__ import annotations

import gerar_paginas as gp

MSG = "Olá! Quero falar com a ORGATEC sobre compliance e conformidade da minha empresa."
SCRIPTS = ["compliance-itens.js", "inicio.js"]

# (chave, título, texto, página)
FRENTES = [
    ("tributario", "Conformidade tributária", "Programa de conformidade de 2026, documentos fiscais com IBS e CBS e programas da Receita Federal.",
     "compliance/conformidade-tributaria.html"),
    ("pld", "Prevenção à lavagem de dinheiro", "Quem a lei obriga a manter cadastro, registrar operações e comunicar ao COAF, e o que ela exige.",
     "compliance/prevencao-lavagem.html"),
    ("lgpd", "Proteção de dados (LGPD)", "Registro, segurança, encarregado e incidentes, com as regras próprias para pequenas empresas.",
     "compliance/protecao-de-dados.html"),
    ("integridade", "Integridade e anticorrupção", "Lei Anticorrupção e programa de integridade, obrigatório nos contratos públicos de grande vulto.",
     "compliance/integridade.html"),
]

# Área "Por público": (id, arquivo em compliance/publico/, título, texto do cartão). Só ganha página e link quem
# está em PUBLICOS_PRONTOS; os demais aparecem como "em preparação" até as normas serem conferidas (relatório, seção 6).
PUBLICOS = [
    ("transportador", "transportador.html", "Transportador de cargas", "RNTRC, CIOT, piso mínimo de frete, vale-pedágio, jornada do motorista e o IBS e a CBS do frete."),
    ("produtor", "produtor-rural.html", "Produtor rural", "CAR, ITR, Funrural, CNPJ e documento fiscal em 2027 e a opção pelo regime regular."),
    ("mei", "mei.html", "MEI", "Limite de receita, declaração anual e como o IBS e a CBS entram no valor fixo."),
    ("autonomo", "autonomo.html", "Autônomo e profissional liberal", "Quando a pessoa física passa a ser contribuinte de IBS e CBS e a redução de 30% das profissões."),
    ("simples", "simples.html", "Simples Nacional", "IBS e CBS dentro ou fora do DAS, crédito para o cliente empresa e as janelas de opção."),
    ("servicos", "servicos.html", "Prestador de serviço", "Lucro presumido ou real: crédito amplo, reduções setoriais e o programa de conformidade de 2026."),
    ("comercio", "comercio-industria.html", "Comércio e indústria", "Crédito amplo, estoque de 2027, IPI, Imposto Seletivo e saldos de ICMS."),
    ("imoveis", "imoveis.html", "Pessoa física com imóveis", "Quando quem aluga ou vende imóveis passa a ser contribuinte de IBS e CBS."),
]
PUBLICOS_PRONTOS = {"transportador", "produtor", "mei", "autonomo", "simples", "comercio", "servicos", "imoveis"}
FILTROS = [(c, t) for c, t, _, _ in FRENTES] + [("transporte", "Obrigações do transportador"), ("rural", "Obrigações do produtor rural"), ("pequenos", "MEI, autônomo e Simples"), ("imoveis", "Pessoa física com imóveis")]

COMO_VERIFICA = gp.marcos([
    ("Levantamento", "Obrigações da empresa, documentos emitidos e cadastros, frente por frente."),
    ("Cruzamento", "Notas, escrituração, extratos e livro-caixa conferidos entre si, com os sistemas do escritório."),
    ("Relatório", "O que corrigir, por prioridade, com a fonte legal de cada ponto."),
    ("Acompanhamento", "Prazos no calendário e revisão a cada mudança de regra."),
])
REVISAO_JURIDICA = ("Sem parecer jurídico", "O escritório faz o diagnóstico e organiza documentos e rotinas. Quando a situação exigir análise jurídica, aponta o ponto e a necessidade de um advogado.")


def frente_cartao(chave: str, titulo: str, texto: str, pagina: str) -> str:
    return (f'<a href="{{p}}{pagina}" class="og-cartao" data-frente="{chave}"><span class="og-cartao-ref">Frente</span>'
            f'<h3 class="og-cartao-titulo">{titulo}</h3><p class="og-cartao-texto">{texto}</p></a>')


def faq(destino: str, fundo: str = "bg-fundo") -> str:
    return gp.secao("Perguntas frequentes", "O que as empresas mais perguntam",
                    f'                <div class="faq max-w-3xl" data-faq-itens="{destino}"></div>', fundo, "perguntas")


def prazos(destino: str) -> str:
    return f'                <ul class="grid grid-cols-1 md:grid-cols-2 gap-4" data-prazos="{destino}"></ul>'


def chamada_termometro(pilar: str, rotulo: str) -> str:
    return gp.secao("Ferramenta", "Como está a sua empresa nesta frente?",
                    f'                <p class="text-tinta-suave max-w-3xl mb-6">Responda às perguntas de {rotulo} no termômetro de conformidade. Cada pergunta traz a fonte legal, e as respostas ficam só no seu navegador.</p>\n'
                    f'                <a href="{{p}}compliance/termometro.html#{pilar}" class="og-btn og-btn-primario og-btn-lg">Abrir o termômetro desta frente</a>',
                    "bg-superficie", "termometro")


def publico_cartao(chave: str, arquivo: str, titulo: str, texto: str) -> str:
    if chave in PUBLICOS_PRONTOS:
        return (f'<a href="{{p}}compliance/publico/{arquivo}" class="og-cartao" data-publico="{chave}"><span class="og-cartao-ref">Público</span>'
                f'<h3 class="og-cartao-titulo">{titulo}</h3><p class="og-cartao-texto">{texto}</p></a>')
    return (f'<div class="og-cartao" data-publico="{chave}" data-em-preparacao><span class="og-cartao-ref">Público</span>'
            f'<h3 class="og-cartao-titulo">{titulo}</h3><p class="og-cartao-texto">{texto}</p>'
            '<p class="mt-3"><span class="og-selo og-selo-pendente">Em preparação</span></p></div>')


def grade_publicos() -> str:
    return gp.grade([publico_cartao(*x) for x in PUBLICOS], "md:grid-cols-2 lg:grid-cols-4")


def visao_geral() -> None:
    corpo = "\n".join([
        gp.hero("Compliance", 'Cumprir antes de ser <mark class="marca-texto">cobrado</mark>.',
                "Conformidade tributária, prevenção à lavagem de dinheiro, proteção de dados e integridade: o que a lei exige da sua empresa, com a fonte de cada ponto, e como a ORGATEC verifica.",
                '<a href="{p}compliance/termometro.html" class="og-btn og-btn-primario og-btn-lg">Fazer o termômetro de conformidade</a>'
                f'<a {gp.WHATS} data-msg="{MSG}" class="og-btn og-btn-contato og-btn-lg">Falar com o escritório</a>'),
        gp.secao("Frentes", "As quatro frentes da área", gp.grade([frente_cartao(*f) for f in FRENTES]), "bg-superficie", "frentes"),
        gp.secao("Por público", "O que cada público precisa cumprir", grade_publicos() +
                 '\n                <p class="mt-6"><a href="{p}compliance/publicos.html" class="og-link">Ver todos os públicos →</a></p>', id_="publicos"),
        gp.secao("Prazos", "Datas que pedem atenção", prazos("compliance") +
                 '\n                <p class="mt-6"><a href="{p}ferramentas/calendario.html" class="og-link">Ver no calendário fiscal (esfera Compliance) →</a></p>', id_="prazos"),
        gp.secao("Pontos acompanhados", "O que a regra exige hoje", gp.itens(destino="compliance"), "bg-superficie", "itens"),
        gp.secao("Como funciona", "Como a ORGATEC verifica", COMO_VERIFICA +
                 '\n                <p class="mt-6"><a href="{p}solucoes/index.html" class="og-link">Os sistemas que o escritório usa nessa verificação →</a></p>', id_="como-funciona"),
        faq("compliance", "bg-superficie"),
        gp.faixa_solucao("Por onde começar na sua empresa?", "Em uma conversa, o escritório indica a frente mais urgente e o que levantar primeiro.", MSG, "Falar com o escritório"),
    ])
    gp.pagina("compliance/index.html", "Compliance: cumprir antes de ser cobrado",
              "Área de compliance da ORGATEC: conformidade tributária, prevenção à lavagem de dinheiro, proteção de dados e integridade, com a fonte oficial de cada ponto.",
              "compliance", "captação + autoridade", corpo, extra=SCRIPTS, trilha=[("Compliance", None)])


def frente(pilar: str, arquivo: str, titulo_pagina: str, descricao: str, rotulo: str, titulo: str, lead: str,
           para_quem: list, como_ajuda: list, relacionados: list | None = None) -> None:
    """Modelo único das páginas de frente (seção 5 do plano)."""
    msg = f"Olá! Quero falar com a ORGATEC sobre {rotulo} na minha empresa."
    partes = [
        gp.hero(f"Compliance · {rotulo[0].upper() + rotulo[1:]}", titulo, lead,
                f'<a {gp.WHATS} data-msg="{msg}" class="og-btn og-btn-contato og-btn-lg">Falar com o escritório</a>'
                '<a href="{p}compliance/index.html" class="og-btn og-btn-sobre-palco og-btn-lg">Ver todas as frentes</a>'),
        gp.secao("Para quem", "Quem mais precisa olhar", gp.lista(para_quem)),
        gp.secao("Prazos", "Datas que pedem atenção", prazos(f"compliance-{pilar}"), "bg-superficie", "prazos"),
        gp.secao("O que a regra exige", "Pontos acompanhados, com a fonte", gp.itens(destino=f"compliance-{pilar}"), id_="itens"),
        gp.secao("Como a ORGATEC ajuda", "Do levantamento à rotina", gp.marcos(como_ajuda), "bg-superficie", "como-funciona"),
        chamada_termometro(pilar, rotulo),
    ]
    partes.append(faq(f"compliance-{pilar}"))
    if relacionados:
        partes.append(gp.secao("Relacionado", "Ferramentas e serviços", gp.grade(relacionados, "md:grid-cols-3")))
    partes.append(gp.faixa_solucao("Quer revisar esta frente na sua empresa?", "Em uma conversa, o escritório levanta o que falta e a prioridade de cada ponto.", msg, "Falar com o escritório"))
    gp.pagina(f"compliance/{arquivo}", titulo_pagina, descricao, "compliance", "captação + autoridade", "\n".join(partes), extra=SCRIPTS,
              trilha=[("Compliance", "compliance/index.html"), (titulo_pagina.split(":")[0], None)])


def frentes() -> None:
    frente("tributario", "conformidade-tributaria.html", "Conformidade tributária: IBS, CBS e programas da Receita",
           "Conformidade tributária com a ORGATEC: Programa Nacional de Conformidade de 2026, documentos fiscais com IBS e CBS e programas de conformidade da Receita Federal, com a fonte oficial.",
           "conformidade tributária", 'A empresa em dia com as <mark class="marca-texto">regras novas</mark> de IBS e CBS.',
           "Programa Nacional de Conformidade de 2026, documentos fiscais com os campos de IBS e CBS e programas de conformidade da Receita: o que vale, para quem e até quando, com a fonte oficial.",
           [("Lucro real", "Obrigações acessórias de IBS e CBS já em 2026 e a escrituração que sustenta os créditos."),
            ("Transporte", "CT-e e MDF-e com os campos de IBS e CBS; erro de classificação vira inconsistência."),
            ("Produtor rural", "CNPJ e documento fiscal do produtor pessoa física a partir de 01/01/2027."),
            ("Quem tem pendências", "O programa de 2026 depende de corrigir as inconsistências dentro do prazo.")],
           [("Inventário", "Documentos emitidos e obrigações acessórias de IBS e CBS da empresa."),
            ("Cruzamento", "Notas, escrituração e livro-caixa conferidos entre si, com os sistemas do escritório."),
            ("Correção", "Lista do que ajustar, por prioridade e com a fonte de cada ponto."),
            ("Acompanhamento", "Prazos no calendário e as intimações do programa acompanhadas pelo escritório.")],
           [gp.C_CALENDARIO,
            gp.cartao("Sistema próprio", "Conciliação bancária", "Extratos conferidos com a contabilidade e laudo das divergências.", "{p}solucoes/conciliacao.html"),
            gp.cartao("Serviço do escritório", "Auditoria forense rural (NFA-e)", "As notas do produtor rural conferidas uma a uma, com laudo.", "{p}solucoes/auditoria-rural.html")])
    frente("pld", "prevencao-lavagem.html", "Prevenção à lavagem de dinheiro (PLD/FT)",
           "Prevenção à lavagem de dinheiro com a ORGATEC: quem a Lei nº 9.613/1998 obriga, cadastro, registro, comunicação ao COAF e sanções, com a fonte oficial.",
           "prevenção à lavagem de dinheiro", 'Saber se a lei <mark class="marca-texto">obriga</mark> a sua empresa, e o que fazer se obrigar.',
           "A Lei nº 9.613/1998 exige cadastro de clientes, registro de operações e comunicação ao COAF de quem atua em setores de maior risco, inclusive no comércio de bens de alto valor de origem rural ou animal. Veja quem é obrigado e o que a regra pede, com a fonte.",
           [("Bens de alto valor", "Comércio de bens de luxo ou de alto valor, inclusive de origem rural ou animal, e a sua intermediação."),
            ("Factoring e crédito", "Empresas de factoring e Empresas Simples de Crédito."),
            ("Imóveis", "Promoção imobiliária e compra e venda de imóveis."),
            ("Dinheiro em espécie", "Atividades que envolvem grande volume de recursos em espécie.")],
           [("Enquadramento", "Verificar se a atividade está entre as pessoas obrigadas e qual é o órgão regulador."),
            ("Organização", "Cadastro de clientes e registro das operações, guardados por no mínimo cinco anos."),
            ("Rotina", "Quem comunica ao COAF em 24 horas e como informar a não ocorrência."),
            REVISAO_JURIDICA])
    frente("lgpd", "protecao-de-dados.html", "Proteção de dados (LGPD)",
           "LGPD com a ORGATEC: registro das operações, segurança, encarregado, incidentes e as regras para microempresas e empresas de pequeno porte, com a fonte oficial.",
           "proteção de dados", 'Dados pessoais <mark class="marca-texto">organizados</mark> e protegidos.',
           "Registro das operações, medidas de segurança, encarregado e comunicação de incidentes: o que a LGPD exige e o que muda para microempresas e empresas de pequeno porte, com a fonte.",
           [("Microempresas e EPP", "Têm regras próprias na Resolução CD/ANPD nº 2/2022, sem dispensa do restante da LGPD."),
            ("Quem tem empregados", "Folha e eSocial tratam dados pessoais de todos os empregados."),
            ("Comércio e serviços", "Cadastros de clientes, notas fiscais e cobranças."),
            ("Dados sensíveis", "Dados de saúde, de crianças, de adolescentes e de idosos podem tornar o tratamento de alto risco.")],
           [("Mapeamento", "Onde a empresa trata dados pessoais: clientes, empregados e fornecedores."),
            ("Registro", "Registro das operações de tratamento, simplificado quando a empresa se enquadra como pequeno porte."),
            ("Rotinas", "Medidas de segurança, canal com os titulares e resposta a incidentes."),
            REVISAO_JURIDICA])
    frente("integridade", "integridade.html", "Integridade e anticorrupção",
           "Integridade com a ORGATEC: Lei Anticorrupção, programa de integridade e a exigência nos contratos públicos de grande vulto, com a fonte oficial.",
           "integridade e anticorrupção", 'Integridade para quem <mark class="marca-texto">contrata</mark> com o poder público.',
           "A Lei Anticorrupção responsabiliza a empresa por atos contra a administração pública, e um programa de integridade conta na aplicação das sanções. Nos contratos públicos de grande vulto, ele é obrigatório. Veja o que a regra considera, com a fonte.",
           [("Fornecedores do poder público", "Empresas que vendem ou prestam serviços a órgãos públicos."),
            ("Transporte", "Frete e logística contratados por órgãos públicos."),
            ("Licitações", "O programa de integridade também conta no desempate e na reabilitação de licitantes."),
            ("Pequenas empresas", "A avaliação considera o porte, inclusive de microempresas e empresas de pequeno porte.")],
           [("Diagnóstico", "Riscos nas relações com o setor público e com terceiros."),
            ("Base contábil", "Registros contábeis e controles internos sobre os relatórios financeiros, dois dos parâmetros do decreto."),
            ("Código e canal", "Organização do código de conduta, dos treinamentos e do canal de denúncias."),
            REVISAO_JURIDICA])


def publicos() -> None:
    """Página-guia da área "Por público": um cartão por público do relatório de públicos."""
    corpo = "\n".join([
        gp.intro("Compliance · Por público", "O que cada público precisa cumprir",
                 "A reforma tributária e as regras de cada setor atingem de forma diferente o transportador, o produtor rural, o MEI, o autônomo, as empresas do Simples e as demais. Escolha o seu caso: cada página reúne as regras com a fonte oficial, as datas e as perguntas do termômetro."),
        gp.secao("Públicos", "Escolha o seu caso", grade_publicos() +
                 '\n                <p class="text-sm text-tinta-fraca mt-6">Páginas "em preparação" entram no ar depois que as normas de cada público forem conferidas na fonte oficial.</p>', id_="publicos"),
        gp.faixa_solucao("Não achou o seu caso?", "Em uma conversa, o escritório identifica o que vale para a sua empresa ou atividade.", MSG, "Falar com o escritório"),
    ])
    gp.pagina("compliance/publicos.html", "Compliance por público",
              "O que cada público atingido pela reforma tributária precisa cumprir: transportador, produtor rural, MEI, autônomo, Simples Nacional, serviços, comércio e indústria e pessoa física com imóveis.",
              "compliance", "captação", corpo, extra=SCRIPTS, trilha=[("Compliance", "compliance/index.html"), ("Por público", None)])


def publico(chave: str, titulo_pagina: str, descricao: str, titulo: str, lead: str, para_quem: list, como_ajuda: list,
            relacionados: list | None = None, ferramenta: str = "") -> None:
    """Modelo único das páginas por público: mesmos blocos de frente(), com o destino 'publico-<chave>'."""
    arquivo = next(a for c, a, _, _ in PUBLICOS if c == chave)
    nome = next(t for c, _, t, _ in PUBLICOS if c == chave)
    destino = f"publico-{chave}"
    msg = f"Olá! Quero falar com a ORGATEC sobre o que preciso cumprir como {nome.lower()}."
    partes = [
        gp.hero(f"Compliance · Por público · {nome}", titulo, lead,
                f'<a {gp.WHATS} data-msg="{msg}" class="og-btn og-btn-contato og-btn-lg">Falar com o escritório</a>'
                '<a href="{p}compliance/publicos.html" class="og-btn og-btn-sobre-palco og-btn-lg">Ver outros públicos</a>'),
        gp.secao("Para quem", "Quem precisa olhar", gp.lista(para_quem)),
        gp.secao("Prazos", "Datas que pedem atenção", prazos(destino) +
                 '\n                <p class="mt-6"><a href="{p}ferramentas/calendario.html" class="og-link">Datas que se repetem todo ano estão no calendário fiscal (esfera Compliance) →</a></p>',
                 "bg-superficie", "prazos"),
        gp.secao("O que a regra exige", "Pontos acompanhados, com a fonte", gp.itens(destino=destino), id_="itens"),
        ferramenta,
        gp.secao("Como a ORGATEC ajuda", "Do levantamento à rotina", gp.marcos(como_ajuda), "bg-superficie", "como-funciona"),
        gp.secao("Ferramenta", "Como está a sua empresa?",
                 '                <p class="text-tinta-suave max-w-3xl mb-6">O termômetro de conformidade abre no perfil deste público. Cada pergunta traz a fonte legal, e as respostas ficam só no seu navegador.</p>\n'
                 f'                <a href="{{p}}compliance/termometro.html#perfil-{chave}" class="og-btn og-btn-primario og-btn-lg">Abrir o termômetro deste público</a>',
                 id_="termometro"),
        faq(destino, "bg-superficie"),
    ]
    if relacionados:
        partes.append(gp.secao("Relacionado", "Páginas e ferramentas", gp.grade(relacionados, "md:grid-cols-3")))
    partes.append(gp.faixa_solucao("Quer revisar isso na sua empresa?", "Em uma conversa, o escritório levanta o que falta e a prioridade de cada ponto.", msg, "Falar com o escritório"))
    gp.pagina(f"compliance/publico/{arquivo}", titulo_pagina, descricao, "compliance", "captação + autoridade", "\n".join(partes), extra=SCRIPTS,
              trilha=[("Compliance", "compliance/index.html"), ("Por público", "compliance/publicos.html"), (nome, None)])


CTRL_NUM = 'og-campo-controle og-campo-md font-mono'


def _campo(id_: str, rotulo: str, ajuda: str = "") -> str:
    dica = f'<p class="og-campo-ajuda">{ajuda}</p>' if ajuda else ""
    return (f'<div class="og-campo"><label class="og-campo-rotulo" for="{id_}">{rotulo}</label>'
            f'<input id="{id_}" inputmode="decimal" class="{CTRL_NUM}">{dica}</div>')


CALC_IMOVEIS = f"""                <form id="formImoveisPF" class="og-cartao grid grid-cols-1 gap-4 min-w-0 max-w-3xl" novalidate>
                    <p class="og-cartao-texto">Os valores ficam só no seu navegador. Deixe em branco o que não se aplica.</p>
                    <fieldset class="grid grid-cols-1 sm:grid-cols-2 gap-4"><legend class="og-campo-rotulo mb-2">Ano anterior</legend>
                        {_campo("iReceitaAnt", "Receita de aluguel (R$)")}
                        {_campo("iLocadosAnt", "Imóveis alugados")}
                        {_campo("iVendidosAnt", "Imóveis vendidos", "Só os que estavam com você havia menos de 5 anos.")}
                        {_campo("iConstruidosAnt", "Imóveis construídos por você e vendidos", "Construídos nos 5 anos anteriores à venda.")}
                    </fieldset>
                    <fieldset class="grid grid-cols-1 sm:grid-cols-2 gap-4"><legend class="og-campo-rotulo mb-2">Este ano (até agora)</legend>
                        {_campo("iReceitaAtual", "Receita de aluguel (R$)")}
                        {_campo("iVendidosAtual", "Imóveis vendidos")}
                        {_campo("iConstruidosAtual", "Imóveis construídos por você e vendidos")}
                    </fieldset>
                    <button type="submit" class="og-btn og-btn-primario og-btn-lg w-full sm:w-auto">Ver o enquadramento</button>
                    <div id="iResultado" class="og-cartao" aria-live="polite" hidden></div>
                </form>"""


def publicos_paginas() -> None:
    publico("transportador", "Compliance do transportador de cargas",
            "O que o transportador de cargas e quem contrata frete precisam cumprir: RNTRC, CIOT, piso mínimo de frete, vale-pedágio, jornada e exame toxicológico do motorista e o IBS e a CBS do frete, com a fonte oficial.",
            'O frete em dia com a <mark class="marca-texto">ANTT</mark> e com a reforma.',
            "RNTRC revalidado todo ano, CIOT antes de cada operação, piso mínimo de frete, vale-pedágio, jornada do motorista e os campos de IBS e CBS no CT-e e no MDF-e: o que vale para quem transporta e para quem contrata, com a fonte oficial.",
            [("Empresa de transporte (ETC)", "Pessoa jurídica que tem no transporte rodoviário de cargas a sua atividade principal."),
             ("Autônomo (TAC)", "Pessoa física que tem no transporte de cargas a sua atividade profissional, inclusive inscrita como MEI."),
             ("Cooperativa (CTC)", "Cooperativa de transporte rodoviário de cargas."),
             ("Quem contrata frete", "Embarcador e transportadora que subcontrata: CIOT, piso, vale-pedágio e pagamento do autônomo são obrigações de quem contrata.")],
            [("Levantamento", "Situação do RNTRC, contratos de frete, CIOT emitidos e motoristas com exame e jornada."),
             ("Conferência", "Fretes contra o piso da ANTT, pagamentos ao autônomo, vale-pedágio no DT-e e IBS e CBS nos documentos fiscais."),
             ("Rotina", "Prazos de revalidação, de exames e de atualização dos pisos acompanhados no calendário."),
             REVISAO_JURIDICA],
            [gp.cartao("Setor", "Reforma tributária no transporte", "IBS e CBS no frete, crédito do autônomo e combustíveis.", "{p}setores/transporte.html"),
             gp.C_CALENDARIO,
             gp.cartao("Ferramenta", "Termômetro de conformidade", "Perguntas do transportador, com a fonte de cada uma.", "{p}compliance/termometro.html#perfil-transportador")])
    publico("produtor", "Compliance do produtor rural",
            "O que o produtor rural precisa cumprir: CAR, ITR, Funrural, NR-31, CNPJ e documento fiscal em 2027, IBS e CBS do produtor e o regulamento europeu contra o desmatamento, com a fonte oficial.",
            'A fazenda em dia com o <mark class="marca-texto">fisco</mark>, o crédito e o comprador.',
            "CAR e ITR em dia para não travar o crédito rural, a escolha do Funrural, a segurança no trabalho do campo, o CNPJ do produtor pessoa física em 2027, o IBS e a CBS na venda da produção e as exigências da União Europeia para soja, gado, café e madeira, com a fonte oficial.",
            [("Produtor pessoa física", "Com ou sem empregados; CNPJ e documento fiscal obrigatórios a partir de 01/01/2027."),
             ("Produtor pessoa jurídica", "Contribuinte de IBS e CBS, com crédito dos insumos e as reduções do agro."),
             ("Quem toma crédito rural", "CAR e ITR dos últimos cinco exercícios em dia são condição para o financiamento."),
             ("Quem vende para exportação", "Soja, gado, café, cacau, borracha, palma e madeira destinados à União Europeia.")],
            [("Levantamento", "Imóveis, CAR, ITR dos últimos cinco anos, empregados e forma de contribuição ao Funrural."),
             ("Conferência", "Notas e livro-caixa (LCDPR) conferidos entre si, com os sistemas do escritório, e o enquadramento em IBS e CBS."),
             ("Rotina", "Prazos do ITR, da opção do Funrural e do CNPJ de 2027 acompanhados no calendário."),
             REVISAO_JURIDICA],
            [gp.cartao("Setor", "Reforma tributária no agro", "Produtor não contribuinte, redução de 60%, diferimento e crédito presumido.", "{p}setores/agro.html"),
             gp.cartao("Serviço do escritório", "Auditoria forense rural (NFA-e)", "As notas do produtor rural conferidas uma a uma, com laudo.", "{p}solucoes/auditoria-rural.html"),
             gp.cartao("Ferramenta", "Termômetro de conformidade", "Perguntas do produtor rural, com a fonte de cada uma.", "{p}compliance/termometro.html#perfil-produtor")])
    publico("mei", "Compliance do MEI",
            "O que o MEI precisa cumprir com a reforma: limite de R$ 110 mil em 2027 e R$ 140 mil em 2028, IBS e CBS no valor fixo mensal, remissão de débitos e quando a pessoa física vira contribuinte, com a fonte oficial.",
            'O MEI em dia com o <mark class="marca-texto">novo limite</mark> e com o IBS e a CBS.',
            "O limite do MEI muda em 2027 e em 2028, o IBS e a CBS entram no valor fixo mensal e há perdão de débitos da contribuição até 13/10/2026, com contrapartida. Veja o que vale, desde quando e o que fazer, com a fonte oficial.",
            [("MEI que cresce", "Receita perto do limite: em 2027 ele é de R$ 110 mil; a partir de 2028, R$ 140 mil."),
             ("MEI com débitos", "Contribuição mensal em atraso até 13/10/2026 pode ser perdoada, desde que os meses seguintes fiquem em dia."),
             ("Quem pensa em virar MEI", "A opção pelo SIMEI é feita em janeiro; fora do MEI, a pessoa física pode ser contribuinte de IBS e CBS."),
             ("MEI com empregado", "A partir de 2027, até 2 empregados com salário mínimo ou piso da categoria.")],
            [("Enquadramento", "Receita do ano conferida com o limite e o risco de desenquadramento."),
             ("Regularização", "Débitos levantados e a contrapartida da remissão acompanhada mês a mês."),
             ("Transição", "Quando sair do MEI: Simples, regime regular ou pessoa física, com o efeito no IBS e na CBS."),
             REVISAO_JURIDICA],
            [gp.cartao("Público", "Simples Nacional", "IBS e CBS dentro ou fora do DAS e as janelas de opção.", "{p}compliance/publico/simples.html"),
             gp.C_CALENDARIO,
             gp.cartao("Ferramenta", "Termômetro de conformidade", "Perguntas do MEI, com a fonte de cada uma.", "{p}compliance/termometro.html#perfil-mei")])
    publico("autonomo", "Compliance do autônomo e do profissional liberal",
            "Quando o autônomo e o profissional liberal pessoa física passam a ser contribuintes de IBS e CBS: habitualidade, nanoempreendedor, regra de 25% para motorista e entregador de aplicativo e a redução de 30% das profissões com conselho, com a fonte oficial.",
            'Saber se a reforma <mark class="marca-texto">alcança</mark> você como pessoa física.',
            "Quem trabalha por conta própria pode passar a ser contribuinte de IBS e CBS. A lei usa a habitualidade, a atividade profissional e um limite de receita. Veja quando isso acontece, a regra dos aplicativos e a redução de 30% das profissões fiscalizadas por conselho, com a fonte oficial.",
            [("Profissional liberal", "Contador, advogado, engenheiro, arquiteto e outras profissões com conselho: redução de 30% ligada à habilitação."),
             ("Motorista e entregador de aplicativo", "Para o limite do nanoempreendedor, conta só 25% do valor bruto recebido no mês."),
             ("Prestador de serviço autônomo", "Atividade habitual ou profissional, ainda que a profissão não seja regulamentada."),
             ("Quem tem receita pequena", "Abaixo de metade do limite do MEI, sem ter aderido ao MEI, a pessoa não é contribuinte.")],
            [("Enquadramento", "Receita do ano, atividade e profissão: contribuinte, nanoempreendedor ou MEI."),
             ("Comparação", "Pessoa física, MEI ou empresa: o efeito de cada caminho no IBS, na CBS e no imposto de renda."),
             ("Rotina", "Cadastro, documento fiscal e prazos, se passar a contribuinte."),
             REVISAO_JURIDICA],
            [gp.cartao("Público", "MEI", "Limite, valor fixo com IBS e CBS e remissão de débitos.", "{p}compliance/publico/mei.html"),
             gp.cartao("Ferramenta", "Simulador de impacto", "IBS e CBS da atividade, com a redução das profissões.", "{p}ferramentas/simulador.html"),
             gp.cartao("Ferramenta", "Termômetro de conformidade", "Perguntas do autônomo, com a fonte de cada uma.", "{p}compliance/termometro.html#perfil-autonomo")])
    publico("simples", "Compliance da empresa do Simples Nacional",
            "O que a empresa do Simples Nacional precisa cumprir com a reforma: IBS e CBS dentro ou fora do DAS, janelas de setembro e março, documentos fiscais em 2027 e a vedação da locação de imóveis próprios, com a fonte oficial.",
            'Simples Nacional: IBS e CBS <mark class="marca-texto">dentro ou fora</mark> do DAS.',
            "A empresa do Simples pode continuar pagando IBS e CBS no DAS ou apurá-los por fora, no regime regular, escolhendo a cada semestre. Veja as janelas de opção, o que muda nos documentos fiscais em 2027 e quem não pode ficar no Simples, com a fonte oficial.",
            [("Quem vende para empresas", "O cliente do regime regular só aproveita, como crédito, o IBS e a CBS cobrados no Simples; por fora, o crédito é integral."),
             ("Quem compra muitos insumos", "No regime regular, a empresa também credita o IBS e a CBS das compras."),
             ("Quem emite nota fiscal", "Campos de IBS e CBS obrigatórios no Simples a partir de 01/01/2027."),
             ("Quem aluga imóveis próprios", "A locação de imóveis próprios impede o Simples Nacional desde 2025.")],
            [("Diagnóstico", "Clientes, fornecedores e margem: IBS e CBS no DAS ou por fora, em números."),
             ("Decisão", "Opção na janela certa (março ou setembro), com o efeito no preço e no caixa."),
             ("Rotina", "Emissor de notas, apuração e prazos acompanhados no calendário."),
             REVISAO_JURIDICA],
            [gp.cartao("Ferramenta", "Simulador de impacto", "Simples, presumido e real com IBS e CBS.", "{p}ferramentas/simulador.html"),
             gp.C_CALENDARIO,
             gp.cartao("Ferramenta", "Termômetro de conformidade", "Perguntas do Simples, com a fonte de cada uma.", "{p}compliance/termometro.html#perfil-simples")])
    publico("comercio", "Compliance do comércio e da indústria",
            "O que o comércio atacadista e a indústria precisam cumprir com a reforma: crédito amplo de IBS e CBS, estoque de 2027, IPI, Imposto Seletivo, documentos fiscais, saldos de ICMS e o programa de conformidade de 2026, com a fonte oficial.",
            'Crédito, estoque e ICMS: a <mark class="marca-texto">transição</mark> sem perder dinheiro.',
            "Crédito amplo de IBS e CBS, crédito presumido sobre o estoque de 01/01/2027, IPI com alíquota zero, Imposto Seletivo, documentos fiscais e os saldos credores de ICMS que só serão compensados se estiverem homologados. Veja o que vale e desde quando, com a fonte oficial.",
            [("Comércio atacadista", "Crédito amplo nas compras e o estoque de 01/01/2027 com crédito presumido de CBS."),
             ("Indústria", "IPI com alíquota zero em 2027 (exceto na Zona Franca de Manaus) e o Imposto Seletivo sobre os produtos listados."),
             ("Quem acumula crédito de ICMS", "Saldo credor ao fim de 2032 compensado com o IBS, se admitido e homologado."),
             ("Quem tem incentivo estadual", "Benefícios de ICMS diminuem com o imposto, de 2029 a 2032.")],
            [("Diagnóstico", "Crédito de compras, estoque, saldos de ICMS e incentivos, em números."),
             ("Conformidade", "Documentos fiscais com IBS e CBS e as inconsistências do programa de 2026 corrigidas."),
             ("Transição", "Plano ano a ano até 2033, com o efeito no preço e no caixa."),
             REVISAO_JURIDICA],
            [gp.cartao("Setor", "Alertas regionais", "Comércio atacadista e indústria em Goiás, Tocantins e Pará.", "{p}setores/regional.html"),
             gp.cartao("Ferramenta", "Simulador de impacto", "Comércio atacadista e indústria com IBS e CBS.", "{p}ferramentas/simulador.html"),
             gp.cartao("Ferramenta", "Termômetro de conformidade", "Perguntas do comércio e da indústria, com a fonte de cada uma.", "{p}compliance/termometro.html#perfil-comercio")])
    publico("servicos", "Compliance do prestador de serviço",
            "O que o prestador de serviço no lucro presumido ou real precisa cumprir com a reforma: crédito amplo, reduções de 60% para saúde e educação e de 30% para profissões com conselho, split payment, ISS até 2032 e o programa de conformidade de 2026, com a fonte oficial.",
            'Serviços: o fim do ISS e as <mark class="marca-texto">reduções</mark> que dependem de enquadramento.',
            "O ISS diminui de 2029 a 2032 e acaba em 2033; o IBS e a CBS chegam com crédito amplo e com reduções de 60% para os serviços de saúde e educação dos anexos e de 30% para as profissões fiscalizadas por conselho. Veja o que vale e o que conferir, com a fonte oficial.",
            [("Saúde e educação", "Redução de 60% só para os serviços listados nos anexos, com a classificação na NBS."),
             ("Sociedades de profissionais", "Redução de 30% com requisitos: sócios habilitados e nenhum sócio pessoa jurídica."),
             ("Lucro presumido", "PIS e Cofins cumulativos dão lugar à CBS não cumulativa em 2027."),
             ("Quem tem pendências", "O programa de conformidade de 2026 depende de corrigir as inconsistências no prazo.")],
            [("Enquadramento", "Cada serviço classificado na NBS e conferido com os anexos e com o art. 127."),
             ("Crédito", "Despesas que passam a gerar crédito de IBS e CBS e o efeito no preço."),
             ("Rotina", "Documentos fiscais, apuração e prazos no calendário."),
             REVISAO_JURIDICA],
            [gp.cartao("Público", "Autônomo e profissional liberal", "Quando a pessoa física vira contribuinte e a redução de 30%.", "{p}compliance/publico/autonomo.html"),
             gp.cartao("Ferramenta", "Simulador de impacto", "Serviços, saúde, educação e profissões com IBS e CBS.", "{p}ferramentas/simulador.html"),
             gp.cartao("Ferramenta", "Termômetro de conformidade", "Perguntas do prestador de serviço, com a fonte de cada uma.", "{p}compliance/termometro.html#perfil-servicos")])
    publico("imoveis", "Compliance da pessoa física com imóveis",
            "Quando quem aluga ou vende imóveis como pessoa física passa a ser contribuinte de IBS e CBS: limites de receita e de imóveis, locação por temporada, reduções de 50% e 70% e redutores sociais, com a fonte oficial e uma calculadora de enquadramento.",
            'Aluguel e venda de imóveis: quando a pessoa física <mark class="marca-texto">entra</mark> no IBS e na CBS.',
            "Quem aluga mais de 3 imóveis com receita acima de R$ 240 mil no ano, ou vende imóveis com frequência, passa a ser contribuinte de IBS e CBS mesmo como pessoa física. Veja os limites, as reduções de 50% e 70%, os redutores sociais e faça a conta na calculadora, com a fonte oficial.",
            [("Quem vive de aluguel", "Mais de 3 imóveis alugados e receita acima de R$ 240 mil no ano anterior."),
             ("Quem aluga por temporada", "Locação de até 90 dias segue as regras da hotelaria e entra na conta do limite."),
             ("Quem compra e vende imóveis", "Mais de 3 imóveis vendidos no ano, com menos de 5 anos no patrimônio."),
             ("Quem constrói para vender", "Mais de 1 imóvel construído nos últimos 5 anos vendido no ano.")],
            [("Enquadramento", "Receita de aluguel, imóveis e vendas conferidos ano a ano com os limites do art. 251."),
             ("Comparação", "Pessoa física ou empresa (holding, administradora), com o efeito no IBS, na CBS e no imposto de renda."),
             ("Rotina", "Cadastro, apuração e documentos, se passar a contribuinte."),
             REVISAO_JURIDICA],
            [gp.cartao("Público", "Autônomo e profissional liberal", "Quando a pessoa física vira contribuinte na atividade.", "{p}compliance/publico/autonomo.html"),
             gp.cartao("Público", "Simples Nacional", "A locação de imóveis próprios impede o Simples.", "{p}compliance/publico/simples.html"),
             gp.cartao("Ferramenta", "Termômetro de conformidade", "Perguntas de quem tem imóveis, com a fonte de cada uma.", "{p}compliance/termometro.html#perfil-imoveis")],
            ferramenta=gp.secao("Calculadora", "Você passa a ser contribuinte?", CALC_IMOVEIS, "bg-superficie", "calculadora"))


def termometro() -> None:
    filtros = "".join(f'<label class="og-consentimento"><input type="checkbox" value="{c}" data-filtro-pilar checked><span>{t}</span></label>'
                      for c, t in FILTROS)
    corpo = "\n".join([
        gp.intro("Compliance · Ferramenta", "Termômetro de conformidade",
                 "Escolha o seu caso e responda às perguntas, cada uma com a fonte legal. As respostas ficam só no seu navegador: nada é enviado para a ORGATEC nem para ninguém."),
        f"""        <section class="py-12" data-termometro>
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)] gap-8 items-start">
                <div class="grid gap-6 min-w-0">
                    <fieldset class="og-cartao"><legend class="og-campo-rotulo">Qual é o seu caso?</legend><div class="chips mt-2" data-termometro-perfis></div></fieldset>
                    <fieldset class="og-cartao"><legend class="og-campo-rotulo">Frentes consideradas</legend><div class="flex flex-wrap gap-x-6 gap-y-2 mt-2">{filtros}</div></fieldset>
                    <div class="grid gap-6" data-termometro-perguntas></div>
                </div>
                <aside class="og-cartao termometro-resultado min-w-0" id="resultado" aria-live="polite">
                    <div data-termometro-resultado></div>
                    <div class="flex flex-wrap gap-3 mt-6">
                        <a {gp.WHATS} data-msg="Olá! Fiz o termômetro de conformidade no site da ORGATEC e quero conversar sobre o resultado." class="og-btn og-btn-contato og-btn-md">Conversar sobre o resultado</a>
                        <button type="button" class="og-btn og-btn-contorno og-btn-md" data-termometro-imprimir>Imprimir ou salvar em PDF</button>
                        <button type="button" class="og-btn og-btn-contorno og-btn-md" data-termometro-limpar>Limpar respostas</button>
                    </div>
                    <p class="text-xs text-tinta-fraca mt-4">A mensagem do WhatsApp não leva as suas respostas.</p>
                </aside>
            </div>
            <a href="#resultado" class="termometro-resumo" data-termometro-resumo hidden></a>
            <section class="relatorio-impressao" data-termometro-relatorio aria-hidden="true"></section>
        </section>""",
    ])
    gp.pagina("compliance/termometro.html", "Termômetro de conformidade",
              "Termômetro de conformidade da ORGATEC: perguntas sobre conformidade tributária, prevenção à lavagem de dinheiro, LGPD e integridade, com a fonte legal de cada uma. Roda só no seu navegador.",
              "compliance", "captação", corpo, extra=["compliance-itens.js", "termometro.js", "compliance.js"], barra=False,
              trilha=[("Compliance", "compliance/index.html"), ("Termômetro", None)])


MAPA = [("compliance/index.html", "captação + autoridade"), ("compliance/termometro.html", "captação"),
        ("compliance/conformidade-tributaria.html", "captação + autoridade"), ("compliance/prevencao-lavagem.html", "autoridade"),
        ("compliance/protecao-de-dados.html", "autoridade"), ("compliance/integridade.html", "autoridade"),
        ("compliance/publicos.html", "captação")] + [(f"compliance/publico/{a}", "captação + autoridade") for c, a, _, _ in PUBLICOS if c in PUBLICOS_PRONTOS]


def gerar() -> None:
    visao_geral()
    frentes()
    publicos()
    publicos_paginas()
    termometro()
