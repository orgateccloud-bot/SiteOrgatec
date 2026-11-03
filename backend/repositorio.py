"""Persistência SQLite com trilha de auditoria encadeada (audit_hash) compatível com a eliminação de dados.

A trilha não cobre o dado pessoal diretamente: cada registro tem um sal aleatório, e o hash encadeado guarda
payload_hash = sha256(sal + payload canônico). Alterar um payload quebra a cadeia (`verificar_cadeia`).
Eliminar (LGPD, arts. 16 e 18) apaga payload e sal e deixa só o esqueleto (protocolo, tipo, datas, hashes):
a cadeia continua íntegra, e sem o sal o payload_hash não permite confirmar nenhum dado, nem com o segredo do servidor.

O IP do remetente nunca é gravado em claro: guarda-se um HMAC com segredo do ambiente.
Os tokens de confirmação e descadastro só existem em claro no retorno de `inserir` (vão no link enviado ao
titular); o banco guarda o sha256, de modo que um vazamento do banco não permite usar os links.
Contatos ficam também como HMAC em `contatos`, para localizar um titular sem ler todo o banco.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .retencao import Prazos

SCHEMA = """
CREATE TABLE IF NOT EXISTS registros (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    protocolo         TEXT UNIQUE NOT NULL,
    tipo              TEXT NOT NULL,            -- lead | optin | contato
    status            TEXT NOT NULL,
    payload           TEXT,                     -- JSON canônico; NULL depois de eliminado
    sal               TEXT,                     -- NULL depois de eliminado
    payload_hash      TEXT NOT NULL,
    contatos          TEXT NOT NULL,            -- JSON: HMAC do e-mail e do WhatsApp
    ip_hmac           TEXT NOT NULL,
    token             TEXT,                     -- sha256 do link de confirmação (double opt-in)
    token_saida       TEXT,                     -- sha256 do link de descadastro
    criado_em         TEXT NOT NULL,
    eliminado_em      TEXT,
    motivo_eliminacao TEXT,                     -- retencao | titular | revogacao
    hash_ant          TEXT NOT NULL,
    audit_hash        TEXT NOT NULL
);
"""

GENESIS = "0" * 64
PREFIXOS = {"lead": "LD", "optin": "OP", "contato": "CT"}


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def hash_trilha(ant: str, protocolo: str, tipo: str, criado: str, payload_hash: str) -> str:
    return hashlib.sha256(f"{ant}|{protocolo}|{tipo}|{criado}|{payload_hash}".encode()).hexdigest()


def hash_payload(sal: str, corpo: str) -> str:
    return hashlib.sha256(f"{sal}|{corpo}".encode()).hexdigest()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def normalizar_whatsapp(numero: str) -> str:
    d = re.sub(r"\D", "", numero)
    return d[2:] if len(d) == 13 and d.startswith("55") else d


class RepositorioBase:
    """Regras comuns aos dois bancos; cada banco implementa só o acesso aos dados."""

    def __init__(self, segredo_ip: str, prazos: Prazos | None = None):
        self._segredo = segredo_ip.encode()
        self.prazos = prazos or Prazos()

    def _ip_hmac(self, ip: str) -> str:
        return hmac.new(self._segredo, ip.encode(), hashlib.sha256).hexdigest()[:16]

    def _contato_hmac(self, canal: str, valor: str) -> str:
        return hmac.new(self._segredo, f"contato|{canal}|{valor}".encode(), hashlib.sha256).hexdigest()[:32]

    def _procura(self, email: str | None, whatsapp: str | None) -> list[str]:
        saida = []
        if email:
            saida.append(self._contato_hmac("email", normalizar_email(email)))
        if whatsapp:
            saida.append(self._contato_hmac("whatsapp", normalizar_whatsapp(whatsapp)))
        return saida

    def _contatos(self, payload: dict) -> list[str]:
        return self._procura(payload.get("email"), payload.get("whatsapp"))

    @staticmethod
    def _canonico(d: dict) -> str:
        return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _protocolo(tipo: str, agora: datetime) -> str:
        return f"{PREFIXOS[tipo]}-{agora:%Y%m%d}-{secrets.token_hex(3).upper()}"

    @staticmethod
    def _tokens(com_token: bool) -> tuple[str | None, str | None]:
        return (secrets.token_urlsafe(24), secrets.token_urlsafe(24)) if com_token else (None, None)

    def _vencido(self, tipo: str, status: str, criado_em: str, agora: datetime) -> bool:
        dias = self.prazos.dias(tipo, status)
        return dias is not None and datetime.fromisoformat(criado_em) + timedelta(days=dias) <= agora

    @staticmethod
    def _elo_valido(ant: str, r: dict) -> bool:
        """Confere um registro contra o anterior. Payload sumido sem registro de eliminação também é adulteração."""
        if r["hash_ant"] != ant:
            return False
        if r["audit_hash"] != hash_trilha(ant, r["protocolo"], r["tipo"], r["criado_em"], r["payload_hash"]):
            return False
        if r["payload"] is None:
            return bool(r["eliminado_em"])
        return bool(r["sal"]) and r["payload_hash"] == hash_payload(r["sal"], r["payload"])

    @staticmethod
    def _publico(r: dict) -> dict:
        return {"protocolo": r["protocolo"], "tipo": r["tipo"], "status": r["status"], "criado_em": r["criado_em"],
                "dados": json.loads(r["payload"])}


class Repositorio(RepositorioBase):
    def __init__(self, caminho: Path, segredo_ip: str, prazos: Prazos | None = None):
        super().__init__(segredo_ip, prazos)
        self._caminho = caminho
        self._lock = threading.Lock()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            colunas = [r["name"] for r in c.execute("PRAGMA table_info(registros)")]
            if colunas and "sal" not in colunas:
                # Banco local da versão anterior (a API nunca recebeu dados reais): guarda de lado, não apaga.
                c.execute("ALTER TABLE registros RENAME TO registros_antes_lgpd")
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._caminho)
        conn.row_factory = sqlite3.Row
        return conn

    def inserir(self, tipo: str, status: str, payload: dict, ip: str, com_token: bool = False) -> dict:
        agora = agora_utc()
        protocolo = self._protocolo(tipo, agora)
        token, saida = self._tokens(com_token)
        criado = agora.isoformat(timespec="seconds")
        corpo = self._canonico(payload)
        sal = secrets.token_hex(16)
        p_hash = hash_payload(sal, corpo)
        with self._lock, self._conn() as c:
            row = c.execute("SELECT audit_hash FROM registros ORDER BY id DESC LIMIT 1").fetchone()
            ant = row["audit_hash"] if row else GENESIS
            h = hash_trilha(ant, protocolo, tipo, criado, p_hash)
            c.execute(
                "INSERT INTO registros (protocolo,tipo,status,payload,sal,payload_hash,contatos,ip_hmac,token,"
                "token_saida,criado_em,hash_ant,audit_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (protocolo, tipo, status, corpo, sal, p_hash, json.dumps(self._contatos(payload)), self._ip_hmac(ip),
                 hash_token(token) if token else None, hash_token(saida) if saida else None, criado, ant, h),
            )
        return {"protocolo": protocolo, "status": status, "audit_hash": h, "token": token, "token_saida": saida}

    def confirmar_optin(self, token: str, agora: datetime | None = None) -> str | None:
        agora = agora or agora_utc()
        with self._lock, self._conn() as c:
            row = c.execute(
                "SELECT protocolo, tipo, status, criado_em FROM registros "
                "WHERE tipo='optin' AND token=? AND status='pendente_confirmacao'",
                (hash_token(token),),
            ).fetchone()
            if not row or self._vencido(row["tipo"], row["status"], row["criado_em"], agora):
                return None
            # A confirmação muda apenas o status; o payload (e o hash) ficam intactos.
            c.execute("UPDATE registros SET status='confirmado', token=NULL WHERE protocolo=?", (row["protocolo"],))
            return row["protocolo"]

    def revogar_optin(self, token_saida: str) -> str | None:
        """Descadastro (LGPD, art. 8º, § 5º): vale para opt-in pendente ou confirmado e elimina os dados na hora."""
        with self._conn() as c:
            row = c.execute(
                "SELECT protocolo FROM registros WHERE tipo='optin' AND token_saida=? AND eliminado_em IS NULL",
                (hash_token(token_saida),),
            ).fetchone()
        if not row or not self.eliminar(row["protocolo"], "revogacao", status="revogado"):
            return None
        return row["protocolo"]

    def eliminar(self, protocolo: str, motivo: str, status: str = "eliminado") -> bool:
        """Apaga dados pessoais, sal e tokens; o esqueleto fica na trilha. Devolve False se já estava eliminado."""
        with self._lock, self._conn() as c:
            cur = c.execute(
                "UPDATE registros SET payload=NULL, sal=NULL, contatos='[]', ip_hmac='', token=NULL, token_saida=NULL, "
                "status=?, eliminado_em=?, motivo_eliminacao=? WHERE protocolo=? AND eliminado_em IS NULL",
                (status, agora_utc().isoformat(timespec="seconds"), motivo, protocolo),
            )
            return cur.rowcount == 1

    def localizar_titular(self, email: str | None = None, whatsapp: str | None = None) -> list[dict]:
        procura = set(self._procura(email, whatsapp))
        with self._conn() as c:
            linhas = c.execute("SELECT * FROM registros WHERE eliminado_em IS NULL ORDER BY id").fetchall()
        return [self._publico(dict(r)) for r in linhas if procura & set(json.loads(r["contatos"]))]

    def vencidos(self, agora: datetime | None = None) -> list[dict]:
        agora = agora or agora_utc()
        with self._conn() as c:
            linhas = c.execute(
                "SELECT protocolo, tipo, status, criado_em FROM registros WHERE eliminado_em IS NULL ORDER BY id"
            ).fetchall()
        return [dict(r) for r in linhas if self._vencido(r["tipo"], r["status"], r["criado_em"], agora)]

    def verificar_cadeia(self) -> bool:
        with self._conn() as c:
            ant = GENESIS
            for r in c.execute("SELECT * FROM registros ORDER BY id"):
                if not self._elo_valido(ant, dict(r)):
                    return False
                ant = r["audit_hash"]
        return True

    def contar(self, tipo: str | None = None) -> int:
        with self._conn() as c:
            if tipo:
                return c.execute("SELECT COUNT(*) FROM registros WHERE tipo=?", (tipo,)).fetchone()[0]
            return c.execute("SELECT COUNT(*) FROM registros").fetchone()[0]
