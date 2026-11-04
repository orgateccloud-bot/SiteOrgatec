# Site ORGATEC + API dos formulários num único serviço (FastAPI serve ./site em / e a API em /api).
# Build:  docker build -t orgatec-site .
# Rodar:  docker run -p 8000:8000 --env-file .env -v orgatec-dados:/dados orgatec-site
# Variáveis: veja .env.example. O SQLite fica em /dados: monte um volume persistente nesse caminho.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ORGATEC_DB=/dados/orgatec.db \
    ORGATEC_SERVIR_SITE=1 \
    ORGATEC_PRODUCAO=1

WORKDIR /app
COPY backend/requirements-prod.txt backend/requirements-prod.txt
RUN pip install -r backend/requirements-prod.txt

COPY backend/ backend/
COPY site/ site/
# Rotinas de LGPD: a retenção roda como tarefa agendada com esta mesma imagem (docs/publicacao.md)
COPY tools/lgpd.py tools/lgpd.py

# Usuário sem privilégios; /dados é o único diretório gravável
RUN useradd --create-home --uid 10001 orgatec \
    && mkdir -p /dados && chown orgatec:orgatec /dados \
    && rm -rf backend/dados
USER orgatec
VOLUME ["/dados"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:%s/api/saude' % os.environ.get('PORT','8000'),timeout=4)"

# PORT é definido pela plataforma (Railway, Render, Fly etc.); 8000 localmente.
# --proxy-headers faz o limite de requisições usar o IP real do visitante. ORGATEC_PROXY_IPS deve listar
# só o proxy da plataforma; "*" é aceitável apenas quando o contêiner não recebe tráfego direto da internet.
CMD ["sh", "-c", "exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=${ORGATEC_PROXY_IPS:-127.0.0.1} --no-server-header"]
