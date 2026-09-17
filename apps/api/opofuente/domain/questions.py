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

    for numero_linea, linea in enumerate(text.splitlines(), 1):
        if not linea.strip():
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


@dataclass(frozen=True, slots=True)
class ParsedKeyLine:
    """Una línea de una plantilla: número de pregunta y opción, u otro desenlace."""

    position: int
    outcome: KeyOutcome
    correct_option_keys: tuple[str, ...] = ()
    line: int = 0


#: Línea de plantilla: `1. b`, `12-a`, `3 anulada`, `4 sin responder`. El separador es opcional,
#: pero algo tiene que separar el número de lo que viene detrás.
_KEY_SHEET = re.compile(r"^\s*(\d{1,3})\s*(?:[.)\-\u2013:]+\s*|\s+)(.+)$")
_ANNULLED = re.compile(r"\banulada\b|\bnula\b|^\s*[-x]\s*$", re.IGNORECASE)
_UNANSWERED = re.compile(r"sin\s+responder|no\s+contestada|\bblanco\b", re.IGNORECASE)


def parse_answer_key(text: str) -> tuple[tuple[ParsedKeyLine, ...], tuple[ParseIssue, ...]]:
    """Parsea una plantilla suelta: `1. b`, `2-a`, `3 anulada`, `4 sin responder`.

    Una plantilla es un documento **independiente** (04_INGESTION §10, paso 6): se lee aparte y
    luego se alinea con las preguntas por número. Lo que no se entiende se informa y no se
    convierte en una clave inventada.
    """
    lineas: list[ParsedKeyLine] = []
    incidencias: list[ParseIssue] = []
    for numero_linea, linea in enumerate(text.splitlines(), 1):
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
        lineas.append(
            ParsedKeyLine(
                position=posicion,
                outcome=KeyOutcome.KEYED,
                correct_option_keys=claves,
                line=numero_linea,
            )
        )
    return tuple(lineas), tuple(incidencias)


__all__ = [
    "REORDERED_OPTIONS",
    "SAME_QUESTION",
    "SIMILAR_QUESTION",
    "AnswerKeyEntry",
    "AnswerKeyVersion",
    "EvidenceRole",
    "ExplanationStatus",
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
    "SetStatus",
    "SetType",
    "can_activate",
    "find_question_duplicates",
    "normalise_question_text",
    "numbering_match",
    "parse_answer_key",
    "parse_questions",
    "question_fingerprint",
    "same_options_in_other_order",
    "strip_numbering",
    "strip_option_label",
]
