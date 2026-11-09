"""Engine e sessão. Uma engine por URL; a API recebe a sessão por dependência."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def criar_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        extra = {"poolclass": StaticPool} if ":memory:" in url or url == "sqlite://" else {}
        return create_engine(url, connect_args={"check_same_thread": False}, **extra)
    return create_engine(url, pool_pre_ping=True)


class FabricaSessao:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._fabrica = sessionmaker(bind=engine, expire_on_commit=False)

    def __call__(self) -> Iterator[Session]:
        sessao = self._fabrica()
        try:
            yield sessao
            sessao.commit()
        except Exception:
            sessao.rollback()
            raise
        finally:
            sessao.close()

    def nova(self) -> Session:
        return self._fabrica()
