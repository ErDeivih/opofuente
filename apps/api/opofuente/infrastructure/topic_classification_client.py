"""Cliente del modelo de lenguaje para clasificar preguntas (F4): DeepSeek sobre su API compatible.

Tres cosas que este fichero hace y no son obvias:

1. **La clave se lee del entorno y no se guarda en ningún sitio**: ni en un fichero, ni en el
   repositorio, ni en un log, ni en un mensaje de error. Si no está, quien llama para; aquí no se
   inventa nada.
2. **El temario va en el mensaje de sistema** para que el proveedor pueda cobrarlo a precio de
   acierto de caché: es el prefijo estable de todas las llamadas.
3. **`http.client` y no `urllib`/`httpx`**: es lo que ya usa la descarga segura del proyecto, no
   añade dependencias y no deja la puerta abierta a abrir una URL arbitraria.
"""

from __future__ import annotations

import http.client
import json
import ssl
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlsplit

from opofuente.domain.errors import ConfigurationError, ExternalServiceError
from opofuente.domain.topic_classification import (
    ClassifiableQuestion,
    OutOfSyllabus,
    ProposalBatch,
    Syllabus,
    TopicProposal,
    build_system_prompt,
    build_user_prompt,
)

#: Endpoint del proveedor. La API de DeepSeek es compatible con la de OpenAI en `/chat/completions`.
BASE_URL_POR_DEFECTO = "https://api.deepseek.com"

#: Modelo con el que se mide y se clasifica (el barato; el `pro` cuesta 4,4 veces más).
MODELO_POR_DEFECTO = "deepseek-flash"

#: Motivos que el modelo puede devolver, con el mismo vocabulario que el dominio.
_MOTIVOS = {motivo.value: motivo for motivo in OutOfSyllabus}


def read_response(payload: str, *, requested: Sequence[str]) -> ProposalBatch:
    """Lee la respuesta del modelo: solo lo que se puede sostener, y sin inventar lo que falta.

    La forma es la de la API compatible con OpenAI: el `usage` va en el sobre y las asignaciones
    dentro del `content` del primer mensaje, que a su vez es JSON. Se leen los dos de una vez para
    que el informe pueda decir lo que costó sin una segunda lectura.

    Un elemento al que le falta el identificador, o que apunta a una pregunta que no se preguntó, se
    descarta: no se puede clasificar una pregunta que no está en el lote. Lo que sí se hace es
    devolver **lo que había legible**, para que el servicio pueda contar el resto como «sin
    propuesta» en lugar de perder el lote entero por una respuesta mal formada.
    """
    sobre = _objeto(payload, "la respuesta del modelo")
    contenido = _contenido(sobre)
    dentro = _objeto(contenido, "el contenido del modelo")
    asignaciones = dentro.get("asignaciones")
    if not isinstance(asignaciones, list):
        raise ExternalServiceError("el contenido del modelo no trae la lista «asignaciones»")

    pedidas = set(requested)
    propuestas: list[TopicProposal] = []
    for elemento in asignaciones:
        if not isinstance(elemento, dict):
            continue
        identificador = elemento.get("id")
        if not isinstance(identificador, str) or identificador not in pedidas:
            continue
        propuestas.append(_proposal(elemento, question_version_id=identificador))
    uso = sobre.get("usage")
    return ProposalBatch(
        proposals=tuple(propuestas),
        input_tokens=_entero(uso, "prompt_tokens"),
        output_tokens=_entero(uso, "completion_tokens"),
    )


def _objeto(payload: str, que: str) -> dict[str, Any]:
    """Un texto que tiene que ser un objeto JSON. Si no lo es, se dice **qué** no lo era."""
    try:
        crudo: Any = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ExternalServiceError(f"{que} no es JSON") from error
    if not isinstance(crudo, dict):
        raise ExternalServiceError(f"{que} no es un objeto JSON")
    return {str(clave): valor for clave, valor in crudo.items()}


def _contenido(sobre: dict[str, Any]) -> str:
    """El `content` del primer mensaje de la respuesta, que es donde viene el JSON de verdad."""
    opciones = sobre.get("choices")
    if not isinstance(opciones, list) or not opciones:
        raise ExternalServiceError("la respuesta del modelo no trae ninguna opción")
    primera = opciones[0]
    mensaje = primera.get("message") if isinstance(primera, dict) else None
    contenido = mensaje.get("content") if isinstance(mensaje, dict) else None
    if not isinstance(contenido, str):
        raise ExternalServiceError("la respuesta del modelo no trae contenido")
    return contenido


