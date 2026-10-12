"""El dominio de la bandeja del motor: sus estados, su nota y su vocabulario cerrado (F18).

Es la parte que decide el panel y por eso se prueba sin base de datos y sin framework:

- el **vocabulario de estados** que la bandeja puede escribir. La tabla de `notes_incidents` no
tenía
  ninguno (migración `0035`): se le dan los cuatro que esta aplicación **ya** usa para despachar una
  bandeja —los de `notes_reports`, `0033`/`0034`— y ni uno más. Inventar un vocabulario nuevo para
  el
  mismo trabajo sería inventar un flujo;
- el **vocabulario de coberturas**: aquí solo caben dos (`doubtful` y `conflict`), porque el `CHECK`
  de la tabla lo dice desde `0031`;
- la **forma de la nota**: una línea, vacía es «no hay nota», y kilométrica se rechaza;
- y **qué cuenta como despachado**: cerrar deja fecha y reabrir la borra, porque la columna dice
  cuándo se despachó y una incidencia abierta con fecha de revisión es una traza que miente.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from opofuente.domain.notes_incidents import (
    CLOSED_STATUSES,
    IncidentCoverage,
    IncidentStatus,
    normalise_note,
    reviewed_at_for,
)
from opofuente.domain.notes_reports import MAX_REASON_CHARS, NoteReportStatus

AHORA = datetime(2026, 10, 13, 9, 30, tzinfo=UTC)


def test_el_vocabulario_es_el_de_bandeja_que_la_aplicacion_ya_tenia() -> None:
    """Los cuatro estados de `notes_reports`, palabra por palabra: la bandeja habla el mismo idioma.

    Es lo que el §1.2 del objetivo pide («usa los estados que existan»): no se estrena vocabulario,
    se reutiliza el de la otra bandeja del panel, que es el único que la aplicación tiene para decir
    «esto espera, lo tengo en la mano, lo he resuelto, o me parece que el aviso se equivoca».
    """
    assert [estado.value for estado in IncidentStatus] == [
        "open",
        "in_progress",
        "reviewed",
        "dismissed",
    ]
    assert [estado.value for estado in IncidentStatus] == [
        estado.value for estado in NoteReportStatus
    ]


def test_solo_caben_las_dos_coberturas_que_la_tabla_admite() -> None:
    """`covered` y `gap` son de `Coverage`, no de la bandeja: una pregunta cubierta no llega
    aquí."""
    assert [cobertura.value for cobertura in IncidentCoverage] == ["doubtful", "conflict"]
    with pytest.raises(ValueError):
        IncidentCoverage("covered")


def test_los_estados_del_dominio_son_los_del_check_de_la_migracion_y_del_modelo() -> None:
    """La base y el dominio, comparados valor por valor.

    Se leen el texto de la migración `0035` y el del modelo en vez de volver a escribir la lista: si
    alguien añade un estado a la base y no al dominio (o al revés), esta prueba lo dice, en vez de
    dejarlo para que lo descubra una escritura rechazada en producción.
    """
    from opofuente.infrastructure import db_models

    raiz = Path(db_models.__file__).resolve().parents[2]
    migracion = (raiz / "alembic" / "versions" / "0035_incidencias_despachables.py").read_text(
        encoding="utf-8"
    )
    modelo = Path(db_models.__file__).read_text(encoding="utf-8")

    for cual in IncidentStatus:
        assert f"'{cual.value}'" in migracion, f"{cual.value} falta en el CHECK de la migración"
        assert f"'{cual.value}'" in modelo, f"{cual.value} falta en el CHECK del modelo"


def test_cerrar_una_incidencia_deja_fecha_y_reabrirla_la_borra() -> None:
    assert reviewed_at_for(IncidentStatus.REVIEWED, AHORA) == AHORA
    assert reviewed_at_for(IncidentStatus.DISMISSED, AHORA) == AHORA
    assert reviewed_at_for(IncidentStatus.IN_PROGRESS, AHORA) is None
    assert reviewed_at_for(IncidentStatus.OPEN, AHORA) is None
    assert {IncidentStatus.REVIEWED, IncidentStatus.DISMISSED} == CLOSED_STATUSES


def test_una_nota_se_guarda_en_una_linea() -> None:
    assert normalise_note("  Resuelto con la clave\ndel banco del 12-oct.  ") == (
        "Resuelto con la clave del banco del 12-oct."
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
