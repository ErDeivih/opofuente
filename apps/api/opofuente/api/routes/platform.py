"""Las rutas de la política de la instalación, la analítica propia y el hueco de pagos.

**Ninguna de las tres contrata nada.** La política dice qué está encendido; la analítica es un
contador en la propia base, sin servicio de fuera y sin identificadores; los pagos son una propuesta
escrita y una bandera apagada.

Van en el mismo módulo porque son las tres caras de la misma decisión —lo que **no** se contrata— y
porque separarlas daría tres ficheros de veinte líneas que se leen peor que uno de ciento cincuenta.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request, status

from opofuente.api.deps import (
    AccountsServiceDep,
    AnalyticsServiceDep,
    AppSettingsDep,
    LegalServiceDep,
)
from opofuente.api.error_responses import BASE_ERRORS, READ_WITH_QUERY_ERRORS, WRITE_ERRORS
from opofuente.api.platform_schemas import (
    AccountsPolicySchema,
    AnalyticsDaySchema,
    AnalyticsEventSchema,
    AnalyticsPolicySchema,
    AnalyticsRecordedSchema,
    AnalyticsSummarySchema,
    LegalPolicySchema,
    PaymentsSchema,
    PlatformPolicySchema,
    count,
    gateway,
    plan,
)
from opofuente.config import Settings
from opofuente.domain.accounts import CONSENT_COOKIE_NAME
from opofuente.domain.payments import GATEWAY_OPTIONS, PAYMENTS_STATUS, PLANS

router = APIRouter()


@router.get(
    "/platform/policy",
    response_model=PlatformPolicySchema,
    responses=BASE_ERRORS,
    summary="Qué funciones están encendidas en esta instalación",
    tags=["sistema"],
)
def platform_policy(
    settings: AppSettingsDep,
    accounts: AccountsServiceDep,
    legal: LegalServiceDep,
    analytics: AnalyticsServiceDep,
) -> PlatformPolicySchema:
    """La única llamada que necesita la interfaz para saber con qué configuración habla.

    Es pública: dice qué está encendido, no nada de nadie. Existe porque la web se construye una vez
    y se sirve en varias configuraciones; con las banderas dentro del paquete habría que construir
    dos
    veces la misma aplicación para probar la versión con cuentas y la versión sin ellas, y las dos
    acabarían divergiendo.
    """
    politica = legal.policy()
    return PlatformPolicySchema(
        accounts=AccountsPolicySchema(
            enabled=accounts.enabled,
            anonymous_study=True,
            session_cookie_name=accounts.session_cookie.name,
            session_days=accounts.session_cookie.max_age // 86400,
            delivery_channel=accounts.delivery_channel,
        ),
        legal=LegalPolicySchema(
            enabled=legal.enabled,
            policy_version=politica.policy_version,
            text_version=politica.text_version,
            updated_on=politica.text_updated_on,
            purposes=list(politica.purposes),
            essential=list(politica.essential),
            owner_fields_pending=bool(legal.owner_fields_pending),
        ),
        analytics=AnalyticsPolicySchema(
            enabled=analytics.enabled,
            requires_consent=analytics.requires_consent,
            retention_days=analytics.retention_days,
        ),
        payments=settings.payments_enabled,
    )


@router.post(
    "/analytics/events",
    response_model=AnalyticsRecordedSchema,
    status_code=status.HTTP_202_ACCEPTED,
    responses=WRITE_ERRORS,
    summary="Contar una pantalla vista o una acción (necesita consentimiento)",
    tags=["analítica"],
)
def record_event(
    payload: AnalyticsEventSchema,
    request: Request,
    analytics: AnalyticsServiceDep,
    legal: LegalServiceDep,
) -> AnalyticsRecordedSchema:
    """Cuenta un suceso **si** está encendida la analítica y **si** hay consentimiento.

    El permiso se lee aquí, de la cookie, y no se acepta del cuerpo: si el permiso viajara en la
    petición, bastaría con mandarlo para contar lo que no se puede contar.
    """
    consentimiento = legal.state(request.cookies.get(CONSENT_COOKIE_NAME))
    evento = analytics.record(name=payload.name, label=payload.label, consent=consentimiento)
    return AnalyticsRecordedSchema(recorded=True, day=evento.day)


@router.get(
    "/analytics/summary",
    response_model=AnalyticsSummarySchema,
    responses=READ_WITH_QUERY_ERRORS,
    summary="Lo contado, agrupado por etiqueta y por día",
    tags=["analítica"],
)
def analytics_summary(
    analytics: AnalyticsServiceDep, days: int = Query(default=30, ge=0, le=3650)
) -> AnalyticsSummarySchema:
    """El resumen va agregado: no se pueden pedir los sucesos uno a uno, porque no tienen sujeto."""
    return AnalyticsSummarySchema(
        enabled=analytics.enabled,
        requires_consent=analytics.requires_consent,
        retention_days=analytics.retention_days,
        counts=[count(renglon) for renglon in analytics.summary(days=days)],
        days=[
            AnalyticsDaySchema(day=dia, total=total)
            for dia, total in analytics.totals_by_day(days=days)
        ],
        notice=(
            "Son contadores: cuántas veces se ha abierto cada pantalla y cuántas veces se ha "
            "pulsado cada acción, por día. No hay cuenta, ni sesión, ni dirección, ni nada que "
            "permita unir dos sucesos de la misma persona."
        ),
    )


@router.get(
    "/payments/plans",
    response_model=PaymentsSchema,
    responses=BASE_ERRORS,
    summary="El hueco de pagos: qué hay contratado (nada) y qué habría que contratar",
    tags=["pagos"],
)
def payment_plans(settings: AppSettingsDep) -> PaymentsSchema:
    """**No cobra nada y no puede cobrar nada.**

    Con la bandera apagada —que es como nace— la respuesta dice que no está disponible y, aun así,
    trae la propuesta escrita: qué pasarela, por qué, qué habría que contratar, qué costaría y qué
    datos personales pasarían a un tercero. Es la respuesta al §11 sin contratar nada.
    """
    return PaymentsSchema(
        enabled=settings.payments_enabled,
        provider=_provider(settings),
        status=PAYMENTS_STATUS,
        plans=[plan(hueco) for hueco in PLANS],
        gateways=[gateway(opcion) for opcion in GATEWAY_OPTIONS],
        notice=(
            "No hay ninguna pasarela integrada, ninguna cuenta creada y ningún cobro posible. Las "
            "comisiones que aparecen aquí son las publicadas por cada proveedor y **no se han "
            "podido comprobar en esta sesión** (sus páginas de precios se sirven con JavaScript): "
            "compruébalas en su página antes de contratar."
        ),
    )


def _provider(settings: Settings) -> str:
    """Qué pasarela hay puesta.

    Con la bandera apagada, ninguna; encendida, sigue sin haber ninguna: encender la bandera no
    integra nada, solo deja de contestar que no está disponible.
    """
    if not settings.payments_enabled:
        return "ninguna (bandera apagada)"
    return "sin integrar"


__all__ = ["router"]
