"""La clave **derivada**: dos fuentes independientes que dicen la misma letra (§1 del encargo).

El problema que resuelve este modulo es el que dejo abierto el bloque del §1: hay conjuntos cuya
clave **esta mal extraida** del material (marca mal detectada, desplazada o de otra pregunta) y sus
preguntas quedan en cuarentena. Con la cuarentena puesta el alumno estudia con menos preguntas de
las que tiene, y la prueba del desplazamiento ya demostro que el arreglo **no** es reextraerlas:
ninguna rotacion baja del 10 %.

Lo que queda es **derivar la letra de cada pregunta** cuando **dos fuentes independientes** dicen lo
mismo:

1. **los apuntes**, con la **cita verificada** —el ancla `question_note_anchors`: la frase que el
   motor comprobo contra el texto y la letra que esa frase sostiene—;
2. **una respuesta del modelo sin apuntes**: la pregunta sola (enunciado y opciones) y nada mas.

Si las dos coinciden, la letra es la respuesta correcta con dos apoyos que no dependen el uno del
otro: la clave extraida del material **no** entra en la decision, que es justo lo que la hace
derivable. Eso se guarda como clave **`derived`**, nunca `active`: la clave oficial o extraida del
conjunto no se toca, y el alumno ve la marca **«clave revisada automaticamente»**.

Si no coinciden —o si falta una de las dos— la pregunta **sigue fuera** y su motivo se guarda para
la bandeja del propietario, agrupado por conjunto. Los tres motivos son los del informe:

- **`sin_material`**: los apuntes no dicen nada de esa pregunta (no hay ancla, o el ancla quedo en
  hueco). No hay primera fuente que consultar.
- **`sin_cita`**: los apuntes dan una letra pero **sin cita verificada** (el ancla quedo en duda).
  Una letra sin la frase que la sostiene no es una fuente: es una opinion.
- **`sin_coincidencia`**: las dos fuentes hablan y **no dicen lo mismo**. Es el caso que va al
  propietario, porque aqui no decide una regla.

Y **las claves oficiales no se derivan**: un examen oficial, un conjunto con plantilla
documento, o un ejercicio de la AGE con su respuesta publicada. El porque lo dice `protege_derivar`,
con el mismo criterio que `protege_cambiar_la_clave` (una sola verdad sobre que es oficial).

Todo lo de este modulo es **puro**: no sabe de SQL, ni de ficheros, ni de modelos. La coincidencia y
la decision por conjunto se prueban sin base de datos.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from opofuente.domain.key_reliability import MARCA_DERIVADA, normalizar_letra
from opofuente.domain.question_file import protege_cambiar_la_clave
from opofuente.domain.questions import OriginScope
from opofuente.domain.topic_classification import ClassifiableQuestion

#: Cuando un conjunto tiene esta proporcion de preguntas con clave fiable, **vuelve a los tests**.
#: Es el liston del encargo, y es el mismo genero de liston que el 90 % de cobertura de un tema: se
#: mira con la cifra delante y no se redondea a favor.
UMBRAL_VUELVE_A_LOS_TESTS = 0.90

#: Los tres motivos por los que una pregunta de un conjunto en cuarentena **sigue fuera**. Es
#: vocabulario cerrado y lo impone la base con un `CHECK`.
MOTIVO_SIN_MATERIAL = "sin_material"
MOTIVO_SIN_CITA = "sin_cita"
MOTIVO_SIN_COINCIDENCIA = "sin_coincidencia"

#: El actor con el que se auditan las escrituras de esta ruta. Uno solo, para que la auditoria diga
#: siempre quien las hizo.
ACTOR = "f29:claves-derivadas"

#: La accion de la auditoria cuando una clave derivada se guarda.
ACCION_CLAVE_DERIVADA = "question.derived_key_saved"

#: La accion de la auditoria cuando un conjunto protegido **se rechaza**.
ACCION_RECHAZO = "question_set.derived_key_refused"

#: La accion de la auditoria cuando se guarda **por que** sigue fuera lo que sigue fuera.
ACCION_HUECOS = "question_set.key_gaps_recorded"

#: La accion de la auditoria cuando se toma la decision de volver (o no) a los tests.
ACCION_DECISION = "question_set.return_decision"


class KeyTrust(StrEnum):
    """De donde sale la clave con la que se corrige una pregunta. Vocabulario cerrado.

    - **`active`**: la clave del conjunto, y el conjunto **no** esta en cuarentena (o su letra esta
      corroborada por la cita de los apuntes). Es el camino de siempre.
    - **`derived`**: una clave derivada **de esa pregunta**, con sus dos fuentes. Es lo que devuelve
      al estudio las preguntas de un conjunto en cuarentena.
    - **`ninguna`**: no hay clave de la que fiarse. La pregunta **sigue fuera**.
    """

    ACTIVE = "active"
    DERIVED = "derived"
    NINGUNA = "ninguna"

    @property
    def es_una_clave(self) -> bool:
        """¿Con esta se puede corregir una respuesta?"""
        return self is not KeyTrust.NINGUNA

    @property
    def se_marca_al_alumno(self) -> bool:
        """¿Lleva marca? Solo la derivada, y su marca es la de `MARCA_DERIVADA`."""
        return self is KeyTrust.DERIVED


class MotivoDeFuera(StrEnum):
    """Por que una pregunta de un conjunto en cuarentena sigue fuera del estudio."""

    SIN_MATERIAL = MOTIVO_SIN_MATERIAL
    SIN_CITA = MOTIVO_SIN_CITA
    SIN_COINCIDENCIA = MOTIVO_SIN_COINCIDENCIA

    @property
    def texto(self) -> str:
        """El motivo, dicho para que el propietario sepa que le toca a el y que no."""
        return {
            MotivoDeFuera.SIN_MATERIAL: (
                "los apuntes no contestan a esta pregunta (no hay cita que la sostenga): "
                "le falta material"
            ),
            MotivoDeFuera.SIN_CITA: (
                "los apuntes dan una letra pero sin cita verificada: una letra sin la frase que la "
                "sostiene no es una fuente"
            ),
            MotivoDeFuera.SIN_COINCIDENCIA: (
                "los apuntes y el modelo, preguntado sin apuntes, no dicen la misma letra: "
                "lo decide el propietario"
            ),
        }[self]


@dataclass(frozen=True, slots=True)
class FuenteDeLosApuntes:
    """La primera fuente: la letra que dan los apuntes, con la cita que la sostiene.

    `key_status` es contra que clave comprobo el motor de apuntes esa pregunta (`active`, `draft` o
    `ninguna`). **No decide nada de la derivacion**: la letra de los apuntes vale por su cita,
    la clave con la que se comparo—, pero se guarda con la evidencia: es de donde sale que una letra
    corrobore o contradiga la clave del conjunto.
    """

    question_version_id: str
    anchor_id: str
    letra: str
    cita: str
    key_status: str = "ninguna"

    @property
    def sirve(self) -> bool:
        """¿Hay letra **y** cita verificada? Sin las dos no hay primera fuente."""
        return bool(normalizar_letra(self.letra)) and bool(self.cita.strip())


@dataclass(frozen=True, slots=True)
class RespuestaDelModelo:
    """La segunda fuente: lo que contesta el modelo a la pregunta **sola**, sin apuntes.

    `letra` vacia o `None` es una respuesta que no sirve: el modelo puede decir que no lo sabe, y
    decirlo es mejor que inventarse una letra (esa letra acabaria en la clave de una pregunta).
    """

    question_version_id: str
    letra: str | None

    @property
    def sirve(self) -> bool:
        return bool(normalizar_letra(self.letra))


def coinciden(apuntes: FuenteDeLosApuntes, modelo: RespuestaDelModelo) -> bool:
    """¿Las dos fuentes dicen la misma letra?

    Se comparan **normalizadas** (sin espacios, sin punto y en minuscula), como se comparan en
    todo el motor de claves: `a` y `A)` son la misma respuesta, y tratarlas como distintas dejaria
    fuera preguntas que si se pueden derivar. Una respuesta vacia **no** coincide con nada: el
    modelo que dice «no lo se» no sostiene ninguna letra.
    """
    propia = normalizar_letra(apuntes.letra)
    return bool(propia) and propia == normalizar_letra(modelo.letra)


@dataclass(frozen=True, slots=True)
class RespuestasBatch:
    """Lo que contesto el modelo a un lote de preguntas, con los tokens que costo.

    `sin_respuesta` son las preguntas que el lote no contesto (el modelo se salto una o devolvio una
    letra que no es una de sus opciones): se conservan para poder decir cuantas preguntas se
    quedaron fuera por eso y no por un desacuerdo.
    """

    respuestas: tuple[RespuestaDelModelo, ...] = ()
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit_tokens: int = 0
    sin_respuesta: tuple[str, ...] = ()

    @property
    def por_pregunta(self) -> dict[str, RespuestaDelModelo]:
        return {respuesta.question_version_id: respuesta for respuesta in self.respuestas}


#: Version del encargo con el que se pide la respuesta independiente. Va guardada con cada clave
#: derivada: si el encargo cambia, las claves derivadas con el anterior se reconocen.
PROMPT_VERSION = "clave-derivada-1"

#: El encargo de la segunda fuente. **Sin apuntes y sin material**: la pregunta sola. Se pide la
#: letra y nada mas (ni explicacion ni confianza) por dos razones: la respuesta tiene que ser una
#: letra para poder compararla, y cada token de mas se paga en cada pregunta del banco.
SYSTEM_PROMPT_RESPONDER = """Eres un examinador de la oposición de Técnico Auxiliar de Informática \
(TAI) de la Administración General del Estado. Recibes preguntas de un banco **sin ningún material \
de apoyo**: solo el enunciado y sus opciones. Tu trabajo es decir **qué opción es la correcta**.

