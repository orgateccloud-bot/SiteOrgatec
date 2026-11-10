"""API dos formulários do site ORGATEC (leads do simulador, opt-in do calendário, contato).

Executar em desenvolvimento (serve também o site estático em /):
    uvicorn backend.app:app --port 8410

Variáveis de ambiente (nunca versionar valores reais):
    ORGATEC_BANCO         "sqlite" ou "firestore" (Cloud Run: o disco do contêiner é efêmero) (padrão: sqlite)
    ORGATEC_FIRESTORE_PROJETO  projeto do Google, se diferente do padrão do ambiente
    ORGATEC_DB            caminho do SQLite            (padrão: backend/dados/orgatec.db)
    ORGATEC_SEGREDO_IP    segredo do HMAC de IP        (obrigatório em produção)
    ORGATEC_ORIGENS       origens CORS separadas por , (padrão: https://orgatec.io)
    ORGATEC_SERVIR_SITE   "1" para servir ./site em /  (padrão: 1)
    ORGATEC_RATE_LIMIT    requisições por IP por 10 min (padrão: 20)
    ORGATEC_PRODUCAO      "1" no servidor publicado: exige ORGATEC_SEGREDO_IP e liga o HSTS (padrão: 0)
    ORGATEC_CABECALHO_IP  cabeçalho com o IP real do visitante, posto pelo proxy da hospedagem
                          (Railway: x-real-ip). Vazio = IP da conexão          (padrão: vazio)
    ORGATEC_IP_POSICAO    posição do IP nesse cabeçalho quando ele traz uma lista (X-Forwarded-For):
                          0 = primeiro, -1 = último, -2 = penúltimo...         (padrão: 0)
    ORGATEC_DIAGNOSTICO_IP "1" registra no log, com o último bloco mascarado, os cabeçalhos de IP de cada
                          envio. Serve para calibrar ORGATEC_IP_POSICAO na homologação (o Firebase Hosting
                          não documenta em que posição o IP do visitante chega ao Cloud Run). Desligue depois.
    ORGATEC_INDEXAR       "1" libera buscadores; enquanto não for "1", toda resposta leva
                          X-Robots-Tag: noindex (homologação fora do Google)            (padrão: 0)
    ORGATEC_RETENCAO_LEAD_DIAS, ORGATEC_RETENCAO_CONTATO_DIAS, ORGATEC_RETENCAO_OPTIN_PENDENTE_DIAS
                          prazos de guarda (backend/retencao.py); a eliminação roda em tools/lgpd.py
    ORGATEC_EMAIL e ORGATEC_SMTP_*  envio da confirmação do opt-in (backend/envio.py)  (padrão: desligado)
"""

from __future__ import annotations

import logging
import os
import re
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .envio import confirmacao_optin, enviador_do_ambiente
from .repositorio import Repositorio
from .retencao import prazos_do_ambiente
from .schemas import ContatoIn, LeadIn, OptInIn, Recibo

RAIZ = Path(__file__).resolve().parent.parent
log = logging.getLogger("orgatec.api")


PRODUCAO = os.environ.get("ORGATEC_PRODUCAO", "0") == "1"
INDEXAR = os.environ.get("ORGATEC_INDEXAR", "0") == "1"


def _segredo() -> str:
    s = os.environ.get("ORGATEC_SEGREDO_IP")
    if not s:
        if PRODUCAO:
            # Um segredo efêmero mudaria a cada reinício e quebraria a comparação dos IPs já gravados.
            raise RuntimeError("ORGATEC_SEGREDO_IP é obrigatório com ORGATEC_PRODUCAO=1")
        log.warning("ORGATEC_SEGREDO_IP ausente: usando segredo efêmero (apenas desenvolvimento)")
        s = secrets.token_hex(32)
    elif PRODUCAO and len(s) < 32:
        raise RuntimeError("ORGATEC_SEGREDO_IP precisa de pelo menos 32 caracteres em produção")
    return s


