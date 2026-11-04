"""Pruebas de integración de la importación de preguntas (S06): texto, CSV y plantilla.

Los criterios de aceptación del slice se comprueban aquí, por el camino real:

- **una fila inválida no aborta el lote**: las buenas entran y las malas salen con su causa;
- **sin plantilla, el examen oficial queda sin clave**: las preguntas entran sin desenlace;
- **una negación se conserva**: dos preguntas opuestas no se agrupan como la misma;
- **claves conflictivas no se fusionan**: el grupo lo dice y `can_merge` se queda en falso.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from sqlalchemy import text

from opofuente.application.question_models import CsvColumnMapping
from opofuente.application.question_service import QuestionService
from opofuente.config import Settings
from opofuente.domain.errors import InvariantViolationError, MappingMismatchError
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.migrations import run_migrations
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente_testing.programs import insert_published_program

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)

TEXTO = """1. La Constitucion espanola se aprobo en:
a) 1976
b) 1978
c) 1980
Respuesta correcta: b

2. El plazo de alegaciones es de diez dias habiles.
a) Verdadero
b) Falso
"""

CSV_VALIDO = (
    "stem;option_a;option_b;option_c;correct;explanation;topic\n"
    "El plazo de alegaciones es de diez dias;Verdadero;Falso;;a;Diez dias habiles;I.1\n"
    "El silencio administrativo se regula en;La Ley 39/2015;La Ley 40/2015;;a;;\n"
)

CSV_CON_FILAS_MALAS = (
    "stem;option_a;option_b;correct\n"
    ";Verdadero;Falso;a\n"
    "Pregunta con una sola opcion;Verdadero;;a\n"
    "Pregunta con clave imposible;Verdadero;Falso;z\n"
    "Pregunta correcta;Verdadero;Falso;b\n"
)


class _Reloj:
    def now(self) -> datetime:
        return AHORA


def _servicio(tmp_path: Path) -> tuple[QuestionService, Settings]:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    settings.data_paths.ensure_directories()
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    sesiones = build_session_factory(engine)
    _sembrar(settings)
    repositorio = SqlAlchemyQuestionRepository(sesiones)
    # El servicio necesita además los documentos: importar preguntas **desde un documento**
    # (DEBT-010) lee la versión y sus fragmentos para crear la cita.
    documentos = SqlAlchemyDocumentRepository(sesiones, RepresentationStore(settings.data_paths))
    return QuestionService(repositorio, _Reloj(), documentos), settings


def _sembrar(settings: Settings) -> None:
    """Oposición, convocatoria y un nodo del programa: es lo que necesita una columna `topic`."""
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
            conexion.execute(
                text(
                    "INSERT INTO convocation_versions (id, opposition_id, code, title, "
                    "official_url, published_at, status, created_at, updated_at) VALUES "
                    "('conv-1', 'op-1', 'tai-age-2025', 'Convocatoria TAI', "
                    "'https://www.boe.es/x', :dia, 'active', :ahora, :ahora)"
                ),
                {"dia": date(2025, 12, 22), "ahora": AHORA},
            )
            version_id = insert_published_program(
                conexion, convocation_id="conv-1", convocation_code="tai-age-2025"
            )
            conexion.execute(
                text(
                    "INSERT INTO curriculum_nodes (id, curriculum_version_id, parent_id, "
                    "node_type, official_code, title, position, path, depth) VALUES "
                    "('nodo-1', :version, NULL, 'topic', 'I.1', 'La Constitucion', 1, 'I.1', 1)"
                ),
                {"version": version_id},
            )
    finally:
        engine.dispose()


def _conjunto(
    servicio: QuestionService, *, set_type: str = "private_bank", convocatoria: str | None = None
) -> str:
    vista = servicio.create_set(
        "Examen de prueba",
        opposition_id="op-1",
        set_type=set_type,
        convocation_version_id=convocatoria,
        model_code="A",
    )
    return vista.id


# --- importar texto ----------------------------------------------------------------------------


def test_importar_texto_y_repetirlo_no_duplica_y_no_repite_la_clave(tmp_path: Path) -> None:
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)

    primera = servicio.import_from_text(set_id, TEXTO)
    segunda = servicio.import_from_text(set_id, TEXTO)

    assert (primera.created, primera.existing) == (2, 0)
    assert (segunda.created, segunda.existing) == (0, 2)
    assert primera.key_entries == 1, "solo la primera pregunta traía su clave en el texto"
    assert len(servicio.keys(set_id)) == 1, "la segunda pasada no crea otra plantilla idéntica"


def test_sin_plantilla_en_el_texto_las_preguntas_entran_sin_clave(tmp_path: Path) -> None:
    """Criterio del slice: sin plantilla, el examen queda sin clave… y las preguntas entran."""
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio, set_type="official_exam")

    informe = servicio.import_from_text(
        set_id,
        "1. Pregunta sin clave en el texto:\na) uno\nb) dos\n",
    )

    assert informe.created == 1
    assert informe.key_entries == 0
    assert servicio.keys(set_id) == ()
    pregunta = servicio.questions(set_id=set_id).questions[0]
    assert pregunta.has_key is False
    assert pregunta.correct_option_keys == ()


def test_una_negacion_no_hace_que_dos_preguntas_sean_la_misma(tmp_path: Path) -> None:
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)

    servicio.import_from_text(
        set_id,
        "1. Cual de las siguientes NO es correcta:\na) uno\nb) dos\n"
        "2. Cual de las siguientes es correcta:\na) uno\nb) dos\n",
    )

    assert all(grupo.kind != "same_question" for grupo in servicio.duplicates(set_id)), (
        "dos preguntas opuestas no son la misma pregunta"
    )


def test_dos_preguntas_iguales_con_claves_distintas_no_se_fusionan(tmp_path: Path) -> None:
    """Criterio del slice: la misma pregunta con dos claves distintas se marca, no se junta."""
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)
    servicio.import_from_text(
        set_id, "1. El plazo es de diez dias:\na) Verdadero\nb) Falso\nRespuesta correcta: a\n"
    )
    segundo = servicio.import_from_text(
        set_id, "1. El plazo es de diez dias:\na) Falso\nb) Verdadero\nRespuesta correcta: b\n"
    )

    assert (segundo.created, segundo.existing) == (0, 1), "es la misma pregunta, no se duplica"
    assert len(segundo.conflicts) == 1, "la contradicción se informa"
    pregunta = servicio.questions(set_id=set_id).questions[0]
    assert pregunta.status == "conflicting", "y se ve en la pregunta"
    # La plantilla que ya estaba no se sustituye por otra que la contradice sin decirlo.
    claves = servicio.keys(set_id)
    assert claves
    assert (
        any(entrada.outcome == "conflicting" for clave in claves for entrada in clave.entries)
        or claves[0].entry_count == 1
    )


# --- importar CSV ------------------------------------------------------------------------------


def test_importar_csv_con_mapeo_por_defecto(tmp_path: Path) -> None:
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio, convocatoria="conv-1")

    informe = servicio.import_from_csv(set_id, CSV_VALIDO)

    assert informe.created == 2
    assert informe.rows_rejected == 0
    assert informe.key_entries == 2
    preguntas = servicio.questions(set_id=set_id).questions
    assert all(pregunta.correct_option_keys for pregunta in preguntas)
    primera = next(pregunta for pregunta in preguntas if "plazo" in pregunta.stem)
    assert primera.explanation_count == 1, "la explicación del CSV se guarda"
    assert primera.correct_option_keys == ("a",)


def test_una_fila_mala_no_aborta_el_lote(tmp_path: Path) -> None:
    """El criterio del slice: la fila ilegible se rechaza con su causa y el resto entra."""
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)

    informe = servicio.import_from_csv(set_id, CSV_CON_FILAS_MALAS)

    assert informe.created == 1, "la única fila buena entra"
    assert [fila.cause for fila in informe.rejected] == [
        "no_stem",
        "few_options",
        "key_without_option",
    ]
    assert [fila.row_number for fila in informe.rejected] == [2, 3, 4]
    assert "z" in informe.rejected[2].detail
    assert servicio.questions(set_id=set_id).total == 1


def test_un_mapeo_que_no_esta_en_la_cabecera_se_dice_antes_de_tocar_nada(tmp_path: Path) -> None:
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)

    with pytest.raises(InvariantViolationError):
        servicio.import_from_csv(
            set_id,
            "enunciado;opcion_1;opcion_2\nuno;dos;tres\n",
            mapping=CsvColumnMapping(stem="stem", options=("option_a", "option_b")),
        )
    assert servicio.questions(set_id=set_id).total == 0


def test_una_pregunta_repetida_con_su_clave_no_rompe_el_lote(tmp_path: Path) -> None:
    """Un cuestionario que repite una pregunta no puede tumbar la importación de su clave.

    Antes esto fallaba con `IntegrityError`: la huella reconoce la pregunta repetida y devuelve dos
    veces el mismo identificador, y una clave no admite dos entradas para la misma pregunta. Ahora
    se queda una y el informe cuenta la pregunta una sola vez.
    """
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)
    repetida = (
        "1. El plazo es de diez dias:\n"
        "a) Verdadero\n"
        "b) Falso\n"
        "Respuesta correcta: a\n"
        "\n"
        "2. El plazo es de diez dias:\n"
        "a) Verdadero\n"
        "b) Falso\n"
        "Respuesta correcta: a\n"
    )

    informe = servicio.import_from_text(set_id, repetida)

    assert informe.created == 1, "la segunda es la misma pregunta: no se duplica"
    assert informe.existing == 1
    assert informe.key_entries == 1, "y su clave tiene una sola entrada"
    assert servicio.questions(set_id=set_id).total == 1


def test_el_mapeo_dice_que_campo_hay_que_corregir(tmp_path: Path) -> None:
    """El error viaja con el campo, para que la API pueda responder un 422 señalándolo."""
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)

    with pytest.raises(MappingMismatchError) as sin_enunciado:
        servicio.import_from_csv(
            set_id,
            "enunciado;opcion_1;opcion_2\nuno;dos;tres\n",
            mapping=CsvColumnMapping(stem="stem", options=("opcion_1", "opcion_2")),
        )
    assert sin_enunciado.value.field == "mapping.stem"

    with pytest.raises(MappingMismatchError) as sin_opciones:
        servicio.import_from_csv(
            set_id,
            "enunciado;opcion_1;opcion_2\nuno;dos;tres\n",
            mapping=CsvColumnMapping(stem="enunciado", options=("option_a", "option_b")),
        )
    assert sin_opciones.value.field == "mapping.options"


def test_el_csv_acepta_otras_cabeceras_y_declara_lo_que_no_guarda(tmp_path: Path) -> None:
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)
    mapeo = CsvColumnMapping(
        stem="pregunta",
        options=("a", "b"),
        correct="solucion",
        tags="etiquetas",
    )

    informe = servicio.import_from_csv(
        set_id,
        "pregunta;a;b;solucion;etiquetas\nEl plazo es de diez dias;Verdadero;Falso;1;plazos\n",
        mapping=mapeo,
    )

    assert informe.created == 1
    assert informe.key_entries == 1, "«1» se entiende como la primera opción"
    assert informe.ignored_columns == ("tags",), "lo que no se guarda se declara"
    pregunta = servicio.questions(set_id=set_id).questions[0]
    assert pregunta.correct_option_keys == ("a",)


def test_la_columna_topic_asigna_la_pregunta_a_su_nodo(tmp_path: Path) -> None:
    servicio, settings = _servicio(tmp_path)
    set_id = _conjunto(servicio, convocatoria="conv-1")

    servicio.import_from_csv(
        set_id,
        "stem;option_a;option_b;topic\nLa Constitucion se aprobo en;1976;1978;I.1\n",
    )

    pregunta = servicio.questions(set_id=set_id).questions[0]
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            mapeos = conexion.execute(
                text(
                    "SELECT subject_type, subject_id FROM curriculum_mappings "
                    "WHERE subject_type = 'question_version'"
                )
            ).all()
    finally:
        engine.dispose()
    assert mapeos == [("question_version", pregunta.id)]


# --- plantilla suelta --------------------------------------------------------------------------


def test_una_plantilla_suelta_se_alinea_por_numero(tmp_path: Path) -> None:
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)
    servicio.import_from_text(set_id, TEXTO)

    informe = servicio.import_key_from_text(set_id, "1. b\n2. a\n3. c\n90. b\n")

    assert informe.applied is True
    assert informe.entries == 2, "las dos preguntas del conjunto tienen su desenlace"
    assert informe.unmatched == (3, 90), "las posiciones sin pregunta se informan, no se inventan"
    claves = servicio.keys(set_id)
    # Dos plantillas: la que traía el propio texto (una pregunta con clave) y la que llega aparte.
    assert len(claves) == 2
    ultima = next(clave for clave in claves if clave.id == informe.key_id)
    assert ultima.status == "draft", "una plantilla importada no se activa sola"
    assert ultima.entry_count == 2


def test_activar_una_plantilla_es_aprobarla_y_retira_la_anterior(tmp_path: Path) -> None:
    servicio, _ = _servicio(tmp_path)
    set_id = _conjunto(servicio)
    servicio.import_from_text(set_id, TEXTO)
    primera = servicio.import_key_from_text(set_id, "1. b\n2. a\n")
    assert primera.key_id is not None

    activada, motivo = servicio.activate_key(primera.key_id)
    assert (activada, motivo) == (True, None)
    activa = next(clave for clave in servicio.keys(set_id) if clave.id == primera.key_id)
    assert activa.status == "active"
    assert activa.approved_at is not None, "activar deja la aprobación registrada"

    # Una plantilla **distinta** entra como versión nueva y, al activarla, retira la anterior.
    segunda = servicio.import_key_from_text(set_id, "1. c\n2. b\n")
    assert segunda.key_id is not None and segunda.version_no == 3

    activada, motivo = servicio.activate_key(segunda.key_id)
    assert (activada, motivo) == (True, None)
    estados = {clave.id: clave.status for clave in servicio.keys(set_id)}
    assert estados[primera.key_id] == "superseded"
    assert estados[segunda.key_id] == "active"
    assert sum(1 for estado in estados.values() if estado == "active") == 1
