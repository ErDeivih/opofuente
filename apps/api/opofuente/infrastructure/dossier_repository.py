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

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import DossierVersionView
from opofuente.domain.dossier import PassageFacts, TopicDossier

#: Tramos citables de un tema y de su subárbol, con los mapeos que los sostienen.
#:
#: **Por qué son dos consultas y no una** (medido el 5 de octubre de 2026): la versión de una sola
#: consulta unía `evidence_spans` con `curriculum_mappings` mediante un `OR` de cinco condiciones
#: —artefacto, representación, versión, sección o cita—, y ese `OR` impedía usar los índices:
#: SQLite acababa comparando cada tramo del tema con las 39.242 filas de mapeos. El tema I.1
#: tardaba **53,6 s** y el II.1 **51,6 s**, y de ese tiempo el cálculo en Python eran 0,16 s y
#: 0,06 s. Con el `OR` fuera de la consulta grande:
#:
#: 1. se leen los mapeos del ámbito, que es una lectura indexada por nodo (`ix_mapping_node`) y son
#:    unos miles de filas;
#: 2. se leen los tramos filtrando por los sujetos de esos mapeos, y aquí cada condición **sí** usa
#:    su índice (`ix_evidence_version`, `ix_evidence_section`, `ix_versions_artifact`, la clave del
#:    tramo…);
#: 3. los estados de mapeo de cada tramo se emparejan en memoria, que es donde salen gratis.
#:
#: El resultado es el mismo —las mismas filas y los mismos estados, que es lo que fija una prueba—
#: y por eso la condición de pertenencia se sigue escribiendo **una sola vez**, en la primera
#: consulta.
_MAPEOS_DEL_AMBITO = """
WITH RECURSIVE ambito(node_id) AS (
    SELECT :node_id
    UNION ALL
    SELECT hijo.id FROM curriculum_nodes hijo JOIN ambito ON hijo.parent_id = ambito.node_id
)
SELECT m.subject_type AS tipo, m.subject_id AS sujeto, m.status AS estado
FROM curriculum_mappings m
WHERE m.curriculum_node_id IN (SELECT node_id FROM ambito)
  AND m.status <> 'rejected'
"""

#: Las versiones de los artefactos y las representaciones que sostienen el tema.
#:
#: Un mapeo de artefacto o de representación alcanza a **todas las versiones** de ese artefacto o
#: esa representación, así que se traducen a versiones antes de pedir los tramos: la tabla de
#: versiones tiene 5.927 filas y sus dos columnas están indexadas (`ix_versions_artifact`), mientras
#: que
#: `representation_id` **no** tiene índice y dejarlo en la consulta grande costaba 2,6 s por tema
#: (medido el 5 de octubre de 2026: 8.145 tramos de I.1). Traducido, la consulta de tramos solo
#: necesita mirar `v.id`, que es su clave.
_VERSIONES_DE_LOS_SUJETOS = {
    "artifact": """
        SELECT v.id FROM document_versions v WHERE v.artifact_id IN :ids
    """,
    "representation": """
        SELECT v.id FROM document_versions v WHERE v.representation_id IN :ids
    """,
}

