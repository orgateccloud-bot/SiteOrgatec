"""Endpoints da Central de Viagem e do portal do cliente (prefixo /api/transporte)."""

from __future__ import annotations

import asyncio
import json
import random
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from transporte.api.deps import Servicos, contexto, exigir, sensores_ligados, servicos, sessao
from transporte.db import repositorios as repo
from transporte.db.tabelas import (
    AlertaRota,
    LeituraTelemetria,
    Motorista,
    ParametroCusto,
    Sensor,
    Transportadora,
    Veiculo,
    Viagem,
)
from transporte.dominio import (
    PARAMETROS_META,
    AjusteDespesa,
    AlertaEntrada,
    Contexto,
    LancarViagem,
    MotoristaEntrada,
    ParametrosCusto,
    SensorEntrada,
    TipoDespesa,
    VeiculoEntrada,
    utc,
)
from transporte.erros import EntradaInvalida
from transporte.geo import acumulado_km, ponto_no_km
from transporte.servicos import viagem as svc_viagem
from transporte.telemetria import ingestao
from transporte.telemetria.seguranca import assinar, gerar_token_stream, verificar_token_stream

router = APIRouter(prefix="/api/transporte", tags=["transporte"])
GESTOR = exigir("gestor")
LANCA = exigir("gestor", "motorista")

# Dependências tipadas (evita chamada em default de argumento — padrão FastAPI).
Db = Depends(sessao)
Srv = Depends(servicos)
Ctx = Depends(contexto)


class MudarStatus(BaseModel):
    status: Literal["planejada", "em_andamento", "concluida", "cancelada"]


def _veiculo_dict(v: Veiculo) -> dict[str, Any]:
    return {
        "id": v.id,
        "placa": v.placa,
        "descricao": v.descricao,
        "eixos": v.eixos,
        "consumo_km_l_carregado": str(v.consumo_km_l_carregado),
        "consumo_km_l_vazio": str(v.consumo_km_l_vazio),
        "tanque_l": str(v.tanque_l),
    }


@router.get("/contexto")
def ver_contexto(ctx: Contexto = Ctx, s: Servicos = Srv, db: Session = Db) -> dict[str, Any]:
    t = db.get(Transportadora, ctx.transportadora_id)
    c = s.config
    return {
        "transportadora": t.nome if t else "",
        "papel": ctx.papel,
        "ambiente": c.ambiente,
        "flags": {
            "rota_real": c.rota_real,
            "clima_real": c.clima_real,
            "combustivel_real": c.combustivel_real,
            "pedagio_real": c.pedagio_real,
            "bloqueio_manual": c.bloqueio_manual,
            "sensores_ativo": c.sensores_ativo,
        },
    }


# ---------- Parâmetros ----------
@router.get("/parametros")
def ver_parametros(ctx: Contexto = Ctx, db: Session = Db) -> dict[str, Any]:
    p, vig = repo.parametros_vigentes(db, ctx.transportadora_id, date.today())
    return {"vigencia": vig, "valores": p.model_dump(mode="json"), "meta": PARAMETROS_META}


@router.put("/parametros")
def salvar_parametros(entrada: ParametrosCusto, ctx: Contexto = Depends(GESTOR), db: Session = Db) -> dict[str, Any]:  # noqa: B008
    hoje = date.today()
    atual = db.scalars(
        select(ParametroCusto).where(
            ParametroCusto.transportadora_id == ctx.transportadora_id, ParametroCusto.vigencia_inicio == hoje
        )
    ).first()
    valores = entrada.model_dump(mode="json")
    if atual:
        atual.valores = valores
    else:
        db.add(
            ParametroCusto(
                transportadora_id=ctx.transportadora_id,
                vigencia_inicio=hoje,
                valores=valores,
                created_by=ctx.usuario_id,
            )
        )
    return {"vigencia": hoje.isoformat(), "valores": valores}


# ---------- Veículos e motoristas ----------
@router.get("/veiculos")
def listar_veiculos(ctx: Contexto = Ctx, db: Session = Db) -> list[dict[str, Any]]:
    q = select(Veiculo).where(Veiculo.transportadora_id == ctx.transportadora_id, Veiculo.ativo.is_(True))
    return [_veiculo_dict(v) for v in db.scalars(q.order_by(Veiculo.placa))]


@router.post("/veiculos", status_code=201)
def criar_veiculo(entrada: VeiculoEntrada, ctx: Contexto = Depends(GESTOR), db: Session = Db) -> dict[str, Any]:  # noqa: B008
    existe = db.scalars(
        select(Veiculo).where(Veiculo.transportadora_id == ctx.transportadora_id, Veiculo.placa == entrada.placa)
    ).first()
    if existe:
        raise EntradaInvalida("Placa já cadastrada.")
    v = Veiculo(transportadora_id=ctx.transportadora_id, created_by=ctx.usuario_id, **entrada.model_dump())
    db.add(v)
    db.flush()
    return _veiculo_dict(v)