def _proposal(elemento: dict[str, Any], *, question_version_id: str) -> TopicProposal:
    """Un elemento de la respuesta, leído con tolerancia pero sin traducir lo que no dice.

    Una confianza que no es un número se lee como 0: por debajo del mínimo no se escribe nada, y eso
    es exactamente lo que corresponde a una respuesta que no se puede interpretar.
    """
    motivo = elemento.get("fuera_de_temario")
    return TopicProposal(
        question_version_id=question_version_id,
        topic_code=_texto(elemento.get("tema")),
        epigraph_code=_texto(elemento.get("epigrafe")),
        confidence=_numero(elemento.get("confianza")),
        out_of_syllabus=_MOTIVOS.get(motivo) if isinstance(motivo, str) else None,
        note=_texto(elemento.get("motivo")),
    )


def _texto(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    limpio = value.strip()
    return limpio or None


def _numero(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def _entero(payload: object, clave: str) -> int:
    if not isinstance(payload, dict):
        return 0
    valor = payload.get(clave)
    return int(valor) if isinstance(valor, int) and not isinstance(valor, bool) else 0


class DeepSeekTopicProposer:
    """Pide al modelo un tema y un epígrafe para cada pregunta de un lote.

    No decide nada: devuelve lo que el modelo contestó y el servicio aplica los umbrales. Así se
    puede probar todo el clasificador con un doble, sin llamar a nadie (y sin gastar).
    """

    name = "deepseek"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = MODELO_POR_DEFECTO,
        base_url: str = BASE_URL_POR_DEFECTO,
        timeout_seconds: float = 120.0,
    ) -> None:
        if not api_key.strip():
            raise ConfigurationError(
                "falta la clave del modelo: se lee de DEEPSEEK_API_KEY y no se guarda en ningún "
                "sitio"
            )
        parts = urlsplit(base_url.strip())
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            raise ConfigurationError(
                f"la dirección del modelo tiene que ser http(s) con servidor: «{base_url}» no lo es"
            )
        self._api_key = api_key
        self._model = model
        self._scheme = parts.scheme.lower()
        self._host = parts.hostname
        self._port = parts.port or (443 if self._scheme == "https" else 80)
        camino = parts.path.rstrip("/")
        self._path = f"{camino}/chat/completions"
        self._timeout = timeout_seconds

    @property
    def version(self) -> str:
        """La versión del motor es el modelo: dos modelos distintos proponen cosas distintas."""
        return self._model

    def propose(
        self, questions: Sequence[ClassifiableQuestion], *, syllabus: Syllabus
    ) -> ProposalBatch:
        """Las propuestas del modelo para este lote, con los tokens que costó.

        `temperature=0`: la misma pregunta debería caer en el mismo tema en dos pasadas. El piloto
        midió un 7 % de inestabilidad con el ajuste por defecto, y esa inestabilidad es justo lo que
        se quiere quitar de una clasificación que se va a revisar a mano.
        """
        cuerpo = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": build_system_prompt(syllabus)},
                {"role": "user", "content": build_user_prompt(questions)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "stream": False,
        }
        respuesta = self._post(json.dumps(cuerpo, ensure_ascii=False))
        return read_response(respuesta, requested=[p.question_version_id for p in questions])

    def _post(self, body: str) -> str:
        """Una petición al modelo. Los fallos se dicen con su tipo, nunca con la clave dentro."""
        context = ssl.create_default_context() if self._scheme == "https" else None
        connection: http.client.HTTPConnection
        if self._scheme == "https":
            connection = http.client.HTTPSConnection(
                self._host, self._port, timeout=self._timeout, context=context
            )
        else:
            connection = http.client.HTTPConnection(self._host, self._port, timeout=self._timeout)
        try:
            connection.request(
                "POST",
                self._path,
                body=body.encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )
            response = connection.getresponse()
            payload = response.read().decode("utf-8", errors="replace")
        except (http.client.HTTPException, OSError, ssl.SSLError) as error:
            raise ExternalServiceError(
                f"el modelo no respondió ({type(error).__name__})"
            ) from error
        finally:
            connection.close()
        if response.status >= 400:
            # El cuerpo del error puede traer detalles útiles, pero **no** se copia entero: podría
            # repetir la cabecera de autenticación. Se dice el estado y nada más.
            raise ExternalServiceError(f"el modelo respondió {response.status}")
        return payload


__all__ = ["BASE_URL_POR_DEFECTO", "MODELO_POR_DEFECTO", "DeepSeekTopicProposer", "read_response"]
