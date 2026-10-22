"""Pruebas de integración del banco de preguntas (S06) por el camino real.

Lo que se comprueba aquí es lo que no se puede comprobar en una prueba unitaria: que importar dos
veces el mismo texto **no duplica** preguntas, que la clave se guarda con su desenlace y solo se
activa una a la vez, que una clave oficial sin su plantilla oficial no se puede activar, y que la
solución **no** viaja en una respuesta que no la pide (contrato §9).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import text

from opofuente.config import Settings
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.questions import (
    AnswerKeyEntry,
    KeyOutcome,
    Origin,
    parse_questions,
)
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.migrations import run_migrations
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)

TEXTO = """Modelo A

1. La Constitucion espanola se aprobo en:
a) 1976
b) 1978
c) 1980
d) 1982

2. [R] El plazo de alegaciones es de diez dias habiles.
a) Verdadero
b) Falso

3. Marque las expresiones incorrectas:
a) Habian muchos
b) Hubieron problemas
c) Ayer fuimos
"""


def _repositorio(tmp_path: Path) -> tuple[SqlAlchemyQuestionRepository, Settings]:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    settings.data_paths.ensure_directories()
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    sesiones = build_session_factory(engine)
    _sembrar_oposicion(settings)
    return SqlAlchemyQuestionRepository(sesiones), settings


def _sembrar_oposicion(settings: Settings) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) "
                    "VALUES ('op-1', 'tai-age', 'TAI', 1, :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
    finally:
        engine.dispose()


def _documento(settings: Settings, *, version_id: str = "ver-1") -> str:
    """Un documento oficial con su versión: es lo que una clave oficial necesita enlazar."""
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "INSERT INTO source_artifacts (id, sha256, size_bytes, media_type, "
                    "storage_key, first_seen_at) VALUES ('art-1', :sha, 100, 'application/pdf', "
                    "'sha256/aa', :ahora)"
                ),
                {"sha": "a" * 64, "ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO logical_documents (id, canonical_title, document_type, "
                    "owner_scope, created_at, updated_at) VALUES ('doc-1', 'Examen oficial', "
                    "'official_exam', 'private_user', :ahora, :ahora)"
                ),
                {"ahora": AHORA},
            )
            conexion.execute(
                text(
                    "INSERT INTO document_versions (id, logical_document_id, artifact_id, status, "
                    "created_at) VALUES (:version, 'doc-1', 'art-1', 'candidate', :ahora)"
                ),
                {"version": version_id, "ahora": AHORA},
            )
    finally:
        engine.dispose()
    return version_id


def _conjunto(repositorio: SqlAlchemyQuestionRepository, *, set_type: str = "private_bank") -> str:
    vista = repositorio.create_set(
        title="Examen de prueba",
        opposition_id="op-1",
        set_type=set_type,
        now=AHORA,
        model_code="a",
    )
    return vista.id


# --- conjuntos y preguntas ---------------------------------------------------------------------


def test_un_conjunto_sin_titulo_no_entra(tmp_path: Path) -> None:
    repositorio, _ = _repositorio(tmp_path)

    with pytest.raises(InvariantViolationError):
        repositorio.create_set(title="   ", opposition_id="op-1", set_type="practice", now=AHORA)


def test_importar_el_mismo_texto_dos_veces_no_duplica(tmp_path: Path) -> None:
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    parseado = parse_questions(TEXTO)

    primera = repositorio.save_questions(
        set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA
    )
    segunda = repositorio.save_questions(
        set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA
    )

    assert (primera.created, primera.existing) == (3, 0)
    assert (segunda.created, segunda.existing) == (0, 3)
    assert primera.question_ids == segunda.question_ids, "la segunda pasada devuelve las mismas"
    assert repositorio.list_questions(set_id=set_id).total == 3


def test_las_preguntas_guardan_opciones_reservas_y_estado(tmp_path: Path) -> None:
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    parseado = parse_questions(TEXTO)
    repositorio.save_questions(set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA)

    pagina = repositorio.list_questions(set_id=set_id)
    preguntas = {pregunta.position: pregunta for pregunta in pagina.questions}

    primera = preguntas[1]
    assert primera.stable_key == "q001", "la clave estable sale del número de la pregunta"
    assert [opcion.stable_key for opcion in primera.options] == ["a", "b", "c", "d"]
    assert [opcion.label for opcion in primera.options] == ["A", "B", "C", "D"]
    assert primera.status == "complete"
    assert primera.is_reserve is False

    reserva = preguntas[2]
    assert reserva.is_reserve is True
    assert reserva.question_type == "true_false"

    tercera = preguntas[3]
    assert tercera.question_type == "multi_mark_error"

    conjunto = repositorio.get_set(set_id)
    assert conjunto is not None
    assert (conjunto.question_count, conjunto.reserve_count, conjunto.incomplete_count) == (3, 1, 0)
    assert conjunto.model_code == "A"


def test_una_pregunta_incompleta_se_guarda_y_se_cuenta(tmp_path: Path) -> None:
    """Una pregunta sin opciones existe y se puede arreglar: lo que no se hace es esconderla."""
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    parseado = parse_questions("1. Explique el procedimiento administrativo comun.\n")

    resultado = repositorio.save_questions(
        set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA
    )

    assert (resultado.created, resultado.incomplete) == (1, 1)
    pregunta = repositorio.list_questions(set_id=set_id).questions[0]
    assert pregunta.status == "incomplete"
    assert pregunta.options == ()
    conjunto = repositorio.get_set(set_id)
    assert conjunto is not None and conjunto.incomplete_count == 1


def test_dos_preguntas_con_el_mismo_numero_no_rompen_la_clave_estable(tmp_path: Path) -> None:
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    texto = (
        "7. Primera pregunta con numero repetido:\n"
        "a) uno\n"
        "b) dos\n"
        "7. Segunda pregunta con numero repetido:\n"
        "a) tres\n"
        "b) cuatro\n"
    )
    parseado = parse_questions(texto)

    resultado = repositorio.save_questions(
        set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA
    )

    assert resultado.created == 2
    claves = [
        pregunta.stable_key for pregunta in repositorio.list_questions(set_id=set_id).questions
    ]
    assert claves == ["q007", "q007-2"], "la segunda se distingue sin fallar"


# --- claves ------------------------------------------------------------------------------------


def _entradas(repositorio: SqlAlchemyQuestionRepository, set_id: str) -> tuple[AnswerKeyEntry, ...]:
    preguntas = repositorio.list_questions(set_id=set_id).questions
    return tuple(
        AnswerKeyEntry(
            question_version_id=pregunta.id,
            outcome=KeyOutcome.KEYED,
            correct_option_keys=("a",),
        )
        for pregunta in preguntas
    )


def test_la_clave_activa_necesita_aprobacion_y_solo_hay_una(tmp_path: Path) -> None:
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    parseado = parse_questions(TEXTO)
    repositorio.save_questions(set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA)

    clave1 = repositorio.save_key(set_id, entries=_entradas(repositorio, set_id), now=AHORA)
    assert clave1 is not None
    assert clave1.version_no == 1

    activada, motivo = repositorio.activate_key(clave1.id, now=AHORA)
    assert activada is False
    assert motivo == "una clave activa necesita aprobación"

    assert repositorio.approve_key(clave1.id, now=AHORA) is True
    activada, motivo = repositorio.activate_key(clave1.id, now=AHORA)
    assert (activada, motivo) == (True, None)

    clave2 = repositorio.save_key(set_id, entries=_entradas(repositorio, set_id), now=AHORA)
    assert clave2 is not None and clave2.version_no == 2
    repositorio.approve_key(clave2.id, now=AHORA)
    activada, motivo = repositorio.activate_key(clave2.id, now=AHORA)
    assert (activada, motivo) == (True, None)

    estados = {clave.id: clave.status for clave in repositorio.list_keys(set_id)}
    assert estados == {clave1.id: "superseded", clave2.id: "active"}


def test_una_clave_oficial_necesita_la_plantilla_oficial_enlazada(tmp_path: Path) -> None:
    repositorio, settings = _repositorio(tmp_path)
    set_id = _conjunto(repositorio, set_type="official_exam")
    parseado = parse_questions(TEXTO)
    repositorio.save_questions(set_id, parseado.questions, origin_type=Origin.OFFICIAL, now=AHORA)

    sin_fuente = repositorio.save_key(set_id, entries=_entradas(repositorio, set_id), now=AHORA)
    assert sin_fuente is not None
    repositorio.approve_key(sin_fuente.id, now=AHORA)
    activada, motivo = repositorio.activate_key(sin_fuente.id, now=AHORA)
    assert activada is False
    assert motivo == "una clave oficial necesita la plantilla oficial enlazada"

    version = _documento(settings)
    con_fuente = repositorio.save_key(
        set_id,
        entries=_entradas(repositorio, set_id),
        source_document_version_id=version,
        now=AHORA,
    )
    assert con_fuente is not None
    repositorio.approve_key(con_fuente.id, now=AHORA)
    assert repositorio.activate_key(con_fuente.id, now=AHORA) == (True, None)


def test_una_plantilla_con_preguntas_de_otro_conjunto_se_rechaza(tmp_path: Path) -> None:
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    otro = _conjunto(repositorio)
    parseado = parse_questions(TEXTO)
    repositorio.save_questions(set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA)
    ajenas = repositorio.list_questions(set_id=otro)

    with pytest.raises(InvariantViolationError):
        repositorio.save_key(
            set_id,
            entries=(AnswerKeyEntry("pregunta-que-no-es-del-conjunto", KeyOutcome.KEYED, ("a",)),),
            now=AHORA,
        )
    assert ajenas.total == 0


def test_marcar_que_una_clave_sustituye_a_otra(tmp_path: Path) -> None:
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    parseado = parse_questions(TEXTO)
    repositorio.save_questions(set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA)
    primera = repositorio.save_key(set_id, entries=_entradas(repositorio, set_id), now=AHORA)
    segunda = repositorio.save_key(set_id, entries=_entradas(repositorio, set_id), now=AHORA)
    assert primera is not None and segunda is not None

    assert repositorio.mark_key_supersedes(segunda.id, superseded_id=segunda.id, now=AHORA) == (
        False,
        "una plantilla no se sustituye a sí misma",
    )
    assert repositorio.mark_key_supersedes(segunda.id, superseded_id="no-existe", now=AHORA) == (
        False,
        "la plantilla que se dice sustituida no existe",
    )

    aprobada, motivo = repositorio.mark_key_supersedes(
        segunda.id, superseded_id=primera.id, now=AHORA
    )
    assert (aprobada, motivo) == (True, None)
    vista = repositorio.get_key(segunda.id)
    assert vista is not None and vista.supersedes_id == primera.id


def test_la_clave_no_viaja_si_no_se_pide(tmp_path: Path) -> None:
    """Contrato §9: la solución no aparece en la pregunta salvo que quien pregunta la pida."""
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    parseado = parse_questions(TEXTO)
    repositorio.save_questions(set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA)
    preguntas = repositorio.list_questions(set_id=set_id).questions
    clave = repositorio.save_key(
        set_id,
        entries=tuple(
            AnswerKeyEntry(pregunta.id, KeyOutcome.KEYED, ("a",)) for pregunta in preguntas
        ),
        now=AHORA,
    )
    assert clave is not None
    repositorio.approve_key(clave.id, now=AHORA)
    repositorio.activate_key(clave.id, now=AHORA)

    sin_clave = repositorio.list_questions(set_id=set_id).questions[0]
    assert sin_clave.correct_option_keys == ()
    assert sin_clave.key_outcome == "keyed", "que tenga clave sí se sabe; cuál es, no"

    con_clave = repositorio.get_question(sin_clave.id, include_key=True)
    assert con_clave is not None
    assert con_clave.correct_option_keys == ("a",)


def test_los_desenlaces_de_la_clave_activa_se_pueden_leer_para_duplicados(tmp_path: Path) -> None:
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    parseado = parse_questions(TEXTO)
    repositorio.save_questions(set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA)
    preguntas = repositorio.list_questions(set_id=set_id).questions
    clave = repositorio.save_key(
        set_id,
        entries=(
            AnswerKeyEntry(preguntas[0].id, KeyOutcome.KEYED, ("b",)),
            AnswerKeyEntry(preguntas[1].id, KeyOutcome.ANNULLED, ()),
        ),
        now=AHORA,
    )
    assert clave is not None

    # Una plantilla en borrador ya dice lo que propone: en el banco es justo lo que se revisa.
    assert repositorio.keys_of_set(set_id)[preguntas[0].id].correct_option_keys == ("b",)

    repositorio.approve_key(clave.id, now=AHORA)
    repositorio.activate_key(clave.id, now=AHORA)
    desenlaces = repositorio.keys_of_set(set_id)

    assert desenlaces[preguntas[0].id].correct_option_keys == ("b",)
    assert desenlaces[preguntas[1].id].outcome is KeyOutcome.ANNULLED


def test_una_explicacion_privada_no_se_sustituye_por_una_generada(tmp_path: Path) -> None:
    """**El generador no toca lo que escribió una persona.**

    El 22 de octubre una corrida de explicaciones sustituyó 5.368 privadas porque
    `add_explanation` reemplaza por identidad y nadie lo comprobaba. Esta prueba es la que
    impide que vuelva a pasar: con `no_sustituir_lo_privado=True` no sustituye, y sin él sí,
    porque el panel tiene que poder corregir la suya.
    """
    repositorio, _ = _repositorio(tmp_path)
    set_id = _conjunto(repositorio)
    parseado = parse_questions(TEXTO)
    repositorio.save_questions(set_id, parseado.questions, origin_type=Origin.PRIVATE, now=AHORA)
    pregunta = repositorio.list_questions(set_id=set_id).questions[0]

    privada = repositorio.add_explanation(
        pregunta.id, text="La explicación del propietario.", origin=Origin.PRIVATE, now=AHORA
    )
    assert privada is not None

    generada = repositorio.add_explanation(
        pregunta.id,
        text="La que escribió un modelo.",
        origin=Origin.GENERATED,
        now=AHORA,
        no_sustituir_lo_privado=True,
    )
    assert generada is None, "el generador no puede sustituir una explicación privada"

    despues = repositorio.explanations_of(pregunta.id)
    assert len(despues) == 1
    assert despues[0].id == privada
    assert str(despues[0].origin) == str(Origin.PRIVATE), "el origen no cambia"
    assert despues[0].text == "La explicación del propietario."

    corregida = repositorio.add_explanation(
        pregunta.id, text="Corregida por el panel.", origin=Origin.PRIVATE, now=AHORA
    )
    assert corregida == privada, "el panel sí sustituye su propia explicación"