@router.get("/motoristas")
def listar_motoristas(ctx: Contexto = Depends(GESTOR), db: Session = Db) -> list[dict[str, Any]]:  # noqa: B008
    q = select(Motorista).where(Motorista.transportadora_id == ctx.transportadora_id, Motorista.ativo.is_(True))
    return [{"id": m.id, "nome": m.nome} for m in db.scalars(q.order_by(Motorista.nome))]


@router.post("/motoristas", status_code=201)
def criar_motorista(entrada: MotoristaEntrada, ctx: Contexto = Depends(GESTOR), db: Session = Db) -> dict[str, Any]:  # noqa: B008
    m = Motorista(transportadora_id=ctx.transportadora_id, created_by=ctx.usuario_id, **entrada.model_dump())
    db.add(m)
    db.flush()
    return {"id": m.id, "nome": m.nome}


# ---------- Viagens ----------
def _calcular(
    db: Session, s: Servicos, ctx: Contexto, entrada: LancarViagem, ajustes: dict[str, str]
) -> dict[str, Any]:
    veiculo = repo.obter(db, Veiculo, ctx.transportadora_id, entrada.veiculo_id)
    params, vig = repo.parametros_vigentes(db, ctx.transportadora_id, date.today())
    consumo = veiculo.consumo_km_l_carregado if entrada.carregado else veiculo.consumo_km_l_vazio
    return svc_viagem.montar(
        entrada.pontos,
        eixos=veiculo.eixos,
        consumo_km_l=consumo,
        partida=entrada.partida_prevista,
        parametros=params,
        parametros_vigencia=vig,
        provedores=s.provedores.provedores(),
        bloqueios=s.provedores.bloqueio(db, ctx.transportadora_id),
        ajustes=ajustes,
    )


@router.post("/viagens", status_code=201)
def lancar_viagem(entrada: LancarViagem, ctx: Contexto = Depends(LANCA), s: Servicos = Srv, db: Session = Db) -> dict:  # noqa: B008
    motorista_id = entrada.motorista_id
    if ctx.papel == "motorista":
        m = repo.motorista_do_usuario(db, ctx)
        if m is None:
            raise EntradaInvalida("Usuário não está vinculado a um motorista desta transportadora.")
        motorista_id = m.id
    elif motorista_id:
        repo.obter(db, Motorista, ctx.transportadora_id, motorista_id)
    resultado = _calcular(db, s, ctx, entrada, {})
    v = Viagem(
        transportadora_id=ctx.transportadora_id,
        veiculo_id=entrada.veiculo_id,
        motorista_id=motorista_id,
        descricao=entrada.descricao or f"{entrada.pontos[0].nome} → {entrada.pontos[-1].nome}",
        pontos=[p.model_dump() for p in entrada.pontos],
        partida_prevista=utc(entrada.partida_prevista),
        carregado=entrada.carregado,
        resultado=resultado,
        ajustes={},
        created_by=ctx.usuario_id,
    )
    db.add(v)
    db.flush()
    return repo.viagem_dict(v)


@router.get("/viagens")
def listar(ctx: Contexto = Ctx, db: Session = Db) -> list[dict[str, Any]]:
    return [repo.viagem_dict(v, resumo=True) for v in repo.listar_viagens(db, ctx)]


@router.get("/viagens/{viagem_id}")
def detalhar(viagem_id: str, ctx: Contexto = Ctx, db: Session = Db) -> dict[str, Any]:
    return repo.viagem_dict(repo.viagem_visivel(db, ctx, viagem_id))


@router.put("/viagens/{viagem_id}/despesas/{tipo}")
def ajustar_despesa(
    viagem_id: str,
    tipo: TipoDespesa,
    entrada: AjusteDespesa,
    ctx: Contexto = Depends(GESTOR),  # noqa: B008
    db: Session = Db,
) -> dict[str, Any]:
    v = repo.viagem_visivel(db, ctx, viagem_id)
    ajustes = dict(v.ajustes)
    if entrada.valor is None:
        ajustes.pop(tipo, None)
    else:
        ajustes[tipo] = str(entrada.valor)
    resultado = dict(v.resultado)
    resultado["despesas"] = svc_viagem.recalcular_despesas(resultado, ajustes)
    v.resultado, v.ajustes = resultado, ajustes
    return repo.viagem_dict(v)


