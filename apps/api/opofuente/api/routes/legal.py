"""Las rutas de los textos legales, el inventario de datos y el consentimiento (§9).

**La decisión sobre las cookies se toma en el servidor y se guarda en una cookie propia.** El
consentimiento se lee de ahí en cada petición que lo necesita —hoy, la analítica—, así que un
«acepto» que no llegue al servidor no enciende nada. Y la cookie se pone **igual** al aceptar y al
rechazar: es la única forma de que rechazar sea tan fácil como aceptar y de que la decisión se
recuerde sin volver a preguntar en cada pantalla.

**La cookie del consentimiento no lleva ningún identificador**: dice qué se ha aceptado, con qué
texto
y cuándo. No dice quién. Por eso no es un dato personal y por eso la constancia que se guarda en la
base puede ser agregada.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from opofuente.api.deps import LegalServiceDep
from opofuente.api.error_responses import BASE_ERRORS, RESOURCE_ERRORS, WRITE_ERRORS
from opofuente.api.legal_schemas import (
    PENDING_OWNER_NOTICE,
    ConsentDecisionSchema,
    ConsentStateSchema,
    ConsentSummarySchema,
    CookiesSchema,
    DataInventorySchema,
    LegalBundleSchema,
    LegalDocumentSchema,
    cookie,
    data_use,
    document,
    negative_claim,
)
from opofuente.domain.accounts import CONSENT_COOKIE_NAME, CONSENT_VALIDITY


def require_legal(service: LegalServiceDep) -> None:
    """La bandera del §9, comprobada **una vez** para todas las rutas de este router.

    Va como dependencia del router y no repetida en cada función a propósito: siete comprobaciones
    copiadas son siete sitios donde olvidarse de una, y la que se olvide será justo la que sirva
    algo con la bandera apagada.
    """
    service.require_enabled()


router = APIRouter(dependencies=[Depends(require_legal)])

#: La cookie del consentimiento **no es `HttpOnly`** a propósito: el servidor tiene que poder leerla
#: para no contar nada sin permiso, y la propia página la lee para saber si puede poner la cookie de
#: preferencias. No lleva ningún identificador, así que poder leerla no expone nada.
CONSENT_COOKIE_PATH = "/"


def _consent_raw(request: Request) -> str | None:
    return request.cookies.get(CONSENT_COOKIE_NAME)


def _put_consent_cookie(response: Response, value: str) -> None:
    response.set_cookie(
        key=CONSENT_COOKIE_NAME,
        value=value,
        max_age=int(CONSENT_VALIDITY.total_seconds()),
        httponly=False,
        secure=False,
        samesite="lax",
        path=CONSENT_COOKIE_PATH,
    )


@router.get(
    "/legal/documents",
    response_model=LegalBundleSchema,
    responses=BASE_ERRORS,
    summary="Los tres textos legales, con lo que falta por rellenar",
    tags=["legal"],
)
def documents(service: LegalServiceDep) -> LegalBundleSchema:
    """Aviso legal, privacidad y cookies, tal como se leen en la aplicación."""
    return LegalBundleSchema(
        text_version=service.text_version,
        updated_on=service.text_updated_on,
        documents=[document(vista) for vista in service.documents],
        owner_fields_pending=list(service.owner_fields_pending),
        pending_owner_notice=PENDING_OWNER_NOTICE,
        notice=(
            "Estos textos son los que usa la aplicación para decir qué hace con los datos. La "
            "aplicación no es una academia oficial ni tiene relación con ninguna administración."
        ),
    )


@router.get(
    "/legal/documents/{key}",
    response_model=LegalDocumentSchema,
    responses=RESOURCE_ERRORS,
    summary="Un texto legal por su nombre corto",
    tags=["legal"],
)
def one_document(key: str, service: LegalServiceDep) -> LegalDocumentSchema:
    for vista in service.documents:
        if vista.key == key:
            return document(vista)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No hay ningún texto legal con ese nombre.",
    )


@router.get(
    "/legal/data-inventory",
    response_model=DataInventorySchema,
    responses=BASE_ERRORS,
    summary="Qué datos se recogen, para qué, dónde y cuánto tiempo",
    tags=["legal"],
)
def data_inventory(service: LegalServiceDep) -> DataInventorySchema:
    """El inventario **verificable**: la prueba de integración lo cruza contra el esquema real.

    Cada fila dice de qué tabla habla, y la prueba comprueba que esa tabla y esa columna existen.
    También comprueba lo que el inventario dice que **no** se recoge: si alguien añadiera mañana una
    columna de dirección de red, la prueba fallaría y este texto dejaría de poder mentir.
    """
    return DataInventorySchema(
        uses=[data_use(uso) for uso in service.inventory],
        not_collected=[negative_claim(claim) for claim in service.negative_claims],
        notice=(
            "Sin cuenta no se recoge ningún dato tuyo: estudiar sin cuenta no manda nada a ningún "
            "sitio. Con cuenta, se recoge lo que dice esta tabla, ni más ni menos; cada fila se "
            "comprueba contra la base de datos de la aplicación."
        ),
    )


@router.get(
    "/legal/cookies",
    response_model=CookiesSchema,
    responses=BASE_ERRORS,
    summary="Qué cookies se ponen y cuáles son necesarias",
    tags=["legal"],
)
def cookies(service: LegalServiceDep) -> CookiesSchema:
    politica = service.policy()
    return CookiesSchema(
        policy_version=politica.policy_version,
        updated_on=service.text_updated_on,
        cookies=[cookie(una) for una in service.cookies],
        essential=list(politica.essential),
        purposes=list(politica.purposes),
        notice=(
            "Antes de que decidas no se pone ninguna cookie que no sea necesaria. Aceptar y "
            "rechazar cuestan lo mismo: se puede rechazar sin explicar nada y se sigue estudiando "
            "igual."
        ),
    )


@router.get(
    "/legal/consent",
    response_model=ConsentStateSchema | None,
    responses=BASE_ERRORS,
    summary="Qué he decidido sobre las cookies (o nada, si no lo he decidido)",
    tags=["legal"],
)
def read_consent(service: LegalServiceDep, request: Request) -> ConsentStateSchema | None:
    """`null` significa **sin decidir**, que no es lo mismo que haber rechazado."""
    estado = service.state(_consent_raw(request))
    if estado is None:
        return None
    return ConsentStateSchema(
        policy_version=estado.policy_version,
        decided_at=estado.decided_at,
        necessary=True,
        analytics=estado.analytics,
        preferences=estado.preferences,
    )


@router.post(
    "/legal/consent",
    response_model=ConsentStateSchema,
    responses=WRITE_ERRORS,
    summary="Decidir sobre las cookies (aceptar o rechazar, con el mismo cuerpo)",
    tags=["legal"],
)
def decide_consent(
    payload: ConsentDecisionSchema,
    request: Request,
    response: Response,
    service: LegalServiceDep,
) -> ConsentStateSchema:
    """Guarda la decisión en una cookie propia y deja constancia agregada, sin sujeto.

    El cuerpo es el mismo para aceptar y para rechazar: dos booleanos. No hay ninguna ruta «fácil»
    para aceptar ni ningún camino que exija explicar un rechazo.
    """
    estado = service.decide(
        analytics=payload.analytics,
        preferences=payload.preferences,
        raw_cookie=_consent_raw(request),
    )
    _put_consent_cookie(response, service.render(estado))
    return ConsentStateSchema(
        policy_version=estado.policy_version,
        decided_at=estado.decided_at,
        necessary=True,
        analytics=estado.analytics,
        preferences=estado.preferences,
    )


@router.get(
    "/legal/consent/summary",
    response_model=ConsentSummarySchema,
    responses=BASE_ERRORS,
    summary="Cuántas decisiones se han tomado, sin decir quién",
    tags=["legal"],
)
def consent_summary(service: LegalServiceDep) -> ConsentSummarySchema:
    """La constancia agregada: demuestra que se preguntó, sin un registro de nadie."""
    resumen = service.summary()
    return ConsentSummarySchema(
        total=resumen.total,
        with_analytics=resumen.with_analytics,
        with_preferences=resumen.with_preferences,
        policy_version=resumen.policy_version,
        since=resumen.since,
    )


__all__ = ["router"]
