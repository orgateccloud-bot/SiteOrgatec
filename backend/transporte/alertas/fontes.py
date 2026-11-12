"""Fontes públicas de alerta (conferidas em 11/11/2026; detalhes e links em docs/ideias/alertas-rota.md).

- INMET, avisos meteorológicos: https://apiprevmet3.inmet.gov.br/avisos/ativos (JSON sem token, com polígono GeoJSON da área).
  Cobre tempestade, chuva, vendaval, granizo, geada, onda de calor e baixa umidade. Licença e limite de uso: não verificados.
- NASA FIRMS, focos de fogo (VIIRS): https://firms.modaps.eosdis.nasa.gov/api/area/ (chave gratuita, 5.000 transações a cada
  10 min). Dados CC0; crédito "NASA FIRMS"; proibido sugerir endosso da NASA.
- INPE Queimadas, focos a cada 10 min: https://data.inpe.br/queimadas/dados-abertos/ (CSV aberto). Pede citação. O uso comercial
  não está explícito: fica desligado (ORGATEC_TRANSPORTE_ALERTAS_INPE) até a confirmação com o INPE.
Nenhuma fonte recebe dado pessoal: o INMET é consultado sem parâmetro e as outras só recebem um retângulo de coordenadas.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from backend.transporte.erros import ProvedorRespostaInvalida
from backend.transporte.geo import Coord
from backend.transporte.provedores.http import ClienteHttp

log = logging.getLogger(__name__)
BRASILIA = timezone(timedelta(hours=-3))

INMET_URL = "https://apiprevmet3.inmet.gov.br/avisos/ativos"
INMET_LINK = "https://avisos.inmet.gov.br/{id}"
INMET_CREDITO = "INMET, avisos meteorológicos (apiprevmet3.inmet.gov.br)"
FIRMS_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{chave}/{fonte}/{w:.3f},{s:.3f},{e:.3f},{n:.3f}/1"
# O Suomi NPP parou de transmitir em 02/11/2026 (aviso do FIRMS): só NOAA-20 e NOAA-21.
FIRMS_FONTES = ("VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT")
FIRMS_CREDITO = "NASA FIRMS (focos de fogo VIIRS, dados CC0)"
INPE_URL = "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/10min/"
INPE_CREDITO = "INPE, Programa Queimadas (focos a cada 10 min)"

GRAVIDADES = ("potencial", "perigo", "grande_perigo")
_SEVERIDADE_INMET = {"perigo potencial": "potencial", "perigo": "perigo", "grande perigo": "grande_perigo"}
# Ordem importa: o primeiro termo encontrado na descrição do aviso define o tipo.
_TIPO_INMET = (("tempestade", "tempestade"), ("granizo", "tempestade"), ("chuva", "chuva"), ("vendaval", "vento"), ("vento", "vento"),
               ("geada", "geada"), ("declínio de temperatura", "frio"), ("onda de frio", "frio"), ("calor", "calor"),
               ("umidade", "baixa_umidade"), ("neve", "frio"))


def rank(gravidade: str) -> int:
    return GRAVIDADES.index(gravidade) if gravidade in GRAVIDADES else -1


@dataclass(frozen=True)
class AlertaExterno:
    """Aviso de uma fonte, já normalizado. `poligonos` (lat, lon) para área; `pontos` para focos de fogo."""

    id: str
    origem: str  # inmet | firms | inpe
    fonte: str  # crédito exibido na tela e na mensagem
    tipo: str  # tempestade | chuva | vento | geada | frio | calor | baixa_umidade | fogo | outro
    gravidade: str  # potencial | perigo | grande_perigo
    titulo: str
    inicio: datetime
    fim: datetime
    poligonos: tuple[tuple[Coord, ...], ...] = ()
    pontos: tuple[Coord, ...] = ()
    riscos: str = ""
    instrucoes: str = ""
    link: str = ""

    def como_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(inicio=self.inicio.isoformat(), fim=self.fim.isoformat(), poligonos=[list(map(list, p)) for p in self.poligonos],
                 pontos=[list(p) for p in self.pontos])
        return d


@dataclass(frozen=True)
class Foco:
    lat: float
    lon: float
    quando: datetime
    origem: str  # firms | inpe
    satelite: str = ""


@dataclass
class ResultadoFonte:
    """O que a rotina sabe de cada fonte nesta execução. Fonte fora do ar nunca vira "sem alerta"."""

    origem: str
    estado: str  # ok | indisponivel | desligada
    credito: str
    detalhe: str = ""
    alertas: list[AlertaExterno] = field(default_factory=list)
    focos: list[Foco] = field(default_factory=list)


def _texto(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def _hora_brasilia(texto: str) -> datetime:
    return datetime.strptime(texto.strip()[:16], "%Y-%m-%d %H:%M").replace(tzinfo=BRASILIA).astimezone(UTC)


def _poligonos(bruto: Any) -> tuple[tuple[Coord, ...], ...]:
    geo = json.loads(bruto) if isinstance(bruto, str) else bruto
    if not isinstance(geo, dict):
        return ()
    if geo.get("type") == "Polygon":
        aneis = [geo["coordinates"][0]]
    elif geo.get("type") == "MultiPolygon":
        aneis = [p[0] for p in geo["coordinates"]]
    else:
        return ()
    return tuple(tuple((float(c[1]), float(c[0])) for c in anel) for anel in aneis if len(anel) >= 3)


def _tipo_inmet(descricao: str) -> str:
    d = descricao.lower()
    return next((t for termo, t in _TIPO_INMET if termo in d), "outro")


def interpretar_inmet(dados: Any) -> list[AlertaExterno]:
    if not isinstance(dados, dict):
        raise ProvedorRespostaInvalida("inmet", "formato inesperado")
    saida: list[AlertaExterno] = []
    for item in [*(dados.get("hoje") or []), *(dados.get("futuro") or [])]:
        try:
            if item.get("encerrado"):
                continue
            descricao = _texto(item.get("descricao"))
            saida.append(AlertaExterno(
                id=f"inmet:{item['id']}", origem="inmet", fonte=INMET_CREDITO, tipo=_tipo_inmet(descricao),
                gravidade=_SEVERIDADE_INMET.get(_texto(item.get("severidade")).lower(), "potencial"),
                titulo=f"{descricao} ({_texto(item.get('severidade'))})", inicio=_hora_brasilia(item["inicio"]), fim=_hora_brasilia(item["fim"]),
                poligonos=_poligonos(item.get("poligono")), riscos=_texto(item.get("riscos"))[:400], instrucoes=_texto(item.get("instrucoes"))[:400],
                link=INMET_LINK.format(id=item["id"])))
        except (KeyError, TypeError, ValueError) as exc:
            log.warning("aviso do INMET ignorado: %s", type(exc).__name__)
    return [a for a in saida if a.poligonos]


class AvisosInmet:
    origem, credito = "inmet", INMET_CREDITO

    def __init__(self, cliente: ClienteHttp, url: str = INMET_URL) -> None:
        self._http, self._url = cliente, url

    def buscar(self) -> list[AlertaExterno]:
        return interpretar_inmet(self._http.requisitar("GET", self._url))


def interpretar_firms(texto: str) -> list[Foco]:
    leitor = csv.DictReader(io.StringIO(texto))
    if not leitor.fieldnames or "latitude" not in leitor.fieldnames:
        raise ProvedorRespostaInvalida("nasa_firms", (texto.strip().splitlines() or ["resposta vazia"])[0][:80])
    focos = []
    for linha in leitor:
        try:
            quando = datetime.strptime(f"{linha['acq_date']} {int(linha['acq_time']):04d}", "%Y-%m-%d %H%M").replace(tzinfo=UTC)
            focos.append(Foco(float(linha["latitude"]), float(linha["longitude"]), quando, "firms", linha.get("satellite", "")))
        except (KeyError, ValueError):
            continue
    return focos


class FocosFirms:
    origem, credito = "firms", FIRMS_CREDITO

    def __init__(self, cliente: ClienteHttp, chave: str, fontes: tuple[str, ...] = FIRMS_FONTES) -> None:
        self._http, self._chave, self._fontes = cliente, chave, fontes

    def buscar(self, caixa: tuple[float, float, float, float]) -> list[Foco]:
        """caixa = (sul, oeste, norte, leste). Um pedido por satélite, último dia."""
        s, w, n, e = caixa
        focos: list[Foco] = []
        for fonte in self._fontes:
            focos += interpretar_firms(self._http.requisitar_texto("GET", FIRMS_URL.format(chave=self._chave, fonte=fonte, w=w, s=s, e=e, n=n)))
        return focos


_ARQ_INPE = re.compile(r"focos_10min_(\d{8})_(\d{4})\.csv")


def arquivos_inpe(listagem: str) -> list[str]:
    return sorted(set(m.group(0) for m in _ARQ_INPE.finditer(listagem)))


def interpretar_inpe(texto: str) -> list[Foco]:
    focos = []
    for linha in csv.DictReader(io.StringIO(texto)):
        try:
            quando = datetime.strptime(linha["data"].strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
            focos.append(Foco(float(linha["lat"]), float(linha["lon"]), quando, "inpe", (linha.get("satelite") or "").strip()))
        except (KeyError, ValueError, AttributeError):
            continue
    return focos


class FocosInpe:
    """Lê só os arquivos de 10 min ainda não processados (o último processado fica no estado da rotina), no máximo `maximo`."""

    origem, credito = "inpe", INPE_CREDITO

    def __init__(self, cliente: ClienteHttp, url: str = INPE_URL, maximo: int = 12) -> None:
        self._http, self._url, self._maximo = cliente, url, maximo

    def buscar(self, depois_de: str = "") -> tuple[list[Foco], str]:
        novos = [a for a in arquivos_inpe(self._http.requisitar_texto("GET", self._url)) if a > depois_de][-self._maximo:]
        focos: list[Foco] = []
        for arq in novos:
            focos += interpretar_inpe(self._http.requisitar_texto("GET", self._url + arq))
        return focos, (novos[-1] if novos else depois_de)