#: Los tramos de las versiones, las secciones y las citas que sostienen el tema.
#:
#: Tres condiciones y las tres con índice: `ix_evidence_version` para las versiones,
#: `ix_evidence_section` para las secciones y la clave del tramo para las citas. Se piden también
#: `artifact_id`, `representation_id` y `section_id` porque son las claves con las que después se
#: busca el estado de mapeo de cada tramo: sin ellas habría que volver a la base por cada uno.
_TRAMOS_DE_LOS_SUJETOS = """
SELECT s.id AS evidence_id,
       s.text AS text,
       s.normalized_text AS normalized,
       s.citation_label AS citation_label,
       s.page AS page,
       s.ordinal AS ordinal,
       s.section_id AS section_id,
       sec.title AS section_title,
       d.id AS document_id,
       d.canonical_title AS document_title,
       d.document_type AS document_type,
       d.authority_tier AS authority_tier,
       v.id AS version_id,
       v.version_label AS version_label,
       v.status AS version_status,
       v.artifact_id AS artifact_id,
       v.representation_id AS representation_id,
       v.valid_from AS valid_from,
       v.valid_to AS valid_to,
       r.quality AS representation_quality
FROM evidence_spans s
JOIN document_versions v ON v.id = s.document_version_id
JOIN logical_documents d ON d.id = v.logical_document_id
LEFT JOIN document_sections sec ON sec.id = s.section_id
LEFT JOIN extracted_representations r ON r.id = v.representation_id
WHERE v.id IN :versiones
   OR s.section_id IN :secciones
   OR s.id IN :citas
ORDER BY d.canonical_title, v.version_label, s.page, s.ordinal
"""

#: Lo que se pide de una vez. SQLite admite listas mucho más largas, pero un lote acotado mantiene
#: la consulta dentro de lo que el planificador resuelve bien y no depende del tope de parámetros.
LOTE_DE_SUJETOS = 400

#: La consulta de tramos con sus listas declaradas como tales: sin `expanding`, SQLAlchemy manda la
#: lista como un único parámetro y SQLite no sabe qué hacer con ella.
_TRAMOS_DE_LOS_SUJETOS_SQL = text(_TRAMOS_DE_LOS_SUJETOS).bindparams(
    bindparam("versiones", expanding=True),
    bindparam("secciones", expanding=True),
    bindparam("citas", expanding=True),
)

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
        """Los tramos del tema y de su subárbol, con los mapeos que los sostienen.

        Dos consultas y un emparejamiento en memoria (ver `_MAPEOS_DEL_AMBITO`): la primera lee los
        mapeos del ámbito, la segunda los tramos de sus sujetos —traducidos antes los artefactos y
        las representaciones a sus versiones— y la tercera, en memoria, pone a cada tramo los
        estados que lo sostienen. El resultado es el mismo que el de la consulta única que había
        antes, y con él se hace en una fracción del tiempo (lo fija una prueba que compara las dos).
        """
        with self._session_factory() as session:
            mapeos = session.execute(text(_MAPEOS_DEL_AMBITO), {"node_id": node_id}).all()
            if not mapeos:
                return ()
            estados: dict[tuple[str, str], set[str]] = {}
            sujetos: dict[str, list[str]] = {
                "document_version": [],
                "artifact": [],
                "representation": [],
                "section": [],
                "evidence": [],
            }
            for fila in mapeos:
                tipo = str(fila.tipo)
                sujeto = str(fila.sujeto)
                if tipo not in sujetos:
                    continue
                estados.setdefault((tipo, sujeto), set()).add(str(fila.estado))
                sujetos[tipo].append(sujeto)
            for tipo, identificadores in sujetos.items():
                sujetos[tipo] = sorted(set(identificadores))

            # Un mapeo de artefacto o de representación alcanza a todas sus versiones: se traducen
            # aquí, que es una lectura pequeña e indexada, para que la consulta de tramos solo tenga
            # que mirar `v.id` (su clave) y no columnas sin índice.
            versiones = set(sujetos["document_version"])
            for tipo, plantilla in _VERSIONES_DE_LOS_SUJETOS.items():
                consulta = text(plantilla).bindparams(bindparam("ids", expanding=True))
                for tanda in _lotes_de_uno(sujetos[tipo]):
                    versiones.update(
                        str(fila[0]) for fila in session.execute(consulta, {"ids": tanda}).all()
                    )
            sujetos["document_version"] = sorted(versiones)

            # Se pregunta por los sujetos a trozos: así la consulta no depende del tope de
            # parámetros de SQLite ni el planificador se atraganta con miles de identificadores.
            hechos: dict[str, PassageFacts] = {}
            for lote in _lotes(sujetos):
                filas = session.execute(
                    _TRAMOS_DE_LOS_SUJETOS_SQL,
                    {
                        "versiones": lote["document_version"],
                        "secciones": lote["section"],
                        "citas": lote["evidence"],
                    },
                ).all()
                for fila in filas:
                    hecho = _facts(fila, estados)
                    anterior = hechos.get(hecho.evidence_id)
                    if anterior is None:
                        hechos[hecho.evidence_id] = hecho
                        continue
                    # Un mismo tramo puede salir en dos lotes o sostenerlo dos mapeos: se une, que
                    # es lo que hacía `group_concat(DISTINCT …)`.
                    hechos[hecho.evidence_id] = replace(
                        anterior,
                        mappings=tuple(sorted(set(anterior.mappings) | set(hecho.mappings))),
                    )
        return tuple(sorted(hechos.values(), key=_orden_de_lectura))

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


