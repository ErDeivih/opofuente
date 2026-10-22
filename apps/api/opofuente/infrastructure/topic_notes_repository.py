"""Las preguntas de un tema y todo lo que escriben los apuntes (pasos B-E).

Es el repositorio del trabajo de apuntes. Tres decisiones que se ven en el SQL y en los métodos:

1. **las preguntas del tema incluyen las de sus epígrafes**: una pregunta asignada a `IV.7.1` cuenta
   para `IV.7` (lo fijó `DECISIONES-Y-SIGUIENTE-TANDA` §3), y los apuntes se escriben del tema
   entero;
2. **la clave se lee con su estado**: la activa es la que corrige los tests y con ella la letra del
   modelo decide; con una clave en borrador (o sin clave) el resultado se decide solo por la frase
   verificada. El estado se guarda con el resultado para que el informe pueda decir con qué se
   comprobó cada pregunta;
3. **todas las escrituras son idempotentes por su clave natural** (tema + huella del hecho, tema +
   subapartado, pregunta + tema), porque una corrida de apuntes se para y se reanuda: lo que ya está
   escrito no se repite y lo que falta se escribe.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.topic_notes_models import NotesNode
from opofuente.domain.key_reliability import KeyReliability
from opofuente.domain.rag import normalise
from opofuente.domain.topic_notes import (
    HECHOS_NUEVOS,
    VERSION_PLANTILLA,
    CategoriaIncidencia,
    Coverage,
    FactKind,
    Hecho,
    IncidenciaDeApuntes,
    KeyStatus,
    Motivo,
    NotesCheck,
    NoteSection,
    QuestionForNotes,
    QuestionGroup,
    SectionNotes,
    TopicNotes,
    agrupar,
)
from opofuente.infrastructure.db_models import (
    AnswerKeyEntryRecord,
    AnswerKeyVersionRecord,
    AuditEventRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    NotesIncidentRecord,
    OptionVersionRecord,
    QuestionNoteAnchorRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
    TopicFactRecord,
    TopicNoteSectionRecord,
)

#: Identificadores por consulta. SQLite tiene un tope de parámetros por sentencia y el tema más
#: grande pasa de dos mil preguntas.
_TANDA = 400

#: Estados de la pregunta que no entran: una versión sustituida ya no es una pregunta del banco.
_ESTADOS_FUERA = ("superseded",)


class SqlAlchemyTopicNotesRepository:
    """Lee las preguntas de un tema y guarda los hechos, los apartados y las comprobaciones."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ el tema

    def node_id(self, code: str) -> str | None:
        """El nodo del tema por su ruta (`IV.7`). Se busca por ruta: el código oficial es el
        número."""
        with self._session_factory() as session:
            fila = session.execute(
                select(CurriculumNodeRecord.id).where(
                    CurriculumNodeRecord.path == code,
                )
            ).first()
        return None if fila is None else str(fila[0])

    def node(self, node_id: str) -> NotesNode | None:
        """El tema con sus epígrafes oficiales, en orden. `None` si el nodo no es un tema."""
        with self._session_factory() as session:
            ambito = self._ambito(session, node_id)
            if not ambito:
                return None
            titulos = {
                str(fila[0]): str(fila[1])
                for fila in session.execute(
                    select(CurriculumNodeRecord.id, CurriculumNodeRecord.title).where(
                        CurriculumNodeRecord.id.in_([nodo for nodo, _ in ambito])
                    )
                ).all()
            }
        return NotesNode(
            node_id=node_id,
            code=ambito[0][1],
            title=titulos.get(node_id, ""),
            epigraphs=tuple((path, titulos.get(nodo, "")) for nodo, path in ambito[1:]),
        )

    def _ambito(self, session: Session, node_id: str) -> tuple[tuple[str, str], ...]:
        """El tema y sus hijos como `(id, path)`, el tema primero y el resto en orden oficial."""
        fila = session.execute(
            select(CurriculumNodeRecord.path).where(
                CurriculumNodeRecord.id == node_id,
            )
        ).first()
        if fila is None:
            return ()
        hijos = session.execute(
            select(CurriculumNodeRecord.id, CurriculumNodeRecord.path)
            .where(CurriculumNodeRecord.parent_id == node_id)
            .order_by(CurriculumNodeRecord.position, CurriculumNodeRecord.path)
        ).all()
        return (
            (node_id, str(fila[0])),
            *((str(hijo[0]), str(hijo[1])) for hijo in hijos),
        )

    # ------------------------------------------------------------------ las preguntas

    def question_groups(self, node_id: str) -> tuple[QuestionGroup, ...]:
        """Los grupos de preguntas del tema y de sus epígrafes, con su clave y su estado.

        Se agrupa por firma (enunciado y opciones normalizados) porque las mismas preguntas
        repetidas
        entre bancos comparten un solo trabajo: se escriben los hechos una vez y se comprueban una
        vez,
        y el resultado se guarda para **todas** las preguntas del grupo.
        """
        with self._session_factory() as session:
            ambito = self._ambito(session, node_id)
            if not ambito:
                return ()
            tema, epigrafes = ambito[0], ambito[1:]
            epigrafe_por_pregunta: dict[str, str] = {}
            estado_por_pregunta: dict[str, str] = {}
            for nodo, path in (tema, *epigrafes):
                filas = session.execute(
                    select(
                        CurriculumMappingRecord.subject_id,
                        CurriculumMappingRecord.status,
                    ).where(
                        CurriculumMappingRecord.subject_type == "question_version",
                        CurriculumMappingRecord.curriculum_node_id == nodo,
                        CurriculumMappingRecord.status != "rejected",
                    )
                ).all()
                for pregunta_id, estado in filas:
                    clave = str(pregunta_id)
                    if path != tema[1]:
                        epigrafe_por_pregunta.setdefault(clave, path)
                    if estado_por_pregunta.get(clave) != "accepted":
                        estado_por_pregunta[clave] = str(estado)
            if not estado_por_pregunta:
                return ()
            identificadores = sorted(estado_por_pregunta)
            leidas = self._leer_preguntas(session, identificadores)
            claves = self._claves(session, identificadores)
            en_cuarentena = self._conjuntos_en_cuarentena(session)
        completo: list[QuestionForNotes] = []
        for pregunta_id in identificadores:
            leida = leidas.get(pregunta_id)
            if leida is None:
                continue
            conjunto, enunciado, opciones = leida
            if conjunto in en_cuarentena:
                # Cuarentena de clave (§1): las preguntas de un conjunto cuya clave discrepa de los
                # apuntes en más del 30 % **no cuentan en el denominador de la cobertura**. Si
                # contaran, la puerta del 90 % estaría midiendo al tema contra una clave que se sabe
                # mala: el tema bajaría por un fallo del banco y el propietario reescribiría apuntes
                # que estaban bien. Tampoco generan hechos ni anclas: la cita que se guardara
                # apuntaría a una respuesta equivocada.
                continue
            letras, estado_clave = claves.get(pregunta_id, ((), KeyStatus.NINGUNA))
            completo.append(
                QuestionForNotes(
                    question_version_id=pregunta_id,
                    set_id=conjunto,
                    stem=enunciado,
                    options=opciones,
                    correct_keys=letras,
                    key_status=estado_clave,
                    epigraph_code=epigrafe_por_pregunta.get(pregunta_id),
                    mapping_status=estado_por_pregunta.get(pregunta_id, "accepted"),
                )
            )
        return agrupar(completo)

    @staticmethod
    def _conjuntos_en_cuarentena(session: Session) -> frozenset[str]:
        """Los conjuntos con la clave en cuarentena (`no_fiable`), en una sola consulta.

        Se leen todos y no solo los del tema a proposito: la consulta es una y la lista es de
        decenas, mientras que acotarla por tema obligaria a otra consulta por cada llamada —y
        `question_groups` se llama en cada paso de cada tema.
        """
        filas = session.execute(
            select(QuestionSetRecord.id).where(
                QuestionSetRecord.key_reliability == KeyReliability.NO_FIABLE.value
            )
        ).scalars()
        return frozenset(str(fila) for fila in filas)

    @staticmethod
    def _leer_preguntas(
        session: Session, identificadores: Sequence[str]
    ) -> dict[str, tuple[str, str, tuple[tuple[str, str], ...]]]:
        """`id → (conjunto, enunciado, opciones)`, saltando las versiones sustituidas."""
        leidas: dict[str, tuple[str, str]] = {}
        opciones: dict[str, list[tuple[str, str]]] = {}
        for tanda in _tandas(identificadores):
            for pregunta_id, conjunto, enunciado, estado in session.execute(
                select(
                    QuestionVersionRecord.id,
                    QuestionVersionRecord.question_set_id,
                    QuestionVersionRecord.stem,
                    QuestionVersionRecord.status,
                ).where(QuestionVersionRecord.id.in_(tanda))
            ).all():
                if str(estado) in _ESTADOS_FUERA:
                    continue
                leidas[str(pregunta_id)] = (str(conjunto), str(enunciado))
            for pregunta_id, clave, texto in session.execute(
                select(
                    OptionVersionRecord.question_version_id,
                    OptionVersionRecord.stable_key,
                    OptionVersionRecord.text,
                )
                .where(OptionVersionRecord.question_version_id.in_(tanda))
                .order_by(OptionVersionRecord.question_version_id, OptionVersionRecord.position)
            ).all():
                opciones.setdefault(str(pregunta_id), []).append((str(clave), str(texto)))
        return {
            pregunta_id: (conjunto, enunciado, tuple(opciones.get(pregunta_id, [])))
            for pregunta_id, (conjunto, enunciado) in leidas.items()
        }

    @staticmethod
    def _claves(
        session: Session, identificadores: Sequence[str]
    ) -> dict[str, tuple[tuple[str, ...], KeyStatus]]:
        """La respuesta correcta de cada pregunta y **cuánto se puede fiar** de ella.

        La activa manda. Si no hay activa, se acepta una en borrador **solo si todas las entradas en
        borrador dicen lo mismo**: los conjuntos con la plantilla desalineada tienen varias
        versiones
        que apuntan a posiciones distintas, y con dos respuestas distintas no hay nada que
        comprobar.
        """
        por_pregunta: dict[str, list[tuple[str, str, tuple[str, ...]]]] = {}
        for tanda in _tandas(identificadores):
            filas = session.execute(
                select(
                    AnswerKeyVersionRecord.status,
                    AnswerKeyEntryRecord.question_version_id,
                    AnswerKeyEntryRecord.outcome,
                    AnswerKeyEntryRecord.correct_option_keys_json,
                )
                .join(
                    AnswerKeyEntryRecord,
                    AnswerKeyEntryRecord.answer_key_version_id == AnswerKeyVersionRecord.id,
                )
                .where(AnswerKeyEntryRecord.question_version_id.in_(tanda))
            ).all()
            for estado, pregunta_id, desenlace, letras in filas:
                por_pregunta.setdefault(str(pregunta_id), []).append(
                    (str(estado), str(desenlace), _letras(letras))
                )
        resultado: dict[str, tuple[tuple[str, ...], KeyStatus]] = {}
        for pregunta_id in identificadores:
            entradas = por_pregunta.get(pregunta_id, [])
            activas = [
                letras
                for estado, desenlace, letras in entradas
                if estado == "active" and desenlace == "keyed"
            ]
            if activas:
                resultado[pregunta_id] = (activas[0], KeyStatus.ACTIVE)
                continue
            borradores = {
                letras
                for estado, desenlace, letras in entradas
                if estado == "draft" and desenlace == "keyed"
            }
            if len(borradores) == 1:
                resultado[pregunta_id] = (next(iter(borradores)), KeyStatus.DRAFT)
            else:
                resultado[pregunta_id] = ((), KeyStatus.NINGUNA)
        return resultado

    # ------------------------------------------------------------------ los hechos

    def facts(self, node_id: str) -> tuple[Hecho, ...]:
        """Los hechos del tema, en un orden **estable**: el mismo tema da el mismo esquema.

        El orden es por cuándo se escribieron y, a igualdad, por el grupo de preguntas del que salen
        (y por el identificador como último desempate). Las dos partes importan:

        - `created_at` solo no basta: los hechos de una misma corrida se guardan con la misma marca
          de tiempo, y ordenar por el identificador (que es aleatorio) barajaría los hechos en cada
          lectura. Como el esquema parte los hechos en trozos de cuarenta **en ese orden**, el
          reparto por apartados cambiaría entre dos corridas y el rastro pregunta → párrafo dejaría
          de valer;
        - el grupo como segundo criterio mantiene juntos los hechos de una misma pregunta, que es lo
          que se espera al leer un apartado.
        """
        with self._session_factory() as session:
            return self._hechos(session, node_id)

    @staticmethod
    def _hechos(session: Session, node_id: str) -> tuple[Hecho, ...]:
        filas = session.execute(
            select(TopicFactRecord)
            .where(TopicFactRecord.curriculum_node_id == node_id)
            .order_by(
                TopicFactRecord.created_at,
                TopicFactRecord.source_group_ids,
                TopicFactRecord.id,
            )
        ).scalars()
        return tuple(_hecho(fila) for fila in filas)

    def save_facts(
        self, node_id: str, hechos: Sequence[Hecho], *, now: datetime
    ) -> tuple[Hecho, ...]:
        """Guarda los hechos nuevos y devuelve los guardados, en el mismo orden que llegaron.

        La huella del texto normalizado evita duplicados: el mismo hecho dos veces (en dos lotes, o
        en
        dos corridas) es un hecho, no dos.
        """
        guardados: list[Hecho] = []
        with self._session_factory() as session:
            existentes = {
                str(fila.text_hash): fila
                for fila in session.execute(
                    select(TopicFactRecord).where(TopicFactRecord.curriculum_node_id == node_id)
                ).scalars()
            }
            for hecho in hechos:
                huella = huella_de_hecho(hecho.text)
                fila = existentes.get(huella)
                if fila is None:
                    fila = TopicFactRecord(
                        id=str(uuid4()),
                        curriculum_node_id=node_id,
                        epigraph_code=hecho.epigraph_code,
                        subsection_key=hecho.section_key or None,
                        text=hecho.text,
                        text_hash=huella,
                        kind=hecho.kind.value,
                        doubtful=hecho.doubtful,
                        note=hecho.note,
                        source_group_ids=json.dumps(sorted(set(hecho.source_groups))),
                        source_question_ids=json.dumps(sorted(set(hecho.source_questions))),
                        created_at=now,
                    )
                    session.add(fila)
                    existentes[huella] = fila
                else:
                    # El mismo hecho con otro rastro: se une, que es lo que pasa con un grupo
                    # repetido.
                    fila.source_group_ids = json.dumps(
                        sorted(
                            set(json.loads(str(fila.source_group_ids))) | set(hecho.source_groups)
                        )
                    )
                    fila.source_question_ids = json.dumps(
                        sorted(
                            set(json.loads(str(fila.source_question_ids)))
                            | set(hecho.source_questions)
                        )
                    )
                    fila.doubtful = bool(fila.doubtful) or hecho.doubtful
                guardados.append(_hecho(fila))
            session.commit()
        return tuple(guardados)

    # ------------------------------------------------------------------ los apartados

    def sections(self, node_id: str) -> tuple[NoteSection, ...]:
        """Los apartados del tema, en orden, con sus hechos."""
        with self._session_factory() as session:
            return self._secciones(session, node_id)

    @staticmethod
    def _secciones(session: Session, node_id: str) -> tuple[NoteSection, ...]:
        filas = (
            session.execute(
                select(TopicNoteSectionRecord)
                .where(TopicNoteSectionRecord.curriculum_node_id == node_id)
                .order_by(TopicNoteSectionRecord.position, TopicNoteSectionRecord.id)
            )
            .scalars()
            .all()
        )
        hechos = SqlAlchemyTopicNotesRepository._hechos(session, node_id)
        por_clave: dict[str, list[Hecho]] = {}
        for hecho in hechos:
            if hecho.section_key:
                por_clave.setdefault(hecho.section_key, []).append(hecho)
        return tuple(
            NoteSection(
                key=str(fila.subsection_key),
                epigraph_code=str(fila.epigraph_code),
                title=str(fila.title),
                anchor=str(fila.anchor),
                position=int(fila.position),
                facts=tuple(por_clave.get(str(fila.subsection_key), ())),
                body_markdown=str(fila.body_markdown),
                needs_review_reason=fila.needs_review_reason,
                section_id=str(fila.id),
            )
            for fila in filas
        )

    def save_sections(
        self, node_id: str, sections: Sequence[NoteSection], *, now: datetime
    ) -> tuple[NoteSection, ...]:
        """Crea o actualiza los apartados del esquema y reparte sus hechos.

        Reglas que se ven en el orden de las operaciones:

        1. un apartado **no se borra** por no venir en la lista: el esquema se recalcula y una lista
           parcial (la de un añadido) no puede llevarse por delante el resto del tema;
        2. el texto de un apartado que ya existía **se conserva** aunque se vuelva a repartir el
           esquema: reescribirlo costaría otra llamada y perdería lo revisado;
        3. cuando a un apartado que ya tenía texto le llegan hechos que no tenía asignados, se marca
           `hechos nuevos sin integrar`: el propietario tiene que saber que ese texto es de antes.
        """
        with self._session_factory() as session:
            existentes = {
                str(fila.subsection_key): fila
                for fila in session.execute(
                    select(TopicNoteSectionRecord).where(
                        TopicNoteSectionRecord.curriculum_node_id == node_id
                    )
                ).scalars()
            }
            for apartado in sections:
                fila = existentes.get(apartado.key)
                if fila is None:
                    fila = TopicNoteSectionRecord(
                        id=str(uuid4()),
                        curriculum_node_id=node_id,
                        subsection_key=apartado.key,
                        epigraph_code=apartado.epigraph_code,
                        title=apartado.title,
                        anchor=apartado.anchor,
                        position=apartado.position,
                        body_markdown="",
                        status="pending",
                        needs_review_reason=apartado.needs_review_reason,
                        model=None,
                        prompt_template_version=VERSION_PLANTILLA,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(fila)
                    existentes[apartado.key] = fila
                else:
                    fila.epigraph_code = apartado.epigraph_code
                    fila.title = apartado.title
                    fila.anchor = apartado.anchor
                    fila.position = apartado.position
                    if apartado.needs_review_reason and not fila.needs_review_reason:
                        fila.needs_review_reason = apartado.needs_review_reason
                    fila.updated_at = now
                session.flush()
                _repartir(session, fila, apartado, now=now)
            session.commit()
        return self.sections(node_id)

    def save_section_body(
        self,
        section: NoteSection,
        *,
        title: str | None,
        body: str,
        needs_review_reason: str | None,
        model: str | None,
        now: datetime,
        append: bool = False,
    ) -> NoteSection:
        """Escribe el texto de un apartado, o le añade un párrafo (`append=True`)."""
        with self._session_factory() as session:
            fila = session.get(TopicNoteSectionRecord, section.section_id)
            if fila is None:
                return section
            if title:
                fila.title = title
            texto = str(fila.body_markdown)
            fila.body_markdown = f"{texto}\n\n{body}" if append and texto.strip() else body
            fila.needs_review_reason = needs_review_reason
            fila.model = model or fila.model
            fila.updated_at = now
            session.commit()
        with self._session_factory() as session:
            guardada = session.get(TopicNoteSectionRecord, section.section_id)
            if guardada is None:
                return section
            hechos = [
                hecho
                for hecho in self._hechos(session, str(guardada.curriculum_node_id))
                if hecho.section_key == str(guardada.subsection_key)
            ]
            return NoteSection(
                key=str(guardada.subsection_key),
                epigraph_code=str(guardada.epigraph_code),
                title=str(guardada.title),
                anchor=str(guardada.anchor),
                position=int(guardada.position),
                facts=tuple(hechos),
                body_markdown=str(guardada.body_markdown),
                needs_review_reason=guardada.needs_review_reason,
                section_id=str(guardada.id),
            )

    # ------------------------------------------------------------------ las comprobaciones

    def checks(self, node_id: str) -> tuple[NotesCheck, ...]:
        """Los resultados guardados del tema, para reanudar sin volver a comprobar lo comprobado."""
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionNoteAnchorRecord)
                .where(QuestionNoteAnchorRecord.curriculum_node_id == node_id)
                .order_by(QuestionNoteAnchorRecord.checked_at, QuestionNoteAnchorRecord.id)
            ).scalars()
            return tuple(_check(fila) for fila in filas)

    def save_checks(self, node_id: str, results: Sequence[NotesCheck], *, now: datetime) -> int:
        """Guarda el resultado de comprobar unas preguntas (una fila por pregunta y tema)."""
        if not results:
            return 0
        with self._session_factory() as session:
            claves = {
                str(fila.subsection_key): str(fila.id)
                for fila in session.execute(
                    select(TopicNoteSectionRecord).where(
                        TopicNoteSectionRecord.curriculum_node_id == node_id
                    )
                ).scalars()
            }
            existentes: dict[str, QuestionNoteAnchorRecord] = {}
            identificadores = [resultado.question_version_id for resultado in results]
            for tanda in _tandas(identificadores):
                for existente in session.execute(
                    select(QuestionNoteAnchorRecord).where(
                        QuestionNoteAnchorRecord.curriculum_node_id == node_id,
                        QuestionNoteAnchorRecord.question_version_id.in_(tanda),
                    )
                ).scalars():
                    existentes[str(existente.question_version_id)] = existente
            for resultado in results:
                fila = existentes.get(resultado.question_version_id)
                if fila is None:
                    fila = QuestionNoteAnchorRecord(
                        id=str(uuid4()),
                        question_version_id=resultado.question_version_id,
                        curriculum_node_id=node_id,
                        anchor=resultado.anchor,
                        group_signature=resultado.group_signature,
                        key_status=resultado.key_status.value,
                        result=resultado.coverage.value,
                        checked_at=now,
                    )
                    session.add(fila)
                    existentes[resultado.question_version_id] = fila
                fila.section_id = claves.get(resultado.section_key)
                fila.anchor = resultado.anchor
                fila.group_signature = resultado.group_signature
                fila.quoted_sentence = resultado.quote
                fila.answer_letter = resultado.letter
                fila.expected_letters = json.dumps(list(resultado.expected))
                fila.key_status = resultado.key_status.value
                fila.result = resultado.coverage.value
                fila.note = None if resultado.note is None else resultado.note.value
                fila.attempts = resultado.attempts
                # La huella del texto contra el que se verificó esta cita: es lo que permite saber,
                # en la corrida siguiente, si la comprobación sigue valiendo o el apartado se ha
                # reescrito y hay que volver a comprobarlo.
                fila.text_sha256 = resultado.text_sha256
                fila.checked_at = now
            session.commit()
        return len(results)

    # ------------------------------------------------------------------ la bandeja del propietario

    def save_incidents(
        self, node_id: str, incidents: Sequence[IncidenciaDeApuntes], *, now: datetime
    ) -> int:
        """Guarda en la bandeja las preguntas que los apuntes no cubren, con su categoría.

        Una fila por pregunta y tema: volver a comprobar el tema **actualiza** la incidencia (puede
        cambiar de categoría o dejar de estar) y la retira si esa pregunta ya está cubierta. Sin
        eso, la bandeja crecería con cada corrida y dejaría de ser una bandeja.

        Devuelve cuántas quedan dentro después de la escritura.
        """
        with self._session_factory() as session:
            existentes: dict[str, NotesIncidentRecord] = {}
            for existente in session.execute(
                select(NotesIncidentRecord).where(NotesIncidentRecord.curriculum_node_id == node_id)
            ).scalars():
                existentes[str(existente.question_version_id)] = existente
            vistas: set[str] = set()
            for incidencia in incidents:
                vistas.add(incidencia.question_version_id)
                fila = existentes.get(incidencia.question_version_id)
                if fila is None:
                    fila = NotesIncidentRecord(
                        id=str(uuid4()),
                        question_version_id=incidencia.question_version_id,
                        curriculum_node_id=node_id,
                        group_signature=incidencia.group_signature,
                        category=incidencia.category.value,
                        coverage=Coverage.DUDOSA.value,
                        reason=incidencia.reason.value,
                        created_at=now,
                    )
                    session.add(fila)
                    existentes[incidencia.question_version_id] = fila
                fila.group_signature = incidencia.group_signature
                fila.category = incidencia.category.value
                # El desenlace que la bandeja enseña: un conflicto de letra es un conflicto, no una
                # duda. Se deduce del motivo, que es lo único que distingue los dos casos.
                fila.coverage = (
                    Coverage.CONFLICTO.value
                    if incidencia.reason is Motivo.LETRA_NO_COINCIDE
                    else Coverage.DUDOSA.value
                )
                fila.reason = incidencia.reason.value
                fila.section_key = incidencia.section_key or None
                fila.anchor = incidencia.anchor or None
                fila.phrase = incidencia.phrase
                fila.detail = incidencia.detail
            # Lo que ya no está en la lista se ha resuelto: sale de la bandeja.
            for question_id, fila in existentes.items():
                if question_id not in vistas:
                    session.delete(fila)
            session.commit()
        return len(vistas)

    def incidents(self, node_id: str) -> tuple[IncidenciaDeApuntes, ...]:
        """La bandeja del tema: lo que espera el criterio del propietario, por categoría."""
        with self._session_factory() as session:
            filas = session.execute(
                select(NotesIncidentRecord)
                .where(NotesIncidentRecord.curriculum_node_id == node_id)
                .order_by(NotesIncidentRecord.category, NotesIncidentRecord.created_at)
            ).scalars()
            return tuple(
                IncidenciaDeApuntes(
                    question_version_id=str(fila.question_version_id),
                    group_signature=str(fila.group_signature),
                    category=CategoriaIncidencia(str(fila.category)),
                    reason=Motivo(str(fila.reason)),
                    detail=str(fila.detail),
                    section_key="" if fila.section_key is None else str(fila.section_key),
                    anchor="" if fila.anchor is None else str(fila.anchor),
                    phrase=fila.phrase,
                )
                for fila in filas
            )

    # ------------------------------------------------------------------ lo que se publica

    def notes_for_node(self, node_id: str) -> TopicNotes | None:
        """Los apuntes del tema con el recuento de sus preguntas, para la versión del tema.

        `None` si el tema todavía no tiene apartados: unos apuntes vacíos no son unos apuntes.
        """
        with self._session_factory() as session:
            secciones = self._secciones(session, node_id)
            if not secciones:
                return None
            filas = (
                session.execute(
                    select(QuestionNoteAnchorRecord).where(
                        QuestionNoteAnchorRecord.curriculum_node_id == node_id
                    )
                )
                .scalars()
                .all()
            )
            ultima = session.execute(
                select(TopicNoteSectionRecord.model, TopicNoteSectionRecord.updated_at)
                .where(TopicNoteSectionRecord.curriculum_node_id == node_id)
                .order_by(TopicNoteSectionRecord.updated_at.desc())
                .limit(1)
            ).first()
        por_ancla: dict[str, list[QuestionNoteAnchorRecord]] = {}
        for fila in filas:
            por_ancla.setdefault(str(fila.anchor), []).append(fila)
        apartados = tuple(
            SectionNotes(
                key=apartado.key,
                epigraph_code=apartado.epigraph_code,
                title=apartado.title,
                anchor=apartado.anchor,
                body_markdown=apartado.body_markdown,
                needs_review_reason=apartado.needs_review_reason,
                facts_total=len(apartado.facts),
                covered=_cuenta(suyos, Coverage.CUBIERTA),
                gaps=_cuenta(suyos, Coverage.HUECO),
                doubtful=_cuenta(suyos, Coverage.DUDOSA),
                conflicts=_cuenta(suyos, Coverage.CONFLICTO),
                question_ids=_preguntas(suyos, Coverage.CUBIERTA),
                gap_question_ids=_preguntas(suyos, Coverage.HUECO),
                doubtful_question_ids=_preguntas(suyos, Coverage.DUDOSA),
                conflict_question_ids=_preguntas(suyos, Coverage.CONFLICTO),
            )
            for apartado in secciones
            for suyos in (por_ancla.get(apartado.anchor, []),)
        )
        return TopicNotes(
            generated_at=None if ultima is None else ultima[1],
            model=None if ultima is None else ultima[0],
            prompt_template_version=VERSION_PLANTILLA,
            sections=apartados,
        )

    def forget_sections(self, node_id: str) -> int:
        """Tira los apartados del tema con sus enlaces y deja los hechos sin repartir.

        Los hechos se conservan (son el trabajo caro y siguen siendo verdad); lo que se pierde es el
        reparto por apartados y las comprobaciones, que es justo lo que dejó de valer cuando el
        esquema se movió.
        """
        with self._session_factory() as session:
            borrados = len(
                session.execute(
                    select(TopicNoteSectionRecord.id).where(
                        TopicNoteSectionRecord.curriculum_node_id == node_id
                    )
                ).all()
            )
            session.execute(
                delete(QuestionNoteAnchorRecord).where(
                    QuestionNoteAnchorRecord.curriculum_node_id == node_id
                )
            )
            session.execute(
                delete(TopicNoteSectionRecord).where(
                    TopicNoteSectionRecord.curriculum_node_id == node_id
                )
            )
            for hecho in session.execute(
                select(TopicFactRecord).where(TopicFactRecord.curriculum_node_id == node_id)
            ).scalars():
                hecho.subsection_key = None
            session.commit()
        return borrados

    def forget(self, node_id: str) -> None:
        """Borra los apuntes de un tema (hechos, apartados y comprobaciones). Solo para pruebas."""
        with self._session_factory() as session:
            session.execute(
                delete(QuestionNoteAnchorRecord).where(
                    QuestionNoteAnchorRecord.curriculum_node_id == node_id
                )
            )
            session.execute(
                delete(TopicNoteSectionRecord).where(
                    TopicNoteSectionRecord.curriculum_node_id == node_id
                )
            )
            session.execute(
                delete(TopicFactRecord).where(TopicFactRecord.curriculum_node_id == node_id)
            )
            session.commit()

    def forget_facts(
        self,
        node_id: str,
        fact_ids: Sequence[str],
        *,
        actor: str,
        reason: str,
        now: datetime,
    ) -> int:
        """Tira los hechos indicados del tema y escribe un evento de auditoría por cada uno.

        Un hecho cuyo tema ya no es el suyo no se queda: sostendría un apartado del que no es y
        volvería a escribirse. Se borra por identificador (nunca por consulta a ciegas) y el evento
        dice **cuál**, **quién** y **por qué**, con el texto delante: la auditoría de una pérdida de
        trabajo tiene que poder leerse sin la base.
        """
        if not fact_ids:
            return 0
        borrados = 0
        with self._session_factory() as session:
            for tanda in _tandas(list(fact_ids)):
                filas = (
                    session.execute(
                        select(TopicFactRecord).where(
                            TopicFactRecord.curriculum_node_id == node_id,
                            TopicFactRecord.id.in_(tanda),
                        )
                    )
                    .scalars()
                    .all()
                )
                for fila in filas:
                    session.add(
                        AuditEventRecord(
                            id=str(uuid4()),
                            actor=actor,
                            action="topic_fact.forgotten",
                            object_type="topic_fact",
                            object_id=str(fila.id),
                            before_json=json.dumps(
                                {
                                    "curriculum_node_id": str(fila.curriculum_node_id),
                                    "text": str(fila.text),
                                    "epigraph_code": str(fila.epigraph_code),
                                    "source_group_ids": json.loads(str(fila.source_group_ids)),
                                },
                                ensure_ascii=False,
                            ),
                            after_json=json.dumps({"reason": reason}, ensure_ascii=False),
                            correlation_id=None,
                            created_at=now,
                        )
                    )
                    session.delete(fila)
                    borrados += 1
            session.commit()
        return borrados


