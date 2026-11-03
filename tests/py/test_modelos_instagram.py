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
    assert perf["nome"].startswith("ORGATEC")
    assert len("\n".join(perf["bio"])) <= 150  # limite da bio
    assert perf["link"].startswith("https://wa.me/") and "Instagram" in perf["link"]
    assert "Quem somos" in perf["destaques"] and len(perf["destaques"]) == 6


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
