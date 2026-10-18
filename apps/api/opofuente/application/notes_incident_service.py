"""La bandeja del motor: lo que el sistema no pudo resolver, listo para que alguien decida (F18).

El servicio hace dos cosas y las dos son delgadas a propósito: **leer** la bandeja con sus filtros y
sus cifras, y **despachar** una incidencia. Lo que decide es:

- qué filtros se pueden pedir (categoría, estado, tema y búsqueda) y que el `total` que viaja con la
  lista sea el del filtro, contado en la base y no el de la página;
- que las cuatro cifras de las categorías y las cuatro de los estados sean **de la bandeja entera**,
  no del filtro: son los números de los botones, y un botón que dice cuántos hay «de esta categoría»
  después de haber filtrado por otra cosa diría un número que nadie entiende;
- que despachar una incidencia que no existe sea un 404 y no una escritura silenciosa.

La nota se normaliza **antes** de tocar la base, con la misma regla que la del aviso del alumno
(`normalise_note`): una nota kilométrica se rechaza sin haber escrito nada, y una nota en blanco no
es un error —significa «no hay nota»—.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace

from opofuente.application.notes_report_service import ACTOR_PROPIETARIO
from opofuente.application.question_models import TopicAssignmentRequest
from opofuente.application.question_service import QuestionService
from opofuente.domain.errors import NotFoundError
from opofuente.domain.key_reliability import KeyReliability
from opofuente.domain.notes_incidents import (
    IncidentFilter,
    IncidentStatus,
    NotesIncident,
    normalise_note,
)
from opofuente.domain.topic_classification import OutOfSyllabus
from opofuente.domain.topic_notes import CategoriaIncidencia
from opofuente.domain.tray import (
    TrayAction,
    TrayPage,
    TrayRefusalError,
    agrupar,
    paginar,
    rechazo_de_accion,
)
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.key_reliability_repository import (
    SqlAlchemyKeyReliabilityRepository,
)
from opofuente.infrastructure.notes_incident_repository import (
    BulkSummary,
    SqlAlchemyNotesIncidentRepository,
)

#: La nota que deja una acción en bloque cuando el propietario no escribe ninguna. Dice **qué** se
#: hizo y con qué regla, que es lo que hace falta para no tener que abrir la incidencia seis meses
#: después: el porqué de la decisión, no el texto de la pantalla.
NOTA_POR_ACCION: dict[TrayAction, str] = {
    TrayAction.ACEPTAR_DERIVADAS: (
        "aceptadas en bloque las claves derivadas del conjunto: apuntes con cita y respuesta "
        "independiente del modelo coinciden en la letra"
    ),
    TrayAction.DEJAR_FUERA: (
        "el conjunto queda fuera de tests, simulacros y repasos hasta que se arregle su clave"
    ),
    TrayAction.NO_SON_PREGUNTAS: (
        "lo que hay en el conjunto no son preguntas contestables: sale del temario y se queda en "
        "la base, fuera de tests y comprobaciones"
    ),
}

#: Por qué se saca del temario una pregunta desde la bandeja. Es el mismo texto que usa la
#: reclasificación automática, porque es el mismo hallazgo.
MOTIVO_EXCLUSION = (
    "el propietario ha decidido que lo que hay en este conjunto no son preguntas contestables "
    "(bandeja por conjunto, §2 del cierre del objetivo)"
)

#: El actor con el que se audita una acción en bloque que no dice quién es. El panel manda el suyo
#: por la cabecera, como en el resto de escrituras; esto es el respaldo.
ACTOR_BLOQUE = "panel:bandeja"


class NotesIncidentsService:
    """Lee la bandeja del motor y despacha las incidencias que el propietario ya ha decidido.

    Desde F31 también **agrupa** la bandeja por conjunto y aplica **acciones en bloque**, que es lo
    que la hace trabajable: 868 incidencias en 150 conjuntos no las revisa nadie una a una. Las dos
    acciones que escriben en otro sitio —dejar el conjunto fuera y sacarlo del temario— van por las
    rutas auditadas que ya existen (`set_verdict` y `apply_topic_batch`) en vez de por una escritura
    propia: dos caminos para el mismo cambio es como acabas con una clave cambiada sin su marca.
    """

    def __init__(
        self,
        incidents: SqlAlchemyNotesIncidentRepository,
        clock: SystemClock | None = None,
        *,
        keys: SqlAlchemyKeyReliabilityRepository | None = None,
        questions: QuestionService | None = None,
    ) -> None:
        self._incidents = incidents
        self._clock = clock if clock is not None else SystemClock()
        self._keys = keys
        self._questions = questions

    def list_incidents(
        self,
        *,
        category: CategoriaIncidencia | None = None,
        status: IncidentStatus | None = None,
        topic_code: str | None = None,
        set_id: str | None = None,
        q: str | None = None,
        limit: int = 200,
    ) -> tuple[NotesIncident, ...]:
        """Las incidencias, de la más nueva a la más vieja, con lo que las provoca resuelto."""
        return self._incidents.list_incidents(
            IncidentFilter(
                category=category,
                status=status,
                topic_code=topic_code,
                set_id=set_id,
                q=q,
                limit=limit,
            )
        )

    def total(
        self,
        *,
        category: CategoriaIncidencia | None = None,
        status: IncidentStatus | None = None,
        topic_code: str | None = None,
        set_id: str | None = None,
        q: str | None = None,
    ) -> int:
        """Cuántas incidencias hay con ese filtro, contadas en la base."""
        return self._incidents.count(
            category=category, status=status, topic_code=topic_code, set_id=set_id, q=q
        )

    def status_counts(self) -> dict[IncidentStatus, int]:
        """Cuántas hay en cada estado: los números de los filtros de estado de la bandeja."""
        return self._incidents.counts_by_status()

    def category_counts(self) -> dict[CategoriaIncidencia, int]:
        """Cuántas hay de cada categoría: **las cuatro cifras** de la bandeja, contadas en la
        base."""
        return self._incidents.counts_by_category()

    def count_open(self) -> int:
        """Cuántas incidencias siguen esperando a que alguien las mire. Es el número del menú."""
        return self._incidents.count_open()

    def update_incident(
        self,
        incident_id: str,
        *,
        status: IncidentStatus,
        note: str | None = None,
        actor: str = ACTOR_PROPIETARIO,
    ) -> NotesIncident:
        """Despacha una incidencia: en curso, resuelta o descartada, con la nota de lo decidido.

        Es la ruta **auditada** del bloque C: el cambio de estado, la nota y su evento entran en
        una sola transacción (lo hace el repositorio). Una incidencia que no existe es un 404: la
        bandeja se lee con identificadores de verdad, y escribir «en curso» sobre algo que no está
        sería dejar un evento que miente.
        """
        incidencia = self._incidents.update(
            incident_id=incident_id,
            status=status,
            note=normalise_note(note),
            actor=actor,
            now=self._clock.now(),
        )
        if incidencia is None:
            raise NotFoundError("incidencia del motor", incident_id)
        return incidencia

    # --------------------------------------------------- la bandeja por conjunto (F31, §2)

    def tray(self, *, page: int = 1) -> TrayPage:
        """Una **hoja** de la bandeja agrupada por conjunto, con la cifra que decide si sirve.

        Las propuestas salen de **una sola fuente** (`proposals()`): la tabla de claves derivadas
        del §1, que puede no estar —y entonces no hay propuestas, que es distinto de que no haya
        ninguna pendiente—. Un conjunto cuya clave está protegida no propone nada: su clave no se
        toca, así que aprobar una derivada ahí no sería una decisión, sería un error esperando.

        Se pagina **solo la lista de bancos** (cincuenta por hoja): con los datos del
        propietario son ciento cincuenta y siete filas, cada una con sus cuatro acciones y su
        resumen, y pintarlas todas de golpe hace que la pantalla tarde y que el trabajo real se
        haga cuesta abajo. Los totales que viajan con la hoja son los de la bandeja entera:
        paginar no puede cambiar la cifra que mide lo que queda.
        """
        filas = {fila.set_id: fila for fila in self._incidents.tray_sets()}
        propuestas: Counter[str] = Counter()
        for propuesta in self._incidents.proposals():
            fila = filas.get(propuesta.set_id)
            if fila is None or fila.es_oficial:
                continue
            propuestas[propuesta.set_id] += 1
        return paginar(
            agrupar(
                [
                    replace(fila, propuestas=propuestas.get(set_id, 0))
                    for set_id, fila in filas.items()
                    if fila.total_pendiente > 0 or propuestas.get(set_id, 0) > 0
                ]
            ),
            page=page,
        )

    def dispatch_bulk(
        self,
        *,
        action: TrayAction,
        set_id: str,
        note: str | None = None,
        actor: str = ACTOR_PROPIETARIO,
    ) -> BulkSummary:
        """Aplica una acción en bloque a un conjunto y deja su rastro.

        El rechazo de una clave oficial se comprueba **antes de escribir nada**, con el mismo
        criterio que la ficha de la pregunta (`protege_cambiar_la_clave`), y sale como
        `TrayRefusalError`: un conjunto oficial no admite ninguna de las tres acciones, porque su
        examen no se saca del temario ni se deja fuera de los tests por un botón.

        **Idempotente por construcción**: la segunda pasada no encuentra incidencias esperando —la
        primera las cerró— y devuelve cero. No hay una lista de «ya hecho» que mantener: el estado
        de la incidencia **es** la memoria.
        """
        fila = self._incidents.tray_set(set_id)
        if fila is None:
            raise NotFoundError("conjunto de la bandeja", set_id)
        rechazo = rechazo_de_accion(
            action, set_type=fila.set_type, tiene_plantilla_enlazada=fila.tiene_plantilla_enlazada
        )
        if rechazo is not None:
            raise TrayRefusalError(rechazo)

        texto = normalise_note(note) or NOTA_POR_ACCION[action]
        ahora = self._clock.now()

        if action is TrayAction.ACEPTAR_DERIVADAS:
            plan = tuple(
                propuesta for propuesta in self._incidents.proposals() if propuesta.set_id == set_id
            )
            if not plan:
                return BulkSummary(action=action.value, set_id=set_id, incidents=0)
            return self._incidents.accept_derived(
                set_id=set_id, plan=plan, note=texto, actor=actor, now=ahora
            )

        if action is TrayAction.DEJAR_FUERA:
            if self._keys is None:  # pragma: no cover - lo dice el montaje de la aplicación
                raise TrayRefusalError(
                    "la ruta que deja un conjunto fuera de los tests no está montada en esta "
                    "aplicación"
                )
            self._keys.set_verdict(
                set_id,
                KeyReliability.NO_FIABLE,
                now=ahora,
                actor=actor,
                reason=texto,
            )
            return self._incidents.leave_out(set_id=set_id, note=texto, actor=actor, now=ahora)

        if self._questions is None:  # pragma: no cover - lo dice el montaje de la aplicación
            raise TrayRefusalError(
                "la ruta que saca una pregunta del temario no está montada en esta aplicación"
            )
        preguntas = self._incidents.question_ids_of_set(set_id)
        if preguntas:
            self._questions.apply_topic_batch(
                [
                    TopicAssignmentRequest(
                        question_version_id=pregunta,
                        exclusion_reason=OutOfSyllabus.ENUNCIADO_ROTO,
                        reason=MOTIVO_EXCLUSION,
                        retire_others=True,
                    )
                    for pregunta in preguntas
                ],
                actor=actor,
            )
        return self._incidents.close_as_not_questions(
            set_id=set_id, note=texto, actor=actor, now=ahora
        )


__all__ = ["NotesIncidentsService"]
