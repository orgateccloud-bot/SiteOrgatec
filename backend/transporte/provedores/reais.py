"""Provedores reais da Central de Viagem. Cada um só é criado com a flag ORGATEC_TRANSPORTE_<X>_REAL=1 e a configuração exigida
(provedores/registro.py); sem isso o módulo recusa em vez de cair em dado simulado sem aviso.

Fontes (verificadas em 09/11/2026; ver docs/ideias/reestruturacao-transporte-fase5.md, seção "Provedores reais"):
- Rota: OpenRouteService, perfil driving-hgv. Gratuito: 2.000 rotas/dia e 40/min. ATENÇÃO: os termos do plano gratuito são ambíguos
  quanto a uso comercial; confirmar em openrouteservice.org/plans antes de ligar para clientes (alternativa: instância própria,
  basta trocar ORGATEC_TRANSPORTE_ORS_URL).
- Rota alternativa: Google Routes API + Geocoding API (RotaGoogle), licença comercial, sem perfil de caminhão; ORGATEC_TRANSPORTE_ROTA_FONTE=google.
- Clima: MET Norway Locationforecast 2.0 (CC BY 4.0, uso comercial permitido). Exige User-Agent com nome do app e contato.
- Combustível: ANP, "Série histórica de preços de combustíveis" (dados abertos), arquivos mensais precos-diesel-gnv-MM.csv.
- Pedágio: ANTT, dados abertos "Praça de Pedágio" (CC BY): localização das praças. NÃO traz tarifa; o custo usa o parâmetro da transportadora.
Os arquivos da ANP e da ANTT são baixados por tools/transporte_dados_abertos.py para uma pasta local; o provedor só lê o arquivo.
"""

from __future__ import annotations

import csv
import io
import logging
import unicodedata
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from backend.transporte.erros import EntradaInvalida, ErroProvedor, ProvedorRespostaInvalida
from backend.transporte.geo import Coord, acumulado_km, distancia_ponto_rota_km, simplificar
from backend.transporte.provedores.base import PracaPedagio, PrecoCombustivel, PrevisaoClima, RotaCalculada
from backend.transporte.provedores.cache import Cache
from backend.transporte.provedores.http import ClienteHttp

log = logging.getLogger(__name__)


class RotaORS:
    """OpenRouteService, perfil driving-hgv."""

    nome = "openrouteservice"

    def __init__(self, cliente: ClienteHttp, url: str, chave: str, cache: Cache, ttl: int) -> None:
        self._http, self._url, self._chave, self._cache, self._ttl = cliente, url.rstrip("/"), chave, cache, ttl

    def geocodificar(self, texto: str, uf: str | None) -> Coord:
        consulta = f"{texto}, {uf}" if uf else texto

        def buscar() -> Coord:
            dados = self._http.requisitar(
                "GET", f"{self._url}/geocode/search",
                params={"text": consulta, "boundary.country": "BR", "size": 1}, headers={"Authorization": self._chave})
            try:
                lon, lat = dados["features"][0]["geometry"]["coordinates"][:2]
            except (KeyError, IndexError, TypeError) as exc:
                raise EntradaInvalida(f"Local não encontrado: {texto}") from exc
            return (float(lat), float(lon))

        return tuple(self._cache.obter_ou_calcular(Cache.chave("geo", consulta), self._ttl, buscar))  # type: ignore[return-value]

    def calcular(self, pontos: list[Coord], eixos: int) -> RotaCalculada:
        def buscar() -> dict[str, Any]:
            dados = self._http.requisitar(
                "POST", f"{self._url}/v2/directions/driving-hgv/geojson",
                headers={"Authorization": self._chave}, json={"coordinates": [[lon, lat] for lat, lon in pontos]})
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
            fonte="OpenRouteService (driving-hgv), dados OpenStreetMap, sem trânsito em tempo real",
        )


def _decodificar_polilinha(codigo: str) -> list[Coord]:
    """Polilinha codificada do Google (precisão 1e-5)."""
    pontos: list[Coord] = []
    i = lat = lon = 0
    try:
        while i < len(codigo):
            for eixo in (0, 1):
                resultado = deslocamento = 0
                while True:
                    b = ord(codigo[i]) - 63
                    i += 1
                    resultado |= (b & 0x1F) << deslocamento
                    deslocamento += 5
                    if b < 0x20:
                        break
                delta = ~(resultado >> 1) if resultado & 1 else resultado >> 1
                if eixo == 0:
                    lat += delta
                else:
                    lon += delta
            pontos.append((lat / 1e5, lon / 1e5))
    except IndexError as exc:
        raise ValueError("polilinha truncada") from exc
    return pontos


