"""Distribui eventos de telemetria para quem acompanha a viagem (SSE).

Em memória: serve para uma instância. Com várias instâncias (Cloud Run escalando), troque por Redis Pub/Sub ou
Firestore mantendo a mesma interface (assinar / cancelar / publicar).
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any


class Broker:
    TAMANHO_FILA = 100

    def __init__(self) -> None:
        self._assinantes: dict[str, set[tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]]] = {}
        self._trava = threading.Lock()

    def assinar(self, viagem_id: str) -> asyncio.Queue[dict[str, Any]]:
        fila: asyncio.Queue[dict[str, Any]] = asyncio.Queue(self.TAMANHO_FILA)
        with self._trava:
            self._assinantes.setdefault(viagem_id, set()).add((asyncio.get_running_loop(), fila))
        return fila

    def cancelar(self, viagem_id: str, fila: asyncio.Queue[dict[str, Any]]) -> None:
        with self._trava:
            grupo = self._assinantes.get(viagem_id, set())
            for item in [i for i in grupo if i[1] is fila]:
                grupo.discard(item)
            if not grupo:
                self._assinantes.pop(viagem_id, None)

    def publicar(self, viagem_id: str, evento: dict[str, Any]) -> int:
        """Seguro para chamar de qualquer thread. Devolve quantos assinantes receberam."""
        with self._trava:
            alvos = list(self._assinantes.get(viagem_id, ()))
        for loop, fila in alvos:
            loop.call_soon_threadsafe(_colocar, fila, evento)
        return len(alvos)


def _colocar(fila: asyncio.Queue[dict[str, Any]], evento: dict[str, Any]) -> None:
    if fila.full():
        fila.get_nowait()  # descarta o mais antigo: para posição, o mais novo é o que importa
    fila.put_nowait(evento)
