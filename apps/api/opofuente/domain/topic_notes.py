"""Los apuntes de un tema, escritos a partir de sus preguntas y comprobados con ellas (pasos B-E).

Este módulo es **la decisión**, y no sabe ni de red ni de base de datos. Es lo que hace el trabajo
de
apuntes que pide `APUNTES-COMPLETOS-GUIADOS-POR-PREGUNTAS-2026-10`:

1. **los hechos** (paso B): de cada grupo de preguntas, de una a tres frases afirmativas que,
sabidas,
   permiten acertar la pregunta. La respuesta de la plantilla viaja al modelo porque sin ella el
   hecho
   no se puede anclar; si esa respuesta contradice la norma, el hecho lo dice y la pregunta queda
   señalada (`dudosa`) en vez de escribirse como si la clave fuera buena;
2. **el esquema** (paso C): los epígrafes oficiales son los apartados; un epígrafe con más hechos de
   los que caben en una llamada se parte en subapartados numerados. **Ningún hecho se queda sin
   apartado** y el reparto es determinista (mismo tema y mismos hechos dan el mismo esquema), que es
   lo que permite reanudar una corrida y volver a comprobar sin que cambien los anclajes;
3. **la redacción** (paso D): un apartado se escribe con **todos** sus hechos y el material del tema
   al que se parecen;
4. **la comprobación** (paso E): al modelo se le dan **solo** los apuntes y la pregunta; tiene que
   contestar la letra y copiar la frase exacta que la justifica. La frase se comprueba
   **mecánicamente**
   contra el texto de los apuntes (`verificar_cita`): el criterio no es lo que el modelo diga que
   hay,
   es lo que hay. Lo que no se puede comprobar no se da por cubierto.

Vocabulario del resultado, y es el del informe: **cubierta** (la frase está y la letra coincide
con la clave; sin ninguna clave, basta la frase), **hueco** (no está: se añade lo que falta y se
vuelve a comprobar), **conflicto** (la frase está y la letra **no** coincide con la clave, activa o
en borrador: o la clave está mal o los apuntes, y eso se revisa, no se da por bueno) y **dudosa**
(la clave contradice el material, la clave no está clara, o tras dos vueltas la frase sigue sin
aparecer). El paso E del plan llama «incidencia» al estado final que aquí se guarda como `dudosa`.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

from opofuente.domain.puertos import familias_para_el_prompt
from opofuente.domain.rag import STOPWORDS, normalise
from opofuente.domain.topic_classification import (
    PRECIO_ENTRADA_USD_POR_MILLON,
    PRECIO_SALIDA_USD_POR_MILLON,
)

#: Versión de las plantillas de instrucciones. Va con cada apartado guardado: un texto escrito con
#: otras instrucciones no es comparable con el que salga de estas. Sube cuando cambie lo que se le
#: pide al redactor: la v2 añade el **tope de extensión** del apartado.
VERSION_PLANTILLA = "apuntes-2"

#: Tope de extensión de un apartado: palabras por **hecho distinto**. Es la puerta de densidad del
#: §2.3, y vive aquí —y no solo en la revisión de forma— porque el redactor tiene que saberlo
#: **antes** de escribir: `notes_quality` la importa de aquí y el encargo la dice en palabras.
MAX_PALABRAS_POR_HECHO = 40

#: Preguntas por llamada al pedir hechos (el paso B del plan mide ≈20).
LOTE_HECHOS = 20

#: Preguntas por llamada al comprobar (paso E). El texto de los apuntes es el mismo para todas las
#: preguntas de un epígrafe y va en el mensaje de sistema, así que agruparlas abarata la entrada.
LOTE_COMPROBACION = 10

#: Hechos por apartado. Por encima de esto el epígrafe se parte en subapartados: una llamada que
#: pida
#: integrar doscientos hechos devuelve un texto peor que cuatro llamadas de cuarenta.
MAX_HECHOS_POR_APARTADO = 40

#: Longitud mínima de una cita para que cuente como justificación. Una frase de tres palabras
#: («el artículo 29») aparece en cualquier parte por casualidad y no justifica nada.
MINIMO_CITA = 20

#: Material que se le da al redactor: los pasajes del tema que más se parecen a los hechos del
#: apartado, con topes de número y de caracteres para que la llamada no se dispare.
MAX_MATERIAL_PASAJES = 12
MAX_MATERIAL_CARACTERES = 24_000

#: Proporción de términos de un hecho que tiene que aparecer en el texto para darlo por integrado.
#: Es una comprobación **de presencia**, no de sentido: el sentido lo juzga la comprobación del paso
#: E
#: y, al final, el propietario.
MINIMO_TERMINOS_INTEGRADOS = 0.6

#: Vueltas de comprobación. La primera es la comprobación entera; la segunda, solo los huecos; y la
#: tercera —`VUELTAS_CON_HUECOS`— el **bucle de huecos** del §2.1.4, que se hace una sola vez sobre
#: lo que quedó sin frase en los apuntes. Más vueltas sobre el mismo hueco no lo rellenan: lo tapan.
VUELTAS_MAXIMAS = 2
VUELTAS_CON_HUECOS = 3

#: Cobertura mínima para publicar un tema: preguntas cubiertas sobre las que tienen **clave
#: utilizable**. Es la puerta del §2.3, y el denominador importa tanto como el umbral: una pregunta
#: cuya respuesta marcada contradice la norma no tiene una respuesta con la que se pueda acertar,
#: así que contarla en contra de los apuntes sería culpar al texto de un fallo del banco. El número
#: se mide y se enseña **siempre**, también cuando el tema queda en borrador.
COBERTURA_MINIMA = 0.90

#: Lo que se marca en un apartado escrito sin material de apoyo. Es lo que el propietario busca al
#: revisar, y el redactor escribe la misma marca dentro del párrafo.
SIN_MATERIAL = "sin material de apoyo"

#: Lo que se marca en un apartado al que le han llegado hechos nuevos después de escribirlo.
HECHOS_NUEVOS = "hechos nuevos sin integrar"

#: Mínimo de palabras de un añadido. Un añadido de cero palabras no rellena nada, y el bucle de
#: huecos existe para rellenar: por debajo de esto no se baja, aunque el apartado esté en su tope.
MINIMO_PALABRAS_ANADIDO = 60


class FactKind(StrEnum):
    """Si el hecho cita una norma o no. Se guarda porque el propietario revisa distinto cada uno."""

    NORMATIVO = "normativo"
    TECNICO = "tecnico"


class NotesState(StrEnum):
    """Qué se puede decir de los apuntes de un tema **en la zona del alumno**.

    Son tres estados y no dos porque «no tiene apuntes» y «los tiene sin publicar» se leen distinto:
    al primero no se puede entrar a leer, y el segundo se lee igual que el publicado pero **diciendo
    que es un borrador** (el tema no pasó las dos puertas del §2.3 y su versión no se archivó).

    Lo decide el par (¿hay apartados escritos?, ¿hay versión archivada?):

    - sin apartados: `NONE`, y la pantalla dice que todavía no hay apuntes de ese tema;
    - con apartados y sin versión: `DRAFT`;
    - con apartados y con versión: `PUBLISHED`.
    """

    NONE = "none"
    DRAFT = "draft"
    PUBLISHED = "published"


class KeyStatus(StrEnum):
    """Qué se puede decir de la respuesta correcta de una pregunta.

    Es la diferencia que decide si la letra del modelo se puede usar como criterio: con una clave
    **activa** sí (es la que corrige los tests); con una **en borrador** también se compara —una
    letra distinta de la clave es un conflicto, no una cobertura—, pero se anota su estado, porque
    hay conjuntos cuya plantilla está desalineada y el conflicto puede ser de la clave; **sin
    ninguna** entrada no hay letra contra la que comparar y manda la frase.
    """

    ACTIVE = "active"
    DRAFT = "draft"
    NINGUNA = "ninguna"

    @property
    def clara(self) -> bool:
        return self is KeyStatus.ACTIVE


class Coverage(StrEnum):
    """El resultado final de una pregunta frente a los apuntes. Es lo que cuenta el informe.

    `conflict` es el que faltaba y el que destapó la revisión del propietario: **una letra distinta
    de la clave no es una pregunta cubierta**. Los apuntes contestan «b» y la plantilla dice «a»; o
    la clave está mal o los apuntes, y ninguna de las dos cosas se arregla dando la pregunta por
    buena. Con clave **activa** el resultado ya terminaba en duda; con clave **en borrador** entraba
    como cubierta, y eran 96 preguntas de los tres pilotos contadas de más.
    """

    CUBIERTA = "covered"
    HUECO = "gap"
    DUDOSA = "doubtful"
    CONFLICTO = "conflict"


class Motivo(StrEnum):
    """Por qué una pregunta no queda cubierta. Se guarda con el resultado, no como texto libre.

    Los dos primeros motivos son de los **apuntes** (hay que añadir o reescribir); los dos últimos,
    de la **clave** (la pregunta se revisa en el panel, no se arregla escribiendo más).

    `SIN_MATERIA_EN_EL_INDICE` es el quinto y no es ninguno de los dos: la pregunta no se puede
    situar en ninguna materia del tema ni por su enunciado ni por el texto de sus hechos, así que no
    hay apartado en el que escribirla. Antes esto **paraba la corrida** diciendo que era una
    pregunta
    mal clasificada; ahora va a la bandeja del propietario con su motivo, que es lo que se pidió: lo
    que no se puede situar se le enseña a él, no se esconde en un cajón de «otros» ni bloquea el
    tema
    entero por diez preguntas.
    """

    SIN_FRASE_EN_LOS_APUNTES = "sin_frase_en_los_apuntes"
    LETRA_NO_COINCIDE = "letra_no_coincide"
    CLAVE_CONTRADICE_LA_NORMA = "clave_contradice_la_norma"
    CLAVE_SIN_DEFINIR = "clave_sin_definir"
    SIN_MATERIA_EN_EL_INDICE = "sin_materia_en_el_indice"

    @property
    def es_de_los_apuntes(self) -> bool:
        """¿El motivo se arregla escribiendo mejor los apuntes?"""
        return self in (Motivo.SIN_FRASE_EN_LOS_APUNTES, Motivo.LETRA_NO_COINCIDE)


class CategoriaIncidencia(StrEnum):
    """La categoría con la que una pregunta que no queda cubierta va a la bandeja del propietario.

    Es el vocabulario del §2.1.4 del objetivo, y son cuatro porque son cuatro trabajos distintos: al
    primero se le escribe más material, al segundo se le revisa la clave, al tercero hay que
    reescribir la pregunta y al cuarto hay que comprobar qué dice hoy la norma. Una incidencia sin
    categoría no se puede despachar, y por eso «conflictos de letra sin categorizar» es una puerta.

    Desde el §2 de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md` son **seis**, porque se midió que
    el motor ponía mal la etiqueta de dos clases enteras de lo que dejaba en la bandeja:

    - `pregunta_mal_importada`: la pregunta está rota por su **forma** —le faltan opciones, dos
      quedaron fundidas, una es el principio de otra— y eso no se arregla mirando la clave;
    - `clave_no_fiable`: la pregunta es de un conjunto con la clave en cuarentena (§1), y mientras
    lo
      esté lo que diga de los apuntes no es una incidencia de los apuntes.

    Las dos las asigna **la reclasificación** (`domain/notes_incidents.py`), no el motor: el motor
    sigue poniendo las cuatro de siempre.
    """

    HUECO_SIN_MATERIAL = "hueco_sin_material"
    CLAVE_SOSPECHOSA = "clave_sospechosa"
    PREGUNTA_AMBIGUA = "pregunta_ambigua"
    NORMA_CAMBIADA = "norma_cambiada"
    PREGUNTA_MAL_IMPORTADA = "pregunta_mal_importada"
    CLAVE_NO_FIABLE = "clave_no_fiable"


#: Qué categoría le toca a cada motivo. El motivo dice **qué pasó**; la categoría, **quién lo
#: arregla**. Un hueco es trabajo de los apuntes; una letra que no coincide, de la clave; una clave
#: que contradice la norma, de la norma; y una pregunta sin clave no se puede juzgar.
CATEGORIA_POR_MOTIVO: dict[Motivo, CategoriaIncidencia] = {
    Motivo.SIN_FRASE_EN_LOS_APUNTES: CategoriaIncidencia.HUECO_SIN_MATERIAL,
    Motivo.LETRA_NO_COINCIDE: CategoriaIncidencia.CLAVE_SOSPECHOSA,
    Motivo.CLAVE_CONTRADICE_LA_NORMA: CategoriaIncidencia.NORMA_CAMBIADA,
    Motivo.CLAVE_SIN_DEFINIR: CategoriaIncidencia.PREGUNTA_AMBIGUA,
    # Una pregunta que no se puede situar en el índice se arregla reescribiéndola o asignándola a
    # mano: es trabajo del propietario sobre la pregunta, no sobre los apuntes.
    Motivo.SIN_MATERIA_EN_EL_INDICE: CategoriaIncidencia.PREGUNTA_AMBIGUA,
}


@dataclass(frozen=True, slots=True)
class IncidenciaDeApuntes:
    """Una pregunta que los apuntes no cubren, con su categoría, su motivo y la frase que lo prueba.

    `frase` es la cita **verificada** de los apuntes cuando la hay (el conflicto de letra la
    tiene: es la frase que sostiene otra opción que la clave). Sin ella, la incidencia sigue siendo
    válida: hay huecos que no tienen frase porque el dato no está escrito.
    """

    question_version_id: str
    group_signature: str
    category: CategoriaIncidencia
    reason: Motivo
    detail: str
    section_key: str = ""
    anchor: str = ""
    phrase: str | None = None


def categoria_de(coverage: Coverage, motivo: Motivo | None) -> CategoriaIncidencia | None:
    """La categoría de una pregunta que no quedó cubierta, o `None` si sí lo quedó."""
    if coverage is Coverage.CUBIERTA or coverage is Coverage.HUECO:
        return None
    if motivo is None:
        return CategoriaIncidencia.PREGUNTA_AMBIGUA
    return CATEGORIA_POR_MOTIVO.get(motivo, CategoriaIncidencia.PREGUNTA_AMBIGUA)


#: Qué se le dice al propietario de cada categoría: es lo que va a leer en la bandeja.
TEXTO_DE_CATEGORIA: dict[CategoriaIncidencia, str] = {
    CategoriaIncidencia.HUECO_SIN_MATERIAL: (
        "los apuntes no contienen el dato ni se ha podido rellenar en las tres vueltas: falta "
        "material de estudio para esta pregunta"
    ),
    CategoriaIncidencia.CLAVE_SOSPECHOSA: (
        "los apuntes sí contestan la pregunta, y con otra letra que su clave: hay que mirar "
        "cuál de las dos está mal"
    ),
    CategoriaIncidencia.PREGUNTA_AMBIGUA: (
        "la pregunta no tiene clave con la que comprobarla: no se puede decidir si los apuntes la "
        "contestan"
    ),
    CategoriaIncidencia.NORMA_CAMBIADA: (
        "la clave contradice la norma o el material de estudio: hay que comprobar qué dice hoy la "
        "norma"
    ),
    CategoriaIncidencia.PREGUNTA_AMBIGUA: (
        "la pregunta no tiene clave con la que comprobarla: no se puede decidir si los apuntes la "
        "contestan"
    ),
    CategoriaIncidencia.PREGUNTA_MAL_IMPORTADA: (
        "la pregunta está rota por su forma —le faltan opciones, dos quedaron fundidas o una es el "
        "principio de otra—: antes de mirar la clave hay que arreglar la pregunta, y lo que no se "
        "pueda reparar con una regla no entra en los tests"
    ),
    CategoriaIncidencia.CLAVE_NO_FIABLE: (
        "la clave de esta pregunta es de un conjunto en cuarentena (más del 30 % de sus claves "
        "contradicen los apuntes): no se usa para corregir ni cuenta para la cobertura hasta que "
        "se arregle, así que lo que diga de los apuntes no es una incidencia de los apuntes"
    ),
}

#: Lo que se le dice al propietario cuando la pregunta no cabe en **ninguna** materia del tema: ni
#: su enunciado ni sus hechos dicen de qué habla. No es un hueco de los apuntes —no hay apartado
#: donde escribirla— ni una clave sospechosa: es una pregunta que necesita que él decida dónde va.
TEXTO_SIN_MATERIA = (
    "la pregunta no se puede situar en ninguna materia del tema ni por su enunciado ni por el "
    "texto de sus hechos: no hay apartado de apuntes donde contestarla, así que hay que "
    "reescribirla o asignarle un tema a mano (no se ha metido en ningún cajón de «otros»)"
)


def detalle_de_incidencia(resultado: NotesCheck, grupo: QuestionGroup | None) -> str:
    """La frase que el propietario lee en la bandeja: qué pasa, con qué pregunta y con qué prueba.

    No es un volcado: es la pregunta, la letra que dieron los apuntes frente a la clave, y la frase
    verificada cuando la hay. Con eso se puede decidir sin abrir la base.
    """
    categoria = categoria_de(resultado.coverage, resultado.note)
    partes = [TEXTO_DE_CATEGORIA.get(categoria, "sin categoría") if categoria else "sin categoría"]
    if grupo is not None:
        partes.append(f"pregunta: {grupo.representative.stem.strip()[:300]}")
        esperadas = ", ".join(grupo.correct_keys) or "sin clave"
        partes.append(
            f"clave: {esperadas} ({grupo.key_status.value}) · los apuntes dicen: "
            f"{resultado.letter or 'no contestan'}"
        )
    if resultado.quote:
        partes.append(f"frase de los apuntes: «{resultado.quote[:400]}»")
    partes.append(f"vueltas: {resultado.attempts}")
    return "\n".join(partes)


# --- las preguntas y sus grupos -------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class QuestionForNotes:
    """Una pregunta del tema, con lo justo para escribir apuntes a partir de ella.

    La respuesta correcta **sí** viaja aquí (a diferencia del clasificador, que no la necesita): sin
    ella el hecho no se puede anclar en lo que la pregunta pregunta. Su estado (`key_status`) dice
    cuánto se puede fiar uno de esa respuesta.
    """

    question_version_id: str
    set_id: str
    stem: str
    options: tuple[tuple[str, str], ...]
    correct_keys: tuple[str, ...]
    key_status: KeyStatus
    epigraph_code: str | None
    mapping_status: str

    @property
    def signature(self) -> str:
        """Firma del grupo: enunciado y opciones normalizados. Las repetidas se trabajan una vez."""
        return firma_de_grupo(self.stem, self.options)


@dataclass(frozen=True, slots=True)
class QuestionGroup:
    """Las preguntas que son la misma (mismo enunciado y mismas opciones), en un solo grupo."""

    signature: str
    epigraph_code: str | None
    questions: tuple[QuestionForNotes, ...]

    @property
    def representative(self) -> QuestionForNotes:
        return self.questions[0]

    @property
    def question_ids(self) -> tuple[str, ...]:
        return tuple(pregunta.question_version_id for pregunta in self.questions)

    @property
    def key_status(self) -> KeyStatus:
        """El mejor estado de clave del grupo: la primera pregunta con clave activa manda."""
        for estado in (KeyStatus.ACTIVE, KeyStatus.DRAFT):
            if any(pregunta.key_status is estado for pregunta in self.questions):
                return estado
        return KeyStatus.NINGUNA

    @property
    def correct_keys(self) -> tuple[str, ...]:
        """La respuesta del **mismo** estado que manda: no se mezcla la clave activa con una en
        borrador, que es como se compararía una letra contra la plantilla equivocada."""
        mejor = self.key_status
        for pregunta in self.questions:
            if pregunta.key_status is mejor and pregunta.correct_keys:
                return pregunta.correct_keys
        return ()


def firma_de_grupo(stem: str, options: Sequence[tuple[str, str]] = ()) -> str:
    """Firma estable de un grupo de preguntas iguales: enunciado y opciones normalizados.

    Se normaliza igual que el resto del proyecto (`rag.normalise`: sin acentos, sin signos, en
    minúsculas), así que dos preguntas que solo se diferencian en la puntuación o en el orden de las
    tildes caen en el mismo grupo y se trabajan una vez.
    """
    cuerpo = (
        normalise(stem)
        + " || "
        + " | ".join(f"{clave}: {normalise(texto)}" for clave, texto in options)
    )
    return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()[:32]


def agrupar(preguntas: Sequence[QuestionForNotes]) -> tuple[QuestionGroup, ...]:
    """Agrupa por firma conservando el orden de entrada, que es el de la publicación."""
    grupos: dict[str, list[QuestionForNotes]] = {}
    for pregunta in preguntas:
        grupos.setdefault(pregunta.signature, []).append(pregunta)
    return tuple(
        QuestionGroup(
            signature=firma,
            epigraph_code=next(
                (p.epigraph_code for p in miembros if p.epigraph_code is not None), None
            ),
            questions=tuple(miembros),
        )
        for firma, miembros in grupos.items()
    )


# --- los hechos (paso B) --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Hecho:
    """Una frase afirmativa y comprobable que, sabida, permite acertar una pregunta.

    `source_groups` es el rastro: de qué grupos de preguntas salió. Se guarda para poder decir qué
    preguntas sostiene cada apartado y para no volver a pedir hechos de un grupo ya trabajado.
    `section_key` dice en qué apartado se integró; lo pone el repositorio al repartir los hechos.
    """

    text: str
    kind: FactKind
    epigraph_code: str
    source_groups: tuple[str, ...] = ()
    source_questions: tuple[str, ...] = ()
    doubtful: bool = False
    note: str | None = None
    fact_id: str = ""
    section_key: str = ""

    @property
    def terms(self) -> tuple[str, ...]:
        """Los términos del hecho, sin palabras vacías: es lo que se busca en el texto escrito."""
        return terminos_significativos(self.text)


@dataclass(frozen=True, slots=True)
class HechosBatch:
    """Los hechos que devolvió el modelo para un lote, con lo que costó pedirlos.

    `sin_hechos` son los identificadores que el modelo no contestó: se cuentan, porque un lote con
    huecos explica por qué faltan hechos y no se puede confundir con «ya estaba hecho».
    """

    hechos: tuple[Hecho, ...]
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit_tokens: int = 0
    sin_hechos: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RedaccionBatch:
    """Un apartado redactado por el modelo."""

    titulo: str | None
    markdown: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit_tokens: int = 0


@dataclass(frozen=True, slots=True)
class QuoteCheck:
    """Lo que el modelo contestó sobre **una** pregunta en la comprobación: letra y cita literal."""

    group_signature: str
    letter: str | None
    quote: str | None


@dataclass(frozen=True, slots=True)
class ComprobacionBatch:
    """Las comprobaciones de un lote, con lo que costaron."""

    checks: tuple[QuoteCheck, ...]
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit_tokens: int = 0
    sin_respuesta: tuple[str, ...] = ()


# --- el esquema (paso C) --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NoteSection:
    """Un apartado de los apuntes: su epígrafe, su anclaje estable y los hechos que tiene que
    llevar.

    `key` y `anchor` son lo mismo a propósito: el anclaje es la clave del subapartado, así que se
    puede enlazar una pregunta a un párrafo sin resolver nada por el camino.

    `encabezados_ya_usados` son los títulos que ya están puestos **en los otros trozos de su misma
    materia**: una materia que no cabe en una llamada se parte, y sin esto cada trozo escribe su
    propio índice y los dos escriben el mismo (le pasó a I.1: «2. Composición de las Cámaras» en los
    dos trozos de las Cortes Generales). Va en el apartado y no en la firma del motor, para no
    cambiar el puerto por un dato del reparto.
    """

    key: str
    epigraph_code: str
    title: str
    anchor: str
    position: int
    facts: tuple[Hecho, ...] = ()
    body_markdown: str = ""
    needs_review_reason: str | None = None
    section_id: str = ""
    encabezados_ya_usados: tuple[str, ...] = ()


def slug(codigo: str) -> str:
    """El código oficial convertido en anclaje: `IV.7.1` → `iv-7-1`."""
    limpio = normalise(codigo.replace(".", " "))
    return re.sub(r"[^a-z0-9]+", "-", limpio).strip("-")


def esquema(
    epigraphs: Sequence[tuple[str, str]], hechos: Sequence[Hecho]
) -> tuple[NoteSection, ...]:
    """El esquema del tema: un apartado por epígrafe y, si no caben, subapartados numerados.

    Decisiones que se ven en el resultado:

    - **el orden es el del temario oficial**, no el de llegada de los hechos: los apuntes se leen en
      el orden en que se estudia el tema;
    - un epígrafe **sin hechos no genera apartado**: un apartado vacío no es un apartado, es un
      hueco, y los huecos ya los declara el dossier;
    - los hechos de un epígrafe se parten en trozos de `MAX_HECHOS_POR_APARTADO` **en orden**, para
      que dos corridas den el mismo esquema;
    - un hecho con un epígrafe que no está en el temario **no se pierde**: va a un último apartado
      («Otros contenidos del tema») que el propietario puede revisar. Perder un hecho en silencio
      sería justo lo contrario de lo que se pide.
    """
    por_epigrafe: dict[str, list[Hecho]] = {}
    for hecho in hechos:
        por_epigrafe.setdefault(hecho.epigraph_code, []).append(hecho)

    apartados: list[NoteSection] = []
    posicion = 1
    for codigo, titulo in epigraphs:
        suyos = por_epigrafe.pop(codigo, [])
        if not suyos:
            continue
        trozos = list(_trozos(suyos, MAX_HECHOS_POR_APARTADO))
        for indice, trozo in enumerate(trozos, start=1):
            clave = slug(codigo) if len(trozos) == 1 else f"{slug(codigo)}-{indice}"
            nombre = titulo if len(trozos) == 1 else f"{titulo} ({indice}/{len(trozos)})"
            apartados.append(
                NoteSection(
                    key=clave,
                    epigraph_code=codigo,
                    title=nombre,
                    anchor=clave,
                    position=posicion,
                    facts=tuple(trozo),
                )
            )
            posicion += 1

    resto = [hecho for codigo in list(por_epigrafe) for hecho in por_epigrafe[codigo]]
    if resto:
        for indice, trozo in enumerate(_trozos(resto, MAX_HECHOS_POR_APARTADO), start=1):
            clave = "otros-contenidos" if indice == 1 else f"otros-contenidos-{indice}"
            apartados.append(
                NoteSection(
                    key=clave,
                    epigraph_code=sorted({h.epigraph_code for h in trozo})[0],
                    title="Otros contenidos del tema (sin epígrafe oficial)",
                    anchor=clave,
                    position=posicion,
                    facts=tuple(trozo),
                    needs_review_reason="hechos con un epígrafe que no está en el temario",
                )
            )
            posicion += 1
    return tuple(apartados)


def _trozos(elementos: Sequence[Hecho], tamano: int) -> Iterable[list[Hecho]]:
    for inicio in range(0, len(elementos), tamano):
        yield list(elementos[inicio : inicio + tamano])


# --- el material ----------------------------------------------------------------------------------


class MaterialInput(Protocol):
    """Lo que el indexador necesita de un tramo del material, sin depender del dossier.

    Es un protocolo y no el tipo del dossier a propósito: el dossier importa este módulo (los
    apuntes van dentro de la versión del tema), así que aquí no se puede importar el dossier sin
    cerrar un ciclo. Las propiedades son de **solo lectura**, que es lo que permite que un
    `PassageFacts` (inmutable) encaje sin obligar a nadie a heredar de nada.
    """

    @property
    def evidence_id(self) -> str: ...

    @property
    def document_title(self) -> str: ...

    @property
    def citation_label(self) -> str | None: ...

    @property
    def page(self) -> int | None: ...

    @property
    def text(self) -> str: ...


@dataclass(frozen=True, slots=True)
class MaterialPassage:
    """Un tramo del material del tema, ya troceado en términos para poder ordenarlo por parecido."""

    evidence_id: str
    document_title: str
    citation_label: str | None
    page: int | None
    text: str
    terms: frozenset[str]

    @property
    def referencia(self) -> str:
        """Cómo se cita el pasaje al dárselo al redactor."""
        if self.citation_label:
            return self.citation_label
        if self.page is not None:
            return f"{self.document_title}, pág. {self.page}"
        return self.document_title


def terminos_significativos(texto: str) -> tuple[str, ...]:
    """Los términos que cuentan para comparar dos textos: sin palabras vacías y sin repetidos.

    Las cifras cuentan aunque sean de un dígito: «artículo 5» y «plazo de 5 días» se distinguen por
    ese número, y tirarlo convertiría dos hechos distintos en el mismo.
    """
    palabras = [palabra for palabra in normalise(texto).split() if palabra not in STOPWORDS]
    return tuple(
        dict.fromkeys(palabra for palabra in palabras if len(palabra) > 2 or palabra.isdigit())
    )


def indexar_material(pasajes: Sequence[MaterialInput]) -> tuple[MaterialPassage, ...]:
    """Prepara el material del tema una sola vez: el tema grande tiene miles de tramos y volver a
    trocearlos por cada apartado costaría más que escribir los apuntes."""
    return tuple(
        MaterialPassage(
            evidence_id=pasaje.evidence_id,
            document_title=pasaje.document_title,
            citation_label=pasaje.citation_label,
            page=pasaje.page,
            text=pasaje.text,
            terms=frozenset(terminos_significativos(pasaje.text)),
        )
        for pasaje in pasajes
    )


def seleccionar_material(
    hechos: Sequence[Hecho],
    material: Sequence[MaterialPassage],
    *,
    max_pasajes: int = MAX_MATERIAL_PASAJES,
    max_caracteres: int = MAX_MATERIAL_CARACTERES,
) -> tuple[MaterialPassage, ...]:
    """Los pasajes del tema que más se parecen a lo que hay que escribir, en orden estable.

    Se ordena por número de términos compartidos y, a igualdad, por documento y página, para que dos
    corridas den el mismo material. Un pasaje que no comparte **ningún** término no se manda: darle
    al
    redactor cien tramos que no hablan de lo que escribe solo le invita a copiar de donde no toca.
    """
    buscados: set[str] = set()
    for hecho in hechos:
        buscados.update(hecho.terms)
    if not buscados:
        return ()
    puntuados: list[tuple[int, str, int, str, MaterialPassage]] = []
    for pasaje in material:
        comunes = len(pasaje.terms & buscados)
        if comunes == 0:
            continue
        puntuados.append(
            (
                comunes,
                pasaje.document_title,
                pasaje.page or 0,
                pasaje.evidence_id,
                pasaje,
            )
        )
    puntuados.sort(key=lambda fila: (-fila[0], fila[1], fila[2], fila[3]))
    elegidos: list[MaterialPassage] = []
    caracteres = 0
    for _, _, _, _, pasaje in puntuados:
        if len(elegidos) >= max_pasajes:
            break
        if caracteres + len(pasaje.text) > max_caracteres and elegidos:
            break
        elegidos.append(pasaje)
        caracteres += len(pasaje.text)
    return tuple(elegidos)


def hechos_integrados(hechos: Sequence[Hecho], texto: str) -> tuple[str, ...]:
    """Qué hechos **no** aparecen en el texto escrito, por sus términos.

    Se exige que estén la mayoría de los términos significativos del hecho. Es una comprobación de
    presencia: sirve para que un hecho obligatorio no se quede por el camino sin que nadie lo diga,
    no
    para juzgar si el texto lo explica bien (eso es la comprobación del paso E y el propietario).
    """
    presentes = set(normalise(texto).split())
    faltan: list[str] = []
    for hecho in hechos:
        terminos = hecho.terms
        if not terminos:
            continue
        encontrados = sum(1 for termino in terminos if termino in presentes)
        if encontrados / len(terminos) < MINIMO_TERMINOS_INTEGRADOS:
            faltan.append(hecho.fact_id or hecho.text[:60])
    return tuple(faltan)


# --- la comprobación (paso E) ---------------------------------------------------------------------


def _sin_marcas(texto: str) -> str:
    """Texto de apuntes sin lo que no se lee: comentarios de revisión y marcas de markdown.

    Los comentarios `<!-- revisar: … -->` están en el markdown pero no en lo que lee el opositor,
    así
    que no pueden servir para justificar una respuesta. Las marcas de énfasis y las barras de tabla
    sí
    se leen (una tabla se lee), y por eso se quitan **de los dos lados** de la comparación.
    """
    sin_comentarios = re.sub(r"<!--.*?-->", " ", texto, flags=re.DOTALL)
    return re.sub(r"[*_`#>|]+", " ", sin_comentarios)


