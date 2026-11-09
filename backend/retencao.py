"""Prazos de guarda dos formulários (LGPD, arts. 15 e 16). Valores da política de privacidade, seção 5.

Pendência V6: os prazos ainda são proposta. Quando aprovados de outro jeito, troque aqui ou nas variáveis
ORGATEC_RETENCAO_* (em dias). Opt-in confirmado não tem prazo: vale até o titular se descadastrar.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Prazos:
    lead_dias: int = 730  # 24 meses
    contato_dias: int = 730
    optin_pendente_dias: int = 30  # também é a validade do link de confirmação
    telemetria_dias: int = 30  # leituras de sensores da Central de Viagem (proposta; ver docs/lgpd/transporte-monitoramento.md)

    def dias(self, tipo: str, status: str) -> int | None:
        """Prazo em dias de um registro; None = sem prazo automático."""
        if tipo == "lead":
            return self.lead_dias
        if tipo == "contato":
            return self.contato_dias
        if tipo == "optin" and status == "pendente_confirmacao":
            return self.optin_pendente_dias
        return None


def prazos_do_ambiente() -> Prazos:
    def dias(nome: str, padrao: int) -> int:
        valor = int(os.environ.get(nome, padrao))
        if valor < 1:
            raise RuntimeError(f"{nome} precisa ser de pelo menos 1 dia")
        return valor

    return Prazos(
        lead_dias=dias("ORGATEC_RETENCAO_LEAD_DIAS", Prazos.lead_dias),
        contato_dias=dias("ORGATEC_RETENCAO_CONTATO_DIAS", Prazos.contato_dias),
        optin_pendente_dias=dias("ORGATEC_RETENCAO_OPTIN_PENDENTE_DIAS", Prazos.optin_pendente_dias),
        telemetria_dias=dias("ORGATEC_RETENCAO_TELEMETRIA_DIAS", Prazos.telemetria_dias),
    )
