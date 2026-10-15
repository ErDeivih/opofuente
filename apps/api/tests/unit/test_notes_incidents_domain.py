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

Y desde el §2 de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`, lo que decide la
**reclasificación** de las incidencias: qué es una pregunta mal importada (mecánico, sin modelo),
cuándo una incidencia de clave es un falso positivo y en qué categoría acaba cada una. Es lo que hay
que poder probar sin base de datos y sin gastar una llamada, porque son 453 filas y una regla mal
puesta se ve en las cifras.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from opofuente.domain.notes_incidents import (
    CLOSED_STATUSES,
    MARCA_DE_RECLASIFICACION,
    REGLA_MENOS_DE_TRES_OPCIONES,
    REGLA_OPCION_CON_PATRON_DE_OTRA,
    REGLA_OPCION_TRUNCADA,
    REGLA_OPCIONES_DUPLICADAS,
    IncidentCoverage,
    IncidentStatus,
    categoria_reclasificada,
    detalle_reclasificado,
    es_falso_positivo,
    fiabilidad_por_discrepancia,
    normalise_note,
    regla_de_mala_importacion,
    reviewed_at_for,
)
from opofuente.domain.notes_reports import MAX_REASON_CHARS, NoteReportStatus
from opofuente.domain.topic_notes import CategoriaIncidencia, Motivo

AHORA = datetime(2026, 10, 13, 9, 30, tzinfo=UTC)


def test_el_vocabulario_es_el_de_bandeja_que_la_aplicacion_ya_tenia() -> None:
    """Los cuatro estados de `notes_reports`, palabra por palabra, más los dos de la regla (F31).

    Es lo que el §1.2 del objetivo pide («usa los estados que existan»): no se estrena vocabulario,
    se reutiliza el de la otra bandeja del panel, que es el único que la aplicación tiene para decir
    «esto espera, lo tengo en la mano, lo he resuelto, o me parece que el aviso se equivoca».

    **Los dos últimos son de esta bandeja y solo de esta**, y la prueba dice las dos cosas a la vez:
    hasta `dismissed` el vocabulario es el compartido, y a partir de ahí está lo que solo puede
    pasar aquí —una regla que resuelve sin el propietario—. La bandeja del alumno no tiene
    resolución
    automática y no le hacen falta: meterlos allí sería inventarle un flujo.
    """
    compartidos = ["open", "in_progress", "reviewed", "dismissed"]
    assert [estado.value for estado in IncidentStatus][: len(compartidos)] == compartidos
    assert [estado.value for estado in IncidentStatus] == [
        estado.value for estado in NoteReportStatus
    ] + ["propuesta_lista", "no_son_preguntas"]


def test_solo_caben_las_dos_coberturas_que_la_tabla_admite() -> None:
    """`covered` y `gap` son de `Coverage`, no de la bandeja: una pregunta cubierta no llega
    aquí."""
    assert [cobertura.value for cobertura in IncidentCoverage] == ["doubtful", "conflict"]
    with pytest.raises(ValueError):
        IncidentCoverage("covered")


def test_los_estados_del_dominio_son_los_del_check_de_la_migracion_y_del_modelo() -> None:
    """La base y el dominio, comparados valor por valor.

    Se leen el texto de **las migraciones que han ampliado el vocabulario** —`0035`, que lo creó con
    los cuatro de siempre, y `0039`, que añade los dos de la resolución automática (F31)— y el del
    modelo, en vez de volver a escribir la lista: si alguien añade un estado a la base y no al
    dominio (o al revés), esta prueba lo dice, en vez de dejarlo para que lo descubra una escritura
    rechazada en producción.
    """
    from opofuente.infrastructure import db_models

    raiz = Path(db_models.__file__).resolve().parents[2]
    versiones = raiz / "alembic" / "versions"
    migraciones = "\n".join(
        (versiones / nombre).read_text(encoding="utf-8")
        for nombre in ("0035_incidencias_despachables.py", "0039_bandeja_por_conjunto.py")
    )
    modelo = Path(db_models.__file__).read_text(encoding="utf-8")

    for cual in IncidentStatus:
        assert f"'{cual.value}'" in migraciones, (
            f"{cual.value} falta en el CHECK de las migraciones"
        )
        assert f"'{cual.value}'" in modelo, f"{cual.value} falta en el CHECK del modelo"


def test_cerrar_una_incidencia_deja_fecha_y_reabrirla_la_borra() -> None:
    assert reviewed_at_for(IncidentStatus.REVIEWED, AHORA) == AHORA
    assert reviewed_at_for(IncidentStatus.DISMISSED, AHORA) == AHORA
    assert reviewed_at_for(IncidentStatus.IN_PROGRESS, AHORA) is None
    assert reviewed_at_for(IncidentStatus.OPEN, AHORA) is None
    # `no_son_preguntas` **deja fecha** aunque no la haya cerrado el propietario: la columna dice
    # cuándo dejó de esperar una incidencia —y esta dejó de esperar cuando la escribió la regla—; el
    # quién vive en el evento de auditoría.
    assert reviewed_at_for(IncidentStatus.NO_SON_PREGUNTAS, AHORA) == AHORA
    # `propuesta_lista` **no**: espera una aprobación, y una incidencia que espera con fecha de
    # revisión es la traza que miente.
    assert reviewed_at_for(IncidentStatus.PROPUESTA_LISTA, AHORA) is None
    assert {
        IncidentStatus.REVIEWED,
        IncidentStatus.DISMISSED,
        IncidentStatus.NO_SON_PREGUNTAS,
    } == CLOSED_STATUSES


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


# ------------------------------------------------------------------ la reclasificación (§2)


def test_una_pregunta_sin_tres_opciones_es_mala_importacion_y_una_de_dos_no() -> None:
    """El juicio de las opciones depende del **tipo**: una de verdadero o falso tiene dos a
    propósito.

    Sin esta distinción la regla marcaría como rotas todas las preguntas de verdadero/falso del
    banco.
    """
    assert (
        regla_de_mala_importacion(["una", "otra"], "single_choice") == REGLA_MENOS_DE_TRES_OPCIONES
    )
    assert regla_de_mala_importacion(["Verdadero", "Falso"], "true_false") is None
    assert regla_de_mala_importacion(["una respuesta larga"], "free_text_reference") is None
    assert regla_de_mala_importacion(["a", "b", "c"], "single_choice") is None


def test_una_opcion_con_el_patron_de_otra_esta_fundida() -> None:
    """«JOB 0d) CALL» son dos opciones en una: se ve sin modelo y se puede reparar partiéndola."""
    assert (
        regla_de_mala_importacion(
            ["primera opción larga", "segunda opción larga", "JOB 0d) CALL"], "single_choice"
        )
        == REGLA_OPCION_CON_PATRON_DE_OTRA
    )
    # Y una opción que **empieza** por su propio rótulo no está fundida.
    assert (
        regla_de_mala_importacion(
            ["primera opción larga", "segunda opción larga", "c) la tercera"], "single_choice"
        )
        is None
    )


def test_dos_opciones_iguales_y_una_cortada_a_media_frase() -> None:
    assert (
        regla_de_mala_importacion(
            ["la misma opción larga", "la misma opción larga", "otra distinta larga"],
            "single_choice",
        )
        == REGLA_OPCIONES_DUPLICADAS
    )
    assert (
        regla_de_mala_importacion(
            [
                "el número de conjuntos de datos duplicados no supera el mínimo necesario",
                "el número de conjuntos de datos duplicados no supera el mínimo necesario para "
                "garantizar la continuidad del servicio",
                "una tercera distinta",
            ],
            "single_choice",
        )
        == REGLA_OPCION_TRUNCADA
    )


def test_un_numero_que_es_el_principio_de_otro_no_esta_cortado() -> None:
    """La guarda del truncado: sin ella, la regla marcaba preguntas de puertos que están
    perfectas.

    «25» es el principio de «2525» y las dos son respuestas válidas a la misma pregunta. Medido en
    la copia de la base real: de las cinco marcas de truncado, cuatro eran de este tipo.
    """
    assert regla_de_mala_importacion(["25", "587", "2525", "134"], "single_choice") is None


def test_un_falso_positivo_es_que_la_letra_de_los_apuntes_este_en_la_clave() -> None:
    """El motor marcaba la incidencia por un hecho dudoso **antes** de comparar letras."""
    assert es_falso_positivo(letra="a", esperadas=("a",), resultado="doubtful") is True
    assert es_falso_positivo(letra="A", esperadas=("a", "b"), resultado="conflict") is True
    assert es_falso_positivo(letra="b", esperadas=("d",), resultado="doubtful") is False
    # Una comprobación que ya está cubierta es un resto: el motor la habría borrado en la corrida
    # siguiente.
    assert es_falso_positivo(letra=None, esperadas=(), resultado="covered") is True
    # Y sin letra no se puede decir nada: no es un falso positivo.
    assert es_falso_positivo(letra=None, esperadas=(), resultado="doubtful") is False


def _categoria(
    *,
    actual: CategoriaIncidencia = CategoriaIncidencia.NORMA_CAMBIADA,
    motivo: Motivo = Motivo.CLAVE_CONTRADICE_LA_NORMA,
    regla: str | None = None,
    cuarentena: bool = False,
    falso: bool = False,
    frase: bool = False,
    norma: bool = False,
) -> CategoriaIncidencia | None:
    return categoria_reclasificada(
        actual=actual,
        motivo=motivo,
        regla_mal_importada=regla,
        conjunto_en_cuarentena=cuarentena,
        falso_positivo=falso,
        tiene_frase=frase,
        norma_citada=norma,
    )


def test_el_orden_de_las_reglas_es_el_del_documento() -> None:
    """Una pregunta mal importada gana a todo, y una clave en cuarentena gana a la sospecha.

    El orden no es un detalle: es lo que hace que las cifras signifiquen algo. Si la cuarentena
    ganara a la mala importación, una pregunta rota contaría como «clave no fiable» y el propietario
    iría a mirar una clave que no es el problema.
    """
    assert _categoria(regla=REGLA_MENOS_DE_TRES_OPCIONES, cuarentena=True, frase=True) is (
        CategoriaIncidencia.PREGUNTA_MAL_IMPORTADA
    )
    assert _categoria(cuarentena=True, frase=True) is CategoriaIncidencia.CLAVE_NO_FIABLE
    assert _categoria(frase=True) is CategoriaIncidencia.CLAVE_SOSPECHOSA


def test_una_incidencia_de_clave_no_se_queda_en_norma_cambiada_sin_la_cita_de_la_norma() -> None:
    """`norma_cambiada` exige la cita de la norma vigente con su versión o fecha; sin ella, no hay
    norma cambiada que afirmar —es una clave que contradice los apuntes, que es lo que se puede
    decir—. El parámetro está para la pasada del modelo que sí traiga la cita."""
    assert _categoria() is CategoriaIncidencia.CLAVE_SOSPECHOSA
    assert _categoria(norma=True) is CategoriaIncidencia.NORMA_CAMBIADA


def test_un_falso_positivo_sale_de_la_bandeja_antes_de_cualquier_regla() -> None:
    assert _categoria(falso=True, regla=REGLA_MENOS_DE_TRES_OPCIONES, cuarentena=True) is None


def test_un_hueco_y_una_pregunta_sin_clave_se_quedan_como_estaban() -> None:
    """El hueco es que falte texto y la ambigua es que no haya clave: ninguna se arregla mirando la
    clave, así que la reclasificación no las toca."""
    assert (
        _categoria(
            actual=CategoriaIncidencia.HUECO_SIN_MATERIAL,
            motivo=Motivo.SIN_FRASE_EN_LOS_APUNTES,
        )
        is CategoriaIncidencia.HUECO_SIN_MATERIAL
    )
    assert (
        _categoria(actual=CategoriaIncidencia.PREGUNTA_AMBIGUA, motivo=Motivo.CLAVE_SIN_DEFINIR)
        is CategoriaIncidencia.PREGUNTA_AMBIGUA
    )
    assert (
        _categoria(
            actual=CategoriaIncidencia.PREGUNTA_AMBIGUA,
            motivo=Motivo.SIN_MATERIA_EN_EL_INDICE,
        )
        is CategoriaIncidencia.PREGUNTA_AMBIGUA
    )


def test_el_detalle_reclasificado_conserva_lo_que_dijo_el_motor_y_no_se_apila() -> None:
    """Lo que escribió la corrida no se tira, y volver a ejecutarlo deja el mismo texto."""
    original = (
        "la clave contradice la norma o el material de estudio\nclave: d — los apuntes dicen: a"
    )
    una = detalle_reclasificado(
        motivo="la clave contradice lo que dicen los apuntes",
        detalle=original,
        fecha=AHORA,
        regla=REGLA_OPCION_TRUNCADA,
    )
    dos = detalle_reclasificado(
        motivo="la clave contradice lo que dicen los apuntes",
        detalle=una,
        fecha=AHORA,
        regla=REGLA_OPCION_TRUNCADA,
    )

    assert una.startswith(f"{MARCA_DE_RECLASIFICACION} 2026-10-13")
    assert f"regla mecánica: {REGLA_OPCION_TRUNCADA}" in una
    assert original in una, "el detalle del motor sigue debajo"
    assert dos == una, "ejecutarla dos veces no apila cabeceras"


def test_la_discrepancia_de_un_conjunto_necesita_una_muestra() -> None:
    """Con dos comprobaciones no se puede decir que una clave sea mala."""
    assert fiabilidad_por_discrepancia(3, 3) is None
    assert fiabilidad_por_discrepancia(14, 15) == "no_fiable"
    assert fiabilidad_por_discrepancia(4, 15) == "dudosa"
    assert fiabilidad_por_discrepancia(1, 15) == "fiable"