def verificar_cita(cita: str | None, apuntes: str) -> bool:
    """¿La frase que copió el modelo está de verdad en los apuntes?

    La comparación es mecánica —normalizar y buscar— y no pasa por el criterio del modelo: un modelo
    al que se le pregunta si su propia respuesta está en el texto contesta que sí con demasiada
    facilidad. Una cita más corta que `MINIMO_CITA` no cuenta, aunque aparezca.
    """
    if not cita:
        return False
    limpia = normalise(_sin_marcas(cita))
    if len(limpia) < MINIMO_CITA:
        return False
    return limpia in normalise(_sin_marcas(apuntes))


def huella_de_texto(texto: str) -> str:
    """La huella del texto que se comprobó: es la clave de la caché del paso E.

    Una comprobación guardada **solo** vale para el texto contra el que se verificó. Comparar la
    huella es lo que impide reutilizar la cita de un apartado que después se ha reescrito: sin esto,
    la bandeja del propietario enseñaba frases que ya no están en los apuntes (le pasó a I.6, cuyo
    texto se rehizo después de comprobarlo).
    """
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def evaluar(
    *,
    grupo: QuestionGroup,
    check: QuoteCheck | None,
    apuntes: str,
    section: NoteSection,
    attempts: int,
    clave_dudosa: bool = False,
) -> NotesCheck:
    """Decide el resultado de una pregunta frente a los apuntes, con las reglas del paso E.

    El orden importa:

    1. si el paso B marcó la clave como contraria a la norma, la letra **no** decide nunca: la clave
       que se sabe mala no puede convertir un acierto en un fallo, y la pregunta queda como
       incidencia de la pregunta (con la frase o sin ella);
    2. **sin frase** que aparezca en el texto → hueco (y, agotadas las vueltas, duda con su motivo):
       lo que no se puede citar no se da por cubierto;
    3. con la frase verificada y **clave** (activa o en borrador), la letra tiene que coincidir: si
       no coincide —o si el modelo no dijo ninguna— el resultado es **conflicto**, no cobertura;
    4. con la frase verificada y **sin ninguna clave** no hay letra contra la que comparar, así que
       manda la frase.

    La regla 3 es la que cambió. Antes, una clave en borrador daba por cubierta cualquier pregunta
    con la frase, aunque el modelo hubiera contestado otra letra: 96 preguntas de los tres pilotos
    contaban como cubiertas diciendo lo contrario que su plantilla, y una letra distinta de la clave
    es justo lo que hay que mirar (o la clave está mal, o los apuntes), no lo que se da por bueno.

    A la primera vuelta un desacuerdo de letra se queda en **hueco** —el añadido puede ser lo que
    falta para que la respuesta correcta se vea—; agotadas las vueltas es un **conflicto**, porque
    escribir más no arregla una clave que dice otra cosa.

    Al agotar las vueltas, un hueco se convierte en **dudosa**: el plan llama incidencia a lo que
    sigue fallando tras dos vueltas, y distinguirlo de «cubierta» es lo que evita dar por bueno un
    tema que no lo está.
    """
    letra = None if check is None else check.letter
    cita = None if check is None else check.quote
    frase_ok = verificar_cita(cita, apuntes)
    clave = grupo.key_status
    correctas = grupo.correct_keys
    letra_ok = bool(correctas) and letra is not None and letra.strip().lower() in correctas

    if clave_dudosa:
        return _resultado(
            grupo,
            section,
            Coverage.DUDOSA,
            Motivo.CLAVE_CONTRADICE_LA_NORMA,
            cita,
            letra,
            correctas,
            clave,
            attempts,
        )
    if frase_ok:
        if not correctas or letra_ok:
            return _resultado(
                grupo, section, Coverage.CUBIERTA, None, cita, letra, correctas, clave, attempts
            )
        if attempts < VUELTAS_MAXIMAS:
            return _resultado(
                grupo, section, Coverage.HUECO, None, cita, letra, correctas, clave, attempts
            )
        return _resultado(
            grupo,
            section,
            Coverage.CONFLICTO,
            Motivo.LETRA_NO_COINCIDE,
            cita,
            letra,
            correctas,
            clave,
            attempts,
        )
    if attempts < VUELTAS_MAXIMAS:
        return _resultado(
            grupo, section, Coverage.HUECO, None, cita, letra, correctas, clave, attempts
        )
    if not correctas:
        return _resultado(
            grupo,
            section,
            Coverage.DUDOSA,
            Motivo.CLAVE_SIN_DEFINIR,
            cita,
            letra,
            correctas,
            clave,
            attempts,
        )
    return _resultado(
        grupo,
        section,
        Coverage.DUDOSA,
        Motivo.SIN_FRASE_EN_LOS_APUNTES,
        cita,
        letra,
        correctas,
        clave,
        attempts,
    )


