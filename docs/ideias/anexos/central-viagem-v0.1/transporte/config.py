"""Configuração validada na subida. Flags de integração externa e de sensores nascem desligadas."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRANSPORTE_", env_file=".env", extra="ignore")

    ambiente: Literal["desenvolvimento", "homologacao", "producao"] = "desenvolvimento"
    database_url: str = "sqlite:///./transporte.db"
    chave_cripto: str = ""
    chave_stream: str = ""
    auth_modo: Literal["dev", "externo"] = "dev"

    rota_real: bool = False
    clima_real: bool = False
    combustivel_real: bool = False
    pedagio_real: bool = False
    bloqueio_manual: bool = False
    sensores_ativo: bool = False

    ors_chave: str = ""
    ors_url: str = "https://api.openrouteservice.org"
    metno_user_agent: str = ""
    metno_url: str = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    anp_arquivo: str = "./dados/anp_precos.csv"
    antt_pracas_arquivo: str = "./dados/antt_pracas.csv"

    http_timeout: float = Field(10.0, gt=0, le=60)
    http_tentativas: int = Field(3, ge=1, le=6)
    cache_ttl_rota: int = Field(86400, ge=0)
    cache_ttl_clima: int = Field(1800, ge=0)

    @model_validator(mode="after")
    def _coerente(self) -> Config:
        erros: list[str] = []
        if self.ambiente == "producao" and self.auth_modo == "dev":
            erros.append("TRANSPORTE_AUTH_MODO=dev não é permitido em produção")
        if self.rota_real and not self.ors_chave:
            erros.append("TRANSPORTE_ROTA_REAL=true exige TRANSPORTE_ORS_CHAVE")
        if self.clima_real and not self.metno_user_agent:
            erros.append("TRANSPORTE_CLIMA_REAL=true exige TRANSPORTE_METNO_USER_AGENT")
        if self.sensores_ativo and not (self.chave_cripto and self.chave_stream):
            erros.append("TRANSPORTE_SENSORES_ATIVO=true exige TRANSPORTE_CHAVE_CRIPTO e TRANSPORTE_CHAVE_STREAM")
        if erros:
            raise ValueError("; ".join(erros))
        return self


@lru_cache
def obter_config() -> Config:
    return Config()
