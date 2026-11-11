"""Testes de ponta a ponta (Playwright + Chromium) contra o backend real servindo o site.

Executar:  python -m pytest tests/e2e -q   (sobe o uvicorn numa porta livre automaticamente)
"""

import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright

RAIZ = Path(__file__).resolve().parents[2]
VIEWPORTS = {"mobile": (375, 812), "tablet": (768, 1024), "desktop": (1440, 900)}
UFS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
       "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def servidor(tmp_path_factory):
    porta = _porta_livre()
    env = {**os.environ, "ORGATEC_DB": str(tmp_path_factory.mktemp("db") / "e2e.db"),
           "ORGATEC_SEGREDO_IP": "e2e", "ORGATEC_RATE_LIMIT": "500", "ORGATEC_SERVIR_SITE": "1"}
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app:app", "--port", str(porta), "--log-level", "warning"],
                            cwd=RAIZ, env=env)
    url = f"http://127.0.0.1:{porta}"
    for _ in range(60):
        try:
            if httpx.get(url + "/api/saude").status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.25)
    yield url
    proc.terminate()
    proc.wait(10)


# T6: ORGATEC_NAVEGADOR=firefox ou webkit (motor do Safari) roda a mesma suíte em outro navegador.
NAVEGADOR = os.environ.get("ORGATEC_NAVEGADOR", "chromium")


@pytest.fixture(scope="session")
def navegador():
    with sync_playwright() as p:
        b = getattr(p, NAVEGADOR).launch()
        yield b
        b.close()


@pytest.fixture(autouse=True)
def _fechar_contextos(request):
    """Fecha as abas de cada teste: com dezenas de contextos abertos, o Chromium perde estabilidade no fim da suíte."""
    yield
    if "navegador" in request.fixturenames:
        for ctx in list(request.getfixturevalue("navegador").contexts):
            ctx.close()


SIMULADOR, CALENDARIO, CONTATO, CLIENTE = "ferramentas/simulador.html", "ferramentas/calendario.html", "contato/index.html", "cliente/index.html"
ESPERA = {SIMULADOR: "#simSector option", CALENDARIO: "#calLista li", CLIENTE: "#xmlTabela tr"}


def _pagina(navegador, servidor, vp="desktop", caminho=SIMULADOR):
    """Abre uma página e espera o app.js ligar o bloco dela (o simulador, por padrão)."""
    w, h = VIEWPORTS[vp]
    ctx = navegador.new_context(viewport={"width": w, "height": h})
    pg = ctx.new_page()
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto(f"{servidor}/{caminho}")
    if caminho in ESPERA:
        pg.wait_for_selector(ESPERA[caminho], state="attached")
    else:
        pg.wait_for_load_state("load")
    return pg, erros


@pytest.mark.parametrize("vp", list(VIEWPORTS))
def test_responsivo_sem_rolagem_horizontal_e_sem_erros(navegador, servidor, vp):
    pg, erros = _pagina(navegador, servidor, vp, "inicio.html")
    largura = pg.evaluate("document.documentElement.scrollWidth")
    assert largura <= VIEWPORTS[vp][0], f"rolagem horizontal em {vp}: {largura}px"
    # Menu: hambúrguer abaixo de xl (1280px), navegação completa acima.
    if vp == "desktop":
        expect(pg.locator("nav[aria-label=Principal]")).to_be_visible()
        expect(pg.locator("#btnMenu")).to_be_hidden()
    else:
        expect(pg.locator("#btnMenu")).to_be_visible()
        pg.click("#btnMenu")
        expect(pg.locator("#menuMobile")).to_be_visible()
        pg.click("#menuMobile a[href='ferramentas/calendario.html']")
        pg.wait_for_url("**/ferramentas/calendario.html")
        expect(pg.locator("#menuMobile")).to_be_hidden()
        pg.go_back()
    # CTAs preservados
    expect(pg.get_by_text("Testar Simulador Tributário").first).to_be_visible()
    assert pg.locator("a[href^='https://wa.me/5562992949161']").count() >= 3
    assert "Não substitui parecer técnico" in pg.content()
    pg.screenshot(path=str(RAIZ / "tests" / "e2e" / f"screenshot-{vp}.png"), full_page=True)
    assert not erros, erros


def test_simulador_27_ufs_pela_interface(navegador, servidor):
    pg, erros = _pagina(navegador, servidor)
    assert pg.locator("#simUf option").count() == 27
    for uf in UFS:
        pg.select_option("#simUf", uf)
        pg.fill("#simFaturamento", "2.400.000")
        pg.click("#btnSimular")
        expect(pg.locator("#simResult")).to_be_visible()
        assert pg.locator("#resultAlertas li").count() >= 1, uf
        assert "OUTRAS" not in pg.inner_text("#resultText")
    assert not erros, erros


def test_simulador_valida_faturamento(navegador, servidor):
    pg, _ = _pagina(navegador, servidor)
    pg.fill("#simFaturamento", "")
    pg.click("#btnSimular")
    expect(pg.locator("#simErro")).to_be_visible()


def test_fluxo_lead_exige_consentimento_e_envia(navegador, servidor):
    pg, erros = _pagina(navegador, servidor, "mobile")
    pg.select_option("#simRegime", "simples")
    pg.fill("#simFaturamento", "1.200.000")
    pg.click("#btnSimular")
    pg.fill("#leadNome", "Teste E2E")
    pg.fill("#leadWhats", "(62) 99999-0000")
    pg.click("#leadForm button[type=submit]")
    expect(pg.locator("#leadMsg")).to_contain_text("autorizar")
    pg.check("#leadConsent")
    pg.click("#leadForm button[type=submit]")
    expect(pg.locator("#leadMsg")).to_contain_text("Protocolo LD-")
    href = pg.get_attribute("#ctaWhatsSim", "href")
    assert "Teste" not in href and "99999" not in href  # nada de dado pessoal na URL
    assert not erros, erros


def test_fluxo_optin(navegador, servidor):
    pg, erros = _pagina(navegador, servidor, "tablet", CALENDARIO)
    pg.click("#optinForm button[type=submit]")
    expect(pg.locator("#optMsg")).to_contain_text("e-mail ou WhatsApp")
    pg.fill("#optEmail", "email-invalido")
    pg.click("#optinForm button[type=submit]")
    expect(pg.locator("#optMsg")).to_contain_text("E-mail inválido")
    pg.fill("#optEmail", "cliente@empresa.com.br")
    pg.select_option("#optUfs", ["GO", "TO", "PA"])
    pg.click("#optinForm button[type=submit]")
    expect(pg.locator("#optMsg")).to_contain_text("aceitar")
    pg.check("#optConsent")
    pg.click("#optinForm button[type=submit]")
    expect(pg.locator("#optMsg")).to_contain_text("protocolo OP-")
    assert not erros, erros


def test_fluxo_contato(navegador, servidor):
    pg, erros = _pagina(navegador, servidor, caminho=CONTATO)
    pg.fill("#ctNome", "Contato E2E")
    pg.fill("#ctEmail", "c@ex.com")
    pg.fill("#ctMensagem", "curta")
    pg.check("#ctConsent")
    pg.click("#contatoForm button[type=submit]")
    expect(pg.locator("#ctMsg")).to_contain_text("10 caracteres")
    pg.fill("#ctMensagem", "Gostaria de um diagnóstico do Simples Híbrido.")
    pg.click("#contatoForm button[type=submit]")
    expect(pg.locator("#ctMsg")).to_contain_text("Protocolo CT-")
    assert not erros, erros


def test_fallback_sem_backend_oferece_whatsapp(navegador, servidor):
    pg, _ = _pagina(navegador, servidor, caminho=CONTATO)
    pg.route("**/api/contato", lambda r: r.abort())
    pg.fill("#ctNome", "Sem Backend")
    pg.fill("#ctWhats", "62999990000")
    pg.fill("#ctMensagem", "Mensagem quando a API está fora do ar.")
    pg.check("#ctConsent")
    pg.click("#contatoForm button[type=submit]")
    expect(pg.locator("#ctMsg a[href^='https://wa.me/']")).to_be_visible()


def test_calendario_e_ics(navegador, servidor):
    pg, erros = _pagina(navegador, servidor, caminho=CALENDARIO)
    pg.fill("#calMes", "2026-12")
    pg.dispatch_event("#calMes", "change")
    assert pg.locator("#calLista li[data-obrigacao=decimo2]").count() == 1
    for uf in UFS:
        pg.select_option("#calUf", uf)
        assert pg.locator(f"#calLista li[data-obrigacao^='{uf}_']").count() >= 1, uf
    with pg.expect_download() as d:
        pg.click("#btnIcs")
    assert d.value.suggested_filename.endswith(".ics")
    assert not erros, erros


def test_demos_homologacao_e_pendencias(navegador, servidor):
    pg, _ = _pagina(navegador, servidor, caminho=CLIENTE)
    assert pg.locator("#xmlTabela tr").count() == 4
    assert pg.locator("#portalTabela tr").count() == 4
    txt = pg.inner_text("#portalTabela")
    assert "177.18.***.***" in txt and "177.18.22.90" not in txt
    expect(pg.locator("#faixaHomologacao")).to_be_visible()
    expect(pg.locator("#xmlFerramenta")).to_contain_text("pendente")
    expect(pg.locator("#portalErp")).to_contain_text("Athenas Online")
    for a in pg.locator("[data-link='portal']").all():  # portal.orgatec.io ainda sem DNS (T5)
        assert a.get_attribute("href").startswith("https://orgatec.athenas.online/")
    expect(pg.locator("#rodapeEmails a[href='mailto:dpo@orgatec.io']")).to_be_visible()  # canal do encarregado no rodapé


@pytest.mark.parametrize("pagina", ["inicio.html", "privacidade.html", "marca.html", "orgatec-template2.html", "reforma/simples-hibrido.html", "reforma/index.html", "consultoria-tributaria.html"])
@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_logotipo_e_nome_orgatec(navegador, servidor, pagina, vp):
    w, h = VIEWPORTS[vp]
    pg = navegador.new_context(viewport={"width": w, "height": h}).new_page()
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto(f"{servidor}/{pagina}")
    pg.wait_for_load_state("load")  # não espera a rede externa (CDN e fontes) ficar ociosa
    logo = pg.locator("header img[src*='orgatec-original']").first
    expect(logo).to_be_visible()
    assert pg.evaluate("(i) => i.complete && i.naturalWidth > 0", logo.element_handle()), "logo não carregou"
    texto = pg.inner_text("body")
    assert "ORGATEC" in pg.inner_text("header")
    # Nome da marca sem ".IO" (marca e design system citam "Orgatec.IO" apenas como exemplo do que não fazer)
    if pagina not in ("marca.html", "orgatec-template2.html"):
        assert ".IO" not in texto
    assert pg.evaluate("document.documentElement.scrollWidth") <= w
    assert pg.locator("link[rel=icon][href$='favicon-32.png']").count() == 1
    assert not erros, erros


@pytest.mark.parametrize("tema", ["claro", "escuro"])
def test_design_system_html(navegador, servidor, tema):
    pg = navegador.new_context(viewport={"width": 375, "height": 812}, color_scheme="dark" if tema == "escuro" else "light").new_page()
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto(f"{servidor}/orgatec-template2.html")
    pg.wait_for_load_state("load")  # não espera a rede externa (CDN e fontes) ficar ociosa
    assert pg.locator(".ds-cor").count() == 38  # um bloco por token de cor
    assert pg.locator(".ds-comp").count() == 7
    assert pg.locator(".og-selo-pendente").count() >= 1
    for img in pg.locator(".ds-arquivo img").all():
        assert img.evaluate("(i) => i.complete && i.naturalWidth > 0"), img.get_attribute("src")
    fundo = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    assert fundo == ("rgb(15, 23, 42)" if tema == "escuro" else "rgb(248, 250, 252)")
    pg.click("#btnTema")  # automático -> claro
    assert pg.evaluate("document.documentElement.dataset.theme") == "claro"
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    pg.screenshot(path=str(RAIZ / "tests" / "e2e" / f"screenshot-ds-{tema}.png"), full_page=True)
    assert not erros, erros


PAGINAS_NOVAS = ["compliance/index.html", "compliance/conformidade-tributaria.html", "compliance/prevencao-lavagem.html",
                 "compliance/protecao-de-dados.html", "compliance/integridade.html", "compliance/termometro.html",
                 "compliance/publicos.html", "compliance/publico/transportador.html", "compliance/publico/produtor-rural.html", "compliance/publico/mei.html", "compliance/publico/autonomo.html", "compliance/publico/simples.html", "compliance/publico/comercio-industria.html", "compliance/publico/servicos.html", "compliance/publico/imoveis.html", "solucoes/index.html", "solucoes/conciliacao.html", "solucoes/auditoria-rural.html", "consultoria-tributaria.html", "reforma/index.html", "rural/index.html", "empresarial/transporte.html", "reforma/alertas-regionais.html",
                 "rural/janela-de-campo.html", "rural/cotacoes.html",
                 "ferramentas/index.html", SIMULADOR, CALENDARIO, CLIENTE, "cliente/locar.html", "quem-somos.html", CONTATO]


def _abrir(navegador, servidor, caminho, vp="desktop", rotas=None):
    w, h = VIEWPORTS[vp]
    pg = navegador.new_context(viewport={"width": w, "height": h}).new_page()
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    for padrao, f in (rotas or {}).items():
        pg.route(padrao, f)
    pg.goto(f"{servidor}/{caminho}")
    pg.wait_for_load_state("load")  # não espera a rede externa (CDN e fontes) ficar ociosa
    return pg, erros


def _config_alterada(substituicoes):
    texto = (RAIZ / "site" / "assets" / "js" / "config.js").read_text(encoding="utf-8")
    for a, b in substituicoes:
        assert a in texto
        texto = texto.replace(a, b)
    return lambda rota: rota.fulfill(status=200, content_type="application/javascript", body=texto)


@pytest.mark.parametrize("caminho", PAGINAS_NOVAS)
@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_paginas_novas_responsivas_e_sem_erro(navegador, servidor, caminho, vp):
    pg, erros = _abrir(navegador, servidor, caminho, vp)
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert pg.get_attribute("main", "data-objetivo")  # cada página declara o objetivo
    expect(pg.locator("header img[src*='orgatec-original']")).to_be_visible()
    assert "ORGATEC" in pg.inner_text("header")
    assert pg.locator("a[href^='https://wa.me/5562992949161']").count() >= 1
    assert "NBC PG 01" in pg.inner_text("footer")
    if vp == "mobile":
        pg.click("#btnMenu")
        expect(pg.locator("#menuMobile")).to_be_visible()
    assert not erros, erros


def test_central_da_reforma_filtros_e_fontes(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "reforma/index.html")
    total = pg.evaluate("window.Orgatec.reformaItens.length")
    itens = pg.locator("#itens .og-item")
    assert itens.count() == total >= 30
    assert pg.locator("#itens .og-item .og-link").count() >= total  # toda afirmação com fonte clicável
    em_31 = pg.evaluate("window.Orgatec.reformaItens.filter(i => i.consultadoEm === '2026-10-31').length")
    assert pg.locator("#itens .og-item-meta", has_text="Consultado em 31/10/2026").count() == em_31 >= total - 2  # itens conferidos depois (ex.: cashback) têm a própria data
    assert pg.locator("[data-linha-tempo] tr").count() == 8
    assert pg.locator("[data-noticias] li").count() == 8
    pg.select_option("#fSetor", "transporte")
    for s in pg.locator("#itens .og-item").evaluate_all("els => els.map(e => e.dataset.setores)"):
        assert "transporte" in s or "todos" in s
    pg.select_option("#fStatus", "pendente_regulamentacao")
    for st in pg.locator("#itens .og-item").evaluate_all("els => els.map(e => e.dataset.status)"):
        assert st == "pendente_regulamentacao"
    assert not erros, erros


def test_producao_esconde_itens_sem_revisao(navegador, servidor):
    rota = _config_alterada([("ambiente: 'homologacao'", "ambiente: 'producao'")])
    pg, erros = _abrir(navegador, servidor, "reforma/index.html", rotas={"**/assets/js/config.js": rota})
    assert pg.locator("#itens .og-item").count() == 0
    expect(pg.locator("#itens")).to_contain_text("aguardando revisão técnica")
    expect(pg.locator("#faixaHomologacao")).to_be_hidden()
    assert not erros, erros


def test_anos_de_atuacao_so_com_comprovacao(navegador, servidor):
    pg, _ = _abrir(navegador, servidor, "quem-somos.html")
    expect(pg.locator("[data-prova-anos]").first).to_be_hidden()
    assert "51 anos" not in pg.inner_text("body")
    rota = _config_alterada([("inicioAtuacao: null", "inicioAtuacao: '1975-01-02'"), ("comprovacao: null", "comprovacao: 'teste e2e'")])
    pg2, erros = _abrir(navegador, servidor, "quem-somos.html", rotas={"**/assets/js/config.js": rota})
    expect(pg2.locator("[data-prova-anos]").first).to_be_visible()
    assert re.search(r"\d+ anos de atuação", pg2.inner_text("main"))
    assert not erros, erros


def test_calculadoras(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "ferramentas/index.html", "mobile")
    pg.select_option("#tAno", "2030")
    pg.fill("#tIcms", "1.000.000")
    pg.click("#formTransicao button[type=submit]")
    expect(pg.locator("#tResultado")).to_contain_text("80%")
    expect(pg.locator("#tResultado")).to_contain_text("800.000,00")
    pg.fill("#tIcms", "-5")
    pg.click("#formTransicao button[type=submit]")
    expect(pg.locator("#tResultado [role=alert]")).to_be_visible()
    pg.fill("#pReceita", "3.200.000")
    pg.click("#formProdutor button[type=submit]")
    expect(pg.locator("#pResultado")).to_contain_text("Não contribuinte")
    pg.fill("#pReceita", "5.000.000")
    pg.fill("#pMesExcesso", "4")
    pg.click("#formProdutor button[type=submit]")
    expect(pg.locator("#pResultado")).to_contain_text("junho do mesmo ano")
    pg.fill("#pReceita", "")
    pg.click("#formProdutor button[type=submit]")
    expect(pg.locator("#pResultado [role=alert]")).to_be_visible()
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def test_setor_agro_e_a_entrada_do_produtor_rural(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "rural/index.html")
    pg.wait_for_selector("#tributos .og-item")
    caminhos = pg.locator("[data-agro-caminho]")
    assert caminhos.count() == 4
    hrefs = caminhos.evaluate_all("els => els.flatMap(e => [...e.querySelectorAll('a')].map(a => a.getAttribute('href')))")
    assert hrefs == ["../rural/janela-de-campo.html", "../rural/cotacoes.html", "#tributos", "../solucoes/auditoria-rural.html"]
    # chamadas claras: a calculadora e a auditoria rural, mais o compliance e os alertas do setor
    passos = pg.locator("#proximos-passos a").evaluate_all("els => els.map(a => a.getAttribute('href'))")
    for esperado in ["../ferramentas/index.html#produtor", "../solucoes/auditoria-rural.html", "../compliance/publico/produtor-rural.html",
                     "../reforma/alertas-regionais.html?setor=agro"]:
        assert esperado in passos, esperado
    assert pg.locator("#tributos [data-itens]").count() == 1  # o caminho "Tributos" leva à lista de pontos da reforma
    # os alertas ficam numa página só: aqui não há mais a lista nem o seletor de estado
    assert pg.locator("#aUf, .lista-alertas").count() == 0
    expect(pg.locator("a[data-alertas-agro]")).to_have_attribute("href", "../reforma/alertas-regionais.html?setor=agro")
    assert not erros, erros


