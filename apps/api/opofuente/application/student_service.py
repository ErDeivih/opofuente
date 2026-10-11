"""La zona del alumno: lo que se pinta, y nada más (F2).

Este servicio existe para que la capa de rutas no tenga que decidir nada. Tres reglas lo gobiernan,
y las tres vienen del contrato de la fase:

1. **La oposición la fija la configuración, no la petición.** `OPOFUENTE_STUDENT_OPPOSITION` dice
   qué cuerpo se sirve y el filtro vive aquí, en el servidor: la pantalla del alumno no elige
   oposición, así que no hay forma de pedir la de otro.
2. **Solo se devuelve lo que se pinta.** Las vistas que salen de aquí (`StudentOverviewView`,
   `StudentBlockProgressView`, `StudentSessionView`…) no tienen campo para la evidencia, el
   conjunto, la clave, la versión ni la ruta: no se filtran al final, es que no existen.
3. **El progreso es de una persona.** Todo lo que se lee se filtra por el dueño del progreso
   (`owner_id`), que hoy es único y el día que haya cuentas ya estará puesto.

El nombre de un test lo compone **esta** capa —modo y número de preguntas—, nunca el título del
conjunto de origen: el nombre del banco del propietario es justo lo que no puede verse (§3.10).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from opofuente.application.ports import Clock
from opofuente.application.read_models import (
    ConvocationDetail,
    NodeView,
    OppositionSummary,
)
from opofuente.application.student_models import (
    StudentAnswerRequest,
    StudentBlockProgressView,
    StudentCorrectionView,
    StudentEpigraphView,
    StudentMockExamRequest,
    StudentNoteSectionView,
    StudentNotesView,
    StudentOppositionView,
    StudentOptionView,
    StudentOverviewView,
    StudentPartScoreView,
    StudentProgressView,
    StudentQuestionView,
    StudentReportView,
    StudentResultView,
    StudentRunView,
    StudentScoreView,
    StudentSessionView,
    StudentSheetRowView,
    StudentTestRequest,
    StudentTopicProgressView,
    StudentTopicView,
)
from opofuente.application.study_models import (
    PartScoreView,
    SessionQuestionView,
    SessionResultView,
    SessionView,
)
from opofuente.application.study_service import (
    AnswerInput,
    CompositionSpec,
    PartSpec,
    RunnerView,
    StudyService,
)
from opofuente.config import Settings
from opofuente.domain.errors import NotFoundError, UnsupportedError
from opofuente.domain.notes_reports import normalise_reason
from opofuente.domain.profiles import NodeType
from opofuente.domain.study import OWNER_ID_LOCAL, Confidence, Feedback, SessionMode, SessionStatus
from opofuente.domain.topic_notes import NoteSection, NotesState
from opofuente.infrastructure.notes_report_repository import SqlAlchemyNotesReportRepository
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.student_repository import SqlAlchemyStudentRepository
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository

#: Cuántas sesiones se miran para decidir qué está «a medias» y qué entra en el historial. Es una
#: ventana, no un listado: la pantalla enseña una tarjeta y cinco filas.
SESSION_SCAN_LIMIT = 50

#: Cuántos tests terminados entran en el historial de progreso.
HISTORY_LIMIT = 20

#: Cuántos tests terminados entran en Inicio («últimos 5 tests con nota», REDISENO §3.1).
RECENT_TESTS_LIMIT = 5

#: Cuántos temas flojos se destacan (REDISENO §3.9: «los 5 temas más flojos»).
WEAKEST_LIMIT = 5

#: El nombre que se le da a cada modo. Es lo que el alumno lee en su historial; el del conjunto de
#: origen no se usa nunca.
NOMBRES_DE_MODO: dict[str, str] = {
    "practice": "Test",
    "error_review": "Repaso de fallos",
    "official_exam": "Examen oficial",
    "mock_exam": "Simulacro",
    "diagnostic": "Diagnóstico",
}

#: Un código de tema: bloque romano y número, separados por punto o por guion (`IV.10`, `IV-10`).
_CODIGO = re.compile(r"^(?P<bloque>[IVXL]+|[0-9]+)[.\-](?P<tema>[0-9]+)$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class _Cifras:
    """Los recuentos de un nodo del programa, juntos porque se leen juntos.

    `graded` es la suma de los tres desenlaces que puntúan (aciertos, fallos y blancos) y es el
    denominador del porcentaje: sobre las **corregidas**, no sobre las disponibles.
    """

    available: int = 0
    answered: int = 0
    correct: int = 0
    graded: int = 0
    due: int = 0

    @property
    def accuracy(self) -> float | None:
        return None if self.graded == 0 else self.correct / self.graded

    def __add__(self, other: _Cifras) -> _Cifras:
        return _Cifras(
            available=self.available + other.available,
            answered=self.answered + other.answered,
            correct=self.correct + other.correct,
            graded=self.graded + other.graded,
            due=self.due + other.due,
        )


@dataclass(frozen=True, slots=True)
class _Agregado:
    """Las cifras por nodo **y** el total de fallos vencidos, calculados en una sola pasada.

    Van juntos porque el total no se puede deducir de las cifras por nodo: una pregunta que se
    repasa y no está catalogada en ningún tema cuenta para «repasar fallos (N)» y no aparece en
    ningún nodo.
    """

    cifras: dict[str, _Cifras]
    due_total: int


def _numero_de(codigo: str) -> int | None:
    """El número del tema, para ordenar y para enseñar: de `IV.10` sale `10`."""
    ultimo = codigo.rsplit(".", 1)[-1]
    return int(ultimo) if ultimo.isdigit() else None


def _normalizar_codigo(codigo: str) -> str:
    """`iv-10`, `IV-10` y `IV.10` son el mismo tema: el código se sirve en su forma canónica.

    La dirección del alumno puede venir del enlace de una pantalla (`IV.10`) o de una ruta escrita a
    mano (`IV-10`), y las dos tienen que encontrar el tema: si solo valiera una, la mitad de los
    enlaces del temario darían 404 sin motivo.
    """
    coincidencia = _CODIGO.match(codigo.strip().replace(" ", ""))
    if coincidencia is None:
        return codigo.strip().upper()
    return f"{coincidencia.group('bloque').upper()}.{coincidencia.group('tema')}"


class StudentService:
    """Lee el progreso y compone las vistas de la zona del alumno."""

    def __init__(
        self,
        *,
        settings: Settings,
        profiles: SqlAlchemyProfileRepository,
        student: SqlAlchemyStudentRepository,
        study: StudyService,
        clock: Clock,
        notes: SqlAlchemyTopicNotesRepository,
        reports: SqlAlchemyNotesReportRepository,
        owner_id: str = OWNER_ID_LOCAL,
    ) -> None:
        self._settings = settings
        self._profiles = profiles
        self._student = student
        self._study = study
        self._clock = clock
        self._notes = notes
        self._reports = reports
        self._owner_id = owner_id

    @property
    def owner_id(self) -> str:
        return self._owner_id

    # ------------------------------------------------------------------ resolución

    def _opposition(self) -> OppositionSummary:
        """La oposición que sirve esta zona, **por su código** y desde la configuración.

        Es el único sitio donde se decide qué cuerpo se sirve. Si el código configurado no existe,
        se dice qué código es: un 404 sin más dejaría al propietario buscando el fallo en la
        pantalla.
        """
        codigo = self._settings.student_opposition
        for oposicion in self._profiles.list_oppositions():
            if oposicion.code == codigo:
                return oposicion
        raise NotFoundError("oposición del alumno", codigo)

    def _convocation_id(self, oposicion: OppositionSummary) -> str:
        if oposicion.convocation_id is None:
            raise UnsupportedError(
                f"la oposición «{oposicion.code}» no tiene convocatoria: sin programa no hay "
                "temario que enseñar (siembra los perfiles oficiales)"
            )
        return oposicion.convocation_id

    def _publico(self) -> bool:
        return self._settings.public_mode

    def opposition_view(self) -> StudentOppositionView:
        """La oposición servida, para enseñarla: código y nombre, sin identificador."""
        oposicion = self._opposition()
        return StudentOppositionView(code=oposicion.code, name=oposicion.name)

    # ------------------------------------------------------------------ lectura

    def overview(self) -> StudentOverviewView:
        """Inicio: el test a medias, los fallos vencidos y el progreso por bloque."""
        oposicion = self._opposition()
        agregado = self._agregado(oposicion)
        sesiones = self._sesiones(oposicion.id)
        return StudentOverviewView(
            opposition=self.opposition_view(),
            in_progress=self._en_curso(sesiones),
            due_reviews=agregado.due_total,
            blocks=self._bloques(oposicion, agregado),
            recent_tests=tuple(
                self._sesion(vista)
                for vista in sesiones
                if vista.is_finished and vista.result is not None
            )[:RECENT_TESTS_LIMIT],
        )

    def syllabus(self) -> tuple[StudentBlockProgressView, ...]:
        """El temario: bloques y temas en orden numérico, con lo disponible y el acierto."""
        oposicion = self._opposition()
        return self._bloques(oposicion, self._agregado(oposicion))

    def topic(self, codigo: str) -> StudentTopicView:
        """Un tema por su código legible: título, epígrafes, recuentos y progreso."""
        oposicion = self._opposition()
        curriculum = self._curriculum(oposicion)
        buscado = _normalizar_codigo(codigo)
        cifras = self._agregado(oposicion).cifras
        estados = self._student.notes_states()
        for bloque in curriculum:
            if bloque.node_type is not NodeType.BLOCK:
                continue
            for tema in bloque.children:
                if tema.path.upper() != buscado:
                    continue
                datos = self._de(tema, cifras)
                return StudentTopicView(
                    code=tema.path,
                    number=_numero_de(tema.path),
                    title=tema.title,
                    description=tema.description,
                    block_code=bloque.path,
                    block_title=bloque.title,
                    epigraphs=tuple(
                        StudentEpigraphView(code=hijo.path, title=hijo.title)
                        for hijo in tema.children
                    ),
                    progress=self._progreso_del_tema(
                        tema.path, tema.title, datos, self._estado_de(estados, tema.id)
                    ),
                )
        raise NotFoundError("tema del programa", buscado)

    def progress(self) -> StudentProgressView:
        """Progreso: acierto por bloque y por tema, los cinco más flojos e historial."""
        oposicion = self._opposition()
        bloques = self._bloques(oposicion, self._agregado(oposicion))
        return StudentProgressView(
            opposition=self.opposition_view(),
            blocks=bloques,
            weakest_topics=self._mas_flojos(bloques),
            history=tuple(
                self._sesion(vista) for vista in self._sesiones(oposicion.id) if vista.is_finished
            )[:HISTORY_LIMIT],
        )

    # ------------------------------------------------------- los apuntes: leerlos y avisar

    def notes(self, codigo: str) -> StudentNotesView:
        """Los apuntes de un tema, para la pantalla de lectura.

        Un tema **en borrador se sirve igual** que uno publicado: la decisión D2 es que el alumno
        pueda leerlo y que se le diga que está en revisión, no que se le esconda. Lo único que
        cambia es el estado que viaja con el texto, y la pantalla lo pinta.

        Un tema sin apuntes tampoco es un error: devuelve su estado (`none`) y una lista vacía. El
        tema existe —si no, `_nodo_por_codigo` habría lanzado el 404— y lo que falta es el texto.
        """
        oposicion = self._opposition()
        node_id = self._nodo_por_codigo(oposicion, codigo)
        apartados = self._notes.notes_for_node(node_id)
        return StudentNotesView(
            code=_normalizar_codigo(codigo),
            state=self._estado_de(self._student.notes_states(), node_id),
            generated_at=None if apartados is None else apartados.generated_at,
            sections=(
                ()
                if apartados is None
                else tuple(
                    StudentNoteSectionView(
                        key=apartado.key,
                        number=numero,
                        title=apartado.title,
                        epigraph_code=apartado.epigraph_code,
                        anchor=apartado.anchor,
                        body_markdown=apartado.body_markdown,
                        questions_covered=apartado.covered,
                    )
                    for numero, apartado in enumerate(apartados.sections, start=1)
                )
            ),
        )

    def report(self, codigo: str, section_key: str, reason: str) -> StudentReportView:
        """Guarda el aviso del alumno sobre un apartado, por la ruta auditada (D2).

        El anclaje lo pone el **servidor**, no la petición: se busca el apartado por su clave en los
        apuntes del tema y se guarda el anclaje que ese apartado tiene hoy. Si la pantalla mandara
        la dirección, un cliente podría escribir un aviso apuntando a un párrafo que no es el suyo.
        """
        oposicion = self._opposition()
        node_id = self._nodo_por_codigo(oposicion, codigo)
        apartado = self._apartado(node_id, section_key)
        aviso = self._reports.save(
            node_id=node_id,
            owner_id=self._owner_id,
            section_key=apartado.key,
            anchor=apartado.anchor,
            reason=normalise_reason(reason),
            now=self._clock.now(),
        )
        return StudentReportView(
            section_key=aviso.section_key,
            reason=aviso.reason,
            status=aviso.status.value,
            created_at=aviso.created_at,
        )

    def _apartado(self, node_id: str, section_key: str) -> NoteSection:
        """El apartado de ese tema, por su clave.

        Si no está, no existe: un 404 antes que guardar un aviso huérfano apuntando a un párrafo que
        este tema no tiene.
        """
        for apartado in self._notes.sections(node_id):
            if apartado.key == section_key:
                return apartado
        raise NotFoundError("apartado de los apuntes del tema", section_key)

    # ------------------------------------------------------------------ ayudas de lectura

    def _curriculum(self, oposicion: OppositionSummary) -> tuple[NodeView, ...]:
        curriculum = self._profiles.get_curriculum(self._convocation_id(oposicion))
        if curriculum is None:
            raise NotFoundError("programa de la convocatoria", self._convocation_id(oposicion))
        return curriculum.nodes

    def _bloques(
        self, oposicion: OppositionSummary, agregado: _Agregado
    ) -> tuple[StudentBlockProgressView, ...]:
        """El árbol del programa con las cifras de cada nodo.

        Los nodos vienen **ya en orden numérico** de la consulta del programa (`curriculum_order`,
        pieza 1 de F1): aquí no se reordena nada. Reordenar otra vez sería tener dos órdenes que
        pueden divergir, que es exactamente lo que aquel arreglo vino a quitar.
        """
        cifras = agregado.cifras
        estados = self._student.notes_states()
        bloques: list[StudentBlockProgressView] = []
        for bloque in self._curriculum(oposicion):
            if bloque.node_type is not NodeType.BLOCK:
                continue
            temas: list[StudentTopicProgressView] = []
            total = self._de(bloque, cifras)
            for tema in bloque.children:
                datos_tema = self._de(tema, cifras)
                temas.append(
                    self._progreso_del_tema(
                        tema.path, tema.title, datos_tema, self._estado_de(estados, tema.id)
                    )
                )
                total = total + datos_tema
            bloques.append(
                StudentBlockProgressView(
                    code=bloque.path,
                    title=bloque.title,
                    position=bloque.position,
                    available_questions=total.available,
                    answered=total.answered,
                    correct=total.correct,
                    accuracy=total.accuracy,
                    due_reviews=total.due,
                    topics=tuple(temas),
                )
            )
        return tuple(bloques)

    def _agregado(self, oposicion: OppositionSummary) -> _Agregado:
        """Las cifras del progreso, en **una** pasada y para toda la respuesta.

        El total de fallos vencidos viaja con las cifras por nodo porque no se puede sumar de ellas:
        una pregunta que se repasa y no está catalogada en ningún tema cuenta en el total y no está
        en ningún nodo. Calcularlo aparte pedía la misma consulta dos veces por carga de pantalla.
        """
        publico = self._publico()
        disponibles = self._student.question_counts(oposicion.id, public_only=publico)
        vistas = self._student.answered_counts(oposicion.id, self._owner_id, public_only=publico)
        desenlaces = self._student.outcome_counts(oposicion.id, self._owner_id, public_only=publico)
        due_total, vencidos = self._student.due_counts(
            oposicion.id,
            self._owner_id,
            now=self._clock.now(),
            public_only=publico,
        )
        nodos = set(disponibles) | set(vistas) | set(desenlaces) | set(vencidos)
        cifras: dict[str, _Cifras] = {}
        for nodo in nodos:
            recuentos = desenlaces.get(nodo, {})
            correct = recuentos.get("correct", 0)
            cifras[nodo] = _Cifras(
                available=disponibles.get(nodo, 0),
                answered=vistas.get(nodo, 0),
                correct=correct,
                graded=correct + recuentos.get("wrong", 0) + recuentos.get("blank", 0),
                due=vencidos.get(nodo, 0),
            )
        return _Agregado(cifras=cifras, due_total=due_total)

    @staticmethod
    def _de(nodo: NodeView, cifras: dict[str, _Cifras]) -> _Cifras:
        """Las cifras de un nodo. Un bloque sin preguntas propias devuelve ceros, no un hueco."""
        return cifras.get(nodo.id, _Cifras())

    @staticmethod
    def _estado_de(estados: Mapping[str, NotesState], node_id: str) -> str:
        """El estado de los apuntes de un nodo: el que traiga el mapa o «sin apuntes».

        El mapa solo trae los temas con apartados escritos (son tres de treinta y tres), así que lo
        que no está se dice con su valor por defecto en lugar de con un cero por tema.
        """
        return estados.get(node_id, NotesState.NONE).value

    @staticmethod
    def _progreso_del_tema(
        codigo: str, titulo: str, datos: _Cifras, notes_state: str
    ) -> StudentTopicProgressView:
        return StudentTopicProgressView(
            code=codigo,
            number=_numero_de(codigo),
            title=titulo,
            available_questions=datos.available,
            answered=datos.answered,
            correct=datos.correct,
            accuracy=datos.accuracy,
            due_reviews=datos.due,
            notes_state=notes_state,
        )

    def _mas_flojos(
        self, bloques: tuple[StudentBlockProgressView, ...]
    ) -> tuple[StudentTopicProgressView, ...]:
        """Los cinco temas con peor acierto, entre los **empezados**.

        Un tema sin responder no entra: no es un punto débil, es un tema sin empezar, y colarlo
        empujaría fuera al que de verdad hay que repasar. Los que aún no tienen corrección (todo
        respondido con corrección al final) van después de los que sí la tienen, porque su
        porcentaje
        todavía no se puede afirmar.
        """
        empezados = [tema for bloque in bloques for tema in bloque.topics if tema.answered > 0]
        empezados.sort(
            key=lambda tema: (
                tema.accuracy is None,
                tema.accuracy if tema.accuracy is not None else 1.0,
                -tema.answered,
                tema.code,
            )
        )
        return tuple(empezados[:WEAKEST_LIMIT])

    def _sesiones(self, opposition_id: str) -> tuple[SessionView, ...]:
        """Las sesiones de esta persona en esta oposición, de la más nueva a la más vieja.

        Se pide a `StudyService`, que es quien sabe leer una sesión, y su listado ya filtra por
        dueño (F2 §2). Lo que se hace aquí es **no copiar** lo que no se puede enseñar: ni el
        conjunto, ni la clave, ni la etiqueta del banco, que es lo que el servicio de estudio sí
        tiene porque el panel lo necesita.

        En modo público se cae además toda sesión que no se pueda demostrar que sale de conjuntos
        publicables: enseñar su nota sería enseñar, en cifras, lo que pasa dentro de un banco
        privado.
        """
        pagina = self._study.list_sessions(opposition_id=opposition_id, limit=SESSION_SCAN_LIMIT)
        if not self._publico():
            return pagina.sessions
        publicables = self._student.public_set_ids(opposition_id)
        return tuple(
            vista for vista in pagina.sessions if self._de_conjuntos_publicables(vista, publicables)
        )

    @staticmethod
    def _de_conjuntos_publicables(vista: SessionView, publicables: frozenset[str]) -> bool:
        """¿Se puede demostrar que esta sesión sale **solo** de conjuntos publicables?

        Se miran las fuentes congeladas y, si no las hay, el conjunto único de la sesión. Una sesión
        sin ningún conjunto identificable se queda fuera: en modo público, «no se puede demostrar» y
        «no se puede enseñar» son lo mismo.
        """
        fuentes = {fuente.question_set_id for fuente in vista.configuration.sources}
        if not fuentes and vista.question_set_id is not None:
            fuentes = {vista.question_set_id}
        return bool(fuentes) and fuentes <= publicables

    @staticmethod
    def _en_curso(sesiones: tuple[SessionView, ...]) -> StudentSessionView | None:
        """El test «a medias»: el que está en marcha o, si no, el borrador ya empezado.

        Un borrador **sin ninguna respuesta** no se enseña como «continuar»: es una sesión montada y
        no empezada, y ofrecerla como si estuviera a medias hace que el alumno pulse «continuar»
        para
        encontrarse un test que nunca abrió.
        """
        for vista in sesiones:
            if vista.status is SessionStatus.RUNNING:
                return StudentService._sesion(vista)
        for vista in sesiones:
            if vista.status is SessionStatus.DRAFT and vista.answered_questions > 0:
                return StudentService._sesion(vista)
        return None

    # ------------------------------------------------------------------ montar y correr un test

    def create_test(self, request: StudentTestRequest) -> StudentSessionView:
        """Monta un test de los temas elegidos, por la composición declarada de `StudyService`.

        Es fino a propósito: traduce el formulario del alumno a un `CompositionSpec` y no decide
        nada de cómo se corrige. La clave que se congela, la penalización y las reservas salen del
        **mismo** camino que en cualquier otra sesión; si esta capa tuviera su propia composición,
        habría dos verdades sobre cómo se corrige un test.
        """
        if request.count <= 0:
            raise UnsupportedError("un test de cero preguntas no tiene sentido")
        if request.filter not in ("all", "unseen", "failed", "flagged"):
            raise UnsupportedError(
                f"«{request.filter}» no es un filtro de test: se elige entre todas, no vistas, "
                "falladas o dudosas"
            )
        if request.feedback not in ("immediate", "at_end"):
            raise UnsupportedError(
                f"«{request.feedback}» no es una forma de corregir: al momento o al final"
            )
        oposicion = self._opposition()
        if not request.nodes:
            raise UnsupportedError(
                "un test necesita al menos un tema: elige de dónde salen sus preguntas"
            )
        nodos = tuple(self._nodo_por_codigo(oposicion, codigo) for codigo in request.nodes)
        # La parte de test de la convocatoria: es la que dice con qué penalización se corrige el
        # material de estos temas. Sin ella (una convocatoria que no publica ninguna), el test se
        # congela sin parte declarada y se corrige en directo, que es lo honesto.
        parte_del_test = self._parte_de_test(oposicion)
        resultado = self._study.compose(
            CompositionSpec(
                parts=(
                    PartSpec(
                        code=parte_del_test or "test",
                        node_ids=nodos,
                        count=request.count,
                    ),
                ),
                mode=SessionMode.PRACTICE,
                filter=request.filter,  # type: ignore[arg-type]
                owner_id=request.owner_id,
                feedback=Feedback(request.feedback),
                # Un test con tiempo lleva reloj: el límite lo elige quien estudia porque **no** es
                # un examen, y por eso se dice en la etiqueta (en un examen lo fija la
                # convocatoria).
                time_limit_minutes=(
                    StudentService._minutos_de_test(request.count) if request.timed else None
                ),
                label=self._etiqueta_del_test(oposicion, nodos),
            ),
            opposition_id=oposicion.id,
        )
        return StudentService._sesion(resultado.session)

    def create_mock_exam(self, request: StudentMockExamRequest) -> StudentSessionView:
        """Monta el simulacro con el perfil del examen: 80 + 5 y su supuesto de 20 + 5.

        Tres decisiones, y las tres se ven aquí:

        1. **el perfil lo pone la convocatoria**, no el formulario: 80 preguntas de la primera parte
           y 20 del supuesto, con sus 5 reservas cada una, y los 120 minutos del ejercicio;
        2. **el supuesto es el bloque elegido** (III o IV) y solo uno: los dos supuestos son
           excluyentes, y montar los dos sería un simulacro que no existe;
        3. si las preguntas del supuesto salen de los temas del bloque —que es lo que hay—, la
           sesión lo **declara** (`practical_case_origin`): no se llama «supuesto práctico» a veinte
           preguntas de tema sin decirlo.

        La variante corta son 40 preguntas y 48 minutos, sin supuesto: es la del diseño, y su
        etiqueta lo dice porque no es el perfil del examen.
        """
        if request.variant not in ("full", "short"):
            raise UnsupportedError(
                f"«{request.variant}» no es una variante de simulacro: completo o corto"
            )
        if request.case_block not in ("III", "IV"):
            raise UnsupportedError(
                f"«{request.case_block}» no es un bloque de supuesto: se elige III o IV"
            )
        oposicion = self._opposition()
        curriculum = self._curriculum(oposicion)
        temas = self._temas_con_codigo(curriculum)
        if not temas:
            raise UnsupportedError(
                "el programa no tiene temas: sin ellos no hay simulacro que montar"
            )
        bloques = {
            bloque.path.upper(): tuple(tema.id for tema in bloque.children)
            for bloque in curriculum
            if bloque.node_type is NodeType.BLOCK
        }
        del_supuesto = bloques.get(request.case_block.upper(), ())
        if not del_supuesto:
            raise NotFoundError("bloque del programa", request.case_block)

        completo = request.variant == "full"
        partes: tuple[PartSpec, ...]
        if completo:
            partes = (
                PartSpec(
                    code="primera_parte",
                    node_ids=tuple(tema.id for tema in temas),
                    count=80,
                    reserve=5,
                ),
                PartSpec(
                    code="segunda_parte",
                    node_ids=del_supuesto,
                    count=20,
                    reserve=5,
                    alternative_group="supuesto",
                ),
            )
            etiqueta = f"Simulacro con supuesto del bloque {request.case_block.upper()}"
            fuente_del_supuesto: str | None = "bloque"
        else:
            partes = (
                PartSpec(
                    code="primera_parte",
                    node_ids=tuple(tema.id for tema in temas),
                    count=40,
                ),
            )
            etiqueta = "Simulacro corto"
            fuente_del_supuesto = None

        resultado = self._study.compose(
            CompositionSpec(
                parts=partes,
                mode=SessionMode.MOCK_EXAM,
                owner_id=request.owner_id,
                exam_like=True,
                public_only=self._publico(),
                time_limit_minutes=None if completo else 48,
                label=etiqueta,
                note=StudentService._nota_del_simulacro(completo=completo),
                practical_case_origin=fuente_del_supuesto,
            ),
            opposition_id=oposicion.id,
        )
        return StudentService._sesion(resultado.session)

    def run(self, session_id: str) -> StudentRunView:
        """El test en curso: la sesión, la pregunta que toca y la hoja de respuestas entera."""
        sesion = self._sesion_del_alumno(session_id)
        vista = self._study.runner_view(session_id)
        return StudentService._run(vista, sesion)

    def start(self, session_id: str) -> StudentRunView:
        """Arranca el test (arrancar uno que ya corre no cambia nada) y devuelve su estado."""
        self._sesion_del_alumno(session_id)
        self._study.start(session_id)
        return self.run(session_id)

    def answer(self, session_id: str, request: StudentAnswerRequest) -> StudentRunView:
        """Contesta la pregunta de una **posición** de la hoja y devuelve el test como queda.

        La respuesta se pide por la fila de la hoja y no por el identificador de la pregunta: es lo
        que el alumno tiene delante, y así ningún identificador de pregunta sale de esta capa. La
        traducción a la pregunta concreta la hace este método, sobre la composición **congelada** de
        la sesión (no sobre el banco de hoy).
        """
        self._sesion_del_alumno(session_id)
        if request.confidence not in (None, "low", "medium", "high"):
            raise UnsupportedError(
                f"«{request.confidence}» no es una confianza: alta, media o baja"
            )
        vista = self._study.runner_view(session_id)
        pregunta = next(
            (candidata for candidata in vista.questions if candidata.position == request.position),
            None,
        )
        if pregunta is None:
            raise NotFoundError("pregunta del test", str(request.position))
        self._study.answer(
            session_id,
            AnswerInput(
                question_version_id=pregunta.question_version_id,
                chosen_option_keys=request.chosen_option_keys,
                elapsed_ms=request.elapsed_ms,
                confidence=(
                    Confidence(request.confidence) if request.confidence is not None else None
                ),
            ),
        )
        return self.run(session_id)

    def finish(self, session_id: str) -> StudentResultView:
        """Termina el test y devuelve su resultado, con la nota de cada parte."""
        self._sesion_del_alumno(session_id)
        resultado = self._study.finish(session_id)
        return StudentResultView(
            session=StudentService._sesion(self._study.session(session_id)),
            parts=tuple(StudentService._parte(parte) for parte in resultado.parts),
            total=StudentService._parte(resultado.total),
            official_available=resultado.official_available,
            official_note=resultado.official_note,
        )

    # ------------------------------------------------------------------ ayudas del test

    def _parte_de_test(self, oposicion: OppositionSummary) -> str | None:
        """El código de la parte de test de la convocatoria: la que corrige el material de un test.

        El material de los temas es el de la parte de cuestionario de la convocatoria, y su
        penalización (un tercio en TAI) es la que la convocatoria publica para ese material: un test
        que no la aplicara daría una cifra que no es la de este examen. Se elige por lo que publica
        —una parte de test con penalización— y no por su nombre, que cambia de una convocatoria a
        otra. Si no hay ninguna, se devuelve `None` y el test se corrige sin penalización: no se
        inventa la de una parte que no existe.
        """
        convocatoria = self._convocatoria(oposicion)
        for parte in convocatoria.parts:
            if (
                parte.kind == "test"
                and parte.format == "single_choice"
                and parte.wrong_penalty_fraction is not None
            ):
                return parte.code
        return None

    def _convocatoria(self, oposicion: OppositionSummary) -> ConvocationDetail:
        """La convocatoria vigente de la oposición servida."""
        identificador = self._convocation_id(oposicion)
        convocatoria = self._profiles.get_convocation(identificador)
        if convocatoria is None:
            raise NotFoundError("convocatoria", identificador)
        return convocatoria

    def _nodo_por_codigo(self, oposicion: OppositionSummary, codigo: str) -> str:
        """El nodo del programa de un tema, por su código legible (`IV.10` o `IV-10`)."""
        buscado = _normalizar_codigo(codigo)
        for tema in self._temas_con_codigo(self._curriculum(oposicion)):
            if tema.path.upper() == buscado:
                return tema.id
        raise NotFoundError("tema del programa", buscado)

    @staticmethod
    def _temas_con_codigo(curriculum: tuple[NodeView, ...]) -> tuple[NodeView, ...]:
        """Los temas del programa, en orden, saltándose los bloques."""
        return tuple(
            tema
            for bloque in curriculum
            if bloque.node_type is NodeType.BLOCK
            for tema in bloque.children
        )

    def _sesion_del_alumno(self, session_id: str) -> StudentSessionView:
        """La sesión, comprobando que es de la oposición que sirve esta zona.

        Una sesión de otra oposición **no existe** para el alumno: se responde lo mismo que si no
        estuviera, porque decir «es de otro cuerpo» ya sería contarle algo que no le toca. Y en modo
        público tiene que poder demostrarse que sale de conjuntos publicables, que es la misma regla
        con la que se decide qué sesiones se listan.
        """
        oposicion = self._opposition()
        vista = self._study.session(session_id)
        if vista.opposition_id != oposicion.id:
            raise NotFoundError("sesión de estudio", session_id)
        if self._publico() and not self._de_conjuntos_publicables(
            vista, self._student.public_set_ids(oposicion.id)
        ):
            raise NotFoundError("sesión de estudio", session_id)
        return StudentService._sesion(vista)

    def _etiqueta_del_test(self, oposicion: OppositionSummary, nodos: tuple[str, ...]) -> str:
        """De qué es el test: sus temas, en orden, y cuántos son."""
        rutas = {
            nodo.id: (nodo.path or "").strip()
            for nodo in self._temas_con_codigo(self._curriculum(oposicion))
        }
        codigos = [codigo for codigo in (rutas.get(nodo, "") for nodo in nodos) if codigo]
        if not codigos:
            return "Test"
        if len(codigos) <= 3:
            return f"Test de {', '.join(codigos)}"
        return f"Test de {len(codigos)} temas"

    @staticmethod
    def _minutos_de_test(preguntas: int) -> int:
        """El reloj de un test con tiempo: dos minutos por pregunta, redondeado a cinco.

        Es una regla de la aplicación y por eso la sesión lo dice: el tiempo de un examen lo fija la
        convocatoria, y un test con reloj no es un examen.
        """
        return max(5, ((preguntas * 2 + 4) // 5) * 5)

    @staticmethod
    def _nota_del_simulacro(*, completo: bool) -> str:
        """Lo que el simulacro dice de sí mismo: tiene el perfil del examen y no es un examen."""
        perfil = (
            "simulacro con el perfil del examen: primera parte de 80 preguntas más 5 de reserva y "
            "supuesto práctico de 20 más 5, con el tiempo y la penalización de la convocatoria"
            if completo
            else "simulacro corto de 40 preguntas, sin supuesto práctico"
        )
        return (
            f"{perfil}. No es un examen oficial, y su nota por parte es una **estimación** (la "
            "puntuación directa escalada a la banda de cada parte), no la calificación oficial."
        )

    # ------------------------------------------------------------------ traducción a vista

    @staticmethod
    def _titulo(vista: SessionView) -> str:
        """El nombre del test, compuesto por el modo y el número de preguntas.

        No se usa `configuration.context_label` aunque esté ahí: ese campo lo rellena el servicio de
        estudio con el **título del conjunto de origen** para la lista del panel, y el nombre de un
        banco privado del propietario («Rojo -General»…) no puede salir por la zona del alumno
        (REDISENO §3.10 y §3.11).
        """
        nombre = NOMBRES_DE_MODO.get(vista.mode.value, "Test")
        return f"{nombre} · {vista.total_questions} preguntas"

    @staticmethod
    def _sesion(vista: SessionView) -> StudentSessionView:
        return StudentSessionView(
            id=vista.id,
            mode=vista.mode.value,
            status=vista.status.value,
            title=StudentService._titulo(vista),
            total_questions=vista.total_questions,
            answered_questions=vista.answered_questions,
            time_limit_minutes=vista.time_limit_minutes,
            started_at=vista.started_at,
            finished_at=vista.finished_at,
            created_at=vista.created_at,
            result=StudentService._resultado(vista.result),
            practical_case_origin=vista.configuration.practical_case_origin,
        )

    @staticmethod
    def _run(vista: RunnerView, sesion: StudentSessionView) -> StudentRunView:
        """El estado del test en curso, con la hoja de respuestas entera."""
        return StudentRunView(
            session=sesion,
            total=vista.total,
            answered=vista.answered,
            pending=vista.pending,
            finished=vista.finished,
            position=None if vista.current is None else vista.current.position,
            question=None if vista.current is None else StudentService._pregunta(vista.current),
            sheet=tuple(StudentService._fila(pregunta) for pregunta in vista.questions),
        )

    @staticmethod
    def _pregunta(pregunta: SessionQuestionView) -> StudentQuestionView:
        return StudentQuestionView(
            position=pregunta.position,
            is_reserve=pregunta.is_reserve,
            stem=pregunta.stem,
            question_type=pregunta.question_type,
            options=tuple(
                StudentOptionView(key=opcion.stable_key, text=opcion.text)
                for opcion in pregunta.options
            ),
            answered=pregunta.answered,
            chosen_option_keys=tuple(pregunta.chosen_option_keys),
            confidence=None if pregunta.confidence is None else pregunta.confidence.value,
            correction=(
                None
                if pregunta.correction is None
                else StudentCorrectionView(
                    outcome=pregunta.correction.outcome,
                    correct_option_keys=tuple(pregunta.correction.correct_option_keys),
                    reason=pregunta.correction.reason,
                )
            ),
        )

    @staticmethod
    def _fila(pregunta: SessionQuestionView) -> StudentSheetRowView:
        return StudentSheetRowView(
            position=pregunta.position,
            answered=pregunta.answered,
            chosen_option_keys=tuple(pregunta.chosen_option_keys),
            confidence=None if pregunta.confidence is None else pregunta.confidence.value,
            outcome=None if pregunta.correction is None else pregunta.correction.outcome,
            correct_option_keys=(
                ()
                if pregunta.correction is None
                else tuple(pregunta.correction.correct_option_keys)
            ),
        )

    @staticmethod
    def _parte(parte: PartScoreView) -> StudentPartScoreView:
        return StudentPartScoreView(
            part_code=parte.part_code,
            part_name=parte.part_name,
            kind=parte.kind,
            correct=parte.correct,
            wrong=parte.wrong,
            blank=parte.blank,
            score=parte.score.fraction,
            score_decimal=parte.score.decimal,
            score_max=parte.score_max,
            pass_score=parte.pass_score,
            passed=parte.passed,
            verdict_note=parte.verdict_note,
        )

    @staticmethod
    def _resultado(resultado: SessionResultView | None) -> StudentScoreView | None:
        if resultado is None:
            return None
        total = resultado.total
        return StudentScoreView(
            correct=total.correct,
            wrong=total.wrong,
            blank=total.blank,
            points=total.score.fraction,
            points_decimal=total.score.decimal,
            maximum=total.score_max,
            passed=total.passed,
        )
