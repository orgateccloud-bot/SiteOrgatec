"""Previsão do tempo do MET Norway (Locationforecast 2.0, dados CC BY 4.0) para o mapa público da Janela do Transporte.

- `PrevisaoMet.ponto(lat, lon)`: previsão resumida de um ponto, para o balão do mapa. Vai pela API do site (GET
  /api/transporte/previsao), com cache: o navegador do visitante nunca fala direto com o MET, como pedem os termos.
- `temporal_sul(...)`: grade sobre PR, SC e RS com a chuva forte prevista nas próximas 48 h, renovada pela rotina dos alertas
  no máximo a cada 3 h e gravada junto do resumo nacional (`temporal`).

Fora da Escandinávia a série do MET não traz trovoada nem rajada (conferido em 13/11/2026: nenhum símbolo "thunder" em 16 pontos
tropicais, Brasil incluído, num dia de aviso de tempestade do INMET). Por isso o Sul é marcado pela chuva prevista, que vem em
todo o globo: "forte" com 10 mm em 1 h (ou 30 mm em 6 h) e "muito forte" com 20 mm em 1 h (ou 50 mm em 6 h).

Termos (https://api.met.no/doc/TermsOfService, conferidos em 13/11/2026): User-Agent com o site da empresa; coordenadas com no
máximo 4 casas; o mesmo pedido não se repete antes do Expires nem, fora da Escandinávia, antes de 3 h; menos de 20 pedidos/s no
total; crédito "Dados do MET Norway". A previsão é de modelo numérico, não é aviso oficial: o mapa diz isso.
"""

from __future__ import annotations

import json
import math
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.transporte.alertas.cruzamento import dentro
from backend.transporte.erros import ErroProvedor, ProvedorLimiteExcedido
from backend.transporte.provedores.http import ClienteHttp

URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
CREDITO = "Dados do MET Norway (Locationforecast), licença CC BY 4.0"
ARQUIVO_UFS = Path(__file__).resolve().parents[3] / "site" / "assets" / "geo" / "ufs.json"
PASSO_PONTO = 0.1  # ~11 km: quem toca em pontos vizinhos recebe a mesma previsão (e a CDN guarda uma só)
RENOVAR = timedelta(hours=3)  # fora da Escandinávia o MET pede no máximo um pedido igual a cada 3 h
JANELA_TEMPORAL = timedelta(hours=48)
PASSO_SUL = 0.75  # grade do Sul (~83 km): 90 pontos em PR, SC e RS
UFS_SUL = ("PR", "SC", "RS")
LIMITE_PEDIDOS = 600  # por processo, a cada 10 min: a API não vira um proxy livre do MET
JANELA_LIMITE = 600.0
BRT = timedelta(hours=-3)  # horário de Brasília, sem horário de verão desde 2019

# Símbolos do MET (sem o sufixo _day/_night/_polartwilight) em categorias, da mais calma para a mais grave.
CATEGORIAS = ("limpo", "poucas_nuvens", "parcial", "nublado", "neblina", "chuva_fraca", "chuva", "chuva_forte", "neve", "trovoada")
ROTULO = {"limpo": "Céu limpo", "poucas_nuvens": "Poucas nuvens", "parcial": "Parcialmente nublado", "nublado": "Nublado",
          "neblina": "Neblina", "chuva_fraca": "Chuva fraca", "chuva": "Chuva", "chuva_forte": "Chuva forte", "neve": "Neve ou granizo",
          "trovoada": "Trovoada"}


def categoria(simbolo: str | None) -> str:
    s = (simbolo or "").split("_")[0]
    if not s:
        return ""
    if "thunder" in s:
        return "trovoada"
    if "sleet" in s or "snow" in s:
        return "neve"
    if s.startswith("heavyrain"):
        return "chuva_forte"
    if s.startswith("lightrain"):
        return "chuva_fraca"
    if "rain" in s:
        return "chuva"
    return {"clearsky": "limpo", "fair": "poucas_nuvens", "partlycloudy": "parcial", "cloudy": "nublado", "fog": "neblina"}.get(s, "nublado")


def _grau(cat: str) -> int:
    return CATEGORIAS.index(cat) if cat in CATEGORIAS else -1


