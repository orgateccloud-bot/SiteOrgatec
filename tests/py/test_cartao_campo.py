"""Cartão da Janela de Campo para o status do WhatsApp e os stories (tools/cartao_campo.py), sem rede: o boletim vem
da resposta gravada do MET Norway em tests/fixtures/campo. Precisa do Node.js; a renderização, do Playwright."""

import colorsys
import copy
import json
import logging
import os
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
import cartao_campo as C  # noqa: E402
import gerar_boletim_campo as G  # noqa: E402

MET = json.loads((RAIZ / "tests" / "fixtures" / "campo" / "met-rio-verde.json").read_text(encoding="utf-8"))
AGORA = datetime(2026, 11, 2, 11, 2, tzinfo=G.BRASILIA)
pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="Node.js ausente")


def _tem_playwright() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


com_navegador = pytest.mark.skipif(not _tem_playwright(), reason="Playwright ausente")


@pytest.fixture(scope="module")
def boletim(tmp_path_factory):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(G.time, "sleep", lambda s: None)
        return G.gerar(AGORA, buscar=lambda polo, cliente, agora: MET, destino=tmp_path_factory.mktemp("campo"))


def com_alerta(b: dict) -> dict:
    """Pior caso de altura: trovoada em quatro regiões."""
    b = copy.deepcopy(b)
    nomes = [r["nome"] for r in b["regioes"][:4]]
    b["alerta"] = {"titulo": "Atenção · trovoadas previstas", "itens": [f"{n}: chuva com trovoada." for n in nomes] +
                   ["Raios: recolha animais de áreas abertas e de perto de cercas de arame; não opere máquinas em campo aberto durante a trovoada."]}
    return b


def test_vigencia_segue_as_regras_da_tela(boletim):
    assert C.motivo_vencido(boletim, AGORA, 18) is None
    assert C.motivo_vencido(boletim, AGORA + timedelta(hours=12), 18) is None          # 23h02 do mesmo dia
    assert "vencido" in C.motivo_vencido(boletim, AGORA + timedelta(hours=13), 18)     # dia seguinte
    atrasado = {**boletim, "dia": "2026-11-03"}                                        # mesmo dia, gerado há 19 h
    assert "desatualizado" in C.motivo_vencido(atrasado, datetime(2026, 11, 3, 6, 5, tzinfo=G.BRASILIA), 18)
    manual = {k: v for k, v in boletim.items() if k != "geradoEm"}
    assert C.motivo_vencido(manual, AGORA, 18)


def test_proxima_emissao_com_data():
    assert C.proxima_emissao(datetime(2026, 11, 2, 5, 0, tzinfo=G.BRASILIA)) == "02/11 às 11h"
    assert C.proxima_emissao(datetime(2026, 11, 2, 11, 2, tzinfo=G.BRASILIA)) == "02/11 às 17h"
    assert C.proxima_emissao(datetime(2026, 11, 2, 17, 0, tzinfo=G.BRASILIA)) == "03/11 às 05h"
    assert C.proxima_emissao(datetime(2026, 12, 31, 17, 0, tzinfo=G.BRASILIA)) == "01/01 às 05h"


def test_conteudo_credito_logotipo_e_rotulos_de_campo_js(boletim):
    rot = C.rotulos(boletim["dia"])
    html = C.montar_html(boletim, rot)
    assert "MET Norway" in html and "CC BY 4.0" in html
    assert "Boletim informativo" in html
    assert "Segunda-feira, 2 de novembro de 2026" in html
    assert "11h02" in html and "23h59 de 02/11" in html and "02/11 às 17h" in html
    assert all(o["nome"] in html for o in rot["operacoes"])
    assert all(e["rotulo"] in html for e in rot["estados"].values())
    assert all(r["nome"] in html for r in boletim["regioes"])
    import base64
    assert base64.b64encode((RAIZ / "site/assets/marca/orgatec-original.png").read_bytes()).decode()[:200] in html  # logotipo original
    assert "<script" not in html and "http://" not in html and "https://" not in html  # sem rede, sem rastreamento