def _criar_repo():
    banco = os.environ.get("ORGATEC_BANCO", "sqlite").strip().lower()
    if banco == "firestore":
        from .repositorio_firestore import RepositorioFirestore
        return RepositorioFirestore(_segredo(), projeto=os.environ.get("ORGATEC_FIRESTORE_PROJETO") or None,
                                    prazos=prazos_do_ambiente())
    if banco != "sqlite":
        raise RuntimeError(f"ORGATEC_BANCO inválido: {banco!r} (use sqlite ou firestore)")
    return Repositorio(Path(os.environ.get("ORGATEC_DB", RAIZ / "backend" / "dados" / "orgatec.db")), _segredo(),
                       prazos_do_ambiente())


repo = _criar_repo()
enviador = enviador_do_ambiente(PRODUCAO)  # e-mail de confirmação do opt-in (backend/envio.py); padrão: desligado

# Sem /docs, /redoc nem /openapi.json: o esquema da API não precisa ficar público.
app = FastAPI(title="ORGATEC — API pública", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("ORGATEC_ORIGENS", "https://orgatec.io").split(",")],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# Cabeçalhos de segurança. Sem script embutido nem externo: Tailwind compilado (tools/compilar_css.py) e os
# scripts das páginas em arquivos próprios. style-src mantém 'unsafe-inline' por causa de atributos style.
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self'",
    "img-src 'self' data: https://gibs.earthdata.nasa.gov",  # mapa de satélite da Janela de Campo
    "connect-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
])
# Páginas da Central de Viagem (/transporte/): além do próprio site, falam com o Firebase Authentication para entrar e renovar o token
# e carregam o mapa do Google (Maps JavaScript API). Lista de domínios do guia oficial de CSP do Maps JavaScript API, sem
# 'unsafe-inline' em script-src e com hosts exatos onde dá (o curinga *.googleapis.com em script-src incluiria o Cloud Storage).
# Mesma política em tools/preparar_firebase.py (csp_transporte); o teste compara as duas.
MAPA_GOOGLE = {
    "script-src": "https://maps.googleapis.com https://maps.gstatic.com",
    "style-src": "https://fonts.googleapis.com",
    "font-src": "https://fonts.gstatic.com",
    "img-src": "https://*.googleapis.com https://*.gstatic.com https://*.google.com https://*.googleusercontent.com",
    "connect-src": "https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://maps.googleapis.com https://*.gstatic.com",
}


def com_mapa_google(politica: str) -> str:
    partes = []
    for diretiva in politica.split("; "):
        nome = diretiva.split(" ", 1)[0]
        partes.append(f"{diretiva} {MAPA_GOOGLE[nome]}" if nome in MAPA_GOOGLE else diretiva)
    return "; ".join([*partes, "worker-src blob:"])


CSP_TRANSPORTE = com_mapa_google(CSP)
# Widget oficial do CEPEA (cotações dos cards Orgatec Audi Agro): só em /cotacoes/, aberto pelos cards num iframe com
# sandbox="allow-scripts" (origem opaca). É a única página que aceita script de fora, e só o do CEPEA.
CSP_WIDGET = "; ".join([
    "default-src 'none'",
    "script-src 'self' https://www.cepea.org.br",
    "style-src 'unsafe-inline'",
    "img-src https://cepea.org.br https://www.cepea.org.br data:",
    "frame-ancestors 'self'",
    "base-uri 'none'",
    "form-action 'none'",
])


# O maior formulário válido (contato com 2.000 caracteres, ou lead com 60 alertas) cabe com folga. O corte vale para
# quem declara o tamanho; os limites de cada campo em schemas.py continuam valendo para o resto.
_MAX_CORPO = 16 * 1024


def _corpo_grande(request: Request) -> bool:
    tamanho = request.headers.get("content-length", "")
    return request.url.path.startswith("/api/") and tamanho.isdigit() and int(tamanho) > _MAX_CORPO


@app.middleware("http")
async def cabecalhos_seguranca(request: Request, call_next):
    if _corpo_grande(request):
        resposta = JSONResponse({"detail": "envio grande demais"}, status_code=413)
    else:
        resposta = await call_next(request)
    h = resposta.headers
    if request.url.path.startswith("/cotacoes/"):
        h["Content-Security-Policy"] = CSP_WIDGET
        h["X-Frame-Options"] = "SAMEORIGIN"
    if request.url.path.startswith("/transporte/"):
        h["Content-Security-Policy"] = CSP_TRANSPORTE
    h.setdefault("Content-Security-Policy", CSP)
    h.setdefault("X-Content-Type-Options", "nosniff")
    h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    h.setdefault("X-Frame-Options", "DENY")
    h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
    if PRODUCAO:
        h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if not INDEXAR:
        h.setdefault("X-Robots-Tag", "noindex, nofollow")
    if request.url.path.startswith("/api/"):
        h["Cache-Control"] = "no-store"  # o Firebase Hosting não guarda respostas da API (protocolos, dados pessoais)
    if request.url.path.startswith("/api/optin/"):
        h["Referrer-Policy"] = "no-referrer"  # o endereço traz o token do link
    return resposta


