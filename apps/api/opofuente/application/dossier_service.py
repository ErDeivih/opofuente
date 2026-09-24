"""El dossier del tema: se calcula, se sirve y se archiva (S13).

El servicio no sabe de SQL ni de HTTP, y hace tres cosas:

1. **montar** el dossier desde el corpus (los tramos que le llegan al nodo), con el reloj del
sistema
   como fecha de lectura: el dominio decide qué es citable y qué es un hueco;
2. **archivar** una versión cuando se pide: guarda el documento canónico tal cual, y repetir la
misma
   lectura no crea una versión nueva (la huella de contenido lo impide);
3. **leer** una versión anterior, tal como se leyó, y decir cuál es la anterior a la actual.

Decisión que se ve en la firma de `build`: devuelve `None` cuando el nodo no existe, para que la API
pueda responder 404 con el identificador que le han dado, en vez de un dossier vacío que parecería
un
tema sin material.
"""

from __future__ import annotations

import json
from datetime import date, datetime

from opofuente.application.ports import Clock, DossierRepository
from opofuente.application.read_models import DossierVersionView
from opofuente.domain.dossier import (
    TopicDossier,
    build_dossier,
    dossier_document,
    dossier_from_document,
)


class DossierService:
    """El tema como unidad de lectura: qué dice el corpus de él, citado y declarado."""

    def __init__(self, repository: DossierRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def build(self, node_id: str) -> TopicDossier | None:
        """El dossier de hoy. `None` si el nodo no existe."""
        nodo = self._repository.node(node_id)
        if nodo is None:
            return None
        path, title, depth = nodo
        momento = self._clock.now()
        dossier = build_dossier(
            node_id=node_id,
            path=path,
            title=title,
            depth=depth,
            generated_at=momento,
            facts=self._repository.passages_for_node(node_id),
            mappings_total=len(self._repository.mappings_for_node(node_id)),
            reference_date=_fecha_de_referencia(momento),
        )
        return self._con_versiones(dossier)

    def archive(self, node_id: str) -> tuple[TopicDossier, bool] | None:
        """Archiva la lectura de ahora como versión del dossier. `(dossier, creada)`.

        Si el contenido no ha cambiado desde la última vez, devuelve la versión que ya estaba con
        `creada=False`: pedir dos veces lo mismo no ensucia el historial, y quien mira puede decir
        «no ha cambiado nada» en lugar de «hay una versión nueva».
        """
        dossier = self.build(node_id)
        if dossier is None:
            return None
        # La versión que había **antes** de archivar es la que era la última: es con la que se va a
        # poder comparar la nueva, y por eso se guarda en la nueva (no la anterior de la anterior).
        anterior = dossier.version_id
        payload = json.dumps(
            dossier_document(dossier), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        version_id, creada = self._repository.save_snapshot(
            node_id=node_id, dossier=dossier, payload=payload, now=self._clock.now()
        )
        return (_con_version(dossier, version_id, anterior), creada)

    def versions(self, node_id: str) -> tuple[DossierVersionView, ...] | None:
        """Las versiones guardadas, de la más nueva a la más antigua. `None` si el nodo no está."""
        if self._repository.node(node_id) is None:
            return None
        return self._repository.snapshots(node_id)

    def version(self, node_id: str, version_id: str) -> TopicDossier | None:
        """Una versión guardada, leída tal como se leyó. `None` si no es de ese tema."""
        guardado = self._repository.snapshot(node_id, version_id)
        if guardado is None:
            return None
        payload, _built_at, _hash = guardado
        dossier = dossier_from_document(json.loads(payload))
        anterior = self._anterior_a(node_id, version_id)
        return _con_version(dossier, version_id, anterior)

    def _con_versiones(self, dossier: TopicDossier) -> TopicDossier:
        """Marca el dossier con la última versión guardada (si hay) y con su anterior."""
        actual = self._repository.latest_snapshot_id(dossier.node_id)
        if actual is None:
            return dossier
        return _con_version(dossier, actual, self._anterior_a(dossier.node_id, actual))

    def _anterior_a(self, node_id: str, version_id: str) -> str | None:
        """La versión inmediatamente anterior a esta, para poder comparar una con otra."""
        anteriores = [
            version.id
            for version in self._repository.snapshots(node_id)
            if version.id != version_id
        ]
        return anteriores[0] if anteriores else None


def _con_version(
    dossier: TopicDossier, version_id: str | None, anterior: str | None
) -> TopicDossier:
    return TopicDossier(
        node_id=dossier.node_id,
        path=dossier.path,
        title=dossier.title,
        depth=dossier.depth,
        generated_at=dossier.generated_at,
        sources=dossier.sources,
        holes=dossier.holes,
        accepted_sources=dossier.accepted_sources,
        provisional_sources=dossier.provisional_sources,
        content_hash=dossier.content_hash,
        version_id=version_id,
        previous_version_id=anterior,
    )


def _fecha_de_referencia(momento: datetime) -> date:
    """La fecha con la que se decide la vigencia de las versiones: la del día de la lectura."""
    return momento.date()