@pytest.mark.parametrize("formato", list(C.FORMATOS))
def test_sem_verde_nem_vermelho(boletim, formato):
    """Regra da Janela de Campo: verde só no WhatsApp; nada de vermelho de semáforo."""
    html = C.montar_html(com_alerta(boletim), C.rotulos(boletim["dia"]), formato)
    css = re.sub(r"url\(data:[^)]*\)|src=\"data:[^\"]*\"", "", html)
    for cor in set(re.findall(r"#([0-9a-fA-F]{6})\b", css)):
        r, g, b = (int(cor[i:i + 2], 16) / 255 for i in (0, 2, 4))
        h, luz, s = colorsys.rgb_to_hls(r, g, b)
        matiz = h * 360
        if s < 0.35 or luz < 0.12:
            continue  # cinzas e fundos quase pretos
        assert not 75 <= matiz <= 165, f"#{cor} é verde"
        assert not (matiz < 12 or matiz > 340), f"#{cor} é vermelho"


def _medir(htmls: list[str]) -> list[dict]:
    from playwright.sync_api import sync_playwright
    medidas = []
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page(viewport={"width": C.LARGURA, "height": C.ALTURA})
        for html in htmls:
            pg.set_content(html)
            pg.evaluate("document.fonts.ready.then(() => 1)")
            medidas.append(pg.evaluate("""() => { const r = [...document.querySelectorAll('.z *')].map(e => e.getBoundingClientRect());
              return {alto: Math.min(...r.map(x => x.top)), baixo: Math.max(...r.map(x => x.bottom)),
                      esquerda: Math.min(...r.map(x => x.left)), direita: Math.max(...r.map(x => x.right))}; }"""))
        nav.close()
    return medidas


@com_navegador
def test_cabe_na_area_segura_de_cada_rede_mesmo_com_alerta(boletim):
    """Nada do cartão nas faixas que a interface cobre: nome e resposta no WhatsApp e no Instagram; botões e legenda no TikTok."""
    from concurrent.futures import ThreadPoolExecutor
    rot = C.rotulos(boletim["dia"])
    casos = [(f, b) for f in C.FORMATOS for b in (boletim, com_alerta(boletim))]
    with ThreadPoolExecutor(max_workers=1) as ex:  # thread própria: a suíte e2e mantém um Playwright síncrono aberto
        medidas = ex.submit(_medir, [C.montar_html(b, rot, f) for f, b in casos]).result()
    for (formato, _), m in zip(casos, medidas):
        alto, direita, baixo, esquerda = C.FORMATOS[formato]["margens"]
        assert m["alto"] >= alto - 1 and m["baixo"] <= C.ALTURA - baixo + 1, (formato, m)
        assert m["esquerda"] >= esquerda - 1 and m["direita"] <= C.LARGURA - direita + 1, (formato, m)


@com_navegador
def test_gera_um_png_1080x1920_por_formato_no_site_e_no_pc(boletim, tmp_path):
    from PIL import Image
    site, pc = tmp_path / "site", tmp_path / "pc"
    pub = C.gerar(boletim, AGORA, destino=site, pc=pc)
    assert pub == {"status": site / "cartao-status.png", "tiktok": site / "cartao-tiktok.png"}
    for nome, arq in pub.items():
        assert Image.open(arq).size == (1080, 1920)
        assert (pc / C.FORMATOS[nome]["pc"]).read_bytes() == arq.read_bytes()
    assert pub["status"].read_bytes() != pub["tiktok"].read_bytes()
    assert (pc / "arquivo" / "janela-de-campo-2026-11-02-11h02.png").exists()
    assert (pc / "arquivo" / "janela-de-campo-2026-11-02-11h02-tiktok.png").exists()
    assert not list(tmp_path.rglob("*.tmp.png"))


def test_boletim_vencido_nao_gera_cartao(boletim, tmp_path):
    with pytest.raises(C.CartaoVencido):
        C.gerar(boletim, AGORA + timedelta(days=1), destino=tmp_path / "site", pc=tmp_path / "pc")
    assert not list(tmp_path.iterdir())


def test_retira_dos_caminhos_fixos_so_os_cartoes_de_dia_anterior(tmp_path):
    site, pc = tmp_path / "site", tmp_path / "pc"
    (pc / "arquivo").mkdir(parents=True)
    site.mkdir()
    fixos = [site / f["site"] for f in C.FORMATOS.values()] + [pc / f["pc"] for f in C.FORMATOS.values()]
    datado = pc / "arquivo" / "janela-de-campo-2026-11-01-17h00-tiktok.png"
    ontem = (AGORA - timedelta(days=1)).timestamp()
    for arq in fixos + [datado]:
        arq.write_bytes(b"png")
        os.utime(arq, (ontem, ontem))
    assert C.retirar_vencido(AGORA, destino=site, pc=pc)
    assert not any(a.exists() for a in fixos) and datado.exists()
    (site / "cartao-tiktok.png").write_bytes(b"png")  # cartão de hoje fica
    assert not C.retirar_vencido(datetime.now(G.BRASILIA), destino=site, pc=pc) and (site / "cartao-tiktok.png").exists()