class RotaGoogle:
    """Google Maps Platform: Routes API (computeRoutes, sem trânsito em tempo real) e Geocoding API.
    Licença comercial, cobrança no projeto Google Cloud. Não há perfil de caminhão com peso e dimensões: a rota é de veículo
    pesado só no sentido de `DRIVE`; o texto da fonte avisa. As duas APIs precisam estar ativadas e a chave restrita a elas."""

    nome = "google_routes"

    def __init__(self, cliente: ClienteHttp, chave: str, cache: Cache, ttl: int,
                 url_rotas: str = "https://routes.googleapis.com/directions/v2:computeRoutes",
                 url_geo: str = "https://maps.googleapis.com/maps/api/geocode/json") -> None:
        self._http, self._chave, self._cache, self._ttl, self._url_rotas, self._url_geo = cliente, chave, cache, ttl, url_rotas, url_geo

    def geocodificar(self, texto: str, uf: str | None) -> Coord:
        consulta = f"{texto}, {uf}" if uf else texto

        def buscar() -> Coord:
            dados = self._http.requisitar(
                "GET", self._url_geo, params={"address": consulta, "components": "country:BR", "region": "br", "key": self._chave})
            if isinstance(dados, dict) and dados.get("status") == "ZERO_RESULTS":
                raise EntradaInvalida(f"Local não encontrado: {texto}")
            try:
                loc = dados["results"][0]["geometry"]["location"]
                return (float(loc["lat"]), float(loc["lng"]))
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise ProvedorRespostaInvalida(self.nome, "formato de geocodificação inesperado") from exc

        return tuple(self._cache.obter_ou_calcular(Cache.chave("ggeo", consulta), self._ttl, buscar))  # type: ignore[return-value]

    def calcular(self, pontos: list[Coord], eixos: int) -> RotaCalculada:
        def ponto(c: Coord) -> dict[str, Any]:
            return {"location": {"latLng": {"latitude": c[0], "longitude": c[1]}}}

        def buscar() -> dict[str, Any]:
            corpo: dict[str, Any] = {"origin": ponto(pontos[0]), "destination": ponto(pontos[-1]), "travelMode": "DRIVE",
                                     "routingPreference": "TRAFFIC_UNAWARE", "regionCode": "BR", "languageCode": "pt-BR"}
            if len(pontos) > 2:
                corpo["intermediates"] = [ponto(c) for c in pontos[1:-1]]
            dados = self._http.requisitar(
                "POST", self._url_rotas, json=corpo,
                headers={"X-Goog-Api-Key": self._chave,
                         "X-Goog-FieldMask": "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline"})
            try:
                rota = dados["routes"][0]
                return {"m": float(rota["distanceMeters"]), "s": float(str(rota["duration"]).rstrip("s")),
                        "g": _decodificar_polilinha(rota["polyline"]["encodedPolyline"])}
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise ProvedorRespostaInvalida(self.nome, "formato de rota inesperado") from exc

        bruto = self._cache.obter_ou_calcular(Cache.chave("grota", pontos), self._ttl, buscar)
        return RotaCalculada(
            distancia_km=round(bruto["m"] / 1000, 1),
            duracao_h=round(bruto["s"] / 3600, 2),
            geometria=simplificar([tuple(c) for c in bruto["g"]], 2000),
            fonte="Google Routes API (veículo de passeio, sem restrição de carga nem trânsito em tempo real)",
        )


class ClimaMetNo:
    """MET Norway Locationforecast 2.0 (compact)."""

    nome = "met_norway"

    def __init__(self, cliente: ClienteHttp, url: str, cache: Cache, ttl: int) -> None:
        self._http, self._url, self._cache, self._ttl = cliente, url, cache, ttl

    def previsao(self, lat: float, lon: float, quando: datetime) -> PrevisaoClima | None:
        lat_r, lon_r = round(lat, 2), round(lon, 2)  # o MET pede no máximo 4 casas; 2 casas também reaproveitam o cache
        dados = self._cache.obter_ou_calcular(
            Cache.chave("metno", lat_r, lon_r), self._ttl,
            lambda: self._http.requisitar("GET", self._url, params={"lat": lat_r, "lon": lon_r}))
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
        d = item.get("data", {})
        instante = d.get("instant", {}).get("details", {})
        prox = d.get("next_1_hours") or d.get("next_6_hours") or {}
        return PrevisaoClima(
            previsto_para=datetime.fromisoformat(item["time"].replace("Z", "+00:00")),
            temperatura_c=instante.get("air_temperature"), chuva_mm=prox.get("details", {}).get("precipitation_amount"),
            vento_ms=instante.get("wind_speed"), condicao=prox.get("summary", {}).get("symbol_code", "sem dado"),
            fonte="MET Norway (api.met.no), licença CC BY 4.0")


