"""El cliente del modelo para los apuntes (pasos B, D y E): DeepSeek sobre su API compatible.

Tres cosas que este fichero hace y no son obvias:

1. **la clave se lee del entorno y no se guarda en ningún sitio**: ni en un fichero, ni en el
   repositorio, ni en un log, ni en un mensaje de error. Si no está, quien llama para; aquí no se
   inventa nada;
2. **lo estable va en el mensaje de sistema**: el temario (paso B) y el texto de los apuntes (paso
E)
   son el mismo prefijo en todas las llamadas de un tema o de un epígrafe, y así el proveedor puede
   cobrarlos a precio de acierto de caché;
3. **`http.client` y no `urllib`/`httpx`**: es lo que ya usa el resto del proyecto, no añade
   dependencias y no deja la puerta abierta a abrir una URL arbitraria.

La lectura de la respuesta es tolerante **por elemento**: un hecho sin texto, una respuesta sin id o
un id que no se preguntó se descartan, y el resto del lote se aprovecha. Perder un lote entero de
veinte preguntas por una coma mal puesta costaría dinero y horas.
"""

from __future__ import annotations

import http.client
import json
import ssl
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlsplit

from opofuente.domain.errors import ConfigurationError, ExternalServiceError
from opofuente.domain.topic_notes import (
    SYSTEM_PROMPT_ANADIR,
    ComprobacionBatch,
    FactKind,
    Hecho,
    HechosBatch,
    MaterialPassage,
    NoteSection,
    QuestionGroup,
    QuoteCheck,
    RedaccionBatch,
    build_system_prompt_comprobar,
    build_system_prompt_hechos,
    build_system_prompt_redactar,
    build_user_prompt_anadir,
    build_user_prompt_comprobar,
    build_user_prompt_hechos,
    build_user_prompt_redactar,
    leer_uso,
)

#: Endpoint del proveedor. La API de DeepSeek es compatible con la de OpenAI en `/chat/completions`.
BASE_URL_POR_DEFECTO = "https://api.deepseek.com"

#: Modelo con el que se escribe y se comprueba (el barato; el `pro` cuesta 4,4 veces más).
MODELO_POR_DEFECTO = "deepseek-flash"


# --- lectura de las respuestas (pura: se prueba sin red) ------------------------------------------


def read_hechos(payload: str, *, requested: Sequence[str]) -> HechosBatch:
    """Los hechos de una respuesta del paso B, con los tokens que costó."""
    sobre = _objeto(payload, "la respuesta del modelo")
    dentro = _objeto(_contenido(sobre), "el contenido del modelo")
    elementos = dentro.get("hechos")
    if not isinstance(elementos, list):
        raise ExternalServiceError("el contenido del modelo no trae la lista «hechos»")
    pedidas = set(requested)
    hechos: list[Hecho] = []
    contestadas: set[str] = set()
    for elemento in elementos:
        if not isinstance(elemento, dict):
            continue
        firma = elemento.get("id")
        if not isinstance(firma, str) or firma not in pedidas:
            continue
        contestadas.add(firma)
        textos = elemento.get("hechos")
        if not isinstance(textos, list):
            continue
        for texto in textos:
            hecho = _hecho(texto, firma=firma, elemento=elemento)
            if hecho is not None:
                hechos.append(hecho)
    entrada, salida, cache = leer_uso(sobre)
    return HechosBatch(
        hechos=tuple(hechos),
        input_tokens=entrada,
        output_tokens=salida,
        cache_hit_tokens=cache,
        sin_hechos=tuple(sorted(pedidas - contestadas)),
    )


def _hecho(texto: object, *, firma: str, elemento: dict[str, Any]) -> Hecho | None:
    """Un hecho del lote, o `None` si no se puede sostener (sin texto o sin epígrafe)."""
    if not isinstance(texto, dict):
        return None
    cuerpo = texto.get("texto")
    if not isinstance(cuerpo, str) or not cuerpo.strip():
        return None
    epigrafe = elemento.get("epigrafe")
    if not isinstance(epigrafe, str) or not epigrafe.strip():
        return None
    tipo = texto.get("tipo")
    return Hecho(
        text=cuerpo.strip(),
        kind=FactKind.NORMATIVO if tipo == FactKind.NORMATIVO.value else FactKind.TECNICO,
        epigraph_code=epigrafe.strip(),
        source_groups=(firma,),
        doubtful=elemento.get("dudosa") is True,
        note=_texto(elemento.get("motivo")),
    )


