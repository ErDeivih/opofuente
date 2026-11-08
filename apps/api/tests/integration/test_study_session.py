"""Pruebas de integración de las sesiones de estudio (S07) por el camino real.

Lo que se comprueba aquí es lo que no se puede comprobar en una prueba unitaria, sobre base de
datos de verdad con los perfiles oficiales sembrados:

1. **una sesión se monta con lo que hay**: la composición sale del conjunto, las reservas se
   separan y la clave se congela; sin clave activa no hay sesión, y sin preguntas suficientes
   tampoco;
2. **el examen oficial no admite parámetros libres**: los fija la convocatoria, y si el banco no
   tiene las preguntas de la parte se dice cuántas faltan en lugar de montar medio examen;
3. **la solución no viaja antes de responder**: la pregunta de la sesión no la lleva, y la
   corrección solo aparece cuando el modo lo permite;
4. **el intento se congela y sobrevive a recargar**: reenviar lo mismo no crea otro intento y
   cambiarlo se rechaza;
5. **la puntuación es exacta y por partes**, y la calificación oficial no se declara;
6. **las reservas sustituyen a las anuladas**, con la composición efectiva guardada en el resultado.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from opofuente.application.question_service import QuestionService
from opofuente.application.study_service import (
    AnswerInput,
    CreateSessionInput,
    SourceInput,
    StudyService,
)
from opofuente.config import Settings
from opofuente.domain.errors import (
    AttemptFrozenError,
    ClassificationConflictError,
    InvalidAnswerError,
    NotFoundError,
    SessionStateError,
    UnsupportedError,
)
from opofuente.domain.study import (
    SUPPORTED_MODES,
    Confidence,
    Feedback,
    SessionMode,
    SessionStatus,
)
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente.infrastructure.study_repository import SqlAlchemyStudyRepository

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)


class _Reloj:
    """Reloj fijo: las pruebas no dependen de la hora real."""

    def __init__(self, ahora: datetime = AHORA) -> None:
        self._ahora = ahora

    def now(self) -> datetime:
        return self._ahora


def _texto(preguntas: int, *, reservas: int = 0, correcta: str = "a") -> str:
    """Un cuestionario de prueba: `preguntas` ordinarias, `reservas` con [R] y su clave.

    Todas las preguntas tienen la misma respuesta correcta a propósito: así el resultado se
    calcula a mano en la prueba y lo que se mide es la aritmética del servidor, no la suerte.
    """
    lineas: list[str] = []
    for numero in range(1, preguntas + reservas + 1):
        marca = "[R] " if numero > preguntas else ""
        lineas.append(f"{numero}. {marca}Pregunta numero {numero} del cuestionario de prueba:")
        for indice in range(4):
            lineas.append(f"{chr(ord('a') + indice)}) Opcion {chr(ord('A') + indice)}")
        lineas.append(f"Respuesta correcta: {correcta}")
        lineas.append("")
    return "\n".join(lineas)


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


def _servicio(settings: Settings) -> StudyService:
    return _piezas(settings)[0]


def _cuestiones(settings: Settings) -> QuestionService:
    return _piezas(settings)[1]


def _ids_de_oposicion(settings: Settings, code: str = "tai-age") -> tuple[str, str | None]:
    """Oposición y convocatoria activa de los perfiles sembrados."""
    engine = build_engine(settings.data_paths.database)
    try:
        perfiles = SqlAlchemyProfileRepository(build_session_factory(engine))
        oposicion = next(op for op in perfiles.list_oppositions() if op.code == code)
        return oposicion.id, oposicion.convocation_id
    finally:
        engine.dispose()


def _conjunto_con_clave(
    settings: Settings,
    *,
    preguntas: int,
    reservas: int = 0,
    activar: bool = True,
    set_type: str = "private_bank",
) -> str:
    """Un conjunto con sus preguntas y su clave (activa o en borrador, según se pida).

    El tipo por defecto es banco privado: una clave de un conjunto **oficial** exige plantilla
    oficial enlazada para activarse (ADR-009), y lo que aquí se mide es la sesión, no esa regla.
    """
    cuestiones = _cuestiones(settings)
    opposition_id, convocation_id = _ids_de_oposicion(settings)
    conjunto = cuestiones.create_set(
        "Examen de prueba",
        opposition_id=opposition_id,
        set_type=set_type,
        convocation_version_id=convocation_id,
    )
    cuestiones.import_from_text(conjunto.id, _texto(preguntas, reservas=reservas))
    if activar:
        clave = cuestiones.keys(conjunto.id)[0]
        aplicada, motivo = cuestiones.activate_key(clave.id)
        assert aplicada, motivo
    return conjunto.id


def _practica(
    settings: Settings,
    set_id: str,
    *,
    cantidad: int,
    reservas: bool = False,
    parte: str = "primera_parte",
) -> CreateSessionInput:
    opposition_id, convocation_id = _ids_de_oposicion(settings)
    return CreateSessionInput(
        opposition_id=opposition_id,
        mode=SessionMode.PRACTICE,
        sources=(
            SourceInput(
                question_set_id=set_id,
                part_code=parte,
                count=cantidad,
                include_reserves=reservas,
            ),
        ),
        convocation_version_id=convocation_id,
    )


def _sesion_en_marcha(
    settings: Settings, *, cantidad: int = 4, reservas: bool = False
) -> tuple[StudyService, str]:
    set_id = _conjunto_con_clave(settings, preguntas=cantidad, reservas=2 if reservas else 0)
    servicio = _servicio(settings)
    session = servicio.create_session(
        _practica(settings, set_id, cantidad=cantidad, reservas=reservas)
    )
    return servicio, servicio.start(session.id).id


# --- montar la sesión ---------------------------------------------------------------------------


def test_una_practica_se_monta_con_la_clave_activa_congelada(seeded_settings: Settings) -> None:
    set_id = _conjunto_con_clave(seeded_settings, preguntas=10)
    servicio = _servicio(seeded_settings)

    session = servicio.create_session(_practica(seeded_settings, set_id, cantidad=4))
    arrancada = servicio.start(session.id)

    assert arrancada.status is SessionStatus.RUNNING
    assert arrancada.total_questions == 4
    assert arrancada.answer_key_version_id is not None
    assert arrancada.key_label is not None and "plantilla v1" in arrancada.key_label
    assert servicio.current_question(session.id).question is not None


def test_sin_clave_activa_no_hay_sesion(seeded_settings: Settings) -> None:
    set_id = _conjunto_con_clave(seeded_settings, preguntas=5, activar=False)
    servicio = _servicio(seeded_settings)

    with pytest.raises(ClassificationConflictError):
        servicio.create_session(_practica(seeded_settings, set_id, cantidad=2))


def test_no_se_puede_pedir_mas_preguntas_de_las_que_hay(seeded_settings: Settings) -> None:
    set_id = _conjunto_con_clave(seeded_settings, preguntas=3)
    servicio = _servicio(seeded_settings)

    with pytest.raises(UnsupportedError) as error:
        servicio.create_session(_practica(seeded_settings, set_id, cantidad=10))

    assert "3 preguntas" in str(error.value)
    assert servicio.list_sessions().total == 0, "una sesión imposible no se crea a medias"


def test_un_examen_oficial_toma_sus_parametros_de_la_convocatoria(
    seeded_settings: Settings,
) -> None:
    """La parte oficial pide 80 preguntas: con 5 en el banco, se dice cuántas faltan."""
    set_id = _conjunto_con_clave(seeded_settings, preguntas=5)
    servicio = _servicio(seeded_settings)
    opposition_id, convocation_id = _ids_de_oposicion(seeded_settings)
    assert convocation_id is not None

    with pytest.raises(UnsupportedError) as error:
        servicio.create_session(
            CreateSessionInput(
                opposition_id=opposition_id,
                mode=SessionMode.OFFICIAL_EXAM,
                sources=(SourceInput(question_set_id=set_id, part_code="primera_parte"),),
                convocation_version_id=convocation_id,
            )
        )

    assert "80" in str(error.value) and "faltan" in str(error.value)
    assert servicio.list_sessions().total == 0

    # Y sin contar con las reservas tampoco: el examen oficial pide las 5 de la convocatoria.
    set_completo = _conjunto_con_clave(seeded_settings, preguntas=80)
    with pytest.raises(UnsupportedError) as error_reservas:
        servicio.create_session(
            CreateSessionInput(
                opposition_id=opposition_id,
                mode=SessionMode.OFFICIAL_EXAM,
                sources=(SourceInput(question_set_id=set_completo, part_code="primera_parte"),),
                convocation_version_id=convocation_id,
            )
        )
    assert "reservas" in str(error_reservas.value)


def test_un_examen_oficial_completo_se_monta_con_el_tiempo_del_grupo(
    seeded_settings: Settings,
) -> None:
    """Con las 80 preguntas y sus 5 reservas, el examen se monta y el tiempo lo pone el grupo."""
    set_id = _conjunto_con_clave(seeded_settings, preguntas=80, reservas=5)
    servicio = _servicio(seeded_settings)
    opposition_id, convocation_id = _ids_de_oposicion(seeded_settings)
    assert convocation_id is not None

    session = servicio.create_session(
        CreateSessionInput(
            opposition_id=opposition_id,
            mode=SessionMode.OFFICIAL_EXAM,
            sources=(SourceInput(question_set_id=set_id, part_code="primera_parte"),),
            convocation_version_id=convocation_id,
        )
    )

    assert session.total_questions == 85, "80 ordinarias y las 5 reservas de la convocatoria"
    assert session.time_limit_minutes == 120, "los 120 minutos del ejercicio único"
    assert session.feedback is Feedback.AT_END, "un examen no corrige mientras se hace"

    # Un examen oficial no admite parámetros libres: los fija la convocatoria.
    with pytest.raises(UnsupportedError):
        servicio.create_session(
            CreateSessionInput(
                opposition_id=opposition_id,
                mode=SessionMode.OFFICIAL_EXAM,
                sources=(SourceInput(question_set_id=set_id, part_code="primera_parte", count=10),),
                convocation_version_id=convocation_id,
                time_limit_minutes=30,
            )
        )


def test_todo_modo_del_vocabulario_esta_construido(seeded_settings: Settings) -> None:
    """Los seis modos de 06_QUESTIONS §5 y B-017 están implementados (DEBT-012, cerrada).

    Esta prueba sustituye a la que comprobaba que un modo sin implementar se rechazaba: ya no hay
    ninguno sin implementar. Lo que se comprueba ahora es que el conjunto de modos construidos es el
    vocabulario **entero**; si alguien declara un séptimo modo sin construirlo, esta prueba falla
    en vez de dejar que el guardia de `create_session` tenga que rechazarlo con un 409.
    """
    assert set(SUPPORTED_MODES) == set(SessionMode)
    assert len(SUPPORTED_MODES) == 6


def test_las_partes_que_no_son_una_parte_se_rechazan(seeded_settings: Settings) -> None:
    """Un grupo de partes no es una parte: la sesión se monta sobre partes con preguntas."""
    set_id = _conjunto_con_clave(seeded_settings, preguntas=5)
    servicio = _servicio(seeded_settings)
    opposition_id, _ = _ids_de_oposicion(seeded_settings)

    with pytest.raises(NotFoundError):
        servicio.create_session(
            CreateSessionInput(
                opposition_id=opposition_id,
                mode=SessionMode.PRACTICE,
                sources=(SourceInput(question_set_id=set_id, part_code="no-existe"),),
            )
        )
    with pytest.raises(UnsupportedError, match="agrupa partes"):
        servicio.create_session(
            CreateSessionInput(
                opposition_id=opposition_id,
                mode=SessionMode.PRACTICE,
                sources=(SourceInput(question_set_id=set_id, part_code="ejercicio_unico"),),
            )
        )


# --- responder ----------------------------------------------------------------------------------


def test_la_pregunta_de_la_sesion_no_lleva_la_solucion(seeded_settings: Settings) -> None:
    """El criterio del contrato §10: ni la clave ni la explicación antes de responder."""
    servicio, session_id = _sesion_en_marcha(seeded_settings)

    actual = servicio.current_question(session_id)

    assert actual.question is not None
    assert actual.question.correction is None
    assert not hasattr(actual.question, "correct_option_keys")
    assert [opcion.stable_key for opcion in actual.question.options] == ["a", "b", "c", "d"]


def test_responder_corrige_y_el_intento_queda_congelado(seeded_settings: Settings) -> None:
    servicio, session_id = _sesion_en_marcha(seeded_settings)
    actual = servicio.current_question(session_id)
    assert actual.question is not None

    respuesta = servicio.answer(
        session_id,
        AnswerInput(
            question_version_id=actual.question.question_version_id,
            chosen_option_keys=("b",),
            elapsed_ms=4200,
            confidence=Confidence.LOW,
            client_sequence=1,
        ),
    )

    assert respuesta.saved is True
    assert respuesta.already_answered is False
    assert respuesta.correction is not None
    assert respuesta.correction.outcome == "wrong"
    assert respuesta.correction.correct_option_keys == ("a",), "al corregir sí se dice cuál era"
    # La penalización se guarda exacta: un tercio, no un decimal.
    assert respuesta.correction.score.fraction == "-1/3"
    assert respuesta.correction.score.decimal == "-0.3333"

    # Recargar y reenviar lo mismo no crea otro intento (criterio de aceptación de S07).
    repetida = servicio.answer(
        session_id,
        AnswerInput(
            question_version_id=actual.question.question_version_id,
            chosen_option_keys=("b",),
            elapsed_ms=99,
        ),
    )
    assert repetida.saved is False
    assert repetida.already_answered is True
    assert repetida.attempt.id == respuesta.attempt.id

    # Y cambiar la respuesta no se admite: el intento se congela al registrarlo.
    with pytest.raises(AttemptFrozenError):
        servicio.answer(
            session_id,
            AnswerInput(
                question_version_id=actual.question.question_version_id,
                chosen_option_keys=("a",),
                elapsed_ms=10,
            ),
        )


def test_una_opcion_que_no_existe_se_rechaza_con_su_campo(seeded_settings: Settings) -> None:
    servicio, session_id = _sesion_en_marcha(seeded_settings)
    actual = servicio.current_question(session_id)
    assert actual.question is not None

    with pytest.raises(InvalidAnswerError):
        servicio.answer(
            session_id,
            AnswerInput(
                question_version_id=actual.question.question_version_id,
                chosen_option_keys=("z",),
                elapsed_ms=10,
            ),
        )
    with pytest.raises(InvalidAnswerError, match="una sola respuesta"):
        servicio.answer(
            session_id,
            AnswerInput(
                question_version_id=actual.question.question_version_id,
                chosen_option_keys=("a", "b"),
                elapsed_ms=10,
            ),
        )


def test_una_pregunta_de_otra_sesion_no_se_puede_responder_aqui(seeded_settings: Settings) -> None:
    servicio, session_id = _sesion_en_marcha(seeded_settings)

    with pytest.raises(NotFoundError):
        servicio.answer(
            session_id,
            AnswerInput(
                question_version_id="no-es-de-esta-sesion",
                chosen_option_keys=("a",),
                elapsed_ms=10,
            ),
        )


def test_no_se_responde_una_sesion_que_no_esta_en_marcha(seeded_settings: Settings) -> None:
    set_id = _conjunto_con_clave(seeded_settings, preguntas=4)
    servicio = _servicio(seeded_settings)
    session = servicio.create_session(_practica(seeded_settings, set_id, cantidad=2))
    actual = servicio.current_question(session.id)
    assert actual.question is not None

    assert session.status is SessionStatus.DRAFT
    with pytest.raises(SessionStateError):
        servicio.answer(
            session.id,
            AnswerInput(
                question_version_id=actual.question.question_version_id,
                chosen_option_keys=("a",),
                elapsed_ms=10,
            ),
        )
    with pytest.raises(SessionStateError):
        servicio.finish(session.id)


def test_la_navegacion_recorre_las_preguntas_y_no_se_sale(seeded_settings: Settings) -> None:
    servicio, session_id = _sesion_en_marcha(seeded_settings, cantidad=3)

    primera = servicio.current_question(session_id)
    segunda = servicio.navigate(session_id, direction="next")
    otra_vez_primera = servicio.navigate(session_id, direction="previous")

    assert primera.question is not None and segunda.question is not None
    assert primera.question.position == 1
    assert segunda.question.position == 2
    assert otra_vez_primera.question is not None
    assert otra_vez_primera.question.position == 1

    with pytest.raises(NotFoundError):
        servicio.navigate(session_id, position=9)
    with pytest.raises(UnsupportedError):
        servicio.navigate(session_id)


# --- resultado ----------------------------------------------------------------------------------


def _responder_todas(
    servicio: StudyService,
    session_id: str,
    *,
    vacias: tuple[int, ...] = (),
    mal: tuple[int, ...] = (),
) -> None:
    """Responde todas las preguntas: «a» acierta, «b» falla y las de `vacias` van en blanco."""
    total = servicio.session(session_id).total_questions
    for posicion in range(1, total + 1):
        if posicion in vacias:
            claves: tuple[str, ...] = ()
        elif posicion in mal:
            claves = ("b",)
        else:
            claves = ("a",)
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


def test_el_resultado_separa_partes_fallos_y_blancos_y_no_inventa_la_oficial(
    seeded_settings: Settings,
) -> None:
    """Caso calculado a mano: 2 aciertos, 1 fallo y 1 blanco con penalización de un tercio."""
    servicio, session_id = _sesion_en_marcha(seeded_settings, cantidad=4)
    _responder_todas(servicio, session_id, vacias=(1,), mal=(2,))

    resultado = servicio.finish(session_id)

    assert resultado.total.correct == 2
    assert resultado.total.wrong == 1
    assert resultado.total.blank == 1
    assert resultado.total.score.fraction == "5/3", "2 aciertos menos un tercio"
    assert resultado.total.score.decimal == "1.6667"
    assert len(resultado.parts) == 1
    assert resultado.parts[0].part_code == "primera_parte"
    assert resultado.parts[0].part_name is not None
    assert resultado.parts[0].pass_score == 25.0
    assert resultado.parts[0].official_available is False
    assert resultado.official_available is False
    assert resultado.official_note is not None
    assert "no se declara aprobado ni suspenso" in resultado.official_note

    # El resultado queda guardado con su composición efectiva y se vuelve a leer tal cual.
    guardado = servicio.result(session_id)
    assert guardado.total == resultado.total
    assert guardado.calculated_at == servicio.session(session_id).finished_at


def test_terminar_dos_veces_devuelve_el_mismo_resultado(seeded_settings: Settings) -> None:
    servicio, session_id = _sesion_en_marcha(seeded_settings, cantidad=2)
    _responder_todas(servicio, session_id)

    primera = servicio.finish(session_id)
    otra_vez = servicio.finish(session_id)

    assert otra_vez.session_id == session_id
    assert otra_vez.total == primera.total
    assert servicio.review(session_id).pending == 0


def test_una_sesion_sin_terminar_no_tiene_resultado(seeded_settings: Settings) -> None:
    servicio, session_id = _sesion_en_marcha(seeded_settings, cantidad=2)

    with pytest.raises(SessionStateError):
        servicio.result(session_id)


def test_la_revision_ensena_lo_respondido_y_avisa_de_lo_pendiente(
    seeded_settings: Settings,
) -> None:
    servicio, session_id = _sesion_en_marcha(seeded_settings, cantidad=3)
    actual = servicio.current_question(session_id)
    assert actual.question is not None
    servicio.answer(
        session_id,
        AnswerInput(
            question_version_id=actual.question.question_version_id,
            chosen_option_keys=("a",),
            elapsed_ms=500,
        ),
    )

    revision = servicio.review(session_id)

    assert revision.partial is True
    assert revision.pending == 0, "con corrección inmediata, lo respondido ya se puede corregir"
    assert revision.unanswered == 2
    respondidas = [entrada for entrada in revision.entries if entrada.answered]
    assert len(respondidas) == 1
    assert respondidas[0].correction is not None
    assert respondidas[0].correction.outcome == "correct"


def test_con_correccion_al_final_no_se_ve_nada_hasta_terminar(seeded_settings: Settings) -> None:
    """Un examen no filtra la solución mientras se hace: es la regla que protege el examen."""
    set_id = _conjunto_con_clave(seeded_settings, preguntas=4)
    servicio = _servicio(seeded_settings)
    opposition_id, convocation_id = _ids_de_oposicion(seeded_settings)
    assert convocation_id is not None
    session = servicio.create_session(
        CreateSessionInput(
            opposition_id=opposition_id,
            mode=SessionMode.PRACTICE,
            sources=(SourceInput(question_set_id=set_id, part_code="primera_parte", count=3),),
            convocation_version_id=convocation_id,
            feedback=Feedback.AT_END,
        )
    )
    servicio.start(session.id)
    actual = servicio.current_question(session.id)
    assert actual.question is not None

    respuesta = servicio.answer(
        session.id,
        AnswerInput(
            question_version_id=actual.question.question_version_id,
            chosen_option_keys=("a",),
            elapsed_ms=500,
        ),
    )

    assert respuesta.correction is None, "con corrección al final no se enseña nada al responder"
    pendiente = servicio.review(session.id)
    assert pendiente.pending == 1, "lo respondido espera a que la sesión termine"
    assert pendiente.unanswered == 2
    assert pendiente.note is not None

    servicio.finish(session.id)
    revision = servicio.review(session.id)

    assert revision.pending == 0
    assert revision.note is None
    assert all(entrada.correction is not None for entrada in revision.entries if entrada.answered)


# --- reservas -----------------------------------------------------------------------------------


def test_una_reserva_contestada_no_cuenta_si_no_se_anula_ninguna(seeded_settings: Settings) -> None:
    """La convocatoria valora las reservas solo si se anula alguna ordinaria."""
    servicio, session_id = _sesion_en_marcha(seeded_settings, cantidad=2, reservas=True)
    vistas = servicio.review(session_id).entries
    assert len(vistas) == 4, "2 ordinarias y 2 reservas"

    _responder_todas(servicio, session_id)
    resultado = servicio.finish(session_id)

    assert resultado.total.reserves_used == 0
    assert resultado.total.unused_reserves == 2
    assert resultado.substitutions == ()
    assert resultado.total.graded == 2, "solo cuentan las ordinarias"
    assert resultado.total.correct == 2


def test_una_pregunta_anulada_la_sustituye_la_primera_reserva(seeded_settings: Settings) -> None:
    """Se anula una ordinaria en la clave congelada y el resultado dice qué reserva entra."""
    servicio, session_id = _sesion_en_marcha(seeded_settings, cantidad=2, reservas=True)
    vistas = servicio.review(session_id).entries
    anulada = vistas[0].question_version_id
    _anular_en_la_sesion(seeded_settings, session_id, anulada)

    _responder_todas(servicio, session_id)
    resultado = servicio.finish(session_id)

    assert resultado.total.annulled == 0, "la anulada sale del cálculo al ser sustituida"
    assert resultado.total.reserves_used == 1
    assert resultado.total.unused_reserves == 1
    assert len(resultado.substitutions) == 1
    sustitucion = resultado.substitutions[0]
    assert sustitucion.annulled_question_version_id == anulada
    assert sustitucion.reserve_question_version_id is not None
    assert resultado.total.graded == 2, "una ordinaria y la reserva que la sustituye"


def _anular_en_la_sesion(settings: Settings, session_id: str, question_version_id: str) -> None:
    """Anula una pregunta en la **clave congelada** de la sesión.

    Se hace por SQL a propósito: lo que decide la corrección es la clave congelada, y este es el
    efecto que una clave v2 anulando tendría (la reevaluación completa es S08).
    """
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "UPDATE session_questions SET key_outcome = 'annulled', "
                    "correct_option_keys_json = '[]' "
                    "WHERE session_id = :sesion AND question_version_id = :pregunta"
                ),
                {"sesion": session_id, "pregunta": question_version_id},
            )
    finally:
        engine.dispose()
