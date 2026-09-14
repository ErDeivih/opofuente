"""Reloj del sistema. Es un puerto para poder inyectar tiempo fijo en las pruebas."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Tiempo real, siempre en UTC (01_PRODUCT-SPEC §7: todas las fechas internas en UTC)."""

    def now(self) -> datetime:
        return datetime.now(UTC)
