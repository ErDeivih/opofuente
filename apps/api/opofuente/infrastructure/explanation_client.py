"""El cliente real de las explicaciones: un POST por lote (M1 de la fase 3).

Se copia la forma de `topic_classification_client`: mismo `Bearer`, mismo
`_post`, mismas reglas de error (sin la clave dentro del mensaje y con el
codigo de estado y nada mas) y `temperature = 0`, porque la misma pregunta
tiene que recibir la misma explicacion en dos pasadas.
"""

from __future__ import annotations

import http.client
import json
import ssl
from collections.abc import Sequence
from urllib.parse import urlsplit

from opofuente.application.explicaciones import ExplicacionPropuesta, PreguntaAExplicar
from opofuente.domain.errors import ConfigurationError, ExternalServiceError
from opofuente.domain.explicacion_prompt import SISTEMA, build_user_prompt, read_response

#: El modelo por defecto.
MODELO_POR_DEFECTO = "deepseek-chat"
#: La base por defecto.
BASE_URL_POR_DEFECTO = "https://api.deepseek.com/v1"


class DeepSeekExplanationProposer:
    """Pide al modelo una explicacion por pregunta. No decide: contesta."""

    name = "deepseek"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = MODELO_POR_DEFECTO,
        base_url: str = BASE_URL_POR_DEFECTO,
        timeout_seconds: float = 180.0,
    ) -> None:
        if not api_key.strip():
            raise ConfigurationError(
                "falta la clave del modelo: se lee de DEEPSEEK_API_KEY y no se guarda"
            )
        parts = urlsplit(base_url.strip())
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            raise ConfigurationError("la direccion del modelo tiene que ser http(s)")
        self._api_key = api_key
        self._model = model
        self._scheme = parts.scheme.lower()
        self._host = parts.hostname
        self._port = parts.port or (443 if self._scheme == "https" else 80)
        self._path = f"{parts.path.rstrip('/')}/chat/completions"
        self._timeout = timeout_seconds
        #: Lo que costo la ultima llamada: la cifra del ensayo.
        self.ultimos_tokens: tuple[int, int] = (0, 0)

    @property
    def version(self) -> str:
        return self._model

    def propose(self, lote: Sequence[PreguntaAExplicar]) -> Sequence[ExplicacionPropuesta]:
        cuerpo = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SISTEMA},
                {"role": "user", "content": build_user_prompt(lote)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "stream": False,
        }
        respuesta = read_response(
            self._post(json.dumps(cuerpo, ensure_ascii=False)),
            requested=[p.question_version_id for p in lote],
            apartados={p.question_version_id: p.apartado for p in lote},
        )
        self.ultimos_tokens = (respuesta.tokens_entrada, respuesta.tokens_salida)
        return respuesta.propuestas

    def _post(self, body: str) -> str:
        if self._scheme == "https":
            conectar: http.client.HTTPConnection = http.client.HTTPSConnection(
                self._host,
                self._port,
                timeout=self._timeout,
                context=ssl.create_default_context(),
            )
        else:
            conectar = http.client.HTTPConnection(self._host, self._port, timeout=self._timeout)
        try:
            conectar.request(
                "POST",
                self._path,
                body=body.encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )
            respuesta = conectar.getresponse()
            payload = respuesta.read().decode("utf-8", errors="replace")
        except (http.client.HTTPException, OSError, ssl.SSLError) as error:
            raise ExternalServiceError(
                f"el modelo no respondio ({type(error).__name__})"
            ) from error
        finally:
            conectar.close()
        if respuesta.status >= 400:
            raise ExternalServiceError(f"el modelo respondio {respuesta.status}")
        return payload
