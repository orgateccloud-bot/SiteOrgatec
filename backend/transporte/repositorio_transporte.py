"""Persistência da Central de Viagem.

Três implementações do mesmo contrato (a lógica de consulta fica em `RepositorioBase`; cada uma só implementa o armazenamento):
`RepositorioMemoria` (teste e demonstração; perde tudo ao reiniciar), `RepositorioSQLite` (tabela `transporte_docs`) e
`RepositorioFirestore` (coleções `transporte_<coleção>`, documento `<transportadora>__<id>`). A escolha é por
ORGATEC_TRANSPORTE_BANCO (`criar_repositorio`); sem a variável nada é gravado em disco. Contrato testado em
tests/py/transporte/test_repositorio_transporte.py (o Firestore só roda com o emulador).

Isolamento entre clientes: toda leitura e escrita exige o `transportadora_id`; registro de outra transportadora é NaoEncontrado.
Motorista: só nome e vínculo ao usuário (LGPD). Leituras de telemetria têm prazo de guarda (backend/retencao.py, `purgar_leituras`).
"""

from __future__ import annotations

import copy
import json
import os
import sqlite3
import threading
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from backend.transporte.dominio import ParametrosCusto, utc
from backend.transporte.erros import NaoEncontrado

COLECOES = ("veiculos", "motoristas", "viagens", "alertas", "sensores", "leituras")


