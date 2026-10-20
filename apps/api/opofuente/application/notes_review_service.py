"""La revisión de los apuntes en el panel: ver, leer, aprobar y rechazar (F24, §4.3 del objetivo).

Es lo que quedaba del punto (4) del objetivo. El propietario ya podía leer los apuntes en su zona y
marcar «esto está mal», y el motor ya dejaba sus incidencias en una bandeja; lo que no existía era
el sitio donde **él decide** sobre el texto de un tema y donde el motivo de un borrador se le
enseña con su cifra sin leer un informe técnico.

Cinco cosas y todo lo demás sale de ahí:

1. **los temas con su estado** (`published` / `draft` / `none`), con lo que ha comprobado el motor
   y lo que la bandeja tiene sin despachar;
2. **el motivo de cada borrador, medido**: se lee de donde ya está —las comprobaciones guardadas—
   con el **mismo camino** que `apuntes --medir` (`TopicNotesService.medir`), que no llama al
   modelo y no cuesta nada. No se recalcula a mano ni se hereda de un documento: la cifra que el
   propietario ve es la que diría el comando. Se mide **solo lo que espera una decisión** (los
   borradores): medir los publicados costaría la mitad de la página para no decir nada nuevo —ya
   pasaron las puertas—, y su ficha sí los mide cuando se abre;
3. **la ficha de un tema, apartado a apartado**, con su texto y su forma, y con las mismas filas
   que lee la zona del alumno: el panel no tiene una segunda versión de los apuntes;
4. **aprobar y rechazar por ruta auditada**: la decisión y su evento en la misma transacción.
   Aprobar **publica** cuando las dos puertas del §2.3 pasan (archiva la versión por el camino de
   siempre) y, cuando no pasan, deja el tema aprobado y dice **qué puerta** lo frena con su cifra.
   **El listón no se toca**: una decisión del propietario no convierte un 82 % en un 90 %;
5. **lo que se decide sobrevive a una corrida del motor**: la decisión vive en su propia tabla
   (`topic_notes_reviews`), y el motor no escribe en ella. Volver a medir un tema no borra que
   alguien lo aprobó o lo rechazó.

El servicio no decide **cuándo** se publica —eso es el par de puertas del §2.3 y
`DossierService`— ni qué apartados están bien: eso lo contestan los hechos guardados y la
comprobación del motor.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, NoReturn

from opofuente.application.dossier_service import DossierService
from opofuente.application.notes_review_models import (
    FichaDeRevision,
    ResultadoDeDecision,
    ReviewBlockName,
    RevisionDeApuntes,
    SeccionDeRevision,
    TemaEnRevision,
    VersionDeTema,
)
from opofuente.application.ports import ProfileRepository, TopicNotesReader
from opofuente.application.topic_notes_models import CoverageReport, TopicNotesReport
from opofuente.application.topic_notes_service import TopicNotesService
from opofuente.domain.errors import InvalidReviewError, NotFoundError, UnsupportedError
from opofuente.domain.notes_review import (
    CifrasDelTema,
    ReviewDecision,
    normalise_decision_note,
    razones_del_tema,
)
from opofuente.domain.topic_notes import Motivo, NotesState, SectionNotes
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.notes_review_repository import (
    ContadoresDeRevision,
    ResumenDeTema,
    SqlAlchemyNotesReviewRepository,
    contadores,
)

#: Qué puerta del §2.3 impide publicar cuando el tema está aprobado y no se puede archivar.
BLOQUEO_POR_COBERTURA: ReviewBlockName = "cobertura"
BLOQUEO_POR_FORMA: ReviewBlockName = "forma"

#: Cómo se ordenan los apartados de la ficha: el de lectura, o lo que queda sin resolver antes.
ReviewOrder = Literal["lectura", "peores"]

#: Cuántos apartados viajan por hoja en la ficha. Seis llena una pantalla de 1280 sin que el primer
#: párrafo llegue tarde y es el mismo tamaño que sirve la zona del alumno.
SECCIONES_POR_PAGINA = 6


class MedidaSinModelo:
    """El motor que **no** se usa: medir un tema lee lo guardado y no llama a nadie.

    El servicio de apuntes necesita un `NotesModel` para construirse, y la revisión solo usa su
    método de medida (`medir`), que trabaja sobre las comprobaciones guardadas. Esto existe para que
    medir un tema no pueda costar dinero **ni por accidente**: si algún camino de la medida acabara
    pidiendo algo al modelo, lo dice en vez de gastar.

    Es el mismo objeto que el comando de apuntes tiene en privado
    (`tools/apuntes._ModeloQueNoSeUsa`). Se repite aquí —veinte líneas— en vez de compartirlo porque
    moverlo tocaría el comando del motor, y esta tanda tiene prohibido tocar el motor de apuntes;
    cuando alguien haga ese cambio, los dos sitios deben quedar en uno.
    """

    name = "sin-modelo"

    @property
    def version(self) -> str:
        return "sin-modelo"

    @staticmethod
    def _no() -> NoReturn:
        raise RuntimeError("medir un tema no llama al modelo: la medida se hace sobre lo guardado")

    def hechos(self, *_args: object, **_kwargs: object) -> NoReturn:
        self._no()

    def redactar(self, *_args: object, **_kwargs: object) -> NoReturn:
        self._no()

    def comprobar(self, *_args: object, **_kwargs: object) -> NoReturn:
        self._no()

    def anadir(self, *_args: object, **_kwargs: object) -> NoReturn:
        self._no()


class NotesReviewService:
    """Lee los apuntes guardados para revisarlos y guarda la decisión del propietario."""

    def __init__(
        self,
        *,
        profiles: ProfileRepository,
        reviews: SqlAlchemyNotesReviewRepository,
        notes: TopicNotesReader,
        topic_notes: TopicNotesService,
        dossier: DossierService,
        clock: SystemClock | None = None,
    ) -> None:
        self._profiles = profiles
        self._reviews = reviews
        self._notes = notes
        self._topic_notes = topic_notes
        self._dossier = dossier
        self._clock = clock if clock is not None else SystemClock()

    # ------------------------------------------------------------------ la tabla

    def revisar(self) -> RevisionDeApuntes:
        """Los temas del programa activo, con su estado y lo que se sabe **sin medir**.

        La tabla del panel **no mide** los borradores, y eso es una decisión medida: medirlos
        costaba 3,7 s de los 5,37 s que tardaba la pantalla entera (17-oct-2026, copia verificada de
        la base: IV.7 1,86 s e I.4 1,5 s, con el índice de materias y la puerta de forma dentro).
        Lo que la tabla enseña —estado, apartados, hechos, comprobaciones guardadas, incidencias sin
        despachar y la decisión escrita— sale de la base en cinco consultas agregadas y se lee en
        0,03 s.

        La cifra de la puerta **no se hereda ni se inventa**: la ficha del tema la mide al abrirlo,
        y la fila lo dice con la razón `sin_medida` en lugar de enseñar un cero que parecería un
        suspenso. Decidir se decide allí, con el texto delante, así que la medida sigue estando
        donde se toma la decisión.
        """
        filas = self._reviews.topics(self._convocatoria())
        return RevisionDeApuntes(
            counters=contadores(filas),
            topics=tuple(self._tema(fila, informe=None) for fila in filas),
        )

    def contadores_del_menu(self) -> ContadoresDeRevision:
        """Cuántos borradores esperan una decisión. Es el número del menú y no mide nada caro."""
        return self._reviews.counters(self._convocatoria())

    # ------------------------------------------------------------------ la ficha

    def ficha(self, code: str, *, page: int = 1, order: ReviewOrder = "lectura") -> FichaDeRevision:
        """Una **página** de un tema, apartado a apartado, tal como se lee.

        Un código que no existe es un 404. El orden lo pone el servidor porque la página se corta
        aquí: «los peores primero» tiene que ordenar los 25 apartados del tema, no los seis que se
        envían, o el propietario vería primero los peores de la primera hoja y no del tema.

        Se pide **una** página y no todas: los cuerpos de los apartados son el 92 % de la respuesta
        —121 de 131 KiB en IV.7— y el navegador tiene que convertir cada uno a HTML antes de que se
        pueda leer el primero. Con seis apartados por hoja, la ficha baja a unos 40 KiB.
        """
        fila = self._fila(code)
        informe = self._topic_notes.medir(fila.code) if fila.has_notes else None
        apuntes = self._notes.notes_for_node(fila.node_id)
        todas = (
            []
            if apuntes is None
            else [
                _seccion(apartado, posicion)
                for posicion, apartado in enumerate(apuntes.sections, start=1)
            ]
        )
        if order == "peores":
            # Lo que queda sin resolver manda; a igualdad, el orden de lectura, para que dos
            # apartados con la misma cifra no cambien de sitio entre dos visitas.
            todas.sort(key=lambda apartado: (-apartado.peor, apartado.position))
        total = len(todas)
        paginas = max(1, -(-total // SECCIONES_POR_PAGINA))
        elegida = min(max(1, page), paginas)
        desde = (elegida - 1) * SECCIONES_POR_PAGINA
        return FichaDeRevision(
            topic=self._tema(fila, informe=informe),
            sections=tuple(todas[desde : desde + SECCIONES_POR_PAGINA]),
            sections_total=total,
            page=elegida,
            page_size=SECCIONES_POR_PAGINA,
        )

    # ------------------------------------------------------------------ la decisión

    def decidir(
        self,
        code: str,
        *,
        decision: ReviewDecision,
        note: str | None,
        actor: str,
    ) -> ResultadoDeDecision:
        """Aprueba o rechaza los apuntes de un tema, y publica si las dos puertas pasan.

        El orden importa y es el que se ve:

        1. se resuelve el tema y se comprueba que **tiene apuntes** (sin texto no hay nada que
           aprobar, y aprobar un tema vacío publicaría un tema sin leer);
        2. se **normaliza la nota**: un rechazo sin motivo no llega a la base;
        3. se **mide** el tema con lo guardado (`medir`, sin modelo y sin coste);
        4. se escribe la decisión con su evento, por la ruta auditada del repositorio;
        5. **y solo entonces**, si la decisión es aprobar y las dos puertas pasan, se archiva la
           versión con `DossierService.archive`, que es el mismo camino que publica desde el
           comando. Si no pasan, no se toca ninguna versión: el tema queda aprobado, sin publicar y
           con la puerta que lo frena escrita en la respuesta.
        """
        fila = self._fila(code)
        if not fila.has_notes:
            raise InvalidReviewError(
                "este tema todavía no tiene apuntes escritos: no hay nada que aprobar ni rechazar"
            )
        limpia = normalise_decision_note(decision, note)
        informe = self._topic_notes.medir(fila.code)
        self._reviews.save_decision(
            node_id=fila.node_id,
            decision=decision,
            note=limpia,
            actor=actor,
            now=self._clock.now(),
        )
        creada: bool | None = None
        bloqueo: ReviewBlockName | None = None
        if decision is ReviewDecision.APPROVED:
            cifras = self._cifras(fila, informe)
            if cifras.pasa_las_puertas:
                archivado = self._dossier.archive(fila.node_id)
                if archivado is not None:
                    creada = archivado[1]
            else:
                bloqueo = BLOQUEO_POR_COBERTURA if not cifras.pasa_cobertura else BLOQUEO_POR_FORMA
        # Se vuelve a leer la fila para contestar **con lo que ha quedado**: la decisión recién
        # escrita y, si se ha archivado, la versión que la hace «publicado».
        despues = self._fila(code)
        return ResultadoDeDecision(
            topic=self._tema(despues, informe=informe),
            published=despues.published,
            version_created=creada,
            blocked_by=bloqueo,
        )

    # ------------------------------------------------------------------ piezas

    def _convocatoria(self) -> str:
        """La convocatoria del programa que se revisa: la de la **oposición activa** del panel.

        No la del alumno (`settings.student_opposition`): el panel tiene su selector de oposición y
        lo que se revisa es la que está elegida ahí. Sin ninguna activa con convocatoria no hay
        programa del que sacar temas, y se dice qué falta en vez de devolver una tabla vacía.
        """
        for oposicion in self._profiles.list_oppositions():
            if oposicion.active and oposicion.convocation_id is not None:
                return oposicion.convocation_id
        raise UnsupportedError(
            "no hay ninguna oposición activa con convocatoria: sin programa no hay temas que "
            "revisar (elige una oposición en el panel)"
        )

    def _fila(self, code: str) -> ResumenDeTema:
        """La fila de un tema por su código legible, buscándola en la misma lectura que la tabla."""
        node_id = self._reviews.node_id(code)
        if node_id is None:
            raise NotFoundError("tema del programa", code)
        filas = self._reviews.topics(self._convocatoria(), solo_nodo=node_id)
        if not filas:
            raise NotFoundError("tema del programa", code)
        return filas[0]

    def _medir_los_borradores(self, filas: Sequence[ResumenDeTema]) -> dict[str, TopicNotesReport]:
        """Mide **solo** los temas con apuntes que no están publicados, y sin llamar a nadie.

        **Hoy no se llama desde ninguna ruta**: la tabla del panel dejó de medir para poder abrirse
        sin esperar (ver `revisar`). Se queda porque es la pieza que mide «lo que espera una
        decisión» y es la que habría que volver a usar el día que la medida se guarde en la base en
        vez de repetirse en cada visita; borrarla y reescribirla después sería peor.

        Cada tema cuesta entre medio segundo y dos (I.4, con 589 preguntas, es el más caro), y con
        los datos del propietario son **dos**: IV.7 e I.4. Se miden en serie a propósito: se probó a
        medirlos a la vez con cuatro hilos y **no mejora nada** —el trabajo es de Python y no suelta
        el GIL—, así que un `ThreadPoolExecutor` que no gana tiempo sería complejidad sin nada a
        cambio.
        """
        medidos: dict[str, TopicNotesReport] = {}
        for fila in filas:
            if fila.has_notes and not fila.published:
                medidos[fila.node_id] = self._topic_notes.medir(fila.code)
        return medidos

    def _tema(self, fila: ResumenDeTema, *, informe: TopicNotesReport | None) -> TemaEnRevision:
        cifras = self._cifras(fila, informe)
        return TemaEnRevision(
            node_id=fila.node_id,
            code=fila.code,
            title=fila.title,
            block_code=fila.block_code,
            block_title=fila.block_title,
            state=_estado(fila),
            sections_written=fila.sections_written,
            facts=fila.facts,
            checks=fila.checks,
            incidents_open=fila.incidents_open,
            incidents_by_category=tuple(sorted(fila.incidents_by_category.items())),
            version=(
                None
                if fila.version_id is None or fila.version_built_at is None
                else VersionDeTema(id=fila.version_id, built_at=fila.version_built_at)
            ),
            review=fila.review,
            razones=razones_del_tema(cifras),
            medida=informe is not None,
            cobertura=None if informe is None else (cifras.covered, cifras.with_key),
            cobertura_todas_las_claves=(
                None if informe is None else (cifras.covered_all_keys, cifras.with_key_all_keys)
            ),
        )

    @staticmethod
    def _cifras(fila: ResumenDeTema, informe: TopicNotesReport | None) -> CifrasDelTema:
        """Las cifras del motivo: de la medida si la hay y, si no, de lo que dice la tabla.

        Sin medida (un tema publicado en la tabla, o uno sin apartados) la forma **no se declara
        caída**: decir «la forma no pasa» sin haberla medido sería inventarse el motivo.
        """
        cobertura: CoverageReport | None = None if informe is None else informe.coverage
        revision = None if informe is None else informe.revision
        return CifrasDelTema(
            has_sections=fila.has_notes,
            published=fila.published,
            measured=informe is not None,
            covered=0 if cobertura is None else cobertura.preguntas_cubiertas_con_clave_utilizable,
            with_key=0 if cobertura is None else cobertura.preguntas_con_clave_utilizable,
            covered_all_keys=0 if cobertura is None else cobertura.preguntas_cubiertas_con_clave,
            with_key_all_keys=0 if cobertura is None else cobertura.preguntas_con_clave,
            form_passes=revision is None or revision.pasa,
            form_failures=() if revision is None else tuple(h.line() for h in revision.hallazgos),
            sin_frase=(
                0
                if cobertura is None
                else cobertura.por_motivo.get(Motivo.SIN_FRASE_EN_LOS_APUNTES, 0)
            ),
            conflictos=0 if cobertura is None else cobertura.conflicts,
            claves_marcadas=0 if cobertura is None else cobertura.incidencias_clave_marcada,
            sin_materia=0 if informe is None else informe.sin_materia,
            incidencias_abiertas=fila.incidents_open,
            incidencias_por_categoria=tuple(sorted(fila.incidents_by_category.items())),
            decision=None if fila.review is None else fila.review.decision,
            decision_note=None if fila.review is None else fila.review.note,
        )


def _estado(fila: ResumenDeTema) -> NotesState:
    """El estado de los apuntes, con la regla de siempre: apartados escritos y versión archivada."""
    if not fila.has_notes:
        return NotesState.NONE
    return NotesState.PUBLISHED if fila.published else NotesState.DRAFT


def _seccion(apartado: SectionNotes, posicion: int) -> SeccionDeRevision:
    """Un apartado de los apuntes, con lo que se ha comprobado en él.

    El orden de la tupla que devuelve el lector **es el orden de lectura** (viene ordenada por
    posición), y por eso la posición se pasa desde fuera: el panel numera los apartados como los lee
    el alumno, no como los guardó el motor.
    """
    return SeccionDeRevision(
        key=apartado.key,
        title=apartado.title,
        epigraph_code=apartado.epigraph_code,
        anchor=apartado.anchor,
        position=posicion,
        body_markdown=apartado.body_markdown,
        facts_total=apartado.facts_total,
        words=len(apartado.body_markdown.split()),
        covered=apartado.covered,
        gaps=apartado.gaps,
        doubtful=apartado.doubtful,
        conflicts=apartado.conflicts,
        needs_review_reason=apartado.needs_review_reason,
    )


__all__ = [
    "BLOQUEO_POR_COBERTURA",
    "BLOQUEO_POR_FORMA",
    "MedidaSinModelo",
    "NotesReviewService",
]
