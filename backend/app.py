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
"""

from __future__ import annotations

import logging
import os
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .repositorio import Repositorio
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
        return RepositorioFirestore(_segredo(), projeto=os.environ.get("ORGATEC_FIRESTORE_PROJETO") or None)
    if banco != "sqlite":
        raise RuntimeError(f"ORGATEC_BANCO inválido: {banco!r} (use sqlite ou firestore)")
    return Repositorio(Path(os.environ.get("ORGATEC_DB", RAIZ / "backend" / "dados" / "orgatec.db")), _segredo())


repo = _criar_repo()

app = FastAPI(title="ORGATEC — API pública", version="1.0.0", docs_url=None, redoc_url=None)
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


@app.middleware("http")
async def cabecalhos_seguranca(request: Request, call_next):
    resposta = await call_next(request)
    h = resposta.headers
    if request.url.path.startswith("/cotacoes/"):
        h["Content-Security-Policy"] = CSP_WIDGET
        h["X-Frame-Options"] = "SAMEORIGIN"
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
_hits: dict[str, deque] = defaultdict(deque)


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
    fila = _hits[ip]
    while fila and agora - fila[0] > _JANELA:
        fila.popleft()
    if len(fila) >= _LIMITE:
        raise HTTPException(status_code=429, detail="muitas requisições; tente novamente mais tarde")
    fila.append(agora)
    return ip


@app.get("/api/saude")
def saude() -> dict:
    return {"ok": True, "cadeia_integra": repo.verificar_cadeia()}


@app.post("/api/leads", response_model=Recibo, status_code=201)
def criar_lead(dados: LeadIn, ip: str = Depends(limitar)) -> dict:
    r = repo.inserir("lead", "novo", dados.model_dump(exclude={"website"}), ip)
    return r


@app.post("/api/optin", response_model=Recibo, status_code=201)
def criar_optin(dados: OptInIn, ip: str = Depends(limitar)) -> dict:
    # Double opt-in: o registro só vale após confirmação pelo link enviado ao contato.
    # O envio da mensagem depende da ativação de contato@orgatec.io (pendência do Plano Diretor),
    # por isso aqui apenas registramos o token; o disparo fica a cargo do serviço de e-mail/WhatsApp.
    r = repo.inserir("optin", "pendente_confirmacao", dados.model_dump(exclude={"website"}), ip, com_token=True)
    log.info("optin %s registrado (aguardando confirmação)", r["protocolo"])
    return r


@app.get("/api/optin/confirmar", response_class=HTMLResponse)
def confirmar_optin(token: str) -> str:
    if not (8 <= len(token) <= 64) or not repo.confirmar_optin(token):
        raise HTTPException(status_code=404, detail="link inválido ou já utilizado")
    return "<p>Inscrição no Calendário Fiscal ORGATEC confirmada. Você pode cancelar a qualquer momento.</p>"


@app.post("/api/contato", response_model=Recibo, status_code=201)
def criar_contato(dados: ContatoIn, ip: str = Depends(limitar)) -> dict:
    return repo.inserir("contato", "novo", dados.model_dump(exclude={"website"}), ip)


if os.environ.get("ORGATEC_SERVIR_SITE", "1") == "1":
    app.mount("/", StaticFiles(directory=RAIZ / "site", html=True), name="site")