def codificar(v: Any) -> Any:
    """JSON sem perda: Decimal e datas voltam como eram (o domínio usa Decimal para dinheiro)."""
    if isinstance(v, Decimal):
        return {"__t": "dec", "v": str(v)}
    if isinstance(v, datetime):
        return {"__t": "dt", "v": v.isoformat()}
    if isinstance(v, date):
        return {"__t": "d", "v": v.isoformat()}
    if isinstance(v, dict):
        return {k: codificar(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [codificar(x) for x in v]
    return v


def decodificar(v: Any) -> Any:
    if isinstance(v, dict):
        t = v.get("__t")
        if set(v) == {"__t", "v"}:
            if t == "dec":
                return Decimal(v["v"])
            if t == "dt":
                return datetime.fromisoformat(v["v"])
            if t == "d":
                return date.fromisoformat(v["v"])
        return {k: decodificar(x) for k, x in v.items()}
    if isinstance(v, list):
        return [decodificar(x) for x in v]
    return v


class RepositorioBase:
    """Consultas do módulo sobre as primitivas de armazenamento que cada implementação define."""

    def __init__(self) -> None:
        self._trava = threading.RLock()

    def _pegar(self, tid: str, colecao: str, rid: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def _gravar(self, tid: str, colecao: str, rid: str, reg: dict[str, Any]) -> None:
        raise NotImplementedError

    def _todos(self, tid: str, colecao: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _global(self, colecao: str, rid: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def _apagar_leituras(self, antes_de: datetime) -> int:
        raise NotImplementedError

    def _tenant_existe(self, tid: str) -> bool:
        raise NotImplementedError

    def _tenant_criar(self, tid: str) -> None:
        raise NotImplementedError

    # ---- transportadoras (tenant) ----
    def criar_transportadora(self, transportadora_id: str | None = None) -> str:
        tid = transportadora_id or str(uuid.uuid4())
        self._tenant_criar(tid)
        return tid

    def existe_transportadora(self, tid: str) -> bool:
        return self._tenant_existe(tid)

    # ---- genérico ----
    def inserir(self, tid: str, colecao: str, registro: dict[str, Any], id_: str | None = None) -> dict[str, Any]:
        rid = id_ or str(uuid.uuid4())
        reg = {**copy.deepcopy(registro), "id": rid, "transportadora_id": tid}
        self._gravar(tid, colecao, rid, reg)
        return copy.deepcopy(reg)

    def obter(self, tid: str, colecao: str, rid: str) -> dict[str, Any]:
        reg = self._pegar(tid, colecao, rid)
        if reg is None:
            raise NaoEncontrado()
        return copy.deepcopy(reg)

    def atualizar(self, tid: str, colecao: str, rid: str, mudancas: dict[str, Any]) -> dict[str, Any]:
        with self._trava:
            atual = self.obter(tid, colecao, rid)
            atual.update(copy.deepcopy(mudancas))
            self._gravar(tid, colecao, rid, atual)
            return copy.deepcopy(atual)

    def listar(self, tid: str, colecao: str) -> list[dict[str, Any]]:
        return [copy.deepcopy(r) for r in self._todos(tid, colecao)]

    # ---- parâmetros ----
    def parametros(self, tid: str) -> tuple[ParametrosCusto, str]:
        reg = self._pegar(tid, "parametros", "atual")
        if reg:
            return ParametrosCusto(**{k: v for k, v in reg.items() if k not in ("id", "transportadora_id")}), "cadastrados pela transportadora"
        return ParametrosCusto(), "padrão de exemplo (sem parâmetros cadastrados)"

    def salvar_parametros(self, tid: str, p: ParametrosCusto) -> None:
        self._gravar(tid, "parametros", "atual", {**p.model_dump(), "id": "atual", "transportadora_id": tid})

    # ---- telemetria ----
    def sensor_global(self, sensor_id: str) -> dict[str, Any] | None:
        """O sensor chama sem sessão de usuário: a busca é só por id; quem pergunta recebe 403 se faltar."""
        r = self._global("sensores", sensor_id)
        return copy.deepcopy(r) if r else None

    @staticmethod
    def _id_leitura(sensor_id: str, leitura_id: str) -> str:
        return f"{sensor_id}:{leitura_id}"  # a idempotência vira uma busca direta pela chave, sem varrer as leituras

    def leitura_ja_vista(self, tid: str, sensor_id: str, leitura_id: str) -> bool:
        return self._pegar(tid, "leituras", self._id_leitura(sensor_id, leitura_id)) is not None

    def registrar_leitura(self, tid: str, registro: dict[str, Any]) -> dict[str, Any]:
        return self.inserir(tid, "leituras", registro, id_=self._id_leitura(registro["sensor_id"], registro["leitura_id"]))

    def _viagens_do_veiculo(self, tid: str, veiculo_id: str) -> list[dict[str, Any]]:
        return [v for v in self._todos(tid, "viagens") if v["veiculo_id"] == veiculo_id]

    def _leituras_da_viagem(self, tid: str, viagem_id: str, limite: int) -> list[dict[str, Any]]:
        pegas = [r for r in self._todos(tid, "leituras") if r.get("viagem_id") == viagem_id]
        return sorted(pegas, key=lambda r: utc(r["ts"]), reverse=True)[:limite]

    def leituras_da_viagem(self, tid: str, viagem_id: str, limite: int = 200) -> list[dict[str, Any]]:
        """As leituras mais recentes da viagem (mais nova primeiro). Indexada no SQLite e no Firestore."""
        return [copy.deepcopy(r) for r in self._leituras_da_viagem(tid, viagem_id, limite)]

    def viagem_ativa(self, tid: str, veiculo_id: str, ts: datetime) -> dict[str, Any] | None:
        candidatas = [v for v in self._viagens_do_veiculo(tid, veiculo_id)
                      if v["status"] in ("planejada", "em_andamento")
                      and utc(v["partida_prevista"]) <= utc(ts) + timedelta(hours=12)]
        candidatas.sort(key=lambda v: v["partida_prevista"], reverse=True)
        return copy.deepcopy(candidatas[0]) if candidatas else None

    def purgar_leituras(self, antes_de: datetime) -> int:
        """Prazo de guarda (LGPD): apaga leituras mais antigas que `antes_de`. Chamado por tools/lgpd.py."""
        return self._apagar_leituras(antes_de)


class RepositorioMemoria(RepositorioBase):
    def __init__(self) -> None:
        super().__init__()
        self._dados: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}  # transportadora -> coleção -> id -> registro
        self._transportadoras: set[str] = set()

    def _tenant_criar(self, tid: str) -> None:
        with self._trava:
            self._transportadoras.add(tid)
            self._dados.setdefault(tid, {})

    def _tenant_existe(self, tid: str) -> bool:
        return tid in self._transportadoras

    def _pegar(self, tid, colecao, rid):
        with self._trava:
            return self._dados.get(tid, {}).get(colecao, {}).get(rid)

    def _gravar(self, tid, colecao, rid, reg):
        with self._trava:
            self._dados.setdefault(tid, {}).setdefault(colecao, {})[rid] = reg

    def _todos(self, tid, colecao):
        with self._trava:
            return list(self._dados.get(tid, {}).get(colecao, {}).values())

    def _global(self, colecao, rid):
        with self._trava:
            for cols in self._dados.values():
                if rid in cols.get(colecao, {}):
                    return cols[colecao][rid]
            return None

    def _apagar_leituras(self, antes_de):
        with self._trava:
            total = 0
            for cols in self._dados.values():
                velhas = [k for k, r in cols.get("leituras", {}).items() if utc(r["ts"]) < utc(antes_de)]
                for k in velhas:
                    del cols["leituras"][k]
                total += len(velhas)
            return total


class RepositorioSQLite(RepositorioBase):
    """Uma tabela de documentos JSON: (transportadora, coleção, id). Toda consulta filtra pela transportadora."""

    def __init__(self, caminho: Path | str) -> None:
        super().__init__()
        self._caminho = str(caminho)
        Path(self._caminho).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        con = self._conn()
        with con:
            con.execute("CREATE TABLE IF NOT EXISTS transporte_docs (tid TEXT NOT NULL, colecao TEXT NOT NULL, id TEXT NOT NULL, "
                        "ts TEXT, viagem_id TEXT, veiculo_id TEXT, doc TEXT NOT NULL, PRIMARY KEY (tid, colecao, id))")
            colunas = {r[1] for r in con.execute("PRAGMA table_info(transporte_docs)")}
            for nova in ("viagem_id", "veiculo_id"):  # bancos criados antes dos índices
                if nova not in colunas:
                    con.execute(f"ALTER TABLE transporte_docs ADD COLUMN {nova} TEXT")
            con.execute("CREATE TABLE IF NOT EXISTS transporte_tenants (tid TEXT PRIMARY KEY)")
            con.execute("CREATE INDEX IF NOT EXISTS transporte_docs_id ON transporte_docs (colecao, id)")
            con.execute("CREATE INDEX IF NOT EXISTS transporte_docs_viagem ON transporte_docs (tid, colecao, viagem_id, ts)")
            con.execute("CREATE INDEX IF NOT EXISTS transporte_docs_veiculo ON transporte_docs (tid, colecao, veiculo_id)")
            con.execute("CREATE INDEX IF NOT EXISTS transporte_docs_ts ON transporte_docs (colecao, ts)")

    def _conn(self) -> sqlite3.Connection:
        """Uma conexão por thread, aberta uma vez (abrir a cada operação custava mais que a própria consulta). WAL deixa leitura e
        escrita andarem juntas; synchronous NORMAL é o par recomendado do WAL."""
        con = getattr(self._local, "con", None)
        if con is None:
            con = sqlite3.connect(self._caminho, timeout=30)
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA synchronous=NORMAL")
            self._local.con = con
        return con

    def _exec(self, sql: str, args: tuple = (), escrever: bool = False):
        con = self._conn()
        with con:
            cur = con.execute(sql, args)
            return cur.rowcount if escrever else cur.fetchall()

    def _tenant_criar(self, tid):
        self._exec("INSERT OR IGNORE INTO transporte_tenants VALUES (?)", (tid,), escrever=True)

    def _tenant_existe(self, tid):
        return bool(self._exec("SELECT 1 FROM transporte_tenants WHERE tid = ?", (tid,)))

    def _pegar(self, tid, colecao, rid):
        r = self._exec("SELECT doc FROM transporte_docs WHERE tid = ? AND colecao = ? AND id = ?", (tid, colecao, rid))
        return decodificar(json.loads(r[0][0])) if r else None

    def _gravar(self, tid, colecao, rid, reg):
        ts = utc(reg["ts"]).isoformat() if colecao == "leituras" and reg.get("ts") else None
        self._exec("INSERT OR REPLACE INTO transporte_docs (tid, colecao, id, ts, viagem_id, veiculo_id, doc) VALUES (?,?,?,?,?,?,?)",
                   (tid, colecao, rid, ts, reg.get("viagem_id") if colecao == "leituras" else None,
                    reg.get("veiculo_id") if colecao == "viagens" else None, json.dumps(codificar(reg), ensure_ascii=False)), escrever=True)

    def _todos(self, tid, colecao):
        return [decodificar(json.loads(r[0])) for r in self._exec("SELECT doc FROM transporte_docs WHERE tid = ? AND colecao = ?", (tid, colecao))]

    def _global(self, colecao, rid):
        r = self._exec("SELECT doc FROM transporte_docs WHERE colecao = ? AND id = ?", (colecao, rid))
        return decodificar(json.loads(r[0][0])) if r else None

    def _viagens_do_veiculo(self, tid, veiculo_id):
        return [decodificar(json.loads(r[0])) for r in self._exec(
            "SELECT doc FROM transporte_docs WHERE tid = ? AND colecao = 'viagens' AND veiculo_id = ?", (tid, veiculo_id))]

    def _leituras_da_viagem(self, tid, viagem_id, limite):
        return [decodificar(json.loads(r[0])) for r in self._exec(
            "SELECT doc FROM transporte_docs WHERE tid = ? AND colecao = 'leituras' AND viagem_id = ? ORDER BY ts DESC LIMIT ?",
            (tid, viagem_id, limite))]

    def _apagar_leituras(self, antes_de):
        return self._exec("DELETE FROM transporte_docs WHERE colecao = 'leituras' AND ts < ?", (utc(antes_de).isoformat(),), escrever=True)


class RepositorioFirestore(RepositorioBase):
    """Coleções `<prefixo>transporte_<coleção>`; documento `<transportadora>__<id>` com os campos tid, id, ts e doc (JSON em texto)."""

    def __init__(self, projeto: str | None = None, cliente=None, prefixo: str = "") -> None:
        super().__init__()
        from google.cloud import firestore
        self._db = cliente or firestore.Client(project=projeto)
        self._prefixo = prefixo

    def _col(self, colecao: str):
        return self._db.collection(f"{self._prefixo}transporte_{colecao}")

    def _tenant_criar(self, tid):
        self._col("tenants").document(tid).set({"tid": tid})

    def _tenant_existe(self, tid):
        return self._col("tenants").document(tid).get().exists

    def _pegar(self, tid, colecao, rid):
        d = self._col(colecao).document(f"{tid}__{rid}").get()
        return decodificar(json.loads(d.get("doc"))) if d.exists else None

    def _gravar(self, tid, colecao, rid, reg):
        ts = utc(reg["ts"]).isoformat() if colecao == "leituras" and reg.get("ts") else None
        self._col(colecao).document(f"{tid}__{rid}").set({"tid": tid, "id": rid, "ts": ts, "viagem_id": reg.get("viagem_id") if colecao == "leituras" else None,
                                                          "veiculo_id": reg.get("veiculo_id") if colecao == "viagens" else None,
                                                          "doc": json.dumps(codificar(reg), ensure_ascii=False)})

    def _todos(self, tid, colecao):
        return [decodificar(json.loads(d.get("doc"))) for d in self._col(colecao).where("tid", "==", tid).stream()]

    def _global(self, colecao, rid):
        for d in self._col(colecao).where("id", "==", rid).limit(1).stream():
            return decodificar(json.loads(d.get("doc")))
        return None

    def _viagens_do_veiculo(self, tid, veiculo_id):
        return [decodificar(json.loads(d.get("doc"))) for d in self._col("viagens").where("tid", "==", tid).where("veiculo_id", "==", veiculo_id).stream()]

    def _leituras_da_viagem(self, tid, viagem_id, limite):
        # exige o índice composto de firestore.indexes.json (tid, viagem_id, ts desc); o emulador não exige
        q = self._col("leituras").where("tid", "==", tid).where("viagem_id", "==", viagem_id).order_by("ts", direction="DESCENDING").limit(limite)
        return [decodificar(json.loads(d.get("doc"))) for d in q.stream()]

    def _apagar_leituras(self, antes_de):
        total = 0
        for d in self._col("leituras").where("ts", "<", utc(antes_de).isoformat()).stream():
            d.reference.delete()
            total += 1
        return total


def criar_repositorio(env: dict[str, str] | None = None) -> RepositorioBase:
    """ORGATEC_TRANSPORTE_BANCO = memoria (padrão) | sqlite | firestore."""
    e = os.environ if env is None else env
    banco = e.get("ORGATEC_TRANSPORTE_BANCO", "memoria").strip().lower()
    if banco == "memoria":
        return RepositorioMemoria()
    if banco == "sqlite":
        padrao = Path(__file__).resolve().parents[1] / "dados" / "transporte.db"
        return RepositorioSQLite(e.get("ORGATEC_TRANSPORTE_DB") or padrao)
    if banco == "firestore":
        return RepositorioFirestore(projeto=e.get("ORGATEC_FIRESTORE_PROJETO") or None)
    raise RuntimeError(f"ORGATEC_TRANSPORTE_BANCO inválido: {banco!r} (memoria, sqlite ou firestore)")
