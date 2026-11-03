"""Informe reproducible de calidad de la clasificación sobre el dataset sintético etiquetado.

Por qué existe: el criterio de aceptación de S04 dice «dataset sintético produce métricas
reproducibles», y eso exige dos piezas que se ejecuten de verdad —un conjunto etiquetado a mano y un
cálculo que no dependa de nadie—. Este módulo carga el dataset de `fixtures/synthetic`, pasa cada
caso por el motor determinista real y imprime el informe del plan de pruebas (§7).

Uso:
    uv run python -m opofuente.tools.classification_metrics
    uv run python -m opofuente.tools.classification_metrics --dataset <ruta.json>
    uv run python -m opofuente.tools.classification_metrics --engine <nombre>

`--engine` elige qué motor se mide, por su nombre registrado en `ENGINES`. Hoy solo hay uno —el
determinista—, y ese es el default; el PoC de un motor de decisiones añade el suyo **en su propia
rama** y lo registra aquí, sin que el producto pase a depender de él. El informe dice siempre qué
motor y versión produjeron los números, porque dos informes que no dicen de quién son no comparan
nada: `evaluate` y `build_report` aceptan cualquier `ClassifierPort`.

Sale con código 1 si se incumple la puerta inicial de §7 (cero promociones automáticas erróneas en
ejes críticos): una puerta que solo se imprime, sin cambiar el código de salida, no es una puerta.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opofuente.application.ports import ClassifierPort
from opofuente.config import project_root
from opofuente.domain.artifacts import OriginType
from opofuente.domain.classification import (
    Axis,
    ClassificationSubject,
    ProfileCandidate,
    SubjectType,
    TopicCandidate,
    value_matches_axis,
)
from opofuente.domain.classification_metrics import (
    FAILURE_LABELS,
    UNCLASSIFIED,
    AxisMetrics,
    AxisOutcome,
    ClassificationReport,
    evaluate,
    outcomes_for_case,
)
from opofuente.infrastructure.classifiers import DeterministicClassifier

#: Dataset versionado con el que se mide. Vive en fixtures porque es material de prueba, no datos de
#: la aplicación: el informe no lee la base de datos ni el material del usuario.
DATASET_PATH = project_root() / "fixtures" / "synthetic" / "classification" / "dataset.json"

#: Intenciones que un caso puede declarar. Se validan porque un caso «sin señales» mal escrito (o un
#: «facil» que en realidad es ambiguo) sesgaría la medida sin dejar rastro.
INTENTS: tuple[str, ...] = ("facil", "ambiguo", "sin_senales", "donde_falla")

_SUBJECT_KEYS = frozenset(
    {
        "subject_type",
        "subject_id",
        "text",
        "original_name",
        "media_type",
        "origin_type",
        "origin_display",
    }
)
_PROFILE_KEYS = frozenset({"opposition_code", "opposition_name", "convocation_code", "topics"})
_TOPIC_KEYS = frozenset({"node_id", "path", "title", "depth"})
_DATASET_KEYS = frozenset({"dataset_version", "description", "label_rules", "profiles", "cases"})
_CASE_KEYS = frozenset({"id", "intent", "note", "subject", "expected"})


@dataclass(frozen=True, slots=True)
class DatasetCase:
    """Un caso etiquetado: el material que se le da al motor y lo que debería salir de él."""

    case_id: str
    intent: str
    note: str
    subject: ClassificationSubject
    expected: Mapping[Axis, str | None]


@dataclass(frozen=True, slots=True)
class SyntheticDataset:
    """Dataset completo: versión, perfiles compartidos y casos."""

    dataset_version: str
    description: str
    cases: tuple[DatasetCase, ...]

    @property
    def intents(self) -> tuple[tuple[str, int], ...]:
        """Cuántos casos hay de cada intención, en el orden declarado y solo con las usadas."""
        return tuple(
            (intencion, sum(1 for caso in self.cases if caso.intent == intencion))
            for intencion in INTENTS
            if any(caso.intent == intencion for caso in self.cases)
        )

    def case(self, case_id: str) -> DatasetCase:
        """Caso por identificador. Falla si no existe en lugar de devolver algo parecido."""
        for caso in self.cases:
            if caso.case_id == case_id:
                return caso
        raise KeyError(case_id)


def load_dataset(path: Path | None = None) -> SyntheticDataset:
    """Lee y valida el dataset etiquetado.

    Se valida a mano y sin piedad: un campo mal escrito, una etiqueta fuera del vocabulario del eje,
    o una etiqueta que falta dejarían el informe midiendo otra cosa. Y eso, en un conjunto que
    existe para fijar números, es peor que fallar.
    """
    ruta = DATASET_PATH if path is None else path
    crudo: Any = json.loads(ruta.read_text(encoding="utf-8"))
    raiz = _as_mapping(crudo, campo=str(ruta))
    _reject_unknown(raiz, _DATASET_KEYS, campo=str(ruta))
    version = _as_text(_field(raiz, "dataset_version"), campo="dataset_version")
    description = _as_text(_field(raiz, "description"), campo="description")
    perfiles = tuple(
        _profile(item, index=indice)
        for indice, item in enumerate(_as_sequence(_field(raiz, "profiles"), campo="profiles"))
    )
    casos = tuple(
        _case(item, index=indice, profiles=perfiles)
        for indice, item in enumerate(_as_sequence(_field(raiz, "cases"), campo="cases"))
    )
    identificadores = [caso.case_id for caso in casos]
    if len(set(identificadores)) != len(identificadores):
        raise ValueError("Hay identificadores de caso repetidos en el dataset")
    return SyntheticDataset(dataset_version=version, description=description, cases=casos)


#: Motores que este arnés puede medir, por nombre. Un motor externo —el del PoC de un motor de
#: decisiones— se registra aquí **en su propia rama**: el producto no depende de él, y el arnés solo
#: lo necesita para comparar. Registrar y medir es todo lo que hace falta: `evaluate` no sabe de
#: motores concretos.
ENGINES: Mapping[str, Callable[[], ClassifierPort]] = {
    "determinista": DeterministicClassifier,
}

#: Motor que se mide si no se dice otro: el que tiene el producto hoy.
DEFAULT_ENGINE = "determinista"


def build_engine(name: str) -> ClassifierPort:
    """El motor registrado con ese nombre, o un error que dice cuáles hay.

    Un nombre mal escrito **no** puede caer al motor de siempre en silencio: el informe saldría con
    los números de otro motor y con el nombre del otro motor, y eso no es un informe, es una trampa.
    """
    constructor = ENGINES.get(name)
    if constructor is None:
        disponibles = ", ".join(sorted(ENGINES))
        raise ValueError(f"Motor desconocido: «{name}». Disponibles: {disponibles}")
    return constructor()


def build_report(
    dataset: SyntheticDataset,
    *,
    engine: ClassifierPort | None = None,
) -> ClassificationReport:
    """Ejecuta el motor sobre cada caso y calcula las métricas del conjunto completo.

    El motor se construye aquí y no se le inyecta nada: no usa azar, ni reloj, ni red, así que dos
    ejecuciones sobre el mismo dataset dan el mismo informe. Es lo que hace que estas métricas
    sirvan como referencia y no como una foto del día.
    """
    motor: ClassifierPort = DeterministicClassifier() if engine is None else engine
    resultados: list[AxisOutcome] = []
    for caso in dataset.cases:
        propuestas = motor.propose(caso.subject)
        resultados.extend(outcomes_for_case(caso.case_id, caso.expected, propuestas))
    return evaluate(resultados)


def format_report(
    dataset: SyntheticDataset,
    report: ClassificationReport,
    *,
    engine: ClassifierPort | None = None,
) -> str:
    """Informe en texto: por eje los números, y después los totales y los casos fallados.

    El motor y su versión se imprimen porque dos informes sin autor no se pueden comparar: el PoC
    mide tres motores distintos sobre el mismo dataset y el número tiene que decir de quién es.
    """
    motor: ClassifierPort = DeterministicClassifier() if engine is None else engine
    lineas = [
        f"Dataset sintético «{dataset.dataset_version}» · {report.case_count} casos · "
        f"{report.slot_count} ranuras (caso, eje)",
        f"Motor: {motor.name} {motor.version}",
        "Casos por intención: "
        + " · ".join(f"{intencion} {total}" for intencion, total in dataset.intents),
        "",
    ]
    for metrics in report.axes:
        lineas.extend(_axis_lines(metrics))
    lineas.extend(_global_lines(dataset, report))
    return "\n".join(lineas).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada: imprime el informe y devuelve 1 si la puerta inicial no se cumple."""
    _use_utf8_stdout()
    args = list(sys.argv[1:] if argv is None else argv)
    engine = build_engine(engine_argument(args))
    dataset = load_dataset(dataset_argument(args))
    report = build_report(dataset, engine=engine)
    print(format_report(dataset, report, engine=engine))
    if report.critical_wrong_automatic_promotions:
        print(
            "Puerta incumplida (10_TEST-PLAN §7): hay promociones automáticas erróneas en un eje "
            "crítico y ninguna puede llegar sola a la aplicación.",
            file=sys.stderr,
        )
        return 1
    return 0


