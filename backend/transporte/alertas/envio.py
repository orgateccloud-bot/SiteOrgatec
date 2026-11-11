"""Mensagens ao motorista: WhatsApp (principal) e SMS (reserva), com teto mensal de gasto e histórico de cada envio.

Decisões de 11/11/2026 (docs/ideias/alertas-rota.md): WhatsApp Cloud API direto da Meta; SMS pela Zenvia só para "Grande perigo"
sem confirmação de entrega do WhatsApp em 15 min; teto de R$ 50/mês para as mensagens. Ao chegar no teto, nada mais é enviado e
o painel mostra o aviso como "bloqueado pelo teto".

- WhatsApp: POST https://graph.facebook.com/<versão>/<id do número>/messages, Authorization: Bearer, mensagem de template
  (fora da janela de 24 h só template aprovado). O id volta em messages[0].id. Versão configurável (a página da Meta cita v27.0).
  https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages
- SMS: POST https://api.zenvia.com/v2/channels/sms/messages, cabeçalho X-API-TOKEN, corpo {from, to, contents:[{type, text}]};
  o id volta em `id`. Especificação: https://zenvia.github.io/zenvia-openapi-spec/v2/
Nenhum dos dois foi testado contra o serviço real nesta entrega (falta conta, número e template aprovado).

LGPD: o telefone só sai do cadastro do motorista na hora do envio; o histórico guarda o número mascarado.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Protocol

from backend.transporte.erros import ErroProvedor
from backend.transporte.provedores.http import ClienteHttp
from backend.transporte.repositorio_transporte import RepositorioBase

log = logging.getLogger(__name__)
SISTEMA = "_sistema"  # registros da ORGATEC que não são de uma transportadora (gasto mensal das mensagens)
ESPERA_SMS = timedelta(minutes=15)
FUSO_TEXTO = timedelta(hours=-3)
ROTULO_TIPO = {"tempestade": "Tempestade", "chuva": "Chuva forte", "vento": "Vento forte", "geada": "Geada", "frio": "Frio intenso",
               "calor": "Calor extremo", "baixa_umidade": "Umidade muito baixa", "fogo": "Fogo e fumaça perto da pista", "outro": "Alerta"}
ROTULO_GRAVIDADE = {"potencial": "atenção", "perigo": "perigo", "grande_perigo": "GRANDE PERIGO"}


class Canal(Protocol):
    nome: str
    custo_brl: Decimal

    def enviar(self, telefone: str, partes: list[str], texto: str) -> str: ...


def _hora(iso: str) -> str:
    return (datetime.fromisoformat(iso) + FUSO_TEXTO).strftime("%d/%m %H:%M")


def partes_mensagem(af: dict[str, Any], descricao_viagem: str) -> list[str]:
    """As 5 variáveis do template: risco, onde, quando, o que fazer, fonte."""
    a = af["alerta"]
    risco = f"{ROTULO_TIPO.get(a['tipo'], 'Alerta')} ({ROTULO_GRAVIDADE.get(a['gravidade'], a['gravidade'])})"
    onde = f"km {af['km_ini']:.0f} a {af['km_fim']:.0f} da viagem {descricao_viagem}"[:120]
    quando = f"você chega lá por volta de {_hora(af['chegada_prevista'])}; vale até {_hora(a['fim'])}"
    acao = (a.get("instrucoes") or "Redobre a atenção e avise a central.")[:200]
    return [risco, onde, quando, acao, a["fonte"][:100]]


def texto_mensagem(partes: list[str]) -> str:
    """Mesmo conteúdo do template, para o SMS e para o histórico. Sem acento: várias operadoras trocam ou cortam acentos."""
    import unicodedata

    t = f"ORGATEC alerta na rota: {partes[0]}. Onde: {partes[1]}. Quando: {partes[2]}. Fonte: {partes[4]}."
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()[:300]


def mascarar(telefone: str) -> str:
    return f"{telefone[:3]} ***** {telefone[-4:]}" if len(telefone) > 7 else "***"


class WhatsAppCloud:
    nome = "whatsapp"

    def __init__(self, cliente: ClienteHttp, token: str, numero_id: str, template: str, versao: str = "v27.0", idioma: str = "pt_BR",
                 custo_brl: Decimal = Decimal("0.05")) -> None:
        self._http, self._token, self._url = cliente, token, f"https://graph.facebook.com/{versao}/{numero_id}/messages"
        self._template, self._idioma, self.custo_brl = template, idioma, custo_brl

    def enviar(self, telefone: str, partes: list[str], texto: str) -> str:
        corpo = {"messaging_product": "whatsapp", "to": telefone.lstrip("+"), "type": "template",
                 "template": {"name": self._template, "language": {"code": self._idioma},
                              "components": [{"type": "body", "parameters": [{"type": "text", "text": p} for p in partes]}]}}
        dados = self._http.requisitar("POST", self._url, json=corpo, headers={"Authorization": f"Bearer {self._token}"})
        try:
            return str(dados["messages"][0]["id"])
        except (KeyError, IndexError, TypeError) as exc:
            raise ErroProvedor("whatsapp", "resposta sem id da mensagem") from exc


class SmsZenvia:
    nome = "sms"
    URL = "https://api.zenvia.com/v2/channels/sms/messages"

    def __init__(self, cliente: ClienteHttp, token: str, remetente: str, custo_brl: Decimal = Decimal("0.10")) -> None:
        self._http, self._token, self._remetente, self.custo_brl = cliente, token, remetente, custo_brl

    def enviar(self, telefone: str, partes: list[str], texto: str) -> str:
        corpo = {"from": self._remetente, "to": telefone.lstrip("+"), "contents": [{"type": "text", "text": texto}]}
        dados = self._http.requisitar("POST", self.URL, json=corpo, headers={"X-API-TOKEN": self._token})
        if not isinstance(dados, dict) or not dados.get("id"):
            raise ErroProvedor("sms", "resposta sem id da mensagem")
        return str(dados["id"])


def id_comunicacao(canal: str, id_provedor: str) -> str:
    """Id do registro a partir do id do provedor: o webhook de status acha o registro sem varrer a coleção."""
    return f"{canal}_{hashlib.sha256(id_provedor.encode()).hexdigest()[:32]}"


@dataclass
class Envio:
    repo: RepositorioBase
    whatsapp: Canal | None
    sms: Canal | None
    teto_brl: Decimal = Decimal("50")

    # ---- teto mensal (todas as transportadoras: o gasto é da ORGATEC) ----
    def gasto_do_mes(self, agora: datetime) -> Decimal:
        try:
            return Decimal(str(self.repo.obter(SISTEMA, "gastos_alertas", agora.strftime("%Y-%m"))["total_brl"]))
        except Exception:  # noqa: BLE001 — sem registro no mês = nada gasto
            return Decimal("0")

    def _somar(self, agora: datetime, valor: Decimal) -> None:
        mes = agora.strftime("%Y-%m")
        self.repo.inserir(SISTEMA, "gastos_alertas", {"total_brl": str(self.gasto_do_mes(agora) + valor), "atualizado_em": agora}, id_=mes)

    # ---- envio ----
    def _registrar(self, tid: str, base: dict[str, Any], estado: str, agora: datetime, canal: str, id_provedor: str = "",
                   detalhe: str = "", custo: Decimal = Decimal("0")) -> dict[str, Any]:
        rid = id_comunicacao(canal, id_provedor) if id_provedor else None
        reg = {**base, "canal": canal, "estado": estado, "enviada_em": agora, "id_provedor": id_provedor, "detalhe": detalhe,
               "custo_brl": str(custo), "historico": [{"estado": estado, "em": agora.isoformat()}]}
        return self.repo.inserir(tid, "comunicacoes", reg, id_=rid)

    def avisar(self, tid: str, motorista: dict[str, Any] | None, af: dict[str, Any], viagem: dict[str, Any], agora: datetime,
               canal_nome: str = "whatsapp", referencia: str = "") -> dict[str, Any]:
        """Tenta avisar o motorista por um canal e registra o resultado, inclusive quando não deu para enviar."""
        partes = partes_mensagem(af, viagem.get("descricao", ""))
        texto = texto_mensagem(partes)
        contato = (motorista or {}).get("contato") or {}
        base = {"viagem_id": viagem["id"], "alerta_rota_id": af["id"], "motorista_id": (motorista or {}).get("id"),
                "destino": mascarar(contato.get("telefone", "")), "gravidade": af["alerta"]["gravidade"], "texto": texto, "referencia": referencia}
        canal = self.whatsapp if canal_nome == "whatsapp" else self.sms
        if canal is None:
            return self._registrar(tid, base, "canal_desligado", agora, canal_nome)
        if motorista is None or not contato.get("telefone") or canal_nome not in (contato.get("canais") or []):
            return self._registrar(tid, base, "sem_consentimento", agora, canal_nome, detalhe="motorista sem telefone ou sem consentimento para o canal")
        if self.gasto_do_mes(agora) + canal.custo_brl > self.teto_brl:
            return self._registrar(tid, base, "bloqueada_teto", agora, canal_nome, detalhe=f"teto mensal de R$ {self.teto_brl} atingido")
        try:
            id_prov = canal.enviar(contato["telefone"], partes, texto)
        except ErroProvedor as exc:
            log.warning("envio falhou: canal=%s %s", canal_nome, type(exc).__name__)  # sem telefone no log
            return self._registrar(tid, base, "falhou", agora, canal_nome, detalhe=exc.estado)
        self._somar(agora, canal.custo_brl)
        return self._registrar(tid, base, "enviada", agora, canal_nome, id_prov, custo=canal.custo_brl)

    def reservas_pendentes(self, tid: str, agora: datetime) -> list[dict[str, Any]]:
        """WhatsApp de "Grande perigo" sem entrega confirmada em 15 min e ainda sem SMS de reserva."""
        coms = self.repo.listar(tid, "comunicacoes")
        com_sms = {c.get("referencia") for c in coms if c["canal"] == "sms"}
        return [c for c in coms if c["canal"] == "whatsapp" and c["gravidade"] == "grande_perigo" and c["id"] not in com_sms
                and c["estado"] in ("enviada", "falhou", "canal_desligado", "bloqueada_teto") and _dt(c["enviada_em"]) <= agora - ESPERA_SMS]


def _dt(v: Any) -> datetime:
    return v if isinstance(v, datetime) else datetime.fromisoformat(str(v))
