"""Escolhe real ou simulado por flag. O restante do código só conhece as interfaces."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from transporte.config import Config
from transporte.provedores.base import (
    BloqueioProvider,
    ClimaProvider,
    CombustivelProvider,
    PedagioProvider,
    RotaProvider,
)
from transporte.provedores.cache import Cache
from transporte.provedores.http import ClienteHttp
from transporte.provedores.reais import (
    BloqueioManual,
    ClimaMetNo,
    CombustivelArquivoANP,
    PedagioArquivoANTT,
    RotaORS,
)
from transporte.provedores.simulados import (
    BloqueioSimulado,
    ClimaSimulado,
    CombustivelSimulado,
    PedagioSimulado,
    RotaSimulada,
)


@dataclass
class Provedores:
    rota: RotaProvider
    combustivel: CombustivelProvider
    pedagio: PedagioProvider
    clima: ClimaProvider


class FabricaProvedores:
    """Mantém clientes e cache entre requisições; o provedor de bloqueio manual depende da sessão e do tenant."""

    def __init__(self, config: Config, cache: Cache | None = None) -> None:
        self.config = config
        self.cache = cache or Cache()
        c = config
        self._rota: RotaProvider = (
            RotaORS(
                ClienteHttp("openrouteservice", timeout=c.http_timeout, tentativas=c.http_tentativas),
                c.ors_url,
                c.ors_chave,
                self.cache,
                c.cache_ttl_rota,
            )
            if c.rota_real
            else RotaSimulada()
        )
        self._clima: ClimaProvider = (
            ClimaMetNo(
                ClienteHttp(
                    "met_norway",
                    timeout=c.http_timeout,
                    tentativas=c.http_tentativas,
                    cabecalhos={"User-Agent": c.metno_user_agent},
                ),
                c.metno_url,
                self.cache,
                c.cache_ttl_clima,
            )
            if c.clima_real
            else ClimaSimulado()
        )
        self._combustivel: CombustivelProvider = (
            CombustivelArquivoANP(c.anp_arquivo) if c.combustivel_real else CombustivelSimulado()
        )
        self._pedagio: PedagioProvider = (
            PedagioArquivoANTT(c.antt_pracas_arquivo) if c.pedagio_real else PedagioSimulado()
        )

    def provedores(self) -> Provedores:
        return Provedores(self._rota, self._combustivel, self._pedagio, self._clima)

    def bloqueio(self, sessao: Session, transportadora_id: str) -> BloqueioProvider:
        return BloqueioManual(sessao, transportadora_id) if self.config.bloqueio_manual else BloqueioSimulado()