def _use_utf8_stdout() -> None:
    """El informe lleva acentos, comillas angulares y rayas.

    En Windows, cuando la salida va a un fichero o a otra herramienta, Python usa la codificación
    local del sistema (cp1252) y el texto sale distinto en cada máquina. Un informe de métricas que
    se quiere reproducir tiene que ser el mismo en todas: se fija UTF-8. Si la salida no se puede
    reconfigurar (una prueba que sustituye `sys.stdout`), se deja tal cual.
    """
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


#: Opciones que acepta el arnés. Cualquier otra cosa se rechaza: ver `_option`.
_OPTIONS = ("--dataset", "--engine")


def _option(args: Sequence[str], name: str) -> str | None:
    """Valor de la opción `--nombre valor`, o `None` si no se indica.

    Se recorren **todas** las opciones antes de devolver nada. Antes esta función volvía en cuanto
    encontraba `--dataset`, así que un `--engine` escrito detrás de él se ignoraba sin decir nada y
    el informe salía con los números del motor de siempre: en un arnés que existe para comparar
    motores, eso no es una comodidad, es un informe falso.
    """
    valor: str | None = None
    indice = 0
    while indice < len(args):
        argumento = args[indice]
        if argumento not in _OPTIONS:
            raise ValueError(f"Argumento no reconocido: «{argumento}»")
        if indice + 1 >= len(args):
            raise ValueError(f"«{argumento}» necesita un valor")
        if argumento == name:
            valor = args[indice + 1]
        indice += 2
    return valor


