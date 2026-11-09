"""Provedores reais. Cada um fica atrás de uma flag desligada por padrão (config.py).

Estado da verificação (09/11/2026) — detalhes no README, seção "Fontes de dados":
- OpenRouteService: endpoints e formato conforme a documentação pública; NÃO testado contra a API real nesta entrega.
- MET Norway Locationforecast 2.0 compact: idem; exige User-Agent identificado (termos de uso).
- ANP e ANTT: leem um CSV NORMALIZADO local. O conversor dos arquivos oficiais para esse formato não está incluído.
"""

from __future__ import annotations

import csv
import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from transporte.db.tabelas import AlertaRota
from transporte.erros import EntradaInvalida, ErroProvedor, ProvedorRespostaInvalida
from transporte.geo import Coord, acumulado_km, distancia_ponto_rota_km, simplificar
from transporte.provedores.base import Bloqueio, PracaPedagio, PrecoCombustivel, PrevisaoClima, RotaCalculada
from transporte.provedores.cache import Cache
from transporte.provedores.http import ClienteHttp

log = logging.getLogger(__name__)


class RotaORS:
    """OpenRouteService, perfil driving-hgv. Plano gratuito: 2.000 rotas/dia e 40/min (openrouteservice.org/plans)."""

    nome = "openrouteservice"

    def __init__(self, cliente: ClienteHttp, url: str, chave: str, cache: Cache, ttl: int) -> None:
        self._http, self._url, self._chave, self._cache, self._ttl = cliente, url.rstrip("/"), chave, cache, ttl

    def geocodificar(self, texto: str, uf: str | None) -> Coord:
        consulta = f"{texto}, {uf}" if uf else texto

        def buscar() -> Coord:
            dados = self._http.requisitar(
                "GET",
                f"{self._url}/geocode/search",
                params={"api_key": self._chave, "text": consulta, "boundary.country": "BR", "size": 1},
            )
            try:
                lon, lat = dados["features"][0]["geometry"]["coordinates"][:2]
            except (KeyError, IndexError, TypeError) as exc:
                raise EntradaInvalida(f"Local não encontrado: {texto}") from exc
            return (float(lat), float(lon))

        return tuple(self._cache.obter_ou_calcular(Cache.chave("geo", consulta), self._ttl, buscar))  # type: ignore[return-value]

    def calcular(self, pontos: list[Coord], eixos: int) -> RotaCalculada:
        def buscar() -> dict[str, Any]:
            dados = self._http.requisitar(
                "POST",
                f"{self._url}/v2/directions/driving-hgv/geojson",
                headers={"Authorization": self._chave},
                json={"coordinates": [[lon, lat] for lat, lon in pontos]},
            )
            try:
                feat = dados["features"][0]
                resumo = feat["properties"]["summary"]
                geometria = [(float(c[1]), float(c[0])) for c in feat["geometry"]["coordinates"]]
                return {"m": float(resumo["distance"]), "s": float(resumo["duration"]), "g": geometria}
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise ProvedorRespostaInvalida(self.nome, "formato de rota inesperado") from exc

        bruto = self._cache.obter_ou_calcular(Cache.chave("rota", pontos, eixos), self._ttl, buscar)
        return RotaCalculada(
            distancia_km=round(bruto["m"] / 1000, 1),
            duracao_h=round(bruto["s"] / 3600, 2),
            geometria=simplificar(bruto["g"], 2000),
            fonte="OpenRouteService (driving-hgv), dados OpenStreetMap — sem trânsito em tempo real",
        )


class ClimaMetNo:
    """MET Norway Locationforecast 2.0 (compact). Gratuito; exige User-Agent identificado e respeito ao cache."""

    nome = "met_norway"

    def __init__(self, cliente: ClienteHttp, url: str, cache: Cache, ttl: int) -> None:
        self._http, self._url, self._cache, self._ttl = cliente, url, cache, ttl

    def previsao(self, lat: float, lon: float, quando: datetime) -> PrevisaoClima | None:
        lat_r, lon_r = round(lat, 2), round(lon, 2)
        dados = self._cache.obter_ou_calcular(
            Cache.chave("metno", lat_r, lon_r),
            self._ttl,
            lambda: self._http.requisitar("GET", self._url, params={"lat": lat_r, "lon": lon_r}),
        )
        try:
            serie = dados["properties"]["timeseries"]
        except (KeyError, TypeError) as exc:
            raise ProvedorRespostaInvalida(self.nome, "sem timeseries") from exc
        if not serie:
            return None
        alvo = quando.astimezone(UTC)

        def distancia(item: dict[str, Any]) -> float:
            return abs((datetime.fromisoformat(item["time"].replace("Z", "+00:00")) - alvo).total_seconds())

        item = min(serie, key=distancia)
        if distancia(item) > 6 * 3600:
            return None  # fora do horizonte da previsão
        dados_item = item.get("data", {})
        instante = dados_item.get("instant", {}).get("details", {})
        prox = dados_item.get("next_1_hours") or dados_item.get("next_6_hours") or {}
        return PrevisaoClima(
            previsto_para=datetime.fromisoformat(item["time"].replace("Z", "+00:00")),
            temperatura_c=instante.get("air_temperature"),
            chuva_mm=prox.get("details", {}).get("precipitation_amount"),
            vento_ms=instante.get("wind_speed"),
            condicao=prox.get("summary", {}).get("symbol_code", "sem dado"),
            fonte="MET Norway (api.met.no), licença CC BY 4.0",
        )


