"""Repositorio de la biblioteca (S05): documentos, versiones, secciones, evidencias y colecciones.

Lo que decide este repositorio, y por qué:

- **Promocionar es explícito y idempotente**: el mismo artefacto no se promociona dos veces al mismo
  documento (lo impide la base y lo comprueba el código devolviendo la versión que ya existía). Se
  puede promocionar a un documento nuevo o **añadir una versión a uno existente**, que es como se
  representa «la misma obra, otro fichero».
- **Las secciones y las evidencias salen de la representación**, no se inventan: S03 ya guardó
  secciones con sus offsets, así que aquí se copian a `document_sections` y su texto se trocea en
  evidencias citables con su página y su etiqueta: **todo** el texto, sin perder lo que pasa del
  tope de una cita.
- **Aceptar y sustituir son promociones críticas**: exigen que alguien lo pida, dejan su evento de
  auditoría y **no borran la versión antigua** (queda `superseded`, con su contenido intacto).
- **Los derechos no se inventan**: si no se indica código, la versión nace sin derechos revisados, y
  eso es «restringido» en todo lo que se sirve hacia fuera.
"""

from __future__ import annotations

import json
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Select, delete, func, literal, or_, select
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, Session, sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from opofuente.application.library_models import (
    ArtifactFile,
    CollectionView,
    DocumentDetail,
    DocumentPage,
    DocumentView,
    EvidenceView,
    PromotionOutcome,
    RightsView,
    SectionDiff,
    SectionView,
    VersionDetail,
    VersionDiff,
    VersionText,
    VersionView,
)
from opofuente.domain.documents import VersionStatus, diff_versions, document_section_type
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.evidence import MAX_EVIDENCE_CHARS, evidence_cuts, uncovered_ranges
from opofuente.infrastructure.db_models import (
    ArtifactOriginRecord,
    AuditEventRecord,
    CollectionItemRecord,
    CollectionRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    DocumentSectionRecord,
    DocumentVersionRecord,
    EvidenceSpanRecord,
    ExtractedRepresentationRecord,
    IngestionItemRecord,
    ItemRepresentationRecord,
    LogicalDocumentRecord,
    RightsStatusRecord,
    SourceArtifactRecord,
)
from opofuente.infrastructure.representation_store import RepresentationStore

#: Cuánto texto se lee de la representación para sacar evidencias: **entera**. La representación ya
#: está acotada al extraerla (`max_representation_chars`), y leer menos dejaba sin citar todo lo que
#: venía después (antes se leían 400.000 caracteres y el resto se perdía).
MAX_EVIDENCE_TEXT_CHARS = 1_000_000_000


def _new_id() -> str:
    return str(uuid4())


def _warnings(representacion: ExtractedRepresentationRecord) -> tuple[str, ...]:
    """Avisos de la extracción, tal y como se guardaron. Un JSON ilegible no rompe la lectura."""
    if not representacion.warnings_json:
        return ()
    try:
        bruto = json.loads(representacion.warnings_json)
    except json.JSONDecodeError:
        return ()
    if not isinstance(bruto, list):
        return ()
    return tuple(str(aviso) for aviso in bruto)


def _quality_rank(valor: str | None) -> int:
    orden = {"good": 0, "usable_with_warnings": 1, "ocr_unreviewed": 2, "poor": 3}
    return orden.get(valor or "", 4)


def _int(valor: object, por_defecto: int = 0) -> int:
    """Entero a partir de lo que venga en el JSON de secciones, con valor por defecto."""
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else por_defecto


def _opt_int(valor: object) -> int | None:
    """Entero o nada: una página que no consta se queda sin página, no en cero."""
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else None


def _str(valor: object) -> str:
    """Texto a partir de lo que venga en el JSON, cadena vacía si no es texto."""
    return valor if isinstance(valor, str) else ""


def _opt_str(valor: object) -> str | None:
    """Texto o nada."""
    return valor if isinstance(valor, str) and valor else None


