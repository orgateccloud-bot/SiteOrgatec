"""Persistência SQLite com trilha de auditoria encadeada (audit_hash).

Cada registro guarda sha256(hash_anterior + payload canônico), de modo que
qualquer alteração retroativa quebra a cadeia (verificável por `verificar_cadeia`).
O IP do remetente nunca é gravado em claro: guarda-se um HMAC com segredo do ambiente.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS registros (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    protocolo   TEXT UNIQUE NOT NULL,
    tipo        TEXT NOT NULL,            -- lead | optin | contato
    status      TEXT NOT NULL,
    payload     TEXT NOT NULL,            -- JSON canônico
    ip_hmac     TEXT NOT NULL,
    token       TEXT,                     -- confirmação de opt-in (double opt-in)
    criado_em   TEXT NOT NULL,
    hash_ant    TEXT NOT NULL,
    audit_hash  TEXT NOT NULL
);
"""

GENESIS = "0" * 64


class Repositorio:
    def __init__(self, caminho: Path, segredo_ip: str):
        self._caminho = caminho
        self._segredo = segredo_ip.encode()
        self._lock = threading.Lock()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._caminho)
        conn.row_factory = sqlite3.Row
        return conn

    def _ip_hmac(self, ip: str) -> str:
        return hmac.new(self._segredo, ip.encode(), hashlib.sha256).hexdigest()[:16]

    @staticmethod
    def _canonico(d: dict) -> str:
        return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def inserir(self, tipo: str, status: str, payload: dict, ip: str, com_token: bool = False) -> dict:
        prefixo = {"lead": "LD", "optin": "OP", "contato": "CT"}[tipo]
        protocolo = f"{prefixo}-{datetime.now(timezone.utc):%Y%m%d}-{secrets.token_hex(3).upper()}"
        token = secrets.token_urlsafe(24) if com_token else None
        criado = datetime.now(timezone.utc).isoformat(timespec="seconds")
        corpo = self._canonico(payload)
        with self._lock, self._conn() as c:
            row = c.execute("SELECT audit_hash FROM registros ORDER BY id DESC LIMIT 1").fetchone()
            ant = row["audit_hash"] if row else GENESIS
            h = hashlib.sha256(f"{ant}|{protocolo}|{tipo}|{criado}|{corpo}".encode()).hexdigest()
            c.execute(
                "INSERT INTO registros (protocolo,tipo,status,payload,ip_hmac,token,criado_em,hash_ant,audit_hash)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (protocolo, tipo, status, corpo, self._ip_hmac(ip), token, criado, ant, h),
            )
        return {"protocolo": protocolo, "status": status, "audit_hash": h, "token": token}

    def confirmar_optin(self, token: str) -> str | None:
        with self._lock, self._conn() as c:
            row = c.execute(
                "SELECT protocolo FROM registros WHERE tipo='optin' AND token=? AND status='pendente_confirmacao'",
                (token,),
            ).fetchone()
            if not row:
                return None
            # A confirmação muda apenas o status; o payload (e o hash) ficam intactos.
            c.execute("UPDATE registros SET status='confirmado', token=NULL WHERE protocolo=?", (row["protocolo"],))
            return row["protocolo"]

    def verificar_cadeia(self) -> bool:
        with self._conn() as c:
            ant = GENESIS
            for r in c.execute("SELECT * FROM registros ORDER BY id"):
                h = hashlib.sha256(
                    f"{ant}|{r['protocolo']}|{r['tipo']}|{r['criado_em']}|{r['payload']}".encode()
                ).hexdigest()
                if r["hash_ant"] != ant or r["audit_hash"] != h:
                    return False
                ant = h
        return True

    def contar(self, tipo: str | None = None) -> int:
        with self._conn() as c:
            if tipo:
                return c.execute("SELECT COUNT(*) FROM registros WHERE tipo=?", (tipo,)).fetchone()[0]
            return c.execute("SELECT COUNT(*) FROM registros").fetchone()[0]
