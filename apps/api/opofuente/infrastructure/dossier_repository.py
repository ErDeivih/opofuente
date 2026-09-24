"""Lectura del corpus para el dossier de un tema, y guardado de sus versiones (S13).

Dos responsabilidades, y las dos son de acceso a datos:

1. **Reunir los tramos que le llegan a un tema**: el tema y su subárbol, unidos por mapeos que no
estén
   rechazados. La condición de pertenencia es la misma que usa la búsqueda por ámbito
   (`search_repository`): el material puede estar asignado por su artefacto, por su representación,
   por
   la versión del documento, por una sección o por una cita concreta. Aquí se escribe una vez, y con
   una diferencia deliberada: **un mapeo de sección alcanza a los tramos de esa sección**, no a todo
   el
   documento (la búsqueda lo hacía al revés; se corrigió con una prueba que compara las dos).
2. **Guardar y leer versiones** del dossier. Una instantánea es lo que se leyó un día: se guarda
entera
   —el documento canónico del dominio— para que una versión anterior se pueda leer como se leyó.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import DossierVersionView
from opofuente.domain.dossier import PassageFacts, TopicDossier

#: Tramos citables de un tema y de su subárbol, con los mapeos que los sostienen.
#:
#: Tres decisiones que se leen en la consulta:
#:
#: - **la condición de pertenencia se escribe una sola vez**, como unión con `curriculum_mappings`:
#:   el material puede estar asignado al tema por su artefacto, por su representación, por la
#:   versión del documento, por una sección o por una cita concreta. Escribirla dos veces —una para
#:   filtrar y otra para contar— es como dos definiciones de «pertenece» acaban diciendo cosas
#:   distintas;
#: - **se agrupa por el tramo** para reunir en un solo campo los estados de mapeo que lo sostienen
#:   (`accepted`, `provisional`). Las demás columnas dependen de `s.id`, así que agrupar por él no
#:   elige valores al azar: son los del tramo;
#: - **se trae ordenado** (documento, versión, página, posición) aunque el dominio vuelva a ordenar:
#:   así el resultado es estable antes de agrupar y la consulta se puede comprobar a mano.
_TRAMOS_DEL_TEMA = """
WITH RECURSIVE ambito(node_id) AS (
    SELECT :node_id
    UNION ALL
    SELECT hijo.id FROM curriculum_nodes hijo JOIN ambito ON hijo.parent_id = ambito.node_id
)
SELECT s.id AS evidence_id,
       s.text AS text,
       s.normalized_text AS normalized,
       s.citation_label AS citation_label,
       s.page AS page,
       s.ordinal AS ordinal,
       sec.title AS section_title,
       d.id AS document_id,
       d.canonical_title AS document_title,
       d.document_type AS document_type,
       d.authority_tier AS authority_tier,
       v.id AS version_id,
       v.version_label AS version_label,
       v.status AS version_status,
       v.valid_from AS valid_from,
       v.valid_to AS valid_to,
       r.quality AS representation_quality,
       group_concat(DISTINCT m.status) AS mappings
FROM evidence_spans s
JOIN document_versions v ON v.id = s.document_version_id
JOIN logical_documents d ON d.id = v.logical_document_id
LEFT JOIN document_sections sec ON sec.id = s.section_id
LEFT JOIN extracted_representations r ON r.id = v.representation_id
JOIN curriculum_mappings m
     ON m.status <> 'rejected'
    AND m.curriculum_node_id IN (SELECT node_id FROM ambito)
    AND (
          (m.subject_type = 'document_version' AND m.subject_id = v.id)
       OR (m.subject_type = 'artifact' AND m.subject_id = v.artifact_id)
       OR (m.subject_type = 'representation' AND m.subject_id = v.representation_id)
       OR (m.subject_type = 'section' AND m.subject_id = s.section_id)
       OR (m.subject_type = 'evidence' AND m.subject_id = s.id)
    )
GROUP BY s.id
ORDER BY d.canonical_title, v.version_label, s.page, s.ordinal
"""

#: Mapeos vivos (no rechazados) que llegan al tema y a su subárbol, con su estado.
_MAPEOS_DEL_TEMA = """
WITH RECURSIVE ambito(node_id) AS (
    SELECT :node_id
    UNION ALL
    SELECT hijo.id FROM curriculum_nodes hijo JOIN ambito ON hijo.parent_id = ambito.node_id
)
SELECT m.status FROM curriculum_mappings m
WHERE m.curriculum_node_id IN (SELECT node_id FROM ambito)
  AND m.status <> 'rejected'
