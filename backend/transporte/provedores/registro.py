"""Escolhe os provedores. Padrão: simulados. Cada tipo real liga por flag e exige a sua configuração; se faltar, a API recusa
(RecursoDesligado) em vez de cair em dado simulado sem aviso.

  ORGATEC_TRANSPORTE_ROTA_REAL=1         exige ORGATEC_TRANSPORTE_ORS_CHAVE (opcional: ORGATEC_TRANSPORTE_ORS_URL), ou, com
                                         ORGATEC_TRANSPORTE_ROTA_FONTE=google, ORGATEC_TRANSPORTE_GOOGLE_CHAVE (Routes API + Geocoding API)
  ORGATEC_TRANSPORTE_CLIMA_REAL=1        exige ORGATEC_TRANSPORTE_METNO_CONTATO (e-mail ou site, vai no User-Agent)
  ORGATEC_TRANSPORTE_COMBUSTIVEL_REAL=1  exige ORGATEC_TRANSPORTE_ANP_ARQUIVO (CSV da ANP)
  ORGATEC_TRANSPORTE_PEDAGIO_REAL=1      exige ORGATEC_TRANSPORTE_ANTT_ARQUIVO (CSV da ANTT)
Os dois arquivos vêm de `python tools/transporte_dados_abertos.py`. Bloqueios seguem manuais (não há API aberta confirmada).
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.transporte.erros import RecursoDesligado
from backend.transporte.provedores.base import (
    BloqueioProvider,
    ClimaProvider,
    CombustivelProvider,
    PedagioProvider,
    RotaProvider,
)
from backend.transporte.provedores.cache import Cache
from backend.transporte.provedores.http import ClienteHttp
from backend.transporte.provedores.reais import ClimaMetNo, CombustivelANP, PedagioANTT, RotaGoogle, RotaORS
from backend.transporte.provedores.simulados import (
    BloqueioSimulado,
    ClimaSimulado,
    CombustivelSimulado,
    PedagioSimulado,
    RotaSimulada,
)

ORS_URL = "https://api.openrouteservice.org"
METNO_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
_CACHE = Cache()  # único por processo: o cache de rota e de clima vale entre requisições


@dataclass
class Provedores:
    rota: RotaProvider
    combustivel: CombustivelProvider
    pedagio: PedagioProvider
    clima: ClimaProvider

    def reais(self) -> list[str]:
        return [n for n, p in (("rota", self.rota), ("combustivel", self.combustivel), ("pedagio", self.pedagio), ("clima", self.clima))
                if not type(p).__name__.endswith(("Simulada", "Simulado"))]


def provedores_simulados() -> Provedores:
    return Provedores(RotaSimulada(), CombustivelSimulado(), PedagioSimulado(), ClimaSimulado())


def bloqueio_simulado() -> BloqueioProvider:
    return BloqueioSimulado()


def _exigir(env: dict[str, str], variavel: str, motivo: str) -> str:
    valor = env.get(variavel, "").strip()
    if not valor:
        raise RecursoDesligado(f"{motivo} exige {variavel}")
    return valor


def provedores_do_ambiente(env: dict[str, str], cache: Cache | None = None, transporte=None) -> Provedores:
    """`transporte` (httpx.BaseTransport) existe só para o teste simular a rede."""
    cache = cache or _CACHE
    p = provedores_simulados()

    def ligado(nome: str) -> bool:
        return env.get(f"ORGATEC_TRANSPORTE_{nome}_REAL", "0") == "1"

    if ligado("ROTA"):
        if env.get("ORGATEC_TRANSPORTE_ROTA_FONTE", "ors").strip().lower() == "google":
            chave = _exigir(env, "ORGATEC_TRANSPORTE_GOOGLE_CHAVE", "rota real (Google)")
            p.rota = RotaGoogle(ClienteHttp("google_routes", transporte=transporte), chave, cache, 86400)
        else:
            chave = _exigir(env, "ORGATEC_TRANSPORTE_ORS_CHAVE", "rota real")
            p.rota = RotaORS(ClienteHttp("openrouteservice", transporte=transporte),
                             env.get("ORGATEC_TRANSPORTE_ORS_URL", ORS_URL), chave, cache, 86400)
    if ligado("CLIMA"):
        contato = _exigir(env, "ORGATEC_TRANSPORTE_METNO_CONTATO", "clima real")
        p.clima = ClimaMetNo(ClienteHttp("met_norway", transporte=transporte, cabecalhos={"User-Agent": f"orgatec.io/1.0 ({contato})"}),
                             METNO_URL, cache, 1800)
    if ligado("COMBUSTIVEL"):
        p.combustivel = CombustivelANP(_exigir(env, "ORGATEC_TRANSPORTE_ANP_ARQUIVO", "combustível real"))
    if ligado("PEDAGIO"):
        p.pedagio = PedagioANTT(_exigir(env, "ORGATEC_TRANSPORTE_ANTT_ARQUIVO", "pedágio real"))
    return p