@router.post("/viagens/{viagem_id}/recalcular")
def recalcular(viagem_id: str, ctx: Contexto = Depends(GESTOR), s: Servicos = Srv, db: Session = Db) -> dict:  # noqa: B008
    v = repo.viagem_visivel(db, ctx, viagem_id)
    entrada = LancarViagem(
        veiculo_id=v.veiculo_id,
        motorista_id=v.motorista_id,
        descricao=v.descricao,
        pontos=v.pontos,
        partida_prevista=utc(v.partida_prevista),
        carregado=v.carregado,
    )
    v.resultado = _calcular(db, s, ctx, entrada, dict(v.ajustes))
    return repo.viagem_dict(v)


@router.post("/viagens/{viagem_id}/status")
def mudar_status(viagem_id: str, entrada: MudarStatus, ctx: Contexto = Depends(LANCA), db: Session = Db) -> dict:  # noqa: B008
    v = repo.viagem_visivel(db, ctx, viagem_id)
    v.status = entrada.status
    return repo.viagem_dict(v, resumo=True)


# ---------- Alertas manuais (bloqueios) ----------
@router.get("/alertas")
def listar_alertas(ctx: Contexto = Ctx, db: Session = Db) -> list[dict[str, Any]]:
    q = select(AlertaRota).where(AlertaRota.transportadora_id == ctx.transportadora_id)
    return [
        {
            "id": a.id,
            "tipo": a.tipo,
            "descricao": a.descricao,
            "lat": a.lat,
            "lon": a.lon,
            "raio_km": a.raio_km,
            "inicio": a.inicio.isoformat(),
            "fim": a.fim.isoformat() if a.fim else None,
            "fonte": a.fonte,
        }
        for a in db.scalars(q.order_by(AlertaRota.inicio.desc()).limit(200))
    ]


@router.post("/alertas", status_code=201)
def criar_alerta(entrada: AlertaEntrada, ctx: Contexto = Depends(LANCA), db: Session = Db) -> dict[str, str]:  # noqa: B008
    if entrada.fim and entrada.fim <= entrada.inicio:
        raise EntradaInvalida("O fim deve ser depois do início.")
    dados = entrada.model_dump()
    dados["inicio"], dados["fim"] = utc(entrada.inicio), utc(entrada.fim) if entrada.fim else None
    a = AlertaRota(transportadora_id=ctx.transportadora_id, created_by=ctx.usuario_id, **dados)
    db.add(a)
    db.flush()
    return {"id": a.id}


# ---------- Sensores, posição e tempo real (flag TRANSPORTE_SENSORES_ATIVO) ----------
def _sensor_dict(se: Sensor) -> dict[str, Any]:
    return {
        "id": se.id,
        "nome": se.nome,
        "veiculo_id": se.veiculo_id,
        "fornecedor": se.fornecedor,
        "tipo": se.tipo,
        "ativo": se.ativo,
        "ultimo_sinal_em": se.ultimo_sinal_em.isoformat() if se.ultimo_sinal_em else None,
    }


@router.get("/sensores")
def listar_sensores(ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(sensores_ligados), db: Session = Db) -> list:  # noqa: B008
    q = select(Sensor).where(Sensor.transportadora_id == ctx.transportadora_id).order_by(Sensor.nome)
    return [_sensor_dict(se) for se in db.scalars(q)]


@router.post("/sensores", status_code=201)
def criar_sensor(
    entrada: SensorEntrada,
    ctx: Contexto = Depends(GESTOR),  # noqa: B008
    s: Servicos = Depends(sensores_ligados),  # noqa: B008
    db: Session = Db,
) -> dict[str, Any]:
    repo.obter(db, Veiculo, ctx.transportadora_id, entrada.veiculo_id)
    segredo = s.cofre_ativo().novo_segredo()
    se = Sensor(
        transportadora_id=ctx.transportadora_id,
        segredo_cifrado=s.cofre_ativo().cifrar(segredo),
        created_by=ctx.usuario_id,
        **entrada.model_dump(),
    )
    db.add(se)
    db.flush()
    return {
        **_sensor_dict(se),
        "segredo": segredo,
        "aviso": "Guarde o segredo agora: ele não é exibido de novo.",
        "endpoint": f"/api/telemetria/{se.id}",
    }


@router.delete("/sensores/{sensor_id}")
def desativar_sensor(
    sensor_id: str,
    ctx: Contexto = Depends(GESTOR),  # noqa: B008
    s: Servicos = Depends(sensores_ligados),  # noqa: B008
    db: Session = Db,
) -> dict[str, Any]:
    se = repo.obter(db, Sensor, ctx.transportadora_id, sensor_id)
    se.ativo = False
    return _sensor_dict(se)


@router.get("/viagens/{viagem_id}/posicoes")
def posicoes(
    viagem_id: str,
    ctx: Contexto = Ctx,
    s: Servicos = Depends(sensores_ligados),  # noqa: B008
    db: Session = Db,
) -> list[dict[str, Any]]:
    v = repo.viagem_visivel(db, ctx, viagem_id)
    q = select(LeituraTelemetria).where(LeituraTelemetria.viagem_id == v.id).order_by(LeituraTelemetria.ts.desc())
    nomes = {
        se.id: se.nome for se in db.scalars(select(Sensor).where(Sensor.transportadora_id == ctx.transportadora_id))
    }
    return [ingestao.evento_posicao(v, nomes.get(le.sensor_id, "?"), le) for le in db.scalars(q.limit(200))]