def _facts(fila: Any, estados: dict[tuple[str, str], set[str]]) -> PassageFacts:
    """Un tramo, con los estados de los mapeos que lo sostienen puestos en memoria.

    Es lo que antes hacía `group_concat(DISTINCT m.status)` dentro de la consulta: los estados del
    tramo son la unión de los que lo alcanzan por su versión, su artefacto, su representación, su
    sección o la cita misma.
    """
    sostienen: set[str] = set()
    for tipo, sujeto in (
        ("document_version", str(fila.version_id)),
        ("artifact", None if fila.artifact_id is None else str(fila.artifact_id)),
        ("representation", None if fila.representation_id is None else str(fila.representation_id)),
        ("section", None if fila.section_id is None else str(fila.section_id)),
        ("evidence", str(fila.evidence_id)),
    ):
        if sujeto is not None:
            sostienen |= estados.get((tipo, sujeto), set())
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
        mappings=tuple(sorted(sostienen)),
        valid_from=fila.valid_from,
        valid_to=fila.valid_to,
    )


def _lotes_de_uno(identificadores: Sequence[str]) -> list[list[str]]:
    """Parte una lista de identificadores en lotes, sin lotes vacíos (`IN ()` no es SQL válido)."""
    tamano = max(1, LOTE_DE_SUJETOS)
    return [
        list(identificadores[inicio : inicio + tamano])
        for inicio in range(0, len(identificadores), tamano)
    ]


def _lotes(sujetos: dict[str, list[str]]) -> list[dict[str, list[str]]]:
    """Parte los sujetos en lotes que comparten una misma «tanda» de identificadores.

    Cada lote lleva, de cada tipo, los identificadores de esa tanda; los tipos con menos
    identificadores se completan con un testigo que no casa con nada (`""`), porque SQLite no admite
    una lista vacía en un `IN`.
    """
    tamano = max(1, LOTE_DE_SUJETOS)
    cuantos = max((len(lista) for lista in sujetos.values()), default=0)
    if cuantos == 0:
        return []
    lotes: list[dict[str, list[str]]] = []
    for inicio in range(0, cuantos, tamano):
        lote = {tipo: (lista[inicio : inicio + tamano] or [""]) for tipo, lista in sujetos.items()}
        lotes.append(lote)
    return lotes


def _orden_de_lectura(hecho: PassageFacts) -> tuple[Any, ...]:
    """El mismo orden de la consulta: documento, versión, página, posición.

    Se ordena también en memoria porque los tramos llegan en lotes y, sin esto, el dossier podría
    salir con los documentos intercalados según el tamaño de cada tanda. Los nulos van primero, como
    en SQLite.
    """
    return (
        (0, "") if hecho.document_title is None else (1, hecho.document_title),
        (0, "") if hecho.version_label is None else (1, hecho.version_label),
        (0, -1) if hecho.page is None else (1, hecho.page),
        hecho.ordinal,
    )
