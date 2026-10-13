"""La ficha de pregunta: se lee, se cambia la respuesta correcta y se repara (F20, §4.2).

El objetivo la llama «el sitio donde el propietario arregla las claves dudosas», y eso son dos
direcciones que ya existían apuntando a ninguna pantalla: la bandeja del motor
(`/notes-incidents` → `/admin/preguntas?pregunta=<id>`) y el banco. Lo que esta ruta publica es lo
que
hace falta para **decidir** una clave y para **cambiarla**:

- **de dónde sale la respuesta correcta que manda hoy**: la plantilla, el material del que salió, el
  estado de esa versión del material y el veredicto de fiabilidad del conjunto (§1). No se recalcula
  nada: la fiabilidad la mantiene la puerta de datos de aquel bloque y aquí se lee, o se dice que no
  está;
- **qué dicen los apuntes**: la letra, la frase verificada y el apartado exacto, que es lo que
permite
  juzgar sin abrir nada más;
- **qué ha señalado el motor**: las incidencias que cuelgan de la pregunta, con su categoría;
- **si está fuera del temario** y por qué;
- **qué se puede hacer**: marcar la correcta (con la anterior al historial) y reparar lo que una
regla
  mecánica pueda reparar. Las dos escrituras van auditadas y las dos se niegan, diciendo por qué,
  cuando la pregunta es de un examen oficial.

Dos cosas que **no** hay aquí a propósito: no hay ruta para escribir un enunciado a mano (eso es la
corrección local que ya existía, `POST /questions/{id}/local-corrections`) y no hay ruta para
recalcular la fiabilidad de un conjunto (eso es la puerta de datos del §1).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Header
from fastapi import Path as PathParam

from opofuente.api.deps import NotesIncidentsServiceDep, QuestionFileServiceDep
from opofuente.api.error_responses import CONFLICT_WRITE_ERRORS, RESOURCE_ERRORS
from opofuente.api.question_file_schemas import (
    MarkCorrectOptionSchema,
    MarkCorrectResultSchema,
    QuestionFileExclusionSchema,
    QuestionFileIncidentSchema,
    QuestionFileKeySchema,
    QuestionFileKeyVersionSchema,
    QuestionFileNotesSchema,
    QuestionFileOptionSchema,
    QuestionFileProtectedSetSchema,
    QuestionFileProtectionSchema,
    QuestionFileRepairSchema,
    QuestionFileSchema,
    QuestionFileVersionSchema,
    RepairQuestionSchema,
    RepairResultSchema,
)
from opofuente.application.question_file_models import QuestionFileView
from opofuente.application.question_file_service import ACTOR_REPARACION
from opofuente.domain.notes_incidents import IncidentStatus
from opofuente.domain.notes_reports import normalise_note

router = APIRouter(tags=["preguntas"])

#: La cabecera con la que el panel dice quién escribe, igual que en la clasificación y en la
#: bandeja.
ACTOR_HEADER = "X-OpoFuente-Actor"

#: Quién firma si nadie lo dice: una persona en esta máquina. El comando de reparación firma con
#: `f20:reparacion-preguntas`, que es lo que distingue una decisión tomada con el encargo delante de
#: una tomada mirando la pantalla.
DEFAULT_ACTOR = "local"


def _actor(*, declared: str | None, header: str | None, defecto: str = DEFAULT_ACTOR) -> str:
    """Quién escribe: lo que dice el cuerpo, si no la cabecera y, si no, el de por defecto."""
    for candidato in (declared, header):
        if candidato is not None and candidato.strip() != "":
            return candidato.strip()
    return defecto


def _file(vista: QuestionFileView) -> QuestionFileSchema:
    return QuestionFileSchema(
        question_version_id=vista.question_version_id,
        question_set_id=vista.question_set_id,
        set_title=vista.set_title,
        set_type=vista.set_type,  # type: ignore[arg-type]
        set_distribution=vista.set_distribution,  # type: ignore[arg-type]
        stable_key=vista.stable_key,
        version_no=vista.version_no,
        position=vista.position,
        question_type=vista.question_type,  # type: ignore[arg-type]
        status=vista.status,  # type: ignore[arg-type]
        origin_type=vista.origin_type,  # type: ignore[arg-type]
        is_reserve=vista.is_reserve,
        reserve_order=vista.reserve_order,
        created_at=vista.created_at,
        note=vista.note,
        stem=vista.stem,
        options=[
            QuestionFileOptionSchema(
                stable_key=opcion.stable_key,
                position=opcion.position,
                text=opcion.text,
                label=opcion.label,
            )
            for opcion in vista.options
        ],
        key=(
            None
            if vista.key is None
            else QuestionFileKeySchema(
                answer_key_version_id=vista.key.answer_key_version_id,
                version_no=vista.key.version_no,
                status=vista.key.status,  # type: ignore[arg-type]
                outcome=vista.key.outcome,  # type: ignore[arg-type]
                correct_option_keys=list(vista.key.correct_option_keys),
                approved_at=vista.key.approved_at,
                published_at=vista.key.published_at,
                source_document_id=vista.key.source_document_id,
                source_document_title=vista.key.source_document_title,
                source_document_type=vista.key.source_document_type,
                source_version_label=vista.key.source_version_label,
                source_version_status=vista.key.source_version_status,
                notes=vista.key.notes,
            )
        ),
        key_reliability=vista.key_reliability,  # type: ignore[arg-type]
        reliability_source=vista.reliability_source,
        notes=[
            QuestionFileNotesSchema(
                answer_letter=contraste.answer_letter,
                expected_letters=list(contraste.expected_letters),
                result=contraste.result,  # type: ignore[arg-type]
                phrase=contraste.phrase,
                anchor=contraste.anchor,
                section_title=contraste.section_title,
                topic_code=contraste.topic_code,
                topic_title=contraste.topic_title,
                key_status=contraste.key_status,  # type: ignore[arg-type]
                checked_at=contraste.checked_at,
                coincides=contraste.coincides,
            )
            for contraste in vista.notes
        ],
        incidents=[
            QuestionFileIncidentSchema(
                id=incidencia.id,
                category=incidencia.category,  # type: ignore[arg-type]
                reason=incidencia.reason,
                status=incidencia.status,  # type: ignore[arg-type]
                coverage=incidencia.coverage,  # type: ignore[arg-type]
                detail=incidencia.detail,
                phrase=incidencia.phrase,
                topic_code=incidencia.topic_code,
                topic_title=incidencia.topic_title,
                resolution_note=incidencia.resolution_note,
                reviewed_at=incidencia.reviewed_at,
            )
            for incidencia in vista.incidents
        ],
        exclusion=(
            None
            if vista.exclusion is None
            else QuestionFileExclusionSchema(
                reason=vista.exclusion.reason,  # type: ignore[arg-type]
                note=vista.exclusion.note,
                actor=vista.exclusion.actor,
                created_at=vista.exclusion.created_at,
            )
        ),
        protection=QuestionFileProtectionSchema(
            protected=vista.protection.protected,
            reason=vista.protection.reason,
            sets=[
                QuestionFileProtectedSetSchema(
                    id=conjunto.id,
                    title=conjunto.title,
                    set_type=conjunto.set_type,
                    source_document_title=conjunto.source_document_title,
                    reason=conjunto.reason,
                )
                for conjunto in vista.protection.sets
            ],
        ),
        repair=QuestionFileRepairSchema(
            reglas=list(vista.repair.reglas),
            titulos=list(vista.repair.titulos),
            detalle=vista.repair.detalle,
            stem=vista.repair.stem,
            opciones=(None if vista.repair.opciones is None else list(vista.repair.opciones)),
            por_que_no=vista.repair.por_que_no,
        ),
        versions=[
            QuestionFileVersionSchema(
                id=version.id,
                version_no=version.version_no,
                status=version.status,  # type: ignore[arg-type]
                stem=version.stem,
                note=version.note,
                created_at=version.created_at,
                option_count=version.option_count,
                correct_option_keys=list(version.correct_option_keys),
            )
            for version in vista.versions
        ],
        keys=[
            QuestionFileKeyVersionSchema(
                id=clave.id,
                version_no=clave.version_no,
                status=clave.status,  # type: ignore[arg-type]
                approved_at=clave.approved_at,
                created_at=clave.created_at,
                source_document_title=clave.source_document_title,
                correct_option_keys=list(clave.correct_option_keys),
            )
            for clave in vista.keys
        ],
        superseded_by=vista.superseded_by,
    )


@router.get(
    "/question-files/{question_version_id}",
    response_model=QuestionFileSchema,
    responses=RESOURCE_ERRORS,
    summary="La ficha de una pregunta: su clave, de dónde sale, los apuntes y qué se puede hacer",
)
def get_question_file(
    service: QuestionFileServiceDep,
    question_version_id: str = PathParam(
        description="Identificador de la versión de la pregunta, el que usa la bandeja del motor."
    ),
) -> QuestionFileSchema:
    """Todo lo que hace falta para decidir una clave, en una sola lectura.

        Es la pantalla que faltaba detrás de dos enlaces que ya existían: el de la bandeja del motor
        y
    el
        del banco. Sin ella, «clave sospechosa» era un enlace a una dirección sin ficha donde
    arreglarla.
    """
    return _file(service.file(question_version_id))


@router.post(
    "/question-files/{question_version_id}/answer-key",
    response_model=MarkCorrectResultSchema,
    responses=CONFLICT_WRITE_ERRORS,
    summary="Marca la respuesta correcta, por la ruta auditada (la anterior queda en el historial)",
)
def mark_correct_option(
    service: QuestionFileServiceDep,
    body: MarkCorrectOptionSchema,
    question_version_id: str = PathParam(description="Identificador de la versión de la pregunta."),
    actor_header: Annotated[str | None, Header(alias=ACTOR_HEADER)] = None,
) -> MarkCorrectResultSchema:
    """Cambia la respuesta correcta escribiendo una **plantilla nueva** del conjunto.

        Lo que garantiza y se puede comprobar después:

        - la plantilla que mandaba pasa a `superseded` y la nueva la apunta con `supersedes_id`:
        **no se
          pisa** nada, y el historial de la ficha enseña las dos con la letra que cada una daba a
          esta
          pregunta;
        - el estado se conserva: una plantilla activa se sustituye por otra activa (si no, marcar la
          correcta no cambiaría la corrección y la pantalla mentiría) y una en borrador por otra en
          borrador;
        - **una clave oficial no se toca**: si el conjunto es un examen oficial —o su plantilla
        viene de
    un
          documento, que es el otro camino a «oficial»— la respuesta es un **409 con el motivo** y
          no se
          escribe nada. Los conjuntos protegidos viajan en la ficha, con su nombre, para que no haya
          que
          adivinar cuál estorba;
        - una letra que la pregunta no tiene es un **422** con el campo, antes de tocar la base;
        - el antes, el después y el actor van en el mismo evento de auditoría y en la misma
        transacción
    que
          la plantilla.
    """
    resultado = service.mark_correct(
        question_version_id,
        correct_option_keys=body.correct_option_keys,
        note=body.note,
        actor=_actor(declared=body.actor, header=actor_header),
    )
    return MarkCorrectResultSchema(
        file=_file(resultado.file),
        key_version_id=resultado.key_version_id,
        superseded_key_version_id=resultado.superseded_key_version_id,
        previous_option_keys=list(resultado.previous_option_keys),
        correct_option_keys=list(resultado.correct_option_keys),
        actor=resultado.actor,
    )


@router.post(
    "/question-files/{question_version_id}/repairs",
    response_model=RepairResultSchema,
    responses=CONFLICT_WRITE_ERRORS,
    summary="Repara lo que una regla mecánica pueda reparar, escribiendo una versión nueva",
)
def repair_question(
    service: QuestionFileServiceDep,
    incidents: NotesIncidentsServiceDep,
    body: Annotated[RepairQuestionSchema, Body()],
    question_version_id: str = PathParam(description="Identificador de la versión de la pregunta."),
    actor_header: Annotated[str | None, Header(alias=ACTOR_HEADER)] = None,
) -> RepairResultSchema:
    """Escribe la versión nueva de la pregunta con lo que una regla mecánica puede arreglar.

        Solo hay dos reglas y las dos salen del §2 de los ajustes: quitar del enunciado la
        referencia
    del
        examen que quedó pegada al final y partir una opción que se tragó a la siguiente. Lo que no
        se
        pueda reparar con una regla **no se toca**: la ficha dice por qué y esta ruta lo repite con
        un
    409,
        en vez de escribir una versión con texto inventado.

        Y al reparar, el **sitio** de la pregunta viaja con ella: sus temas, sus anclas de apuntes y
        su
        marca de fuera de temario se mudan a la versión nueva. Sin eso, limpiar un enunciado sacaría
        la
        pregunta del temario y de la cobertura de los apuntes en silencio, que es un cambio mucho
        mayor
    que
        el que se ha pedido.

        Las incidencias de la pregunta se despachan como **resueltas** por la ruta auditada de la
    bandeja,
        con la nota de lo hecho: una bandeja que siguiera enseñando una pregunta ya reparada
        mentiría.
    """
    actor = _actor(declared=body.actor, header=actor_header, defecto=ACTOR_REPARACION)
    incidencias = service.incident_ids_of(question_version_id)
    resultado = service.repair(
        question_version_id,
        note=body.note,
        reglas=body.reglas,
        actor=actor,
    )
    despachadas = 0
    for incidencia_id in incidencias:
        incidents.update_incident(
            incidencia_id,
            status=IncidentStatus.REVIEWED,
            note=normalise_note(
                f"reparada: se escribió la versión "
                f"{resultado.file.version_no} de la pregunta ({', '.join(resultado.reglas)})"
            ),
            actor=actor,
        )
        despachadas += 1
    # La ficha se vuelve a leer **después** de despachar: la que devolvió la reparación se armó
    # antes
    # de que las incidencias cambiaran de estado, y contestar con ella diría que siguen abiertas
    # cuando ya no lo están.
    return RepairResultSchema(
        file=_file(service.file(resultado.new_question_version_id)),
        new_question_version_id=resultado.new_question_version_id,
        superseded_question_version_id=resultado.superseded_question_version_id,
        reglas=list(resultado.reglas),
        key_version_id=resultado.key_version_id,
        moved_topics=resultado.moved_topics,
        moved_anchors=resultado.moved_anchors,
        moved_exclusion=resultado.moved_exclusion,
        dispatched_incidents=despachadas,
        actor=resultado.actor,
    )
