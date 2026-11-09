"""Mede a Central de Viagem com frotas de 10 a 100 caminhões (docs/ideias/reestruturacao-transporte-fase5.md, seção Desempenho).

  python tools/transporte_carga.py --frota 10 20 30 50 100 --banco memoria sqlite --duracao 30

Sobe um servidor local (uvicorn, porta 8791) por cenário, com dados de demonstração, e faz o que a frota faria:
  - cada caminhão envia uma leitura de posição a cada --intervalo segundos (padrão 10), assinada com HMAC;
  - um painel aberto por 5 caminhões consulta /posicoes a cada 15 s (o portal do cliente);
  - o gestor lança uma viagem por caminhão no começo (cálculo de rota e despesas).
Relata, por cenário: requisições por segundo, latência p50/p95/p99 por tipo, erros e tamanho do banco. Nada vai a serviço externo.
Os limites de aceitação ficam no fim (LIMITES) e fazem o comando sair com erro quando um cenário os viola.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess  # nosec B404 - só sobe o uvicorn local com argumentos fixos
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from backend.transporte.telemetria.seguranca import assinar  # noqa: E402

PORTA = 8791
TID = "00000000-0000-4000-8000-000000000001"
CHAVE = "carga-" + "x" * 40
H = {"X-Transportadora-Id": TID, "X-Usuario-Papel": "gestor", "X-Usuario-Id": "carga"}
LIMITES = {"p95_leitura_ms": 250, "p95_posicoes_ms": 1000, "erros_pct": 0.5}  # critérios de aceite por cenário


def _pct(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    v = sorted(valores)
    return v[min(len(v) - 1, int(len(v) * p))]


def cenario(frota: int, banco: str, duracao: int, intervalo: float) -> dict:
    pasta = Path(tempfile.mkdtemp(prefix="carga-"))
    env = {**os.environ, "ORGATEC_TRANSPORTE": "1", "ORGATEC_TRANSPORTE_SENSORES": "1", "ORGATEC_TRANSPORTE_DEMO": "1", "ORGATEC_TRANSPORTE_CHAVE": CHAVE,
           "ORGATEC_TRANSPORTE_BANCO": banco, "ORGATEC_TRANSPORTE_DB": str(pasta / "t.db"), "ORGATEC_DB": str(pasta / "site.db"), "ORGATEC_SEGREDO_IP": "s" * 40}
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app:app", "--port", str(PORTA), "--log-level", "error"], cwd=RAIZ, env=env)  # nosec B603
    base = f"http://127.0.0.1:{PORTA}"
    try:
        for _ in range(60):
            try:
                if httpx.get(base + "/api/transporte/contexto", headers=H, timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.5)
        cli = httpx.Client(base_url=base, headers=H, timeout=30)
        pontos = [{"nome": "Goiânia", "uf": "GO"}, {"nome": "Palmas", "uf": "TO"}]
        lat_rota: list[float] = []
        frota_ids = []
        for i in range(frota):
            v = cli.post("/api/transporte/veiculos", json={"placa": f"CAR{i:04d}", "eixos": 5, "consumo_km_l_carregado": 2.5, "consumo_km_l_vazio": 3.2, "tanque_l": 600}).json()
            t0 = time.perf_counter()
            viagem = cli.post("/api/transporte/viagens", json={"veiculo_id": v["id"], "pontos": pontos, "carregado": True,
                                                              "partida_prevista": (datetime.now(UTC) + timedelta(minutes=5)).isoformat()}).json()
            lat_rota.append((time.perf_counter() - t0) * 1000)
            s = cli.post("/api/transporte/sensores", json={"veiculo_id": v["id"], "nome": f"GPS {i}", "tipo": "rastreador"}).json()
            frota_ids.append((s["id"], s["segredo"], viagem["id"]))

        lat = {"leitura": [], "posicoes": []}
        erros = {"total": 0, "reqs": 0}
        codigos: dict[str, int] = {}
        trava = threading.Lock()
        fim = time.monotonic() + duracao

        def registrar(tipo: str, ms: float, ok: bool, codigo: int = 0) -> None:
            with trava:
                codigos[f"{tipo}:{codigo}"] = codigos.get(f"{tipo}:{codigo}", 0) + 1
                erros["reqs"] += 1
                erros["total"] += 0 if ok else 1
                if ok:
                    lat[tipo].append(ms)

        def caminhao(idx: int, sid: str, segredo: str) -> None:
            c = httpx.Client(base_url=base, timeout=30)
            n = 0
            time.sleep((idx % 100) / 100 * intervalo)  # espalha os primeiros envios
            while time.monotonic() < fim:
                corpo = json.dumps({"leituras": [{"id": f"{idx}-{n}", "ts": datetime.now(UTC).isoformat(), "lat": -16.6 + n * 1e-4, "lon": -49.2,
                                                  "velocidade_kmh": 80, "ignicao": True}]}).encode()
                ts = str(int(time.time()))
                t0 = time.perf_counter()
                try:
                    r = c.post(f"/api/telemetria/{sid}", content=corpo, headers={"X-Timestamp": ts, "X-Assinatura": assinar(segredo, ts, corpo)})
                    registrar("leitura", (time.perf_counter() - t0) * 1000, r.status_code == 200, r.status_code)
                except httpx.HTTPError:
                    registrar("leitura", 0, False)
                n += 1
                time.sleep(max(0.0, intervalo - (time.perf_counter() - t0)))

        def painel(ids: list[str], n: int) -> None:
            # um usuário por painel, como na vida real (o limite da API é por usuário logado)
            c = httpx.Client(base_url=base, headers={**H, "X-Usuario-Id": f"painel{n}"}, timeout=30)
            while time.monotonic() < fim:
                for vid in ids:
                    t0 = time.perf_counter()
                    try:
                        r = c.get(f"/api/transporte/viagens/{vid}/posicoes")
                        registrar("posicoes", (time.perf_counter() - t0) * 1000, r.status_code == 200, r.status_code)
                    except httpx.HTTPError:
                        registrar("posicoes", 0, False)
                time.sleep(15)

        fios = [threading.Thread(target=caminhao, args=(i, sid, seg), daemon=True) for i, (sid, seg, _) in enumerate(frota_ids)]
        fios += [threading.Thread(target=painel, args=([v for _, _, v in frota_ids[i:i + 5]], i // 5), daemon=True) for i in range(0, frota, 5)]
        t_ini = time.monotonic()
        for f in fios:
            f.start()
        for f in fios:
            f.join()
        dur = time.monotonic() - t_ini
        banco_kb = (pasta / "t.db").stat().st_size // 1024 if (pasta / "t.db").exists() else 0
        return {"frota": frota, "banco": banco, "req_s": round(erros["reqs"] / dur, 1), "rota_ms_p50": round(statistics.median(lat_rota)),
                "leitura_p50": round(_pct(lat["leitura"], 0.5)), "leitura_p95": round(_pct(lat["leitura"], 0.95)), "leitura_p99": round(_pct(lat["leitura"], 0.99)),
                "posicoes_p50": round(_pct(lat["posicoes"], 0.5)), "posicoes_p95": round(_pct(lat["posicoes"], 0.95)),
                "erros_pct": round(100 * erros["total"] / max(1, erros["reqs"]), 2), "banco_kb": banco_kb, "reqs": erros["reqs"], "codigos": codigos}
    finally:
        srv.terminate()
        srv.wait(timeout=15)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--frota", type=int, nargs="+", default=[10, 20, 30, 50, 100])
    ap.add_argument("--banco", nargs="+", default=["memoria", "sqlite"], choices=["memoria", "sqlite"])
    ap.add_argument("--duracao", type=int, default=30, help="segundos de tráfego por cenário")
    ap.add_argument("--intervalo", type=float, default=10.0, help="segundos entre leituras de cada caminhão")
    ap.add_argument("--saida", help="grava o resultado em JSON")
    a = ap.parse_args(argv)
    res, reprovado = [], False
    print(f"{'frota':>5} {'banco':8} {'req/s':>6} {'rota p50':>9} {'leit p50':>9} {'p95':>6} {'p99':>6} {'pos p50':>8} {'p95':>6} {'erros%':>7} {'banco KB':>9}")
    for b in a.banco:
        for n in a.frota:
            r = cenario(n, b, a.duracao, a.intervalo)
            res.append(r)
            falha = r["leitura_p95"] > LIMITES["p95_leitura_ms"] or r["posicoes_p95"] > LIMITES["p95_posicoes_ms"] or r["erros_pct"] > LIMITES["erros_pct"]
            reprovado |= falha
            if r["erros_pct"]:
                print("   códigos HTTP:", r["codigos"])
            print(f"{r['frota']:>5} {r['banco']:8} {r['req_s']:>6} {r['rota_ms_p50']:>9} {r['leitura_p50']:>9} {r['leitura_p95']:>6} {r['leitura_p99']:>6} "
                  f"{r['posicoes_p50']:>8} {r['posicoes_p95']:>6} {r['erros_pct']:>7} {r['banco_kb']:>9} {'REPROVADO' if falha else ''}")
    if a.saida:
        Path(a.saida).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if reprovado else 0


if __name__ == "__main__":
    sys.exit(main())
