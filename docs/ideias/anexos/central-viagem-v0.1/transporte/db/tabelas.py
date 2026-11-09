"""Modelo de dados. Toda tabela de negócio carrega transportadora_id: o isolamento é feito nas consultas."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _agora() -> datetime:
    return datetime.now(UTC)


def _id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Auditoria:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_agora, onupdate=_agora, nullable=False
    )
    created_by: Mapped[str | None] = mapped_column(String(64))


class Transportadora(Auditoria, Base):
    __tablename__ = "tr_transportadora"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)


class Veiculo(Auditoria, Base):
    __tablename__ = "tr_veiculo"
    __table_args__ = (UniqueConstraint("transportadora_id", "placa", name="uq_veiculo_placa"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    transportadora_id: Mapped[str] = mapped_column(ForeignKey("tr_transportadora.id"), index=True, nullable=False)
    placa: Mapped[str] = mapped_column(String(8), nullable=False)
    descricao: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    eixos: Mapped[int] = mapped_column(Integer, nullable=False)
    consumo_km_l_carregado: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    consumo_km_l_vazio: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    tanque_l: Mapped[Decimal] = mapped_column(Numeric(8, 1), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Motorista(Auditoria, Base):
    """Só o necessário para a viagem (minimização — LGPD). Sem CPF, telefone ou endereço."""

    __tablename__ = "tr_motorista"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    transportadora_id: Mapped[str] = mapped_column(ForeignKey("tr_transportadora.id"), index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    usuario_id: Mapped[str | None] = mapped_column(String(64), index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ParametroCusto(Auditoria, Base):
    """Parâmetros de custo versionados por vigência. `valores` guarda Decimal como texto."""

    __tablename__ = "tr_parametro_custo"
    __table_args__ = (UniqueConstraint("transportadora_id", "vigencia_inicio", name="uq_parametro_vigencia"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    transportadora_id: Mapped[str] = mapped_column(ForeignKey("tr_transportadora.id"), index=True, nullable=False)
    vigencia_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    valores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class Viagem(Auditoria, Base):
    __tablename__ = "tr_viagem"
    __table_args__ = (Index("ix_viagem_transp_partida", "transportadora_id", "partida_prevista"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    transportadora_id: Mapped[str] = mapped_column(ForeignKey("tr_transportadora.id"), nullable=False)
    veiculo_id: Mapped[str] = mapped_column(ForeignKey("tr_veiculo.id"), nullable=False)
    motorista_id: Mapped[str | None] = mapped_column(ForeignKey("tr_motorista.id"))
    descricao: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    pontos: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    partida_prevista: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    carregado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="planejada", nullable=False)
    resultado: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    ajustes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AlertaRota(Auditoria, Base):
    """Bloqueio/interdição cadastrado manualmente (não há fonte aberta confirmada — ver README)."""

    __tablename__ = "tr_alerta_rota"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    transportadora_id: Mapped[str] = mapped_column(ForeignKey("tr_transportadora.id"), index=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    raio_km: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fonte: Mapped[str] = mapped_column(String(200), nullable=False)


class Sensor(Auditoria, Base):
    __tablename__ = "tr_sensor"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    transportadora_id: Mapped[str] = mapped_column(ForeignKey("tr_transportadora.id"), index=True, nullable=False)
    veiculo_id: Mapped[str] = mapped_column(ForeignKey("tr_veiculo.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    fornecedor: Mapped[str] = mapped_column(String(40), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    segredo_cifrado: Mapped[str] = mapped_column(String(500), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultimo_sinal_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeituraTelemetria(Base):
    __tablename__ = "tr_leitura_telemetria"
    __table_args__ = (
        UniqueConstraint("sensor_id", "leitura_id", name="uq_leitura_idempotente"),
        Index("ix_leitura_viagem_ts", "viagem_id", "ts"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    transportadora_id: Mapped[str] = mapped_column(ForeignKey("tr_transportadora.id"), nullable=False)
    sensor_id: Mapped[str] = mapped_column(ForeignKey("tr_sensor.id"), nullable=False)
    viagem_id: Mapped[str | None] = mapped_column(ForeignKey("tr_viagem.id"))
    leitura_id: Mapped[str] = mapped_column(String(80), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    velocidade_kmh: Mapped[float | None] = mapped_column(Float)
    ignicao: Mapped[bool | None] = mapped_column(Boolean)
    temperatura_c: Mapped[float | None] = mapped_column(Float)
    combustivel_pct: Mapped[float | None] = mapped_column(Float)
    evento: Mapped[str | None] = mapped_column(String(40))
    recebido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora, nullable=False)
