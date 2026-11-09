"""Ambiente Alembic: usa TRANSPORTE_DATABASE_URL e o metadata do módulo."""

from alembic import context

from transporte.config import obter_config
from transporte.db.sessao import criar_engine
from transporte.db.tabelas import Base

alvo = Base.metadata


def rodar_offline() -> None:
    context.configure(url=obter_config().database_url, target_metadata=alvo, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def rodar_online() -> None:
    engine = criar_engine(obter_config().database_url)
    with engine.connect() as conexao:
        context.configure(connection=conexao, target_metadata=alvo, render_as_batch=conexao.dialect.name == "sqlite")
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    rodar_offline()
else:
    rodar_online()
