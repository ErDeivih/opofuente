"""Dominio de preguntas (S06): normalización, duplicados y parser, sin base de datos.

Lo que se prueba aquí es lo que sostiene los criterios de aceptación del slice:

1. **una fila mala no aborta el lote**: el parser informa la incidencia y sigue con las demás;
2. **las negaciones se conservan**: «¿cuál NO es correcta?» no es la misma pregunta que «¿cuál es
   correcta?», y la normalización no puede hacerlas parecer iguales;
3. **claves conflictivas no se fusionan**: dos preguntas idénticas con claves distintas se agrupan,
   pero el grupo dice que hay conflicto y no se puede fusionar;
4. **sin plantilla, un examen oficial queda sin clave**: `can_activate` lo explica con palabras.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from opofuente.domain.questions import (
    REORDERED_OPTIONS,
    SAME_QUESTION,
    SIMILAR_QUESTION,
    AnswerKeyEntry,
    AnswerKeyVersion,
    KeyOutcome,
    KeyStatus,
    OptionVersion,
    Origin,
    QuestionSet,
    QuestionStatus,
    QuestionType,
    QuestionVersion,
    SetType,
    ano_del_titulo,
    can_activate,
    find_question_duplicates,
    mostrar_huecos,
    parse_answer_key,
    parse_questions,
    parse_questions_json,
    question_fingerprint,
    same_options_in_other_order,
    strip_markdown_decoration,
    strip_numbering,
    strip_option_label,
)

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)

TEXTO = """Modelo A

1. La Constitucion espanola se aprobo en:
a) 1976
b) 1978
c) 1980
d) 1982
Respuesta correcta: b

2. [R] El plazo de alegaciones es de diez dias habiles.
a) Verdadero
b) Falso
Solución: a

