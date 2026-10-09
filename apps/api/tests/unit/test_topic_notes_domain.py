"""El dominio de los apuntes guiados por preguntas (pasos B-E), sin red y sin base de datos.

Lo que se comprueba aquí es la **decisión**: qué es un grupo de preguntas iguales, cómo se reparten
los hechos por apartados, cuándo una frase copiada cuenta como justificación, qué se da por
cubierto y qué queda como duda. Todo eso se puede probar sin llamar a nadie, que es justo por lo
que está aparte de la red.
"""

from __future__ import annotations

from opofuente.domain.dossier import PassageFacts
from opofuente.domain.topic_notes import (
    MAX_HECHOS_POR_APARTADO,
    Coverage,
    FactKind,
    Hecho,
    KeyStatus,
    Motivo,
    NoteSection,
    QuestionForNotes,
    QuestionGroup,
    QuoteCheck,
    agrupar,
    esquema,
    evaluar,
    firma_de_grupo,
    hechos_integrados,
    indexar_material,
    notes_document,
    notes_from_document,
    notes_signature,
    seleccionar_material,
    verificar_cita,
)
from opofuente.domain.topic_notes import (
    SectionNotes as SectionNotesDomain,
)
from opofuente.domain.topic_notes import (
    TopicNotes as TopicNotesDomain,
)

EPIGRAFES = (
    ("IV.7.1", "El modelo TCP/IP y el modelo OSI."),
    ("IV.7.2", "Protocolos TCP/IP."),
)


def _pregunta(
    identificador: str,
    *,
    enunciado: str = "¿En qué año se aprobó la Constitución?",
    opciones: tuple[tuple[str, str], ...] = (("a", "1976"), ("b", "1978")),
    letras: tuple[str, ...] = ("b",),
    estado: KeyStatus = KeyStatus.ACTIVE,
    epigrafe: str | None = None,
) -> QuestionForNotes:
    return QuestionForNotes(
        question_version_id=identificador,
        set_id="conjunto-1",
        stem=enunciado,
        options=opciones,
        correct_keys=letras,
        key_status=estado,
        epigraph_code=epigrafe,
        mapping_status="accepted",
    )


def _grupo(*preguntas: QuestionForNotes) -> QuestionGroup:
    return agrupar(list(preguntas))[0]


def _hecho(texto: str, *, epigrafe: str = "IV.7.1", firma: str = "f1") -> Hecho:
    return Hecho(
        text=texto,
        kind=FactKind.NORMATIVO,
        epigraph_code=epigrafe,
        source_groups=(firma,),
        fact_id=f"hecho-{texto[:6]}",
    )


def _seccion(facts: tuple[Hecho, ...] = (), body: str = "") -> NoteSection:
    return NoteSection(
        key="iv-7-1",
        epigraph_code="IV.7.1",
        title="El modelo TCP/IP",
        anchor="iv-7-1",
        position=1,
        facts=facts,
        body_markdown=body,
        section_id="seccion-1",
    )


# --- los grupos -----------------------------------------------------------------------------------


def test_dos_preguntas_iguales_son_un_grupo_y_las_de_opciones_distintas_no() -> None:
    """La firma normaliza el enunciado: los acentos y la puntuación no separan lo mismo."""
    iguales = agrupar(
        [
            _pregunta("q1", enunciado="¿En qué año se aprobó la Constitución Española?"),
            _pregunta("q2", enunciado="En que año se aprobo la constitucion espanola"),
            _pregunta("q3", opciones=(("a", "1976"), ("b", "1977"))),
        ]
    )
    assert len(iguales) == 2
    assert len(iguales[0].questions) == 2
    assert iguales[0].question_ids == ("q1", "q2")
    assert iguales[0].key_status is KeyStatus.ACTIVE
    assert iguales[0].correct_keys == ("b",)


def test_la_firma_es_estable_entre_llamadas() -> None:
    """La misma pregunta da la misma firma: es lo que permite guardar el rastro y reanudar."""
    assert firma_de_grupo("¿Qué es el DNS?", (("a", "Un protocolo"),)) == firma_de_grupo(
        "que es el dns", (("a", "un protocolo"),)
    )


def test_una_clave_en_borrador_con_dos_respuestas_distintas_no_es_clara() -> None:
    """El grupo se queda con el mejor estado de clave que tenga, y con **su** respuesta."""
    grupo = _grupo(
        _pregunta("q1", estado=KeyStatus.DRAFT, letras=("a",)),
        _pregunta("q2", estado=KeyStatus.ACTIVE, letras=("b",)),
    )
    assert grupo.key_status is KeyStatus.ACTIVE
    assert grupo.correct_keys == ("b",), "la letra que se compara es la de la clave que manda"


