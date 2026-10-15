"""El hueco de los pagos (§11 del objetivo vivo): la propuesta, escrita, y nada integrado.

**Qué hay aquí: una propuesta y una bandera apagada.** No hay ninguna pasarela integrada, ninguna
cuenta creada y ninguna petición a ningún proveedor. Lo que hay es la respuesta escrita a las tres
preguntas del §11 —qué pasarela, por qué, qué habría que contratar y qué datos personales pasarían a
un tercero— para que el día que se decida cobrar no haya que empezar por pensar esto.

**Las comisiones no se inventan.** El precio de una pasarela cambia sin avisar y este bloque no ha
podido leer las páginas de tarifas de los proveedores (se sirven con JavaScript y no devolvieron el
texto). Por eso cada cifra viaja marcada como **sin verificar en esta sesión**, con el enlace a la
página donde se comprueba: una cifra que va a un documento y no se ha medido se declara, no se
hereda.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CostLine:
    """Una línea de coste, con la marca de si se ha podido comprobar."""

    concept: str
    amount: str
    verified: bool


@dataclass(frozen=True, slots=True)
class GatewayOption:
    """Una pasarela que se ha considerado, con lo que costaría y lo que habría que contratar."""

    key: str
    name: str
    is_recommended: bool
    why: str
    what_to_contract: tuple[str, ...]
    costs: tuple[CostLine, ...]
    invoices_in_spain: str
    integration_effort: str
    personal_data_to_third_party: tuple[str, ...]
    price_page: str
    rejected_because: str = ""


@dataclass(frozen=True, slots=True)
class PlanSlot:
    """Un hueco de plan: sin precios, porque el precio lo decide el propietario."""

    key: str
    name: str
    detail: str
    price: str


#: La recomendación. Va primera y con su motivo: la pasarela que menos trabajo da a una persona sola
#: que no quiere firmar nada con un banco antes de saber si esto se va a usar.
GATEWAY_OPTIONS: tuple[GatewayOption, ...] = (
    GatewayOption(
        key="stripe",
        name="Stripe",
        is_recommended=True,
        why=(
            "Es la que menos cosas hay que contratar antes de cobrar: se abre la cuenta por "
            "internet, sin firmar nada con un banco, y con la misma cuenta vienen el cobro con "
            "tarjeta, la autenticación reforzada del banco (3-D Secure) y la factura. Se integra "
            "con un enlace de pago o con su biblioteca de servidor, así que el hueco de esta "
            "aplicación se rellena sin rehacer nada. Emite facturas conformes en España y calcula "
            "el IVA de cada país de la Unión si se activa su servicio de impuestos."
        ),
        what_to_contract=(
            "Una cuenta de Stripe (se abre por internet, con los datos del titular y una cuenta "
            "bancaria donde recibir).",
            "Si se cobra por suscripción, activar la facturación periódica (tiene coste aparte).",
            "Si se quiere que calcule el IVA de cada país, activar su servicio de impuestos.",
            "Certificado de titularidad de la cuenta bancaria, según lo pida la verificación.",
        ),
        costs=(
            CostLine(
                concept="Cobro con tarjeta europea (una compra)",
                amount="Comisión publicada por el proveedor; sin verificar en esta sesión",
                verified=False,
            ),
            CostLine(
                concept="Cobro con tarjeta de fuera del Espacio Económico Europeo",
                amount="Comisión más alta que la europea; sin verificar en esta sesión",
                verified=False,
            ),
            CostLine(
                concept="Cuota mensual",
                amount="No hay cuota por tener la cuenta abierta",
                verified=False,
            ),
            CostLine(
                concept="Facturación periódica (suscripciones)",
                amount="Porcentaje adicional sobre el importe; sin verificar en esta sesión",
                verified=False,
            ),
        ),
        invoices_in_spain="Sí: emite factura conforme y calcula el IVA si se contrata su servicio.",
        integration_effort=(
            "Baja: enlace de pago (sin código) o una llamada de servidor para crear la sesión de "
            "cobro y un aviso de vuelta para marcar la cuenta como de pago."
        ),
        personal_data_to_third_party=(
            "Dirección de correo.",
            "Nombre y dirección de facturación.",
            "Número de identificación fiscal, si se pide factura.",
            "Datos del medio de pago: **los recoge la pasarela**, nunca esta aplicación.",
            "Historial de cobros.",
        ),
        price_page="https://stripe.com/es/pricing",
    ),
    GatewayOption(
        key="paddle",
        name="Paddle",
        is_recommended=False,
        why=(
            "Es un revendedor: la venta la hace él, así que él es el responsable del IVA y de las "
            "facturas de cada país. Quita de encima el papeleo del impuesto, y eso vale dinero "
            "cuando se vende a varios países sin tener empresa para llevarlo."
        ),
        what_to_contract=(
            "Una cuenta de Paddle y su verificación como vendedor.",
            "Sus condiciones de revendedor: él pone el precio final al cliente.",
        ),
        costs=(
            CostLine(
                concept="Comisión por venta (incluye la gestión del impuesto)",
                amount="Sensiblemente más alta que la de una pasarela normal; sin verificar aquí",
                verified=False,
            ),
        ),
        invoices_in_spain="Sí, pero las emite él como vendedor, no el titular.",
        integration_effort="Media: su cobro se integra por su biblioteca o por enlaces de pago.",
        personal_data_to_third_party=(
            "Dirección de correo.",
            "Nombre y dirección de facturación.",
            "Datos del medio de pago.",
            "Historial de compras.",
        ),
        price_page="https://www.paddle.com/pricing",
        rejected_because=(
            "No se descarta: se propone como segunda opción si se prefiere no encargarse del IVA. "
            "Sale más caro por venta."
        ),
    ),
    GatewayOption(
        key="redsys",
        name="Redsys (TPV del banco)",
        is_recommended=False,
        why=(
            "Es la pasarela de la mayoría de los bancos españoles: la comisión negociada suele ser "
            "la más baja de las tres y el dinero llega a la cuenta del banco de siempre."
        ),
        what_to_contract=(
            "Un contrato de comercio electrónico con el banco (TPV virtual).",
            "La integración con su firma propia, que hay que hacer a mano.",
        ),
        costs=(
            CostLine(
                concept="Comisión por operación",
                amount="Se negocia con el banco; sin verificar en esta sesión",
                verified=False,
            ),
            CostLine(
                concept="Cuota de mantenimiento del TPV virtual",
                amount="Habitual en este tipo de contrato; sin verificar en esta sesión",
                verified=False,
            ),
        ),
        invoices_in_spain="Sí, pero la facturación al cliente la pone el titular.",
        integration_effort=(
            "Alta: firma propia, claves del banco y avisos de vuelta que hay que gestionar a mano."
        ),
        personal_data_to_third_party=(
            "Datos del medio de pago.",
            "Importe y referencia de la operación.",
        ),
        price_page="https://pagos.redsys.es/",
        rejected_because=(
            "No se descarta para más adelante: exige firmar con el banco antes de saber si hay "
            "alguien dispuesto a pagar. Es el camino razonable cuando el volumen ya existe."
        ),
    ),
)

#: Los huecos de plan. **Sin precios**: el precio lo decide el propietario, no este bloque.
PLANS: tuple[PlanSlot, ...] = (
    PlanSlot(
        key="free",
        name="Estudiar sin cuenta",
        detail="Lo de siempre: los temas, los tests y el progreso en este ordenador.",
        price="0",
    ),
    PlanSlot(
        key="account",
        name="Cuenta",
        detail="Lo mismo, con el progreso guardado y accesible desde otro sitio.",
        price="sin decidir",
    ),
    PlanSlot(
        key="paid",
        name="De pago",
        detail="El hueco existe y está apagado. No hay nada contratado ni cobrado.",
        price="sin decidir",
    ),
)

#: Lo que el §11 pide decir cuando alguien pregunte por los pagos, en una línea.
PAYMENTS_STATUS = (
    "Solo el hueco y la bandera. No hay ninguna pasarela integrada, ninguna cuenta creada y ningún "
    "cobro posible: con la bandera apagada, las rutas de pago contestan que no está disponible."
)


__all__ = [
    "GATEWAY_OPTIONS",
    "PAYMENTS_STATUS",
    "PLANS",
    "CostLine",
    "GatewayOption",
    "PlanSlot",
]