@dataclass(frozen=True, slots=True)
class NotesCheck:
    """El resultado de comprobar una pregunta: es lo que se guarda como enlace pregunta →
    párrafo."""

    question_version_id: str
    group_signature: str
    section_key: str
    anchor: str
    coverage: Coverage
    note: Motivo | None
    quote: str | None
    letter: str | None
    expected: tuple[str, ...]
    key_status: KeyStatus
    attempts: int
    #: Huella del texto contra el que se verificó `quote`. Es lo que decide si esta comprobación se
    #: puede reutilizar en la corrida siguiente: solo si el texto es el mismo.
    text_sha256: str | None = None


def _resultado(
    grupo: QuestionGroup,
    section: NoteSection,
    coverage: Coverage,
    note: Motivo | None,
    quote: str | None,
    letter: str | None,
    expected: tuple[str, ...],
    key_status: KeyStatus,
    attempts: int,
) -> NotesCheck:
    """El resultado de una pregunta, con la cita **solo** cuando está verificada.

    La cita se guarda cuando la pregunta está cubierta (es el enlace al párrafo que la contesta) y
    cuando está en **conflicto**: ahí la frase es la prueba que el propietario necesita para decidir
    si el que está mal es la clave o los apuntes (§2.1.4, «con la frase que lo demuestra»). Lo
    que no
    se guarda nunca es una cita sin verificar: el modelo la copia a veces de memoria.
    """
    return NotesCheck(
        question_version_id=grupo.representative.question_version_id,
        group_signature=grupo.signature,
        section_key=section.key,
        anchor=section.anchor,
        coverage=coverage,
        note=note,
        quote=quote if coverage in (Coverage.CUBIERTA, Coverage.CONFLICTO) else None,
        letter=letter,
        expected=expected,
        key_status=key_status,
        attempts=attempts,
    )