def test_alertas_regionais_abrem_no_setor_e_estado_do_link(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "reforma/alertas-regionais.html?setor=agro&uf=TO")
    expect(pg.locator("#tabsSetor button.tab-ativa")).to_have_text("Agronegócio")
    expect(pg.locator("#tabsUf button.tab-ativa")).to_have_text("Tocantins")
    assert pg.locator("#listaRegional li").count() >= 1
    pg2, erros2 = _abrir(navegador, servidor, "reforma/alertas-regionais.html?setor=inexistente&uf=XX")  # valor inválido: volta ao padrão
    expect(pg2.locator("#tabsUf button.tab-ativa")).to_have_text("Goiás")
    assert pg2.locator("#listaRegional li").count() >= 1
    assert not erros and not erros2, (erros, erros2)


def test_home_ultimas_da_reforma_e_simulador_pre_selecionado(navegador, servidor):
    pg, erros = _pagina(navegador, servidor, caminho="inicio.html")
    assert pg.locator("#ultimas [data-noticias] li").count() == 3
    expect(pg.locator("[data-prova-anos]")).to_be_hidden()
    # endereço antigo da home (links já compartilhados) leva ao simulador com o setor escolhido
    pg.goto(servidor + "/index.html?setor=agro#simulador")
    pg.wait_for_url("**/ferramentas/simulador.html?setor=agro")
    pg.wait_for_selector("#simSector option", state="attached")
    assert pg.input_value("#simSector") == "agro"
    pg.goto(servidor + "/#calendario")
    pg.wait_for_url("**/ferramentas/calendario.html")
    assert not erros, erros


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_painel_de_testes(navegador, servidor, vp):
    pg, erros = _abrir(navegador, servidor, "testes/index.html", vp)
    assert pg.locator("meta[name=robots][content=noindex]").count() == 1
    casos = pg.locator("[data-autoteste] li")
    # O autoteste preenche a lista depois do carregamento: espera o 12º caso antes de contar (no celular, numa
    # máquina ocupada pela suíte, a contagem imediata já deu 0 e barrou uma publicação em 08/11/2026).
    expect(casos.nth(11)).to_be_attached(timeout=15000)
    assert casos.count() >= 12
    assert pg.locator("[data-autoteste] li[data-ok=false]").count() == 0, pg.inner_text("[data-autoteste]")
    expect(pg.locator("[data-resumo=ambiente]")).to_have_text("Homologação")
    abertas = pg.locator("[data-pendencias] article").count()
    assert abertas >= 20 and pg.locator("[data-pendencias] article[data-status=resolvida]").count() == 0
    pg.check("#pdBloqueia")
    bloqueios = pg.locator("[data-pendencias] article").count()
    assert 0 < bloqueios < abertas
    assert pg.locator("[data-pendencias] article[data-bloqueia=false]").count() == 0
    pg.select_option("#pdStatus", "")
    pg.uncheck("#pdBloqueia")
    assert pg.locator("[data-pendencias] article").count() > abertas  # inclui as resolvidas (V8)
    assert pg.locator("tbody a.og-link").count() == 39  # mapa de páginas
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


def test_painel_reflete_configuracao(navegador, servidor):
    rota = _config_alterada([("validado: false\n    },", "validado: true\n    },")])
    pg, erros = _abrir(navegador, servidor, "testes/index.html", rotas={"**/assets/js/config.js": rota})
    pg.select_option("#pdStatus", "")
    expect(pg.locator("#pendencia-C5")).to_have_attribute("data-status", "resolvida")
    expect(pg.locator("#pendencia-C1")).to_have_attribute("data-status", "aberta")
    assert not erros, erros


def test_faixa_de_homologacao_leva_ao_painel(navegador, servidor):
    pg, _ = _abrir(navegador, servidor, "consultoria-tributaria.html")
    expect(pg.locator("#faixaHomologacao a[href$='testes/index.html']")).to_be_visible()


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_design_orgatec_trilha(navegador, servidor, vp):
    pg, erros = _abrir(navegador, servidor, "orgatec-trilha.html", vp)
    texto = pg.inner_text("body")
    assert "ORGATEC" in pg.inner_text("header")
    assert "trilhum" not in texto.lower()
    assert pg.locator("meta[name=robots][content=noindex]").count() == 1
    assert pg.locator("#paletas .pre").count() == 8
    # padrão do site: Azul flutuante (claro, com estilo flutuante)
    assert pg.evaluate("document.documentElement.dataset.float") == "light"
    assert pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--bg').trim().toLowerCase()") == "#eaf1fb"
    pg.click("#paletas [data-t=verde]")
    assert pg.evaluate("document.documentElement.dataset.float") is None
    assert pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--brand').trim().toLowerCase()") == "#1f4d40"
    expect(pg.locator("#toast")).to_contain_text("Cores: Verde Toga")
    assert pg.locator("#tabTokens tr").count() == 15
    pg.click("#btnApagar")
    expect(pg.locator("#btnApagar")).to_contain_text("Confirmar")
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


@pytest.mark.parametrize("caminho", ["inicio.html", "consultoria-tributaria.html", "reforma/ibs.html", "privacidade.html"])
def test_seletor_de_cores_do_design_trilha(navegador, servidor, caminho):
    ctx = navegador.new_context(viewport={"width": 375, "height": 812})
    pg = ctx.new_page()
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto(f"{servidor}/{caminho}")
    pg.wait_for_load_state("load")  # não espera a rede externa (CDN e fontes) ficar ociosa
    cor = lambda v: pg.evaluate(f"getComputedStyle(document.documentElement).getPropertyValue('{v}').trim().toLowerCase()")
    # padrão: Azul flutuante escuro (escolha de 02/11/2026), estilo flutuante e símbolo colorido
    assert pg.get_attribute("html", "data-tema") == "azul-fl-esc"
    assert pg.get_attribute("html", "data-float") == "dark"
    assert cor("--bg") == "#08111f" and cor("--brand") == "#6ea8ff"
    assert pg.get_attribute("header img", "src").endswith("orgatec-original.png")
    pg.click("#btnCores")
    expect(pg.locator("#temaPop")).to_be_visible()
    assert pg.locator("#temaPop [data-tema-id]").count() == 8
    expect(pg.locator("#temaPop [data-tema-id=azul-fl-esc]")).to_have_attribute("aria-pressed", "true")
    pg.click("#temaPop [data-tema-id=verde]")
    assert cor("--bg") == "#f3f5f2" and cor("--brand") == "#1f4d40"
    assert pg.get_attribute("html", "data-float") is None
    expect(pg.locator(".tema-toast")).to_contain_text("Cores: Verde Toga")
    pg.click("#temaPop [data-tema-id=azul-fl-esc]")  # paleta escura: o símbolo continua colorido
    assert cor("--bg") == "#08111f" and pg.get_attribute("html", "data-float") == "dark"
    assert pg.get_attribute("header img", "src").endswith("orgatec-original.png")  # cores originais também no escuro
    if pg.locator("footer img").count():  # a política de privacidade não tem símbolo no rodapé
        assert pg.get_attribute("footer img", "src").endswith("orgatec-original.png")
    pg.click("#temaPop [data-tema-id=verde]")
    pg.keyboard.press("Escape")
    expect(pg.locator("#temaPop")).to_be_hidden()
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    # a escolha vale nas outras páginas
    pg.goto(f"{servidor}/ferramentas/index.html")
    assert pg.get_attribute("html", "data-tema") == "verde"
    assert not erros, erros


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_pagina_inicial_interativa(navegador, servidor, vp):
    pg, erros = _abrir(navegador, servidor, "inicio.html", vp)
    # imagem correta: símbolo extraído do logotipo original
    logo = pg.locator(".painel-logo")
    expect(logo).to_be_visible()
    assert "orgatec-original.png" in logo.get_attribute("src")
    assert logo.evaluate("(i) => i.complete && i.naturalWidth > 300")
    assert pg.get_attribute("header img", "src").endswith("orgatec-original.png")
    # painel da transição
    assert re.match(r"^\d{1,3}%$", pg.inner_text("[data-progresso]"))
    assert pg.locator("[data-anos] .chip").count() == 8
    pg.click("[data-anos] [data-ano='2030']")
    expect(pg.locator("[data-anos] [data-ano='2030']")).to_have_attribute("aria-pressed", "true")
    expect(pg.locator("[data-linha-ano]")).to_contain_text("80% das alíquotas atuais")
    pg.focus("[data-anos] [data-ano='2030']")
    pg.keyboard.press("ArrowRight")
    expect(pg.locator("[data-linha-ano]")).to_contain_text("70% das alíquotas atuais")
    pg.click("[data-anos] [data-ano='2033']")
    expect(pg.locator("[data-linha-ano]")).to_contain_text("extintos")
    # números reais (após a animação)
    pg.locator("[data-numeros]").scroll_into_view_if_needed()
    total = pg.evaluate("window.Orgatec.reformaItens.length")
    expect(pg.locator("[data-contador=itens]")).to_have_text(str(total))
    expect(pg.locator("[data-contador=ufs]")).to_have_text("27")
    # perguntas com fonte e status (a home mostra 4; as demais ficam na Central da Reforma)
    perguntas = pg.locator("[data-faq] details")
    assert perguntas.count() == 4
    perguntas.first.locator("summary").click()
    expect(perguntas.first.locator(".og-link").first).to_be_visible()
    expect(perguntas.first).to_contain_text("Consultado em")
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


def test_perguntas_somem_em_producao_sem_revisao(navegador, servidor):
    rota = _config_alterada([("ambiente: 'homologacao'", "ambiente: 'producao'")])
    pg, erros = _abrir(navegador, servidor, "inicio.html", rotas={"**/assets/js/config.js": rota})
    assert pg.locator("[data-faq] details").count() == 0
    expect(pg.locator("[data-faq]")).to_contain_text("depois da revisão técnica")
    expect(pg.locator("[data-contador=itens]")).to_have_text("0")
    assert not erros, erros


@pytest.mark.parametrize("caminho", ["inicio.html", "consultoria-tributaria.html", "reforma/index.html", "reforma/ibs.html",
                                     "ferramentas/index.html", SIMULADOR, CALENDARIO, CLIENTE, CONTATO, "reforma/alertas-regionais.html",
                                     "testes/index.html", "privacidade.html", "marca.html", "index.html",
                                     "orgatec-trilha.html", "orgatec-template2.html"])
def test_css_compilado_e_csp_sem_script_embutido(navegador, servidor, caminho):
    """T3: sem o CDN do Tailwind; a CSP só permite scripts do próprio site e nenhuma página esbarra nela."""
    ctx = navegador.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pedidos, avisos, erros = [], [], []
    pg.on("request", lambda r: pedidos.append(r.url))
    pg.on("console", lambda m: avisos.append(m.text) if "Content Security Policy" in m.text or "Refused" in m.text else None)
    pg.on("pageerror", lambda e: erros.append(str(e)))
    resposta = pg.goto(f"{servidor}/{caminho}")
    pg.wait_for_load_state("load")  # não espera a rede externa (fontes) ficar ociosa
    assert "script-src 'self';" in resposta.headers["content-security-policy"]
    assert not [u for u in pedidos if "cdn.tailwindcss.com" in u]
    assert not avisos, avisos
    assert not erros, erros
    if caminho not in ("orgatec-trilha.html", "orgatec-template2.html"):  # páginas com Tailwind compilado
        assert pg.locator("link[href$='assets/css/tailwind.css']").count() == 1
        # classe utilitária aplicada: o cabeçalho é sticky (a tela de abertura não tem cabeçalho)
        if caminho != "index.html":
            assert pg.evaluate("getComputedStyle(document.querySelector('header')).position") in ("sticky", "static")


# ---------- Nova arquitetura (31/10/2026): home curta, ferramentas em páginas próprias, menu único ----------

INTERNAS = ("orgatec-template2.html", "orgatec-trilha.html", "marca.html", "privacidade.html", "index.html")  # sem o menu comum
GERADAS = sorted(p.relative_to(RAIZ / "site").as_posix() for p in (RAIZ / "site").rglob("*.html")
                 if p.name not in INTERNAS and p.parent.name != "cotacoes")  # cotacoes/: só o widget do CEPEA, sem menu


def test_nenhum_link_para_as_secoes_antigas_da_home():
    """Simulador, calendário e contato saíram da home: nenhum link pode apontar para index.html#..."""
    for caminho in GERADAS:
        html = (RAIZ / "site" / caminho).read_text(encoding="utf-8")
        assert not re.search(r'href="[^"]*index\.html#(simulador|calendario|contato|regional|servicos)"', html), caminho
        assert 'href="#simulador"' not in html and 'href="#calendario"' not in html, caminho


def test_menu_e_rodape_iguais_em_todas_as_paginas():
    """Cabeçalho e rodapé vêm todos de tools/layout.py: mesmos rótulos e destinos (fora o prefixo ../)."""
    def assinatura(caminho):
        html = (RAIZ / "site" / caminho).read_text(encoding="utf-8")
        nav = re.search(r'<nav class="hidden xl:flex.*?</nav>', html, re.S).group(0)
        rodape = re.search(r"<footer.*?</footer>", html, re.S).group(0)
        limpa = lambda t: re.sub(r' aria-current="page"| text-acao font-semibold', "", t.replace("../", ""))
        return limpa(nav), limpa(rodape)
    base = assinatura("inicio.html")
    for caminho in GERADAS:
        assert assinatura(caminho) == base, caminho


def test_home_curta_no_celular(navegador, servidor):
    pg = navegador.new_context(viewport={"width": 548, "height": 900}).new_page()
    pg.goto(f"{servidor}/inicio.html")
    pg.wait_for_load_state("load")
    altura = pg.evaluate("document.documentElement.scrollHeight")
    # limite subiu de 7.000 para 8.000 px quando entrou o painel de fontes oficiais (padrões do Firefly, 31/10/2026)
    assert altura < 8000, f"home com {altura}px (antes da nova arquitetura: ~17.100px)"
    # herói, transição + números, casos, últimas, ferramentas, fontes, perguntas, faixa
    assert pg.locator("main section").count() == 8


def test_menu_com_grupos_desktop_e_celular(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "reforma/index.html")
    grupo = pg.locator("nav[aria-label=Principal] [data-nav-grupo]").nth(2)  # Setores, Empresarial, Ferramentas
    grupo.locator("summary").click()
    expect(grupo.locator(".nav-sub a[href$='simulador.html']")).to_be_visible()
    pg.keyboard.press("Escape")
    expect(grupo.locator(".nav-sub")).to_be_hidden()
    expect(pg.locator("nav.trilha")).to_contain_text("Reforma")
    pg2, erros2 = _abrir(navegador, servidor, SIMULADOR, "mobile")
    expect(pg2.locator("nav.trilha a[href='../inicio.html']")).to_be_visible()  # Início = vitrine, não a tela de abertura
    pg2.click("#btnMenu")
    expect(pg2.locator("#menuMobile a[href='../ferramentas/calendario.html']")).to_be_visible()
    expect(pg2.locator("#menuMobile a[href='../ferramentas/simulador.html'][aria-current=page]")).to_be_visible()
    assert not erros and not erros2, erros + erros2


def test_barra_fixa_do_celular(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "inicio.html", "mobile")
    barra = pg.locator("[data-barra-movel]")
    expect(barra).to_have_class(re.compile("recolhida"))  # herói na tela: a barra fica escondida
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    expect(barra).not_to_have_class(re.compile("recolhida"))
    expect(barra.locator("a[href='ferramentas/simulador.html']")).to_be_visible()
    pg2, _ = _abrir(navegador, servidor, "inicio.html", "desktop")
    expect(pg2.locator("[data-barra-movel]")).to_be_hidden()
    assert not erros, erros


def test_alertas_regionais_em_pagina_propria(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "reforma/alertas-regionais.html", "mobile")
    for uf in ["Goiás", "Tocantins", "Pará"]:
        pg.click(f"#tabsUf button:has-text('{uf}')")
        assert pg.locator("#listaRegional li").count() >= 1, uf
    expect(pg.locator("#tabsUf button.tab-ativa")).to_have_count(1)
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def test_rodape_dpo_aponta_para_o_contato(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "reforma/ibs.html")
    expect(pg.locator("#rodapeEmails a")).to_have_attribute("href", "mailto:dpo@orgatec.io")
    # com o canal desligado em config.js, o rodapé volta a apontar para o formulário de contato
    rota = _config_alterada([("dpo: { endereco: 'dpo@orgatec.io', ativo: true }", "dpo: { endereco: 'dpo@orgatec.io', ativo: false }")])
    pg2, erros2 = _abrir(navegador, servidor, "reforma/ibs.html", rotas={"**/assets/js/config.js": rota})
    expect(pg2.locator("#rodapeEmails a")).to_have_attribute("href", "../contato/index.html")
    assert not erros and not erros2, erros + erros2


def test_marcos_do_metodo_na_consultoria(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "consultoria-tributaria.html")
    pg.locator("[data-marcos]").scroll_into_view_if_needed()
    expect(pg.locator("[data-marcos] .marco.aceso")).to_have_count(4)
    assert not erros, erros


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_seletor_de_casos_na_home(navegador, servidor, vp):
    pg, erros = _abrir(navegador, servidor, "inicio.html", vp)
    painel = pg.locator("#painelCaso")
    expect(painel).to_be_hidden()
    pg.click("a[data-caso=agro]")
    assert pg.url.endswith("/inicio.html")  # com JS o cartão abre o painel em vez de navegar
    expect(painel).to_be_visible()
    expect(pg.locator("a[data-caso=agro]")).to_have_attribute("aria-pressed", "true")
    assert painel.locator(".og-item").count() == 3
    assert painel.locator(".og-item .og-link").count() >= 3  # cada ponto com fonte clicável
    expect(painel.locator("a[href='ferramentas/simulador.html?setor=agro']")).to_be_visible()
    pg.click("a[data-caso=simples]")
    expect(pg.locator("a[data-caso=agro]")).to_have_attribute("aria-pressed", "false")
    expect(painel.locator("#item-simples-hibrido")).to_be_visible()
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


def test_casos_em_producao_so_com_itens_aprovados(navegador, servidor):
    rota = _config_alterada([("ambiente: 'homologacao'", "ambiente: 'producao'")])
    pg, erros = _abrir(navegador, servidor, "inicio.html", rotas={"**/assets/js/config.js": rota})
    pg.click("a[data-caso=transporte]")
    assert pg.locator("#painelCaso .og-item").count() == 0
    expect(pg.locator("#painelCaso")).to_contain_text("depois da revisão técnica")
    assert not erros, erros


def test_simulacao_rapida_abre_o_resultado_sem_valor_na_url(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "inicio.html", "mobile")
    assert pg.locator("#rSetor option").count() == 8
    pg.select_option("#rSetor", "agro")
    pg.select_option("#rRegime", "presumido")
    pg.fill("#rFat", "3.000.000")
    pg.click("[data-sim-rapida] button[type=submit]")
    pg.wait_for_url("**/ferramentas/simulador.html?setor=agro&regime=presumido")
    expect(pg.locator("#simResult")).to_be_visible()
    assert pg.input_value("#simFaturamento") == "3.000.000"
    assert "3.000.000" not in pg.url and "3000000" not in pg.url
    assert pg.evaluate("sessionStorage.getItem('orgatec.simulacaoRapida')") is None  # apagado depois de lido
    assert not erros, erros


