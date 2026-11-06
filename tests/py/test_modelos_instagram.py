"""Modelos do Instagram (tools/modelos_instagram.py): leitura dos rascunhos do marketing (só leitura), regras das peças
(Marketing/conteudo/_modelos/peca.md) e encaixe de cada lâmina. Pula se a pasta do marketing não existir nesta máquina."""

import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import modelos_instagram as I  # noqa: E402
from gerar_design_system import CONTATO  # noqa: E402

pytestmark = pytest.mark.skipif(not (I.MARKETING / "conteudo" / "calendario" / "2026-11.md").exists(),
                                reason="pasta do marketing ausente")


def _tem_playwright() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.fixture(scope="module")
def dados():
    cfg = I.config_site()
    pecas, stories = I.calendario("2026-11")
    casos, por_id = [], {}
    for p in pecas:
        if p["rascunho"]:
            fm, lams = I.laminas(p)
            status = fm.get("status", "rascunho")
        else:
            lams, status = [{"tipo": "capa", "titulo": p["titulo"], "sub": "A escrever"}], "rascunho"
        por_id[p["id"]] = (p, lams, status)
        casos += [(p, status, lam, I.lamina_html(p, status, lam, i, len(lams), cfg)) for i, lam in enumerate(lams, 1)]
    htmls_story = [I.story_html(s, *por_id.get(s["usa"], (None, [], "rascunho")), cfg) for s in stories]  # (peça, lâminas, status)
    return {"cfg": cfg, "pecas": pecas, "stories": stories, "casos": casos, "por_id": por_id, "stories_html": htmls_story}


def test_calendario_e_rascunhos_lidos_do_marketing(dados):
    ids = [p["id"] for p in dados["pecas"]]
    assert ids[:7] == [f"P0{i}" for i in range(1, 8)]
    assert all(s["prazo"] in s["texto"] for s in dados["stories"])
    p03, lams, _ = dados["por_id"]["P03"]
    assert [x["tipo"] for x in lams] == ["capa", "ideia", "ideia", "ideia", "ideia", "fazer", "fontes"]
    fontes = lams[-1]
    assert fontes["consulta"] == "Consultadas em 02/11/2026"
    assert not any(f.startswith(("ORGATEC", "CRC")) for f in fontes["itens"])
    assert lams[0]["titulo"] == "Contratou frete? Quem emite o CIOT é você."
    assert dados["por_id"]["P01"][1][0]["sub"] == "Contabilidade consultiva e auditoria."  # nota de arte entre parênteses fora


def test_perfil_do_kit_cabe_no_instagram():
    perf = I.perfil()
    assert perf["nome"] == "ORGATEC" and len(perf["nome"]) <= 30  # o nome da conta vale sobre o do kit
    assert len("\n".join(perf["bio"])) <= 150  # limite da bio
    assert perf["link"].startswith("https://wa.me/") and "Instagram" in perf["link"]
    assert "Quem somos" in perf["destaques"] and len(perf["destaques"]) == 6


def test_simulacao_mostra_a_conta_real():
    perf, cfg = I.perfil(), I.config_site()
    html = I.simulacao_html(perf, [], [], cfg)
    assert "@orgatec.io" in html and "a definir" not in html
    assert '<p class="nome">ORGATEC</p>' in html and f'<p class="cat">{perf["categoria"]}</p>' in html
    assert 'class="end"' not in html and 'class="zap"' not in html  # sem contato público, por decisão da ORGATEC
    com_contato = I.simulacao_html({**perf, "contato": True}, [], [], cfg)
    assert 'class="end"' in com_contato and 'class="zap"' in com_contato


def test_arte_aprovada_sem_etiqueta_nem_codigo_interno(dados):
    p, lams, _ = dados["por_id"]["P01"]
    texto = lambda status: re.sub(r"data:[^\"')]+", "", I.lamina_html(p, status, lams[1], 2, len(lams), dados["cfg"]))  # noqa: E731
    assert "P01" not in texto("aprovado") and "Rascunho" not in texto("aprovado") and "02/06" in texto("aprovado")
    assert "P01 · 02/06" in texto("rascunho") and "Rascunho" in texto("rascunho")


def test_capa_tem_simbolo_grande_so_quando_o_rascunho_pede(dados):
    p01 = dados["por_id"]["P01"][1][0]
    assert p01["simbolo"] is True and p01["sub"] == "Contabilidade consultiva e auditoria."
    assert dados["por_id"]["P03"][1][0]["simbolo"] is False


def test_lamina_com_varios_itens_vira_lista(dados):
    p, lams, _ = dados["por_id"]["P01"]
    html = I.lamina_html(p, "aprovado", lams[2], 3, len(lams), dados["cfg"])
    assert '<ul class="itens">' in html and html.count("<li>") == 5
    assert "<li>Empresas do Simples, do presumido e do real</li>" in html and "<li>Pessoas físicas com imóveis</li>" in html


