"""Almacén de artefactos por SHA-256: originales inmutables y escritura atómica.

Cómo se copia (02_ARCHITECTURE §5):

1. se lee el fichero de origen por trozos, calculando el sha256 y el tamaño mientras se escribe en
   `data/tmp/<uuid>.part`;
2. se hace `fsync` y se cierra;
3. si el destino `data/artifacts/sha256/ab/cd/<hash>` ya existe, se descarta el temporal y se
   reutiliza el artefacto (dos ficheros iguales con nombres distintos son **un** artefacto);
4. si no existe, se crea el directorio y se mueve con `os.replace` (atómico en el mismo volumen).

El archivo de origen **nunca** se modifica: solo se abre en lectura.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import uuid4

from opofuente.config import DataPaths
from opofuente.domain.artifacts import Sha256, StoredArtifact
from opofuente.domain.errors import InvariantViolationError
from opofuente.infrastructure.safe_paths import resolve_within

CHUNK_BYTES = 1024 * 1024


class ArtifactStore:
    def __init__(self, paths: DataPaths, *, chunk_bytes: int = CHUNK_BYTES) -> None:
        self._paths = paths
        self._chunk_bytes = chunk_bytes

    def path_for(self, digest: Sha256) -> Path:
        """Ruta absoluta del artefacto, validada dentro del directorio de datos."""
        return resolve_within(self._paths.root, self._paths.artifacts / digest.storage_key)

    def exists(self, digest: Sha256) -> bool:
        return self.path_for(digest).is_file()

    def store_file(self, source: Path) -> StoredArtifact:
        """Copia un fichero al almacén por contenido. No toca el original."""
        if not source.is_file():
            raise InvariantViolationError("solo se pueden almacenar ficheros regulares")

        self._paths.ensure_directories()
        temporary = resolve_within(self._paths.root, self._paths.tmp / f"ingest-{uuid4().hex}.part")
        digest = hashlib.sha256()
        size = 0
        try:
            with source.open("rb") as stream, temporary.open("wb") as target:
                while True:
                    chunk = stream.read(self._chunk_bytes)
                    if not chunk:
                        break
                    digest.update(chunk)
                    size += len(chunk)
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
            sha = Sha256(digest.hexdigest())
            target_path = self.path_for(sha)
            if target_path.is_file():
                temporary.unlink(missing_ok=True)
                return StoredArtifact(
                    sha256=sha,
                    size_bytes=size,
                    storage_key=sha.storage_key,
                    reused=True,
                )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temporary, target_path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
        return StoredArtifact(
            sha256=sha, size_bytes=size, storage_key=sha.storage_key, reused=False
        )

    def verify(self, digest: Sha256) -> bool:
        """Recalcula el hash del contenido almacenado. Se usa en diagnóstico y en pruebas."""
        path = self.path_for(digest)
        if not path.is_file():
            return False
        computed = hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(self._chunk_bytes)
                if not chunk:
                    break
                computed.update(chunk)
        return computed.hexdigest() == digest.value
