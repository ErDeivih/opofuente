"""Pruebas de integración de Guardia Civil y del recálculo (S08) por el camino real.

Lo que se comprueba aquí, con los perfiles oficiales sembrados:

1. **la fórmula `Px = (Y/T)·(A - E/(N-1))`** se calcula exacta sobre una parte completa de la
   convocatoria de Guardia Civil, y su umbral publicado sí se aplica (es la nota de la prueba);
2. **una práctica parcial no se escala**: con cuatro preguntas de un cuestionario de cien se muestra
   la puntuación directa y se dice por qué, en lugar de inventar una nota sobre cien;
3. **la regla de seis errores es exacta**: ortografía se evalúa como apto o no apto, sin puntuación;
4. **recalcular no reescribe el pasado**: al activar una clave nueva, la sesión se corrige otra
   vez con ella (evaluación nueva que sustituye a la anterior) y el resultado anterior se
   conserva para poder explicar qué cambió.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from opofuente.application.question_service import QuestionService
from opofuente.application.study_service import (
    AnswerInput,
    CreateSessionInput,
    SourceInput,
    StudyService,
)
from opofuente.config import Settings
from opofuente.domain.errors import SessionStateError
from opofuente.domain.study import Feedback, SessionMode
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)
GC = "gc-cabos-guardias"


class _Reloj:
    def now(self) -> datetime:
        return AHORA


def _piezas(settings: Settings) -> tuple[StudyService, QuestionService, SqlAlchemyStudyRepository]:
    engine = build_engine(settings.data_paths.database)
    sesiones = build_session_factory(engine)
    preguntas = SqlAlchemyQuestionRepository(sesiones)
    estudio = SqlAlchemyStudyRepository(sesiones)
    perfiles = SqlAlchemyProfileRepository(sesiones)
    reloj = _Reloj()
    return (
        StudyService(study=estudio, questions=preguntas, profiles=perfiles, clock=reloj),
        QuestionService(
            questions=preguntas,
            clock=reloj,
            documents=SqlAlchemyDocumentRepository(
                sesiones, RepresentationStore(settings.data_paths)
            ),
        ),
        estudio,
    )


def _ids(settings: Settings, code: str = GC) -> tuple[str, str | None]:
    engine = build_engine(settings.data_paths.database)
    try:
        perfiles = SqlAlchemyProfileRepository(build_session_factory(engine))
        oposicion = next(op for op in perfiles.list_oppositions() if op.code == code)
        return oposicion.id, oposicion.convocation_id
    finally:
        engine.dispose()


def _texto(preguntas: int, *, reservas: int = 0, correcta: str = "a", marcar: bool = False) -> str:
    """Un cuestionario de prueba con preguntas distintas (el enunciado las diferencia)."""
    lineas: list[str] = []
    for numero in range(1, preguntas + reservas + 1):
        marca = "[R] " if numero > preguntas else ""
        caso = f"{chr(ord('A') + (numero - 1) % 26)}{numero}"
        if marcar:
            lineas.append(f"{numero}. {marca}Marque las expresiones incorrectas del caso {caso}:")
            for indice in range(4):
                lineas.append(f"{chr(ord('a') + indice)}) Expresion {chr(ord('A') + indice)}")
        else:
            lineas.append(
                f"{numero}. {marca}El plazo del procedimiento del caso {caso} es de diez dias:"
            )
            for indice in range(4):
                lineas.append(f"{chr(ord('a') + indice)}) Opcion {chr(ord('A') + indice)}")
        lineas.append(f"Respuesta correcta: {correcta}")
        lineas.append("")
    return "\n".join(lineas)


def _conjunto(
    settings: Settings,
    *,
    preguntas: int,
    reservas: int = 0,
    marcar: bool = False,
    correcta: str = "a",
) -> str:
    """Un conjunto con su clave activa (banco privado: activar no necesita plantilla oficial)."""
    cuestiones = _piezas(settings)[1]
    opposition_id, _ = _ids(settings)
    conjunto = cuestiones.create_set(
        "Prueba de Guardia Civil", opposition_id=opposition_id, set_type="private_bank"
    )
    cuestiones.import_from_text(
        conjunto.id, _texto(preguntas, reservas=reservas, marcar=marcar, correcta=correcta)
    )
    clave = cuestiones.keys(conjunto.id)[0]
    aplicada, motivo = cuestiones.activate_key(clave.id)
    assert aplicada, motivo
    return conjunto.id


def _sesion(
    settings: Settings,
    set_id: str,
    *,
    parte: str,
    cantidad: int,
    feedback: Feedback = Feedback.IMMEDIATE,
) -> tuple[StudyService, str]:
    servicio = _piezas(settings)[0]
    opposition_id, gc_convocation = _ids(settings)
    assert gc_convocation is not None
    session = servicio.create_session(
        CreateSessionInput(
            opposition_id=opposition_id,
            mode=SessionMode.PRACTICE,
            sources=(
                SourceInput(
                    question_set_id=set_id, part_code=parte, count=cantidad, include_reserves=False
                ),
            ),
            convocation_version_id=gc_convocation,
            feedback=feedback,
        )
    )
    return servicio, servicio.start(session.id).id


def _responder(
    servicio: StudyService, session_id: str, *, correctas: int, fallos: int = 0, blancos: int = 0
) -> None:
    """Responde la sesión en orden: aciertos, fallos y blancos."""
    total = correctas + fallos + blancos
    for posicion in range(1, total + 1):
        if posicion <= correctas:
            claves: tuple[str, ...] = ("a",)
        elif posicion <= correctas + fallos:
            claves = ("b",)
        else:
            claves = ()
        vista = servicio.navigate(session_id, position=posicion).question
        assert vista is not None
        servicio.answer(
            session_id,
            AnswerInput(
                question_version_id=vista.question_version_id,
                chosen_option_keys=claves,
                elapsed_ms=1000,
            ),
        )


# --- la fórmula de Guardia Civil -----------------------------------------------------------------


def test_una_practica_parcial_no_se_escala_y_lo_dice(seeded_settings: Settings) -> None:
    """La fórmula de la convocatoria se aplica al cuestionario completo, no a cuatro preguntas."""
    set_id = _conjunto(seeded_settings, preguntas=10)
    servicio, session_id = _sesion(
        seeded_settings, set_id, parte="conocimientos_generales", cantidad=4
    )
    _responder(servicio, session_id, correctas=3, fallos=1)

    resultado = servicio.finish(session_id)
    parte = resultado.parts[0]

    assert parte.part_code == "conocimientos_generales"
    assert parte.kind == "direct", "sin el cuestionario completo no se escala"
    assert parte.score.fraction == "8/3", "3 aciertos menos un tercio"
    assert parte.passed is None
    assert parte.verdict_note is not None and "Práctica parcial" in parte.verdict_note


def test_el_cuestionario_completo_se_calcula_con_la_formula_publicada(
    seeded_settings: Settings,
) -> None:
    """Cien preguntas, 60 aciertos y 12 errores: `(100/100)·(60 - 12/3) = 56`, y el mínimo es 50."""
    set_id = _conjunto(seeded_settings, preguntas=100)
    servicio = _piezas(seeded_settings)[0]
    opposition_id, gc_convocation = _ids(seeded_settings)
    assert gc_convocation is not None
    session = servicio.create_session(
        CreateSessionInput(
            opposition_id=opposition_id,
            mode=SessionMode.PRACTICE,
            sources=(
                SourceInput(question_set_id=set_id, part_code="conocimientos_generales", count=100),
            ),
            convocation_version_id=gc_convocation,
            feedback=Feedback.AT_END,
        )
    )
    servicio.start(session.id)
    _responder(servicio, session.id, correctas=60, fallos=12, blancos=28)

    resultado = servicio.finish(session.id)
    parte = resultado.parts[0]

    assert parte.kind == "scaled"
    assert parte.score.fraction == "56", "(100/100)·(60 - 12/3)"
    assert parte.passed is True, "el mínimo publicado de la prueba es 50"
    assert resultado.total.score == parte.score
    assert resultado.official_available is False, "el proceso entero no se declara superado"
    assert resultado.total.passed is None


# --- la regla de seis errores --------------------------------------------------------------------


def test_ortografia_se_evalua_como_apto_o_no_apto(seeded_settings: Settings) -> None:
    """Cinco errores se pasan y seis no: es la regla publicada, y no da puntuación."""
    set_id = _conjunto(seeded_settings, preguntas=20, marcar=True)
    servicio, session_id = _sesion(seeded_settings, set_id, parte="ortografia", cantidad=20)
    _responder(servicio, session_id, correctas=15, fallos=5)

    resultado = servicio.finish(session_id)
    parte = resultado.parts[0]

    assert parte.kind == "pass_fail"
    assert parte.penalty is None, "una parte de apto/no apto no tiene penalización que enseñar"
    assert parte.score.value == 0, "y no suma puntos"
    assert parte.passed is True, "cinco respuestas erróneas están por debajo del límite de seis"
    assert resultado.total.score.value == 0

    # La otra cara: seis errores suspenden la prueba.
    otro = _conjunto(seeded_settings, preguntas=20, marcar=True)
    servicio2, session2 = _sesion(seeded_settings, otro, parte="ortografia", cantidad=20)
    _responder(servicio2, session2, correctas=14, fallos=6)

    resultado2 = servicio2.finish(session2)
    assert resultado2.parts[0].passed is False
    assert "límite de 6" in (resultado2.parts[0].verdict_note or "")


# --- recálculo con una clave nueva ---------------------------------------------------------------


def test_recalcular_con_una_clave_nueva_conserva_la_puntuacion_anterior(
    seeded_settings: Settings,
) -> None:
    """La sesión no se reescribe: se corrige otra vez y se explica de dónde a dónde cambió."""
    set_id = _conjunto(seeded_settings, preguntas=4, correcta="a")
    servicio = _piezas(seeded_settings)[0]
    cuestiones = _piezas(seeded_settings)[1]
    opposition_id, gc_convocation = _ids(seeded_settings)
    assert gc_convocation is not None
    session = servicio.create_session(
        CreateSessionInput(
            opposition_id=opposition_id,
            mode=SessionMode.PRACTICE,
            sources=(
                SourceInput(
                    question_set_id=set_id,
                    part_code="conocimientos_generales",
                    count=4,
                    include_reserves=False,
                ),
            ),
            convocation_version_id=gc_convocation,
        )
    )
    servicio.start(session.id)
    # Se responde con la «a», que es la correcta en la clave v1.
    _responder(servicio, session.id, correctas=4)
    antes = servicio.finish(session.id)
    assert antes.parts[0].correct == 4
    assert antes.recalculation is None

    # Una clave v2 corrige la respuesta: ahora la buena es la «b» en las cuatro preguntas. Se
    # importa como plantilla suelta (posición y letra), que es para lo que sirve esa vía.
    corregido = cuestiones.import_key_from_text(set_id, "1. b\n2. b\n3. b\n4. b\n")
    assert corregido.applied
    nueva = cuestiones.keys(set_id)[-1]
    aplicada, motivo = cuestiones.activate_key(nueva.id)
    assert aplicada, motivo

    despues = servicio.recalculate(session.id)

    assert despues.parts[0].correct == 0
    assert despues.parts[0].wrong == 4
    assert despues.recalculation is not None
    assert despues.recalculation.previous_total.value == antes.total.score.value
    assert despues.recalculation.changed is True
    assert "cambió de" in despues.recalculation.note
    # La sesión guarda la clave nueva y su etiqueta, para que la pantalla pueda decirlo.
    assert despues.key_label is not None and "plantilla v2" in despues.key_label

    # Y al releer la sesión, la comparación sigue ahí (no se pierde al recargar).
    releído = servicio.result(session.id)
    assert releído.recalculation is not None
    assert releído.recalculation.previous_total.value == antes.total.score.value


def test_recalcular_una_sesion_sin_terminar_se_rechaza(seeded_settings: Settings) -> None:
    set_id = _conjunto(seeded_settings, preguntas=4)
    servicio, session_id = _sesion(
        seeded_settings, set_id, parte="conocimientos_generales", cantidad=3
    )

    with pytest.raises(SessionStateError):
        servicio.recalculate(session_id)