_LIMITE = int(os.environ.get("ORGATEC_RATE_LIMIT", "20"))
# Só use quando o serviço for alcançável apenas pelo proxy da hospedagem: o cabeçalho pode ser forjado
# por quem acessa o contêiner diretamente.
_CABECALHO_IP = os.environ.get("ORGATEC_CABECALHO_IP", "").strip().lower()
_IP_POSICAO = int(os.environ.get("ORGATEC_IP_POSICAO", "0"))
_DIAGNOSTICO_IP = os.environ.get("ORGATEC_DIAGNOSTICO_IP", "0") == "1"


def mascarar_ip(ip: str) -> str:
    """Último bloco escondido (IPv4 .x; IPv6 :x): suficiente para comparar posições, sem guardar o IP inteiro."""
    ip = ip.strip()
    if "." in ip:
        return ip.rsplit(".", 1)[0] + ".x"
    if ":" in ip:
        return ip.rsplit(":", 1)[0] + ":x"
    return "?" if ip else ""
_JANELA = 600
_MAX_IPS = 50_000  # teto da memória do limite por IP: ao chegar nele, sai quem já passou da janela
_hits: dict[str, deque] = defaultdict(deque)


def _podar_hits(agora: float) -> None:
    for ip in [ip for ip, fila in _hits.items() if not fila or agora - fila[-1] > _JANELA]:
        del _hits[ip]
    if len(_hits) >= _MAX_IPS:  # todos dentro da janela: só uma enxurrada de endereços chega aqui
        _hits.clear()


def limitar(request: Request) -> str:
    # Atrás de proxy reverso: ORGATEC_CABECALHO_IP (ex.: x-real-ip na Railway) ou uvicorn --proxy-headers.
    ip = ""
    if _CABECALHO_IP:
        lista = [x.strip() for x in request.headers.get(_CABECALHO_IP, "").split(",") if x.strip()]
        if -len(lista) <= _IP_POSICAO < len(lista):
            ip = lista[_IP_POSICAO][:64]
    if not ip:
        ip = request.client.host if request.client else "desconhecido"
    if _DIAGNOSTICO_IP:
        cab = {k: ",".join(mascarar_ip(x) for x in request.headers.get(k, "").split(",") if x.strip())
               for k in ("x-forwarded-for", "x-real-ip", "forwarded") if request.headers.get(k)}
        log.warning("diagnostico-ip conexao=%s cabecalhos=%s escolhido=%s",
                    mascarar_ip(request.client.host if request.client else ""), cab, mascarar_ip(ip))
    agora = time.monotonic()
    if len(_hits) >= _MAX_IPS:
        _podar_hits(agora)
    fila = _hits[ip]
    while fila and agora - fila[0] > _JANELA:
        fila.popleft()
    if len(fila) >= _LIMITE:
        raise HTTPException(status_code=429, detail="muitas requisições; tente novamente mais tarde")
    fila.append(agora)
    return ip


@app.get("/api/saude")
def saude() -> dict:
    # Pública e sem limite: não toca no banco. A conferência da trilha lê todos os registros (no Firestore, cada
    # leitura é cobrada) e roda em tools/lgpd.py trilha.
    return {"ok": True}


@app.post("/api/leads", response_model=Recibo, status_code=201)
def criar_lead(dados: LeadIn, ip: str = Depends(limitar)) -> dict:
    r = repo.inserir("lead", "novo", dados.model_dump(exclude={"website"}), ip)
    return r


