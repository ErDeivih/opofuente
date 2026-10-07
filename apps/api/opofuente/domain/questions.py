"""Preguntas, opciones, claves y su plantilla (03_DATA-MODEL §6 y 04_INGESTION §10).

Dos reglas gobiernan todo lo de aquí:

1. **Nada se fusiona solo.** Detectar que dos preguntas son la misma —o la misma con las opciones
   reordenadas— produce un **grupo**, nunca una fusión. Si las claves de las dos no coinciden, el
   grupo lo dice: dos claves en conflicto no se pueden juntar sin decidir cuál es la buena, y esa
   decisión no es de una función.
2. **La normalización es solo para comparar.** El texto que se guarda y se cita no se toca, y de una
   pregunta se quitan únicamente la numeración y las etiquetas de opción. Las palabras se quedan
   todas, incluidas las negaciones: «¿cuál NO es correcta?» pregunta lo contrario que «¿cuál es
   correcta?», y una normalización que se comiera el «no» las haría parecer la misma pregunta.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from opofuente.domain.duplicates import jaccard, normalise_for_comparison, shingles

# --- vocabularios (los mismos que la migración 0014) -------------------------------------------


class SetType(StrEnum):
    """Qué es el conjunto: un examen oficial, un banco privado, práctica o un lote generado."""

    OFFICIAL_EXAM = "official_exam"
    PRIVATE_BANK = "private_bank"
    PRACTICE = "practice"
    GENERATED_BATCH = "generated_batch"


class SetStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"


class SetDistribution(StrEnum):
    """Quién puede ver el conjunto: su dueño (`personal`) o cualquiera (`public`).

    El valor por defecto es `personal` y es deliberado: el material que el propietario ha reunido no
    se hace visible por descuido. `public` se declara a propósito, conjunto a conjunto (F2).
    """

    PERSONAL = "personal"
    PUBLIC = "public"


class QuestionType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTI_MARK_ERROR = "multi_mark_error"
    TRUE_FALSE = "true_false"
    FREE_TEXT_REFERENCE = "free_text_reference"


class QuestionStatus(StrEnum):
    """`incomplete` es un estado de verdad.

    Una pregunta sin clave o sin opciones existe, pero no está entera, y el banco lo dice en lugar
    de esconderla o de rellenarla con algo inventado.
    """

    INCOMPLETE = "incomplete"
    COMPLETE = "complete"
    VERIFIED = "verified"
    CONFLICTING = "conflicting"
    ANNULLED = "annulled"
    SUPERSEDED = "superseded"


class Origin(StrEnum):
    OFFICIAL = "official"
    PRIVATE = "private"
    GENERATED = "generated"


class KeyStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class KeyOutcome(StrEnum):
    KEYED = "keyed"
    ANNULLED = "annulled"
    UNANSWERED = "unanswered"
    CONFLICTING = "conflicting"


class EvidenceRole(StrEnum):
    STEM = "stem"
    CORRECT = "correct"
    DISTRACTOR = "distractor"
    EXPLANATION = "explanation"


class ExplanationStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    REJECTED = "rejected"


# --- piezas ------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OptionVersion:
    """Una opción de una pregunta. La clave estable no cambia al reordenar las opciones."""

    id: str
    question_version_id: str
    stable_key: str
    text: str
    position: int
    label: str | None = None


@dataclass(frozen=True, slots=True)
class QuestionVersion:
    """Una versión de una pregunta, con sus opciones."""

    id: str
    question_set_id: str
    stable_key: str
    version_no: int
    stem: str
    question_type: QuestionType
    position: int
    origin_type: Origin
    status: QuestionStatus = QuestionStatus.INCOMPLETE
    is_reserve: bool = False
    reserve_order: int | None = None
    source_section_id: str | None = None
    supersedes_id: str | None = None
    created_at: datetime | None = None
    options: tuple[OptionVersion, ...] = ()

    @property
    def is_reserve_ordered(self) -> bool:
        return self.is_reserve and self.reserve_order is not None

    @property
    def option_keys(self) -> tuple[str, ...]:
        return tuple(opcion.stable_key for opcion in self.options)


@dataclass(frozen=True, slots=True)
class QuestionSet:
    id: str
    title: str
    opposition_id: str
    set_type: SetType
    status: SetStatus = SetStatus.DRAFT
    convocation_version_id: str | None = None
    model_code: str | None = None
    held_at: date | None = None
    source_document_version_id: str | None = None
    created_at: datetime | None = None

    @property
    def is_official(self) -> bool:
        return self.set_type is SetType.OFFICIAL_EXAM


@dataclass(frozen=True, slots=True)
class AnswerKeyEntry:
    """Qué le pasa a una pregunta en una plantilla."""

    question_version_id: str
    outcome: KeyOutcome
    correct_option_keys: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.outcome is KeyOutcome.KEYED and not self.correct_option_keys:
            raise ValueError("Un desenlace con clave necesita al menos una opción correcta")


@dataclass(frozen=True, slots=True)
class AnswerKeyVersion:
    id: str
    question_set_id: str
    version_no: int
    status: KeyStatus = KeyStatus.DRAFT
    source_document_version_id: str | None = None
    supersedes_id: str | None = None
    published_at: date | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    entries: tuple[AnswerKeyEntry, ...] = ()

    @property
    def is_active(self) -> bool:
        return self.status is KeyStatus.ACTIVE

    def entry_of(self, question_version_id: str) -> AnswerKeyEntry | None:
        return next(
            (
                entrada
                for entrada in self.entries
                if entrada.question_version_id == question_version_id
            ),
            None,
        )


def can_activate(conjunto: QuestionSet, clave: AnswerKeyVersion) -> tuple[bool, str | None]:
    """¿Se puede activar esta plantilla? Devuelve si se puede y, si no, por qué.

    Dos reglas de las invariantes que un `CHECK` de SQLite no puede imponer, porque dependen del
    tipo del conjunto (que vive en otra tabla):

    - **invariante 4**: una clave oficial necesita la plantilla oficial enlazada;
    - una clave activa necesita aprobación (eso sí lo impone la base; aquí se comprueba antes para
      poder decirlo con palabras en lugar de con un error de integridad).
    """
    if clave.question_set_id != conjunto.id:
        return False, "la plantilla no es de este conjunto"
    if clave.approved_at is None:
        return False, "una clave activa necesita aprobación"
    if conjunto.is_official and clave.source_document_version_id is None:
        return False, "una clave oficial necesita la plantilla oficial enlazada"
    return True, None


# --- normalización: solo para comparar ---------------------------------------------------------

#: Numeración escrita con la palabra: `Pregunta 7`, `Pregunta 7.-`. El separador es opcional.
_NUMBERING_WORD = re.compile(r"^\s*pregunta\s*(\d{1,3})\s*[.)\-\u2013:]*\s*", re.IGNORECASE)
#: Numeración con separador obligatorio: `1.`, `12)`, `7-`, `3.-`. Sin separador no se toca nada,
#: para que un enunciado que empieza por un número («3 de mayo de 1978…») no pierda su número.
_NUMBERING_MARK = re.compile(r"^\s*(\d{1,3})\s*[.)\-\u2013:]+\s*")
#: Etiqueta de una opción: `a)`, `B.`, `(c)`, `d-`, `e:`.
_OPTION_LABEL = re.compile(r"^\s*\(?\s*([a-hA-H])\s*[.)\-\u2013:]\s*")
#: Marca de reserva: `(R)`, `[R]`, `reserva 2`.
_RESERVE = re.compile(r"[\[(]\s*r\s*[\])]|reserva\s*(\d{1,2})?", re.IGNORECASE)
#: Cabecera de modelo: `Modelo A`, `MODELO: B`.
_MODEL = re.compile(r"modelo\s*[:\-]?\s*([a-dA-D])\b", re.IGNORECASE)
#: Cabecera de parte: `Primera parte`, `Parte 2`, `PARTE I`.
_PART = re.compile(r"(?:parte|ejercicio)\s*[:\-]?\s*([0-9ivx]+)", re.IGNORECASE)
#: Línea de clave dentro del bloque de una pregunta: `Respuesta correcta: b`, `Solución: A, C`.
_KEY_LINE = re.compile(
    r"^\s*(?:respuesta\s+correcta|respuesta|soluci[oó]n|clave|correcta)\s*[:\-]\s*(.+)$",
    re.IGNORECASE,
)
#: Instrucción que pide marcar errores (GC: ortografía y gramática).
_MARK_ERRORS = re.compile(
    r"\b(marque|se[ñn]ale|indique)\b[^.]*\b(errores?|incorrect[ao]s?|expresiones)\b", re.IGNORECASE
)
_OPTION_KEYS = ("a", "b", "c", "d", "e", "f", "g", "h")

#: Adornos de Markdown que envuelven una línea entera y no forman parte de lo que dice.
_MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
_MD_QUOTE = re.compile(r"^\s{0,3}>\s?")
_MD_BULLET = re.compile(r"^\s{0,3}[-*+]\s+")
#: Marcas de énfasis fuerte (`**`, `__`). Se quitan estén donde estén: marcan énfasis, no dicen
#: nada. Las de énfasis simple (`*`, `_`) **no** se tocan, porque un guion bajo separa palabras.
_MD_STRONG = re.compile(r"\*\*|__")


def strip_markdown_decoration(line: str) -> str:
    """Quita de una línea el adorno de Markdown que no es contenido.

    Un cuestionario escrito en Markdown no dice lo mismo con `**Respuesta correcta: b**` que sin los
    asteriscos: los asteriscos son cómo se escribe, no qué se dice. Se quitan encabezados (`##`),
    citas (`>`), viñetas de lista (`- `) y las marcas de énfasis fuerte (`**`, `__`).

    Lo que **no** hace: tocar las palabras ni el énfasis simple. `*diez* días` sigue diciendo lo
    mismo, y el enunciado se guarda con su texto.
    """
    texto = _MD_HEADING.sub("", line)
    texto = _MD_QUOTE.sub("", texto)
    texto = _MD_BULLET.sub("", texto)
    return _MD_STRONG.sub("", texto).strip()


def numbering_match(line: str) -> re.Match[str] | None:
    """Numeración de una pregunta, en cualquiera de sus dos formas, o nada.

    Se pide un **separador** (`1.`, `12)`) o la palabra `Pregunta`, y no solo un número: «3 de mayo
    de 1978 fue…» es un enunciado que empieza por un número, no la pregunta número 3.
    """
    return _NUMBERING_WORD.match(line) or _NUMBERING_MARK.match(line)


def strip_numbering(text: str) -> str:
    """Quita la numeración del principio, y solo eso: el resto del enunciado no se toca."""
    encontrado = numbering_match(text)
    return text[encontrado.end() :].strip() if encontrado is not None else text.strip()


def strip_option_label(text: str) -> str:
    """Quita la etiqueta de una opción (`a)`, `B.`), y solo eso."""
    return _OPTION_LABEL.sub("", text, count=1).strip()


def normalise_question_text(text: str) -> str:
    """Normaliza para comparar: minúsculas, sin tildes, sin puntuación y con espacios simples.

    **No** se quitan palabras: las negaciones se conservan, porque cambian lo que se pregunta. Y
    esto no toca el texto guardado: solo decide si dos cosas se parecen.
    """
    return normalise_for_comparison(text)


@dataclass(frozen=True, slots=True)
class QuestionFingerprint:
    """Huella de una pregunta: enunciado normalizado y conjunto de opciones, sin orden.

    Las opciones se comparan **como conjunto** a propósito: el mismo juego de opciones en otro orden
    es el modelo A/B de la misma pregunta (03_DATA-MODEL §6). El orden real vive en cada versión.
    """

    stem_key: str
    options_key: tuple[str, ...]

    @property
    def is_complete(self) -> bool:
        return bool(self.stem_key) and len(self.options_key) >= 2

    @property
    def identity(self) -> str:
        return f"{self.stem_key}||{'|'.join(self.options_key)}"


def question_fingerprint(stem: str, option_texts: Sequence[str]) -> QuestionFingerprint:
    """Huella de una pregunta: enunciado y opciones, sin numeración ni etiquetas."""
    opciones = sorted(
        {normalise_question_text(strip_option_label(texto)) for texto in option_texts} - {""}
    )
    return QuestionFingerprint(
        stem_key=normalise_question_text(strip_numbering(stem)), options_key=tuple(opciones)
    )


def same_options_in_other_order(left: Sequence[str], right: Sequence[str]) -> bool:
    """¿Son las mismas opciones en otro orden? Es lo que distingue el modelo A del modelo B."""
    izquierda = [normalise_question_text(strip_option_label(texto)) for texto in left]
    derecha = [normalise_question_text(strip_option_label(texto)) for texto in right]
    return sorted(izquierda) == sorted(derecha) and izquierda != derecha


# --- duplicados: se agrupan, no se fusionan ----------------------------------------------------

#: Nombres de los grupos que produce la comparación de preguntas.
SAME_QUESTION = "same_question"
REORDERED_OPTIONS = "reordered_options"
SIMILAR_QUESTION = "similar"


@dataclass(frozen=True, slots=True)
class QuestionDuplicateGroup:
    """Grupo de preguntas que son la misma cosa, con lo que **impide** fusionarlas.

    `conflicting_keys` es lo importante: si dos miembros tienen claves distintas, fusionarlos
    elegiría una respuesta en lugar del usuario, y eso no lo hace una función (04_INGESTION §9).
    """

    kind: str
    members: tuple[str, ...]
    conflicting_keys: bool = False
    keys_seen: tuple[str, ...] = ()

    @property
    def can_merge(self) -> bool:
        """Solo se puede fusionar lo que es la misma pregunta y no tiene claves en conflicto."""
        return self.kind == SAME_QUESTION and not self.conflicting_keys

    @property
    def size(self) -> int:
        return len(self.members)


def _key_signature(entry: AnswerKeyEntry | None, pregunta: QuestionVersion) -> str | None:
    """Firma de una clave **por el texto de la opción**, no por su letra.

    Es lo que hace que el modelo A y el modelo B no aparezcan en conflicto: la misma respuesta
    correcta cambia de letra al reordenar las opciones, y comparar letras diría que se contradicen
    cuando dicen lo mismo. Si la clave apunta a una opción que no está en esta versión, se firma por
    letra: mejor decir que no se sabe a qué corresponde que inventar una equivalencia.
    """
    if entry is None:
        return None
    if entry.outcome is not KeyOutcome.KEYED:
        return entry.outcome.value
    letras = entry.correct_option_keys
    textos = {
        normalise_question_text(opcion.text)
        for opcion in pregunta.options
        if opcion.stable_key in letras
    }
    if len(textos) < len(letras) or not textos:
        return "+".join(sorted(letras))
    return "|".join(sorted(textos))


def _fingerprint_of(pregunta: QuestionVersion) -> QuestionFingerprint:
    return question_fingerprint(pregunta.stem, [opcion.text for opcion in pregunta.options])


def _signatures(
    claves: Mapping[str, AnswerKeyEntry], miembros: Sequence[QuestionVersion]
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                firma
                for firma in (
                    _key_signature(claves.get(pregunta.id), pregunta) for pregunta in miembros
                )
                if firma is not None
            }
        )
    )


def find_question_duplicates(
    questions: Sequence[QuestionVersion],
    *,
    keys: Mapping[str, AnswerKeyEntry] | None = None,
    similarity_threshold: float = 0.8,
) -> tuple[QuestionDuplicateGroup, ...]:
    """Agrupa repetidas, reordenadas y casi iguales. **No fusiona nada.**

    Mismo enunciado y mismas opciones en el mismo orden es `same_question`; mismas opciones en otro
    orden es `reordered_options` (el modelo A/B); y un enunciado muy parecido es `similar`, que solo
    señala. En todos los casos el grupo dice si las claves se contradicen.
    """
    claves = keys or {}
    grupos: list[QuestionDuplicateGroup] = []
    vistas: set[str] = set()
    huellas = {pregunta.id: _fingerprint_of(pregunta) for pregunta in questions}

    por_identidad: dict[str, list[QuestionVersion]] = {}
    for pregunta in questions:
        huella = huellas[pregunta.id]
        if huella.is_complete:
            por_identidad.setdefault(huella.identity, []).append(pregunta)

    for miembros in por_identidad.values():
        if len(miembros) < 2:
            continue
        vistas.update(pregunta.id for pregunta in miembros)
        reordenadas = any(
            same_options_in_other_order(
                [opcion.text for opcion in miembros[0].options],
                [opcion.text for opcion in otro.options],
            )
            for otro in miembros[1:]
        )
        firmas = _signatures(claves, miembros)
        grupos.append(
            QuestionDuplicateGroup(
                kind=REORDERED_OPTIONS if reordenadas else SAME_QUESTION,
                members=tuple(pregunta.id for pregunta in miembros),
                conflicting_keys=len(firmas) > 1,
                keys_seen=firmas,
            )
        )

    # Casi iguales: enunciado que se solapa mucho y opciones que coinciden en parte. Solo se señala.
    restantes = [pregunta for pregunta in questions if pregunta.id not in vistas]
    for indice, pregunta in enumerate(restantes):
        for otra in restantes[indice + 1 :]:
            huella_a, huella_b = huellas[pregunta.id], huellas[otra.id]
            if not huella_a.is_complete or not huella_b.is_complete:
                continue
            similitud = jaccard(
                shingles(huella_a.stem_key, size=4), shingles(huella_b.stem_key, size=4)
            )
            mismas_opciones = huella_a.options_key == huella_b.options_key
            if similitud >= similarity_threshold or (mismas_opciones and similitud > 0):
                firmas = _signatures(claves, (pregunta, otra))
                grupos.append(
                    QuestionDuplicateGroup(
                        kind=SIMILAR_QUESTION,
                        members=(pregunta.id, otra.id),
                        conflicting_keys=len(firmas) > 1,
                        keys_seen=firmas,
                    )
                )
    return tuple(grupos)


# --- parser de preguntas (04_INGESTION §10) ----------------------------------------------------


@dataclass(frozen=True, slots=True)
class ParseIssue:
    """Lo que el parser no pudo leer, con su motivo: una fila mala no aborta el resto."""

    line: int
    code: str
    detail: str


@dataclass(frozen=True, slots=True)
class ParsedOption:
    stable_key: str
    text: str
    position: int


@dataclass(frozen=True, slots=True)
class ParsedQuestion:
    number: int | None
    stem: str
    options: tuple[ParsedOption, ...]
    question_type: QuestionType
    line: int
    is_reserve: bool = False
    reserve_order: int | None = None
    correct_option_keys: tuple[str, ...] = ()
    type_reason: str | None = None
    #: Sección del documento de la que salió la pregunta (DEBT-010). El parser de un texto pegado no
    #: la conoce —ahí no hay documento—, así que la rellena quien importa desde una versión.
    source_section_id: str | None = None
    #: Explicación de **cada opción** («por qué la b no vale»), por clave de opción (S12.7). El
    #: modelo ya guardaba esto (`question_explanations.option_stable_key`); lo que faltaba era que
    #: llegara desde el material, y de eso se encargan los parsers.
    option_explanations: tuple[tuple[str, str], ...] = ()
    #: Explicación general y tema (ruta o código del programa) que trae el propio material: los
    #: lee el asistente JSON. Antes se leían en el contrato pero no llegaban a ningún sitio.
    explanation: str | None = None
    topic: str | None = None

    @property
    def is_complete(self) -> bool:
        return bool(self.stem) and len(self.options) >= 2

    @property
    def has_key(self) -> bool:
        return bool(self.correct_option_keys)


@dataclass(frozen=True, slots=True)
class ParsedSet:
    """Resultado de parsear un texto: lo leído, lo que falta y por qué."""

    questions: tuple[ParsedQuestion, ...] = ()
    issues: tuple[ParseIssue, ...] = field(default_factory=tuple)
    model_code: str | None = None
    parts_detected: tuple[str, ...] = ()
    #: Campos que venían en el origen y este asistente no guarda: se informan, no se esconden.
    ignored_fields: tuple[str, ...] = ()

    @property
    def with_key(self) -> int:
        return sum(1 for pregunta in self.questions if pregunta.has_key)

    @property
    def incomplete(self) -> int:
        return sum(1 for pregunta in self.questions if not pregunta.is_complete)

    @property
    def reserves(self) -> int:
        return sum(1 for pregunta in self.questions if pregunta.is_reserve)


def _option_key(indice: int) -> str:
    return _OPTION_KEYS[indice] if indice < len(_OPTION_KEYS) else f"op{indice + 1}"


def _infer_type(stem: str, options: Sequence[ParsedOption]) -> tuple[QuestionType, str | None]:
    """Tipo de pregunta inferido, con el motivo a la vista (04_INGESTION §10, paso 3).

    Se infiere **solo** cuando el propio texto lo dice: dos opciones que son «verdadero» y «falso»,
    o una instrucción de marcar errores. Lo que no se puede saber se queda en `single_choice`, que
    es el formato más común, y el motivo va vacío para que nadie crea que viene del texto.
    """
    textos = [normalise_question_text(opcion.text) for opcion in options]
    if len(textos) == 2 and set(textos) == {"verdadero", "falso"}:
        return QuestionType.TRUE_FALSE, "las dos opciones son «verdadero» y «falso»"
    if _MARK_ERRORS.search(stem) and len(textos) >= 3:
        return QuestionType.MULTI_MARK_ERROR, "el enunciado pide marcar errores o expresiones"
    if not textos:
        return QuestionType.FREE_TEXT_REFERENCE, "no hay opciones: es una pregunta de referencia"
    return QuestionType.SINGLE_CHOICE, None


def _parse_key_line(line: str) -> tuple[str, ...] | None:
    encontrado = _KEY_LINE.match(line)
    if encontrado is None:
        return None
    bruto = encontrado.group(1)
    claves = tuple(
        letra.lower() for letra in re.findall(r"\b([a-hA-H])\b", bruto.replace(",", " "))
    )
    return claves or None


def parse_questions(text: str) -> ParsedSet:
    """Parsea preguntas de un texto: bloques de enunciado con sus opciones.

    Cada bloque empieza en una línea numerada (`1.`, `Pregunta 7`, `12)`) o por la palabra
    `Pregunta`. Lo que no se puede leer se informa como incidencia y **no** aborta el resto: es el
    criterio de aceptación del slice (una fila mala no rompe el lote).

    Lo que este parser **no** hace: adivinar. No inventa opciones que no están, no rellena claves
    que no aparecen y no llama «reserva» a nada que no lleve su marca.
    """
    preguntas: list[ParsedQuestion] = []
    incidencias: list[ParseIssue] = []
    modelo: str | None = None
    partes: list[str] = []

    # Estado del bloque que se está leyendo: locales y no un diccionario, para que el tipo se sepa.
    # Un `dict[str, object]` obligaría a comprobar el tipo en cada uso.
    en_bloque = False
    linea_inicio = 0
    numero: int | None = None
    es_reserva = False
    orden_reserva: int | None = None
    lineas_enunciado: list[str] = []
    opciones: list[ParsedOption] = []
    claves: tuple[str, ...] = ()

    def cerrar() -> None:
        nonlocal en_bloque, lineas_enunciado, opciones, claves
        if not en_bloque:
            return
        stem = " ".join(lineas_enunciado).strip()
        if not stem:
            incidencias.append(
                ParseIssue(line=linea_inicio, code="empty_stem", detail="bloque sin enunciado")
            )
        else:
            if len(opciones) == 1:
                incidencias.append(
                    ParseIssue(
                        line=linea_inicio, code="few_options", detail="solo se leyó una opción"
                    )
                )
            tipo, motivo = _infer_type(stem, opciones)
            preguntas.append(
                ParsedQuestion(
                    number=numero,
                    stem=stem,
                    options=tuple(opciones),
                    question_type=tipo,
                    line=linea_inicio,
                    is_reserve=es_reserva,
                    reserve_order=orden_reserva,
                    correct_option_keys=claves,
                    type_reason=motivo,
                )
            )
        en_bloque = False
        lineas_enunciado = []
        opciones = []
        claves = ()

    for numero_linea, linea_texto in enumerate(text.splitlines(), 1):
        # Un cuestionario escrito en Markdown trae adornos que no son parte del enunciado
        # (`**Respuesta correcta: b**`, `- a) opción`, `## Tema 5`). Se quitan **antes** de mirar la
        # línea, y el fragmento original sigue siendo el que se cita.
        es_encabezado = _MD_HEADING.match(linea_texto) is not None
        linea = strip_markdown_decoration(linea_texto)
        if not linea.strip():
            continue
        if es_encabezado:
            # Un encabezado de Markdown es **estructura**, no texto suelto: encabeza lo que viene
            # debajo. Se entiende y no se informa como problema, igual que «Modelo A» o «Parte 2».
            continue

        encontrado_modelo = _MODEL.search(linea)
        cabecera = encontrado_modelo is not None and len(linea.strip()) <= 40
        if cabecera and encontrado_modelo is not None:
            modelo = encontrado_modelo.group(1).upper()

        encontrado_parte = _PART.search(linea)
        if encontrado_parte is not None and len(linea.strip()) <= 60:
            partes.append(encontrado_parte.group(1).upper())
            cabecera = True

        # Una cabecera se **entiende**: no es texto suelto ni se informa como problema.
        if cabecera:
            continue

        marca_clave = _parse_key_line(linea)
        if marca_clave is not None:
            if not en_bloque:
                incidencias.append(
                    ParseIssue(
                        line=numero_linea,
                        code="orphan_key",
                        detail="clave sin pregunta a la que pertenecer",
                    )
                )
                continue
            claves = marca_clave
            continue

        if _OPTION_LABEL.match(linea):
            if not en_bloque:
                incidencias.append(
                    ParseIssue(
                        line=numero_linea,
                        code="orphan_option",
                        detail="opción sin enunciado al que pertenecer",
                    )
                )
                continue
            texto_opcion = strip_option_label(linea)
            if not texto_opcion:
                incidencias.append(
                    ParseIssue(line=numero_linea, code="empty_option", detail="opción vacía")
                )
                continue
            opciones.append(
                ParsedOption(
                    stable_key=_option_key(len(opciones)),
                    text=texto_opcion,
                    position=len(opciones) + 1,
                )
            )
            continue

        encontrado_numero = numbering_match(linea)
        if encontrado_numero is not None:
            cerrar()
            en_bloque = True
            linea_inicio = numero_linea
            numero = int(encontrado_numero.group(1))
            reserva = _RESERVE.search(linea)
            es_reserva = reserva is not None
            orden_reserva = (
                int(reserva.group(1)) if reserva is not None and reserva.group(1) else None
            )
            # La marca de reserva no forma parte del enunciado: se quita del texto, no se guarda.
            resto = _RESERVE.sub("", strip_numbering(linea)).strip()
            lineas_enunciado = [resto] if resto else []
            continue

        if en_bloque and opciones:
            # Línea de continuación de la última opción: se añade a su texto, no se descarta.
            ultima = opciones[-1]
            opciones[-1] = ParsedOption(
                stable_key=ultima.stable_key,
                text=f"{ultima.text} {linea.strip()}".strip(),
                position=ultima.position,
            )
            continue

        if en_bloque:
            lineas_enunciado.append(linea.strip())
            continue

        # Texto suelto antes de la primera pregunta: se informa, no se descarta en silencio.
        incidencias.append(
            ParseIssue(
                line=numero_linea,
                code="text_outside_question",
                detail=f"texto fuera de toda pregunta: {linea.strip()[:60]}",
            )
        )

    cerrar()
    if not preguntas:
        incidencias.append(
            ParseIssue(line=0, code="no_questions", detail="no se reconoció ninguna pregunta")
        )
    return ParsedSet(
        questions=tuple(preguntas),
        issues=tuple(incidencias),
        model_code=modelo,
        parts_detected=tuple(dict.fromkeys(partes)),
    )


# --- importación desde JSON (11_IMPLEMENTATION-SLICES §S06: «asistente CSV/JSON») ---------------

#: Campos que el asistente JSON entiende en cada pregunta. Lo que no esté aquí se **declara** como
#: ignorado en lugar de fingir que se ha importado (misma regla que las columnas del CSV).
JSON_QUESTION_FIELDS = (
    "stem",
    "options",
    "correct",
    "explanation",
    "topic",
    "number",
    "reserve",
    "reserve_order",
    "type",
)

#: Campos que el asistente JSON **lee y todavía no guarda**: se declaran en el informe, no se
#: tiran en silencio. `explanation` y `topic` sí se guardan (van a la explicación y al mapeo).
JSON_UNSTORED_FIELDS = ("tags", "source", "section", "reference", "image", "id")

#: Nombres de tipo que el asistente acepta, con el vocabulario del dominio.
_JSON_TYPES = {tipo.value: tipo for tipo in QuestionType}


def _json_rows(payload: object, issues: list[ParseIssue]) -> tuple[Mapping[str, object], ...]:
    """Las preguntas del sobre JSON, sea una lista o un objeto con `questions`/`items`.

    Un JSON que no es ni una cosa ni la otra no se puede importar: se dice con una incidencia y no
    se inventa nada.
    """
    if isinstance(payload, Mapping):
        for clave in ("questions", "items", "preguntas"):
            valor = payload.get(clave)
            if isinstance(valor, list):
                return tuple(fila for fila in valor if isinstance(fila, Mapping))
            if valor is not None:
                issues.append(
                    ParseIssue(
                        line=0,
                        code="bad_json_shape",
                        detail=f"«{clave}» no es una lista de preguntas",
                    )
                )
                return ()
        issues.append(
            ParseIssue(
                line=0,
                code="bad_json_shape",
                detail="el objeto no trae ninguna lista de preguntas (`questions`, `items`)",
            )
        )
        return ()
    if isinstance(payload, list):
        return tuple(fila for fila in payload if isinstance(fila, Mapping))
    issues.append(
        ParseIssue(
            line=0,
            code="bad_json_shape",
            detail="se esperaba una lista de preguntas o un objeto con «questions»",
        )
    )
    return ()


def _json_key_value(
    bruto: object, *, opciones: Sequence[ParsedOption]
) -> tuple[str, ...] | str | None:
    """Clave de una pregunta JSON: letras/índices/números, o los enunciados exactos de las opciones.

    Devolver el texto de la opción —y no solo la letra— es lo que hace útil el asistente: un JSON
    exportado de otra herramienta trae la respuesta escrita, no su letra. Lo que no se reconoce
    devuelve una cadena con el motivo, que es lo que se le enseña a quien importa.
    """
    textos = [opcion.text.strip() for opcion in opciones]
    if isinstance(bruto, bool):
        return "la respuesta no puede ser un booleano"
    if isinstance(bruto, int):
        indice = bruto - 1
        if 0 <= indice < len(opciones):
            return (opciones[indice].stable_key,)
        return f"la posición {bruto} no corresponde a ninguna opción"
    if isinstance(bruto, str):
        limpio = bruto.strip()
        if not limpio:
            return ()
        if limpio.lower() in {texto.lower() for texto in textos}:
            return tuple(
                opcion.stable_key
                for opcion, texto in zip(opciones, textos, strict=True)
                if texto.lower() == limpio.lower()
            )
        claves: list[str] = []
        for trozo in limpio.lower().replace(",", " ").replace(";", " ").split():
            letra = trozo.strip("()[].").strip()
            if len(letra) == 1 and "a" <= letra <= "h":
                if ord(letra) - ord("a") >= len(opciones):
                    return f"«{bruto.strip()}» no corresponde a ninguna opción"
                claves.append(letra)
            elif letra.isdigit():
                indice = int(letra) - 1
                if indice < 0 or indice >= len(opciones):
                    return f"«{bruto.strip()}» no corresponde a ninguna opción"
                claves.append(opciones[indice].stable_key)
            else:
                return f"«{bruto.strip()}» no corresponde a ninguna opción"
        return tuple(dict.fromkeys(claves))
    if isinstance(bruto, Sequence):
        acumulado: list[str] = []
        for pieza in bruto:
            leida = _json_key_value(pieza, opciones=opciones)
            if isinstance(leida, str):
                return leida
            acumulado.extend(leida or ())
        return tuple(dict.fromkeys(acumulado))
    return f"«{bruto}» no corresponde a ninguna opción"


def _json_text(valor: object) -> str | None:
    """Un campo de texto opcional del JSON: limpio, o `None` si no viene o viene vacío."""
    if isinstance(valor, str) and valor.strip():
        return valor.strip()
    return None


def parse_questions_json(text: str) -> ParsedSet:
    """Parsea el mismo cuestionario en JSON, para el asistente del slice S06.

    Entiende una lista de objetos —o un objeto con `questions`/`items`— donde cada pregunta trae al
    menos `stem` y dos `options`. Todo lo demás (`correct`, `explanation`, `topic`, `number`,
    `reserve`, `reserve_order`, `type`) es opcional y, cuando falta, se deja vacío: el asistente
    **no** inventa una clave que el fichero no trae.

    Dos reglas que vienen de los criterios de aceptación del slice: una pregunta mala **no** aborta
    el lote (se informa con su motivo) y un campo desconocido se **declara** (`json_fields_ignored`
    lo recoge quien llama) en lugar de desaparecer en silencio.
    """
    preguntas: list[ParsedQuestion] = []
    incidencias: list[ParseIssue] = []
    modelo: str | None = None
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError) as error:
        return ParsedSet(
            issues=(
                ParseIssue(line=0, code="not_json", detail=f"el texto no es JSON válido: {error}"),
            )
        )

    if isinstance(payload, Mapping):
        bruto_modelo = payload.get("model_code")
        if isinstance(bruto_modelo, str) and bruto_modelo.strip():
            modelo = bruto_modelo.strip().upper()[:1]
        elif bruto_modelo is not None:
            incidencias.append(
                ParseIssue(line=0, code="bad_model", detail="«model_code» no es un texto")
            )

    for indice, fila in enumerate(_json_rows(payload, incidencias)):
        numero_fila = indice + 1
        stem = fila.get("stem")
        if not isinstance(stem, str) or not stem.strip():
            incidencias.append(
                ParseIssue(line=numero_fila, code="no_stem", detail="la pregunta no trae enunciado")
            )
            continue
        bruto_opciones = fila.get("options")
        if not isinstance(bruto_opciones, list):
            incidencias.append(
                ParseIssue(
                    line=numero_fila,
                    code="no_options",
                    detail="la pregunta no trae una lista de opciones",
                )
            )
            continue
        textos: list[str] = []
        for opcion in bruto_opciones:
            # Un texto sin etiqueta también vale: se quita la etiqueta **solo si la trae**.
            limpio = strip_option_label(opcion).strip() if isinstance(opcion, str) else ""
            if not limpio:
                textos = []
                break
            textos.append(limpio)
        if len(textos) < 2:
            incidencias.append(
                ParseIssue(
                    line=numero_fila,
                    code="few_options",
                    detail=f"la pregunta trae {len(textos)} opción(es) legibles: hacen falta dos",
                )
            )
            continue
        opciones = tuple(
            ParsedOption(
                stable_key=_option_key(orden),
                text=texto,
                position=orden + 1,
            )
            for orden, texto in enumerate(textos)
        )

        claves: tuple[str, ...] = ()
        if "correct" in fila:
            leida = _json_key_value(fila.get("correct"), opciones=opciones)
            if isinstance(leida, str):
                incidencias.append(
                    ParseIssue(line=numero_fila, code="key_without_option", detail=leida)
                )
                continue
            claves = leida or ()

        tipo: QuestionType | None = None
        motivo: str | None = None
        bruto_tipo = fila.get("type")
        if isinstance(bruto_tipo, str) and bruto_tipo.strip():
            tipo = _JSON_TYPES.get(bruto_tipo.strip().lower())
            if tipo is None:
                incidencias.append(
                    ParseIssue(
                        line=numero_fila,
                        code="unknown_type",
                        detail=(
                            f"«{bruto_tipo.strip()}» no es un tipo de pregunta conocido: "
                            f"{', '.join(sorted(_JSON_TYPES))}"
                        ),
                    )
                )
                continue
            motivo = "el fichero declara el tipo"
        if tipo is None:
            tipo, motivo = _infer_type(stem.strip(), opciones)

        bruto_numero = fila.get("number")
        numero: int | None = None
        if isinstance(bruto_numero, int) and not isinstance(bruto_numero, bool):
            numero = bruto_numero
        elif isinstance(bruto_numero, str) and bruto_numero.strip().isdigit():
            numero = int(bruto_numero.strip())
        elif bruto_numero is not None:
            incidencias.append(
                ParseIssue(
                    line=numero_fila,
                    code="bad_number",
                    detail="«number» no es un número entero",
                )
            )

        bruto_reserva = fila.get("reserve")
        if isinstance(bruto_reserva, bool):
            reserva = bruto_reserva
        elif isinstance(bruto_reserva, str):
            reserva = _is_truthy(bruto_reserva)
        elif isinstance(bruto_reserva, int):
            reserva = bruto_reserva != 0
        else:
            reserva = False
        bruto_orden = fila.get("reserve_order")
        orden_reserva = (
            bruto_orden
            if isinstance(bruto_orden, int) and not isinstance(bruto_orden, bool)
            else None
        )
        if orden_reserva is not None:
            reserva = True

        explicaciones, incidencia_explicacion = _json_option_explanations(
            fila.get("explanations"), opciones=opciones
        )
        if incidencia_explicacion is not None:
            incidencias.append(
                ParseIssue(
                    line=numero_fila,
                    code="explanation_without_option",
                    detail=incidencia_explicacion,
                )
            )

        preguntas.append(
            ParsedQuestion(
                number=numero,
                stem=stem.strip(),
                options=opciones,
                question_type=tipo,
                line=numero_fila,
                is_reserve=reserva,
                reserve_order=orden_reserva,
                correct_option_keys=claves,
                type_reason=motivo,
                option_explanations=explicaciones,
                explanation=_json_text(fila.get("explanation")),
                topic=_json_text(fila.get("topic")),
            )
        )

    return ParsedSet(
        questions=tuple(preguntas),
        issues=tuple(incidencias),
        model_code=modelo,
        ignored_fields=_json_ignored_fields(payload),
    )


def _json_option_explanations(
    bruto: object, *, opciones: Sequence[ParsedOption]
) -> tuple[tuple[tuple[str, str], ...], str | None]:
    """Explicaciones **por opción** de una pregunta JSON (S12.7).

    El formato es `"explanations": {"b": "por qué la b no vale", ...}`, con la clave de la opción
    (letra) o el texto exacto de la opción, igual que la respuesta. Lo que no se puede atribuir a
    una opción **no se guarda** y se informa: una explicación colgada de la opción equivocada es
    peor que ninguna, porque enseña mal.
    """
    if bruto is None:
        return (), None
    if not isinstance(bruto, Mapping):
        return (), "«explanations» no es un objeto de opción → explicación"
    textos = [opcion.text.strip().lower() for opcion in opciones]
    pares: list[tuple[str, str]] = []
    sin_pareja: list[str] = []
    for clave, valor in bruto.items():
        if not isinstance(valor, str) or not valor.strip():
            continue
        destino: str | None = None
        referencia = str(clave).strip().lower()
        if len(referencia) == 1 and "a" <= referencia <= "h":
            if ord(referencia) - ord("a") < len(opciones):
                destino = opciones[ord(referencia) - ord("a")].stable_key
        elif referencia in textos:
            destino = opciones[textos.index(referencia)].stable_key
        if destino is None:
            sin_pareja.append(str(clave).strip())
            continue
        pares.append((destino, valor.strip()))
    motivo = (
        f"estas claves de «explanations» no corresponden a ninguna opción: {', '.join(sin_pareja)}"
        if sin_pareja
        else None
    )
    return tuple(pares), motivo


def _json_ignored_fields(payload: object) -> tuple[str, ...]:
    """Campos que el JSON trae y el asistente no guarda, en orden y sin repetir.

    Se declaran para que el informe pueda decir «esto lo he leído y no lo he guardado», que es lo
    contrario de perderlo por el camino sin decirlo.
    """
    vistas: list[str] = []
    for fila in _json_rows(payload, []):
        for clave in fila:
            if clave in JSON_UNSTORED_FIELDS and clave not in vistas:
                vistas.append(clave)
    return tuple(vistas)


def _is_truthy(value: str) -> bool:
    """Síes de un campo JSON que viene como texto. Lo demás es «no», sin inventar."""
    return value.strip().lower() in {"1", "s", "si", "sí", "r", "reserva", "true", "x", "yes"}


@dataclass(frozen=True, slots=True)
class ParsedKeyLine:
    """Una línea de una plantilla: número de pregunta y opción, u otro desenlace."""

    position: int
    outcome: KeyOutcome
    correct_option_keys: tuple[str, ...] = ()
    line: int = 0
    note: str | None = None
    """Lo que la plantilla dice de esa respuesta además de la letra: «modificada» (la Comisión la
    cambió tras las alegaciones), «rectificada»… Se guarda con la entrada de la clave."""


#: Línea de plantilla: `1. b`, `12-a`, `3 anulada`, `4 sin responder`. El separador es opcional,
#: pero algo tiene que separar el número de lo que viene detrás.
_KEY_SHEET = re.compile(r"^\s*(\d{1,3})\s*(?:[.)\-\u2013:]+\s*|\s+)(.+)$")
_ANNULLED = re.compile(r"\banulada\b|\bnula\b|^\s*[-x]\s*$", re.IGNORECASE)
_UNANSWERED = re.compile(r"sin\s+responder|no\s+contestada|\bblanco\b", re.IGNORECASE)
#: Un número de pregunta **solo** en su línea: `1.`, `12)`, `3 -`. El PDF de las plantillas
#: oficiales del INAP (TAI 2025) saca así las preguntas 1 a 9, con la letra en la línea de abajo.
_KEY_NUMBER_ALONE = re.compile(r"^\s*(\d{1,3})\s*[.)\-\u2013:]*\s*$")
#: Lo que puede ser la respuesta de esa línea de abajo: una o varias letras, o un desenlace.
#: Marca que una plantilla definitiva pone junto a una respuesta cambiada: «d MODIFICADA».
_KEY_AMENDMENT = re.compile(
    r"\(?\s*\b(modificada|rectificada|corregida|cambiada)\b\s*\)?", re.IGNORECASE
)
_KEY_ANSWER_ALONE = re.compile(
    r"^\s*(?:[a-hA-H](?:\s*[,y]\s*[a-hA-H])*"
    r"(?:\s*\(?\s*(?:modificada|rectificada|corregida|cambiada)\s*\)?)?"
    r"|anulada|nula|sin\s+responder|[-x])\s*$",
    re.IGNORECASE,
)


def _join_split_key_lines(lineas: list[str]) -> list[tuple[int, str]]:
    """Junta «1.» con la respuesta de la línea siguiente cuando la extracción las separó.

    Devuelve `(número de línea original, texto)`. Solo se junta si la línea es **solo** un número
    y la siguiente con contenido es **solo** una respuesta: así un encabezado como «Supuesto I» o un
    enunciado nunca se pega a nada.
    """
    resultado: list[tuple[int, str]] = []
    indice = 0
    while indice < len(lineas):
        linea = lineas[indice]
        numero = _KEY_NUMBER_ALONE.match(linea)
        if numero is not None:
            siguiente = indice + 1
            while siguiente < len(lineas) and not lineas[siguiente].strip():
                siguiente += 1
            if siguiente < len(lineas) and _KEY_ANSWER_ALONE.match(lineas[siguiente]):
                resultado.append((indice + 1, f"{numero.group(1)}. {lineas[siguiente].strip()}"))
                indice = siguiente + 1
                continue
        resultado.append((indice + 1, linea))
        indice += 1
    return resultado


#: El modelo del examen, cuando la plantilla lo declara: «Modelo A», «MODELO B», «modelo: A».
#: Un examen oficial sale en varios modelos y cada uno tiene **su** plantilla: enlazar la equivocada
#: corrige el examen con las respuestas de otro (S12.6).
_KEY_MODEL = re.compile(r"\bmodelo\s*:?\s*([A-Z])\b", re.IGNORECASE)


def parse_key_model(text: str) -> str | None:
    """El modelo que declara una plantilla de respuestas, si lo declara.

    Devuelve la letra en mayúsculas (`A`, `B`) o `None` cuando la plantilla no dice de qué modelo
    es. No se adivina por el nombre del fichero ni por la fecha: un enlace equivocado corrige un
    examen entero con las respuestas de otro, y eso es peor que no enlazar nada.
    """
    encontrado = _KEY_MODEL.search(text)
    return encontrado.group(1).upper() if encontrado is not None else None


def parse_answer_key(text: str) -> tuple[tuple[ParsedKeyLine, ...], tuple[ParseIssue, ...]]:
    """Parsea una plantilla suelta: `1. b`, `2-a`, `3 anulada`, `4 sin responder`.

    Una plantilla es un documento **independiente** (04_INGESTION §10, paso 6): se lee aparte y
    luego se alinea con las preguntas por número. Lo que no se entiende se informa y no se
    convierte en una clave inventada.
    """
    lineas: list[ParsedKeyLine] = []
    incidencias: list[ParseIssue] = []
    for numero_linea, linea in _join_split_key_lines(text.splitlines()):
        if not linea.strip():
            continue
        encontrado = _KEY_SHEET.match(linea)
        if encontrado is None:
            incidencias.append(
                ParseIssue(
                    line=numero_linea,
                    code="key_line_unreadable",
                    detail=f"no se entiende la línea: {linea.strip()[:60]}",
                )
            )
            continue
        posicion = int(encontrado.group(1))
        resto = encontrado.group(2).strip()
        if _ANNULLED.search(resto):
            lineas.append(
                ParsedKeyLine(position=posicion, outcome=KeyOutcome.ANNULLED, line=numero_linea)
            )
            continue
        if _UNANSWERED.search(resto):
            lineas.append(
                ParsedKeyLine(position=posicion, outcome=KeyOutcome.UNANSWERED, line=numero_linea)
            )
            continue
        claves = tuple(
            letra.lower() for letra in re.findall(r"\b([a-hA-H])\b", resto.replace(",", " "))
        )
        if not claves:
            incidencias.append(
                ParseIssue(
                    line=numero_linea,
                    code="key_line_without_option",
                    detail=f"línea de plantilla sin opción: {resto[:60]}",
                )
            )
            continue
        enmienda = _KEY_AMENDMENT.search(resto)
        lineas.append(
            ParsedKeyLine(
                position=posicion,
                outcome=KeyOutcome.KEYED,
                correct_option_keys=claves,
                line=numero_linea,
                note=None if enmienda is None else f"respuesta {enmienda.group(1).lower()}",
            )
        )
    return tuple(lineas), tuple(incidencias)


@dataclass(frozen=True, slots=True)
class KeyAlignment:
    """Cómo encaja una plantilla suelta con un conjunto **por número de pregunta**.

    Mira en las dos direcciones, y no se fía de un número compartido:

    - `matched`: líneas cuyo número es el de **una sola** pregunta del conjunto;
    - `ambiguous`: líneas cuyo número tienen varias preguntas (un conjunto con secciones que
      vuelven a numerar desde 1): por número no se sabe a cuál se refiere;
    - `covered` / `questions`: preguntas del conjunto que reciben respuesta, de todas.

    Antes solo se miraba la primera dirección: 93 líneas sobre un conjunto de 135 preguntas con la
    numeración reiniciada daban «100 % de encaje» (informe de claves de octubre de 2026).
    """

    lines: int
    matched: int
    ambiguous: int
    covered: int
    questions: int

    @property
    def score(self) -> float:
        """Lo peor de las dos direcciones: una plantilla buena encaja **y** cubre el conjunto."""
        if self.lines == 0 or self.questions == 0:
            return 0.0
        return min(self.matched / self.lines, self.covered / self.questions)


def key_alignment(
    lines: Sequence[ParsedKeyLine], by_position: Mapping[int, Sequence[str]]
) -> KeyAlignment:
    """Alinea las líneas de una plantilla con las preguntas de un conjunto, por su número."""
    emparejadas = 0
    ambiguas = 0
    cubiertas: set[str] = set()
    for linea in lines:
        candidatas = by_position.get(linea.position, ())
        if len(candidatas) == 1:
            emparejadas += 1
            cubiertas.add(candidatas[0])
        elif len(candidatas) > 1:
            ambiguas += 1
    preguntas = {pregunta for ids in by_position.values() for pregunta in ids}
    return KeyAlignment(
        lines=len(lines),
        matched=emparejadas,
        ambiguous=ambiguas,
        covered=len(cubiertas),
        questions=len(preguntas),
    )


def ordered_key_mapping(
    lines: Sequence[ParsedKeyLine], questions_in_order: Sequence[tuple[str, int]]
) -> tuple[str, ...] | None:
    """Empareja las líneas de una plantilla con las preguntas **en orden**, si y solo si encajan.

    Es para los exámenes cuya numeración vuelve a empezar en cada sección (TAI 2025: dos partes
    que numeran desde 1). Por número no se pueden alinear —el «12» es de las dos partes—, pero en
    orden sí: la plantilla lista las respuestas en el mismo orden que el examen.

    La regla es estricta a propósito, porque emparejar mal corrige mal: tiene que haber **tantas
    líneas como preguntas** y el número de cada línea tiene que ser **el de su pregunta**, uno a
    uno. Si algo no cuadra (una pregunta de más, una línea de menos, un número cambiado) devuelve
    `None` y quien llama sigue por número. Solo se usa si hay números repetidos: sin ellos, el
    número basta.

    `questions_in_order` son `(id, posición)` en el orden del documento.
    """
    if not lines or len(lines) != len(questions_in_order):
        return None
    posiciones = [posicion for _id, posicion in questions_in_order]
    if len(set(posiciones)) == len(posiciones):
        return None
    if any(
        linea.position != posicion
        for linea, (_id, posicion) in zip(lines, questions_in_order, strict=True)
    ):
        return None
    return tuple(pregunta_id for pregunta_id, _posicion in questions_in_order)


__all__ = [
    "JSON_QUESTION_FIELDS",
    "REORDERED_OPTIONS",
    "SAME_QUESTION",
    "SIMILAR_QUESTION",
    "AnswerKeyEntry",
    "AnswerKeyVersion",
    "EvidenceRole",
    "ExplanationStatus",
    "KeyAlignment",
    "KeyOutcome",
    "KeyStatus",
    "OptionVersion",
    "Origin",
    "ParseIssue",
    "ParsedKeyLine",
    "ParsedOption",
    "ParsedQuestion",
    "ParsedSet",
    "QuestionDuplicateGroup",
    "QuestionFingerprint",
    "QuestionSet",
    "QuestionStatus",
    "QuestionType",
    "QuestionVersion",
    "SetDistribution",
    "SetStatus",
    "SetType",
    "can_activate",
    "find_question_duplicates",
    "key_alignment",
    "normalise_question_text",
    "numbering_match",
    "ordered_key_mapping",
    "parse_answer_key",
    "parse_questions",
    "parse_questions_json",
    "question_fingerprint",
    "same_options_in_other_order",
    "strip_markdown_decoration",
    "strip_numbering",
    "strip_option_label",
]