# --- el esquema -----------------------------------------------------------------------------------


def test_el_esquema_respeta_el_orden_oficial_y_no_deja_hechos_sin_apartado() -> None:
    """Un hecho con un epígrafe inventado cae en «otros contenidos»: se señala, no se pierde."""
    hechos = [
        _hecho("El modelo OSI tiene siete capas.", epigrafe="IV.7.1"),
        _hecho("La capa de transporte usa puertos.", epigrafe="IV.7.2"),
        _hecho("Hecho con epígrafe que no existe.", epigrafe="IX.9.9"),
    ]
    apartados = esquema(EPIGRAFES, hechos)
    assert [apartado.epigraph_code for apartado in apartados[:2]] == ["IV.7.1", "IV.7.2"]
    assert apartados[0].anchor == "iv-7-1"
    assert apartados[2].key == "otros-contenidos"
    assert apartados[2].needs_review_reason is not None
    assert sum(len(apartado.facts) for apartado in apartados) == len(hechos)


def test_un_epigrafe_con_muchos_hechos_se_parte_en_subapartados_numerados() -> None:
    hechos = [
        _hecho(f"Hecho número {numero} del epígrafe.", epigrafe="IV.7.1") for numero in range(45)
    ]
    apartados = esquema(EPIGRAFES, hechos)
    assert len(apartados) == 2
    assert [apartado.key for apartado in apartados] == ["iv-7-1-1", "iv-7-1-2"]
    assert all(len(apartado.facts) <= MAX_HECHOS_POR_APARTADO for apartado in apartados)
    assert sum(len(apartado.facts) for apartado in apartados) == 45


def test_un_epigrafe_sin_hechos_no_genera_apartado() -> None:
    apartados = esquema(EPIGRAFES, [_hecho("Solo del segundo.", epigrafe="IV.7.2")])
    assert [apartado.epigraph_code for apartado in apartados] == ["IV.7.2"]


# --- la comprobación de la cita -------------------------------------------------------------------


def test_la_frase_copiada_tiene_que_estar_en_los_apuntes_de_verdad() -> None:
    """La comprobación es mecánica: lo que el modelo diga que hay no cuenta, cuenta lo que hay."""
    apuntes = "El **artículo 29** de la Constitución reconoce el derecho de petición."
    assert verificar_cita("reconoce el derecho de petición", apuntes)
    assert verificar_cita("El artículo 29 de la Constitución reconoce", apuntes)
    assert not verificar_cita("El artículo 29 reconoce el derecho de huelga", apuntes)
    assert not verificar_cita("artículo 29", apuntes), "una cita muy corta no justifica nada"
    assert not verificar_cita(None, apuntes)


def test_los_comentarios_de_revision_no_sirven_para_justificar_una_respuesta() -> None:
    """Lo que el opositor no lee no puede sostener una respuesta."""
    apuntes = "El plazo es de diez días. <!-- revisar: sin material de apoyo -->"
    assert not verificar_cita("revisar: sin material de apoyo", apuntes)
    assert verificar_cita("El plazo es de diez días", apuntes)


# --- el resultado de cada pregunta ----------------------------------------------------------------


def test_con_clave_activa_hacen_falta_la_frase_y_la_letra() -> None:
    apuntes = "El derecho de petición se reconoce en el artículo 29 de la Constitución."
    grupo = _grupo(_pregunta("q1", letras=("b",)))
    seccion = _seccion()

    cubierta = evaluar(
        grupo=grupo,
        check=QuoteCheck("f", "b", "se reconoce en el artículo 29 de la Constitución"),
        apuntes=apuntes,
        section=seccion,
        attempts=1,
    )
    assert cubierta.coverage is Coverage.CUBIERTA
    assert cubierta.quote is not None
    assert cubierta.note is None

    letra_mala = evaluar(
        grupo=grupo,
        check=QuoteCheck("f", "a", "se reconoce en el artículo 29 de la Constitución"),
        apuntes=apuntes,
        section=seccion,
        attempts=1,
    )
    assert letra_mala.coverage is Coverage.HUECO, "a la primera es un hueco: se puede arreglar"

    repetida = evaluar(
        grupo=grupo,
        check=QuoteCheck("f", "a", "se reconoce en el artículo 29 de la Constitución"),
        apuntes=apuntes,
        section=seccion,
        attempts=2,
    )
    assert repetida.coverage is Coverage.CONFLICTO, "con clave activa, la letra decide"
    assert repetida.note is Motivo.LETRA_NO_COINCIDE


