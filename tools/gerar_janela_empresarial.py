"""Janela Empresarial e do Transporte: monta site/dados/empresarial/atual.json no padrão da Janela de Campo.

Uso:
    python tools/gerar_janela_empresarial.py            gera o arquivo agora (NUNCA publica)

Regras de cada cartão (docs/ideias/reestruturacao-transporte.md, Fase 4):
- todo cartão traz fonte, horário da coleta e estado: ok, atrasado ou indisponivel;
- falha ou fonte sem termos de uso conferidos: o cartão fica 'indisponivel' e NÃO traz valor antigo;
- piso de frete e alertas normativos só entram com revisão humana (tools/janela_manual.json);
- só usa dados do próprio site e o arquivo tools/janela_fontes.json; nenhuma fonte externa é consultada enquanto
  'termosConferidos' estiver vazio.
Este script não publica e não está ligado a agendador. A semana de sombra no GitHub Actions é um passo à parte.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess  # nosec B404 — só executa node com argumentos fixos
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "tools" / "janela_fontes.json"
MANUAL = RAIZ / "tools" / "janela_manual.json"
MONTAR = RAIZ / "tools" / "janela_empresarial_montar.js"
DESTINO = RAIZ / "site" / "dados" / "empresarial"
BRASILIA = timezone(timedelta(hours=-3))
HORARIOS = (5, 11, 17)
PERFIS = [{"id": f"{r}-{u}", "regime": r, "uf": u} for r in ("simples", "presumido", "real") for u in ("GO", "TO", "PA")]
AVISO = "Informação de apoio. Não substitui a SEFAZ, a ANTT nem o parecer do contador responsável."


def carregar_fontes() -> dict:
    return {f["id"]: f for f in json.loads(FONTES.read_text(encoding="utf-8"))["fontes"]}


def proxima_atualizacao(agora: datetime) -> str:
    for h in HORARIOS:
        if agora.hour < h:
            return f"hoje às {h:02d}h"
    return f"amanhã às {HORARIOS[0]:02d}h"


def montar_do_site(hoje: str) -> dict:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js não encontrado no PATH (necessário para tools/janela_empresarial_montar.js)")
    r = subprocess.run([node, str(MONTAR)], input=json.dumps({"hoje": hoje, "perfis": PERFIS}), capture_output=True, text=True,  # nosec B603
                       encoding="utf-8", cwd=RAIZ, check=False)
    if r.returncode != 0:
        raise RuntimeError(f"montagem da janela falhou: {r.stderr.strip()}")
    return json.loads(r.stdout)


def cartao(fonte: dict, agora: datetime, estado: str, dados=None, motivo: str | None = None) -> dict:
    """Cartão com fonte, horário da coleta e estado. 'indisponivel' nunca leva dados."""
    c = {"id": fonte["id"], "modulo": fonte["modulo"], "fonte": fonte["fonte"], "url": fonte.get("url", ""),
         "estado": estado, "validadeHoras": fonte["validadeHoras"]}
    if estado == "indisponivel":
        c["coletadoEm"] = None
        c["motivo"] = motivo or "fonte não habilitada"
    else:
        c["coletadoEm"] = agora.isoformat(timespec="minutes")
        c["dados"] = dados
    return c


def cartao_externo(fonte: dict, agora: datetime) -> dict:
    """Fonte externa: só é consultada com os termos conferidos e a fonte habilitada. Nesta versão não há coletor ligado."""
    if not fonte.get("termosConferidos") or not fonte.get("habilitada"):
        return cartao(fonte, agora, "indisponivel", motivo="termos de uso ainda não conferidos: a fonte não é consultada")
    return cartao(fonte, agora, "indisponivel", motivo="coletor ainda não implementado")


def cartao_piso(fonte: dict, agora: datetime, manual: dict) -> dict:
    piso = manual.get("pisoFrete")
    obrigatorios = ("resolucao", "publicadaEm", "vigenciaEm", "url", "revisadoPor", "revisadoEm")
    if not piso or any(not piso.get(k) for k in obrigatorios):
        return cartao(fonte, agora, "indisponivel", motivo="aguardando a revisão humana da resolução vigente; use a calculadora oficial da ANTT")
    return cartao(fonte, agora, "ok", {k: piso[k] for k in obrigatorios})


def gerar(agora: datetime | None = None, destino: Path = DESTINO, montar=montar_do_site) -> dict:
    agora = (agora or datetime.now(BRASILIA)).astimezone(BRASILIA)
    fontes = carregar_fontes()
    manual = json.loads(MANUAL.read_text(encoding="utf-8"))
    site = montar(agora.date().isoformat())
    transportador = {p: [x for x in site["perfis"][p] if x["esfera"] == "compliance" or x["id"] in ("pisosfrete01", "pisosfrete07")] for p in site["perfis"]}
    cartoes = []
    for f in fontes.values():
        if f["id"] == "E1":
            cartoes.append(cartao(f, agora, "ok", {"porPerfil": site["perfis"]}))
        elif f["id"] == "E4":
            cartoes.append(cartao(f, agora, "ok", {"itens": site["mudou"]}))
        elif f["id"] == "T4":
            cartoes.append(cartao(f, agora, "ok", {"porPerfil": transportador}))
        elif f["id"] == "T1":
            cartoes.append(cartao_piso(f, agora, manual))
        else:
            cartoes.append(cartao_externo(f, agora))
    janela = {"geradoEm": agora.isoformat(timespec="minutes"), "proximaAtualizacao": proxima_atualizacao(agora), "aviso": AVISO,
              "perfis": [{"id": p["id"], "regime": p["regime"], "uf": p["uf"]} for p in PERFIS], "cartoes": cartoes}
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "atual.json").write_text(json.dumps(janela, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return janela


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.parse_args(argv)
    j = gerar()
    ok = sum(1 for c in j["cartoes"] if c["estado"] == "ok")
    print(f"gerado: site/dados/empresarial/atual.json ({ok} cartões ok, {len(j['cartoes']) - ok} indisponíveis)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
