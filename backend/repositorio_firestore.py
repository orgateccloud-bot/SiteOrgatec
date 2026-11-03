"""Persistência no Firestore com a mesma interface e a mesma trilha de auditoria do `Repositorio` (SQLite).

Usada no Cloud Run (ORGATEC_BANCO=firestore), onde o disco do contêiner é apagado a cada reinício.

Modelo:
  registros/{protocolo}  protocolo, tipo, status, payload (JSON canônico, texto), sal, payload_hash, contatos,
                         ip_hmac, token, token_saida, criado_em, eliminado_em, motivo_eliminacao, seq, hash_ant, audit_hash
  controle/cadeia        seq, ultimo_hash  (cabeça da cadeia)

Cada inserção é uma transação que lê a cabeça, calcula o hash com a mesma fórmula do SQLite e grava o
registro e a nova cabeça juntos: dois envios simultâneos nunca recebem o mesmo hash anterior.
Clientes (navegador) não têm acesso ao banco: firestore.rules nega tudo; só a conta de serviço da API grava.

A retenção NÃO usa a política de TTL do Firestore: o TTL apaga o documento inteiro e quebraria a cadeia.
`eliminar` apaga só os dados pessoais e mantém o esqueleto (veja backend/repositorio.py).
"""

from __future__ import annotations

import secrets
import threading
from datetime import datetime, timedelta

from .repositorio import GENESIS, RepositorioBase, agora_utc, hash_payload, hash_token, hash_trilha
from .retencao import Prazos

# Toda inserção grava a cabeça da cadeia, um único documento: o Firestore aceita poucas escritas por segundo
# num mesmo documento, e transações simultâneas se anulam. Por isso, dentro da instância, as inserções entram
# numa fila (lock), como no SQLite; a transação continua garantindo a ordem entre instâncias diferentes, e as
# tentativas extras cobrem o raro caso de duas instâncias ao mesmo tempo (no Cloud Run: --max-instances=1).
_TENTATIVAS = 15


