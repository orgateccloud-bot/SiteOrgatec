"""Consultas sempre filtradas pela transportadora do usuário (isolamento entre clientes)."""

from __future__ import annotations

from datetime import date
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from transporte.db.tabelas import Base, Motorista, ParametroCusto, Viagem
from transporte.dominio import Contexto, ParametrosCusto, utc
from transporte.erros import NaoEncontrado

T = TypeVar("T", bound=Base)


def obter(sessao: Session, modelo: type[T], transportadora_id: str, id_: str) -> T:
    obj = sessao.get(modelo, id_)
    if obj is None or getattr(obj, "transportadora_id", None) != transportadora_id:
        raise NaoEncontrado()
    if getattr(obj, "deleted_at", None) is not None:
        raise NaoEncontrado()
    return obj


def parametros_vigentes(sessao: Session, transportadora_id: str, hoje: date) -> tuple[ParametrosCusto, str]:
    reg = sessao.scalars(
        select(ParametroCusto)
        .where(ParametroCusto.transportadora_id == transportadora_id, ParametroCusto.vigencia_inicio <= hoje)
        .order_by(ParametroCusto.vigencia_inicio.desc())
        .limit(1)
    ).first()
    if reg is None:
        return ParametrosCusto(), "padrão de exemplo (sem parâmetros cadastrados)"
    return ParametrosCusto.model_validate(reg.valores), reg.vigencia_inicio.isoformat()


def motorista_do_usuario(sessao: Session, ctx: Contexto) -> Motorista | None:
    return sessao.scalars(
        select(Motorista).where(
            Motorista.transportadora_id == ctx.transportadora_id, Motorista.usuario_id == ctx.usuario_id
        )
    ).first()


def listar_viagens(sessao: Session, ctx: Contexto, limite: int = 50) -> list[Viagem]:
    q = select(Viagem).where(Viagem.transportadora_id == ctx.transportadora_id, Viagem.deleted_at.is_(None))
    if ctx.papel == "motorista":
        m = motorista_do_usuario(sessao, ctx)
        if m is None:
            return []
        q = q.where(Viagem.motorista_id == m.id)
    return list(sessao.scalars(q.order_by(Viagem.partida_prevista.desc()).limit(limite)))


def viagem_visivel(sessao: Session, ctx: Contexto, viagem_id: str) -> Viagem:
    v = obter(sessao, Viagem, ctx.transportadora_id, viagem_id)
    if ctx.papel == "motorista":
        m = motorista_do_usuario(sessao, ctx)
        if m is None or v.motorista_id != m.id:
            raise NaoEncontrado()
    return v


def viagem_dict(v: Viagem, resumo: bool = False) -> dict[str, Any]:
    r = v.resultado
    base = {
        "id": v.id,
        "descricao": v.descricao,
        "status": v.status,
        "partida_prevista": utc(v.partida_prevista).isoformat(),
        "veiculo_id": v.veiculo_id,
        "motorista_id": v.motorista_id,
        "carregado": v.carregado,
        "origem": r["pontos"][0]["nome"],
        "destino": r["pontos"][-1]["nome"],
        "distancia_km": r["rota"]["distancia_km"],
        "chegada_prevista": r["jornada"]["chegada_prevista"],
        "total_despesas": r["despesas"]["total"],
        "alertas": len(r["bloqueios"]),
    }
    if not resumo:
        base.update({"resultado": r, "ajustes": v.ajustes, "criado_em": v.created_at.isoformat()})
    return base