def _passos(dados: dict[str, Any]) -> list[dict[str, Any]]:
    """Cada passo da série com hora, temperatura, vento (km/h), chuva (mm) e categoria, e quantas horas ele cobre (1 ou 6)."""
    saida = []
    for t in (dados.get("properties") or {}).get("timeseries") or []:
        try:
            quando = datetime.fromisoformat(t["time"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        d = t.get("data") or {}
        inst = (d.get("instant") or {}).get("details") or {}
        prox = d.get("next_1_hours") or d.get("next_6_hours") or {}
        horas = 1 if "next_1_hours" in d else 6
        vento = inst.get("wind_speed")
        saida.append({"quando": quando, "horas": horas, "temp": inst.get("air_temperature"),
                      "vento": None if vento is None else round(vento * 3.6), "chuva": (prox.get("details") or {}).get("precipitation_amount"),
                      "cat": categoria((prox.get("summary") or {}).get("symbol_code"))})
    return saida


def _dia_br(t: datetime) -> str:
    return (t + BRT).date().isoformat()


def resumir(dados: dict[str, Any], agora: datetime, horas: int = 12, dias: int = 5) -> dict[str, Any]:
    """Próximas horas e próximos dias (em horário de Brasília) para o balão do mapa."""
    passos = [p for p in _passos(dados) if p["quando"] >= agora - timedelta(hours=1)]
    proximas = [{"hora": p["quando"].isoformat(), "temp": p["temp"], "vento": p["vento"], "chuva": p["chuva"], "tempo": p["cat"]}
                for p in passos if p["horas"] == 1][:horas]
    por_dia: dict[str, dict[str, Any]] = {}
    for i, p in enumerate(passos):
        # depois das primeiras ~60 h a série passa a vir de 6 em 6 h: cada passo soma só o próprio intervalo, sem contar duas vezes
        if p["horas"] == 6 and i + 1 < len(passos) and passos[i + 1]["horas"] == 1:
            continue
        d = por_dia.setdefault(_dia_br(p["quando"]), {"min": None, "max": None, "chuva": 0.0, "vento_max": None, "tempo": "", "trovoada": False})
        if p["temp"] is not None:
            d["min"] = p["temp"] if d["min"] is None else min(d["min"], p["temp"])
            d["max"] = p["temp"] if d["max"] is None else max(d["max"], p["temp"])
        if p["vento"] is not None:
            d["vento_max"] = p["vento"] if d["vento_max"] is None else max(d["vento_max"], p["vento"])
        d["chuva"] += p["chuva"] or 0.0
        if _grau(p["cat"]) > _grau(d["tempo"]):
            d["tempo"] = p["cat"]
        d["trovoada"] = d["trovoada"] or p["cat"] == "trovoada"
    lista = [{"dia": k, **v, "chuva": round(v["chuva"], 1), "min": _r(v["min"]), "max": _r(v["max"])} for k, v in sorted(por_dia.items())]
    return {"horas": proximas, "dias": lista[:dias], "atualizado_em": ((dados.get("properties") or {}).get("meta") or {}).get("updated_at"),
            "credito": CREDITO, "rotulos": ROTULO}


def _r(v: float | None) -> int | None:
    return None if v is None else round(v)


LIMIARES = {"forte": (10.0, 30.0), "muito_forte": (20.0, 50.0)}  # mm em 1 h e em 6 h


def risco(dados: dict[str, Any], agora: datetime, janela: timedelta = JANELA_TEMPORAL) -> dict[str, Any]:
    """Chuva forte prevista num ponto nas próximas 48 h: nível "muito_forte", "forte" ou "" (nenhuma), a primeira hora em que o
    nível aparece (`inicio`), a maior chuva por hora e o total do período."""
    nivel, inicio, chuva_max, total = "", None, 0.0, 0.0
    for p in _passos(dados):
        if not (agora - timedelta(hours=1) <= p["quando"] < agora + janela):
            continue
        chuva = p["chuva"] or 0.0
        total += chuva
        chuva_max = max(chuva_max, chuva / p["horas"])
        coluna = 0 if p["horas"] == 1 else 1
        n = next((k for k in ("muito_forte", "forte") if chuva >= LIMIARES[k][coluna]), "")
        if n:
            inicio = inicio or p["quando"].isoformat()
            nivel = max(nivel, n, key=_ordem)
    return {"nivel": nivel, "inicio": inicio, "chuva_max": round(chuva_max, 1), "chuva_total": round(total, 1)}


class PrevisaoMet:
    """Pedidos ao MET Norway com cache por ponto arredondado e limite por processo."""

    def __init__(self, cliente: ClienteHttp, relogio: Callable[[], float] = time.time, limite: int = LIMITE_PEDIDOS) -> None:
        self.cliente = cliente
        self._relogio = relogio
        self._limite = limite
        self._cache: dict[tuple[float, float], tuple[float, dict[str, Any]]] = {}
        self._pedidos: list[float] = []
        self._trava = threading.Lock()

    @staticmethod
    def arredondar(lat: float, lon: float, passo: float = PASSO_PONTO) -> tuple[float, float]:
        return round(round(lat / passo) * passo, 4), round(round(lon / passo) * passo, 4)

    def buscar(self, lat: float, lon: float) -> dict[str, Any]:
        """Série completa do MET para o ponto (já arredondado). Usa o cache até o Expires, nunca antes de 3 h."""
        chave = (round(lat, 4), round(lon, 4))
        agora = self._relogio()
        with self._trava:
            guardado = self._cache.get(chave)
            if guardado and guardado[0] > agora:
                return guardado[1]
            self._pedidos = [t for t in self._pedidos if t > agora - JANELA_LIMITE]
            if len(self._pedidos) >= self._limite:
                raise ProvedorLimiteExcedido("met_norway", "limite local de pedidos")
            self._pedidos.append(agora)
        dados, cabecalhos = self.cliente.requisitar_com_cabecalhos("GET", URL, params={"lat": f"{chave[0]:.4f}", "lon": f"{chave[1]:.4f}"})
        expira = agora + RENOVAR.total_seconds()
        try:
            expira = max(expira, parsedate_to_datetime(cabecalhos.get("expires", "")).timestamp())
        except (TypeError, ValueError):
            pass
        with self._trava:
            if len(self._cache) > 5000:  # pontos vencidos saem primeiro; o resto, na ordem de entrada
                self._cache = {k: v for k, v in self._cache.items() if v[0] > agora} or {}
                while len(self._cache) > 4000:
                    self._cache.pop(next(iter(self._cache)))
            self._cache[chave] = (expira, dados)
        return dados

    def ponto(self, lat: float, lon: float, agora: datetime | None = None) -> dict[str, Any]:
        la, lo = self.arredondar(lat, lon)
        return {"lat": la, "lon": lo, **resumir(self.buscar(la, lo), agora or datetime.now(UTC))}


USER_AGENT = "orgatec.io/1.0 (https://orgatec.io)"  # o mesmo da rotina dos alertas: nome do site e endereço para contato


def previsao_met(transporte: Any = None) -> PrevisaoMet:
    """Cliente do MET com espera curta: o balão do mapa não pode ficar pendurado."""
    return PrevisaoMet(ClienteHttp("met_norway", timeout=8.0, tentativas=2, transporte=transporte,
                                   cabecalhos={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}))


@lru_cache(maxsize=1)
def grade_sul(passo: float = PASSO_SUL) -> tuple[tuple[str, float, float], ...]:
    """Centros das células de `passo` graus que caem dentro de PR, SC e RS (limites do IBGE em site/assets/geo/ufs.json)."""
    ufs = {e["uf"]: e for e in json.loads(ARQUIVO_UFS.read_text(encoding="utf-8"))["ufs"] if e["uf"] in UFS_SUL}
    pontos = []
    for uf in UFS_SUL:
        e = ufs[uf]
        aneis = [tuple((p[0], p[1]) for p in anel) for anel in e["aneis"]]
        s, w, n, l = e["caixa"]
        la = math.floor(s / passo) * passo + passo / 2
        while la < n:
            lo = math.floor(w / passo) * passo + passo / 2
            while lo < l:
                if any(dentro((la, lo), anel) for anel in aneis):
                    pontos.append((uf, round(la, 4), round(lo, 4)))
                lo += passo
            la += passo
    return tuple(pontos)


def _ordem(nivel: str) -> int:
    return {"": 0, "forte": 1, "muito_forte": 2}.get(nivel, 0)


def montar_temporal(resultados: list[tuple[str, float, float, dict[str, Any]]], agora: datetime) -> dict[str, Any]:
    pontos, ufs = [], {uf: {"nivel": "", "inicio": None, "pontos": 0} for uf in UFS_SUL}
    for uf, la, lo, r in resultados:
        pontos.append([la, lo, uf, r["nivel"], r["inicio"], r["chuva_total"], r["chuva_max"]])
        u = ufs[uf]
        if r["nivel"]:
            u["pontos"] += 1
            u["nivel"] = max(u["nivel"], r["nivel"], key=_ordem)
            u["inicio"] = min(filter(None, (u["inicio"], r["inicio"])))
    return {"estado": "ok", "atualizado_em": agora.isoformat(), "credito": CREDITO, "passo": PASSO_SUL,
            "janela_h": int(JANELA_TEMPORAL.total_seconds() // 3600), "pontos": pontos, "ufs": ufs}


def temporal_sul(guardado: dict[str, Any] | None, met: PrevisaoMet | None, agora: datetime) -> dict[str, Any] | None:
    """Devolve o resumo do Sul: o guardado enquanto tiver menos de 3 h; depois, um novo (90 pedidos, 4 de cada vez).
    Com o MET fora do ar, mantém o anterior marcado como indisponível (o mapa avisa em vez de mostrar 'sem risco')."""
    if guardado and guardado.get("atualizado_em") and datetime.fromisoformat(guardado["atualizado_em"]) > agora - RENOVAR:
        return guardado
    if met is None:
        return None
    pontos = grade_sul()
    falhou = threading.Event()  # na primeira falha os outros pedidos nem saem: o job não fica minutos esperando um MET fora do ar

    def um(p: tuple[str, float, float]) -> tuple[str, float, float, dict[str, Any]]:
        if falhou.is_set():
            raise ProvedorLimiteExcedido("met_norway", "interrompido após falha")
        try:
            return (*p, risco(met.buscar(p[1], p[2]), agora))
        except ErroProvedor:
            falhou.set()
            raise

    try:
        with ThreadPoolExecutor(max_workers=4) as ex:
            resultados = list(ex.map(um, pontos))
    except ErroProvedor as exc:
        if guardado:
            return {**guardado, "estado": "indisponivel", "detalhe": exc.estado}
        return {"estado": "indisponivel", "detalhe": exc.estado, "atualizado_em": None, "credito": CREDITO, "pontos": [], "ufs": {}}
    return montar_temporal(resultados, agora)