class RepositorioFirestore(RepositorioBase):
    def __init__(self, segredo_ip: str, projeto: str | None = None, cliente=None, prefixo: str = "",
                 prazos: Prazos | None = None):
        """cliente: um google.cloud.firestore.Client já criado (testes); prefixo isola coleções nos testes."""
        from google.api_core import exceptions as gexc
        from google.cloud import firestore

        super().__init__(segredo_ip, prazos)
        self._fs = firestore
        self._existe = gexc.AlreadyExists
        self._lock = threading.Lock()
        self._db = cliente or firestore.Client(project=projeto)
        self._col = self._db.collection(f"{prefixo}registros")
        self._cabeca = self._db.collection(f"{prefixo}controle").document("cadeia")

    def inserir(self, tipo: str, status: str, payload: dict, ip: str, com_token: bool = False) -> dict:
        token, saida = self._tokens(com_token)
        corpo = self._canonico(payload)
        sal = secrets.token_hex(16)
        p_hash = hash_payload(sal, corpo)
        contatos = self._contatos(payload)
        ip_hmac = self._ip_hmac(ip)

        @self._fs.transactional
        def gravar(tx, protocolo: str, criado: str) -> str:
            cab = self._cabeca.get(transaction=tx)
            seq = cab.get("seq") if cab.exists else 0
            ant = cab.get("ultimo_hash") if cab.exists else GENESIS
            h = hash_trilha(ant, protocolo, tipo, criado, p_hash)
            # create (e não set): se o protocolo já existir, a transação falha em vez de sobrescrever
            tx.create(self._col.document(protocolo), {
                "protocolo": protocolo, "tipo": tipo, "status": status, "payload": corpo, "sal": sal,
                "payload_hash": p_hash, "contatos": contatos, "ip_hmac": ip_hmac,
                "token": hash_token(token) if token else None, "token_saida": hash_token(saida) if saida else None,
                "criado_em": criado, "eliminado_em": None, "motivo_eliminacao": None,
                "seq": seq + 1, "hash_ant": ant, "audit_hash": h,
            })
            tx.set(self._cabeca, {"seq": seq + 1, "ultimo_hash": h})
            return h

        with self._lock:
            for _ in range(5):  # colisão de protocolo (3 bytes aleatórios por dia) é rara; tenta outro
                agora = agora_utc()
                protocolo = self._protocolo(tipo, agora)
                try:
                    h = gravar(self._db.transaction(max_attempts=_TENTATIVAS), protocolo, agora.isoformat(timespec="seconds"))
                    return {"protocolo": protocolo, "status": status, "audit_hash": h, "token": token, "token_saida": saida}
                except self._existe:
                    continue
        raise RuntimeError("não foi possível gerar um protocolo único")

    @staticmethod
    def _filtro(campo: str, operador: str, valor):
        from google.cloud.firestore_v1.base_query import FieldFilter

        return FieldFilter(campo, operador, valor)

    def confirmar_optin(self, token: str, agora: datetime | None = None) -> str | None:
        agora = agora or agora_utc()
        guardado = hash_token(token)
        consulta = (self._col.where(filter=self._filtro("tipo", "==", "optin"))
                    .where(filter=self._filtro("token", "==", guardado))
                    .where(filter=self._filtro("status", "==", "pendente_confirmacao"))
                    .limit(1))
        achados = list(consulta.stream())
        if not achados:
            return None
        ref = achados[0].reference

        @self._fs.transactional
        def confirmar(tx) -> str | None:
            snap = ref.get(transaction=tx)
            if not snap.exists or snap.get("status") != "pendente_confirmacao" or snap.get("token") != guardado:
                return None  # já confirmado por outra requisição
            if self._vencido(snap.get("tipo"), snap.get("status"), snap.get("criado_em"), agora):
                return None
            # A confirmação muda apenas o status; o payload (e o hash) ficam intactos.
            # O token já usado é apagado (None); não é senha, apesar do aviso B105 do bandit.
            tx.update(ref, {"status": "confirmado", "token": None})  # nosec B105
            return snap.get("protocolo")

        return confirmar(self._db.transaction(max_attempts=_TENTATIVAS))

    def revogar_optin(self, token_saida: str) -> str | None:
        """Descadastro (LGPD, art. 8º, § 5º): vale para opt-in pendente ou confirmado e elimina os dados na hora."""
        consulta = (self._col.where(filter=self._filtro("tipo", "==", "optin"))
                    .where(filter=self._filtro("token_saida", "==", hash_token(token_saida)))
                    .limit(1))
        achados = list(consulta.stream())
        if not achados or not self.eliminar(achados[0].get("protocolo"), "revogacao", status="revogado"):
            return None
        return achados[0].get("protocolo")

    def eliminar(self, protocolo: str, motivo: str, status: str = "eliminado") -> bool:
        """Apaga dados pessoais, sal e tokens; o esqueleto fica na trilha. Devolve False se já estava eliminado."""
        ref = self._col.document(protocolo)

        @self._fs.transactional
        def apagar(tx) -> bool:
            snap = ref.get(transaction=tx)
            if not snap.exists or snap.get("eliminado_em"):
                return False
            tx.update(ref, {"payload": None, "sal": None, "contatos": [], "ip_hmac": "", "token": None,  # nosec B105
                            "token_saida": None, "status": status, "motivo_eliminacao": motivo,
                            "eliminado_em": agora_utc().isoformat(timespec="seconds")})
            return True

        return apagar(self._db.transaction(max_attempts=_TENTATIVAS))

    def localizar_titular(self, email: str | None = None, whatsapp: str | None = None) -> list[dict]:
        achados = {}
        for h in self._procura(email, whatsapp):
            for doc in self._col.where(filter=self._filtro("contatos", "array_contains", h)).stream():
                achados[doc.id] = doc.to_dict()
        return [self._publico(r) for r in sorted(achados.values(), key=lambda r: r["seq"])]

    def vencidos(self, agora: datetime | None = None) -> list[dict]:
        agora = agora or agora_utc()
        # Só pelo campo criado_em (índice automático): o menor prazo define o corte, e o resto se filtra aqui.
        menor = min(self.prazos.lead_dias, self.prazos.contato_dias, self.prazos.optin_pendente_dias)
        corte = (agora - timedelta(days=menor)).isoformat(timespec="seconds")
        saida = []
        for doc in self._col.where(filter=self._filtro("criado_em", "<=", corte)).stream():
            r = doc.to_dict()
            if not r["eliminado_em"] and self._vencido(r["tipo"], r["status"], r["criado_em"], agora):
                saida.append({k: r[k] for k in ("protocolo", "tipo", "status", "criado_em")})
        return sorted(saida, key=lambda r: r["criado_em"])

    def verificar_cadeia(self) -> bool:
        ant = GENESIS
        for doc in self._col.order_by("seq").stream():
            r = doc.to_dict()
            if not self._elo_valido(ant, r):
                return False
            ant = r["audit_hash"]
        cab = self._cabeca.get()
        return (cab.get("ultimo_hash") if cab.exists else GENESIS) == ant  # pega também o último registro apagado

    def contar(self, tipo: str | None = None) -> int:
        consulta = self._col.where(filter=self._filtro("tipo", "==", tipo)) if tipo else self._col
        return int(consulta.count().get()[0][0].value)
