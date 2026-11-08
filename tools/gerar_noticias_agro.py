"""Notícias e legislação por atividade agropecuária (cards Orgatec Audi Agro da Janela de Campo).

Lê os feeds RSS de tools/agro_fontes.json (Agência Câmara por tema, Agência Senado e Receita Federal),
filtra por palavras-chave de cada atividade e de "tributação rural" e grava site/dados/agro/noticias.json.
Só título, link, data e fonte (os textos ficam no site de origem). Chamado por tools/gerar_boletim_campo.py nas
rodadas das 05h, 11h e 17h; também roda sozinho:  python tools/gerar_noticias_agro.py

Os feeds são rasos (de 1 a 10 dias de notícias), então cada rodada acumula o que já foi coletado em
site/dados/agro/historico.json (180 dias) e o card mostra as dos últimos 90 dias. Sem notícia recente, o card mostra a
última que houver (com a data) e os links das fontes oficiais; nada é inventado.

Se um feed falhar, os itens válidos dele da rodada anterior continuam, marcados com a data em que foram
coletados, e a falha aparece em "fontes" (o site avisa).

Termos de cada fonte (o que permite e o que o site faz): tools/agro_fontes.json, chaves "termos", "acompanhe" e
"descartadas". Título de feed sob licença sem derivações (gov.br, CC BY-ND) e política do Senado (sem descaracterizar)
exigem o título inteiro: título com mais de 300 caracteres não é listado, em vez de ser cortado.
"""

from __future__ import annotations

import html
import json
import logging
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx
from defusedxml import ElementTree

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "tools" / "agro_fontes.json"
DESTINO = RAIZ / "site" / "dados" / "agro" / "noticias.json"
USER_AGENT = "orgatec.io contato@orgatec.io"
BRASILIA = timezone(timedelta(hours=-3))
DIAS_MAX = 90          # notícia mais antiga que isso não entra (o feed da Receita mistura itens de anos atrás)
RETENCAO_DIAS = 180    # quanto tempo o histórico guarda (a "última notícia" de um tema sem notícia recente sai daqui)
TITULO_MAX = 300
POR_ATIVIDADE = 3
TRIBUTACAO = 5

log = logging.getLogger("orgatec.agro")


def normalizar(texto: str) -> str:
    """Minúsculas e sem acento, para casar "suín" com "suínos" e "suinos"."""
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def texto_limpo(bruto: str | None, limite: int = 220) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", " ", bruto or ""))
    return re.sub(r"\s+", " ", t).strip()[:limite]


