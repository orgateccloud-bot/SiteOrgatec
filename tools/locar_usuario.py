"""Dá a um usuário do Firebase Authentication o acesso ao painel do grupo LOCAR (declarações locar_grupo e locar_papel).

  python tools/locar_usuario.py --projeto orgatec-site --listar
  python tools/locar_usuario.py --projeto orgatec-site --email pessoa@orgatec.io --grupo <uuid> --papel equipe             (só mostra)
  python tools/locar_usuario.py --projeto orgatec-site --email pessoa@orgatec.io --grupo <uuid> --papel equipe --confirmar  (grava)
  python tools/locar_usuario.py --projeto orgatec-site --email pessoa@orgatec.io --revogar --confirmar

Sem --confirmar nada é gravado. O usuário precisa já existir (Firebase Console > Authentication > Users). As declarações do
LOCAR são mescladas às que o usuário já tem (as da Central de Viagem ficam como estão). A declaração só vale no próximo
login ou renovação do token (até 1 hora). O `usuario_id` impresso é o que entra em `acessos` do arquivo de carga
(tools/locar_carregar.py). Credenciais: `gcloud auth application-default login` com uma conta que administre o projeto; nada
é gravado em arquivo.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

import httpx

PAPEIS = ("equipe", "diretor", "leitura")
CHAVES = ("locar_grupo", "locar_papel")
BASE = "https://identitytoolkit.googleapis.com/v1/projects/{projeto}/accounts"


def _token_adc() -> str:
    import google.auth
    from google.auth.transport.requests import Request

    cred, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    cred.refresh(Request())
    return cred.token


def _declaracoes(usuario: dict[str, Any]) -> dict[str, Any]:
    try:
        d = json.loads(usuario.get("customAttributes") or "{}")
    except ValueError:
        return {}
    return d if isinstance(d, dict) else {}


def definir_acesso(cliente: httpx.Client, projeto: str, email: str, grupo: str | None, papel: str | None, confirmar: bool = False) -> str:
    """Mescla (ou remove, com grupo=None) as declarações do LOCAR. Sem `confirmar` não grava. Devolve uma frase para o operador."""
    cab = {"Content-Type": "application/json"}
    r = cliente.post(BASE.format(projeto=projeto) + ":lookup", headers=cab, json={"email": [email]})
    r.raise_for_status()
    usuarios = r.json().get("users", [])
    if not usuarios:
        raise SystemExit(f"Não existe usuário com esse e-mail no projeto {projeto}. Crie primeiro no Firebase Authentication.")
    uid = usuarios[0]["localId"]
    declaracoes = _declaracoes(usuarios[0])
    for chave in CHAVES:
        declaracoes.pop(chave, None)
    if grupo is not None:
        declaracoes |= {"locar_grupo": grupo, "locar_papel": papel}
    acao = "remover o acesso ao LOCAR" if grupo is None else f"conceder o papel {papel} no grupo {grupo}"
    if not confirmar:
        return f"[simulação] usuario_id {uid}: {acao}. Nada foi gravado; repita com --confirmar."
    r = cliente.post(BASE.format(projeto=projeto) + ":update", headers=cab, json={"localId": uid, "customAttributes": json.dumps(declaracoes)})
    r.raise_for_status()
    return f"usuario_id {uid}: acesso removido" if grupo is None else f"usuario_id {uid}: acesso concedido, papel {papel}, grupo {grupo}"


def listar(cliente: httpx.Client, projeto: str) -> list[str]:
    """Quem tem acesso ao LOCAR: usuario_id, papel e grupo (sem e-mail na saída, para não ir parar em log)."""
    saida, pagina = [], None
    while True:
        params = {"maxResults": 500, **({"nextPageToken": pagina} if pagina else {})}
        r = cliente.get(BASE.format(projeto=projeto) + ":batchGet", params=params)
        r.raise_for_status()
        dados = r.json()
        for u in dados.get("users", []):
            d = _declaracoes(u)
            if d.get("locar_grupo"):
                saida.append(f"{u['localId']}  papel={d.get('locar_papel')}  grupo={d['locar_grupo']}")
        pagina = dados.get("nextPageToken")
        if not pagina:
            return saida


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--projeto", required=True)
    ap.add_argument("--email")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--grupo", help="UUID do grupo")
    g.add_argument("--revogar", action="store_true")
    g.add_argument("--listar", action="store_true")
    ap.add_argument("--papel", choices=PAPEIS, default="equipe")
    ap.add_argument("--confirmar", action="store_true", help="grava; sem isto só mostra o que faria")
    a = ap.parse_args(argv)
    if not a.listar and not a.email:
        raise SystemExit("Informe --email.")
    if a.grupo and not re.fullmatch(r"[0-9a-fA-F-]{36}", a.grupo):
        raise SystemExit("O grupo deve ser um UUID (36 caracteres).")
    # x-goog-user-project: com credencial de usuário o Identity Toolkit exige o projeto de cota
    with httpx.Client(timeout=30, headers={"Authorization": f"Bearer {_token_adc()}", "x-goog-user-project": a.projeto}) as c:
        if a.listar:
            linhas = listar(c, a.projeto)
            print("\n".join(linhas) if linhas else "nenhum usuário com acesso ao LOCAR")
        else:
            print(definir_acesso(c, a.projeto, a.email, None if a.revogar else a.grupo, a.papel, a.confirmar))
    return 0


if __name__ == "__main__":
    sys.exit(main())
