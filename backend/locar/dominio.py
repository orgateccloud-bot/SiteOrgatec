"""Modelos e regras de visibilidade do módulo LOCAR.

Hierarquia: grupo (o "tenant") → entidade (empresa ou produtor rural pessoa física) → item (obrigação, marco da reforma, marco societário).
Item sem `entidade_id` é do grupo todo. Nenhum dado real do grupo mora neste repositório: tudo vem do banco, por carga local
(tools/locar_carregar.py). Os campos de documento guardam só o CNPJ mascarado, nunca o CPF.

Quem vê o quê:
  equipe   toda a equipe da ORGATEC do grupo: todas as entidades, escreve.
  diretor  só as entidades do seu acesso (`locar_acessos`), lê.
  leitura  igual ao diretor, sem escrita.
  Entidade `sensivel` (produtor rural pessoa física) só aparece para a equipe e para os `titulares` listados nela, mesmo que
  o acesso do diretor a cite.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Papel = Literal["equipe", "diretor", "leitura"]
PAPEIS: tuple[str, ...] = ("equipe", "diretor", "leitura")
TipoEntidade = Literal["pj", "produtor_pf"]
StatusEntidade = Literal["planejada", "ativa", "em_incorporacao", "extinta"]
Regime = Literal["lucro_real", "lucro_presumido", "simples", "produtor_rural_pf", "a_definir"]
TipoItem = Literal["obrigacao", "evento_reforma", "marco_societario"]
StatusItem = Literal["a_fazer", "em_andamento", "entregue", "nao_se_aplica"]
Responsavel = Literal["equipe", "grupo"]

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_UID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_GRUPO = re.compile(r"^[0-9a-fA-F-]{36}$")
_FONTE = re.compile(r"^[a-z0-9_]{1,64}$")
_POLO = re.compile(r"^[a-z0-9-]{1,40}$")
_ESQUEMA_PERIGOSO = re.compile(r"^\s*(javascript|data|vbscript|file):", re.I)


def id_valido(valor: str) -> bool:
    return bool(_ID.match(valor))


def uid_valido(valor: str) -> bool:
    return bool(_UID.match(valor))


def grupo_valido(valor: str) -> bool:
    return bool(_GRUPO.match(valor))


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class GrupoEntrada(_Base):
    id: str
    nome: str = Field(min_length=1, max_length=80)
    polos: list[str] = Field(default_factory=list, max_length=20)  # polos da Janela de Campo onde o grupo opera (ids de tools/campo_polos.json)

    @field_validator("polos")
    @classmethod
    def _polos(cls, v: list[str]) -> list[str]:
        if not all(_POLO.match(x) for x in v):
            raise ValueError("polo inválido")
        return v

    @field_validator("id")
    @classmethod
    def _grupo(cls, v: str) -> str:
        if not grupo_valido(v):
            raise ValueError("o grupo deve ser um UUID")
        return v


class EntidadeEntrada(_Base):
    id: str
    nome: str = Field(min_length=1, max_length=120)
    tipo: TipoEntidade
    status: StatusEntidade = "ativa"
    sucessora_id: str | None = None
    regime: Regime = "a_definir"
    regime_vigencia: date | None = None
    documento_mascarado: str | None = Field(default=None, max_length=24)
    sensivel: bool = False
    titulares: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("id", "sucessora_id")
    @classmethod
    def _ids(cls, v: str | None) -> str | None:
        if v is not None and not id_valido(v):
            raise ValueError("id inválido (letras, números, _ e -, até 64 caracteres)")
        return v

    @field_validator("titulares")
    @classmethod
    def _titulares(cls, v: list[str]) -> list[str]:
        if not all(uid_valido(x) for x in v):
            raise ValueError("titular inválido")
        return v

    @field_validator("documento_mascarado")
    @classmethod
    def _mascara(cls, v: str | None) -> str | None:
        # CNPJ mascarado guarda no máximo 6 dígitos (filial e verificador); CPF só aparece todo mascarado.
        if v is not None and sum(c.isdigit() for c in v) > 6:
            raise ValueError("o documento deve vir mascarado")
        return v

    @model_validator(mode="after")
    def _regras(self) -> "EntidadeEntrada":
        if self.tipo == "produtor_pf":
            self.sensivel = True  # a pessoa física é sempre sensível, qualquer que seja a carga
        if self.sucessora_id == self.id:
            raise ValueError("a sucessora não pode ser a própria entidade")
        return self


class EntidadePatch(_Base):
    status: StatusEntidade | None = None
    sucessora_id: str | None = None
    regime: Regime | None = None
    regime_vigencia: date | None = None

    @field_validator("sucessora_id")
    @classmethod
    def _sucessora(cls, v: str | None) -> str | None:
        if v is not None and not id_valido(v):
            raise ValueError("id inválido")
        return v


def _evidencia(v: str | None) -> str | None:
    if v is None:
        return None
    if _ESQUEMA_PERIGOSO.match(v):
        raise ValueError("use um endereço https:// ou texto simples")
    return v


class ItemEntrada(_Base):
    id: str | None = None
    entidade_id: str | None = None
    tipo: TipoItem
    titulo: str = Field(min_length=1, max_length=160)
    prazo: date | None = None
    prazo_a_confirmar: bool = False
    responsavel: Responsavel = "equipe"
    status: StatusItem = "a_fazer"
    fonte_id: str | None = None
    modelo_id: str | None = None
    evidencia_ref: str | None = Field(default=None, max_length=300)

    @field_validator("id", "entidade_id")
    @classmethod
    def _ids(cls, v: str | None) -> str | None:
        if v is not None and not id_valido(v):
            raise ValueError("id inválido (letras, números, _ e -, até 64 caracteres)")
        return v

    @field_validator("fonte_id", "modelo_id")
    @classmethod
    def _fonte(cls, v: str | None) -> str | None:
        if v is not None and not _FONTE.match(v):
            raise ValueError("identificador de fonte inválido")
        return v

    @field_validator("evidencia_ref")
    @classmethod
    def _evidencia_ok(cls, v: str | None) -> str | None:
        return _evidencia(v)


class ItemPatch(_Base):
    titulo: str | None = Field(default=None, min_length=1, max_length=160)
    prazo: date | None = None
    prazo_a_confirmar: bool | None = None
    responsavel: Responsavel | None = None
    status: StatusItem | None = None
    evidencia_ref: str | None = Field(default=None, max_length=300)

    @field_validator("evidencia_ref")
    @classmethod
    def _evidencia_ok(cls, v: str | None) -> str | None:
        return _evidencia(v)


class AcessoEntrada(_Base):
    usuario_id: str
    papel: Papel
    entidades: list[str] = Field(default_factory=list, max_length=200)

    @field_validator("usuario_id")
    @classmethod
    def _uid(cls, v: str) -> str:
        if not uid_valido(v):
            raise ValueError("usuário inválido")
        return v

    @field_validator("entidades")
    @classmethod
    def _entidades(cls, v: list[str]) -> list[str]:
        if not all(id_valido(x) for x in v):
            raise ValueError("id de entidade inválido")
        return v


class Contexto(BaseModel):
    grupo_id: str
    usuario_id: str
    papel: Papel


def entidade_visivel(ctx: Contexto, entidade: dict[str, Any], acesso: dict[str, Any] | None) -> bool:
    """Regra única de visibilidade de entidade; todo endpoint passa por aqui."""
    if ctx.papel == "equipe":
        return True
    if entidade.get("sensivel"):
        return ctx.usuario_id in entidade.get("titulares", [])
    return entidade["id"] in (acesso or {}).get("entidades", [])


def item_visivel(item: dict[str, Any], ids_visiveis: set[str]) -> bool:
    """Item do grupo (sem entidade) todos veem; item de entidade, só quem vê a entidade."""
    return item.get("entidade_id") is None or item["entidade_id"] in ids_visiveis


def entidade_publica(ctx: Contexto, entidade: dict[str, Any]) -> dict[str, Any]:
    """O que sai na resposta: quem não é da equipe não vê a lista de titulares (nem de quem mais pode ler)."""
    saida = {k: v for k, v in entidade.items() if k != "grupo_id"}
    if ctx.papel != "equipe":
        saida.pop("titulares", None)
    return saida
