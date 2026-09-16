"""Métricas de calidad de la clasificación (10_TEST-PLAN §7): dominio puro y determinista.

Qué se mide aquí y por qué de esta forma:

- **Precisión, recall y F1 por eje.** El eje se mide como una decisión: o se propone el valor
  correcto, o se propone otro (falso positivo), o no se propone nada cuando hacía falta (falso
  negativo). Un valor equivocado cuenta a la vez como falso positivo y como falso negativo, que es
  la convención de un problema de etiqueta única y la única que no maquilla el recall.
- **Matriz de confusión** con una casilla `sin_clasificar` para la abstención del motor y otra para
  la etiqueta humana ausente: así se ve *qué* se confunde con *qué*, y no solo cuántas veces.
- **Calibración de confianza.** La confianza declarada sirve de poco si no se comprueba: se agrupa
  en cubos de 0,2 y se compara con el acierto real. Un cubo con confianza alta y acierto bajo es la
  señal de que el umbral está mal puesto.
- **Precisión de las propuestas que la banda aplicaría sola** (`ConfidenceBands.decides_itself`). En
  los ejes críticos el resultado es siempre cero propuestas autoaplicadas: autoridad y derechos se
  confirman siempre (04 §8). Eso también se cuenta, porque es la puerta inicial del plan de pruebas.
- **Porcentaje sin clasificar.** Se cuentan las ranuras (caso, eje) sin propuesta sobre el total.
  Se separa en dos: las abstenciones correctas (el humano tampoco esperaba valor) y las que dejan
  material sin cubrir. Sin esa separación, «sin clasificar» mezcla dos cosas opuestas.
- **Correcciones necesarias.** Una por ranura que no queda como el humano dice: proponer un valor
  equivocado, proponer donde no había nada o no proponer donde hacía falta. Es el trabajo humano que
  va a costar el lote, no una estimación de minutos. La lista de fallos trae exactamente esa lista
  de trabajo —una fila por ranura—, aunque en los contadores un valor equivocado sume en dos sitios.

Lo que **no** se mide aquí, y por qué: «minutos por 100 elementos» necesita que una persona
cronometre una muestra real. Deducirlo del dataset sintético daría un número inventado, y un número
inventado en un informe de calidad es peor que no tenerlo.

Todo es determinista: sin azar, sin reloj, sin base de datos y sin red. El informe se ordena por
caso y eje, y las medias se redondean a cuatro decimales para que dos ejecuciones den exactamente el
mismo texto.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from opofuente.domain.classification import CRITICAL_AXES, Axis, ConfidenceBands, Proposal

#: Etiqueta que representa «no hay valor»: ni etiqueta humana ni propuesta. Se usa en la matriz de
#: confusión para que una abstención sea una casilla más y no un hueco invisible.
UNCLASSIFIED = "sin_clasificar"

#: Bordes de los cubos de calibración: cinco cubos de anchura 0,2, con el último cerrado en 1,0.
#: Son fijos a propósito: dos motores solo se pueden comparar con los mismos cubos.
CALIBRATION_EDGES: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)

#: Nombre de cada eje para los informes en texto.
AXIS_LABELS: Mapping[Axis, str] = {
    Axis.DOCUMENT_TYPE: "tipo documental",
    Axis.OPPOSITION: "oposición",
    Axis.TOPIC: "tema",
    Axis.AUTHORITY: "autoridad",
    Axis.RIGHTS: "derechos",
}


class FailureKind(StrEnum):
    """Por qué una ranura no queda como el humano dice que debería quedar."""

    FALSE_POSITIVE = "falso_positivo"
    FALSE_NEGATIVE = "falso_negativo"


#: Motivo que se imprime para cada tipo de fallo (el informe nombra el caso, no solo el eje).
FAILURE_LABELS: Mapping[FailureKind, str] = {
    FailureKind.FALSE_POSITIVE: "propuesta equivocada",
    FailureKind.FALSE_NEGATIVE: "etiqueta sin cubrir",
}


@dataclass(frozen=True, slots=True)
class AxisOutcome:
    """Resultado de un caso en un eje: lo que dice el humano y lo que propuso el motor.

    `expected` es la etiqueta humana y `proposed` el valor del motor; `None` en cualquiera de los
    dos significa «no hay valor». Una ranura con propuesta **siempre** trae confianza: una propuesta
    sin confianza declarada no se puede calibrar y se rechaza al construirla.
    """

    case_id: str
    axis: Axis
    expected: str | None
    proposed: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("Un resultado necesita caso")
        if (self.proposed is None) is not (self.confidence is None):
            raise ValueError("Una propuesta sin confianza no se puede calibrar")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("La confianza debe estar entre 0 y 1")

    @property
    def is_hit(self) -> bool:
        """¿El motor propuso exactamente lo que el humano etiqueta?"""
        return self.expected is not None and self.expected == self.proposed

    @property
    def is_false_positive(self) -> bool:
        """El motor propuso un valor, pero no el correcto (o propuso donde no había nada)."""
        return self.proposed is not None and self.proposed != self.expected

    @property
    def is_false_negative(self) -> bool:
        """La etiqueta humana no aparece en lo propuesto: no se propuso, o se propuso otra cosa."""
        return self.expected is not None and self.proposed != self.expected

    @property
    def is_unclassified(self) -> bool:
        """El motor no propuso nada en este eje."""
        return self.proposed is None

    @property
    def is_correct_abstention(self) -> bool:
        """Ni el humano esperaba valor ni el motor lo propuso: abstenerse era lo correcto."""
        return self.expected is None and self.proposed is None

    @property
    def is_correction(self) -> bool:
        """¿Esta ranura necesita que una persona la arregle? Una corrección por ranura, no dos."""
        return not self.is_hit and not self.is_correct_abstention


def outcomes_for_case(
    case_id: str,
    expected: Mapping[Axis, str | None],
    proposals: Sequence[Proposal],
) -> tuple[AxisOutcome, ...]:
    """Un resultado por eje —los cinco— a partir de las propuestas del motor para un caso.

    Se emite una fila por eje **aunque el motor no proponga nada**: «sin propuesta» es justo lo que
    se quiere medir, y omitirlo inflaría la precisión sin que nadie lo notara.
    """
    por_eje: dict[Axis, Proposal] = {}
    for propuesta in proposals:
        if propuesta.axis in por_eje:
            raise ValueError(
                f"El caso «{case_id}» tiene dos propuestas del motor en el eje "
                f"{propuesta.axis.value}: las métricas no pueden elegir una por su cuenta"
            )
        por_eje[propuesta.axis] = propuesta
    filas: list[AxisOutcome] = []
    for eje in Axis:
        encontrada = por_eje.get(eje)
        filas.append(
            AxisOutcome(
                case_id=case_id,
                axis=eje,
                expected=expected.get(eje),
                proposed=None if encontrada is None else encontrada.proposed_value,
                confidence=None if encontrada is None else encontrada.confidence,
            )
        )
    return tuple(filas)


@dataclass(frozen=True, slots=True)
class ConfusionCell:
    """Casilla de la matriz de confusión: etiqueta humana frente a valor propuesto."""

    expected: str
    proposed: str
    count: int


@dataclass(frozen=True, slots=True)
class CalibrationBucket:
    """Cubo de calibración: cuántas propuestas caen en ese tramo y cuántas acertaron.

    `accuracy` es `None` cuando el cubo está vacío: un cubo sin propuestas no acierta el 0 %, no
    dice nada.
    """

    lower: float
    upper: float
    proposals: int
    hits: int

    @property
    def accuracy(self) -> float | None:
        return _ratio(self.hits, self.proposals)


@dataclass(frozen=True, slots=True)
class FailedOutcome:
    """Ranura fallada, con nombre y apellidos, para que el informe no esconda nada."""

    case_id: str
    axis: Axis
    kind: FailureKind
    expected: str | None
    proposed: str | None
    confidence: float | None


@dataclass(frozen=True, slots=True)
class AxisMetrics:
    """Todo lo que el plan de pruebas pide de un eje."""

    axis: Axis
    expected: int
    proposed: int
    hits: int
    false_positives: int
    false_negatives: int
    correct_abstentions: int
    unclassified: int
    unclassified_missing_expected: int
    precision: float | None
    recall: float | None
    f1: float | None
    corrections: int
    auto_applied: int
    auto_applied_hits: int
    auto_applied_precision: float | None
    wrong_automatic_promotions: int
    critical_wrong_automatic_promotions: int
    confusion: tuple[ConfusionCell, ...] = ()
    calibration: tuple[CalibrationBucket, ...] = ()

    @property
    def label(self) -> str:
        return AXIS_LABELS[self.axis]


@dataclass(frozen=True, slots=True)
class ClassificationReport:
    """Informe completo del conjunto: por eje, más los totales y los casos fallados."""

    case_count: int
    slot_count: int
    axes: tuple[AxisMetrics, ...]
    failures: tuple[FailedOutcome, ...]
    unclassified_cases: tuple[str, ...]
    unclassified_slots: int
    unclassified_with_expected: int
    correct_abstentions: int

    @property
    def unclassified_share(self) -> float | None:
        """Porcentaje de ranuras (caso, eje) que el motor dejó sin propuesta."""
        return _ratio(self.unclassified_slots, self.slot_count)

    @property
    def unclassified_case_share(self) -> float | None:
        """Porcentaje de casos que no reciben ninguna propuesta."""
        return _ratio(len(self.unclassified_cases), self.case_count)

    @property
    def total_corrections(self) -> int:
        return sum(metrics.corrections for metrics in self.axes)

    @property
    def wrong_automatic_promotions(self) -> int:
        return sum(metrics.wrong_automatic_promotions for metrics in self.axes)

    @property
    def critical_wrong_automatic_promotions(self) -> int:
        """Puerta inicial del plan de pruebas: tiene que ser cero."""
        return sum(metrics.critical_wrong_automatic_promotions for metrics in self.axes)

    def metrics_for(self, axis: Axis) -> AxisMetrics:
        """Métricas de un eje. Si el eje no se midió, falla: un informe incompleto no se rellena."""
        for metrics in self.axes:
            if metrics.axis is axis:
                return metrics
        raise KeyError(axis.value)


def evaluate(
    outcomes: Sequence[AxisOutcome],
    *,
    bands: ConfidenceBands | None = None,
) -> ClassificationReport:
    """Calcula el informe completo a partir de las ranuras (caso, eje).

    El resultado no depende del orden de entrada: las ranuras se ordenan antes de contar, de modo
    que dos ejecuciones (o dos ficheros con las mismas filas en otro orden) dan el mismo informe.
    """
    cubos = ConfidenceBands() if bands is None else bands
    ordenados = sorted(outcomes, key=lambda resultado: (resultado.case_id, resultado.axis.value))
    _reject_duplicate_slots(ordenados)

    ejes = tuple(
        _axis_metrics(
            eje,
            [resultado for resultado in ordenados if resultado.axis is eje],
            cubos,
        )
        for eje in Axis
    )
    casos = sorted({resultado.case_id for resultado in ordenados})
    return ClassificationReport(
        case_count=len(casos),
        slot_count=len(ordenados),
        axes=ejes,
        failures=tuple(_failures(ordenados)),
        unclassified_cases=tuple(
            caso
            for caso in casos
            if all(
                resultado.is_unclassified for resultado in ordenados if resultado.case_id == caso
            )
        ),
        unclassified_slots=sum(1 for resultado in ordenados if resultado.is_unclassified),
        unclassified_with_expected=sum(
            1
            for resultado in ordenados
            if resultado.is_unclassified and resultado.expected is not None
        ),
        correct_abstentions=sum(1 for resultado in ordenados if resultado.is_correct_abstention),
    )


def _axis_metrics(
    axis: Axis,
    outcomes: Sequence[AxisOutcome],
    bands: ConfidenceBands,
) -> AxisMetrics:
    propuestas = [resultado for resultado in outcomes if resultado.proposed is not None]
    autoaplicadas = [
        resultado
        for resultado in propuestas
        if resultado.confidence is not None
        and bands.decides_itself(resultado.confidence, axis=axis)
    ]
    aciertos = sum(1 for resultado in outcomes if resultado.is_hit)
    falsos_positivos = sum(1 for resultado in outcomes if resultado.is_false_positive)
    falsos_negativos = sum(1 for resultado in outcomes if resultado.is_false_negative)
    autoaciertos = sum(1 for resultado in autoaplicadas if resultado.is_hit)
    return AxisMetrics(
        axis=axis,
        expected=sum(1 for resultado in outcomes if resultado.expected is not None),
        proposed=len(propuestas),
        hits=aciertos,
        false_positives=falsos_positivos,
        false_negatives=falsos_negativos,
        correct_abstentions=sum(1 for resultado in outcomes if resultado.is_correct_abstention),
        unclassified=sum(1 for resultado in outcomes if resultado.is_unclassified),
        unclassified_missing_expected=sum(
            1
            for resultado in outcomes
            if resultado.is_unclassified and resultado.expected is not None
        ),
        precision=_ratio(aciertos, aciertos + falsos_positivos),
        recall=_ratio(aciertos, aciertos + falsos_negativos),
        f1=_ratio(2 * aciertos, 2 * aciertos + falsos_positivos + falsos_negativos),
        corrections=sum(1 for resultado in outcomes if resultado.is_correction),
        auto_applied=len(autoaplicadas),
        auto_applied_hits=autoaciertos,
        auto_applied_precision=_ratio(autoaciertos, len(autoaplicadas)),
        wrong_automatic_promotions=sum(1 for resultado in autoaplicadas if not resultado.is_hit),
        # En un eje crítico `decides_itself` nunca es verdadero; el contador existe para que, si
        # algún día alguien cambia las bandas, la puerta del plan de pruebas lo diga en voz alta.
        critical_wrong_automatic_promotions=sum(
            1 for resultado in autoaplicadas if not resultado.is_hit and axis in CRITICAL_AXES
        ),
        confusion=_confusion(outcomes),
        calibration=_calibration(propuestas),
    )


def _failures(outcomes: Sequence[AxisOutcome]) -> list[FailedOutcome]:
    """Una entrada por ranura fallada: los fallos se nombran, no solo se cuentan.

    Un valor equivocado es a la vez falso positivo y falso negativo en los contadores —así lo exige
    la convención de etiqueta única—, pero aquí aparece **una vez**: el informe es la lista de
    trabajo de una persona, y nadie arregla la misma ranura dos veces.
    """
    fallos: list[FailedOutcome] = []
    for resultado in outcomes:
        if resultado.is_false_positive:
            tipo = FailureKind.FALSE_POSITIVE
        elif resultado.is_false_negative:
            tipo = FailureKind.FALSE_NEGATIVE
        else:
            continue
        fallos.append(
            FailedOutcome(
                case_id=resultado.case_id,
                axis=resultado.axis,
                kind=tipo,
                expected=resultado.expected,
                proposed=resultado.proposed,
                confidence=resultado.confidence,
            )
        )
    return fallos


def _confusion(outcomes: Sequence[AxisOutcome]) -> tuple[ConfusionCell, ...]:
    """Matriz de confusión agregada por par (etiqueta, propuesta), en orden determinista."""
    conteo: dict[tuple[str, str], int] = {}
    for resultado in outcomes:
        clave = (
            resultado.expected if resultado.expected is not None else UNCLASSIFIED,
            resultado.proposed if resultado.proposed is not None else UNCLASSIFIED,
        )
        conteo[clave] = conteo.get(clave, 0) + 1
    return tuple(
        ConfusionCell(expected=esperado, proposed=propuesto, count=count)
        for (esperado, propuesto), count in sorted(conteo.items())
    )


def _calibration(proposals: Sequence[AxisOutcome]) -> tuple[CalibrationBucket, ...]:
    """Cubos de confianza frente a acierto real. Los cubos vacíos no se informan."""
    por_cubo: dict[int, list[AxisOutcome]] = {}
    for resultado in proposals:
        if resultado.confidence is None:
            continue
        por_cubo.setdefault(_bucket_index(resultado.confidence), []).append(resultado)
    return tuple(
        CalibrationBucket(
            lower=CALIBRATION_EDGES[indice],
            upper=CALIBRATION_EDGES[indice + 1],
            proposals=len(filas),
            hits=sum(1 for fila in filas if fila.is_hit),
        )
        for indice, filas in sorted(por_cubo.items())
    )


def _bucket_index(confidence: float) -> int:
    """Cubo de una confianza. El límite superior pertenece al cubo de arriba, y 1,0 al último."""
    for indice in range(len(CALIBRATION_EDGES) - 1):
        if confidence < CALIBRATION_EDGES[indice + 1]:
            return indice
    return len(CALIBRATION_EDGES) - 2


def _reject_duplicate_slots(outcomes: Sequence[AxisOutcome]) -> None:
    """Dos filas para el mismo caso y eje harían que los números no signifiquen nada."""
    vistos: set[tuple[str, Axis]] = set()
    for resultado in outcomes:
        clave = (resultado.case_id, resultado.axis)
        if clave in vistos:
            raise ValueError(
                f"El caso «{resultado.case_id}» tiene dos resultados en el eje "
                f"{resultado.axis.value}"
            )
        vistos.add(clave)


def _ratio(numerator: int, denominator: int) -> float | None:
    """Una métrica sin denominador no es cero: es indefinida, y así se informa."""
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)