"""


class SqlAlchemyDossierRepository:
    """Tramos del tema y versiones guardadas del dossier."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # --- el corpus

    def node(self, node_id: str) -> tuple[str, str, int] | None:
        """`(path, title, depth)` del nodo, o `None` si no existe (la API responde 404)."""
        with self._session_factory() as session:
            fila = session.execute(
                text("SELECT path, title, depth FROM curriculum_nodes WHERE id = :node_id"),
                {"node_id": node_id},
            ).first()
        return None if fila is None else (str(fila[0]), str(fila[1]), int(fila[2]))

    def passages_for_node(self, node_id: str) -> tuple[PassageFacts, ...]:
        """Los tramos del tema y de su subárbol, con los mapeos que los sostienen."""
        with self._session_factory() as session:
            filas = session.execute(text(_TRAMOS_DEL_TEMA), {"node_id": node_id}).all()
        return tuple(_facts(fila) for fila in filas)

    def mappings_for_node(self, node_id: str) -> tuple[str, ...]:
        """Estados de los mapeos que llegan al tema y a su subárbol, sin los rechazados.

        Sirve para distinguir dos huecos que se parecen y no son lo mismo: **no tener material
        asignado** y **tener material que todavía no tiene nada que citar**.
        """
        with self._session_factory() as session:
            filas = session.execute(text(_MAPEOS_DEL_TEMA), {"node_id": node_id}).all()
        return tuple(str(fila[0]) for fila in filas)

    # --- las versiones del dossier

    def save_snapshot(
        self,
        *,
        node_id: str,
        dossier: TopicDossier,
        payload: str,
        now: datetime,
    ) -> tuple[str, bool]:
        """Guarda el dossier como versión. Devuelve `(id, creada)`.

        Es **idempotente por contenido**: el mismo dossier dos veces devuelve la versión que ya
        estaba, con `creada=False`. Se comprueba antes de insertar para poder decirlo, en vez de
        tragarse el conflicto de la clave única.
        """
        with self._session_factory() as session:
            existente = session.execute(
                text(
                    "SELECT id FROM dossier_snapshots "
                    "WHERE curriculum_node_id = :node_id AND content_hash = :hash"
                ),
                {"node_id": node_id, "hash": dossier.content_hash},
            ).first()
            if existente is not None:
                return (str(existente[0]), False)
            version_id = str(uuid4())
            session.execute(
                text(
                    "INSERT INTO dossier_snapshots (id, curriculum_node_id, content_hash, "
                    "built_at, created_at, sources_count, passages_count, payload_json) "
                    "VALUES (:id, :node_id, :hash, :built_at, :created_at, :sources, :passages, "
                    ":payload)"
                ),
                {
                    "id": version_id,
                    "node_id": node_id,
                    "hash": dossier.content_hash,
                    "built_at": dossier.generated_at,
                    "created_at": now,
                    "sources": dossier.sources_total,
                    "passages": dossier.passages_total,
                    "payload": payload,
                },
            )
            session.commit()
        return (version_id, True)

    def latest_snapshot_id(self, node_id: str) -> str | None:
        with self._session_factory() as session:
            fila = session.execute(
                text(
                    "SELECT id FROM dossier_snapshots WHERE curriculum_node_id = :node_id "
                    "ORDER BY built_at DESC, created_at DESC, id DESC LIMIT 1"
                ),
                {"node_id": node_id},
            ).first()
        return None if fila is None else str(fila[0])

    def snapshot(self, node_id: str, version_id: str) -> tuple[str, datetime, str] | None:
        """`(payload, built_at, content_hash)` de una versión, si es de ese tema."""
        with self._session_factory() as session:
            fila = session.execute(
                text(
                    "SELECT payload_json, built_at, content_hash FROM dossier_snapshots "
                    "WHERE id = :id AND curriculum_node_id = :node_id"
                ),
                {"id": version_id, "node_id": node_id},
            ).first()
        if fila is None:
            return None
        return (str(fila[0]), _momento(fila[1]), str(fila[2]))

    def snapshots(self, node_id: str) -> tuple[DossierVersionView, ...]:
        """Las versiones guardadas, de la más nueva a la más antigua, **sin** su contenido."""
        with self._session_factory() as session:
            filas = session.execute(
                text(
                    "SELECT id, content_hash, built_at, sources_count, passages_count "
                    "FROM dossier_snapshots WHERE curriculum_node_id = :node_id "
                    "ORDER BY built_at DESC, created_at DESC, id DESC"
                ),
                {"node_id": node_id},
            ).all()
        return tuple(
            DossierVersionView(
                id=str(fila[0]),
                content_hash=str(fila[1]),
                built_at=_momento(fila[2]),
                sources_count=int(fila[3]),
                passages_count=int(fila[4]),
            )
            for fila in filas
        )


def _momento(valor: object) -> datetime:
    if isinstance(valor, datetime):
        return valor
    return datetime.fromisoformat(str(valor))


def _facts(fila: Any) -> PassageFacts:
    return PassageFacts(
        evidence_id=str(fila.evidence_id),
        text=str(fila.text),
        normalized=str(fila.normalized),
        citation_label=None if fila.citation_label is None else str(fila.citation_label),
        page=None if fila.page is None else int(fila.page),
        section_title=None if fila.section_title is None else str(fila.section_title),
        ordinal=int(fila.ordinal),
        document_id=str(fila.document_id),
        document_title=str(fila.document_title),
        document_type=str(fila.document_type),
        authority_tier=None if fila.authority_tier is None else str(fila.authority_tier),
        version_id=str(fila.version_id),
        version_label=None if fila.version_label is None else str(fila.version_label),
        version_status=str(fila.version_status),
        quality=None if fila.representation_quality is None else str(fila.representation_quality),
        mappings=tuple(sorted({parte for parte in str(fila.mappings or "").split(",") if parte})),
        valid_from=fila.valid_from,
        valid_to=fila.valid_to,
    )