# --- lo que costó ---------------------------------------------------------------------------------


@dataclass
class TokenLedger:
    """Los tokens de una corrida, por llamada. El dinero se estima, los tokens se miden."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit_tokens: int = 0
    failed_calls: int = 0

    def add(self, *, input_tokens: int, output_tokens: int, cache_hit_tokens: int = 0) -> None:
        self.calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cache_hit_tokens += cache_hit_tokens

    def merge(self, otro: TokenLedger) -> None:
        """Suma otra cuenta (la de un hilo) a esta."""
        self.calls += otro.calls
        self.input_tokens += otro.input_tokens
        self.output_tokens += otro.output_tokens
        self.cache_hit_tokens += otro.cache_hit_tokens
        self.failed_calls += otro.failed_calls

    @property
    def estimated_cost_usd(self) -> float:
        """La estimación con la tabla de precios del proyecto (valle, 7-oct-2026).

        Es una estimación y se dice: la factura la da el proveedor. Los tokens son los que devolvió
        cada llamada, así que sirve para decidir si seguir.
        """
        return (
            self.input_tokens / 1_000_000 * PRECIO_ENTRADA_USD_POR_MILLON
            + self.output_tokens / 1_000_000 * PRECIO_SALIDA_USD_POR_MILLON
        )

    def lines(self) -> tuple[str, ...]:
        return (
            f"llamadas {self.calls} ({self.failed_calls} fallidas) · "
            f"{self.input_tokens} tokens de entrada ({self.cache_hit_tokens} de caché) · "
            f"{self.output_tokens} de salida · coste estimado {self.estimated_cost_usd:.4f} $",
        )


# --- la forma canónica de los apuntes: lo que se guarda con la versión del tema -------------------


@dataclass(frozen=True, slots=True)
class SectionNotes:
    """Un apartado de los apuntes tal como se lee, con el rastro de las preguntas que cubre.

    `question_ids` son las preguntas que este apartado **cubre** (frase verificada y letra de
    acuerdo
    con la clave cuando la clave existe). Es el rastro que pide el propietario: qué preguntas
    sostiene cada apartado, sin tener que volver a comprobarlas. `conflict_question_ids` es aparte a
    propósito: una pregunta en conflicto no está cubierta y se revisa.
    """

    key: str
    epigraph_code: str
    title: str
    anchor: str
    body_markdown: str
    needs_review_reason: str | None = None
    facts_total: int = 0
    covered: int = 0
    gaps: int = 0
    doubtful: int = 0
    conflicts: int = 0
    question_ids: tuple[str, ...] = ()
    gap_question_ids: tuple[str, ...] = ()
    doubtful_question_ids: tuple[str, ...] = ()
    conflict_question_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TopicNotes:
    """Los apuntes de un tema: sus apartados y el resultado de comprobarlos con las preguntas."""

    generated_at: datetime | None
    model: str | None
    prompt_template_version: str
    sections: tuple[SectionNotes, ...] = ()

    @property
    def sections_total(self) -> int:
        return len(self.sections)

    @property
    def questions_total(self) -> int:
        return sum(
            apartado.covered + apartado.gaps + apartado.doubtful + apartado.conflicts
            for apartado in self.sections
        )

    @property
    def covered(self) -> int:
        return sum(apartado.covered for apartado in self.sections)

    @property
    def gaps(self) -> int:
        return sum(apartado.gaps for apartado in self.sections)

    @property
    def doubtful(self) -> int:
        return sum(apartado.doubtful for apartado in self.sections)

    @property
    def conflicts(self) -> int:
        """Preguntas que los apuntes contestan con otra letra que su clave: van a revisión."""
        return sum(apartado.conflicts for apartado in self.sections)


def notes_signature(notes: TopicNotes | None) -> dict[str, Any]:
    """Huella de los apuntes para la firma del tema: qué se escribió y qué se comprobó.

    Se calcula sobre el texto de cada apartado y sobre el resultado de sus preguntas, no sobre la
    fecha: volver a mirar el mismo tema no puede crear una versión nueva.
    """
    if notes is None:
        return {"notes": None}
    return {
        "notes": {
            "prompt_template_version": notes.prompt_template_version,
            "sections": [
                {
                    "key": apartado.key,
                    "anchor": apartado.anchor,
                    "body": apartado.body_markdown,
                    "needs_review_reason": apartado.needs_review_reason,
                    "covered": sorted(apartado.question_ids),
                    "gaps": sorted(apartado.gap_question_ids),
                    "doubtful": sorted(apartado.doubtful_question_ids),
                    "conflict": sorted(apartado.conflict_question_ids),
                }
                for apartado in notes.sections
            ],
        }
    }


def notes_document(notes: TopicNotes | None) -> dict[str, Any] | None:
    """Los apuntes como documento: la misma forma que se guarda en la versión del tema."""
    if notes is None:
        return None
    return {
        "generated_at": None if notes.generated_at is None else notes.generated_at.isoformat(),
        "model": notes.model,
        "prompt_template_version": notes.prompt_template_version,
        "sections_total": notes.sections_total,
        "questions_total": notes.questions_total,
        "covered": notes.covered,
        "gaps": notes.gaps,
        "doubtful": notes.doubtful,
        "conflicts": notes.conflicts,
        "sections": [
            {
                "key": apartado.key,
                "epigraph_code": apartado.epigraph_code,
                "title": apartado.title,
                "anchor": apartado.anchor,
                "body_markdown": apartado.body_markdown,
                "needs_review_reason": apartado.needs_review_reason,
                "facts_total": apartado.facts_total,
                "covered": apartado.covered,
                "gaps": apartado.gaps,
                "doubtful": apartado.doubtful,
                "conflicts": apartado.conflicts,
                "question_ids": list(apartado.question_ids),
                "gap_question_ids": list(apartado.gap_question_ids),
                "doubtful_question_ids": list(apartado.doubtful_question_ids),
                "conflict_question_ids": list(apartado.conflict_question_ids),
            }
            for apartado in notes.sections
        ],
    }


def notes_from_document(datos: Mapping[str, Any] | None) -> TopicNotes | None:
    """Reconstruye los apuntes desde el documento guardado en una versión del tema."""
    if not datos:
        return None
    generado = datos.get("generated_at")
    return TopicNotes(
        generated_at=None if generado is None else datetime.fromisoformat(str(generado)),
        model=None if datos.get("model") is None else str(datos["model"]),
        prompt_template_version=str(datos.get("prompt_template_version", VERSION_PLANTILLA)),
        sections=tuple(
            SectionNotes(
                key=str(apartado["key"]),
                epigraph_code=str(apartado.get("epigraph_code", "")),
                title=str(apartado.get("title", "")),
                anchor=str(apartado.get("anchor", apartado["key"])),
                body_markdown=str(apartado.get("body_markdown", "")),
                needs_review_reason=(
                    None
                    if apartado.get("needs_review_reason") is None
                    else str(apartado["needs_review_reason"])
                ),
                facts_total=_entero(apartado.get("facts_total")),
                covered=_entero(apartado.get("covered")),
                gaps=_entero(apartado.get("gaps")),
                doubtful=_entero(apartado.get("doubtful")),
                conflicts=_entero(apartado.get("conflicts")),
                question_ids=_textos(apartado.get("question_ids")),
                gap_question_ids=_textos(apartado.get("gap_question_ids")),
                doubtful_question_ids=_textos(apartado.get("doubtful_question_ids")),
                conflict_question_ids=_textos(apartado.get("conflict_question_ids")),
            )
            for apartado in _diccionarios(datos.get("sections"))
        ),
    )


def _diccionarios(valor: object) -> Sequence[Mapping[str, Any]]:
    if not isinstance(valor, Sequence) or isinstance(valor, str | bytes):
        return ()
    return [elemento for elemento in valor if isinstance(elemento, Mapping)]


def _textos(valor: object) -> tuple[str, ...]:
    if not isinstance(valor, Sequence) or isinstance(valor, str | bytes):
        return ()
    return tuple(str(elemento) for elemento in valor)


# --- las instrucciones ----------------------------------------------------------------------------

SYSTEM_PROMPT_HECHOS = """Eres un redactor de apuntes de la oposición de Técnico Auxiliar de \
Informática (TAI) de la Administración General del Estado. Recibes preguntas de un banco con la \
respuesta que trae su plantilla y escribes los HECHOS que un opositor necesita saber para
acertarlas.

