"""Búsqueda y RAG: corpus elegible, fusión de rankings y respuesta con citas (05_RAG §1-§6).

Cuatro reglas que este módulo implementa y que son criterios de aceptación del slice:

1. **RAG no es la fuente de verdad** (§1): solo se recupera material **publicado y vigente**, y lo
    que
   no está respaldado por una evidencia entregada se declara insuficiente. No hay forma de que una
   afirmación sin cita salga como `supported`.
2. **FTS funciona sin vectores ni modelo** (§5): la búsqueda léxica es la base, y sin proveedor de
   embeddings la recuperación sigue siendo completa (solo deja de ser híbrida, y lo dice).
3. **Las afirmaciones solo citan lo que se entregó** (§6): cada claim lleva los identificadores de
    los
   fragmentos usados, y `assert_grounded` comprueba que todos existan entre los entregados. Una cita
       a
   un fragmento que no se usó es un fallo, no un detalle.
4. **Nada se mezcla en silencio** (§7): si falta un término de la pregunta, la respuesta es
    `partial` y
   se dice qué no se ha encontrado; si el corpus no cubre la pregunta, es `insufficient` y no se
   inventa una respuesta aproximada.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from opofuente.domain.errors import InvariantViolationError

# --- vocabularios (los mismos que la migración 0018) --------------------------------------------


class AnswerStatus(StrEnum):
    """Lo que la aplicación puede afirmar de una respuesta (§6)."""

    SUPPORTED = "supported"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class ClaimSupport(StrEnum):
    DIRECT = "direct"
    INFERRED = "inferred"


class SearchStrategy(StrEnum):
    """Cómo se recupera: solo léxica o léxica más vectorial (§5)."""

    LEXICAL = "lexical"
    HYBRID = "hybrid"


class VersionMode(StrEnum):
    """Vigente por defecto; una versión histórica hay que pedirla (§2)."""

    CURRENT = "current"
    EXPLICIT_HISTORICAL = "explicit_historical"


#: Estados de versión que se pueden recuperar. `candidate`, `superseded`, `rejected` y `withdrawn`
#: quedan fuera salvo que se pida explícitamente una versión histórica (§2).
RETRIEVABLE_STATUSES = ("accepted", "outdated")

#: Calidades de representación admitidas: una extracción pobre no sostiene una cita (§2).
RETRIEVABLE_QUALITIES = ("good", "usable_with_warnings")

#: Palabras que no cuentan para decidir si una respuesta está respaldada: sin ellas, «¿cuál es el
#: plazo del artículo 5?» se declararía parcial por no encontrar «es», «el» o «del».
STOPWORDS = frozenset(
    {
        "a",
        "al",
        "algo",
        "como",
        "con",
        "cual",
        "cuando",
        "de",
        "del",
        "donde",
        "el",
        "en",
        "es",
        "esta",
        "este",
        "la",
        "las",
        "lo",
        "los",
        "mas",
        "más",
        "me",
        "ni",
        "no",
        "o",
        "para",
        "pero",
        "por",
        "que",
        "qué",
        "se",
        "sin",
        "sobre",
        "son",
        "su",
        "sus",
        "un",
        "una",
        "y",
        "ya",
    }
)


def normalise(text: str) -> str:
    """Texto normalizado para comparar: sin acentos, sin signos y en minúsculas.

    Es la misma normalización con la que se indexa (`evidence_spans.normalized_text`), así que lo
        que
    se compara y lo que se guarda no pueden divergir.
    """
    descompuesto = unicodedata.normalize("NFKD", text.lower())
    sin_acentos = "".join(
        caracter for caracter in descompuesto if not unicodedata.combining(caracter)
    )
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", sin_acentos)).strip()


def significant_terms(question: str) -> tuple[str, ...]:
    """Términos que la respuesta tiene que poder respaldar: sin palabras vacías y sin repetidos.

    Una cifra cuenta aunque sea de un solo carácter: «artículo 5» y «plazo de 5 días» se responden o
    no se responden por ese número, y descartarlo convertiría la pregunta en otra.
    """
    terminos = [palabra for palabra in normalise(question).split() if palabra not in STOPWORDS]
    return tuple(
        dict.fromkeys(palabra for palabra in terminos if len(palabra) > 1 or palabra.isdigit())
    )


def match_expression(question: str) -> str:
    """La pregunta convertida en expresión FTS5: términos entre comillas, unidos con `OR`.

    `OR` a propósito: recuperar de más y ordenar por relevancia es mejor que no recuperar nada
        porque
    falte una palabra. Cada término va entre comillas para que un guion o un paréntesis de la
        pregunta
    no se interprete como sintaxis de FTS5.
    """
    terminos = significant_terms(question)
    if not terminos:
        # Una pregunta sin términos útiles (solo signos o palabras vacías) no se puede buscar.
        limpio = normalise(question).strip()
        if not limpio:
            raise InvariantViolationError("una búsqueda necesita texto")
        return f'"{limpio}"'
    return " OR ".join(f'"{termino}"*' for termino in terminos)


# --- corpus elegible (§2) -----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CorpusDecision:
    eligible: bool
    reason: str | None = None


def corpus_eligible(
    *,
    version_status: str,
    representation_quality: str | None,
    valid_from: date | None,
    valid_to: date | None,
    reference_date: date | None,
    version_mode: VersionMode = VersionMode.CURRENT,
) -> CorpusDecision:
    """¿Se puede recuperar esta versión para esta consulta? Y si no, por qué.

    El motivo viaja siempre: un resultado que falta sin explicación es indistinguible de un fallo.
    """
    if version_mode is VersionMode.CURRENT:
        if version_status not in RETRIEVABLE_STATUSES:
            return CorpusDecision(False, f"la versión está en estado «{version_status}»")
        if (
            representation_quality is not None
            and representation_quality not in RETRIEVABLE_QUALITIES
        ):
            return CorpusDecision(
                False, f"la representación es «{representation_quality}» y no sostiene una cita"
            )
        if reference_date is not None:
            if valid_from is not None and valid_from > reference_date:
                return CorpusDecision(False, "la versión todavía no estaba vigente en esa fecha")
            if valid_to is not None and valid_to < reference_date:
                return CorpusDecision(False, "la versión ya no estaba vigente en esa fecha")
    return CorpusDecision(True)


@dataclass(frozen=True, slots=True)
class SearchFilters:
    """Filtros de una consulta (08_API-CONTRACT §8).

    `include_obsolete` está **apagado** por defecto: una versión sustituida no aparece salvo que se
    pida mirar el histórico, y entonces la pantalla lo dice.
    """

    opposition_id: str | None = None
    convocation_id: str | None = None
    curriculum_node_ids: tuple[str, ...] = ()
    document_ids: tuple[str, ...] = ()
    authority_tier: str | None = None
    reference_date: date | None = None
    version_mode: VersionMode = VersionMode.CURRENT
    languages: tuple[str, ...] = ()
    limit: int = 10

    @property
    def include_obsolete(self) -> bool:
        return self.version_mode is VersionMode.EXPLICIT_HISTORICAL


# --- fragmentos y fusión de rankings ------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CandidateSpan:
    """Un fragmento candidato, con lo que hace falta para citarlo y para decidir si vale.

    `score` es el del ranking que lo trajo y `strategy` dice de cuál viene: sin eso no se puede
    explicar por qué un fragmento salió primero, ni fusionar dos búsquedas sin mezclarlas a ciegas.
    """

    span_id: str
    document_version_id: str
    document_id: str
    document_title: str
    document_type: str
    authority_tier: str | None
    version_status: str
    citation_label: str | None
    page: int | None
    section_id: str | None
    section_title: str | None
    text: str
    score: float
    strategy: SearchStrategy
    matched_terms: tuple[str, ...] = ()
    valid_from: date | None = None
    valid_to: date | None = None


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]], *, k: int = 60
) -> tuple[tuple[str, float], ...]:
    """Fusiona rankings por Reciprocal Rank Fusion (§5, paso 4).

    RRF usa **posiciones**, no puntuaciones: así no hay que normalizar escalas que no son
        comparables
    (una distancia vectorial y un `bm25` no lo son) y un fragmento que sale bien en las dos
        búsquedas
    sube sin que ninguna domine.
    """
    acumulado: dict[str, float] = {}
    for ranking in rankings:
        for posicion, identificador in enumerate(ranking, start=1):
            acumulado[identificador] = acumulado.get(identificador, 0.0) + 1.0 / (k + posicion)
    return tuple(sorted(acumulado.items(), key=lambda par: (-par[1], par[0])))


def diversify(
    spans: Sequence[CandidateSpan], *, limit: int, max_por_documento: int = 3
) -> tuple[CandidateSpan, ...]:
    """Diversifica evitando diez fragmentos equivalentes (§5, paso 7).

    Se limita cuántos fragmentos entran por documento, pero **no se descarta** lo que sobra: si no
        hay
    suficientes documentos, los siguientes entran igual, porque quedarse sin evidencia es peor que
    repetir fuente.
    """
    elegidos: list[CandidateSpan] = []
    por_documento: dict[str, int] = {}
    for span in spans:
        if len(elegidos) >= limit:
            break
        if por_documento.get(span.document_id, 0) >= max_por_documento:
            continue
        por_documento[span.document_id] = por_documento.get(span.document_id, 0) + 1
        elegidos.append(span)
    if len(elegidos) < min(limit, len(spans)):
        ya = {span.span_id for span in elegidos}
        for span in spans:
            if len(elegidos) >= limit:
                break
            if span.span_id not in ya:
                elegidos.append(span)
    return tuple(elegidos)


# --- respuesta con citas (§6) -------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Claim:
    """Una afirmación con las evidencias que la sostienen. Sin evidencias no hay afirmación."""

    text: str
    evidence_ids: tuple[str, ...]
    support: ClaimSupport = ClaimSupport.DIRECT


@dataclass(frozen=True, slots=True)
class RagDraft:
    """La respuesta antes de guardarla: lo que la aplicación se atreve a decir y con qué
    respaldo."""

    status: AnswerStatus
    short_answer: str
    explanation: str
    claims: tuple[Claim, ...] = ()
    uncertainties: tuple[str, ...] = ()
    suggested_followups: tuple[str, ...] = ()
    missing_terms: tuple[str, ...] = ()

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                identificador for claim in self.claims for identificador in claim.evidence_ids
            )
        )


#: Cuánto texto de un fragmento entra en una respuesta extractiva: es una cita, no un resumen.
EXTRACT_CHARS = 320


def _extract(text: str, *, limite: int = EXTRACT_CHARS) -> str:
    limpio = " ".join(text.split())
    if len(limpio) <= limite:
        return limpio
    recortado = limpio[:limite].rsplit(" ", 1)[0]
    return f"{recortado}…"


def assert_grounded(draft: RagDraft, delivered_ids: Sequence[str]) -> None:
    """Comprueba que **todas** las citas existen y se entregaron al redactor (§6).

    Se ejecuta antes de guardar nada: una cita a un fragmento que no se usó (o que no existe) impide
    publicar la respuesta como respaldada.
    """
    permitidos = set(delivered_ids)
    for claim in draft.claims:
        if not claim.evidence_ids:
            raise InvariantViolationError(
                f"una afirmación sin evidencia no se publica: «{claim.text[:60]}»"
            )
        desconocidas = [
            identificador for identificador in claim.evidence_ids if identificador not in permitidos
        ]
        if desconocidas:
            raise InvariantViolationError(
                "una afirmación cita evidencia que no se entregó: " + ", ".join(desconocidas)
            )
    if draft.status is AnswerStatus.SUPPORTED and not draft.claims:
        raise InvariantViolationError(
            "una respuesta respaldada necesita al menos una afirmación citada"
        )


def compose_extractive_answer(
    question: str,
    delivered: Sequence[CandidateSpan],
    *,
    max_claims: int = 3,
) -> RagDraft:
    """Respuesta **extractiva**, sin modelo de lenguaje (§5: «FTS sigue funcionando sin LLM»).

    No redacta: elige lo que sostiene la pregunta y lo cita tal cual. Con eso se cumplen las tres
    obligaciones del contrato de respuesta sin depender de ningún proveedor:

    - cada término significativo de la pregunta que aparezca en los fragmentos entregados queda
      respaldado; los que no aparezcan se declaran como incertidumbre y la respuesta baja a
          `partial`;
    - sin fragmentos entregados que cubran algo, la respuesta es `insufficient` y **no lleva
      afirmaciones**: es la respuesta correcta a una pregunta fuera del corpus, no un fallo;
    - cada afirmación cita el fragmento del que sale su texto, y solo fragmentos entregados.
    """
    terminos = significant_terms(question)
    if not delivered:
        return RagDraft(
            status=AnswerStatus.INSUFFICIENT,
            short_answer="No hay evidencia en el corpus para responder a esto.",
            explanation=(
                "No se ha recuperado ningún fragmento del material publicado que trate esta "
                "pregunta. Puede que el tema no esté en el corpus, o que lo esté en una versión "
                "no vigente."
            ),
            missing_terms=terminos,
            suggested_followups=(
                "Importar material sobre el tema y volver a preguntar",
                "Comprobar si la pregunta usa el vocabulario del programa",
            ),
        )

    cubiertos: dict[str, list[CandidateSpan]] = {termino: [] for termino in terminos}
    for span in delivered:
        normalizado = normalise(span.text)
        for termino in terminos:
            if termino in normalizado:
                cubiertos[termino].append(span)
    faltan = tuple(termino for termino, spans in cubiertos.items() if not spans)

    usados = tuple(delivered[:max_claims])
    claims = tuple(
        Claim(
            text=_extract(span.text),
            evidence_ids=(span.span_id,),
            support=ClaimSupport.DIRECT,
        )
        for span in usados
    )

    lugares = ", ".join(
        dict.fromkeys(span.citation_label or span.document_title for span in usados)
    )
    if faltan:
        estado = AnswerStatus.PARTIAL
        respuesta_corta = (
            f"El corpus sostiene parte de la pregunta. No se ha encontrado nada sobre: "
            f"{', '.join(faltan)}."
        )
        explicacion = (
            f"Se han recuperado {len(usados)} fragmentos de {lugares}, y ninguno cubre "
            f"«{', '.join(faltan)}». Lo que se muestra está citado; lo que falta, también se dice."
        )
    else:
        estado = AnswerStatus.SUPPORTED
        respuesta_corta = _extract(usados[0].text)
        explicacion = (
            f"Respuesta extraída de {len(usados)} fragmento(s) del corpus ({lugares}). "
            "No es una redacción del modelo: es el texto de las evidencias, tal cual."
        )

    return RagDraft(
        status=estado,
        short_answer=respuesta_corta,
        explanation=explicacion,
        claims=claims,
        uncertainties=((f"no se ha encontrado nada sobre: {', '.join(faltan)}",) if faltan else ()),
        suggested_followups=tuple(
            dict.fromkeys(f"buscar «{span.section_title}»" for span in usados if span.section_title)
        ),
        missing_terms=faltan,
    )


@dataclass
class RetrievalPack:
    """El paquete de evidencia que se entrega (y que se guarda, §5 paso 9)."""

    hits: tuple[CandidateSpan, ...] = ()
    degradations: tuple[str, ...] = field(default_factory=tuple)
    strategies: tuple[SearchStrategy, ...] = ()

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(span.span_id for span in self.hits)


def fuse_candidates(
    lexical: Sequence[CandidateSpan],
    vector: Sequence[CandidateSpan] = (),
    *,
    limit: int,
) -> RetrievalPack:
    """Fusiona lo que devolvió cada estrategia y devuelve el paquete de evidencia.

    Si no hay resultados vectoriales, se devuelve la lista léxica **tal cual** y se dice que la
    búsqueda fue solo léxica: es lo que exige §5 («FTS sigue funcionando si embeddings están
    desactivados»), sin fingir una fusión que no ocurrió.
    """
    por_id: dict[str, CandidateSpan] = {span.span_id: span for span in lexical}
    for span in vector:
        por_id.setdefault(span.span_id, span)

    if not vector:
        return RetrievalPack(
            hits=diversify(list(lexical), limit=limit),
            strategies=(SearchStrategy.LEXICAL,),
            degradations=("sin proveedor de embeddings: la búsqueda ha sido solo léxica (FTS5)",),
        )

    ranking = reciprocal_rank_fusion(
        [[span.span_id for span in lexical], [span.span_id for span in vector]]
    )
    ordenados = [por_id[identificador] for identificador, _ in ranking if identificador in por_id]
    return RetrievalPack(
        hits=diversify(ordenados, limit=limit),
        strategies=(SearchStrategy.LEXICAL, SearchStrategy.HYBRID),
    )


def terms_in_delivered(terms: Mapping[str, Sequence[str]]) -> tuple[str, ...]:
    """Ayuda para la interfaz: términos de la pregunta sin ningún fragmento que los cubra."""
    return tuple(termino for termino, spans in terms.items() if not spans)
