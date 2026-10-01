"""Documentos, versiones y derechos (S05): reglas puras, sin base de datos ni red.

La biblioteca convierte material copiado en **obras**: un documento lógico (la obra) con sus
versiones (los ficheros concretos que la representan), sus derechos y su vigencia. Aquí viven las
reglas que la aplicación no puede decidir a ojo:

- **`owner_scope`**: un documento privado **nunca** pasa a público por una clasificación
  automática (03_DATA-MODEL §4). Público solo lo es si alguien lo dice expresamente.
- **Vigencia**: de las versiones hay **una activa**. Manda la aceptada; una candidata
  se muestra como propuesta de cambio, nunca como la versión buena.
- **Nada se pierde**: una versión sustituida sigue existiendo y su contenido sigue siendo citable.
- **Derechos**: lo desconocido se trata como **privado y restringido** (09_SECURITY §8) y no se
  presentar como reutilizable. Conservar atribución, URL, fecha y licencia es obligatorio.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from opofuente.domain.classification import DocumentType  # vocabulario único, no dos listas


class OwnerScope(StrEnum):
    """De quién es la obra. Es lo que decide si se puede mostrar o compartir."""

    PUBLIC = "public"
    PRIVATE_USER = "private_user"
    GENERATED = "generated"


class VersionStatus(StrEnum):
    """Estados de una versión (03_DATA-MODEL §4)."""

    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    OUTDATED = "outdated"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    REJECTED = "rejected"


class RightsReview(StrEnum):
    """Estado de revisión de los derechos de una fuente."""

    UNKNOWN = "unknown"
    REVIEWED = "reviewed"
    RESTRICTED = "restricted"


#: Estados desde los que se puede aceptar una versión sin destruir historia.
ACCEPTABLE_FROM: frozenset[VersionStatus] = frozenset(
    {VersionStatus.CANDIDATE, VersionStatus.OUTDATED}
)

#: Estados desde los que una versión se puede **retirar**: deja de buscarse y citarse, sin borrarse.
#: Una sustituida ya está fuera del corpus y una rechazada nunca entró.
WITHDRAWABLE_FROM: frozenset[VersionStatus] = frozenset(
    {VersionStatus.CANDIDATE, VersionStatus.ACCEPTED, VersionStatus.OUTDATED}
)

#: Estados que siguen contando como versiones vivas del documento (ni retiradas ni rechazadas).
LIVE_STATUSES: frozenset[VersionStatus] = frozenset(
    {
        VersionStatus.CANDIDATE,
        VersionStatus.ACCEPTED,
        VersionStatus.OUTDATED,
        VersionStatus.SUPERSEDED,
    }
)


@dataclass(frozen=True, slots=True)
class RightsProfile:
    """Condiciones de uso de una fuente (03_DATA-MODEL §4, tabla `rights_statuses`).

    `review_status` empieza en `unknown` y **unknown se trata como restringido**: mientras nadie
    revisado la licencia, la aplicación no puede afirmar que el material se pueda reutilizar.
    """

    code: str
    review_status: RightsReview = RightsReview.UNKNOWN
    license_name: str | None = None
    license_url: str | None = None
    attribution: str | None = None
    commercial_reuse: bool = False
    sharing: bool = False
    notes: str | None = None

    @property
    def is_restricted(self) -> bool:
        """¿Se trata como restringido? Sí mientras no haya una revisión explícita."""
        return self.review_status is not RightsReview.REVIEWED

    @property
    def is_reusable(self) -> bool:
        """¿Se puede reutilizar (compartir) el contenido? Nunca por defecto."""
        return self.review_status is RightsReview.REVIEWED and self.sharing

    def can_show_publicly(self) -> bool:
        """Mostrar material al usuario es siempre posible; publicarlo o compartirlo, no."""
        return True

    def missing_attribution(self) -> tuple[str, ...]:
        """Qué falta para poder atribuir correctamente la fuente."""
        faltan = []
        if not self.attribution:
            faltan.append("attribution")
        if not self.license_url:
            faltan.append("license_url")
        return tuple(faltan)


@dataclass(frozen=True, slots=True)
class DocumentVersion:
    """Un fichero concreto que representa una obra, con su vigencia y sus derechos."""

    id: str
    logical_document_id: str
    artifact_id: str
    representation_id: str | None
    version_label: str | None
    status: VersionStatus = VersionStatus.CANDIDATE
    published_at: date | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    retrieved_at: datetime | None = None
    language: str | None = None
    supersedes_id: str | None = None
    rights_code: str | None = None
    official_url: str | None = None
    content_hash: str | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("Una versión necesita el artefacto del que sale")
        if self.supersedes_id == self.id:
            raise ValueError("Una versión no puede sustituirse a sí misma")
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and self.valid_to < self.valid_from
        ):
            raise ValueError("La vigencia no puede terminar antes de empezar")

    @property
    def is_live(self) -> bool:
        return self.status in LIVE_STATUSES

    @property
    def is_accepted(self) -> bool:
        return self.status is VersionStatus.ACCEPTED

    def can_accept(self) -> bool:
        """Solo se acepta una versión candidata o anticuada; nunca una retirada o rechazada."""
        return self.status in ACCEPTABLE_FROM

    def acceptance_requires_approval(self) -> bool:
        """Aceptar una versión es una promoción crítica: siempre la confirma una persona.

        Devuelve `True` siempre, y el método existe para que quede escrito en el dominio y no haya
        duda de que aceptar versiones no es algo que la aplicación haga sola (D006).
        """
        return True


@dataclass(frozen=True, slots=True)
class LogicalDocument:
    """La obra: título canónico, tipo documental y a quién pertenece."""

    id: str
    canonical_title: str
    document_type: str
    owner_scope: OwnerScope = OwnerScope.PRIVATE_USER
    authority_tier: str | None = None
    canonical_identifier: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.canonical_title.strip():
            raise ValueError("Un documento necesita título canónico")
        try:
            DocumentType(self.document_type)
        except ValueError as error:
            raise ValueError(f"«{self.document_type}» no es un tipo documental") from error

    @property
    def is_public(self) -> bool:
        return self.owner_scope is OwnerScope.PUBLIC


def active_version(versions: tuple[DocumentVersion, ...]) -> DocumentVersion | None:
    """La versión que manda: la aceptada más reciente; si no hay, la candidata más reciente.

    No se elige «la última que llegó»: una candidata sin aceptar es una **propuesta de cambio** y no
    puede presentarse como la versión buena del documento (03_DATA-MODEL §10).
    """
    aceptadas = [version for version in versions if version.is_accepted]
    if aceptadas:
        return max(aceptadas, key=lambda version: (version.approved_at or _epoch(), version.id))
    candidatas = [version for version in versions if version.status is VersionStatus.CANDIDATE]
    if candidatas:
        return max(candidatas, key=lambda version: (version.retrieved_at or _epoch(), version.id))
    return None


def can_promote_to_public(document: LogicalDocument, rights: RightsProfile | None) -> bool:
    """¿Se puede marcar un documento público? Solo si alguien lo dice y los derechos lo permiten.

    La clasificación automática nunca cambia `owner_scope`; y una fuente con derechos desconocidos
    queda restringida aunque el usuario quiera compartirla (09_SECURITY §8).
    """
    if rights is None:
        return False
    if not rights.is_reusable:
        return False
    return document.owner_scope is OwnerScope.PUBLIC


def supersedes_chain(
    versions: tuple[DocumentVersion, ...], start: str
) -> tuple[DocumentVersion, ...]:
    """Recorrido determinista de la cadena de sustituciones, empezando por una versión.

    Se detiene si hay un ciclo (que no debería existir) en lugar de colgarse: una cadena rota se
    informa, no se recorre en bucle.
    """
    por_id = {version.id: version for version in versions}
    cadena: list[DocumentVersion] = []
    vistos: set[str] = set()
    actual = por_id.get(start)
    while actual is not None and actual.id not in vistos:
        vistos.add(actual.id)
        cadena.append(actual)
        actual = por_id.get(actual.supersedes_id) if actual.supersedes_id else None
    return tuple(cadena)


def _epoch() -> datetime:
    from datetime import UTC

    return datetime(1970, 1, 1, tzinfo=UTC)


class SectionType(StrEnum):
    """Tipo de sección de un **documento**: cómo está organizada la obra (03_DATA-MODEL §4).

    No es lo mismo que el tipo de tramo del extractor (`SectionType` de `domain.extraction`): el
    extractor dice cómo ha partido el texto que leyó, y esto dice qué es esa parte dentro del
    documento. La traducción entre los dos vocabularios es `document_section_type`.
    """

    PAGE = "page"
    TITLE = "title"
    CHAPTER = "chapter"
    ARTICLE = "article"
    PROVISION = "provision"
    TECHNICAL = "technical"
    TOPIC = "topic"


#: Traducción explícita de lo que sabe distinguir el extractor al vocabulario del documento.
#: `chapter` y `provision` existen en el vocabulario pero **ningún extractor los produce todavía**:
#: se distinguirán cuando un documento real permita reconocerlos, no antes.
_EXTRACTOR_TO_DOCUMENT: dict[str, SectionType] = {
    "page": SectionType.PAGE,
    "title": SectionType.TITLE,
    "heading": SectionType.TITLE,
    "article": SectionType.ARTICLE,
    "paragraph": SectionType.TECHNICAL,
    "list": SectionType.TECHNICAL,
    "table": SectionType.TECHNICAL,
    "question_block": SectionType.TECHNICAL,
    "metadata": SectionType.TECHNICAL,
}


def document_section_type(extractor_type: str) -> SectionType:
    """Traduce el tipo de tramo del extractor al tipo de sección del documento.

    Lo que no se reconoce se trata como `technical`: una sección de texto de la que no sabemos más.
    Es conservador y **no inventa estructura**: un párrafo no es un artículo solo porque lo
    parezca: el extractor no lo ha comprobado.
    """
    return _EXTRACTOR_TO_DOCUMENT.get(extractor_type, SectionType.TECHNICAL)


@dataclass(frozen=True, slots=True)
class SectionDiff:
    """Qué le ha pasado a una sección entre dos versiones."""

    label: str
    kind: str
    left: str | None = None
    right: str | None = None


@dataclass(frozen=True, slots=True)
class VersionDiff:
    """Comparación determinista de dos versiones, sección a sección.

    No fusiona nada ni decide cuál es mejor: dice **qué cambió** y deja la decisión al usuario. Las
    secciones se emparejan por su etiqueta (título o nombre), que es lo único estable entre dos
    extracciones del mismo texto; lo que no se empareja se informa como añadido o quitado.
    """

    from_version_id: str
    to_version_id: str
    sections: tuple[SectionDiff, ...] = ()

    @property
    def added(self) -> int:
        return sum(1 for seccion in self.sections if seccion.kind == "added")

    @property
    def removed(self) -> int:
        return sum(1 for seccion in self.sections if seccion.kind == "removed")

    @property
    def changed(self) -> int:
        return sum(1 for seccion in self.sections if seccion.kind == "changed")

    @property
    def unchanged(self) -> int:
        return sum(1 for seccion in self.sections if seccion.kind == "unchanged")

    @property
    def has_changes(self) -> bool:
        return self.added + self.removed + self.changed > 0


def section_label(titulo: str | None, ordinal: int) -> str:
    """Cómo se llama una sección en una comparación: su título o «sección N».

    Es la **misma** regla que usa la biblioteca para citar y la que usa S11 para emparejar
    secciones entre versiones: si cada sitio inventara la suya, una sección «cambiada» en un listado
    no sería la misma que en el otro.
    """
    return titulo.strip() if titulo and titulo.strip() else f"sección {ordinal}"


def diff_versions(
    from_version_id: str,
    to_version_id: str,
    *,
    before: tuple[tuple[str | None, str], ...],
    after: tuple[tuple[str | None, str], ...],
) -> VersionDiff:
    """Compara dos versiones por sus secciones (título y texto), en orden determinista.

    `before` y `after` son `(título, texto)` en el orden en que aparecen las secciones. El resultado
    se ordena por el orden de la versión nueva y, al final, lo que solo estaba en la vieja.
    """
    por_titulo_antes = {
        section_label(titulo, indice): texto for indice, (titulo, texto) in enumerate(before, 1)
    }
    por_titulo_despues = {
        section_label(titulo, indice): texto for indice, (titulo, texto) in enumerate(after, 1)
    }

    diffs: list[SectionDiff] = []
    vistas: set[str] = set()
    for etiqueta, texto in por_titulo_despues.items():
        vistas.add(etiqueta)
        anterior = por_titulo_antes.get(etiqueta)
        if anterior is None:
            diffs.append(SectionDiff(label=etiqueta, kind="added", right=texto))
        elif anterior == texto:
            diffs.append(SectionDiff(label=etiqueta, kind="unchanged", left=anterior, right=texto))
        else:
            diffs.append(SectionDiff(label=etiqueta, kind="changed", left=anterior, right=texto))
    for etiqueta, texto in por_titulo_antes.items():
        if etiqueta not in vistas:
            diffs.append(SectionDiff(label=etiqueta, kind="removed", left=texto))
    return VersionDiff(
        from_version_id=from_version_id, to_version_id=to_version_id, sections=tuple(diffs)
    )
