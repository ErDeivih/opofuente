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
from collections.abc import Mapping, Sequence
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
    StudentMistakesView,
    StudentMistakeTopicView,
    StudentMistakeView,
    StudentMockCaseBlockView,
    StudentMockCaseTopicView,
    StudentMockExamPartView,
    StudentMockExamPlanView,
    StudentMockExamRequest,
    StudentMockExamVariantView,
    StudentNoteAnchorView,
    StudentNoteChapterSectionView,
    StudentNoteChapterView,
    StudentNoteSectionView,
    StudentNotesView,
    StudentOfficialExamsView,
    StudentOfficialExamView,
    StudentOppositionView,
    StudentOptionView,
    StudentOverviewView,
    StudentPartScoreView,
    StudentProgressView,
    StudentQuestionView,
    StudentReportView,
    StudentResultQuestionView,
    StudentResultTopicView,
    StudentResultView,
    StudentRunView,
    StudentScoreView,
    StudentSessionResultView,
    StudentSessionView,
    StudentSheetRowView,
    StudentTestCountView,
    StudentTestPlanView,
    StudentTestRequest,
    StudentTopicProgressView,
    StudentTopicRefView,
    StudentTopicView,
)
from opofuente.application.study_models import (
    PartScoreView,
    ScoreView,
    SessionQuestionView,
    SessionResultView,
    SessionView,
)
from opofuente.application.study_service import (
    AnswerInput,
    CompositionSpec,
    CreateSessionInput,
    PartSpec,
    RunnerView,
    SourceInput,
    StudyService,
)
from opofuente.config import Settings
from opofuente.domain.errors import NotFoundError, UnsupportedError
from opofuente.domain.key_reliability import KeyReliability
from opofuente.domain.notes_reports import normalise_reason
from opofuente.domain.profiles import ExamPart, NodeType
from opofuente.domain.study import (
    OWNER_ID_LOCAL,
    Confidence,
    Feedback,
    SessionMode,
    SessionStatus,
    exact_fraction,
)
from opofuente.domain.topic_notes import NoteSection, NotesState, SectionNotes
from opofuente.infrastructure.notes_report_repository import SqlAlchemyNotesReportRepository
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.student_repository import (
    OfficialExamRow,
    SqlAlchemyStudentRepository,
)
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

#: Cuántas preguntas falladas entran en la lista de fallos. Es una página, no un listado: los
#: totales que la enmarcan se cuentan aparte y sobre todos los fallos.
MISTAKES_LIMIT = 50

#: La parte del examen que corrige el material de un cuestionario: la que publica la penalización.
#: Es la misma que usa el motor para un test, y aquí sirve para saber con qué se corregirá un examen
#: oficial importado.
PARTE_DE_CUESTIONARIO = "primera_parte"

#: La parte del supuesto práctico del simulacro completo.
PARTE_DEL_SUPUESTO = "segunda_parte"

#: Los desenlaces que esta capa puede pronunciar. `annulled`, `excluded` y `conflicting` no son
#: fallos ni aciertos: la plantilla no corrige esa pregunta, y decirlo con `void` es más honesto que
#: contarla como blanco o como error.
OUTCOMES_DE_ALUMNO: frozenset[str] = frozenset({"correct", "wrong", "blank"})

#: La variante corta del simulacro: 40 preguntas y 48 minutos. Son cifras de la **aplicación**,
#: no de la convocatoria, y por eso la variante se llama «corto» y lo dice: no es el perfil.
SIMULACRO_CORTO_PREGUNTAS = 40
SIMULACRO_CORTO_MINUTOS = 48

#: Los bloques de los que se puede elegir el supuesto práctico (el perfil de TAI publica dos).
BLOQUES_DEL_SUPUESTO: frozenset[str] = frozenset({"III", "IV"})

#: Los tamaños de test que ofrece la pantalla de Tests (F22). Son de la **aplicación** —la
#: convocatoria no publica tamaños de test— y el 20 está porque es el del atajo «Test rápido de 20»
#: de Inicio, que ya existía y apunta a esta pantalla.
TAMANOS_DE_TEST: tuple[int, ...] = (10, 20, 25, 50, 100)

#: La nota que acompaña al reloj de un test. Va con el plan y no en la pantalla para que la regla
#: del reloj se lea de un solo sitio: el mismo del que salen los minutos.
NOTA_DEL_RELOJ = (
    "El reloj de un test lo pone la aplicación —dos minutos por pregunta, redondeado a cinco—. El "
    "tiempo de un examen lo fija la convocatoria, y es el que lleva un test cuando no se le pone "
    "el reloj del test."
)

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