Tema {tema}: {titulo}
Epígrafes oficiales del tema (usa EXACTAMENTE estos códigos):
{epigrafes}

Reglas:
1. Para cada pregunta escribe entre 1 y 3 hechos: frases afirmativas, autónomas (se entienden sin la
\
pregunta) y comprobables. El conjunto de los hechos tiene que bastar para acertar la pregunta.
2. Si la pregunta se contesta descartando opciones, incluye el hecho que descarta la trampa más \
tentadora (por ejemplo: «El artículo 23 regula la participación en asuntos públicos, no la \
petición»).
3. Nada inventado. Si no puedes sostener un hecho con seguridad, escribe menos hechos: un hecho \
falso es peor que un hueco.
4. `tipo`: "normativo" si el hecho cita una norma, un artículo o un órgano; "tecnico" si no.
5. `epigrafe`: el código del epígrafe al que pertenece la pregunta, de la lista de arriba. Si la \
pregunta ya trae epígrafe, respétalo. Si dudas, elige el más cercano.
6. `dudosa`: true SOLO si la respuesta que trae la plantilla contradice la norma o el material de \
estudio. Entonces escribe el hecho con lo correcto y explica la contradicción en `motivo`.
7. Prohibido escribir afirmaciones sobre exámenes, convocatorias o frecuencia de las preguntas: no \
tienes esos datos.

