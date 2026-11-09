"""Central de Viagem e portal do cliente (site/transporte/central.html e portal.html), Fase 5 de docs/ideias/reestruturacao-transporte.md.

Páginas com noindex, FORA do menu, do hub e do mapa do site até a decisão R4 (login e área do cliente). Os fragmentos de tela vêm de
tools/transporte_modelos/ (a lógica é a do módulo de referência de docs/ideias/anexos/central-viagem-v0.1/). A API só responde com
ORGATEC_TRANSPORTE=1 no servidor; sem isso, a tela mostra o aviso de recurso desligado.
"""
from __future__ import annotations

from pathlib import Path

import gerar_paginas as gp

MODELOS = Path(__file__).resolve().parent / "transporte_modelos"
CSS = '    <link rel="stylesheet" href="{p}assets/css/transporte.css">'
SCRIPTS = ["transporte-comum.js", "transporte-viagem.js"]
NAV = ('<nav class="mb-4 flex gap-2" aria-label="Seções"><a href="central.html" class="og-btn og-btn-{c} og-btn-md">Central</a>'
       '<a href="portal.html" class="og-btn og-btn-{p} og-btn-md">Portal do cliente</a></nav>')


def _pagina(nome: str, titulo: str, descricao: str, ativo_central: bool) -> None:
    frag = (MODELOS / f"{nome}.html.frag").read_text(encoding="utf-8")
    nav = NAV.format(c="primario" if ativo_central else "contorno", p="contorno" if ativo_central else "primario")
    corpo = (f'        <div class="ot max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">\n<p class="eyebrow">Transporte · acesso restrito</p><h1 class="text-3xl font-extrabold my-3">{titulo}</h1>\n'
             f'{nav}\n{frag}\n<p class="fonte mt-4">Estimativas orientativas; confira a fonte indicada em cada item. Posição de veículo é dado pessoal do motorista: acesso restrito à transportadora.</p></div>')
    gp.pagina(f"transporte/{nome}.html", titulo, descricao, None, "retenção", corpo, indexar=False, extra=SCRIPTS + [f"transporte-{nome}.js"],
              head_extra=CSS.replace("{p}", "../"), barra=False)


def gerar() -> None:
    _pagina("central", "Central de Viagem", "Lance uma rota e veja despesas, tempo, bloqueios e clima do trajeto.", True)
    _pagina("portal", "Portal do cliente · Viagens", "Acompanhe viagens, previsão, alertas e posição do veículo em tempo real.", False)
