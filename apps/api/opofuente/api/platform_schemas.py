"""Los esquemas de la analítica propia y del hueco de pagos (§10 y §11).

Los dos tienen la misma forma por dentro —una lista de lo que hay y un aviso de lo que no— y por eso
viven juntos: son las dos partes del bloque que **no** contratan nada.
"""

from __future__ import annotations

from pydantic import BaseModel

from opofuente.application.account_models import CountByLabel
from opofuente.domain.payments import CostLine, GatewayOption, PlanSlot


class AnalyticsEventSchema(BaseModel):
    """El suceso que se cuenta. Solo dos campos, y los dos de una lista cerrada."""

    name: str
    label: str


class AnalyticsCountSchema(BaseModel):
    """Un renglón del resumen: el tipo, la etiqueta y cuántas veces."""

    name: str
    label: str
    total: int


class AnalyticsDaySchema(BaseModel):
    """Cuántos sucesos hubo un día."""

    day: str
    total: int


class AnalyticsSummarySchema(BaseModel):
    """Lo contado, agrupado por etiqueta y por día, con el plazo declarado."""

    enabled: bool
    requires_consent: bool
    retention_days: int
    counts: list[AnalyticsCountSchema]
    days: list[AnalyticsDaySchema]
    notice: str


class AnalyticsRecordedSchema(BaseModel):
    """Acuse de un suceso contado. No devuelve lo contado: no hay nada que devolver."""

    recorded: bool
    day: str


class PaymentPlanSchema(BaseModel):
    """Un hueco de plan. Sin precio decidido: eso no lo decide este bloque."""

    key: str
    name: str
    detail: str
    price: str


class PaymentCostSchema(BaseModel):
    """Una línea de coste, con la marca de si se ha podido comprobar."""

    concept: str
    amount: str
    verified: bool


class PaymentGatewaySchema(BaseModel):
    """Una pasarela considerada: por qué, qué contratar, qué costaría y qué datos saldrían."""

    key: str
    name: str
    recommended: bool
    why: str
    what_to_contract: list[str]
    costs: list[PaymentCostSchema]
    invoices_in_spain: str
    integration_effort: str
    personal_data_to_third_party: list[str]
    price_page: str
    rejected_because: str


class PaymentsSchema(BaseModel):
    """El estado de los pagos: apagados, con la propuesta escrita y nada contratado."""

    enabled: bool
    provider: str
    status: str
    plans: list[PaymentPlanSchema]
    gateways: list[PaymentGatewaySchema]
    notice: str


class AccountsPolicySchema(BaseModel):
    """Lo que la interfaz tiene que saber de las cuentas para ofrecer o no el acceso."""

    enabled: bool
    #: #: **La regla que manda**, dicha por el servidor: sin cuenta se sigue pudiendo estudiar. Se
    #: declara
    #: aquí para que ninguna pantalla tenga que deducirlo del código.
    anonymous_study: bool
    session_cookie_name: str
    session_days: int
    delivery_channel: str


class LegalPolicySchema(BaseModel):
    """Lo que la interfaz necesita para pedir el consentimiento."""

    enabled: bool
    policy_version: int
    text_version: int
    updated_on: str
    purposes: list[str]
    essential: list[str]
    owner_fields_pending: bool


class AnalyticsPolicySchema(BaseModel):
    """Si hay analítica y de qué depende."""

    enabled: bool
    requires_consent: bool
    retention_days: int


class PlatformPolicySchema(BaseModel):
    """**Una sola llamada** para saber qué está encendido en esta instalación.

    Existe porque la web se construye una vez y se sirve en varias configuraciones: si las banderas
    se hornearan en el paquete, habría que construir dos veces la misma aplicación para probar la
    versión con cuentas y la versión sin ellas, y las dos acabarían divergiendo. Se pregunta al
    servidor en cada arranque, y lo que diga el servidor es lo que hay.

    Es pública a propósito: dice qué funciones están encendidas, no nada de nadie.
    """

    accounts: AccountsPolicySchema
    legal: LegalPolicySchema
    analytics: AnalyticsPolicySchema
    payments: bool


def count(view: CountByLabel) -> AnalyticsCountSchema:
    return AnalyticsCountSchema(name=view.name, label=view.label, total=view.total)


def cost(view: CostLine) -> PaymentCostSchema:
    return PaymentCostSchema(concept=view.concept, amount=view.amount, verified=view.verified)


def gateway(view: GatewayOption) -> PaymentGatewaySchema:
    return PaymentGatewaySchema(
        key=view.key,
        name=view.name,
        recommended=view.is_recommended,
        why=view.why,
        what_to_contract=list(view.what_to_contract),
        costs=[cost(linea) for linea in view.costs],
        invoices_in_spain=view.invoices_in_spain,
        integration_effort=view.integration_effort,
        personal_data_to_third_party=list(view.personal_data_to_third_party),
        price_page=view.price_page,
        rejected_because=view.rejected_because,
    )


def plan(view: PlanSlot) -> PaymentPlanSchema:
    return PaymentPlanSchema(key=view.key, name=view.name, detail=view.detail, price=view.price)


__all__ = [
    "AccountsPolicySchema",
    "AnalyticsCountSchema",
    "AnalyticsDaySchema",
    "AnalyticsEventSchema",
    "AnalyticsPolicySchema",
    "AnalyticsRecordedSchema",
    "AnalyticsSummarySchema",
    "LegalPolicySchema",
    "PaymentCostSchema",
    "PaymentGatewaySchema",
    "PaymentPlanSchema",
    "PaymentsSchema",
    "PlatformPolicySchema",
    "cost",
    "count",
    "gateway",
    "plan",
]
