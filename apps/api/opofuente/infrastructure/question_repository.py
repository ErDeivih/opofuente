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
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy import text as sql_text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from opofuente.application.question_models import (
    AnswerKeyView,
    ConflictingTopicView,
    ExplanationView,
    IssueReportView,
    KeyEntryView,
    OptionView,
    ProgrammeNodeRef,
    QuestionEvidenceView,
    QuestionExclusionView,
    QuestionPage,
    QuestionSetPage,
    QuestionSetView,
    QuestionTopicConflictView,
    QuestionTopicProposalsView,
    QuestionTopicView,
    QuestionView,
    SaveQuestionsOutcome,
    TopicProposalView,
)
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.questions import (
    AnswerKeyEntry,
    AnswerKeyVersion,
    KeyOutcome,
    Origin,
    OriginScope,
    ParsedQuestion,
    QuestionSet,
    SetDistribution,
    SetType,
    can_activate,
    question_fingerprint,
)
from opofuente.infrastructure.curriculum_order import curriculum_order
from opofuente.infrastructure.db_models import (
    AnswerKeyEntryRecord,
    AnswerKeyVersionRecord,
    AuditEventRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    DerivedKeyRecord,
    EvidenceSpanRecord,
    KeyGapRecord,
    OppositionRecord,
    OptionVersionRecord,
    QuestionCurriculumExclusionRecord,
    QuestionEvidenceRecord,
    QuestionExplanationRecord,
    QuestionIssueReportRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
)
from opofuente.infrastructure.key_policy import clave_servible


def _new_id() -> str:
    return str(uuid4())


def _topic_view(mapeo: CurriculumMappingRecord, nodo: CurriculumNodeRecord) -> QuestionTopicView:
    """Un mapeo pregunta↔nodo leído como tema: el mapeo, con el nodo que le da nombre y código."""
    return QuestionTopicView(
        mapping_id=str(mapeo.id),
        question_version_id=str(mapeo.subject_id),
        curriculum_node_id=str(nodo.id),
        official_code=str(nodo.official_code),
        title=str(nodo.title),
        status=str(mapeo.status),
        confidence=float(mapeo.confidence),
        created_at=mapeo.created_at,
    )


def _reason(reason: str | None) -> dict[str, object]:
    """El motivo, si lo hay, listo para el `after` de la auditoría.

    Un motivo en blanco no se guarda: una clave con un hueco dentro parece un motivo y no lo es.
    """
    limpio = (reason or "").strip()
    return {"reason": limpio} if limpio else {}


def _node_ref(nodo: CurriculumNodeRecord) -> ProgrammeNodeRef:
    """Un nodo del programa como referencia para una propuesta: su identificador, sus dos códigos y
    su título, que es lo que se enseña y lo que se manda de vuelta al escribir."""
    return ProgrammeNodeRef(
        node_id=str(nodo.id),
        official_code=str(nodo.official_code),
        path=str(nodo.path),
        title=str(nodo.title),
    )


def _orphan_proposal(
    mapeo: CurriculumMappingRecord,
    epigrafe: CurriculumNodeRecord,
    parents: Mapping[str, CurriculumNodeRecord],
    reasons: Mapping[str, str],
) -> TopicProposalView | None:
    """Un epígrafe propuesto cuyo tema nadie propuso (ni está aceptado), como candidato de su tema.

    Sin esto, la propuesta existiría, mantendría la pregunta en la cola y no habría forma de
    decidirla: la tarjeta saldría vacía. `None` si el padre no está en el programa, que sería un
    árbol roto y no algo que se pueda proponer.
    """
    padre = None if epigrafe.parent_id is None else parents.get(str(epigrafe.parent_id))
    if padre is None:
        return None
    return TopicProposalView(
        mapping_id=str(mapeo.id),
        topic=_node_ref(padre),
        epigraphs=(_node_ref(epigrafe),),
        confidence=float(mapeo.confidence),
        reason=reasons.get(str(mapeo.id)),
        created_at=mapeo.created_at,
    )


def _exclusion_view(
    fila: QuestionCurriculumExclusionRecord, stem: str | None = None
) -> QuestionExclusionView:
    """Una marca de fuera de temario leída como vista: la pregunta, el motivo y quién lo decidió."""
    return QuestionExclusionView(
        question_version_id=str(fila.question_version_id),
        reason=str(fila.reason),
        actor=str(fila.actor),
        note=fila.note,
        created_at=fila.created_at,
        stem=stem,
    )


#: Filtro de las versiones que **son** pregunta del conjunto.
#:
#: Corregir una pregunta no borra la anterior: la deja `superseded` para poder leer qué decía. Pero
#: una versión sustituida no es una pregunta del banco, y contarla lo infla: con una corrección, un
#: examen de 70 preguntas pasa a tener 71, la lista del banco enseña la versión vieja y una sesión
#: nueva puede componerse con ella (DEBT-025). Solo queda fuera `superseded`: una pregunta
#: `annulled` sigue siendo parte del examen, y quien dice que está anulada es su clave.
_NO_SUSTITUIDAS: ColumnElement[bool] = QuestionVersionRecord.status != "superseded"

#: Cuántos identificadores caben en un `IN (...)`. SQLite admite muchos más, pero una consulta con
#: mil parámetros se compila despacio: una sesión de examen tiene 85 preguntas y una comprobación de
#: una sesión entera cabe de sobra en una tanda.
_TANDA_DE_CONSULTA = 500

