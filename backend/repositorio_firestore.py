"""Persistência no Firestore com a mesma interface e a mesma trilha de auditoria do `Repositorio` (SQLite).

Usada no Cloud Run (ORGATEC_BANCO=firestore), onde o disco do contêiner é apagado a cada reinício.

Modelo:
  registros/{protocolo}  protocolo, tipo, status, payload (JSON canônico, texto), ip_hmac, token,
                         criado_em, seq, hash_ant, audit_hash
  controle/cadeia        seq, ultimo_hash  (cabeça da cadeia)

Cada inserção é uma transação que lê a cabeça, calcula o hash com a mesma fórmula do SQLite e grava o
registro e a nova cabeça juntos: dois envios simultâneos nunca recebem o mesmo hash anterior.
Clientes (navegador) não têm acesso ao banco: firestore.rules nega tudo; só a conta de serviço da API grava.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
from datetime import datetime, timezone

from .repositorio import GENESIS, Repositorio

_PREFIXOS = {"lead": "LD", "optin": "OP", "contato": "CT"}
# Toda inserção grava a cabeça da cadeia, um único documento: o Firestore aceita poucas escritas por segundo
# num mesmo documento, e transações simultâneas se anulam. Por isso, dentro da instância, as inserções entram
# numa fila (lock), como no SQLite; a transação continua garantindo a ordem entre instâncias diferentes, e as
# tentativas extras cobrem o raro caso de duas instâncias ao mesmo tempo (no Cloud Run: --max-instances=1).
_TENTATIVAS = 15


def _hash(ant: str, protocolo: str, tipo: str, criado: str, corpo: str) -> str:
    # Mesma fórmula do Repositorio (SQLite): a verificação da cadeia é idêntica nos dois bancos.
    return hashlib.sha256(f"{ant}|{protocolo}|{tipo}|{criado}|{corpo}".encode()).hexdigest()


class RepositorioFirestore:
    def __init__(self, segredo_ip: str, projeto: str | None = None, cliente=None, prefixo: str = ""):
        """cliente: um google.cloud.firestore.Client já criado (testes); prefixo isola coleções nos testes."""
        from google.api_core import exceptions as gexc
        from google.cloud import firestore

        self._fs = firestore
        self._existe = gexc.AlreadyExists
        self._segredo = segredo_ip.encode()
        self._lock = threading.Lock()
        self._db = cliente or firestore.Client(project=projeto)
        self._col = self._db.collection(f"{prefixo}registros")
        self._cabeca = self._db.collection(f"{prefixo}controle").document("cadeia")

    def _ip_hmac(self, ip: str) -> str:
        return hmac.new(self._segredo, ip.encode(), hashlib.sha256).hexdigest()[:16]

    def inserir(self, tipo: str, status: str, payload: dict, ip: str, com_token: bool = False) -> dict:
        prefixo = _PREFIXOS[tipo]
        token = secrets.token_urlsafe(24) if com_token else None
        corpo = Repositorio._canonico(payload)
        ip_hmac = self._ip_hmac(ip)

        @self._fs.transactional
        def gravar(tx, protocolo: str, criado: str) -> str:
            cab = self._cabeca.get(transaction=tx)
            seq = cab.get("seq") if cab.exists else 0
            ant = cab.get("ultimo_hash") if cab.exists else GENESIS
            h = _hash(ant, protocolo, tipo, criado, corpo)
            # create (e não set): se o protocolo já existir, a transação falha em vez de sobrescrever
            tx.create(self._col.document(protocolo), {
                "protocolo": protocolo, "tipo": tipo, "status": status, "payload": corpo, "ip_hmac": ip_hmac,
                "token": token, "criado_em": criado, "seq": seq + 1, "hash_ant": ant, "audit_hash": h,
            })
            tx.set(self._cabeca, {"seq": seq + 1, "ultimo_hash": h})
            return h

        with self._lock:
            for _ in range(5):  # colisão de protocolo (3 bytes aleatórios por dia) é rara; tenta outro
                agora = datetime.now(timezone.utc)
                protocolo = f"{prefixo}-{agora:%Y%m%d}-{secrets.token_hex(3).upper()}"
                try:
                    h = gravar(self._db.transaction(max_attempts=_TENTATIVAS), protocolo, agora.isoformat(timespec="seconds"))
                    return {"protocolo": protocolo, "status": status, "audit_hash": h, "token": token}
                except self._existe:
                    continue
        raise RuntimeError("não foi possível gerar um protocolo único")

    def confirmar_optin(self, token: str) -> str | None:
        from google.cloud.firestore_v1.base_query import FieldFilter

        consulta = (self._col.where(filter=FieldFilter("tipo", "==", "optin"))
                    .where(filter=FieldFilter("token", "==", token))
                    .where(filter=FieldFilter("status", "==", "pendente_confirmacao"))
                    .limit(1))
        achados = list(consulta.stream())
        if not achados:
            return None
        ref = achados[0].reference

        @self._fs.transactional
        def confirmar(tx) -> str | None:
            snap = ref.get(transaction=tx)
            if not snap.exists or snap.get("status") != "pendente_confirmacao" or snap.get("token") != token:
                return None  # já confirmado por outra requisição
            # A confirmação muda apenas o status; o payload (e o hash) ficam intactos.
            # O token já usado é apagado (None); não é senha, apesar do aviso B105 do bandit.
            tx.update(ref, {"status": "confirmado", "token": None})  # nosec B105
            return snap.get("protocolo")

        return confirmar(self._db.transaction(max_attempts=_TENTATIVAS))

    def verificar_cadeia(self) -> bool:
        ant = GENESIS
        for doc in self._col.order_by("seq").stream():
            r = doc.to_dict()
            if r["hash_ant"] != ant or r["audit_hash"] != _hash(ant, r["protocolo"], r["tipo"], r["criado_em"], r["payload"]):
                return False
            ant = r["audit_hash"]
        return True

    def contar(self, tipo: str | None = None) -> int:
        from google.cloud.firestore_v1.base_query import FieldFilter

        consulta = self._col.where(filter=FieldFilter("tipo", "==", tipo)) if tipo else self._col
        return int(consulta.count().get()[0][0].value)