def huella_de_hecho(texto: str) -> str:
    """La huella normalizada de un hecho: sin acentos, sin signos, sin espacios de más."""
    apretado = re.sub(r"\s+", " ", normalise(texto)).strip()
    return hashlib.sha256(apretado.encode("utf-8")).hexdigest()


def _repartir(
    session: Session,
    fila: TopicNoteSectionRecord,
    apartado: NoteSection,
    *,
    now: datetime,
) -> None:
    """Pone los hechos del apartado en su sitio y marca los que llegan a un texto ya escrito."""
    identificadores = [hecho.fact_id for hecho in apartado.facts if hecho.fact_id]
    if not identificadores:
        return
    suyos = (
        session.execute(select(TopicFactRecord).where(TopicFactRecord.id.in_(identificadores)))
        .scalars()
        .all()
    )
    if (
        any(hecho.subsection_key is None for hecho in suyos)
        and str(fila.body_markdown).strip()
        and not fila.needs_review_reason
    ):
        fila.needs_review_reason = HECHOS_NUEVOS
    for hecho in suyos:
        if hecho.subsection_key != apartado.key:
            hecho.subsection_key = apartado.key
    fila.updated_at = now


def _letras(valor: object) -> tuple[str, ...]:
    """Las letras de una clave, en minúscula y ordenadas: `["b"]` → `("b",)`."""
    if not isinstance(valor, str):
        return ()
    try:
        crudo = json.loads(valor)
    except json.JSONDecodeError:
        return ()
    if not isinstance(crudo, list):
        return ()
    return tuple(sorted(str(letra).strip().lower() for letra in crudo if str(letra).strip()))


