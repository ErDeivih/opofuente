"""La ficha de pregunta: qué se puede arreglar de una pregunta y qué no (F20, §4.2 del objetivo).

El objetivo llama a esta pantalla «el sitio donde el propietario arregla las claves dudosas» y le
pide
tres cosas que son de **dominio**, no de interfaz:

1. **cambiar la respuesta correcta sin tocar la que había**: la anterior se queda en el historial.
Lo
   que se puede y lo que no de ese cambio se decide aquí (`protege_cambiar_la_clave`);
2. **reparar una pregunta mal importada con una regla mecánica**: hay exactamente dos reparaciones
que
   una regla puede hacer sin inventarse texto —quitar la referencia del examen que quedó pegada al
   enunciado y partir una opción que se tragó a la siguiente— y las dos viven aquí, con su guarda;
3. **decir por qué una pregunta señalada como mal importada no se puede reparar**. Esto es lo que
   convierte la ficha en una pantalla de trabajo y no en un visor: de las once preguntas que el
bloque
   del panel dejó marcadas como reparables, **una** se repara con una regla. Las otras diez están
   marcadas por reglas mecánicas que en su caso son falsos positivos —una opción que menciona a otra
   («las consecuencia indicadas en la opción c)») no está fundida— o son restos que ninguna regla
   puede reconstruir. Decirlo es el trabajo; callarlo dejaría al propietario «reparando» preguntas
que
   están bien.

Tres reglas que se aplican aquí y no en la ruta:

- **una clave oficial no se cambia, se dice por qué**: un conjunto es oficial si su tipo lo dice
  (`official_exam`) o si su plantilla viene de un documento (material de origen). El INAP y la
Guardia
  Civil entran por los dos caminos, y los dos se respetan;
- **una reparación no inventa**: si la guarda no pasa, no hay reparación disponible. Es preferible
  decir «esto no se puede arreglar con una regla» a escribir una versión nueva con texto inventado;
- **la letra de una opción que no existe no se escribe**: cambiar la respuesta correcta a `e` en una
  pregunta de cuatro opciones es un error de quien llama, y se contesta antes de tocar la base.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from opofuente.domain.notes_incidents import (
    PATRON_REFERENCIA_PEGADA,
    regla_de_mala_importacion,
)

#: El tipo de conjunto que la aplicación ya considera oficial (`QuestionSet.is_official`).
TIPO_OFICIAL = "official_exam"

#: Las dos reparaciones que una regla mecánica puede hacer. Son las claves del vocabulario que viaja
#: al contrato y a la auditoría: cambiarlas cambia lo que dice el historial de la pregunta.
REGLA_REFERENCIA_DEL_EXAMEN = "quitar_referencia_del_examen"
REGLA_OPCION_FUNDIDA = "partir_opcion_fundida"

#: Cómo se llama cada reparación en la pantalla. El nombre corto es el de la interfaz; la clave de
#: arriba es la del dato, y por eso están separadas: la primera se puede reescribir, la segunda no.
TITULO_DE_REGLA: dict[str, str] = {
    REGLA_REFERENCIA_DEL_EXAMEN: "Quitar la referencia del examen",
    REGLA_OPCION_FUNDIDA: "Partir la opción fundida",
}

#: El patrón de una opción dentro de otra: `a)`, `b)`, `3 c)` en mitad del texto.
#:
#: `PATRON_REFERENCIA_PEGADA` —la referencia del examen pegada al enunciado, «2011 Universidad
#: Internacional de Andalucía…»— se importa de la reclasificación de incidencias (§2 de los ajustes)
#: en vez de escribirla otra vez: dos expresiones para lo mismo acaban diciendo cosas distintas, y
#: la
#: que se queda vieja es siempre la que nadie lee.
PATRON_DE_OPCION = re.compile(r"\b\d?[a-dA-D]\)")

#: Palabras que delatan que lo que hay dentro de una opción **es una referencia a otra opción** y no
#: dos opciones fundidas: «conforme a lo indicado en la opción c)», «de conformidad con la letra
#: a)».
#: Es la guarda que evita «reparar» una pregunta que está bien, y es la mitad del hallazgo de esta
#: tanda: siete de las once señales del motor son menciones legítimas.
PALABRAS_DE_REFERENCIA = (
    "opci",
    "letra",
    "letras",
    "respuesta",
    "respuestas",
    "caso indicado",
    "apartado",
)

#: Lo que puede quedar detrás de la referencia del examen sin que deje de ser una referencia: el
#: resto del nombre del cuerpo y su grupo («de Gestión de Sistemas e Informática de la AGE - Gr.B»).
#:
#: Medido el 13 de octubre de 2026 sobre la copia de la base: las veinte referencias de verdad miden
#: entre 27 y 68 caracteres detrás del año, y las dos que no son referencias miden 277 y 7.916. El
#: listón de 120 deja fuera las dos y no roza ninguna de las veinte.
MAXIMO_DETRAS_DE_LA_REFERENCIA = 120

#: Lo mínimo que tiene que quedar de enunciado para que la limpieza valga la pena: un enunciado de
#: diez caracteres no es una pregunta, es un resto.
MINIMO_DE_ENUNCIADO = 20

#: Lo mínimo que tiene que medir un trozo para que partirlo deje dos opciones y no dos restos.
MINIMO_DE_TROZO = 2

#: Los separadores que quedan colgando cuando se corta la referencia del examen. Incluye los puntos
#: y
#: los dos puntos porque la cola de una referencia suele traerlos pegados («. 2013 Cuerpo…»), y se
#: usa
#: **solo** en la cola: al trozo que se queda no se le quitan los suyos, que son justo los que dicen
#: que la frase acaba ahí.
_SEPARADORES = " \t\u00a0\u2003.,;:/*--—·()[]«»\"'“”¡!"

#: Lo que sí se le puede quitar al trozo que se queda: espacios y signos que no cierran una frase.
#: Un
#: `.` o un `:` no están aquí a propósito —son el final de la frase que hay que conservar— y una `(`
#: o
#: un `«` sí, porque abren algo que la referencia se llevó.
_SEPARADORES_DE_APERTURA = " \t\u00a0\u2003([«\"'“--—·,;/"


def protege_cambiar_la_clave(*, set_type: str, tiene_plantilla_enlazada: bool) -> str | None:
    """Por qué **no** se puede cambiar la clave de este conjunto, o `None` si sí se puede.

        Dos caminos llevan a «oficial», y los dos cuentan:

        1. **el tipo del conjunto**: un `official_exam` es un examen oficial, y su clave es la que
    publicó
           la administración;
        2. **el material de origen**: una plantilla enlazada a un documento es una plantilla que
        salió
    de
           un papel, aunque el conjunto esté marcado como banco privado. Es el camino por el que la
           Guardia Civil 2026 entra —sus conjuntos son `official_exam`, pero su plantilla además
           está
           enlazada— y el que protege a un examen importado antes de que el tipo se arreglara.

        El texto es el que lee el propietario en la pantalla cuando intenta cambiarla, así que dice
    **cuál**
        de los dos caminos lo impide: con diez conjuntos oficiales en la base, «no se puede» a secas
        obligaría a adivinar cuál es el que estorba.
    """
    if set_type == TIPO_OFICIAL:
        return (
            "el conjunto es un examen oficial: su respuesta correcta es la que publicó la "
            "administración y no se cambia desde aquí"
        )
    if tiene_plantilla_enlazada:
        return (
            "la plantilla de este conjunto viene de un documento (material de origen): es una "
            "plantilla oficial y su respuesta correcta no se cambia desde aquí"
        )
    return None


@dataclass(frozen=True, slots=True)
class Reparacion:
    """Una reparación disponible para una pregunta: **qué** se escribe y con qué regla.

    `stem` y `opciones` son nulos cuando la reparación no toca esa mitad: una referencia del examen
    pegada se arregla en el enunciado y una opción fundida, en las opciones. Los dos campos pueden
    venir a la vez —la pregunta del JCL tiene las dos cosas— y entonces la versión nueva se escribe
    con las dos reparaciones, en **una** versión y no en dos: partir una pregunta en dos versiones
    seguidas llenaría su historial de pasos intermedios que nadie escribió.
    """

    reglas: tuple[str, ...]
    detalle: str
    stem: str | None = None
    opciones: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if not self.reglas:
            raise ValueError("Una reparación necesita al menos una regla")
        if self.stem is None and self.opciones is None:
            raise ValueError("Una reparación que no cambia nada no es una reparación")


def quitar_referencia_del_examen(stem: str) -> str | None:
    """El enunciado sin las referencias de examen pegadas al final, o `None` si no se puede quitar.

        La referencia es un resto de la extracción: el cuestionario original lleva al lado de la
    pregunta
        de qué examen salió («2013 Cuerpo de Gestión de Sistemas e Informática de la AGE - Gr.B») y
        el
        extractor se la llevó dentro del enunciado. El §2 de los ajustes dice que **eso se limpia**:
        no
    es
        una incidencia, es una pregunta con basura al final.

        Se quitan **todas** las que haya pegadas al final, de la última hacia atrás, y no solo una:
        hay
        preguntas con dos seguidas —«… AGE - Gr. C 2016 Técnicos Auxiliares Informática Acceso Libre
        AGE - Gr.C»— y cortar solo la última dejaría la primera dentro del enunciado. La vuelta se
        para
        en cuanto la siguiente no cumple las guardas, así que una pregunta que hable de un examen
        **en
        medio** no se toca.

        Tres guardas, y las tres están por un caso real medido el 13 de octubre de 2026 sobre la
        copia
    de
        la base:

        1. **lo que queda detrás tiene que ser una referencia, no texto**: como mucho 120 caracteres
        y
           ninguna interrogación. Es la guarda que deja fuera las dos coincidencias que no son
    referencias
           —una de 277 caracteres y otra de 7.916, que son un párrafo del BOE que habla de 2025— y
           no
           roza ninguna de las veinte de verdad;
        2. **el enunciado tiene que seguir siendo un enunciado**: si al cortar quedan menos de 20
           caracteres, lo que había era la referencia con un resto delante y no una pregunta;
        3. **el corte tiene que caer en un final de frase**: si lo que queda no termina en `.`, `:`,
    `?`,
           `!` o comilla, la referencia estaba dentro de una frase y quitarla dejaría el enunciado a
           medias. Es lo que impide que «Según la Ley de 2011 Universidades, el plazo es:» pierda su
           principio. Se comprueba **al final** de la vuelta y no en cada paso: entre dos
           referencias
           seguidas el trozo de en medio acaba en el nombre del cuerpo y no cierra ninguna frase, y
           esa
           todavía hay que quitarla.
    """
    actual = stem.strip()
    if not actual:
        return None
    quitada = False
    while True:
        coincidencias = list(PATRON_REFERENCIA_PEGADA.finditer(actual))
        if not coincidencias:
            break
        ultima = coincidencias[-1]
        detras = actual[ultima.end() :].strip(_SEPARADORES)
        if "?" in detras or "¿" in detras or len(detras) > MAXIMO_DETRAS_DE_LA_REFERENCIA:
            break
        recortado = actual[: ultima.start()].rstrip()
        while recortado and recortado[-1] in _SEPARADORES_DE_APERTURA:
            recortado = recortado[:-1].rstrip()
        if len(recortado) < MINIMO_DE_ENUNCIADO:
            break
        actual = recortado
        quitada = True
    if not quitada:
        return None
    # La frase tiene que cerrar **al final**, y solo al final: entre dos referencias seguidas el
    # trozo de en medio acaba en el nombre del cuerpo («… AGE - Gr. C») y no cierra nada, pero la
    # vuelta siguiente se lleva también esa. Comprobarlo en cada vuelta dejaba sin limpiar las
    # preguntas con dos referencias pegadas, que son un caso real y medido.
    if actual[-1] not in ".:;?!»\"'”":
        return None
    return actual


def _partes_de_la_fusion(texto: str) -> tuple[str, str] | None:
    """En qué dos trozos se parte una opción fundida, o `None` si no es una fusión.

    La guarda es lo que separa una fusión de una **mención**: una opción que dice «conforme a lo
    indicado en la opción c)» contiene el patrón de otra opción, pero no está fundida con nada. Se
    distinguen por lo que hay **antes** del patrón: si nombra otra opción, es una mención y no se
    toca.
    """
    coincidencia = PATRON_DE_OPCION.search(texto[1:])
    if coincidencia is None:
        return None
    inicio = coincidencia.start() + 1
    antes = texto[:inicio].strip(_SEPARADORES)
    despues = texto[inicio + len(coincidencia.group(0)) :].strip(_SEPARADORES)
    if len(antes) < MINIMO_DE_TROZO or len(despues) < MINIMO_DE_TROZO:
        return None
    if any(palabra in antes.lower() for palabra in PALABRAS_DE_REFERENCIA):
        return None
    return antes, despues


def partir_opcion_fundida(opciones: Sequence[str]) -> tuple[str, ...] | None:
    """Las opciones con la fundida partida en dos, o `None` si no hay ninguna que partir.

        Se parte **una sola** opción, la primera que esté fundida: partir dos a la vez en una
        pregunta
        reescrita por una regla es demasiado para una regla, y si hay dos, lo que hace falta es
        volver
    al
        original. El caso real que esto arregla está medido: la opción «JOB 0d) CALL» del examen de
        JCL,
        donde «JOB» y «CALL» son dos opciones y el `0d)` es el rótulo de la segunda comido por la
        extracción.
    """
    for indice, texto in enumerate(opciones):
        partes = _partes_de_la_fusion(texto)
        if partes is None:
            continue
        antes, despues = partes
        return (*opciones[:indice], antes, despues, *opciones[indice + 1 :])
    return None


def _por_que_no_se_parte(texto: str) -> str:
    """Por qué una opción con el patrón de otra **no** se parte. Vacío si sí se parte.

        Tres desenlaces y no dos, porque son tres trabajos distintos para el propietario: una
    **mención**
        («… indicado en la opción c)») es una pregunta bien escrita, un **resto** («y c)») es una
        opción
    a
        la que le falta el principio, y una opción **desbordada** es la que se llevó el documento
    dentro.
        Decirle «no se puede» a las tres por igual le dejaría sin saber cuál de las tres tiene
        delante.
    """
    if _partes_de_la_fusion(texto) is not None:
        return ""
    coincidencia = PATRON_DE_OPCION.search(texto[1:])
    if coincidencia is None:
        return ""
    antes = texto[: coincidencia.start() + 1].strip(_SEPARADORES)
    if any(palabra in antes.lower() for palabra in PALABRAS_DE_REFERENCIA):
        return (
            "la opción nombra a otra opción («… en la opción c)») y eso no es una "
            "fusión: la pregunta "
            "está bien escrita y lo que falla es la regla mecánica"
        )
    return (
        "la opción es un resto —le falta el principio o el final— y ninguna regla puede "
        "adivinar el "
        "texto que se perdió"
    )


def _hay_una_opcion_desbordada(opciones: Sequence[str]) -> bool:
    """¿Una opción se tragó el resto del documento?

        Pasó de verdad: en «Doc Adicional» la opción C lleva dentro cuatro disposiciones del BOE,
        sus
        artículos y hasta el pie de página. Ninguna regla puede reconstruir las opciones que se
    perdieron
        ni separar eso sin criterio, así que estas se quedan donde están y la ficha lo dice.
    """
    con_texto = [texto for texto in opciones if texto.strip()]
    if len(con_texto) < 2:
        return False
    otras = sorted(len(texto) for texto in con_texto)
    mediana = otras[len(otras) // 2]
    return max(otras) > max(1500, 8 * max(mediana, 1))


def reparacion_disponible(*, stem: str, opciones: Sequence[str], tipo: str) -> Reparacion | None:
    """La reparación que una regla puede hacer en esta pregunta, o `None` si no hay ninguna.

        Solo dos reglas, y las dos con guarda. Lo que **no** se repara aquí: una opción que se tragó
        el
        documento (`_hay_una_opcion_desbordada`), una opción que es un resto de otra («y c)») y una
    opción
        que falta. Las tres se quedan donde están y la ficha dice por qué en `motivo_de_no_reparar`.
    """
    reglas: list[str] = []
    detalles: list[str] = []
    nuevo_stem = quitar_referencia_del_examen(stem)
    if nuevo_stem is not None:
        reglas.append(REGLA_REFERENCIA_DEL_EXAMEN)
        detalles.append("se quita del enunciado la referencia del examen que quedó pegada al final")
    nuevas_opciones: tuple[str, ...] | None = None
    if not _hay_una_opcion_desbordada(opciones):
        nuevas_opciones = partir_opcion_fundida(opciones)
    if nuevas_opciones is not None:
        reglas.append(REGLA_OPCION_FUNDIDA)
        detalles.append(
            "se parte en dos la opción que se tragó a la siguiente (dos opciones fundidas en una)"
        )
    if not reglas:
        return None
    return Reparacion(
        reglas=tuple(reglas),
        detalle="; ".join(detalles),
        stem=nuevo_stem,
        opciones=nuevas_opciones,
    )


def _regla_mecanica(opciones: Sequence[str], tipo: str) -> str | None:
    """La regla del §2 que señala esta pregunta como mal importada, si alguna.

        La regla es **la misma** que usa la bandeja del motor para clasificar la incidencia
        (`domain/notes_incidents`), y por eso se llama en vez de reescribirse: si mañana la regla
    cambia,
        la ficha y la bandeja cambian juntas. Escribir aquí una copia sería tener dos verdades sobre
        qué
        es una pregunta mal importada.
    """
    return regla_de_mala_importacion(opciones, tipo)


def motivo_de_no_reparar(*, stem: str, opciones: Sequence[str], tipo: str) -> str | None:
    """Por qué una pregunta señalada por el motor **no** se puede reparar con una regla.

        `None` cuando el motor no la señaló: sin señal no hay nada que explicar, y la ficha no
        inventa
    un
        motivo para las preguntas que están bien.

        Los cinco motivos son los cinco casos que hay en los datos medidos, y cada uno es un trabajo
        distinto para el propietario:

        - **una mención no es una fusión**: «las consecuencia indicadas en la opción c)» nombra otra
          opción; la pregunta está bien y lo que falla es la regla mecánica;
        - **un resto sin principio**: «y c)», una opción a la que le falta el texto de delante.
        Ninguna
          regla puede adivinarlo; el caso hermano —«JOB 0d) CALL», con el rótulo comido— sí se
          repara;
        - **una opción desbordada**: se llevó el resto del documento dentro;
        - **dos opciones que solo se diferencian en las mayúsculas**: en una pregunta de
        `LC_COLLATE`
    esa
          diferencia **es** el contenido, así que no hay resto que quitar;
        - **una opción que es el principio de otra**: la más específica incluye a la más general, y
        eso
    es
          cómo estaba escrita la pregunta. Se arregla marcando la respuesta correcta, no
          reescribiendo
    el
          texto.
    """
    regla = _regla_mecanica(opciones, tipo)
    if regla is None:
        return None
    if regla == "menos_de_tres_opciones":
        return (
            "le faltan opciones y ninguna regla puede inventarse las que no están: hay que "
            "volver al "
            "original"
        )
    if regla == "opcion_con_patron_de_otra":
        if _hay_una_opcion_desbordada(opciones):
            return (
                "una opción se llevó el resto del documento dentro: hay que volver a extraerla del "
                "original, no se puede partir a ciegas"
            )
        if partir_opcion_fundida(opciones) is not None:
            return None
        for texto in opciones:
            if PATRON_DE_OPCION.search(texto[1:]):
                return _por_que_no_se_parte(texto)
        return None
    if regla == "opciones_duplicadas":
        return (
            "las dos opciones solo se diferencian en las mayúsculas, y en esta pregunta esa "
            "diferencia "
            "es justo lo que se pregunta: no hay ningún resto que quitar"
        )
    if regla == "opcion_truncada":
        return (
            "una opción es el principio de otra y así estaba escrita la pregunta (la más "
            "específica "
            "incluye a la más general): se arregla marcando la respuesta correcta, no el texto"
        )
    return None


def letras_de_opcion(opciones: Sequence[str]) -> tuple[str, ...]:
    """Las letras que **existen** en esta pregunta, en orden: `a`, `b`, `c`…

        Es lo que valida una respuesta correcta nueva: escribir `d` en una pregunta de tres opciones
        es
    un
        error de quien llama, y se contesta antes de tocar la base. El orden es el de las opciones,
        que
    es
        el que usa el alumno para contestar.
    """
    return tuple(chr(ord("a") + indice) for indice in range(len(opciones)))


def normalizar_letras(letras: Sequence[str]) -> tuple[str, ...]:
    """Las letras tal como se guardan: minúsculas, sin repetir y en orden alfabético.

        La base guarda la clave como una lista JSON de claves de opción («a», «b»), y el usuario las
        escribe como quiera. Normalizar aquí —y no en cada sitio que compara— es lo que hace que
        `["C"]` y `["c"]` sean la misma respuesta: si no, la comprobación de «la letra de los
        apuntes
    está
        en la clave» fallaría por una mayúscula.
    """
    vistas: list[str] = []
    for letra in letras:
        limpia = letra.strip().lower()
        if limpia and limpia not in vistas:
            vistas.append(limpia)
    return tuple(sorted(vistas))


def letras_que_no_existen(*, pedidas: Sequence[str], disponibles: Sequence[str]) -> tuple[str, ...]:
    """Las letras pedidas que la pregunta no tiene: lo que hay que rechazar antes de escribir."""
    existentes = set(normalizar_letras(disponibles))
    return tuple(letra for letra in normalizar_letras(pedidas) if letra not in existentes)


__all__ = [
    "MAXIMO_DETRAS_DE_LA_REFERENCIA",
    "MINIMO_DE_ENUNCIADO",
    "PALABRAS_DE_REFERENCIA",
    "PATRON_DE_OPCION",
    "PATRON_REFERENCIA_PEGADA",
    "REGLA_OPCION_FUNDIDA",
    "REGLA_REFERENCIA_DEL_EXAMEN",
    "TIPO_OFICIAL",
    "TITULO_DE_REGLA",
    "Reparacion",
    "letras_de_opcion",
    "letras_que_no_existen",
    "motivo_de_no_reparar",
    "normalizar_letras",
    "partir_opcion_fundida",
    "protege_cambiar_la_clave",
    "quitar_referencia_del_examen",
    "reparacion_disponible",
]
