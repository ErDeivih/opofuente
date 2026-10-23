"""El cliente del supuesto practico: dos llamadas al modelo (M5).

**Las dos, y por que son dos:**

1. **escribir el caso y sus veinticinco preguntas**, con su clave y su cita;
2. **responder esas preguntas a ciegas** —sin la clave delante— **para
   comprobar que hay una respuesta defendible**. **Es la unica forma de
   saber que el supuesto no se lo invento un solo modelo.**

**Sin clave no hay llamada y el cliente no se construye**: la ruta responde
503, igual que «regenerar» en M1. **Un supuesto que se genera sin modelo es
un supuesto inventado por el programa, y el hito no lo pide.**

**Y el gasto se dice antes**: veinticinco preguntas con su cita son unos
cuatro mil tokens de salida, y la segunda llamada otros mil. **Con el tope
de 6 $ del hito, eso son unos 0,012 $ por supuesto** —la cifra medida de
las explicaciones, 0,000024 $ por pregunta, por cuatrocientas preguntas—.
"""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from typing import Any

from opofuente.domain.practical_case import (
    PreguntaPropuesta,
    SupuestoPropuesto,
)

#: El sistema: **pide el caso y sus preguntas, y prohibe inventar fuera de
#: los apuntes**. Sin esta frase el modelo rellena con lo que sabe del
#: temario, que puede estar bien y no ser lo que el alumno estudia.
SISTEMA = (
    "Eres un examinador de oposiciones. Escribes un supuesto practico sobre "
    "el material que se te da, y nada mas: no uses conocimientos que no "
    "esten en el texto. Devuelve JSON con las claves exactas que se piden."
)

#: La segunda llamada: **responde sin ver la clave**.
SISTEMA_A_CIEGAS = (
    "Eres un opositor. Contesta estas preguntas usando solo el texto del "
    "caso y de los apuntes. No sabes cual es la respuesta correcta. "
    "Devuelve JSON con una letra por pregunta."
)


class PracticalCaseClient:
    """Escribe supuestos y los responde a ciegas. **No decide nada.**"""

    name = "deepseek"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        timeout_seconds: float = 120.0,
        cliente: Any | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("sin clave no hay supuesto: no se puede construir")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        self._cliente = cliente

    def _post(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        """Una llamada, con tres reintentos solo en errores de conexion.

        **Los 4xx no se reintentan**: una clave mal puesta no se arregla
        esperando.
        """
        ultimo: Exception | None = None
        for intento in range(3):
            try:
                if self._cliente is not None:
                    return self._cliente(cuerpo)  # type: ignore[no-any-return]
                return self._post_una_vez(cuerpo)
            except (ConnectionError, TimeoutError) as error:
                ultimo = error
                time.sleep(2 * (intento + 1))
        raise RuntimeError(f"el modelo no respondio: {ultimo}")

    def _post_una_vez(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        import httpx

        with httpx.Client(timeout=self._timeout) as http:
            respuesta = http.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "temperature": 0,
                    "max_tokens": 8000,
                    "response_format": {"type": "json_object"},
                    **cuerpo,
                },
            )
            respuesta.raise_for_status()
            return dict(respuesta.json())

    def proponer(self, *, block: str, apartado: str) -> SupuestoPropuesto:
        """Escribe el caso y sus veinticinco preguntas, **o lanza**.

        **No valida**: devuelve lo que dijo el modelo y `validar_forma`
        decide. **Separar las dos cosas es lo que permite probar la
        validacion sin red.**
        """
        sobre = self._post(
            {
                "messages": [
                    {"role": "system", "content": SISTEMA},
                    {
                        "role": "user",
                        "content": (
                            f"Bloque {block}. Escribe un supuesto practico sobre este apartado. "
                            "Tiene que traer EXACTAMENTE veinticinco preguntas: veinte ordinarias "
                            "y cinco de reserva, y las de reserva empiezan su enunciado por la "
                            "palabra RESERVA. Ni mas ni menos.\n\n"
                            f"{apartado}\n\nDevuelve: "
                            '{"statement": "...", "preguntas": ['
                            '{"enunciado": "...", "opciones": {"a": "...", "b": "...", '
                            '"c": "...", "d": "..."}, "clave": "a", "cita": "..."}]}'
                        ),
                    },
                ],
            }
        )
        datos = _contenido(sobre)
        preguntas = tuple(
            PreguntaPropuesta(
                enunciado=str(item.get("enunciado", "")),
                opciones=tuple(
                    (letra, str(texto)) for letra, texto in dict(item.get("opciones", {})).items()
                ),
                clave=str(item.get("clave", "")),
                cita=str(item.get("cita", "")),
            )
            for item in datos.get("preguntas", [])
        )
        return SupuestoPropuesto(
            block=block,
            statement=str(datos.get("statement", "")),
            preguntas=preguntas,
        )

    def responder_a_ciegas(self, *, supuesto: SupuestoPropuesto, apartado: str) -> tuple[str, ...]:
        """El segundo modelo contesta **sin ver la clave**.

        **Solo se le manda el enunciado y las opciones**: si se le pasara la
        clave, la comprobacion no valdria nada. **Y se le manda el apartado**
        para que conteste con el temario delante, que es lo que hara el
        alumno.
        """
        preguntas = [
            {
                "numero": numero,
                "enunciado": pregunta.enunciado,
                "opciones": dict(pregunta.opciones),
            }
            for numero, pregunta in enumerate(supuesto.preguntas, start=1)
        ]
        sobre = self._post(
            {
                "messages": [
                    {"role": "system", "content": SISTEMA_A_CIEGAS},
                    {
                        "role": "user",
                        "content": (
                            f"Caso:\n{supuesto.statement}\n\n"
                            f"Material:\n{apartado}\n\n"
                            f"Preguntas:\n{json.dumps(preguntas, ensure_ascii=False)}\n\n"
                            'Devuelve: {"respuestas": ["a", "b", ...]} con una letra '
                            "por pregunta, en orden."
                        ),
                    },
                ],
            }
        )
        datos = _contenido(sobre)
        return tuple(str(letra).strip().lower() for letra in datos.get("respuestas", []))


def _contenido(sobre: dict[str, Any]) -> dict[str, Any]:
    """El JSON del mensaje, **no el sobre**.

    **El fallo de M1 fue leer el sobre como si fuera el mensaje**: los
    tokens vienen fuera y el contenido dentro, y confundirlos da un
    `KeyError` o, peor, una respuesta vacia que se toma por buena.
    """
    try:
        texto = sobre["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"la respuesta no trae mensaje: {error}") from error
    try:
        datos = json.loads(texto)
    except ValueError as error:
        raise RuntimeError(f"el mensaje no es JSON: {error}") from error
    if not isinstance(datos, dict):
        raise RuntimeError("el mensaje no es un objeto JSON")
    return datos


def respuestas_de(datos: Sequence[Any]) -> tuple[str, ...]:
    """Las letras de una lista cualquiera, normalizadas. **Ayuda a las pruebas.**"""
    return tuple(str(valor).strip().lower() for valor in datos)
