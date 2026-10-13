"""La segunda mitad del importador: la plantilla entra en la biblioteca y enlaza con su clave (D10).

**Por qué hace falta.** Un examen oficial **no se puede hacer** sin su clave activa, y la invariante
del proyecto (`can_activate`) no deja activar la clave de un examen oficial si su plantilla no está
enlazada a una **versión de documento de la biblioteca**. Eso no es un estorbo: enlazar exige que la
plantilla diga lo mismo que la clave, pregunta a pregunta, y esa comprobación es la que demuestra
que la clave que se aplica es la del documento oficial y no una parecida.

**Cómo lo hace.** Por las **rutas de la API**, que es donde vive el pipeline de ingesta (la
extracción es un trabajo del worker, no algo que se pueda hacer «a mano» sin inventarse la
maquinaria):

1. sube el PDF de la plantilla a un lote de ingesta (`POST /ingestion-batches/files`);
2. espera a que el worker lo extraiga y lee la representación (su texto);
3. promociona el artefacto a documento con tipo `answer_key` (`POST /documents`);
4. acepta la versión (`POST /documents/{id}/versions/{id}/accept`);
5. enlaza la plantilla a la clave del examen (`POST /question-sets/{id}/answer-keys/{id}/source`),
   que **verifica** que coinciden;
6. activa la clave (`POST .../activate`), que es lo que deja el examen practicable.

Por eso este módulo necesita la API levantada: se le pasa su dirección. Lo que **no** hace es tocar
la base por su cuenta ni saltarse ninguna comprobación.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Cuánto se espera a que el worker extraiga una plantilla (una página de texto: segundos).
ESPERA_DE_EXTRACCION_SEGUNDOS = 180.0

#: Cada cuánto se pregunta si el lote ya terminó.
INTERVALO_DE_ESPERA_SEGUNDOS = 1.5


@dataclass(frozen=True, slots=True)
class EnlaceDePlantilla:
    """Qué ha pasado al intentar dejar un examen con su clave activa."""

    ok: bool
    detalle: str
    document_version_id: str | None = None
    key_id: str | None = None
    activa: bool = False


class ApiInalcanzableError(RuntimeError):
    """La API no responde: sin ella no se puede ingerir ni enlazar nada."""


def _peticion(
    api: str,
    metodo: str,
    ruta: str,
    *,
    cuerpo: dict[str, object] | None = None,
    fichero: Path | None = None,
    campo: str = "files",
) -> Any:
    """Una petición a la API. Con `fichero`, se manda como `multipart/form-data`."""
    url = f"{api.rstrip('/')}{ruta}"
    datos: bytes | None = None
    cabeceras: dict[str, str] = {"Accept": "application/json"}
    if fichero is not None:
        frontera = "----opofuente-inap-frontera"
        contenido = fichero.read_bytes()
        cuerpo_multipart = (
            f"--{frontera}\r\n"
            f'Content-Disposition: form-data; name="{campo}"; filename="{fichero.name}"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode()
        cierre = f"\r\n--{frontera}--\r\n".encode()
        datos = cuerpo_multipart + contenido + cierre
        cabeceras["Content-Type"] = f"multipart/form-data; boundary={frontera}"
    elif cuerpo is not None:
        datos = json.dumps(cuerpo).encode("utf-8")
        cabeceras["Content-Type"] = "application/json"
    peticion = urllib.request.Request(url, data=datos, headers=cabeceras, method=metodo)  # noqa: S310
    try:
        with urllib.request.urlopen(peticion, timeout=60) as respuesta:  # noqa: S310
            texto = respuesta.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"{metodo} {ruta} → {error.code}: {detalle}") from error
    except urllib.error.URLError as error:
        raise ApiInalcanzableError(
            f"la API de {api} no responde ({error.reason}): el enlace de plantillas necesita la "
            "API levantada, porque la extracción la hace su worker"
        ) from error
    return {} if not texto.strip() else json.loads(texto)


def _subir_y_esperar(api: str, plantilla: Path) -> tuple[str, str]:
    """Sube el PDF y espera la extracción. Devuelve `(artifact_id, representación)`."""
    lote = str(_peticion(api, "POST", "/api/v1/ingestion-batches/files", fichero=plantilla)["id"])
    limite = time.monotonic() + ESPERA_DE_EXTRACCION_SEGUNDOS
    estado = "queued"
    while time.monotonic() < limite:
        detalle = _peticion(api, "GET", f"/api/v1/ingestion-batches/{lote}")
        estado = str(detalle["batch"]["status"])
        if estado in {"succeeded", "failed", "cancelled"}:
            break
        time.sleep(INTERVALO_DE_ESPERA_SEGUNDOS)
    if estado != "succeeded":
        raise RuntimeError(f"la extracción del lote {lote} quedó en «{estado}»")
    representaciones = _peticion(api, "GET", f"/api/v1/ingestion-batches/{lote}/representations")
    if not isinstance(representaciones, list) or not representaciones:  # pragma: no cover - defensa
        raise RuntimeError(f"el lote {lote} no dejó ninguna representación con texto")
    primera = representaciones[0]
    if not primera.get("has_text"):
        raise RuntimeError(
            f"la plantilla {plantilla.name} se extrajo sin texto: no se puede enlazar a ciegas"
        )
    return str(primera["artifact_id"]), str(primera["id"])


def _aceptar_si_hace_falta(api: str, *, documento: str, version: str) -> None:
    """Acepta la versión, y no se queja si ya estaba aceptada.

    La ingesta **promociona y acepta sola** algunas versiones (el pipeline de clasificación va
    detrás de la extracción), así que aceptar puede llegar tarde: «No se puede aceptar una versión
    «accepted»» no es un fallo, es que el trabajo ya estaba hecho. Cualquier otro 409 sí se propaga.
    """
    try:
        _peticion(api, "POST", f"/api/v1/documents/{documento}/versions/{version}/accept")
    except RuntimeError as error:
        if "accepted" not in str(error):
            raise


def enlazar_plantilla(
    api: str,
    *,
    plantilla: Path,
    titulo_documento: str,
    set_id: str,
    etiqueta_de_version: str,
) -> EnlaceDePlantilla:
    """Deja el examen `set_id` con su plantilla enlazada y su clave activa, por la API."""
    artefacto, _representacion = _subir_y_esperar(api, plantilla)
    promocion = _peticion(
        api,
        "POST",
        "/api/v1/documents",
        cuerpo={
            "artifact_id": artefacto,
            "title": titulo_documento,
            "document_type": "answer_key",
            "authority_tier": "A",
            "version_label": etiqueta_de_version,
        },
    )
    documento = str(promocion["document_id"])
    version = str(promocion["version_id"])
    _aceptar_si_hace_falta(api, documento=documento, version=version)

    claves = _peticion(api, "GET", f"/api/v1/question-sets/{set_id}/answer-keys")
    candidatas = [clave for clave in claves if str(clave["status"]) in {"draft", "active"}]
    if not candidatas:
        return EnlaceDePlantilla(False, "el examen no tiene ninguna clave que enlazar")
    clave = candidatas[0]
    # Enlazar **verifica**: la API compara la plantilla con la clave, pregunta a pregunta, y
    # responde con un conflicto si una sola no coincide. Es la comprobación que demuestra que la
    # clave que se va a activar es la del documento oficial.
    _peticion(
        api,
        "POST",
        f"/api/v1/question-sets/{set_id}/answer-keys/{clave['id']}/source",
        cuerpo={"source_document_version_id": version},
    )
    activa = _peticion(
        api, "POST", f"/api/v1/question-sets/{set_id}/answer-keys/{clave['id']}/activate"
    )
    return EnlaceDePlantilla(
        ok=str(activa["status"]) == "active",
        detalle=f"clave v{activa['version_no']} → {activa['status']}",
        document_version_id=version,
        key_id=str(clave["id"]),
        activa=str(activa["status"]) == "active",
    )


__all__ = [
    "ApiInalcanzableError",
    "EnlaceDePlantilla",
    "enlazar_plantilla",
]