def test_arquivo_do_pc_guarda_7_dias(tmp_path):
    for d in range(20, 32):
        (tmp_path / f"janela-de-campo-2026-10-{d:02d}-05h00.png").write_bytes(b"png")
        (tmp_path / f"janela-de-campo-2026-10-{d:02d}-05h00-tiktok.png").write_bytes(b"png")
    (tmp_path / "outro.png").write_bytes(b"png")
    C.limpar_arquivo(datetime(2026, 11, 2, 5, 0, tzinfo=G.BRASILIA), tmp_path)
    dias = sorted(a.name[16:26] for a in tmp_path.glob("janela-de-campo-*.png"))
    assert dias[0] == "2026-10-26" and len(dias) == 12 and (tmp_path / "outro.png").exists()


def test_falha_no_cartao_nao_impede_publicar_o_boletim(monkeypatch, caplog):
    publicou = []
    monkeypatch.setattr(G, "configurar_log", lambda: None)
    monkeypatch.setattr(G, "atualizar_noticias", lambda: True)
    monkeypatch.setattr(G, "gerar", lambda: {"dia": "2026-11-02"})
    monkeypatch.setattr(G, "publicar", lambda: publicou.append(True))
    monkeypatch.setattr(C, "gerar", lambda b: (_ for _ in ()).throw(RuntimeError("Chromium não abriu")))
    with caplog.at_level(logging.ERROR, logger="orgatec.campo"):
        assert G.main(["--publicar"]) == 0
    assert publicou == [True]
    assert "cartão do status não gerado: Chromium não abriu" in caplog.text


def test_endereco_do_site_so_com_o_site_em_producao(boletim):
    """Regra das peças do marketing: nada de levar o público ao site enquanto ele estiver em homologação."""
    rot = C.rotulos(boletim["dia"])
    assert rot["ambiente"] in ("homologacao", "producao")
    assert C.PAGINA not in C.montar_html(boletim, {**rot, "ambiente": "homologacao"})
    assert C.PAGINA in C.montar_html(boletim, {**rot, "ambiente": "producao"})


def test_hosting_revalida_o_cartao_publicado():
    """Os cartões têm nome fixo e mudam 3 vezes ao dia: a regra de /dados/ vem DEPOIS da das imagens (a última vale)."""
    import preparar_firebase as pf
    assert G.DADOS.relative_to(RAIZ / "site").as_posix().startswith("dados/")  # onde gerar() publica os cartões
    for cfg in (pf.firebase_json(None, indexar=False), json.loads((RAIZ / "firebase.json").read_text(encoding="utf-8"))):
        fontes = [h["source"] for h in cfg["hosting"]["headers"]]
        regra = cfg["hosting"]["headers"][fontes.index("/dados/**")]["headers"]
        assert regra == [{"key": "Cache-Control", "value": "no-cache"}]
        assert fontes.index("/dados/**") > fontes.index("**/*.@(png|svg|ico|jpg|webp|woff2)")


def test_boletim_que_falha_retira_o_cartao_vencido(monkeypatch):
    retirou = []
    monkeypatch.setattr(G, "configurar_log", lambda: None)
    monkeypatch.setattr(G, "atualizar_noticias", lambda: False)
    monkeypatch.setattr(G, "gerar", lambda: (_ for _ in ()).throw(G.FonteIndisponivel("fora do ar")))
    monkeypatch.setattr(C, "retirar_vencido", lambda: retirou.append(True))
    assert G.main([]) == 1 and retirou == [True]


def test_cartao_traz_o_veredito_primeiro_e_os_glifos_da_pagina(boletim):
    """V4 da Janela de Campo 2: o veredito do boletim vem antes da tabela, escrito pela mesma regra da página (campo-veredito.js)."""
    ver = C.veredito(boletim)
    html = C.montar_html(boletim, C.rotulos(boletim["dia"]))
    assert ver["titulo"] in html
    assert html.index('class="vt"') < html.index('class="info"') < html.index('class="tabela"')
    assert all(f"gl-{e}" in html for e in ("ok", "atencao"))
    assert "Sem previsão" in html  # a legenda tem os quatro glifos
    assert len(ver["matriz"]) == len(boletim["regioes"]) and all(len(linha) == 5 for linha in ver["matriz"])


def test_veredito_sem_regioes_nao_quebra_o_cartao(boletim):
    assert C.veredito({"regioes": []}) is None