3. Marque las expresiones incorrectas del siguiente texto:
a) Habian muchos
b) Hubieron problemas
c) Ayer fuimos
Correcta: b
"""


def _pregunta(
    id_: str,
    stem: str,
    opciones: tuple[str, ...],
    *,
    stable_key: str | None = None,
    origen: Origin = Origin.PRIVATE,
    tipo: QuestionType = QuestionType.SINGLE_CHOICE,
) -> QuestionVersion:
    return QuestionVersion(
        id=id_,
        question_set_id="set-1",
        stable_key=stable_key or id_,
        version_no=1,
        stem=stem,
        question_type=tipo,
        position=1,
        origin_type=origen,
        status=QuestionStatus.COMPLETE,
        options=tuple(
            OptionVersion(
                id=f"{id_}-{posicion}",
                question_version_id=id_,
                stable_key=letra,
                text=texto,
                position=posicion,
                label=letra.upper(),
            )
            for posicion, (letra, texto) in enumerate(
                zip(("a", "b", "c", "d"), opciones, strict=False), start=1
            )
        ),
    )


# --- normalización: la numeración y las etiquetas se quitan, las palabras no -------------------


def test_la_normalizacion_quita_numeracion_y_etiquetas_pero_no_palabras() -> None:
    assert strip_numbering("12. La Constitucion espanola") == "La Constitucion espanola"
    assert strip_numbering("Pregunta 7.- El plazo") == "El plazo"
    assert strip_numbering("Sin numero") == "Sin numero"
    assert strip_option_label("b) 1978") == "1978"
    assert strip_option_label("(C) Ayer fuimos") == "Ayer fuimos"
    assert strip_option_label("Sin etiqueta") == "Sin etiqueta"


def test_una_negacion_no_desaparece_al_normalizar() -> None:
    """El «no» cambia lo que se pregunta: si la normalización se lo comiera, serían la misma."""
    con_negacion = question_fingerprint("¿Cual de las siguientes NO es correcta?", ("uno", "dos"))
    sin_negacion = question_fingerprint("¿Cual de las siguientes es correcta?", ("uno", "dos"))

    assert con_negacion.stem_key != sin_negacion.stem_key
    assert "no" in con_negacion.stem_key.split()
    # Se pueden **señalar** como parecidas —para que una persona las mire—, pero nunca son la misma
    # pregunta ni se pueden fusionar: eso es lo que impide que la respuesta se dé la vuelta.
    grupos = find_question_duplicates(
        (
            _pregunta("q1", "¿Cual de las siguientes NO es correcta?", ("uno", "dos")),
            _pregunta("q2", "¿Cual de las siguientes es correcta?", ("uno", "dos")),
        )
    )
    assert all(grupo.kind != SAME_QUESTION for grupo in grupos)
    assert all(grupo.can_merge is False for grupo in grupos)


def test_numeracion_tildes_y_espacios_no_cambian_la_huella() -> None:
    izquierda = question_fingerprint("1. La Constitución española se aprobó en:", ("1976", "1978"))
    derecha = question_fingerprint(
        "Pregunta 9 - la constitucion espanola se aprobo en:", ("1978", "1976")
    )

    assert izquierda.stem_key == derecha.stem_key
    # Y el conjunto de opciones tampoco depende del orden: es el modelo A/B de la misma pregunta.
    assert izquierda.options_key == derecha.options_key


def test_las_mismas_opciones_en_otro_orden_se_reconocen() -> None:
    assert same_options_in_other_order(("uno", "dos"), ("dos", "uno")) is True
    assert same_options_in_other_order(("uno", "dos"), ("uno", "dos")) is False
    assert same_options_in_other_order(("uno", "dos"), ("uno", "tres")) is False


# --- duplicados --------------------------------------------------------------------------------


def test_la_misma_pregunta_se_agrupa_y_sin_claves_en_conflicto_se_puede_fusionar() -> None:
    repetidas = (
        _pregunta("q1", "El plazo es de:", ("diez dias", "veinte dias")),
        _pregunta("q2", "2. El plazo es de:", ("veinte dias", "diez dias")),
    )
    claves = {
        "q1": AnswerKeyEntry("q1", KeyOutcome.KEYED, ("a",)),
        "q2": AnswerKeyEntry("q2", KeyOutcome.KEYED, ("b",)),
    }

    grupos = find_question_duplicates(repetidas, keys=claves)

    assert len(grupos) == 1
    grupo = grupos[0]
    assert grupo.kind == REORDERED_OPTIONS, "las mismas opciones en otro orden son el modelo A/B"
    assert set(grupo.members) == {"q1", "q2"}
    # Las claves no se contradicen aunque las letras cambien: `a` en el modelo A es `b` en el B.
    assert grupo.conflicting_keys is False
    assert grupo.can_merge is False, "solo se fusiona lo que es la misma pregunta sin reordenar"


def test_dos_preguntas_iguales_con_claves_distintas_no_se_pueden_fusionar() -> None:
    """Criterio del slice: dos claves en conflicto no se juntan solas."""
    repetidas = (
        _pregunta("q1", "El plazo es de diez dias habiles.", ("Verdadero", "Falso")),
        _pregunta("q2", "1. El plazo es de diez dias habiles.", ("Verdadero", "Falso")),
    )
    claves = {
        "q1": AnswerKeyEntry("q1", KeyOutcome.KEYED, ("a",)),
        "q2": AnswerKeyEntry("q2", KeyOutcome.KEYED, ("b",)),
    }

    grupos = find_question_duplicates(repetidas, keys=claves)

    assert len(grupos) == 1
    assert grupos[0].kind == SAME_QUESTION
    assert grupos[0].conflicting_keys is True
    # La firma de una clave es el **texto** de la respuesta, no su letra: aquí se ve que se
    # contradicen («verdadero» frente a «falso») y no un «a» frente a un «b», que no dice nada.
    assert grupos[0].keys_seen == ("falso", "verdadero")
    assert grupos[0].can_merge is False, "un conflicto de claves no se resuelve fusionando"


def test_una_anulada_frente_a_una_con_clave_tambien_es_conflicto() -> None:
    repetidas = (
        _pregunta("q1", "El plazo es de diez dias.", ("uno", "dos")),
        _pregunta("q2", "El plazo es de diez dias.", ("uno", "dos")),
    )
    claves = {
        "q1": AnswerKeyEntry("q1", KeyOutcome.KEYED, ("a",)),
        "q2": AnswerKeyEntry("q2", KeyOutcome.ANNULLED, ()),
    }

    grupos = find_question_duplicates(repetidas, keys=claves)

    assert grupos[0].conflicting_keys is True
    assert grupos[0].keys_seen == ("annulled", "uno")


def test_un_enunciado_muy_parecido_solo_se_senala() -> None:
    larga = (
        "La Ley 39/2015 regula el procedimiento administrativo comun de las administraciones "
        "publicas y el silencio administrativo en los plazos de alegaciones"
    )
    parecida = larga.replace("alegaciones", "reclamaciones")
    grupos = find_question_duplicates(
        (
            _pregunta("q1", larga, ("uno", "dos")),
            _pregunta("q2", parecida, ("uno", "dos")),
        )
    )

    assert grupos
    assert all(grupo.kind == SIMILAR_QUESTION for grupo in grupos)
    assert all(grupo.can_merge is False for grupo in grupos), "parecerse no es ser la misma"


# --- parser de preguntas -----------------------------------------------------------------------


def test_el_parser_lee_enunciados_opciones_claves_y_reservas() -> None:
    resultado = parse_questions(TEXTO)

    assert [pregunta.number for pregunta in resultado.questions] == [1, 2, 3]
    primera = resultado.questions[0]
    assert primera.stem == "La Constitucion espanola se aprobo en:"
    assert [opcion.stable_key for opcion in primera.options] == ["a", "b", "c", "d"]
    assert [opcion.position for opcion in primera.options] == [1, 2, 3, 4]
    assert primera.correct_option_keys == ("b",)
    assert primera.question_type is QuestionType.SINGLE_CHOICE

    # La reserva se marca y **no** se cuela en el enunciado.
    segunda = resultado.questions[1]
    assert segunda.is_reserve is True
    assert "R]" not in segunda.stem
    assert segunda.stem.startswith("El plazo de alegaciones")
    assert segunda.question_type is QuestionType.TRUE_FALSE
    assert segunda.type_reason is not None

    # «Marque las expresiones incorrectas» es un tipo distinto, y el motivo lo dice.
    tercera = resultado.questions[2]
    assert tercera.question_type is QuestionType.MULTI_MARK_ERROR
    assert tercera.correct_option_keys == ("b",)

    assert resultado.model_code == "A"
    assert resultado.with_key == 3
    assert resultado.incomplete == 0
    assert resultado.reserves == 1
    assert [incidencia.code for incidencia in resultado.issues] == [], resultado.issues


CUESTIONARIO_MARKDOWN = """## Tema 5. Los plazos

