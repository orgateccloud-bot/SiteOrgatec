"""Vigia do boletim da Janela de Campo: confere o boletim que está NO AR e acusa quando ele ficou velho ou ilegível.

Existe porque o boletim pode falhar sem ninguém saber (entre 04 e 08/11/2026, 4 rodadas foram geradas e não publicadas por
credencial vencida) e porque execuções agendadas podem atrasar ou ser descartadas. Quem roda o vigia (hoje, nada: o workflow
de exemplo está em docs/ideias/boletim-vigia.yml.exemplo) usa o código de saída como alerta.

Uso:
    python tools/vigiar_boletim.py                          confere https://orgatec.io/dados/campo/atual.json
    python tools/vigiar_boletim.py --limite-horas 14        muda o limite (padrão 14 h; as rodadas são às 05h, 11h e 17h,
                                                            então o maior intervalo normal é de 12 h)
    python tools/vigiar_boletim.py --url OUTRA_URL

Saída 0: o boletim está em dia. Saída 1: atrasado, ilegível ou fora do ar (a mensagem diz qual e o que olhar).
O site mostra "Boletim desatualizado" ao visitante só depois de 18 h (LIMITE_HORAS em campo.js); o vigia avisa antes.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

URL = "https://orgatec.io/dados/campo/atual.json"
LIMITE_HORAS = 14.0
USER_AGENT = "orgatec.io vigia do boletim"


def avaliar(boletim: object, agora: datetime, limite_horas: float = LIMITE_HORAS) -> tuple[bool, str]:
    """(em_dia, mensagem). Só lê o campo geradoEm; não confia no resto do arquivo."""
    if not isinstance(boletim, dict) or not boletim.get("geradoEm"):
        return False, "O boletim no ar não tem a data de geração (geradoEm): o arquivo está ilegível ou fora do formato."
    try:
        gerado = datetime.fromisoformat(str(boletim["geradoEm"]))
    except ValueError:
        return False, f"A data de geração do boletim no ar não é válida: {boletim['geradoEm']!r}."
    if gerado.tzinfo is None:
        return False, f"A data de geração do boletim no ar não traz fuso horário: {boletim['geradoEm']!r}."
    horas = (agora - gerado).total_seconds() / 3600
    if horas < -1:
        return False, f"O boletim no ar diz ter sido gerado no futuro ({boletim['geradoEm']}); confira o relógio de quem gera."
    if horas > limite_horas:
        return False, (f"O boletim no ar foi gerado há {horas:.0f} h ({boletim['geradoEm']}), acima do limite de {limite_horas:g} h. "
                       "A rodada das 05h, 11h ou 17h pode não ter rodado ou não ter publicado: veja o log do agendador "
                       "(tools/logs/campo.log) ou a execução do workflow, e se a credencial do Firebase venceu.")
    return True, f"Boletim em dia: gerado há {max(horas, 0):.1f} h ({boletim['geradoEm']}), limite de {limite_horas:g} h."


def baixar(url: str) -> object:
    r = httpx.get(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"}, timeout=20, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def main(argv: list[str] | None = None, agora: datetime | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", default=URL)
    ap.add_argument("--limite-horas", type=float, default=LIMITE_HORAS)
    a = ap.parse_args(argv)
    try:
        em_dia, mensagem = avaliar(baixar(a.url), agora or datetime.now(timezone.utc), a.limite_horas)
    except (httpx.HTTPError, ValueError) as erro:
        em_dia, mensagem = False, f"Não foi possível ler o boletim no ar em {a.url}: {erro}"
    print(("OK: " if em_dia else "ALERTA: ") + mensagem)
    resumo = os.environ.get("GITHUB_STEP_SUMMARY")  # no GitHub Actions, o resultado aparece também no resumo da execução
    if resumo:
        with Path(resumo).open("a", encoding="utf-8") as f:
            f.write(f"### Vigia do boletim\n\n{'Em dia' if em_dia else '**ALERTA**'}: {mensagem}\n")
    return 0 if em_dia else 1


if __name__ == "__main__":
    sys.exit(main())