def test_heroi_com_caixa_de_simulacao_e_faixa_de_marcos(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "inicio.html", "mobile")
    expect(pg.locator("[data-hero] form[data-sim-rapida] #rFat")).to_be_visible()
    marcos = pg.locator("[data-faixa-trilho] li")
    assert marcos.count() >= 2 and marcos.count() % 2 == 0  # duas cópias para o laço
    assert pg.locator("[data-faixa-trilho] li[aria-hidden=true] a[tabindex='-1']").count() == marcos.count() // 2
    pausa = pg.locator("[data-faixa-pausa]")
    pausa.click()
    expect(pausa).to_have_attribute("aria-pressed", "true")
    expect(pg.locator("[data-faixa-marcos]")).to_have_class(re.compile("pausada"))
    estado = pg.evaluate("getComputedStyle(document.querySelector('[data-faixa-trilho]')).animationPlayState")
    assert estado == "paused"
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def test_carrossel_de_ferramentas(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "inicio.html", "mobile")
    trilho = pg.locator("[data-carrossel-trilho]")
    assert pg.locator("[data-carrossel] .carrossel-cartao").count() == 4
    expect(pg.locator("[data-carrossel-ant]")).to_be_disabled()
    pg.locator("[data-carrossel]").scroll_into_view_if_needed()
    pg.click("[data-carrossel-prox]")
    expect(pg.locator("[data-carrossel-ant]")).to_be_enabled()  # habilita quando o trilho já andou
    for _ in range(50):  # a rolagem é suave: o botão habilita antes de ela terminar
        if trilho.evaluate("t => t.scrollLeft") > 100:
            break
        pg.wait_for_timeout(100)
    assert trilho.evaluate("t => t.scrollLeft") > 100
    assert trilho.evaluate("t => t.scrollWidth > t.clientWidth")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def test_painel_de_fontes_oficiais(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "inicio.html")
    orgaos = pg.locator("[data-orgao]")
    assert orgaos.count() >= 5
    planalto = pg.evaluate("window.Orgatec.fontes.lista.filter(f => f.url && /planalto\.gov\.br/.test(f.url)).length")
    expect(orgaos.first).to_contain_text(f"{planalto} dispositivos citados")
    expect(pg.locator("#fontes")).to_contain_text("não indica parceria")
    # No vidro azul (paleta padrão) a seção é transparente de propósito: os cartões de vidro desfocam a logo que passa atrás
    assert pg.locator("#fontes [data-orgao]").first.evaluate("e => getComputedStyle(e).backdropFilter || getComputedStyle(e).webkitBackdropFilter") != "none"
    # Em outra paleta, volta o painel escuro: fundo da seção diferente do fundo da página
    pg.click("#btnCores")
    pg.click("#temaPop [data-tema-id=verde]")
    fundo = pg.evaluate("getComputedStyle(document.getElementById('fontes')).backgroundColor")
    assert fundo != pg.evaluate("getComputedStyle(document.body).backgroundColor")
    assert not erros, erros


# ---------- Tela de abertura: raiz do site (site/index.html); a vitrine fica em inicio.html

@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_abertura_entrada_atalhos_e_fontes(navegador, servidor, vp):
    pg, erros = _abrir(navegador, servidor, "index.html", vp)
    pg.keyboard.press("Shift")  # uma tecla pula a sequência de entrada: a tela fica pronta para medir
    entrar = pg.locator("[data-entrar]:not([data-entrar-fixo])")
    expect(entrar).to_be_visible()
    assert entrar.get_attribute("href") == pg.evaluate("window.Orgatec.config.abertura.entrada") == "inicio.html"  # entra na vitrine
    assert entrar.evaluate("e => e.getBoundingClientRect().bottom") <= VIEWPORTS[vp][1]  # na primeira tela
    # Primeiro foco do teclado: o botão de entrada. No Safari/WebKit o Tab pula links por padrão (preferência do
    # navegador), então ali só se confere que o link pode receber foco.
    if NAVEGADOR == "webkit":
        entrar.focus()
    else:
        pg.keyboard.press("Tab")
    assert pg.evaluate("document.activeElement.hasAttribute('data-entrar')")
    for destino in ("tributario", "areaCliente", "locar", "simuladores", "noticias"):
        assert pg.get_attribute(f".holo-atalhos [data-destino={destino}]", "href") == pg.evaluate(f"window.Orgatec.config.abertura.{destino}")
    assert pg.get_attribute(".holo-atalhos [data-link=whatsapp]", "href").startswith("https://wa.me/5562992949161?text=")
    # marca: o nome fica ao lado do símbolo, sem sobrepor (classe própria; .holo-nome é o nome holográfico da vitrine)
    simbolo = pg.locator(".holo-marca img").bounding_box()
    nome = pg.locator(".holo-marca-nome").bounding_box()
    assert nome["x"] >= simbolo["x"] + simbolo["width"], (simbolo, nome)
    # modelo do trilhum.io (02/11/2026): texto direto no fundo, sem caixa de vidro e sem cards de marcos
    assert pg.locator(".holo-cartao, .holo-chip, [data-holo-dados]").count() == 0
    expect(pg.locator("[data-prova-anos]")).to_be_hidden()
    assert "51 anos" not in pg.inner_text("body")
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


def test_abertura_sequencia(navegador, servidor):
    """Primeira visita da aba: o holograma se forma e o texto surge depois; um clique pula; não repete na aba;
    com movimento reduzido abre pronta; "Entrar no site" chega à vitrine."""
    opacidade = "parseFloat(getComputedStyle(document.querySelector('[data-abertura-texto] h1')).opacity)"
    ctx = navegador.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="no-preference")
    pg = ctx.new_page()
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto(f"{servidor}/")
    assert pg.evaluate("document.documentElement.classList.contains('abertura-intro')")
    assert pg.evaluate(opacidade) < 0.1  # só o holograma no começo
    expect(pg.locator("html")).not_to_have_class(re.compile("abertura-intro"), timeout=4000)  # termina sozinha
    assert pg.evaluate(opacidade) == 1
    pg.reload()
    pg.wait_for_load_state("load")
    assert not pg.evaluate("document.documentElement.classList.contains('abertura-intro')")  # já vista nesta aba
    pg2 = ctx.new_page()
    pg2.goto(f"{servidor}/")
    pg2.evaluate("sessionStorage.clear()")
    pg2.reload()
    assert pg2.evaluate("document.documentElement.classList.contains('abertura-intro')")
    pg2.mouse.click(5, 5)  # clique fora do texto pula a sequência
    assert not pg2.evaluate("document.documentElement.classList.contains('abertura-intro')")
    expect(pg2.locator("[data-abertura-texto] h1")).to_have_css("opacity", "1")
    pg2.click("[data-entrar]:not([data-entrar-fixo])")
    pg2.wait_for_url("**/inicio.html")
    ctx_r = navegador.new_context(viewport={"width": 375, "height": 812}, reduced_motion="reduce")
    pg3 = ctx_r.new_page()
    pg3.goto(f"{servidor}/")
    assert not pg3.evaluate("document.documentElement.classList.contains('abertura-intro')")
    assert pg3.evaluate(opacidade) == 1
    assert not erros, erros


def test_abertura_holograma_rodizio(navegador, servidor):
    """Projeção com os logotipos da ORGATEC em rodízio (máscaras de holo-logos.js), terminando na assinatura
    "By Warley Veloso": a legenda acompanha o logotipo; "50 anos" só com os anos de atuação comprovados; com movimento
    reduzido, quadro fixo no símbolo."""
    pg, erros = _abrir(navegador, servidor, "index.html")
    assert pg.evaluate("window.Orgatec.holoLogos.length") == 7
    status = pg.evaluate("Promise.all(window.Orgatec.holoLogos.map(l => fetch(l.arquivo).then(r => r.status + ' ' + r.headers.get('content-type'))))")
    assert all(s.startswith("200 image/png") for s in status), status  # máscaras publicadas junto com o site
    legenda = pg.locator("[data-holo-legenda]")
    # sem comprovação, sem "50 anos"; a assinatura fecha o rodízio
    assert legenda.get_attribute("data-rodizio") == "simbolo servicos ia parceiro audi-agro trilhum assinatura"
    expect(legenda).to_have_attribute("data-logo", "simbolo")
    expect(legenda).to_have_attribute("data-logo", "servicos", timeout=10000)  # entrada + 5 s + meia troca
    expect(legenda).to_have_text("ORGATEC SERVIÇOS CONTÁBEIS")
    rota = _config_alterada([("inicioAtuacao: null", "inicioAtuacao: '1975-03-01'"), ("comprovacao: null", "comprovacao: 'contrato social'")])
    pg2, erros2 = _abrir(navegador, servidor, "index.html", rotas={"**/assets/js/config.js": rota})
    assert pg2.get_attribute("[data-holo-legenda]", "data-rodizio") == "simbolo servicos ia 50-anos parceiro audi-agro trilhum assinatura"
    ctx = navegador.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
    pg3 = ctx.new_page()
    pg3.goto(f"{servidor}/")
    pg3.wait_for_timeout(7000)
    assert pg3.get_attribute("[data-holo-legenda]", "data-logo") == "simbolo"  # sem rodízio
    assert not erros and not erros2, erros + erros2


def test_abertura_movimento_reduzido(navegador, servidor):
    ctx = navegador.new_context(viewport={"width": 375, "height": 812}, reduced_motion="reduce")
    pg = ctx.new_page()
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto(f"{servidor}/")
    pg.wait_for_load_state("load")
    assert pg.evaluate("document.documentElement.classList.contains('movimento-reduzido')")
    botao = pg.locator("[data-movimento]")
    expect(botao).to_have_attribute("aria-pressed", "true")
    botao.click()  # o visitante pode religar a animação; a escolha fica salva
    assert not pg.evaluate("document.documentElement.classList.contains('movimento-reduzido')")
    pg.reload()
    pg.wait_for_load_state("load")
    expect(pg.locator("[data-movimento]")).to_have_attribute("aria-pressed", "false")
    assert not erros, erros


def test_abertura_botao_fixo_e_producao(navegador, servidor):
    # celular de tela baixa: o botão principal fica abaixo da dobra, então a cópia fixa aparece
    pg = navegador.new_context(viewport={"width": 375, "height": 560}).new_page()
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto(f"{servidor}/")
    pg.wait_for_load_state("load")
    fixo = pg.locator("[data-entrar-fixo]")
    expect(fixo).to_have_class(re.compile("visivel"))
    expect(fixo).to_have_attribute("aria-hidden", "false")
    pg.locator("[data-entrar]:not([data-entrar-fixo])").scroll_into_view_if_needed()
    expect(fixo).not_to_have_class(re.compile("visivel"))  # o original voltou à tela: a cópia some
    rota = _config_alterada([("ambiente: 'homologacao'", "ambiente: 'producao'")])
    pg2, erros2 = _abrir(navegador, servidor, "index.html", rotas={"**/assets/js/config.js": rota})
    expect(pg2.locator("[data-homologacao]")).to_be_hidden()
    assert not erros and not erros2, erros + erros2


# ---------- Janela de Campo (rural/janela-de-campo.html)

@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_janela_de_campo(navegador, servidor, vp):
    # sem o boletim automático publicado, a página usa o manual mais recente (28/10/2026, já vencido)
    sem_auto = {"**/dados/campo/*.json": lambda rota: rota.fulfill(status=404, body="")}
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", vp, rotas=sem_auto)
    pg.wait_for_selector(".campo-celula", state="attached")
    regioes = pg.evaluate("window.Orgatec.boletinsCampo[0].regioes.length")
    assert pg.locator(".campo-celula").count() == regioes * 5
    # boletim de 28/10/2026 já passou: aparece como arquivo, com o aviso para consultar o INMET, e sem role=alert
    expect(pg.locator("[data-campo-situacao]")).to_contain_text("vencido")
    expect(pg.locator("[data-campo-situacao] a[href='https://alertas2.inmet.gov.br']")).to_be_visible()
    assert pg.locator(".campo-alerta[role=alert]").count() == 0
    expect(pg.locator("[data-campo-dia]")).to_contain_text("28 de outubro de 2026")
    # célula da matriz escolhe região e operação (no celular a comparação vem recolhida)
    if not pg.locator("[data-campo-comparar]").evaluate("e => e.open"):
        pg.click("[data-campo-comparar] summary")
    pg.click(".campo-celula[data-r=sul][data-o=colheita]")
    expect(pg.locator("#campoRegiao")).to_have_text("Sul")
    expect(pg.locator(".campo-op[data-o=colheita]")).to_contain_text("Colheita")
    expect(pg.locator("[data-campo-rec]")).to_contain_text("trigo")
    expect(pg.locator(".campo-op[data-o=colheita]")).to_have_attribute("aria-expanded", "true")
    expect(pg.locator("[data-campo-veredito]")).to_contain_text("Sem veredito: boletim vencido")  # arquivo: nunca mostra veredito
    assert pg.locator("[data-campo-linha] > div").count() == 6
    assert pg.locator("[data-campo-fontes] a[href^='https://']").count() >= 1
    # a escolha fica lembrada
    pg.reload()
    pg.wait_for_load_state("load")
    expect(pg.locator("#campoRegiao")).to_have_text("Sul")
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


# ---------- Soluções (sistemas da ORGATEC, Fase 1 do docs/plano-incorporacao-produtos.md)

SOLUCOES = ["solucoes/index.html", "solucoes/conciliacao.html", "solucoes/auditoria-rural.html", "cliente/index.html"]


def test_solucoes_sem_link_para_sistemas_e_sem_codigo_externo():
    """O site só faz link para os sistemas, e só quando config.solucoes disser 'disponivel'. No HTML gerado
    não pode haver endereço de sistema (Railway, subdomínio de app), iframe nem script de outro domínio."""
    for caminho in SOLUCOES:
        html = (RAIZ / "site" / caminho).read_text(encoding="utf-8")
        assert "<iframe" not in html, caminho
        assert not re.search(r"railway\.app|onrender\.com|vercel\.app|supabase\.co", html), caminho
        assert not re.search(r'<script[^>]+src="https?://', html), caminho


def test_conciliacao_bloco_de_confianca_so_afirma_o_conferido():
    """Cada controle tem selo de situação e evidência em docs/conciliacao-confianca-evidencias.md.
    Frases que o código do OrgConc não sustenta (conferido em 07/11/2026) não podem voltar."""
    html = (RAIZ / "site" / "solucoes" / "conciliacao.html").read_text(encoding="utf-8")
    bloco = html[html.index('id="confianca"'):]
    bloco = bloco[:bloco.index("</section>")]
    selos = re.findall(r'data-controle><span class="og-selo og-selo-\w+ mb-3">([^<]+)</span>', bloco)
    assert len(selos) == 6 and set(selos) <= {"no sistema", "em parte", "a definir"}, selos
    for proibida in ("aplicado pelo próprio banco de dados, não só pela tela", "ISO 27001 e", "certificad", "São Paulo",
                     "treina", "à prova de adulteração", "nomes são substituídos"):
        assert proibida not in bloco, proibida
    assert "não tem certificação ISO 27001 nem SOC 2" in bloco
    assert (RAIZ / "docs" / "conciliacao-confianca-evidencias.md").exists()


def test_solucoes_entrar_obedece_config(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "solucoes/index.html")
    assert pg.locator("[data-solucao-entrar]:not([hidden])").count() == 0  # nada disponível por padrão
    expect(pg.locator("[data-solucao=conciliacao] [data-solucao-selo]")).to_have_text("Demonstração com a equipe")
    expect(pg.locator("[data-solucao=auditoriaRural] [data-solucao-selo]")).to_have_text("Serviço do escritório")
    expect(pg.locator("[data-solucao=gestaoFinanceira] [data-solucao-selo]")).to_have_text("Em breve")
    # endereço sem https não liga o botão, mesmo com 'disponivel'
    rota = _config_alterada([("conciliacao: { situacao: 'demonstracao', url: null }", "conciliacao: { situacao: 'disponivel', url: 'http://inseguro.exemplo' }")])
    pg2, erros2 = _abrir(navegador, servidor, "solucoes/conciliacao.html", rotas={"**/assets/js/config.js": rota})
    assert pg2.locator("[data-solucao-entrar] a").count() == 0
    rota = _config_alterada([("conciliacao: { situacao: 'demonstracao', url: null }", "conciliacao: { situacao: 'disponivel', url: 'https://conciliacao.exemplo.com.br' }")])
    for caminho in ("solucoes/conciliacao.html", "cliente/index.html"):
        pg3, erros3 = _abrir(navegador, servidor, caminho, rotas={"**/assets/js/config.js": rota})
        entrar = pg3.locator("[data-solucao=conciliacao] [data-solucao-entrar] a")
        expect(entrar).to_have_text("Entrar")
        assert entrar.get_attribute("href") == "https://conciliacao.exemplo.com.br"
        expect(pg3.locator("[data-solucao=conciliacao] [data-solucao-selo]")).to_have_text("Disponível")
        assert not erros3, erros3
    assert not erros and not erros2, erros + erros2


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_auditoria_rural_laudo_de_exemplo_ficticio(navegador, servidor, vp):
    pg, erros = _abrir(navegador, servidor, "solucoes/auditoria-rural.html", vp)
    laudo = pg.locator("[data-laudo-exemplo]")
    expect(laudo).to_contain_text("DADOS FICTÍCIOS")
    expect(laudo).to_contain_text("***.***.***-**")  # CPF sempre mascarado no exemplo
    assert not re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", pg.inner_text("main"))  # nenhum CPF na página
    expect(pg.locator("a[href='../reforma/index.html#item-lcdpr']")).to_be_visible()
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


def test_menu_tem_solucoes_e_atalhos_levam_as_solucoes(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "inicio.html")
    grupo = pg.locator("nav[aria-label=Principal] [data-nav-grupo]").nth(3)  # Setores, Empresarial, Ferramentas, Soluções
    expect(grupo.locator("summary")).to_have_text("Soluções")
    grupo.locator("summary").click()
    expect(grupo.locator(".nav-sub a[href='solucoes/auditoria-rural.html']")).to_be_visible()
    expect(pg.locator("#ferramentas a[href='solucoes/index.html']")).to_be_visible()
    pg2, erros2 = _abrir(navegador, servidor, "index.html", "mobile")
    assert pg2.get_attribute(".holo-atalhos [data-destino=solucoes]", "href") == "solucoes/index.html"
    assert not erros and not erros2, erros + erros2


# ---------- Área de Compliance (Fase A do docs/plano-area-compliance.md)

