"""La analítica propia (§10 del objetivo vivo): el vocabulario cerrado y nada más.

**La decisión, dicha en la primera línea del módulo donde se pueda leer**: sí se monta una
analítica,y es **propia**, **agregada** y **sin identificadores**. El §10 permite no montar ninguna;
se monta
porque la pregunta «¿qué pantallas se usan de verdad?» tiene respuesta con veinte líneas de código y
sin ella se decide a ojo. Y se monta así, con un **vocabulario cerrado de etiquetas**, por el motivo
que de verdad importa: **el esquema no puede guardar datos personales aunque alguien se equivoque**.
Una etiqueta que no está en la lista se rechaza; no hay ningún campo de texto libre, ni cuenta, ni
sesión, ni navegador, ni dirección de red. No hay nada que anonimizar porque nunca se guarda.

**Lo que no se hace.** No hay ningún servicio de fuera: ni una cookie de terceros, ni un píxel, ni
una llamada a un dominio ajeno. Y no se cuenta nada si quien navega no ha aceptado la analítica: el
servidor lo comprueba en cada petición y contesta que no, en vez de fiarse de la pantalla.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Los dos tipos de suceso que el §10 pide contar: qué pantalla se abre y qué acción se pulsa.
PAGE_VIEW = "page_view"
ACTION = "action"

EVENT_NAMES: frozenset[str] = frozenset({PAGE_VIEW, ACTION})

#: Las pantallas que se pueden contar. Son **nombres de pantalla**, no direcciones: una dirección
# # con#: un identificador dentro (`/temario/IV.7`) sería un dato sobre lo que alguien estudia, y
# eso sí es
#: personal. El nombre de la pantalla no dice qué tema.
PAGE_LABELS: frozenset[str] = frozenset(
    {
        "inicio",
        "temario",
        "tema",
        "tests",
        "test_en_curso",
        "resultado",
        "simulacros",
        "examenes",
        "fallos",
        "progreso",
        "acceso",
        "registro",
        "recuperar",
        "mi_cuenta",
        "aviso_legal",
        "privacidad",
        "cookies",
    }
)

#: Las acciones que se pueden contar. Son verbos del recorrido de estudio, sin sujeto.
ACTION_LABELS: frozenset[str] = frozenset(
    {
        "test_iniciado",
        "test_terminado",
        "simulacro_iniciado",
        "examen_abierto",
        "aviso_de_apuntes_enviado",
        "consentimiento_otorgado",
        "consentimiento_rechazado",
        "cuenta_creada",
        "sesion_iniciada",
        "sesion_cerrada",
    }
)

#: Un tope de longitud para la etiqueta, por si algún día se añade una lista más larga: la columna
# no#: puede crecer sin que nadie lo mire.
MAX_LABEL_LENGTH = 48

#: Cuánto se guardan los contadores. Doce meses, como declara el inventario de datos.
RETENTION_DAYS = 365


@dataclass(frozen=True, slots=True)
class AnalyticsEvent:
    """Un suceso contado: qué día, de qué tipo y de qué pantalla o acción.

    **No tiene sujeto**: ni cuenta, ni sesión, ni nada que permita unir dos sucesos de la misma
    persona. Es un contador, y por eso no es un dato personal.
    """

    day: str
    name: str
    label: str


def labels_for(name: str) -> frozenset[str]:
    """Las etiquetas admitidas para un tipo de suceso. Un tipo desconocido no admite ninguna."""
    if name == PAGE_VIEW:
        return PAGE_LABELS
    if name == ACTION:
        return ACTION_LABELS
    return frozenset()


def is_valid_event(name: str, label: str) -> bool:
    """¿Se puede contar esto? Se comprueba en el servidor, no en la pantalla.

    La lista cerrada es lo que convierte el esquema en una garantía: no hay ninguna forma de guardar
    un texto libre por este camino, así que no hay ninguna forma de guardar ahí el enunciado de una
    pregunta, el nombre de un tema ni un identificador de alguien.
    """
    if len(label) > MAX_LABEL_LENGTH:
        return False
    return label in labels_for(name)


__all__ = [
    "ACTION",
    "ACTION_LABELS",
    "EVENT_NAMES",
    "MAX_LABEL_LENGTH",
    "PAGE_LABELS",
    "PAGE_VIEW",
    "RETENTION_DAYS",
    "AnalyticsEvent",
    "is_valid_event",
    "labels_for",
]