Reglas:
1. Devuelve **un objeto por pregunta**, con su `id` tal cual te lo he dado.
2. `letra`: la clave estable de la opción correcta, tal como aparece en la lista de opciones \
(por ejemplo "a" o "b"). **Una sola letra**: si dudas entre dos, elige la que defenderías.
3. Si de verdad no lo sabes, `letra` en null. Decir que no lo sabes es correcto y es mejor que \
inventar: esta letra va a ser la respuesta con la que alguien estudie.
4. No expliques nada y no devuelvas nada más que el JSON.

Formato exacto:
{"respuestas": [{"id": "<el id que te he dado>", "letra": "a"}]}"""


def build_system_prompt_responder() -> str:
    """El mensaje de sistema de la segunda fuente. Es el mismo para todo el lote."""
    return SYSTEM_PROMPT_RESPONDER


def build_user_prompt_responder(preguntas: Sequence[ClassifiableQuestion]) -> str:
    """Las preguntas del lote: enunciado y opciones, **sin nada mas**.

    Lo que no entra aqui es tan importante como lo que entra: ni los apuntes, ni la clave del
    conjunto, ni la letra que dio el motor de apuntes. Si la clave del conjunto viajara en el
    mensaje, la segunda fuente dejaria de ser independiente y la coincidencia no probaria nada.
    """
    bloques = [
        "\n".join(
            (
                f"id: {pregunta.question_version_id}",
                f"enunciado: {pregunta.stem.strip()}",
                "opciones:",
                *(f"  {clave}) {texto.strip()}" for clave, texto in sorted(pregunta.options)),
            )
        )
        for pregunta in preguntas
    ]
    return "Preguntas:\n\n" + "\n\n".join(bloques)


@dataclass(frozen=True, slots=True)
class Derivacion:
    """La clave derivada de una pregunta: la letra, y las dos fuentes que la sostienen."""

    question_version_id: str
    letra: str
    apuntes: FuenteDeLosApuntes
    modelo: RespuestaDelModelo

    @property
    def referencias(self) -> tuple[str, ...]:
        """De donde sale, en una linea, para la ficha y para la auditoria."""
        return (
            f"apuntes: «{self.apuntes.cita.strip()}» → {normalizar_letra(self.apuntes.letra)}",
            f"modelo sin apuntes: {normalizar_letra(self.modelo.letra)}",
        )


def derivar(
    apuntes: FuenteDeLosApuntes | None, modelo: RespuestaDelModelo
) -> Derivacion | MotivoDeFuera:
    """La derivacion, o el motivo por el que no la hay. **Una sola funcion decide.**

    El orden es el del informe y no es casual: primero se mira si hay material (fuente que
    despues si esa fuente tiene cita (una letra sin frase no es fuente) y solo al final se comparan
    las dos letras. Cambiar el orden cambiaria a quien se le echa la culpa de que una pregunta siga
    fuera, que es justo lo que el propietario necesita saber.
    """
    if apuntes is None or not normalizar_letra(apuntes.letra):
        return MotivoDeFuera.SIN_MATERIAL
    if not apuntes.sirve:
        return MotivoDeFuera.SIN_CITA
    if not coinciden(apuntes, modelo):
        return MotivoDeFuera.SIN_COINCIDENCIA
    return Derivacion(
        question_version_id=apuntes.question_version_id,
        letra=normalizar_letra(apuntes.letra),
        apuntes=apuntes,
        modelo=modelo,
    )


def protege_derivar(
    *, set_type: str, tiene_plantilla_enlazada: bool, origin_scope: str
) -> str | None:
    """Por que **no** se puede derivar la clave de este conjunto, o `None` si si se puede.

    Tres caminos llevan a «clave oficial», y los tres cuentan:

    1. **el tipo del conjunto**: un `official_exam` es un examen oficial y su clave la publico
       la administracion;
    2. **el material de origen**: una plantilla enlazada a un documento salio de un papel, aunque el
       conjunto este marcado como banco privado;
    3. **la procedencia**: un conjunto de la **AGE** con su respuesta publicada. Los dos primeros
       caminos son los de `protege_cambiar_la_clave` (una verdad sobre que es oficial y por que);
       este tercero lo añade esta ruta: hay ejercicios de la AGE con la respuesta publicada que
       no estan enlazados a ningun documento —su clave llego copiada— y su clave **es** la oficial.
       Derivarla seria sustituir la respuesta que publico la administracion por la de un modelo.

    El texto dice **cual** de los tres caminos lo impide, porque con decenas de conjuntos
    con decenas de conjuntos oficiales en la base, «no se puede» a secas obligaria a adivinar cual
    estorba.
    """
    motivo = protege_cambiar_la_clave(
        set_type=set_type, tiene_plantilla_enlazada=tiene_plantilla_enlazada
    )
    if motivo is not None:
        return f"no se deriva su clave: {motivo}"
    if origin_scope == OriginScope.AGE.value:
        return (
            "no se deriva su clave: el conjunto es un ejercicio de la Administración General del "
            f"Estado ({OriginScope.AGE.value}) con su respuesta publicada"
        )
    return None


@dataclass(frozen=True, slots=True)
class DecisionDeConjunto:
    """¿Vuelve este conjunto a los tests? Con la cifra delante, que es como se decide.

    `preguntas` es el total del conjunto —lo que el alumno se juega—, y `con_clave` las que tienen
    una clave de la que fiarse: **las derivadas mas las corroboradas por la cita de los apuntes**.
    Las que no la tienen **siguen fuera** aunque el conjunto vuelva.

    Los dos numeros no son lo mismo y por eso se guardan por separado: una pregunta **derivada**
    entra ya (su clave no depende de la plantilla del conjunto), y una **corroborada** —los apuntes
    confirman la letra de la plantilla activa— entra **cuando el conjunto vuelve**, porque la
    plantilla de la que sale es la que esta en cuarentena.
    """

    set_id: str
    set_title: str
    preguntas: int
    con_clave: int
    derivadas: int = 0
    corroboradas: int = 0

    @property
    def proporcion(self) -> float:
        return 0.0 if not self.preguntas else self.con_clave / self.preguntas

    @property
    def vuelve_a_los_tests(self) -> bool:
        """Al 90 % o mas. El liston es `>=`, como el de cobertura de un tema."""
        return self.preguntas > 0 and self.proporcion >= UMBRAL_VUELVE_A_LOS_TESTS

    @property
    def fuera(self) -> int:
        return max(0, self.preguntas - self.con_clave)

    def linea(self) -> str:
        decision = "VUELVE a los tests" if self.vuelve_a_los_tests else "sigue fuera"
        falta = "" if self.vuelve_a_los_tests else f" (le faltan {self.para_el_liston()})"
        return (
            f"{self.set_title}: {self.con_clave}/{self.preguntas} = "
            f"{100 * self.proporcion:.1f} % con clave fiable "
            f"({self.derivadas} derivada(s), {self.corroboradas} corroborada(s)) · {decision}"
            f"{falta}"
        )

    def para_el_liston(self) -> int:
        """Cuantas preguntas mas harian falta para llegar al liston (no se recorta a 0)."""
        necesarias = math.ceil(UMBRAL_VUELVE_A_LOS_TESTS * self.preguntas)
        return max(0, necesarias - self.con_clave)

    def motivo(self) -> str:
        """La decision en una frase, con su cifra: es lo que se guarda en la auditoria."""
        if self.vuelve_a_los_tests:
            return (
                f"vuelve: {self.con_clave}/{self.preguntas} = {100 * self.proporcion:.1f} % "
                f"alcanza el liston del {UMBRAL_VUELVE_A_LOS_TESTS:.0%} de clave fiable"
            )
        return (
            f"sigue fuera: {self.con_clave}/{self.preguntas} = {100 * self.proporcion:.1f} % y le "
            f"faltan {self.para_el_liston()} pregunta(s) para el "
            f"{UMBRAL_VUELVE_A_LOS_TESTS:.0%}"
        )


def decidir_conjuntos(
    preguntas_por_conjunto: Iterable[tuple[str, str, int]],
    *,
    derivadas: Iterable[tuple[str, str]] = (),
    corroboradas: Iterable[tuple[str, str]] = (),
) -> tuple[DecisionDeConjunto, ...]:
    """La decision de **cada** conjunto, con sus dos numeros, en orden estable.

    `preguntas_por_conjunto` son `(set_id, titulo, total)`; `derivadas` y `corroboradas` son pares
    `(set_id, question_version_id)`. Se pasan como listas de pares —y no como conjuntos por
    conjunto— para que el llamante no tenga que montar la misma estructura dos veces: el recuento lo
    hace esta funcion, que es la que se prueba.
    """
    derivadas_por_conjunto: dict[str, int] = {}
    for set_id, _ in derivadas:
        derivadas_por_conjunto[set_id] = derivadas_por_conjunto.get(set_id, 0) + 1
    corroboradas_por_conjunto: dict[str, int] = {}
    for set_id, _ in corroboradas:
        corroboradas_por_conjunto[set_id] = corroboradas_por_conjunto.get(set_id, 0) + 1

    decisiones = [
        DecisionDeConjunto(
            set_id=set_id,
            set_title=titulo,
            preguntas=total,
            con_clave=derivadas_por_conjunto.get(set_id, 0)
            + corroboradas_por_conjunto.get(set_id, 0),
            derivadas=derivadas_por_conjunto.get(set_id, 0),
            corroboradas=corroboradas_por_conjunto.get(set_id, 0),
        )
        for set_id, titulo, total in preguntas_por_conjunto
    ]
    decisiones.sort(
        key=lambda decision: (-decision.proporcion, -decision.preguntas, decision.set_title)
    )
    return tuple(decisiones)


@dataclass(frozen=True, slots=True)
class RecuentoDeFuera:
    """Cuantas preguntas se quedan fuera y **por que**, para el informe del encargo."""

    motivo: MotivoDeFuera
    preguntas: int

    def linea(self) -> str:
        return f"{self.preguntas} sin clave ({self.motivo.value}): {self.motivo.texto}"


def recuento_de_fuera(motivos: Sequence[MotivoDeFuera]) -> tuple[RecuentoDeFuera, ...]:
    """Los motivos contados, de mas a menos, con el vocabulario cerrado del dominio."""
    cuentas: dict[MotivoDeFuera, int] = {}
    for motivo in motivos:
        cuentas[motivo] = cuentas.get(motivo, 0) + 1
    recuentos = [RecuentoDeFuera(motivo=motivo, preguntas=n) for motivo, n in cuentas.items()]
    recuentos.sort(key=lambda recuento: (-recuento.preguntas, recuento.motivo.value))
    return tuple(recuentos)


__all__ = [
    "ACCION_CLAVE_DERIVADA",
    "ACCION_DECISION",
    "ACCION_HUECOS",
    "ACCION_RECHAZO",
    "ACTOR",
    "MARCA_DERIVADA",
    "MOTIVO_SIN_CITA",
    "MOTIVO_SIN_COINCIDENCIA",
    "MOTIVO_SIN_MATERIAL",
    "PROMPT_VERSION",
    "SYSTEM_PROMPT_RESPONDER",
    "UMBRAL_VUELVE_A_LOS_TESTS",
    "DecisionDeConjunto",
    "Derivacion",
    "FuenteDeLosApuntes",
    "KeyTrust",
    "MotivoDeFuera",
    "RecuentoDeFuera",
    "RespuestaDelModelo",
    "RespuestasBatch",
    "build_system_prompt_responder",
    "build_user_prompt_responder",
    "coinciden",
    "decidir_conjuntos",
    "derivar",
    "protege_derivar",
    "recuento_de_fuera",
]
