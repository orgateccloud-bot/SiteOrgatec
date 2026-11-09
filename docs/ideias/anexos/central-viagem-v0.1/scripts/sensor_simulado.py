"""Sensor simulado que envia leituras pela API de telemetria, como um rastreador real faria.

Coordenadas negativas precisam da forma --de=LAT,LON (com "=").

Uso:
    python scripts/sensor_simulado.py --url http://localhost:8000 --sensor <id> --segredo <segredo> \
        --de=-16.6869,-49.2648 --para=-10.1844,-48.3336 --passos 20 --intervalo 2
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime

import httpx

from transporte.telemetria.seguranca import assinar


def coord(txt: str) -> tuple[float, float]:
    lat, lon = (float(x) for x in txt.split(","))
    return lat, lon


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--sensor", required=True)
    ap.add_argument("--segredo", required=True)
    ap.add_argument("--de", type=coord, required=True)
    ap.add_argument("--para", type=coord, required=True)
    ap.add_argument("--passos", type=int, default=20)
    ap.add_argument("--intervalo", type=float, default=2.0)
    a = ap.parse_args()
    with httpx.Client(timeout=10) as cli:
        for i in range(a.passos + 1):
            f = i / a.passos
            leitura = {
                "id": f"cli-{int(time.time() * 1000)}-{i}",
                "ts": datetime.now(UTC).isoformat(),
                "lat": round(a.de[0] + (a.para[0] - a.de[0]) * f, 5),
                "lon": round(a.de[1] + (a.para[1] - a.de[1]) * f, 5),
                "velocidade_kmh": 68.0,
                "ignicao": True,
            }
            corpo = json.dumps({"leituras": [leitura]}).encode()
            ts = str(int(time.time()))
            r = cli.post(
                f"{a.url}/api/telemetria/{a.sensor}",
                content=corpo,
                headers={
                    "X-Timestamp": ts,
                    "X-Assinatura": assinar(a.segredo, ts, corpo),
                    "Content-Type": "application/json",
                },
            )
            print(i, r.status_code, r.text)
            time.sleep(a.intervalo)


if __name__ == "__main__":
    main()
