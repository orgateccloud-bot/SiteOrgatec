"""Servidor de desenvolvimento com dados de demonstração. NÃO usar em produção.

uvicorn transporte.dev:app --reload
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from transporte.api.app import criar_app
from transporte.config import obter_config
from transporte.db.tabelas import Motorista, Transportadora, Veiculo

log = logging.getLogger("transporte.dev")
ID_DEMO = "00000000-0000-4000-8000-000000000001"


def _semear(app) -> None:  # type: ignore[no-untyped-def]
    with app.state.servicos.sessoes.nova() as s:
        if s.scalars(select(Transportadora).where(Transportadora.id == ID_DEMO)).first():
            return
        s.add(Transportadora(id=ID_DEMO, nome="Transportadora Demonstração (dados fictícios)"))
        s.flush()
        s.add(
            Veiculo(
                transportadora_id=ID_DEMO,
                placa="DEM0A01",
                descricao="Cavalo 6x2 + carreta (demo)",
                eixos=6,
                consumo_km_l_carregado=2.3,
                consumo_km_l_vazio=2.9,
                tanque_l=700,
            )
        )
        s.add(Motorista(transportadora_id=ID_DEMO, nome="Motorista Demonstração", usuario_id="u-motorista"))
        s.commit()


config = obter_config()
if config.ambiente == "producao":
    raise RuntimeError("transporte.dev não pode ser usado em produção")
app = criar_app(config, criar_tabelas=True)
_semear(app)
log.warning("Transportadora de demonstração: %s", ID_DEMO)
