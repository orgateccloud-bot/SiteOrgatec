"""Compila o Tailwind do site (pendência T3: sai o CDN de teste, entra um CSS estático).

Lê tailwind.config.js (gerado por tools/gerar_design_system.py a partir de tokens.json) e as classes usadas
em site/**/*.html e site/assets/js/**/*.js, e grava site/assets/css/tailwind.css minificado.

Uso:  python tools/compilar_css.py
Rode depois de gerar_design_system.py, gerar_paginas.py e gerar_hub.py, sempre que uma página ganhar classes novas.
"""
from __future__ import annotations

import shutil
import subprocess  # nosec B404 - executa só o npx com argumentos fixos
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
VERSAO = "3.4.17"  # mesma família v3 do CDN usado na fase de testes
SAIDA = RAIZ / "site" / "assets" / "css" / "tailwind.css"


def main() -> None:
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise SystemExit("npx não encontrado: instale o Node.js para compilar o CSS.")
    cmd = [npx, "--yes", f"tailwindcss@{VERSAO}", "-c", "tailwind.config.js",
           "-i", "tools/tailwind-entrada.css", "-o", str(SAIDA.relative_to(RAIZ)), "--minify"]
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True)  # nosec B603 - argumentos fixos, sem shell
    if r.returncode != 0 or not SAIDA.exists():
        raise SystemExit(f"falha ao compilar o Tailwind:\n{r.stderr[-2000:]}")
    print(f"gerado: {SAIDA.relative_to(RAIZ)} ({SAIDA.stat().st_size // 1024} KB, Tailwind {VERSAO})")


if __name__ == "__main__":
    main()
