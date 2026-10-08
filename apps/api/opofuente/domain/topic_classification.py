"""Qué hacer con lo que un modelo propone para una pregunta (F4, pilotaje del paso A).

Este módulo es **la decisión**, y no sabe ni de red ni de base de datos: recibe el temario, recibe
lo que el modelo contestó y dice qué se escribe. Está aparte porque es lo único de la clasificación
que se puede probar sin llamar a nadie, y porque es donde viven los umbrales que el propietario
revisa:

- **confianza alta** (`>= UMBRAL_ALTA`): la pregunta se asigna y la asignación cuenta (es la banda
  que entra sola, con el actor `llm:…` en la auditoría para poder revisarla después);
- **confianza media** (`>= UMBRAL_MINIMO`): se guarda como **propuesta provisional**, que es la cola
  de revisión: se ve en el panel, no cuenta en el diagnóstico por temas y no se da por buena;
- **confianza baja** (`< UMBRAL_MINIMO`) o sin código: **no se escribe nada**. Una pregunta que se
  queda sin clasificar es un hueco del informe; una pregunta clasificada a cara o cruz es un dato
  falso que después nadie sabe de dónde salió.

Los dos umbrales están medidos, no elegidos a ojo: el piloto del paso A revisó 40 asignaciones a
mano y salieron **35 defendibles (87,5 %)** con un **7 % de inestabilidad** entre pasadas. Con esa
calidad, la banda automática tiene que ser estrecha (0,75 deja fuera la mitad dudosa de cada diez) y
por debajo de 0,5 la propuesta es una moneda al aire: se descarta en lugar de ensuciar la cola.

**Las preguntas fuera de temario** (normativa u organización de otra administración, o un enunciado
roto) no se asignan a ningún tema: se declaran con su motivo. Ese motivo viaja a la revisión del
propietario y es lo que después las deja fuera de simulacros y exámenes oficiales.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

#: A partir de aquí la asignación entra sola (banda automática).
UMBRAL_ALTA = 0.75

#: Por debajo de aquí no se escribe nada, ni asignación ni propuesta ni fuera de temario.
UMBRAL_MINIMO = 0.5


class OutOfSyllabus(StrEnum):
    """Por qué una pregunta no es materia del programa vigente.

    Son dos motivos distintos y se guardan distintos porque se revisan distinto: una pregunta de la
    ley autonómica de otra administración es material bueno que no cae en este examen; un enunciado
    roto es un error de los datos que hay que arreglar.
    """

    OTRA_ADMINISTRACION = "otra_administracion"
    ENUNCIADO_ROTO = "enunciado_roto"


class ProposalOutcome(StrEnum):
    """Qué se hace con la propuesta del modelo. Es el vocabulario del informe y de las pruebas."""

    #: Se asigna (`accepted`): cuenta en todo.
    ASSIGN = "asignar"
    #: Se guarda como propuesta (`provisional`): cola de revisión, no cuenta.
    REVIEW = "revisar"
    #: Fuera de temario: se declara con su motivo y queda excluida de simulacros y exámenes.
    OUT_OF_SYLLABUS = "fuera_de_temario"
    #: No se escribe nada: confianza por debajo del mínimo o el modelo se abstuvo.
    NOTHING = "sin_propuesta"
    #: La propuesta no se puede aplicar (un código que no está en el temario, por ejemplo).
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SyllabusEpigraph:
    """Un epígrafe del temario: su código oficial (`I.1.1`), su título y el tema del que cuelga."""

    code: str
    title: str
    node_id: str
    topic_code: str


@dataclass(frozen=True, slots=True)
class SyllabusTopic:
    """Un tema del temario con sus epígrafes, tal como los publica la convocatoria."""

    code: str
    title: str
    node_id: str
    block_code: str
    epigraphs: tuple[SyllabusEpigraph, ...]


@dataclass(frozen=True, slots=True)
class Syllabus:
    """El temario que se le enseña al modelo, leído de la base (nunca escrito a mano).

    Se construye desde el programa **sembrado** de la convocatoria: si el BOE cambia y la siembra
    cambia, el prompt cambia con ella. Un temario copiado en el código se quedaría viejo sin que
    nadie lo notara, que es la peor forma de fallar en esto.
    """

    opposition_code: str
    topics: tuple[SyllabusTopic, ...]

    @property
    def epigraph_count(self) -> int:
        return sum(len(tema.epigraphs) for tema in self.topics)

    def topic(self, code: str | None) -> SyllabusTopic | None:
        """Tema por su código oficial. `None` si no está: un código inventado no se adivina."""
        if code is None:
            return None
        limpio = code.strip().upper()
        return next((tema for tema in self.topics if tema.code.upper() == limpio), None)

    def epigraph(self, code: str | None) -> SyllabusEpigraph | None:
        """Epígrafe por su código oficial (`I.1.1`), en cualquier tema."""
        if code is None:
            return None
        limpio = code.strip().upper()
        for tema in self.topics:
            for epigrafe in tema.epigraphs:
                if epigrafe.code.upper() == limpio:
                    return epigrafe
        return None

    def lines(self) -> tuple[str, ...]:
        """El temario en texto, una línea por tema y una por epígrafe, con su código delante.

        El código va primero y **es** lo que se le pide al modelo: pedir «el tema de la
        Constitución» obligaría a emparejar títulos después, y un título se puede escribir de tres
        maneras.
        """
        lineas: list[str] = []
        for tema in self.topics:
            lineas.append(f"{tema.code} — {tema.title}")
            lineas.extend(f"    {epigrafe.code} — {epigrafe.title}" for epigrafe in tema.epigraphs)
        return tuple(lineas)


@dataclass(frozen=True, slots=True)
class TopicProposal:
    """Lo que el modelo contestó sobre **una** pregunta, ya leído y sin interpretar.

    `topic_code` nulo es una respuesta legítima: el modelo dice que no lo tiene claro. Inventarle un
    tema para no dejar el hueco sería justo lo que no se puede hacer.
    """

    question_version_id: str
    topic_code: str | None
    epigraph_code: str | None
    confidence: float
    out_of_syllabus: OutOfSyllabus | None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ProposalBatch:
    """Las propuestas de un lote con lo que costó pedirlas.

    Los tokens se cuentan porque el propietario paga la corrida: un informe que dice cuántas
    preguntas se clasificaron y no lo que costó obliga a mirarlo en la consola del proveedor.
    """

    proposals: tuple[TopicProposal, ...]
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True, slots=True)
class ClassifiableQuestion:
    """Lo mínimo de una pregunta para clasificarla: su enunciado y sus opciones.

    La **clave no viaja** a propósito: clasificar por el tema que trata una pregunta no necesita
    saber cuál es la correcta, y mandarla invitaría al modelo a razonar sobre una respuesta que
    puede estar mal (las hay `conflicting` en el banco).
    """

    question_version_id: str
    stem: str
    options: tuple[tuple[str, str], ...] = ()


#: Precio del modelo en dólares por millón de tokens, en **valle** (la tabla oficial consultada el
#: 7-oct-2026: entrada 0,15 · salida 0,60; en punta, el doble). Se usa solo para estimar el informe:
#: el gasto real lo dice el proveedor.
PRECIO_ENTRADA_USD_POR_MILLON = 0.15
PRECIO_SALIDA_USD_POR_MILLON = 0.60

#: El temario va en el **mensaje de sistema** y no en el de cada lote: es el mismo para todas las
#: llamadas, y así el proveedor puede cobrarlo a precio de acierto de caché (el trabajo de apuntes
#: midió 11.776 de 15.321 tokens de entrada con caché en la segunda pasada).
SYSTEM_PROMPT = """Eres un catalogador del temario de la oposición de Técnico Auxiliar de \
Informática (TAI) de la Administración General del Estado. Recibes preguntas de un banco y dices a \
qué tema del temario oficial pertenece cada una, y a qué epígrafe si lo tienes claro.