Responde SOLO con un objeto JSON, sin texto alrededor:
{{"hechos": [{{"id": "<el id que te he dado>", "epigrafe": "I.1.1", "dudosa": false, \
"motivo": null, "hechos": [{{"texto": "...", "tipo": "normativo"}}]}}]}}"""

SYSTEM_PROMPT_REDACTAR = """Eres un redactor de apuntes de la oposición de Técnico Auxiliar de \
Informática (TAI) de la Administración General del Estado. Escribes un apartado de los apuntes del \
tema a partir de unos hechos obligatorios y del material de estudio del opositor.

Tema {tema}: {titulo}

Reglas:
1. TODOS los hechos que se te dan tienen que estar en el texto, integrados en la explicación (en \
prosa, en una lista o en una tabla), nunca como una lista pegada al final.
2. Explica, no solo enumeres: qué es, para qué sirve, cómo se relaciona con lo anterior y, cuando \
ayude, un ejemplo.
3. Mantén TODAS las cifras, plazos, mayorías, órganos, siglas, versiones de norma y números de \
artículo que aparezcan en los hechos.
4. Usa tablas de markdown cuando haya conceptos que se confunden entre sí.
5. Escribe con palabras propias. Solo se cita literalmente la normativa, y nunca más de 20 palabras
\
seguidas de otro documento.
6. Nada inventado. Si un hecho no lo sostiene el material que se te da, escríbelo igualmente a \
partir del hecho y de la norma, y cierra ese párrafo con la marca `<!-- revisar: sin material de \
apoyo -->`.
7. Nada de afirmaciones sobre exámenes, convocatorias o frecuencia de las preguntas.
8. Devuelve un título corto (menos de 12 palabras) para el apartado.

