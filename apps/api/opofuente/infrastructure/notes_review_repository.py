"""La revisión de los apuntes: se lee lo que ya está guardado y se decide con su evento (F24).

Tres cosas y las tres con una regla detrás:

1. **la tabla que pide el panel se lee con agregados** (`GROUP BY` por tema) y no tema a tema: son
   33 filas y cinco consultas fijas, en lugar de cinco consultas por cada una de las 33. Lo único
   caro —la **cobertura medida**— no se lee aquí: la mide el servicio con el mismo camino que
   `apuntes --medir`, solo de los temas que esperan una decisión, y no se recalcula nada a mano;
2. **la decisión es una escritura auditada**: la fila de la revisión y su evento entran en la
   **misma transacción**, con el antes y el después. Una decisión sin evento no se podría revisar
   después, y una segunda revisión del mismo tema **actualiza** su fila —no apila otra— porque la
   pregunta que contesta la tabla es «qué he decidido de este tema»;
3. **lo que se lee es de hoy**: los apartados, las comprobaciones guardadas y la bandeja son los del
   motor, tal como están. La decisión es del propietario y **sobrevive a una corrida** que vuelva a
   medir el tema: el motor no escribe en esta tabla.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.notes_review import ReviewDecision, TopicReview
from opofuente.domain.topic_notes import CategoriaIncidencia
from opofuente.infrastructure.db_models import (
    AuditEventRecord,
    CurriculumNodeRecord,
    DossierSnapshotRecord,
    NotesIncidentRecord,
    QuestionNoteAnchorRecord,
    TopicFactRecord,
    TopicNoteSectionRecord,
    TopicNotesReviewRecord,
)

#: La acción del evento, con el mismo vocabulario `objeto.verbo` que el resto del panel.
ACCION_REVISION = "notes.topic_reviewed"

#: El objeto de la auditoría es **el tema**: lo que se decide es «los apuntes de este tema».
OBJETO_TEMA = "topic_notes"


@dataclass(frozen=True, slots=True)
class ComprobacionesDelTema:
    """Las comprobaciones guardadas de un tema, **contadas en la base**.

    Son las que dejó el motor al comprobar: una fila por pregunta y tema. `total` es cuántas hay, y
    de ahí sale la frase «se han comprobado N preguntas». No son la puerta de cobertura —esa se mide
    aparte, porque su denominador excluye las respuestas correctas que no se pueden usar— y por eso
    van con su propio nombre.
    """

    total: int = 0
    covered: int = 0
    gaps: int = 0
    doubtful: int = 0
    conflicts: int = 0


@dataclass(frozen=True, slots=True)
class ResumenDeTema:
    """Una fila de la tabla del panel: el tema, su estado, sus cifras y lo que se decidió.

    `block_code` y `block_title` van resueltos porque la tabla los enseña agrupados y resolverlos en
    el navegador obligaría a traerse el árbol del programa entero para pintar una columna.
    """

    node_id: str
    code: str
    title: str
    block_code: str
    block_title: str
    sections_written: int
    facts: int
    checks: ComprobacionesDelTema
    incidents_open: int
    incidents_by_category: Mapping[CategoriaIncidencia, int]
    version_id: str | None
    version_built_at: datetime | None
    review: TopicReview | None

    @property
    def published(self) -> bool:
        """Publicado es «tiene versión archivada»: la regla de siempre (`NotesState`)."""
        return self.version_id is not None

    @property
    def has_notes(self) -> bool:
        return self.sections_written > 0


@dataclass(frozen=True, slots=True)
class ContadoresDeRevision:
    """Los números de la cabecera y del menú: cuánto espera una decisión y cuánto no.

    `pending_decision` es el número del contador del panel y cuenta lo que de verdad espera al
    propietario: los temas **con apuntes escritos, sin publicar y sin una decisión que los
    apruebe**. Un tema aprobado que no se ha podido publicar (porque la puerta no pasa) no vuelve a
    la lista de pendientes: ya lo miró y ya dijo lo que pensaba.
    """

    topics_total: int = 0
    with_notes: int = 0
    published: int = 0
    draft: int = 0
    without_notes: int = 0
    approved: int = 0
    rejected: int = 0
    pending_decision: int = 0


@dataclass(slots=True)
class _Acumulado:
    """Lo que se va reuniendo por tema antes de armar el resumen."""

    sections: int = 0
    facts: int = 0
    checks: ComprobacionesDelTema = field(default_factory=ComprobacionesDelTema)
    incidents_open: int = 0
    incidents_by_category: dict[CategoriaIncidencia, int] = field(default_factory=dict)


class SqlAlchemyNotesReviewRepository:
    """Lee la tabla de la revisión y escribe la decisión del propietario, auditada."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ lectura

    def node_id(self, code: str) -> str | None:
        """El nodo del tema por su código legible (`I.4`), aceptando también `I-4`."""
        limpio = code.replace("-", ".").strip()
        with self._session_factory() as session:
            return session.execute(
                select(CurriculumNodeRecord.id).where(
                    CurriculumNodeRecord.node_type == "topic",
                    CurriculumNodeRecord.path == limpio,
                )
            ).scalar_one_or_none()

    def topics(
        self, convocation_id: str, *, solo_nodo: str | None = None
    ) -> tuple[ResumenDeTema, ...]:
        """Los temas del programa de esa convocatoria, en orden, con sus cifras y su decisión.

        `solo_nodo` limita la lectura a un tema: la ficha y la decisión lo piden así en vez de
        traerse las 33 filas para quedarse con una.
        """
        with self._session_factory() as session:
            bloques = {
                str(fila.id): (str(fila.path), str(fila.title))
                for fila in session.execute(
                    select(
                        CurriculumNodeRecord.id,
                        CurriculumNodeRecord.path,
                        CurriculumNodeRecord.title,
                    ).where(CurriculumNodeRecord.node_type == "block")
                ).all()
            }
            condiciones = [
                CurriculumNodeRecord.node_type == "topic",
                CurriculumNodeRecord.convocation_version_id == convocation_id,
            ]
            if solo_nodo is not None:
                condiciones.append(CurriculumNodeRecord.id == solo_nodo)
            nodos = session.execute(
                select(
                    CurriculumNodeRecord.id,
                    CurriculumNodeRecord.path,
                    CurriculumNodeRecord.title,
                    CurriculumNodeRecord.parent_id,
                )
                .where(*condiciones)
                .order_by(CurriculumNodeRecord.position, CurriculumNodeRecord.path)
            ).all()
            ids = [str(fila[0]) for fila in nodos]
            acumulado: dict[str, _Acumulado] = {clave: _Acumulado() for clave in ids}
            self._contar_apartados(session, ids, acumulado)
            self._contar_hechos(session, ids, acumulado)
            self._contar_comprobaciones(session, ids, acumulado)
            self._contar_incidencias(session, ids, acumulado)
            versiones = self._ultimas_versiones(session, ids)
            revisiones = self._revisiones(session, ids)
        return tuple(
            self._resumen(
                node_id=str(identificador),
                code=str(path),
                title=str(title),
                parent_id=None if parent_id is None else str(parent_id),
                bloques=bloques,
                acumulado=acumulado[str(identificador)],
                versiones=versiones,
                revisiones=revisiones,
            )
            for identificador, path, title, parent_id in nodos
        )

    def counters(self, convocation_id: str) -> ContadoresDeRevision:
        """Los contadores del menú, contados sobre la misma lectura que la tabla.

        No mide la cobertura de nada: es el número que aparece en el menú de **cualquier** pantalla
        del panel, y una cifra que se pide en todas partes no puede costar lo que cuesta medir
        cuatro temas. Lo que espera una decisión se ve en el estado y en la revisión, y eso ya está
        leído.
        """
        return contadores(self.topics(convocation_id))

    def review(self, node_id: str) -> TopicReview | None:
        """La decisión guardada de un tema, o `None` si nadie lo ha revisado."""
        with self._session_factory() as session:
            fila = session.execute(
                select(TopicNotesReviewRecord).where(
                    TopicNotesReviewRecord.curriculum_node_id == node_id
                )
            ).scalar_one_or_none()
        return None if fila is None else _revision(fila)

    # ------------------------------------------------------------------ la decisión

    def save_decision(
        self,
        *,
        node_id: str,
        decision: ReviewDecision,
        note: str | None,
        actor: str,
        now: datetime,
    ) -> TopicReview:
        """Guarda la decisión con su evento, en **una sola transacción**.

        La segunda revisión del mismo tema actualiza su fila: la tabla contesta «qué he decidido de
        este tema», y dos filas para la misma pregunta dejarían dos verdades y ninguna buena. El
        evento guarda el **antes** y el **después** —decisión y si había nota— y no copia el texto
        de la nota: es texto de una persona, como el motivo del alumno.
        """
        with self._session_factory() as session:
            fila = session.execute(
                select(TopicNotesReviewRecord).where(
                    TopicNotesReviewRecord.curriculum_node_id == node_id
                )
            ).scalar_one_or_none()
            antes = {
                "node_id": node_id,
                "decision": None if fila is None else str(fila.decision),
                "has_note": fila is not None and fila.note is not None,
            }
            if fila is None:
                session.add(
                    TopicNotesReviewRecord(
                        id=str(uuid4()),
                        curriculum_node_id=node_id,
                        decision=decision.value,
                        note=note,
                        actor=actor,
                        reviewed_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                )
            else:
                fila.decision = decision.value
                fila.note = note
                fila.actor = actor
                fila.reviewed_at = now
                fila.updated_at = now
            despues = {
                "node_id": node_id,
                "decision": decision.value,
                "has_note": note is not None,
            }
            session.add(
                AuditEventRecord(
                    id=str(uuid4()),
                    actor=actor,
                    action=ACCION_REVISION,
                    object_type=OBJETO_TEMA,
                    object_id=node_id,
                    before_json=json.dumps(antes, ensure_ascii=False, sort_keys=True),
                    after_json=json.dumps(despues, ensure_ascii=False, sort_keys=True),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()
        return TopicReview(
            node_id=node_id,
            decision=decision,
            note=note,
            actor=actor,
            reviewed_at=now,
        )

    # ------------------------------------------------------------------ agregados

    def _contar_apartados(
        self, session: Session, ids: list[str], acumulado: dict[str, _Acumulado]
    ) -> None:
        """Apartados **con texto** por tema: un apartado sin escribir no es un apunte."""
        filas = session.execute(
            select(TopicNoteSectionRecord.curriculum_node_id, func.count())
            .where(
                TopicNoteSectionRecord.curriculum_node_id.in_(ids),
                func.length(func.trim(TopicNoteSectionRecord.body_markdown)) > 0,
            )
            .group_by(TopicNoteSectionRecord.curriculum_node_id)
        ).all()
        for node_id, cuantos in filas:
            acumulado[str(node_id)].sections = int(cuantos)

    def _contar_hechos(
        self, session: Session, ids: list[str], acumulado: dict[str, _Acumulado]
    ) -> None:
        filas = session.execute(
            select(TopicFactRecord.curriculum_node_id, func.count())
            .where(TopicFactRecord.curriculum_node_id.in_(ids))
            .group_by(TopicFactRecord.curriculum_node_id)
        ).all()
        for node_id, cuantos in filas:
            acumulado[str(node_id)].facts = int(cuantos)

    def _contar_comprobaciones(
        self, session: Session, ids: list[str], acumulado: dict[str, _Acumulado]
    ) -> None:
        """Las comprobaciones guardadas, por tema y desenlace."""
        filas = session.execute(
            select(
                QuestionNoteAnchorRecord.curriculum_node_id,
                QuestionNoteAnchorRecord.result,
                func.count(),
            )
            .where(QuestionNoteAnchorRecord.curriculum_node_id.in_(ids))
            .group_by(QuestionNoteAnchorRecord.curriculum_node_id, QuestionNoteAnchorRecord.result)
        ).all()
        for node_id, resultado, cuantos in filas:
            tema = acumulado[str(node_id)]
            tema.checks = _con_desenlace(tema.checks, str(resultado), int(cuantos))

    def _contar_incidencias(
        self, session: Session, ids: list[str], acumulado: dict[str, _Acumulado]
    ) -> None:
        """Lo que la bandeja del motor tiene **sin despachar** de cada tema."""
        filas = session.execute(
            select(
                NotesIncidentRecord.curriculum_node_id,
                NotesIncidentRecord.category,
                func.count(),
            )
            .where(
                NotesIncidentRecord.curriculum_node_id.in_(ids),
                NotesIncidentRecord.status == "open",
            )
            .group_by(NotesIncidentRecord.curriculum_node_id, NotesIncidentRecord.category)
        ).all()
        for node_id, categoria, cuantos in filas:
            tema = acumulado[str(node_id)]
            tema.incidents_open += int(cuantos)
            tema.incidents_by_category[CategoriaIncidencia(str(categoria))] = int(cuantos)

    def _ultimas_versiones(
        self, session: Session, ids: list[str]
    ) -> dict[str, tuple[str, datetime]]:
        """La última versión archivada de cada tema: es lo que lo hace «publicado»."""
        filas = session.execute(
            select(
                DossierSnapshotRecord.curriculum_node_id,
                DossierSnapshotRecord.id,
                DossierSnapshotRecord.built_at,
            ).where(DossierSnapshotRecord.curriculum_node_id.in_(ids))
        ).all()
        ultimas: dict[str, tuple[str, datetime]] = {}
        for node_id, version_id, built_at in filas:
            clave = str(node_id)
            momento = built_at if isinstance(built_at, datetime) else datetime.min
            actual = ultimas.get(clave)
            if actual is None or momento > actual[1]:
                ultimas[clave] = (str(version_id), momento)
        return ultimas

    def _revisiones(self, session: Session, ids: list[str]) -> dict[str, TopicReview]:
        filas = (
            session.execute(
                select(TopicNotesReviewRecord).where(
                    TopicNotesReviewRecord.curriculum_node_id.in_(ids)
                )
            )
            .scalars()
            .all()
        )
        return {str(fila.curriculum_node_id): _revision(fila) for fila in filas}

    @staticmethod
    def _resumen(
        *,
        node_id: str,
        code: str,
        title: str,
        parent_id: str | None,
        bloques: Mapping[str, tuple[str, str]],
        acumulado: _Acumulado,
        versiones: Mapping[str, tuple[str, datetime]],
        revisiones: Mapping[str, TopicReview],
    ) -> ResumenDeTema:
        version = versiones.get(node_id)
        bloque = None if parent_id is None else bloques.get(parent_id)
        return ResumenDeTema(
            node_id=node_id,
            code=code,
            title=title,
            block_code="" if bloque is None else bloque[0],
            block_title="" if bloque is None else bloque[1],
            sections_written=acumulado.sections,
            facts=acumulado.facts,
            checks=acumulado.checks,
            incidents_open=acumulado.incidents_open,
            incidents_by_category=dict(acumulado.incidents_by_category),
            version_id=None if version is None else version[0],
            version_built_at=None if version is None else version[1],
            review=revisiones.get(node_id),
        )


def contadores(resumenes: Sequence[ResumenDeTema]) -> ContadoresDeRevision:
    """Los contadores de una lectura de temas, en **un solo sitio**.

    Los piden dos caminos —la tabla, que ya tiene las filas, y el contador del menú, que solo
    quiere el número— y contar en dos sitios acaba dando dos cifras distintas de lo mismo.

    Los cuatro recuentos salen de la **misma** regla que el estado de cada fila (`NotesState`): un
    tema sin apartados escritos no es un borrador, es un tema que todavía no se ha escrito, aunque
    tenga una versión archivada de antes. Por eso `published` y `draft` cuentan solo temas **con
    apuntes**, y `with_notes` es exactamente su suma.
    """
    con_apuntes = [tema for tema in resumenes if tema.has_notes]
    return ContadoresDeRevision(
        topics_total=len(resumenes),
        with_notes=len(con_apuntes),
        published=sum(1 for tema in con_apuntes if tema.published),
        draft=sum(1 for tema in con_apuntes if not tema.published),
        without_notes=sum(1 for tema in resumenes if not tema.has_notes),
        approved=sum(1 for tema in con_apuntes if tema_aprobado(tema)),
        rejected=sum(
            1
            for tema in con_apuntes
            if tema.review is not None and tema.review.decision is ReviewDecision.REJECTED
        ),
        pending_decision=sum(1 for tema in con_apuntes if not tema_aprobado(tema)),
    )


def tema_aprobado(tema: ResumenDeTema) -> bool:
    """¿Este tema ya no espera al propietario?

    Publicado cuenta como aprobado a efectos del contador: un tema que pasó las puertas y archivó su
    versión ya no espera a nadie. Lo que espera es el que **no** está publicado y nadie ha aprobado.
    """
    if tema.published:
        return True
    return tema.review is not None and tema.review.decision is ReviewDecision.APPROVED


def _con_desenlace(
    comprobaciones: ComprobacionesDelTema, resultado: str, cuantos: int
) -> ComprobacionesDelTema:
    """Suma un desenlace al recuento de un tema. El desenlace que no se conoce no se inventa."""
    datos = {
        "total": comprobaciones.total + cuantos,
        "covered": comprobaciones.covered,
        "gaps": comprobaciones.gaps,
        "doubtful": comprobaciones.doubtful,
        "conflicts": comprobaciones.conflicts,
    }
    if resultado in ("covered", "gap", "doubtful", "conflict"):
        clave = {
            "covered": "covered",
            "gap": "gaps",
            "doubtful": "doubtful",
            "conflict": "conflicts",
        }[resultado]
        datos[clave] = datos[clave] + cuantos
    return ComprobacionesDelTema(**datos)


def _revision(fila: TopicNotesReviewRecord) -> TopicReview:
    return TopicReview(
        node_id=str(fila.curriculum_node_id),
        decision=ReviewDecision(str(fila.decision)),
        note=None if fila.note is None else str(fila.note),
        actor=str(fila.actor),
        reviewed_at=fila.reviewed_at,
    )


__all__ = [
    "ACCION_REVISION",
    "OBJETO_TEMA",
    "ComprobacionesDelTema",
    "ContadoresDeRevision",
    "ResumenDeTema",
    "SqlAlchemyNotesReviewRepository",
    "contadores",
    "tema_aprobado",
]
