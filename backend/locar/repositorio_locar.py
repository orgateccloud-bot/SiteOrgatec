"""Persistência do módulo LOCAR.

Três implementações do mesmo contrato, no padrão de backend/transporte/repositorio_transporte.py: `RepositorioMemoria` (teste e
demonstração), `RepositorioSQLite` (tabela `locar_docs`) e `RepositorioFirestore` (coleções `locar_<coleção>`, documento
`<grupo>__<id>`). A escolha é por ORGATEC_LOCAR_BANCO (`criar_repositorio`). Contrato testado em tests/py/locar/test_repositorio.py
(o Firestore só roda com o emulador).

Isolamento: toda leitura e escrita exige o `grupo_id`; registro de outro grupo é NaoEncontrado. Nada é apagado por este módulo:
a trilha de auditoria e os registros ficam até o prazo de retenção ser decidido (pendência V6).

Trilha de auditoria: uma cadeia por grupo, com o mesmo `hash_trilha` dos formulários (backend/repositorio.py). Cada elo guarda
quem, o quê e quando, nunca o conteúdo dos campos. A cadeia só avança por `anexar_auditoria` (no Firestore, em transação).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.locar.erros import NaoEncontrado
from backend.repositorio import GENESIS, hash_trilha
from backend.transporte.repositorio_transporte import codificar, decodificar

COLECOES = ("entidades", "itens", "acessos", "auditoria", "auditoria_cabeca")


def agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def montar_elo(grupo_id: str, seq_ant: int, hash_ant: str, usuario_id: str, acao: str, recurso: str, recurso_id: str,
               quando: str) -> dict[str, Any]:
    """Elo da cadeia. O conteúdo do pedido não entra: só quem, qual ação, qual recurso e quando."""
    seq = seq_ant + 1
    p_hash = hashlib.sha256(f"{usuario_id}|{recurso}|{recurso_id}".encode()).hexdigest()
    h = hash_trilha(hash_ant, f"{grupo_id}:{seq}", acao, quando, p_hash)
    return {"id": f"{seq:010d}", "grupo_id": grupo_id, "seq": seq, "quando": quando, "usuario_id": usuario_id, "acao": acao,
            "recurso": recurso, "recurso_id": recurso_id, "payload_hash": p_hash, "hash_ant": hash_ant, "audit_hash": h}


class RepositorioBase:
    """Consultas do módulo sobre as primitivas de armazenamento que cada implementação define."""

    def __init__(self) -> None:
        self._trava = threading.RLock()

    def _pegar(self, gid: str, colecao: str, rid: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def _gravar(self, gid: str, colecao: str, rid: str, reg: dict[str, Any]) -> None:
        raise NotImplementedError

    def _todos(self, gid: str, colecao: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _grupo_gravar(self, gid: str, dados: dict[str, Any]) -> None:
        raise NotImplementedError

    def _grupo_pegar(self, gid: str) -> dict[str, Any] | None:
        raise NotImplementedError

    # ---- grupo (tenant) ----
    def criar_grupo(self, grupo_id: str, nome: str) -> str:
        with self._trava:
            existente = self._grupo_pegar(grupo_id)
            self._grupo_gravar(grupo_id, {"id": grupo_id, "nome": nome, **({"criado_em": existente["criado_em"]} if existente else {"criado_em": agora_iso()})})
        return grupo_id

    def obter_grupo(self, gid: str) -> dict[str, Any] | None:
        g = self._grupo_pegar(gid)
        return copy.deepcopy(g) if g else None

    def existe_grupo(self, gid: str) -> bool:
        return self._grupo_pegar(gid) is not None

    # ---- genérico ----
    def inserir(self, gid: str, colecao: str, rid: str, registro: dict[str, Any]) -> dict[str, Any]:
        reg = {**copy.deepcopy(registro), "id": rid, "grupo_id": gid}
        self._gravar(gid, colecao, rid, reg)
        return copy.deepcopy(reg)

    def obter(self, gid: str, colecao: str, rid: str) -> dict[str, Any]:
        reg = self._pegar(gid, colecao, rid)
        if reg is None:
            raise NaoEncontrado()
        return copy.deepcopy(reg)

    def existe(self, gid: str, colecao: str, rid: str) -> bool:
        return self._pegar(gid, colecao, rid) is not None

    def atualizar(self, gid: str, colecao: str, rid: str, mudancas: dict[str, Any]) -> dict[str, Any]:
        with self._trava:
            atual = self.obter(gid, colecao, rid)
            atual.update(copy.deepcopy(mudancas))
            self._gravar(gid, colecao, rid, atual)
            return copy.deepcopy(atual)

    def listar(self, gid: str, colecao: str) -> list[dict[str, Any]]:
        return sorted((copy.deepcopy(r) for r in self._todos(gid, colecao)), key=lambda r: r["id"])

    # ---- acessos (usuário → entidades) ----
    def obter_acesso(self, gid: str, usuario_id: str) -> dict[str, Any] | None:
        a = self._pegar(gid, "acessos", usuario_id)
        return copy.deepcopy(a) if a else None

    def salvar_acesso(self, gid: str, usuario_id: str, papel: str, entidades: list[str]) -> dict[str, Any]:
        return self.inserir(gid, "acessos", usuario_id, {"usuario_id": usuario_id, "papel": papel, "entidades": sorted(set(entidades))})

    # ---- trilha de auditoria ----
    def anexar_auditoria(self, gid: str, usuario_id: str, acao: str, recurso: str, recurso_id: str) -> dict[str, Any]:
        with self._trava:
            cab = self._pegar(gid, "auditoria_cabeca", "atual") or {"seq": 0, "ultimo_hash": GENESIS}
            elo = montar_elo(gid, cab["seq"], cab["ultimo_hash"], usuario_id, acao, recurso, recurso_id, agora_iso())
            self._gravar(gid, "auditoria", elo["id"], elo)
            self._gravar(gid, "auditoria_cabeca", "atual", {"id": "atual", "grupo_id": gid, "seq": elo["seq"], "ultimo_hash": elo["audit_hash"]})
            return copy.deepcopy(elo)

    def auditoria(self, gid: str, limite: int = 200) -> list[dict[str, Any]]:
        """Os últimos elos (mais novo primeiro)."""
        elos = sorted(self._todos(gid, "auditoria"), key=lambda e: e["seq"], reverse=True)
        return [copy.deepcopy(e) for e in elos[:limite]]

    def verificar_cadeia(self, gid: str) -> tuple[bool, int]:
        """Refaz a cadeia do começo: contagem contínua, elo anterior e hash de cada elo. Devolve (íntegra, quantidade de elos)."""
        elos = sorted(self._todos(gid, "auditoria"), key=lambda e: e["seq"])
        ant = GENESIS
        for n, e in enumerate(elos, start=1):
            esperado = montar_elo(gid, n - 1, ant, e["usuario_id"], e["acao"], e["recurso"], e["recurso_id"], e["quando"])
            if e["seq"] != n or e["hash_ant"] != ant or e["audit_hash"] != esperado["audit_hash"]:
                return False, len(elos)
            ant = e["audit_hash"]
        cab = self._pegar(gid, "auditoria_cabeca", "atual")
        cabeca_ok = (cab is None and not elos) or (cab is not None and cab["seq"] == len(elos) and cab["ultimo_hash"] == ant)
        return cabeca_ok, len(elos)


class RepositorioMemoria(RepositorioBase):
    def __init__(self) -> None:
        super().__init__()
        self._dados: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
        self._grupos: dict[str, dict[str, Any]] = {}

    def _grupo_gravar(self, gid, dados):
        with self._trava:
            self._grupos[gid] = dados
            self._dados.setdefault(gid, {})

    def _grupo_pegar(self, gid):
        return self._grupos.get(gid)

    def _pegar(self, gid, colecao, rid):
        with self._trava:
            return self._dados.get(gid, {}).get(colecao, {}).get(rid)

    def _gravar(self, gid, colecao, rid, reg):
        with self._trava:
            self._dados.setdefault(gid, {}).setdefault(colecao, {})[rid] = reg

    def _todos(self, gid, colecao):
        with self._trava:
            return list(self._dados.get(gid, {}).get(colecao, {}).values())


class RepositorioSQLite(RepositorioBase):
    """Uma tabela de documentos JSON: (grupo, coleção, id). Toda consulta filtra pelo grupo."""

    def __init__(self, caminho: Path | str) -> None:
        super().__init__()
        self._caminho = str(caminho)
        Path(self._caminho).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        con = self._conn()
        with con:
            con.execute("CREATE TABLE IF NOT EXISTS locar_docs (gid TEXT NOT NULL, colecao TEXT NOT NULL, id TEXT NOT NULL, "
                        "doc TEXT NOT NULL, PRIMARY KEY (gid, colecao, id))")
            con.execute("CREATE TABLE IF NOT EXISTS locar_grupos (gid TEXT PRIMARY KEY, doc TEXT NOT NULL)")

    def _conn(self) -> sqlite3.Connection:
        con = getattr(self._local, "con", None)
        if con is None:
            con = sqlite3.connect(self._caminho, timeout=30)
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA synchronous=NORMAL")
            self._local.con = con
        return con

    def _exec(self, sql: str, args: tuple = ()):
        con = self._conn()
        with con:
            return con.execute(sql, args).fetchall()

    def _grupo_gravar(self, gid, dados):
        self._exec("INSERT OR REPLACE INTO locar_grupos (gid, doc) VALUES (?,?)", (gid, json.dumps(codificar(dados), ensure_ascii=False)))

    def _grupo_pegar(self, gid):
        r = self._exec("SELECT doc FROM locar_grupos WHERE gid = ?", (gid,))
        return decodificar(json.loads(r[0][0])) if r else None

    def _pegar(self, gid, colecao, rid):
        r = self._exec("SELECT doc FROM locar_docs WHERE gid = ? AND colecao = ? AND id = ?", (gid, colecao, rid))
        return decodificar(json.loads(r[0][0])) if r else None

    def _gravar(self, gid, colecao, rid, reg):
        self._exec("INSERT OR REPLACE INTO locar_docs (gid, colecao, id, doc) VALUES (?,?,?,?)",
                   (gid, colecao, rid, json.dumps(codificar(reg), ensure_ascii=False)))

    def _todos(self, gid, colecao):
        return [decodificar(json.loads(r[0])) for r in self._exec("SELECT doc FROM locar_docs WHERE gid = ? AND colecao = ?", (gid, colecao))]


class RepositorioFirestore(RepositorioBase):
    """Coleções `<prefixo>locar_<coleção>`; documento `<grupo>__<id>` com os campos gid, id e doc (JSON em texto)."""

    def __init__(self, projeto: str | None = None, cliente=None, prefixo: str = "") -> None:
        super().__init__()
        from google.cloud import firestore

        self._fs = firestore
        self._db = cliente or firestore.Client(project=projeto)
        self._prefixo = prefixo

    def _col(self, colecao: str):
        return self._db.collection(f"{self._prefixo}locar_{colecao}")

    def _grupo_gravar(self, gid, dados):
        self._col("grupos").document(gid).set({"gid": gid, "doc": json.dumps(codificar(dados), ensure_ascii=False)})

    def _grupo_pegar(self, gid):
        d = self._col("grupos").document(gid).get()
        return decodificar(json.loads(d.get("doc"))) if d.exists else None

    def _pegar(self, gid, colecao, rid):
        d = self._col(colecao).document(f"{gid}__{rid}").get()
        return decodificar(json.loads(d.get("doc"))) if d.exists else None

    def _gravar(self, gid, colecao, rid, reg):
        self._col(colecao).document(f"{gid}__{rid}").set({"gid": gid, "id": rid, "doc": json.dumps(codificar(reg), ensure_ascii=False)})

    def _todos(self, gid, colecao):
        return [decodificar(json.loads(d.get("doc"))) for d in self._col(colecao).where("gid", "==", gid).stream()]

    def anexar_auditoria(self, gid, usuario_id, acao, recurso, recurso_id):
        """Em transação: duas instâncias do Cloud Run não bifurcam a cadeia."""
        cabeca = self._col("auditoria_cabeca").document(f"{gid}__atual")

        @self._fs.transactional
        def gravar(tx, quando: str) -> dict[str, Any]:
            cab = cabeca.get(transaction=tx)
            seq = cab.get("seq") if cab.exists else 0
            ant = cab.get("ultimo_hash") if cab.exists else GENESIS
            elo = montar_elo(gid, seq, ant, usuario_id, acao, recurso, recurso_id, quando)
            tx.create(self._col("auditoria").document(f"{gid}__{elo['id']}"), {"gid": gid, "id": elo["id"], "doc": json.dumps(elo)})
            tx.set(cabeca, {"gid": gid, "id": "atual", "doc": json.dumps({"id": "atual", "grupo_id": gid, "seq": elo["seq"], "ultimo_hash": elo["audit_hash"]}),
                            "seq": elo["seq"], "ultimo_hash": elo["audit_hash"]})
            return elo

        with self._trava:  # na mesma instância, uma escrita por vez; entre instâncias, a transação do Firestore repete se houver conflito
            return gravar(self._db.transaction(max_attempts=10), agora_iso())


def criar_repositorio(env: dict[str, str] | None = None) -> RepositorioBase:
    """ORGATEC_LOCAR_BANCO = memoria (padrão) | sqlite | firestore."""
    e = os.environ if env is None else env
    banco = e.get("ORGATEC_LOCAR_BANCO", "memoria").strip().lower()
    if banco == "memoria":
        return RepositorioMemoria()
    if banco == "sqlite":
        padrao = Path(__file__).resolve().parents[1] / "dados" / "locar.db"
        return RepositorioSQLite(e.get("ORGATEC_LOCAR_DB") or padrao)
    if banco == "firestore":
        return RepositorioFirestore(projeto=e.get("ORGATEC_FIRESTORE_PROJETO") or None)
    raise RuntimeError(f"ORGATEC_LOCAR_BANCO inválido: {banco!r} (memoria, sqlite ou firestore)")
