"""Configuración efectiva de OpoFuente.

Prioridad (02_ARCHITECTURE §8): valores seguros por defecto -> fichero local (`.env`) ->
variables de entorno. Ningún secreto de este módulo se expone por la API ni se registra en logs.

Regla dura: el host debe ser loopback. Un host público falla al arrancar
(09_SECURITY-PRIVACY-AND-RIGHTS §2).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

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

    @classmethod
    def from_root(cls, root: Path) -> DataPaths:
        return cls(
            root=root,
            artifacts=root / "artifacts",
            extracted=root / "extracted",
            qdrant=root / "qdrant",
            exports=root / "exports",
            backups=root / "backups",
            logs=root / "logs",
            tmp=root / "tmp",
        )

    @property
    def database(self) -> Path:
        return self.root / "opofuente.sqlite3"

    def ensure_directories(self) -> None:
        """Crea el árbol de datos. Idempotente; no toca ningún original del usuario."""
        for directory in (
            self.root,
            self.artifacts,
            self.extracted,
            self.qdrant,
            self.exports,
            self.backups,
            self.logs,
            self.tmp,
        ):
            directory.mkdir(parents=True, exist_ok=True)


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