@pytest.mark.skipif(not _tem_playwright(), reason="Playwright ausente")
def test_simbolo_da_capa_mantem_a_proporcao_original(dados):
    from concurrent.futures import ThreadPoolExecutor

    from PIL import Image

    def medir(html):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pg = nav.new_page(viewport={"width": I.FEED[0], "height": I.FEED[1]})
            pg.set_content(html)
            r = pg.evaluate("(() => { const q = document.querySelector('.meio img').getBoundingClientRect(); return [q.width, q.height]; })()")
            nav.close()
        return r

    p, lams, _ = dados["por_id"]["P01"]
    with ThreadPoolExecutor(max_workers=1) as ex:  # thread própria: a suíte e2e mantém um Playwright síncrono aberto
        largura, altura = ex.submit(medir, I.lamina_html(p, "aprovado", lams[0], 1, len(lams), dados["cfg"])).result()
    original = Image.open(RAIZ / "site" / "assets" / "marca" / "orgatec-original.png").size
    assert abs(largura / altura - original[0] / original[1]) < 0.02


@pytest.mark.skipif(not _tem_playwright(), reason="Playwright ausente")
def test_simulacao_abre_e_arrasta_o_carrossel():
    from concurrent.futures import ThreadPoolExecutor

    peca = {"id": "P01", "titulo": "Teste", "data": "05/11", "canais": "IG", "publico": "geral", "rascunho": "x.md",
            "status": "rascunho", "arquivos": ["a.png", "b.png"]}
    html = I.simulacao_html(I.perfil(), [peca], [], I.config_site())

    def exercitar():
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pg = nav.new_page(viewport={"width": 1200, "height": 800})
            pg.set_content(html)
            pg.click('.grade a[data-abrir="p01"]')
            antes = pg.inner_text(".conta")
            q = pg.locator(".visor figure").bounding_box()
            pg.mouse.move(q["x"] + q["width"] - 30, q["y"] + 60)
            pg.mouse.down()
            pg.mouse.move(q["x"] + 30, q["y"] + 60, steps=5)
            pg.mouse.up()
            depois = pg.inner_text(".conta")
            pg.keyboard.press("Escape")
            fechou = pg.evaluate("document.getElementById('visor').hidden")
            nav.close()
        return antes, depois, fechou

    with ThreadPoolExecutor(max_workers=1) as ex:  # thread própria: a suíte e2e mantém um Playwright síncrono aberto
        assert ex.submit(exercitar).result() == ("1/2", "2/2", True)


def test_regras_das_pecas(dados):
    for p, status, lam, html in dados["casos"] + [(None, "rascunho", None, h) for h in dados["stories_html"]]:
        texto = re.sub(r"data:[^\"')]+", "", html)
        assert "orgatec.io" not in texto  # sem o endereço do site enquanto ele estiver em homologação
        assert "http://" not in texto and "https://" not in texto and "<script" not in texto
        assert ("Rascunho" in texto) == (status != "aprovado")
        assert "50 anos" not in texto and "51 anos" not in texto
        verdes = [m for m in re.findall(r"[^{}]*\{[^{}]*\}", texto) if CONTATO["contato"] in m]
        assert all(m.strip().startswith(".zap") for m in verdes), verdes  # verde só no botão de contato


def test_ultima_lamina_tem_fonte_whatsapp_e_crc(dados):
    for pid, (p, lams, _) in dados["por_id"].items():
        if not p["rascunho"]:
            continue
        fim = I.lamina_html(p, "rascunho", lams[-1], len(lams), len(lams), dados["cfg"])
        assert "WhatsApp" in fim and I.RT[1] in fim and dados["cfg"]["w"] in fim, pid


@pytest.mark.skipif(not _tem_playwright(), reason="Playwright ausente")
def test_nenhuma_lamina_transborda(dados):
    from concurrent.futures import ThreadPoolExecutor

    def medir(itens):
        from playwright.sync_api import sync_playwright
        ruins = []
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pg = nav.new_page()
            for nome, html, (w, h) in itens:
                pg.set_viewport_size({"width": w, "height": h})
                pg.set_content(html)
                pg.evaluate("document.fonts.ready.then(() => 1)")
                if pg.evaluate("document.querySelector('main').scrollHeight > document.querySelector('main').clientHeight"):
                    ruins.append(nome)
            nav.close()
        return ruins

    itens = [(f'{p["id"]} {lam["tipo"]}', html, I.FEED) for p, _, lam, html in dados["casos"]]
    itens += [(f"story {s['data']}", h, I.STORY) for s, h in zip(dados["stories"], dados["stories_html"])]
    with ThreadPoolExecutor(max_workers=1) as ex:  # thread própria: a suíte e2e mantém um Playwright síncrono aberto
        assert ex.submit(medir, itens).result() == []


def test_simulacao_aponta_so_para_arquivos_gerados():
    pagina = I.SAIDA / "simulacao-perfil.html"
    if not pagina.exists():
        pytest.skip("modelos ainda não gerados (python tools/modelos_instagram.py)")
    html = pagina.read_text(encoding="utf-8")
    assert "não é a interface do Instagram" in html.lower() or "Não é a interface do Instagram" in html
    for src in re.findall(r'(?:src|href)="([^"#]+)"', html):
        assert (pagina.parent / src).resolve().is_file(), src