@router.post("/viagens/{viagem_id}/stream-token")
def token_stream(
    viagem_id: str,
    ctx: Contexto = Ctx,
    s: Servicos = Depends(sensores_ligados),  # noqa: B008
    db: Session = Db,
) -> dict[str, str]:
    repo.viagem_visivel(db, ctx, viagem_id)
    return {"token": gerar_token_stream(s.config.chave_stream, viagem_id, ctx.transportadora_id)}


@router.get("/viagens/{viagem_id}/stream")
async def stream(
    viagem_id: str,
    token: str,
    request: Request,
    s: Servicos = Depends(sensores_ligados),  # noqa: B008
) -> StreamingResponse:
    transportadora_id = verificar_token_stream(s.config.chave_stream, viagem_id, token)
    with s.sessoes.nova() as db:
        repo.obter(db, Viagem, transportadora_id, viagem_id)
    fila = s.broker.assinar(viagem_id)

    async def eventos() -> AsyncIterator[str]:
        try:
            yield "retry: 5000\n\n"
            while not await request.is_disconnected():
                try:
                    evento = await asyncio.wait_for(fila.get(), timeout=15)
                    yield f"event: posicao\ndata: {json.dumps(evento, ensure_ascii=False)}\n\n"
                except TimeoutError:
                    yield ": ping\n\n"
        finally:
            s.broker.cancelar(viagem_id, fila)

    return StreamingResponse(
        eventos(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


class SimularSensor(BaseModel):
    sensor_id: str
    leituras: int = Field(default=5, ge=1, le=50)


@router.post("/viagens/{viagem_id}/simular-sensor")
def simular_sensor(
    viagem_id: str,
    entrada: SimularSensor,
    ctx: Contexto = Depends(GESTOR),  # noqa: B008
    s: Servicos = Depends(sensores_ligados),  # noqa: B008
    db: Session = Db,
) -> dict[str, Any]:
    """Gera leituras ao longo da rota e as envia pelo MESMO caminho da API de telemetria (assinatura incluída)."""
    if s.config.ambiente == "producao":
        raise EntradaInvalida("Sensor simulado não é permitido em produção.")
    v = repo.viagem_visivel(db, ctx, viagem_id)
    se = repo.obter(db, Sensor, ctx.transportadora_id, entrada.sensor_id)
    if se.veiculo_id != v.veiculo_id:
        raise EntradaInvalida("O sensor não está no veículo desta viagem.")
    corpo = gerar_leituras_simuladas(v, entrada.leituras, db, se.id)
    ts = str(int(datetime.now(UTC).timestamp()))
    assinatura = assinar(s.cofre_ativo().decifrar(se.segredo_cifrado), ts, corpo)
    return ingestao.receber(db, s.cofre_ativo(), s.broker, s.limitador, se.id, corpo, ts, assinatura)


def gerar_leituras_simuladas(v: Viagem, n: int, db: Session, sensor_id: str) -> bytes:
    geo = [tuple(p) for p in v.resultado["rota"]["geometria"]]
    acc = acumulado_km(geo)  # type: ignore[arg-type]
    feitas = db.scalars(select(LeituraTelemetria).where(LeituraTelemetria.viagem_id == v.id)).all()
    km_ini = len(feitas) * 25.0
    partida = utc(v.partida_prevista)
    vel = v.resultado["rota"]["distancia_km"] / max(v.resultado["rota"]["duracao_direcao_h"], 0.1)
    escala = v.resultado["rota"]["distancia_km"] / acc[-1] if acc[-1] else 1.0
    rng = random.Random(f"{v.id}{len(feitas)}")  # noqa: S311  # nosec B311 — dado de demonstração, não segurança
    leituras = []
    for i in range(n):
        km = min(acc[-1], km_ini + i * 25.0)
        lat, lon = ponto_no_km(geo, km, acc)  # type: ignore[arg-type]
        leituras.append(
            {
                "id": f"sim-{sensor_id[:8]}-{len(feitas) + i}",
                "ts": (partida + timedelta(hours=km * escala / vel)).isoformat(),
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "velocidade_kmh": round(rng.uniform(55, 80), 1),
                "ignicao": True,
                "temperatura_c": round(rng.uniform(3, 6), 1),
                "combustivel_pct": round(max(5.0, 95 - km / acc[-1] * 70), 1) if acc[-1] else None,
            }
        )
    return json.dumps({"leituras": leituras}).encode()