def _ler_csv(caminho: str, provedor: str) -> list[dict[str, str]]:
    arq = Path(caminho)
    if not arq.is_file():
        raise ErroProvedor(provedor, f"arquivo não encontrado: {arq.name}")
    with arq.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


class CombustivelArquivoANP:
    """Lê CSV normalizado (uf;municipio;produto;preco_medio;data_referencia) gerado a partir do levantamento da ANP."""

    nome = "anp_arquivo"
    PRODUTO = "DIESEL S10"

    def __init__(self, caminho: str) -> None:
        self._caminho = caminho
        self._linhas: list[dict[str, str]] | None = None

    def _dados(self) -> list[dict[str, str]]:
        if self._linhas is None:
            self._linhas = [
                r for r in _ler_csv(self._caminho, self.nome) if r.get("produto", "").upper() == self.PRODUTO
            ]
        return self._linhas

    def preco_diesel(self, uf: str | None, municipio: str | None) -> PrecoCombustivel | None:
        linhas = self._dados()
        candidatos = [
            r for r in linhas if uf and r["uf"] == uf and municipio and r["municipio"].upper() == municipio.upper()
        ]
        escopo = f"{municipio}/{uf}"
        if not candidatos and uf:
            candidatos, escopo = [r for r in linhas if r["uf"] == uf], f"média de {uf}"
        if not candidatos:
            return None
        try:
            valores = [Decimal(r["preco_medio"].replace(",", ".")) for r in candidatos]
        except InvalidOperation as exc:
            raise ProvedorRespostaInvalida(self.nome, "preço inválido no CSV") from exc
        media = (sum(valores) / len(valores)).quantize(Decimal("0.001"))
        data = max(r["data_referencia"] for r in candidatos)
        return PrecoCombustivel(media, f"{escopo}, semana de {data}", "ANP — Levantamento de Preços de Combustíveis")


class PedagioArquivoANTT:
    """Lê CSV normalizado (concessionaria;praca;lat;lon;situacao;tarifa_cat1) das praças federais (dados abertos ANTT).

    tarifa_cat1 pode vir vazia: a tarifa por praça não foi confirmada em formato de dados abertos; o serviço de
    despesas usa então o parâmetro da transportadora.
    """

    nome = "antt_arquivo"
    DISTANCIA_MAX_KM = 0.5

    def __init__(self, caminho: str) -> None:
        self._caminho = caminho

    def pracas_na_rota(self, geometria: list[Coord]) -> list[PracaPedagio]:
        acc = acumulado_km(geometria)
        vistas: set[str] = set()
        achadas: list[PracaPedagio] = []
        for r in _ler_csv(self._caminho, self.nome):
            if r.get("situacao", "").strip().lower() not in {"ativa", "ativo", ""}:
                continue
            try:
                lat, lon = float(r["lat"].replace(",", ".")), float(r["lon"].replace(",", "."))
            except (KeyError, ValueError):
                continue
            dist, km = distancia_ponto_rota_km((lat, lon), geometria, acc)
            nome = f"{r.get('praca', '?')} ({r.get('concessionaria', '?')})"
            if dist <= self.DISTANCIA_MAX_KM and nome not in vistas:
                vistas.add(nome)  # evita contar duas vezes a mesma praça (um registro por sentido)
                tarifa = r.get("tarifa_cat1", "").strip()
                achadas.append(
                    PracaPedagio(
                        nome, lat, lon, round(km, 1), Decimal(tarifa.replace(",", ".")) if tarifa else None, "ANTT"
                    )
                )
        return sorted(achadas, key=lambda p: p.km_na_rota)


class BloqueioManual:
    """Bloqueios cadastrados pela transportadora. Não há API aberta de interdições confirmada (DNIT/PRF/ANTT)."""

    nome = "bloqueio_manual"

    def __init__(self, sessao: Session, transportadora_id: str) -> None:
        self._sessao, self._transportadora_id = sessao, transportadora_id

    def na_rota(self, geometria: list[Coord], inicio: datetime, fim: datetime) -> list[Bloqueio]:
        consulta = select(AlertaRota).where(
            AlertaRota.transportadora_id == self._transportadora_id,
            AlertaRota.inicio <= fim,
            or_(AlertaRota.fim.is_(None), AlertaRota.fim >= inicio),
        )
        acc = acumulado_km(geometria)
        saida: list[Bloqueio] = []
        for a in self._sessao.scalars(consulta):
            dist, km = distancia_ponto_rota_km((a.lat, a.lon), geometria, acc)
            if dist <= a.raio_km:
                saida.append(Bloqueio(a.tipo, a.descricao, a.lat, a.lon, round(km, 1), a.fonte, a.inicio, a.fim))
        return sorted(saida, key=lambda b: b.km_na_rota)
