"""Cartão da Janela de Campo para o status do WhatsApp Business, os stories (pedido S2 do marketing, 02/11/2026) e o
modo foto do TikTok (03/11/2026).

A cada boletim publicado, tools/gerar_boletim_campo.py chama gerar(): imagens PNG 1080 × 1920 com o estado de cada
operação por região (favorável, com restrição, evitar), a data, a hora de emissão e até quando o boletim vale. Um
arquivo por formato (FORMATOS): o mesmo cartão, encaixado na área que a interface de cada rede deixa livre.

Onde fica o cartão mais recente:
    no PC:       cartoes-status/janela-de-campo.png e janela-de-campo-tiktok.png
                 (cópias datadas dos últimos 7 dias em cartoes-status/arquivo/)
    no site:     site/dados/campo/cartao-status.png e cartao-tiktok.png → https://orgatec.io/dados/campo/...
                 (publicados junto com o boletim, para abrir e salvar no celular de onde se posta)

Regras da Janela de Campo: sem verde nem vermelho (os estados usam as cores do site: azul e âmbar, com ícone);
boletim vencido ou desatualizado não gera cartão novo, e o cartão do dia anterior sai dos caminhos fixos
(retirar_vencido) para ninguém postar previsão vencida. Crédito obrigatório da fonte: MET Norway, licença CC BY 4.0.

Uso avulso (refaz os cartões do boletim atual, sem publicar):  python tools/cartao_campo.py
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess  # nosec B404 — só executa node com argumentos fixos
import sys
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

import imagem_marca as M
from gerar_boletim_campo import BRASILIA, DADOS, HORARIOS, RAIZ, configurar_log

PC = RAIZ / "cartoes-status"
ARQUIVO = "arquivo"
DIAS_ARQUIVO = 7
LARGURA, ALTURA = 1080, 1920
PAGINA = "orgatec.io/rural/janela-de-campo.html"

# margens = (alto, direita, baixo, esquerda) em px: faixas que a interface de cada rede cobre. escala = tamanho do
# cartão dentro da área livre (o desenho é o mesmo). site = nome publicado em site/dados/campo/; pc = nome em PC.
FORMATOS = {
    # WhatsApp e stories do Instagram: nome e barra de progresso no alto, campo de resposta embaixo
    "status": {"margens": (140, 72, 210, 72), "escala": 1.0, "site": "cartao-status.png", "pc": "janela-de-campo.png"},
    # TikTok, modo foto: coluna de botões à direita e legenda embaixo. O TikTok não publica as medidas; estas são as
    # mais conservadoras dos guias consultados em 03/11/2026 (moda.app: 130 no alto, 480 embaixo, 150 à direita).
    "tiktok": {"margens": (130, 150, 480, 60), "escala": 0.8, "site": "cartao-tiktok.png", "pc": "janela-de-campo-tiktok.png"},
}

log = logging.getLogger("orgatec.campo")

# Ícones dos estados (mesmo significado de ✓ ! ✕ em campo.js), desenhados em SVG para não depender de glifo da fonte
ICONES = {
    "ok": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "atencao": '<path d="M12 5v9"/><path d="M12 19h.01"/>',
    "evitar": '<path d="M6.5 6.5l11 11"/><path d="M17.5 6.5l-11 11"/>',
}

CSS = """
.c{height:100%;background:radial-gradient(900px 700px at 100% 0,var(--brand-soft),transparent 70%),var(--bg)}
.z{display:flex;flex-direction:column;gap:24px}
svg{fill:none;stroke:currentColor;stroke-width:3.2;stroke-linecap:round;stroke-linejoin:round;flex:none}
.topo{display:flex;align-items:center;gap:22px}
.marca{font:800 42px/1 var(--f-display);letter-spacing:-.02em}
.sub{font:500 17px/1 var(--f-mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-top:10px}
.eyebrow{font:500 22px/1 var(--f-mono);letter-spacing:.14em;text-transform:uppercase;color:var(--hl)}
h1{font:700 80px/1 var(--f-display);letter-spacing:-.03em;margin-top:14px}
.dia{font:600 34px/1.2 var(--f-body);color:var(--ink);margin-top:14px}
.info{display:grid;grid-template-columns:repeat(3,1fr);background:var(--surface);border:1px solid var(--line);border-radius:22px}
.info div{padding:16px 22px}.info div+div{border-left:1px solid var(--line)}
.info b{display:block;font:500 16px/1 var(--f-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.info span{display:block;font:600 28px/1.15 var(--f-display);margin-top:10px}
.legenda{display:flex;gap:14px;flex-wrap:wrap}
.selo{display:inline-flex;align-items:center;gap:10px;padding:8px 18px 8px 12px;border-radius:999px;font:600 24px/1 var(--f-body);border:2px solid transparent}
.ic{display:grid;place-items:center;border-radius:16px;border:2px solid transparent}
.ok{background:var(--brand-soft);color:var(--brand)}
.atencao{background:var(--warn-soft);color:var(--warn);border-color:var(--warn)}
.evitar{background:var(--warn);color:var(--surface)}
.tabela{flex:1;display:grid;grid-template-columns:300px repeat(5,1fr);grid-template-rows:auto;grid-auto-rows:1fr;
  background:var(--surface);border:1px solid var(--line);border-radius:22px;padding:4px 18px}
.tabela>*{display:flex;align-items:center;justify-content:center;border-bottom:1px solid var(--line)}
.tabela>.fim{border-bottom:0}
.op{font:600 18px/1.15 var(--f-body);color:var(--muted);text-align:center;padding:12px 2px}
.reg{flex-direction:column;align-items:flex-start;justify-content:center;padding:10px 10px 10px 0}
.reg strong{font:600 28px/1.1 var(--f-display)}
.reg small{font:400 19px/1.25 var(--f-body);color:var(--muted);margin-top:6px}
.ic.grande{width:88px;height:70px}
.alerta{border:2px solid var(--warn);background:var(--warn-soft);border-radius:22px;padding:18px 24px}
.alerta strong{display:block;font:700 26px/1.1 var(--f-display);color:var(--warn);text-transform:uppercase;letter-spacing:.02em}
.alerta p{font:400 21px/1.3 var(--f-body);margin-top:8px}
.rodape{display:flex;flex-direction:column;gap:6px;font:400 20px/1.3 var(--f-body);color:var(--muted)}
.rodape .aviso{color:var(--ink)}
.rodape .url{font:500 20px/1 var(--f-mono);color:var(--brand);margin-top:4px}
"""


class CartaoVencido(RuntimeError):
    """O boletim já venceu (dia anterior) ou está desatualizado: não se faz cartão para postar."""


def rotulos(dia: str) -> dict:
    """Operações, estados, limite de horas e o dia por extenso de site/assets/js/campo.js (fonte única da tela) e o
    ambiente de site/assets/js/config.js."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", dia or ""):
        raise ValueError(f"dia inválido no boletim: {dia!r}")
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js não encontrado no PATH (necessário para ler site/assets/js/campo.js)")
    js = ("const c=require('./site/assets/js/campo.js'),a=require('./site/assets/js/config.js').ambiente;"
          "process.stdout.write(JSON.stringify({operacoes:c.OPERACOES,estados:c.ESTADOS,limiteHoras:c.LIMITE_HORAS,"
          "diaExtenso:c.formatarDia(process.argv[1]),ambiente:a}))")
    r = subprocess.run([node, "-e", js, dia], capture_output=True, text=True, encoding="utf-8", cwd=RAIZ, check=False)  # nosec B603
    if r.returncode != 0:
        raise RuntimeError(f"leitura de campo.js falhou: {r.stderr.strip()}")
    return json.loads(r.stdout)


def gerado_em(boletim: dict) -> datetime:
    return datetime.fromisoformat(boletim["geradoEm"]).astimezone(BRASILIA)


def motivo_vencido(boletim: dict, agora: datetime, limite_horas: float) -> str | None:
    """Mesmas regras da tela (campo.situacao e LIMITE_HORAS): None quando o boletim ainda vale."""
    hoje = agora.astimezone(BRASILIA).date().isoformat()
    if boletim["dia"] < hoje:
        return f"boletim de {boletim['dia']} vencido"
    if not boletim.get("geradoEm"):
        return "boletim sem hora de emissão (só o automático gera cartão)"
    horas = (agora - gerado_em(boletim)).total_seconds() / 3600
    if horas > limite_horas:
        return f"boletim desatualizado: gerado há {round(horas)} horas"
    return None


def proxima_emissao(g: datetime) -> str:
    """Próximo horário do agendador, com data (o cartão circula depois da emissão: 'amanhã' perderia o sentido)."""
    for h in HORARIOS:
        if g.hour < h:
            return f"{g:%d/%m} às {h:02d}h"
    return f"{g + timedelta(days=1):%d/%m} às {HORARIOS[0]:02d}h"


def icone(estado: str, tamanho: int) -> str:
    return f'<svg viewBox="0 0 24 24" width="{tamanho}" height="{tamanho}" aria-hidden="true">{ICONES[estado]}</svg>'


def montar_html(boletim: dict, rot: dict, formato: str = "status") -> str:
    alto, direita, baixo, esquerda = FORMATOS[formato]["margens"]
    escala = FORMATOS[formato]["escala"]
    g = gerado_em(boletim)
    dia = rot["diaExtenso"]
    estados, ops = rot["estados"], rot["operacoes"]
    legenda = "".join(f'<span class="selo {s}">{icone(s, 26)}{escape(e["rotulo"])}</span>' for s, e in estados.items())
    celulas = ['<div></div>'] + [f'<div class="op">{escape(o["nome"])}</div>' for o in ops]
    regioes = boletim["regioes"]
    for i, r in enumerate(regioes):
        fim = " fim" if i == len(regioes) - 1 else ""  # a janela de horário de cada região fica na página (PAGINA)
        celulas.append(f'<div class="reg{fim}"><strong>{escape(r["nome"])}</strong><small>{escape(r["uf"])}</small></div>')
        for o in ops:
            s = r["ops"][o["id"]][0]
            celulas.append(f'<div class="{fim.strip()}"><span class="ic grande {s}" title="{escape(estados[s]["rotulo"])}">{icone(s, 44)}</span></div>')
    alerta = ""
    if boletim.get("alerta"):
        itens = boletim["alerta"].get("itens") or []
        nomes = [t.split(":")[0] for t in itens[:-1]]
        texto = (f"Regiões: {', '.join(nomes)}. " if nomes else "") + (itens[-1] if itens else "")
        alerta = f'<section class="alerta"><strong>{escape(boletim["alerta"]["titulo"])}</strong><p>{escape(texto)}</p></section>'
    # Endereço do site só com o site em produção: as peças das redes não levam o site em homologação (regra do marketing)
    url = f'<p class="url">{PAGINA}</p>' if rot.get("ambiente") == "producao" else ""
    # A área livre recebe o cartão em escala: com zoom, a altura declarada é multiplicada por ele
    caixa = f"padding:{alto}px {direita}px {baixo}px {esquerda}px"
    miolo = f"zoom:{escala};height:{(ALTURA - alto - baixo) / escala:.2f}px"
    corpo = f"""<main class="c" style="{caixa}"><div class="z" style="{miolo}">
<header class="topo">{M.logo_img(96)}<div><p class="marca">ORGATEC</p><p class="sub">Inteligência Tributária</p></div></header>
<section><p class="eyebrow">Boletim informativo · tempo no agro</p><h1>Janela de Campo</h1>
<p class="dia">{escape(dia[:1].upper() + dia[1:])}</p></section>
<section class="info"><div><b>Emitido às</b><span>{g:%H}h{g:%M}</span></div><div><b>Vale até</b><span>23h59 de {g:%d/%m}</span></div>
<div><b>Próxima</b><span>{proxima_emissao(g)}</span></div></section>
<section class="legenda">{legenda}</section>
{alerta}
<section class="tabela">{''.join(celulas)}</section>
<footer class="rodape"><p class="aviso">Boletim informativo: não substitui os avisos oficiais do INMET nem a avaliação no local. Horários de Brasília; critérios em validação técnica.</p>
<p>Previsão: MET Norway (api.met.no), licença CC BY 4.0.</p>{url}</footer>
</div></main>"""
    return M.documento(corpo, CSS, LARGURA, ALTURA)


def _copiar(origem: Path, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.stem + ".tmp.png")
    shutil.copyfile(origem, tmp)
    tmp.replace(destino)


def limpar_arquivo(agora: datetime, pasta: Path = PC / ARQUIVO) -> None:
    corte = (agora.astimezone(BRASILIA) - timedelta(days=DIAS_ARQUIVO)).date().isoformat()
    for arq in pasta.glob("janela-de-campo-*.png"):
        m = re.match(r"janela-de-campo-(\d{4}-\d{2}-\d{2})-", arq.name)
        if m and m.group(1) < corte:
            arq.unlink()


def gerar(boletim: dict | None = None, agora: datetime | None = None, destino: Path = DADOS, pc: Path = PC) -> dict[str, Path]:
    """Grava os cartões do boletim (o atual, se nenhum for passado), um por formato. Devolve {formato: caminho publicado}.
    CartaoVencido se o boletim não vale mais; nesse caso nenhum arquivo é tocado."""
    boletim = boletim or json.loads((DADOS / "atual.json").read_text(encoding="utf-8"))
    agora = (agora or datetime.now(BRASILIA)).astimezone(BRASILIA)
    rot = rotulos(boletim["dia"])
    motivo = motivo_vencido(boletim, agora, rot["limiteHoras"])
    if motivo:
        raise CartaoVencido(motivo)
    publicados = {nome: destino / f["site"] for nome, f in FORMATOS.items()}
    M.renderizar([(montar_html(boletim, rot, nome), LARGURA, ALTURA, saida) for nome, saida in publicados.items()])
    g = gerado_em(boletim)
    for nome, saida in publicados.items():
        _copiar(saida, pc / FORMATOS[nome]["pc"])
        sufixo = "" if nome == "status" else f"-{nome}"
        _copiar(saida, pc / ARQUIVO / f"janela-de-campo-{boletim['dia']}-{g:%H}h{g:%M}{sufixo}.png")
    limpar_arquivo(agora, pc / ARQUIVO)
    log.info("cartões do status e do TikTok gravados em %s e %s", destino, pc)
    return publicados


def retirar_vencido(agora: datetime | None = None, destino: Path = DADOS, pc: Path = PC) -> bool:
    """Boletim do dia não saiu: tira dos caminhos fixos os cartões de dia anterior (os arquivos datados continuam no PC)."""
    agora = (agora or datetime.now(BRASILIA)).astimezone(BRASILIA)
    retirou = False
    for f in FORMATOS.values():
        for arq in (destino / f["site"], pc / f["pc"]):
            if arq.exists() and datetime.fromtimestamp(arq.stat().st_mtime, BRASILIA).date() < agora.date():
                arq.unlink()
                retirou = True
    if retirou:
        log.warning("cartões de dia anterior retirados dos caminhos fixos (boletim de hoje não gerado)")
    return retirou


def main() -> int:
    configurar_log()
    try:
        for caminho in gerar().values():
            print(caminho)
    except CartaoVencido as erro:
        log.warning("cartão do status não gerado: %s", erro)
        retirar_vencido()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