**1.** El plazo del procedimiento es de:
- a) diez días
- b) veinte días
- c) treinta días
**Respuesta correcta: a**

2. La Ley 39/2015 se aplica a:
a) todo el sector público
b) nadie
Respuesta correcta: b
"""


def test_un_cuestionario_en_markdown_se_lee_igual_que_uno_en_texto() -> None:
    """El adorno de Markdown no es contenido: `**Respuesta correcta: a**` dice lo mismo.

    Sin esto, un cuestionario en Markdown entraba con las preguntas sin opciones («orphan
    option») y sin clave, porque la línea de la clave empieza por `**` y las opciones por `- `.
    """
    resultado = parse_questions(CUESTIONARIO_MARKDOWN)

    assert [pregunta.number for pregunta in resultado.questions] == [1, 2]
    primera = resultado.questions[0]
    assert primera.stem == "El plazo del procedimiento es de:"
    assert [opcion.text for opcion in primera.options] == [
        "diez días",
        "veinte días",
        "treinta días",
    ]
    assert primera.correct_option_keys == ("a",)
    segunda = resultado.questions[1]
    assert segunda.correct_option_keys == ("b",)
    assert resultado.with_key == 2
    # El encabezado de Markdown es estructura: no se informa como texto suelto.
    assert [incidencia.code for incidencia in resultado.issues] == [], resultado.issues


def test_el_adorno_de_markdown_se_quita_sin_tocar_las_palabras() -> None:
    assert strip_markdown_decoration("**Respuesta correcta: b**") == "Respuesta correcta: b"
    assert strip_markdown_decoration("## Tema 5") == "Tema 5"
    assert strip_markdown_decoration("> cita textual") == "cita textual"
    assert strip_markdown_decoration("- a) diez días") == "a) diez días"
    assert strip_markdown_decoration("1. La Ley 39/2015 **es** de 2015") == (
        "1. La Ley 39/2015 es de 2015"
    )
    # El énfasis simple no se toca: un guion bajo separa palabras y un asterisco puede ser una nota.
    assert strip_markdown_decoration("archivo_final.txt") == "archivo_final.txt"


def test_una_fila_mala_no_aborta_el_lote() -> None:
    """Criterio del slice: lo que no se entiende se informa y el resto se sigue leyendo."""
    texto = (
        "Texto de cabecera que no es una pregunta\n"
        "b) opcion suelta sin enunciado\n"
        "1. Primera pregunta correcta:\n"
        "a) uno\n"
        "b) dos\n"
        "Solución: c\n"
        "2. Segunda pregunta correcta:\n"
        "a) uno\n"
        "3. Tercera pregunta correcta:\n"
        "a) uno\n"
        "b) dos\n"
    )

    resultado = parse_questions(texto)

    assert len(resultado.questions) == 3, "las tres preguntas se leen aunque haya ruido"
    codigos = [incidencia.code for incidencia in resultado.issues]
    assert codigos == ["text_outside_question", "orphan_option", "few_options"]
    # La clave del bloque 1 apunta a una opción que no existe: se lee, no se inventa.
    assert resultado.questions[0].correct_option_keys == ("c",)
    assert resultado.questions[1].is_complete is False
    assert resultado.questions[2].is_complete is True


def test_un_texto_sin_preguntas_lo_dice() -> None:
    resultado = parse_questions("Solo hay prosa suelta en este fichero.")

    assert resultado.questions == ()
    assert [incidencia.code for incidencia in resultado.issues] == [
        "text_outside_question",
        "no_questions",
    ]


def test_sin_opciones_la_pregunta_es_de_referencia() -> None:
    resultado = parse_questions("1. Explique el procedimiento administrativo comun.\n")

    assert len(resultado.questions) == 1
    assert resultado.questions[0].question_type is QuestionType.FREE_TEXT_REFERENCE
    assert resultado.questions[0].options == ()
    assert resultado.questions[0].is_complete is False, "sin opciones no está entera"


def test_una_linea_de_continuacion_se_une_a_su_opcion() -> None:
    texto = (
        "1. Pregunta con opciones largas:\n"
        "a) una opcion que sigue\n"
        "en la linea siguiente\n"
        "b) otra opcion\n"
    )

    resultado = parse_questions(texto)

    assert resultado.questions[0].options[0].text == "una opcion que sigue en la linea siguiente"
    assert resultado.questions[0].options[1].text == "otra opcion"


# --- parser de plantillas ----------------------------------------------------------------------


def test_el_parser_de_plantillas_lee_claves_anuladas_y_sin_responder() -> None:
    texto = "1. b\n2-a\n3 anulada\n4 sin responder\n5. c, d\nbasura sin numero\n"

    lineas, incidencias = parse_answer_key(texto)

    assert [(linea.position, linea.outcome) for linea in lineas] == [
        (1, KeyOutcome.KEYED),
        (2, KeyOutcome.KEYED),
        (3, KeyOutcome.ANNULLED),
        (4, KeyOutcome.UNANSWERED),
        (5, KeyOutcome.KEYED),
    ]
    assert lineas[0].correct_option_keys == ("b",)
    assert lineas[4].correct_option_keys == ("c", "d")
    assert [incidencia.code for incidencia in incidencias] == ["key_line_unreadable"]


def test_una_linea_de_plantilla_sin_opcion_se_informa() -> None:
    lineas, incidencias = parse_answer_key("1. ?\n")

    assert lineas == ()
    assert [incidencia.code for incidencia in incidencias] == ["key_line_without_option"]


# --- claves: cuándo se puede activar una plantilla ---------------------------------------------


def _conjunto(tipo: SetType) -> QuestionSet:
    return QuestionSet(id="set-1", title="Examen", opposition_id="op-1", set_type=tipo)


def _clave(**campos: object) -> AnswerKeyVersion:
    datos: dict[str, object] = {
        "id": "key-1",
        "question_set_id": "set-1",
        "version_no": 1,
        "status": KeyStatus.DRAFT,
        "approved_at": None,
        "source_document_version_id": None,
    }
    datos.update(campos)
    return AnswerKeyVersion(**datos)  # type: ignore[arg-type]


def test_una_clave_oficial_sin_plantilla_oficial_no_se_puede_activar() -> None:
    puede, motivo = can_activate(_conjunto(SetType.OFFICIAL_EXAM), _clave(approved_at=AHORA))

    assert puede is False
    assert motivo == "una clave oficial necesita la plantilla oficial enlazada"

    puede, motivo = can_activate(
        _conjunto(SetType.OFFICIAL_EXAM),
        _clave(approved_at=AHORA, source_document_version_id="ver-1"),
    )
    assert (puede, motivo) == (True, None)


def test_una_clave_sin_aprobacion_no_se_activa() -> None:
    puede, motivo = can_activate(
        _conjunto(SetType.PRIVATE_BANK), _clave(source_document_version_id="ver-1")
    )

    assert puede is False
    assert motivo == "una clave activa necesita aprobación"


def test_una_clave_privada_no_necesita_documento_oficial() -> None:
    puede, motivo = can_activate(_conjunto(SetType.PRIVATE_BANK), _clave(approved_at=AHORA))

    assert (puede, motivo) == (True, None)


def test_una_plantilla_de_otro_conjunto_no_vale() -> None:
    puede, motivo = can_activate(
        _conjunto(SetType.PRACTICE), _clave(approved_at=AHORA, question_set_id="set-9")
    )

    assert puede is False
    assert motivo == "la plantilla no es de este conjunto"


def test_un_desenlace_con_clave_sin_clave_es_un_error_de_dominio() -> None:
    with pytest.raises(ValueError):
        AnswerKeyEntry("q1", KeyOutcome.KEYED, ())


# --- asistente JSON (11_IMPLEMENTATION-SLICES §S06) ---------------------------------------------


def test_el_asistente_json_lee_preguntas_claves_y_reservas() -> None:
    texto = json.dumps(
        {
            "model_code": "B",
            "questions": [
                {
                    "stem": "¿Cuál es el plazo?",
                    "options": ["a) diez días", "b) quince días", "c) un mes"],
                    "correct": "b",
                    "number": 7,
                },
                {
                    "stem": "¿Cuál NO es un recurso?",
                    "options": ["alzada", "reposición", "revisión"],
                    "correct": ["c"],
                    "reserve": True,
                    "reserve_order": 1,
                },
            ],
        }
    )

    resultado = parse_questions_json(texto)

    assert len(resultado.questions) == 2, resultado.issues
    assert resultado.model_code == "B"
    assert resultado.with_key == 2
    assert resultado.reserves == 1
    # La etiqueta de la opción se quita; el texto que se cita no se toca más.
    assert [opcion.text for opcion in resultado.questions[0].options] == [
        "diez días",
        "quince días",
        "un mes",
    ]
    assert resultado.questions[0].correct_option_keys == ("b",)
    assert resultado.questions[0].number == 7
    assert resultado.questions[1].is_reserve is True
    assert resultado.questions[1].reserve_order == 1
    assert [incidencia.code for incidencia in resultado.issues] == []


def test_el_asistente_json_acepta_la_respuesta_escrita_o_numerada() -> None:
    """Un JSON exportado de otra herramienta trae la respuesta escrita, no su letra."""
    texto = json.dumps(
        [
            {
                "stem": "¿Qué artículo?",
                "options": ["el 14", "el 23", "el 103"],
                "correct": "el 23",
            },
            {
                "stem": "¿Cuántos bloques?",
                "options": ["tres", "cuatro", "cinco"],
                "correct": 2,
            },
        ]
    )

    resultado = parse_questions_json(texto)

    assert resultado.questions[0].correct_option_keys == ("b",)
    assert resultado.questions[1].correct_option_keys == ("b",)


def test_el_json_trae_explicaciones_por_opcion_y_sabe_a_cual_van() -> None:
    """S12.7: «por qué la b no vale» llega desde el material, atado a **su** opción.

    La clave puede ser la letra o el texto exacto de la opción, como en la respuesta. Una clave que
    no corresponde a ninguna opción **no se guarda** y se informa: una explicación colgada de la
    opción equivocada enseña mal, y eso es peor que no tenerla.
    """
    texto = json.dumps(
        [
            {
                "stem": "¿Cuál es el plazo?",
                "options": ["diez días", "quince días"],
                "correct": "a",
                "explanations": {
                    "b": "la ley dice diez días hábiles",
                    "diez días": "es la correcta",
                },
            },
            {
                "stem": "¿Qué artículo?",
                "options": ["el 14", "el 23"],
                "explanations": {"z": "no existe esa opción", "b": 17},
            },
        ]
    )

    resultado = parse_questions_json(texto)

    assert resultado.questions[0].option_explanations == (
        ("b", "la ley dice diez días hábiles"),
        ("a", "es la correcta"),
    )
    # La segunda pregunta no trae ninguna explicación utilizable: la clave «z» no es una opción y el
    # valor 17 no es texto, así que no se guarda nada y la incidencia dice qué clave sobra.
    assert resultado.questions[1].option_explanations == ()
    assert [incidencia.code for incidencia in resultado.issues] == ["explanation_without_option"]
    assert "z" in resultado.issues[0].detail


def test_una_pregunta_mala_del_json_no_aborta_el_lote() -> None:
    """El mismo criterio que el CSV: lo que no se entiende se informa y el resto entra."""
    texto = json.dumps(
        [
            {"stem": "Buena", "options": ["uno", "dos"], "correct": "a"},
            {"stem": "", "options": ["uno", "dos"]},
            {"stem": "Sin opciones", "options": ["solo una"]},
            {"stem": "Clave imposible", "options": ["uno", "dos"], "correct": "z"},
            {"stem": "Tipo raro", "options": ["uno", "dos"], "type": "inventado"},
            {"stem": "Otra buena", "options": ["tres", "cuatro"]},
        ]
    )

    resultado = parse_questions_json(texto)

    assert [pregunta.stem for pregunta in resultado.questions] == ["Buena", "Otra buena"]
    assert [incidencia.code for incidencia in resultado.issues] == [
        "no_stem",
        "few_options",
        "key_without_option",
        "unknown_type",
    ]
    # Una pregunta sin clave entra **sin clave**: no se rellena con nada.
    assert resultado.questions[1].correct_option_keys == ()
    assert resultado.with_key == 1


def test_un_texto_que_no_es_json_lo_dice_sin_inventar_preguntas() -> None:
    resultado = parse_questions_json("esto no es JSON, es texto suelto")

    assert resultado.questions == ()
    assert [incidencia.code for incidencia in resultado.issues] == ["not_json"]


def test_el_json_declara_los_campos_que_no_guarda() -> None:
    """Lo que el asistente lee y no guarda se declara: no desaparece sin decirlo."""
    texto = json.dumps(
        [
            {
                "stem": "Pregunta",
                "options": ["uno", "dos"],
                "tags": ["tema-1"],
                "source": "apuntes",
            }
        ]
    )

    resultado = parse_questions_json(texto)

    assert resultado.ignored_fields == ("tags", "source")
    assert len(resultado.questions) == 1


# --- el hueco `[]` y el año del título (F39, §3.7) ------------------------------------------------

#: Los enunciados reales del banco del propietario que traen `[]`, con lo que cada uno es. Son los
#: 28 medidos sobre su copia verificada: 21 huecos de frase para completar (todos del conjunto
#: del modelo OSI) y 7 corchetes de código. La lista va aquí entera porque la regla tiene que
#: acertar en los 28 y en el mismo sentido.
#: en el mismo sentido; un heurístico que solo se prueba con un caso bonito no se puede fiar.
HUECOS_DEL_PROPIETARIO: tuple[tuple[str, bool], ...] = (
    ("En el modelo OSI, los cambios en una capa deben ser [] para el resto de niveles", True),
    (
        "Las capas superiores definen cómo deben comunicarse las aplicaciones entre sí y con "
        "los []",
        True,
    ),
    ("Las capas inferiores definen cómo deben ser transmitidos los datos de [] a []", True),
    ("La capa física se encarga de la transmisión de bits a través de un canal de []", True),
    (
        "Definir los niveles de tensión y el tipo de señal eléctrica es una función de la capa []",
        True,
    ),
    (
        "La capa de [] toma el medio de transmisión en bruto y lo transforma en una línea libre de "
        "errores",
        True,
    ),
    (
        "La capa de enlace regula el tráfico mediante el control de [] para evitar saturar al "
        "receptor",
        True,
    ),
    (
        "Para aumentar el volumen de transmisión, el nivel 4 puede crear múltiples conexiones de "
        "[] para una sola de transporte",
        True,
    ),
    (
        "En el nivel de transporte, los datos [] pueden saltarse los mecanismos de control de "
        "flujo",
        True,
    ),
    (
        "El manejo de turnos mediante fichas o testigos (tokens) es parte del control del [] en la "
        "capa de sesión",
        True,
    ),
    ("En la capa de sesión, los dispositivos se referencian por [] y no por dirección", True),
    ("La conversión entre códigos como ASCII y EBCDIC es responsabilidad la capa de []", True),
    (
        "La capa de presentación realiza la [] de datos para reducir el ancho de banda necesario",
        True,
    ),
    ("El elemento ROSE de la capa de aplicación facilita la petición de operaciones []", True),
    ("La capa de [] gestiona el direccionamiento lógico y el control de tráfico", True),
    (
        "En las comunicaciones [] de la capa 5, el tráfico puede ir en ambas direcciones al mismo "
        "tiempo",
        True,
    ),
    (
        "El control de acceso al canal compartido en redes de difusión es función de la capa de []",
        True,
    ),
    (
        "La división de mensajes en unidades más complejas y la asignación de rutas es tarea de la "
        "capa de []",
        True,
    ),
    (
        "La capa de [] proporciona medios para que las entidades de presentación sincronicen su "
        "diálogo",
        True,
    ),
    (
        "En la capa física, los conectores mecánicos y niveles de tensión son características []",
        True,
    ),
    (
        "El elemento de servicio [] garantiza fiabilidad manejando funciones de nivel 5 desde la "
        "capa de aplicación",
        True,
    ),
    ("Si declaramos int[][] matriz = new int[3][4], ¿cuántos elementos contiene la matriz?", False),
    (
        "Supongamos que existe una matriz saldoMensual declarada de la siguiente forma: float[] "
        "saldoMensual = new float[12]",
        False,
    ),
    (
        "Dado el siguiente código Java: int notas[] = {7,8,5,6,7,5}; elegido = notas [posicion];",
        False,
    ),
    ('01. El siguiente código C int v[]={1,2,3,4,5}; int *i = v; printf("%d\\n", *(i+4));', False),
    ("(EXAMEN 2016) float[] SaldoMensual = new float[12]", False),
    ("public static void main(String[] args) { }", False),
    ("La capa de aplicación ejecuta operaciones sobre los []", True),
)


@pytest.mark.parametrize(("enunciado", "es_hueco"), HUECOS_DEL_PROPIETARIO)
def test_el_hueco_se_ensena_y_el_corchete_de_codigo_no_se_toca(
    enunciado: str, es_hueco: bool
) -> None:
    """`[]` es un hueco cuando cuelga del aire; pegado a un identificador es un corchete de código.

    Es la separación medida sobre las 28 preguntas del propietario: 21 son huecos (se enseñan como
    `_____`) y 7 son `int[]`, `float[] saldoMensual`, `notas[] = {...}` o `String[] args`, que se
    quedan como están. Convertir un `int[]` en un `int_____` sería un error nuevo.
    """
    visible = mostrar_huecos(enunciado)

    if es_hueco:
        assert "[]" not in visible, "el hueco no se enseña como corchetes"
        assert "_____" in visible
    else:
        assert visible == enunciado, "el código se queda tal cual"


def test_el_ano_del_titulo_es_el_que_declara_el_documento() -> None:
    """Los títulos de los 13 exámenes declaran su año; el del INAP lo rotula en la cabecera.

    Ninguno declara el día, así que lo único que se puede afirmar —y lo que la fila enseña— es el
    año. Poner un 1 de enero sería inventarse el día y el mes.
    """
    assert ano_del_titulo("TAI ingreso libre 2019 · ejercicio único (examen oficial INAP)") == 2019
    assert ano_del_titulo("TAI ingreso libre 2025 · modelo A (examen oficial INAP)") == 2025
    assert ano_del_titulo("TAI promoción interna 2024 · modelo B (examen oficial INAP)") == 2024
    # Un título sin año no lo inventa.
    assert ano_del_titulo("Examen oficial sin año en el título") is None
    # Y si hay dos, manda el primero: el del ejercicio va delante del nombre de la versión.
    assert ano_del_titulo("TAI 2019 · Test GSI (v2024)") == 2019
