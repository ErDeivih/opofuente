"""Caso de uso: exportar el banco de preguntas (08_API-CONTRACT §11).

Tres decisiones que se ven en el resultado:

1. **se exporta lo que se puede estudiar**: preguntas con sus opciones y su respuesta cuando la
   plantilla activa la cubre. Lo que no la tiene se exporta diciéndolo, y se cuenta;
2. **la procedencia va dentro del fichero**, no en un correo aparte: conjunto, plantilla, origen,
   tema y las versiones de los documentos citados (§8 y 09_SECURITY §8);
3. **el material restringido se avisa** (y se puede dejar fuera): exportar es sacar material de la
   aplicación, y quien lo haga tiene que saber qué está sacando.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from opofuente.application.ports import Clock
from opofuente.application.question_models import QuestionSetView
from opofuente.domain.errors import NotFoundError, UnsupportedError
from opofuente.domain.export import (
    ExportDocument,
    ExportRow,
    export_warnings,
    render_anki_csv,
    render_markdown,
)
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository

#: Tope de preguntas por exportación. Un fichero de decenas de miles de tarjetas no lo importa nadie
#: de una vez, y sin tope una exportación accidental puede llenar el disco.
MAX_EXPORT_ITEMS = 2000

#: Derechos que impiden compartir el material. `unknown` es el valor conservador (09_SECURITY §8):
#: no se sabe si se puede compartir, así que se avisa igual.
RESTRICTED_RIGHTS = ("restricted", "unknown")


@dataclass(frozen=True, slots=True)
class ExportRequest:
    """Qué se exporta: un conjunto, un tema, o todo lo de una oposición."""

    opposition_id: str | None = None
    question_set_id: str | None = None
    node_id: str | None = None
    #: Dejar fuera el material con derechos restringidos. Por defecto **no** se deja fuera: es del
    #: usuario y se le avisa; quien prefiera no sacarlo, lo pide.
    include_restricted: bool = True
    title: str | None = None


class ExportService:
    def __init__(
        self,
        *,
        questions: SqlAlchemyQuestionRepository,
        documents: SqlAlchemyDocumentRepository,
        profiles: SqlAlchemyProfileRepository,
        exports_dir: Path,
        clock: Clock,
        version: str,
    ) -> None:
        self._questions = questions
        self._documents = documents
        self._profiles = profiles
        self._exports_dir = exports_dir
        self._clock = clock
        self._version = version

    # ------------------------------------------------------------------ las dos exportaciones

    def anki_csv(self, request: ExportRequest) -> ExportDocument:
        rows, avisos_alcance = self._rows(request)
        contenido, avisos_csv = render_anki_csv(rows)
        momento = self._clock.now()
        return self._escribir(
            content=contenido,
            extension="csv",
            formato="anki_csv",
            rows=rows,
            request=request,
            avisos=(*avisos_csv, *avisos_alcance, *export_warnings(rows)),
            momento=momento,
        )

    def markdown(self, request: ExportRequest) -> ExportDocument:
        rows, avisos_alcance = self._rows(request)
        momento = self._clock.now()
        contenido = render_markdown(
            rows,
            title=request.title or "Banco de preguntas",
            generated_at=momento,
            version=self._version,
        )
        return self._escribir(
            content=contenido,
            extension="md",
            formato="markdown",
            rows=rows,
            request=request,
            avisos=(*avisos_alcance, *export_warnings(rows)),
            momento=momento,
        )

    # ------------------------------------------------------------------ recoger las preguntas

    def _rows(self, request: ExportRequest) -> tuple[tuple[ExportRow, ...], tuple[str, ...]]:
        conjuntos = self._conjuntos(request)
        if not conjuntos:
            raise NotFoundError("conjunto de preguntas", request.question_set_id or "(ninguno)")

        nodo = None
        if request.node_id is not None:
            detalle = self._profiles.get_node(request.node_id)
            if detalle is None:
                raise NotFoundError("nodo del programa", request.node_id)
            nodo = detalle.node

        filas: list[ExportRow] = []
        excluidas = 0
        cortada = False
        for conjunto in conjuntos:
            clave_activa = next(
                (clave for clave in self._questions.list_keys(conjunto.id) if clave.is_active),
                None,
            )
            entradas = self._questions.entry_map(conjunto.id) if clave_activa else {}
            for pregunta in self._questions.all_questions(conjunto.id):
                if nodo is not None and nodo.id not in self._nodes_of(pregunta.id):
                    continue
                evidencia = self._questions.question_evidence(pregunta.id)
                citas = tuple(cita.citation_label or cita.text[:80].strip() for cita in evidencia)
                versiones = tuple(dict.fromkeys(cita.document_version_id for cita in evidencia))
                restringida = self._restringida(versiones)
                if restringida and not request.include_restricted:
                    excluidas += 1
                    continue
                entrada = entradas.get(pregunta.id)
                filas.append(
                    ExportRow(
                        stable_key=pregunta.stable_key,
                        question=pregunta.stem,
                        options=tuple(
                            (opcion.stable_key, opcion.text) for opcion in pregunta.options
                        ),
                        correct_option_keys=(
                            () if entrada is None else tuple(entrada.correct_option_keys)
                        ),
                        explanation=None if entrada is None else entrada.notes,
                        citations=citas,
                        document_titles=self._titulos(versiones),
                        document_versions=versiones,
                        opposition=self._nombre_oposicion(conjunto.opposition_id),
                        topic=None if nodo is None else nodo.title,
                        origin_type=pregunta.origin_type,
                        set_title=conjunto.title,
                        key_label=(
                            None
                            if clave_activa is None
                            else f"plantilla v{clave_activa.version_no}"
                        ),
                        restricted=restringida,
                    )
                )
                if len(filas) >= MAX_EXPORT_ITEMS:
                    cortada = True
                    break
            if cortada:
                break
        if not filas:
            raise UnsupportedError(
                "no hay ninguna pregunta que exportar con ese criterio: el conjunto está vacío, "
                "sus preguntas no están asignadas al tema pedido, o todas citan material "
                "restringido que se ha pedido dejar fuera"
            )
        avisos: list[str] = []
        if excluidas:
            avisos.append(
                f"{excluidas} pregunta(s) se han quedado fuera por citar material con derechos "
                "restringidos o sin determinar"
            )
        if cortada:
            # El tope existe para no llenar el disco, pero **no** puede recortar en silencio: un
            # fichero con la mitad del banco que nadie sabe que está a medias es peor que un error.
            avisos.append(
                f"la exportación se ha cortado en {MAX_EXPORT_ITEMS} preguntas: exporta por "
                "conjunto o por tema para llevarte el resto"
            )
        return tuple(filas), tuple(avisos)

    def _conjuntos(self, request: ExportRequest) -> tuple[QuestionSetView, ...]:
        if request.question_set_id is not None:
            conjunto = self._questions.get_set(request.question_set_id)
            return () if conjunto is None else (conjunto,)
        if request.opposition_id is None:
            return ()
        pagina = self._questions.list_sets(opposition_id=request.opposition_id, limit=200, offset=0)
        return tuple(pagina.sets)

    def _nodes_of(self, question_version_id: str) -> tuple[str, ...]:
        """Los nodos del programa a los que está asignada una pregunta (vacío si a ninguno)."""
        return self._questions.node_ids_of_question(question_version_id)

    def _restringida(self, versiones: Sequence[str]) -> bool:
        """¿Viene esta cita de material que no se puede compartir sin revisarlo?

        Sin registro de derechos se trata como restringido: es el valor conservador de
        `RightsView.is_restricted` (desconocido no es un permiso) y aquí significa «avisa al
        exportar».
        """
        for version_id in versiones:
            detalle = self._documents.version_detail(version_id)
            if detalle is None:
                return True
            derechos = detalle.version.rights
            if derechos is None or derechos.is_restricted:
                return True
        return False

    def _titulos(self, versiones: Sequence[str]) -> tuple[str, ...]:
        titulos: list[str] = []
        for version_id in versiones:
            detalle = self._documents.version_detail(version_id)
            titulos.append("documento desconocido" if detalle is None else detalle.document_title)
        return tuple(titulos)

    def _nombre_oposicion(self, opposition_id: str | None) -> str | None:
        if opposition_id is None:
            return None
        detalle = self._profiles.get_opposition(opposition_id)
        return None if detalle is None else detalle.opposition.name

    # ------------------------------------------------------------------ escribir

    def _escribir(
        self,
        *,
        content: str,
        extension: str,
        formato: str,
        rows: Sequence[ExportRow],
        request: ExportRequest,
        avisos: Sequence[str],
        momento: datetime,
    ) -> ExportDocument:
        """Escribe el fichero en `<datos>/exports` y devuelve lo que hay que saber de él."""
        self._exports_dir.mkdir(parents=True, exist_ok=True)
        nombre = f"{_slug(request.title or 'opofuente')}-{momento:%Y%m%d-%H%M%S}.{extension}"
        destino = self._exports_dir / nombre
        destino.write_text(content, encoding="utf-8")
        return ExportDocument(
            filename=nombre,
            content=content,
            format=formato,
            item_count=len(rows),
            documents=tuple(
                dict.fromkeys(
                    f"{titulo}: {version}"
                    for row in rows
                    for titulo, version in zip(
                        row.document_titles, row.document_versions, strict=False
                    )
                )
            ),
            warnings=tuple(dict.fromkeys(avisos)),
            provenance={
                "generated_at": momento.isoformat(),
                "opofuente": self._version,
                "question_sets": ", ".join(dict.fromkeys(row.set_title for row in rows)),
                "key_labels": ", ".join(
                    dict.fromkeys(row.key_label for row in rows if row.key_label)
                ),
                "oppositions": ", ".join(
                    dict.fromkeys(row.opposition for row in rows if row.opposition)
                ),
                "origin_types": ", ".join(sorted({row.origin_type for row in rows})),
                "path": str(destino),
            },
        )


def _slug(texto: str) -> str:
    """Nombre de fichero legible y seguro: sin acentos, sin espacios y sin rutas."""
    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    limpio = re.sub(r"[^a-z0-9]+", "-", sin_acentos).strip("-")
    return limpio[:60] or "opofuente"


__all__ = ["MAX_EXPORT_ITEMS", "RESTRICTED_RIGHTS", "ExportRequest", "ExportService"]
