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
import logging
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from typing import Any

from opofuente.application.ports import Clock
from opofuente.application.question_models import (
    AnswerKeyView,
    CsvColumnMapping,
    IssueReportView,
    KeyImportReport,
    QuestionEvidenceView,
    QuestionImportReport,
    QuestionPage,
    QuestionSetPage,
    QuestionSetView,
    QuestionView,
    RejectedRow,
)
from opofuente.domain.errors import InvariantViolationError, MappingMismatchError, NotFoundError
from opofuente.domain.questions import (
    AnswerKeyEntry,
    KeyOutcome,
    Origin,
    ParsedOption,
    ParsedQuestion,
    ParseIssue,
    QuestionDuplicateGroup,
    QuestionStatus,
    QuestionType,
    QuestionVersion,
    SetStatus,
    SetType,
    find_question_duplicates,
    parse_answer_key,
    parse_questions,
    parse_questions_json,
)
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository

logger = logging.getLogger("opofuente.application.question_service")

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

    def __init__(
        self,
        questions: SqlAlchemyQuestionRepository,
        clock: Clock,
        documents: SqlAlchemyDocumentRepository,
    ) -> None:
        self._questions = questions
        self._clock = clock
        # Se inyecta porque importar **desde un documento** (DEBT-010) necesita leer las secciones y
        # los fragmentos de una versión: la cita de una pregunta sale de ahí, no de un texto suelto.
        self._documents = documents

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

    def archive_set(self, set_id: str, *, reason: str, actor: str = "local") -> bool:
        """Archiva un conjunto. Se usa cuando algo lo creó y resultó no tener nada dentro.

        Un conjunto vacío no es un conjunto: es una fila que ensucia la lista del banco. Se archiva
        (no se borra: el producto no borra) y el motivo queda en el registro.
        """
        archivado = self._questions.set_status(
            set_id, SetStatus.ARCHIVED.value, now=self._clock.now(), actor=actor
        )
        if archivado:
            logger.info(
                "questions.set_archived",
                extra={"event": "set_archived", "path": set_id, "reason": reason},
            )
        return archivado

    def set_detail(self, set_id: str) -> QuestionSetView | None:
        return self._questions.get_set(set_id)

    def questions_without_topic(self, set_id: str, *, limit: int = 500) -> tuple[str, ...]:
        """Preguntas del conjunto sin tema asignado: las únicas que la catalogación puede tocar."""
        return self._questions.questions_without_topic(set_id, limit=limit)

    def map_question_to_node(
        self, question_id: str, *, node_id: str, actor: str = "auto"
    ) -> str | None:
        """Cataloga una pregunta en un nodo del programa. Idempotente por `(nodo, pregunta)`.

        `actor` vale `auto` cuando lo hace la aplicación sola (S12.6) y `local` cuando lo pide una
        persona: la auditoría tiene que poder distinguirlos.
        """
        return self._questions.map_question_to_node(
            question_id, node_id=node_id, now=self._clock.now(), actor=actor
        )

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
            parts=parseado.parts_detected,
            actor=actor,
        )

    def import_from_document(
        self,
        set_id: str,
        document_version_id: str,
        *,
        origin_type: Origin = Origin.PRIVATE,
        actor: str = "local",
    ) -> QuestionImportReport:
        """Importa las preguntas de una **versión de documento** y su cita (DEBT-010).

        Es la mitad que faltaba del importador: hasta ahora el camino era texto pegado, CSV y JSON,
        y una pregunta que salía de un documento de la biblioteca perdía de dónde salió — la ficha
        no podía abrir la cita que sostiene el enunciado porque no había cita.

        Cómo se enlaza, sin inventar nada: se lee la versión por sus **fragmentos** (en su orden),
        se reconstruye el texto con la misma estructura de líneas y se guarda, para cada línea, de
        qué fragmento venía. El parser devuelve, por pregunta, la línea donde empezó su enunciado,
        así que la cita es exactamente el fragmento del que se leyó. Y la **sección** de origen se
        guarda en `source_section_id`, que el modelo ya tenía y nadie rellenaba.

        Lo que **no** hace: resolver la parte del examen. El parser detecta los rótulos que trae el
        material («Parte 2», «Primera parte») y aquí se **declaran** en el informe, pero no se
        guardan por pregunta: el modelo no tiene dónde, y emparejar un rótulo suelto con los
        códigos de `exam_parts` de la convocatoria sería adivinar. Queda en el ADR-014.
        """
        if self._questions.get_set(set_id) is None:
            return QuestionImportReport(set_id=set_id)
        detalle = self._documents.version_detail(document_version_id)
        if detalle is None:
            raise NotFoundError("versión de documento", document_version_id)

        texto, mapa = self._texto_de_la_version(document_version_id)
        parseado = parse_questions(texto)
        fuentes = tuple(self._fuente_de(pregunta.line, mapa) for pregunta in parseado.questions)
        # La sección de origen viaja en la pregunta: el modelo tenía el campo y nadie lo rellenaba.
        preguntas = tuple(
            pregunta
            if fuente is None or fuente[1] is None
            else replace(pregunta, source_section_id=fuente[1])
            for pregunta, fuente in zip(parseado.questions, fuentes, strict=True)
        )
        return self._guardar(
            set_id,
            preguntas,
            extras=[(pregunta.correct_option_keys, None, None) for pregunta in preguntas],
            origin_type=origin_type,
            issues=parseado.issues,
            model_code=parseado.model_code,
            parts=parseado.parts_detected,
            evidence_spans=tuple(None if fuente is None else fuente[0] for fuente in fuentes),
            actor=actor,
        )

    def _texto_de_la_version(
        self, document_version_id: str
    ) -> tuple[str, tuple[tuple[str, str | None, str | None], ...]]:
        """El texto de la versión, línea a línea, con el fragmento y la sección de cada línea.

        El mapa es tan importante como el texto: sin él, una pregunta sabría de qué documento salió
        pero no de qué fragmento, y la cita sería una promesa sin dirección.
        """
        lineas: list[str] = []
        mapa: list[tuple[str, str | None, str | None]] = []
        for fragmento in self._documents.list_evidence(document_version_id):
            texto = str(fragmento.text or "").strip("\n")
            if texto.strip() == "":
                continue
            for linea in texto.splitlines():
                lineas.append(linea)
                mapa.append((fragmento.id, fragmento.section_id, fragmento.citation_label))
            # Un fragmento no se pega al siguiente: entre uno y otro va una línea en blanco, para
            # que dos párrafos no formen una sola frase a ojos del parser.
            lineas.append("")
            mapa.append((fragmento.id, fragmento.section_id, fragmento.citation_label))
        return "\n".join(lineas), tuple(mapa)

    @staticmethod
    def _fuente_de(
        line: int, mapa: tuple[tuple[str, str | None, str | None], ...]
    ) -> tuple[str, str | None, str | None] | None:
        """El fragmento del que salió el enunciado de una pregunta, por su número de línea."""
        if line < 1 or line > len(mapa):
            return None
        return mapa[line - 1]

    def import_from_json(
        self,
        set_id: str,
        text: str,
        *,
        origin_type: Origin = Origin.PRIVATE,
        actor: str = "local",
    ) -> QuestionImportReport:
        """Importa preguntas de un JSON, la otra mitad del asistente del slice S06.

        Vale lo mismo que para el CSV: una pregunta mala no aborta el lote, entra todo lo legible y
        lo rechazado se informa con su motivo. Lo que **no** se hace es suponer: una pregunta sin
        clave entra sin clave, y los campos que el asistente no guarda se declaran en
        `ignored_columns` en vez de desaparecer sin decirlo.
        """
        if self._questions.get_set(set_id) is None:
            return QuestionImportReport(set_id=set_id)
        parseado = parse_questions_json(text)
        return self._guardar(
            set_id,
            parseado.questions,
            extras=[(pregunta.correct_option_keys, None, None) for pregunta in parseado.questions],
            origin_type=origin_type,
            issues=parseado.issues,
            model_code=parseado.model_code,
            ignored=parseado.ignored_fields,
            parts=parseado.parts_detected,
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
            raise MappingMismatchError(
                f"el fichero no trae la columna del enunciado «{mapeo.stem}»",
                field="mapping.stem",
            )
        columnas_opcion = tuple(
            columna for columna in mapeo.options if columna.strip().lower() in cabecera
        )
        if len(columnas_opcion) < 2:
            raise MappingMismatchError(
                "el fichero no trae al menos dos columnas de opciones del mapeo",
                field="mapping.options",
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

    def key(self, key_id: str) -> AnswerKeyView | None:
        return self._questions.get_key(key_id)

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

    # ------------------------------------------------------------------ edición y correcciones

    def update_question(
        self,
        question_id: str,
        *,
        stem: str | None = None,
        question_type: str | None = None,
        position: int | None = None,
        is_reserve: bool | None = None,
        reserve_order: int | None = None,
        actor: str = "local",
    ) -> QuestionView | None:
        """Cambia la composición de una pregunta (tipo, posición, reserva) o su enunciado."""
        if question_type is not None:
            try:
                QuestionType(question_type)
            except ValueError as error:
                raise InvariantViolationError(
                    f"«{question_type}» no es un tipo de pregunta"
                ) from error
        return self._questions.update_question(
            question_id,
            stem=stem,
            question_type=question_type,
            position=position,
            is_reserve=is_reserve,
            reserve_order=reserve_order,
            now=self._clock.now(),
            actor=actor,
        )

    def correct_question(
        self,
        question_id: str,
        *,
        note: str,
        stem: str | None = None,
        options: Sequence[str] | None = None,
        actor: str = "local",
    ) -> tuple[QuestionView | None, str | None]:
        """Corrige una transcripción **sin tocar el original**: crea versión nueva con su motivo.

        Si la pregunta tenía clave, la corrección **no la pierde**: se crea una plantilla nueva (en
        borrador) igual que la anterior pero apuntando a la versión corregida. La plantilla de
        antes no se toca, porque corregir una clave no reescribe lo que ya se corrigió con ella.
        """
        if not note.strip():
            raise InvariantViolationError("una corrección local necesita motivo")
        anterior = self._questions.get_question(question_id, include_key=True)
        if anterior is None:
            return None, None
        nueva_id = self._questions.create_corrected_version(
            question_id,
            stem=stem,
            options=options,
            note=note,
            now=self._clock.now(),
            actor=actor,
        )
        if nueva_id is None:
            return None, None
        clave_nueva: str | None = None
        claves = self._questions.list_keys(anterior.question_set_id)
        if claves:
            ultima = claves[-1]
            entradas = []
            for entrada in ultima.entries:
                if entrada.question_version_id == question_id:
                    entradas.append(
                        AnswerKeyEntry(
                            question_version_id=nueva_id,
                            outcome=KeyOutcome(entrada.outcome),
                            correct_option_keys=tuple(entrada.correct_option_keys),
                            notes=entrada.notes,
                        )
                    )
                else:
                    entradas.append(
                        AnswerKeyEntry(
                            question_version_id=entrada.question_version_id,
                            outcome=KeyOutcome(entrada.outcome),
                            correct_option_keys=tuple(entrada.correct_option_keys),
                            notes=entrada.notes,
                        )
                    )
            if any(entrada.question_version_id == nueva_id for entrada in entradas):
                guardada = self._questions.save_key(
                    anterior.question_set_id,
                    entries=tuple(entradas),
                    source_document_version_id=ultima.source_document_version_id,
                    now=self._clock.now(),
                    actor=actor,
                )
                clave_nueva = guardada.id if guardada is not None else None
        return self._questions.get_question(nueva_id, include_key=True), clave_nueva

    def report_issue(
        self, question_id: str, *, kind: str, detail: str, actor: str = "local"
    ) -> IssueReportView | None:
        """Guarda lo que reporta quien estudia sobre una pregunta."""
        identificador = self._questions.add_issue_report(
            question_id, kind=kind, detail=detail, now=self._clock.now(), actor=actor
        )
        if identificador is None:
            return None
        return next(
            (
                informe
                for informe in self._questions.issue_reports(question_id)
                if informe.id == identificador
            ),
            None,
        )

    def issues(self, question_id: str) -> tuple[IssueReportView, ...]:
        return self._questions.issue_reports(question_id)

    def evidence(self, question_id: str) -> tuple[QuestionEvidenceView, ...]:
        """Lo que sostiene la pregunta, con su cita: es lo que hace abrible una explicación."""
        return self._questions.question_evidence(question_id)

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
        issues: Sequence[ParseIssue],
        model_code: str | None,
        actor: str,
        ignored: tuple[str, ...] = (),
        missing: tuple[str, ...] = (),
        rejected: tuple[RejectedRow, ...] = (),
        parts: tuple[str, ...] = (),
        evidence_spans: Sequence[str | None] | None = None,
    ) -> QuestionImportReport:
        ahora = self._clock.now()
        resultado = self._questions.save_questions(
            set_id, preguntas, origin_type=origin_type, now=ahora, actor=actor
        )
        entradas: list[AnswerKeyEntry] = []
        conflictos: list[str] = []
        temas_sin_convocatoria: list[str] = []
        temas_sin_nodo: list[str] = []
        ya_conocidas = self._questions.entry_map(set_id)
        guardadas = self._questions.get_set(set_id)
        convocatoria = guardadas.convocation_version_id if guardadas is not None else None
        # Las entradas de la clave se agrupan por pregunta: un cuestionario que repite una pregunta
        # (una fila duplicada, por ejemplo) devuelve dos veces el mismo identificador, y una clave
        # no puede tener dos entradas para la misma pregunta. Con la misma respuesta se queda una;
        # con otra distinta, el conflicto se marca como siempre.
        por_pregunta: dict[str, AnswerKeyEntry] = {}
        for (claves, explicacion, tema), pregunta_id in zip(
            extras, resultado.question_ids, strict=False
        ):
            if claves:
                anterior = ya_conocidas.get(pregunta_id)
                # Dos claves distintas de la misma pregunta no se fusionan: se dicen y se marcan.
                if anterior is not None and set(anterior.correct_option_keys) != set(claves):
                    if pregunta_id not in conflictos:
                        conflictos.append(pregunta_id)
                    self._questions.set_question_status(
                        pregunta_id, "conflicting", now=ahora, actor=actor
                    )
                    por_pregunta[pregunta_id] = AnswerKeyEntry(
                        pregunta_id, KeyOutcome.CONFLICTING, tuple(claves)
                    )
                else:
                    previa = por_pregunta.get(pregunta_id)
                    if previa is None:
                        por_pregunta[pregunta_id] = AnswerKeyEntry(
                            pregunta_id, KeyOutcome.KEYED, tuple(claves)
                        )
                    elif set(previa.correct_option_keys) != set(claves):
                        # La misma pregunta, dos respuestas distintas en el mismo lote: es el mismo
                        # conflicto y se dice, en lugar de romper la clave.
                        if pregunta_id not in conflictos:
                            conflictos.append(pregunta_id)
                        self._questions.set_question_status(
                            pregunta_id, "conflicting", now=ahora, actor=actor
                        )
                        por_pregunta[pregunta_id] = AnswerKeyEntry(
                            pregunta_id, KeyOutcome.CONFLICTING, tuple(claves)
                        )
            if explicacion:
                self._questions.add_explanation(
                    pregunta_id,
                    text=explicacion,
                    origin=origin_type,
                    now=ahora,
                    actor=actor,
                )
            if tema:
                # Un tema sin convocatoria no se puede resolver a un nodo del programa, y decir que
                # no
                # se ha asignado es la diferencia entre perderlo en silencio y explicarlo: el
                # conjunto
                # no cuelga de ningún programa, así que no hay contra qué emparejar «I.1».
                if convocatoria is None:
                    temas_sin_convocatoria.append(tema)
                else:
                    nodo = self._questions.node_by_reference(
                        convocation_version_id=convocatoria, reference=tema
                    )
                    if nodo is not None:
                        self._questions.map_question_to_node(
                            pregunta_id, node_id=nodo[0], now=ahora, actor=actor
                        )
                    else:
                        temas_sin_nodo.append(tema)
        entradas = list(por_pregunta.values())
        if entradas:
            self._save_key_if_new(set_id, tuple(entradas), actor=actor)
        # Los temas que no se pudieron emparejar se declaran: un tema perdido en silencio deja al
        # banco
        # sin cobertura de programa y al diagnóstico sin temas, y nadie se entera hasta que falla.
        incidencias = list(issues)
        if temas_sin_convocatoria:
            incidencias.append(
                ParseIssue(
                    line=0,
                    code="topic_without_convocation",
                    detail=(
                        "el conjunto no cuelga de ninguna convocatoria, así que sus temas "
                        f"({', '.join(dict.fromkeys(temas_sin_convocatoria))}) no se han podido "
                        "asignar a un nodo del programa"
                    ),
                )
            )
        if temas_sin_nodo:
            incidencias.append(
                ParseIssue(
                    line=0,
                    code="topic_not_found",
                    detail=(
                        "estos temas no son ninguna ruta ni código del programa de la "
                        f"convocatoria: {', '.join(dict.fromkeys(temas_sin_nodo))}"
                    ),
                )
            )
        # La cita se crea **después** de guardar: hace falta el identificador de cada pregunta, y el
        # de una que ya estaba también vale — volver a importar el mismo documento repara sus citas.
        enlazadas = 0
        if evidence_spans is not None:
            for question_id, span_id in zip(resultado.question_ids, evidence_spans, strict=False):
                if span_id is None:
                    continue
                if self._questions.link_evidence(
                    question_id,
                    evidence_span_id=span_id,
                    role="stem",
                    status="accepted",
                    now=ahora,
                    actor=actor,
                ):
                    enlazadas += 1
        return QuestionImportReport(
            set_id=set_id,
            created=resultado.created,
            existing=resultado.existing,
            incomplete=resultado.incomplete,
            with_key=len(entradas),
            key_entries=len(entradas),
            duplicates=self.duplicates(set_id),
            issues=tuple(incidencias),
            rejected=rejected,
            ignored_columns=ignored,
            missing_columns=missing,
            conflicts=tuple(conflictos),
            model_code_detected=model_code,
            parts_detected=parts,
            evidence_links=enlazadas,
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
