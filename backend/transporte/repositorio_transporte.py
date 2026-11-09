"""Persistência da Central de Viagem.

Nesta versão só existe a implementação EM MEMÓRIA (`RepositorioMemoria`): serve ao teste e à demonstração e perde tudo ao
reiniciar. Criar as coleções do Firestore e as tabelas do SQLite é decisão que depende de aprovação (proposta em
docs/ideias/reestruturacao-transporte-fase5.md); quando aprovada, as duas implementações seguem este mesmo contrato, no
padrão de backend/repositorio.py e backend/repositorio_firestore.py, com teste de contrato (tests/py/transporte).

Isolamento entre clientes: toda leitura e escrita exige o `transportadora_id`; registro de outra transportadora é NaoEncontrado.
Motorista: só nome e vínculo ao usuário (LGPD). Leituras de telemetria têm prazo de guarda (backend/retencao.py, `purgar_leituras`).
"""

from __future__ import annotations

import copy
import threading
import uuid
from datetime import datetime, timedelta
from typing import Any

from backend.transporte.dominio import ParametrosCusto, utc
from backend.transporte.erros import NaoEncontrado

COLECOES = ("veiculos", "motoristas", "viagens", "alertas", "sensores", "leituras")


class RepositorioMemoria:
    def __init__(self) -> None:
        self._trava = threading.RLock()
        self._dados: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}  # transportadora -> coleção -> id -> registro
        self._parametros: dict[str, ParametrosCusto] = {}
        self._transportadoras: set[str] = set()

    # ---- transportadoras (tenant) ----
    def criar_transportadora(self, transportadora_id: str | None = None) -> str:
        with self._trava:
            tid = transportadora_id or str(uuid.uuid4())
            self._transportadoras.add(tid)
            self._dados.setdefault(tid, {c: {} for c in COLECOES})
            return tid

    def existe_transportadora(self, tid: str) -> bool:
        return tid in self._transportadoras

    # ---- genérico ----
    def inserir(self, tid: str, colecao: str, registro: dict[str, Any], id_: str | None = None) -> dict[str, Any]:
        with self._trava:
            rid = id_ or str(uuid.uuid4())
            reg = {**copy.deepcopy(registro), "id": rid, "transportadora_id": tid}
            self._dados[tid][colecao][rid] = reg
            return copy.deepcopy(reg)

    def obter(self, tid: str, colecao: str, rid: str) -> dict[str, Any]:
        with self._trava:
            reg = self._dados.get(tid, {}).get(colecao, {}).get(rid)
            if reg is None:
                raise NaoEncontrado()
            return copy.deepcopy(reg)

    def atualizar(self, tid: str, colecao: str, rid: str, mudancas: dict[str, Any]) -> dict[str, Any]:
        with self._trava:
            atual = self.obter(tid, colecao, rid)
            atual.update(copy.deepcopy(mudancas))
            self._dados[tid][colecao][rid] = atual
            return copy.deepcopy(atual)

    def listar(self, tid: str, colecao: str) -> list[dict[str, Any]]:
        with self._trava:
            return [copy.deepcopy(r) for r in self._dados.get(tid, {}).get(colecao, {}).values()]

    # ---- parâmetros ----
    def parametros(self, tid: str) -> tuple[ParametrosCusto, str]:
        with self._trava:
            p = self._parametros.get(tid)
            return (p, "cadastrados pela transportadora") if p else (ParametrosCusto(), "padrão de exemplo (sem parâmetros cadastrados)")

    def salvar_parametros(self, tid: str, p: ParametrosCusto) -> None:
        with self._trava:
            self._parametros[tid] = p

    # ---- telemetria ----
    def sensor_global(self, sensor_id: str) -> dict[str, Any] | None:
        """O sensor chama sem sessão de usuário: a busca é só por id (que embute o tenant), e quem pergunta recebe 403 se faltar."""
        with self._trava:
            for tid, cols in self._dados.items():
                if sensor_id in cols["sensores"]:
                    return copy.deepcopy(cols["sensores"][sensor_id])
            return None

    def leitura_ja_vista(self, tid: str, sensor_id: str, leitura_id: str) -> bool:
        with self._trava:
            return any(r["sensor_id"] == sensor_id and r["leitura_id"] == leitura_id for r in self._dados[tid]["leituras"].values())

    def viagem_ativa(self, tid: str, veiculo_id: str, ts: datetime) -> dict[str, Any] | None:
        with self._trava:
            candidatas = [v for v in self._dados[tid]["viagens"].values()
                          if v["veiculo_id"] == veiculo_id and v["status"] in ("planejada", "em_andamento")
                          and utc(v["partida_prevista"]) <= utc(ts) + timedelta(hours=12)]
            candidatas.sort(key=lambda v: v["partida_prevista"], reverse=True)
            return copy.deepcopy(candidatas[0]) if candidatas else None

    def purgar_leituras(self, antes_de: datetime) -> int:
        """Prazo de guarda (LGPD): apaga leituras mais antigas que `antes_de`. Chamado por tools/lgpd.py quando o repositório for persistente."""
        with self._trava:
            total = 0
            for cols in self._dados.values():
                velhas = [k for k, r in cols["leituras"].items() if utc(r["ts"]) < utc(antes_de)]
                for k in velhas:
                    del cols["leituras"][k]
                total += len(velhas)
            return total
