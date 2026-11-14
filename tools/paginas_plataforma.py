"""Página "Como os sistemas são construídos" (site/solucoes/plataforma.html): mapa por módulo de cada sistema público.

Hoje só o OrgConc. O OrgAudi fica de fora enquanto é de uso interno (decisão de 13/11/2026; "publico" em plataforma_curar.SISTEMAS).
Os textos da página acompanham o número de sistemas: com um só, falam "do sistema de ..."; com mais, "dos sistemas".

Os números vêm de tools/plataforma_grafo.json, que tools/plataforma_curar.py tira do grafo de código do Graphify. O mapa é
desenhado aqui, em SVG estático: a página não carrega script nem biblioteca de grafo (CSP script-src 'self') e funciona
sem JavaScript. Só entram nomes públicos de módulo e contagens; o teste tests/py/test_plataforma.py barra nome de arquivo,
caminho e extensão de código na página.
"""
from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path

import gerar_paginas as gp

DADOS = Path(__file__).resolve().parent / "plataforma_grafo.json"
CAMADAS = ["Entrada", "Regras e serviços", "Leitura e conferência", "Dados e infraestrutura"]
LARG, ALT_NO, ESP_COL, ESP_LIN, MARGEM, TOPO = 210, 58, 270, 84, 16, 34
INFERIDAS_TRACEJADO = 0.3  # acima desta fração de ligações inferidas, a linha sai tracejada


