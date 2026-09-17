"""Servicio de la biblioteca (S05): promocionar, versionar, citar y organizar.

Es fino a propósito: no decide reglas nuevas, sino que ordena lo que ya está decidido en el
dominio y
en el repositorio, y **no deja pasar** lo que no se puede hacer sin decir por qué. Las tres
reglas que
sí vive aquí:

- **aceptar una versión** es una promoción crítica y lo confirma una persona (D006): el servicio no
  acepta nada por su cuenta, ni al promocionar ni al sustituir;
- **compartir** exige que los derechos estén revisados y permitan compartir, y que alguien haya
puesto
  el documento en público: una fuente con derechos desconocidos se queda restringida;
- **una cita tiene que poder abrirse**: si la evidencia no existe o no tiene sección, se
devuelve nada
  en lugar de una cita a medias.
"""

from __future__ import annotations

from datetime import datetime

from opofuente.application.library_models import (
    CollectionView,
    DocumentDetail,
    DocumentPage,
    EvidenceView,
    PromotionOutcome,
    SectionView,
    VersionView,
)
from opofuente.application.ports import Clock
from opofuente.domain.documents import (
    LogicalDocument,
    OwnerScope,
    RightsProfile,
    RightsReview,
    SectionType,
    VersionStatus,
    can_promote_to_public,
)
from opofuente.infrastructure.classification_repository import SqlAlchemyClassificationRepository
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository


