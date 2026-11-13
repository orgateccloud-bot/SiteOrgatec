"""Rotina periódica dos alertas (job agendado a cada 15 min: tools/transporte_alertas.py).

1. Seleciona as viagens em andamento e as planejadas para as próximas 72 h (todas as transportadoras).
2. Busca as fontes uma vez por execução: INMET (Brasil todo, um pedido), FIRMS e INPE (só o retângulo que cobre as rotas).
3. Cruza cada alerta com o trecho que falta de cada viagem e grava em `alertas_rota` (um registro por alerta e viagem).
4. Avisa o motorista quando o alerta chega a "Perigo" ou sobe de gravidade, e manda o SMS de reserva quando cabe.
5. Grava o estado das fontes por transportadora (`alertas_estado/atual`): o painel mostra "fonte indisponível" em vez de silêncio.
6. Grava os resumos públicos (`_sistema/alertas_publicos/atual` e um por estado, publico.py) para o mapa da Janela do Transporte,
   do Brasil inteiro, mesmo sem viagem.

Ligada por ORGATEC_TRANSPORTE_ALERTAS=1. Fontes e canais têm flags próprias (`configurar`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from backend.transporte.alertas import cruzamento as cz
from backend.transporte.alertas import publico
from backend.transporte.alertas.envio import SISTEMA, Envio, SmsZenvia, WhatsAppCloud
from backend.transporte.alertas.fontes import AvisosInmet, FocosFirms, FocosInpe, ResultadoFonte, rank
from backend.transporte.dominio import utc
from backend.transporte.erros import ErroProvedor, RecursoDesligado
from backend.transporte.provedores.http import ClienteHttp
from backend.transporte.repositorio_transporte import RepositorioBase

log = logging.getLogger(__name__)
USER_AGENT = "orgatec.io/1.0 (https://orgatec.io)"
GUARDA_ENCERRADOS = timedelta(days=2)  # alerta encerrado some do painel depois disso (o histórico fica nas comunicações)
PRAZO_COORDENADAS = timedelta(days=29)  # o ponto do alerta sai do traçado do Google: mesmo prazo de 30 dias dos termos do Maps
PRAZO_COMUNICACOES = timedelta(days=180)  # LGPD: depois disso o histórico de envio perde texto e destino (fica só a contagem)


@dataclass
class Configuracao:
    inmet: AvisosInmet | None
    firms: FocosFirms | None
    inpe: FocosInpe | None
    envio: Envio | None
    desligadas: dict[str, str] = field(default_factory=dict)


def ligado(env: dict[str, str]) -> bool:
    return env.get("ORGATEC_TRANSPORTE_ALERTAS", "0") == "1"


def configurar(env: dict[str, str], repo: RepositorioBase, transporte: Any = None) -> Configuracao:
    """Monta fontes e canais a partir do ambiente. Canal ligado sem configuração completa é recusado (nada é enviado às cegas)."""
    def cliente(nome: str) -> ClienteHttp:
        # O servidor do INMET derruba a conexão com o User-Agent padrão do httpx (testado em 11/11/2026); com um identificado, responde.
        return ClienteHttp(nome, timeout=20.0, transporte=transporte, cabecalhos={"User-Agent": USER_AGENT})

    desligadas = {}
    firms_chave = env.get("ORGATEC_TRANSPORTE_FIRMS_CHAVE", "").strip()
    firms = FocosFirms(cliente("nasa_firms"), firms_chave) if firms_chave else None
    if firms is None:
        desligadas["firms"] = "sem chave (ORGATEC_TRANSPORTE_FIRMS_CHAVE)"
    inpe = FocosInpe(cliente("inpe_queimadas")) if env.get("ORGATEC_TRANSPORTE_ALERTAS_INPE", "0") == "1" else None
    if inpe is None:
        desligadas["inpe"] = "desligada até confirmar com o INPE o uso comercial"

    def exigir(var: str, motivo: str) -> str:
        v = env.get(var, "").strip()
        if not v:
            raise RecursoDesligado(f"{motivo} exige {var}")
        return v

    whatsapp = sms = None
    if env.get("ORGATEC_TRANSPORTE_WHATSAPP", "0") == "1":
        whatsapp = WhatsAppCloud(cliente("whatsapp"), exigir("ORGATEC_TRANSPORTE_WHATSAPP_TOKEN", "WhatsApp"),
                                 exigir("ORGATEC_TRANSPORTE_WHATSAPP_NUMERO_ID", "WhatsApp"), exigir("ORGATEC_TRANSPORTE_WHATSAPP_TEMPLATE", "WhatsApp"),
                                 versao=env.get("ORGATEC_TRANSPORTE_WHATSAPP_VERSAO", "v27.0").strip() or "v27.0",
                                 custo_brl=Decimal(env.get("ORGATEC_TRANSPORTE_CUSTO_WHATSAPP_BRL", "0.05")))
    if env.get("ORGATEC_TRANSPORTE_SMS", "0") == "1":
        sms = SmsZenvia(cliente("sms"), exigir("ORGATEC_TRANSPORTE_ZENVIA_TOKEN", "SMS"), exigir("ORGATEC_TRANSPORTE_ZENVIA_REMETENTE", "SMS"),
                        custo_brl=Decimal(env.get("ORGATEC_TRANSPORTE_CUSTO_SMS_BRL", "0.10")))
    envio = Envio(repo, whatsapp, sms, Decimal(env.get("ORGATEC_TRANSPORTE_ALERTAS_TETO_BRL", "50")))
    return Configuracao(AvisosInmet(cliente("inmet")), firms, inpe, envio, desligadas)


def _caixa_total(rotas: list[cz.RotaViagem]) -> tuple[float, float, float, float]:
    """Retângulo das rotas somado à região do mapa público (o FIRMS é pedido uma vez para os dois usos)."""
    cs = [r.caixa for r in rotas] + [publico.REGIAO]
    m = 0.1  # ~10 km de folga
    return (min(c[0] for c in cs) - m, min(c[1] for c in cs) - m, max(c[2] for c in cs) + m, max(c[3] for c in cs) + m)


def _buscar(cfg: Configuracao, rotas: list[cz.RotaViagem], repo: RepositorioBase, agora: datetime) -> dict[str, ResultadoFonte]:
    res: dict[str, ResultadoFonte] = {}
    if cfg.inmet is not None:
        r = res["inmet"] = ResultadoFonte("inmet", "ok", cfg.inmet.credito)
        try:
            r.alertas = cfg.inmet.buscar()
        except ErroProvedor as exc:
            r.estado, r.detalhe = "indisponivel", exc.estado
    caixa = _caixa_total(rotas)
    if cfg.firms is not None:
        r = res["firms"] = ResultadoFonte("firms", "ok", cfg.firms.credito)
        try:
            r.focos = cfg.firms.buscar(caixa)
        except ErroProvedor as exc:
            r.estado, r.detalhe = "indisponivel", exc.estado
    if cfg.inpe is not None:
        r = res["inpe"] = ResultadoFonte("inpe", "ok", cfg.inpe.credito)
        try:
            marca = (repo.listar(SISTEMA, "alertas_marcas") or [{}])[0].get("inpe", "")
            focos, nova = cfg.inpe.buscar(marca)
            r.focos = [f for f in focos if caixa[0] <= f.lat <= caixa[2] and caixa[1] <= f.lon <= caixa[3]]
            repo.inserir(SISTEMA, "alertas_marcas", {"inpe": nova}, id_="atual")
            # os focos do INPE de execuções anteriores ficam nos alertas já gravados (validade de 12 h)
        except ErroProvedor as exc:
            r.estado, r.detalhe = "indisponivel", exc.estado
    for origem, motivo in cfg.desligadas.items():
        res[origem] = ResultadoFonte(origem, "desligada", origem, motivo)
    return res


def executar(repo: RepositorioBase, cfg: Configuracao, agora: datetime | None = None) -> dict[str, Any]:
    agora = utc(agora or datetime.now(UTC))
    rotas: list[cz.RotaViagem] = []
    tids: set[str] = set()
    for tid, v in repo._todas_viagens():  # noqa: SLF001 — rotina de sistema, nunca resposta a usuário
        tids.add(tid)
        if v.get("status") not in ("planejada", "em_andamento"):
            continue
        leituras = repo.leituras_da_viagem(tid, v["id"], 1) if v["status"] == "em_andamento" else []
        rota = cz.preparar(tid, v, leituras[0] if leituras else None, agora)
        if rota is not None:
            rotas.append(rota)
    resumo: dict[str, Any] = {"viagens": len(rotas), "afetacoes": 0, "mensagens": 0, "fontes": {}}
    for tid in tids:
        reter(repo, tid, agora)
    fontes = _buscar(cfg, rotas, repo, agora)
    resumo["fontes"] = {k: r.estado for k, r in fontes.items()}
    publicos = publico.montar(fontes, agora)
    for chave, registro in publicos.items():  # "atual" (nacional) e um por estado
        repo.inserir(SISTEMA, "alertas_publicos", registro, id_=chave)
    resumo["publico"] = {"avisos": len(publicos["atual"]["avisos"]), "focos": publicos["atual"]["focos_total"]}
    if not rotas:
        return resumo
    alertas = [a for r in fontes.values() for a in r.alertas]
    focos = [f for r in fontes.values() for f in r.focos]
    ok = {k for k, r in fontes.items() if r.estado == "ok"}
    estado_fontes = {k: {"estado": r.estado, "credito": r.credito, "detalhe": r.detalhe, "consultado_em": agora.isoformat()}
                     for k, r in fontes.items()}

    por_tid: dict[str, list[cz.RotaViagem]] = {}
    for r in rotas:
        por_tid.setdefault(r.tid, []).append(r)
    for tid, rs in por_tid.items():
        atuais: dict[str, dict[str, Any]] = {}
        for rota in rs:
            afs = [a for a in (cz.cruzar_area(rota, al) for al in alertas) if a] + cz.cruzar_focos(rota, focos, agora)
            for af in afs:
                af["id"] = cz.chave(rota.viagem["id"], af["alerta"]["id"])
                atuais[af["id"]] = af
        resumo["afetacoes"] += len(atuais)
        resumo["mensagens"] += _gravar_e_avisar(repo, cfg.envio, tid, rs, atuais, ok, agora)
        repo.inserir(tid, "alertas_estado", {"fontes": estado_fontes, "atualizado_em": agora.isoformat()}, id_="atual")
    return resumo


def _origens_ok(alerta: dict[str, Any], ok: set[str]) -> bool:
    return all(o in ok for o in alerta["origem"].split("+"))


def _gravar_e_avisar(repo: RepositorioBase, envio: Envio | None, tid: str, rotas: list[cz.RotaViagem], atuais: dict[str, dict[str, Any]],
                     ok: set[str], agora: datetime) -> int:
    viagens = {r.viagem["id"]: r.viagem for r in rotas}
    existentes = {a["id"]: a for a in repo.listar(tid, "alertas_rota")}
    mensagens = 0
    for rid, af in atuais.items():
        antigo = existentes.get(rid)
        reg = {**af, "estado": "ativo", "atualizado_em": agora.isoformat(),
               "criado_em": antigo["criado_em"] if antigo else agora.isoformat(),
               "visto": bool(antigo and antigo.get("visto") and rank(antigo["alerta"]["gravidade"]) >= rank(af["alerta"]["gravidade"])),
               "avisado_gravidade": (antigo or {}).get("avisado_gravidade", "")}
        if envio is not None and af["avisar_motorista"] and rank(af["alerta"]["gravidade"]) > rank(reg["avisado_gravidade"]):
            v = viagens[af["viagem_id"]]
            motorista = _motorista(repo, tid, v.get("motorista_id"))
            com = envio.avisar(tid, motorista, af, v, agora)
            reg["avisado_gravidade"] = af["alerta"]["gravidade"]
            mensagens += com["estado"] == "enviada"
        repo.inserir(tid, "alertas_rota", reg, id_=rid)
    # Alertas que sumiram: só encerra se a fonte respondeu nesta execução (fonte fora do ar não vira "sem risco").
    em_cruzamento = {r.viagem["id"] for r in rotas}
    for rid, antigo in existentes.items():
        if rid in atuais or antigo["estado"] != "ativo":
            if antigo["estado"] != "ativo" and datetime.fromisoformat(antigo["atualizado_em"]) < agora - GUARDA_ENCERRADOS:
                repo.inserir(tid, "alertas_rota", {**antigo, "estado": "arquivado"}, id_=rid)
            continue
        vencido = datetime.fromisoformat(antigo["alerta"]["fim"]) < agora
        if vencido or antigo["viagem_id"] not in em_cruzamento or _origens_ok(antigo["alerta"], ok):
            repo.inserir(tid, "alertas_rota", {**antigo, "estado": "expirado" if vencido else "encerrado", "atualizado_em": agora.isoformat()}, id_=rid)
    if envio is not None:
        for com in envio.reservas_pendentes(tid, agora):
            alerta = existentes.get(com["alerta_rota_id"]) or atuais.get(com["alerta_rota_id"])
            v = viagens.get(com["viagem_id"])
            if not alerta or not v or alerta["id"] not in atuais:
                continue
            res = envio.avisar(tid, _motorista(repo, tid, v.get("motorista_id")), atuais[alerta["id"]], v, agora, "sms", referencia=com["id"])
            mensagens += res["estado"] == "enviada"
    return mensagens


def reter(repo: RepositorioBase, tid: str, agora: datetime) -> None:
    """Prazos de guarda: tira as coordenadas dos alertas com mais de 29 dias e o texto e o destino das comunicações com mais de 180."""
    for a in repo.listar(tid, "alertas_rota"):
        if a.get("lat") is not None and datetime.fromisoformat(a["atualizado_em"]) < agora - PRAZO_COORDENADAS:
            alerta = {**a["alerta"], "pontos": []}
            repo.inserir(tid, "alertas_rota", {**a, "lat": None, "lon": None, "alerta": alerta, "estado": "arquivado"}, id_=a["id"])
    for c in repo.listar(tid, "comunicacoes"):
        enviada = c["enviada_em"] if isinstance(c["enviada_em"], datetime) else datetime.fromisoformat(str(c["enviada_em"]))
        if c.get("texto") and utc(enviada) < agora - PRAZO_COMUNICACOES:
            repo.inserir(tid, "comunicacoes", {**c, "texto": "", "destino": "", "detalhe": "", "anonimizada_em": agora.isoformat()}, id_=c["id"])


def _motorista(repo: RepositorioBase, tid: str, mid: str | None) -> dict[str, Any] | None:
    if not mid:
        return None
    try:
        return repo.obter(tid, "motoristas", mid)
    except Exception:  # noqa: BLE001 — motorista removido: segue sem destinatário (fica registrado como sem consentimento)
        return None