def read_redaccion(payload: str) -> RedaccionBatch:
    """El texto de un apartado (o de un añadido) y los tokens que costó."""
    sobre = _objeto(payload, "la respuesta del modelo")
    dentro = _objeto(_contenido(sobre), "el contenido del modelo")
    markdown = dentro.get("markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        raise ExternalServiceError("el modelo no devolvió texto para el apartado")
    entrada, salida, cache = leer_uso(sobre)
    return RedaccionBatch(
        titulo=_texto(dentro.get("titulo")),
        markdown=markdown.strip(),
        input_tokens=entrada,
        output_tokens=salida,
        cache_hit_tokens=cache,
    )


def read_comprobacion(payload: str, *, requested: Sequence[str]) -> ComprobacionBatch:
    """Las respuestas del paso E: la letra y la frase copiada de cada pregunta del lote."""
    sobre = _objeto(payload, "la respuesta del modelo")
    dentro = _objeto(_contenido(sobre), "el contenido del modelo")
    elementos = dentro.get("respuestas")
    if not isinstance(elementos, list):
        raise ExternalServiceError("el contenido del modelo no trae la lista «respuestas»")
    pedidas = set(requested)
    checks: list[QuoteCheck] = []
    contestadas: set[str] = set()
    for elemento in elementos:
        if not isinstance(elemento, dict):
            continue
        firma = elemento.get("id")
        if not isinstance(firma, str) or firma not in pedidas:
            continue
        contestadas.add(firma)
        frase = _texto(elemento.get("frase"))
        checks.append(
            QuoteCheck(
                group_signature=firma,
                letter=_letra(elemento.get("letra")),
                quote=None if frase is None or frase.upper().startswith("NO EST") else frase,
            )
        )
    entrada, salida, cache = leer_uso(sobre)
    return ComprobacionBatch(
        checks=tuple(checks),
        input_tokens=entrada,
        output_tokens=salida,
        cache_hit_tokens=cache,
        sin_respuesta=tuple(sorted(pedidas - contestadas)),
    )


def _letra(valor: object) -> str | None:
    """La letra de una respuesta: una sola, en minúscula. Cualquier otra cosa es «no lo sé»."""
    if not isinstance(valor, str):
        return None
    limpia = valor.strip().lower().rstrip(").")
    return limpia if len(limpia) == 1 and limpia.isalpha() else None


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


def _texto(valor: object) -> str | None:
    if not isinstance(valor, str):
        return None
    limpio = valor.strip()
    return limpio or None


class DeepSeekNotesModel:
    """Pide al modelo los hechos, los apartados y las comprobaciones de los apuntes de un tema.

    No decide nada: devuelve lo que el modelo contestó y el servicio aplica las reglas. Así los
    apuntes se pueden probar enteros con un doble que no llama a nadie (y sin gastar).
    """

    name = "deepseek"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = MODELO_POR_DEFECTO,
        base_url: str = BASE_URL_POR_DEFECTO,
        timeout_seconds: float = 300.0,
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
        self._path = f"{parts.path.rstrip('/')}/chat/completions"
        self._timeout = timeout_seconds

    @property
    def version(self) -> str:
        """La versión del motor es el modelo: dos modelos distintos escriben apuntes distintos."""
        return self._model

    def hechos(
        self,
        grupos: Sequence[QuestionGroup],
        *,
        topic_code: str,
        topic_title: str,
        epigraphs: Sequence[tuple[str, str]],
    ) -> HechosBatch:
        """Los hechos del lote. `temperature=0`: la misma pregunta da el mismo hecho en dos
        pasadas."""
        cuerpo = self._cuerpo(
            system=build_system_prompt_hechos(
                topic_code=topic_code, topic_title=topic_title, epigraphs=epigraphs
            ),
            user=build_user_prompt_hechos(grupos),
        )
        return read_hechos(
            self._post(json.dumps(cuerpo, ensure_ascii=False)),
            requested=[grupo.signature for grupo in grupos],
        )

    def redactar(
        self,
        section: NoteSection,
        *,
        topic_code: str,
        topic_title: str,
        material: Sequence[MaterialPassage],
        es_tabla_de_puertos: bool = False,
    ) -> RedaccionBatch:
        """El texto de un apartado, con todos sus hechos dentro."""
        cuerpo = self._cuerpo(
            system=build_system_prompt_redactar(topic_code=topic_code, topic_title=topic_title),
            user=build_user_prompt_redactar(
                section, material, es_tabla_de_puertos=es_tabla_de_puertos
            ),
        )
        return read_redaccion(self._post(json.dumps(cuerpo, ensure_ascii=False)))

    def comprobar(self, grupos: Sequence[QuestionGroup], *, apuntes: str) -> ComprobacionBatch:
        """La comprobación del lote contra los apuntes que se le dan (y solo contra ellos)."""
        cuerpo = self._cuerpo(
            system=build_system_prompt_comprobar(apuntes),
            user=build_user_prompt_comprobar(grupos),
        )
        return read_comprobacion(
            self._post(json.dumps(cuerpo, ensure_ascii=False)),
            requested=[grupo.signature for grupo in grupos],
        )

    def anadir(
        self, section: NoteSection, grupos: Sequence[QuestionGroup], hechos: Sequence[Hecho]
    ) -> RedaccionBatch:
        """Lo que falta en un apartado, con los hechos que faltan como contenido obligatorio."""
        cuerpo = self._cuerpo(
            system=SYSTEM_PROMPT_ANADIR,
            user=build_user_prompt_anadir(section, grupos, hechos),
        )
        return read_redaccion(self._post(json.dumps(cuerpo, ensure_ascii=False)))

    def _cuerpo(self, *, system: str, user: str) -> dict[str, Any]:
        """El sobre de la petición. `temperature=0`: dos pasadas tienen que decir lo mismo."""
        return {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "stream": False,
        }

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


__all__ = [
    "BASE_URL_POR_DEFECTO",
    "MODELO_POR_DEFECTO",
    "DeepSeekNotesModel",
    "read_comprobacion",
    "read_hechos",
    "read_redaccion",
]
