"""Entrada genérica de telemetria: POST /api/telemetria/{sensor_id}, autenticada por HMAC do próprio sensor.

Cabeçalhos: X-Timestamp (segundos Unix) e X-Assinatura = hex(HMAC-SHA256(segredo, "<timestamp>." + corpo)).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from transporte.api.deps import Servicos, sensores_ligados, sessao
from transporte.telemetria import ingestao

router = APIRouter(prefix="/api/telemetria", tags=["telemetria"])


@router.post("/{sensor_id}")
async def receber(
    sensor_id: str,
    request: Request,
    s: Servicos = Depends(sensores_ligados),  # noqa: B008
    db: Session = Depends(sessao),  # noqa: B008
) -> dict[str, Any]:
    corpo = await request.body()
    return await run_in_threadpool(
        ingestao.receber,
        db,
        s.cofre_ativo(),
        s.broker,
        s.limitador,
        sensor_id,
        corpo,
        request.headers.get("X-Timestamp"),
        request.headers.get("X-Assinatura"),
    )