def dataset_argument(args: Sequence[str]) -> Path | None:
    """Ruta indicada con `--dataset`, o `None` para usar el dataset versionado."""
    ruta = _option(args, "--dataset")
    return None if ruta is None else Path(ruta)


def engine_argument(args: Sequence[str]) -> str:
    """Motor indicado con `--engine`, o `None` para el que tiene el producto hoy."""
    return _option(args, "--engine") or DEFAULT_ENGINE


def _axis_lines(metrics: AxisMetrics) -> list[str]:
    lineas = [
        f"[{metrics.axis.value}] {metrics.label}",
        f"  etiquetas humanas: {metrics.expected} · propuestas: {metrics.proposed}",
        f"  precisión: {_number(metrics.precision)} · recall: {_number(metrics.recall)} · "
        f"f1: {_number(metrics.f1)}",
        f"  aciertos: {metrics.hits} · falsos positivos: {metrics.false_positives} · "
        f"falsos negativos: {metrics.false_negatives} · abstenciones correctas: "
        f"{metrics.correct_abstentions}",
        f"  sin propuesta: {metrics.unclassified} "
        f"(de ellas, con etiqueta humana: {metrics.unclassified_missing_expected})",
        f"  correcciones necesarias: {metrics.corrections}",
        f"  autoaplicadas: {metrics.auto_applied} · aciertos: {metrics.auto_applied_hits} · "
        f"precisión: {_number(metrics.auto_applied_precision)} · promociones erróneas: "
        f"{metrics.wrong_automatic_promotions} (en ejes críticos: "
        f"{metrics.critical_wrong_automatic_promotions})",
    ]
    if metrics.confusion:
        lineas.append("  matriz de confusión (etiqueta humana -> valor propuesto):")
        lineas.extend(
            f"    {cell.expected} -> {cell.proposed}: {cell.count}" for cell in metrics.confusion
        )
    if metrics.calibration:
        lineas.append("  calibración (confianza declarada -> acierto real):")
        lineas.extend(
            f"    confianza {bucket.lower:.1f} a {bucket.upper:.1f}: "
            f"{bucket.proposals} propuestas, {bucket.hits} aciertos, "
            f"acierto {_number(bucket.accuracy)}"
            for bucket in metrics.calibration
        )
    lineas.append("")
    return lineas


