"""O crédito do OrgCred entra em Gestão financeira sem virar oferta (decisão D5 do plano de incorporação)."""

import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[2] / "site"


def _cartao_gestao(html: str) -> str:
    inicio = html.index("Gestão financeira")
    return html[inicio : html.index("</div>", inicio)]


@pytest.mark.parametrize("pagina", ["solucoes/index.html", "cliente/index.html"])
def test_cartao_avisa_que_nao_ha_oferta_de_credito(pagina):
    cartao = _cartao_gestao((SITE / pagina).read_text(encoding="utf-8"))
    assert "ainda não há oferta de crédito" in cartao
    # Condição de crédito no cartão seria publicidade antes de operar.
    assert not re.search(r"\d\s*%|taxa|juros|parcela|R\$", cartao, re.IGNORECASE)


def test_gestao_financeira_segue_em_breve_e_sem_endereco():
    config = (SITE / "assets/js/config.js").read_text(encoding="utf-8")
    assert "gestaoFinanceira: { situacao: 'em_breve', url: null }" in config