Temario oficial (usa EXACTAMENTE el código que aparece delante):
{temario}

Reglas:
1. Devuelve **un objeto por pregunta**, con su `id` tal cual te lo he dado.
2. `tema`: el código del tema (por ejemplo "I.1"). Si no lo tienes claro, déjalo en null.
3. `epigrafe`: el código del epígrafe (por ejemplo "I.1.2") solo si pertenece al tema que has \
dicho. Si no lo tienes claro, déjalo en null. Un epígrafe mal puesto es peor que ninguno.
4. `fuera_de_temario`: null, o uno de estos dos motivos cuando la pregunta **no** sea materia \
de este programa:
   - "otra_administracion": normativa, organización o procedimiento propios de otra \
administración (estatutos de autonomía, leyes autonómicas, régimen local, organigramas \
municipales…). La informática de los bloques II a IV **sí** es de este temario, aunque venga \
de un examen de otra administración.
   - "enunciado_roto": el enunciado no es una pregunta contestable (un trozo de norma sin \
pregunta, opciones incompletas).
5. `confianza`: un número de 0 a 1. Sé honesto: 0,9 solo si lo tienes claro; 0,5 si dudas \
entre dos temas; por debajo de 0,5 si es una suposición. Una confianza baja hace que un humano \
lo revise, no que se descarte la respuesta.
6. `motivo`: una frase corta que explique la decisión, sobre todo cuando dudes o cuando sea \
fuera de temario.