def _global_lines(dataset: SyntheticDataset, report: ClassificationReport) -> list[str]:
    notas = {caso.case_id: caso.note for caso in dataset.cases}
    lineas = [
        "Conjunto",
        f"  sin clasificar: {report.unclassified_slots} de {report.slot_count} ranuras "
        f"({_percent(report.unclassified_share)}) · de ellas, abstenciones correctas: "
        f"{report.correct_abstentions} · material sin cubrir: {report.unclassified_with_expected}",
        f"  casos sin ninguna propuesta: {len(report.unclassified_cases)} de {report.case_count} "
        f"({_percent(report.unclassified_case_share)})",
        f"  correcciones necesarias: {report.total_corrections}",
        f"  promociones automáticas erróneas (ejes no críticos): "
        f"{report.wrong_automatic_promotions}",
        f"  puerta §7 · promociones automáticas erróneas en ejes críticos: "
        f"{report.critical_wrong_automatic_promotions} (debe ser 0)",
        "",
        f"Casos fallados ({len(report.failures)}):",
    ]
    if not report.failures:
        lineas.append("  ninguno")
    for fallo in report.failures:
        lineas.append(
            f"  - {fallo.case_id} [{fallo.axis.value}] {FAILURE_LABELS[fallo.kind]}: "
            f"etiqueta {_value(fallo.expected)}, propuesto {_value(fallo.proposed)}, "
            f"confianza {_number(fallo.confidence)}"
        )
        nota = notas.get(fallo.case_id)
        if nota:
            lineas.append(f"      {nota}")
    lineas.append("")
    lineas.append("Casos sin ninguna propuesta:")
    if not report.unclassified_cases:
        lineas.append("  ninguno")
    for case_id in report.unclassified_cases:
        lineas.append(f"  - {case_id}")
        nota = notas.get(case_id)
        if nota:
            lineas.append(f"      {nota}")
    return lineas


def _value(value: str | None) -> str:
    """Etiqueta o propuesta para imprimir: la abstención se nombra, no se deja en blanco."""
    return UNCLASSIFIED if value is None else value


def _number(value: float | None) -> str:
    """Número para imprimir. Una métrica indefinida se dice con una raya, no con un cero falso."""
    return "—" if value is None else f"{value:.4f}"


def _percent(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f} %"


def _field(raw: Mapping[str, Any], key: str) -> Any:
    if key not in raw:
        raise ValueError(f"Falta el campo obligatorio «{key}»")
    return raw[key]


def _reject_unknown(raw: Mapping[str, Any], allowed: frozenset[str], *, campo: str) -> None:
    """Un campo que no se reconoce es casi siempre una errata, y una errata aquí mide otra cosa."""
    desconocidos = sorted(set(raw) - allowed)
    if desconocidos:
        raise ValueError(f"Campos no reconocidos en «{campo}»: {', '.join(desconocidos)}")


def _as_mapping(value: Any, *, campo: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"«{campo}» debe ser un objeto JSON")
    return {str(clave): item for clave, item in value.items()}


def _as_sequence(value: Any, *, campo: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"«{campo}» debe ser una lista JSON")
    return list(value)


def _as_text(value: Any, *, campo: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"«{campo}» debe ser texto")
    return value


def _as_optional_text(value: Any, *, campo: str) -> str | None:
    return None if value is None else _as_text(value, campo=campo)


def _as_int(value: Any, *, campo: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"«{campo}» debe ser un entero")
    return value


def _origin_type(value: Any, *, campo: str) -> str | None:
    texto = _as_optional_text(value, campo=campo)
    if texto is None:
        return None
    try:
        origen = OriginType(texto)
    except ValueError as error:
        raise ValueError(f"«{texto}» no es un tipo de origen válido en «{campo}»") from error
    return origen.value


def _subject_type(value: Any, *, campo: str) -> SubjectType:
    texto = _as_text(value, campo=campo)
    try:
        return SubjectType(texto)
    except ValueError as error:
        raise ValueError(f"«{texto}» no es un tipo de sujeto válido en «{campo}»") from error