Responde SOLO con un objeto JSON, sin texto alrededor:
{{"titulo": "...", "markdown": "..."}}"""

SYSTEM_PROMPT_COMPROBAR = """Vas a comprobar si unos apuntes contestan a unas preguntas de test. \
Solo puedes usar el texto de los apuntes que viene a continuación: no uses nada que sepas de \
memoria, ni lo que creas correcto por otra vía.

=== APUNTES DEL TEMA ===
{apuntes}
=== FIN DE LOS APUNTES ===

Para cada pregunta devuelve:
- `letra`: la opción correcta **según los apuntes** ("a", "b", "c"…), o null si los apuntes no \
permiten decidirlo.
- `frase`: la frase EXACTA que justifica la respuesta, copiada carácter a carácter de los apuntes. \
Si ninguna frase de los apuntes justifica la respuesta, escribe exactamente "NO ESTÁ".

Responde SOLO con un objeto JSON, sin texto alrededor:
{{"respuestas": [{{"id": "<el id que te he dado>", "letra": "b", "frase": "..."}}]}}"""

SYSTEM_PROMPT_ANADIR = """Eres un redactor de apuntes de la oposición de Técnico Auxiliar de \
Informática (TAI) de la Administración General del Estado. Un apartado de los apuntes no contesta a
\
unas preguntas: escribe lo que falta.

Reglas:
1. Escribe un párrafo (o varios) que añada **solo** lo que falta para contestar esas preguntas: no \
repitas lo que ya está escrito y no lo contradigas.
2. Empieza con una línea `### ` y un título corto.
3. Nada inventado: si no puedes sostener algo, no lo escribas.
4. Nada de afirmaciones sobre exámenes, convocatorias o frecuencia de las preguntas.