def test_sin_frase_es_hueco_a_la_primera_y_duda_a_la_segunda() -> None:
    grupo = _grupo(_pregunta("q1"))
    seccion = _seccion()
    apuntes = "Los apuntes hablan de otra cosa completamente distinta y lo dicen así."

    primera = evaluar(
        grupo=grupo,
        check=QuoteCheck("f", "b", None),
        apuntes=apuntes,
        section=seccion,
        attempts=1,
    )
    assert primera.coverage is Coverage.HUECO

    segunda = evaluar(
        grupo=grupo,
        check=QuoteCheck("f", "b", None),
        apuntes=apuntes,
        section=seccion,
        attempts=2,
    )
    assert segunda.coverage is Coverage.DUDOSA
    assert segunda.note is Motivo.SIN_FRASE_EN_LOS_APUNTES


def test_con_clave_en_borrador_la_frase_cubre_solo_si_la_letra_coincide() -> None:
    """La revisión del propietario cambió este criterio, y eran 96 preguntas de los tres pilotos.

    Antes, con clave en borrador mandaba la frase y la letra del modelo no decidía: una pregunta que
    los apuntes contestaban «b» con la plantilla diciendo «a» contaba como cubierta. Una letra
    distinta de la clave no es una cobertura: es un conflicto (o la clave está mal, o los apuntes) y
    va a la cola de revisión. La frase verificada sigue siendo obligatoria.
    """
    apuntes = "El derecho de petición se reconoce en el artículo 29 de la Constitución."
    frase = "se reconoce en el artículo 29 de la Constitución"

    coincide = evaluar(
        grupo=_grupo(_pregunta("q1", letras=("a",), estado=KeyStatus.DRAFT)),
        check=QuoteCheck("f", "a", frase),
        apuntes=apuntes,
        section=_seccion(),
        attempts=1,
    )
    assert coincide.coverage is Coverage.CUBIERTA

    primera = evaluar(
        grupo=_grupo(_pregunta("q2", letras=("a",), estado=KeyStatus.DRAFT)),
        check=QuoteCheck("f", "b", frase),
        apuntes=apuntes,
        section=_seccion(),
        attempts=1,
    )
    assert primera.coverage is Coverage.HUECO, "a la primera se le da la vuelta del añadido"

    final = evaluar(
        grupo=_grupo(_pregunta("q3", letras=("a",), estado=KeyStatus.DRAFT)),
        check=QuoteCheck("f", "b", frase),
        apuntes=apuntes,
        section=_seccion(),
        attempts=2,
    )
    assert final.coverage is Coverage.CONFLICTO
    assert final.note is Motivo.LETRA_NO_COINCIDE
    assert final.quote is None, "un conflicto no es una pregunta cubierta: no se guarda como cita"


def test_con_la_frase_y_sin_letra_del_modelo_es_un_conflicto_con_clave() -> None:
    """No decir la letra no puede contar como decir la buena: con clave, la letra tiene que valer.

    Es el otro lado de la regla nueva: sin letra no se puede afirmar que coincida.
    """
    apuntes = "El derecho de petición se reconoce en el artículo 29 de la Constitución."
    resultado = evaluar(
        grupo=_grupo(_pregunta("q1", letras=("a",), estado=KeyStatus.DRAFT)),
        check=QuoteCheck("f", None, "se reconoce en el artículo 29 de la Constitución"),
        apuntes=apuntes,
        section=_seccion(),
        attempts=2,
    )
    assert resultado.coverage is Coverage.CONFLICTO
    assert resultado.note is Motivo.LETRA_NO_COINCIDE


def test_sin_ninguna_clave_manda_la_frase_porque_no_hay_letra_que_comparar() -> None:
    apuntes = "El derecho de petición se reconoce en el artículo 29 de la Constitución."
    resultado = evaluar(
        grupo=_grupo(_pregunta("q1", letras=(), estado=KeyStatus.NINGUNA)),
        check=QuoteCheck("f", None, "se reconoce en el artículo 29 de la Constitución"),
        apuntes=apuntes,
        section=_seccion(),
        attempts=1,
    )
    assert resultado.coverage is Coverage.CUBIERTA