@app.post("/api/optin", response_model=Recibo, status_code=201)
def criar_optin(dados: OptInIn, ip: str = Depends(limitar)) -> dict:
    # Double opt-in: o registro só vale após confirmação pelo link enviado ao contato (backend/envio.py).
    # Os tokens só existem em claro aqui: o banco guarda o hash. A resposta (Recibo) não os devolve.
    r = repo.inserir("optin", "pendente_confirmacao", dados.model_dump(exclude={"website"}), ip, com_token=True)
    log.info("optin %s registrado (aguardando confirmação)", r["protocolo"])
    if dados.email:
        try:
            enviador.enviar(confirmacao_optin(dados.email, r["token"], r["token_saida"], list(dados.ufs), list(dados.esferas),
                                              prazos_do_ambiente().optin_pendente_dias))
            log.info("optin %s: confirmação entregue ao provedor de e-mail", r["protocolo"])
        except Exception as erro:  # o cadastro fica; sem confirmação, a retenção apaga o pedido no prazo
            log.error("optin %s: falha no envio da confirmação (%s)", r["protocolo"], type(erro).__name__)
    else:
        log.warning("optin %s só com WhatsApp: confirmação por WhatsApp ainda não existe", r["protocolo"])
    return r


_TOKEN = re.compile(r"[A-Za-z0-9_-]{8,64}")


def _pagina(titulo: str, corpo: str) -> str:
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>{titulo} | ORGATEC</title></head>'
            f'<body style="font-family:system-ui,sans-serif;max-width:32rem;margin:3rem auto;padding:0 1rem">'
            f'<h1 style="font-size:1.4rem">{titulo}</h1>{corpo}</body></html>')


def _pedir_clique(token: str, rota: str, titulo: str, botao: str) -> str:
    """O GET só mostra o botão: robôs de e-mail abrem os links das mensagens e não podem confirmar nem cancelar."""
    if not _TOKEN.fullmatch(token):
        raise HTTPException(status_code=404, detail="link inválido ou já utilizado")
    return _pagina(titulo, f'<form method="post" action="/api/optin/{rota}?token={token}"><button type="submit" '
                           f'style="font:inherit;padding:.6rem 1rem">{botao}</button></form>')


@app.get("/api/optin/confirmar", response_class=HTMLResponse, dependencies=[Depends(limitar)])
def pedir_confirmacao(token: str) -> str:
    return _pedir_clique(token, "confirmar", "Confirmar inscrição no Calendário Fiscal", "Confirmar inscrição")


@app.post("/api/optin/confirmar", response_class=HTMLResponse, dependencies=[Depends(limitar)])
def confirmar_optin(token: str) -> str:
    if not _TOKEN.fullmatch(token) or not repo.confirmar_optin(token):
        raise HTTPException(status_code=404, detail="link inválido, vencido ou já utilizado")
    return _pagina("Inscrição confirmada", "<p>Todo alerta traz um link para cancelar quando quiser.</p>")


@app.get("/api/optin/sair", response_class=HTMLResponse, dependencies=[Depends(limitar)])
def pedir_descadastro(token: str) -> str:
    return _pedir_clique(token, "sair", "Cancelar os alertas do Calendário Fiscal", "Cancelar e apagar meus dados")


@app.post("/api/optin/sair", response_class=HTMLResponse, dependencies=[Depends(limitar)])
def descadastrar(token: str) -> str:
    if not _TOKEN.fullmatch(token) or not repo.revogar_optin(token):
        raise HTTPException(status_code=404, detail="link inválido ou já utilizado")
    return _pagina("Inscrição cancelada", "<p>Seu contato foi apagado e você não receberá mais alertas.</p>")


@app.post("/api/contato", response_model=Recibo, status_code=201)
def criar_contato(dados: ContatoIn, ip: str = Depends(limitar)) -> dict:
    return repo.inserir("contato", "novo", dados.model_dump(exclude={"website"}), ip)


# Central de Viagem (docs/ideias/reestruturacao-transporte.md, Fase 5): só existe com ORGATEC_TRANSPORTE=1 (padrão: desligada).
# Antes do mount do site, para as rotas /api/transporte e /api/telemetria valerem.
from .transporte import api as _transporte  # noqa: E402

_transporte.instalar(app, limite_ip=limitar)

if os.environ.get("ORGATEC_SERVIR_SITE", "1") == "1":
    app.mount("/", StaticFiles(directory=RAIZ / "site", html=True), name="site")