class LibraryService:
    """Cara de la biblioteca para la API: nada de reglas nuevas, sí de comprobaciones."""

    def __init__(
        self,
        documents: SqlAlchemyDocumentRepository,
        classifications: SqlAlchemyClassificationRepository,
        clock: Clock,
    ) -> None:
        self._documents = documents
        self._classifications = classifications
        self._clock = clock

    # ------------------------------------------------------------------ promoción

    def promote(
        self,
        artifact_id: str,
        *,
        document_id: str | None = None,
        title: str | None = None,
        document_type: str = "unknown",
        authority_tier: str | None = None,
        version_label: str | None = None,
        rights_code: str | None = None,
        official_url: str | None = None,
        owner_scope: str = "private_user",
    ) -> PromotionOutcome:
        """Promociona un artefacto a documento (o le añade una versión). Nunca lo hace público."""
        if owner_scope == "public":
            # Promocionar no es compartir: poner algo en público exige revisar derechos y pedirlo
            # aparte, así que aquí no se admite.
            return PromotionOutcome(
                None,
                None,
                False,
                False,
                reason="Promocionar no hace público un documento: eso se decide aparte",
            )
        return self._documents.promote_artifact(
            artifact_id,
            now=self._clock.now(),
            document_id=document_id,
            title=title,
            document_type=document_type,
            owner_scope=owner_scope,
            authority_tier=authority_tier,
            version_label=version_label,
            rights_code=rights_code,
            official_url=official_url,
        )

    def accept_version(self, version_id: str, *, actor: str = "local") -> PromotionOutcome:
        """Acepta una versión: promoción crítica, confirmada por una persona y auditada."""
        return self._documents.accept_version(version_id, now=self._clock.now(), actor=actor)

    def mark_supersedes(
        self, version_id: str, *, superseded_id: str, actor: str = "local"
    ) -> PromotionOutcome:
        """Confirma que una versión sustituye a otra. La antigua no se borra."""
        return self._documents.mark_supersedes(
            version_id, superseded_id=superseded_id, now=self._clock.now(), actor=actor
        )

    def add_mapping(
        self,
        version_id: str,
        *,
        curriculum_node_id: str,
        coverage_type: str = "partial",
        actor: str = "local",
    ) -> str | None:
        """Asigna una versión de documento a un nodo del programa (contrato §7).

        Devuelve el id del mapeo, o `None` si la versión o el nodo no existen: la API responde 404
        y no escribe nada. El mapeo nace **aceptado** porque lo pide una persona desde la interfaz,
        y queda auditado como cualquier otra decisión.
        """
        return self._documents.add_mapping(
            version_id=version_id,
            curriculum_node_id=curriculum_node_id,
            coverage_type=coverage_type,
            status="accepted",
            actor=actor,
            now=self._clock.now(),
        )

    # ------------------------------------------------------------------ consulta

    def documents(
        self,
        *,
        document_type: str | None = None,
        owner_scope: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> DocumentPage:
        return self._documents.list_documents(
            document_type=document_type, owner_scope=owner_scope, limit=limit, offset=offset
        )

    def document(self, document_id: str) -> DocumentDetail | None:
        return self._documents.get_document(document_id)

    def version(self, document_id: str, version_id: str) -> VersionView | None:
        detalle = self._documents.get_document(document_id)
        if detalle is None:
            return None
        return next(
            (version for version in detalle.versions if version.id == version_id),
            None,
        )

    def sections(self, version_id: str) -> tuple[SectionView, ...]:
        return self._documents.list_sections(version_id)

    def evidence(self, version_id: str) -> tuple[EvidenceView, ...]:
        return self._documents.list_evidence(version_id)

    def citation(self, evidence_id: str) -> EvidenceView | None:
        """La evidencia que sostiene una cita. Sin sección no hay cita que abrir."""
        evidencia = self._documents.get_evidence(evidence_id)
        if evidencia is None or evidencia.section_id is None:
            return None
        return evidencia

    def can_share(self, document_id: str) -> bool:
        """¿Se puede compartir? Solo con derechos revisados y decisión explícita."""
        detalle = self._documents.get_document(document_id)
        if detalle is None:
            return False
        derechos = (
            detalle.document.active_version.rights if detalle.document.active_version else None
        )
        if derechos is None:
            return False
        perfil = RightsProfile(
            code=derechos.code,
            review_status=RightsReview(derechos.review_status),
            sharing=derechos.sharing,
        )
        documento = LogicalDocument(
            id=detalle.document.id,
            canonical_title=detalle.document.canonical_title,
            document_type=detalle.document.document_type,
            owner_scope=OwnerScope(detalle.document.owner_scope),
        )
        return can_promote_to_public(documento, perfil)

    def history(self, document_id: str) -> tuple[VersionView, ...]:
        """Cadena de sustituciones desde la versión activa hacia atrás: lo viejo no se pierde."""
        detalle = self._documents.get_document(document_id)
        if detalle is None or detalle.document.active_version is None:
            return ()
        por_id = {version.id: version for version in detalle.versions}
        activa = detalle.document.active_version
        cadena: list[VersionView] = []
        vistas: set[str] = set()
        actual: VersionView | None = activa
        while actual is not None and actual.id not in vistas:
            vistas.add(actual.id)
            cadena.append(actual)
            actual = por_id.get(actual.supersedes_id) if actual.supersedes_id else None
        return tuple(cadena)

    # ------------------------------------------------------------------ colecciones

    def collections(self) -> tuple[CollectionView, ...]:
        return self._documents.list_collections()

    def create_collection(self, name: str, *, description: str | None = None) -> CollectionView:
        return self._documents.create_collection(
            name, description=description, now=self._clock.now()
        )

    def add_to_collection(
        self, collection_id: str, *, subject_type: str, subject_id: str
    ) -> CollectionView | None:
        return self._documents.add_to_collection(
            collection_id,
            subject_type=subject_type,
            subject_id=subject_id,
            now=self._clock.now(),
        )


#: Estados que la API puede aceptar como destino de una versión (los demás no se piden desde fuera).
ACCEPTABLE_STATUSES: frozenset[VersionStatus] = frozenset(
    {VersionStatus.CANDIDATE, VersionStatus.OUTDATED}
)

#: Tipos de sección que se sirven (el vocabulario del documento, no el del extractor).
SECTION_TYPES: tuple[str, ...] = tuple(tipo.value for tipo in SectionType)


def current_time() -> datetime:
    """Reloj del sistema, para quien no quiera inyectarlo (los servicios sí lo inyectan)."""
    from opofuente.infrastructure.clock import SystemClock

    return SystemClock().now()
