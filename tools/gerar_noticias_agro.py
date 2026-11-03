"""Notícias e legislação por atividade agropecuária (cards Orgatec Audi Agro da Janela de Campo).

Lê os feeds RSS de tools/agro_fontes.json (Agência Câmara · Agropecuária, Agência Senado e Receita Federal),
filtra por palavras-chave de cada atividade e de "tributação rural" e grava site/dados/agro/noticias.json.
Só título, link, data e fonte (os textos ficam no site de origem). Chamado por tools/gerar_boletim_campo.py nas
rodadas das 05h, 11h e 17h; também roda sozinho:  python tools/gerar_noticias_agro.py

Se um feed falhar, os itens válidos dele da rodada anterior continuam, marcados com a data em que foram
coletados, e a falha aparece em "fontes" (o site avisa). Nada é inventado: sem notícia na fonte, o card diz isso.
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
USER_AGENT = "orgatec.io orgatec.cloud@gmail.com"
BRASILIA = timezone(timedelta(hours=-3))
DIAS_MAX = 90          # notícia mais antiga que isso não entra (o feed da Receita mistura itens de anos atrás)
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
        titulo = texto_limpo(it.findtext("title"))
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


def baixar(feed: dict, cliente: httpx.Client) -> bytes:
    r = cliente.get(feed["url"], headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)
    r.raise_for_status()
    return r.content


def gerar(agora: datetime | None = None, baixar=baixar, destino: Path = DESTINO) -> dict:
    agora = (agora or datetime.now(BRASILIA)).astimezone(BRASILIA)
    coletado = agora.isoformat(timespec="minutes")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    anterior = json.loads(destino.read_text(encoding="utf-8")) if destino.exists() else {}
    guardados = anterior.get("itens", [])
    itens, fontes = [], []
    with httpx.Client() as cliente:
        for feed in cfg["feeds"]:
            situacao = {"id": feed["id"], "nome": feed["nome"], "url": feed["url"]}
            try:
                novos = ler_feed(baixar(feed, cliente), feed, coletado)
                itens += novos
                situacao.update(ok=True, coletadoEm=coletado, itens=len(novos))
            except (httpx.HTTPError, ElementTree.ParseError, ValueError) as erro:
                # Último dado válido: os itens desta fonte da rodada anterior, com a data da coleta original
                antigos = [i for i in guardados if i.get("fonte") == feed["id"]]
                itens += antigos
                ultima = max((i["coletadoEm"] for i in antigos), default=None)
                situacao.update(ok=False, erro=str(erro)[:200], ultimaColetaValida=ultima, itens=len(antigos))
                log.warning("feed %s indisponível: %s (mantidos %d itens de %s)", feed["id"], erro, len(antigos), ultima)
            fontes.append(situacao)
    atividades, tributacao = classificar(itens, cfg, agora)
    saida = {"geradoEm": coletado, "fontes": fontes, "atividades": atividades, "tributacao": tributacao,
             "itens": [i for i in itens if i.get("data")]}
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(saida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    log.info("notícias do agro: %d itens, %d fontes com falha", len(saida["itens"]), sum(not f["ok"] for f in fontes))
    return saida


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    gerar()
