"""Consultas del progreso del alumno (F2).

Es un repositorio **de lectura** y tiene las consultas agregadas que la zona del alumno necesita más
una de estado (qué temas tienen sus apuntes publicados). Todas las del progreso comparten tres
filtros, y los tres son la razón de que este fichero exista:

1. **la oposición**, siempre: el progreso de otro cuerpo no aparece por aquí ni en forma de cuenta
   (es el requisito de aislamiento de la fase);
2. **el dueño del progreso** (`owner_id`), siempre: hoy es `'local'`, y el filtro ya está para que
el
   día que haya cuentas nadie tenga que acordarse;
3. **`public` cuando el modo público está activo**: con la zona abierta, un banco privado del
   propietario no puede contar ni en un recuento.

Las cifras se calculan **en SQL** y no en Python a propósito: la zona del alumno pide el programa
entero (4 bloques, 33 temas) en cada carga, y traer todas las filas para contarlas aquí haría que la
pantalla tardara más cuanta más gente estudiara.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import ScalarSelect, Select, func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.topic_notes import NotesState
from opofuente.infrastructure.db_models import (
    AnswerKeyVersionRecord,
    AttemptEvaluationRecord,
    AttemptRecord,
    CurriculumMappingRecord,
    DossierSnapshotRecord,
    QuestionCurriculumExclusionRecord,
    QuestionNoteAnchorRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
    ReviewItemRecord,
    SessionQuestionRecord,
    StudySessionRecord,
    TopicNoteSectionRecord,
)
from opofuente.infrastructure.key_policy import clave_servible

#: Los desenlaces que cuentan para el porcentaje de acierto: los tres que puntúan, con el blanco
#: dentro. Un blanco no es un acierto, y dejarlo fuera subiría el porcentaje sin haber acertado
#: nada.
OUTCOMES_QUE_CUENTAN: tuple[str, ...] = ("correct", "wrong", "blank")

#: El desenlace que convierte una pregunta en un fallo para la lista de fallos.
OUTCOME_FALLADO = "wrong"


@dataclass(frozen=True, slots=True)
class MistakeRow:
    """Una pregunta que esta persona falló **la última vez** que la contestó.

    El identificador de la pregunta está aquí porque es lo que cruza sus temas y lo que pide el
    recuento; el servicio lo usa y **no lo publica**: la capa del alumno no tiene dónde ponerlo.
    """

    question_version_id: str
    stem: str
    last_failed_at: datetime
    times_failed: int
    due: bool


@dataclass(frozen=True, slots=True)
class MistakesView:
    """Los fallos de esta persona: la página que se enseña, los totales y el reparto por tema.

    `total` y `due_total` se cuentan sobre **todos** los fallos, no sobre la página: un
    «12 fallos» que en realidad son 300 porque solo se contaron los veinte que caben sería una
    cifra que miente. `topics` es el mismo recuento repartido por nodo del programa —`{nodo:
    (fallos, vencidos)}`—, que es con lo que la pantalla ofrece montar un test solo de los fallos de
    un tema.
    """

    rows: tuple[MistakeRow, ...]
    total: int
    due_total: int
    topics: Mapping[str, tuple[int, int]]
    #: De los fallos, cuántos se pueden **corregir** y por tanto se pueden repasar (F39). Es la
    #: cifra que decide si la pantalla ofrece el test de fallos o explica por qué no hay ninguno que
    #: montar: una pregunta fallada cuyo conjunto no tiene plantilla activa no se puede corregir, y
    #: ofrecer el botón acababa en un 409.
    servable_total: int = 0


@dataclass(frozen=True, slots=True)
class OfficialExamRow:
    """Un examen oficial importado, tal como la zona del alumno lo puede ofrecer.

    `ready` es si se puede **hacer** hoy: tener preguntas y una plantilla activa. Un examen a medio
    importar se enseña igual —existe— pero dice que todavía no se puede correr, en vez de ofrecer un
    botón que responde con un error.

    `origin_scope` es **de dónde sale** (D10): el alumno tiene que saber qué está practicando, y un
    examen de otra administración no es el examen que se va a encontrar.
    """

    question_set_id: str
    title: str
    held_at: date | None
    #: Las preguntas **que el examen serviría**: las ordinarias y las reservas que entran con la
    #: regla publicada por la convocatoria. No es el número de preguntas del conjunto: el
    #: cuestionario del INAP trae 135 (115 ordinarias y 20 de reserva) y el examen de TAI sirve 85
    #: (80 + 5), y una fila que dijera 135 estaría prometiendo un examen que no existe (§3.7).
    ordinary_questions: int
    reserve_questions: int
    ready: bool
    origin_scope: str = "desconocida"


def _solo_publicos[Fila: tuple[Any, ...]](
    consulta: Select[Fila], public_only: bool
) -> Select[Fila]:
    """Añade el filtro de visibilidad pública cuando la zona del alumno está abierta.

    La consulta que llega tiene que traer ya `question_sets` unido: el filtro es del conjunto,
    que es donde vive `distribution`, no de la pregunta.
    """
    if not public_only:
        return consulta
    return consulta.where(QuestionSetRecord.distribution == "public")


class SqlAlchemyStudentRepository:
    """Las consultas del progreso del alumno, y nada más."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ recuentos

    def question_counts(self, opposition_id: str, *, public_only: bool) -> Mapping[str, int]:
        """Preguntas **disponibles** por nodo del programa: catalogadas y vigentes.

        Es la misma regla que la cifra «preguntas: N» del Programa —mapeo aceptado— más los dos
        filtros de esta capa (la oposición del alumno y, en modo público, solo conjuntos públicos).
        Una versión sustituida no cuenta: ya no se practica.
        """
        consulta = (
            select(
                CurriculumMappingRecord.curriculum_node_id,
                func.count(func.distinct(QuestionVersionRecord.id)),
            )
            .join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == CurriculumMappingRecord.subject_id,
            )
            .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
            .where(
                CurriculumMappingRecord.subject_type == "question_version",
                CurriculumMappingRecord.status == "accepted",
                QuestionVersionRecord.status != "superseded",
                QuestionSetRecord.status != "archived",
                QuestionSetRecord.opposition_id == opposition_id,
            )
            .group_by(CurriculumMappingRecord.curriculum_node_id)
        )
        with self._session_factory() as session:
            filas = session.execute(_solo_publicos(consulta, public_only)).all()
        return {str(nodo): int(total) for nodo, total in filas}

    def answered_counts(
        self, opposition_id: str, owner_id: str, *, public_only: bool
    ) -> Mapping[str, int]:
        """Preguntas **vistas** por nodo: intentos registrados, se hayan corregido o no.

        El intento cuenta aunque la sesión no se haya cerrado y la corrección no se pueda enseñar:
        «vistas» es lo que el alumno ha hecho, no lo que ya sabe.
        """
        # **Dos pasos y no uno**: primero los intentos por pregunta —son 119—,
        # y despues el mapeo. **En una sola consulta SQLite elegia escanear los
        # 47.113 mapeos** aunque se le diera el indice: el `group by` por nodo lo
        # empujaba a empezar por ahi. **Con la subconsulta no puede**.
        seleccion_intentos = (
            select(
                SessionQuestionRecord.question_version_id.label("pregunta"),
                func.count(func.distinct(AttemptRecord.id)).label("intentos"),
            )
            .select_from(AttemptRecord)
            .join(
                SessionQuestionRecord,
                SessionQuestionRecord.id == AttemptRecord.session_question_id,
            )
            .join(StudySessionRecord, StudySessionRecord.id == SessionQuestionRecord.session_id)
            .join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == SessionQuestionRecord.question_version_id,
            )
            .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
            .where(
                StudySessionRecord.opposition_id == opposition_id,
                StudySessionRecord.owner_id == owner_id,
                QuestionSetRecord.opposition_id == opposition_id,
            )
        )
        # **El filtro de modo publico va AQUI, donde `question_sets` SI esta unido.** Antes se
        # aplicaba a la consulta de fuera, que solo une los mapeos: **referenciar `question_sets`
        # alli sin unirlo es un producto cartesiano**, y la condicion pasaba a decir «existe algun
        # conjunto publico» —**siempre verdadero**—, asi que **el modo publico servia los intentos
        # de un banco privado**. Lo dijo la prueba del modo publico, que llevaba en rojo sin que
        # constara.
        intentos_por_pregunta = (
            _solo_publicos(seleccion_intentos, public_only)
            .group_by(SessionQuestionRecord.question_version_id)
            .subquery()
        )
        consulta = (
            select(
                CurriculumMappingRecord.curriculum_node_id,
                func.sum(intentos_por_pregunta.c.intentos),
            )
            .select_from(intentos_por_pregunta)
            .join(
                CurriculumMappingRecord,
                (CurriculumMappingRecord.subject_id == intentos_por_pregunta.c.pregunta)
                & (CurriculumMappingRecord.subject_type == "question_version")
                & (CurriculumMappingRecord.status == "accepted"),
            )
            .group_by(CurriculumMappingRecord.curriculum_node_id)
        )
        with self._session_factory() as session:
            filas = session.execute(consulta).all()
        return {str(nodo): int(total) for nodo, total in filas}

    def outcome_counts(
        self, opposition_id: str, owner_id: str, *, public_only: bool
    ) -> Mapping[str, Mapping[str, int]]:
        """Desenlaces por nodo, con la evaluación **vigente** de cada intento.

        Recalcular con una clave nueva crea una evaluación nueva y no borra la anterior (invariante
        7): sumar todas contaría dos veces el mismo intento. La vigente es la última por fecha y, a
        igualdad, por identificador — el mismo desempate que usa el repositorio de estudio.
        """
        # **La evaluacion vigente, con una ventana y no con una subconsulta**
        # (M7): la version anterior pedia «la ultima evaluacion de este intento»
        # con una subconsulta correlacionada, y eso es una consulta por intento.
        # **Con `row_number()` la vigente se calcula de una pasada**, y el plan
        # deja de tener un `CORRELATED SCALAR SUBQUERY`.
        numeradas = select(
            AttemptEvaluationRecord.id.label("id"),
            AttemptEvaluationRecord.attempt_id.label("attempt_id"),
            AttemptEvaluationRecord.outcome.label("outcome"),
            func.row_number()
            .over(
                partition_by=AttemptEvaluationRecord.attempt_id,
                order_by=(
                    AttemptEvaluationRecord.evaluated_at.desc(),
                    AttemptEvaluationRecord.id.desc(),
                ),
            )
            .label("rango"),
        ).subquery()
        vigente = select(numeradas.c.id).where(numeradas.c.rango == 1).subquery()
        consulta = (
            select(
                CurriculumMappingRecord.curriculum_node_id,
                AttemptEvaluationRecord.outcome,
                func.count(func.distinct(AttemptEvaluationRecord.id)),
            )
            .select_from(AttemptEvaluationRecord)
            .join(AttemptRecord, AttemptRecord.id == AttemptEvaluationRecord.attempt_id)
            .join(
                SessionQuestionRecord,
                SessionQuestionRecord.id == AttemptRecord.session_question_id,
            )
            .join(StudySessionRecord, StudySessionRecord.id == SessionQuestionRecord.session_id)
            .join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == SessionQuestionRecord.question_version_id,
            )
            .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
            .join(
                CurriculumMappingRecord,
                (CurriculumMappingRecord.subject_id == SessionQuestionRecord.question_version_id)
                & (CurriculumMappingRecord.subject_type == "question_version")
                & (CurriculumMappingRecord.status == "accepted"),
            )
            .where(
                StudySessionRecord.opposition_id == opposition_id,
                StudySessionRecord.owner_id == owner_id,
                QuestionSetRecord.opposition_id == opposition_id,
                AttemptEvaluationRecord.outcome.in_(OUTCOMES_QUE_CUENTAN),
                AttemptEvaluationRecord.id.in_(select(vigente)),
            )
            .group_by(CurriculumMappingRecord.curriculum_node_id, AttemptEvaluationRecord.outcome)
        )
        with self._session_factory() as session:
            filas = session.execute(_solo_publicos(consulta, public_only)).all()
        recuentos: dict[str, dict[str, int]] = {}
        for nodo, desenlace, total in filas:
            recuentos.setdefault(str(nodo), {})[str(desenlace)] = int(total)
        return recuentos

    def public_set_ids(self, opposition_id: str) -> frozenset[str]:
        """Los conjuntos **publicables** de esta oposición: con ellos se decide qué sesión se sirve.

        Es la consulta que hace que el modo público no sea solo un filtro de recuentos: en modo
        público, un test cuyas preguntas salen de un banco privado del propietario no se enseña ni
        en el historial, porque su nota y sus aciertos son información de ese banco.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionSetRecord.id).where(
                    QuestionSetRecord.opposition_id == opposition_id,
                    QuestionSetRecord.distribution == "public",
                    QuestionSetRecord.status != "archived",
                )
            ).scalars()
            return frozenset(str(fila) for fila in filas)

    def due_counts(
        self,
        opposition_id: str,
        owner_id: str,
        *,
        now: datetime,
        public_only: bool,
    ) -> tuple[int, Mapping[str, int]]:
        """Fallos vencidos: el total y su reparto por tema `(total, {nodo: cuántos})`.

        Un fallo vencido es una pregunta de repaso cuya fecha ya pasó **y** que esta persona falló
        de
        verdad: la cola de repaso se llena sola al responder, así que sin el `EXISTS` sobre los
        intentos del dueño se contarían repasos de sesiones que no son suyos.

        El total **no** exige que la pregunta esté catalogada en un tema: una pregunta sin tema
        también se repasa, y el total tiene que cuadrar con la lista que la pantalla enseña.

        **Y cuenta solo lo que el repaso puede servir** (F39, §2 de la revisión del recorrido): la
        cola de repaso se llena sola al fallar, y una pregunta fallada puede no tener con qué
        corregirse —su conjunto se archivó, su plantilla se sustituyó, la letra no está—. Contarla
        hacía que Inicio prometiera «5 preguntas para repasar hoy» y el repaso contestara 409: la
        cifra y lo que la cifra promete salen de la **misma** política de claves, que está en
        `key_policy.clave_servible` y es la que usan los tests de práctica.
        """
        del_dueno = (
            select(func.count())
            .select_from(AttemptRecord)
            .join(
                SessionQuestionRecord,
                SessionQuestionRecord.id == AttemptRecord.session_question_id,
            )
            .join(StudySessionRecord, StudySessionRecord.id == SessionQuestionRecord.session_id)
            .where(
                SessionQuestionRecord.question_version_id == ReviewItemRecord.question_version_id,
                StudySessionRecord.owner_id == owner_id,
                StudySessionRecord.opposition_id == opposition_id,
            )
            .exists()
        )
        base = (
            select(ReviewItemRecord.id, ReviewItemRecord.question_version_id)
            .join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == ReviewItemRecord.question_version_id,
            )
            .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
            .where(
                ReviewItemRecord.opposition_id == opposition_id,
                ReviewItemRecord.due_at <= now,
                QuestionSetRecord.opposition_id == opposition_id,
                QuestionSetRecord.status != "archived",
                del_dueno,
                clave_servible(ReviewItemRecord.question_version_id),
            )
        )
        with self._session_factory() as session:
            vencidos = session.execute(_solo_publicos(base, public_only)).all()
            if not vencidos:
                return 0, {}
            por_pregunta = {str(pregunta) for _, pregunta in vencidos}
            mapeos = session.execute(
                select(
                    CurriculumMappingRecord.curriculum_node_id,
                    CurriculumMappingRecord.subject_id,
                ).where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    CurriculumMappingRecord.subject_id.in_(por_pregunta),
                )
            ).all()
        por_nodo: dict[str, int] = {}
        for nodo, _pregunta in mapeos:
            por_nodo[str(nodo)] = por_nodo.get(str(nodo), 0) + 1
        return len(vencidos), por_nodo

    def notes_states(self) -> Mapping[str, NotesState]:
        """El estado de los apuntes de cada tema que **tiene apartados escritos**.

        Un tema que no aparece aquí no tiene apuntes (`NotesState.NONE`), y quien pregunta lo dice
        con su valor por defecto: devolver una fila «sin apuntes» por cada nodo del programa sería
        escribir 33 ceros para contar tres temas.

        Lo que separa el borrador del publicado no es el texto —los tres temas redactados lo
        tienen—, sino la **versión archivada**: el tema que pasa las dos puertas del §2.3 archiva su
        versión y es lo que la marca «Versión generada · en revisión» señala al alumno. Un tema con
        texto y sin versión se lee igual, y la pantalla dice que está en borrador.
        """
        with self._session_factory() as session:
            con_apartados = set(
                session.execute(
                    select(TopicNoteSectionRecord.curriculum_node_id).distinct()
                ).scalars()
            )
            publicados = set(
                session.execute(
                    select(DossierSnapshotRecord.curriculum_node_id).distinct()
                ).scalars()
            )
        return {
            str(nodo): (NotesState.PUBLISHED if str(nodo) in publicados else NotesState.DRAFT)
            for nodo in con_apartados
        }

    # ------------------------------------------------------------------ los fallos (F14)

    def mistakes(
        self,
        opposition_id: str,
        owner_id: str,
        *,
        now: datetime,
        public_only: bool,
        limit: int,
    ) -> MistakesView:
        """Las preguntas que esta persona falló **la última vez**, de la más reciente a la más
        vieja.

        Cuatro decisiones, y las cuatro se ven en la consulta:

        1. **manda la última vez que la contestó**, no cualquier intento: una pregunta fallada y
           después acertada no es un fallo, y la lista tiene que decir lo mismo que el filtro de
           falladas con el que se monta un test (`_pasa_el_filtro`), o la pantalla ofrecería repasar
           preguntas que el test no pondría;
        2. **manda la evaluación vigente** de cada intento: recalcular con otra plantilla añade una
           evaluación nueva sin borrar la anterior (invariante 7), así que sumarlas contaría dos
           veces el mismo intento;
        3. **`times_failed` cuenta fallos de verdad**, no intentos: la cifra que el alumno lee
           («la has fallado 3 veces») sale de las evaluaciones con desenlace `wrong` de sus
           propios intentos;
        4. **el vencimiento se mira contra `review_items`**, que es la cola de repaso, y se calcula
           para **todos** los fallos aunque solo se devuelva una página: el «N para repasar hoy»
           de la pantalla tiene que cuadrar con lo que hay, no con lo que cabe.
        """
        vigente = (
            select(AttemptEvaluationRecord.id)
            .where(AttemptEvaluationRecord.attempt_id == AttemptRecord.id)
            .order_by(
                AttemptEvaluationRecord.evaluated_at.desc(),
                AttemptEvaluationRecord.id.desc(),
            )
            .limit(1)
            # `correlate` explícito, como en `outcome_counts`: sin él SQLAlchemy autocorrelaciona la
            # tabla de dentro y la subconsulta se queda sin `FROM`.
            .correlate(AttemptRecord)
            .scalar_subquery()
        )
        # La última vez que esta persona vio la pregunta: la sesión más reciente en la que salió.
        presentacion = (
            select(SessionQuestionRecord.id)
            .join(StudySessionRecord, StudySessionRecord.id == SessionQuestionRecord.session_id)
            .where(
                SessionQuestionRecord.question_version_id == QuestionVersionRecord.id,
                StudySessionRecord.opposition_id == opposition_id,
                StudySessionRecord.owner_id == owner_id,
            )
            .order_by(
                StudySessionRecord.created_at.desc(),
                StudySessionRecord.id.desc(),
                SessionQuestionRecord.position.desc(),
            )
            .limit(1)
            .correlate(QuestionVersionRecord)
            .scalar_subquery()
        )
        consulta = (
            select(QuestionVersionRecord.id, QuestionVersionRecord.stem)
            .select_from(QuestionVersionRecord)
            .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
            .join(AttemptRecord, AttemptRecord.session_question_id == presentacion)
            .join(AttemptEvaluationRecord, AttemptEvaluationRecord.attempt_id == AttemptRecord.id)
            .where(
                QuestionSetRecord.opposition_id == opposition_id,
                AttemptEvaluationRecord.outcome == OUTCOME_FALLADO,
                AttemptEvaluationRecord.id.in_(select(vigente)),
            )
            .order_by(AttemptRecord.answered_at.desc(), QuestionVersionRecord.id.asc())
        )
        with self._session_factory() as session:
            filas = session.execute(_solo_publicos(consulta, public_only)).all()
            identificadores = [str(fila[0]) for fila in filas]
            vencidas: set[str] = set()
            servibles: set[str] = set()
            por_nodo: dict[str, list[int]] = {}
            cuenta_de_fallos: dict[str, tuple[int, datetime]] = {}
            if identificadores:
                # Lo que se puede corregir, con la política de claves de siempre (`key_policy`): un
                # fallo sin clave no se puede repasar, y la pantalla no puede ofrecer un test que la
                # API va a rechazar con un 409.
                servibles = {
                    str(pregunta)
                    for pregunta in session.execute(
                        select(QuestionVersionRecord.id).where(
                            QuestionVersionRecord.id.in_(identificadores),
                            clave_servible(QuestionVersionRecord.id),
                        )
                    ).scalars()
                }
                vencidas = {
                    str(pregunta)
                    for pregunta in session.execute(
                        select(ReviewItemRecord.question_version_id).where(
                            ReviewItemRecord.question_version_id.in_(identificadores),
                            ReviewItemRecord.opposition_id == opposition_id,
                            ReviewItemRecord.due_at <= now,
                            clave_servible(ReviewItemRecord.question_version_id),
                        )
                    ).scalars()
                }
                mapeos = session.execute(
                    select(
                        CurriculumMappingRecord.curriculum_node_id,
                        CurriculumMappingRecord.subject_id,
                    ).where(
                        CurriculumMappingRecord.subject_type == "question_version",
                        CurriculumMappingRecord.status == "accepted",
                        CurriculumMappingRecord.subject_id.in_(identificadores),
                    )
                ).all()
                for nodo, pregunta in mapeos:
                    cuenta = por_nodo.setdefault(str(nodo), [0, 0])
                    cuenta[0] += 1
                    if str(pregunta) in vencidas:
                        cuenta[1] += 1
                # Los fallos de cada pregunta y cuándo fue el último: se piden solo para la página,
                # porque son los que se enseñan (los totales se cuentan sin esto).
                pagina = identificadores[:limit]
                repetidos = session.execute(
                    select(
                        SessionQuestionRecord.question_version_id,
                        func.count(func.distinct(AttemptEvaluationRecord.id)),
                        func.max(AttemptEvaluationRecord.evaluated_at),
                    )
                    .select_from(AttemptEvaluationRecord)
                    .join(AttemptRecord, AttemptRecord.id == AttemptEvaluationRecord.attempt_id)
                    .join(
                        SessionQuestionRecord,
                        SessionQuestionRecord.id == AttemptRecord.session_question_id,
                    )
                    .join(
                        StudySessionRecord,
                        StudySessionRecord.id == SessionQuestionRecord.session_id,
                    )
                    .where(
                        SessionQuestionRecord.question_version_id.in_(pagina),
                        StudySessionRecord.opposition_id == opposition_id,
                        StudySessionRecord.owner_id == owner_id,
                        AttemptEvaluationRecord.outcome == OUTCOME_FALLADO,
                        AttemptEvaluationRecord.id.in_(select(vigente)),
                    )
                    .group_by(SessionQuestionRecord.question_version_id)
                ).all()
                for pregunta, cuantos, ultima in repetidos:
                    cuenta_de_fallos[str(pregunta)] = (int(cuantos), ultima)
        rows: list[MistakeRow] = []
        for fila in filas[:limit]:
            identificador = str(fila[0])
            fallos, ultima = cuenta_de_fallos.get(identificador, (0, None))
            if ultima is None:  # pragma: no cover - toda fila de la página tiene su cuenta
                continue
            rows.append(
                MistakeRow(
                    question_version_id=identificador,
                    stem=str(fila[1]),
                    times_failed=fallos,
                    last_failed_at=ultima,
                    due=identificador in vencidas,
                )
            )
        return MistakesView(
            rows=tuple(rows),
            total=len(filas),
            due_total=len(vencidas),
            topics={nodo: (cuenta[0], cuenta[1]) for nodo, cuenta in por_nodo.items()},
            servable_total=sum(
                1 for identificador in identificadores if identificador in servibles
            ),
        )

    def topics_of_questions(
        self, question_version_ids: Sequence[str]
    ) -> Mapping[str, tuple[str, ...]]:
        """Los temas **aceptados** de cada pregunta: `{pregunta: (nodo, …)}`.

        Una pregunta puede estar en dos temas (D7): por eso el valor es una tupla y no un nodo
        suelto.
        Elegir uno aquí sería inventar cuál manda, y la pantalla de fallos lo que tiene que decir es
        por qué temas se puede repasar esa pregunta.
        """
        if not question_version_ids:
            return {}
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    CurriculumMappingRecord.subject_id,
                    CurriculumMappingRecord.curriculum_node_id,
                ).where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.status == "accepted",
                    CurriculumMappingRecord.subject_id.in_(list(question_version_ids)),
                )
            ).all()
        por_pregunta: dict[str, list[str]] = {}
        for pregunta, nodo in filas:
            por_pregunta.setdefault(str(pregunta), []).append(str(nodo))
        return {pregunta: tuple(nodos) for pregunta, nodos in por_pregunta.items()}

    def note_anchors_of_questions(
        self, question_version_ids: Sequence[str]
    ) -> Mapping[str, tuple[tuple[str, str, str], ...]]:
        """El apartado que contesta cada pregunta: su nodo, su ancla y **su capítulo**.

        Se devuelve `{pregunta: ((nodo, ancla, capítulo), …)}`. Es lo que convierte «Ver en
        apuntes» en una salida útil: la dirección del apartado dentro del tema
        (`/temario/IV.7?capitulo=IV.7.2#apartado-udp`), no la portada.

        Tres decisiones, y las tres son sobre lo que **no** se devuelve:

        1. solo las comprobaciones con desenlace `covered`: un hueco (`gap`) o una duda
           (`doubtful`) no son un párrafo que explique nada, y enlazarlos mandaría al alumno a un
           apartado que no contesta su pregunta;
        2. solo si el apartado **existe hoy** (el `JOIN` con `topic_note_sections` por nodo y
           ancla): los apuntes se reescriben, y un ancla guardada que ya no está daría un enlace
           que no lleva a ninguna parte sin decirlo;
        3. una pregunta puede estar en dos temas (D7) y tener un apartado en cada uno: se
           devuelven todos y **quien decide** es el servicio, con el mismo orden del programa que
           usa para los temas. Elegir aquí sería inventar cuál de los dos manda.

        El **capítulo** (el `epigraph_code` del apartado) sale del mismo `JOIN` y por eso se
        devuelve aquí y no se busca después: desde que los apuntes se leen por epígrafes, el anclaje
        solo no resuelve —`#osi-capas` no está en el primer capítulo de IV.7— y el enlace necesita
        saber qué epígrafe abrir. Resolverlo en el servicio sería una consulta más por pregunta.
        """
        if not question_version_ids:
            return {}
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    QuestionNoteAnchorRecord.question_version_id,
                    QuestionNoteAnchorRecord.curriculum_node_id,
                    QuestionNoteAnchorRecord.anchor,
                    TopicNoteSectionRecord.epigraph_code,
                )
                .join(
                    TopicNoteSectionRecord,
                    (
                        TopicNoteSectionRecord.curriculum_node_id
                        == QuestionNoteAnchorRecord.curriculum_node_id
                    )
                    & (TopicNoteSectionRecord.anchor == QuestionNoteAnchorRecord.anchor),
                )
                .where(
                    QuestionNoteAnchorRecord.question_version_id.in_(list(question_version_ids)),
                    QuestionNoteAnchorRecord.result == "covered",
                )
            ).all()
        por_pregunta: dict[str, list[tuple[str, str, str]]] = {}
        for pregunta, nodo, ancla, epigrafe in filas:
            por_pregunta.setdefault(str(pregunta), []).append(
                (str(nodo), str(ancla), str(epigrafe))
            )
        return {pregunta: tuple(anclas) for pregunta, anclas in por_pregunta.items()}

    # ------------------------------------------------------- los exámenes oficiales (F14)

    def official_exams(
        self, opposition_id: str, *, public_only: bool
    ) -> tuple[OfficialExamRow, ...]:
        """Los exámenes oficiales importados de esta oposición, con lo que hace falta para hacer
        uno.

        Qué es un examen oficial aquí **no se decide en esta capa**: es un conjunto cuyo tipo lo
        dice
        (`official_exam`), que es como lo deja el importador del INAP. Si no hay ninguno importado,
        la
        lista sale vacía y la pantalla lo dice; no se rellena con bancos de práctica disfrazados.

        **Lo que cuenta no es lo que el conjunto tiene, sino lo que el examen sirve.** Un
        cuestionario del INAP trae 135 preguntas vigentes —115 ordinarias y 20 de reserva— y el
        examen de TAI monta 85, porque la convocatoria publica 80 preguntas y 5 de reserva para su
        primera
        parte. Contar las del conjunto hacía que la fila dijera 135 y el examen tuviera 85, y el
        alumno que elige «135 preguntas» se encuentra 85 sin saber si le falta algo (§3.7).

        Se devuelven las **dos** cifras que hacen falta para aplicar esa regla —ordinarias y
        reservas, ya sin las marcadas fuera de temario, que tampoco entran en el examen— y la regla
        se aplica donde se conoce la parte, que es el servicio. Aquí no se adivina.

        `ready` mira la plantilla activa: sin ella el examen no se puede corregir, y ofrecerlo sería
        ofrecer un examen que no se puede terminar.
        """
        fuera_de_temario = (
            select(QuestionCurriculumExclusionRecord.question_version_id)
            .where(
                QuestionCurriculumExclusionRecord.question_version_id == QuestionVersionRecord.id
            )
            .exists()
        )

        def cuenta(*, reserva: bool) -> ScalarSelect[int]:
            return (
                select(func.count(func.distinct(QuestionVersionRecord.id)))
                .where(
                    QuestionVersionRecord.question_set_id == QuestionSetRecord.id,
                    QuestionVersionRecord.status != "superseded",
                    QuestionVersionRecord.is_reserve.is_(reserva),
                    ~fuera_de_temario,
                )
                .correlate(QuestionSetRecord)
                .scalar_subquery()
            )

        plantillas = (
            select(func.count())
            .select_from(AnswerKeyVersionRecord)
            .where(
                AnswerKeyVersionRecord.question_set_id == QuestionSetRecord.id,
                AnswerKeyVersionRecord.status == "active",
            )
            .correlate(QuestionSetRecord)
            .scalar_subquery()
        )
        consulta = (
            select(
                QuestionSetRecord.id,
                QuestionSetRecord.title,
                QuestionSetRecord.held_at,
                cuenta(reserva=False),
                cuenta(reserva=True),
                plantillas,
                QuestionSetRecord.origin_scope,
            )
            .where(
                QuestionSetRecord.opposition_id == opposition_id,
                QuestionSetRecord.set_type == "official_exam",
                QuestionSetRecord.status != "archived",
            )
            # Los que tienen fecha, del más antiguo al más nuevo, y delante los que no la tienen:
            # una fecha ausente no puede ordenar como si fuera 1970. El título desempata para que
            # dos corridas den la misma lista (y, con ella, las mismas posiciones).
            .order_by(
                QuestionSetRecord.held_at.is_(None),
                QuestionSetRecord.held_at.asc(),
                QuestionSetRecord.title.asc(),
            )
        )
        with self._session_factory() as session:
            filas = session.execute(_solo_publicos(consulta, public_only)).all()
        return tuple(
            OfficialExamRow(
                question_set_id=str(fila[0]),
                title=str(fila[1]),
                held_at=fila[2],
                ordinary_questions=int(fila[3]),
                reserve_questions=int(fila[4]),
                ready=int(fila[5]) > 0 and (int(fila[3]) + int(fila[4])) > 0,
                origin_scope=str(fila[6]),
            )
            for fila in filas
        )
