import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from transporte.api.app import criar_app
from transporte.config import Config
from transporte.db.tabelas import Motorista, Transportadora


def config(**kw):
    base = dict(
        _env_file=None,
        database_url="sqlite://",
        sensores_ativo=True,
        chave_cripto=Fernet.generate_key().decode(),
        chave_stream="s" * 40,
    )
    base.update(kw)
    return Config(**base)


@pytest.fixture
def ambiente():
    app = criar_app(config(), criar_tabelas=True, servir_web=False)
    s = app.state.servicos.sessoes.nova()
    a, b = Transportadora(nome="Transportadora A"), Transportadora(nome="Transportadora B")
    s.add_all([a, b])
    s.flush()
    s.add(Motorista(transportadora_id=a.id, nome="João", usuario_id="u-motorista"))
    s.commit()
    cli = TestClient(app)

    def h(tid=a.id, papel="gestor", usuario="u-gestor"):
        return {"X-Transportadora-Id": tid, "X-Usuario-Papel": papel, "X-Usuario-Id": usuario}

    return {"app": app, "cli": cli, "a": a.id, "b": b.id, "h": h}
