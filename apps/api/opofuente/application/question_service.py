"""Servicio del banco de preguntas (S06): importar, leer y decidir sobre las claves.

Lo que vive aquí y no en el repositorio:

1. **El asistente de importación** (texto y CSV): leer con un mapeo de columnas, decir qué fila no
   pudo entrar y por qué, y no abortar el lote por una fila mala (criterio de aceptación del slice).
2. **La alineación de la plantilla**: una plantilla suelta se lee aparte y se empareja con las
   preguntas **por número** (04_INGESTION §10, paso 7). Lo que no empareja se informa: no se
   inventa a qué pregunta corresponde.
3. **Activar una plantilla es aprobarla**: la invariante exige aprobación antes de activar, y quien
   activa desde la interfaz está decidiendo exactamente eso. Queda auditado con quién y cuándo.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from datetime import date
from typing import Any

from opofuente.application.ports import Clock
from opofuente.application.question_models import (
    AnswerKeyView,
    CsvColumnMapping,
    KeyImportReport,
    QuestionImportReport,
    QuestionPage,
    QuestionSetPage,
    QuestionSetView,
    QuestionView,
    RejectedRow,
)
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.questions import (
    AnswerKeyEntry,
    KeyOutcome,
    Origin,
    ParsedOption,
    ParsedQuestion,
    QuestionDuplicateGroup,
    QuestionStatus,
    QuestionType,
    QuestionVersion,
    SetType,
    find_question_duplicates,
    parse_answer_key,
    parse_questions,
)
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository

#: Columnas que el CSV puede traer y que **todavía no se guardan**: se leen y se declaran, en
#: lugar de fingir que se han importado.
UNSTORED_COLUMNS = ("tags", "source")

#: Valores que cuentan como «sí» en una columna de reserva.
_TRUE_VALUES = {"1", "s", "si", "sí", "r", "reserva", "true", "x", "yes"}


def _delimiter(text: str) -> str:
    """Separador del CSV: el que más aparece en la primera línea con contenido."""
    for linea in text.splitlines():
        if linea.strip():
            candidatos = {";": linea.count(";"), ",": linea.count(","), "\t": linea.count("\t")}
            mejor = max(candidatos, key=lambda clave: candidatos[clave])
            return mejor if candidatos[mejor] > 0 else ","
    return ","


def _letters(value: str, *, option_count: int) -> tuple[str, ...] | None:
    """Opciones correctas de una celda: `b`, `B`, `2` o `b, c`. `None` si no se entiende."""
    limpio = value.strip().lower().replace(",", " ")
    if not limpio:
        return ()
    claves: list[str] = []
    for trozo in limpio.split():
        if trozo.isdigit():
            indice = int(trozo) - 1
            if indice < 0 or indice >= option_count:
                return None
            claves.append(chr(ord("a") + indice))
        elif len(trozo) == 1 and "a" <= trozo <= "h":
            if ord(trozo) - ord("a") >= option_count:
                return None
            claves.append(trozo)
        else:
            return None
    return tuple(dict.fromkeys(claves))


def _is_true(value: str) -> bool:
    return value.strip().lower() in _TRUE_VALUES


class QuestionService:
    """Cara del banco de preguntas para la API: nada de reglas nuevas, sí de comprobaciones."""

    def __init__(self, questions: SqlAlchemyQuestionRepository, clock: Clock) -> None:
        self._questions = questions
        self._clock = clock

    # ------------------------------------------------------------------ conjuntos

    def create_set(
        self,
        title: str,
        *,
        opposition_id: str,
        set_type: str,
        convocation_version_id: str | None = None,
        model_code: str | None = None,
        held_at: date | None = None,
        source_document_version_id: str | None = None,
        actor: str = "local",
    ) -> QuestionSetView:
        try:
            tipo = SetType(set_type)
        except ValueError as error:
            raise InvariantViolationError(f"«{set_type}» no es un tipo de conjunto") from error
        return self._questions.create_set(
            title=title,
            opposition_id=opposition_id,
            set_type=tipo.value,
            now=self._clock.now(),
            convocation_version_id=convocation_version_id,
            model_code=model_code,
            held_at=held_at,
            source_document_version_id=source_document_version_id,
            actor=actor,
        )

    def sets(
        self,
        *,
        opposition_id: str | None = None,
        set_type: str | None = None,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> QuestionSetPage:
        return self._questions.list_sets(
            opposition_id=opposition_id,
            set_type=set_type,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )

    def set_detail(self, set_id: str) -> QuestionSetView | None:
        return self._questions.get_set(set_id)

    def questions(
        self,
        *,
        set_id: str | None = None,
        status: str | None = None,
        origin_type: str | None = None,
        only_reserves: bool = False,
        limit: int = 50,
        offset: int = 0,
        include_key: bool = True,
    ) -> QuestionPage:
        """Preguntas del banco. Aquí la clave **sí** se incluye: esto es el banco, no un examen."""
        return self._questions.list_questions(
            set_id=set_id,
            status=status,
            origin_type=origin_type,
            only_reserves=only_reserves,
            limit=limit,
            offset=offset,
            include_key=include_key,
        )

    def question(self, question_id: str, *, include_key: bool = True) -> QuestionView | None:
        return self._questions.get_question(question_id, include_key=include_key)

    def duplicates(self, set_id: str) -> tuple[QuestionDuplicateGroup, ...]:
        """Preguntas repetidas o con las opciones reordenadas, **sin fusionar nada**."""
        pagina = self._questions.list_questions(set_id=set_id, limit=200, include_key=True)
        dominio = tuple(self._domain(pregunta) for pregunta in pagina.questions)
        return find_question_duplicates(dominio, keys=self._questions.keys_of_set(set_id))

    # ------------------------------------------------------------------ importación

    def import_from_text(
        self,
        set_id: str,
        text: str,
        *,
        origin_type: Origin = Origin.PRIVATE,
        actor: str = "local",
    ) -> QuestionImportReport:
        """Importa preguntas de un texto pegado o de un documento ya extraído."""
        if self._questions.get_set(set_id) is None:
            return QuestionImportReport(set_id=set_id)
        parseado = parse_questions(text)
        return self._guardar(
            set_id,
            parseado.questions,
            extras=[(pregunta.correct_option_keys, None, None) for pregunta in parseado.questions],
            origin_type=origin_type,
            issues=parseado.issues,
            model_code=parseado.model_code,
            actor=actor,
        )

    def import_from_csv(
        self,
        set_id: str,
        text: str,
        *,
        mapping: CsvColumnMapping | None = None,
        origin_type: Origin = Origin.PRIVATE,
        actor: str = "local",
    ) -> QuestionImportReport:
        """Importa un CSV con el mapeo de columnas que elija quien lo sube.

        Una fila mala **no** aborta el lote: se rechaza y se informa con su causa, para poder
        arreglarla y volver a importar solo eso.

        El mapeo tiene dos columnas imprescindibles —el enunciado y al menos dos opciones—: si no
        están, no se puede importar nada y se dice antes de tocar la base. Las demás son
        **opcionales**: si el mapeo pide una que el fichero no trae, se informa en el resultado y la
        importación sigue, porque un CSV sin columna de explicación es un CSV perfectamente normal.
        """
        mapeo = mapping or CsvColumnMapping()
        if self._questions.get_set(set_id) is None:
            return QuestionImportReport(set_id=set_id)
        lector = csv.DictReader(io.StringIO(text), delimiter=_delimiter(text))
        cabecera = tuple((nombre or "").strip().lower() for nombre in (lector.fieldnames or ()))
        if mapeo.stem.strip().lower() not in cabecera:
            raise InvariantViolationError(
                f"el fichero no trae la columna del enunciado «{mapeo.stem}»"
            )
        columnas_opcion = tuple(
            columna for columna in mapeo.options if columna.strip().lower() in cabecera
        )
        if len(columnas_opcion) < 2:
            raise InvariantViolationError(
                "el fichero no trae al menos dos columnas de opciones del mapeo"
            )
        faltan = tuple(
            columna
            for columna in mapeo.columns
            if columna.strip().lower() not in cabecera
            and columna not in (mapeo.stem, *columnas_opcion)
        )

        preguntas: list[ParsedQuestion] = []
        extras: list[tuple[tuple[str, ...], str | None, str | None]] = []
        rechazadas: list[RejectedRow] = []
        for indice, fila in enumerate(lector, start=2):
            normalizada = {
                (clave or "").strip().lower(): (valor or "") for clave, valor in fila.items()
            }
            posicion = self._position(normalizada, mapeo, indice)
            stem = normalizada.get(mapeo.stem.strip().lower(), "").strip()
            if not stem:
                rechazadas.append(RejectedRow(indice, "no_stem", "la fila no trae enunciado"))
                continue
            opciones = tuple(
                texto.strip()
                for texto in (
                    normalizada.get(columna.strip().lower(), "") for columna in columnas_opcion
                )
                if texto.strip()
            )
            if len(opciones) < 2:
                rechazadas.append(
                    RejectedRow(indice, "few_options", f"solo trae {len(opciones)} opción(es)")
                )
                continue
            claves: tuple[str, ...] = ()
            if mapeo.correct is not None:
                bruto = normalizada.get(mapeo.correct.strip().lower(), "")
                leidas = _letters(bruto, option_count=len(opciones))
                if leidas is None:
                    rechazadas.append(
                        RejectedRow(
                            indice,
                            "key_without_option",
                            f"«{bruto.strip()}» no corresponde a ninguna opción",
                        )
                    )
                    continue
                claves = leidas
            explicacion = (
                normalizada.get(mapeo.explanation.strip().lower(), "").strip()
                if mapeo.explanation is not None
                else ""
            )
            tema = (
                normalizada.get(mapeo.topic.strip().lower(), "").strip()
                if mapeo.topic is not None
                else ""
            )
            reserva = (
                _is_true(normalizada.get(mapeo.reserve.strip().lower(), ""))
                if mapeo.reserve is not None
                else False
            )
            preguntas.append(
                ParsedQuestion(
                    number=posicion,
                    stem=stem,
                    options=tuple(
                        ParsedOption(
                            stable_key=chr(ord("a") + orden),
                            text=texto,
                            position=orden + 1,
                        )
                        for orden, texto in enumerate(opciones)
                    ),
                    question_type=QuestionType.SINGLE_CHOICE,
                    line=indice,
                    is_reserve=reserva,
                    reserve_order=None,
                    correct_option_keys=claves,
                )
            )
            extras.append((claves, explicacion or None, tema or None))

        return self._guardar(
            set_id,
            tuple(preguntas),
            extras=extras,
            origin_type=origin_type,
            issues=(),
            model_code=None,
            ignored=tuple(
                columna
                for columna in UNSTORED_COLUMNS
                if getattr(mapeo, columna, None) is not None
                and str(getattr(mapeo, columna)).strip().lower() in cabecera
            ),
            missing=faltan,
            rejected=tuple(rechazadas),
            actor=actor,
        )

    def import_key_from_text(
        self,
        set_id: str,
        text: str,
        *,
        source_document_version_id: str | None = None,
        actor: str = "local",
    ) -> KeyImportReport:
        """Alinea una plantilla suelta con las preguntas del conjunto **por número**."""
        conjunto = self._questions.get_set(set_id)
        if conjunto is None:
            return KeyImportReport(key_id=None, version_no=None)
        lineas, incidencias = parse_answer_key(text)
        por_posicion = self._questions.questions_by_position(set_id)
        entradas: list[AnswerKeyEntry] = []
        sin_pareja: list[int] = []
        for linea in lineas:
            pregunta_id = por_posicion.get(linea.position)
            if pregunta_id is None:
                sin_pareja.append(linea.position)
                continue
            entradas.append(
                AnswerKeyEntry(
                    question_version_id=pregunta_id,
                    outcome=linea.outcome,
                    correct_option_keys=linea.correct_option_keys,
                )
            )
        if not entradas:
            return KeyImportReport(
                key_id=None, version_no=None, unmatched=tuple(sin_pareja), issues=incidencias
            )
        clave = self._save_key_if_new(
            set_id,
            tuple(entradas),
            source_document_version_id=source_document_version_id,
            actor=actor,
        )
        if clave is None:
            return KeyImportReport(
                key_id=None, version_no=None, unmatched=tuple(sin_pareja), issues=incidencias
            )
        return KeyImportReport(
            key_id=clave.id,
            version_no=clave.version_no,
            entries=clave.entry_count,
            unmatched=tuple(sin_pareja),
            issues=incidencias,
        )

    # ------------------------------------------------------------------ claves

    def keys(self, set_id: str) -> tuple[AnswerKeyView, ...]:
        return self._questions.list_keys(set_id)

    def activate_key(self, key_id: str, *, actor: str = "local") -> tuple[bool, str | None]:
        """Activa una plantilla. **Activar es aprobar**: lo decide una persona y queda auditado.

        La invariante dice que una clave activa necesita aprobación; si nadie la había aprobado
        antes, esta acción la aprueba con la misma fecha y el mismo actor, y eso se puede leer en
        la auditoría. Si la clave es de un conjunto oficial y no tiene su plantilla enlazada, no se
        activa: eso no lo arregla una aprobación.
        """
        clave = self._questions.get_key(key_id)
        if clave is None:
            return False, "la plantilla no existe"
        if clave.approved_at is None:
            self._questions.approve_key(key_id, now=self._clock.now(), actor=actor)
        return self._questions.activate_key(key_id, now=self._clock.now(), actor=actor)

    def mark_key_supersedes(
        self, key_id: str, *, superseded_id: str, actor: str = "local"
    ) -> tuple[bool, str | None]:
        return self._questions.mark_key_supersedes(
            key_id, superseded_id=superseded_id, now=self._clock.now(), actor=actor
        )

    # ------------------------------------------------------------------ auxiliares

    @staticmethod
    def _firma(
        entradas: Sequence[AnswerKeyEntry] | Sequence[object],
    ) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
        firma = []
        for entrada in entradas:
            if isinstance(entrada, AnswerKeyEntry):
                firma.append(
                    (
                        entrada.question_version_id,
                        entrada.outcome.value,
                        tuple(entrada.correct_option_keys),
                    )
                )
            else:
                firma.append(
                    (
                        str(getattr(entrada, "question_version_id", "")),
                        str(getattr(entrada, "outcome", "")),
                        tuple(str(clave) for clave in getattr(entrada, "correct_option_keys", ())),
                    )
                )
        return tuple(sorted(firma))

    def _save_key_if_new(
        self,
        set_id: str,
        entradas: Sequence[AnswerKeyEntry],
        *,
        source_document_version_id: str | None = None,
        actor: str = "local",
    ) -> AnswerKeyView | None:
        """Guarda la plantilla solo si dice algo distinto de las que ya hay.

        Reimportar el mismo texto no puede llenar el conjunto de versiones idénticas: si los
        desenlaces son los mismos que los de una plantilla existente, se devuelve esa.
        """
        if not entradas:
            return None
        firma = self._firma(entradas)
        for clave in self._questions.list_keys(set_id):
            if self._firma(clave.entries) == firma:
                return clave
        return self._questions.save_key(
            set_id,
            entries=entradas,
            source_document_version_id=source_document_version_id,
            now=self._clock.now(),
            actor=actor,
        )

    def _guardar(
        self,
        set_id: str,
        preguntas: Sequence[ParsedQuestion],
        *,
        extras: Sequence[tuple[tuple[str, ...], str | None, str | None]],
        origin_type: Origin,
        issues: Sequence[object],
        model_code: str | None,
        actor: str,
        ignored: tuple[str, ...] = (),
        missing: tuple[str, ...] = (),
        rejected: tuple[RejectedRow, ...] = (),
    ) -> QuestionImportReport:
        ahora = self._clock.now()
        resultado = self._questions.save_questions(
            set_id, preguntas, origin_type=origin_type, now=ahora, actor=actor
        )
        entradas: list[AnswerKeyEntry] = []
        conflictos: list[str] = []
        ya_conocidas = self._questions.entry_map(set_id)
        guardadas = self._questions.get_set(set_id)
        convocatoria = guardadas.convocation_version_id if guardadas is not None else None
        for (claves, explicacion, tema), pregunta_id in zip(
            extras, resultado.question_ids, strict=False
        ):
            if claves:
                anterior = ya_conocidas.get(pregunta_id)
                # Dos claves distintas de la misma pregunta no se fusionan: se dicen y se marcan.
                if anterior is not None and set(anterior.correct_option_keys) != set(claves):
                    conflictos.append(pregunta_id)
                    self._questions.set_question_status(
                        pregunta_id, "conflicting", now=ahora, actor=actor
                    )
                    entradas.append(
                        AnswerKeyEntry(pregunta_id, KeyOutcome.CONFLICTING, tuple(claves))
                    )
                else:
                    entradas.append(AnswerKeyEntry(pregunta_id, KeyOutcome.KEYED, tuple(claves)))
            if explicacion:
                self._questions.add_explanation(
                    pregunta_id,
                    text=explicacion,
                    origin=origin_type,
                    now=ahora,
                    actor=actor,
                )
            if tema and convocatoria is not None:
                nodo = self._questions.node_by_reference(
                    convocation_version_id=convocatoria, reference=tema
                )
                if nodo is not None:
                    self._questions.map_question_to_node(
                        pregunta_id, node_id=nodo[0], now=ahora, actor=actor
                    )
        if entradas:
            self._save_key_if_new(set_id, tuple(entradas), actor=actor)
        return QuestionImportReport(
            set_id=set_id,
            created=resultado.created,
            existing=resultado.existing,
            incomplete=resultado.incomplete,
            with_key=len(entradas),
            key_entries=len(entradas),
            duplicates=self.duplicates(set_id),
            issues=tuple(issues),
            rejected=rejected,
            ignored_columns=ignored,
            missing_columns=missing,
            conflicts=tuple(conflictos),
            model_code_detected=model_code,
        )

    @staticmethod
    def _position(fila: dict[str, Any], mapeo: CsvColumnMapping, indice: int) -> int:
        if mapeo.position is None:
            return indice - 1
        bruto = fila.get(mapeo.position.strip().lower(), "").strip()
        return int(bruto) if bruto.isdigit() else indice - 1

    @staticmethod
    def _domain(pregunta: QuestionView) -> QuestionVersion:
        from opofuente.domain.questions import OptionVersion

        return QuestionVersion(
            id=pregunta.id,
            question_set_id=pregunta.question_set_id,
            stable_key=pregunta.stable_key,
            version_no=pregunta.version_no,
            stem=pregunta.stem,
            question_type=QuestionType(pregunta.question_type),
            position=pregunta.position,
            origin_type=Origin(pregunta.origin_type),
            status=QuestionStatus(pregunta.status),
            is_reserve=pregunta.is_reserve,
            reserve_order=pregunta.reserve_order,
            options=tuple(
                OptionVersion(
                    id=opcion.id,
                    question_version_id=pregunta.id,
                    stable_key=opcion.stable_key,
                    text=opcion.text,
                    position=opcion.position,
                    label=opcion.label,
                )
                for opcion in pregunta.options
            ),
        )


__all__ = ["UNSTORED_COLUMNS", "QuestionService"]
