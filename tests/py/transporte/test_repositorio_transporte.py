"""Contrato do repositório da Central de Viagem: memória, SQLite e (com o emulador) Firestore se comportam igual.

Firestore: firebase emulators:exec --only firestore --project demo-orgatec "python -m pytest tests/py/transporte/test_repositorio_transporte.py"
Sem FIRESTORE_EMULATOR_HOST os casos do Firestore são pulados.
"""

import os
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from backend.transporte.dominio import ParametrosCusto
from backend.transporte.erros import NaoEncontrado
from backend.transporte.repositorio_transporte import (
    RepositorioFirestore,
    RepositorioMemoria,
    RepositorioSQLite,
    criar_repositorio,
)


@pytest.fixture(params=["memoria", "sqlite", "firestore"])
def repo(request, tmp_path):
    if request.param == "memoria":
        return RepositorioMemoria()
    if request.param == "sqlite":
        return RepositorioSQLite(tmp_path / "t.db")
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        pytest.skip("emulador do Firestore não está rodando")
    return RepositorioFirestore(projeto="demo-orgatec", prefixo=f"t{uuid.uuid4().hex[:8]}_")


def test_isolamento_entre_transportadoras(repo):
    a, b = repo.criar_transportadora(), repo.criar_transportadora()
    v = repo.inserir(a, "veiculos", {"placa": "ABC1D23"})
    assert repo.obter(a, "veiculos", v["id"])["placa"] == "ABC1D23"
    with pytest.raises(NaoEncontrado):
        repo.obter(b, "veiculos", v["id"])
    assert repo.listar(b, "veiculos") == []
    assert repo.existe_transportadora(a) and not repo.existe_transportadora("inexistente")


def test_decimal_e_data_voltam_como_eram(repo):
    t = repo.criar_transportadora()
    quando = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)
    v = repo.inserir(t, "viagens", {"veiculo_id": "x", "status": "planejada", "partida_prevista": quando, "resultado": {"total": Decimal("1234.50")}})
    lido = repo.obter(t, "viagens", v["id"])
    assert lido["resultado"]["total"] == Decimal("1234.50") and isinstance(lido["resultado"]["total"], Decimal)
    assert lido["partida_prevista"] == quando


def test_atualizar_e_parametros(repo):
    t = repo.criar_transportadora()
    v = repo.inserir(t, "viagens", {"veiculo_id": "x", "status": "planejada", "partida_prevista": datetime.now(UTC)})
    assert repo.atualizar(t, "viagens", v["id"], {"status": "em_andamento"})["status"] == "em_andamento"
    padrao, vig = repo.parametros(t)
    assert "padrão" in vig
    repo.salvar_parametros(t, padrao.model_copy(update={"diaria_hospedagem": Decimal("200.00")}))
    novo, vig2 = repo.parametros(t)
    assert isinstance(novo, ParametrosCusto) and novo.diaria_hospedagem == Decimal("200.00") and "cadastrados" in vig2


def test_sensor_global_viagem_ativa_e_idempotencia(repo):
    t = repo.criar_transportadora()
    s = repo.inserir(t, "sensores", {"nome": "S1"}, id_="sensor-abc")
    assert repo.sensor_global("sensor-abc")["id"] == s["id"] and repo.sensor_global("nao-existe") is None
    agora = datetime.now(UTC)
    repo.inserir(t, "viagens", {"veiculo_id": "V1", "status": "em_andamento", "partida_prevista": agora - timedelta(hours=1)})
    assert repo.viagem_ativa(t, "V1", agora)["veiculo_id"] == "V1" and repo.viagem_ativa(t, "V2", agora) is None
    repo.registrar_leitura(t, {"sensor_id": "sensor-abc", "leitura_id": "L1", "ts": agora, "viagem_id": None})
    assert repo.leitura_ja_vista(t, "sensor-abc", "L1") and not repo.leitura_ja_vista(t, "sensor-abc", "L2")


def test_purga_so_leituras_antigas(repo):
    t = repo.criar_transportadora()
    agora = datetime.now(UTC)
    repo.registrar_leitura(t, {"sensor_id": "s", "leitura_id": "velha", "ts": agora - timedelta(days=40), "viagem_id": None})
    repo.registrar_leitura(t, {"sensor_id": "s", "leitura_id": "nova", "ts": agora, "viagem_id": None})
    assert repo.purgar_leituras(agora - timedelta(days=30)) == 1
    assert [x["leitura_id"] for x in repo.listar(t, "leituras")] == ["nova"]


def test_sqlite_persiste_entre_instancias(tmp_path):
    t = RepositorioSQLite(tmp_path / "p.db")
    tid = t.criar_transportadora()
    t.inserir(tid, "veiculos", {"placa": "ZZZ9Z99"})
    outro = RepositorioSQLite(tmp_path / "p.db")
    assert outro.existe_transportadora(tid) and outro.listar(tid, "veiculos")[0]["placa"] == "ZZZ9Z99"


def test_criar_repositorio_por_variavel(tmp_path):
    assert isinstance(criar_repositorio({}), RepositorioMemoria)
    assert isinstance(criar_repositorio({"ORGATEC_TRANSPORTE_BANCO": "sqlite", "ORGATEC_TRANSPORTE_DB": str(tmp_path / "x.db")}), RepositorioSQLite)
    with pytest.raises(RuntimeError):
        criar_repositorio({"ORGATEC_TRANSPORTE_BANCO": "mongo"})


def test_leituras_da_viagem_vem_da_mais_nova_para_a_mais_antiga_e_so_da_viagem(repo):
    t, outro = repo.criar_transportadora(), repo.criar_transportadora()
    agora = datetime.now(UTC)
    for i in range(5):
        repo.registrar_leitura(t, {"sensor_id": "s", "leitura_id": f"a{i}", "ts": agora - timedelta(minutes=10 - i), "viagem_id": "V1"})
    repo.registrar_leitura(t, {"sensor_id": "s", "leitura_id": "b0", "ts": agora, "viagem_id": "V2"})
    repo.registrar_leitura(outro, {"sensor_id": "s2", "leitura_id": "c0", "ts": agora, "viagem_id": "V1"})  # mesmo id de viagem, outro cliente
    ids = [r["leitura_id"] for r in repo.leituras_da_viagem(t, "V1", 3)]
    assert ids == ["a4", "a3", "a2"]
    assert len(repo.leituras_da_viagem(t, "V1", 200)) == 5 and [r["leitura_id"] for r in repo.leituras_da_viagem(outro, "V1")] == ["c0"]
    assert repo.leituras_da_viagem(t, "V9") == []


def test_mesma_leitura_nao_duplica(repo):
    t = repo.criar_transportadora()
    reg = {"sensor_id": "s", "leitura_id": "L1", "ts": datetime.now(UTC), "viagem_id": None}
    repo.registrar_leitura(t, reg)
    repo.registrar_leitura(t, reg)
    assert len(repo.listar(t, "leituras")) == 1