def _ler_csv(caminho: str, provedor: str) -> list[dict[str, str]]:
    arq = Path(caminho)
    if not arq.is_file():
        raise ErroProvedor(provedor, f"arquivo não encontrado: {arq.name} (rode tools/transporte_dados_abertos.py)")
    bruto = arq.read_bytes()
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = bruto.decode("cp1252", errors="replace")  # o CSV da ANTT vem em Windows-1252
    return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(io.StringIO(texto, newline=""), delimiter=";")]


def _sem_acento(txt: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn").upper().strip()


def _decimal(txt: str, provedor: str) -> Decimal:
    try:
        return Decimal(txt.replace(".", "").replace(",", ".")) if "," in txt else Decimal(txt)
    except InvalidOperation as exc:
        raise ProvedorRespostaInvalida(provedor, "preço inválido no CSV") from exc


class CombustivelANP:
    """Lê o CSV mensal da ANP (colunas 'Estado - Sigla', 'Municipio', 'Produto', 'Data da Coleta', 'Valor de Venda').

    Usa a semana mais recente do arquivo; por município quando houver, senão a média da UF. Aceita 'DIESEL S10' e 'DIESEL'
    (S500), preferindo o S10. Nunca lê nem guarda dados da revenda (nome, CNPJ, endereço).
    """

    nome = "anp_arquivo"

    def __init__(self, caminho: str) -> None:
        self._caminho = caminho
        self._linhas: list[dict[str, str]] | None = None

    def _dados(self) -> list[dict[str, str]]:
        if self._linhas is None:
            self._linhas = [{"uf": r.get("Estado - Sigla", ""), "municipio": r.get("Municipio", ""), "produto": r.get("Produto", "").upper(),
                             "data": r.get("Data da Coleta", ""), "valor": r.get("Valor de Venda", "")}
                            for r in _ler_csv(self._caminho, self.nome) if r.get("Produto", "").upper().startswith("DIESEL")]
        return self._linhas

    @staticmethod
    def _iso(dmy: str) -> str:
        d, m, a = dmy.split("/")
        return f"{a}-{m}-{d}"

    def preco_diesel(self, uf: str | None, municipio: str | None) -> PrecoCombustivel | None:
        linhas = [r for r in self._dados() if r["valor"] and "/" in r["data"]]
        s10 = [r for r in linhas if r["produto"] == "DIESEL S10"]
        linhas = s10 or linhas
        if not linhas or not uf:
            return None
        recente = max(self._iso(r["data"]) for r in linhas)
        limite = datetime.fromisoformat(recente).toordinal() - 7  # a última semana do arquivo
        semana = [r for r in linhas if datetime.fromisoformat(self._iso(r["data"])).toordinal() >= limite]
        escopo = f"{municipio}/{uf}"
        cand = [r for r in semana if r["uf"] == uf and municipio and _sem_acento(r["municipio"]) == _sem_acento(municipio)]
        if not cand:
            cand, escopo = [r for r in semana if r["uf"] == uf], f"média de {uf}"
        if not cand:
            return None
        valores = [_decimal(r["valor"], self.nome) for r in cand]
        media = (sum(valores) / len(valores)).quantize(Decimal("0.001"))
        return PrecoCombustivel(media, f"{escopo}, coleta até {recente}", "ANP, Série histórica de preços de combustíveis (dados abertos)")


class PedagioANTT:
    """Lê o CSV de praças da ANTT (concessionaria;praca_de_pedagio;rodovia;uf;sentido;situacao;latitude;longitude).

    O arquivo não traz tarifa: `tarifa_cat1` fica None e o serviço de despesas usa o parâmetro da transportadora.
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
            if r.get("situacao", "").lower() not in {"ativo", "ativa", ""} or r.get("data_da_inativacao"):
                continue
            try:
                lat, lon = float(r["latitude"].replace(",", ".")), float(r["longitude"].replace(",", "."))
            except (KeyError, ValueError):
                continue
            dist, km = distancia_ponto_rota_km((lat, lon), geometria, acc)
            nome = f"{r.get('praca_de_pedagio', '?')} ({r.get('concessionaria', '?')}, {r.get('rodovia', '?')})"
            if dist <= self.DISTANCIA_MAX_KM and nome not in vistas:
                vistas.add(nome)  # um registro por sentido: a praça conta uma vez
                achadas.append(PracaPedagio(nome, lat, lon, round(km, 1), None, "ANTT, dados abertos (CC BY)"))
        return sorted(achadas, key=lambda p: p.km_na_rota)
