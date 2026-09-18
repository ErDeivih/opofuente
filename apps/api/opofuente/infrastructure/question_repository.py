"""Repositorio del banco de preguntas (S06): conjuntos, preguntas, opciones y claves.

Tres reglas que se aplican aquí y no en el servicio:

1. **Guardar un lote es idempotente por contenido**: la identidad de una pregunta es su huella
   (enunciado normalizado + conjunto de opciones), así que volver a importar el mismo texto no
   duplica nada; se cuenta como «ya estaba» y se devuelve el identificador de la que ya había.
2. **La clave se guarda con su desenlace** y una clave activa necesita aprobación (lo impone la
   base); aquí se comprueba antes para poder decirlo con palabras.
3. **Los recuentos del conjunto se calculan**, no se guardan: un conjunto que dice tener 100
   preguntas cuando tiene 97 es peor que no decir nada.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.question_models import (
    AnswerKeyView,
    IssueReportView,
    KeyEntryView,
    OptionView,
    QuestionEvidenceView,
    QuestionPage,
    QuestionSetPage,
    QuestionSetView,
    QuestionView,
    SaveQuestionsOutcome,
)
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.questions import (
    AnswerKeyEntry,
    AnswerKeyVersion,
    KeyOutcome,
    Origin,
    ParsedQuestion,
    QuestionSet,
    SetType,
    can_activate,
    question_fingerprint,
)
from opofuente.infrastructure.db_models import (
    AnswerKeyEntryRecord,
    AnswerKeyVersionRecord,
    AuditEventRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    EvidenceSpanRecord,
    OppositionRecord,
    OptionVersionRecord,
    QuestionEvidenceRecord,
    QuestionExplanationRecord,
    QuestionIssueReportRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
)


def _new_id() -> str:
    return str(uuid4())


def _nuevo_stable_key(numero: int | None, identidad: str, usadas: set[str]) -> str:
    """Clave estable de una pregunta: su número si consta, o su huella. Nunca se repite.

    Si el número ya está cogido —una hoja con dos preguntas «7»— se añade un sufijo en lugar de
    fallar: la pregunta entra y la clave dice que es la segunda del mismo número.
    """
    base = f"q{numero:03d}" if numero is not None else f"q{identidad[:10]}"
    candidata = base
    sufijo = 1
    while candidata in usadas:
        sufijo += 1
        candidata = f"{base}-{sufijo}"
    usadas.add(candidata)
    return candidata


def _identidad(stem: str, option_texts: Sequence[str]) -> str:
    huella = question_fingerprint(stem, option_texts)
    return hashlib.sha256(huella.identity.encode("utf-8")).hexdigest()


class SqlAlchemyQuestionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ conjuntos

    def create_set(
        self,
        *,
        title: str,
        opposition_id: str,
        set_type: str,
        now: datetime,
        convocation_version_id: str | None = None,
        model_code: str | None = None,
        held_at: date | None = None,
        source_document_version_id: str | None = None,
        actor: str = "local",
    ) -> QuestionSetView:
        """Crea un conjunto. El título vacío no entra: un conjunto sin nombre no se puede elegir."""
        if not title.strip():
            raise InvariantViolationError("Un conjunto de preguntas necesita título")
        with self._session_factory() as session:
            if session.get(OppositionRecord, opposition_id) is None:
                raise InvariantViolationError(f"la oposición «{opposition_id}» no existe")
            fila = QuestionSetRecord(
                id=_new_id(),
                title=title.strip(),
                opposition_id=opposition_id,
                convocation_version_id=convocation_version_id,
                set_type=set_type,
                model_code=model_code.upper() if model_code else None,
                held_at=held_at,
                source_document_version_id=source_document_version_id,
                status="draft",
                created_at=now,
                updated_at=now,
            )
            session.add(fila)
            self._audit(
                session,
                actor=actor,
                action="question_set.created",
                object_type="question_set",
                object_id=fila.id,
                before={},
                after={"title": fila.title, "set_type": set_type, "model_code": fila.model_code},
                now=now,
            )
            session.commit()
            return self._set_view(session, fila)

    def list_sets(
        self,
        *,
        opposition_id: str | None = None,
        set_type: str | None = None,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> QuestionSetPage:
        filtros = []
        if opposition_id is not None:
            filtros.append(QuestionSetRecord.opposition_id == opposition_id)
        if set_type is not None:
            filtros.append(QuestionSetRecord.set_type == set_type)
        if not include_archived:
            filtros.append(QuestionSetRecord.status != "archived")
        with self._session_factory() as session:
            total = int(
                session.execute(
                    select(func.count()).select_from(QuestionSetRecord).where(*filtros)
                ).scalar_one()
            )
            filas = (
                session.execute(
                    select(QuestionSetRecord)
                    .where(*filtros)
                    .order_by(QuestionSetRecord.created_at.desc(), QuestionSetRecord.id)
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            vistas = tuple(self._set_view(session, fila) for fila in filas)
        return QuestionSetPage(sets=vistas, total=total, limit=limit, offset=offset)

    def get_set(self, set_id: str) -> QuestionSetView | None:
        with self._session_factory() as session:
            fila = session.get(QuestionSetRecord, set_id)
            if fila is None:
                return None
            return self._set_view(session, fila)

    def set_status(self, set_id: str, status: str, *, now: datetime, actor: str = "local") -> bool:
        with self._session_factory() as session:
            fila = session.get(QuestionSetRecord, set_id)
            if fila is None:
                return False
            antes = fila.status
            fila.status = status
            fila.updated_at = now
            self._audit(
                session,
                actor=actor,
                action="question_set.status_changed",
                object_type="question_set",
                object_id=set_id,
                before={"status": antes},
                after={"status": status},
                now=now,
            )
            session.commit()
            return True

    # ------------------------------------------------------------------ preguntas

    def save_questions(
        self,
        set_id: str,
        questions: Sequence[ParsedQuestion],
        *,
        origin_type: Origin,
        now: datetime,
        actor: str = "local",
    ) -> SaveQuestionsOutcome:
        """Guarda preguntas parseadas, sin duplicar las que ya están (misma huella)."""
        creadas = 0
        existentes = 0
        incompletas = 0
        ids: list[str] = []
        with self._session_factory() as session:
            conjunto = session.get(QuestionSetRecord, set_id)
            if conjunto is None:
                return SaveQuestionsOutcome()
            previas = self._identidades(session, set_id)
            usadas = set(self._stable_keys(session, set_id))
            for parseada in questions:
                textos = [opcion.text for opcion in parseada.options]
                identidad = _identidad(parseada.stem, textos)
                ya = previas.get(identidad)
                if ya is not None:
                    existentes += 1
                    ids.append(ya)
                    continue
                pregunta_id = _new_id()
                session.add(
                    QuestionVersionRecord(
                        id=pregunta_id,
                        question_set_id=set_id,
                        stable_key=_nuevo_stable_key(parseada.number, identidad, usadas),
                        version_no=1,
                        stem=parseada.stem,
                        question_type=parseada.question_type.value,
                        position=parseada.number or (len(usadas) + 1),
                        is_reserve=parseada.is_reserve,
                        reserve_order=parseada.reserve_order,
                        status="complete" if parseada.is_complete else "incomplete",
                        origin_type=origin_type.value,
                        source_section_id=None,
                        supersedes_id=None,
                        created_at=now,
                    )
                )
                # Se confirma la fila de la pregunta **antes** de sus opciones: sin relaciones
                # declaradas entre los modelos, SQLAlchemy no sabe que la opción depende de la
                # pregunta y podría intentar el `INSERT` al revés (lo cazó la clave foránea).
                session.flush()
                for opcion in parseada.options:
                    session.add(
                        OptionVersionRecord(
                            id=_new_id(),
                            question_version_id=pregunta_id,
                            stable_key=opcion.stable_key,
                            label=opcion.stable_key.upper(),
                            text=opcion.text,
                            position=opcion.position,
                        )
                    )
                creadas += 1
                previas[identidad] = pregunta_id
                ids.append(pregunta_id)
                if not parseada.is_complete:
                    incompletas += 1
            self._audit(
                session,
                actor=actor,
                action="questions.saved",
                object_type="question_set",
                object_id=set_id,
                before={},
                after={
                    "created": creadas,
                    "existing": existentes,
                    "incomplete": incompletas,
                    "origin_type": origin_type.value,
                },
                now=now,
            )
            session.commit()
        return SaveQuestionsOutcome(
            created=creadas,
            existing=existentes,
            incomplete=incompletas,
            question_ids=tuple(ids),
        )

    def list_questions(
        self,
        *,
        set_id: str | None = None,
        status: str | None = None,
        origin_type: str | None = None,
        only_reserves: bool = False,
        limit: int = 50,
        offset: int = 0,
        include_key: bool = False,
    ) -> QuestionPage:
        filtros = []
        if set_id is not None:
            filtros.append(QuestionVersionRecord.question_set_id == set_id)
        if status is not None:
            filtros.append(QuestionVersionRecord.status == status)
        if origin_type is not None:
            filtros.append(QuestionVersionRecord.origin_type == origin_type)
        if only_reserves:
            filtros.append(QuestionVersionRecord.is_reserve.is_(True))
        with self._session_factory() as session:
            total = int(
                session.execute(
                    select(func.count()).select_from(QuestionVersionRecord).where(*filtros)
                ).scalar_one()
            )
            filas = (
                session.execute(
                    select(QuestionVersionRecord)
                    .where(*filtros)
                    .order_by(
                        QuestionVersionRecord.question_set_id,
                        QuestionVersionRecord.position,
                        # La clave estable desempata: el orden no puede depender del identificador,
                        # que es un UUID y cambia en cada importación.
                        QuestionVersionRecord.stable_key,
                        QuestionVersionRecord.id,
                    )
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            claves = self._active_entries(session, [fila.question_set_id for fila in filas])
            return QuestionPage(
                questions=tuple(
                    self._question_view(session, fila, claves, include_key=include_key)
                    for fila in filas
                ),
                total=total,
                limit=limit,
                offset=offset,
            )

    def get_question(self, question_id: str, *, include_key: bool = False) -> QuestionView | None:
        with self._session_factory() as session:
            fila = session.get(QuestionVersionRecord, question_id)
            if fila is None:
                return None
            claves = self._active_entries(session, [fila.question_set_id])
            return self._question_view(session, fila, claves, include_key=include_key)

    def keys_of_set(self, set_id: str) -> dict[str, AnswerKeyEntry]:
        """Desenlaces de la clave **activa** del conjunto, por pregunta.

        Es lo que necesita la comparación de duplicados: dos preguntas iguales con claves distintas
        no se pueden fusionar, y eso solo se puede saber mirando las claves.
        """
        with self._session_factory() as session:
            return self._active_entries(session, [set_id]).get(set_id, {})

    def update_question(
        self,
        question_id: str,
        *,
        stem: str | None,
        question_type: str | None,
        position: int | None,
        is_reserve: bool | None,
        reserve_order: int | None,
        now: datetime,
        actor: str = "local",
    ) -> QuestionView | None:
        """Cambia lo que se puede cambiar sin tocar el texto importado de otros.

        Una pregunta **oficial** no se reescribe aquí: eso son correcciones locales, que crean
        versión nueva (04_INGESTION §9 y 06 §4). Este método es para el banco privado y para
        arreglar datos de composición (posición, reserva, tipo).
        """
        with self._session_factory() as session:
            fila = session.get(QuestionVersionRecord, question_id)
            if fila is None:
                return None
            antes: dict[str, object] = {
                "stem": fila.stem,
                "question_type": fila.question_type,
                "position": fila.position,
                "is_reserve": fila.is_reserve,
                "reserve_order": fila.reserve_order,
            }
            if stem is not None:
                fila.stem = stem.strip()
            if question_type is not None:
                fila.question_type = question_type
            if position is not None:
                fila.position = position
            if is_reserve is not None:
                fila.is_reserve = is_reserve
            if reserve_order is not None:
                fila.reserve_order = reserve_order
            if not fila.is_reserve:
                fila.reserve_order = None
            despues: dict[str, object] = {
                "stem": fila.stem,
                "question_type": fila.question_type,
                "position": fila.position,
                "is_reserve": fila.is_reserve,
                "reserve_order": fila.reserve_order,
            }
            self._audit(
                session,
                actor=actor,
                action="question.updated",
                object_type="question_version",
                object_id=question_id,
                before=antes,
                after=despues,
                now=now,
            )
            session.commit()
            claves = self._active_entries(session, [fila.question_set_id])
            return self._question_view(session, fila, claves, include_key=True)

    # ------------------------------------------------------------------ claves

    def save_key(
        self,
        set_id: str,
        *,
        entries: Sequence[AnswerKeyEntry],
        now: datetime,
        source_document_version_id: str | None = None,
        published_at: date | None = None,
        actor: str = "local",
    ) -> AnswerKeyView | None:
        """Guarda una plantilla nueva (versión siguiente), sin activarla todavía."""
        with self._session_factory() as session:
            conjunto = session.get(QuestionSetRecord, set_id)
            if conjunto is None:
                return None
            preguntas = set(self._question_ids(session, set_id))
            ajenas = [
                entrada.question_version_id
                for entrada in entries
                if entrada.question_version_id not in preguntas
            ]
            if ajenas:
                raise InvariantViolationError(
                    "La plantilla incluye preguntas que no son de este conjunto: "
                    + ", ".join(sorted(ajenas)[:5])
                )
            version = (
                int(
                    session.execute(
                        select(func.coalesce(func.max(AnswerKeyVersionRecord.version_no), 0)).where(
                            AnswerKeyVersionRecord.question_set_id == set_id
                        )
                    ).scalar_one()
                )
                + 1
            )
            fila = AnswerKeyVersionRecord(
                id=_new_id(),
                question_set_id=set_id,
                source_document_version_id=source_document_version_id,
                version_no=version,
                status="draft",
                supersedes_id=None,
                published_at=published_at,
                approved_at=None,
                created_at=now,
            )
            session.add(fila)
            session.flush()
            for entrada in entries:
                session.add(
                    AnswerKeyEntryRecord(
                        answer_key_version_id=fila.id,
                        question_version_id=entrada.question_version_id,
                        outcome=entrada.outcome.value,
                        correct_option_keys_json=json.dumps(
                            list(entrada.correct_option_keys), ensure_ascii=False
                        ),
                        notes=entrada.notes,
                    )
                )
            self._audit(
                session,
                actor=actor,
                action="answer_key.saved",
                object_type="answer_key_version",
                object_id=fila.id,
                before={},
                after={
                    "question_set_id": set_id,
                    "version_no": version,
                    "entries": len(entries),
                    "source_document_version_id": source_document_version_id,
                },
                now=now,
            )
            session.commit()
            return self._key_view(session, fila)

    def approve_key(self, key_id: str, *, now: datetime, actor: str = "local") -> bool:
        """Aprueba una plantilla. Sin aprobación no se puede activar (invariante 4 y la base)."""
        with self._session_factory() as session:
            fila = session.get(AnswerKeyVersionRecord, key_id)
            if fila is None:
                return False
            fila.approved_at = now
            self._audit(
                session,
                actor=actor,
                action="answer_key.approved",
                object_type="answer_key_version",
                object_id=key_id,
                before={"approved_at": None},
                after={"approved_at": now.isoformat()},
                now=now,
            )
            session.commit()
            return True

    def activate_key(
        self, key_id: str, *, now: datetime, actor: str = "local"
    ) -> tuple[bool, str | None]:
        """Activa una plantilla y retira la que estuviera activa. No se borra ninguna."""
        with self._session_factory() as session:
            fila = session.get(AnswerKeyVersionRecord, key_id)
            if fila is None:
                return False, "la plantilla no existe"
            conjunto = session.get(QuestionSetRecord, fila.question_set_id)
            if conjunto is None:
                return False, "el conjunto de la plantilla no existe"
            permitido, motivo = can_activate(self._set_domain(conjunto), self._key_domain(fila))
            if not permitido:
                return False, motivo
            anteriores = (
                session.execute(
                    select(AnswerKeyVersionRecord).where(
                        AnswerKeyVersionRecord.question_set_id == fila.question_set_id,
                        AnswerKeyVersionRecord.status == "active",
                        AnswerKeyVersionRecord.id != key_id,
                    )
                )
                .scalars()
                .all()
            )
            for anterior in anteriores:
                anterior.status = "superseded"
            # Primero se retira la que estaba activa y **después** se activa la nueva: el índice
            # único parcial solo admite una activa por conjunto, así que el orden importa.
            session.flush()
            fila.status = "active"
            self._audit(
                session,
                actor=actor,
                action="answer_key.activated",
                object_type="answer_key_version",
                object_id=key_id,
                before={"status": "draft", "superseded": [fila.id for fila in anteriores]},
                after={"status": "active"},
                now=now,
            )
            session.commit()
            return True, None

    def mark_key_supersedes(
        self, key_id: str, *, superseded_id: str, now: datetime, actor: str = "local"
    ) -> tuple[bool, str | None]:
        """Confirma que una plantilla sustituye a otra. La antigua se conserva."""
        with self._session_factory() as session:
            fila = session.get(AnswerKeyVersionRecord, key_id)
            anterior = session.get(AnswerKeyVersionRecord, superseded_id)
            if fila is None:
                return False, "la plantilla no existe"
            if anterior is None:
                return False, "la plantilla que se dice sustituida no existe"
            if anterior.question_set_id != fila.question_set_id:
                return False, "las dos plantillas tienen que ser del mismo conjunto"
            if anterior.id == fila.id:
                return False, "una plantilla no se sustituye a sí misma"
            fila.supersedes_id = anterior.id
            if anterior.status == "active":
                anterior.status = "superseded"
            self._audit(
                session,
                actor=actor,
                action="answer_key.supersedes",
                object_type="answer_key_version",
                object_id=key_id,
                before={"supersedes_id": None},
                after={"supersedes_id": anterior.id},
                now=now,
            )
            session.commit()
            return True, None

    def list_keys(self, set_id: str) -> tuple[AnswerKeyView, ...]:
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(AnswerKeyVersionRecord)
                    .where(AnswerKeyVersionRecord.question_set_id == set_id)
                    .order_by(AnswerKeyVersionRecord.version_no)
                )
                .scalars()
                .all()
            )
            return tuple(self._key_view(session, fila) for fila in filas)

    def get_key(self, key_id: str) -> AnswerKeyView | None:
        with self._session_factory() as session:
            fila = session.get(AnswerKeyVersionRecord, key_id)
            if fila is None:
                return None
            return self._key_view(session, fila)

    # ------------------------------------------------------------------ explicaciones y mapeos

    def add_explanation(
        self,
        question_version_id: str,
        *,
        text: str,
        origin: Origin,
        now: datetime,
        option_stable_key: str | None = None,
        model_name: str | None = None,
        prompt_template_version: str | None = None,
        actor: str = "local",
    ) -> str | None:
        """Guarda (o reemplaza) la explicación de la pregunta entera o de una opción.

        La identidad es `(pregunta, opción)`: la segunda explicación de la misma opción sustituye a
        la primera en lugar de acumularse, porque dos explicaciones distintas de lo mismo es una
        decisión editorial, no un dato más.
        """
        if not text.strip():
            return None
        with self._session_factory() as session:
            pregunta = session.get(QuestionVersionRecord, question_version_id)
            if pregunta is None:
                return None
            existente = session.execute(
                select(QuestionExplanationRecord).where(
                    QuestionExplanationRecord.question_version_id == question_version_id,
                    QuestionExplanationRecord.option_stable_key.is_(None)
                    if option_stable_key is None
                    else QuestionExplanationRecord.option_stable_key == option_stable_key,
                )
            ).scalar_one_or_none()
            if existente is not None:
                existente.text = text.strip()
                existente.origin = origin.value
                existente.model_name = model_name
                existente.prompt_template_version = prompt_template_version
                session.commit()
                return existente.id
            fila = QuestionExplanationRecord(
                id=_new_id(),
                question_version_id=question_version_id,
                option_stable_key=option_stable_key,
                origin=origin.value,
                status="draft",
                model_name=model_name,
                prompt_template_version=prompt_template_version,
                created_at=now,
                text=text.strip(),
            )
            session.add(fila)
            self._audit(
                session,
                actor=actor,
                action="question_explanation.saved",
                object_type="question_version",
                object_id=question_version_id,
                before={},
                after={"option_stable_key": option_stable_key, "origin": origin.value},
                now=now,
            )
            session.commit()
            return fila.id

    def questions_by_position(self, set_id: str) -> dict[int, str]:
        """Identificador de cada pregunta por su posición: es lo que alinea una plantilla suelta."""
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionVersionRecord.position, QuestionVersionRecord.id).where(
                    QuestionVersionRecord.question_set_id == set_id
                )
            ).all()
        return {int(posicion): str(pregunta_id) for posicion, pregunta_id in filas}

    def all_questions(self, set_id: str) -> tuple[QuestionView, ...]:
        """Todas las preguntas de un conjunto en su orden, sin clave.

        Es la lista de la que una sesión elige su composición: no lleva la solución porque una
        sesión se corrige con la clave **activa** congelada, no con lo que devuelva esta consulta.
        Sin tope de página a propósito: recortar aquí dejaría una sesión oficial sin las últimas
        preguntas.
        """
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(QuestionVersionRecord)
                    .where(QuestionVersionRecord.question_set_id == set_id)
                    .order_by(
                        QuestionVersionRecord.position,
                        QuestionVersionRecord.stable_key,
                        QuestionVersionRecord.id,
                    )
                )
                .scalars()
                .all()
            )
            return tuple(
                self._question_view(session, fila, {}, include_key=False) for fila in filas
            )

    def node_by_reference(
        self, *, convocation_version_id: str, reference: str
    ) -> tuple[str, int] | None:
        """Nodo del programa por su ruta o su código oficial: lo que trae una columna `topic`."""
        limpio = reference.strip()
        if not limpio:
            return None
        with self._session_factory() as session:
            fila = session.execute(
                select(CurriculumNodeRecord)
                .where(
                    CurriculumNodeRecord.convocation_version_id == convocation_version_id,
                    (CurriculumNodeRecord.path == limpio)
                    | (CurriculumNodeRecord.official_code == limpio),
                )
                .order_by(CurriculumNodeRecord.depth)
                .limit(1)
            ).scalar_one_or_none()
        if fila is None:
            return None
        return str(fila.id), int(fila.depth)

    def map_question_to_node(
        self,
        question_version_id: str,
        *,
        node_id: str,
        now: datetime,
        coverage_type: str = "partial",
        actor: str = "local",
    ) -> str | None:
        """Asigna una pregunta a un nodo del programa. Idempotente por `(nodo, pregunta)`."""
        with self._session_factory() as session:
            pregunta = session.get(QuestionVersionRecord, question_version_id)
            if pregunta is None:
                return None
            nodo = session.get(CurriculumNodeRecord, node_id)
            if nodo is None:
                return None
            existente = session.execute(
                select(CurriculumMappingRecord.id).where(
                    CurriculumMappingRecord.curriculum_node_id == node_id,
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.subject_id == question_version_id,
                )
            ).scalar_one_or_none()
            if existente is not None:
                return str(existente)
            mapeo = CurriculumMappingRecord(
                id=_new_id(),
                curriculum_node_id=node_id,
                subject_type="question_version",
                subject_id=question_version_id,
                coverage_type=coverage_type,
                depth=int(nodo.depth),
                confidence=1.0,
                status="accepted",
                source_proposal_id=None,
                created_at=now,
                approved_at=now,
            )
            session.add(mapeo)
            self._audit(
                session,
                actor=actor,
                action="question.mapped",
                object_type="curriculum_mapping",
                object_id=mapeo.id,
                before={},
                after={"node_id": node_id, "question_version_id": question_version_id},
                now=now,
            )
            session.commit()
            return mapeo.id

    def entry_map(self, set_id: str) -> dict[str, AnswerKeyEntry]:
        """Desenlaces conocidos de cada pregunta, de **todas** las plantillas del conjunto.

        Se miran todas y no solo la activa porque lo que se está comprobando es si una clave nueva
        **contradice** algo que ya se sabía, aunque la plantilla anterior esté en borrador. Manda
        la versión más alta.
        """
        resultado: dict[str, AnswerKeyEntry] = {}
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(AnswerKeyVersionRecord)
                    .where(AnswerKeyVersionRecord.question_set_id == set_id)
                    .order_by(AnswerKeyVersionRecord.version_no)
                )
                .scalars()
                .all()
            )
            for clave in filas:
                entradas = (
                    session.execute(
                        select(AnswerKeyEntryRecord).where(
                            AnswerKeyEntryRecord.answer_key_version_id == clave.id
                        )
                    )
                    .scalars()
                    .all()
                )
                for entrada in entradas:
                    resultado[entrada.question_version_id] = AnswerKeyEntry(
                        question_version_id=entrada.question_version_id,
                        outcome=KeyOutcome(entrada.outcome),
                        correct_option_keys=tuple(
                            str(clave_opcion)
                            for clave_opcion in json.loads(entrada.correct_option_keys_json or "[]")
                        ),
                        notes=entrada.notes,
                    )
        return resultado

    def set_question_status(
        self, question_id: str, status: str, *, now: datetime, actor: str = "local"
    ) -> bool:
        """Cambia el estado de una pregunta: `conflicting` cuando dos claves chocan, por ejemplo."""
        with self._session_factory() as session:
            fila = session.get(QuestionVersionRecord, question_id)
            if fila is None:
                return False
            antes = fila.status
            fila.status = status
            self._audit(
                session,
                actor=actor,
                action="question.status_changed",
                object_type="question_version",
                object_id=question_id,
                before={"status": antes},
                after={"status": status},
                now=now,
            )
            session.commit()
            return True

    # ------------------------------------------------------------------ correcciones e incidencias

    def create_corrected_version(
        self,
        question_id: str,
        *,
        stem: str | None,
        options: Sequence[str] | None,
        note: str,
        now: datetime,
        actor: str = "local",
    ) -> str | None:
        """Crea la versión corregida de una pregunta y deja la anterior como `superseded`.

        El texto importado no se toca: se añade una versión nueva que sustituye a la anterior, con
        el motivo en su `note`. Así se puede ver qué decía el original y por qué se cambió.
        """
        with self._session_factory() as session:
            anterior = session.get(QuestionVersionRecord, question_id)
            if anterior is None:
                return None
            version = (
                int(
                    session.execute(
                        select(func.coalesce(func.max(QuestionVersionRecord.version_no), 0)).where(
                            QuestionVersionRecord.question_set_id == anterior.question_set_id,
                            QuestionVersionRecord.stable_key == anterior.stable_key,
                        )
                    ).scalar_one()
                )
                + 1
            )
            nueva_id = _new_id()
            session.add(
                QuestionVersionRecord(
                    id=nueva_id,
                    question_set_id=anterior.question_set_id,
                    stable_key=anterior.stable_key,
                    version_no=version,
                    stem=(stem or anterior.stem).strip(),
                    question_type=anterior.question_type,
                    position=anterior.position,
                    is_reserve=anterior.is_reserve,
                    reserve_order=anterior.reserve_order,
                    status="complete" if (options or stem) else anterior.status,
                    origin_type=anterior.origin_type,
                    source_section_id=anterior.source_section_id,
                    supersedes_id=anterior.id,
                    created_at=now,
                    note=note.strip(),
                )
            )
            session.flush()
            textos = (
                list(options)
                if options is not None
                else [
                    str(opcion.text)
                    for opcion in self._options_by_question(session, [question_id]).get(
                        question_id, ()
                    )
                ]
            )
            for orden, texto in enumerate(textos, start=1):
                session.add(
                    OptionVersionRecord(
                        id=_new_id(),
                        question_version_id=nueva_id,
                        stable_key=chr(ord("a") + orden - 1),
                        label=chr(ord("A") + orden - 1),
                        text=texto.strip(),
                        position=orden,
                    )
                )
            antes = anterior.status
            anterior.status = "superseded"
            self._audit(
                session,
                actor=actor,
                action="question.corrected",
                object_type="question_version",
                object_id=nueva_id,
                before={"supersedes_id": question_id, "status": antes},
                after={"version_no": version, "note": note.strip()},
                now=now,
            )
            session.commit()
            return nueva_id

    def add_issue_report(
        self, question_id: str, *, kind: str, detail: str, now: datetime, actor: str = "local"
    ) -> str | None:
        """Guarda lo que reporta quien estudia: es información suya, no una clasificación."""
        with self._session_factory() as session:
            if session.get(QuestionVersionRecord, question_id) is None:
                return None
            fila = QuestionIssueReportRecord(
                id=_new_id(),
                question_version_id=question_id,
                kind=kind,
                detail=detail.strip(),
                status="open",
                created_at=now,
                reviewed_at=None,
            )
            session.add(fila)
            self._audit(
                session,
                actor=actor,
                action="question.issue_reported",
                object_type="question_version",
                object_id=question_id,
                before={},
                after={"kind": kind, "report_id": fila.id},
                now=now,
            )
            session.commit()
            return fila.id

    def issue_reports(self, question_id: str) -> tuple[IssueReportView, ...]:
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(QuestionIssueReportRecord)
                    .where(QuestionIssueReportRecord.question_version_id == question_id)
                    .order_by(QuestionIssueReportRecord.created_at)
                )
                .scalars()
                .all()
            )
            return tuple(
                IssueReportView(
                    id=fila.id,
                    question_version_id=fila.question_version_id,
                    kind=str(fila.kind),
                    detail=str(fila.detail),
                    status=str(fila.status),
                    created_at=fila.created_at,
                )
                for fila in filas
            )

    def node_ids_of_question(self, question_version_id: str) -> tuple[str, ...]:
        """Los nodos del programa a los que está asignada una pregunta.

        Se lee solo lo aceptado: una asignación propuesta y sin revisar no es un hecho, y usarla
        para filtrar una exportación sacaría preguntas de un tema en el que nadie las ha puesto.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(CurriculumMappingRecord.curriculum_node_id).where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.subject_id == question_version_id,
                    CurriculumMappingRecord.status == "accepted",
                )
            ).scalars()
            return tuple(str(node_id) for node_id in filas)

    def question_evidence(self, question_id: str) -> tuple[QuestionEvidenceView, ...]:
        """Evidencia que sostiene la pregunta, con el texto de la cita ya recortado."""
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionEvidenceRecord, EvidenceSpanRecord)
                .join(
                    EvidenceSpanRecord,
                    EvidenceSpanRecord.id == QuestionEvidenceRecord.evidence_span_id,
                )
                .where(QuestionEvidenceRecord.question_version_id == question_id)
                .order_by(QuestionEvidenceRecord.role, EvidenceSpanRecord.ordinal)
            ).all()
        return tuple(
            QuestionEvidenceView(
                span_id=span.id,
                role=str(enlace.role),
                status=str(enlace.status),
                claim=enlace.claim,
                text=str(span.text),
                page=span.page,
                citation_label=span.citation_label,
                document_version_id=span.document_version_id,
                section_id=span.section_id,
            )
            for enlace, span in filas
        )

    # ------------------------------------------------------------------ auxiliares

    @staticmethod
    def _identidades(session: Session, set_id: str) -> dict[str, str]:
        """Identidad (huella) de cada pregunta del conjunto, con su identificador."""
        filas = (
            session.execute(
                select(QuestionVersionRecord).where(QuestionVersionRecord.question_set_id == set_id)
            )
            .scalars()
            .all()
        )
        opciones = SqlAlchemyQuestionRepository._options_by_question(
            session, [fila.id for fila in filas]
        )
        return {
            _identidad(
                fila.stem,
                [opcion.text for opcion in opciones.get(fila.id, ())],
            ): fila.id
            for fila in filas
        }

    @staticmethod
    def _stable_keys(session: Session, set_id: str) -> list[str]:
        return [
            str(clave)
            for clave in session.execute(
                select(QuestionVersionRecord.stable_key).where(
                    QuestionVersionRecord.question_set_id == set_id
                )
            )
            .scalars()
            .all()
        ]

    @staticmethod
    def _question_ids(session: Session, set_id: str) -> list[str]:
        return [
            str(fila)
            for fila in session.execute(
                select(QuestionVersionRecord.id).where(
                    QuestionVersionRecord.question_set_id == set_id
                )
            )
            .scalars()
            .all()
        ]

    @staticmethod
    def _options_by_question(
        session: Session, question_ids: Sequence[str]
    ) -> dict[str, tuple[OptionVersionRecord, ...]]:
        if not question_ids:
            return {}
        filas = (
            session.execute(
                select(OptionVersionRecord)
                .where(OptionVersionRecord.question_version_id.in_(list(question_ids)))
                .order_by(OptionVersionRecord.position, OptionVersionRecord.stable_key)
            )
            .scalars()
            .all()
        )
        agrupadas: dict[str, list[OptionVersionRecord]] = {}
        for fila in filas:
            agrupadas.setdefault(fila.question_version_id, []).append(fila)
        return {clave: tuple(valor) for clave, valor in agrupadas.items()}

    @staticmethod
    def _active_entries(
        session: Session, set_ids: Sequence[str]
    ) -> dict[str, dict[str, AnswerKeyEntry]]:
        """Desenlaces que **mandan** en cada conjunto, por identificador de pregunta.

        Manda la clave activa y, si no hay ninguna activa todavía, la última plantilla que exista:
        en el banco de preguntas, una plantilla en borrador es justo lo que se está revisando, y
        esconder su clave dejaría la pantalla sin lo único que hay que mirar. Activar sigue siendo
        lo que decide qué clave corrige un examen (eso lo usa S07), no lo que decide qué se lee.
        """
        if not set_ids:
            return {}
        claves = (
            session.execute(
                select(AnswerKeyVersionRecord).where(
                    AnswerKeyVersionRecord.question_set_id.in_(list(set_ids))
                )
            )
            .scalars()
            .all()
        )
        elegidas: dict[str, AnswerKeyVersionRecord] = {}
        for clave in sorted(
            claves, key=lambda fila: (fila.status == "active", int(fila.version_no))
        ):
            elegidas[clave.question_set_id] = clave
        claves = list(elegidas.values())
        resultado: dict[str, dict[str, AnswerKeyEntry]] = {}
        for clave in claves:
            entradas = (
                session.execute(
                    select(AnswerKeyEntryRecord).where(
                        AnswerKeyEntryRecord.answer_key_version_id == clave.id
                    )
                )
                .scalars()
                .all()
            )
            resultado[clave.question_set_id] = {
                entrada.question_version_id: AnswerKeyEntry(
                    question_version_id=entrada.question_version_id,
                    outcome=KeyOutcome(entrada.outcome),
                    correct_option_keys=tuple(
                        str(clave_opcion)
                        for clave_opcion in json.loads(entrada.correct_option_keys_json or "[]")
                    ),
                    notes=entrada.notes,
                )
                for entrada in entradas
            }
        return resultado

    @staticmethod
    def _explanations_count(session: Session, question_ids: Sequence[str]) -> dict[str, int]:
        if not question_ids:
            return {}
        filas = session.execute(
            select(
                QuestionExplanationRecord.question_version_id,
                func.count(),
            )
            .where(QuestionExplanationRecord.question_version_id.in_(list(question_ids)))
            .group_by(QuestionExplanationRecord.question_version_id)
        ).all()
        return {str(pregunta_id): int(total) for pregunta_id, total in filas}

    def _set_view(self, session: Session, fila: QuestionSetRecord) -> QuestionSetView:
        preguntas = int(
            session.execute(
                select(func.count())
                .select_from(QuestionVersionRecord)
                .where(QuestionVersionRecord.question_set_id == fila.id)
            ).scalar_one()
        )
        reservas = int(
            session.execute(
                select(func.count())
                .select_from(QuestionVersionRecord)
                .where(
                    QuestionVersionRecord.question_set_id == fila.id,
                    QuestionVersionRecord.is_reserve.is_(True),
                )
            ).scalar_one()
        )
        incompletas = int(
            session.execute(
                select(func.count())
                .select_from(QuestionVersionRecord)
                .where(
                    QuestionVersionRecord.question_set_id == fila.id,
                    QuestionVersionRecord.status == "incomplete",
                )
            ).scalar_one()
        )
        claves = (
            session.execute(
                select(AnswerKeyVersionRecord).where(
                    AnswerKeyVersionRecord.question_set_id == fila.id
                )
            )
            .scalars()
            .all()
        )
        activa = next((clave.id for clave in claves if clave.status == "active"), None)
        return QuestionSetView(
            id=fila.id,
            title=str(fila.title),
            set_type=str(fila.set_type),
            status=str(fila.status),
            opposition_id=str(fila.opposition_id),
            convocation_version_id=fila.convocation_version_id,
            model_code=fila.model_code,
            held_at=fila.held_at,
            source_document_version_id=fila.source_document_version_id,
            created_at=fila.created_at,
            question_count=preguntas,
            reserve_count=reservas,
            incomplete_count=incompletas,
            key_count=len(claves),
            active_key_id=activa,
        )

    def _question_view(
        self,
        session: Session,
        fila: QuestionVersionRecord,
        claves: Mapping[str, Mapping[str, AnswerKeyEntry]],
        *,
        include_key: bool,
    ) -> QuestionView:
        opciones = self._options_by_question(session, [fila.id]).get(fila.id, ())
        entrada = claves.get(fila.question_set_id, {}).get(fila.id)
        explicaciones = self._explanations_count(session, [fila.id]).get(fila.id, 0)
        return QuestionView(
            id=fila.id,
            question_set_id=fila.question_set_id,
            stable_key=str(fila.stable_key),
            version_no=int(fila.version_no),
            stem=str(fila.stem),
            question_type=str(fila.question_type),
            position=int(fila.position),
            status=str(fila.status),
            origin_type=str(fila.origin_type),
            is_reserve=bool(fila.is_reserve),
            reserve_order=fila.reserve_order,
            source_section_id=fila.source_section_id,
            supersedes_id=fila.supersedes_id,
            created_at=fila.created_at,
            note=fila.note,
            options=tuple(
                OptionView(
                    id=opcion.id,
                    stable_key=str(opcion.stable_key),
                    text=str(opcion.text),
                    position=int(opcion.position),
                    label=opcion.label,
                )
                for opcion in opciones
            ),
            # La clave solo sale si se pide: el valor por defecto no la lleva (contrato §9).
            correct_option_keys=(
                tuple(entrada.correct_option_keys) if include_key and entrada is not None else ()
            ),
            key_outcome=entrada.outcome.value if entrada is not None else None,
            explanation_count=explicaciones,
        )

    def _key_view(self, session: Session, fila: AnswerKeyVersionRecord) -> AnswerKeyView:
        entradas = (
            session.execute(
                select(AnswerKeyEntryRecord)
                .where(AnswerKeyEntryRecord.answer_key_version_id == fila.id)
                .order_by(AnswerKeyEntryRecord.question_version_id)
            )
            .scalars()
            .all()
        )
        return AnswerKeyView(
            id=fila.id,
            question_set_id=fila.question_set_id,
            version_no=int(fila.version_no),
            status=str(fila.status),
            source_document_version_id=fila.source_document_version_id,
            supersedes_id=fila.supersedes_id,
            published_at=fila.published_at,
            approved_at=fila.approved_at,
            created_at=fila.created_at,
            entries=tuple(
                KeyEntryView(
                    question_version_id=entrada.question_version_id,
                    outcome=str(entrada.outcome),
                    correct_option_keys=tuple(
                        str(clave) for clave in json.loads(entrada.correct_option_keys_json or "[]")
                    ),
                    notes=entrada.notes,
                )
                for entrada in entradas
            ),
        )

    @staticmethod
    def _set_domain(fila: QuestionSetRecord) -> QuestionSet:
        return QuestionSet(
            id=fila.id,
            title=str(fila.title),
            opposition_id=fila.opposition_id,
            set_type=SetType(str(fila.set_type)),
            model_code=fila.model_code,
            source_document_version_id=fila.source_document_version_id,
        )

    @staticmethod
    def _key_domain(fila: AnswerKeyVersionRecord) -> AnswerKeyVersion:
        return AnswerKeyVersion(
            id=fila.id,
            question_set_id=fila.question_set_id,
            version_no=int(fila.version_no),
            approved_at=fila.approved_at,
            source_document_version_id=fila.source_document_version_id,
        )

    @staticmethod
    def _audit(
        session: Session,
        *,
        actor: str,
        action: str,
        object_type: str,
        object_id: str,
        before: Mapping[str, object],
        after: Mapping[str, object],
        now: datetime,
    ) -> str:
        evento = AuditEventRecord(
            id=_new_id(),
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=object_id,
            before_json=json.dumps(before, ensure_ascii=False),
            after_json=json.dumps(after, ensure_ascii=False),
            correlation_id=None,
            created_at=now,
        )
        session.add(evento)
        return evento.id


#: Lo mínimo que `can_activate` necesita del conjunto y de la clave: los objetos de dominio, que ya
#: describen esas reglas. No se arrastra la fila de base de datos al dominio ni se inventa un tipo.
__all__ = ["SqlAlchemyQuestionRepository"]
