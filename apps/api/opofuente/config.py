"""Configuración efectiva de OpoFuente.

Prioridad (02_ARCHITECTURE §8): valores seguros por defecto -> fichero local (`.env`) ->
variables de entorno. Ningún secreto de este módulo se expone por la API ni se registra en logs.

Regla dura: el host debe ser loopback. Un host público falla al arrancar
(09_SECURITY-PRIVACY-AND-RIGHTS §2).
"""

from __future__ import annotations

import os
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from opofuente.domain.errors import ConfigurationError
from opofuente.domain.providers import DestinationReason, classify_provider

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LlmProvider = Literal["disabled", "openai_compatible", "ollama"]
EmbeddingProvider = Literal["disabled", "local", "openai_compatible"]

#: Únicos hosts admitidos: la aplicación es local-first y de un solo usuario.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

#: Orígenes del frontend autorizados en desarrollo (Vite) y en preview.
DEFAULT_CORS_ORIGINS: tuple[str, ...] = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
)


def project_root() -> Path:
    """Raíz del repositorio, para resolver rutas relativas de forma determinista."""
    candidate = Path(__file__).resolve().parents[3]
    if (candidate / "pyproject.toml").is_file():
        return candidate
    return Path.cwd()


@dataclass(frozen=True, slots=True)
class DataPaths:
    """Árbol de datos local definido en 02_ARCHITECTURE §5."""

    root: Path
    #: Raíz del almacén. `storage_key` de un artefacto empieza por `sha256/…`, de modo que la ruta
    #: final es `data/artifacts/sha256/ab/cd/<hash>`, exactamente la documentada.
    artifacts: Path
    extracted: Path
    qdrant: Path
    exports: Path
    backups: Path
    logs: Path
    tmp: Path
    #: El temporal **de repuesto**, en el mismo árbol que la base. Existe porque `tmp` puede ser un
    #: enlace a otra unidad —en este equipo lo es, a `E:`— y una unidad que no está conectada deja
    # # el    #: temporal en un directorio que existe en el nombre y no en los hechos: se puede
    # listar y no se
    #: puede escribir. Ver `resolve_tmp_directory`.
    tmp_fallback: Path
    #: Los enlaces de recuperación de contraseña mientras **no** haya un servicio de correo
    #: contratado (§8). Vive dentro del árbol de datos, en la misma unidad que la base, y solo lo
    # # lee    #: el titular: el enlace no se registra en los logs ni viaja en ninguna respuesta
    # —las dos cosas
    #: están prohibidas por las reglas del proyecto—.
    recovery: Path

    @classmethod
    def from_root(cls, root: Path, *, tmp_fallback_name: str = "_tmp") -> DataPaths:
        return cls(
            root=root,
            artifacts=root / "artifacts",
            extracted=root / "extracted",
            qdrant=root / "qdrant",
            exports=root / "exports",
            backups=root / "backups",
            logs=root / "logs",
            tmp=root / "tmp",
            tmp_fallback=root / tmp_fallback_name,
            recovery=root / "recovery",
        )

    @property
    def database(self) -> Path:
        return self.root / "opofuente.sqlite3"

    def ensure_directories(self) -> None:
        """Crea el árbol de datos. Idempotente; no toca ningún original del usuario.

        **El temporal se crea con tolerancia y los demás no.** Los demás directorios son carpetas
        normales dentro del árbol: si alguno no se puede crear, es un fallo que hay que ver. El
        temporal puede ser un **enlace a otra unidad** y de eso ya se ocupa
        `resolve_tmp_directory`, que decide si se usa o se cae al de repuesto. Dejar que un `mkdir`
        sobre un enlace roto tumbe el arranque **aquí** daría el peor mensaje posible: una
        excepción de sistema, sin decir qué disco falta ni qué hacer.
        """
        for directory in (
            self.root,
            self.artifacts,
            self.extracted,
            self.qdrant,
            self.exports,
            self.backups,
            self.logs,
            self.recovery,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        with suppress(OSError):
            self.tmp.mkdir(parents=True, exist_ok=True)


def writable_directory_problem(path: Path) -> str | None:
    """¿Se puede escribir de verdad en este directorio? `None` significa que sí.

    **Se comprueba escribiendo.** `Path.exists()` no vale aquí y es justo la trampa que motivó esta
    función: un enlace a una unidad que no está conectada contesta que no existe o que existe, según
    cómo se pregunte, y ninguna de las dos respuestas dice lo único que importa —si se puede
    escribir un fichero—. El fichero de sonda se crea y se borra en la misma llamada, así que no
    deja rastro.
    """
    sonda = path / f".opofuente-sonda-{os.getpid()}-{uuid4().hex}"
    try:
        path.mkdir(parents=True, exist_ok=True)
        sonda.write_text("ok", encoding="utf-8")
    except OSError as error:
        return f"{type(error).__name__}: {error.strerror or error}"
    finally:
        # El borrado va aparte: si la escritura falló, el fichero no está y `unlink` tampoco debe
        # tumbar el arranque por un fallo que ya se ha explicado.
        with suppress(OSError):
            sonda.unlink()
    return None


@dataclass(frozen=True, slots=True)
class TmpDirectoryDecision:
    """Dónde queda el temporal y por qué. Se enseña en el arranque; no es un detalle interno."""

    paths: DataPaths
    #: `True` cuando **no** se usa el temporal configurado y se ha caído al de repuesto.
    fallback_used: bool
    #: El motivo por el que el temporal configurado no vale (vacío si vale).
    problem: str
    #: Si **ninguno** de los dos admite escritura. Entonces el arranque no puede seguir.
    nothing_writable: bool

    @property
    def detail(self) -> str:
        if not self.fallback_used:
            return f"temporal en {self.paths.tmp}"
        if self.nothing_writable:
            return (
                f"no se puede escribir ni en {self.paths.tmp} ({self.problem}) "
                f"ni en el temporal de repuesto {self.paths.tmp_fallback}"
            )
        return (
            f"el temporal configurado no admite escritura ({self.problem}); se usa el de repuesto "
            f"en {self.paths.tmp_fallback}"
        )


def resolve_tmp_directory(paths: DataPaths) -> TmpDirectoryDecision:
    """Elige el temporal que se puede usar de verdad, probándolo.

    El caso que lo motiva, medido en este equipo el 15 de octubre de 2026: `datos\\tmp` es un
    enlace a    `E:\\OpoFuente-archivo\\datos-tmp`, de los 41,6 GB que se movieron para liberar
    `F:`. Si `E:` no
    está conectado, el temporal configurado no se puede escribir y **todo lo que pasa por ahí** —el
    volcado de un artefacto al importar, la instantánea antes de una copia, la restauración— falla a
    media operación. Caer al temporal de repuesto, que vive en el mismo árbol que la base y por
    tanto en la misma unidad, convierte «falla a medias» en «funciona, y se dice por qué».
    """
    problema = writable_directory_problem(paths.tmp)
    if problema is None:
        return TmpDirectoryDecision(
            paths=paths, fallback_used=False, problem="", nothing_writable=False
        )

    problema_repuesto = writable_directory_problem(paths.tmp_fallback)
    sin_nada = problema_repuesto is not None
    return TmpDirectoryDecision(
        paths=replace(paths, tmp=paths.tmp_fallback),
        fallback_used=True,
        problem=problema,
        nothing_writable=sin_nada,
    )


class Settings(BaseSettings):
    """Configuración validada del proceso."""

    model_config = SettingsConfigDict(
        env_prefix="OPOFUENTE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    data_dir: Path = Path("data")
    host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1024, le=65535)
    log_level: LogLevel = "INFO"
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS

    llm_provider: LlmProvider = "disabled"
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None

    embedding_provider: EmbeddingProvider = "disabled"
    embedding_model: str | None = None
    #: Endpoint del proveedor de embeddings. Es un campo propio porque su destino se informa
    #: **aparte** del de lenguaje (DEBT-001): con un solo `llm_base_url` no se podía decir a dónde
    #: van los embeddings aunque el proveedor estuviera configurado.
    embedding_base_url: str | None = None

    # --- Zona del alumno (F2) -------------------------------------------------
    #: La oposición que sirve `/api/v1/student/*`. Es un **código**, no un identificador: los
    #: identificadores son de esta base y no se pueden escribir en un fichero de configuración que
    #: se copia entre máquinas. El filtro vive aquí, en el servidor: la pantalla del alumno no elige
    #: oposición (REDISENO-ALUMNO §3.11).
    student_opposition: str = Field(default="tai-age", min_length=1)
    #: Con `True`, la API del alumno sirve **solo** conjuntos `public` (los que la administración
    #: publica). Por defecto `False`: el propietario estudia con su propio material.
    public_mode: bool = False

    # --- Plataforma desplegable (§8 a §11 del objetivo vivo) ------------------
    #: **La regla que manda**: el alumno que ya existe tiene que seguir estudiando igual. Las cuatro
    #: banderas nacen apagadas, y con las cuatro a 0 el árbol se comporta exactamente como antes
    # para    #: quien estudia sin cuenta. Se encienden de una en una y a propósito.
    #:
    #: Cuentas y sesiones (§8). Encendida, la API de administración deja de ser abierta: pasa a
    #: exigir sesión, y las rutas de la cuenta (quién soy, cerrar sesión, darse de baja) contestan
    #: 401 sin ella. La zona de estudio sigue abierta a quien no tiene cuenta.
    accounts_enabled: bool = False
    #: Páginas legales, aviso de cookies y control de datos (§9). Encendida, la aplicación sirve los
    #: textos, pide la decisión sobre las cookies y no pone ninguna que no sea necesaria hasta que
    # se    #: decide.
    legal_enabled: bool = False
    #: Analítica propia (§10). Exige **además** el consentimiento de quien navega: con la bandera
    #: encendida y sin consentimiento, el servidor rechaza el suceso. Nunca hay identificadores de
    #: terceros.
    analytics_enabled: bool = False
    #: Pagos (§11). Es **solo el hueco**: no hay ninguna pasarela integrada ni ninguna cuenta
    # creada.    #: Encendida, las rutas informan de lo que habría que contratar; nunca cobran.
    payments_enabled: bool = False

    #: `SameSite` de la cookie de sesión. `lax` por defecto: el navegador no la manda en una
    # # petición    #: que venga de otro sitio, que es la defensa de fondo contra el CSRF. La
    # comprobación de
    # `Origin`    #: del middleware sigue siendo la primera.
    session_cookie_same_site: Literal["lax", "strict", "none"] = "lax"
    #: `Secure` de la cookie de sesión. **Apagado por defecto** porque la aplicación escucha en
    #: `http://127.0.0.1` y con `Secure` la cookie no se pondría nunca. El día que se sirva por
    # HTTPS    #: hay que encenderlo: está escrito en `PARA-EL-PROPIETARIO.md`.
    session_cookie_secure: bool = False
    #: Dónde vive la web cuando se despliegue, para poder componer el enlace de recuperación. Vacío
    #: significa «el primer origen autorizado», que es el servidor de la web en local.
    public_base_url: str | None = None
    #: ¿Hay servicio de correo contratado? **Hoy no**, y por eso está en `False` y el valor `True`
    #: **falla al arrancar**: sin proveedor, decir que sí solo serviría para que el enlace de
    #: recuperación se perdiera sin que nadie lo note. Mientras esté en `False`, el enlace se deja
    # en    #: `datos/recovery/` para que lo lea el titular (ver `PARA-EL-PROPIETARIO.md`).
    mail_enabled: bool = False
    #: Horas que dura una sesión sin volver a entrar.
    session_ttl_hours: int = Field(default=720, ge=1, le=8760)
    #: Coste de argon2id. Los valores por defecto del proyecto (los de la biblioteca) tardan del
    #: orden de una décima de segundo por comprobación; se dejan explícitos para poder bajarlos en
    #: una prueba que verifica cientos de contraseñas sin tardar minutos.
    password_hash_time_cost: int = Field(default=3, ge=1, le=20)
    password_hash_memory_cost_kib: int = Field(default=65536, ge=8192, le=1048576)
    password_hash_parallelism: int = Field(default=4, ge=1, le=16)

    @property
    def any_platform_feature_enabled(self) -> bool:
        """¿Hay algo de la plataforma encendido? Lo usa el arranque para decirlo en el registro."""
        return (
            self.accounts_enabled
            or self.legal_enabled
            or self.analytics_enabled
            or self.payments_enabled
        )

    @property
    def session_ttl(self) -> timedelta:
        return timedelta(hours=self.session_ttl_hours)

    tesseract_path: Path | None = None
    #: Idiomas del OCR, en la forma que entiende Tesseract (`spa`, `spa+eng`). Por defecto español,
    #: porque el material de esta aplicación está en español y un OCR en inglés sobre texto español
    #: produce texto plausible y equivocado.
    tesseract_languages: str = "spa"
    #: Directorio de datos de idioma de Tesseract (`tessdata`). Se pasa explícitamente al binario en
    #: vez de depender de `TESSDATA_PREFIX` del sistema: en Windows el directorio del programa no
    #: es escribible sin administrador, así que el modelo de español suele vivir en otro sitio.
    tesseract_tessdata: Path | None = None

    # --- Ingestión y worker local (S02) ---------------------------------------
    #: Worker en el propio proceso: consume la cola persistida sin Redis ni Celery.
    worker_enabled: bool = True
    worker_poll_seconds: float = Field(default=1.0, gt=0.05, le=60)
    #: Duración del lease de un trabajo. Si el proceso muere, el trabajo vuelve a la cola.
    job_lease_seconds: int = Field(default=60, ge=5, le=3600)
    #: Límites de la ingesta: por fichero y por lote.
    max_file_bytes: int = Field(default=512 * 1024 * 1024, ge=1024)
    max_batch_entries: int = Field(default=50_000, ge=1, le=1_000_000)

    # --- Extracción y entradas de S03 -----------------------------------------
    #: Caracteres como máximo por representación: por encima se recorta y se avisa.
    max_representation_chars: int = Field(default=2_000_000, ge=1_000)
    #: Páginas como máximo por PDF.
    max_pdf_pages: int = Field(default=2_000, ge=1, le=20_000)
    #: Límites de un ZIP (propio o dentro de un DOCX/PPTX): entradas, bytes y expansión.
    max_zip_entries: int = Field(default=2_000, ge=1, le=100_000)
    max_zip_uncompressed_bytes: int = Field(default=1024 * 1024 * 1024, ge=1024)
    max_zip_ratio: int = Field(default=200, ge=1, le=10_000)
    #: Anidamiento de ZIP dentro de ZIP que se expande (0 = no expandir ninguno).
    max_zip_depth: int = Field(default=1, ge=0, le=3)
    #: Descarga segura por URL: tiempo, tamaño y redirecciones.
    url_timeout_seconds: float = Field(default=20.0, gt=0.5, le=300)
    max_url_bytes: int = Field(default=64 * 1024 * 1024, ge=1024)
    max_url_redirects: int = Field(default=5, ge=0, le=20)
    #: Texto pegado: tope de tamaño para no convertir un pegado en un lote gigante.
    max_paste_bytes: int = Field(default=4 * 1024 * 1024, ge=1024)
    #: Cuánto puede leer cada extractor de un fichero. El texto, el HTML y el CSV se leen hasta este
    #: tope (si hay más, se lee el principio y se avisa); el JSON hay que parsearlo entero, así que
    #: si no cabe se declara en lugar de cargarlo en memoria; una imagen mayor que su tope se
    #: conserva sin describirla. Sin estos límites, un fichero válido de 512 MiB agotaba la memoria.
    max_text_bytes: int = Field(default=32 * 1024 * 1024, ge=1024)
    max_json_bytes: int = Field(default=8 * 1024 * 1024, ge=1024)
    max_image_bytes: int = Field(default=256 * 1024 * 1024, ge=1024)

    @field_validator("data_dir", mode="after")
    @classmethod
    def _resolve_data_dir(cls, value: Path) -> Path:
        resolved = value.expanduser()
        if not resolved.is_absolute():
            resolved = project_root() / resolved
        resolved = resolved.resolve()
        if resolved.exists() and not resolved.is_dir():
            raise ConfigurationError(
                f"OPOFUENTE_DATA_DIR apunta a un fichero, no a un directorio: {resolved.name}"
            )
        return resolved

    @field_validator("tesseract_path", "tesseract_tessdata", mode="after")
    @classmethod
    def _resolve_tesseract_path(cls, value: Path | None) -> Path | None:
        if value is None:
            return None
        resolved = value.expanduser()
        if not resolved.is_absolute():
            resolved = project_root() / resolved
        return resolved

    @field_validator(
        "llm_base_url",
        "llm_model",
        "embedding_base_url",
        "embedding_model",
        "tesseract_path",
        "tesseract_tessdata",
        "public_base_url",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("host", mode="after")
    @classmethod
    def _require_loopback(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in LOOPBACK_HOSTS:
            raise ConfigurationError(
                "OPOFUENTE_HOST debe ser loopback "
                f"({', '.join(sorted(LOOPBACK_HOSTS))}); recibido {value!r}. "
                "Publicar en LAN o nube exige un proyecto de autenticación aparte "
                "(09_SECURITY-PRIVACY-AND-RIGHTS §2)."
            )
        return normalized

    @model_validator(mode="after")
    def _require_llm_endpoint(self) -> Settings:
        if self.llm_provider != "disabled":
            missing = [
                name
                for name, value in (
                    ("OPOFUENTE_LLM_BASE_URL", self.llm_base_url),
                    ("OPOFUENTE_LLM_MODEL", self.llm_model),
                )
                if not value
            ]
            if missing:
                raise ConfigurationError(
                    f"llm_provider={self.llm_provider!r} exige {' y '.join(missing)}"
                )
        return self

    @model_validator(mode="after")
    def _refuse_features_without_legal_frame(self) -> Settings:
        """La analítica y los pagos exigen el marco legal encendido, y no es un capricho de orden.

        La analítica pide **consentimiento**, y el consentimiento se pide y se guarda con las rutas
        del §9: encenderla sin ellas dejaría un contador que no puede contar nada porque no hay
        ninguna forma de que nadie acepte. Y los pagos meterían datos personales en un tercero que
        la política de privacidad tiene que declarar **antes** de que ocurra; sin página de
        privacidad, esa declaración no existe.
        """
        if self.analytics_enabled and not self.legal_enabled:
            raise ConfigurationError(
                "OPOFUENTE_ANALYTICS_ENABLED=1 exige OPOFUENTE_LEGAL_ENABLED=1: la analítica solo "
                "cuenta con consentimiento, y el consentimiento se pide y se guarda con las rutas "
                "legales. Sin ellas el contador no podría contar nunca."
            )
        if self.payments_enabled and not self.legal_enabled:
            raise ConfigurationError(
                "OPOFUENTE_PAYMENTS_ENABLED=1 exige OPOFUENTE_LEGAL_ENABLED=1: los datos "
                "personales que recibiría la pasarela tienen que estar declarados en la política "
                "de privacidad antes de que ocurran."
            )
        return self

    @model_validator(mode="after")
    def _refuse_mail_without_provider(self) -> Settings:
        """Sin proveedor de correo contratado, `mail_enabled` no puede estar encendido.

        No es prudencia: es que **no hay ningún proveedor implementado**. Encenderlo dejaría el
        enlace de recuperación creyendo que se ha enviado un correo que nadie ha enviado, y quien no
        puede entrar se quedaría esperando un mensaje que no va a llegar. Se falla al arrancar, con
        lo que hay que contratar, en lugar de fallar en silencio al recuperar la contraseña.
        """
        if self.mail_enabled:
            raise ConfigurationError(
                "OPOFUENTE_MAIL_ENABLED=1 exige un proveedor de correo contratado y no hay "
                "ninguno. Mientras no lo haya, deja el enlace de recuperación en "
                "datos/recovery/ (lo lee el titular) o contrata un servicio de correo y añade su "
                "integración."
            )
        return self

    @property
    def web_base_url(self) -> str:
        """Dónde vive la web, para componer enlaces absolutos (el de recuperación)."""
        if self.public_base_url:
            return self.public_base_url.rstrip("/")
        return self.cors_origins[0].rstrip("/") if self.cors_origins else "http://127.0.0.1:4173"

    @property
    def data_paths(self) -> DataPaths:
        return DataPaths.from_root(self.data_dir)

    @property
    def llm_api_key_configured(self) -> bool:
        """Indica si hay clave; nunca devuelve su valor."""
        return self.llm_api_key is not None and bool(self.llm_api_key.get_secret_value())

    @property
    def llm_destination(self) -> DestinationReason:
        """A dónde irían los fragmentos que se manderen al modelo de lenguaje (DEBT-001)."""
        return classify_provider(
            name="el modelo de lenguaje",
            provider=self.llm_provider,
            endpoint=self.llm_base_url,
        )

    @property
    def embeddings_destination(self) -> DestinationReason:
        """A dónde iría el texto que se mandara a embeddings, por separado del modelo (DEBT-001).

        Es la mitad del defecto que registró la deuda: antes había un booleano global que mezclaba
        los dos proveedores, así que un endpoint de embeddings remoto aparecía informado dentro del
        bloque del modelo de lenguaje.
        """
        return classify_provider(
            name="el proveedor de embeddings",
            provider=self.embedding_provider,
            endpoint=self.embedding_base_url,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Configuración del proceso, leída una sola vez."""
    return Settings()
