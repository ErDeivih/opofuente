"""Pruebas de las métricas de clasificación y del dataset sintético etiquetado (S04).

Dos ideas mandan aquí:

- **Los números están fijados.** Si el motor o el dataset cambian, estas pruebas fallan y obligan a
  mirar si la calidad mejoró o empeoró. Una prueba que solo comprueba que «sale un número» no mide
  nada.
- **Los fallos se nombran.** El informe tiene que decir qué casos falla el motor y en qué eje, en
  lugar de esconderlos detrás de una media.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path

import pytest

from opofuente.domain.classification import (
    Axis,
    ClassificationSubject,
    ConfidenceBands,
    Proposal,
    SubjectType,
)
from opofuente.domain.classification_metrics import (
    UNCLASSIFIED,
    AxisOutcome,
    evaluate,
    outcomes_for_case,
)
from opofuente.infrastructure.classifiers import DeterministicClassifier
from opofuente.tools.classification_metrics import (
    DATASET_PATH,
    DEFAULT_ENGINE,
    INTENTS,
    build_engine,
    build_report,
    dataset_argument,
    engine_argument,
    format_report,
    load_dataset,
    main,
)

#: Dataset e informe del estado actual. Se calculan una vez: son datos, no estado que cambie.
DATASET = load_dataset()
REPORT = build_report(DATASET)

#: Fallos del dataset de hoy, en el orden en que los informa el informe (caso, eje, tipo).
FALLOS_ESPERADOS = (
    ("ambiguo-apuntes-para-el-foro", Axis.DOCUMENT_TYPE, "falso_positivo"),
    ("ambiguo-dos-temas", Axis.DOCUMENT_TYPE, "falso_negativo"),
    ("ambiguo-dos-temas", Axis.TOPIC, "falso_positivo"),
    ("donde-falla-cita-de-resolucion", Axis.AUTHORITY, "falso_positivo"),
    ("donde-falla-tema-sin-tipo", Axis.DOCUMENT_TYPE, "falso_negativo"),
)


def _outcomes(
    *,
    hits: int = 0,
    false_positives: int = 0,
    missing: int = 0,
    correct_abstentions: int = 0,
    axis: Axis = Axis.DOCUMENT_TYPE,
    confidence: float = 0.9,
) -> list[AxisOutcome]:
    """Ranuras construidas a mano, para comprobar la aritmética sin depender del motor."""
    outcomes: list[AxisOutcome] = []
    for indice in range(hits):
        outcomes.append(
            AxisOutcome(
                case_id=f"acierto-{indice}",
                axis=axis,
                expected="convocation",
                proposed="convocation",
                confidence=confidence,
            )
        )
    for indice in range(false_positives):
        outcomes.append(
            AxisOutcome(
                case_id=f"equivocado-{indice}",
                axis=axis,
                expected="convocation",
                proposed="curriculum",
                confidence=confidence,
            )
        )
    for indice in range(missing):
        outcomes.append(
            AxisOutcome(case_id=f"sin-propuesta-{indice}", axis=axis, expected="convocation")
        )
    for indice in range(correct_abstentions):
        outcomes.append(AxisOutcome(case_id=f"abstencion-{indice}", axis=axis, expected=None))
    return outcomes


def _propuesta(axis: Axis, value: str) -> Proposal:
    return Proposal(
        id="",
        subject_type=SubjectType.ARTIFACT,
        subject_id="syn-cls-001",
        axis=axis,
        proposed_value=value,
        confidence=0.6,
        engine_name="determinista",
        engine_version="1",
    )


def _outcomes_del_dataset(case_id: str) -> tuple[AxisOutcome, ...]:
    """Ranuras reales de un caso del dataset: el motor de verdad, no un doble de prueba."""
    caso = DATASET.case(case_id)
    motor = DeterministicClassifier()
    return outcomes_for_case(caso.case_id, caso.expected, motor.propose(caso.subject))


# --- Números reales del dataset actual ------------------------------------------------


def test_las_metricas_por_eje_del_dataset_actual_estan_fijadas() -> None:
    """Precisión, recall y F1 por eje: el número real de hoy, sin redondear a ojo."""
    esperado = {
        Axis.DOCUMENT_TYPE: (0.9, 0.75, 0.8182),
        Axis.OPPOSITION: (1.0, 1.0, 1.0),
        Axis.TOPIC: (0.6667, 0.6667, 0.6667),
        Axis.AUTHORITY: (0.75, 1.0, 0.8571),
        Axis.RIGHTS: (1.0, 1.0, 1.0),
    }

    for eje, (precision, recall, f1) in esperado.items():
        metrics = REPORT.metrics_for(eje)
        assert (metrics.precision, metrics.recall, metrics.f1) == (precision, recall, f1), (
            f"El eje {eje.value} cambió de números: mira si el motor mejoró o empeoró."
        )


def test_los_contadores_por_eje_del_dataset_actual_estan_fijados() -> None:
    """Los contadores explican las medias: 15 casos, 75 ranuras y 21 propuestas en total."""
    documental = REPORT.metrics_for(Axis.DOCUMENT_TYPE)
    tema = REPORT.metrics_for(Axis.TOPIC)
    autoridad = REPORT.metrics_for(Axis.AUTHORITY)

    assert (REPORT.case_count, REPORT.slot_count) == (15, 75)
    assert sum(metrics.proposed for metrics in REPORT.axes) == 21
    assert (documental.expected, documental.proposed) == (12, 10)
    assert (documental.hits, documental.false_positives, documental.false_negatives) == (9, 1, 3)
    assert (tema.hits, tema.false_positives, tema.false_negatives) == (2, 1, 1)
    assert (autoridad.hits, autoridad.false_positives) == (3, 1)
    assert REPORT.metrics_for(Axis.RIGHTS).correct_abstentions == 13


def test_la_puerta_de_promociones_criticas_erroneas_esta_en_cero() -> None:
    """Puerta inicial de §7: un eje crítico no se aplica solo, ni acertando ni equivocándose."""
    for eje in (Axis.AUTHORITY, Axis.RIGHTS):
        metrics = REPORT.metrics_for(eje)
        assert metrics.auto_applied == 0
        assert metrics.critical_wrong_automatic_promotions == 0
        # Sin propuestas autoaplicables la precisión no es 0: es indefinida, y así se informa.
        assert metrics.auto_applied_precision is None

    assert REPORT.critical_wrong_automatic_promotions == 0
    # La puerta es una puerta de verdad: la herramienta sale con 0 cuando se cumple.
    assert main([]) == 0


def test_las_promociones_automaticas_erroneas_fuera_de_los_ejes_criticos_se_cuentan() -> None:
    """El otro lado de la puerta: una promoción equivocada con banda alta sí se aplicaría."""
    # La señal débil sola ya no cruza la banda alta (corrector de S04): la etiqueta equivocada de
    # «apuntes de foro» se queda en revisión, así que el documental ya no promociona nada erróneo.
    assert REPORT.wrong_automatic_promotions == 1
    assert REPORT.metrics_for(Axis.TOPIC).wrong_automatic_promotions == 1
    documental = REPORT.metrics_for(Axis.DOCUMENT_TYPE)
    assert documental.wrong_automatic_promotions == 0
    assert (documental.auto_applied, documental.auto_applied_hits) == (2, 2)
    assert documental.auto_applied_precision == 1.0
    # Lo que se aplica solo en el documental acierta siempre ahora: la etiqueta equivocada que


def test_la_calibracion_enfrenta_confianza_declarada_con_acierto_real() -> None:
    """Una confianza de 0,8 no vale lo mismo en un eje que se equivoca que en uno que no."""
    documental = REPORT.metrics_for(Axis.DOCUMENT_TYPE).calibration
    tema = REPORT.metrics_for(Axis.TOPIC).calibration
    autoridad = REPORT.metrics_for(Axis.AUTHORITY).calibration

    assert [(cubo.lower, cubo.proposals, cubo.hits) for cubo in documental] == [
        (0.6, 8, 7),
        (0.8, 2, 2),
    ]
    assert [(cubo.lower, cubo.upper) for cubo in tema] == [(0.8, 1.0)]
    assert tema[0].accuracy == 0.6667
    # Autoridad propone casi todo por debajo de 0,6 (citas), y ahí es donde se equivoca.
    assert [(cubo.lower, cubo.proposals, cubo.accuracy) for cubo in autoridad] == [
        (0.4, 3, 0.6667),
        (0.8, 1, 1.0),
    ]
    # Un cubo sin propuestas no informa: no hay acierto que medir.
    assert all(cubo.accuracy is not None for cubo in documental + tema + autoridad)


def test_el_sin_clasificar_separa_la_abstencion_correcta_del_material_sin_cubrir() -> None:
    """«Sin clasificar» mezcla dos cosas opuestas: abstenerse bien y no cubrir lo que faltaba."""
    assert REPORT.unclassified_slots == 54
    assert REPORT.correct_abstentions == 52
    assert REPORT.unclassified_with_expected == 2
    assert REPORT.unclassified_share == 0.72
    assert REPORT.unclassified_cases == (
        "sin-senales-escaneo-sin-texto",
        "sin-senales-nota-cotidiana",
    )
    assert REPORT.unclassified_case_share == 0.1333
    assert REPORT.total_corrections == 5
    assert sum(metrics.corrections for metrics in REPORT.axes) == 5


# --- Reproducibilidad -----------------------------------------------------------------


def test_el_mismo_dataset_da_exactamente_el_mismo_informe_dos_veces() -> None:
    """Reproducible: mismo dataset, mismo motor, mismos números y mismo texto, sin excepciones."""
    otra_copia = load_dataset(DATASET_PATH)
    segundo_informe = build_report(otra_copia)

    assert otra_copia == DATASET
    assert segundo_informe == REPORT
    assert format_report(otra_copia, segundo_informe) == format_report(DATASET, REPORT)
    # Y dos motores distintos sobre el mismo caso dan la misma propuesta: no hay estado compartido.
    caso = DATASET.case("facil-bases-convocatoria")
    assert DeterministicClassifier().propose(caso.subject) == DeterministicClassifier().propose(
        caso.subject
    )


def test_el_orden_de_las_ranuras_no_cambia_el_informe() -> None:
    """El informe ordena por caso y eje antes de contar: las mismas filas dan los mismos números."""
    outcomes = [
        outcome
        for caso in DATASET.cases
        for outcome in outcomes_for_case(
            caso.case_id, caso.expected, DeterministicClassifier().propose(caso.subject)
        )
    ]

    assert evaluate(list(reversed(outcomes))) == evaluate(outcomes)


# --- La aritmética, comprobada a mano ------------------------------------------------


def test_mismas_ranuras_dan_mismas_metricas() -> None:
    """A mano: 3 aciertos, 1 equivocado, 1 sin propuesta y 2 abstenciones correctas."""
    informe = evaluate(
        _outcomes(hits=3, false_positives=1, missing=1, correct_abstentions=2, confidence=0.7)
    )
    metrics = informe.metrics_for(Axis.DOCUMENT_TYPE)

    assert (metrics.hits, metrics.false_positives, metrics.false_negatives) == (3, 1, 2)
    assert (metrics.precision, metrics.recall, metrics.f1) == (0.75, 0.6, 0.6667)
    assert metrics.corrections == 2
    assert informe.correct_abstentions == 2
    # 0,7 no llega a la banda alta: nada se aplicaría solo.
    assert metrics.auto_applied == 0
    assert metrics.calibration[0].proposals == 4
    assert metrics.calibration[0].hits == 3


def test_una_metrica_sin_denominador_es_indefinida_y_no_cero() -> None:
    """Un eje donde el motor no propone nada no tiene precisión: un cero sería una mentira."""
    informe = evaluate(_outcomes(missing=2, correct_abstentions=1))
    metrics = informe.metrics_for(Axis.DOCUMENT_TYPE)
    vacio = evaluate([])

    assert (metrics.precision, metrics.recall, metrics.f1) == (None, 0.0, 0.0)
    assert metrics.auto_applied_precision is None
    assert vacio.metrics_for(Axis.RIGHTS).precision is None
    assert vacio.unclassified_share is None
    assert vacio.unclassified_case_share is None


def test_un_valor_equivocado_cuenta_una_sola_correccion() -> None:
    """El humano arregla la ranura una vez, aunque sume un falso positivo y un falso negativo."""
    informe = evaluate(_outcomes(hits=1, false_positives=1))
    metrics = informe.metrics_for(Axis.DOCUMENT_TYPE)

    assert (metrics.false_positives, metrics.false_negatives) == (1, 1)
    assert metrics.corrections == 1
    assert len(informe.failures) == 1
    assert informe.failures[0].case_id == "equivocado-0"
    assert informe.failures[0].kind.value == "falso_positivo"


def test_dos_resultados_para_el_mismo_caso_y_eje_no_se_aceptan() -> None:
    """Dos filas del mismo caso y eje harían que las métricas no significaran nada."""
    repetido = _outcomes(hits=1)

    with pytest.raises(ValueError, match="dos resultados"):
        evaluate(repetido + repetido)

    with pytest.raises(ValueError, match="dos propuestas"):
        outcomes_for_case(
            "caso",
            dict.fromkeys(Axis),
            [_propuesta(Axis.DOCUMENT_TYPE, "convocation")] * 2,
        )


def test_una_propuesta_sin_confianza_no_se_puede_calibrar() -> None:
    """La calibración necesita la confianza declarada: sin ella la ranura no se construye."""
    with pytest.raises(ValueError, match="confianza"):
        AxisOutcome(case_id="caso", axis=Axis.TOPIC, expected=None, proposed="I.1")
    with pytest.raises(ValueError, match="entre 0 y 1"):
        AxisOutcome(case_id="caso", axis=Axis.TOPIC, expected="I.1", proposed="I.1", confidence=1.5)


def test_los_ejes_criticos_nunca_llegan_a_la_banda_que_decide_sola() -> None:
    """La parte que no depende del motor: `decides_itself` calla siempre en un eje crítico."""
    bandas = ConfidenceBands()
    motor = DeterministicClassifier()
    sujeto = ClassificationSubject(
        subject_type=SubjectType.ARTIFACT,
        subject_id="syn-cls-016",
        text="Boletín Oficial del Estado. Todos los derechos reservados.",
    )
    outcomes = outcomes_for_case("critico", dict.fromkeys(Axis), motor.propose(sujeto))
    informe = evaluate(outcomes, bands=bandas)

    assert {outcome.axis for outcome in outcomes if outcome.proposed is not None} == {
        Axis.AUTHORITY,
        Axis.RIGHTS,
    }
    for eje in (Axis.AUTHORITY, Axis.RIGHTS):
        assert bandas.decides_itself(0.99, axis=eje) is False
        assert informe.metrics_for(eje).auto_applied == 0
    assert informe.critical_wrong_automatic_promotions == 0


# --- Casos sin señales ----------------------------------------------------------------


def test_un_caso_sin_senales_cuenta_como_sin_clasificar_y_no_como_acierto() -> None:
    """Abstenerse no es acertar: cinco ranuras sin propuesta no pueden volverse cinco aciertos."""
    caso = DATASET.case("sin-senales-nota-cotidiana")
    outcomes = _outcomes_del_dataset(caso.case_id)
    informe = evaluate(outcomes)

    assert [outcome.proposed for outcome in outcomes] == [None] * len(Axis)
    assert caso.case_id in REPORT.unclassified_cases
    assert informe.unclassified_cases == (caso.case_id,)
    assert informe.unclassified_slots == len(Axis)
    assert informe.unclassified_with_expected == 0
    assert informe.correct_abstentions == len(Axis)
    for eje in Axis:
        metrics = informe.metrics_for(eje)
        assert (metrics.hits, metrics.proposed, metrics.precision) == (0, 0, None)
    # Un caso sin señales no mueve la aguja: ni aciertos, ni correcciones, ni promociones.
    assert informe.total_corrections == 0
    assert informe.wrong_automatic_promotions == 0


def test_el_caso_sin_senales_sin_texto_tampoco_genera_propuestas() -> None:
    """Un escaneo sin texto no es una excusa para rellenar: cero propuestas, cero correcciones."""
    caso = DATASET.case("sin-senales-escaneo-sin-texto")

    assert caso.subject.text == ""
    assert DeterministicClassifier().propose(caso.subject) == ()
    assert caso.case_id in REPORT.unclassified_cases


# --- El informe dice lo que falla -----------------------------------------------------


def test_el_informe_nombra_los_casos_fallados_en_lugar_de_esconderlos() -> None:
    """El texto del informe es la lista de trabajo: caso, eje, etiqueta humana y valor propuesto."""
    texto = format_report(DATASET, REPORT)

    assert len(REPORT.failures) == REPORT.total_corrections == 5
    assert (
        tuple((fallo.case_id, fallo.axis, fallo.kind.value) for fallo in REPORT.failures)
        == FALLOS_ESPERADOS
    )
    for case_id, eje, _ in FALLOS_ESPERADOS:
        assert f"- {case_id} [{eje.value}]" in texto
    assert "etiqueta private_syllabus, propuesto community_material" in texto
    assert "etiqueta IV.5, propuesto IV.2" in texto
    assert "etiqueta sin_clasificar, propuesto A" in texto
    assert "etiqueta curriculum, propuesto sin_clasificar" in texto
    assert UNCLASSIFIED in texto


def test_el_ejecutable_imprime_el_informe_con_los_casos_fallados(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """La herramienta que se ejecuta de verdad: sin argumentos, dataset versionado y código 0."""
    assert main([]) == 0
    salida = capsys.readouterr().out

    assert "Dataset sintético «1» · 15 casos · 75 ranuras (caso, eje)" in salida
    assert "Motor: determinista 1" in salida
    assert "precisión: 0.9000 · recall: 0.7500 · f1: 0.8182" in salida
    assert "Casos fallados (5):" in salida
    assert "promociones automáticas erróneas en ejes críticos: 0 (debe ser 0)" in salida
    for case_id in (
        "sin-senales-nota-cotidiana",
        "ambiguo-dos-temas",
        "ambiguo-apuntes-para-el-foro",
    ):
        assert case_id in salida
    # El informe no se limita a las medias: cada fallo llega con su nota del dataset.
    assert "solo se menciona un foro" in salida


# --- El dataset está bien formado y es honesto ---------------------------------------


def test_el_dataset_declara_las_cuatro_intenciones_y_cubre_las_etiquetas() -> None:
    """15 casos, cinco etiquetas cada uno y las cuatro intenciones, con sus notas."""
    assert len(DATASET.cases) == 15
    assert {caso.intent for caso in DATASET.cases} == set(INTENTS)
    assert [intencion for intencion, _ in DATASET.intents] == list(INTENTS)
    assert len({caso.case_id for caso in DATASET.cases}) == 15

    for caso in DATASET.cases:
        assert caso.note, f"El caso {caso.case_id} no explica por qué está en el dataset"
        assert set(caso.expected) == set(Axis)

    # Los casos «sin señales» tienen que serlo de verdad: el motor no propone nada y el humano
    # tampoco espera nada. Un caso mal etiquetado aquí sería una medida falsa.
    motor = DeterministicClassifier()
    sin_senales = [caso for caso in DATASET.cases if caso.intent == "sin_senales"]
    assert len(sin_senales) == 2
    for caso in sin_senales:
        assert motor.propose(caso.subject) == ()
        assert all(valor is None for valor in caso.expected.values())

    # Y tiene que haber al menos un caso donde el motor se equivoque: si no, no se mide nada.
    fallados = {fallo.case_id for fallo in REPORT.failures}
    intenciones_falladas = {caso.intent for caso in DATASET.cases if caso.case_id in fallados}
    assert "ambiguo" in intenciones_falladas
    assert "donde_falla" in intenciones_falladas


def test_el_dataset_no_contiene_rutas_del_disco_de_nadie() -> None:
    """Ni rutas del usuario ni material de terceros: el fixture es texto inventado para medir."""
    crudo = DATASET_PATH.read_text(encoding="utf-8")

    # `\b` para no confundir «https:/» con una unidad de disco: una ruta de Windows empieza por una
    # letra suelta seguida de dos puntos.
    assert not re.search(r"\b[A-Za-z]:[\\/]", crudo), "Hay una ruta con unidad de disco"
    assert "\\" not in crudo, "Hay una ruta con barras invertidas de Windows"
    for carpeta in ("/Users/", "/home/", "OneDrive", "Desktop", "Descargas"):
        assert carpeta not in crudo, f"El dataset nombra una carpeta del usuario: {carpeta}"
    # El único dominio con forma real es el identificador inventado que prueba la regla de
    # procedencia oficial; el resto de casos no llevan procedencia.
    assert crudo.count("https://") == 1


def test_una_ruta_de_dataset_inexistente_o_mal_formada_falla_en_voz_alta(tmp_path) -> None:
    """La herramienta no se inventa un informe: si el dataset no está o está roto, lo dice."""
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "no-existe.json")

    roto = tmp_path / "roto.json"
    roto.write_text(
        json.dumps({"dataset_version": "1", "description": "sin perfiles", "cases": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="profiles"):
        load_dataset(roto)


@pytest.mark.parametrize(
    ("campo", "valor", "mensaje"),
    [
        ("cases[0].intent", "facilísimo", "Intención no reconocida"),
        ("cases[0].expected.document_type", "resumen_inventado", "no es un valor válido"),
        ("cases[0].expected.authority", "Z", "no es un valor válido"),
        ("cases[0].subject.origin_type", "pegado", "no es un tipo de origen válido"),
        ("cases[0].subject.subject_type", "documento", "no es un tipo de sujeto válido"),
    ],
)
def test_una_etiqueta_o_un_valor_fuera_de_vocabulario_no_se_acepta(
    campo: str, valor: object, mensaje: str, tmp_path
) -> None:
    """Un valor inventado en el dataset se rechaza al cargarlo, no se mide en silencio."""
    crudo = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    partes = campo.split(".")
    destino = crudo
    for parte in partes[:-1]:
        if parte.startswith("cases["):
            destino = destino["cases"][int(parte[6:-1])]
        else:
            destino = destino[parte]
    destino[partes[-1]] = valor
    alterado = tmp_path / "alterado.json"
    alterado.write_text(json.dumps(crudo, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match=mensaje):
        load_dataset(alterado)


# --- el motor que se mide (PoC de un motor de decisiones) --------------------------------------


class _MotorDeMentira:
    """Un motor que no existe, para probar que el arnés mide el que le dicen y lo dice.

    Cumple el puerto sin heredar de nada —nombre, versión y `propose`—, que es justo lo que hará el
    motor del PoC: registrarse aquí **en su propia rama** sin que el producto dependa de él.
    """

    name = "de-mentira"
    version = "9"

    def propose(self, subject: ClassificationSubject) -> Sequence[Proposal]:
        return list(DeterministicClassifier().propose(subject))


def test_el_arnes_mide_el_motor_que_le_dicen_y_lo_dice_en_el_informe() -> None:
    """Dos informes sin autor no se pueden comparar: el PoC mide tres motores y los nombra.

    El motor de mentira delega en el determinista, así que los números tienen que ser los mismos y
    lo único que cambia es de quién son.
    """
    motor = _MotorDeMentira()

    informe = format_report(DATASET, build_report(DATASET, engine=motor), engine=motor)

    assert "Motor: de-mentira 9" in informe
    assert "precisión: 0.9000 · recall: 0.7500 · f1: 0.8182" in informe


def test_un_motor_desconocido_no_cae_en_silencio_al_de_siempre() -> None:
    """Un nombre mal escrito tiene que doler: medir otro motor y llamarlo determinista es mentir."""
    assert build_engine(DEFAULT_ENGINE).name == DeterministicClassifier.name

    with pytest.raises(
        ValueError, match=r"Motor desconocido: «no-existe»\. Disponibles: determinista"
    ):
        build_engine("no-existe")


def test_las_opciones_se_leen_todas_y_no_solo_la_primera() -> None:
    """`--engine` detrás de `--dataset` se ignoraba en silencio: el informe salía de otro motor.

    Y una opción que no existe se rechaza, en lugar de ignorarse: en un arnés que existe para
    comparar motores, leer mal una opción es un informe falso.
    """
    args = ["--dataset", "otro.json", "--engine", "determinista"]

    assert dataset_argument(args) == Path("otro.json")
    assert engine_argument(args) == "determinista"
    assert engine_argument([]) == DEFAULT_ENGINE

    with pytest.raises(ValueError, match="«--engine» necesita un valor"):
        engine_argument(["--engine"])
    with pytest.raises(ValueError, match="Argumento no reconocido"):
        engine_argument(["--motor", "determinista"])