def _hecho(fila: TopicFactRecord) -> Hecho:
    return Hecho(
        text=str(fila.text),
        kind=(
            FactKind.NORMATIVO if str(fila.kind) == FactKind.NORMATIVO.value else FactKind.TECNICO
        ),
        epigraph_code=str(fila.epigraph_code),
        source_groups=tuple(str(firma) for firma in json.loads(str(fila.source_group_ids))),
        source_questions=tuple(
            str(pregunta) for pregunta in json.loads(str(fila.source_question_ids))
        ),
        doubtful=bool(fila.doubtful),
        note=fila.note,
        fact_id=str(fila.id),
        section_key="" if fila.subsection_key is None else str(fila.subsection_key),
    )


def _check(fila: QuestionNoteAnchorRecord) -> NotesCheck:
    return NotesCheck(
        question_version_id=str(fila.question_version_id),
        group_signature=str(fila.group_signature),
        section_key="",
        anchor=str(fila.anchor),
        coverage=Coverage(str(fila.result)),
        note=None if fila.note is None else Motivo(str(fila.note)),
        quote=fila.quoted_sentence,
        letter=fila.answer_letter,
        expected=_letras(fila.expected_letters),
        key_status=KeyStatus(str(fila.key_status)),
        attempts=int(fila.attempts),
        text_sha256=fila.text_sha256,
    )


def _cuenta(filas: Sequence[QuestionNoteAnchorRecord], cobertura: Coverage) -> int:
    return sum(1 for fila in filas if str(fila.result) == cobertura.value)


def _preguntas(filas: Sequence[QuestionNoteAnchorRecord], cobertura: Coverage) -> tuple[str, ...]:
    return tuple(
        str(fila.question_version_id) for fila in filas if str(fila.result) == cobertura.value
    )


def _tandas(identificadores: Sequence[str], tamano: int = _TANDA) -> list[list[str]]:
    """Trocea una lista de identificadores para no pasarse del tope de parámetros de SQLite."""
    return [
        list(identificadores[inicio : inicio + tamano])
        for inicio in range(0, len(identificadores), tamano)
    ]


__all__ = ["SqlAlchemyTopicNotesRepository", "huella_de_hecho"]