Responde SOLO con un objeto JSON, sin texto alrededor:
{{"markdown": "### ..."}}"""


def build_system_prompt_hechos(
    *, topic_code: str, topic_title: str, epigraphs: Sequence[tuple[str, str]]
) -> str:
    """Las instrucciones del paso B, con el tema y sus epígrafes reales dentro.

    El tema va en el mensaje de sistema y no en el de cada lote: es el mismo para todas las llamadas
    del tema, así que el proveedor puede cobrarlo a precio de acierto de caché.
    """
    lista = (
        "\n".join(f"    {codigo} — {titulo}" for codigo, titulo in epigraphs)
        or "    (sin epígrafes)"
    )
    return SYSTEM_PROMPT_HECHOS.format(tema=topic_code, titulo=topic_title, epigrafes=lista)


def build_system_prompt_redactar(*, topic_code: str, topic_title: str) -> str:
    """Las instrucciones del paso D. Estables por tema: es el prefijo que se cachea."""
    return SYSTEM_PROMPT_REDACTAR.format(tema=topic_code, titulo=topic_title)


def build_system_prompt_comprobar(apuntes: str) -> str:
    """Las instrucciones del paso E con los apuntes dentro.

    Los apuntes van en el mensaje de sistema para que el proveedor pueda cobrar la parte repetida
    (el mismo epígrafe se comprueba en varios lotes) a precio de acierto de caché.
    """
    return SYSTEM_PROMPT_COMPROBAR.format(apuntes=apuntes)


def build_user_prompt_hechos(grupos: Sequence[QuestionGroup]) -> str:
    """El lote de preguntas del paso B: una por grupo, con su id, sus opciones y su respuesta.

    La respuesta viaja marcada como «de la plantilla» a propósito: es un dato del banco, no una
    verdad, y el modelo tiene instrucciones de decir cuándo la contradice la norma.
    """
    bloques: list[str] = []
    for grupo in grupos:
        pregunta = grupo.representative
        lineas = [f"id: {grupo.signature}", f"enunciado: {pregunta.stem.strip()}"]
        lineas.extend(f"  {clave}) {texto}" for clave, texto in pregunta.options)
        if grupo.correct_keys:
            lineas.append(
                f"respuesta de la plantilla ({grupo.key_status.value}): "
                + ", ".join(grupo.correct_keys)
            )
        else:
            lineas.append("respuesta de la plantilla: no consta")
        if grupo.epigraph_code:
            lineas.append(f"epígrafe ya asignado: {grupo.epigraph_code}")
        bloques.append("\n".join(lineas))
    return "Escribe los hechos de estas preguntas:\n\n" + "\n\n".join(bloques)


def build_user_prompt_redactar(
    section: NoteSection,
    material: Sequence[MaterialPassage],
    *,
    es_tabla_de_puertos: bool = False,
) -> str:
    """El encargo de un apartado: el título, los hechos obligatorios y el material que los
    sostiene.

    Si el apartado es la tabla de puertos, se le añaden las instrucciones de sus **familias** y la
    regla de la columna de notas: es un apartado con una forma propia y decirlo aquí (y no en las
    instrucciones generales) es lo que hace que el resto de apartados no cargue con esas reglas.
    """
    hechos = "\n".join(
        f"{numero}. [{hecho.kind.value}] {hecho.text}"
        for numero, hecho in enumerate(section.facts, start=1)
    )
    if material:
        # Cada pasaje va con su procedencia: el redactor tiene que poder decir de dónde sale lo que
        # copia, y el comentario de revisión se apoya en esa procedencia.
        cuerpo_material = "\n\n".join(
            f"[{pasaje.referencia}] {pasaje.text.strip()}" for pasaje in material
        )
    else:
        cuerpo_material = "(no hay material del tema que trate estos hechos)"
    propio = f"\n\n{familias_para_el_prompt()}" if es_tabla_de_puertos else ""
    # Los encabezados que ya están puestos en los otros trozos de esta misma materia: partir una
    # materia en dos llamadas (no cabe en una) hace que cada trozo escriba su propio índice, y sin
    # esto los dos escriben el mismo. La puerta de encabezados repetidos lo dice con razón.
    ya_puestos = ""
    if section.encabezados_ya_usados:
        lista = "\n".join(f"- {titulo}" for titulo in section.encabezados_ya_usados)
        ya_puestos = (
            f"\n\nENCABEZADOS QUE YA ESTÁN PUESTOS EN LOS OTROS TROZOS DE ESTA MATERIA (no los "
            f"repitas: este apartado es la continuación de esa misma materia):\n{lista}"
        )
    # El tope de extensión, dicho en el encargo y no solo comprobado después: un apartado se mide en
    # `40 x hechos distintos` (la puerta de densidad del §2.3) y el redactor tiene que saberlo antes
    # de escribir, no descubrirlo en el informe. I.6 salió con 82 palabras por hecho y no pasó.
    tope = MAX_PALABRAS_POR_HECHO * max(len(section.facts), 1)
    return (
        f"Apartado: {section.title}\n"
        f"Epígrafe oficial: {section.epigraph_code}\n\n"
        f"HECHOS OBLIGATORIOS ({len(section.facts)}):\n{hechos}\n\n"
        f"MATERIAL DEL OPOSITOR (citas de su biblioteca; úsalo como apoyo, no lo copies entero):\n"
        f"{cuerpo_material}{propio}{ya_puestos}\n\n"
        f"Escribe el apartado. No pases de unas {tope} palabras en total (son "
        f"{MAX_PALABRAS_POR_HECHO} por cada uno de los {len(section.facts)} hechos): lo que no sea "
        "explicar un hecho, no va."
    )


def build_user_prompt_comprobar(grupos: Sequence[QuestionGroup]) -> str:
    """El lote de preguntas del paso E, con sus opciones y **sin** la respuesta correcta.

    La respuesta no viaja: el paso E pregunta si los apuntes contestan la pregunta, y mandarle la
    clave invitaría a contestar «lo que ya sabía» en vez de «lo que está escrito».
    """
    bloques: list[str] = []
    for grupo in grupos:
        pregunta = grupo.representative
        lineas = [f"id: {grupo.signature}", f"enunciado: {pregunta.stem.strip()}"]
        lineas.extend(f"  {clave}) {texto}" for clave, texto in pregunta.options)
        bloques.append("\n".join(lineas))
    return "Comprueba si los apuntes contestan a estas preguntas:\n\n" + "\n\n".join(bloques)


def build_user_prompt_anadir(
    section: NoteSection,
    grupos: Sequence[QuestionGroup],
    hechos: Sequence[Hecho] = (),
    *,
    maximo_caracteres: int = 6_000,
) -> str:
    """El encargo del añadido: lo ya escrito, los hechos que faltan y lo que no se contesta.

    Los hechos van **obligatorios**: son los del paso B para esas mismas preguntas, así que el
    añadido no se apoya en lo que el modelo recuerde, sino en lo que ya se escribió y se comprueba.

    Y el añadido lleva **su tope**: lo que le queda al apartado para llegar a `40 x hechos` (§2.3),
    nunca menos de `MINIMO_PALABRAS_ANADIDO` (un párrafo tiene que poder decir algo). Sin esto, el
    añadido escribía sin límite y el tema acababa por encima del tope de extensión justo por
    rellenar sus huecos: I.6 quedó en 18.795 palabras de 13.840 después de cuatro añadidos, con el
    texto ya bien. El tope se saca del apartado (sus hechos y lo que ya tiene escrito) y no de un
    parámetro, para que valga en los dos sitios donde se escribe un añadido.
    """
    ya = section.body_markdown.strip()
    if len(ya) > maximo_caracteres:
        ya = ya[-maximo_caracteres:]
    bloques: list[str] = []
    for grupo in grupos:
        pregunta = grupo.representative
        lineas = [f"id: {grupo.signature}", f"enunciado: {pregunta.stem.strip()}"]
        lineas.extend(f"  {clave}) {texto}" for clave, texto in pregunta.options)
        bloques.append("\n".join(lineas))
    obligatorios = (
        "\n".join(f"{numero}. {hecho.text}" for numero, hecho in enumerate(hechos, start=1))
        or "(no hay hechos nuevos: escribe a partir de la norma, sin inventar)"
    )
    tope = tope_del_anadido(section)
    return (
        f"Apartado: {section.title}\n\n"
        f"LO QUE YA DICEN LOS APUNTES (final del apartado):\n{ya or '(vacío)'}\n\n"
        f"HECHOS QUE FALTAN (obligatorios, intégralos en el añadido):\n{obligatorios}\n\n"
        "PREGUNTAS QUE LOS APUNTES NO CONTESTAN:\n" + "\n\n".join(bloques) + "\n\nEscribe lo que "
        f"falta, sin repetir lo que ya está. **Como mucho {tope} palabras**: es lo que le queda al "
        "apartado para no pasar de 40 por cada hecho suyo. Si no cabe todo, di primero lo que "
        "contesta a las preguntas de arriba."
    )


def tope_del_anadido(section: NoteSection) -> int:
    """Cuántas palabras le quedan al apartado antes de pasarse de `40 x hechos` (§2.3).

    Nunca menos de `MINIMO_PALABRAS_ANADIDO`: un añadido de cero palabras no rellena nada, y el
    objetivo del bucle de huecos es justo lo contrario. El hueco que quede por encima de eso se
    declara (va a la bandeja del propietario con su categoría), no se tapa escribiendo de más.
    """
    tope = MAX_PALABRAS_POR_HECHO * max(len(section.facts), 1)
    return max(MINIMO_PALABRAS_ANADIDO, tope - len(section.body_markdown.split()))


def serializar_hechos(hechos: Sequence[Hecho]) -> str:
    """Los identificadores de los grupos de origen, en JSON, para guardarlos en una columna."""
    return json.dumps(sorted({firma for hecho in hechos for firma in hecho.source_groups}))


def _entero(valor: object) -> int:
    return int(valor) if isinstance(valor, int) and not isinstance(valor, bool) else 0


def leer_uso(sobre: dict[str, Any]) -> tuple[int, int, int]:
    """`(entrada, salida, entrada cacheada)` del sobre de la respuesta. Ceros si no viene."""
    uso = sobre.get("usage")
    if not isinstance(uso, dict):
        return (0, 0, 0)
    return (
        _entero(uso.get("prompt_tokens")),
        _entero(uso.get("completion_tokens")),
        _entero(uso.get("prompt_cache_hit_tokens")),
    )


__all__ = [
    "HECHOS_NUEVOS",
    "LOTE_COMPROBACION",
    "LOTE_HECHOS",
    "MAX_HECHOS_POR_APARTADO",
    "MINIMO_CITA",
    "MINIMO_PALABRAS_ANADIDO",
    "SIN_MATERIAL",
    "VERSION_PLANTILLA",
    "VUELTAS_MAXIMAS",
    "ComprobacionBatch",
    "Coverage",
    "FactKind",
    "Hecho",
    "HechosBatch",
    "KeyStatus",
    "MaterialInput",
    "MaterialPassage",
    "Motivo",
    "NoteSection",
    "NotesCheck",
    "QuestionForNotes",
    "QuestionGroup",
    "QuoteCheck",
    "RedaccionBatch",
    "SectionNotes",
    "TokenLedger",
    "TopicNotes",
    "agrupar",
    "build_system_prompt_comprobar",
    "build_system_prompt_hechos",
    "build_system_prompt_redactar",
    "build_user_prompt_anadir",
    "build_user_prompt_comprobar",
    "build_user_prompt_hechos",
    "build_user_prompt_redactar",
    "esquema",
    "evaluar",
    "firma_de_grupo",
    "hechos_integrados",
    "indexar_material",
    "leer_uso",
    "notes_document",
    "notes_from_document",
    "notes_signature",
    "seleccionar_material",
    "serializar_hechos",
    "slug",
    "terminos_significativos",
    "tope_del_anadido",
    "verificar_cita",
]
