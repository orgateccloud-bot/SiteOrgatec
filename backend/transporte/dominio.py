"""Esquemas de entrada/saída e parâmetros de custo. Valores monetários sempre em Decimal."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

Papel = Literal["gestor", "motorista", "leitura"]
StatusViagem = Literal["planejada", "em_andamento", "concluida", "cancelada"]
TipoDespesa = Literal[
    "combustivel",
    "arla",
    "pedagio",
    "hospedagem",
    "alimentacao",
    "pneus",
    "manutencao",
    "borracharia",
    "outros",
    "reserva_imprevistos",
]


class Ponto(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    uf: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    lat: float | None = Field(default=None, ge=-34.0, le=6.0)
    lon: float | None = Field(default=None, ge=-74.0, le=-34.0)


class ParametrosCusto(BaseModel):
    """Parâmetros ajustáveis por transportadora. Padrões são EXEMPLOS de primeiro uso, não referência de mercado."""

    model_config = ConfigDict(extra="forbid")

    preco_diesel_padrao: Decimal = Field(Decimal("6.50"), ge=0)
    preco_arla_l: Decimal = Field(Decimal("4.00"), ge=0)
    arla_pct_diesel: Decimal = Field(Decimal("0.05"), ge=0, le=Decimal("0.2"))
    pedagio_tarifa_padrao_cat1: Decimal = Field(Decimal("8.00"), ge=0)
    pedagio_multiplicador_por_eixo: Decimal = Field(Decimal("1"), ge=0)
    diaria_hospedagem: Decimal = Field(Decimal("120.00"), ge=0)
    diaria_alimentacao: Decimal = Field(Decimal("90.00"), ge=0)
    custo_pneus_km: Decimal = Field(Decimal("0.12"), ge=0)
    custo_manutencao_km: Decimal = Field(Decimal("0.25"), ge=0)
    reserva_borracharia_viagem: Decimal = Field(Decimal("50.00"), ge=0)
    outros_custos_viagem: Decimal = Field(Decimal("0.00"), ge=0)
    reserva_imprevistos_pct: Decimal = Field(Decimal("0.05"), ge=0, le=Decimal("0.5"))
    pernoite_no_veiculo: bool = False
    direcao_continua_max_h: Decimal = Field(Decimal("5.5"), gt=0, le=Decimal("12"))
    pausa_min: int = Field(30, ge=0, le=240)
    refeicao_min: int = Field(60, ge=0, le=240)
    jornada_direcao_max_h: Decimal = Field(Decimal("10"), gt=0, le=Decimal("16"))
    descanso_diario_h: Decimal = Field(Decimal("11"), ge=0, le=Decimal("24"))
    tempo_parada_intermediaria_h: Decimal = Field(Decimal("1"), ge=0, le=Decimal("24"))


# Onde cada parâmetro vem e por que tem esse valor. Aparece na tela de parâmetros.
PARAMETROS_META: dict[str, dict[str, str]] = {
    "preco_diesel_padrao": {"rotulo": "Diesel (R$/l) sem dado da ANP", "fonte": "Parâmetro da transportadora"},
    "preco_arla_l": {"rotulo": "ARLA 32 (R$/l)", "fonte": "Parâmetro da transportadora"},
    "arla_pct_diesel": {"rotulo": "Consumo de ARLA (% do diesel)", "fonte": "Parâmetro da transportadora"},
    "pedagio_tarifa_padrao_cat1": {
        "rotulo": "Tarifa de pedágio por praça (cat. 1) sem tabela",
        "fonte": "Parâmetro — tarifas da ANTT não confirmadas em formato de dados abertos",
    },
    "pedagio_multiplicador_por_eixo": {
        "rotulo": "Multiplicador por eixo",
        "fonte": "Parâmetro — conferir regra da praça",
    },
    "diaria_hospedagem": {"rotulo": "Diária de hospedagem (R$)", "fonte": "Parâmetro da transportadora"},
    "diaria_alimentacao": {"rotulo": "Diária de alimentação (R$)", "fonte": "Parâmetro da transportadora"},
    "custo_pneus_km": {"rotulo": "Pneus (R$/km)", "fonte": "Parâmetro da transportadora"},
    "custo_manutencao_km": {"rotulo": "Manutenção (R$/km)", "fonte": "Parâmetro da transportadora"},
    "reserva_borracharia_viagem": {"rotulo": "Reserva de borracharia por viagem (R$)", "fonte": "Parâmetro"},
    "outros_custos_viagem": {"rotulo": "Outros custos fixos por viagem (R$)", "fonte": "Parâmetro"},
    "reserva_imprevistos_pct": {"rotulo": "Reserva para imprevistos (%)", "fonte": "Parâmetro"},
    "pernoite_no_veiculo": {"rotulo": "Pernoite na cabine (sem hospedagem)", "fonte": "Parâmetro"},
    "direcao_continua_max_h": {
        "rotulo": "Direção contínua máxima (h)",
        "fonte": "CTB art. 67-C (Lei 13.103/2015) — revisão jurídica pendente",
    },
    "pausa_min": {"rotulo": "Pausa obrigatória (min)", "fonte": "CTB art. 67-C §1º — revisão jurídica pendente"},
    "refeicao_min": {"rotulo": "Intervalo de refeição (min)", "fonte": "Parâmetro — revisão jurídica pendente"},
    "jornada_direcao_max_h": {
        "rotulo": "Direção máxima por dia (h)",
        "fonte": "Parâmetro (jornada + extras) — revisão jurídica pendente; STF ADI 5322",
    },
    "descanso_diario_h": {"rotulo": "Descanso diário (h)", "fonte": "CTB art. 67-C §3º — revisão jurídica pendente"},
    "tempo_parada_intermediaria_h": {"rotulo": "Tempo em cada parada intermediária (h)", "fonte": "Parâmetro"},
}


class VeiculoEntrada(BaseModel):
    placa: str = Field(pattern=r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")
    descricao: str = Field(default="", max_length=120)
    eixos: int = Field(ge=2, le=9)
    consumo_km_l_carregado: Decimal = Field(gt=0, le=Decimal("15"))
    consumo_km_l_vazio: Decimal = Field(gt=0, le=Decimal("20"))
    tanque_l: Decimal = Field(gt=0, le=Decimal("2000"))

    @field_validator("placa", mode="before")
    @classmethod
    def _normalizar_placa(cls, v: Any) -> Any:
        return v.replace("-", "").upper().strip() if isinstance(v, str) else v


class MotoristaEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    usuario_id: str | None = Field(default=None, max_length=64)


class LancarViagem(BaseModel):
    veiculo_id: str
    motorista_id: str | None = None
    descricao: str = Field(default="", max_length=160)
    pontos: list[Ponto] = Field(min_length=2, max_length=10)
    partida_prevista: AwareDatetime
    carregado: bool = True


class AjusteDespesa(BaseModel):
    valor: Decimal | None = Field(default=None, ge=0, le=Decimal("10000000"))


class AlertaEntrada(BaseModel):
    tipo: Literal["bloqueio", "interdicao_parcial", "obra", "outro"]
    descricao: str = Field(min_length=3, max_length=300)
    lat: float = Field(ge=-34.0, le=6.0)
    lon: float = Field(ge=-74.0, le=-34.0)
    raio_km: float = Field(default=2.0, gt=0, le=50)
    inicio: AwareDatetime
    fim: AwareDatetime | None = None
    fonte: str = Field(min_length=3, max_length=200)


TipoLancamento = Literal["abastecimento", "pedagio_pago", "parada", "ocorrencia", "posicao_manual"]
FONTE_MANUAL = "informado manualmente"


class LancamentoEntrada(BaseModel):
    """O que o motorista ou o gestor informa à mão durante a viagem. A fonte é sempre "informado manualmente"."""

    model_config = ConfigDict(extra="forbid")

    tipo: TipoLancamento
    ts: AwareDatetime
    local: str = Field(default="", max_length=120)
    lat: float | None = Field(default=None, ge=-34.0, le=6.0)
    lon: float | None = Field(default=None, ge=-74.0, le=-34.0)
    valor: Decimal | None = Field(default=None, ge=0, le=Decimal("1000000"))
    litros: Decimal | None = Field(default=None, gt=0, le=Decimal("3000"))
    preco_l: Decimal | None = Field(default=None, gt=0, le=Decimal("100"))
    observacao: str = Field(default="", max_length=300)

    @model_validator(mode="after")
    def _coerente(self) -> LancamentoEntrada:
        if (self.lat is None) != (self.lon is None):
            raise ValueError("informe latitude e longitude juntas")
        if self.tipo == "posicao_manual" and self.lat is None:
            raise ValueError("a posição informada precisa de latitude e longitude")
        if self.tipo != "abastecimento" and (self.litros is not None or self.preco_l is not None):
            raise ValueError("litros e preço por litro só valem para abastecimento")
        return self


class SensorEntrada(BaseModel):
    veiculo_id: str
    nome: str = Field(min_length=2, max_length=80)
    fornecedor: str = Field(default="generico", pattern=r"^[a-z0-9_]{2,40}$")
    tipo: Literal["rastreador", "telemetria", "temperatura", "outro"] = "rastreador"


class LeituraEntrada(BaseModel):
    """Formato normalizado de leitura. Adaptadores convertem o formato de cada fornecedor para este."""

    id: str = Field(min_length=1, max_length=80)
    ts: AwareDatetime
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    velocidade_kmh: float | None = Field(default=None, ge=0, le=250)
    ignicao: bool | None = None
    temperatura_c: float | None = Field(default=None, ge=-60, le=120)
    combustivel_pct: float | None = Field(default=None, ge=0, le=100)
    evento: str | None = Field(default=None, max_length=40)


class Contexto(BaseModel):
    transportadora_id: str
    usuario_id: str
    papel: Papel


def utc(dt: datetime) -> datetime:
    """Normaliza para UTC antes de gravar (o SQLite não guarda fuso; no PostgreSQL vira timestamptz)."""
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