#: Los tres ámbitos de procedencia (`0037`, D10). El vocabulario vive en el dominio
#: (`OriginScope`) y aquí se materializa una vez para no recorrer el enumerado en cada cambio.
_ORIGENES = frozenset(valor.value for valor in OriginScope)


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
        origin_scope: str = OriginScope.DESCONOCIDA.value,
        actor: str = "local",
    ) -> QuestionSetView:
        """Crea un conjunto. El título vacío no entra: un conjunto sin nombre no se puede elegir."""
        if not title.strip():
            raise InvariantViolationError("Un conjunto de preguntas necesita título")
        if origin_scope not in _ORIGENES:
            raise InvariantViolationError(
                f"«{origin_scope}» no es un ámbito de procedencia de conjunto"
            )
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
                origin_scope=origin_scope,
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
                after={
                    "title": fila.title,
                    "set_type": set_type,
                    "model_code": fila.model_code,
                    "origin_scope": fila.origin_scope,
                },
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

    def sets_by_ids(self, set_ids: Sequence[str]) -> dict[str, QuestionSetView]:
        """Los conjuntos de esos identificadores, en **una** consulta y con sus recuentos.

        Es la versión por lotes de `get_set`, y existe por el mismo motivo que
        `questions_by_ids`: quien compone una sesión recorre cientos o miles de preguntas de decenas
        de temas, y una consulta por conjunto (más tres de recuento y una de claves cada una) es el
        N+1 que hacía que montar un simulacro tardara minutos. Devuelve solo los que existen: pedir
        un identificador que no está no es un error, es que no está.
        """
        if not set_ids:
            return {}
        unicos = tuple(dict.fromkeys(set_ids))
        with self._session_factory() as session:
            filas: list[QuestionSetRecord] = []
            # En tandas: una composición de todo el temario pide más identificadores de los que
            # SQLite admite en una sola cláusula `IN` (999 por defecto).
            for inicio in range(0, len(unicos), _TANDA_DE_CONSULTA):
                tanda = unicos[inicio : inicio + _TANDA_DE_CONSULTA]
                filas.extend(
                    session.execute(
                        select(QuestionSetRecord).where(QuestionSetRecord.id.in_(list(tanda)))
                    )
                    .scalars()
                    .all()
                )
            if not filas:
                return {}
            identificadores = [str(fila.id) for fila in filas]
            # Los tres recuentos de `_set_view`, agrupados en tres consultas para todo el lote en
            # lugar de tres por conjunto.
            preguntas: dict[str, int] = {}
            reservas: dict[str, int] = {}
            incompletas: dict[str, int] = {}
            claves_por_conjunto: dict[str, list[AnswerKeyVersionRecord]] = {}
            for inicio in range(0, len(identificadores), _TANDA_DE_CONSULTA):
                tanda_actual = identificadores[inicio : inicio + _TANDA_DE_CONSULTA]
                preguntas.update(
                    {
                        str(set_id): int(total)
                        for set_id, total in session.execute(
                            select(QuestionVersionRecord.question_set_id, func.count())
                            .where(
                                QuestionVersionRecord.question_set_id.in_(tanda_actual),
                                _NO_SUSTITUIDAS,
                            )
                            .group_by(QuestionVersionRecord.question_set_id)
                        ).all()
                    }
                )
                reservas.update(
                    {
                        str(set_id): int(total)
                        for set_id, total in session.execute(
                            select(QuestionVersionRecord.question_set_id, func.count())
                            .where(
                                QuestionVersionRecord.question_set_id.in_(tanda_actual),
                                QuestionVersionRecord.is_reserve.is_(True),
                                _NO_SUSTITUIDAS,
                            )
                            .group_by(QuestionVersionRecord.question_set_id)
                        ).all()
                    }
                )
                incompletas.update(
                    {
                        str(set_id): int(total)
                        for set_id, total in session.execute(
                            select(QuestionVersionRecord.question_set_id, func.count())
                            .where(
                                QuestionVersionRecord.question_set_id.in_(tanda_actual),
                                QuestionVersionRecord.status == "incomplete",
                            )
                            .group_by(QuestionVersionRecord.question_set_id)
                        ).all()
                    }
                )
                for clave in (
                    session.execute(
                        select(AnswerKeyVersionRecord).where(
                            AnswerKeyVersionRecord.question_set_id.in_(tanda_actual)
                        )
                    )
                    .scalars()
                    .all()
                ):
                    claves_por_conjunto.setdefault(clave.question_set_id, []).append(clave)
            return {
                fila.id: self._set_view_con_recuentos(
                    fila,
                    preguntas=preguntas.get(fila.id, 0),
                    reservas=reservas.get(fila.id, 0),
                    incompletas=incompletas.get(fila.id, 0),
                    claves=tuple(claves_por_conjunto.get(fila.id, ())),
                )
                for fila in filas
            }

    def set_distribution(
        self, set_id: str, distribution: str, *, now: datetime, actor: str = "local"
    ) -> bool:
        """Cambia quién puede ver un conjunto. `False` si el conjunto no existe.

        Es un cambio deliberado y se audita: pasar un banco privado a `public` es hacerlo
        publicable, y tiene que quedar escrito quién lo hizo y cuándo.
        """
        if distribution not in {valor.value for valor in SetDistribution}:
            raise InvariantViolationError(f"«{distribution}» no es una distribución de conjunto")
        with self._session_factory() as session:
            fila = session.get(QuestionSetRecord, set_id)
            if fila is None:
                return False
            anterior = str(fila.distribution)
            if anterior == distribution:
                return True
            fila.distribution = distribution
            fila.updated_at = now
            self._audit(
                session,
                actor=actor,
                action="question_set.distribution_changed",
                object_type="question_set",
                object_id=set_id,
                before={"distribution": anterior},
                after={"distribution": distribution},
                now=now,
            )
            session.commit()
            return True

    def set_origin_scope(
        self, set_id: str, origin_scope: str, *, now: datetime, actor: str = "local"
    ) -> bool:
        """Cambia de qué administración sale el material de un conjunto. `False` si no existe.

        Es un cambio deliberado y se **audita** por la misma razón que `distribution`: marcar un
        conjunto como `otra_administracion` lo deja fuera de los simulacros, y eso es una decisión
        sobre qué mide el examen simulado; tiene que quedar escrito quién la tomó y cuándo.
        """
        if origin_scope not in _ORIGENES:
            raise InvariantViolationError(
                f"«{origin_scope}» no es un ámbito de procedencia de conjunto"
            )
        with self._session_factory() as session:
            fila = session.get(QuestionSetRecord, set_id)
            if fila is None:
                return False
            anterior = str(fila.origin_scope)
            if anterior == origin_scope:
                return True
            fila.origin_scope = origin_scope
            fila.updated_at = now
            self._audit(
                session,
                actor=actor,
                action="question_set.origin_scope_changed",
                object_type="question_set",
                object_id=set_id,
                before={"origin_scope": anterior},
                after={"origin_scope": origin_scope},
                now=now,
            )
            session.commit()
            return True

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
                        source_section_id=parseada.source_section_id,
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
        else:
            # Sin estado pedido se listan las preguntas del banco, no su historia: la versión
            # sustituida solo aparece si alguien la pide por su estado (DEBT-025).
            filtros.append(_NO_SUSTITUIDAS)
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

    def questions_by_ids(
        self, question_ids: Sequence[str], *, include_options: bool = True
    ) -> dict[str, QuestionView]:
        """Las preguntas de esos identificadores, en **una** consulta y con sus opciones.

        Es la versión por lotes de `get_question`, y existe porque quien compone una sesión recorre
        el banco entero de los temas pedidos —miles de preguntas— y una consulta por pregunta (más
        sus opciones, sus explicaciones y su clave) es exactamente el N+1 que convertía montar un
        simulacro en dos minutos y medio. Los que no existen simplemente no salen en el mapa.

        `include_options=False` deja las opciones fuera: la composición solo las necesita para la
        firma de «la misma pregunta», y eso solo hace falta en las que de verdad van a poder entrar.
        Cargar las 74.000 opciones por pregunta del banco para descartar casi todas por la clave era
        el último tercio del tiempo del montaje.
        """
        if not question_ids:
            return {}
        unicos = tuple(dict.fromkeys(question_ids))
        with self._session_factory() as session:
            filas: list[QuestionVersionRecord] = []
            # En tandas: la composición de un simulacro pide más identificadores de los que SQLite
            # admite en una sola cláusula `IN` (999 por defecto).
            for inicio in range(0, len(unicos), _TANDA_DE_CONSULTA):
                tanda = unicos[inicio : inicio + _TANDA_DE_CONSULTA]
                filas.extend(
                    session.execute(
                        select(QuestionVersionRecord).where(
                            QuestionVersionRecord.id.in_(list(tanda))
                        )
                    )
                    .scalars()
                    .all()
                )
            if not filas:
                return {}
            identificadores = [str(fila.id) for fila in filas]
            opciones = (
                self._options_by_question(session, identificadores) if include_options else {}
            )
            explicaciones = self._explanations_count(session, identificadores)
            return {
                fila.id: self._question_view_con_datos(
                    fila,
                    # **Sin claves**: la composición pide el desenlace de la clave por otro camino
                    # (`active_key_entries_by_set`, que trae solo la plantilla que corrige de cada
                    # conjunto). Leer aquí todas las plantillas de todos los conjuntos para rellenar
                    # un `key_outcome` que la composición no mira era la mitad del tiempo que
                    # quedaba: medido, 2,8 s de los 9,8 del montaje.
                    claves={},
                    opciones=opciones.get(fila.id, ()),
                    explicaciones=explicaciones.get(fila.id, 0),
                    include_key=False,
                )
                for fila in filas
            }

    def options_by_question_ids(
        self, question_ids: Sequence[str]
    ) -> dict[str, tuple[OptionView, ...]]:
        """Las opciones de esas preguntas, en **una** consulta.

        Es la segunda mitad de `questions_by_ids(include_options=False)`: la composición carga
        primero las preguntas sin opciones, descarta las que no pueden entrar y solo entonces pide
        las opciones de las que quedan, que son las únicas cuya firma hace falta.
        """
        if not question_ids:
            return {}
        unicos = [str(uno) for uno in dict.fromkeys(question_ids)]
        with self._session_factory() as session:
            agrupadas: dict[str, list[OptionView]] = {}
            for inicio in range(0, len(unicos), _TANDA_DE_CONSULTA):
                tanda = unicos[inicio : inicio + _TANDA_DE_CONSULTA]
                for opcion in self._options_by_question(session, tanda).values():
                    for vista in opcion:
                        agrupadas.setdefault(vista.question_version_id, []).append(
                            OptionView(
                                id=vista.id,
                                stable_key=str(vista.stable_key),
                                text=str(vista.text),
                                position=int(vista.position),
                                label=vista.label,
                            )
                        )
            return {pregunta_id: tuple(vistas) for pregunta_id, vistas in agrupadas.items()}

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
            veces = Counter(entrada.question_version_id for entrada in entries)
            repetidas = sorted(pregunta for pregunta, cuantas in veces.items() if cuantas > 1)
            if repetidas:
                # La base lo rechazaría igual, pero como un 500: esto es un error de quien llama.
                raise InvariantViolationError(
                    "La plantilla incluye la misma pregunta más de una vez: "
                    + ", ".join(repetidas[:5])
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

    def set_key_source(
        self,
        key_id: str,
        *,
        source_document_version_id: str | None,
        now: datetime,
        actor: str = "local",
    ) -> bool:
        """Cambia la plantilla oficial enlazada a una clave. Queda en la auditoría."""
        with self._session_factory() as session:
            fila = session.get(AnswerKeyVersionRecord, key_id)
            if fila is None:
                return False
            anterior = fila.source_document_version_id
            fila.source_document_version_id = source_document_version_id
            self._audit(
                session,
                actor=actor,
                action="answer_key.source_linked"
                if source_document_version_id is not None
                else "answer_key.source_unlinked",
                object_type="answer_key_version",
                object_id=key_id,
                before={"source_document_version_id": anterior},
                after={"source_document_version_id": source_document_version_id},
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

    def explanations_of(self, question_id: str) -> tuple[ExplanationView, ...]:
        """Explicaciones de una pregunta: la de la pregunta entera y las de sus opciones (S12.7).

        Se devuelven **todas**, con su `option_stable_key` a la vista: la de la pregunta entera lo
        lleva nulo y la interfaz la coloca bajo el enunciado; las demás, bajo su opción. El orden es
        la pregunta entera primero y después las opciones por su clave.
        """
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(QuestionExplanationRecord)
                    .where(QuestionExplanationRecord.question_version_id == question_id)
                    .order_by(
                        QuestionExplanationRecord.option_stable_key.is_(None).desc(),
                        QuestionExplanationRecord.option_stable_key,
                        QuestionExplanationRecord.id,
                    )
                )
                .scalars()
                .all()
            )
        return tuple(
            ExplanationView(
                id=str(fila.id),
                question_version_id=str(fila.question_version_id),
                option_stable_key=fila.option_stable_key,
                text=str(fila.text),
                origin=str(fila.origin),
                status=str(fila.status),
                model_name=fila.model_name,
                created_at=fila.created_at,
            )
            for fila in filas
        )

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

    def question_ids_by_position(self, set_id: str) -> dict[int, tuple[str, ...]]:
        """Las preguntas de cada posición: es lo que alinea una plantilla suelta.

        Devuelve **todas** las de cada posición, no una: un conjunto con dos preguntas en la misma
        posición no puede recibir la plantilla por número, y elegir una a ciegas (lo que hacía un
        diccionario posición → pregunta) aplicaba la clave a la pregunta equivocada sin avisar.

        Sin la versión sustituida (DEBT-025): la corregida conserva la posición de la anterior, y
        con las dos dentro la plantilla se alinearía con la que devolviera el orden de la consulta.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionVersionRecord.position, QuestionVersionRecord.id)
                .where(
                    QuestionVersionRecord.question_set_id == set_id,
                    _NO_SUSTITUIDAS,
                )
                .order_by(QuestionVersionRecord.position, QuestionVersionRecord.id)
            ).all()
        por_posicion: dict[int, list[str]] = {}
        for posicion, pregunta_id in filas:
            por_posicion.setdefault(int(posicion), []).append(str(pregunta_id))
        return {posicion: tuple(ids) for posicion, ids in por_posicion.items()}

    def questions_in_document_order(self, set_id: str) -> tuple[tuple[str, int], ...]:
        """`(id, posición)` de las preguntas vigentes **en el orden del documento**.

        La posición no sirve para ordenar un examen cuya numeración se reinicia en cada sección.
        El orden de inserción sí: las preguntas se guardan según se leen del material. Una pregunta
        corregida tiene su versión nueva al final, así que se ordena por la de su **primera**
        versión, que es la que ocupa su sitio.
        """
        with self._session_factory() as session:
            filas = session.execute(
                sql_text(
                    "SELECT rowid, id, supersedes_id, position, status FROM question_versions "
                    "WHERE question_set_id = :conjunto"
                ),
                {"conjunto": set_id},
            ).all()
        por_id = {str(fila.id): fila for fila in filas}

        def raiz(pregunta_id: str) -> int:
            vistos: set[str] = set()
            actual = por_id[pregunta_id]
            while actual.supersedes_id is not None and str(actual.supersedes_id) in por_id:
                if str(actual.id) in vistos:
                    break
                vistos.add(str(actual.id))
                actual = por_id[str(actual.supersedes_id)]
            return int(actual.rowid)

        vigentes = [fila for fila in filas if fila.status != "superseded"]
        vigentes.sort(key=lambda fila: (raiz(str(fila.id)), int(fila.rowid)))
        return tuple((str(fila.id), int(fila.position)) for fila in vigentes)

    def all_questions(self, set_id: str) -> tuple[QuestionView, ...]:
        """Todas las preguntas de un conjunto **en el orden del documento**, sin clave.

        Es la lista de la que una sesión elige su composición: no lleva la solución porque una
        sesión se corrige con la clave **activa** congelada, no con lo que devuelva esta consulta.
        Sin tope de página a propósito: recortar aquí dejaría una sesión oficial sin las últimas
        preguntas.

        El orden es el del **documento** (`questions_in_document_order`), no el de la posición: un
        examen que numera desde 1 en cada sección —los del INAP, sin ir más lejos— tiene posiciones
        repetidas, y ordenar por posición mezcla la parte primera con los supuestos prácticos.
        Medido el 2 de octubre de 2026 con los exámenes reimportados: la sesión salía con las
        preguntas intercaladas (parte primera nº 1, supuesto I nº 1, supuesto II nº 1, parte primera
        nº 2…), que no es el examen.

        Por eso el orden del documento se usa **solo** cuando hay posiciones repetidas. Sin ellas
        se ordena por posición, como siempre: el orden de inserción no es el de la posición si se
        cambió la posición de una pregunta (`update_question`) o si el conjunto se importó en
        tandas desordenadas, y en esos casos la posición es la que manda.

        La versión sustituida de una pregunta corregida **no** entra (DEBT-025): si entrara, una
        sesión nueva podría preguntar el texto viejo y contar la pregunta dos veces.
        """
        orden = list(self.questions_in_document_order(set_id))
        posiciones = [posicion for _identificador, posicion in orden]
        if len(set(posiciones)) == len(posiciones):
            orden.sort(key=lambda par: par[1])
        with self._session_factory() as session:
            filas = {
                str(fila.id): fila
                for fila in session.execute(
                    select(QuestionVersionRecord).where(
                        QuestionVersionRecord.question_set_id == set_id,
                        _NO_SUSTITUIDAS,
                    )
                )
                .scalars()
                .all()
            }
            return tuple(
                self._question_view(session, filas[identificador], {}, include_key=False)
                for identificador, _posicion in orden
                if identificador in filas
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

    def node_facts(self, node_id: str) -> tuple[str, str, str] | None:
        """`(tipo, código oficial, título)` del nodo del programa, o `None` si no existe.

        El **tipo** es lo que permite rechazar con motivo un destino que no vale: una pregunta se
        asigna a un tema, y eso no se puede suponer desde fuera sin leer el nodo.
        """
        with self._session_factory() as session:
            fila = session.get(CurriculumNodeRecord, node_id)
            if fila is None:
                return None
            return str(fila.node_type), str(fila.official_code), str(fila.title)

    def question_topics(self, question_version_id: str) -> tuple[QuestionTopicView, ...] | None:
        """Los temas de una pregunta, con el estado de cada mapeo, por orden de programa.

        `None` es «la pregunta no existe» y una tupla vacía es «existe y no tiene ningún tema»: son
        dos cosas distintas y la ruta las contesta distinto (404 y lista vacía).
        """
        with self._session_factory() as session:
            if session.get(QuestionVersionRecord, question_version_id) is None:
                return None
            filas = session.execute(
                select(CurriculumMappingRecord, CurriculumNodeRecord)
                .join(
                    CurriculumNodeRecord,
                    CurriculumNodeRecord.id == CurriculumMappingRecord.curriculum_node_id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.subject_id == question_version_id,
                )
                .order_by(*curriculum_order(CurriculumNodeRecord.path))
            ).all()
            return tuple(_topic_view(mapeo, nodo) for mapeo, nodo in filas)

    def assign_question_to_node(
        self,
        question_version_id: str,
        *,
        node_id: str,
        now: datetime,
        actor: str = "local",
        confidence: float = 1.0,
        coverage_type: str = "partial",
        status: str = "accepted",
        reason: str | None = None,
        promote: bool = False,
    ) -> tuple[QuestionTopicView, str] | None:
        """Asigna una pregunta a un nodo y devuelve `(tema, qué ha pasado)`. `None` si algo no
        existe.

        El segundo valor es del vocabulario del lote: `created` (esta llamada lo escribió),
        `existing` (ya estaba tal cual) o `promoted` (ya estaba **como propuesta** y esta llamada la
        ha confirmado). Tres estados y no dos porque la cola de revisión vive justo en el tercero:
        «ya estaba» y «lo he confirmado» no pueden contarse igual.

        Idempotente por `(nodo, pregunta)`: si el mapeo ya estaba con el mismo estado se devuelve
        con `existing` y **no** se escribe un segundo evento de auditoría. Dos eventos idénticos no
        son dos hechos, y la clasificación de 7.677 preguntas se reintenta: ensuciar el registro con
        la misma línea repetida lo haría ilegible justo donde hay que leer qué pasó.

        `promote` es lo que convierte una **propuesta** (`provisional`) en la decisión que dice
        `status`, con su evento. Va apagado por defecto y a propósito: la catalogación automática
        (S12.6) y el clasificador escriben con `status="accepted"`, y ninguno de los dos puede
        confirmar por su cuenta una propuesta que el propietario no ha mirado —el segundo, además,
        solo coge preguntas sin ningún mapeo, así que nunca se topa con una.

        La idempotencia vale también **contra otro escritor**: el worker cataloga al aceptar una
        versión (S12.6) y una pasada de clasificación de miles de preguntas puede coincidir con él.
        Cuando eso pasa, la comprobación de arriba no vio la fila y el `INSERT` choca contra
        `uq_mapping_identity`; eso no es un fallo de quien pidió la asignación —la pareja ya está,
        que es lo que quería—, así que se relee y se devuelve como existente en lugar de dejar un
        500 en medio de un lote. El evento que se había escrito se va con el `rollback`: queda el
        del escritor que ganó, no dos.

        `status` distingue una decisión de una **propuesta**: `accepted` es un tema decidido
        (cuenta en todo) y `provisional` es lo que un motor propuso y nadie ha confirmado (cola de
        revisión, no cuenta en el diagnóstico). `reason` es el motivo en palabras del clasificador
        y viaja a la auditoría: es donde se lee por qué se asignó, y no forma parte de la identidad
        del mapeo.

        No comprueba el **tipo** del nodo: la catalogación automática (S12.6) hereda el destino del
        documento del que salen las preguntas y puede apuntar a un bloque a propósito. Quién decide
        si un destino vale es el servicio, que sí tiene el motivo que hay que dar.
        """
        with self._session_factory() as session:
            if session.get(QuestionVersionRecord, question_version_id) is None:
                return None
            nodo = session.get(CurriculumNodeRecord, node_id)
            if nodo is None:
                return None
            existente = session.execute(
                select(CurriculumMappingRecord).where(
                    CurriculumMappingRecord.curriculum_node_id == node_id,
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.subject_id == question_version_id,
                )
            ).scalar_one_or_none()
            if existente is not None:
                if not promote or str(existente.status) == status:
                    return _topic_view(existente, nodo), "existing"
                return (
                    self._promote_mapping(
                        session,
                        existente,
                        nodo,
                        status=status,
                        confidence=confidence,
                        reason=reason,
                        actor=actor,
                        now=now,
                    ),
                    "promoted",
                )
            mapeo = CurriculumMappingRecord(
                id=_new_id(),
                curriculum_node_id=node_id,
                subject_type="question_version",
                subject_id=question_version_id,
                coverage_type=coverage_type,
                depth=int(nodo.depth),
                confidence=confidence,
                status=status,
                source_proposal_id=None,
                created_at=now,
                # La base exige fecha de aprobación en lo aceptado y **solo** en lo aceptado: una
                # propuesta provisional con fecha de aprobación sería una aprobación que no ha
                # ocurrido.
                approved_at=now if status == "accepted" else None,
            )
            # La vista se arma antes de confirmar: el mapeo ya tiene todos sus valores y así la
            # respuesta no depende de una lectura extra tras el `commit`.
            vista = _topic_view(mapeo, nodo)
            session.add(mapeo)
            self._audit(
                session,
                actor=actor,
                action="question.mapped",
                object_type="curriculum_mapping",
                object_id=mapeo.id,
                before={},
                after={
                    "node_id": node_id,
                    "question_version_id": question_version_id,
                    "status": status,
                    "confidence": confidence,
                    **_reason(reason),
                },
                now=now,
            )
            try:
                session.commit()
            except IntegrityError:
                # Otro escritor confirmó la misma pareja entre la comprobación y el `INSERT`. Se
                # relee con la sesión ya limpia; si no está, el choque era de otra cosa y se propaga
                # en vez de esconderse.
                session.rollback()
                repetido = session.execute(
                    select(CurriculumMappingRecord).where(
                        CurriculumMappingRecord.curriculum_node_id == node_id,
                        CurriculumMappingRecord.subject_type == "question_version",
                        CurriculumMappingRecord.subject_id == question_version_id,
                    )
                ).scalar_one_or_none()
                nodo = session.get(CurriculumNodeRecord, node_id)
                if repetido is None or nodo is None:
                    raise
                return _topic_view(repetido, nodo), "existing"
            return vista, "created"

    def _promote_mapping(
        self,
        session: Session,
        mapeo: CurriculumMappingRecord,
        nodo: CurriculumNodeRecord,
        *,
        status: str,
        confidence: float,
        reason: str | None,
        actor: str,
        now: datetime,
    ) -> QuestionTopicView:
        """Confirma (o vuelve a proponer) un mapeo que ya estaba, y lo deja auditado.

        El `before` lleva el estado y la confianza de antes porque es lo que hace falta para
        entender la decisión al leer el registro: sin él, un evento de confirmación no dice de
        dónde venía. La fecha de aprobación se escribe al confirmar y se retira al volver a
        proponer, por la misma razón que en el alta: una propuesta con fecha de aprobación sería
        una aprobación que no ha ocurrido.
        """
        antes = {"status": str(mapeo.status), "confidence": float(mapeo.confidence)}
        mapeo.status = status
        mapeo.confidence = confidence
        mapeo.approved_at = now if status == "accepted" else None
        vista = _topic_view(mapeo, nodo)
        self._audit(
            session,
            actor=actor,
            action="question.mapped",
            object_type="curriculum_mapping",
            object_id=str(mapeo.id),
            before=antes,
            after={
                "node_id": str(mapeo.curriculum_node_id),
                "question_version_id": str(mapeo.subject_id),
                "status": status,
                "confidence": confidence,
                **_reason(reason),
            },
            now=now,
        )
        session.commit()
        return vista

    def unmap_question_from_node(
        self,
        question_version_id: str,
        *,
        node_id: str,
        now: datetime,
        actor: str = "local",
    ) -> bool:
        """Quita el tema que la pregunta tenía en ese nodo y lo deja auditado (`question.unmapped`).

        `False` si la pareja no tenía mapeo: quitar lo que no estaba no es un hecho, y auditarlo
        dejaría en el registro una retirada que no ocurrió.
        """
        with self._session_factory() as session:
            fila = session.execute(
                select(CurriculumMappingRecord).where(
                    CurriculumMappingRecord.curriculum_node_id == node_id,
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.subject_id == question_version_id,
                )
            ).scalar_one_or_none()
            if fila is None:
                return False
            mapeo_id = str(fila.id)
            anterior: dict[str, object] = {
                "node_id": str(fila.curriculum_node_id),
                "question_version_id": str(fila.subject_id),
                "status": str(fila.status),
                "confidence": float(fila.confidence),
            }
            session.delete(fila)
            self._audit(
                session,
                actor=actor,
                action="question.unmapped",
                object_type="curriculum_mapping",
                object_id=mapeo_id,
                before=anterior,
                after={},
                now=now,
            )
            session.commit()
            return True

    def map_question_to_node(
        self,
        question_version_id: str,
        *,
        node_id: str,
        now: datetime,
        coverage_type: str = "partial",
        actor: str = "local",
    ) -> str | None:
        """Asigna una pregunta a un nodo del programa y devuelve su identificador de mapeo.

        Es el camino de la catalogación automática: idempotente por `(nodo, pregunta)` y con su
        evento de auditoría. `None` si la pregunta o el nodo no existen.
        """
        asignado = self.assign_question_to_node(
            question_version_id,
            node_id=node_id,
            now=now,
            actor=actor,
            coverage_type=coverage_type,
        )
        return None if asignado is None else asignado[0].mapping_id

    def parent_topic(self, node_id: str) -> tuple[str, str, str] | None:
        """El **tema** del que cuelga un nodo, subiendo por el árbol. `None` si no hay ninguno.

        Un epígrafe no sustituye a su tema: la pregunta se asigna a los dos, y para eso hay que
        saber cuál es el tema que lo contiene. Se sube por `parent_id` en lugar de cortar la ruta
        por puntos: la ruta es del programa y podría cambiar de forma, y el árbol es el que manda.
        """
        with self._session_factory() as session:
            actual = session.get(CurriculumNodeRecord, node_id)
            while actual is not None and actual.parent_id is not None:
                actual = session.get(CurriculumNodeRecord, actual.parent_id)
                if actual is None:
                    return None
                if str(actual.node_type) == "topic":
                    return str(actual.id), str(actual.official_code), str(actual.title)
        return None

    def exclude_question_from_curriculum(
        self,
        question_version_id: str,
        *,
        reason: str,
        now: datetime,
        actor: str = "local",
        note: str | None = None,
    ) -> tuple[QuestionExclusionView, bool] | None:
        """Declara una pregunta fuera del temario y deja el evento. `None` si la pregunta no existe.

        Idempotente por pregunta: una pregunta está fuera de temario o no lo está. Repetirlo
        devuelve la marca que ya estaba con `creado=False` y **no** escribe un segundo evento — el
        lote de clasificación se reintenta y la auditoría tiene que poder leerse.

        La marca **no** sustituye a un mapeo ni lo retira: si la pregunta tuviera un tema aceptado y
        se declarara fuera de temario, las dos cosas estarían dichas. Quien tiene que decidir entre
        una y otra es el servicio, que es donde se puede explicar por qué.
        """
        with self._session_factory() as session:
            if session.get(QuestionVersionRecord, question_version_id) is None:
                return None
            existente = session.get(QuestionCurriculumExclusionRecord, question_version_id)
            if existente is not None:
                return _exclusion_view(existente), False
            fila = QuestionCurriculumExclusionRecord(
                question_version_id=question_version_id,
                reason=reason,
                note=(note or "").strip() or None,
                actor=actor,
                created_at=now,
            )
            vista = _exclusion_view(fila)
            session.add(fila)
            self._audit(
                session,
                actor=actor,
                action="question.out_of_syllabus",
                object_type="question_version",
                object_id=question_version_id,
                before={},
                after={"question_version_id": question_version_id, "reason": reason},
                now=now,
            )
            try:
                session.commit()
            except IntegrityError:
                # Otro escritor declaró lo mismo entre la comprobación y el `INSERT`. La marca ya
                # está, que es lo que se quería; se relee y se devuelve como existente.
                session.rollback()
                repetido = session.get(QuestionCurriculumExclusionRecord, question_version_id)
                if repetido is None:
                    raise
                return _exclusion_view(repetido), False
            return vista, True

    def question_exclusion(self, question_version_id: str) -> QuestionExclusionView | None:
        """La marca de fuera de temario de una pregunta, o `None` si no la tiene."""
        with self._session_factory() as session:
            fila = session.get(QuestionCurriculumExclusionRecord, question_version_id)
            return None if fila is None else _exclusion_view(fila)

    def excluded_question_ids(self, set_id: str) -> frozenset[str]:
        """Las preguntas del conjunto declaradas fuera de temario.

        Lo usa la composición de **simulacros y exámenes oficiales**: el examen se parece al real,
        y la normativa de otra administración no cae en el de TAI. En un test por tema y en los
        apuntes sí cuentan, y por eso el filtro vive en quien compone y no en el recuento.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionCurriculumExclusionRecord.question_version_id)
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id
                    == QuestionCurriculumExclusionRecord.question_version_id,
                )
                .where(QuestionVersionRecord.question_set_id == set_id)
            ).scalars()
            return frozenset(str(fila) for fila in filas)

    def excluded_question_ids_by_set(self, set_ids: Sequence[str]) -> dict[str, frozenset[str]]:
        """Las preguntas excluidas de **cada** uno de esos conjuntos, en **una** consulta.

        Es la versión por lotes de `excluded_question_ids`, y existe por el mismo motivo que las
        demás: quien compone recorre los conjuntos de los temas pedidos y una consulta por conjunto,
        cada una recorriendo la tabla entera de exclusiones en su unión, era otro de los N+1 del
        montaje de un simulacro. Un conjunto sin exclusiones no sale en el mapa: quien pregunta
        recibe el vacío.
        """
        if not set_ids:
            return {}
        unicos = tuple(dict.fromkeys(set_ids))
        agrupadas: dict[str, set[str]] = {}
        with self._session_factory() as session:
            for inicio in range(0, len(unicos), _TANDA_DE_CONSULTA):
                tanda = unicos[inicio : inicio + _TANDA_DE_CONSULTA]
                filas = session.execute(
                    select(
                        QuestionVersionRecord.question_set_id,
                        QuestionCurriculumExclusionRecord.question_version_id,
                    )
                    .join(
                        QuestionVersionRecord,
                        QuestionVersionRecord.id
                        == QuestionCurriculumExclusionRecord.question_version_id,
                    )
                    .where(QuestionVersionRecord.question_set_id.in_(tanda))
                ).all()
                for set_id, pregunta_id in filas:
                    agrupadas.setdefault(str(set_id), set()).add(str(pregunta_id))
        return {set_id: frozenset(preguntas) for set_id, preguntas in agrupadas.items()}

    def servable_question_ids(self, question_ids: Sequence[str]) -> frozenset[str]:
        """Las que se pueden **corregir**, con la política de claves de siempre y en una consulta.

        Lo usan los tres sitios del motor que eligen preguntas —el test de práctica por conjuntos,
        la práctica por tema y el repaso de fallos— y por eso está aquí y no en cada uno: lo que se
        puede practicar se puede repasar, y tener la regla tres veces es cómo se acaba con dos
        políticas (el repaso pedía plantilla activa y la práctica no).

        Se pide el bloque entero de identificadores, no pregunta a pregunta: una composición recorre
        cientos de preguntas y una consulta por cada una es justo lo que el motor no puede pagar.
        """
        if not question_ids:
            return frozenset()
        identificadores = list(question_ids)
        servibles: set[str] = set()
        with self._session_factory() as session:
            for inicio in range(0, len(identificadores), _TANDA_DE_CONSULTA):
                tanda = identificadores[inicio : inicio + _TANDA_DE_CONSULTA]
                filas = session.execute(
                    select(QuestionVersionRecord.id).where(
                        QuestionVersionRecord.id.in_(tanda),
                        clave_servible(QuestionVersionRecord.id),
                    )
                ).scalars()
                servibles.update(str(fila) for fila in filas)
        return frozenset(servibles)

    def key_reliability_by_question(self, question_ids: Sequence[str]) -> dict[str, str]:
        """El veredicto de la clave del conjunto de cada pregunta. Una consulta, no una por
        pregunta.

        Lo necesitan las **dos** cosas que dependen del veredicto y no pasan por la composición: la
        marca «clave en revisión» que se le enseña al alumno pregunta a pregunta, y la comprobación
        de que una sesión no lleva preguntas de un conjunto en cuarentena. Se pide por identificador
        y en una sola consulta porque una sesión tiene hasta 85 preguntas.
        """
        if not question_ids:
            return {}
        salida: dict[str, str] = {}
        with self._session_factory() as session:
            identificadores = list(question_ids)
            for inicio in range(0, len(identificadores), _TANDA_DE_CONSULTA):
                tanda = identificadores[inicio : inicio + _TANDA_DE_CONSULTA]
                filas = session.execute(
                    select(QuestionVersionRecord.id, QuestionSetRecord.key_reliability)
                    .join(
                        QuestionSetRecord,
                        QuestionSetRecord.id == QuestionVersionRecord.question_set_id,
                    )
                    .where(QuestionVersionRecord.id.in_(tanda))
                ).all()
                for pregunta_id, veredicto in filas:
                    salida[str(pregunta_id)] = str(veredicto)
        return salida

    def derived_keys(self) -> dict[str, tuple[str, ...]]:
        """Las letras de las claves **derivadas** de cada pregunta (`0039`, §1 del encargo).

        Se leen **todas** y de una vez, no pregunta a pregunta: la composición recorre el banco
        entero de los temas pedidos (miles de identificadores) y una consulta por pregunta sería
        justo lo que el motor no puede permitirse. La tabla tiene una fila por pregunta derivada, y
        el conjunto de las que lo están es pequeño por construcción: solo las que tienen cita
        verificada en los apuntes **y** coinciden con la respuesta del modelo sin apuntes.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    DerivedKeyRecord.question_version_id,
                    DerivedKeyRecord.correct_option_keys_json,
                )
            ).all()
        return {
            str(pregunta_id): tuple(str(letra) for letra in json.loads(str(crudo)))
            for pregunta_id, crudo in filas
        }

    def sets_with_derived_keys(self) -> frozenset[str]:
        """Los conjuntos con **alguna** clave derivada. Una consulta, y de una sola vez.

        Lo necesita el diagnóstico, que elige conjuntos enteros: uno en cuarentena del que se
        han derivado letras **sí** puede aportar sus preguntas derivadas a la muestra.
        """
        with self._session_factory() as session:
            filas = session.execute(select(DerivedKeyRecord.question_set_id).distinct()).all()
        return frozenset(str(fila[0]) for fila in filas)

    def questions_without_reliable_key(self) -> frozenset[str]:
        """Las preguntas que la derivación dejó **fuera** y con su motivo escrito.

        Son las preguntas de un conjunto en cuarentena cuya clave no se pudo derivar. Se excluyen
        **aunque su conjunto vuelva** a los tests: es la mitad del encargo que dice que las que no
        tienen clave fiable siguen fuera de ese conjunto. Una pregunta sin fila aquí entra por el
        camino de siempre (la clave de su conjunto), así que ningún conjunto sano cambia.
        """
        with self._session_factory() as session:
            filas = session.execute(select(KeyGapRecord.question_version_id)).all()
        return frozenset(str(fila[0]) for fila in filas)

    def clear_exclusion(
        self, question_version_id: str, *, now: datetime, actor: str = "local"
    ) -> bool:
        """Levanta la marca de fuera de temario y lo deja auditado. `False` si no la tenía.

        Existe porque las dos cosas no pueden ser verdad a la vez: si alguien asigna un tema a una
        pregunta marcada fuera de temario, está diciendo que **sí** es de este temario, y dejar la
        marca puesta la excluiría de los simulacros contradiciendo su propio tema. Lo que no se hace
        es borrarla en silencio: la retirada es un hecho y va al registro con su autor.
        """
        with self._session_factory() as session:
            fila = session.get(QuestionCurriculumExclusionRecord, question_version_id)
            if fila is None:
                return False
            anterior = {"reason": str(fila.reason)}
            session.delete(fila)
            self._audit(
                session,
                actor=actor,
                action="question.in_syllabus",
                object_type="question_version",
                object_id=question_version_id,
                before=anterior,
                after={},
                now=now,
            )
            session.commit()
            return True

    def list_exclusions(
        self,
        *,
        reason: str | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[tuple[QuestionExclusionView, ...], int]:
        """Las marcas de fuera de temario, de la más nueva a la más antigua, con el total.

        El total viaja aparte porque la pantalla de revisión lo necesita para decir cuántas quedan:
        contar en Python lo que se ha traído con un tope daría un número que miente.

        Y el **enunciado** viaja con cada marca: sin él, lo único que se puede enseñar de una
        pregunta excluida es un identificador, y un identificador no se puede juzgar. Es la misma
        razón por la que la cola de propuestas trae la pregunta entera.

        `q` busca en el enunciado (F16, la sección «No son preguntas»): con 769 enunciados rotos en
        la base, recorrerlos a ojo no es una forma de encontrar el que se busca. `LIKE` sin
        `lower()` a propósito: SQLite ya compara sin distinguir mayúsculas en ASCII, y envolver la
        columna en una función impediría cualquier uso de índice. Lo que no iguala son los
        acentos, y eso lo dice la pantalla.
        """
        filtro = [] if reason is None else [QuestionCurriculumExclusionRecord.reason == reason]
        if q is not None:
            filtro.append(QuestionVersionRecord.stem.like(f"%{q.strip()}%"))
        with self._session_factory() as session:
            total = session.execute(
                select(func.count())
                .select_from(QuestionCurriculumExclusionRecord)
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id
                    == QuestionCurriculumExclusionRecord.question_version_id,
                )
                .where(*filtro)
            ).scalar_one()
            filas = session.execute(
                select(QuestionCurriculumExclusionRecord, QuestionVersionRecord.stem)
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id
                    == QuestionCurriculumExclusionRecord.question_version_id,
                )
                .where(*filtro)
                .order_by(
                    QuestionCurriculumExclusionRecord.created_at.desc(),
                    QuestionCurriculumExclusionRecord.question_version_id,
                )
                .limit(limit)
                .offset(offset)
            ).all()
        return tuple(_exclusion_view(fila, stem) for fila, stem in filas), int(total)

    def count_exclusions_by_reason(self) -> dict[str, int]:
        """Cuántas preguntas hay fuera de temario **por cada motivo**, sin traerse las filas.

        Es lo que permite que la sección «No son preguntas» diga cuántos enunciados rotos hay —la
        cifra que va al informe del propietario— sin leer 769 filas para contarlas. Los motivos que
        no tengan ninguna marca no salen: el vocabulario cerrado lo conoce quien pinta la pantalla.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionCurriculumExclusionRecord.reason, func.count()).group_by(
                    QuestionCurriculumExclusionRecord.reason
                )
            ).all()
        return {str(motivo): int(total) for motivo, total in filas}

    def list_topic_proposals(
        self, *, limit: int, offset: int
    ) -> tuple[tuple[QuestionTopicProposalsView, ...], int]:
        """La cola de revisión: **una tarjeta por pregunta**, con todas sus propuestas dentro.

        Es lo que despacha el propietario, y se lee entera de una vez en lugar de pregunta a
        pregunta: una tarjeta sin su enunciado no se puede juzgar, y pedir la pregunta después sería
        una petición por propuesta —justo lo que la pantalla existe para no hacer.

        Cinco decisiones que se ven en el SQL:

        1. **La unidad es la pregunta**, no el mapeo. Una pregunta con dos propuestas distintas
           —pasó en la corrida real, por dos procesos que se pisaron— sale **una sola vez**, con los
           dos candidatos juntos: si saliera dos veces, aceptar una dejaría la otra puesta y la
           misma pregunta volvería a la cola.
        2. **De lo más dudoso a lo menos**: el propietario empieza por donde el modelo dudó más, y
           el identificador de la pregunta desempata para que dos páginas no se pisen. El `total`
           cuenta tarjetas, que es lo que le queda por despachar.
        3. **Lo ya aceptado viaja aparte de lo propuesto.** Si la pregunta tiene un tema decidido,
           ese manda y lo que sobra son propuestas que se retiran; mezclarlos en una lista no
           dejaría distinguir «lo que la máquina propone» de «lo que ya está decidido».
        4. **El motivo sale de la auditoría**, que es donde vive: el mapeo guarda confianza y
           estado, no la frase con la que el modelo se explicó. Se lee el último `question.mapped`
           de cada mapeo, que es el que vale si la propuesta se reescribió.
        5. **Un epígrafe propuesto sin tema propuesto se enseña igual.** Si el epígrafe cuelga de un
           tema que nadie propuso (ni está aceptado), se presenta como candidato de su tema: dejarlo
           fuera mantendría la pregunta en la cola sin nada que decidir, que es la peor forma de
           atascarla.
        """
        con_propuesta = (
            select(CurriculumMappingRecord.subject_id)
            .where(
                CurriculumMappingRecord.subject_type == "question_version",
                CurriculumMappingRecord.status == "provisional",
            )
            .group_by(CurriculumMappingRecord.subject_id)
        )
        with self._session_factory() as session:
            total = session.execute(
                select(func.count()).select_from(con_propuesta.subquery())
            ).scalar_one()
            identificadores = [
                str(fila)
                for fila in session.execute(
                    con_propuesta.order_by(
                        func.min(CurriculumMappingRecord.confidence),
                        CurriculumMappingRecord.subject_id,
                    )
                    .limit(limit)
                    .offset(offset)
                ).scalars()
            ]
            if not identificadores:
                return (), int(total)

            filas = session.execute(
                select(CurriculumMappingRecord, CurriculumNodeRecord)
                .join(
                    CurriculumNodeRecord,
                    CurriculumNodeRecord.id == CurriculumMappingRecord.curriculum_node_id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.subject_id.in_(identificadores),
                )
                .order_by(*curriculum_order(CurriculumNodeRecord.path))
            ).all()
            preguntas = {
                fila.id: fila
                for fila in session.execute(
                    select(QuestionVersionRecord).where(
                        QuestionVersionRecord.id.in_(identificadores)
                    )
                )
                .scalars()
                .all()
            }
            conjuntos = {
                fila.id: str(fila.title)
                for fila in session.execute(
                    select(QuestionSetRecord).where(
                        QuestionSetRecord.id.in_(
                            {str(pregunta.question_set_id) for pregunta in preguntas.values()}
                        )
                    )
                )
                .scalars()
                .all()
            }
            opciones = self._options_by_question(session, identificadores)
            padres = {
                str(fila.id): fila
                for fila in session.execute(
                    select(CurriculumNodeRecord).where(
                        CurriculumNodeRecord.id.in_(
                            {
                                str(nodo.parent_id)
                                for _, nodo in filas
                                if str(nodo.node_type) == "epigraph" and nodo.parent_id is not None
                            }
                        )
                    )
                )
                .scalars()
                .all()
            }
            motivos = self._mapping_reasons(
                session,
                [str(mapeo.id) for mapeo, _ in filas if str(mapeo.status) == "provisional"],
            )

        return (
            tuple(
                self._proposal_card(
                    identificador,
                    filas=[
                        (mapeo, nodo)
                        for mapeo, nodo in filas
                        if str(mapeo.subject_id) == identificador
                    ],
                    pregunta=preguntas.get(identificador),
                    set_title=conjuntos.get(
                        ""
                        if preguntas.get(identificador) is None
                        else str(preguntas[identificador].question_set_id),
                        "",
                    ),
                    options=opciones.get(identificador, ()),
                    parents=padres,
                    reasons=motivos,
                )
                for identificador in identificadores
            ),
            int(total),
        )

    @staticmethod
    def _proposal_card(
        question_version_id: str,
        *,
        filas: Sequence[tuple[CurriculumMappingRecord, CurriculumNodeRecord]],
        pregunta: QuestionVersionRecord | None,
        set_title: str,
        options: Sequence[OptionVersionRecord],
        parents: Mapping[str, CurriculumNodeRecord],
        reasons: Mapping[str, str],
    ) -> QuestionTopicProposalsView:
        """Arma la tarjeta de una pregunta: lo aceptado, los candidatos y sus epígrafes.

        Se separa de la consulta porque aquí está la decisión de qué es un candidato: un mapeo
        `provisional` de tema, o un epígrafe `provisional` cuyo tema no se propuso (ni está
        aceptado). Todo lo demás de la pregunta —lo aceptado, lo rechazado— no es una propuesta.
        """
        aceptados = [
            nodo
            for mapeo, nodo in filas
            if str(mapeo.status) == "accepted" and str(nodo.node_type) == "topic"
        ]
        candidatos = {
            str(nodo.id): (mapeo, nodo)
            for mapeo, nodo in filas
            if str(mapeo.status) == "provisional" and str(nodo.node_type) == "topic"
        }
        epigrafes: dict[str, list[CurriculumNodeRecord]] = {}
        huerfanos: list[tuple[CurriculumMappingRecord, CurriculumNodeRecord]] = []
        for mapeo, nodo in filas:
            if str(mapeo.status) != "provisional" or str(nodo.node_type) != "epigraph":
                continue
            padre = None if nodo.parent_id is None else str(nodo.parent_id)
            if padre is not None and padre in candidatos:
                epigrafes.setdefault(padre, []).append(nodo)
            elif padre is None or all(str(aceptado.id) != padre for aceptado in aceptados):
                huerfanos.append((mapeo, nodo))

        propuestas = [
            TopicProposalView(
                mapping_id=str(mapeo.id),
                topic=_node_ref(nodo),
                epigraphs=tuple(_node_ref(hijo) for hijo in epigrafes.get(clave, ())),
                confidence=float(mapeo.confidence),
                reason=reasons.get(str(mapeo.id)),
                created_at=mapeo.created_at,
            )
            for clave, (mapeo, nodo) in candidatos.items()
        ]
        propuestas.extend(
            propuesta
            for propuesta in (
                _orphan_proposal(mapeo, nodo, parents, reasons) for mapeo, nodo in huerfanos
            )
            if propuesta is not None
        )
        propuestas.sort(key=lambda propuesta: (propuesta.confidence, propuesta.mapping_id))
        return QuestionTopicProposalsView(
            question_version_id=question_version_id,
            question_set_id="" if pregunta is None else str(pregunta.question_set_id),
            set_title=set_title,
            stem="" if pregunta is None else str(pregunta.stem),
            options=tuple(
                OptionView(
                    id=opcion.id,
                    stable_key=str(opcion.stable_key),
                    text=str(opcion.text),
                    position=int(opcion.position),
                    label=opcion.label,
                )
                for opcion in options
            ),
            accepted=None if not aceptados else _node_ref(aceptados[0]),
            proposals=tuple(propuestas),
        )

    @staticmethod
    def _mapping_reasons(session: Session, mapping_ids: Sequence[str]) -> dict[str, str]:
        """El motivo de cada mapeo, leído de su último evento `question.mapped`.

        La auditoría es la que lo guarda (el mapeo no tiene columna de motivo), y se toma el evento
        más nuevo porque es el que describe el estado que se está leyendo.
        """
        if not mapping_ids:
            return {}
        filas = session.execute(
            select(AuditEventRecord.object_id, AuditEventRecord.after_json)
            .where(
                AuditEventRecord.object_id.in_(list(mapping_ids)),
                AuditEventRecord.action == "question.mapped",
            )
            .order_by(AuditEventRecord.created_at)
        ).all()
        motivos: dict[str, str] = {}
        for object_id, despues in filas:
            try:
                datos = json.loads(despues or "{}")
            except ValueError:  # pragma: no cover - la auditoría la escribe esta aplicación
                continue
            motivo = datos.get("reason")
            if isinstance(motivo, str) and motivo.strip():
                motivos[str(object_id)] = motivo
        return motivos

    @staticmethod
    def _mapping_actors(session: Session, mapping_ids: Sequence[str]) -> dict[str, str]:
        """Quién escribió cada mapeo, leído de su último evento `question.mapped`.

        La auditoría es la que lo guarda, y se toma el evento más nuevo porque es el que describe el
        estado que se está leyendo. Un mapeo sin evento no aparece en el diccionario: no se inventa
        un actor para lo que no consta, que es justo lo que hay que poder ver en la lista.
        """
        if not mapping_ids:
            return {}
        filas = session.execute(
            select(AuditEventRecord.object_id, AuditEventRecord.actor)
            .where(
                AuditEventRecord.object_id.in_(list(mapping_ids)),
                AuditEventRecord.action == "question.mapped",
            )
            .order_by(AuditEventRecord.created_at)
        ).all()
        actores: dict[str, str] = {}
        for object_id, actor in filas:
            limpio = str(actor).strip()
            if limpio:
                actores[str(object_id)] = limpio
        return actores

    def reject_other_mappings(
        self,
        question_version_id: str,
        *,
        keep_node_ids: frozenset[str],
        now: datetime,
        actor: str = "local",
        reason: str | None = None,
    ) -> int:
        """Deja la pregunta con **un solo tema**: retira los demás mapeos de tema y epígrafe.

        Retirar es marcar `rejected`, **no** borrar el mapeo, y esa es la decisión importante: una
        pregunta ya decidida que se quedara sin ningún mapeo volvería a entrar en la siguiente
        pasada del clasificador y la cola se llenaría de lo mismo que el propietario ya despachó.
        Con la marca puesta, la propuesta sigue ahí —se puede leer qué se propuso y quién lo
        retiró— y el clasificador no la vuelve a coger.

        Qué se queda, exactamente:

        - los nodos de `keep_node_ids` (el tema elegido y lo que se acabe de escribir);
        - los **epígrafes cuyo tema es el elegido**: un epígrafe no sustituye a su tema, así que
          retirarlo al retirar «el otro tema» sería tirar la clasificación fina que sí vale;
        - y **nada de lo que no sea tema o epígrafe**: un mapeo a un bloque es la catalogación que
          el documento traía (S12.6) y no es un tema, así que no entra en esta limpieza.

        No se toca la fecha de aprobación (un mapeo retirado no está aprobado) ni la confianza: lo
        que cambia es el estado, y el `before` lo dice en la auditoría.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(CurriculumMappingRecord, CurriculumNodeRecord)
                .join(
                    CurriculumNodeRecord,
                    CurriculumNodeRecord.id == CurriculumMappingRecord.curriculum_node_id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.subject_id == question_version_id,
                    CurriculumNodeRecord.node_type.in_(("topic", "epigraph")),
                )
            ).all()
            sobran = [
                mapeo
                for mapeo, nodo in filas
                if str(nodo.id) not in keep_node_ids
                and (
                    str(nodo.node_type) == "topic"
                    or nodo.parent_id is None
                    or str(nodo.parent_id) not in keep_node_ids
                )
            ]
            for mapeo in sobran:
                antes = {"status": str(mapeo.status), "confidence": float(mapeo.confidence)}
                mapeo.status = "rejected"
                self._audit(
                    session,
                    actor=actor,
                    action="question.proposal_retired",
                    object_type="curriculum_mapping",
                    object_id=str(mapeo.id),
                    before=antes,
                    after={
                        "node_id": str(mapeo.curriculum_node_id),
                        "question_version_id": question_version_id,
                        "status": "rejected",
                        **_reason(reason),
                    },
                    now=now,
                )
            if sobran:
                session.commit()
            return len(sobran)

    def list_topic_conflicts(
        self, *, limit: int, offset: int
    ) -> tuple[tuple[QuestionTopicConflictView, ...], int]:
        """Las preguntas que cuentan en **dos o más temas aceptados**, con quién decidió cada uno.

        Es la lectura de lo que quedó torcido antes de esta tanda: la catalogación heredada del
        documento, las migraciones y las dos corridas del clasificador que se pisaron. Una pregunta
        en dos temas cuenta en los dos en todos los agregados, así que esto no es una curiosidad: es
        un recuento que miente hasta que alguien lo arregla —y lo arregla el propietario, eligiendo
        cuál se queda; la aplicación no lo decide por su cuenta.
        """
        con_conflicto = (
            select(CurriculumMappingRecord.subject_id)
            .join(
                CurriculumNodeRecord,
                CurriculumNodeRecord.id == CurriculumMappingRecord.curriculum_node_id,
            )
            .where(
                CurriculumMappingRecord.subject_type == "question_version",
                CurriculumMappingRecord.status == "accepted",
                CurriculumNodeRecord.node_type == "topic",
            )
            .group_by(CurriculumMappingRecord.subject_id)
            .having(func.count() > 1)
        )
        with self._session_factory() as session:
            total = session.execute(
                select(func.count()).select_from(con_conflicto.subquery())
            ).scalar_one()
            identificadores = [
                str(fila)
                for fila in session.execute(
                    con_conflicto.order_by(CurriculumMappingRecord.subject_id)
                    .limit(limit)
                    .offset(offset)
                ).scalars()
            ]
            if not identificadores:
                return (), int(total)

            filas = session.execute(
                select(CurriculumMappingRecord, CurriculumNodeRecord)
                .join(
                    CurriculumNodeRecord,
                    CurriculumNodeRecord.id == CurriculumMappingRecord.curriculum_node_id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    CurriculumNodeRecord.node_type == "topic",
                    CurriculumMappingRecord.subject_id.in_(identificadores),
                )
                .order_by(*curriculum_order(CurriculumNodeRecord.path))
            ).all()
            preguntas = {
                fila.id: fila
                for fila in session.execute(
                    select(QuestionVersionRecord).where(
                        QuestionVersionRecord.id.in_(identificadores)
                    )
                )
                .scalars()
                .all()
            }
            conjuntos = {
                fila.id: str(fila.title)
                for fila in session.execute(
                    select(QuestionSetRecord).where(
                        QuestionSetRecord.id.in_(
                            {str(pregunta.question_set_id) for pregunta in preguntas.values()}
                        )
                    )
                )
                .scalars()
                .all()
            }
            opciones = self._options_by_question(session, identificadores)
            actores = self._mapping_actors(session, [str(mapeo.id) for mapeo, _ in filas])

        return (
            tuple(
                QuestionTopicConflictView(
                    question_version_id=identificador,
                    question_set_id=(
                        ""
                        if identificador not in preguntas
                        else str(preguntas[identificador].question_set_id)
                    ),
                    set_title=conjuntos.get(
                        ""
                        if identificador not in preguntas
                        else str(preguntas[identificador].question_set_id),
                        "",
                    ),
                    stem=""
                    if identificador not in preguntas
                    else str(preguntas[identificador].stem),
                    options=tuple(
                        OptionView(
                            id=opcion.id,
                            stable_key=str(opcion.stable_key),
                            text=str(opcion.text),
                            position=int(opcion.position),
                            label=opcion.label,
                        )
                        for opcion in opciones.get(identificador, ())
                    ),
                    topics=tuple(
                        ConflictingTopicView(
                            mapping_id=str(mapeo.id),
                            topic=_node_ref(nodo),
                            confidence=float(mapeo.confidence),
                            actor=actores.get(str(mapeo.id)),
                            created_at=mapeo.created_at,
                        )
                        for mapeo, nodo in filas
                        if str(mapeo.subject_id) == identificador
                    ),
                )
                for identificador in identificadores
            ),
            int(total),
        )

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

    def link_evidence(
        self,
        question_version_id: str,
        *,
        evidence_span_id: str,
        role: str,
        status: str = "accepted",
        claim: str | None = None,
        now: datetime,
        actor: str = "local",
    ) -> bool:
        """Enlaza una pregunta con el fragmento del que salió (DEBT-010).

        Es **idempotente**: la clave primaria de `question_evidence` es (pregunta, fragmento,
        papel), así que volver a importar el mismo documento no duplica la cita ni la cuenta.
        Devuelve si el enlace es nuevo, para que el informe pueda decir cuántas citas ha creado.

        El papel por defecto es `stem` y el estado `accepted`: la cita de una pregunta importada de
        un documento **no es una propuesta**, es de dónde se leyó el enunciado.
        """
        with self._session_factory() as session:
            existente = session.get(
                QuestionEvidenceRecord, (question_version_id, evidence_span_id, role)
            )
            if existente is not None:
                return False
            if session.get(QuestionVersionRecord, question_version_id) is None:
                return False
            if session.get(EvidenceSpanRecord, evidence_span_id) is None:
                return False
            session.add(
                QuestionEvidenceRecord(
                    question_version_id=question_version_id,
                    evidence_span_id=evidence_span_id,
                    role=role,
                    claim=claim,
                    status=status,
                    created_at=now,
                )
            )
            self._audit(
                session,
                actor=actor,
                action="question.evidence_linked",
                object_type="question_version",
                object_id=question_version_id,
                before={},
                after={"evidence_span_id": evidence_span_id, "role": role, "status": status},
                now=now,
            )
            session.commit()
            return True

    def question_ids_of_node(self, node_id: str) -> tuple[str, ...]:
        """Las preguntas catalogadas en este tema, en orden estable.

        Es la misma regla que la cifra «preguntas: N» del Programa: mapeo **aceptado** de la
        pregunta
        al nodo, sin contar las versiones sustituidas. Si aquí contara otra cosa, practicar un tema
        traería preguntas distintas de las que la pantalla dice que tiene.

        **El tema es el exacto**, no su subárbol: la cifra del Programa se cuenta así, y practicar
        un
        bloque que no tiene preguntas propias no puede inventarse las de sus temas.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    QuestionVersionRecord.id,
                    QuestionSetRecord.title,
                    QuestionVersionRecord.position,
                    QuestionVersionRecord.stable_key,
                )
                .join(
                    CurriculumMappingRecord,
                    CurriculumMappingRecord.subject_id == QuestionVersionRecord.id,
                )
                .join(
                    QuestionSetRecord,
                    QuestionSetRecord.id == QuestionVersionRecord.question_set_id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    CurriculumMappingRecord.curriculum_node_id == node_id,
                    _NO_SUSTITUIDAS,
                )
                .order_by(
                    QuestionSetRecord.title,
                    QuestionVersionRecord.position,
                    QuestionVersionRecord.stable_key,
                    QuestionVersionRecord.id,
                )
            ).all()
        ordenadas: dict[str, None] = {}
        for pregunta_id, _titulo, _posicion, _clave in filas:
            ordenadas.setdefault(str(pregunta_id), None)
        return tuple(ordenadas)

    def question_ids_of_nodes(self, node_ids: Sequence[str]) -> dict[str, tuple[str, ...]]:
        """Las preguntas de **cada** uno de esos nodos, en **una** consulta y en su orden estable.

        Es la versión por lotes de `question_ids_of_node`, y existe porque una composición pide las
        preguntas de un bloque entero —una treintena de temas— y una consulta por tema era otro de
        los N+1 del montaje de un simulacro. El orden dentro de cada nodo es el mismo que el de la
        consulta suelta: por título del conjunto, posición, clave estable e identificador. Un nodo
        sin preguntas sale con la tupla vacía, no se omite: quien lo pide necesita saber que no hay.
        """
        if not node_ids:
            return {}
        unicos = tuple(dict.fromkeys(node_ids))
        ordenadas: dict[str, dict[str, None]] = {node_id: {} for node_id in unicos}
        with self._session_factory() as session:
            for inicio in range(0, len(unicos), _TANDA_DE_CONSULTA):
                tanda = unicos[inicio : inicio + _TANDA_DE_CONSULTA]
                filas = session.execute(
                    select(
                        CurriculumMappingRecord.curriculum_node_id,
                        QuestionVersionRecord.id,
                        QuestionSetRecord.title,
                        QuestionVersionRecord.position,
                        QuestionVersionRecord.stable_key,
                    )
                    .join(
                        CurriculumMappingRecord,
                        CurriculumMappingRecord.subject_id == QuestionVersionRecord.id,
                    )
                    .join(
                        QuestionSetRecord,
                        QuestionSetRecord.id == QuestionVersionRecord.question_set_id,
                    )
                    .where(
                        CurriculumMappingRecord.subject_type == "question_version",
                        CurriculumMappingRecord.status == "accepted",
                        CurriculumMappingRecord.curriculum_node_id.in_(list(tanda)),
                        _NO_SUSTITUIDAS,
                    )
                    .order_by(
                        CurriculumMappingRecord.curriculum_node_id,
                        QuestionSetRecord.title,
                        QuestionVersionRecord.position,
                        QuestionVersionRecord.stable_key,
                        QuestionVersionRecord.id,
                    )
                ).all()
                for nodo_id, pregunta_id, _titulo, _posicion, _clave in filas:
                    ordenadas[str(nodo_id)].setdefault(str(pregunta_id), None)
        return {node_id: tuple(ordenadas[node_id]) for node_id in unicos}

    def questions_without_topic(self, set_id: str, *, limit: int = 500) -> tuple[str, ...]:
        """Preguntas del conjunto que **no** están catalogadas en ningún nodo del programa.

        Lo usa la catalogación automática (S12.6): solo se catalogan las que no tienen tema, porque
        pisar un tema que ya estaba —puesto a mano o traído de una columna del material— sería
        cambiar una decisión sin decirlo. Una sola consulta, con la ausencia comprobada en la base y
        no pregunta a pregunta.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionVersionRecord.id)
                .where(
                    QuestionVersionRecord.question_set_id == set_id,
                    _NO_SUSTITUIDAS,
                    ~session.query(CurriculumMappingRecord.id)
                    .filter(
                        CurriculumMappingRecord.subject_type == "question_version",
                        CurriculumMappingRecord.subject_id == QuestionVersionRecord.id,
                        CurriculumMappingRecord.status == "accepted",
                    )
                    .exists(),
                )
                .order_by(
                    QuestionVersionRecord.position,
                    QuestionVersionRecord.stable_key,
                    QuestionVersionRecord.id,
                )
                .limit(limit)
            ).scalars()
            return tuple(str(fila) for fila in filas)

    def node_titles_of_set(self, set_id: str) -> dict[str, tuple[tuple[str, str], ...]]:
        """Los temas (nodos del programa) de cada pregunta del conjunto, por orden de nodo.

        Lo usa el diagnóstico para estratificar la muestra (DEBT-012). Solo cuenta lo **aceptado**:
        una
        propuesta de mapeo sin revisar no es un tema de la pregunta, y usarla metería en el
        diagnóstico
        una clasificación que nadie ha confirmado.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    CurriculumMappingRecord.subject_id,
                    CurriculumNodeRecord.id,
                    CurriculumNodeRecord.title,
                    CurriculumNodeRecord.position,
                    CurriculumNodeRecord.path,
                )
                .join(
                    CurriculumNodeRecord,
                    CurriculumNodeRecord.id == CurriculumMappingRecord.curriculum_node_id,
                )
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == CurriculumMappingRecord.subject_id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    QuestionVersionRecord.question_set_id == set_id,
                    _NO_SUSTITUIDAS,
                )
                .order_by(
                    CurriculumMappingRecord.subject_id,
                    CurriculumNodeRecord.path,
                    CurriculumNodeRecord.id,
                )
            ).all()
        acumulado: dict[str, list[tuple[str, str]]] = {}
        for pregunta_id, node_id, titulo, _posicion, _ruta in filas:
            acumulado.setdefault(str(pregunta_id), []).append((str(node_id), str(titulo)))
        return {pregunta: tuple(temas) for pregunta, temas in acumulado.items()}

    def node_titles_of_questions(
        self, question_ids: Sequence[str]
    ) -> dict[str, tuple[tuple[str, str], ...]]:
        """Los temas de unas preguntas concretas, por orden de nodo.

        Es la lectura que necesita el diagnóstico para agrupar lo contestado por tema: la sesión
        guarda
        qué preguntas se presentaron, no de qué tema eran, y el tema vive en el mapeo de la
        pregunta.
        """
        if not question_ids:
            return {}
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    CurriculumMappingRecord.subject_id,
                    CurriculumNodeRecord.id,
                    CurriculumNodeRecord.title,
                )
                .join(
                    CurriculumNodeRecord,
                    CurriculumNodeRecord.id == CurriculumMappingRecord.curriculum_node_id,
                )
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    CurriculumMappingRecord.subject_id.in_(list(question_ids)),
                )
                .order_by(
                    CurriculumMappingRecord.subject_id,
                    CurriculumNodeRecord.path,
                    CurriculumNodeRecord.id,
                )
            ).all()
        acumulado: dict[str, list[tuple[str, str]]] = {}
        for pregunta_id, node_id, titulo in filas:
            acumulado.setdefault(str(pregunta_id), []).append((str(node_id), str(titulo)))
        return {pregunta: tuple(temas) for pregunta, temas in acumulado.items()}

    # ------------------------------------------------------------------ auxiliares

    @staticmethod
    def _identidades(session: Session, set_id: str) -> dict[str, str]:
        """Identidad (huella) de cada pregunta del conjunto, con su identificador.

        Aquí **sí** entran las versiones sustituidas, a diferencia del resto de consultas del banco
        (DEBT-025): esta es la comprobación de «esa pregunta ya estaba» al importar, y si la versión
        vieja no contara, volver a importar el texto original crearía una pregunta nueva con el
        enunciado equivocado que alguien ya había corregido.
        """
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
        # Con las sustituidas dentro: la clave estable de una pregunta corregida sigue siendo la
        # misma, y si no contara, una reimportación le daría una clave nueva y la duplicaría.
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
        """Identificadores de las preguntas del conjunto, sin las sustituidas (DEBT-025)."""
        return [
            str(fila)
            for fila in session.execute(
                select(QuestionVersionRecord.id).where(
                    QuestionVersionRecord.question_set_id == set_id,
                    _NO_SUSTITUIDAS,
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
        # Los recuentos del conjunto no cuentan las versiones sustituidas (DEBT-025): corregir una
        # pregunta no puede hacer que el conjunto tenga una pregunta más de las que tiene.
        preguntas = int(
            session.execute(
                select(func.count())
                .select_from(QuestionVersionRecord)
                .where(
                    QuestionVersionRecord.question_set_id == fila.id,
                    _NO_SUSTITUIDAS,
                )
            ).scalar_one()
        )
        reservas = int(
            session.execute(
                select(func.count())
                .select_from(QuestionVersionRecord)
                .where(
                    QuestionVersionRecord.question_set_id == fila.id,
                    QuestionVersionRecord.is_reserve.is_(True),
                    _NO_SUSTITUIDAS,
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
        return self._set_view_con_recuentos(
            fila,
            preguntas=preguntas,
            reservas=reservas,
            incompletas=incompletas,
            claves=tuple(claves),
        )

    @staticmethod
    def _set_view_con_recuentos(
        fila: QuestionSetRecord,
        *,
        preguntas: int,
        reservas: int,
        incompletas: int,
        claves: tuple[AnswerKeyVersionRecord, ...],
    ) -> QuestionSetView:
        """La vista del conjunto a partir de lo que ya se contó, sin volver a preguntar.

        `_set_view` cuenta y luego llama aquí; `sets_by_ids` cuenta todo el lote de una vez y llama
        aquí con los mismos números. Es **una** definición de qué se enseña de un conjunto, para que
        el lote y la consulta suelta no puedan decir cosas distintas.
        """
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
            distribution=str(fila.distribution),
            origin_scope=str(fila.origin_scope),
            key_reliability=str(fila.key_reliability),
            key_checked_count=int(fila.key_checked_count),
            key_discrepant_count=int(fila.key_discrepant_count),
        )

    def _question_view(
        self,
        session: Session,
        fila: QuestionVersionRecord,
        claves: Mapping[str, Mapping[str, AnswerKeyEntry]],
        *,
        include_key: bool,
    ) -> QuestionView:
        return self._question_view_con_datos(
            fila,
            claves=claves,
            opciones=self._options_by_question(session, [fila.id]).get(fila.id, ()),
            explicaciones=self._explanations_count(session, [fila.id]).get(fila.id, 0),
            include_key=include_key,
        )

    @staticmethod
    def _question_view_con_datos(
        fila: QuestionVersionRecord,
        *,
        claves: Mapping[str, Mapping[str, AnswerKeyEntry]],
        opciones: Sequence[OptionVersionRecord],
        explicaciones: int,
        include_key: bool,
    ) -> QuestionView:
        """La vista de la pregunta a partir de lo que ya se leyó, sin volver a preguntar.

        `_question_view` lee lo suyo y llama aquí; `questions_by_ids` lee todo el lote de una vez y
        llama aquí con los mismos datos. Es **una** definición de qué se enseña de una pregunta,
        para que el lote y la consulta suelta no puedan decir cosas distintas.
        """
        entrada = claves.get(fila.question_set_id, {}).get(fila.id)
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
        return self._key_view_con_entradas(fila, entradas)

    def active_key_entries_by_set(
        self, set_ids: Sequence[str]
    ) -> dict[str, tuple[str, dict[str, KeyEntryView]]]:
        """La plantilla **activa** de cada conjunto, con su desenlace por pregunta.

        Es lo que necesita la composición, y **solo eso**: la plantilla que corrige (su
        identificador) y, por pregunta, qué letra manda. Se leen únicamente las plantillas activas
        —no las 584 versiones que hay en el banco—, que es lo que hacía que esta lectura costara
        1,7 s y se solapara con la de las preguntas. Cuando un conjunto tiene más de una activa,
        manda la de número de versión más bajo, igual que `list_keys` + `next(… "active")`.
        """
        if not set_ids:
            return {}
        unicos = tuple(dict.fromkeys(set_ids))
        with self._session_factory() as session:
            activas: dict[str, AnswerKeyVersionRecord] = {}
            for inicio in range(0, len(unicos), _TANDA_DE_CONSULTA):
                tanda = unicos[inicio : inicio + _TANDA_DE_CONSULTA]
                for fila in (
                    session.execute(
                        select(AnswerKeyVersionRecord)
                        .where(
                            AnswerKeyVersionRecord.question_set_id.in_(list(tanda)),
                            AnswerKeyVersionRecord.status == "active",
                        )
                        .order_by(
                            AnswerKeyVersionRecord.question_set_id,
                            AnswerKeyVersionRecord.version_no,
                        )
                    )
                    .scalars()
                    .all()
                ):
                    activas.setdefault(fila.question_set_id, fila)
            if not activas:
                return {}
            por_clave: dict[str, list[AnswerKeyEntryRecord]] = {}
            identificadores = list(activas.values())
            for inicio in range(0, len(identificadores), _TANDA_DE_CONSULTA):
                tanda_actual = [
                    str(clave.id) for clave in identificadores[inicio : inicio + _TANDA_DE_CONSULTA]
                ]
                for entrada in (
                    session.execute(
                        select(AnswerKeyEntryRecord)
                        .where(AnswerKeyEntryRecord.answer_key_version_id.in_(tanda_actual))
                        .order_by(AnswerKeyEntryRecord.question_version_id)
                    )
                    .scalars()
                    .all()
                ):
                    por_clave.setdefault(entrada.answer_key_version_id, []).append(entrada)
            salida: dict[str, tuple[str, dict[str, KeyEntryView]]] = {}
            for set_id, clave in activas.items():
                salida[set_id] = (
                    clave.id,
                    {
                        entrada.question_version_id: KeyEntryView(
                            question_version_id=entrada.question_version_id,
                            outcome=str(entrada.outcome),
                            correct_option_keys=tuple(
                                str(letra)
                                for letra in json.loads(entrada.correct_option_keys_json or "[]")
                            ),
                            notes=entrada.notes,
                        )
                        for entrada in por_clave.get(clave.id, [])
                    },
                )
            return salida

    def keys_by_set_ids(self, set_ids: Sequence[str]) -> dict[str, tuple[AnswerKeyView, ...]]:
        """Las plantillas de esos conjuntos, todas y en **dos** consultas.

        Es la versión por lotes de `list_keys`, y existe por el mismo motivo que las demás: quien
        compone un simulacro pide la clave activa de cada conjunto que toca, y una consulta por
        conjunto (más una por plantilla para sus entradas) es otra vez el N+1. El orden dentro de
        cada conjunto es el de `list_keys` —por número de versión—, para que «la activa» sea la
        misma en los dos caminos.
        """
        if not set_ids:
            return {}
        unicos = tuple(dict.fromkeys(set_ids))
        with self._session_factory() as session:
            filas: list[AnswerKeyVersionRecord] = []
            for inicio in range(0, len(unicos), _TANDA_DE_CONSULTA):
                tanda = unicos[inicio : inicio + _TANDA_DE_CONSULTA]
                filas.extend(
                    session.execute(
                        select(AnswerKeyVersionRecord)
                        .where(AnswerKeyVersionRecord.question_set_id.in_(list(tanda)))
                        .order_by(AnswerKeyVersionRecord.version_no)
                    )
                    .scalars()
                    .all()
                )
            if not filas:
                return {}
            entradas: dict[str, list[AnswerKeyEntryRecord]] = {}
            identificadores = [str(fila.id) for fila in filas]
            for inicio in range(0, len(identificadores), _TANDA_DE_CONSULTA):
                tanda_actual = identificadores[inicio : inicio + _TANDA_DE_CONSULTA]
                for entrada in (
                    session.execute(
                        select(AnswerKeyEntryRecord)
                        .where(AnswerKeyEntryRecord.answer_key_version_id.in_(tanda_actual))
                        .order_by(AnswerKeyEntryRecord.question_version_id)
                    )
                    .scalars()
                    .all()
                ):
                    entradas.setdefault(entrada.answer_key_version_id, []).append(entrada)
            agrupadas: dict[str, list[AnswerKeyView]] = {}
            for fila in filas:
                agrupadas.setdefault(fila.question_set_id, []).append(
                    self._key_view_con_entradas(fila, entradas.get(fila.id, []))
                )
            return {set_id: tuple(claves) for set_id, claves in agrupadas.items()}

    @staticmethod
    def _key_view_con_entradas(
        fila: AnswerKeyVersionRecord, entradas: Sequence[AnswerKeyEntryRecord]
    ) -> AnswerKeyView:
        """La vista de la plantilla a partir de sus entradas ya leídas."""
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
