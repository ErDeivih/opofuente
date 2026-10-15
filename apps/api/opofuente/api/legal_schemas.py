"""Esquemas de las páginas legales, el inventario de datos y el consentimiento (§9).

Los textos viajan en **Markdown** desde el servidor y la pantalla los pinta: una sola redacción, la
del servidor, así que no puede haber una página que diga una cosa y una prueba que compruebe otra.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from opofuente.domain.legal import CookieDeclaration, DataUse, LegalDocument, NegativeClaim

#: #: El aviso que se sirve con los documentos mientras falten los datos del titular. Va en la
#: respuesta
#: y no solo dentro del texto para que la pantalla pueda enseñarlo **arriba**, donde se ve.
PENDING_OWNER_NOTICE = (
    "Faltan datos del titular (nombre, NIF y contacto). Están marcados en el texto con "
    "[PENDIENTE: …] y hay que rellenarlos antes de publicar esto en internet."
)


class LegalDocumentSchema(BaseModel):
    """Un documento legal: su nombre corto, su título y su texto."""

    key: str
    title: str
    summary: str
    body_markdown: str


class LegalBundleSchema(BaseModel):
    """Los tres documentos, la fecha del texto vigente y lo que falta por rellenar."""

    text_version: int
    updated_on: str
    documents: list[LegalDocumentSchema]
    owner_fields_pending: list[str]
    pending_owner_notice: str
    notice: str


class DataUseSchema(BaseModel):
    """Una fila del inventario: qué, para qué, dónde y cuánto tiempo, con su base jurídica."""

    what: str
    why: str
    where: str
    retention: str
    lawful_basis: str
    needs_account: bool
    needs_consent: str | None


class NegativeClaimSchema(BaseModel):
    """Lo que **no** se recoge, declarado para poder comprobarlo."""

    claim: str


class DataInventorySchema(BaseModel):
    """El inventario completo: lo que se recoge y lo que no."""

    uses: list[DataUseSchema]
    not_collected: list[NegativeClaimSchema]
    notice: str


class CookieSchema(BaseModel):
    """Una cookie, con su finalidad, su duración y si es necesaria."""

    name: str
    purpose: str
    essential: bool
    duration: str
    set_by: str
    purpose_key: str


class CookiesSchema(BaseModel):
    """Las cookies de esta aplicación y el texto vigente que se acepta."""

    policy_version: int
    updated_on: str
    cookies: list[CookieSchema]
    essential: list[str]
    purposes: list[str]
    notice: str


class ConsentDecisionSchema(BaseModel):
    """Lo que se decide. Los dos fines son independientes y los dos nacen en falso.

    Aceptar y rechazar usan **el mismo cuerpo**: la diferencia es el valor de dos booleanos, y por
    eso
    no hay ninguna forma de que un camino sea más fácil que el otro en el contrato. `necesarias` no
    se
    pide: no se puede rechazar lo que hace falta para que la aplicación funcione.
    """

    analytics: bool = False
    preferences: bool = False


class ConsentStateSchema(BaseModel):
    """Lo que se ha decidido, tal como queda guardado."""

    policy_version: int
    decided_at: datetime
    necessary: bool
    analytics: bool
    preferences: bool


class ConsentSummarySchema(BaseModel):
    """Cuántas decisiones se han tomado, contadas por desenlace y **sin ningún sujeto**."""

    total: int
    with_analytics: int
    with_preferences: int
    policy_version: int
    since: datetime | None = Field(
        default=None, description="Cuándo se tomó la primera decisión que sigue guardada."
    )


def document(view: LegalDocument) -> LegalDocumentSchema:
    return LegalDocumentSchema(
        key=view.key,
        title=view.title,
        summary=view.summary,
        body_markdown=view.body_markdown,
    )


def data_use(view: DataUse) -> DataUseSchema:
    return DataUseSchema(
        what=view.what,
        why=view.why,
        where=view.where,
        retention=view.retention,
        lawful_basis=view.lawful_basis,
        needs_account=view.needs_account,
        needs_consent=view.needs_consent,
    )


def negative_claim(view: NegativeClaim) -> NegativeClaimSchema:
    return NegativeClaimSchema(claim=view.claim)


def cookie(view: CookieDeclaration) -> CookieSchema:
    return CookieSchema(
        name=view.name,
        purpose=view.purpose,
        essential=view.essential,
        duration=view.duration,
        set_by=view.set_by,
        purpose_key=view.purpose_key,
    )


__all__ = [
    "PENDING_OWNER_NOTICE",
    "ConsentDecisionSchema",
    "ConsentStateSchema",
    "ConsentSummarySchema",
    "CookieSchema",
    "CookiesSchema",
    "DataInventorySchema",
    "DataUseSchema",
    "LegalBundleSchema",
    "LegalDocumentSchema",
    "NegativeClaimSchema",
    "cookie",
    "data_use",
    "document",
    "negative_claim",
]