Responde SOLO con un objeto JSON con esta forma, sin texto alrededor:
{{"asignaciones": [{{"id": "...", "tema": "I.1", "epigrafe": "I.1.2", "fuera_de_temario": null, \
"confianza": 0.9, "motivo": "..."}}]}}"""


def build_user_prompt(questions: Sequence[ClassifiableQuestion]) -> str:
    """El lote de preguntas en texto: una por bloque, con su identificador delante.

    El identificador es lo que permite emparejar la respuesta con la pregunta, así que va primero
    y sin adornos. Las opciones van debajo porque muchas veces son las que dicen de qué va la
    pregunta (un enunciado genérico con opciones de redes es de redes).
    """
    bloques: list[str] = []
    for pregunta in questions:
        lineas = [f"id: {pregunta.question_version_id}", f"enunciado: {pregunta.stem.strip()}"]
        lineas.extend(f"  {clave}) {texto}" for clave, texto in pregunta.options)
        bloques.append("\n".join(lineas))
    return "Clasifica estas preguntas:\n\n" + "\n\n".join(bloques)


def build_system_prompt(syllabus: Syllabus) -> str:
    """Las instrucciones con el temario real dentro, listas para mandar."""
    return SYSTEM_PROMPT.format(temario="\n".join(syllabus.lines()))


@dataclass(frozen=True, slots=True)
class Decision:
    """Qué se escribe para una pregunta: el resultado de aplicar los umbrales a una propuesta."""

    question_version_id: str
    outcome: ProposalOutcome
    confidence: float
    topic: SyllabusTopic | None = None
    epigraph: SyllabusEpigraph | None = None
    out_of_syllabus: OutOfSyllabus | None = None
    note: str | None = None

    @property
    def writes(self) -> bool:
        """¿Esta decisión escribe algo? El modo `--dry-run` lo usa para no mentir en su informe."""
        return self.outcome in (
            ProposalOutcome.ASSIGN,
            ProposalOutcome.REVIEW,
            ProposalOutcome.OUT_OF_SYLLABUS,
        )


def decide(proposal: TopicProposal, *, syllabus: Syllabus) -> Decision:
    """Aplica los umbrales y resuelve los códigos contra el temario real.

    El orden importa:

    1. **fuera de temario** manda sobre cualquier tema propuesto: si el modelo dijo que la pregunta
       no es de este programa, asignarle además un tema sería contradecirse;
    2. un **código que no está en el temario** es un error de la propuesta y va al informe como tal:
       asignar «lo más parecido» sería inventar la clasificación con el nombre del modelo;
    3. el **epígrafe** puede venir sin tema (el tema se deduce del árbol oficial, que es la
       verdad) y un epígrafe que no existe se descarta **diciéndolo**, sin tumbar el tema, que sí
       se resolvió.
    """
    confianza = min(max(float(proposal.confidence), 0.0), 1.0)

    if proposal.out_of_syllabus is not None:
        if confianza < UMBRAL_MINIMO:
            return Decision(
                question_version_id=proposal.question_version_id,
                outcome=ProposalOutcome.NOTHING,
                confidence=confianza,
                note="fuera de temario con confianza insuficiente: no se escribe",
            )
        return Decision(
            question_version_id=proposal.question_version_id,
            outcome=ProposalOutcome.OUT_OF_SYLLABUS,
            confidence=confianza,
            out_of_syllabus=proposal.out_of_syllabus,
            note=proposal.note,
        )

    epigrafe = syllabus.epigraph(proposal.epigraph_code)
    avisos: list[str] = []
    if proposal.epigraph_code and epigrafe is None:
        avisos.append(f"el epígrafe «{proposal.epigraph_code}» no está en el temario: se descarta")

    if epigrafe is not None:
        # El epígrafe manda: viene del árbol oficial, y su tema es el suyo aunque el modelo diga
        # otro.
        tema = syllabus.topic(epigrafe.topic_code)
        if proposal.topic_code and (
            (propuesto := syllabus.topic(proposal.topic_code)) is None
            or propuesto.code != epigrafe.topic_code
        ):
            avisos.append(
                f"el tema «{proposal.topic_code}» no es el del epígrafe «{epigrafe.code}»: "
                f"se usa «{epigrafe.topic_code}»"
            )
    else:
        tema = syllabus.topic(proposal.topic_code)

    if tema is None:
        if proposal.topic_code:
            return Decision(
                question_version_id=proposal.question_version_id,
                outcome=ProposalOutcome.ERROR,
                confidence=confianza,
                note=f"el tema «{proposal.topic_code}» no está en el temario",
            )
        return Decision(
            question_version_id=proposal.question_version_id,
            outcome=ProposalOutcome.NOTHING,
            confidence=confianza,
            note=proposal.note or "el modelo no lo tenía claro",
        )

    if confianza < UMBRAL_MINIMO:
        return Decision(
            question_version_id=proposal.question_version_id,
            outcome=ProposalOutcome.NOTHING,
            confidence=confianza,
            topic=tema,
            note="confianza por debajo del mínimo: no se escribe",
        )

    resultado = ProposalOutcome.ASSIGN if confianza >= UMBRAL_ALTA else ProposalOutcome.REVIEW
    return Decision(
        question_version_id=proposal.question_version_id,
        outcome=resultado,
        confidence=confianza,
        topic=tema,
        epigraph=epigrafe,
        note="; ".join(avisos) if avisos else proposal.note,
    )


__all__ = [
    "PRECIO_ENTRADA_USD_POR_MILLON",
    "PRECIO_SALIDA_USD_POR_MILLON",
    "SYSTEM_PROMPT",
    "UMBRAL_ALTA",
    "UMBRAL_MINIMO",
    "ClassifiableQuestion",
    "Decision",
    "OutOfSyllabus",
    "ProposalBatch",
    "ProposalOutcome",
    "Syllabus",
    "SyllabusEpigraph",
    "SyllabusTopic",
    "TopicProposal",
    "build_system_prompt",
    "build_user_prompt",
    "decide",
]
