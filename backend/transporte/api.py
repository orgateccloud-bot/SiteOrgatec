"""API da Central de Viagem e do portal do cliente (APIRouter incluído em backend/app.py, atrás da flag ORGATEC_TRANSPORTE=1).

- Desligada por padrão: com a flag off o app nem registra as rotas (404).
- Documentação automática desligada, como no app atual (docs_url=None); o limite por IP e o tratamento de IP do app valem aqui.
- Autenticação: interface `Autenticador`. O modo de desenvolvimento (cabeçalhos X-Transportadora-Id etc.) é RECUSADO em produção,
  e não há login real até a decisão R4: sem autenticador configurado, em produção, tudo responde 403.
- Provedores: só simulados (ver provedores/registro.py). Tempo real: a tela consulta /posicoes a cada 15 s.
- Sem coordenadas em log; só coordenadas (nunca dado pessoal) iriam a APIs estrangeiras quando os provedores reais existirem.
"""

from __future__ import annotations

import json
import logging
import os
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.transporte.dominio import (
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
from backend.transporte.erros import AcessoNegado, EntradaInvalida, ErroTransporte, NaoEncontrado, RecursoDesligado
from backend.transporte.geo import acumulado_km, distancia_ponto_rota_km, ponto_no_km
from backend.transporte.provedores.base import Bloqueio
from backend.transporte.provedores.registro import Provedores, bloqueio_simulado, provedores_do_ambiente
from backend.transporte.repositorio_transporte import RepositorioMemoria
from backend.transporte.servicos import viagem as svc_viagem
from backend.transporte.telemetria import ingestao
from backend.transporte.telemetria.adaptadores import ADAPTADORES
from backend.transporte.telemetria.seguranca import Cofre, assinar

log = logging.getLogger("orgatec.transporte")
Autenticador = Callable[[Request], Contexto]
TRANSPORTADORA_DEMO = "00000000-0000-4000-8000-000000000001"


def ligado(env: dict[str, str] | None = None) -> bool:
    return (env if env is not None else os.environ).get("ORGATEC_TRANSPORTE", "0") == "1"


def autenticador_dev(request: Request) -> Contexto:
    """SOMENTE fora de produção: o contexto vem de cabeçalhos. Em produção, `criar_servicos` recusa este modo."""
    tid = request.headers.get("X-Transportadora-Id")
    papel = request.headers.get("X-Usuario-Papel", "gestor")
    if not tid or papel not in ("gestor", "motorista", "leitura"):
        raise AcessoNegado()
    return Contexto(transportadora_id=tid, usuario_id=request.headers.get("X-Usuario-Id", "dev"), papel=papel)  # type: ignore[arg-type]


def autenticador_recusa_tudo(_request: Request) -> Contexto:
    raise AcessoNegado()


@dataclass
class Servicos:
    repo: RepositorioMemoria
    provedores: Provedores
    autenticador: Autenticador
    cofre: Cofre | None
    producao: bool
    limitador: ingestao.Limitador = field(default_factory=ingestao.Limitador)

    def cofre_ativo(self) -> Cofre:
        if self.cofre is None:
            raise RecursoDesligado("sensores desligados")
        return self.cofre


def criar_servicos(env: dict[str, str] | None = None, autenticador: Autenticador | None = None, repo: RepositorioMemoria | None = None) -> Servicos:
    e = env if env is not None else dict(os.environ)
    producao = e.get("ORGATEC_PRODUCAO", "0") == "1"
    auth_modo = e.get("ORGATEC_TRANSPORTE_AUTH", "dev")
    if autenticador is None:
        if auth_modo == "dev":
            if producao:
                raise RecursoDesligado("ORGATEC_TRANSPORTE_AUTH=dev não é permitido em produção")
            autenticador = autenticador_dev
        else:
            autenticador = autenticador_recusa_tudo  # login real depende da decisão R4
    chave = e.get("ORGATEC_TRANSPORTE_CHAVE", "")
    cofre = Cofre(chave) if e.get("ORGATEC_TRANSPORTE_SENSORES", "0") == "1" else None
    repo = repo or RepositorioMemoria()
    if e.get("ORGATEC_TRANSPORTE_DEMO", "0") == "1" and not producao:
        repo.criar_transportadora(TRANSPORTADORA_DEMO)  # só desenvolvimento: transportadora fictícia para experimentar a tela
    return Servicos(repo, provedores_do_ambiente(e), autenticador, cofre, producao)


def servicos(request: Request) -> Servicos:
    return request.app.state.transporte


def contexto(request: Request, s: Servicos = Depends(servicos)) -> Contexto:  # noqa: B008
    ctx = s.autenticador(request)
    if not s.repo.existe_transportadora(ctx.transportadora_id):
        raise AcessoNegado()
    return ctx


def exigir(*papeis: str) -> Callable[..., Contexto]:
    def verificar(ctx: Contexto = Depends(contexto)) -> Contexto:  # noqa: B008
        if ctx.papel not in papeis:
            raise AcessoNegado()
        return ctx
    return verificar


GESTOR, LANCA = exigir("gestor"), exigir("gestor", "motorista")
router = APIRouter(prefix="/api/transporte", tags=["transporte"])
telemetria = APIRouter(prefix="/api/telemetria", tags=["telemetria"])


def tratar_erro(_request: Request, exc: ErroTransporte) -> JSONResponse:
    if exc.codigo_http >= 500:
        log.error("erro no módulo de transporte: %s", type(exc).__name__)  # sem coordenadas nem dados pessoais no log
    return JSONResponse(status_code=exc.codigo_http, content={"detail": exc.mensagem_publica})


class MudarStatus(BaseModel):
    status: Literal["planejada", "em_andamento", "concluida", "cancelada"]


class SimularSensor(BaseModel):
    sensor_id: str
    leituras: int = 5


class BloqueioDaTransportadora:
    """Bloqueios cadastrados pela transportadora (não há API aberta de interdições confirmada: DNIT, PRF e ANTT)."""

    nome = "bloqueio_manual"

    def __init__(self, repo: RepositorioMemoria, tid: str) -> None:
        self._repo, self._tid = repo, tid

    def na_rota(self, geometria: Any, inicio: datetime, fim: datetime) -> list[Bloqueio]:
        acc = acumulado_km(geometria)
        saida: list[Bloqueio] = []
        for a in self._repo.listar(self._tid, "alertas"):
            if utc(a["inicio"]) > utc(fim) or (a["fim"] and utc(a["fim"]) < utc(inicio)):
                continue
            dist, km = distancia_ponto_rota_km((a["lat"], a["lon"]), geometria, acc)
            if dist <= a["raio_km"]:
                saida.append(Bloqueio(a["tipo"], a["descricao"], a["lat"], a["lon"], round(km, 1), a["fonte"], a["inicio"], a["fim"]))
        return sorted(saida, key=lambda b: b.km_na_rota)


def _veiculo_dict(v: dict[str, Any]) -> dict[str, Any]:
    return {k: (str(v[k]) if k.startswith(("consumo", "tanque")) else v[k]) for k in
            ("id", "placa", "descricao", "eixos", "consumo_km_l_carregado", "consumo_km_l_vazio", "tanque_l")}


def _viagem_dict(v: dict[str, Any], resumo: bool = False) -> dict[str, Any]:
    r = v["resultado"]
    base = {"id": v["id"], "descricao": v["descricao"], "status": v["status"], "partida_prevista": utc(v["partida_prevista"]).isoformat(),
            "veiculo_id": v["veiculo_id"], "motorista_id": v["motorista_id"], "carregado": v["carregado"],
            "origem": r["pontos"][0]["nome"], "destino": r["pontos"][-1]["nome"], "distancia_km": r["rota"]["distancia_km"],
            "chegada_prevista": r["jornada"]["chegada_prevista"], "total_despesas": r["despesas"]["total"], "alertas": len(r["bloqueios"])}
    if not resumo:
        base.update({"resultado": r, "ajustes": v["ajustes"]})
    return base


def _motorista_do_usuario(s: Servicos, ctx: Contexto) -> dict[str, Any] | None:
    return next((m for m in s.repo.listar(ctx.transportadora_id, "motoristas") if m.get("usuario_id") == ctx.usuario_id), None)


def _viagem_visivel(s: Servicos, ctx: Contexto, viagem_id: str) -> dict[str, Any]:
    v = s.repo.obter(ctx.transportadora_id, "viagens", viagem_id)
    if ctx.papel == "motorista":
        m = _motorista_do_usuario(s, ctx)
        if m is None or v["motorista_id"] != m["id"]:
            raise NaoEncontrado()
    return v


def _calcular(s: Servicos, ctx: Contexto, entrada: LancarViagem, ajustes: dict[str, str]) -> dict[str, Any]:
    veiculo = s.repo.obter(ctx.transportadora_id, "veiculos", entrada.veiculo_id)
    params, vigencia = s.repo.parametros(ctx.transportadora_id)
    consumo = veiculo["consumo_km_l_carregado"] if entrada.carregado else veiculo["consumo_km_l_vazio"]
    manual = BloqueioDaTransportadora(s.repo, ctx.transportadora_id)
    return svc_viagem.montar(entrada.pontos, eixos=veiculo["eixos"], consumo_km_l=consumo, partida=entrada.partida_prevista, parametros=params,
                             parametros_vigencia=vigencia, provedores=s.provedores, bloqueios=manual, ajustes=ajustes)


@router.get("/contexto")
def ver_contexto(ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    return {"papel": ctx.papel, "ambiente": "producao" if s.producao else "desenvolvimento",
            "flags": {"provedores_reais": False, "sensores_ativo": s.cofre is not None}}


@router.get("/parametros")
def ver_parametros(ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    p, vigencia = s.repo.parametros(ctx.transportadora_id)
    return {"vigencia": vigencia, "valores": p.model_dump(mode="json"), "meta": PARAMETROS_META}


@router.put("/parametros")
def salvar_parametros(entrada: ParametrosCusto, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    s.repo.salvar_parametros(ctx.transportadora_id, entrada)
    return ver_parametros(ctx, s)


@router.get("/veiculos")
def listar_veiculos(ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> list[dict[str, Any]]:  # noqa: B008
    return [_veiculo_dict(v) for v in s.repo.listar(ctx.transportadora_id, "veiculos")]


@router.post("/veiculos", status_code=201)
def criar_veiculo(entrada: VeiculoEntrada, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    if any(v["placa"] == entrada.placa for v in s.repo.listar(ctx.transportadora_id, "veiculos")):
        raise EntradaInvalida("Já existe um veículo com esta placa.")
    return _veiculo_dict(s.repo.inserir(ctx.transportadora_id, "veiculos", entrada.model_dump()))


@router.get("/motoristas")
def listar_motoristas(ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(servicos)) -> list[dict[str, Any]]:  # noqa: B008
    return [{"id": m["id"], "nome": m["nome"]} for m in s.repo.listar(ctx.transportadora_id, "motoristas")]


@router.post("/motoristas", status_code=201)
def criar_motorista(entrada: MotoristaEntrada, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    m = s.repo.inserir(ctx.transportadora_id, "motoristas", entrada.model_dump())  # LGPD: só nome e vínculo de usuário
    return {"id": m["id"], "nome": m["nome"]}


@router.post("/viagens", status_code=201)
def lancar_viagem(entrada: LancarViagem, ctx: Contexto = Depends(LANCA), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    motorista_id = entrada.motorista_id
    if ctx.papel == "motorista":
        m = _motorista_do_usuario(s, ctx)
        if m is None:
            raise EntradaInvalida("Usuário não está vinculado a um motorista desta transportadora.")
        motorista_id = m["id"]
    elif motorista_id:
        s.repo.obter(ctx.transportadora_id, "motoristas", motorista_id)
    resultado = _calcular(s, ctx, entrada, {})
    v = s.repo.inserir(ctx.transportadora_id, "viagens", {
        "veiculo_id": entrada.veiculo_id, "motorista_id": motorista_id, "status": "planejada",
        "descricao": entrada.descricao or f"{entrada.pontos[0].nome} → {entrada.pontos[-1].nome}",
        "pontos": [p.model_dump() for p in entrada.pontos], "partida_prevista": utc(entrada.partida_prevista),
        "carregado": entrada.carregado, "resultado": resultado, "ajustes": {}, "criado_por": ctx.usuario_id})
    return _viagem_dict(v)


@router.get("/viagens")
def listar_viagens(ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> list[dict[str, Any]]:  # noqa: B008
    todas = s.repo.listar(ctx.transportadora_id, "viagens")
    if ctx.papel == "motorista":
        m = _motorista_do_usuario(s, ctx)
        todas = [v for v in todas if m and v["motorista_id"] == m["id"]]
    todas.sort(key=lambda v: v["partida_prevista"], reverse=True)
    return [_viagem_dict(v, resumo=True) for v in todas[:50]]


@router.get("/viagens/{viagem_id}")
def detalhar(viagem_id: str, ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    return _viagem_dict(_viagem_visivel(s, ctx, viagem_id))


@router.put("/viagens/{viagem_id}/despesas/{tipo}")
def ajustar_despesa(viagem_id: str, tipo: TipoDespesa, entrada: AjusteDespesa, ctx: Contexto = Depends(GESTOR),  # noqa: B008
                    s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    v = _viagem_visivel(s, ctx, viagem_id)
    ajustes = dict(v["ajustes"])
    if entrada.valor is None:
        ajustes.pop(tipo, None)
    else:
        ajustes[tipo] = str(entrada.valor)
    resultado = dict(v["resultado"])
    resultado["despesas"] = svc_viagem.recalcular_despesas(resultado, ajustes)
    return _viagem_dict(s.repo.atualizar(ctx.transportadora_id, "viagens", v["id"], {"resultado": resultado, "ajustes": ajustes}))


@router.post("/viagens/{viagem_id}/recalcular")
def recalcular(viagem_id: str, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    v = _viagem_visivel(s, ctx, viagem_id)
    entrada = LancarViagem(veiculo_id=v["veiculo_id"], motorista_id=v["motorista_id"], descricao=v["descricao"], pontos=v["pontos"],
                           partida_prevista=utc(v["partida_prevista"]), carregado=v["carregado"])
    return _viagem_dict(s.repo.atualizar(ctx.transportadora_id, "viagens", v["id"], {"resultado": _calcular(s, ctx, entrada, dict(v["ajustes"]))}))


@router.post("/viagens/{viagem_id}/status")
def mudar_status(viagem_id: str, entrada: MudarStatus, ctx: Contexto = Depends(LANCA), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    v = _viagem_visivel(s, ctx, viagem_id)
    return _viagem_dict(s.repo.atualizar(ctx.transportadora_id, "viagens", v["id"], {"status": entrada.status}), resumo=True)


@router.get("/alertas")
def listar_alertas(ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> list[dict[str, Any]]:  # noqa: B008
    alertas = sorted(s.repo.listar(ctx.transportadora_id, "alertas"), key=lambda a: a["inicio"], reverse=True)
    return [{**{k: a[k] for k in ("id", "tipo", "descricao", "lat", "lon", "raio_km", "fonte")}, "inicio": utc(a["inicio"]).isoformat(),
             "fim": utc(a["fim"]).isoformat() if a["fim"] else None} for a in alertas[:200]]


@router.post("/alertas", status_code=201)
def criar_alerta(entrada: AlertaEntrada, ctx: Contexto = Depends(LANCA), s: Servicos = Depends(servicos)) -> dict[str, str]:  # noqa: B008
    if entrada.fim and entrada.fim <= entrada.inicio:
        raise EntradaInvalida("O fim deve ser depois do início.")
    dados = entrada.model_dump()
    dados["inicio"], dados["fim"] = utc(entrada.inicio), utc(entrada.fim) if entrada.fim else None
    return {"id": s.repo.inserir(ctx.transportadora_id, "alertas", dados)["id"]}


# ---------- Sensores e posição (flag ORGATEC_TRANSPORTE_SENSORES) ----------
def sensores_ligados(s: Servicos = Depends(servicos)) -> Servicos:  # noqa: B008
    if s.cofre is None:
        raise RecursoDesligado("sensores desligados")
    return s


def _sensor_dict(se: dict[str, Any]) -> dict[str, Any]:
    ult = se.get("ultimo_sinal_em")
    return {"id": se["id"], "nome": se["nome"], "veiculo_id": se["veiculo_id"], "fornecedor": se["fornecedor"], "tipo": se["tipo"], "ativo": se["ativo"],
            "ultimo_sinal_em": utc(ult).isoformat() if ult else None}


@router.get("/sensores")
def listar_sensores(ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(sensores_ligados)) -> list[dict[str, Any]]:  # noqa: B008
    return [_sensor_dict(se) for se in sorted(s.repo.listar(ctx.transportadora_id, "sensores"), key=lambda x: x["nome"])]


@router.post("/sensores", status_code=201)
def criar_sensor(entrada: SensorEntrada, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(sensores_ligados)) -> dict[str, Any]:  # noqa: B008
    s.repo.obter(ctx.transportadora_id, "veiculos", entrada.veiculo_id)
    if entrada.fornecedor not in ADAPTADORES:
        raise EntradaInvalida(f"Fornecedor '{entrada.fornecedor}' sem adaptador registrado.")
    se = s.repo.inserir(ctx.transportadora_id, "sensores", {**entrada.model_dump(), "ativo": True, "versao": 1, "ultimo_sinal_em": None,
                                                           "criado_por": ctx.usuario_id})
    return {**_sensor_dict(se), "segredo": s.cofre_ativo().segredo_do_sensor(se["id"], se["versao"]), "aviso": "Guarde o segredo agora: ele não é exibido de novo.",
            "endpoint": f"/api/telemetria/{se['id']}"}


@router.delete("/sensores/{sensor_id}")
def desativar_sensor(sensor_id: str, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(sensores_ligados)) -> dict[str, Any]:  # noqa: B008
    return _sensor_dict(s.repo.atualizar(ctx.transportadora_id, "sensores", sensor_id, {"ativo": False}))


@router.get("/viagens/{viagem_id}/posicoes")
def posicoes(viagem_id: str, ctx: Contexto = Depends(contexto), s: Servicos = Depends(sensores_ligados)) -> list[dict[str, Any]]:  # noqa: B008
    v = _viagem_visivel(s, ctx, viagem_id)
    nomes = {se["id"]: se["nome"] for se in s.repo.listar(ctx.transportadora_id, "sensores")}
    leituras = sorted((le for le in s.repo.listar(ctx.transportadora_id, "leituras") if le["viagem_id"] == v["id"]), key=lambda le: le["ts"], reverse=True)
    return [ingestao.evento_posicao(v, nomes.get(le["sensor_id"], "?"), le) for le in leituras[:200]]


@router.post("/viagens/{viagem_id}/simular-sensor")
def simular_sensor(viagem_id: str, entrada: SimularSensor, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(sensores_ligados)) -> dict[str, Any]:  # noqa: B008
    """Gera leituras ao longo da rota e as envia pelo MESMO caminho da API de telemetria (assinatura incluída). Recusado em produção."""
    if s.producao:
        raise EntradaInvalida("Sensor simulado não é permitido em produção.")
    v = _viagem_visivel(s, ctx, viagem_id)
    se = s.repo.obter(ctx.transportadora_id, "sensores", entrada.sensor_id)
    if se["veiculo_id"] != v["veiculo_id"]:
        raise EntradaInvalida("O sensor não está no veículo desta viagem.")
    corpo = _leituras_simuladas(s, v, max(1, min(entrada.leituras, 50)), se["id"])
    ts = str(int(datetime.now(UTC).timestamp()))
    assinatura = assinar(s.cofre_ativo().segredo_do_sensor(se["id"], se["versao"]), ts, corpo)
    return ingestao.receber(s.repo, s.cofre_ativo(), s.limitador, se["id"], corpo, ts, assinatura)


def _leituras_simuladas(s: Servicos, v: dict[str, Any], n: int, sensor_id: str) -> bytes:
    geo = [tuple(p) for p in v["resultado"]["rota"]["geometria"]]
    acc = acumulado_km(geo)  # type: ignore[arg-type]
    feitas = [le for le in s.repo.listar(v["transportadora_id"], "leituras") if le["viagem_id"] == v["id"]]
    rota = v["resultado"]["rota"]
    vel = rota["distancia_km"] / max(rota["duracao_direcao_h"], 0.1)
    escala = rota["distancia_km"] / acc[-1] if acc[-1] else 1.0
    rng = random.Random(f"{v['id']}{len(feitas)}")  # noqa: S311  # nosec B311 — dado de demonstração, não segurança
    leituras = []
    for i in range(n):
        km = min(acc[-1], len(feitas) * 25.0 + i * 25.0)
        lat, lon = ponto_no_km(geo, km, acc)  # type: ignore[arg-type]
        leituras.append({"id": f"sim-{sensor_id[:8]}-{len(feitas) + i}", "ts": (utc(v["partida_prevista"]) + timedelta(hours=km * escala / vel)).isoformat(),
                         "lat": round(lat, 5), "lon": round(lon, 5), "velocidade_kmh": round(rng.uniform(55, 80), 1), "ignicao": True,
                         "temperatura_c": round(rng.uniform(3, 6), 1), "combustivel_pct": round(max(5.0, 95 - km / acc[-1] * 70), 1) if acc[-1] else None})
    return json.dumps({"leituras": leituras}).encode()


# ---------- Telemetria (chamada pelo sensor, sem sessão de usuário: a assinatura HMAC é a credencial) ----------
@telemetria.post("/{sensor_id}")
async def receber_leituras(sensor_id: str, request: Request, s: Servicos = Depends(sensores_ligados)) -> dict[str, Any]:  # noqa: B008
    corpo = await request.body()
    return ingestao.receber(s.repo, s.cofre_ativo(), s.limitador, sensor_id, corpo, request.headers.get("X-Timestamp"), request.headers.get("X-Assinatura"))


def instalar(app: Any, env: dict[str, str] | None = None, autenticador: Autenticador | None = None, repo: RepositorioMemoria | None = None,
             limite_ip: Any = None) -> bool:
    """Chamado por backend/app.py. Com a flag desligada não registra nada e devolve False."""
    if not ligado(env):
        return False
    app.state.transporte = criar_servicos(env, autenticador, repo)
    app.add_exception_handler(ErroTransporte, tratar_erro)
    # limite por IP do app (backend/app.py) nas rotas de usuário; a telemetria tem limite próprio por sensor
    app.include_router(router, dependencies=[Depends(limite_ip)] if limite_ip else None)
    app.include_router(telemetria)
    return True
