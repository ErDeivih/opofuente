"""Repositorio de cambios, dependencias y derivados (S11).

Tres cosas que hace de una manera concreta:

1. **el recorrido de dependencias se hace en SQL** y devuelve, por sección, qué depende de ella. Así
   la invalidación selectiva se apoya en las aristas guardadas y no en una semejanza calculada al
   vuelo;
2. **la etiqueta de sección es la misma que la del diff** (`section_label`): si aquí se llamara de
   otra forma, una sección «cambiada» no coincidiría con la que depende de ella;
3. **nada se borra**: un cambio descartado, un derivado descartado y las aristas se quedan; lo que
   cambia es su estado.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.change_models import (
    AffectedView,
    ChangeSetView,
    DerivedArtifactView,
    SectionChangeView,
)
from opofuente.domain.changes import Dependent, EdgeSource, EdgeTarget
from opofuente.domain.documents import section_label
from opofuente.infrastructure.db import as_utc
from opofuente.infrastructure.db_models import (
    ChangeSetRecord,
    DependencyEdgeRecord,
    DerivedArtifactRecord,
    DocumentSectionRecord,
    DocumentVersionRecord,
    EvidenceSpanRecord,
    LogicalDocumentRecord,
)


def _new_id() -> str:
    return str(uuid4())


def _json_lista(texto: str) -> list[dict[str, object]]:
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError:
        return []
    if not isinstance(datos, list):
        return []
    return [elemento for elemento in datos if isinstance(elemento, dict)]


def _secciones_de(valor: object) -> tuple[str, ...]:
    """Las etiquetas de sección guardadas en un afectado, sin fiarse del tipo del JSON."""
    if not isinstance(valor, list):
        return ()
    return tuple(str(elemento) for elemento in valor)


class SqlAlchemyChangeRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ derivados

    def create_artifact(
        self,
        *,
        kind: str,
        title: str,
        content: str,
        document_version_id: str,
        generator: str,
        prompt_template_version: str | None,
        model: str | None,
        now: datetime,
    ) -> DerivedArtifactView | None:
        with self._session_factory() as session:
            if session.get(DocumentVersionRecord, document_version_id) is None:
                return None
            fila = DerivedArtifactRecord(
                id=_new_id(),
                kind=kind,
                title=title,
                content=content,
                document_version_id=document_version_id,
                generator=generator,
                prompt_template_version=prompt_template_version,
                model=model,
                review_status="pending",
                needs_review=False,
                needs_review_reason=None,
                created_at=now,
                updated_at=now,
            )
            session.add(fila)
            session.commit()
            return self._artifact_view(session, fila)

    def artifact(self, artifact_id: str) -> DerivedArtifactView | None:
        with self._session_factory() as session:
            fila = session.get(DerivedArtifactRecord, artifact_id)
            return None if fila is None else self._artifact_view(session, fila)

    def artifacts(
        self,
        *,
        document_version_id: str | None = None,
        needs_review: bool | None = None,
        limit: int = 200,
    ) -> tuple[DerivedArtifactView, ...]:
        with self._session_factory() as session:
            consulta = (
                select(DerivedArtifactRecord)
                .order_by(DerivedArtifactRecord.created_at.desc())
                .limit(limit)
            )
            if document_version_id is not None:
                consulta = consulta.where(
                    DerivedArtifactRecord.document_version_id == document_version_id
                )
            if needs_review is not None:
                consulta = consulta.where(DerivedArtifactRecord.needs_review == needs_review)
            return tuple(
                self._artifact_view(session, fila) for fila in session.execute(consulta).scalars()
            )

    def mark_artifacts_for_review(
        self, artifact_ids: Sequence[str], *, reason: str, now: datetime
    ) -> tuple[str, ...]:
        """Marca derivados para revisar. Devuelve los que **de verdad** han cambiado de estado."""
        marcados: list[str] = []
        if not artifact_ids:
            return ()
        with self._session_factory() as session:
            for artifact_id in artifact_ids:
                fila = session.get(DerivedArtifactRecord, artifact_id)
                if fila is None:
                    continue
                if not fila.needs_review:
                    marcados.append(fila.id)
                fila.needs_review = True
                fila.needs_review_reason = reason
                fila.needs_review_at = now
                fila.review_status = "pending"
                fila.updated_at = now
            session.commit()
        return tuple(marcados)

    def resolve_artifact(
        self, artifact_id: str, *, resolution: str, now: datetime
    ) -> DerivedArtifactView | None:
        with self._session_factory() as session:
            fila = session.get(DerivedArtifactRecord, artifact_id)
            if fila is None:
                return None
            fila.review_status = resolution
            fila.reviewed_at = now
            fila.updated_at = now
            if resolution == "reviewed":
                # Revisado y sigue valiendo: deja de estar pendiente, pero se conserva por qué se
                # marcó (el motivo es la historia de la revisión).
                fila.needs_review = False
                fila.needs_review_at = None
            session.commit()
            return self._artifact_view(session, fila)

    # ------------------------------------------------------------------ dependencias

    def add_edges(
        self,
        *,
        from_type: EdgeSource,
        from_ids: Sequence[str],
        to_type: EdgeTarget,
        to_id: str,
        now: datetime,
        role: str | None = None,
    ) -> int:
        """Escribe las aristas de dependencia al crear el derivado. Idempotente por arista."""
        if not from_ids:
            return 0
        creadas = 0
        with self._session_factory() as session:
            for from_id in dict.fromkeys(from_ids):
                existente = session.execute(
                    select(DependencyEdgeRecord.id).where(
                        DependencyEdgeRecord.from_type == from_type.value,
                        DependencyEdgeRecord.from_id == from_id,
                        DependencyEdgeRecord.to_type == to_type.value,
                        DependencyEdgeRecord.to_id == to_id,
                    )
                ).scalar_one_or_none()
                if existente is not None:
                    continue
                session.add(
                    DependencyEdgeRecord(
                        id=_new_id(),
                        from_type=from_type.value,
                        from_id=from_id,
                        to_type=to_type.value,
                        to_id=to_id,
                        role=role,
                        created_at=now,
                    )
                )
                creadas += 1
            session.commit()
        return creadas

    def dependents_by_section(self, version_id: str) -> Mapping[str, tuple[Dependent, ...]]:
        """Qué depende de cada sección de una versión, con la etiqueta que usa el diff.

        Se recorren las aristas que salen de los fragmentos de esa versión (y las que salen de la
        propia versión o de sus secciones) y se agrupan por la sección de la que cuelgan.
        """
        with self._session_factory() as session:
            secciones = (
                session.execute(
                    select(DocumentSectionRecord)
                    .where(DocumentSectionRecord.document_version_id == version_id)
                    .order_by(DocumentSectionRecord.position, DocumentSectionRecord.id)
                )
                .scalars()
                .all()
            )
            etiquetas: dict[str, str] = {
                fila.id: section_label(fila.title, indice)
                for indice, fila in enumerate(secciones, start=1)
            }
            filas = session.execute(
                select(
                    DependencyEdgeRecord.from_type,
                    DependencyEdgeRecord.from_id,
                    DependencyEdgeRecord.to_type,
                    DependencyEdgeRecord.to_id,
                    EvidenceSpanRecord.section_id,
                )
                .select_from(DependencyEdgeRecord)
                .outerjoin(
                    EvidenceSpanRecord,
                    (DependencyEdgeRecord.from_type == EdgeSource.EVIDENCE_SPAN.value)
                    & (DependencyEdgeRecord.from_id == EvidenceSpanRecord.id),
                )
                .where(
                    (EvidenceSpanRecord.document_version_id == version_id)
                    | (
                        (DependencyEdgeRecord.from_type == EdgeSource.DOCUMENT_VERSION.value)
                        & (DependencyEdgeRecord.from_id == version_id)
                    )
                )
            ).all()

            agrupado: dict[str, dict[tuple[str, str], Dependent]] = {}
            for _from_type, _from_id, to_type, to_id, section_id in filas:
                titulo = self._dependent_title(session, to_type, to_id)
                if titulo is None:
                    continue
                etiqueta = (
                    etiquetas.get(str(section_id))
                    if section_id is not None
                    else self._version_label(session, version_id)
                )
                if etiqueta is None:
                    continue
                dependiente = Dependent(
                    kind=EdgeTarget(str(to_type)),
                    id=str(to_id),
                    title=titulo,
                    reviewable=EdgeTarget(str(to_type)) is not EdgeTarget.RAG_ANSWER,
                )
                agrupado.setdefault(etiqueta, {})[(dependiente.kind.value, dependiente.id)] = (
                    dependiente
                )
            return {
                etiqueta: tuple(dependientes.values())
                for etiqueta, dependientes in agrupado.items()
            }

    def artifact_sections(self, artifact_id: str) -> tuple[str, ...]:
        """Las secciones de las que depende un derivado, con su etiqueta: su procedencia."""
        with self._session_factory() as session:
            filas = session.execute(
                select(DocumentSectionRecord, EvidenceSpanRecord.section_id)
                .select_from(DependencyEdgeRecord)
                .join(
                    EvidenceSpanRecord,
                    (DependencyEdgeRecord.from_type == EdgeSource.EVIDENCE_SPAN.value)
                    & (DependencyEdgeRecord.from_id == EvidenceSpanRecord.id),
                )
                .join(
                    DocumentSectionRecord,
                    DocumentSectionRecord.id == EvidenceSpanRecord.section_id,
                )
                .where(
                    DependencyEdgeRecord.to_type == EdgeTarget.DERIVED_ARTIFACT.value,
                    DependencyEdgeRecord.to_id == artifact_id,
                )
            ).all()
        por_seccion: dict[str, str] = {}
        for seccion, _ in filas:
            por_seccion.setdefault(seccion.id, section_label(seccion.title, seccion.ordinal))
        return tuple(por_seccion.values())

    def spans_of_sections(self, section_ids: Sequence[str]) -> tuple[str, ...]:
        """Los fragmentos de unas secciones: las entradas exactas de un resumen extractivo."""
        if not section_ids:
            return ()
        with self._session_factory() as session:
            filas = session.execute(
                select(EvidenceSpanRecord.id)
                .where(EvidenceSpanRecord.section_id.in_(tuple(section_ids)))
                .order_by(EvidenceSpanRecord.ordinal)
            ).scalars()
            return tuple(str(span_id) for span_id in filas)

    # ------------------------------------------------------------------ conjuntos de cambios

    def create_change_set(
        self,
        *,
        document_id: str,
        previous_version_id: str,
        new_version_id: str,
        sections: Sequence[SectionChangeView],
        affected: Sequence[AffectedView],
        counters: Mapping[str, int],
        effect_note: str,
        notes: Sequence[str],
        now: datetime,
    ) -> ChangeSetView:
        with self._session_factory() as session:
            fila = ChangeSetRecord(
                id=_new_id(),
                document_id=document_id,
                previous_version_id=previous_version_id,
                new_version_id=new_version_id,
                status="proposed",
                sections_json=json.dumps(
                    [
                        {"label": s.label, "kind": s.kind, "left": s.left, "right": s.right}
                        for s in sections
                    ],
                    ensure_ascii=False,
                ),
                affected_json=json.dumps(
                    [
                        {
                            "kind": a.kind,
                            "id": a.id,
                            "title": a.title,
                            "sections": list(a.sections),
                            "reason": a.reason,
                            "reviewable": a.reviewable,
                        }
                        for a in affected
                    ],
                    ensure_ascii=False,
                ),
                sections_changed=int(counters.get("changed", 0)),
                sections_added=int(counters.get("added", 0)),
                sections_removed=int(counters.get("removed", 0)),
                sections_unchanged=int(counters.get("unchanged", 0)),
                effect_note=effect_note,
                created_at=now,
            )
            session.add(fila)
            session.flush()
            vista = self._change_view(session, fila, notes=tuple(notes))
            session.commit()
            return vista

    def change_set(self, change_id: str) -> ChangeSetView | None:
        with self._session_factory() as session:
            fila = session.get(ChangeSetRecord, change_id)
            return None if fila is None else self._change_view(session, fila)

    def change_sets(
        self,
        *,
        document_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> tuple[ChangeSetView, ...]:
        with self._session_factory() as session:
            consulta = (
                select(ChangeSetRecord).order_by(ChangeSetRecord.created_at.desc()).limit(limit)
            )
            if document_id is not None:
                consulta = consulta.where(ChangeSetRecord.document_id == document_id)
            if status is not None:
                consulta = consulta.where(ChangeSetRecord.status == status)
            return tuple(
                self._change_view(session, fila) for fila in session.execute(consulta).scalars()
            )

    def proposed_for_version(self, new_version_id: str) -> ChangeSetView | None:
        """La propuesta pendiente de una versión, si la hay: es lo que impide aceptarla a ciegas."""
        with self._session_factory() as session:
            fila = session.execute(
                select(ChangeSetRecord).where(
                    ChangeSetRecord.new_version_id == new_version_id,
                    ChangeSetRecord.status == "proposed",
                )
            ).scalar_one_or_none()
            return None if fila is None else self._change_view(session, fila)

    def set_status(
        self,
        change_id: str,
        *,
        status: str,
        now: datetime,
        actor: str = "local",
    ) -> ChangeSetView | None:
        with self._session_factory() as session:
            fila = session.get(ChangeSetRecord, change_id)
            if fila is None:
                return None
            fila.status = status
            fila.reviewed_by = actor
            if status == "confirmed":
                fila.confirmed_at = now
            if status == "discarded":
                fila.discarded_at = now
            session.flush()
            vista = self._change_view(session, fila)
            session.commit()
            return vista

    # ------------------------------------------------------------------ vistas

    @staticmethod
    def _dependent_title(session: Session, to_type: str, to_id: str) -> str | None:
        if to_type == EdgeTarget.DERIVED_ARTIFACT.value:
            fila = session.get(DerivedArtifactRecord, to_id)
            return None if fila is None else fila.title
        if to_type == EdgeTarget.QUESTION_VERSION.value:
            from opofuente.infrastructure.db_models import QuestionVersionRecord

            pregunta = session.get(QuestionVersionRecord, to_id)
            return None if pregunta is None else f"pregunta {pregunta.stable_key}"
        if to_type == EdgeTarget.RAG_ANSWER.value:
            return "respuesta guardada sobre este material"
        return None

    @staticmethod
    def _version_label(session: Session, version_id: str) -> str | None:
        version = session.get(DocumentVersionRecord, version_id)
        if version is None:
            return None
        return version.version_label or version.id

    def _artifact_view(self, session: Session, fila: DerivedArtifactRecord) -> DerivedArtifactView:
        version = session.get(DocumentVersionRecord, fila.document_version_id)
        documento = (
            None
            if version is None
            else session.get(LogicalDocumentRecord, version.logical_document_id)
        )
        return DerivedArtifactView(
            id=fila.id,
            kind=fila.kind,
            title=fila.title,
            content=fila.content,
            document_version_id=fila.document_version_id,
            document_id="" if documento is None else documento.id,
            document_title="documento desconocido"
            if documento is None
            else documento.canonical_title,
            generator=fila.generator,
            prompt_template_version=fila.prompt_template_version,
            model=fila.model,
            review_status=fila.review_status,
            needs_review=bool(fila.needs_review),
            needs_review_reason=fila.needs_review_reason,
            needs_review_at=as_utc(fila.needs_review_at),
            reviewed_at=as_utc(fila.reviewed_at),
            created_at=as_utc(fila.created_at) or fila.created_at,
            updated_at=as_utc(fila.updated_at) or fila.updated_at,
            sections=self.artifact_sections(fila.id),
        )

    def _change_view(
        self, session: Session, fila: ChangeSetRecord, *, notes: tuple[str, ...] = ()
    ) -> ChangeSetView:
        documento = session.get(LogicalDocumentRecord, fila.document_id)
        return ChangeSetView(
            id=fila.id,
            document_id=fila.document_id,
            document_title="documento desconocido"
            if documento is None
            else documento.canonical_title,
            previous_version_id=fila.previous_version_id,
            previous_version_label=self._version_label(session, fila.previous_version_id),
            new_version_id=fila.new_version_id,
            new_version_label=self._version_label(session, fila.new_version_id),
            status=fila.status,
            created_at=as_utc(fila.created_at) or fila.created_at,
            confirmed_at=as_utc(fila.confirmed_at),
            discarded_at=as_utc(fila.discarded_at),
            reviewed_by=fila.reviewed_by,
            sections=tuple(
                SectionChangeView(
                    label=str(elemento.get("label", "")),
                    kind=str(elemento.get("kind", "unchanged")),
                    left=None if elemento.get("left") is None else str(elemento["left"]),
                    right=None if elemento.get("right") is None else str(elemento["right"]),
                )
                for elemento in _json_lista(fila.sections_json)
            ),
            affected=tuple(
                AffectedView(
                    kind=str(elemento.get("kind", "")),
                    id=str(elemento.get("id", "")),
                    title=str(elemento.get("title", "")),
                    sections=_secciones_de(elemento.get("sections")),
                    reason=str(elemento.get("reason", "")),
                    reviewable=bool(elemento.get("reviewable", True)),
                )
                for elemento in _json_lista(fila.affected_json)
            ),
            sections_changed=fila.sections_changed,
            sections_added=fila.sections_added,
            sections_removed=fila.sections_removed,
            sections_unchanged=fila.sections_unchanged,
            effect_note=fila.effect_note,
            notes=notes,
        )


__all__ = ["SqlAlchemyChangeRepository"]