def _mil(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _posicoes(modulos: list[dict]) -> tuple[dict, int]:
    colunas: dict[int, list[dict]] = {}
    for m in modulos:
        colunas.setdefault(m["camada"], []).append(m)
    linhas = max(len(c) for c in colunas.values())
    altura = TOPO + linhas * ESP_LIN + MARGEM
    pos = {}
    for c, ms in colunas.items():
        inicio = TOPO + (linhas - len(ms)) * ESP_LIN / 2
        for i, m in enumerate(ms):
            pos[m["id"]] = (MARGEM + c * ESP_COL, inicio + i * ESP_LIN)
    return pos, int(altura)


def _caminho(a: tuple, b: tuple) -> str:
    (xa, ya), (xb, yb) = a, b
    ya, yb = ya + ALT_NO / 2, yb + ALT_NO / 2
    if xb > xa:  # para a direita: da borda direita à esquerda
        x1, x2 = xa + LARG, xb
        meio = (x1 + x2) / 2
        return f"M{x1:.0f},{ya:.0f} C{meio:.0f},{ya:.0f} {meio:.0f},{yb:.0f} {x2 - 6:.0f},{yb:.0f}"
    if xb < xa:  # para a esquerda: da borda esquerda à direita
        x1, x2 = xa, xb + LARG
        meio = (x1 + x2) / 2
        return f"M{x1:.0f},{ya:.0f} C{meio:.0f},{ya:.0f} {meio:.0f},{yb:.0f} {x2 + 6:.0f},{yb:.0f}"
    x = xa + LARG  # mesma coluna: arco pela direita
    return f"M{x:.0f},{ya:.0f} C{x + 46:.0f},{ya:.0f} {x + 46:.0f},{yb:.0f} {x + 6:.0f},{yb:.0f}"


def mapa_svg(chave: str, sistema: dict) -> str:
    pos, altura = _posicoes(sistema["modulos"])
    nomes = {m["id"]: m["nome"] for m in sistema["modulos"]}
    largura = MARGEM * 2 + (len(CAMADAS) - 1) * ESP_COL + LARG + 50  # folga para os arcos da última coluna
    cabecalho = "".join(f'<text x="{MARGEM + i * ESP_COL + LARG / 2:.0f}" y="16" text-anchor="middle" class="text-tinta-fraca" fill="currentColor" font-size="12">{c}</text>'
                        for i, c in enumerate(CAMADAS))
    arestas = []
    for e in sistema["ligacoes"]:
        inferidas = 1 - e["lidas"] / e["total"]
        tracejado = ' stroke-dasharray="5 4"' if inferidas > INFERIDAS_TRACEJADO else ""
        espessura = 0.8 + 1.2 * math.log10(e["total"])
        titulo = f'{nomes[e["de"]]} → {nomes[e["para"]]}: {e["total"]} ligações, {e["lidas"]} lidas direto no código'
        arestas.append(f'<path d="{_caminho(pos[e["de"]], pos[e["para"]])}" fill="none" stroke="currentColor" stroke-opacity="0.45" '
                       f'stroke-width="{espessura:.1f}"{tracejado} marker-end="url(#seta-{chave})"><title>{escape(titulo)}</title></path>')
    nos = []
    for m in sistema["modulos"]:
        x, y = pos[m["id"]]
        nos.append(f'<rect x="{x}" y="{y:.0f}" width="{LARG}" height="{ALT_NO}" rx="10" style="fill: rgb(var(--surface-rgb))"/>'
                   f'<g class="text-acao"><rect x="{x}" y="{y:.0f}" width="{LARG}" height="{ALT_NO}" rx="10" fill="currentColor" fill-opacity="0.1" '
                   f'stroke="currentColor" stroke-opacity="0.6"><title>{escape(m["nome"])}: {escape(m["texto"])}</title></rect></g>'
                   f'<text x="{x + 12}" y="{y + 24:.0f}" class="text-tinta" fill="currentColor" font-size="14" font-weight="700">{escape(m["nome"])}</text>'
                   f'<text x="{x + 12}" y="{y + 44:.0f}" class="text-tinta-suave" fill="currentColor" font-size="12">{m["arquivos"]} arquivos · {m["simbolos"]} símbolos</text>')
    descricao = f'Mapa por módulo do sistema de {sistema["nome"].lower()}: {len(nos)} módulos e {len(arestas)} ligações. A lista abaixo traz o mesmo conteúdo em texto.'
    return f"""                <figure class="og-cartao overflow-x-auto" data-mapa-plataforma="{chave}">
                    <svg viewBox="0 0 {largura} {altura}" class="w-full min-w-[720px] h-auto text-tinta-suave" role="img" aria-labelledby="t-{chave} d-{chave}">
                        <title id="t-{chave}">{escape(sistema["nome"])}: mapa dos módulos</title>
                        <desc id="d-{chave}">{escape(descricao)}</desc>
                        <defs><marker id="seta-{chave}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
                        {cabecalho}
                        {"".join(arestas)}
                        {"".join(nos)}
                    </svg>
                    <figcaption class="text-xs text-tinta-fraca mt-3">Linha cheia: ligações lidas direto no código. Tracejada: mais de {int(INFERIDAS_TRACEJADO * 100)}% delas deduzidas pela ferramenta. Quanto mais grossa, mais ligações. Passe o mouse para ver os números; no celular, arraste o mapa para o lado.</figcaption>
                </figure>"""


def lista_texto(sistema: dict) -> str:
    nomes = {m["id"]: m["nome"] for m in sistema["modulos"]}
    modulos = "".join(f'<li><strong class="text-tinta">{escape(m["nome"])}</strong> ({m["arquivos"]} arquivos): {escape(m["texto"])}</li>' for m in sistema["modulos"])
    ligacoes = "".join(f'<tr class="border-b border-linha"><td class="py-1 pr-4">{escape(nomes[e["de"]])}</td><td class="py-1 pr-4">{escape(nomes[e["para"]])}</td>'
                       f'<td class="py-1 pr-4 text-right">{e["total"]}</td><td class="py-1 text-right">{e["lidas"]}</td></tr>' for e in sistema["ligacoes"])
    return f"""                <details class="mt-4 text-sm text-tinta-suave">
                    <summary class="cursor-pointer og-link">Ver o mapa em texto</summary>
                    <ul class="mt-3 grid gap-1 list-disc pl-5">{modulos}</ul>
                    <div class="overflow-x-auto mt-4"><table class="w-full text-left min-w-[480px]"><thead><tr class="text-xs uppercase text-tinta-fraca border-b border-linha">
                        <th class="py-2 pr-4">De</th><th class="py-2 pr-4">Para</th><th class="py-2 pr-4 text-right">Ligações</th><th class="py-2 text-right">Lidas no código</th></tr></thead>
                        <tbody>{ligacoes}</tbody></table></div>
                </details>"""


def gerar() -> None:
    dados = json.loads(DADOS.read_text(encoding="utf-8"))
    secoes = []
    for i, (chave, s) in enumerate(dados["sistemas"].items()):
        total = sum(e["total"] for e in s["ligacoes"])
        lidas = sum(e["lidas"] for e in s["ligacoes"])
        arquivos = sum(m["arquivos"] for m in s["modulos"])
        resumo = (f'                <p class="text-tinta-suave mb-6 max-w-3xl">{arquivos} arquivos de código em {len(s["modulos"])} módulos. '
                  f'Das {_mil(total)} ligações entre módulos, {round(100 * lidas / total)}% foram lidas direto no código e o restante deduzido pela ferramenta. '
                  f'<a class="og-link" href="{{p}}{s["pagina"]}">Conhecer a solução →</a></p>')
        secoes.append(gp.secao("Mapa do sistema", s["nome"], resumo + "\n" + mapa_svg(chave, s) + "\n" + lista_texto(s),
                               "bg-superficie" if i % 2 else "bg-fundo", f"mapa-{chave}"))
    varios = len(dados["sistemas"]) > 1
    nomes = " e ".join(s["nome"].lower() for s in dados["sistemas"].values())
    corpo = "\n".join([
        gp.intro("Soluções · Por dentro", "Como os sistemas da ORGATEC são construídos",
                 ("Um mapa de cada sistema" if varios else f"Um mapa do sistema de {nomes}")
                 + ", módulo por módulo: o que cada parte faz e com quais outras ela conversa. "
                 "É o mesmo mapa que a equipe usa para revisar e evoluir o código."),
        *secoes,
        gp.secao("Como este mapa é feito", "Lido do código, sem inteligência artificial", gp.lista([
            ("Leitura do código-fonte", f'A ferramenta de código aberto Graphify (versão {escape(dados["graphify"])}) lê o código-fonte e monta o grafo de quem chama, importa ou herda de quem. Nessa leitura nenhum modelo de IA é usado e nenhum código sai do escritório.'),
            ("Só o nível de módulo", "Nomes de arquivos, funções e tabelas ficam de fora. A página mostra apenas os módulos, quantos arquivos têm e quantas ligações existem entre eles."),
            ("Lido ou deduzido", "Cada ligação é marcada como lida no código ou deduzida pela ferramenta. As deduzidas aparecem tracejadas quando são muitas."),
            ("Limite conhecido", "A ferramenta ainda deixa passar algumas chamadas entre classes herdadas, então o número real de ligações pode ser um pouco maior. O mapa mostra a estrutura, não prova que o sistema está correto."),
        ]), "bg-superficie" if len(secoes) % 2 else "bg-fundo", "metodo"),
        f'                <p class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs text-tinta-fraca" data-plataforma-data>Mapa gerado em {dados["gerado"]}.</p>',
        gp.faixa_solucao("Quer ver um desses sistemas funcionando?" if varios else "Quer ver o sistema funcionando?",
                         "Na demonstração, a equipe mostra o sistema com dados fictícios.",
                         "Olá! Quero ver uma demonstração dos sistemas da ORGATEC." if varios
                         else f"Olá! Quero ver uma demonstração do sistema de {nomes} da ORGATEC.", "Solicitar demonstração"),
    ])
    gp.pagina("solucoes/plataforma.html", "Como os sistemas são construídos",
              f"Mapa por módulo dos sistemas da ORGATEC ({nomes}), lido do código-fonte." if varios
              else f"Mapa por módulo do sistema de {nomes} da ORGATEC, lido do código-fonte.",
              "solucoes", "autoridade", corpo, trilha=[("Soluções", "solucoes/index.html"), ("Como os sistemas são construídos", None)])
