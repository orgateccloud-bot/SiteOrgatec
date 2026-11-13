"""Painel do grupo LOCAR (site/locar/painel.html). docs/ideias/locar-painel.md.

Página com `noindex`, fora do menu e do mapa do site. A página é só estrutura: nenhum dado do grupo mora no HTML nem nos scripts.
Tudo chega pela API (/api/locar, só com ORGATEC_LOCAR=1) depois do login. Está em /locar/ porque só esse caminho ganha uma CSP que
deixa o navegador falar com o Firebase Authentication (backend/app.py: CSP_LOCAR; firebase.json); o resto do site continua só com 'self'.
"""
from __future__ import annotations

import gerar_paginas as gp

CSS = '    <link rel="stylesheet" href="{p}assets/css/locar.css">'
SCRIPTS = ["login-comum.js", "locar-agenda.js", "locar-modelos.js", "locar.js"]

CORPO = """        <div class="lc max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div id="lcAcesso" class="lc-acesso" hidden></div>
            <div id="lcMsg" aria-live="polite"></div>
            <div id="lcPainel" hidden>
                <header id="lcCabeca" class="lc-cabeca"></header>
                <div id="lcKpis" class="lc-kpis"></div>
                <section class="lc-operacao" aria-labelledby="lcTitOperacao">
                    <h2 id="lcTitOperacao" class="lc-h2">Operação do grupo</h2>
                    <div class="lc-op-grade">
                        <article class="lc-cartao lc-op-tempo"><h3>Tempo nas regiões do grupo</h3><div id="lcTempo"><p class="lc-nota">Carregando a Janela de Campo…</p></div>
                            <p class="lc-op-link"><a href="{p}rural/janela-de-campo.html">Abrir a Janela de Campo</a></p></article>
                        <article class="lc-cartao"><h3>Alertas nas rodovias</h3><div id="lcAlertas"><p class="lc-nota">Carregando os alertas…</p></div>
                            <p class="lc-op-link"><a href="{p}empresarial/janela.html#alertas-rodovias">Ver o mapa de alertas</a></p></article>
                        <article class="lc-cartao"><h3>Central de Viagem</h3>
                            <p class="lc-nota">Lance a rota e veja despesas, tempo de viagem, bloqueios e o clima no trajeto. Usa o mesmo login deste painel; o acesso da transportadora é liberado pela ORGATEC.</p>
                            <p class="lc-op-acoes"><a class="lc-btn" href="{p}transporte/central.html">Abrir a Central</a><a class="lc-btn lc-btn-sec" href="{p}transporte/portal.html">Portal de viagens</a></p></article>
                    </div>
                </section>
                <div id="lcFiltros" class="lc-filtros"></div>
                <div class="lc-grade">
                    <section aria-labelledby="lcTitAgenda">
                        <h2 id="lcTitAgenda" class="lc-h2">Agenda</h2>
                        <div id="lcAgenda"></div>
                    </section>
                    <aside class="lc-lateral" aria-label="Entidades e marcos">
                        <section aria-labelledby="lcTitEntidades">
                            <h2 id="lcTitEntidades" class="lc-h2">Entidades</h2>
                            <div id="lcEntidades" class="lc-entidades"></div>
                        </section>
                        <details id="lcAdicionar" class="lc-cartao" hidden></details>
                        <section aria-labelledby="lcTitMarcos">
                            <h2 id="lcTitMarcos" class="lc-h2">Marcos da reforma</h2>
                            <ul id="lcMarcos" class="lc-marcos"></ul>
                            <details class="lc-cartao">
                                <summary>Transição 2026 a 2033</summary>
                                <div class="overflow-x-auto">
                                    <table class="lc-tabela">
                                        <thead><tr><th>Ano</th><th>CBS</th><th>IBS</th><th>PIS/Cofins</th><th>IPI</th><th>ICMS e ISS</th></tr></thead>
                                        <tbody data-linha-tempo></tbody>
                                    </table>
                                </div>
                                <p class="lc-nota">Fonte: ADCT, arts. 125 a 129 (EC nº 132/2023).</p>
                            </details>
                        </section>
                        <details id="lcAuditoria" class="lc-cartao" hidden></details>
                    </aside>
                </div>
            </div>
            <p class="lc-rodape">Conteúdo orientativo, com fonte oficial em cada item; não substitui parecer técnico do contador responsável. Itens “em revisão técnica” ainda não foram aprovados.
                Documentos e guias ficam no <a href="{p}cliente/locar.html">portal do cliente</a>. Posição e dados pessoais de produtores são restritos à equipe e aos titulares.</p>
        </div>"""


def gerar() -> None:
    gp.pagina("locar/painel.html", "Painel do grupo LOCAR", "Agenda de obrigações e da transição da reforma tributária por entidade, com acesso restrito.",
              None, "retenção", CORPO, indexar=False, extra=SCRIPTS, head_extra=CSS.replace("{p}", "../"), barra=False,
              trilha=[("Área do cliente", "cliente/index.html"), ("Módulo LOCAR", "cliente/locar.html"), ("Painel", None)])