def _profile(raw: Any, *, index: int) -> ProfileCandidate:
    campo = f"profiles[{index}]"
    datos = _as_mapping(raw, campo=campo)
    _reject_unknown(datos, _PROFILE_KEYS, campo=campo)
    nodos = _as_sequence(_field(datos, "topics"), campo=f"{campo}.topics")
    return ProfileCandidate(
        opposition_code=_as_text(
            _field(datos, "opposition_code"), campo=f"{campo}.opposition_code"
        ),
        opposition_name=_as_text(
            _field(datos, "opposition_name"), campo=f"{campo}.opposition_name"
        ),
        convocation_code=_as_text(
            _field(datos, "convocation_code"), campo=f"{campo}.convocation_code"
        ),
        topics=tuple(
            _topic(nodo, campo=f"{campo}.topics[{orden}]") for orden, nodo in enumerate(nodos)
        ),
    )


def _topic(raw: Any, *, campo: str) -> TopicCandidate:
    datos = _as_mapping(raw, campo=campo)
    _reject_unknown(datos, _TOPIC_KEYS, campo=campo)
    return TopicCandidate(
        node_id=_as_text(_field(datos, "node_id"), campo=f"{campo}.node_id"),
        path=_as_text(_field(datos, "path"), campo=f"{campo}.path"),
        title=_as_text(_field(datos, "title"), campo=f"{campo}.title"),
        depth=_as_int(_field(datos, "depth"), campo=f"{campo}.depth"),
    )


def _case(raw: Any, *, index: int, profiles: tuple[ProfileCandidate, ...]) -> DatasetCase:
    campo = f"cases[{index}]"
    datos = _as_mapping(raw, campo=campo)
    _reject_unknown(datos, _CASE_KEYS, campo=campo)
    intencion = _as_text(_field(datos, "intent"), campo=f"{campo}.intent")
    if intencion not in INTENTS:
        raise ValueError(f"Intención no reconocida en «{campo}»: «{intencion}»")
    return DatasetCase(
        case_id=_as_text(_field(datos, "id"), campo=f"{campo}.id"),
        intent=intencion,
        note=_as_text(_field(datos, "note"), campo=f"{campo}.note"),
        subject=_subject(_field(datos, "subject"), campo=f"{campo}.subject", profiles=profiles),
        expected=_expected(_field(datos, "expected"), campo=f"{campo}.expected"),
    )


def _subject(
    raw: Any,
    *,
    campo: str,
    profiles: tuple[ProfileCandidate, ...],
) -> ClassificationSubject:
    datos = _as_mapping(raw, campo=campo)
    _reject_unknown(datos, _SUBJECT_KEYS, campo=campo)
    texto = _as_optional_text(datos.get("text"), campo=f"{campo}.text")
    return ClassificationSubject(
        subject_type=_subject_type(_field(datos, "subject_type"), campo=f"{campo}.subject_type"),
        subject_id=_as_text(_field(datos, "subject_id"), campo=f"{campo}.subject_id"),
        text="" if texto is None else texto,
        original_name=_as_optional_text(datos.get("original_name"), campo=f"{campo}.original_name"),
        media_type=_as_optional_text(datos.get("media_type"), campo=f"{campo}.media_type"),
        origin_type=_origin_type(datos.get("origin_type"), campo=f"{campo}.origin_type"),
        origin_display=_as_optional_text(
            datos.get("origin_display"), campo=f"{campo}.origin_display"
        ),
        profiles=profiles,
    )


def _expected(raw: Any, *, campo: str) -> dict[Axis, str | None]:
    datos = _as_mapping(raw, campo=campo)
    _reject_unknown(datos, frozenset(eje.value for eje in Axis), campo=campo)
    etiquetas: dict[Axis, str | None] = {}
    for eje in Axis:
        if eje.value not in datos:
            raise ValueError(f"Falta la etiqueta del eje «{eje.value}» en «{campo}»")
        valor = datos[eje.value]
        if valor is None:
            etiquetas[eje] = None
            continue
        texto = _as_text(valor, campo=f"{campo}.{eje.value}")
        if not value_matches_axis(eje, texto):
            raise ValueError(f"«{texto}» no es un valor válido del eje «{eje.value}» en «{campo}»")
        etiquetas[eje] = texto
    return etiquetas


if __name__ == "__main__":
    raise SystemExit(main())
