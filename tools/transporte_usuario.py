"""Dá a um usuário do Firebase Authentication o acesso à Central de Viagem (declarações transportadora_id e papel).

  python tools/transporte_usuario.py --projeto orgatec-site --email motorista@cliente.com --transportadora <uuid> --papel gestor
  python tools/transporte_usuario.py --projeto orgatec-site --email x@y.com --revogar     tira o acesso

O usuário precisa já existir (Firebase Console > Authentication > Users, ou o convite por e-mail). A declaração só vale no próximo
login/renovação do token (até 1 hora). Credenciais: `gcloud auth application-default login` com uma conta que administre o
projeto; nada é gravado em arquivo. A transportadora é o UUID criado no cadastro do cliente (backend/transporte/repositorio_transporte.py).
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import httpx

PAPEIS = ("gestor", "motorista", "leitura")
BASE = "https://identitytoolkit.googleapis.com/v1/projects/{projeto}/accounts"


def _token_adc() -> str:
    import google.auth
    from google.auth.transport.requests import Request

    cred, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    cred.refresh(Request())
    return cred.token


def definir_acesso(cliente: httpx.Client, projeto: str, email: str, transportadora: str | None, papel: str | None) -> str:
    """Grava (ou remove, com transportadora=None) as declarações. Devolve uma frase para o operador."""
    cab = {"Content-Type": "application/json"}
    r = cliente.post(BASE.format(projeto=projeto) + ":lookup", headers=cab, json={"email": [email]})
    r.raise_for_status()
    usuarios = r.json().get("users", [])
    if not usuarios:
        raise SystemExit(f"Não existe usuário com esse e-mail no projeto {projeto}. Crie primeiro no Firebase Authentication.")
    uid = usuarios[0]["localId"]
    # Preserva as declarações de outros módulos (ex.: locar_grupo e locar_papel, de tools/locar_usuario.py): só as do Transporte mudam.
    try:
        declaracoes = json.loads(usuarios[0].get("customAttributes") or "{}")
    except ValueError:
        declaracoes = {}
    if not isinstance(declaracoes, dict):
        declaracoes = {}
    declaracoes.pop("transportadora_id", None)
    declaracoes.pop("papel", None)
    if transportadora is not None:
        declaracoes |= {"transportadora_id": transportadora, "papel": papel}
    r = cliente.post(BASE.format(projeto=projeto) + ":update", headers=cab, json={"localId": uid, "customAttributes": json.dumps(declaracoes)})
    r.raise_for_status()
    return "acesso removido" if transportadora is None else f"acesso concedido: papel {papel}, transportadora {transportadora}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--projeto", required=True)
    ap.add_argument("--email", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--transportadora", help="UUID da transportadora")
    g.add_argument("--revogar", action="store_true")
    ap.add_argument("--papel", choices=PAPEIS, default="gestor")
    a = ap.parse_args(argv)
    if a.transportadora and not re.fullmatch(r"[0-9a-fA-F-]{36}", a.transportadora):
        raise SystemExit("A transportadora deve ser um UUID (36 caracteres).")
    # x-goog-user-project: com credencial de usuário (gcloud auth application-default login) o Identity Toolkit exige o projeto de cota
    with httpx.Client(timeout=30, headers={"Authorization": f"Bearer {_token_adc()}", "x-goog-user-project": a.projeto}) as c:
        print(definir_acesso(c, a.projeto, a.email, None if a.revogar else a.transportadora, a.papel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