def test_compliance_frentes_prazos_e_itens_com_fonte(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/index.html")
    frentes = pg.locator("[data-frente]")
    assert frentes.count() == 4
    for chave, pagina in [("tributario", "conformidade-tributaria"), ("pld", "prevencao-lavagem"), ("lgpd", "protecao-de-dados"), ("integridade", "integridade")]:
        assert pg.get_attribute(f"a[data-frente={chave}]", "href") == f"../compliance/{pagina}.html"
    datas = pg.locator("[data-prazos] li .og-item-meta").all_inner_texts()
    assert datas[:3] == ["31/12/2026", "01/01/2027", "31/01/2027"]  # do mais próximo ao mais distante
    itens = pg.locator("#itens .og-item")
    assert itens.count() >= 3
    for i in range(itens.count()):
        assert itens.nth(i).locator(".og-item-fontes .og-citacao").count() >= 1
    # LC 225/2026 conferida no Planalto; a notícia sobre o prazo do Confia continua "pendente de validação"
    expect(pg.locator("#item-programas-conformidade-receita")).to_contain_text("Em vigor")
    expect(pg.locator("#item-programas-conformidade-receita")).to_contain_text("pendente de validação")
    assert not erros, erros


def test_compliance_tributaria_reaproveita_itens_da_reforma(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/conformidade-tributaria.html", "mobile")
    ids = pg.locator("#itens .og-item").evaluate_all("els => els.map(e => e.id)")
    assert {"item-conformidade-2026", "item-documentos-fiscais", "item-programas-conformidade-receita", "item-produtor-cnpj-documento-2027"} <= set(ids)
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def test_compliance_em_producao_so_itens_aprovados(navegador, servidor):
    rota = _config_alterada([("ambiente: 'homologacao'", "ambiente: 'producao'")])
    pg, erros = _abrir(navegador, servidor, "compliance/index.html", rotas={"**/assets/js/config.js": rota})
    assert pg.locator("#itens .og-item").count() == 0
    expect(pg.locator("#itens")).to_contain_text("aguardando revisão técnica")
    expect(pg.locator("[data-prazos]")).to_contain_text("aguardando revisão técnica")
    assert not erros, erros


def test_menu_com_compliance_e_escritorio_no_rodape(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "inicio.html")  # desktop 1440
    nav = pg.locator("nav[aria-label=Principal]")
    expect(nav.locator("[data-nav-grupo] summary", has_text="Compliance")).to_be_visible()
    assert nav.locator("a[href='quem-somos.html']").count() == 0
    expect(pg.locator("footer a[href='quem-somos.html']")).to_be_visible()
    # 1280 px (menor largura com o menu completo): o menu não encosta no logotipo nem nos botões
    pg2 = navegador.new_context(viewport={"width": 1280, "height": 860}).new_page()
    pg2.goto(f"{servidor}/compliance/index.html")
    pg2.wait_for_load_state("load")
    folgas = pg2.evaluate("""() => { const b = [...document.querySelector('header .h-20').children].map(c => c.getBoundingClientRect());
        return [b[1].left - b[0].right, b[2].left - b[1].right]; }""")
    assert min(folgas) >= 8, folgas
    marca = pg2.evaluate("(() => { const s = document.querySelector('header a[aria-label^=ORGATEC] span.hidden'); return s.getBoundingClientRect().right; })()")
    inicio_menu = pg2.evaluate("document.querySelector('nav[aria-label=Principal]').getBoundingClientRect().left")
    assert marca <= inicio_menu, (marca, inicio_menu)  # a linha "Inteligência Tributária" não passa por baixo do menu
    pg3, erros3 = _abrir(navegador, servidor, "inicio.html", "mobile")
    pg3.click("#btnMenu")
    expect(pg3.locator("#menuMobile a[href='quem-somos.html']")).to_be_visible()
    assert not erros and not erros3, erros + erros3


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_item_inicio_no_menu(navegador, servidor, vp):
    pg, erros = _abrir(navegador, servidor, "consultoria-tributaria.html", vp)
    if vp == "desktop":
        link = pg.locator("nav[aria-label=Principal] a[title='Início']")
        expect(link).to_be_visible()
        assert link.get_attribute("href") == "inicio.html"
        assert link.inner_text().strip() == "Início"  # nome acessível, mesmo com só o ícone visível em 1440 px
    else:
        pg.click("#btnMenu")
        expect(pg.locator("#menuMobile a[href='inicio.html']").first).to_have_text("Início")
    pg2, _ = _abrir(navegador, servidor, "inicio.html", vp)
    seletor = "nav[aria-label=Principal] a[title='Início']" if vp == "desktop" else "#menuMobile a[href='inicio.html']"
    assert pg2.locator(seletor).first.get_attribute("aria-current") == "page"
    assert not erros, erros


# ---------- Compliance, fases B a D: termômetro, frentes PLD/LGPD/integridade e calendário

def test_termometro_calcula_no_navegador_sem_rede(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/termometro.html", "mobile")
    pedidos = []
    pg.on("request", lambda r: pedidos.append(r.url))
    assert pg.locator("[data-pergunta]").count() == pg.evaluate("window.Orgatec.termometro.PERGUNTAS.length") >= 16
    assert pg.locator("[data-pergunta] .og-citacao").count() >= 16  # toda pergunta com fonte
    pg.check("[data-pergunta=t-docs-fiscais] input[value=sim]", force=True)
    pg.check("[data-pergunta=t-obrigacoes-2026] input[value=nao]", force=True)
    pg.check("[data-pergunta=t-inconsistencias] input[value=nao_sei]", force=True)
    expect(pg.locator("[data-percentual]")).to_have_text("33%")
    expect(pg.locator("[data-nivel]")).to_have_attribute("data-nivel", "risco")
    assert pg.locator("[data-pendencias-termometro] li").evaluate_all("els => els.map(e => e.dataset.pendencia)") == ["t-obrigacoes-2026", "t-inconsistencias"]
    expect(pg.locator("[data-pendencia=t-obrigacoes-2026] [data-ver-regra]")).to_have_attribute("href", "conformidade-tributaria.html#item-teste-2026")
    assert pedidos == [], pedidos  # responder não gera nenhuma requisição
    wa = pg.get_attribute("aside [data-link=whatsapp]", "href")
    assert "nao" not in wa and "33" not in wa  # a mensagem não leva as respostas
    pg.click("[data-termometro-limpar]")
    expect(pg.locator("[data-percentual]")).to_have_text("—")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def test_termometro_abre_so_a_frente_da_ancora_e_some_em_producao(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/termometro.html#lgpd")
    expect(pg.locator("#frente-lgpd")).to_be_visible()
    expect(pg.locator("#frente-tributario")).to_be_hidden()
    rota = _config_alterada([("ambiente: 'homologacao'", "ambiente: 'producao'")])
    pg2, erros2 = _abrir(navegador, servidor, "compliance/termometro.html", rotas={"**/assets/js/config.js": rota})
    assert pg2.locator("[data-pergunta]").count() == 0  # pesos sem revisão técnica (V11)
    expect(pg2.locator("[data-termometro]")).to_contain_text("revisão técnica")
    assert not erros and not erros2, erros + erros2


@pytest.mark.parametrize("pagina,minimo", [("prevencao-lavagem", 5), ("protecao-de-dados", 5), ("integridade", 3)])
def test_frentes_pld_lgpd_integridade_com_fontes_conferidas(navegador, servidor, pagina, minimo):
    pg, erros = _abrir(navegador, servidor, f"compliance/{pagina}.html")
    itens = pg.locator("#itens .og-item")
    assert itens.count() >= minimo
    for i in range(itens.count()):
        it = itens.nth(i)
        assert it.locator(".og-citacao a[href^='https://']").count() >= 1
        expect(it).to_contain_text("em revisão técnica")
    expect(pg.locator("#termometro a")).to_have_attribute("href", re.compile(r"termometro\.html#(pld|lgpd|integridade)$"))
    assert not erros, erros


def test_pld_nao_ocorrencia_vai_ao_cfc(navegador, servidor):
    pg, _ = _abrir(navegador, servidor, "compliance/prevencao-lavagem.html")
    expect(pg.locator("#item-pld-profissionais-contabilidade")).to_contain_text("ao CFC até 31 de janeiro")
    expect(pg.locator("[data-prazos]")).to_contain_text("31/01/2027")


def test_calendario_esfera_compliance(navegador, servidor):
    pg, erros = _pagina(navegador, servidor, caminho=CALENDARIO)
    pg.fill("#calMes", "2026-12")
    pg.dispatch_event("#calMes", "change")
    expect(pg.locator("#calLista li[data-obrigacao=conformidade2026]")).to_contain_text("31/12/2026")
    pg.uncheck("input[name=calEsfera][value=compliance]")
    assert pg.locator("#calLista li[data-obrigacao=conformidade2026]").count() == 0
    assert not erros, erros


def test_termometro_ver_a_regra_leva_a_pagina_onde_o_item_esta():
    """Cada pergunta aponta para um item que aparece na página da frente dela (T.REGRA: destino compliance-<frente> ou publico-<id>)."""
    import json
    js = lambda nome: (RAIZ / "site" / "assets" / "js" / nome).read_text(encoding="utf-8")
    script = ("const T=require('./site/assets/js/termometro.js'),C=require('./site/assets/js/compliance-itens.js'),R=require('./site/assets/js/reforma-itens.js');"
              "const it={};C.concat(R).forEach(i=>it[i.id]=i);"
              "console.log(JSON.stringify(T.PERGUNTAS.filter(p=>!it[p.item].destinos.includes(T.regraDe(p).destino)).map(p=>p.id)))")
    fora = json.loads(subprocess.run(["node", "-e", script], cwd=RAIZ, capture_output=True, text=True, check=True).stdout)
    assert fora == [], fora


# ---------- Compliance: perguntas frequentes, resumo do termômetro no celular e ligações com o resto do site

@pytest.mark.parametrize("pagina,minimo", [("index", 3), ("conformidade-tributaria", 2), ("prevencao-lavagem", 4), ("protecao-de-dados", 3), ("integridade", 3)])
def test_compliance_perguntas_frequentes_vem_dos_itens(navegador, servidor, pagina, minimo):
    pg, erros = _abrir(navegador, servidor, f"compliance/{pagina}.html")
    perguntas = pg.locator("[data-faq-itens] details")
    assert perguntas.count() >= minimo
    primeira = perguntas.first
    primeira.locator("summary").click()
    expect(primeira.locator(".og-citacao").first).to_be_visible()  # resposta com fonte
    expect(primeira).to_contain_text("Consultado em")
    item = primeira.get_attribute("data-item")
    assert pg.locator(f"#item-{item}").count() == 1  # "ver o ponto completo" leva a um item desta página
    assert not erros, erros


def test_compliance_perguntas_somem_em_producao_sem_revisao(navegador, servidor):
    rota = _config_alterada([("ambiente: 'homologacao'", "ambiente: 'producao'")])
    pg, erros = _abrir(navegador, servidor, "compliance/prevencao-lavagem.html", rotas={"**/assets/js/config.js": rota})
    assert pg.locator("[data-faq-itens] details").count() == 0
    expect(pg.locator("[data-faq-itens]")).to_contain_text("depois da revisão técnica")
    assert not erros, erros


def test_termometro_resumo_fixo_no_celular(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/termometro.html", "mobile")
    resumo = pg.locator("[data-termometro-resumo]")
    expect(resumo).to_be_hidden()  # antes de responder
    assert pg.locator("[data-barra-movel]").count() == 0  # a barra geral do site não disputa o rodapé
    pg.check("[data-pergunta=t-docs-fiscais] input[value=nao]", force=True)
    expect(resumo).to_be_visible()
    expect(resumo).to_contain_text("0%")
    assert resumo.evaluate("e => getComputedStyle(e).position") == "fixed"
    pg.locator("#resultado").scroll_into_view_if_needed()
    expect(resumo).to_be_hidden()  # com o painel na tela, a barra sai
    pg2, _ = _abrir(navegador, servidor, "compliance/termometro.html", "desktop")
    pg2.check("[data-pergunta=t-docs-fiscais] input[value=nao]", force=True)
    expect(pg2.locator("[data-termometro-resumo]")).to_be_hidden()  # no desktop o painel já é fixo ao lado
    assert not erros, erros


def test_ligacoes_para_o_compliance(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "inicio.html")
    expect(pg.locator("#ferramentas a[href='compliance/termometro.html']")).to_be_visible()
    pg2, erros2 = _abrir(navegador, servidor, "ferramentas/index.html")
    expect(pg2.locator("main a.og-cartao[href='../compliance/termometro.html']")).to_be_visible()
    pg3, erros3 = _abrir(navegador, servidor, "quem-somos.html")
    expect(pg3.locator("main a[href='compliance/index.html']")).to_be_visible()
    assert not erros and not erros2 and not erros3, erros + erros2 + erros3


def test_escritorio_obrigacoes_proprias_e_canal_do_dpo(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "quem-somos.html", "mobile")
    bloco = pg.locator("[data-obrigacoes-proprias]")
    expect(bloco).to_contain_text("não ocorrência ao CFC até 31 de janeiro")
    expect(bloco).to_contain_text("não emite parecer jurídico")
    expect(bloco.locator("a[href='compliance/prevencao-lavagem.html#item-pld-profissionais-contabilidade']")).to_be_visible()
    expect(pg.locator("[data-dpo] a[href='mailto:dpo@orgatec.io']")).to_be_visible()
    # com o canal desligado em config.js, o endereço some e volta o aviso
    rota = _config_alterada([("dpo: { endereco: 'dpo@orgatec.io', ativo: true }", "dpo: { endereco: 'dpo@orgatec.io', ativo: false }")])
    pg2, erros2 = _abrir(navegador, servidor, "quem-somos.html", rotas={"**/assets/js/config.js": rota})
    expect(pg2.locator("[data-dpo]")).to_contain_text("canal em ativação")
    assert pg2.locator("[data-dpo] a[href^='mailto:']").count() == 0
    assert not erros and not erros2, erros + erros2


# ---------- Janela de Campo automática (boletim gerado por tools/gerar_boletim_campo.py)

PNG_1PX = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                        "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")


def _abrir_local(pg):
    """A região e o polo ficam numa folha que abre pela barra do local (V1 da Janela de Campo 2)."""
    pg.click("[data-campo-local]")
    expect(pg.locator("[data-campo-folha]")).to_be_visible()


def _boletim_automatico(horas_atras=0.0):
    """Boletim de hoje montado com a resposta gravada do MET Norway, com as datas deslocadas para hoje."""
    import json
    from datetime import datetime, timedelta
    sys.path.insert(0, str(RAIZ / "tools"))
    import gerar_boletim_campo as G
    met = json.loads((RAIZ / "tests" / "fixtures" / "campo" / "met-rio-verde.json").read_text(encoding="utf-8"))
    agora = datetime.now(G.BRASILIA) - timedelta(hours=horas_atras)
    desloc = (agora.date() - datetime(2026, 11, 2).date()).days
    for e in met["properties"]["timeseries"]:
        t = datetime.fromisoformat(e["time"].replace("Z", "+00:00")) + timedelta(days=desloc)
        e["time"] = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    cfg = G.carregar_polos()
    polos = [{**p, "met": met} for p in cfg["polos"]]
    return G.montar({"dia": agora.date().isoformat(), "geradoEm": agora.isoformat(timespec="minutes"), "regioes": cfg["regioes"],
                     "polos": polos, "proximaAtualizacao": "hoje às 17h"})


def _rotas_campo(boletim):
    import json
    corpo = json.dumps(boletim)
    return {
        "**/dados/campo/atual.json": lambda rota: rota.fulfill(status=200, content_type="application/json", body=corpo),
        "**/dados/campo/indice.json": lambda rota: rota.fulfill(status=200, content_type="application/json", body='{"boletins":[]}'),
        "https://gibs.earthdata.nasa.gov/**": lambda rota: rota.fulfill(status=200, content_type="image/png", body=PNG_1PX),
    }


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_janela_de_campo_automatica(navegador, servidor, vp):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", vp, rotas=_rotas_campo(b))
    expect(pg.locator("[data-campo-situacao]")).to_contain_text(re.compile(r"Vigente · atualizado \d{2}h\d{2}"))
    expect(pg.locator("[data-campo-situacao]")).not_to_contain_text("vencido")
    if vp == "mobile":
        pg.click("[data-aba=satelite]")  # no desktop o satélite fica sempre à vista
    # mapa de satélite: imagens da NASA (aqui servidas pelo teste), 20 polos coloridos e horário do infravermelho
    expect(pg.locator(".mapa-polo")).to_have_count(len(b["polos"]))
    expect(pg.locator("[data-mapa-hora]")).to_contain_text("Infravermelho")
    assert pg.locator(".mapa-polo.mapa-polo-ok, .mapa-polo.mapa-polo-atencao, .mapa-polo.mapa-polo-evitar").count() == len(b["polos"])
    # clique no polo abre a região e a linha hora a hora (24 horas)
    pg.click("[data-polo='palmas']")
    expect(pg.locator("#campoRegiao")).to_have_text("Norte e Tocantins")
    expect(pg.locator(".campo-aba[data-p='palmas']")).to_have_attribute("aria-pressed", "true")
    assert pg.locator("[data-campo-horaria] > div").count() == 24
    expect(pg.locator("[data-campo-polo-txt]")).to_contain_text("Palmas")
    # trocar a operação recolore o mapa
    pg.locator(".campo-op[data-o=animais]").click()
    expect(pg.locator("[data-polo='palmas']")).to_have_attribute("aria-label", re.compile("Palmas"))
    # próximos 7 dias, critérios pendentes e fontes com o MET Norway
    assert pg.locator(".campo-semana tbody tr").count() == len(b["regioes"])
    assert pg.locator(".campo-semana thead th").count() == 8
    assert pg.locator(".campo-criterios .og-selo-pendente").count() == 5
    assert pg.locator("[data-campo-fontes] a[href*='api.met.no']").count() == 1
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


def test_janela_de_campo_animacao_e_movimento_reduzido(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", rotas=_rotas_campo(b))
    play = pg.locator("[data-mapa-play]")
    expect(play).to_be_visible()
    play.click()
    expect(play).to_have_attribute("aria-pressed", "true")
    assert pg.locator(".mapa-palco .mapa-camada:not(.mapa-chuva):not(.mapa-fronteiras)").count() == 12  # 2 h em quadros de 10 min
    play.click()
    expect(play).to_have_attribute("aria-pressed", "false")
    pg.check("[data-mapa-chuva]")
    expect(pg.locator(".mapa-chuva")).to_be_visible()
    ctx = navegador.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    pg2 = ctx.new_page()
    for padrao, f in _rotas_campo(b).items():
        pg2.route(padrao, f)
    pg2.goto(f"{servidor}/rural/janela-de-campo.html")
    pg2.wait_for_selector("[data-mapa-quadro]", state="attached")
    expect(pg2.locator("[data-mapa-play]")).to_be_hidden()  # sem animação automática; o controle de horário continua
    assert not erros, erros


def test_janela_de_campo_desatualizada(navegador, servidor):
    b = _boletim_automatico(horas_atras=20)
    if b["dia"] < __import__("datetime").datetime.now().date().isoformat():
        b = _boletim_automatico(horas_atras=0)  # perto da meia-noite: força só a idade de geração
        b["geradoEm"] = "2000-01-01T05:00-03:00"
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", rotas=_rotas_campo(b))
    expect(pg.locator("[data-campo-situacao]")).to_contain_text(re.compile("desatualizado|vencido"))
    assert not erros, erros


def test_fontes_servidas_pelo_proprio_site(navegador, servidor):
    """T4: nenhuma página chama o Google Fonts, e as fontes do Trilha carregam do próprio domínio."""
    for arq in (RAIZ / "site").rglob("*.html"):
        assert "fonts.googleapis.com" not in arq.read_text(encoding="utf-8"), arq.name
    externos = []
    pg = navegador.new_context().new_page()
    pg.on("request", lambda r: None if r.url.startswith(servidor) or r.url.startswith("data:") else externos.append(r.url))
    pg.goto(f"{servidor}/inicio.html")
    pg.wait_for_load_state("load")
    carregadas = pg.evaluate("document.fonts.ready.then(() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family.replace(/[\"']/g, '')))")
    assert {"Sora", "IBM Plex Sans"} <= set(carregadas), carregadas  # paleta padrão Azul flutuante escuro
    assert not externos, externos


# ---------- Compliance por público (fase 2, docs/relatorio-publicos-reforma-compliance.md)

def test_compliance_por_publico_guia_e_transportador(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/publicos.html", "mobile")
    assert pg.locator("[data-publico]").count() == 8
    expect(pg.locator("main a[data-publico=transportador]")).to_have_attribute("href", "../compliance/publico/transportador.html")
    assert pg.locator("[data-publico][data-em-preparacao]").count() == 0  # todos os públicos com as normas conferidas
    pg2, erros2 = _abrir(navegador, servidor, "compliance/publico/transportador.html")
    itens = pg2.locator("#itens .og-item")
    assert itens.count() >= 12  # 7 do setor + 5 da reforma pelo destino, sem cópia
    for i in range(itens.count()):
        assert itens.nth(i).locator(".og-citacao a[href^='https://']").count() >= 1
    expect(pg2.locator("#item-transporte-ciot")).to_contain_text("18/09/2026")
    expect(pg2.locator("#item-transporte-jornada-motorista")).to_contain_text("declarou inconstitucionais")
    assert pg2.locator("[data-faq-itens] details").count() >= 5
    expect(pg2.locator("#termometro a")).to_have_attribute("href", "../../compliance/termometro.html#perfil-transportador")
    expect(pg2.locator("header a[href='../../compliance/publicos.html']").first).to_be_attached()  # menu "Por público"
    assert not erros and not erros2, erros + erros2


def test_termometro_perfil_transportador_pela_ancora(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/termometro.html#perfil-transportador", "mobile")
    expect(pg.locator("input[data-perfil][value=transportador]")).to_be_checked()
    expect(pg.locator("#frente-transporte")).to_be_visible()
    expect(pg.locator("#frente-pld")).to_be_hidden()
    pg.check("[data-pergunta=tr-ciot] input[value=nao]", force=True)
    expect(pg.locator("[data-pendencia=tr-ciot] [data-ver-regra]")).to_have_attribute("href", "publico/transportador.html#item-transporte-ciot")
    pg.check("input[data-perfil][value=geral]", force=True)
    expect(pg.locator("#frente-transporte")).to_be_hidden()  # o perfil geral não traz as obrigações do setor
    expect(pg.locator("#frente-pld")).to_be_visible()
    pg2, _ = _abrir(navegador, servidor, "compliance/termometro.html")
    expect(pg2.locator("#frente-transporte")).to_be_hidden()  # padrão: qualquer empresa
    assert not erros, erros


def test_termometro_relatorio_so_na_impressao(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/termometro.html#perfil-transportador")
    pedidos = []
    pg.on("request", lambda r: pedidos.append(r.url))
    pg.check("[data-pergunta=tr-rntrc] input[value=sim]", force=True)
    pg.check("[data-pergunta=tr-ciot] input[value=nao]", force=True)
    rel = pg.locator("[data-termometro-relatorio]")
    expect(rel).to_be_hidden()  # na tela, o relatório não aparece
    expect(rel).to_contain_text("Perfil: Transportador de cargas")
    expect(rel).to_contain_text("Emitir o CIOT")
    expect(rel).to_contain_text("Consultado em 02/11/2026")
    pg.emulate_media(media="print")
    expect(rel).to_be_visible()
    expect(pg.locator("[data-termometro-perguntas]")).to_be_hidden()
    expect(pg.locator("header").first).to_be_hidden()
    assert pedidos == [], pedidos
    assert not erros, erros


def test_setor_transporte_aponta_para_o_compliance_do_setor(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "empresarial/transporte.html")
    expect(pg.locator("a[data-compliance-setor]")).to_have_attribute("href", "../compliance/publico/transportador.html")
    pg2, _ = _abrir(navegador, servidor, "rural/index.html")
    expect(pg2.locator("a[data-compliance-setor]")).to_have_attribute("href", "../compliance/publico/produtor-rural.html")
    assert not erros, erros


# ---------- Cards por atividade na página de cotações e notícias (rural/cotacoes.html)

# Só no teste: substitui o script do CEPEA por uma tabela marcada como exemplo (nenhum valor real nem inventado no site)
WIDGET_TESTE = ("document.write('<table class=\"imagenet-widget-tabela\"><tr><td>EXEMPLO DE TESTE</td></tr>"
                "<tr><td>tabela simulada pelo teste</td></tr><tr><td>sem valor real</td></tr></table>');")
CEPEA_EXEMPLO = {"https://www.cepea.org.br/**": lambda rota: rota.fulfill(status=200, content_type="application/javascript", body=WIDGET_TESTE)}
CEPEA_FORA = {"https://www.cepea.org.br/**": lambda rota: rota.abort()}


# site/dados fica fora do git (regravado pelo agendador): os testes usam esta amostra, em vez do arquivo gerado.
NOTICIAS_EXEMPLO = {"geradoEm": "2026-11-02T12:40-03:00", "janelaDias": 90, "fontes": [{"id": "senado", "nome": "Agência Senado", "ok": True}],
                    "atividades": {"soja": [{"titulo": "Governo anuncia nova regra para a soja", "link": "https://www12.senado.leg.br/noticias/materias/1",
                                             "data": "2026-11-01T09:00-03:00", "fonte": "senado", "fonteNome": "Agência Senado", "coletadoEm": "2026-11-02T12:40-03:00"}]},
                    "tributacao": [],
                    "ultimas": {"cafe": {"titulo": "Regras da safra de café", "link": "https://www.camara.leg.br/noticias/2", "data": "2026-07-06T09:00-03:00",
                                         "fonte": "camara-agro", "fonteNome": "Agência Câmara · Agropecuária", "coletadoEm": "2026-11-02T12:40-03:00"},
                                "tributacao": None},
                    "acompanhe": [{"nome": "Conab", "url": "https://www.gov.br/conab/pt-br/assuntos/noticias"},
                                  {"nome": "Embrapa", "url": "https://www.embrapa.br/busca-de-noticias"}]}


def _cards(navegador, servidor, vp="desktop", rotas=None):
    import json
    noticias = {"**/dados/agro/noticias.json": lambda rota: rota.fulfill(status=200, content_type="application/json", body=json.dumps(NOTICIAS_EXEMPLO))}
    pg, erros = _abrir(navegador, servidor, "rural/cotacoes.html", vp, rotas={**noticias, **(rotas or {})})
    pg.locator("[data-agro]").scroll_into_view_if_needed()
    return pg, erros


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_cards_por_atividade(navegador, servidor, vp):
    pg, erros = _cards(navegador, servidor, vp, CEPEA_EXEMPLO)
    import json
    cfg = json.loads((RAIZ / "tools" / "agro_fontes.json").read_text(encoding="utf-8"))
    assert pg.locator("[data-agro-atividade]").count() == len(cfg["atividades"]) == 11
    quadros = pg.locator("[data-agro-widget]")
    assert quadros.count() == sum(1 for a in cfg["atividades"] if a["cepea"]) == 10
    for s in quadros.evaluate_all("els => els.map(e => e.getAttribute('sandbox'))"):
        assert s == "allow-scripts allow-popups allow-popups-to-escape-sandbox"  # sem allow-same-origin: origem opaca
    expect(pg.locator("[data-agro-widget][data-respondeu=ok]")).to_have_count(10, timeout=15000)
    assert all(h.endswith("px") for h in quadros.evaluate_all("els => els.map(e => e.style.height)"))
    expect(pg.locator("[data-agro-atividade=leite] .audi-agro-sem")).to_contain_text("não está disponível no widget")
    expect(pg.locator("[data-agro-situacao]")).to_contain_text("Notícias coletadas em")
    assert pg.locator("[data-agro-noticias] li").count() >= 11  # uma notícia ou o aviso de "sem notícia" em cada card
    # tema com notícia recente: só a lista; tema sem: aviso, a última que houver (com a data completa) e os links oficiais
    soja = pg.locator("[data-agro-atividade=soja] [data-agro-noticias]")
    expect(soja).to_contain_text("Governo anuncia nova regra para a soja")
    assert soja.locator(".audi-agro-ultima, .audi-agro-acompanhe").count() == 0
    cafe = pg.locator("[data-agro-atividade=cafe] [data-agro-noticias]")
    expect(cafe).to_contain_text("Sem notícia sobre o tema nos últimos 90 dias")
    expect(cafe.locator(".audi-agro-ultima")).to_contain_text("Última encontrada, de 06/07/2026")
    expect(cafe.locator(".audi-agro-ultima a")).to_have_attribute("href", "https://www.camara.leg.br/noticias/2")
    assert cafe.locator(".audi-agro-acompanhe a").evaluate_all("els => els.map(a => a.getAttribute('href'))") == [
        "https://www.gov.br/conab/pt-br/assuntos/noticias", "https://www.embrapa.br/busca-de-noticias"]
    milho = pg.locator("[data-agro-atividade=milho] [data-agro-noticias]")  # sem última: só o aviso e os links, nada inventado
    assert milho.locator(".audi-agro-ultima").count() == 0 and milho.locator(".audi-agro-acompanhe").count() == 1
    assert pg.locator(".audi-agro-selo, .audi-agro-selo img").count() == 0  # a marca está desligada (agro_fontes.json, marca.exibir)
    expect(pg.locator("[data-agro] .eyebrow").first).to_have_text("Mercado")
    assert "Audi Agro" not in pg.locator("[data-agro]").inner_text()
    assert pg.locator("[data-agro-aviso]:not([hidden])").count() == 0
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


def test_cards_com_cepea_fora_do_ar(navegador, servidor):
    pg, erros = _cards(navegador, servidor, rotas=CEPEA_FORA)
    avisos = pg.locator("[data-agro-aviso]:not([hidden])")
    expect(avisos).to_have_count(10, timeout=15000)
    expect(avisos.first).to_contain_text("indisponível agora")
    expect(avisos.first.locator("a[href^='https://cepea.org.br/br/indicador/']")).to_be_visible()
    assert pg.locator("[data-agro-widget]:not([hidden])").count() == 0
    assert not erros, erros


def test_cards_sem_noticias_nao_quebram(navegador, servidor):
    pg, erros = _cards(navegador, servidor, rotas={**CEPEA_EXEMPLO, "**/dados/agro/noticias.json": lambda rota: rota.fulfill(status=503, body="")})
    expect(pg.locator("[data-agro-noticias]").first).to_contain_text("Notícias indisponíveis agora")
    expect(pg.locator("[data-agro-widget][data-respondeu=ok]")).to_have_count(10, timeout=15000)  # a cotação continua
    assert not erros, erros


def test_csp_so_libera_o_cepea_nas_paginas_de_cotacao(servidor):
    cot = httpx.get(f"{servidor}/cotacoes/soja.html")
    assert cot.status_code == 200
    assert "script-src 'self' https://www.cepea.org.br" in cot.headers["content-security-policy"]
    assert cot.headers["x-frame-options"] == "SAMEORIGIN"
    pagina = httpx.get(f"{servidor}/rural/janela-de-campo.html")
    assert "cepea" not in pagina.headers["content-security-policy"]  # no resto do site, só scripts próprios
    assert pagina.headers["x-frame-options"] == "DENY"


@pytest.mark.parametrize("calmo", [False, True])
def test_vitrine_nome_holografico_segue_o_ponteiro(navegador, servidor, calmo):
    """Topo da vitrine: nome ORGATEC em holograma, decorativo, que inclina com o ponteiro e fica parado com movimento reduzido."""
    ctx = navegador.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce" if calmo else "no-preference")
    pg = ctx.new_page()
    pg.goto(f"{servidor}/inicio.html")
    pg.wait_for_load_state("load")
    holo = pg.locator("[data-hero] [data-holo-nome]")
    assert holo.get_attribute("aria-hidden") == "true" and holo.inner_text().strip() == "ORGATEC"
    assert holo.evaluate("e => getComputedStyle(e).pointerEvents") == "none"  # não atrapalha o formulário
    caixa = pg.locator("[data-hero]").bounding_box()
    pg.mouse.move(caixa["x"] + caixa["width"] * 0.9, caixa["y"] + caixa["height"] * 0.2)
    pg.wait_for_timeout(100)
    hx = holo.evaluate("e => e.style.getPropertyValue('--hx')")
    if calmo:
        assert hx == ""
    else:
        assert float(hx) > 0.5
    assert pg.evaluate("document.documentElement.scrollWidth") <= 1280


def test_compliance_produtor_rural(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/publico/produtor-rural.html", "mobile")
    assert pg.locator("#itens .og-item").count() >= 15  # 6 próprios + 10 da reforma e do CNPJ de 2027, sem cópia
    expect(pg.locator("#item-rural-itr")).to_contain_text("PRONAF")
    expect(pg.locator("#item-rural-eudr")).to_contain_text("30/06/2027")
    expect(pg.locator("[data-prazos]")).to_contain_text("30/12/2026")  # EUDR, item com prazo
    assert pg.locator("[data-faq-itens] details").count() >= 5
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    pg2, erros2 = _abrir(navegador, servidor, "compliance/termometro.html#perfil-produtor")
    expect(pg2.locator("#frente-rural")).to_be_visible()
    expect(pg2.locator("#frente-transporte")).to_be_hidden()
    pg2.check("[data-pergunta=ru-itr] input[value=nao]", force=True)
    expect(pg2.locator("[data-pendencia=ru-itr] [data-ver-regra]")).to_have_attribute("href", "publico/produtor-rural.html#item-rural-itr")
    assert not erros and not erros2, erros + erros2


@pytest.mark.parametrize("pagina,item,texto", [("mei", "mei-limite-2027", "R$ 110.000,00"), ("mei", "mei-ibs-cbs-valor-fixo", "R$ 0,994"),
                                               ("autonomo", "pf-contribuinte", "25% do valor bruto"), ("simples", "simples-locacao-imoveis", "imóveis próprios")])
def test_compliance_mei_autonomo_simples(navegador, servidor, pagina, item, texto):
    pg, erros = _abrir(navegador, servidor, f"compliance/publico/{pagina}.html", "mobile")
    expect(pg.locator(f"#item-{item}")).to_contain_text(texto)
    assert pg.locator("[data-faq-itens] details").count() >= 2
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def test_termometro_perguntas_por_publico(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/termometro.html#perfil-mei")
    expect(pg.locator("[data-pergunta=pq-mei-limite]")).to_be_visible()
    expect(pg.locator("[data-pergunta=pq-simples-opcao]")).to_be_hidden()  # pergunta do Simples fora do perfil MEI
    expect(pg.locator("#frente-tributario")).to_be_hidden()
    pg.check("[data-pergunta=pq-mei-limite] input[value=nao]", force=True)
    expect(pg.locator("[data-pendencia=pq-mei-limite] [data-ver-regra]")).to_have_attribute("href", "publico/mei.html#item-mei-limite-2027")
    pg.check("input[data-perfil][value=simples]", force=True)
    expect(pg.locator("[data-pergunta=pq-simples-opcao]")).to_be_visible()
    expect(pg.locator("[data-pergunta=pq-mei-limite]")).to_be_hidden()
    expect(pg.locator("[data-pendencias-termometro] li")).to_have_count(0)  # a resposta do MEI não conta no perfil Simples
    assert not erros, erros


@pytest.mark.parametrize("pagina,item,texto,minimo", [("comercio-industria", "comercio-saldo-icms", "240 parcelas", 12),
                                                      ("servicos", "servicos-reducao-60", "Anexo III", 11)])
def test_compliance_comercio_e_servicos(navegador, servidor, pagina, item, texto, minimo):
    pg, erros = _abrir(navegador, servidor, f"compliance/publico/{pagina}.html", "mobile")
    expect(pg.locator(f"#item-{item}")).to_contain_text(texto)
    assert pg.locator("#itens .og-item").count() >= minimo  # itens da reforma ligados pelo destino, sem cópia
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    pg2, erros2 = _abrir(navegador, servidor, f"compliance/termometro.html#perfil-{'comercio' if pagina.startswith('comercio') else 'servicos'}")
    expect(pg2.locator("[data-pergunta=t-docs-fiscais]")).to_be_visible()  # as perguntas gerais da frente tributária valem
    assert not erros and not erros2, erros + erros2


def test_compliance_imoveis_calculadora_sem_rede(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/publico/imoveis.html", "mobile")
    expect(pg.locator("#item-imoveis-reducoes")).to_contain_text("70%")
    expect(pg.locator("#item-imoveis-pf-contribuinte")).to_contain_text("R$ 240.000,00")
    pedidos = []
    pg.on("request", lambda r: pedidos.append(r.url))
    pg.fill("#iReceitaAnt", "300.000")
    pg.fill("#iLocadosAnt", "4")
    pg.click("#formImoveisPF button[type=submit]")
    expect(pg.locator("[data-imoveis-resultado]")).to_have_attribute("data-imoveis-resultado", "contribuinte")
    expect(pg.locator("#iResultado")).to_contain_text("art. 251, § 1º, I")
    pg.fill("#iLocadosAnt", "3")  # 3 imóveis não bastam: a lei exige mais de 3
    pg.click("#formImoveisPF button[type=submit]")
    expect(pg.locator("[data-imoveis-resultado]")).to_have_attribute("data-imoveis-resultado", "nao")
    assert pedidos == [], pedidos  # a conta não sai do navegador
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def test_reforma_perguntas_frequentes_com_cashback(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "reforma/index.html", "mobile")
    perguntas = pg.locator("[data-faq-itens=reforma] details")
    assert perguntas.count() >= 7
    cash = pg.locator("[data-faq-itens=reforma] details[data-item=cashback]")
    cash.locator("summary").click()
    expect(cash).to_contain_text("meio salário mínimo")
    expect(cash.locator(".og-citacao a[href^='https://']").first).to_be_visible()
    assert pg.locator("#item-cashback").count() == 1  # "ver o ponto completo" leva ao item na mesma página
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


# ---------- Política de privacidade: o texto acompanha o que o site faz

def test_politica_declara_o_que_o_site_guarda_e_quem_recebe_dados():
    politica = (RAIZ / "site" / "privacidade.html").read_text(encoding="utf-8")
    versao = re.search(r"versaoPolitica: '([\d-]+)'", (RAIZ / "site" / "assets" / "js" / "config.js").read_text(encoding="utf-8")).group(1)
    assert f"Versão {versao}" in politica  # os consentimentos registram esta versão
    chaves, cookies = set(), []
    for arq in (RAIZ / "site" / "assets" / "js").glob("*.js"):
        if arq.name.startswith("ds-"):
            continue
        texto = arq.read_text(encoding="utf-8")
        chaves |= set(re.findall(r"Storage\.\w+Item\('(orgatec\.[\w.]+)'", texto)) | set(re.findall(r"CHAVE(?:_\w+)? = '(orgatec\.[\w.]+)'", texto))
        cookies += ["document.cookie"] if "document.cookie" in texto else []
    assert len(chaves) >= 6 and not cookies  # a política diz que o site não grava cookies
    assert not [c for c in chaves if c not in politica], "chave do navegador fora da política"
    for host in ("gibs.earthdata.nasa.gov", "cepea.org.br"):  # terceiros liberados na CSP
        assert host in politica
    assert "multifator" not in re.sub(r"<p>Autenticação multifator.*?</p>", "", politica, flags=re.S)  # só como pendente


def test_caminho_do_titular_ate_o_formulario(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "privacidade.html")
    pg.click("[data-exercer-direitos]")
    pg.wait_for_url("**/contato/index.html?assunto=lgpd")
    expect(pg.locator("#ctAssunto")).to_have_value("lgpd")
    pg.goto(f"{servidor}/contato/index.html?assunto=%22inventado")  # assunto que não existe é ignorado
    expect(pg.locator("#ctAssunto")).to_have_value("diagnostico")
    assert not erros, erros


def test_modulo_locar_na_area_do_cliente(navegador, servidor):
    """Módulo exclusivo: acesso pela Área do cliente e pela tela inicial, fora do Google e sem dados do grupo."""
    pg, erros = _abrir(navegador, servidor, CLIENTE)
    pg.click("text=Abrir módulo")
    expect(pg).to_have_url(f"{servidor}/cliente/locar.html")
    assert pg.locator("meta[name=robots][content=noindex]").count() == 1
    texto = pg.inner_text("main").lower()
    assert "em implantação" in texto
    for sensivel in ("r$", "cnpj", "honorário", "incorpora", "parcelamento", "faturamento"):
        assert sensivel not in texto, sensivel
    assert pg.locator("main a[data-link=portal]").get_attribute("href").startswith("https://orgatec.athenas.online/")
    assert not erros, erros
    pg2, _ = _abrir(navegador, servidor, "index.html")
    assert pg2.locator(".holo-atalhos [data-destino=locar]").inner_text().strip() == "Módulo LOCAR"


def test_emails_institucionais_ativos(navegador, servidor):
    """C3 e C4: contato@ e dpo@ aparecem no site depois de ativados em config.js."""
    pg, erros = _abrir(navegador, servidor, "contato/index.html")
    expect(pg.locator("#contatoEmailLinha a[href='mailto:contato@orgatec.io']")).to_be_visible()
    pg2, erros2 = _abrir(navegador, servidor, "privacidade.html")
    expect(pg2.locator("#dpoLinha a[href='mailto:dpo@orgatec.io']")).to_be_visible()
    assert not erros and not erros2, erros + erros2


# ---------- Vitrine em vidro azul com a logo em holograma (ideia/vidro-azul, modelo A "Noturno")

@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_vitrine_em_vidro_azul(navegador, servidor, vp):
    pg, erros = _abrir(navegador, servidor, "inicio.html", vp)
    assert pg.get_attribute("html", "data-tema") == "azul-fl-esc"  # o vidro vale na paleta padrão
    assert pg.evaluate("document.documentElement.hasAttribute('data-vidro')")
    fundo = pg.locator(".vidro-fundo")
    assert fundo.get_attribute("aria-hidden") == "true"  # decorativo: leitor de tela ignora
    assert fundo.evaluate("e => getComputedStyle(e).pointerEvents") == "none"  # não atrapalha cliques
    assert pg.locator(".vidro-fundo .vidro-logo > i").count() == 3  # base e as duas franjas de cor; o brilho fica numa camada à parte
    assert pg.locator(".vidro-fundo .vidro-logo .brilho").count() == 1
    assert pg.locator(".vidro-fundo .vidro-orbita").count() == 1  # a logo segue o Cristal: órbita tracejada e cantos de mira
    # No computador, texto à esquerda e a logo à direita; no celular o texto fica centralizado e a logo, cortada à direita
    alinhamento = pg.locator("[data-hero] h1").evaluate("e => getComputedStyle(e).textAlign")
    assert alinhamento == ("left" if vp == "desktop" else "center")
    centro_logo = pg.locator(".vidro-palco").evaluate("e => { const r = e.getBoundingClientRect(); return r.left + r.width / 2; }")
    assert centro_logo > VIEWPORTS[vp][0] * 0.65
    mascara = pg.locator(".vidro-logo .base").evaluate("e => getComputedStyle(e).maskImage || getComputedStyle(e).webkitMaskImage")
    assert "orgatec-simbolo-branco.svg" in mascara  # a logo é o símbolo ORGATEC, não um desenho refeito
    assert pg.request.get(f"{servidor}/assets/marca/orgatec-simbolo-branco.svg").ok
    filtro = pg.locator("main .og-cartao").first.evaluate("e => getComputedStyle(e).backdropFilter || getComputedStyle(e).webkitBackdropFilter")
    assert filtro and filtro != "none"  # os cartões são de vidro: desfocam o que passa atrás
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


def test_vidro_so_na_paleta_padrao(navegador, servidor):
    """Quem troca a paleta em "Cores" vê a vitrine normal; ao voltar para a padrão, o vidro volta."""
    pg, erros = _abrir(navegador, servidor, "inicio.html")
    html = pg.locator("html")
    expect(html).to_have_attribute("data-vidro", "")
    pg.click("#btnCores")
    pg.click("#temaPop [data-tema-id=verde]")
    expect(html).not_to_have_attribute("data-vidro", "")
    assert pg.locator(".vidro-fundo").evaluate("e => getComputedStyle(e).display") == "none"
    assert pg.locator("main .og-cartao").first.evaluate("e => getComputedStyle(e).backdropFilter || getComputedStyle(e).webkitBackdropFilter") in ("none", "", None)
    pg.click("#temaPop [data-tema-id=azul-fl-esc]")
    expect(html).to_have_attribute("data-vidro", "")
    assert pg.locator(".vidro-fundo").evaluate("e => getComputedStyle(e).display") != "none"
    assert not erros, erros


def test_vidro_nao_aparece_com_outra_paleta_salva(navegador, servidor):
    ctx = navegador.new_context(viewport={"width": 1280, "height": 800})
    ctx.add_init_script("try { localStorage.setItem('orgatec.tema', 'verde'); } catch (e) {}")
    pg = ctx.new_page()
    pg.goto(f"{servidor}/inicio.html")
    pg.wait_for_load_state("load")
    assert pg.get_attribute("html", "data-tema") == "verde"
    assert not pg.evaluate("document.documentElement.hasAttribute('data-vidro')")
    assert pg.locator(".vidro-fundo").count() == 0  # nem chega a montar o fundo


@pytest.mark.parametrize("calmo", [False, True])
def test_vidro_holograma_segue_o_ponteiro_e_para_com_movimento_reduzido(navegador, servidor, calmo):
    ctx = navegador.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce" if calmo else "no-preference")
    pg = ctx.new_page()
    pg.goto(f"{servidor}/inicio.html")
    pg.wait_for_load_state("load")
    fundo = pg.locator(".vidro-fundo")
    pg.mouse.move(1180, 200)
    pg.wait_for_timeout(150)
    hx = fundo.evaluate("e => e.style.getPropertyValue('--hx')")
    animacao = pg.locator(".vidro-varredura b").evaluate("e => getComputedStyle(e).animationName")
    if calmo:
        assert hx == "" and animacao == "none"
    else:
        assert float(hx) > 0.5 and animacao != "none"


def test_vidro_desliga_as_animacoes_com_a_pagina_rolada(navegador, servidor):
    """Com a logo atrás dos cartões, qualquer animação faria todo cartão de vidro refazer o desfoque a cada quadro."""
    ctx = navegador.new_context(viewport={"width": 1280, "height": 800})
    pg = ctx.new_page()
    pg.add_init_script("window.__vidroSemSonda = true")
    pg.goto(f"{servidor}/inicio.html")
    pg.wait_for_load_state("load")
    html, varredura = pg.locator("html"), pg.locator(".vidro-varredura b")
    expect(varredura).not_to_have_css("animation-name", "none")
    pg.evaluate("window.scrollTo(0, 1200)")  # a rolagem da página é suave: as verificações esperam o fim
    expect(html).to_have_class(re.compile("vidro-pausa"))
    expect(varredura).to_have_css("animation-name", "none")
    pg.evaluate("window.scrollTo(0, 0)")
    expect(html).not_to_have_class(re.compile("vidro-pausa"))
    expect(varredura).not_to_have_css("animation-name", "none")


def test_vidro_aparelho_lento_desliga_as_animacoes(navegador, servidor):
    """Aparelho lento = quadros a cada 80 ms (12 por segundo). É simulado no próprio quadro, não por limitação de CPU:
    no runner do GitHub a CPU limitada 25 vezes ainda dava quadros de 33 ms (a mediana ficava abaixo do corte de 34 ms)
    e o resultado dependia da máquina que rodava o teste."""
    ctx = navegador.new_context(viewport={"width": 1280, "height": 800})
    pg = ctx.new_page()
    pg.add_init_script("""
        window.requestAnimationFrame = function (cb) { return window.setTimeout(function () { cb(window.performance.now()); }, 80); };
        window.cancelAnimationFrame = window.clearTimeout;
    """)
    pg.goto(f"{servidor}/inicio.html")
    pg.wait_for_load_state("load")
    for _ in range(60):  # a sonda mede duas vezes seguidas, 1,5 s cada, depois de 1,5 s de espera: leva uns 5 s
        if pg.evaluate("document.documentElement.classList.contains('vidro-leve')"):
            break
        pg.wait_for_timeout(500)
    assert pg.evaluate("document.documentElement.classList.contains('vidro-leve')")
    assert pg.locator(".vidro-varredura b").evaluate("e => getComputedStyle(e).animationName") == "none"
    assert pg.locator(".vidro-orbita").evaluate("e => getComputedStyle(e).animationName") == "none"


# ---------- Onda 1 do estudo de compliance moderno: camadas de prova e plano de ação em .ics

def test_termometro_camadas_de_prova_e_plano_ics(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "compliance/termometro.html#perfil-transportador", "mobile")
    pedidos = []
    pg.on("request", lambda r: pedidos.append(r.url))
    camada = pg.locator("[data-camadas=tr-ciot]")
    expect(camada).to_be_hidden()  # só aparece depois de um "sim"
    pg.check("[data-pergunta=tr-ciot] input[value=sim]", force=True)
    expect(camada).to_be_visible()
    expect(pg.locator("[data-evidencia-resumo]")).to_contain_text("0 de 1")
    pg.check("input[name=tr-ciot__funciona][value=nao]", force=True)  # pergunta invertida: "nenhum frete sem CIOT"
    pg.check("input[name=tr-ciot__prova][value=sim]", force=True)
    expect(pg.locator("[data-evidencia-resumo]")).to_contain_text("1 de 1")
    expect(pg.locator("[data-termometro-ics]")).to_be_hidden()  # nenhuma pendência com prazo ainda
    pg2, erros2 = _abrir(navegador, servidor, "compliance/termometro.html#perfil-produtor")
    pg2.check("[data-pergunta=ru-eudr] input[value=nao]", force=True)
    botao = pg2.locator("[data-termometro-ics]")
    expect(botao).to_be_visible()
    with pg2.expect_download() as d:
        botao.click()
    caminho = d.value.path()
    texto = open(caminho, encoding="utf-8").read()
    assert d.value.suggested_filename == "orgatec-plano-de-acao.ics"
    assert "BEGIN:VCALENDAR" in texto and "DTSTART;VALUE=DATE:20261230" in texto
    assert pedidos == [], pedidos
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros and not erros2, erros + erros2


def test_janela_de_campo_sem_os_cards_e_com_caminho_para_o_mercado(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(_boletim_automatico()))
    assert pg.locator("[data-agro], [data-agro-atividade], iframe").count() == 0
    expect(pg.locator("a[data-agro-mercado]")).to_have_attribute("href", "../rural/cotacoes.html")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def test_subnav_dos_setores_inclui_cotacoes_e_noticias(navegador, servidor):
    for caminho in ["rural/index.html", "rural/janela-de-campo.html", "rural/cotacoes.html", "reforma/alertas-regionais.html", "empresarial/transporte.html"]:
        pg, erros = _abrir(navegador, servidor, caminho)
        expect(pg.locator("main a[href='agro-mercado.html'], main a[href='../rural/cotacoes.html']").locator("visible=true").first).to_be_visible()
        assert not erros, (caminho, erros)


# ---------- Janela de Campo: nova ordem (Fase 3 do plano de modernização do agro)

def test_janela_primeira_decisao_na_primeira_tela_do_celular(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(_boletim_automatico()))
    pg.wait_for_selector(".campo-op")
    assert pg.locator(".campo-op").count() == 5
    topo = pg.evaluate("document.querySelector('.campo-op').getBoundingClientRect().top + scrollY")
    assert topo <= 812, topo
    assert pg.evaluate("document.documentElement.scrollHeight") <= 5000
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    # resumo curto por operação e comparação das regiões recolhida
    assert all(len(t) <= 90 for t in pg.locator(".campo-op-txt").all_inner_texts())
    assert not pg.locator("[data-campo-comparar]").evaluate("e => e.open")
    # o satélite só carrega quando a aba é aberta
    assert pg.locator(".mapa-satelite").count() == 0 and pg.locator(".mapa-palco img").count() == 0
    assert not erros, erros


def test_janela_abas_com_teclado_e_satelite_sob_demanda(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    assert pg.locator("[data-aba]").evaluate_all("els => els.map(e => e.getAttribute('data-aba'))") == ["horas", "semana", "satelite", "como"]
    expect(pg.locator("[data-aba=horas]")).to_have_attribute("aria-selected", "true")
    expect(pg.locator("[data-painel=horas]")).to_be_visible()
    expect(pg.locator("[data-painel=semana]")).to_be_hidden()
    pg.focus("[data-aba=horas]")
    pg.keyboard.press("ArrowRight")
    expect(pg.locator("[data-aba=semana]")).to_have_attribute("aria-selected", "true")
    expect(pg.locator("[data-painel=semana]")).to_be_visible()
    pg.keyboard.press("End")
    expect(pg.locator("[data-aba=como]")).to_have_attribute("aria-selected", "true")
    expect(pg.locator("[data-painel=como] .campo-criterios")).to_be_visible()
    pg.keyboard.press("Home")
    expect(pg.locator("[data-aba=horas]")).to_have_attribute("aria-selected", "true")
    pg.click("[data-aba=satelite]")
    expect(pg.locator(".mapa-polo")).to_have_count(len(b["polos"]))
    assert not erros, erros


def test_janela_desktop_duas_colunas_com_satelite_sempre_a_vista(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "desktop", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    expect(pg.locator("[data-painel=satelite]")).to_be_visible()
    expect(pg.locator("[data-aba=satelite]")).to_be_hidden()
    expect(pg.locator(".mapa-polo")).to_have_count(len(b["polos"]))
    expect(pg.locator("[data-campo-comparar]")).to_have_attribute("open", "")
    esq, dir_ = pg.locator(".campo-esq").bounding_box(), pg.locator(".campo-dir").bounding_box()
    assert esq["x"] + esq["width"] <= dir_["x"] + 1 and abs(esq["y"] - dir_["y"]) < 40  # lado a lado
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS["desktop"][0]
    assert not erros, erros


def test_janela_avisa_polo_sem_previsao_e_mantem_um_polo_escolhido(navegador, servidor):
    b = _boletim_automatico()
    ausente = b["polos"].pop()
    b["semDados"] = [{"id": ausente["id"], "nome": ausente["nome"], "uf": ausente["uf"], "regiao": ausente["regiao"]}]
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    expect(pg.locator("[data-campo-situacao]")).to_contain_text("Sem previsão neste horário: " + ausente["nome"])
    _abrir_local(pg)
    pg.click(f".campo-aba[data-r={ausente['regiao']}]")
    regiao = next(r for r in b["regioes"] if r["id"] == ausente["regiao"])
    assert pg.locator("[data-campo-polos] .campo-aba").count() == len(regiao["polos"]) - 1
    assert pg.locator("[data-campo-polos] .campo-aba[aria-pressed=true]").count() == 1
    assert pg.locator("[data-campo-horaria] > div").count() == 24
    assert not erros, erros


def test_janela_minha_atividade_leva_ao_card_e_fica_lembrada(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", rotas=_rotas_campo(_boletim_automatico()))
    expect(pg.locator("a[data-agro-mercado]")).to_have_attribute("href", "../rural/cotacoes.html")
    pg.select_option("[data-minha-atividade]", "soja")
    expect(pg.locator("a[data-agro-mercado]")).to_have_attribute("href", "../rural/cotacoes.html#agro-soja")
    pg.reload()
    pg.wait_for_load_state("load")
    expect(pg.locator("[data-minha-atividade]")).to_have_value("soja")
    expect(pg.locator("a[data-agro-mercado]")).to_have_attribute("href", "../rural/cotacoes.html#agro-soja")
    assert not erros, erros


# ---------- Janela de Campo 2, V1: veredito, barra do local, cartões com faixa horária (docs/ideias/campo-visual-2.md)

def test_janela_veredito_acompanha_os_estados_do_polo_escolhido(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    polo = next(p for p in b["polos"] if p["id"] == pg.evaluate("JSON.parse(localStorage.getItem('orgatec.campo') || '{}').p"))
    favoraveis = [o for o in ("pulv", "plantio", "colheita", "animais", "maquinas") if polo["ops"][o]["estado"] == "ok" and polo["ops"][o]["horasPrevistas"] > 0]
    titulo = pg.locator(".campo-veredito-titulo").inner_text()
    if len(favoraveis) == 5:
        assert titulo == "Dia favorável para todas as operações."
    elif favoraveis:
        assert titulo.startswith("Favorável hoje: ")
    else:
        assert titulo in ("Nenhuma operação está favorável hoje.", "Dia ruim: evite todas as operações.") or titulo.startswith("Sem veredito")
    # os cinco glifos do dia repetem o estado de cada cartão
    estados = pg.locator(".campo-glifo").evaluate_all("els => els.map(e => e.className.match(/campo-glifo-(\\w+)/)[1])")
    cartoes = pg.locator(".campo-card").evaluate_all("els => els.map(e => e.className.match(/campo-card-(\\w+)/)[1])")
    assert estados == cartoes and len(estados) == 5
    assert not erros, erros


def test_janela_barra_do_local_abre_folha_troca_o_polo_e_fecha(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    expect(pg.locator("[data-campo-folha]")).to_be_hidden()
    _abrir_local(pg)
    pg.click(".campo-aba[data-r=norte]")
    expect(pg.locator("#campoRegiao")).to_have_text("Norte e Tocantins")
    expect(pg.locator("[data-campo-folha]")).to_be_visible()  # escolher a região não fecha: falta o polo
    pg.click("[data-campo-polos] .campo-aba[data-p=palmas]")
    expect(pg.locator("[data-campo-folha]")).to_be_hidden()
    expect(pg.locator("[data-campo-nome]")).to_contain_text("Palmas")
    expect(pg.locator("[data-campo-titulo]")).to_have_text("Hoje em Palmas")
    _abrir_local(pg)
    pg.keyboard.press("Escape")
    expect(pg.locator("[data-campo-folha]")).to_be_hidden()
    assert not erros, erros


def test_janela_cartao_tem_faixa_horaria_e_orientacao_no_proprio_cartao(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    assert pg.locator(".campo-faixa").count() == 5
    assert pg.locator(".campo-faixa > .campo-h").count() == 5 * 16
    assert all(rotulo and "hora a hora" in rotulo for rotulo in pg.locator(".campo-faixa").evaluate_all("els => els.map(e => e.getAttribute('aria-label'))"))
    # só o cartão da operação escolhida mostra a orientação; tocar em outro troca; tocar no aberto recolhe
    assert pg.locator("[data-campo-rec]").count() == 1
    pg.click(".campo-op[data-o=colheita]")
    expect(pg.locator(".campo-op[data-o=colheita]")).to_have_attribute("aria-expanded", "true")
    expect(pg.locator(".campo-op[data-o=pulv]")).to_have_attribute("aria-expanded", "false")
    assert pg.locator("[data-campo-rec]").count() == 1
    pg.click(".campo-op[data-o=colheita]")
    assert pg.locator("[data-campo-rec]").count() == 0
    # o glifo do dia escolhe a operação
    pg.click(".campo-glifo[data-o=animais]")
    expect(pg.locator(".campo-op[data-o=animais]")).to_have_attribute("aria-expanded", "true")
    assert all(len(t) <= 90 for t in pg.locator(".campo-op-txt").all_inner_texts())
    assert not erros, erros


def test_janela_boletim_desatualizado_nao_tem_veredito(navegador, servidor):
    b = _boletim_automatico()
    b["geradoEm"] = "2000-01-01T05:00-03:00"
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    expect(pg.locator(".campo-veredito-titulo")).to_contain_text("Sem veredito: boletim")
    assert pg.locator(".campo-glifo-ok, .campo-glifo-atencao, .campo-glifo-evitar").count() == 0
    assert pg.locator(".campo-glifo-sem").count() == 5
    expect(pg.locator("[data-campo-veredito]")).not_to_contain_text("favoráveis")
    assert not erros, erros


def test_janela_barra_do_local_gruda_ao_rolar_e_mostra_os_glifos(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(_boletim_automatico()))
    pg.wait_for_selector(".campo-op")
    barra = pg.locator("[data-campo-barra]")
    assert "fixo" not in (barra.get_attribute("class") or "")
    pg.evaluate("window.scrollTo(0, 1400)")
    expect(barra).to_have_class(re.compile("fixo"))
    topo = pg.evaluate("document.querySelector('[data-campo-barra]').getBoundingClientRect().top")
    cabecalho = pg.evaluate("document.querySelector('body > header').getBoundingClientRect().height")
    assert abs(topo - cabecalho) <= 2, (topo, cabecalho)  # colada logo abaixo do cabeçalho do site
    expect(pg.locator("[data-campo-mini] .glifo")).to_have_count(5)
    assert not erros, erros


def test_janela_celular_alvos_de_toque_e_menu_de_setores(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(_boletim_automatico()))
    pg.wait_for_selector(".campo-op")
    expect(pg.locator("[data-subnav-setores]")).to_be_hidden()  # a fileira vira o menu "Setores"
    pg.click("[data-subnav-menu] summary")
    expect(pg.locator("[data-subnav-menu] a[href='../rural/cotacoes.html']")).to_be_visible()
    pg.click("[data-subnav-menu] summary")
    # botões do boletim, abas inclusive, com pelo menos 44 px de altura (a folha do local tem os chips de 44 px)
    pequenos = pg.evaluate("""() => [...document.querySelectorAll('[data-campo] button')]
        .filter(e => e.offsetParent && !e.closest('dialog') && e.getBoundingClientRect().height < 43.5).map(e => e.className + ' ' + Math.round(e.getBoundingClientRect().height))""")
    assert not pequenos, pequenos
    _abrir_local(pg)
    altos = pg.evaluate("[...document.querySelectorAll('[data-campo-folha] .campo-aba, [data-campo-fechar]')].map(e => Math.round(e.getBoundingClientRect().height))")
    assert altos and min(altos) >= 44, altos
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


def _variar_regioes(b):
    """O boletim de teste usa o mesmo MET em todos os polos; aqui as regiões ganham estados diferentes em colheita e animais."""
    for i, r in enumerate(b["regioes"]):
        r["ops"]["colheita"][0] = "atencao" if i % 2 else "ok"
        r["ops"]["animais"][0] = "ok" if i % 3 else "atencao"
        for op in ("pulv", "plantio", "maquinas"):
            r["ops"][op][0] = {"pulv": "atencao", "plantio": "ok", "maquinas": "ok"}[op]
    return b


@pytest.mark.parametrize("largura", [320, 375, 768, 1280])
def test_janela_grade_das_regioes_sem_rolagem_horizontal(navegador, servidor, largura):
    b = _variar_regioes(_boletim_automatico())
    ctx = navegador.new_context(viewport={"width": largura, "height": 800})
    pg = ctx.new_page()
    for padrao, f in _rotas_campo(b).items():
        pg.route(padrao, f)
    pg.goto(f"{servidor}/rural/janela-de-campo.html")
    pg.wait_for_selector(".campo-op")
    if not pg.locator("[data-campo-comparar]").evaluate("e => e.open"):
        pg.click("[data-campo-comparar] summary")
    assert pg.locator(".campo-regioes tbody tr").count() == len(b["regioes"])
    assert pg.locator(".campo-regioes .campo-celula").count() == len(b["regioes"]) * 5
    assert pg.evaluate("document.documentElement.scrollWidth") <= largura
    rolagem = pg.locator(".campo-regioes").evaluate("t => { const r = t.closest('.campo-matriz-rolagem'); return r.scrollWidth - r.clientWidth; }")
    assert rolagem <= 1, rolagem  # a grade cabe sem rolar nem por dentro
    assert min(pg.locator(".campo-regioes .campo-celula, .campo-regiao").evaluate_all("els => els.map(e => e.getBoundingClientRect().height)")) >= 44


def test_janela_grade_diz_igual_em_todas_so_nas_colunas_iguais(navegador, servidor):
    b = _variar_regioes(_boletim_automatico())
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "desktop", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-regioes")
    iguais = pg.locator(".campo-regioes thead th").evaluate_all("els => els.map(e => !!e.querySelector('.campo-igual'))")
    assert iguais == [False, True, True, False, False, True]  # região, pulv, plantio, colheita, animais, máquinas
    expect(pg.locator(".campo-igual-texto")).to_have_text("Igual em todas as regiões: pulverização (com restrição), plantio (favorável) e máquinas (favorável).")
    assert not erros, erros


def test_janela_grade_tocar_na_regiao_ou_na_celula_escolhe(navegador, servidor):
    b = _variar_regioes(_boletim_automatico())
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "desktop", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-regioes")
    pg.click(".campo-regiao[data-r=sul]")
    expect(pg.locator("#campoRegiao")).to_have_text("Sul")
    expect(pg.locator(".campo-regioes tr[data-r=sul]")).to_have_class(re.compile("selecionada"))
    pg.click(".campo-celula[data-r=ne][data-o=animais]")
    expect(pg.locator("#campoRegiao")).to_have_text("Nordeste e Matopiba")
    expect(pg.locator(".campo-op[data-o=animais]")).to_have_attribute("aria-expanded", "true")
    expect(pg.locator(".campo-celula[data-r=ne][data-o=animais]")).to_have_attribute("aria-pressed", "true")
    assert not erros, erros


def test_janela_grade_regiao_sem_previsao_tem_glifo_proprio(navegador, servidor):
    b = _variar_regioes(_boletim_automatico())
    b["regioes"][0]["ops"]["colheita"] = ["atencao", "Sem previsão para as horas úteis de hoje (05h às 20h).", "Veja os avisos do INMET."]
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "desktop", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-regioes")
    celula = pg.locator(f".campo-celula[data-r={b['regioes'][0]['id']}][data-o=colheita]")
    expect(celula).to_have_attribute("aria-label", re.compile("sem previsão"))
    expect(celula.locator(".glifo-sem")).to_have_count(1)
    assert not erros, erros


def test_janela_boletim_vencido_fica_em_cinza(navegador, servidor):
    sem_auto = {"**/dados/campo/*.json": lambda rota: rota.fulfill(status=404, body="")}
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "desktop", rotas=sem_auto)  # o boletim manual de 28/10 já venceu
    pg.wait_for_selector(".campo-regioes")
    expect(pg.locator("[data-campo]")).to_have_class(re.compile("campo-arquivo"))
    assert pg.locator(".campo-card").first.evaluate("e => getComputedStyle(e).filter") == "grayscale(1)"
    b = _boletim_automatico()
    pg2, erros2 = _abrir(navegador, servidor, "rural/janela-de-campo.html", "desktop", rotas=_rotas_campo(b))
    pg2.wait_for_selector(".campo-regioes")
    assert "campo-arquivo" not in (pg2.locator("[data-campo]").get_attribute("class") or "")
    assert not erros and not erros2, (erros, erros2)


CONTRASTE_JS = """() => {
    const lum = c => { const [r, g, b] = c.match(/[\\d.]+/g).slice(0, 3).map(Number).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
    const fundo = e => { while (e) { const c = getComputedStyle(e).backgroundColor; const m = c.match(/[\\d.]+/g); if (m && (m.length < 4 || Number(m[3]) > 0.95)) return c; e = e.parentElement; } return 'rgb(255,255,255)'; };
    const razao = e => { const a = lum(getComputedStyle(e).color), b = lum(fundo(e)); const [x, y] = a > b ? [a, b] : [b, a]; return (x + 0.05) / (y + 0.05); };
    const alvos = ['.campo-selo.campo-atencao', '.campo-selo.campo-ok', '.campo-card-atencao .campo-op-txt', '.campo-card-ok .campo-op-txt', '.campo-glifo span', '.campo-op-nome', '.campo-veredito-linha'];
    return alvos.map(s => { const e = document.querySelector(s); return e ? [s, +razao(e).toFixed(2)] : null; }).filter(Boolean);
}"""


def test_janela_linha_do_dia_em_svg_com_tabela_para_leitor_de_tela(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    grafico = pg.locator("[data-campo-grafico] .dia-svg")
    expect(grafico).to_have_count(1)
    assert grafico.get_attribute("aria-label").startswith("Temperatura de ")
    assert pg.locator("[data-campo-grafico] .dia-temp").get_attribute("d").startswith("M")
    linhas = pg.locator("[data-campo-grafico] .sr-only tbody tr").count()
    assert 1 <= linhas <= 16, linhas  # uma linha por hora com previsão entre 05h e 20h
    expect(pg.locator("[data-campo-linhadia-titulo]")).to_contain_text("pulverização")
    pg.click(".campo-glifo[data-o=colheita]")  # a operação escolhida muda o título e o sombreado das horas favoráveis
    expect(pg.locator("[data-campo-linhadia-titulo]")).to_contain_text("colheita")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375  # a tabela só para leitor de tela não pode alargar a página
    assert not erros, erros


def test_janela_sete_dias_com_icones_de_tempo(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    pg.click("[data-aba=semana]")
    tempos = pg.locator(".campo-semana .campo-tempo")
    assert tempos.count() >= len(b["regioes"])
    assert pg.locator(".campo-semana .campo-tempo .icone-tempo").count() == tempos.count()
    assert pg.locator(".campo-semana .icone-tempo[aria-hidden=true]").count() == tempos.count()  # o texto ("Chuva fraca") continua dizendo o tempo
    assert not erros, erros


def test_janela_ao_sol_liga_a_paleta_clara_lembra_e_mantem_o_contraste(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", "mobile", rotas=_rotas_campo(b))
    pg.wait_for_selector(".campo-op")
    sol = pg.locator("[data-campo-sol]")
    expect(sol).to_have_attribute("aria-pressed", "false")
    escuro = pg.evaluate(CONTRASTE_JS)
    assert escuro and all(r >= 4.5 for _, r in escuro), escuro
    sol.click()
    expect(sol).to_have_attribute("aria-pressed", "true")
    assert pg.evaluate("document.documentElement.getAttribute('data-tema')") == "azul-fl"
    assert pg.evaluate("localStorage.getItem('orgatec.tema')") == "azul-fl"  # a mesma chave do botão "Cores"
    claro = pg.evaluate(CONTRASTE_JS)
    assert claro and all(r >= 4.5 for _, r in claro), claro
    pg.reload()
    pg.wait_for_selector(".campo-op")
    expect(pg.locator("[data-campo-sol]")).to_have_attribute("aria-pressed", "true")
    pg.click("[data-campo-sol]")
    assert pg.evaluate("document.documentElement.getAttribute('data-tema')") == "azul-fl-esc"
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros


@pytest.mark.parametrize("tema", ["verde", "azul", "vinho", "ciano", "noite", "azul-fl", "azul-fl-esc"])
def test_janela_contraste_do_texto_em_todas_as_paletas(navegador, servidor, tema):
    b = _boletim_automatico()
    ctx = navegador.new_context(viewport={"width": 375, "height": 812})
    ctx.add_init_script(f"localStorage.setItem('orgatec.tema', '{tema}')")
    pg = ctx.new_page()
    for padrao, f in _rotas_campo(b).items():
        pg.route(padrao, f)
    pg.goto(f"{servidor}/rural/janela-de-campo.html")
    pg.wait_for_selector(".campo-op")
    assert pg.evaluate("document.documentElement.getAttribute('data-tema')") == tema
    medidas = pg.evaluate(CONTRASTE_JS)
    assert medidas and all(r >= 4.5 for _, r in medidas), (tema, medidas)


# ---------- Página Agro: resumo do dia, pontos da reforma recolhidos por tema (Fase 4)

def _agro(navegador, servidor, vp="desktop", boletim=None, rotas=None):
    todas = _rotas_campo(boletim) if boletim is not None else {"**/dados/campo/*.json": lambda rota: rota.fulfill(status=404, body="")}
    return _abrir(navegador, servidor, "rural/index.html", vp, rotas={**todas, **(rotas or {})})


def test_agro_resumo_do_dia_na_regiao_escolhida(navegador, servidor):
    b = _boletim_automatico()
    pg, erros = _agro(navegador, servidor, boletim=b)
    pg.wait_for_selector("[data-agro-hoje-lista] li")
    assert pg.locator("[data-agro-hoje-lista] li").count() == 5
    nomes = pg.locator("[data-agro-hoje-lista] li > span:first-child").all_inner_texts()
    assert nomes == ["Pulverização", "Plantio", "Colheita", "Manejo de animais", "Máquinas e insumos"]
    assert pg.locator("[data-agro-hoje-lista] .campo-selo").count() == 5  # estado com ícone, texto e cor
    # trocar a região grava a escolha na mesma chave da Janela de Campo, que abre na mesma região
    alvo = b["regioes"][2]
    pg.select_option("#agroHojeRegiao", alvo["id"])
    assert pg.evaluate("JSON.parse(localStorage.getItem('orgatec.campo')).r") == alvo["id"]
    pg2 = pg.context.new_page()
    for padrao, f in _rotas_campo(b).items():
        pg2.route(padrao, f)
    pg2.goto(f"{servidor}/rural/janela-de-campo.html")
    expect(pg2.locator("#campoRegiao")).to_have_text(alvo["nome"])
    assert not erros, erros


def test_agro_resumo_do_dia_sem_boletim_valido_fica_so_o_link(navegador, servidor):
    for boletim in (None, _boletim_automatico(horas_atras=20)):
        pg, erros = _agro(navegador, servidor, boletim=boletim)
        pg.wait_for_timeout(800)
        assert pg.locator("[data-agro-hoje-lista]").count() == 0  # nenhum número sem boletim vigente
        expect(pg.locator("a[data-agro-hoje-link]")).to_have_attribute("href", "../rural/janela-de-campo.html")
        assert not [e for e in erros if "404" not in e], erros


def test_agro_pontos_da_reforma_recolhidos_por_tema_com_fontes(navegador, servidor):
    pg, erros = _agro(navegador, servidor)
    pg.wait_for_selector("#tributos .og-item")
    total = pg.evaluate("window.Orgatec.reformaItens.filter(i => i.destinos.includes('setor-agro')).length")
    assert pg.locator("#tributos details.og-item").count() == 5 and pg.locator("#tributos details[open]").count() == 0
    expect(pg.locator("#tributos [data-contagem]")).to_have_text(f"Mostrando 5 de {total} pontos")
    pg.click("[data-ver-todos]")
    assert pg.locator("#tributos details.og-item").count() == total
    expect(pg.locator("[data-ver-todos]")).to_be_hidden()
    # leitura sob demanda, com o teclado: fato, orientação e fontes só depois de abrir; nada é omitido
    primeiro = pg.locator("#tributos details.og-item").first
    expect(primeiro.locator(".og-item-fontes a").first).to_be_hidden()
    primeiro.locator("summary").focus()
    pg.keyboard.press("Enter")
    expect(primeiro).to_have_attribute("open", "")
    expect(primeiro.locator(".og-item-fontes a").first).to_be_visible()
    expect(primeiro.locator(".og-item-meta")).to_contain_text("Consultado em")
    # chips de tema: só os temas que têm item; o filtro mostra todos os itens do tema
    chips = pg.locator("[data-temas] button")
    rotulos = chips.all_inner_texts()
    assert rotulos[0] == "Todos" and len(rotulos) >= 3
    chips.nth(1).click()
    tema = pg.evaluate("window.Orgatec.reformaItens.find(i => i.destinos.includes('setor-agro')).tema")
    esperado = pg.evaluate("t => window.Orgatec.reformaItens.filter(i => i.destinos.includes('setor-agro') && i.tema === t).length", pg.locator("#tributos details.og-item").first.get_attribute("data-tema"))
    assert pg.locator("#tributos details.og-item").count() == esperado and tema
    expect(chips.nth(1)).to_have_attribute("aria-pressed", "true")
    assert not erros, erros


def test_agro_celular_curto_e_sem_rolagem_horizontal(navegador, servidor):
    pg, erros = _agro(navegador, servidor, "mobile", boletim=_boletim_automatico())
    pg.wait_for_selector("[data-agro-hoje-lista] li")
    assert pg.evaluate("document.documentElement.scrollHeight") <= 5000
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    # o resumo do dia vem antes dos caminhos, e estes antes dos pontos da reforma
    ys = pg.evaluate("['[data-agro-hoje]', '[data-agro-caminho]', '#tributos', '#proximos-passos'].map(s => document.querySelector(s).getBoundingClientRect().top + scrollY)")
    assert ys == sorted(ys)
    assert not erros, erros


# ---------- Satélite da Janela de Campo: divisas, hora de cada imagem, falha da NASA, carga sob demanda (Fase 5)

GIBS = "https://gibs.earthdata.nasa.gov/**"


def _png(rota):
    rota.fulfill(status=200, content_type="image/png", body=PNG_1PX)


def _satelite(navegador, servidor, vp="desktop", gibs=_png):
    b = _boletim_automatico()
    rotas = {**_rotas_campo(b), GIBS: gibs}
    pg, erros = _abrir(navegador, servidor, "rural/janela-de-campo.html", vp, rotas=rotas)
    pg.wait_for_selector(".campo-op")
    if vp == "mobile":
        pg.click("[data-aba=satelite]")
    return pg, erros


def test_satelite_divisas_dos_estados_com_credito_do_ibge(navegador, servidor):
    pg, erros = _satelite(navegador, servidor)
    divisas = pg.locator("img[data-mapa-divisas]")
    expect(divisas).to_be_visible()
    assert divisas.get_attribute("src").endswith("assets/img/divisas-ufs.svg")
    assert divisas.evaluate("i => i.complete && i.naturalWidth > 0"), "o SVG das divisas não carregou"
    chave = pg.locator("[data-mapa-divisas-chave]")
    expect(chave).to_be_checked()
    chave.uncheck()
    expect(divisas).to_be_hidden()
    chave.check()
    expect(divisas).to_be_visible()
    creditos = pg.locator(".mapa-creditos")
    creditos.locator("summary").click()
    for texto in ("IBGE", "Malha Municipal Digital", "CC BY 4.0", "simplificadas"):
        expect(creditos).to_contain_text(texto)
    assert not erros, erros


def test_satelite_hora_de_cada_imagem_e_legendas(navegador, servidor):
    pg, erros = _satelite(navegador, servidor)
    hora = pg.locator("[data-mapa-hora]")
    expect(hora).to_contain_text(re.compile(r"Infravermelho · \d{2}h\d{2} \(Brasília\)"))
    # a faixa de tempo mostra as horas das pontas e a da imagem escolhida
    expect(pg.locator("[data-mapa-inicio]")).to_have_text(re.compile(r"\d{2}h\d{2}"))
    expect(pg.locator("[data-mapa-faixa-hora]")).to_have_text(re.compile(r"\d{2}h\d{2}"))
    pg.locator("[data-mapa-quadro]").fill("0")
    expect(pg.locator("[data-mapa-faixa-hora]")).to_have_text(pg.locator("[data-mapa-inicio]").inner_text())
    assert "Brasília" in pg.locator("[data-mapa-quadro]").get_attribute("aria-valuetext")
    # legenda de cores do infravermelho, a partir da escala oficial da NASA (°C)
    expect(pg.locator(".mapa-escala-titulo").first).to_have_text("Temperatura do topo da nuvem (°C)")
    assert pg.locator(".mapa-escala-barra").first.evaluate("e => getComputedStyle(e).backgroundImage").startswith("linear-gradient")
    # cor real: a hora também aparece
    pg.click("[data-camada=cor]")
    expect(hora).to_contain_text(re.compile(r"Cor real · \d{2}h\d{2} \(Brasília\)"))
    expect(pg.locator("[data-mapa-tempo]")).to_be_hidden()
    # chuva: só é pedida quando ligada; traz o dia e a escala em mm/h
    pedidas = []
    pg.on("request", lambda r: pedidas.append(r.url) if "IMERG" in r.url else None)
    assert not pedidas
    pg.check("[data-mapa-chuva]")
    expect(pg.locator(".mapa-chuva")).to_be_visible()
    expect(hora).to_contain_text(re.compile(r"chuva IMERG de \d{2}/\d{2}"))
    expect(pg.locator(".mapa-escala-titulo").last).to_contain_text("mm/h")
    assert pedidas and all("/IMERG_Precipitation_Rate/default/20" in u for u in pedidas)  # com o dia na URL
    pg.uncheck("[data-mapa-chuva]")
    expect(pg.locator(".mapa-chuva")).to_be_hidden()
    assert not erros, erros


def test_satelite_aviso_claro_quando_a_nasa_nao_responde_e_tentar_de_novo(navegador, servidor):
    pg, erros = _satelite(navegador, servidor, gibs=lambda rota: rota.abort())
    aviso = pg.locator("[data-mapa-aviso]")
    expect(aviso).to_be_visible(timeout=15000)
    expect(aviso).to_contain_text("NASA")
    expect(aviso).to_contain_text("previsão e os polos continuam valendo")
    expect(pg.locator("[data-mapa-hora]")).to_have_text("Imagem de satélite indisponível agora")
    # a previsão não depende do satélite: os polos seguem no mapa e a decisão do dia segue na tela
    assert pg.locator(".mapa-polo").count() == 20 and pg.locator(".campo-op").count() == 5
    # a NASA volta: o botão tenta de novo e o aviso some
    pg.unroute(GIBS)
    pg.route(GIBS, _png)
    pg.click("[data-mapa-tentar]")
    expect(aviso).to_be_hidden(timeout=15000)
    expect(pg.locator("[data-mapa-hora]")).to_contain_text("Infravermelho ·")
    assert not [e for e in erros if "ERR_FAILED" not in e and "net::" not in e], erros


def test_satelite_aviso_de_imagem_parcial(navegador, servidor):
    import re as _re
    # o quadrado do canto do recorte (não o central, que a sondagem usa) falha na primeira e na segunda tentativa
    pg0, _ = _abrir(navegador, servidor, "rural/janela-de-campo.html", "desktop", rotas=_rotas_campo(_boletim_automatico()))
    tx, ty = pg0.evaluate("Orgatec.campoMapa.TILES[0]")
    pg0.close()

    def falha_quadrado(rota):
        if _re.search(rf"Band13.*/4/{ty}/{tx}\.png", rota.request.url):
            rota.fulfill(status=404, body="")
        else:
            _png(rota)
    pg, erros = _satelite(navegador, servidor, gibs=falha_quadrado)
    aviso = pg.locator("[data-mapa-aviso]")
    expect(aviso).to_be_visible(timeout=15000)
    expect(aviso).to_contain_text("Parte da imagem de satélite não carregou")
    assert pg.locator(".mapa-polo").count() == 20


def test_satelite_so_carrega_quando_aparece_na_tela(navegador, servidor):
    b = _boletim_automatico()
    # desktop com janela baixa: o painel do satélite começa bem abaixo da dobra; nada é pedido à NASA até a rolagem chegar perto
    ctx = navegador.new_context(viewport={"width": 1440, "height": 300})
    pg = ctx.new_page()
    pedidas = []
    pg.on("request", lambda r: pedidas.append(r.url) if "gibs.earthdata.nasa.gov" in r.url else None)
    for padrao, f in {**_rotas_campo(b), GIBS: _png}.items():
        pg.route(padrao, f)
    pg.goto(f"{servidor}/rural/janela-de-campo.html")
    pg.wait_for_selector(".campo-op")
    pg.wait_for_timeout(800)
    assert pg.locator(".mapa-satelite").count() == 0 and not pedidas
    pg.evaluate("window.scrollTo(0, 700)")
    expect(pg.locator(".mapa-satelite")).to_be_attached(timeout=10000)
    expect(pg.locator("[data-mapa-hora]")).to_contain_text("Infravermelho")
    assert pedidas
    # celular: nada é pedido até a aba Satélite ser aberta
    ctx2 = navegador.new_context(viewport={"width": 375, "height": 812})
    pm = ctx2.new_page()
    pedidas_m = []
    pm.on("request", lambda r: pedidas_m.append(r.url) if "gibs.earthdata.nasa.gov" in r.url else None)
    for padrao, f in {**_rotas_campo(b), GIBS: _png}.items():
        pm.route(padrao, f)
    pm.goto(f"{servidor}/rural/janela-de-campo.html")
    pm.wait_for_selector(".campo-op")
    pm.wait_for_timeout(800)
    assert not pedidas_m
    pm.click("[data-aba=satelite]")
    expect(pm.locator("[data-mapa-hora]")).to_contain_text("Infravermelho")
    assert pedidas_m


def test_satelite_celular_controle_de_tempo_facil_de_tocar_e_sem_rolagem_lateral(navegador, servidor):
    pg, erros = _satelite(navegador, servidor, "mobile")
    pg.wait_for_selector("[data-mapa-quadro]", state="attached")
    expect(pg.locator("[data-mapa-tempo]")).to_be_visible()
    assert pg.locator("[data-mapa-quadro]").bounding_box()["height"] >= 40  # área de toque confortável
    assert pg.locator("[data-mapa-play]").bounding_box()["height"] >= 40
    for seletor in ("[data-mapa-inicio]", "[data-mapa-faixa-hora]", "[data-mapa-fim]", ".mapa-escala-barra"):
        expect(pg.locator(seletor).first).to_be_visible()
    assert pg.evaluate("document.documentElement.scrollWidth") <= 375
    assert not erros, erros
def test_cards_creditos_com_portais_termos_e_fontes_oficiais_fixas(navegador, servidor):
    """O crédito leva ao portal de cada fonte e aos termos conferidos; a linha das fontes oficiais não depende de JavaScript."""
    import json
    cfg = json.loads((RAIZ / "tools" / "agro_fontes.json").read_text(encoding="utf-8"))
    pg, erros = _cards(navegador, servidor, "desktop", CEPEA_EXEMPLO)
    credito = pg.locator("[data-agro-situacao] + p")
    termos = credito.locator("a", has_text="termos").evaluate_all("els => els.map(a => a.getAttribute('href'))")
    assert termos == [cfg["termos"][k]["url"] for k in ("camara", "senado", "govbr")]  # um link de termos por grupo de fontes
    portais = credito.locator("a").evaluate_all("els => els.map(a => a.getAttribute('href'))")
    assert all(f["portal"] in portais for f in cfg["feeds"])  # o nome leva ao portal da fonte, não ao arquivo do feed
    assert not any(f["url"] in portais for f in cfg["feeds"])
    expect(credito).to_contain_text("conferidos em 07/11/2026")
    expect(credito).to_contain_text("A B3 não entra")  # nenhuma cotação da B3 (pendência D22)
    oficiais = pg.locator("[data-agro-oficiais] a").evaluate_all("els => els.map(a => a.getAttribute('href'))")
    assert oficiais == [a["url"] for a in cfg["acompanhe"]]
    assert "www.conab.gov.br" not in " ".join(oficiais)
    assert not erros, erros


def test_cards_sem_o_arquivo_de_noticias_mantem_o_aviso_e_as_fontes_oficiais(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "rural/cotacoes.html", "desktop",
                       rotas={"**/dados/agro/noticias.json": lambda rota: rota.fulfill(status=404, body=""), **CEPEA_EXEMPLO})
    pg.locator("[data-agro]").scroll_into_view_if_needed()
    expect(pg.locator("[data-agro-noticias]").first).to_contain_text("Notícias indisponíveis agora")
    assert pg.locator("[data-agro-oficiais] a").count() == 4
    expect(pg.locator("[data-agro-atividade=leite] .audi-agro-sem")).to_contain_text("não está disponível no widget")  # leite segue sem cotação


def test_area_empresarial_hub_e_lucro_real(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "empresarial/index.html")
    for href in ("../empresarial/transporte.html", "../empresarial/lucro-real.html", "../reforma/simples-hibrido.html", "../compliance/publicos.html"):
        expect(pg.locator(f"main a.og-cartao[href='{href}']")).to_be_visible()
    pg2, erros2 = _abrir(navegador, servidor, "empresarial/lucro-real.html")
    expect(pg2.locator("[data-itens] .og-item, [data-itens] details").first).to_be_visible()  # itens da reforma com destino empresarial-lucro-real
    expect(pg2.locator("#item-cbs-2027")).to_have_count(1)
    assert not erros and not erros2, erros + erros2


def test_transporte_mostra_as_obrigacoes_do_transportador_e_sem_link_de_alertas(navegador, servidor):
    pg, erros = _abrir(navegador, servidor, "empresarial/transporte.html")
    expect(pg.locator("#obrigacoes")).to_be_visible()
    expect(pg.locator("#obrigacoes .lista-itens > *").first).to_be_visible()  # itens do transportador (RNTRC, CIOT, piso, vale-pedágio)
    expect(pg.locator("[data-subnav-setores] a[href$='alertas-regionais.html']")).to_have_count(0)
    assert not erros, erros


def test_janela_empresarial_marca_atrasado_e_indisponivel(navegador, servidor):
    janela = {"geradoEm": "2026-01-01T05:00-03:00", "proximaAtualizacao": "hoje às 11h", "aviso": "Não substitui a SEFAZ, a ANTT nem o contador.",
              "perfis": [], "cartoes": [
                  {"id": "E1", "modulo": "Prazos", "fonte": "Calendário", "url": "", "estado": "ok", "validadeHoras": 36, "coletadoEm": "2026-01-01T05:00-03:00",
                   "dados": {"porPerfil": {"real-GO": []}}},
                  {"id": "E2", "modulo": "Selic", "fonte": "BCB", "url": "", "estado": "indisponivel", "validadeHoras": 36, "coletadoEm": None, "motivo": "termos não conferidos"}]}
    pg, erros = _abrir(navegador, servidor, "empresarial/janela.html",
                       rotas={"**/dados/empresarial/atual.json": lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(janela))})
    expect(pg.locator("[data-cartao=E1][data-estado=atrasado]")).to_be_visible()
    expect(pg.locator("[data-cartao=E2][data-estado=indisponivel]")).to_contain_text("termos não conferidos")
    expect(pg.locator("[data-cartao=T1]")).to_have_count(0)
    pg.select_option("#jAtividade", "transportador")
    assert not [e for e in erros if "atual.json" not in e], erros


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_janela_empresarial_score_igual_ao_termometro_e_sem_rede(navegador, servidor, vp):
    """Score de compliance na Janela: sem respostas, convida ao termômetro no perfil da atividade; depois de responder na
    mesma aba, mostra a mesma nota do termômetro, por frente do perfil, sem mandar as respostas para a rede."""
    sem_dados = {"**/dados/empresarial/atual.json": lambda r: r.fulfill(status=404, body="")}
    pg, erros = _abrir(navegador, servidor, "empresarial/janela.html", vp, rotas=sem_dados)
    expect(pg.locator("[data-cartao=score][data-score-estado=sem-resposta]")).to_be_visible()
    # toda atividade da Janela tem perfil no termômetro
    assert pg.evaluate("Array.from(document.querySelectorAll('#jAtividade option')).filter(o => o.value)"
                       ".every(o => window.Orgatec.termometro.ATIVIDADE_PERFIL[o.value] === o.value)")
    pg.select_option("#jAtividade", "transportador")
    expect(pg.locator("[data-score-responder]")).to_have_attribute("href", "../compliance/termometro.html#perfil-transportador")

    pg.goto(f"{servidor}/compliance/termometro.html")  # mesma aba: as respostas ficam na memória dela
    pg.check("[data-pergunta=t-docs-fiscais] input[value=sim]", force=True)
    pg.check("[data-pergunta=t-obrigacoes-2026] input[value=nao]", force=True)
    pg.check("[data-pergunta=t-inconsistencias] input[value=nao_sei]", force=True)
    expect(pg.locator("[data-percentual]")).to_have_text("33%")

    pedidos = []
    pg.on("request", lambda r: pedidos.append((r.method, r.url, r.post_data)))
    pg.goto(f"{servidor}/empresarial/janela.html")
    expect(pg.locator("[data-score-nota]")).to_contain_text("33")
    expect(pg.locator("[data-cartao=score]")).to_have_attribute("data-score-perfil", "geral")
    expect(pg.locator("[data-score-faixa]")).to_have_attribute("data-score-faixa", "risco")
    expect(pg.locator("[data-score-frente=tributario]")).to_contain_text("33")
    expect(pg.locator("[data-score-pendencia]")).to_have_count(2)
    expect(pg.locator("[data-score-pendencia=t-obrigacoes-2026]")).to_contain_text("Fonte:")
    pg.select_option("#jAtividade", "transportador")
    expect(pg.locator("[data-cartao=score]")).to_have_attribute("data-score-perfil", "transportador")
    expect(pg.locator("[data-score-frente=transporte]")).to_be_visible()
    expect(pg.locator("[data-score-frente=pld]")).to_have_count(0)
    assert all(m == "GET" and not d for m, d in [(m, d) for m, _, d in pedidos]), pedidos
    assert not [u for _, u, _ in pedidos if "t-obrigacoes" in u or "nao_sei" in u], pedidos
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


@pytest.mark.parametrize("vp", ["mobile", "desktop"])
def test_janela_do_score_graficos_alertas_e_historico(navegador, servidor, vp):
    """Janela do score (empresarial/score.html): mesma nota do termômetro e da Janela, medidor, alertas de prazo e de frente
    em Risco, histórico só com as notas e só quando o visitante registra, e nada para a rede."""
    sem_dados = {"**/dados/empresarial/atual.json": lambda r: r.fulfill(status=404, body="")}
    pg, erros = _abrir(navegador, servidor, "compliance/termometro.html", vp, rotas=sem_dados)
    pg.check("[data-pergunta=t-docs-fiscais] input[value=sim]", force=True)
    pg.check("[data-pergunta=t-obrigacoes-2026] input[value=nao]", force=True)
    pg.check("[data-pergunta=t-inconsistencias] input[value=nao_sei]", force=True)
    expect(pg.locator("[data-percentual]")).to_have_text("33%")

    pedidos = []
    pg.on("request", lambda r: pedidos.append((r.method, r.url, r.post_data)))
    pg.goto(f"{servidor}/empresarial/janela.html")
    expect(pg.locator("[data-score-nota]")).to_contain_text("33")
    pg.click("[data-score-janela]")
    pg.wait_for_url("**/empresarial/score.html#perfil-geral")
    expect(pg.locator("[data-medidor]")).to_have_attribute("data-medidor", "33")
    expect(pg.locator("[data-medidor-faixa]")).to_have_attribute("data-medidor-faixa", "risco")
    expect(pg.locator("[data-score-perfil]")).to_have_text("Qualquer empresa")
    # alertas: frente tributária em Risco e os prazos que o motor calcula para hoje (o .ics só aparece com prazo)
    expect(pg.locator("[data-alerta=risco][data-alerta-pilar=tributario]")).to_contain_text("33 de 100")
    prazos = pg.evaluate("(() => { const O = window.Orgatec, it = {}; O.reformaItens.concat(O.complianceItens).forEach(i => it[i.id] = i);"
                         " const r = JSON.parse(sessionStorage.getItem(O.termometro.CHAVE_RESPOSTAS));"
                         " return O.scoreEmpresa.alertas(O.termometro, r, 'geral', it, O.scoreEmpresa.hojeLocal()).plano.length; })()")
    expect(pg.locator("[data-alerta=prazo]")).to_have_count(prazos)
    if prazos:
        expect(pg.locator("[data-score-ics]")).to_be_visible()
        expect(pg.locator("[data-alerta=prazo]").first).to_contain_text("Fonte:")
    # histórico: vazio, registrar, sobreviver ao recarregar, guardar só as notas, apagar
    expect(pg.locator("[data-evolucao-vazia]")).to_be_visible()
    pg.click("[data-score-registrar]")
    expect(pg.locator("[data-score-status]")).to_contain_text("registrada neste navegador")
    pg.reload()
    expect(pg.locator("[data-evolucao]")).to_have_attribute("data-evolucao", "1")
    guardado = pg.evaluate("JSON.parse(localStorage.getItem('orgatec.score.historico'))")
    assert len(guardado) == 1 and set(guardado[0]) == {"data", "perfil", "geral", "porPilar"} and guardado[0]["geral"] == 33, guardado
    pg.click("[data-score-apagar]")
    expect(pg.locator("[data-evolucao-vazia]")).to_be_visible()
    assert pg.evaluate("localStorage.getItem('orgatec.score.historico')") is None
    # outro perfil: o transportador vê só as frentes dele
    pg.select_option("#sAtividade", "transportador")
    expect(pg.locator("[data-score-perfil]")).to_have_text("Transportador de cargas")
    expect(pg.locator("[data-alerta-pilar=pld]")).to_have_count(0)
    assert all(m == "GET" and not d for m, _, d in pedidos), pedidos
    assert not [u for _, u, _ in pedidos if "t-obrigacoes" in u or "historico" in u or "nao_sei" in u], pedidos
    assert pg.evaluate("document.documentElement.scrollWidth") <= VIEWPORTS[vp][0]
    assert not erros, erros


def test_janela_do_score_some_em_producao_sem_revisao(navegador, servidor):
    if (RAIZ / "site" / "assets" / "js" / "termometro.js").read_text(encoding="utf-8").count("status: 'aprovada'"):
        pytest.skip("revisão V11 aprovada: o score aparece em produção")
    rota = _config_alterada([("ambiente: 'homologacao'", "ambiente: 'producao'")])
    pg, erros = _abrir(navegador, servidor, "empresarial/score.html", rotas={"**/assets/js/config.js": rota})
    expect(pg.locator("[data-score-revisao]")).to_contain_text("revisão técnica")
    expect(pg.locator("[data-medidor]")).to_have_count(0)
    assert not erros, erros


def test_central_de_viagem_entra_com_email_e_senha_e_manda_o_token(navegador, servidor):
    """Login Firebase na Central: a tela pede e-mail e senha, entra no Google (simulado) e passa a enviar Authorization: Bearer."""
    vistos = {"auth": [], "google": 0}

    def entrada(rota):
        rota.fulfill(status=200, content_type="application/json", body=json.dumps({"modo": "firebase", "chave_web": "CHAVE-WEB-TESTE"}))

    def contexto(rota):
        cab = rota.request.headers.get("authorization")
        vistos["auth"].append(cab)
        if cab == "Bearer ID-TOKEN-TESTE":
            rota.fulfill(status=200, content_type="application/json", body=json.dumps(
                {"papel": "leitura", "ambiente": "producao", "entrada": "firebase", "flags": {"provedores_reais": [], "sensores_ativo": False}}))
        else:
            rota.fulfill(status=403, content_type="application/json", body=json.dumps({"detail": "acesso negado"}))

    def google(rota):
        vistos["google"] += 1
        assert "CHAVE-WEB-TESTE" in rota.request.url
        rota.fulfill(status=200, content_type="application/json", body=json.dumps(
            {"idToken": "ID-TOKEN-TESTE", "refreshToken": "R", "expiresIn": "3600"}))

    def vazio(rota):
        rota.fulfill(status=200, content_type="application/json", body="[]")

    pg, erros = _abrir(navegador, servidor, "transporte/portal.html", rotas={
        "**/api/transporte/entrada": entrada, "**/api/transporte/contexto": contexto, "**/api/transporte/viagens*": vazio,
        "https://identitytoolkit.googleapis.com/**": google})
    form = pg.locator("#dev form.entrar")
    expect(form).to_be_visible()
    form.locator("input[name=email]").fill("gestor@cliente.com")
    form.locator("input[name=senha]").fill("senha-de-teste")
    form.locator("button[type=submit]").click()
    expect(pg.locator("#dev")).to_be_hidden()
    assert vistos["google"] == 1 and vistos["auth"][-1] == "Bearer ID-TOKEN-TESTE" and vistos["auth"][0] is None
    assert not erros, erros