class SqlAlchemyDocumentRepository:
    """Biblioteca sobre SQLite: promoción, versiones, secciones, evidencias y colecciones."""

    def __init__(self, session_factory: sessionmaker[Session], store: RepresentationStore) -> None:
        self._session_factory = session_factory
        self._store = store

    # ------------------------------------------------------------------ promoción

    def promote_artifact(
        self,
        artifact_id: str,
        *,
        now: datetime,
        document_id: str | None = None,
        title: str | None = None,
        document_type: str = "unknown",
        owner_scope: str = "private_user",
        authority_tier: str | None = None,
        canonical_identifier: str | None = None,
        version_label: str | None = None,
        rights_code: str | None = None,
        official_url: str | None = None,
        actor: str = "local",
    ) -> PromotionOutcome:
        """Convierte un artefacto copiado en un documento con su versión, o lo dice y no lo hace."""
        with self._session_factory() as session:
            artefacto = session.get(SourceArtifactRecord, artifact_id)
            if artefacto is None:
                return PromotionOutcome(
                    document_id=None,
                    version_id=None,
                    created_document=False,
                    created_version=False,
                    reason="El artefacto no existe: no hay nada que promocionar",
                )

            representacion = self._best_representation(session, artifact_id)
            derechos = self._rights(session, rights_code)

            documento: LogicalDocumentRecord | None = None
            if document_id is not None:
                documento = session.get(LogicalDocumentRecord, document_id)
                if documento is None:
                    return PromotionOutcome(
                        document_id=None,
                        version_id=None,
                        created_document=False,
                        created_version=False,
                        reason="El documento indicado no existe",
                    )
                ya = self._existing_version(session, documento.id, artifact_id)
                if ya is not None:
                    return PromotionOutcome(
                        document_id=documento.id,
                        version_id=ya.id,
                        created_document=False,
                        created_version=False,
                    )
            else:
                # Sin documento indicado, si el artefacto ya es versión de alguna obra, se devuelve
                # esa versión: promocionar dos veces no puede crear dos documentos iguales.
                existente = self._version_of_artifact(session, artifact_id)
                if existente is not None:
                    return PromotionOutcome(
                        document_id=existente.logical_document_id,
                        version_id=existente.id,
                        created_document=False,
                        created_version=False,
                    )

            creado_documento = False
            if documento is None:
                titulo = (title or self._label_of(session, artifact_id) or "").strip()
                if not titulo:
                    return PromotionOutcome(
                        document_id=None,
                        version_id=None,
                        created_document=False,
                        created_version=False,
                        reason="Un documento necesita título: no se puede promocionar sin él",
                    )
                documento = LogicalDocumentRecord(
                    id=_new_id(),
                    canonical_title=titulo,
                    document_type=document_type,
                    authority_tier=authority_tier,
                    owner_scope=owner_scope,
                    canonical_identifier=canonical_identifier,
                    created_at=now,
                    updated_at=now,
                )
                session.add(documento)
                session.flush()
                creado_documento = True

            version = DocumentVersionRecord(
                id=_new_id(),
                logical_document_id=documento.id,
                artifact_id=artifact_id,
                representation_id=representacion.id if representacion is not None else None,
                version_label=version_label,
                status=VersionStatus.CANDIDATE.value,
                supersedes_id=None,
                rights_status_id=derechos.id if derechos is not None else None,
                official_url=official_url,
                content_hash=artefacto.sha256,
                created_at=now,
            )
            session.add(version)
            session.flush()

            secciones, evidencias = self._derive_structure(session, version, representacion, now)
            self._audit(
                session,
                actor=actor,
                action="document.promoted",
                object_type="document_version",
                object_id=version.id,
                before={},
                after={
                    "document_id": documento.id,
                    "artifact_id": artifact_id,
                    "sections": secciones,
                    "evidence": evidencias,
                },
                now=now,
            )
            session.commit()
            return PromotionOutcome(
                document_id=documento.id,
                version_id=version.id,
                created_document=creado_documento,
                created_version=True,
            )

    def _derive_structure(
        self,
        session: Session,
        version: DocumentVersionRecord,
        representacion: ExtractedRepresentationRecord | None,
        now: datetime,
    ) -> tuple[int, int]:
        """Copia la estructura que S03 ya extrajo y trocea **todo** su texto en evidencias citables.

        Cada sección produce tantas evidencias como hagan falta para que ninguna pase del tope, y el
        texto que no cae en ninguna sección se cubre con evidencias propias (ver
        `opofuente.domain.evidence`).
        """
        if representacion is None:
            return 0, 0
        # Las secciones de S03 guardan **offsets** sobre el texto de la representacion, no el texto:
        # la evidencia se recorta de ahi. Sin el texto no hay nada que citar y se dice con un cero.
        texto_completo = self._read_text(representacion)
        secciones = self._parse_sections(representacion.sections_json)
        creadas = 0
        evidencias = 0
        cubiertos: list[tuple[int, int]] = []
        # Sección más cercana por delante de cada offset: da etiqueta y página a los huecos.
        anclas: list[tuple[int, DocumentSectionRecord]] = []
        for indice, seccion in enumerate(secciones, start=1):
            registro = DocumentSectionRecord(
                id=_new_id(),
                document_version_id=version.id,
                parent_id=None,
                section_type=document_section_type(_str(seccion.get("section_type"))).value,
                label=_opt_str(seccion.get("label")),
                title=_opt_str(seccion.get("title")),
                position=indice,
                page_start=_opt_int(seccion.get("page_start")),
                page_end=_opt_int(seccion.get("page_end")),
                char_start=_int(seccion.get("char_start")),
                char_end=_int(seccion.get("char_end")),
                ordinal=indice,
            )
            session.add(registro)
            session.flush()
            creadas += 1
            inicio, fin = registro.char_start, registro.char_end
            cubiertos.append((inicio, fin))
            anclas.append((inicio, registro))
            # Una sección larga produce **varias** evidencias: antes producía una recortada a 1.200
            # caracteres y el resto del texto se perdía (§4.1 del traspaso de octubre de 2026).
            for corte in evidence_cuts(texto_completo, inicio, fin):
                evidencias += 1
                session.add(
                    self._evidence(
                        version,
                        representacion,
                        texto_completo,
                        corte,
                        evidencias,
                        now,
                        seccion=registro,
                    )
                )
        # El texto que no cae en ninguna sección también se cita: el cuerpo de un Markdown cuyas
        # secciones solo eran los encabezados, o lo que quedaba tras el tope de bloques de un .txt.
        anclas.sort(key=lambda par: par[0])
        inicios = [inicio for inicio, _ in anclas]
        for hueco in uncovered_ranges(len(texto_completo), cubiertos):
            cortes = evidence_cuts(texto_completo, *hueco)
            if not cortes:
                continue
            posicion = bisect_right(inicios, hueco[0])
            ancla = anclas[posicion - 1][1] if posicion else None
            for corte in cortes:
                evidencias += 1
                session.add(
                    self._evidence(
                        version,
                        representacion,
                        texto_completo,
                        corte,
                        evidencias,
                        now,
                        seccion=None,
                        ancla=ancla,
                    )
                )
        return creadas, evidencias

    @staticmethod
    def _citation_label(seccion: DocumentSectionRecord) -> str:
        """Etiqueta de cita: título (o etiqueta) y página, para poder abrir el sitio correcto."""
        nombre = seccion.title or seccion.label
        if nombre and seccion.page_start:
            return f"{nombre}, pág. {seccion.page_start}"
        if nombre:
            return nombre
        if seccion.page_start:
            return f"pág. {seccion.page_start}"
        return f"sección {seccion.ordinal}"

    def _read_text(self, representacion: ExtractedRepresentationRecord) -> str:
        """Texto de la representación, leído del almacén. Si ya no está, se devuelve vacío."""
        if not representacion.text_storage_key:
            return ""
        try:
            return self._store.read(
                representacion.text_storage_key, limit=MAX_EVIDENCE_TEXT_CHARS
            ).text
        except OSError:
            return ""

    def _evidence(
        self,
        version: DocumentVersionRecord,
        representacion: ExtractedRepresentationRecord,
        texto: str,
        corte: tuple[int, int],
        ordinal: int,
        now: datetime,
        *,
        seccion: DocumentSectionRecord | None,
        ancla: DocumentSectionRecord | None = None,
    ) -> EvidenceSpanRecord:
        """Una evidencia con offsets exactos: `texto[char_start:char_end]` es su texto.

        `seccion` es la sección que la contiene. Una evidencia de texto que no cae en ninguna
        sección no se cuelga de ninguna, pero toma la página y la etiqueta de la sección anterior
        (`ancla`), que es dónde está en el documento.
        """
        inicio, fin = corte
        fragmento = texto[inicio:fin]
        if len(fragmento) > MAX_EVIDENCE_CHARS:  # lo garantiza `evidence_cuts`; se comprueba igual
            raise InvariantViolationError("Una evidencia no puede pasar del tope de caracteres")
        referencia = seccion if seccion is not None else ancla
        return EvidenceSpanRecord(
            id=_new_id(),
            document_version_id=version.id,
            section_id=None if seccion is None else seccion.id,
            ordinal=ordinal,
            text=fragmento,
            normalized_text=" ".join(fragmento.split()),
            char_start=inicio,
            char_end=fin,
            # Dentro de una sección, su primera página; tras ella, la última, que es donde sigue.
            page=(
                seccion.page_start
                if seccion is not None
                else None
                if ancla is None
                else ancla.page_end or ancla.page_start
            ),
            citation_label=(
                f"fragmento {ordinal}" if referencia is None else self._citation_label(referencia)
            ),
            quality=representacion.quality,
            index_status="pending",
            created_at=now,
        )

    @staticmethod
    def _parse_sections(raw: str | None) -> tuple[dict[str, object], ...]:
        if not raw:
            return ()
        try:
            datos = json.loads(raw)
        except json.JSONDecodeError:
            return ()
        if not isinstance(datos, list):
            return ()
        return tuple(item for item in datos if isinstance(item, dict))

    # ------------------------------------------------------------------ versiones

    def accept_version(
        self, version_id: str, *, now: datetime, actor: str = "local"
    ) -> PromotionOutcome:
        """Acepta una versión candidata. Es una promoción crítica y queda auditada."""
        with self._session_factory() as session:
            version = session.get(DocumentVersionRecord, version_id)
            if version is None:
                return PromotionOutcome(None, None, False, False, reason="La versión no existe")
            actual = VersionStatus(version.status)
            from opofuente.domain.documents import ACCEPTABLE_FROM

            if actual not in ACCEPTABLE_FROM:
                return PromotionOutcome(
                    version.logical_document_id,
                    version.id,
                    False,
                    False,
                    reason=f"No se puede aceptar una versión «{actual.value}»",
                )
            anterior = {"status": version.status}
            version.status = VersionStatus.ACCEPTED.value
            version.approved_at = now
            version.approved_by = actor
            self._audit(
                session,
                actor=actor,
                action="version.accepted",
                object_type="document_version",
                object_id=version.id,
                before=anterior,
                after={"status": version.status},
                now=now,
            )
            session.commit()
            return PromotionOutcome(version.logical_document_id, version.id, False, False)

    def mark_supersedes(
        self, version_id: str, *, superseded_id: str, now: datetime, actor: str = "local"
    ) -> PromotionOutcome:
        """Confirma que una versión sustituye a otra. La antigua **no se borra**."""
        with self._session_factory() as session:
            nueva = session.get(DocumentVersionRecord, version_id)
            vieja = session.get(DocumentVersionRecord, superseded_id)
            if nueva is None or vieja is None:
                return PromotionOutcome(None, None, False, False, reason="Alguna versión no existe")
            if nueva.id == vieja.id:
                return PromotionOutcome(
                    None, None, False, False, reason="Una versión no se sustituye a sí misma"
                )
            if nueva.logical_document_id != vieja.logical_document_id:
                return PromotionOutcome(
                    None,
                    None,
                    False,
                    False,
                    reason="Solo se sustituyen versiones del mismo documento",
                )
            anterior = {"supersedes_id": nueva.supersedes_id, "superseded_status": vieja.status}
            nueva.supersedes_id = vieja.id
            if VersionStatus(vieja.status) in {
                VersionStatus.ACCEPTED,
                VersionStatus.CANDIDATE,
                VersionStatus.OUTDATED,
            }:
                vieja.status = VersionStatus.SUPERSEDED.value
            self._audit(
                session,
                actor=actor,
                action="version.supersedes",
                object_type="document_version",
                object_id=nueva.id,
                before=anterior,
                after={"supersedes_id": nueva.supersedes_id, "superseded_status": vieja.status},
                now=now,
            )
            session.commit()
            return PromotionOutcome(nueva.logical_document_id, nueva.id, False, False)

    # ------------------------------------------------------------------ consulta

    def list_documents(
        self,
        *,
        document_type: str | None = None,
        owner_scope: str | None = None,
        collection_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> DocumentPage:
        """Documentos de la biblioteca, con los filtros que el contrato admite.

        El filtro por **colección** (07_UI-UX §6: «filtros por … y colección») se resuelve por los
        miembros de la colección, que pueden ser de cinco tipos distintos. Un documento entra si
        alguno de sus sujetos está dentro:

        - el propio documento lógico (`document_version` → su versión);
        - el artefacto o la representación de una de sus versiones;
        - una sección o una evidencia de una de sus versiones.
        """
        filtros = []
        if document_type is not None:
            filtros.append(LogicalDocumentRecord.document_type == document_type)
        if owner_scope is not None:
            filtros.append(LogicalDocumentRecord.owner_scope == owner_scope)
        if collection_id is not None:
            filtros.append(self._in_collection(collection_id))
        with self._session_factory() as session:
            total = int(
                session.execute(
                    select(func.count()).select_from(LogicalDocumentRecord).where(*filtros)
                ).scalar_one()
            )
            filas = (
                session.execute(
                    select(LogicalDocumentRecord)
                    .where(*filtros)
                    .order_by(LogicalDocumentRecord.canonical_title, LogicalDocumentRecord.id)
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            vistas = tuple(self._document_view(session, fila) for fila in filas)
        return DocumentPage(documents=vistas, total=total, limit=limit, offset=offset)

    @staticmethod
    def _in_collection(collection_id: str) -> ColumnElement[bool]:
        """Condición «este documento tiene algún sujeto dentro de la colección».

        Una colección agrupa **sujetos** de cinco tipos, así que un documento pertenece a ella si
        alguno de sus sujetos está dentro. Se resuelve con un `EXISTS` por tipo, correlacionado **a
        mano** con el documento de la consulta externa (`correlate(LogicalDocumentRecord)`): sin esa
        correlación explícita, SQLAlchemy autocorrelaciona la subconsulta consigo misma y la
        condición se cumple siempre —el fallo que encontró la prueba de integración cuando devolvía
        cuatro documentos donde había uno—.
        """

        def existe_miembro(tipo: str, condicion: ColumnElement[bool]) -> ColumnElement[bool]:
            return (
                select(literal(1))
                .select_from(CollectionItemRecord)
                .where(
                    CollectionItemRecord.collection_id == collection_id,
                    CollectionItemRecord.subject_type == tipo,
                    condicion,
                )
                .correlate(LogicalDocumentRecord)
                .exists()
            )

        def sujetos_del_documento(columna: InstrumentedAttribute[str | None]) -> Select[Any]:
            """Columna de una versión del documento de fuera, correlacionada **a mano**.

            Sin `correlate(LogicalDocumentRecord)`, SQLAlchemy mete el documento en el `FROM` de la
            subconsulta y la condición deja de depender del documento de fuera: el filtro devolvía
            todos los documentos. La subconsulta tiene que usar **el de la consulta externa**, y eso
            hay que decirlo explícitamente.
            """
            return (
                select(columna)
                .where(DocumentVersionRecord.logical_document_id == LogicalDocumentRecord.id)
                .correlate(LogicalDocumentRecord)
            )

        def sujetos_por_version(
            columna: InstrumentedAttribute[str],
            tabla: type[DeclarativeBase],
            clave: str,
        ) -> Select[Any]:
            """Igual que el anterior, pero la tabla cuelga de la **versión**, no del documento."""
            return (
                select(columna)
                .select_from(tabla)
                .join(DocumentVersionRecord, DocumentVersionRecord.id == getattr(tabla, clave))
                .where(DocumentVersionRecord.logical_document_id == LogicalDocumentRecord.id)
                .correlate(LogicalDocumentRecord)
            )

        return or_(
            existe_miembro(
                "document_version",
                CollectionItemRecord.subject_id.in_(
                    sujetos_del_documento(DocumentVersionRecord.id)
                ),
            ),
            existe_miembro(
                "artifact",
                CollectionItemRecord.subject_id.in_(
                    sujetos_del_documento(DocumentVersionRecord.artifact_id)
                ),
            ),
            existe_miembro(
                "representation",
                CollectionItemRecord.subject_id.in_(
                    sujetos_del_documento(DocumentVersionRecord.representation_id)
                ),
            ),
            existe_miembro(
                "section",
                CollectionItemRecord.subject_id.in_(
                    sujetos_por_version(
                        DocumentSectionRecord.id, DocumentSectionRecord, "document_version_id"
                    )
                ),
            ),
            existe_miembro(
                "evidence",
                CollectionItemRecord.subject_id.in_(
                    sujetos_por_version(
                        EvidenceSpanRecord.id, EvidenceSpanRecord, "document_version_id"
                    )
                ),
            ),
        )

    def get_document(self, document_id: str) -> DocumentDetail | None:
        with self._session_factory() as session:
            fila = session.get(LogicalDocumentRecord, document_id)
            if fila is None:
                return None
            versiones = self._versions_of(session, document_id)
            return DocumentDetail(
                document=self._document_view(session, fila, versiones), versions=versiones
            )

    def list_sections(self, version_id: str) -> tuple[SectionView, ...]:
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(DocumentSectionRecord)
                    .where(DocumentSectionRecord.document_version_id == version_id)
                    .order_by(DocumentSectionRecord.ordinal)
                )
                .scalars()
                .all()
            )
        return tuple(self._section_view(fila) for fila in filas)

    def list_evidence(self, version_id: str) -> tuple[EvidenceView, ...]:
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(EvidenceSpanRecord)
                    .where(EvidenceSpanRecord.document_version_id == version_id)
                    .order_by(EvidenceSpanRecord.ordinal)
                )
                .scalars()
                .all()
            )
        return tuple(self._evidence_view(fila) for fila in filas)

    def get_evidence(self, evidence_id: str) -> EvidenceView | None:
        with self._session_factory() as session:
            fila = session.get(EvidenceSpanRecord, evidence_id)
            if fila is None:
                return None
            return self._evidence_view(fila)

    # ------------------------------------------------------------------ versiones sueltas

    def version_detail(self, version_id: str) -> VersionDetail | None:
        """Una versión con su documento: es lo que responde `GET /document-versions/{id}`."""
        with self._session_factory() as session:
            fila = session.get(DocumentVersionRecord, version_id)
            if fila is None:
                return None
            documento = session.get(LogicalDocumentRecord, fila.logical_document_id)
            if documento is None:
                return None
            mapeos = int(
                session.execute(
                    select(func.count())
                    .select_from(CurriculumMappingRecord)
                    .where(
                        CurriculumMappingRecord.subject_type == "document_version",
                        CurriculumMappingRecord.subject_id == version_id,
                    )
                ).scalar_one()
            )
            return VersionDetail(
                document_id=documento.id,
                document_title=documento.canonical_title,
                document_type=documento.document_type,
                owner_scope=documento.owner_scope,
                version=self._version_view(session, fila),
                mapping_count=mapeos,
            )

    def version_text(
        self, version_id: str, *, offset: int = 0, limit: int = 20_000
    ) -> VersionText | None:
        """Texto extraído de la versión, por trozos, leído del almacén (nunca de la base).

        Si la extracción no dejó texto —un escaneo sin OCR— se devuelve vacío con su calidad: la
        versión existe, lo que no hay es texto, y eso se dice en lugar de inventarlo.
        """
        with self._session_factory() as session:
            fila = session.get(DocumentVersionRecord, version_id)
            if fila is None:
                return None
            representacion = self._best_representation(session, fila.artifact_id)
            if representacion is None or not representacion.text_storage_key:
                return VersionText(
                    document_version_id=version_id,
                    text="",
                    offset=offset,
                    limit=limit,
                    total_chars=0,
                    truncated=False,
                    representation_id=representacion.id if representacion is not None else None,
                    quality=representacion.quality if representacion is not None else None,
                    warnings=_warnings(representacion) if representacion is not None else (),
                )
            trozo = self._store.read(representacion.text_storage_key, offset=offset, limit=limit)
            return VersionText(
                document_version_id=version_id,
                text=trozo.text,
                offset=trozo.offset,
                limit=trozo.limit,
                total_chars=trozo.total_chars,
                truncated=trozo.truncated,
                representation_id=representacion.id,
                quality=representacion.quality,
                warnings=_warnings(representacion),
            )

    def version_artifact(self, version_id: str) -> ArtifactFile | None:
        """El fichero original de la versión: clave en el almacén, tipo y nombre visible."""
        with self._session_factory() as session:
            fila = session.get(DocumentVersionRecord, version_id)
            if fila is None:
                return None
            artefacto = session.get(SourceArtifactRecord, fila.artifact_id)
            if artefacto is None:
                return None
            return ArtifactFile(
                storage_key=artefacto.storage_key,
                media_type=artefacto.media_type,
                size_bytes=artefacto.size_bytes,
                sha256=artefacto.sha256,
                original_name=self._label_of(session, fila.artifact_id),
                quarantine_status=str(artefacto.quarantine_status),
            )

    def document_diff(
        self, document_id: str, *, from_version_id: str, to_version_id: str
    ) -> VersionDiff | None:
        """Compara dos versiones **del mismo documento**: las de otro documento no son un diff.

        Compara el texto real de cada sección (leído del almacén por sus offsets), emparejando por
        etiqueta. No fusiona nada, no decide cuál es mejor y no escribe nada.
        """
        with self._session_factory() as session:
            antes = session.get(DocumentVersionRecord, from_version_id)
            despues = session.get(DocumentVersionRecord, to_version_id)
            if antes is None or despues is None:
                return None
            if (
                antes.logical_document_id != document_id
                or despues.logical_document_id != document_id
            ):
                return None
            dominio = diff_versions(
                from_version_id,
                to_version_id,
                before=self._section_texts(session, antes),
                after=self._section_texts(session, despues),
            )
            return VersionDiff(
                document_id=document_id,
                from_version_id=from_version_id,
                to_version_id=to_version_id,
                sections=tuple(
                    SectionDiff(
                        label=seccion.label,
                        kind=seccion.kind,
                        left=seccion.left,
                        right=seccion.right,
                    )
                    for seccion in dominio.sections
                ),
                added=dominio.added,
                removed=dominio.removed,
                changed=dominio.changed,
                unchanged=dominio.unchanged,
            )

    def _section_texts(
        self, session: Session, version: DocumentVersionRecord
    ) -> tuple[tuple[str | None, str], ...]:
        """`(título, texto)` de cada sección en orden: lo que compara `diff_versions`."""
        filas = (
            session.execute(
                select(DocumentSectionRecord)
                .where(DocumentSectionRecord.document_version_id == version.id)
                .order_by(DocumentSectionRecord.position, DocumentSectionRecord.id)
            )
            .scalars()
            .all()
        )
        representacion = self._best_representation(session, version.artifact_id)
        texto = self._read_text(representacion) if representacion is not None else ""
        return tuple(
            (
                fila.title,
                texto[fila.char_start : fila.char_end][:MAX_EVIDENCE_CHARS].strip()
                if fila.char_end > fila.char_start
                else "",
            )
            for fila in filas
        )

    def update_document(
        self,
        document_id: str,
        *,
        canonical_title: str,
        document_type: str,
        owner_scope: str,
        authority_tier: str | None,
        canonical_identifier: str | None,
        now: datetime,
        actor: str = "local",
    ) -> DocumentView | None:
        """Cambia los metadatos de la obra. El cambio queda auditado con su antes y su después."""
        with self._session_factory() as session:
            fila = session.get(LogicalDocumentRecord, document_id)
            if fila is None:
                return None
            antes: dict[str, object] = {
                "canonical_title": fila.canonical_title,
                "document_type": fila.document_type,
                "owner_scope": fila.owner_scope,
                "authority_tier": fila.authority_tier,
                "canonical_identifier": fila.canonical_identifier,
            }
            fila.canonical_title = canonical_title
            fila.document_type = document_type
            fila.owner_scope = owner_scope
            fila.authority_tier = authority_tier
            fila.canonical_identifier = canonical_identifier
            fila.updated_at = now
            despues: dict[str, object] = {
                "canonical_title": canonical_title,
                "document_type": document_type,
                "owner_scope": owner_scope,
                "authority_tier": authority_tier,
                "canonical_identifier": canonical_identifier,
            }
            self._audit(
                session,
                actor=actor,
                action="document.updated",
                object_type="logical_document",
                object_id=document_id,
                before=antes,
                after=despues,
                now=now,
            )
            session.commit()
            return self._document_view(session, fila)

    # ------------------------------------------------------------------ colecciones

    def create_collection(
        self, name: str, *, description: str | None, now: datetime
    ) -> CollectionView:
        with self._session_factory() as session:
            fila = CollectionRecord(
                id=_new_id(),
                name=name,
                description=description,
                created_at=now,
                updated_at=now,
            )
            session.add(fila)
            session.commit()
            return CollectionView(id=fila.id, name=name, description=description, item_count=0)

    # ------------------------------------------------------------------ mapeos

    def add_mapping(
        self,
        *,
        version_id: str,
        curriculum_node_id: str,
        now: datetime,
        coverage_type: str = "partial",
        confidence: float = 1.0,
        status: str = "accepted",
        actor: str = "local",
    ) -> str | None:
        """Asigna una **versión** de documento a un nodo del programa (contrato §7).

        Es lo que sostiene la promesa de «una fuente compartida se guarda una vez»: un artefacto, un
        documento, una versión y **dos mapeos**. Devuelve el id del mapeo, o el del existente si ya
        había uno idéntico (la identidad es nodo + sujeto); `None` si la versión o el nodo no
        existen, y en ese caso no escribe nada.
        """
        with self._session_factory() as session:
            version = session.get(DocumentVersionRecord, version_id)
            if version is None:
                return None
            nodo = session.get(CurriculumNodeRecord, curriculum_node_id)
            if nodo is None:
                return None
            existente = session.execute(
                select(CurriculumMappingRecord.id).where(
                    CurriculumMappingRecord.curriculum_node_id == curriculum_node_id,
                    CurriculumMappingRecord.subject_type == "document_version",
                    CurriculumMappingRecord.subject_id == version_id,
                )
            ).scalar_one_or_none()
            if existente is not None:
                return str(existente)
            mapeo = CurriculumMappingRecord(
                id=_new_id(),
                curriculum_node_id=curriculum_node_id,
                subject_type="document_version",
                subject_id=version_id,
                coverage_type=coverage_type,
                depth=nodo.depth,
                confidence=confidence,
                status=status,
                source_proposal_id=None,
                created_at=now,
                approved_at=now if status == "accepted" else None,
            )
            session.add(mapeo)
            self._audit(
                session,
                actor=actor,
                action="mapping.created",
                object_type="curriculum_mapping",
                object_id=mapeo.id,
                before={},
                after={
                    "curriculum_node_id": curriculum_node_id,
                    "version_id": version_id,
                    "coverage_type": coverage_type,
                    "status": status,
                },
                now=now,
            )
            session.commit()
            return mapeo.id

    def list_collections(self) -> tuple[CollectionView, ...]:
        with self._session_factory() as session:
            filas = (
                session.execute(select(CollectionRecord).order_by(CollectionRecord.name))
                .scalars()
                .all()
            )
            return tuple(self._collection_view(session, fila) for fila in filas)

    def add_to_collection(
        self, collection_id: str, *, subject_type: str, subject_id: str, now: datetime
    ) -> CollectionView | None:
        with self._session_factory() as session:
            coleccion = session.get(CollectionRecord, collection_id)
            if coleccion is None:
                return None
            ya = session.execute(
                select(CollectionItemRecord.id).where(
                    CollectionItemRecord.collection_id == collection_id,
                    CollectionItemRecord.subject_type == subject_type,
                    CollectionItemRecord.subject_id == subject_id,
                )
            ).first()
            if ya is None:
                posicion = (
                    session.execute(
                        select(func.count())
                        .select_from(CollectionItemRecord)
                        .where(CollectionItemRecord.collection_id == collection_id)
                    ).scalar_one()
                    + 1
                )
                session.add(
                    CollectionItemRecord(
                        id=_new_id(),
                        collection_id=collection_id,
                        subject_type=subject_type,
                        subject_id=subject_id,
                        position=int(posicion),
                        added_at=now,
                    )
                )
                session.commit()
            return self._collection_view(session, coleccion)

    def remove_from_collection(
        self, collection_id: str, *, subject_type: str, subject_id: str
    ) -> CollectionView | None:
        """Quita un sujeto de una colección. No borra nada del sujeto: solo deja de agruparlo.

        Es **idempotente**: quitar algo que no estaba devuelve la colección como está, sin error. A
        diferencia de retirar material (que sí exige confirmación), esto no necesita ninguna: el
        documento, la versión o la cita siguen donde estaban, y lo único que cambia es en qué
        colecciones aparecen. Y a diferencia de `add_to_collection`, aquí no se crea nada si falta:
        una colección o un miembro que no existen no se inventan.
        """
        with self._session_factory() as session:
            coleccion = session.get(CollectionRecord, collection_id)
            if coleccion is None:
                return None
            session.execute(
                delete(CollectionItemRecord)
                .where(CollectionItemRecord.collection_id == collection_id)
                .where(CollectionItemRecord.subject_type == subject_type)
                .where(CollectionItemRecord.subject_id == subject_id)
            )
            session.commit()
            return self._collection_view(session, coleccion)

    # ------------------------------------------------------------------ auxiliares

    @staticmethod
    def _best_representation(
        session: Session, artifact_id: str
    ) -> ExtractedRepresentationRecord | None:
        filas = (
            session.execute(
                select(ExtractedRepresentationRecord).where(
                    ExtractedRepresentationRecord.artifact_id == artifact_id
                )
            )
            .scalars()
            .all()
        )
        if not filas:
            return None
        return min(filas, key=lambda fila: (_quality_rank(fila.quality), -fila.char_count, fila.id))

    @staticmethod
    def _rights(session: Session, code: str | None) -> RightsStatusRecord | None:
        if code is None:
            return None
        return session.execute(
            select(RightsStatusRecord).where(RightsStatusRecord.code == code)
        ).scalar_one_or_none()

    @staticmethod
    def _existing_version(
        session: Session, document_id: str, artifact_id: str
    ) -> DocumentVersionRecord | None:
        return session.execute(
            select(DocumentVersionRecord).where(
                DocumentVersionRecord.logical_document_id == document_id,
                DocumentVersionRecord.artifact_id == artifact_id,
            )
        ).scalar_one_or_none()

    @staticmethod
    def _version_of_artifact(session: Session, artifact_id: str) -> DocumentVersionRecord | None:
        return session.execute(
            select(DocumentVersionRecord)
            .where(DocumentVersionRecord.artifact_id == artifact_id)
            .order_by(DocumentVersionRecord.created_at)
            .limit(1)
        ).scalar_one_or_none()

    @staticmethod
    def _label_of(session: Session, artifact_id: str) -> str | None:
        """Nombre visible del artefacto: el del fichero del que salió, o su origen."""
        nombre = session.execute(
            select(IngestionItemRecord.original_name)
            .join(
                ItemRepresentationRecord, ItemRepresentationRecord.item_id == IngestionItemRecord.id
            )
            .join(
                ExtractedRepresentationRecord,
                ExtractedRepresentationRecord.id == ItemRepresentationRecord.representation_id,
            )
            .where(ExtractedRepresentationRecord.artifact_id == artifact_id)
            .order_by(IngestionItemRecord.position)
            .limit(1)
        ).scalar_one_or_none()
        if nombre:
            return str(nombre)
        origen = session.execute(
            select(ArtifactOriginRecord.display_location)
            .where(ArtifactOriginRecord.artifact_id == artifact_id)
            .order_by(ArtifactOriginRecord.id)
            .limit(1)
        ).scalar_one_or_none()
        return str(origen) if origen else None

    def _versions_of(self, session: Session, document_id: str) -> tuple[VersionView, ...]:
        filas = (
            session.execute(
                select(DocumentVersionRecord)
                .where(DocumentVersionRecord.logical_document_id == document_id)
                .order_by(DocumentVersionRecord.created_at, DocumentVersionRecord.id)
            )
            .scalars()
            .all()
        )
        return tuple(self._version_view(session, fila) for fila in filas)

    def _document_view(
        self,
        session: Session,
        fila: LogicalDocumentRecord,
        versiones: Sequence[VersionView] | None = None,
    ) -> DocumentView:
        lista = tuple(versiones) if versiones is not None else self._versions_of(session, fila.id)
        activa = self._active(lista)
        # Mapeos de **programa** de este documento: los que apuntan a alguna de sus versiones. Antes
        # contaba versiones, que es otra cosa y engañaba al leerlo.
        mapeos = (
            int(
                session.execute(
                    select(func.count())
                    .select_from(CurriculumMappingRecord)
                    .where(
                        CurriculumMappingRecord.subject_type == "document_version",
                        CurriculumMappingRecord.subject_id.in_([version.id for version in lista]),
                    )
                ).scalar_one()
            )
            if lista
            else 0
        )
        return DocumentView(
            id=fila.id,
            canonical_title=fila.canonical_title,
            document_type=fila.document_type,
            owner_scope=fila.owner_scope,
            authority_tier=fila.authority_tier,
            canonical_identifier=fila.canonical_identifier,
            active_version=activa,
            version_count=len(lista),
            mapping_count=mapeos,
            created_at=fila.created_at,
        )

    @staticmethod
    def _active(versiones: Sequence[VersionView]) -> VersionView | None:
        """Manda la aceptada; si no hay, la candidata. Nunca «la última que llegó»."""
        aceptadas = [version for version in versiones if version.status == "accepted"]
        if aceptadas:
            return sorted(aceptadas, key=lambda version: version.id)[-1]
        candidatas = [version for version in versiones if version.status == "candidate"]
        if candidatas:
            return sorted(candidatas, key=lambda version: version.id)[-1]
        return None

    def _version_view(self, session: Session, fila: DocumentVersionRecord) -> VersionView:
        secciones = int(
            session.execute(
                select(func.count())
                .select_from(DocumentSectionRecord)
                .where(DocumentSectionRecord.document_version_id == fila.id)
            ).scalar_one()
        )
        evidencias = int(
            session.execute(
                select(func.count())
                .select_from(EvidenceSpanRecord)
                .where(EvidenceSpanRecord.document_version_id == fila.id)
            ).scalar_one()
        )
        derechos = (
            session.get(RightsStatusRecord, fila.rights_status_id)
            if fila.rights_status_id
            else None
        )
        return VersionView(
            id=fila.id,
            logical_document_id=fila.logical_document_id,
            version_label=fila.version_label,
            status=fila.status,
            artifact_id=fila.artifact_id,
            representation_id=fila.representation_id,
            published_at=fila.published_at,
            valid_from=fila.valid_from,
            valid_to=fila.valid_to,
            retrieved_at=fila.retrieved_at,
            language=fila.language,
            supersedes_id=fila.supersedes_id,
            rights=(
                RightsView(
                    code=derechos.code,
                    review_status=derechos.review_status,
                    license_name=derechos.license_name,
                    license_url=derechos.license_url,
                    attribution=derechos.attribution,
                    commercial_reuse=derechos.commercial_reuse,
                    sharing=derechos.sharing,
                    notes=derechos.notes,
                )
                if derechos is not None
                else None
            ),
            official_url=fila.official_url,
            content_hash=fila.content_hash,
            approved_at=fila.approved_at,
            approved_by=fila.approved_by,
            section_count=secciones,
            evidence_count=evidencias,
        )

    @staticmethod
    def _section_view(fila: DocumentSectionRecord) -> SectionView:
        return SectionView(
            id=fila.id,
            document_version_id=fila.document_version_id,
            section_type=fila.section_type,
            title=fila.title,
            label=fila.label,
            position=fila.position,
            ordinal=fila.ordinal,
            parent_id=fila.parent_id,
            page_start=fila.page_start,
            page_end=fila.page_end,
            char_start=fila.char_start,
            char_end=fila.char_end,
        )

    @staticmethod
    def _evidence_view(fila: EvidenceSpanRecord) -> EvidenceView:
        return EvidenceView(
            id=fila.id,
            document_version_id=fila.document_version_id,
            text=fila.text,
            normalized_text=fila.normalized_text,
            ordinal=fila.ordinal,
            section_id=fila.section_id,
            page=fila.page,
            citation_label=fila.citation_label,
            quality=fila.quality,
            index_status=fila.index_status,
            char_start=fila.char_start,
            char_end=fila.char_end,
        )

    def _collection_view(self, session: Session, fila: CollectionRecord) -> CollectionView:
        miembros = (
            session.execute(
                select(CollectionItemRecord)
                .where(CollectionItemRecord.collection_id == fila.id)
                .order_by(CollectionItemRecord.position)
            )
            .scalars()
            .all()
        )
        return CollectionView(
            id=fila.id,
            name=fila.name,
            description=fila.description,
            item_count=len(miembros),
            items=tuple(miembro.subject_id for miembro in miembros),
            created_at=fila.created_at,
        )

    @staticmethod
    def _audit(
        session: Session,
        *,
        actor: str,
        action: str,
        object_type: str,
        object_id: str,
        before: Mapping[str, object],
        after: Mapping[str, object],
        now: datetime,
    ) -> str:
        evento = AuditEventRecord(
            id=_new_id(),
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=object_id,
            before_json=json.dumps(before, ensure_ascii=False),
            after_json=json.dumps(after, ensure_ascii=False),
            correlation_id=None,
            created_at=now,
        )
        session.add(evento)
        return evento.id
