"""El dominio de los avisos del alumno: los estados y la nota del despacho (F16, bloque C).

Es la parte que decide el panel y por eso se prueba sin base de datos y sin framework:

- el **vocabulario de estados** que la bandeja puede escribir, con el que ya había y el que faltaba
  para poder decir «lo he visto y estoy en ello»;
- la **forma de la nota**: una línea, vacía es «no hay nota», y kilométrica se rechaza;
- y **qué cuenta como despachado**: cerrar deja fecha y reabrir la borra, porque la columna dice
  cuándo se despachó y un aviso abierto con fecha de revisión es una traza que miente.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from opofuente.domain.notes_reports import (
    CLOSED_STATUSES,
    MAX_REASON_CHARS,
    NoteReportStatus,
    normalise_note,
    reviewed_at_for,
)

AHORA = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)


def test_el_vocabulario_tiene_los_cuatro_estados_que_la_bandeja_despacha() -> None:
    """Los tres de `0033` y el que faltaba: sin él un aviso está pendiente o está cerrado."""
    assert [estado.value for estado in NoteReportStatus] == [
        "open",
        "in_progress",
        "reviewed",
        "dismissed",
    ]


def test_cerrar_un_aviso_deja_fecha_y_reabrirlo_la_borra() -> None:
    assert reviewed_at_for(NoteReportStatus.REVIEWED, AHORA) == AHORA
    assert reviewed_at_for(NoteReportStatus.DISMISSED, AHORA) == AHORA
    assert reviewed_at_for(NoteReportStatus.IN_PROGRESS, AHORA) is None
    assert reviewed_at_for(NoteReportStatus.OPEN, AHORA) is None
    assert {NoteReportStatus.REVIEWED, NoteReportStatus.DISMISSED} == CLOSED_STATUSES


def test_una_nota_se_guarda_en_una_linea() -> None:
    assert normalise_note("  Arreglado en la versión\ndel 12-oct.  ") == (
        "Arreglado en la versión del 12-oct."
    )


def test_sin_nota_es_none_y_no_una_cadena_vacia() -> None:
    """`None` y en blanco son lo mismo: «no hay nota». Guardar `''` obligaría a distinguirlos."""
    assert normalise_note(None) is None
    assert normalise_note("   ") is None
    assert normalise_note("\n\t ") is None


def test_una_nota_kilometrica_se_rechaza() -> None:
    with pytest.raises(ValueError, match=str(MAX_REASON_CHARS)):
        normalise_note("x" * (MAX_REASON_CHARS + 1))

    assert normalise_note("x" * MAX_REASON_CHARS) == "x" * MAX_REASON_CHARS