def data_iso(bruta: str | None) -> str | None:
    if not bruta:
        return None
    try:
        d = parsedate_to_datetime(bruta.strip())
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(bruta.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(BRASILIA).isoformat(timespec="minutes")


def ler_feed(conteudo: bytes, feed: dict, coletado: str) -> list[dict]:
    """Itens do RSS 2.0: título, link (link ou guid com http), data e um resumo curto só para o filtro."""
    raiz = ElementTree.fromstring(conteudo)
    itens = []
    for it in raiz.iter("item"):
        titulo = texto_limpo(it.findtext("title"), limite=10_000)
        if len(titulo) > TITULO_MAX:  # o título não é cortado (licença sem derivações; política do Senado): não é listado
            continue
        link = (it.findtext("link") or "").strip()
        guid = (it.findtext("guid") or "").strip()
        if not link.startswith("http") and guid.startswith("http"):
            link = guid
        if not titulo or not re.match(r"^https?://", link):
            continue
        itens.append({"titulo": titulo, "link": link, "data": data_iso(it.findtext("pubDate")),
                      "fonte": feed["id"], "fonteNome": feed["nome"], "coletadoEm": coletado,
                      "_filtro": normalizar(titulo + " " + texto_limpo(it.findtext("description"), 600))})
    return itens


def casa(item: dict, palavras: list[str]) -> bool:
    """A palavra-chave precisa começar uma palavra ("gado" não casa com "empregado"; "suín" casa com "suínos")."""
    return any(re.search(r"(?<![a-z0-9])" + re.escape(normalizar(p)), item["_filtro"]) for p in palavras)


def classificar(itens: list[dict], cfg: dict, agora: datetime) -> tuple[dict, list]:
    limite = (agora - timedelta(days=DIAS_MAX)).isoformat()
    vistos, recentes = set(), []
    for i in sorted(itens, key=lambda x: x["data"] or "", reverse=True):
        if not i["data"] or i["data"] < limite or i["link"] in vistos:
            continue
        vistos.add(i["link"])
        recentes.append(i)
    sem_filtro = lambda i: {k: v for k, v in i.items() if not k.startswith("_")}
    atividades = {a["id"]: [sem_filtro(i) for i in recentes if casa(i, a["palavras"])][:POR_ATIVIDADE] for a in cfg["atividades"]}
    tributacao = [sem_filtro(i) for i in recentes if casa(i, cfg["tributacao"]["palavras"])][:TRIBUTACAO]
    return atividades, tributacao


def ultimas_noticias(itens: list[dict], cfg: dict, atividades: dict, tributacao: list) -> dict:
    """Para cada tema SEM notícia dos últimos 90 dias (as atividades e a "tributacao"), a mais recente que o histórico tiver
    (de qualquer idade dentro da retenção) ou None. Tema com notícia recente fica com None: o card já mostra a lista."""
    ordenados = sorted((i for i in itens if i.get("data")), key=lambda x: x["data"], reverse=True)

    def primeira(palavras):
        achada = next((i for i in ordenados if casa(i, palavras)), None)
        return {k: v for k, v in achada.items() if not k.startswith("_")} if achada else None
    ultimas = {a["id"]: (None if atividades.get(a["id"]) else primeira(a["palavras"])) for a in cfg["atividades"]}
    ultimas["tributacao"] = None if tributacao else primeira(cfg["tributacao"]["palavras"])
    return ultimas


def ler_json(caminho: Path) -> dict:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def baixar(feed: dict, cliente: httpx.Client) -> bytes:
    r = cliente.get(feed["url"], headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)
    r.raise_for_status()
    return r.content


def gerar(agora: datetime | None = None, baixar=baixar, destino: Path = DESTINO, historico: Path | None = None) -> dict:
    agora = (agora or datetime.now(BRASILIA)).astimezone(BRASILIA)
    coletado = agora.isoformat(timespec="minutes")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    historico = historico or destino.with_name("historico.json")
    # o noticias.json antigo guardava os itens dentro dele: vale como histórico na primeira rodada depois da mudança
    anterior = ler_json(historico) or ler_json(destino)
    corte = (agora - timedelta(days=RETENCAO_DIAS)).isoformat()
    guardados = [i for i in anterior.get("itens", []) if i.get("data") and i["data"] >= corte]
    itens, fontes = [], []
    with httpx.Client() as cliente:
        for feed in cfg["feeds"]:
            situacao = {"id": feed["id"], "nome": feed["nome"], "url": feed["url"], "portal": feed.get("portal")}
            antigos = [i for i in guardados if i.get("fonte") == feed["id"]]
            try:
                novos = ler_feed(baixar(feed, cliente), feed, coletado)
                links = {n["link"] for n in novos}
                acumulados = [i for i in antigos if i["link"] not in links]  # saíram do feed, mas seguem valendo
                itens += novos + acumulados
                situacao.update(ok=True, coletadoEm=coletado, itens=len(novos), acumulados=len(acumulados))
            except (httpx.HTTPError, ElementTree.ParseError, ValueError) as erro:
                # Último dado válido: os itens desta fonte da rodada anterior, com a data da coleta original
                itens += antigos
                ultima = max((i["coletadoEm"] for i in antigos), default=None)
                situacao.update(ok=False, erro=str(erro)[:200], ultimaColetaValida=ultima, itens=len(antigos))
                log.warning("feed %s indisponível: %s (mantidos %d itens de %s)", feed["id"], erro, len(antigos), ultima)
            fontes.append(situacao)
    # a retenção vale para tudo, inclusive o que ainda vem no feed (o da Receita mistura itens de 2022)
    com_data = sorted((i for i in itens if i.get("data") and i["data"] >= corte), key=lambda x: x["data"], reverse=True)
    atividades, tributacao = classificar(com_data, cfg, agora)
    ultimas = ultimas_noticias(com_data, cfg, atividades, tributacao)
    saida = {"geradoEm": coletado, "janelaDias": DIAS_MAX, "fontes": fontes, "atividades": atividades, "tributacao": tributacao,
             "ultimas": ultimas, "acompanhe": [{"nome": a["nome"], "url": a["url"]} for a in cfg.get("acompanhe", [])]}
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(saida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    historico.write_text(json.dumps({"geradoEm": coletado, "itens": com_data}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    log.info("notícias do agro: %d itens no histórico, %d fontes com falha", len(com_data), sum(not f["ok"] for f in fontes))
    return saida


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    gerar()
