"""El encargo al modelo y la lectura de su respuesta (M1 de la fase 3).

Separado del cliente a propósito: **esto son funciones puras** —lo que se le pide y cómo se lee lo
    que
contesta— y se prueban sin red y sin gastar. El cliente que hace el POST es lo único que necesita
modelo de verdad.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass

from opofuente.application.explicaciones import ExplicacionPropuesta, PreguntaAExplicar
from opofuente.domain.errors import ExternalServiceError

#: Lo que se le pide al modelo, y las cuatro reglas que el servicio comprobará después.
SISTEMA = (
    "Eres un profesor que prepara oposiciones. Para cada pregunta escribes una explicación de"
    " DOS a CINCO frases, en español, que diga por qué la opción correcta lo es y por qué la"
    "tentadora no lo es.\n\n"
    "Reglas que no puedes romper:\n"
    "- La explicación se apoya SOLO en el texto del apartado que se te da.\n"
    "- Copia LITERALMENTE, sin cambiar una coma, la frase del apartado en la que te apoyas.\n"
    "- No hables nunca de exámenes, de frecuencias ni de probabilidad de que algo caiga.\n"
    '- Devuelve JSON: {"explicaciones": [{"id", "texto", "cita", "letra"}]}, una por pregunta.'
    "\n"
    '- "letra" es la letra de la opción CORRECTA, la que se te da en la línea CLAVE. NUNCA la de la'
    ' tentadora: esa se nombra en el texto, pero no es la que va en "letra".'
)


@dataclass(frozen=True, slots=True)
class RespuestaDelModelo:
    """Lo que volvió y lo que costó. Los tokens son la cifra que decide el hito."""

    propuestas: tuple[ExplicacionPropuesta, ...]
    tokens_entrada: int
    tokens_salida: int


def build_user_prompt(preguntas: Sequence[PreguntaAExplicar]) -> str:
    """El encargo: pregunta, opciones, clave y el apartado que la sostiene."""
    partes: list[str] = []
    for pregunta in preguntas:
        opciones = "; ".join(f"{letra}) {texto}" for letra, texto in pregunta.opciones)
        partes.append(
            f"ID: {pregunta.question_version_id}\n"
            f"PREGUNTA: {pregunta.enunciado}\n"
            f"OPCIONES: {opciones}\n"
            f"CLAVE (letras correctas): {', '.join(pregunta.clave)}\n"
            f"APARTADO DE LOS APUNTES:\n{pregunta.apartado.strip()}"
        )
    return "\n\n---\n\n".join(partes)


def _texto(valor: object) -> str:
    return str(valor).strip() if valor is not None else ""


def contenido_del_sobre(sobre: dict[str, object]) -> str:
    """El texto que escribió el modelo, sacado del sobre de la API.

    **El modelo no devuelve su JSON en la raíz**: lo devuelve dentro de `choices[0].message.content`,
    y el sobre trae además el `usage`. Por eso la lectura se hace en dos pasos —abrir el sobre y
    luego leer el contenido—: **mezclarlos fue el fallo que dejó a M1 sin ensayo**.
    """
    elecciones = sobre.get("choices")
    if not isinstance(elecciones, list) or not elecciones:
        raise ExternalServiceError("el modelo no devolvió ninguna elección")
    primera = elecciones[0]
    if not isinstance(primera, dict):
        raise ExternalServiceError("el modelo devolvió una elección que no es un objeto")
    mensaje = primera.get("message")
    if not isinstance(mensaje, dict):
        raise ExternalServiceError("la elección del modelo no trae mensaje")
    contenido = _texto(mensaje.get("content"))
    if not contenido:
        raise ExternalServiceError("el modelo devolvió un mensaje vacío")
    return contenido


def read_response(payload: str, *, requested: Sequence[str]) -> RespuestaDelModelo:
    """Lee la respuesta del modelo; **lo que no corresponde a una pregunta pedida se queda fuera**.

    **`payload` es el sobre entero**, el que devuelve el POST: **los tokens viajan en el sobre, no en
    el contenido**, así que abrirlo aquí es lo que permite devolver la cifra del ensayo junto con las
    propuestas. El contenido se abre con `contenido_del_sobre` y **ese** es el que se parsea.
    """
    try:
        sobre = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ExternalServiceError("el modelo no devolvió JSON") from error
    if not isinstance(sobre, dict):
        raise ExternalServiceError("el modelo devolvió algo que no es un objeto JSON")
    try:
        datos = json.loads(contenido_del_sobre(sobre))
    except json.JSONDecodeError as error:
        raise ExternalServiceError("el modelo no devolvió JSON en su mensaje") from error
    if not isinstance(datos, dict):
        raise ExternalServiceError("el contenido del modelo no es un objeto JSON")
    crudas = datos.get("explicaciones")
    if not isinstance(crudas, list):
        raise ExternalServiceError("el modelo no devolvió la lista «explicaciones»")
    pedidas = set(requested)
    propuestas: list[ExplicacionPropuesta] = []
    for cruda in crudas:
        if not isinstance(cruda, dict):
            continue
        ident = _texto(cruda.get("id"))
        if ident not in pedidas:
            continue
        propuestas.append(
            ExplicacionPropuesta(
                question_version_id=ident,
                texto=_texto(cruda.get("texto")),
                cita=_texto(cruda.get("cita")),
                letra=_texto(cruda.get("letra")).lower()[:1],
            )
        )
    uso = sobre.get("usage")
    uso = uso if isinstance(uso, dict) else {}
    return RespuestaDelModelo(
        propuestas=tuple(propuestas),
        tokens_entrada=int(uso.get("prompt_tokens", 0) or 0),
        tokens_salida=int(uso.get("completion_tokens", 0) or 0),
    )
