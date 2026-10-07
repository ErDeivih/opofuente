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
from dataclasses import dataclass

from opofuente.application.ports import Clock
from opofuente.application.read_models import NodeView, OppositionSummary
from opofuente.application.student_models import (
    StudentBlockProgressView,
    StudentEpigraphView,
    StudentOppositionView,
    StudentOverviewView,
    StudentProgressView,
    StudentScoreView,
    StudentSessionView,
    StudentTopicProgressView,
    StudentTopicView,
)
from opofuente.application.study_models import SessionResultView, SessionView
from opofuente.application.study_service import StudyService
from opofuente.config import Settings
from opofuente.domain.errors import NotFoundError, UnsupportedError
from opofuente.domain.profiles import NodeType
from opofuente.domain.study import OWNER_ID_LOCAL, SessionStatus
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.student_repository import SqlAlchemyStudentRepository

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
        owner_id: str = OWNER_ID_LOCAL,
    ) -> None:
        self._settings = settings
        self._profiles = profiles
        self._student = student
        self._study = study
        self._clock = clock
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
                    progress=self._progreso_del_tema(tema.path, tema.title, datos),
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
        bloques: list[StudentBlockProgressView] = []
        for bloque in self._curriculum(oposicion):
            if bloque.node_type is not NodeType.BLOCK:
                continue
            temas: list[StudentTopicProgressView] = []
            total = self._de(bloque, cifras)
            for tema in bloque.children:
                datos_tema = self._de(tema, cifras)
                temas.append(self._progreso_del_tema(tema.path, tema.title, datos_tema))
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
    def _progreso_del_tema(codigo: str, titulo: str, datos: _Cifras) -> StudentTopicProgressView:
        return StudentTopicProgressView(
            code=codigo,
            number=_numero_de(codigo),
            title=titulo,
            available_questions=datos.available,
            answered=datos.answered,
            correct=datos.correct,
            accuracy=datos.accuracy,
            due_reviews=datos.due,
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
        )
