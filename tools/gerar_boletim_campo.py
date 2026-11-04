"""Janela de Campo automática: busca a previsão hora a hora do MET Norway para os polos de tools/campo_polos.json,
monta o boletim com site/assets/js/campo-regras.js (via tools/campo_montar.js) e grava em site/dados/campo/.
Depois de gravar, faz os cartões para o status do WhatsApp, os stories e o TikTok (tools/cartao_campo.py); erro no cartão só vai
para o log e não impede a publicação.

Uso:
    python tools/gerar_boletim_campo.py                          gera o boletim de agora (não publica)
    python tools/gerar_boletim_campo.py --publicar               gera e publica no Firebase Hosting
    python tools/gerar_boletim_campo.py --instalar-agendador     cria as tarefas das 05h, 11h e 17h no Windows
    python tools/gerar_boletim_campo.py --remover-agendador      remove as tarefas
    (--simular mostra os comandos do agendador sem executar)

Regras da fonte (api.met.no, termos conferidos em 02/11/2026): identificar o site no User-Agent, respeitar o
cabeçalho Expires (cache em tools/cache/campo) e não consultar com frequência. Licença CC BY 4.0: o site cita
"MET Norway". O CPTEC/INPE não é usado: os termos dele proíbem reproduzir os dados em site comercial sem
autorização. Se a previsão de algum polo falhar, nada é gravado nem publicado e o boletim anterior continua no ar.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess  # nosec B404 — só executa node e schtasks com argumentos fixos
import sys
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parent.parent
POLOS = RAIZ / "tools" / "campo_polos.json"
DADOS = RAIZ / "site" / "dados" / "campo"
CACHE = RAIZ / "tools" / "cache" / "campo"
LOG = RAIZ / "tools" / "logs" / "campo.log"
MONTAR = RAIZ / "tools" / "campo_montar.js"

URL_MET = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
# Contato exigido pelos termos do MET Norway
USER_AGENT = "orgatec.io contato@orgatec.io"
BRASILIA = timezone(timedelta(hours=-3))  # o Brasil não tem horário de verão desde 2019
HORARIOS = (5, 11, 17)
ARQUIVO_DIAS = 30
TAREFA = "ORGATEC\\JanelaCampo{h:02d}h"

log = logging.getLogger("orgatec.campo")


class FonteIndisponivel(RuntimeError):
    """A previsão de um polo não veio: o boletim não é gerado (melhor o anterior, marcado, do que um incompleto)."""


def configurar_log() -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(LOG, encoding="utf-8"), logging.StreamHandler()])


def carregar_polos() -> dict:
    cfg = json.loads(POLOS.read_text(encoding="utf-8"))
    regiao_de = {p: r["id"] for r in cfg["regioes"] for p in r["polos"]}
    for p in cfg["polos"]:
        p["regiao"] = regiao_de[p["id"]]
    return cfg


def buscar_met(polo: dict, cliente: httpx.Client, agora: datetime) -> dict:
    """Previsão do polo com cache: dentro do Expires usa o arquivo; depois, pergunta com If-Modified-Since."""
    CACHE.mkdir(parents=True, exist_ok=True)
    arq = CACHE / f"met-{polo['id']}.json"
    guardado = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None
    if guardado and agora.timestamp() < guardado["expira"]:
        return guardado["corpo"]
    cab = {"User-Agent": USER_AGENT}
    if guardado and guardado.get("modificado"):
        cab["If-Modified-Since"] = guardado["modificado"]
    # 4 casas decimais no máximo: pedido dos termos (coordenadas mais precisas não mudam a previsão e quebram o cache deles)
    params = {"lat": f"{polo['lat']:.4f}", "lon": f"{polo['lon']:.4f}"}
    try:
        r = cliente.get(URL_MET, params=params, headers=cab, timeout=30)
    except httpx.HTTPError as erro:
        raise FonteIndisponivel(f"MET Norway sem resposta para {polo['nome']}: {erro}") from erro
    if r.status_code == 304 and guardado:
        corpo = guardado["corpo"]
    elif r.status_code == 200:
        corpo = r.json()
    else:
        raise FonteIndisponivel(f"MET Norway respondeu {r.status_code} para {polo['nome']}")
    expira = agora.timestamp() + 1800
    if r.headers.get("expires"):
        try:
            expira = parsedate_to_datetime(r.headers["expires"]).timestamp()
        except (TypeError, ValueError):
            pass
    arq.write_text(json.dumps({"expira": expira, "modificado": r.headers.get("last-modified"), "corpo": corpo}), encoding="utf-8")
    return corpo


def proxima_atualizacao(agora: datetime) -> str:
    for h in HORARIOS:
        if agora.hour < h:
            return f"hoje às {h:02d}h"
    return f"amanhã às {HORARIOS[0]:02d}h"


def montar(entrada: dict) -> dict:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js não encontrado no PATH (necessário para tools/campo_montar.js)")
    r = subprocess.run([node, str(MONTAR)], input=json.dumps(entrada), capture_output=True, text=True,  # nosec B603
                       encoding="utf-8", cwd=RAIZ, check=False)
    if r.returncode != 0:
        raise RuntimeError(f"montagem do boletim falhou: {r.stderr.strip()}")
    return json.loads(r.stdout)


def gerar(agora: datetime | None = None, buscar=buscar_met, destino: Path = DADOS) -> dict:
    """Busca, monta, valida e grava. Devolve o boletim. Não grava nada se alguma fonte falhar."""
    agora = (agora or datetime.now(BRASILIA)).astimezone(BRASILIA)
    dia = agora.date().isoformat()
    cfg = carregar_polos()
    polos = []
    with httpx.Client() as cliente:
        for p in cfg["polos"]:
            polos.append({**p, "met": buscar(p, cliente, agora)})
            time.sleep(0.2)  # sem rajada de pedidos à fonte
    anterior_arq = destino / f"boletim-{dia}.json"
    anterior = json.loads(anterior_arq.read_text(encoding="utf-8")) if anterior_arq.exists() else None
    boletim = montar({"dia": dia, "geradoEm": agora.isoformat(timespec="minutes"), "regioes": cfg["regioes"],
                      "polos": polos, "anterior": anterior, "proximaAtualizacao": proxima_atualizacao(agora)})
    gravar(boletim, destino)
    log.info("boletim %s gerado às %s (%d polos)", dia, boletim["geradoEm"], len(polos))
    return boletim


def gravar(boletim: dict, destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(boletim, ensure_ascii=False, separators=(",", ":"))
    (destino / f"boletim-{boletim['dia']}.json").write_text(texto, encoding="utf-8")
    (destino / "atual.json").write_text(texto, encoding="utf-8")
    # Índice do arquivo: os 30 dias mais recentes (os arquivos antigos ficam, só saem da lista)
    itens = []
    for arq in sorted(destino.glob("boletim-*.json"), reverse=True)[:ARQUIVO_DIAS]:
        b = json.loads(arq.read_text(encoding="utf-8"))
        itens.append({"id": b["id"], "dia": b["dia"], "geradoEm": b.get("geradoEm"), "arquivo": arq.name})
    (destino / "indice.json").write_text(json.dumps({"boletins": itens}, ensure_ascii=False, indent=1), encoding="utf-8")


def publicar() -> None:
    """Mesma trava da publicação manual: só da main e sem alterações pendentes, para não levar trabalho pela metade."""
    import publicar as P
    motivo = P.motivo_para_nao_publicar()
    if motivo:
        raise RuntimeError(f"publicação bloqueada: {motivo}")
    P.implantar()
    log.info("publicado no Firebase Hosting")


def comandos_agendador(remover: bool = False) -> list[list[str]]:
    """Uma tarefa diária por horário, rodando este script com --publicar (só com o usuário conectado ao Windows)."""
    if remover:
        return [["schtasks", "/Delete", "/TN", TAREFA.format(h=h), "/F"] for h in HORARIOS]
    acao = f'"{sys.executable}" "{Path(__file__).resolve()}" --publicar'
    return [["schtasks", "/Create", "/TN", TAREFA.format(h=h), "/TR", acao, "/SC", "DAILY", "/ST", f"{h:02d}:00", "/F"]
            for h in HORARIOS]


def agendador(remover: bool, simular: bool) -> None:
    schtasks = shutil.which("schtasks")
    for cmd in comandos_agendador(remover):
        print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
        if not simular:
            if not schtasks:
                raise RuntimeError("schtasks não encontrado (o agendador só existe no Windows)")
            subprocess.run([schtasks, *cmd[1:]], check=True)  # nosec B603 — argumentos fixos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--publicar", action="store_true", help="publica no Firebase Hosting depois de gerar")
    ap.add_argument("--instalar-agendador", action="store_true")
    ap.add_argument("--remover-agendador", action="store_true")
    ap.add_argument("--simular", action="store_true", help="mostra os comandos do agendador sem executar")
    a = ap.parse_args(argv)
    configurar_log()
    if a.instalar_agendador or a.remover_agendador:
        agendador(remover=a.remover_agendador, simular=a.simular)
        return 0
    noticias_ok = atualizar_noticias()
    try:
        boletim = gerar()
    except (FonteIndisponivel, RuntimeError) as erro:
        log.error("boletim não atualizado: %s", erro)
        retirar_cartao_vencido()
        if a.publicar and noticias_ok:  # o boletim anterior continua no ar; as notícias novas vão mesmo assim
            try:
                publicar()
            except RuntimeError as erro_pub:
                log.error("publicação falhou: %s", erro_pub)
        return 1
    atualizar_cartao(boletim)
    if a.publicar:
        try:
            publicar()
        except RuntimeError as erro:
            log.error("publicação falhou: %s", erro)
            return 1
    return 0


def atualizar_noticias() -> bool:
    """Notícias e legislação dos cards Orgatec Audi Agro (tools/gerar_noticias_agro.py). Falha aqui não impede o boletim."""
    try:
        import gerar_noticias_agro
        gerar_noticias_agro.gerar()
        return True
    except Exception as erro:  # noqa: BLE001 — qualquer erro nas notícias só é registrado
        log.warning("notícias do agro não atualizadas: %s", erro)
        return False


def atualizar_cartao(boletim: dict) -> bool:
    """Cartões para o status do WhatsApp, os stories e o TikTok (tools/cartao_campo.py). Falha aqui não impede publicar o boletim."""
    try:
        import cartao_campo
        cartao_campo.gerar(boletim)
        return True
    except Exception as erro:  # noqa: BLE001 — qualquer erro no cartão só é registrado
        log.error("cartão do status não gerado: %s", erro)
        return False


def retirar_cartao_vencido() -> None:
    """Boletim do dia não saiu: o cartão de dia anterior sai do caminho fixo, para ninguém postar previsão vencida."""
    try:
        import cartao_campo
        cartao_campo.retirar_vencido()
    except Exception as erro:  # noqa: BLE001 — só registra
        log.error("cartão vencido não retirado: %s", erro)


if __name__ == "__main__":
    sys.exit(main())
