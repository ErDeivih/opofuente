"""El encargo al modelo y la lectura de su respuesta (M1 de la fase 3).

Separado del cliente a propósito: **esto son funciones puras** —lo que se le pide y cómo
se lee lo que contesta- y se prueban sin red y sin gastar.
modelo de verdad.

**La cita, por construcción.** Pedirle al modelo que copie una frase literal del apartado falla una
de cada tres veces: parafrasea, y la comprobación lo rechaza con razón. Por eso **el apartado viaja
con las frases numeradas**, el modelo **elige números** y **la cita la compone el programa** con el
texto del propio apartado. Así la cita es literal siempre.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from opofuente.application.explicaciones import ExplicacionPropuesta, PreguntaAExplicar
from opofuente.domain.errors import ExternalServiceError
from opofuente.domain.explicaciones import apartado_numerado, componer_cita

#: Lo que se le pide al modelo. **`numeros`, no `cita`**: la cita la pone el programa.
SISTEMA = (
    "Eres un profesor que prepara oposiciones. Para cada pregunta escribes una explicación de"
    " DOS a CINCO frases, en español, que diga por qué la opción correcta lo es y por qué la"
    " tentadora no lo es.\n\n"
    "Reglas que no puedes romper:\n"
    "- La explicación se apoya SOLO en el apartado que se te da, que viene con las frases"
    " numeradas.\n"
    "- Elige el NUMERO de la frase —o los números, como mucho dos— que justifican la respuesta."
    " No copies el texto: con el número basta, y el texto lo pone el programa.\n"
    "- No hables nunca de exámenes, de frecuencias ni de probabilidad de que algo caiga.\n"
    '- Devuelve JSON: {"explicaciones": [{"id", "texto", "numeros", "letra"}]}, una por pregunta.\n'
    '- "numeros" es una lista de enteros con las frases elegidas, por ejemplo [2] o [2, 3].\n'
    '- "letra" es la letra de la opción CORRECTA, la que se te da en la línea CLAVE. NUNCA la de'
    " la tentadora."
)


@dataclass(frozen=True, slots=True)
class RespuestaDelModelo:
    """Lo que volvió y lo que costó. Los tokens son la cifra que decide el hito."""

    propuestas: tuple[ExplicacionPropuesta, ...]
    tokens_entrada: int
    tokens_salida: int


def build_user_prompt(preguntas: Sequence[PreguntaAExplicar]) -> str:
    """El encargo: pregunta, opciones, clave y el apartado **con las frases numeradas**."""
    partes: list[str] = []
    for pregunta in preguntas:
        opciones = "; ".join(f"{letra}) {texto}" for letra, texto in pregunta.opciones)
        partes.append(
            f"ID: {pregunta.question_version_id}\n"
            f"PREGUNTA: {pregunta.enunciado}\n"
            f"OPCIONES: {opciones}\n"
            f"CLAVE (letras correctas): {', '.join(pregunta.clave)}\n"
            f"APARTADO DE LOS APUNTES (frases numeradas):\n{apartado_numerado(pregunta.apartado)}"
        )
    return "\n\n---\n\n".join(partes)


def _texto(valor: object) -> str:
    return str(valor).strip() if valor is not None else ""


def _numeros(valor: object) -> tuple[int, ...]:
    """Los números de frase que devolvió el modelo, **como mucho dos** y sin repetidos.

    **Acepta el número suelto, la lista y el texto**: el modelo devuelve a veces `"[2, 3]"` y otras
    `[2, 3]`, y las dos cosas quieren decir lo mismo. Un número que no sea entero se ignora: **no se
    adivina**. Y **el tope de dos** está aquí, no en el prompt, porque un modelo obediente no es una
    garantía.
    """
    if isinstance(valor, bool):
        return ()
    if isinstance(valor, str):
        return tuple(int(digitos) for digitos in re.findall(r"\d+", valor)[:2])
    if isinstance(valor, int):
        crudos: list[object] = [valor]
    elif isinstance(valor, list):
        crudos = list(valor)
    else:
        return ()
    elegidos: list[int] = []
    for crudo in crudos:
        try:
            numero = int(str(crudo))
        except (TypeError, ValueError):
            continue
        if numero >= 1 and numero not in elegidos:
            elegidos.append(numero)
        if len(elegidos) == 2:
            break
    return tuple(elegidos)


def contenido_del_sobre(sobre: dict[str, object]) -> str:
    """El texto que escribió el modelo, sacado del sobre de la API.

    **El modelo no devuelve su JSON en la raiz**: lo devuelve dentro de
    `choices[0].message.content`, y el sobre trae ademas el `usage`.
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


def read_response(
    payload: str,
    *,
    requested: Sequence[str],
    apartados: Mapping[str, str],
) -> RespuestaDelModelo:
    """Lee la respuesta del modelo y **compone la cita** con los números elegidos.

    **`payload` es el sobre entero**, el que devuelve el POST: **los tokens viajan
    en el sobre**, asi que abrirlo devuelve la cifra del ensayo y las propuestas.
    sobre**, así que abrirlo aquí devuelve la cifra del ensayo junto con las propuestas.
    **`apartados` es la tabla `id -> apartado`**, y es lo que hace literal la cita:
    sale de ese texto, no del modelo.
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
                cita=componer_cita(apartados.get(ident, ""), _numeros(cruda.get("numeros"))),
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
