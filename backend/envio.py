"""Envio do e-mail de confirmação do opt-in (double opt-in do Calendário Fiscal, pendência T2).

O provedor é escolhido por variável de ambiente, sem mudar código:
    ORGATEC_EMAIL            "desligado" (padrão: registra no log e não envia) ou "smtp"
    ORGATEC_SMTP_HOST        servidor SMTP                    (padrão: smtp.gmail.com, o do Google Workspace)
    ORGATEC_SMTP_PORTA       porta com STARTTLS               (padrão: 587)
    ORGATEC_SMTP_USUARIO     conta que autentica              (ex.: contato@orgatec.io)
    ORGATEC_SMTP_SENHA       senha de app da conta (Secret Manager; nunca versionar)
    ORGATEC_EMAIL_REMETENTE  endereço do campo De             (padrão: contato@orgatec.io)
    ORGATEC_SITE_URL         base dos links da mensagem       (padrão: https://orgatec.io)

O domínio orgatec.io já tem SPF, DKIM e DMARC do Google Workspace: enviando pelo SMTP do Workspace, nada muda no DNS.
Com outro provedor, ele precisa entrar no SPF e ter o próprio DKIM.

Toda mensagem leva o link de descadastro no corpo e nos cabeçalhos List-Unsubscribe e List-Unsubscribe-Post
(RFC 8058, cancelamento com um clique): POST /api/optin/sair?token=... já cancela e apaga o contato.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Protocol
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field

log = logging.getLogger("orgatec.envio")

ESFERAS = {"federal": "federal", "trabalhista": "trabalhista", "estadual": "estadual"}


class Mensagem(BaseModel):
    """Contrato de uma mensagem de e-mail (só texto: sem imagem, sem rastreamento de abertura)."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    para: str = Field(min_length=3, max_length=254)
    assunto: str = Field(min_length=1, max_length=200)
    texto: str = Field(min_length=1)
    descadastro: str = Field(pattern=r"^https://")


class Enviador(Protocol):
    def enviar(self, msg: Mensagem) -> None: ...


class EnviadorDesligado:
    """Padrão: nada sai. Fica no log só que houve um pedido, sem o endereço."""

    nome = "desligado"

    def enviar(self, msg: Mensagem) -> None:
        log.warning("envio de e-mail desligado (ORGATEC_EMAIL): a confirmação não foi enviada")


class EnviadorSMTP:
    nome = "smtp"

    def __init__(self, host: str, porta: int, usuario: str, senha: str, remetente: str, tempo_limite: float = 15.0):
        self.host, self.porta, self.usuario, self._senha, self.remetente = host, porta, usuario, senha, remetente
        self.tempo_limite = tempo_limite

    def montar(self, msg: Mensagem) -> EmailMessage:
        m = EmailMessage()
        m["From"] = f"ORGATEC <{self.remetente}>"
        m["To"] = msg.para
        m["Subject"] = msg.assunto
        m["List-Unsubscribe"] = f"<{msg.descadastro}>"
        m["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
        m.set_content(msg.texto)
        return m

    def enviar(self, msg: Mensagem) -> None:
        contexto = ssl.create_default_context()
        with smtplib.SMTP(self.host, self.porta, timeout=self.tempo_limite) as s:
            s.starttls(context=contexto)  # sem TLS, smtplib levanta erro: a senha nunca trafega aberta
            s.login(self.usuario, self._senha)
            s.send_message(self.montar(msg))


def enviador_do_ambiente(producao: bool = False) -> Enviador:
    tipo = os.environ.get("ORGATEC_EMAIL", "desligado").strip().lower()
    if tipo == "desligado":
        return EnviadorDesligado()
    if tipo != "smtp":
        raise RuntimeError(f"ORGATEC_EMAIL inválido: {tipo!r} (use desligado ou smtp)")
    usuario, senha = os.environ.get("ORGATEC_SMTP_USUARIO", ""), os.environ.get("ORGATEC_SMTP_SENHA", "")
    if not usuario or not senha:
        # Falha ao subir, e não no primeiro cadastro: melhor o deploy não passar do que perder confirmações em silêncio.
        raise RuntimeError("ORGATEC_EMAIL=smtp exige ORGATEC_SMTP_USUARIO e ORGATEC_SMTP_SENHA")
    if producao and not os.environ.get("ORGATEC_SITE_URL", "https://orgatec.io").startswith("https://"):
        raise RuntimeError("ORGATEC_SITE_URL precisa ser https em produção")
    return EnviadorSMTP(os.environ.get("ORGATEC_SMTP_HOST", "smtp.gmail.com"), int(os.environ.get("ORGATEC_SMTP_PORTA", "587")),
                        usuario, senha, os.environ.get("ORGATEC_EMAIL_REMETENTE", "contato@orgatec.io"))


def confirmacao_optin(email: str, token: str, token_saida: str, ufs: list[str], esferas: list[str], validade_dias: int,
                      base: str | None = None) -> Mensagem:
    base = (base or os.environ.get("ORGATEC_SITE_URL", "https://orgatec.io")).rstrip("/")
    confirmar = f"{base}/api/optin/confirmar?token={quote(token)}"
    sair = f"{base}/api/optin/sair?token={quote(token_saida)}"
    alertas = ", ".join(ESFERAS.get(e, e) for e in esferas)
    texto = (
        "Olá,\n\n"
        "Recebemos um pedido para enviar a este e-mail os alertas do Calendário Fiscal da ORGATEC "
        f"(obrigações {alertas}; UFs: {', '.join(ufs)}).\n\n"
        "Para confirmar, abra o link abaixo e clique em \"Confirmar inscrição\":\n"
        f"{confirmar}\n\n"
        f"Se não foi você, ignore esta mensagem. Sem a confirmação, o pedido é apagado em até {validade_dias} dias.\n\n"
        "Para cancelar a qualquer momento e apagar seus dados:\n"
        f"{sair}\n\n"
        "ORGATEC Contabilidade\nhttps://orgatec.io/privacidade.html\n"
    )
    return Mensagem(para=email, assunto="Confirme sua inscrição no Calendário Fiscal da ORGATEC", texto=texto, descadastro=sair)
