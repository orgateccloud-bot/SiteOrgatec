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
autorização.

Falhas da fonte (o MET Norway devolveu 502 e 503 em 04 e 05/11/2026): cada polo tem 3 tentativas com espera; se ainda
assim falhar, vale a previsão guardada há até 3 horas. Polo sem previsão fica de fora do boletim, que avisa quais são
(campo "semDados"), desde que cada região mantenha pelo menos metade dos polos. Abaixo disso, ou com a fonte fora do ar,
nada é gravado nem publicado e o boletim anterior continua no ar (a tela o marca como desatualizado depois de 18 horas).
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
ESPERAS = (2, 6)  # segundos entre as 3 tentativas por polo
ESPERA_MAXIMA = 30  # teto para o Retry-After da fonte
STATUS_TENTAR_DE_NOVO = {429, 500, 502, 503, 504}
CACHE_VELHO_HORAS = 3  # previsão guardada que ainda serve quando a fonte falha
FALHAS_SEGUIDAS = 3  # polos seguidos sem previsão: a fonte está fora do ar, para de insistir
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


def _pedir_met(polo: dict, cliente: httpx.Client, cab: dict, params: dict) -> httpx.Response:
    """Pede a previsão com até 3 tentativas (erro de rede, 429 ou 5xx). Devolve a resposta ou levanta FonteIndisponivel."""
    ultima: httpx.Response | None = None
    erro: httpx.HTTPError | None = None
    for tentativa in range(len(ESPERAS) + 1):
        try:
            ultima, erro = cliente.get(URL_MET, params=params, headers=cab, timeout=30), None
        except httpx.HTTPError as e:
            ultima, erro = None, e
        if ultima is not None and ultima.status_code not in STATUS_TENTAR_DE_NOVO:
            return ultima
        if tentativa < len(ESPERAS):
            espera = ESPERAS[tentativa]
            retry = ultima.headers.get("retry-after", "") if ultima is not None else ""
            if retry.isdigit():
                espera = min(int(retry), ESPERA_MAXIMA)
            time.sleep(espera)
    if ultima is not None:
        raise FonteIndisponivel(f"MET Norway respondeu {ultima.status_code} para {polo['nome']}")
    raise FonteIndisponivel(f"MET Norway sem resposta para {polo['nome']}: {erro}")


def buscar_met(polo: dict, cliente: httpx.Client, agora: datetime) -> dict:
    """Previsão do polo com cache: dentro do Expires usa o arquivo; depois, pergunta com If-Modified-Since.
    Se a fonte falhar mesmo com as tentativas, vale o arquivo guardado há até CACHE_VELHO_HORAS horas."""
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
        r = _pedir_met(polo, cliente, cab, params)
        if r.status_code == 304 and guardado:
            corpo = guardado["corpo"]
        elif r.status_code == 200:
            corpo = r.json()
        else:
            raise FonteIndisponivel(f"MET Norway respondeu {r.status_code} para {polo['nome']}")
    except FonteIndisponivel as falha:
        if guardado and agora.timestamp() - arq.stat().st_mtime <= CACHE_VELHO_HORAS * 3600:
            log.warning("%s; usando a previsão guardada há menos de %d h", falha, CACHE_VELHO_HORAS)
            return guardado["corpo"]
        raise
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
    polos, sem_dados, seguidas = [], [], 0
    with httpx.Client() as cliente:
        for p in cfg["polos"]:
            try:
                polos.append({**p, "met": buscar(p, cliente, agora)})
                seguidas = 0
            except FonteIndisponivel as falha:
                log.warning("polo sem previsão: %s", falha)
                sem_dados.append(p)
                seguidas += 1
                if seguidas >= FALHAS_SEGUIDAS:
                    raise FonteIndisponivel(f"{falha} (e mais {seguidas - 1} polos seguidos: fonte fora do ar)") from falha
            time.sleep(0.2)  # sem rajada de pedidos à fonte
    conferir_cobertura(cfg, sem_dados)
    anterior_arq = destino / f"boletim-{dia}.json"
    anterior = json.loads(anterior_arq.read_text(encoding="utf-8")) if anterior_arq.exists() else None
    boletim = montar({"dia": dia, "geradoEm": agora.isoformat(timespec="minutes"), "regioes": cfg["regioes"],
                      "polos": polos, "anterior": anterior, "proximaAtualizacao": proxima_atualizacao(agora),
                      "semDados": [{"id": p["id"], "nome": p["nome"], "uf": p["uf"], "regiao": p["regiao"]} for p in sem_dados]})
    gravar(boletim, destino)
    log.info("boletim %s gerado às %s (%d polos, %d sem previsão)", dia, boletim["geradoEm"], len(polos), len(sem_dados))
    return boletim


def conferir_cobertura(cfg: dict, sem_dados: list[dict]) -> None:
    """Cada região precisa manter pelo menos metade dos polos; senão o boletim não sai (vale o anterior, marcado)."""
    ausentes = {p["id"] for p in sem_dados}
    for r in cfg["regioes"]:
        total = len(r["polos"])
        com = sum(1 for pid in r["polos"] if pid not in ausentes)
        if com * 2 < total:
            raise FonteIndisponivel(f"região {r['nome']} ficaria com {com} de {total} polos")


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
    indice = {"boletins": itens, "lacunas": lacunas([i["dia"] for i in itens])}
    (destino / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")


def lacunas(dias: list[str]) -> list[str]:
    """Dias sem boletim entre o mais antigo e o mais recente do índice (registro da falha; nada é inventado para eles)."""
    if len(dias) < 2:
        return []
    ini, fim = datetime.fromisoformat(min(dias)).date(), datetime.fromisoformat(max(dias)).date()
    existentes = set(dias)
    todos = (ini + timedelta(days=n) for n in range((fim - ini).days + 1))
    return [d.isoformat() for d in todos if d.isoformat() not in existentes]


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
