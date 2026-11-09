import httpx
import pytest

from transporte.config import Config
from transporte.erros import ProvedorLimiteExcedido, ProvedorRespostaInvalida, ProvedorTimeout
from transporte.provedores.cache import Cache
from transporte.provedores.http import ClienteHttp


def _cliente(handler, tentativas=3):
    esperas = []
    c = ClienteHttp("teste", tentativas=tentativas, transporte=httpx.MockTransport(handler), dormir=esperas.append)
    return c, esperas


def test_sucesso_devolve_json():
    c, _ = _cliente(lambda req: httpx.Response(200, json={"ok": 1}))
    assert c.requisitar("GET", "https://x.test/a") == {"ok": 1}


def test_429_repetido_vira_limite_excedido_com_espera_crescente():
    c, esperas = _cliente(lambda req: httpx.Response(429))
    with pytest.raises(ProvedorLimiteExcedido):
        c.requisitar("GET", "https://x.test/a")
    assert esperas == [0.5, 1.0]


def test_retry_after_e_respeitado():
    respostas = iter([httpx.Response(503, headers={"Retry-After": "2"}), httpx.Response(200, json=[])])
    c, esperas = _cliente(lambda req: next(respostas))
    assert c.requisitar("GET", "https://x.test/a") == []
    assert esperas == [2.0]


def test_timeout_vira_provedor_timeout():
    def h(req):
        raise httpx.ReadTimeout("lento", request=req)

    c, esperas = _cliente(h, tentativas=2)
    with pytest.raises(ProvedorTimeout):
        c.requisitar("GET", "https://x.test/a")
    assert len(esperas) == 1


def test_4xx_nao_repete_e_vira_resposta_invalida():
    chamadas = []

    def h(req):
        chamadas.append(1)
        return httpx.Response(401)

    c, _ = _cliente(h)
    with pytest.raises(ProvedorRespostaInvalida):
        c.requisitar("GET", "https://x.test/a")
    assert len(chamadas) == 1


def test_corpo_nao_json():
    c, _ = _cliente(lambda req: httpx.Response(200, text="<html>"))
    with pytest.raises(ProvedorRespostaInvalida):
        c.requisitar("GET", "https://x.test/a")


def test_cache_expira_e_evita_recalculo():
    agora = [0.0]
    cache = Cache(relogio=lambda: agora[0])
    calls = []

    def calc():
        calls.append(1)
        return "v"

    k = Cache.chave("rota", 1, 2)
    assert cache.obter_ou_calcular(k, 10, calc) == "v"
    assert cache.obter_ou_calcular(k, 10, calc) == "v"
    assert len(calls) == 1
    agora[0] = 11
    cache.obter_ou_calcular(k, 10, calc)
    assert len(calls) == 2


def test_config_recusa_auth_dev_em_producao():
    with pytest.raises(ValueError, match="não é permitido em produção"):
        Config(ambiente="producao", auth_modo="dev")


def test_config_flags_desligadas_por_padrao():
    c = Config(_env_file=None)
    assert not any([c.rota_real, c.clima_real, c.combustivel_real, c.pedagio_real, c.bloqueio_manual, c.sensores_ativo])


def test_config_flag_real_exige_chave():
    with pytest.raises(ValueError, match="ORS_CHAVE"):
        Config(_env_file=None, rota_real=True)