def test_una_pregunta_sin_ninguna_clave_y_sin_frase_queda_como_incidencia_de_la_pregunta() -> None:
    grupo = _grupo(_pregunta("q1", letras=(), estado=KeyStatus.NINGUNA))
    resultado = evaluar(
        grupo=grupo,
        check=QuoteCheck("f", None, None),
        apuntes="Unos apuntes que no hablan de esto en absoluto, con más texto para comparar.",
        section=_seccion(),
        attempts=2,
    )
    assert resultado.coverage is Coverage.DUDOSA
    assert resultado.note is Motivo.CLAVE_SIN_DEFINIR


def test_una_clave_señalada_por_el_paso_b_es_una_incidencia_aunque_los_apuntes_la_contesten() -> (
    None
):
    """La clave que se sabe mala no decide: se revisa la pregunta, no se reescribe el tema."""
    apuntes = "El derecho de petición se reconoce en el artículo 29 de la Constitución."
    grupo = _grupo(_pregunta("q1", letras=("a",)))
    resultado = evaluar(
        grupo=grupo,
        check=QuoteCheck("f", "a", "se reconoce en el artículo 29 de la Constitución"),
        apuntes=apuntes,
        section=_seccion(),
        attempts=1,
        clave_dudosa=True,
    )
    assert resultado.coverage is Coverage.DUDOSA
    assert resultado.note is Motivo.CLAVE_CONTRADICE_LA_NORMA


# --- el material y los hechos integrados ----------------------------------------------------------


def _pasaje(
    identificador: str, texto: str, *, documento: str = "Apuntes del bloque 4"
) -> PassageFacts:
    return PassageFacts(
        evidence_id=identificador,
        text=texto,
        normalized=texto.lower(),
        citation_label=None,
        page=1,
        section_title=None,
        ordinal=1,
        document_id="doc-1",
        document_title=documento,
        document_type="personal_notes",
        authority_tier=None,
        version_id="version-1",
        version_label=None,
        version_status="accepted",
        quality="good",
    )


def test_el_material_se_elige_por_parecido_con_los_hechos_y_sin_repetir_lo_que_no_viene() -> None:
    material = indexar_material(
        [
            _pasaje("e1", "El modelo OSI tiene siete capas y cada una tiene su función."),
            _pasaje("e2", "La receta de la tortilla lleva patatas y huevos."),
            _pasaje("e3", "Las siete capas del modelo OSI se numeran de abajo arriba."),
        ]
    )
    elegidos = seleccionar_material(
        [_hecho("El modelo OSI tiene siete capas.")], material, max_pasajes=5
    )
    assert [pasaje.evidence_id for pasaje in elegidos] == ["e1", "e3"]
    assert "tortilla" not in " ".join(pasaje.text for pasaje in elegidos)


def test_el_material_respeta_el_tope_de_pasajes() -> None:
    pasajes = [
        _pasaje(f"e{numero}", "El modelo OSI tiene siete capas y se estudia así.")
        for numero in range(10)
    ]
    elegidos = seleccionar_material(
        [_hecho("El modelo OSI tiene siete capas.")], indexar_material(pasajes), max_pasajes=3
    )
    assert len(elegidos) == 3


def test_un_hecho_que_no_aparece_en_el_texto_se_detecta() -> None:
    hechos = [
        _hecho("El derecho de petición se reconoce en el artículo 29 de la Constitución."),
        _hecho("El Defensor del Pueblo es el alto comisionado de las Cortes Generales."),
    ]
    faltan = hechos_integrados(
        hechos,
        "El derecho de petición se reconoce en el artículo 29 de la Constitución Española.",
    )
    assert len(faltan) == 1


# --- la forma canónica de los apuntes -------------------------------------------------------------


def test_los_apuntes_se_guardan_y_se_leen_igual_y_cambian_la_firma_del_tema() -> None:
    notas = TopicNotesDomain(
        generated_at=None,
        model="deepseek-flash",
        prompt_template_version="apuntes-1",
        sections=(
            SectionNotesDomain(
                key="iv-7-1",
                epigraph_code="IV.7.1",
                title="El modelo OSI",
                anchor="iv-7-1",
                body_markdown="# El modelo OSI\n\nTiene siete capas.",
                covered=2,
                question_ids=("q1", "q2"),
            ),
        ),
    )
    documento = notes_document(notas)
    assert documento is not None and documento["covered"] == 2
    vuelta = notes_from_document(documento)
    assert vuelta is not None
    assert vuelta.sections[0].body_markdown == notas.sections[0].body_markdown
    assert vuelta.covered == 2
    assert vuelta.sections[0].question_ids == ("q1", "q2")
    assert notes_signature(notas) != notes_signature(None)
    assert notes_from_document(None) is None
