"""API da Central de Viagem e do portal do cliente (APIRouter incluído em backend/app.py, atrás da flag ORGATEC_TRANSPORTE=1).

- Desligada por padrão: com a flag off o app nem registra as rotas (404).
- Documentação automática desligada, como no app atual (docs_url=None); o limite por IP e o tratamento de IP do app valem aqui.
- Autenticação: interface `Autenticador`. O modo de desenvolvimento (cabeçalhos X-Transportadora-Id etc.) é RECUSADO em produção.
  Login real: ORGATEC_TRANSPORTE_AUTH=firebase (backend/transporte/autenticacao.py). Sem autenticador válido, em produção, tudo responde 403.
- Provedores: simulados por padrão, reais por flag (provedores/registro.py). Tempo real: a tela consulta /posicoes e os lançamentos a cada 15 s.
- Sem coordenadas em log; só coordenadas (nunca dado pessoal) iriam a APIs estrangeiras quando os provedores reais existirem.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import hmac
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from backend.transporte.alertas.envio import SISTEMA, id_comunicacao
from backend.transporte.autenticacao import autenticador_firebase
from backend.transporte.dominio import (
    FONTE_MANUAL,
    PARAMETROS_META,
    AjusteDespesa,
    TERMO_ALERTAS,
    VERSAO_TERMO_ALERTAS,
    AlertaEntrada,
    ContatoMotorista,
    Contexto,
    LancamentoEntrada,
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
from backend.transporte.repositorio_transporte import RepositorioBase, criar_repositorio
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
    repo: RepositorioBase
    provedores: Provedores
    autenticador: Autenticador
    cofre: Cofre | None
    producao: bool
    limitador: ingestao.Limitador = field(default_factory=ingestao.Limitador)
    entrada: dict[str, Any] = field(default_factory=dict)  # o que a tela precisa para entrar (modo e chave web pública)
    traccar: bool = False  # ORGATEC_TRANSPORTE_TRACCAR=1: aceita o app Traccar Client (teste com celular), ver receber_traccar
    mapa: dict[str, str] | None = None  # chave pública do Maps JavaScript API (restrita por domínio no Console) e Map ID opcional
    limite_ip: Callable[[Request], Any] | None = None  # limite por IP do site: só tentativas de acesso NEGADAS gastam dele
    alertas: bool = False  # ORGATEC_TRANSPORTE_ALERTAS=1: alertas de clima e desastres na rota (backend/transporte/alertas)
    whatsapp_webhook: dict[str, str] | None = None  # token de verificação e segredo do app da Meta (status de entrega)
    # Limite por usuário logado (o painel consulta a cada 15 s; o limite por IP do site, feito para formulários, não serve aqui)
    limitador_usuario: ingestao.Limitador = field(default_factory=lambda: ingestao.Limitador(maximo=600, janela_s=60.0))

    def cofre_ativo(self) -> Cofre:
        if self.cofre is None:
            raise RecursoDesligado("sensores desligados")
        return self.cofre


def criar_servicos(env: dict[str, str] | None = None, autenticador: Autenticador | None = None, repo: RepositorioBase | None = None,
                   limite_ip: Callable[[Request], Any] | None = None) -> Servicos:
    e = env if env is not None else dict(os.environ)
    producao = e.get("ORGATEC_PRODUCAO", "0") == "1"
    auth_modo = e.get("ORGATEC_TRANSPORTE_AUTH", "dev")
    if autenticador is None:
        if auth_modo == "dev":
            if producao:
                raise RecursoDesligado("ORGATEC_TRANSPORTE_AUTH=dev não é permitido em produção")
            autenticador = autenticador_dev
        elif auth_modo == "firebase":
            autenticador = autenticador_firebase(e.get("ORGATEC_FIREBASE_PROJETO", "").strip())
        else:
            autenticador = autenticador_recusa_tudo  # "externo" (sem implementação): recusa tudo
    chave = e.get("ORGATEC_TRANSPORTE_CHAVE", "")
    cofre = Cofre(chave) if e.get("ORGATEC_TRANSPORTE_SENSORES", "0") == "1" else None
    repo = repo or criar_repositorio(e)
    if e.get("ORGATEC_TRANSPORTE_DEMO", "0") == "1" and not producao:
        repo.criar_transportadora(TRANSPORTADORA_DEMO)  # só desenvolvimento: transportadora fictícia para experimentar a tela
    chave_web = e.get("ORGATEC_TRANSPORTE_FIREBASE_WEB_KEY", "").strip()
    entrada = {"modo": auth_modo, **({"chave_web": chave_web} if auth_modo == "firebase" and chave_web else {})}
    chave_mapa = e.get("ORGATEC_TRANSPORTE_MAPS_CHAVE_WEB", "").strip()
    mapa = {"provedor": "google", "chave": chave_mapa, **({"map_id": e["ORGATEC_TRANSPORTE_MAPS_ID"].strip()}
                                                          if e.get("ORGATEC_TRANSPORTE_MAPS_ID", "").strip() else {})} if chave_mapa else None
    verificacao = e.get("ORGATEC_TRANSPORTE_WHATSAPP_VERIFICACAO", "").strip()
    segredo_app = e.get("ORGATEC_TRANSPORTE_WHATSAPP_APP_SEGREDO", "").strip()
    return Servicos(repo, provedores_do_ambiente(e), autenticador, cofre, producao, entrada=entrada, limite_ip=limite_ip, mapa=mapa,
                    traccar=e.get("ORGATEC_TRANSPORTE_TRACCAR", "0") == "1", alertas=e.get("ORGATEC_TRANSPORTE_ALERTAS", "0") == "1",
                    whatsapp_webhook={"verificacao": verificacao, "segredo_app": segredo_app} if verificacao and segredo_app else None)


def servicos(request: Request) -> Servicos:
    return request.app.state.transporte


def contexto(request: Request, s: Servicos = Depends(servicos)) -> Contexto:  # noqa: B008
    try:
        ctx = s.autenticador(request)
        if not s.repo.existe_transportadora(ctx.transportadora_id):
            raise AcessoNegado()
    except AcessoNegado:
        if s.limite_ip:
            s.limite_ip(request)  # quem erra o acesso repetidamente leva 429 pelo limite por IP do site
        raise
    s.limitador_usuario.registrar(f"{ctx.transportadora_id}:{ctx.usuario_id}")
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

    def __init__(self, repo: RepositorioBase, tid: str) -> None:
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


@router.get("/entrada")
def como_entrar(s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    """Sem login: a tela pergunta se deve mostrar o painel de desenvolvimento ou o formulário de entrada (a chave web é pública)."""
    return s.entrada


@router.get("/contexto")
def ver_contexto(ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    return {"papel": ctx.papel, "usuario_id": ctx.usuario_id, "ambiente": "producao" if s.producao else "desenvolvimento", "entrada": s.entrada.get("modo"),
            "flags": {"provedores_reais": s.provedores.reais(), "sensores_ativo": s.cofre is not None, "alertas_ativo": s.alertas},
            "mapa": s.mapa}  # só depois do login: a chave é pública, mas não precisa ficar exposta a quem não entrou


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
    return [{"id": m["id"], "nome": m["nome"], "alertas_canais": (m.get("contato") or {}).get("canais", [])}
            for m in s.repo.listar(ctx.transportadora_id, "motoristas")]


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


# ---------- Alertas de clima e desastres na rota (flag ORGATEC_TRANSPORTE_ALERTAS; a rotina agendada grava, a API só lê) ----------
def alertas_ligados(s: Servicos = Depends(servicos)) -> Servicos:  # noqa: B008
    if not s.alertas:
        raise RecursoDesligado("alertas desligados")
    return s


ORDEM_GRAVIDADE = ("potencial", "perigo", "grande_perigo")


def _alerta_rota_dict(a: dict[str, Any]) -> dict[str, Any]:
    al = a["alerta"]
    return {**{k: a.get(k) for k in ("id", "viagem_id", "km_ini", "km_fim", "chegada_prevista", "lat", "lon", "grupo", "posicao_fonte",
                                      "avisar_motorista", "estado", "visto", "avisado_gravidade", "criado_em", "atualizado_em")},
            "alerta": {k: al.get(k) for k in ("id", "origem", "fonte", "tipo", "gravidade", "titulo", "inicio", "fim", "poligonos", "pontos",
                                              "riscos", "instrucoes", "link")}}


@router.get("/alertas-rota")
def listar_alertas_rota(viagem_id: str | None = None, ctx: Contexto = Depends(contexto),  # noqa: B008
                        s: Servicos = Depends(alertas_ligados)) -> dict[str, Any]:  # noqa: B008
    """Alertas ativos e recém-encerrados, com o estado de cada fonte. Com `viagem_id`, só os dessa viagem. O motorista só vê os dele."""
    tid = ctx.transportadora_id
    if viagem_id:
        permitidas: set[str] | None = {_viagem_visivel(s, ctx, viagem_id)["id"]}
    elif ctx.papel == "motorista":
        m = _motorista_do_usuario(s, ctx)
        permitidas = {v["id"] for v in s.repo.listar(tid, "viagens") if m and v["motorista_id"] == m["id"]}
    else:
        permitidas = None
    itens = [a for a in s.repo.listar(tid, "alertas_rota") if a["estado"] != "arquivado" and (permitidas is None or a["viagem_id"] in permitidas)]
    itens.sort(key=lambda a: (a["estado"] != "ativo", -ORDEM_GRAVIDADE.index(a["alerta"]["gravidade"]), a["chegada_prevista"]))
    estado = next(iter(s.repo.listar(tid, "alertas_estado")), None) or {}
    return {"fontes": estado.get("fontes", {}), "atualizado_em": estado.get("atualizado_em"), "alertas": [_alerta_rota_dict(a) for a in itens[:200]]}


@router.post("/alertas-rota/{alerta_id}/visto")
def marcar_alerta_visto(alerta_id: str, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(alertas_ligados)) -> dict[str, Any]:  # noqa: B008
    return _alerta_rota_dict(s.repo.atualizar(ctx.transportadora_id, "alertas_rota", alerta_id, {"visto": True, "visto_por": ctx.usuario_id}))


@router.get("/comunicacoes")
def listar_comunicacoes(viagem_id: str, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(alertas_ligados)) -> list[dict[str, Any]]:  # noqa: B008
    v = _viagem_visivel(s, ctx, viagem_id)
    coms = [c for c in s.repo.listar(ctx.transportadora_id, "comunicacoes") if c["viagem_id"] == v["id"]]
    coms.sort(key=lambda c: utc(c["enviada_em"]), reverse=True)
    return [{**{k: c.get(k) for k in ("id", "alerta_rota_id", "canal", "estado", "destino", "gravidade", "texto", "detalhe", "historico")},
             "enviada_em": utc(c["enviada_em"]).isoformat()} for c in coms[:100]]


@router.get("/alertas-publicos")
def alertas_publicos(s: Servicos = Depends(alertas_ligados)) -> JSONResponse:  # noqa: B008
    """Sem login: o mapa público da Janela do Transporte. Só avisos do INMET, focos do FIRMS e o resumo por rodovia
    (backend/transporte/alertas/publico.py); nenhuma viagem, posição ou dado de transportadora. Cache de 5 min na CDN."""
    reg = (s.repo.listar(SISTEMA, "alertas_publicos") or [None])[0]
    corpo = {k: v for k, v in reg.items() if k not in ("id", "transportadora_id")} if reg else {"atualizado_em": None, "avisos": [], "focos": [], "rodovias": [], "fontes": {}}
    return JSONResponse(corpo, headers={"Cache-Control": "public, max-age=60, s-maxage=300"})


@router.get("/alertas-termo")
def termo_alertas(_ctx: Contexto = Depends(GESTOR), _s: Servicos = Depends(alertas_ligados)) -> dict[str, str]:  # noqa: B008
    return {"versao": VERSAO_TERMO_ALERTAS, "texto": TERMO_ALERTAS}


@router.put("/motoristas/{motorista_id}/contato")
def salvar_contato(motorista_id: str, entrada: ContatoMotorista, ctx: Contexto = Depends(GESTOR),  # noqa: B008
                   s: Servicos = Depends(alertas_ligados)) -> dict[str, Any]:  # noqa: B008
    """Telefone e canais dos alertas, com o registro do consentimento (quem registrou, quando e qual texto). LGPD: só isso."""
    contato = {"telefone": entrada.telefone, "canais": sorted(set(entrada.canais)), "versao_termo": entrada.versao_termo,
               "consentimento_em": datetime.now(UTC).isoformat(), "registrado_por": ctx.usuario_id}
    m = s.repo.atualizar(ctx.transportadora_id, "motoristas", motorista_id, {"contato": contato})
    return {"id": m["id"], "nome": m["nome"], "alertas_canais": contato["canais"]}


@router.delete("/motoristas/{motorista_id}/contato")
def remover_contato(motorista_id: str, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(alertas_ligados)) -> dict[str, Any]:  # noqa: B008
    """Revogação: o telefone sai do cadastro na hora e nenhuma mensagem nova é enviada."""
    m = s.repo.atualizar(ctx.transportadora_id, "motoristas", motorista_id,
                         {"contato": None, "contato_revogado_em": datetime.now(UTC).isoformat(), "contato_revogado_por": ctx.usuario_id})
    return {"id": m["id"], "nome": m["nome"], "alertas_canais": []}


ESTADO_WHATSAPP = {"sent": "enviada", "delivered": "entregue", "read": "lida", "failed": "falhou"}
ORDEM_ENTREGA = ("enviada", "entregue", "lida")


@router.get("/whatsapp/webhook")
def verificar_webhook(request: Request, s: Servicos = Depends(alertas_ligados)) -> PlainTextResponse:  # noqa: B008
    """Verificação da Meta: devolve hub.challenge quando o token confere."""
    cfg, q = s.whatsapp_webhook, request.query_params
    if not cfg or q.get("hub.mode") != "subscribe" or not hmac.compare_digest(q.get("hub.verify_token", "").encode(), cfg["verificacao"].encode()):
        raise AcessoNegado()
    return PlainTextResponse(q.get("hub.challenge", ""))


@router.post("/whatsapp/webhook")
async def receber_webhook(request: Request, s: Servicos = Depends(alertas_ligados)) -> dict[str, int]:  # noqa: B008
    """Status de entrega do WhatsApp. Assinatura X-Hub-Signature-256 = "sha256=" + HMAC-SHA256 do corpo com o segredo do app."""
    cfg = s.whatsapp_webhook
    corpo = await request.body()
    if not cfg or len(corpo) > ingestao.TAMANHO_MAX_CORPO:
        raise AcessoNegado()
    esperado = "sha256=" + hmac.new(cfg["segredo_app"].encode(), corpo, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(request.headers.get("X-Hub-Signature-256", "").encode(), esperado.encode()):
        raise AcessoNegado()
    try:
        dados = json.loads(corpo)
        status = [st for en in dados.get("entry", []) for ch in en.get("changes", []) for st in (ch.get("value") or {}).get("statuses", [])]
    except (ValueError, AttributeError, TypeError) as exc:
        raise EntradaInvalida("Corpo inesperado.") from exc
    atualizados = 0
    for st in status:
        recebido = ESTADO_WHATSAPP.get(str(st.get("status")))
        com = s.repo.comunicacao_global(id_comunicacao("whatsapp", str(st.get("id", ""))))
        if not recebido or com is None:
            continue
        novo = recebido
        if novo in ORDEM_ENTREGA and com["estado"] in ORDEM_ENTREGA and ORDEM_ENTREGA.index(novo) < ORDEM_ENTREGA.index(com["estado"]):
            novo = com["estado"]  # os avisos chegam fora de ordem: "lida" não volta para "entregue"
        em = datetime.fromtimestamp(int(st.get("timestamp") or time.time()), UTC).isoformat()
        detalhe = "; ".join(str(e.get("title", "")) for e in st.get("errors", []) if isinstance(e, dict))[:200]
        s.repo.atualizar(com["transportadora_id"], "comunicacoes", com["id"],
                         {"estado": novo, "historico": [*com.get("historico", []), {"estado": recebido, "em": em}], **({"detalhe": detalhe} if detalhe else {})})
        atualizados += 1
    return {"atualizados": atualizados}


# ---------- Lançamentos manuais da viagem (abastecimento, pedágio pago, parada, ocorrência, posição informada) ----------
def _lancamento_dict(r: dict[str, Any]) -> dict[str, Any]:
    return {**{k: r.get(k) for k in ("id", "tipo", "local", "lat", "lon", "observacao", "autor_id", "fonte")},
            **{k: (str(r[k]) if r.get(k) is not None else None) for k in ("valor", "litros", "preco_l")},
            "ts": utc(r["ts"]).isoformat(), "criado_em": utc(r["criado_em"]).isoformat()}


@router.get("/viagens/{viagem_id}/lancamentos")
def listar_lancamentos(viagem_id: str, ctx: Contexto = Depends(contexto), s: Servicos = Depends(servicos)) -> list[dict[str, Any]]:  # noqa: B008
    v = _viagem_visivel(s, ctx, viagem_id)
    regs = [r for r in s.repo.listar(ctx.transportadora_id, "lancamentos") if r["viagem_id"] == v["id"] and not r.get("removido")]
    return [_lancamento_dict(r) for r in sorted(regs, key=lambda r: utc(r["ts"]), reverse=True)[:300]]


@router.post("/viagens/{viagem_id}/lancamentos", status_code=201)
def criar_lancamento(viagem_id: str, entrada: LancamentoEntrada, ctx: Contexto = Depends(LANCA),  # noqa: B008
                     s: Servicos = Depends(servicos)) -> dict[str, Any]:  # noqa: B008
    v = _viagem_visivel(s, ctx, viagem_id)
    agora = datetime.now(UTC)
    if utc(entrada.ts) > agora + timedelta(minutes=10):
        raise EntradaInvalida("O lançamento não pode ter data no futuro.")
    dados = {**entrada.model_dump(), "ts": utc(entrada.ts), "viagem_id": v["id"], "autor_id": ctx.usuario_id, "fonte": FONTE_MANUAL,
             "criado_em": agora, "removido": False}
    return _lancamento_dict(s.repo.inserir(ctx.transportadora_id, "lancamentos", dados))


@router.delete("/viagens/{viagem_id}/lancamentos/{lancamento_id}")
def remover_lancamento(viagem_id: str, lancamento_id: str, ctx: Contexto = Depends(LANCA),  # noqa: B008
                       s: Servicos = Depends(servicos)) -> dict[str, str]:  # noqa: B008
    """Remoção lógica (fica registrado quem removeu). O motorista só remove o que ele mesmo lançou."""
    v = _viagem_visivel(s, ctx, viagem_id)
    r = s.repo.obter(ctx.transportadora_id, "lancamentos", lancamento_id)
    if r["viagem_id"] != v["id"] or r.get("removido"):
        raise NaoEncontrado()
    if ctx.papel != "gestor" and r["autor_id"] != ctx.usuario_id:
        raise AcessoNegado()
    s.repo.atualizar(ctx.transportadora_id, "lancamentos", r["id"], {"removido": True, "removido_por": ctx.usuario_id,
                                                                     "removido_em": datetime.now(UTC)})
    return {"id": r["id"]}


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
    segredo = s.cofre_ativo().segredo_do_sensor(se["id"], se["versao"])
    if entrada.fornecedor == "traccar_client":
        return {**_sensor_dict(se), "segredo": segredo, "endpoint": f"/api/telemetria/{se['id']}/traccar",
                "aviso": "No app Traccar Client: endereço do servidor = https://orgatec.io + endpoint; identificador do dispositivo = segredo. "
                         "Guarde o segredo agora: ele não é exibido de novo."}
    return {**_sensor_dict(se), "segredo": segredo, "aviso": "Guarde o segredo agora: ele não é exibido de novo.",
            "endpoint": f"/api/telemetria/{se['id']}"}


@router.delete("/sensores/{sensor_id}")
def desativar_sensor(sensor_id: str, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(sensores_ligados)) -> dict[str, Any]:  # noqa: B008
    return _sensor_dict(s.repo.atualizar(ctx.transportadora_id, "sensores", sensor_id, {"ativo": False}))


@router.get("/viagens/{viagem_id}/posicoes")
def posicoes(viagem_id: str, ctx: Contexto = Depends(contexto), s: Servicos = Depends(sensores_ligados)) -> list[dict[str, Any]]:  # noqa: B008
    v = _viagem_visivel(s, ctx, viagem_id)
    nomes = {se["id"]: se["nome"] for se in s.repo.listar(ctx.transportadora_id, "sensores")}
    leituras = s.repo.leituras_da_viagem(ctx.transportadora_id, v["id"], 200)  # indexada: não lê as leituras das outras viagens
    if not v["resultado"]["rota"]["geometria"]:  # traçado apagado após 30 dias (termos do Google): sem km nem desvio
        return [{"tipo": "posicao", "viagem_id": v["id"], "status": v["status"], "sensor": nomes.get(le["sensor_id"], "?"),
                 "ts": utc(le["ts"]).isoformat(), "lat": le["lat"], "lon": le["lon"], "velocidade_kmh": le.get("velocidade_kmh"),
                 "km_percorrido": None, "desvio_km": None, "fora_da_rota": False} for le in leituras]
    rota = ingestao.preparar_rota(v)
    return [ingestao.evento_posicao(v, nomes.get(le["sensor_id"], "?"), le, rota) for le in leituras]


@router.post("/viagens/{viagem_id}/simular-sensor")
def simular_sensor(viagem_id: str, entrada: SimularSensor, ctx: Contexto = Depends(GESTOR), s: Servicos = Depends(sensores_ligados)) -> dict[str, Any]:  # noqa: B008
    """Gera leituras ao longo da rota e as envia pelo MESMO caminho da API de telemetria (assinatura incluída). Recusado em produção."""
    if s.producao:
        raise EntradaInvalida("Sensor simulado não é permitido em produção.")
    v = _viagem_visivel(s, ctx, viagem_id)
    if not v["resultado"]["rota"]["geometria"]:
        raise EntradaInvalida("Recalcule a viagem: o traçado foi apagado após 30 dias.")
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


@telemetria.api_route("/{sensor_id}/traccar", methods=["GET", "POST"])
async def receber_traccar(sensor_id: str, request: Request, s: Servicos = Depends(sensores_ligados)) -> dict[str, Any]:  # noqa: B008
    """App Traccar Client (celular como rastreador, para teste). O app não sabe assinar: o identificador do dispositivo
    configurado nele é o segredo do sensor, conferido aqui; depois a leitura segue pelo mesmo caminho assinado dos
    outros sensores. Só para sensores com fornecedor traccar_client e com ORGATEC_TRANSPORTE_TRACCAR=1."""
    if not s.traccar:
        raise RecursoDesligado("Traccar Client desligado")
    corpo = await request.body()
    if len(corpo) > ingestao.TAMANHO_MAX_CORPO:
        raise EntradaInvalida("Corpo acima de 256 KB.")
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            dados = json.loads(corpo)
        except ValueError as exc:
            raise EntradaInvalida("Corpo não é JSON válido.") from exc
        if not isinstance(dados, dict):
            raise EntradaInvalida("Corpo deve ser um objeto JSON.")
    else:  # protocolo OsmAnd por parâmetros: na URL ou no corpo (formulário)
        dados = dict(request.query_params)
        dados.update({k: v[-1] for k, v in parse_qs(corpo.decode("utf-8", "replace")).items()})
    sensor = s.repo.sensor_global(sensor_id)
    if sensor is None or not sensor["ativo"] or sensor["fornecedor"] != "traccar_client":
        raise AcessoNegado()
    segredo = s.cofre_ativo().segredo_do_sensor(sensor["id"], sensor["versao"])
    identificador = str(dados.pop("device_id", None) or dados.pop("id", None) or dados.pop("deviceid", None) or "")
    if not hmac.compare_digest(identificador.encode(), segredo.encode()):
        raise AcessoNegado()
    normalizado = json.dumps(dados).encode()  # sem o identificador: o segredo não segue adiante
    ts = str(int(time.time()))
    return ingestao.receber(s.repo, s.cofre_ativo(), s.limitador, sensor["id"], normalizado, ts, assinar(segredo, ts, normalizado))


def instalar(app: Any, env: dict[str, str] | None = None, autenticador: Autenticador | None = None, repo: RepositorioBase | None = None,
             limite_ip: Any = None) -> bool:
    """Chamado por backend/app.py. Com a flag desligada não registra nada e devolve False."""
    if not ligado(env):
        return False
    app.state.transporte = criar_servicos(env, autenticador, repo, limite_ip)
    app.add_exception_handler(ErroTransporte, tratar_erro)
    # usuários: limite por usuário logado + limite por IP do app só para acessos negados; telemetria: limite próprio por sensor
    app.include_router(router)
    app.include_router(telemetria)
    return True
