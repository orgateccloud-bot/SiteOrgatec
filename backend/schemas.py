"""Contratos de dados (Pydantic V2) dos formulários públicos do site."""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

UF = Literal[
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
    "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")


class Consentimento(BaseModel):
    """Registro de consentimento (LGPD, art. 7º, I, e art. 8º)."""

    model_config = ConfigDict(extra="forbid")
    aceito: Literal[True]
    versao_politica: str = Field(min_length=1, max_length=20)
    finalidade: str = Field(min_length=3, max_length=200)


class _ComContato(BaseModel):
    """Base dos formulários: honeypot, consentimento e ao menos um canal de retorno."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    # Honeypot: campo invisível; humanos deixam vazio.
    website: str = Field(default="", max_length=0)
    consentimento: Consentimento
    email: str | None = None
    whatsapp: str | None = None

    @field_validator("email")
    @classmethod
    def _valida_email(cls, v: str | None) -> str | None:
        if not v:
            return None
        v = v.strip().lower()
        if len(v) > 254 or not EMAIL_RE.match(v):
            raise ValueError("e-mail inválido")
        return v

    @field_validator("whatsapp")
    @classmethod
    def _valida_celular(cls, v: str | None) -> str | None:
        if not v:
            return None
        d = re.sub(r"\D", "", v)
        if len(d) == 13 and d.startswith("55"):
            d = d[2:]
        if len(d) != 11 or d[2] != "9" or int(d[:2]) < 11:
            raise ValueError("celular deve ter DDD + 9 dígitos")
        return d

    @model_validator(mode="after")
    def _algum_contato(self):
        if not self.email and not self.whatsapp:
            raise ValueError("informe e-mail ou WhatsApp")
        return self


class SimulacaoResumo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    setor: str = Field(max_length=40)
    regime: Literal["simples", "presumido", "real"]
    perfil: Literal["b2b", "b2c"]
    uf: UF
    faturamento_anual: float | None = Field(default=None, ge=0, le=1e12)
    alertas: list[Annotated[str, Field(max_length=80)]] = Field(default_factory=list, max_length=60)


# Porte e origem do pedido de proposta (Modelo C): os mesmos valores de tools/gerar_paginas.py (PORTES e ORIGENS).
Porte = Literal["mei", "pequeno", "medio", "grande", "produtor_pf"]
Origem = Literal["indicacao", "whatsapp", "instagram", "linkedin", "busca", "evento", "outro"]


class LeadIn(_ComContato):
    nome: str = Field(min_length=2, max_length=120)
    empresa: str | None = Field(default=None, max_length=160)
    porte: Porte | None = None
    origem: Origem | None = None
    simulacao: SimulacaoResumo


class OptInIn(_ComContato):
    ufs: list[UF] = Field(min_length=1, max_length=27)
    esferas: list[Literal["federal", "trabalhista", "estadual"]] = Field(min_length=1, max_length=3)


class ContatoIn(_ComContato):
    nome: str = Field(min_length=2, max_length=120)
    assunto: Literal["diagnostico", "portal", "lgpd", "outro"]
    mensagem: str = Field(min_length=10, max_length=2000)


class Recibo(BaseModel):
    protocolo: str
    status: str
    audit_hash: str