@dataclass(frozen=True, slots=True)
class _CapituloLeido:
    """Un capítulo de los apuntes ya repartido: su identidad y los apartados que le tocan.

    `apartados` son las vistas **con su texto** —las del capítulo que se va a leer— y `indice` la
    misma lista sin él, que es lo que viaja con los demás capítulos para que la pantalla pueda
    enseñar el índice entero.
    """

    code: str
    title: str
    position: int
    apartados: tuple[StudentNoteSectionView, ...]

    @property
    def indice(self) -> StudentNoteChapterView:
        return StudentNoteChapterView(
            code=self.code,
            title=self.title,
            position=self.position,
            sections=tuple(
                StudentNoteChapterSectionView(
                    key=apartado.key,
                    number=apartado.number,
                    title=apartado.title,
                    anchor=apartado.anchor,
                    questions_covered=apartado.questions_covered,
                )
                for apartado in self.apartados
            ),
        )


def _leer_por_capitulos(
    tema: NodeView, apartados: tuple[SectionNotes, ...]
) -> tuple[_CapituloLeido, ...]:
    """Reparte los apartados de un tema en sus **epígrafes oficiales**, en orden de lectura.

    Los capítulos y su orden salen del **programa** (`tema.children`, los epígrafes oficiales); los
    apartados, de los apuntes, cada uno en el epígrafe que tiene guardado. El número del apartado es
    su lugar en el tema entero (1..N) y no se reinicia en cada capítulo: es el número con el que se
    cita un apartado y el que sale en el índice completo, que es el mismo en todas las pantallas.

    Dos casos límite que no pueden perder texto:

    - un apartado cuyo epígrafe **no es** un epígrafe del programa (el programa se reorganizó y los
      apuntes se quedaron con el código viejo) abre su propio capítulo al final, titulado con su
      código. Es feo, pero perder el párrafo es peor;
    - un apartado **sin** código de epígrafe cae en un capítulo que es el tema, con su título. Hoy
      no hay ninguno de los dos casos (medido sobre los 29 temas con apuntes: 0 apartados fuera de
      su programa), y por eso el camino está escrito pero no probado con datos: se prueba con los
      suyos.
    """
    if not apartados:
        return ()

    numeros = {apartado.key: numero for numero, apartado in enumerate(apartados, start=1)}
    oficiales = [hijo for hijo in tema.children if hijo.node_type is NodeType.EPIGRAPH]
    titulos = {epigrafe.path: epigrafe.title for epigrafe in oficiales}
    orden = {epigrafe.path: posicion for posicion, epigrafe in enumerate(oficiales, start=1)}

    por_codigo: dict[str, list[SectionNotes]] = {}
    for apartado in apartados:
        por_codigo.setdefault(apartado.epigraph_code, []).append(apartado)

    # El orden es el del programa; lo que no está en el programa va detrás, por orden de aparición.
    codigos = [epigrafe.path for epigrafe in oficiales if epigrafe.path in por_codigo]
    codigos.extend(codigo for codigo in por_codigo if codigo not in orden)

    leidos: list[_CapituloLeido] = []
    for posicion, codigo in enumerate(codigos, start=1):
        suyos = tuple(
            StudentNoteSectionView(
                key=apartado.key,
                number=numeros[apartado.key],
                title=apartado.title,
                epigraph_code=apartado.epigraph_code,
                anchor=apartado.anchor,
                body_markdown=apartado.body_markdown,
                questions_covered=apartado.covered,
            )
            for apartado in por_codigo[codigo]
        )
        leidos.append(
            _CapituloLeido(
                code=codigo,
                title=titulos.get(codigo) or codigo or tema.title,
                position=posicion,
                apartados=suyos,
            )
        )
    return tuple(leidos)


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
            tests_finished=self._tests_hechos(oposicion),
        )

    # ------------------------------------------------------- los apuntes: leerlos y avisar

    def notes(self, codigo: str, capitulo: str | None = None) -> StudentNotesView:
        """Los apuntes de un tema, **un capítulo cada vez**, para la pantalla de lectura.

        Un tema **en borrador se sirve igual** que uno publicado: la decisión D2 es que el alumno
        pueda leerlo y que se le diga que está en revisión, no que se le esconda. Lo único que
        cambia es el estado que viaja con el texto, y la pantalla lo pinta.

        Un tema sin apuntes tampoco es un error: devuelve su estado (`none`) y una lista vacía. El
        tema existe —si no, `_nodo_por_codigo` habría lanzado el 404— y lo que falta es el texto.

        **Por qué un capítulo y no el tema entero.** Un tema del programa son varios epígrafes
        oficiales y cada uno tiene sus apartados. Servirlos todos de una vez es lo que hacía que I.1
        midiera 314.000 px de alto y que el índice (1.405 px, `sticky`, en una ventana de 800) no se
        pudiera recorrer entero. Con `capitulo` se elige el epígrafe, `sections` trae **solo** sus
        apartados con su texto, y `chapters` trae el índice completo **sin los textos**, que es lo
        que la pantalla necesita para el índice y para saber a qué capítulo pertenece un anclaje.

        Un `capitulo` que no existe **no es un 404**: se sirve el primero y el campo `chapter` dice
        cuál se sirvió de verdad, para que la pantalla corrija la dirección. Un enlace guardado a un
        epígrafe que el programa reorganizó tiene que llevar a leer, no a un error.
        """
        oposicion = self._opposition()
        tema = self._tema_por_codigo(oposicion, codigo)
        apuntes = self._notes.notes_for_node(tema.id)
        leidos = _leer_por_capitulos(tema, () if apuntes is None else apuntes.sections)
        servido = next((leido for leido in leidos if leido.code == capitulo), None)
        if servido is None and leidos:
            servido = leidos[0]
        return StudentNotesView(
            code=_normalizar_codigo(codigo),
            state=self._estado_de(self._student.notes_states(), tema.id),
            generated_at=None if apuntes is None else apuntes.generated_at,
            sections=() if servido is None else servido.apartados,
            chapter=None if servido is None else servido.code,
            chapters=tuple(leido.indice for leido in leidos),
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

    def test_plan(self) -> StudentTestPlanView:
        """Qué puede elegir el alumno antes de montar un test, con lo que dura cada tamaño (F22).

        Lo que se sirve es lo que la pantalla necesita para no inventarse nada: los tamaños que
        ofrece la aplicación, los minutos que le pondría el reloj a cada uno y el tiempo que lleva
        el test **sin** reloj —el de la parte del perfil con la que se corrige este material—.

        Los minutos del reloj salen de `_minutos_de_test`, la **misma** regla con la que
        `create_test` pone el reloj de la sesión; y el tiempo sin reloj sale de la convocatoria, que
        es de donde lo toma la composición cuando no se le pide otro. Se enseña porque es una cifra
        que sorprende: medido en la base, un test de diez preguntas sin reloj no se queda sin
        tiempo, se queda con los 120 minutos del ejercicio.
        """
        oposicion = self._opposition()
        convocatoria = self._convocatoria(oposicion)
        parte_del_test = self._parte_de_test(oposicion)
        parte = (
            None
            if parte_del_test is None
            else StudentService._parte_del_perfil(convocatoria, parte_del_test)
        )
        return StudentTestPlanView(
            counts=tuple(
                StudentTestCountView(
                    questions=tamano,
                    minutes=StudentService._minutos_de_test(tamano),
                )
                for tamano in TAMANOS_DE_TEST
            ),
            timed_note=NOTA_DEL_RELOJ,
            # El tiempo de la parte, con la regla del motor: si la parte no lo declara, lo declara
            # el grupo que la contiene (en TAI, los 120 minutos están en el ejercicio único). Se usa
            # el mismo ayudante que el plan del simulacro, que ya está atado a la sesión por prueba.
            convocation_minutes=(
                None if parte is None else StudentService._tiempo_de_parte(convocatoria, parte)
            ),
        )

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
        return StudentService._run(vista, sesion, self._en_revision(vista), self._derivadas(vista))

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

    # --------------------------------------------------- el resultado: qué fallaste y de qué (F14)

    def result(self, session_id: str) -> StudentSessionResultView:
        """El resultado de un test terminado, pregunta a pregunta y **por tema**.

        Solo de un test terminado: el resultado se calcula al cerrar la sesión, y una pantalla de
        resultado con la mitad de las preguntas sin corregir sería una pantalla a medias sin
        decirlo.
        El motor lo comprueba antes (`result`), así que el error que sale dice que hay que
        terminarlo.

        Las preguntas se piden a la **revisión** de la sesión, que es donde vive la corrección
        congelada
        con la plantilla de ese día: recalcular aquí con la plantilla de hoy cambiaría lo que el
        alumno
        vio, y la puntuación que se enseña es la que se guardó al cerrar.
        """
        oposicion = self._opposition()
        self._sesion_del_alumno(session_id)
        calculado = self._study.result(session_id)
        revision = self._study.review(session_id)
        sesion = StudentService._sesion(self._study.session(session_id))
        catalogo = self._catalogo_de_temas(oposicion)
        temas = self._temas_de_preguntas(
            [entrada.question_version_id for entrada in revision.entries], catalogo
        )
        partes = {
            parte.code: parte.name for parte in self._convocatoria(oposicion).parts if parte.name
        }
        en_revision = self._study.key_reliability_of(
            [entrada.question_version_id for entrada in revision.entries]
        )
        derivadas = self._study.derived_key_questions(
            [entrada.question_version_id for entrada in revision.entries]
        )
        anclas = self._anclas_de_apuntes(
            [entrada.question_version_id for entrada in revision.entries], catalogo
        )
        preguntas = tuple(
            StudentService._pregunta_corregida(
                entrada,
                partes,
                temas,
                frozenset(
                    pregunta_id
                    for pregunta_id, veredicto in en_revision.items()
                    if veredicto == KeyReliability.DUDOSA.value
                ),
                derivadas,
                anclas,
            )
            for entrada in revision.entries
        )
        return StudentSessionResultView(
            session=sesion,
            parts=tuple(StudentService._parte(parte) for parte in calculado.parts),
            total=StudentService._parte(calculado.total),
            official_available=calculado.official_available,
            official_note=calculado.official_note,
            duration_seconds=StudentService._duracion(sesion),
            questions=preguntas,
            topics=StudentService._desglose_por_tema(preguntas),
        )

    # --------------------------------------------------- el simulacro antes de montarlo (F14)

    def mock_exam_plan(self) -> StudentMockExamPlanView:
        """Qué va a caer en el simulacro, **antes** de montarlo.

        Todo lo que se enseña sale del perfil del examen: las partes con sus preguntas ordinarias y
        sus
        reservas, la banda de puntuación, el mínimo, la penalización y el tiempo. Lo que el perfil
        no
        publica va en `None`, que es distinto de cero; y **no se añade nada** que la convocatoria no
        diga: si mañana cambia el perfil, esta pantalla cambia con él.

        La variante corta **no es el examen**, y lo dice: sus 40 preguntas y sus 48 minutos son de
        la
        aplicación, no de la convocatoria.
        """
        oposicion = self._opposition()
        convocatoria = self._convocatoria(oposicion)
        cifras = self._agregado(oposicion).cifras
        curriculum = self._curriculum(oposicion)

        primera = StudentService._parte_del_perfil(convocatoria, PARTE_DE_CUESTIONARIO)
        supuesto = StudentService._parte_del_perfil(convocatoria, PARTE_DEL_SUPUESTO)
        completas = tuple(
            StudentService._plan_de_parte(convocatoria, parte)
            for parte in (primera, supuesto)
            if parte is not None
        )
        corta = (
            ()
            if primera is None
            else (StudentService._plan_de_parte(convocatoria, primera, corta=True),)
        )
        return StudentMockExamPlanView(
            opposition=self.opposition_view(),
            full=StudentMockExamVariantView(
                variant="full",
                title="Simulacro completo",
                time_limit_minutes=(
                    None
                    if primera is None
                    else StudentService._tiempo_de_parte(convocatoria, primera)
                ),
                parts=completas,
                note=StudentService._nota_del_simulacro(completo=True),
            ),
            short=StudentMockExamVariantView(
                variant="short",
                title="Simulacro corto",
                time_limit_minutes=SIMULACRO_CORTO_MINUTOS,
                parts=corta,
                note=StudentService._nota_del_simulacro(completo=False),
            ),
            case_blocks=tuple(
                StudentMockCaseBlockView(
                    code=bloque.path,
                    title=bloque.title,
                    topics=tuple(
                        StudentMockCaseTopicView(
                            code=tema.path,
                            title=tema.title,
                            available_questions=StudentService._de(tema, cifras).available,
                        )
                        for tema in bloque.children
                    ),
                )
                for bloque in curriculum
                if bloque.node_type is NodeType.BLOCK
                and bloque.path.upper() in BLOQUES_DEL_SUPUESTO
            ),
        )

    # --------------------------------------------------- los exámenes oficiales (F14)

    def official_exams(self) -> StudentOfficialExamsView:
        """Los exámenes oficiales importados de esta oposición.

        Hoy no hay ninguno importado (su importación es otro bloque) y la lista sale **vacía**, no
        inventada: no se rellenan con bancos de práctica ni con las sesiones ya hechas, porque
        llamar
        «examen oficial» a otra cosa es justo lo que no se puede hacer. La pantalla, con una lista
        vacía, dice que todavía no hay exámenes oficiales importados.

        `position` es la dirección del alumno en esa lista (el primero, el segundo): la zona del
        alumno
        no enseña de dónde salen las preguntas de un test (F2 §4), así que un examen se pide por su
        sitio, como una fila de la hoja de respuestas.
        """
        return StudentOfficialExamsView(
            exams=tuple(
                StudentOfficialExamView(
                    position=posicion,
                    title=fila.title,
                    held_at=fila.held_at,
                    questions=fila.questions,
                    ready=fila.ready,
                    origin_scope=fila.origin_scope,
                )
                for posicion, fila in enumerate(self._examenes_oficiales(), start=1)
            )
        )

    def create_official_exam(self, position: int) -> StudentSessionView:
        """Monta el examen oficial que ocupa esa posición de la lista.

        Se corrige como el cuestionario de la convocatoria —su penalización y su tiempo— y se cierra
        al terminar, como un examen: la corrección mientras se contesta filtraría la solución.
        """
        oposicion = self._opposition()
        examenes = self._examenes_oficiales()
        if position < 1 or position > len(examenes):
            raise NotFoundError("examen oficial", str(position))
        examen = examenes[position - 1]
        if not examen.ready:
            raise UnsupportedError(
                "ese examen todavía no se puede hacer: le falta la plantilla con la que se corrige"
            )
        parte = self._parte_de_test(oposicion)
        if parte is None:
            raise UnsupportedError(
                "la convocatoria no publica cómo se corrige el cuestionario: sin esa regla no se "
                "puede montar un examen oficial"
            )
        vista = self._study.create_session(
            CreateSessionInput(
                opposition_id=oposicion.id,
                mode=SessionMode.OFFICIAL_EXAM,
                sources=(SourceInput(question_set_id=examen.question_set_id, part_code=parte),),
            )
        )
        return StudentService._sesion(vista)

    # --------------------------------------------------- los fallos (F14)

    def mistakes(self) -> StudentMistakesView:
        """Las preguntas que falló la última vez que las contestó, con su tema y sus fallos.

        De aquí sale un test: los temas que aparecen con sus fallos se le pueden pedir a la ruta que
        monta un test con el filtro de falladas, que **vuelve a elegir** sobre los intentos de
        verdad
        en lugar de sobre esta lista. La lista es para mirar y entender; el test lo compone el
        motor.
        """
        oposicion = self._opposition()
        fallos = self._student.mistakes(
            oposicion.id,
            self._owner_id,
            now=self._clock.now(),
            public_only=self._publico(),
            limit=MISTAKES_LIMIT,
        )
        catalogo = self._catalogo_de_temas(oposicion)
        referencias = self._temas_de_preguntas(
            [fila.question_version_id for fila in fallos.rows], catalogo
        )
        return StudentMistakesView(
            total=fallos.total,
            due_total=fallos.due_total,
            questions=tuple(
                StudentMistakeView(
                    stem=fila.stem,
                    topics=referencias.get(fila.question_version_id, ()),
                    last_failed_at=fila.last_failed_at,
                    times_failed=fila.times_failed,
                    due=fila.due,
                )
                for fila in fallos.rows
            ),
            topics=tuple(
                StudentMistakeTopicView(
                    code=tema.path,
                    title=tema.title,
                    failed=fallos.topics[tema.id][0],
                    due=fallos.topics[tema.id][1],
                )
                # El orden es el del programa, no el de un diccionario: los bloques y los temas se
                # leen como se leen en el temario.
                for tema in self._temas_con_codigo(self._curriculum(oposicion))
                if tema.id in fallos.topics
            ),
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
        return self._tema_por_codigo(oposicion, codigo).id

    def _tema_por_codigo(self, oposicion: OppositionSummary, codigo: str) -> NodeView:
        """El tema del programa, entero: hace falta su `children` para leerlo por capítulos.

        Los capítulos de los apuntes son los **epígrafes oficiales** del tema, y su título y su
        orden viven en el programa, no en `topic_note_sections` (que solo guarda el código del
        epígrafe al que pertenece cada apartado). Sin el nodo no se puede titular un capítulo.
        """
        buscado = _normalizar_codigo(codigo)
        for tema in self._temas_con_codigo(self._curriculum(oposicion)):
            if tema.path.upper() == buscado:
                return tema
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

    # ------------------------------------------------------ ayudas del simulacro y del resultado

    @staticmethod
    def _parte_del_perfil(convocatoria: ConvocationDetail, code: str) -> ExamPart | None:
        """La parte del perfil del examen con ese código, si la convocatoria la publica.

        `None` cuando no está: un perfil que no la declara no se completa a mano. La ausencia se
        enseña como ausencia, y el motor montará el simulacro con lo que sí haya.
        """
        for parte in convocatoria.parts:
            if parte.code == code:
                return parte
        return None

    @staticmethod
    def _tiempo_de_parte(convocatoria: ConvocationDetail, parte: ExamPart) -> int | None:
        """El tiempo de una parte: el suyo y, si ella no lo dice, el del grupo que la contiene.

        Es la regla que aplica el motor al montar la sesión (en TAI los 120 minutos están en el
        ejercicio único, no en cada parte) y esta pantalla la necesita **antes** de montar nada. Que
        las dos coincidan no se deja al cuidado de nadie: hay una prueba que monta el simulacro y
        comprueba que el tiempo que prometía el plan es el que tiene la sesión.
        """
        if parte.time_minutes is not None:
            return parte.time_minutes
        if parte.parent_code is None:
            return None
        padre = StudentService._parte_del_perfil(convocatoria, parte.parent_code)
        return None if padre is None else padre.time_minutes

    @staticmethod
    def _plan_de_parte(
        convocatoria: ConvocationDetail, parte: ExamPart, *, corta: bool = False
    ) -> StudentMockExamPartView:
        """Una parte del simulacro tal como se anuncia: con lo que publica el perfil y nada más.

        En la variante corta se anuncian las 40 preguntas de la aplicación y su tiempo, y **no** sus
        reservas: la variante corta no lleva ninguna, y decir «5 de reserva» sería prometer
        preguntas
        que no van a caer.
        """
        return StudentMockExamPartView(
            code=parte.code,
            name=parte.name,
            ordinary_items=SIMULACRO_CORTO_PREGUNTAS if corta else parte.ordinary_items,
            reserve_items=None if corta else parte.reserve_items,
            score_max=parte.score_max,
            pass_score=parte.pass_score,
            penalty=StudentService._penalizacion_de(parte),
            time_minutes=(
                SIMULACRO_CORTO_MINUTOS
                if corta
                else StudentService._tiempo_de_parte(convocatoria, parte)
            ),
        )

    @staticmethod
    def _penalizacion_de(parte: ExamPart) -> str | None:
        """La penalización publicada, como fracción legible (`1/3`). `None` si no publica ninguna.

        Se lee del perfil y se enseña con la misma aritmética exacta que usa la corrección: un
        tercio
        no es `0.3333`, y la pantalla no puede decir una cifra y corregir con otra.
        """
        if parte.wrong_penalty_fraction is None:
            return None
        return ScoreView(exact_fraction(parte.wrong_penalty_fraction)).fraction

    def _examenes_oficiales(self) -> tuple[OfficialExamRow, ...]:
        """Los exámenes oficiales importados, ya filtrados por lo que esta zona puede enseñar."""
        return self._student.official_exams(self._opposition().id, public_only=self._publico())

    def _catalogo_de_temas(self, oposicion: OppositionSummary) -> dict[str, tuple[int, str, str]]:
        """Los temas del programa por su identificador: `{nodo: (orden, código, título)}`.

        El orden es el del programa y sirve para ordenar los temas de una pregunta: una pregunta con
        dos temas (D7) se lee siempre en el mismo orden, y no en el que devuelva la consulta.
        """
        return {
            tema.id: (posicion, tema.path, tema.title)
            for posicion, tema in enumerate(self._temas_con_codigo(self._curriculum(oposicion)))
        }

    def _temas_de_preguntas(
        self,
        preguntas: Sequence[str],
        catalogo: Mapping[str, tuple[int, str, str]],
    ) -> dict[str, tuple[StudentTopicRefView, ...]]:
        """De qué temas es cada pregunta, en el orden del programa.

        Un tema que no esté en el catálogo se cae en silencio: es un mapeo a un nodo de otra
        convocatoria, y enseñarlo sería dar una dirección que en esta zona no lleva a ningún sitio.
        """
        if not preguntas:
            return {}
        mapeos = self._student.topics_of_questions(list(preguntas))
        devueltos: dict[str, tuple[StudentTopicRefView, ...]] = {}
        for pregunta, nodos in mapeos.items():
            ordenados = sorted(
                (catalogo[nodo] for nodo in nodos if nodo in catalogo), key=lambda fila: fila[0]
            )
            if ordenados:
                devueltos[pregunta] = tuple(
                    StudentTopicRefView(code=codigo, title=titulo)
                    for _, codigo, titulo in ordenados
                )
        return devueltos

    @staticmethod
    def _pregunta_corregida(
        entrada: SessionQuestionView,
        partes: Mapping[str, str],
        temas: Mapping[str, tuple[StudentTopicRefView, ...]],
        en_revision: frozenset[str] = frozenset(),
        derivadas: frozenset[str] = frozenset(),
        anclas: Mapping[str, StudentNoteAnchorView] = {},
    ) -> StudentResultQuestionView:
        """Una pregunta de la revisión, con su corrección y sin nada que no se pueda enseñar."""
        correccion = entrada.correction
        return StudentResultQuestionView(
            position=entrada.position,
            is_reserve=entrada.is_reserve,
            part_code=entrada.part_code,
            part_name=None if entrada.part_code is None else partes.get(entrada.part_code),
            stem=entrada.stem,
            options=tuple(
                StudentOptionView(key=opcion.stable_key, text=opcion.text)
                for opcion in entrada.options
            ),
            chosen_option_keys=tuple(entrada.chosen_option_keys),
            correct_option_keys=(
                () if correccion is None else tuple(correccion.correct_option_keys)
            ),
            outcome=StudentService._outcome(correccion.outcome if correccion else None),
            elapsed_ms=entrada.elapsed_ms,
            topics=temas.get(entrada.question_version_id, ()),
            in_review=entrada.question_version_id in en_revision,
            derived_key=entrada.question_version_id in derivadas,
            note_anchor=anclas.get(entrada.question_version_id),
        )

    def _anclas_de_apuntes(
        self,
        preguntas: Sequence[str],
        catalogo: Mapping[str, tuple[int, str, str]],
    ) -> dict[str, StudentNoteAnchorView]:
        """El apartado de los apuntes que contesta cada pregunta, ya con su **código de tema**.

        Dos reglas de la casa, las mismas que usa `_temas_de_preguntas`:

        - un ancla de un nodo que **no está en el catálogo de esta convocatoria** se cae en
          silencio: es un mapeo a un nodo de otro programa, y el enlace no llevaría a nada;
        - si la pregunta tiene ancla en **dos** temas (D7), manda el primero **en el orden del
          programa**, que es el mismo orden en que se enseñan sus temas. Elegirlo al azar daría un
          enlace distinto en cada carga.

        Y el **capítulo** viaja con el ancla: los apuntes se leen por epígrafes oficiales, así que
        decir solo `#osi-capas` no basta —ese apartado vive en `IV.7.2`, y la página abriría el
        primero—. Es el fallo que se midió en el recorrido: `scrollY = 0` con el apartado a
        10.288 px.
        """
        if not preguntas:
            return {}
        mapeos = self._student.note_anchors_of_questions(list(preguntas))
        devueltas: dict[str, StudentNoteAnchorView] = {}
        for pregunta, anclas in mapeos.items():
            candidatas = sorted(
                (
                    (catalogo[nodo][0], catalogo[nodo][1], ancla, epigrafe)
                    for nodo, ancla, epigrafe in anclas
                    if nodo in catalogo
                ),
                key=lambda fila: fila[0],
            )
            if candidatas:
                _, codigo, ancla, epigrafe = candidatas[0]
                devueltas[pregunta] = StudentNoteAnchorView(
                    topic_code=codigo, anchor=ancla, epigraph_code=epigrafe
                )
        return devueltas

    @staticmethod
    def _outcome(desenlace: str | None) -> str:
        """El desenlace, en el vocabulario de esta capa.

        Una pregunta que la plantilla no corrige (anulada, sin entrada o en conflicto) no es un
        blanco ni un fallo del alumno: se dice `void`, que es lo que la pantalla enseña como «no se
        corrige».
        """
        if desenlace is None:
            return "void"
        return desenlace if desenlace in OUTCOMES_DE_ALUMNO else "void"

    @staticmethod
    def _desglose_por_tema(
        preguntas: Sequence[StudentResultQuestionView],
    ) -> tuple[StudentResultTopicView, ...]:
        """Cómo fue el test en cada tema, sumando las preguntas que se pueden corregir.

        Una pregunta sin tema **no entra** en ningún desglose: inventarle uno escondería que hay
        preguntas del banco sin catalogar, que es justo lo que el propietario tiene que ver en su
        panel. Las que la plantilla no corrige (`void`) tampoco cuentan: no son ni acierto ni fallo.
        """
        acumulado: dict[str, list[int]] = {}
        titulos: dict[str, str] = {}
        orden: list[str] = []
        for pregunta in preguntas:
            if pregunta.outcome == "void":
                continue
            for tema in pregunta.topics:
                if tema.code not in acumulado:
                    acumulado[tema.code] = [0, 0, 0]
                    titulos[tema.code] = tema.title
                    orden.append(tema.code)
                cuenta = acumulado[tema.code]
                if pregunta.outcome == "correct":
                    cuenta[0] += 1
                elif pregunta.outcome == "wrong":
                    cuenta[1] += 1
                else:
                    cuenta[2] += 1
        return tuple(
            StudentResultTopicView(
                code=codigo,
                title=titulos[codigo],
                correct=acumulado[codigo][0],
                wrong=acumulado[codigo][1],
                blank=acumulado[codigo][2],
            )
            for codigo in orden
        )

    @staticmethod
    def _duracion(sesion: StudentSessionView) -> int | None:
        """Cuánto duró el test, en segundos, o `None` si no se puede afirmar.

        Sin hora de arranque o de cierre no se inventa un cero: una sesión que no llegó a arrancar
        no
        tardó cero segundos, tardó lo que tardó en no arrancar.
        """
        if sesion.started_at is None or sesion.finished_at is None:
            return None
        return max(0, int((sesion.finished_at - sesion.started_at).total_seconds()))

    def _tests_hechos(self, oposicion: OppositionSummary) -> int:
        """Cuántos tests ha **terminado** esta persona en esta oposición.

        El total lo cuenta la consulta de sesiones (que ya filtra por dueño): traer la lista entera
        para contarla en memoria sería leer cientos de filas para escribir un número.

        En modo público la cifra se cuenta sobre lo que se puede enseñar —la misma regla que el
        historial— y por eso se queda dentro de la ventana de sesiones que se miran: decir un total
        que
        incluye sesiones que la pantalla no enseña sería contradecirse en la misma pantalla.
        """
        pagina = self._study.list_sessions(
            opposition_id=oposicion.id,
            status=SessionStatus.FINISHED.value,
            limit=SESSION_SCAN_LIMIT,
        )
        if not self._publico():
            return pagina.total
        publicables = self._student.public_set_ids(oposicion.id)
        return sum(
            1 for vista in pagina.sessions if self._de_conjuntos_publicables(vista, publicables)
        )

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
    def _run(
        vista: RunnerView,
        sesion: StudentSessionView,
        en_revision: frozenset[str] = frozenset(),
        derivadas: frozenset[str] = frozenset(),
    ) -> StudentRunView:
        """El estado del test en curso, con la hoja de respuestas entera."""
        return StudentRunView(
            session=sesion,
            total=vista.total,
            answered=vista.answered,
            pending=vista.pending,
            finished=vista.finished,
            position=None if vista.current is None else vista.current.position,
            question=(
                None
                if vista.current is None
                else StudentService._pregunta(vista.current, en_revision, derivadas)
            ),
            sheet=tuple(StudentService._fila(pregunta) for pregunta in vista.questions),
            questions_in_review=sum(
                1 for pregunta in vista.questions if pregunta.question_version_id in en_revision
            ),
            questions_derived=sum(
                1 for pregunta in vista.questions if pregunta.question_version_id in derivadas
            ),
        )

    def _en_revision(self, vista: RunnerView) -> frozenset[str]:
        """Las preguntas de esta sesión cuya clave está en revisión (`dudosa`, §1).

        Se pide **una vez por vista** y no una vez por pregunta: una sesión de simulacro tiene 85
        preguntas y preguntar el veredicto de cada una por separado serían 85 consultas para pintar
        una marca.
        """
        fiabilidad = self._study.key_reliability_of(
            [pregunta.question_version_id for pregunta in vista.questions]
        )
        return frozenset(
            pregunta_id
            for pregunta_id, veredicto in fiabilidad.items()
            if veredicto == KeyReliability.DUDOSA.value
        )

    def _derivadas(self, vista: RunnerView) -> frozenset[str]:
        """Las preguntas de esta sesión con **clave derivada** (§1 del encargo F29).

        Se piden igual que las de revisión —una vez por vista— y por el mismo motivo: la marca se
        pinta pregunta a pregunta y una consulta por pregunta para pintar un rótulo no se sostiene.
        """
        return self._study.derived_key_questions(
            [pregunta.question_version_id for pregunta in vista.questions]
        )

    @staticmethod
    def _pregunta(
        pregunta: SessionQuestionView,
        en_revision: frozenset[str] = frozenset(),
        derivadas: frozenset[str] = frozenset(),
    ) -> StudentQuestionView:
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
            in_review=pregunta.question_version_id in en_revision,
            derived_key=pregunta.question_version_id in derivadas,
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
