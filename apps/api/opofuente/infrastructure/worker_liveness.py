"""Estado real del worker en este proceso.

El informe de capacidades no puede suponer que la cola se está trabajando: lo pregunta. La tarea
del worker marca aquí su arranque y su parada, de modo que una instalación con
`OPOFUENTE_WORKER_ENABLED=false` o con la base de datos sin migrar se declara **no disponible** en
lugar de operativa. Vive en `infrastructure` (y no en `workers`) para que el proveedor de
capacidades, que es infraestructura, no dependa de la capa del worker.
"""

from __future__ import annotations


class WorkerLiveness:
    """Marca de que la cola se está trabajando en este proceso."""

    def __init__(self) -> None:
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def mark_running(self) -> None:
        self._running = True

    def mark_stopped(self) -> None:
        self._running = False
