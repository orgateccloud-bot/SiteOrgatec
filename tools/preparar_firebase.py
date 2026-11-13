"""Prepara a publicação no Firebase Hosting.

Gera firebase.json (hospedagem de ./site com os cabeçalhos de segurança, regras do Firestore e emulador)
e, quando informados, .firebaserc (projeto do Firebase) e api.publica em site/assets/js/config.js.

Modelos:
  --cloud-run SERVICO   API no Cloud Run do mesmo projeto: o Hosting encaminha /api/** (mesma origem,
                        sem CORS). Região padrão southamerica-east1 (São Paulo). api.publica = ''.
  --api https://...     API em outro domínio (ex.: Railway). api.publica = endereço; imprime ORGATEC_ORIGENS.
  (nenhum)              sem API: os formulários caem no WhatsApp. api.publica não é alterado.

Uso:
  python tools/preparar_firebase.py
  python tools/preparar_firebase.py --projeto orgatec-site --cloud-run orgatec-api
  python tools/preparar_firebase.py --projeto orgatec-site --api https://orgatec-api.up.railway.app
  python tools/preparar_firebase.py ... --indexar          # só na virada para produção
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "site" / "assets" / "js" / "config.js"
REGIAO_PADRAO = "southamerica-east1"  # São Paulo: Cloud Run e Firestore com dados no Brasil


def origem_api(url: str | None) -> str | None:
    """Valida e normaliza o endereço da API: https, sem caminho, sem barra final."""
    if not url:
        return None
    u = urlparse(url.strip())
    if u.scheme != "https" or not u.netloc or u.path not in ("", "/") or u.query or u.fragment:
        raise SystemExit(f"Endereço da API inválido: {url!r}. Use só https://dominio (sem caminho).")
    return f"https://{u.netloc.lower()}"


def projeto_valido(pid: str | None) -> str | None:
    if pid is None:
        return None
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", pid):
        raise SystemExit(f"ID de projeto do Firebase inválido: {pid!r} (letras minúsculas, números e hífen; 6 a 30 caracteres).")
    return pid


def servico_valido(nome: str | None) -> str | None:
    if nome is None:
        return None
    if not re.fullmatch(r"[a-z]([a-z0-9-]{0,47}[a-z0-9])?", nome):
        raise SystemExit(f"Nome de serviço do Cloud Run inválido: {nome!r} (minúsculas, números e hífen).")
    return nome


# Páginas movidas: 301 direto para o destino final, sem cadeia (Fase 2, docs/ideias/reestruturacao-transporte-fase2.md).
# R1: o site segue com .html (cleanUrls desligado); por isso só a forma com .html existe.
REDIRECIONAMENTOS = [
    ("/setores/transporte.html", "/empresarial/transporte.html"),
    ("/setores/agro.html", "/rural/index.html"),
    ("/setores/janela-de-campo.html", "/rural/janela-de-campo.html"),
    ("/setores/agro-mercado.html", "/rural/cotacoes.html"),
    ("/setores/regional.html", "/reforma/alertas-regionais.html"),  # o navegador mantém ?setor= e ?uf= no 301
    ("/tributario/index.html", "/consultoria-tributaria.html"),
    ("/escritorio/index.html", "/quem-somos.html"),
]


def csp(api: str | None) -> str:
    """Mesma política do backend (backend/app.py); uma API em outro domínio entra em connect-src."""
    return "; ".join([
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "font-src 'self'",
        "img-src 'self' data: https://gibs.earthdata.nasa.gov",
        "connect-src 'self'" + (f" {api}" if api else ""),
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    ])


# Central de Viagem: Firebase Authentication (entrar e renovar o token) e mapa do Google (Maps JavaScript API). Igual a
# backend/app.py (MAPA_GOOGLE); o teste compara as duas.
MAPA_GOOGLE = {
    "script-src": "https://maps.googleapis.com https://maps.gstatic.com",
    "style-src": "https://fonts.googleapis.com",
    "font-src": "https://fonts.gstatic.com",
    "img-src": "https://*.googleapis.com https://*.gstatic.com https://*.google.com https://*.googleusercontent.com",
    "connect-src": "https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://maps.googleapis.com https://*.gstatic.com",
}


def csp_transporte(api: str | None) -> str:
    """Só as páginas de /transporte/ falam com o Google (login e mapa); o resto do site mantém a política geral."""
    partes = []
    for diretiva in csp(api).split("; "):
        nome = diretiva.split(" ", 1)[0]
        partes.append(f"{diretiva} {MAPA_GOOGLE[nome]}" if nome in MAPA_GOOGLE else diretiva)
    return "; ".join([*partes, "worker-src blob:"])


# Mapa interativo da Janela do Transporte (MapLibre GL em assets/vendor/): igual a backend/app.py (MAPA_JANELA).
MAPA_JANELA = {"img-src": "blob:", "connect-src": "https://gibs.earthdata.nasa.gov"}


def csp_janela(api: str | None) -> str:
    """Só a página da Janela do Transporte baixa imagens da NASA por fetch; o resto do site mantém a política geral."""
    return "; ".join(f"{d} {MAPA_JANELA[d.split(' ', 1)[0]]}" if d.split(" ", 1)[0] in MAPA_JANELA else d for d in csp(api).split("; "))


CSP_WIDGET = "; ".join([  # mesma do backend (backend/app.py): widget do CEPEA em /cotacoes/, dentro de iframe isolado
    "default-src 'none'",
    "script-src 'self' https://www.cepea.org.br",
    "style-src 'unsafe-inline'",
    "img-src https://cepea.org.br https://www.cepea.org.br data:",
    "frame-ancestors 'self'",
    "base-uri 'none'",
    "form-action 'none'",
])


def firebase_json(api: str | None, indexar: bool, cloud_run: str | None = None, regiao: str = REGIAO_PADRAO) -> dict:
    seguranca = [
        {"key": "Content-Security-Policy", "value": csp(api)},
        {"key": "X-Content-Type-Options", "value": "nosniff"},
        {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
        {"key": "X-Frame-Options", "value": "DENY"},
        {"key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=(), payment=()"},
        {"key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains"},
    ]
    if not indexar:
        seguranca.append({"key": "X-Robots-Tag", "value": "noindex, nofollow"})
    hosting = {
        "public": "site",
        "ignore": ["**/.*", "**/node_modules/**"],
        "cleanUrls": False,
        "trailingSlash": False,
        "headers": [
            {"source": "**", "headers": seguranca},
            # Depois da regra geral, para valer por cima dela nas páginas do widget do CEPEA
            {"source": "/transporte/**", "headers": [{"key": "Content-Security-Policy", "value": csp_transporte(api)}]},
            {"source": "/empresarial/janela.html", "headers": [{"key": "Content-Security-Policy", "value": csp_janela(api)}]},
            {"source": "/cotacoes/**", "headers": [{"key": "Content-Security-Policy", "value": CSP_WIDGET},
                                                  {"key": "X-Frame-Options", "value": "SAMEORIGIN"}]},
            # Arquivos gerados não levam hash no nome: na homologação, o navegador sempre revalida.
            {"source": "**/*.@(html|js|css|json)", "headers": [{"key": "Cache-Control", "value": "no-cache"}]},
            {"source": "/", "headers": [{"key": "Cache-Control", "value": "no-cache"}]},  # a raiz não casa com *.html
            {"source": "**/*.@(png|svg|ico|jpg|webp|woff2)", "headers": [{"key": "Cache-Control", "value": "public, max-age=86400"}]},
            # Bibliotecas de terceiros com a versão no nome da pasta (assets/vendor/<nome>-<versão>/): nunca mudam no lugar.
            {"source": "/assets/vendor/**", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
            # Depois da regra das imagens: o cartão da Janela de Campo (dados/campo/cartao-status.png) muda 3 vezes ao dia
            {"source": "/dados/**", "headers": [{"key": "Cache-Control", "value": "no-cache"}]},
        ],
    }
    hosting["redirects"] = [{"source": de, "destination": para, "type": 301} for de, para in REDIRECIONAMENTOS]
    if cloud_run:
        hosting["rewrites"] = [{"source": "/api/**", "run": {"serviceId": cloud_run, "region": regiao}}]
    return {
        "hosting": hosting,
        # Regras: nenhum acesso pelo navegador (só a API, com conta de serviço)
        "firestore": {"rules": "firestore.rules", "indexes": "firestore.indexes.json"},
        "emulators": {"firestore": {"port": 8085}, "ui": {"enabled": False}, "singleProjectMode": True},
    }


def gravar_api_no_config(api: str | None) -> None:
    texto = CONFIG.read_text(encoding="utf-8")
    valor = "null" if api is None else "'" + api.replace("'", "") + "'"
    novo, n = re.subn(r"api: \{ publica: (?:null|'[^']*'), base: '' \}", f"api: {{ publica: {valor}, base: '' }}", texto)
    if n != 1:
        raise SystemExit("Não encontrei a linha 'api: { publica: ..., base: '' }' em config.js.")
    CONFIG.write_text(novo, encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projeto", help="ID do projeto no Firebase")
    modelo = ap.add_mutually_exclusive_group()
    modelo.add_argument("--cloud-run", metavar="SERVICO", help="serviço do Cloud Run no mesmo projeto (rewrite /api/**)")
    modelo.add_argument("--api", help="endereço público da API em outro domínio, ex.: Railway (https://...)")
    ap.add_argument("--regiao", default=REGIAO_PADRAO, help=f"região do Cloud Run (padrão {REGIAO_PADRAO})")
    ap.add_argument("--indexar", action="store_true", help="libera buscadores (só na produção)")
    a = ap.parse_args()
    api, projeto, servico = origem_api(a.api), projeto_valido(a.projeto), servico_valido(a.cloud_run)

    (RAIZ / "firebase.json").write_text(json.dumps(firebase_json(api, a.indexar, servico, a.regiao), ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    print("gerado: firebase.json" + ("" if a.indexar else " (com X-Robots-Tag: noindex)")
          + (f", /api/** → Cloud Run {servico} ({a.regiao})" if servico else ""))
    if projeto:
        (RAIZ / ".firebaserc").write_text(json.dumps({"projects": {"default": projeto}}, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
        print(f"gerado: .firebaserc (projeto {projeto})")
    if servico:
        gravar_api_no_config("")
        print("config.js: api.publica = '' (mesma origem pelo rewrite)")
    elif a.api is not None:
        gravar_api_no_config(api)
        print(f"config.js: api.publica = {api}")
    if projeto and (servico or api):
        print(f"\nCadastre na API ({'Cloud Run' if servico else 'Railway'}):\n"
              f"  ORGATEC_ORIGENS=https://{projeto}.web.app,https://{projeto}.firebaseapp.com")


if __name__ == "__main__":
    main()
