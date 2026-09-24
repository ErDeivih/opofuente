"""El dossier de un tema (S13): lo que el corpus dice de un nodo del programa, citado.

Reglas puras, sin base de datos ni red. Lo que se decide aquí, y por qué:

- **toda frase del dossier es una cita literal**. No hay prosa generada: las fuentes son los tramos
de
  evidencia que ya existen, con su documento, su versión, su sección y su página. Redactar hace
  falta
  un modelo, y eso es otra decisión (ADR-019);
- **lo que no se puede citar no se cita, y se dice**. Se aplica la misma regla que la búsqueda
  (`corpus_eligible`): una versión sin aceptar o un texto pobre no sostienen una cita. Lo que se
  queda
  fuera aparece como **hueco** con su motivo, en lugar de desaparecer sin explicación;
- **el mismo texto no se enseña dos veces**. Si dos fuentes traen el mismo tramo, se cita una vez y
la
  otra queda declarada como «también aquí», que es información, no ruido;
- **el orden es estable y explicable**: documento, versión, página y posición. Un dossier que cambia
de
  orden entre dos lecturas idénticas no se puede comparar con su versión anterior.

El **documento** del dossier (`dossier_document`) es la forma canónica de todo esto: es lo que se
guarda al archivar una versión y lo que se sirve por la API. Una sola forma para las dos cosas, con
su
versión de formato declarada, para que una versión guardada se pueda leer como se escribió.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from opofuente.domain.classification import MappingStatus
from opofuente.domain.rag import VersionMode, corpus_eligible

#: Versión del formato del dossier guardado. Si cambia la forma en que se archiva, sube: una versión
#: guardada se lee con la versión con la que se escribió (misma regla que las representaciones).
DOSSIER_FORMAT_VERSION = 1


class HoleCode(StrEnum):
    """Lo que el dossier **no** tiene, como código: la interfaz lo traduce, el dominio no escribe
    frases.

    Un cero sin motivo es indistinguible de un fallo, así que un tema sin material no devuelve «0
    pasajes»: devuelve el hueco con su nombre.
    """

    SIN_MATERIAL = "sin_material"
    """Al tema no le llega ningún documento: nadie ha clasificado material hacia él."""

    SIN_TEXTO = "sin_texto"
    """Hay material asignado, pero ninguna de sus representaciones tiene texto que citar."""

    NO_CITABLE = "no_citable"
    """Hay tramos, pero la versión o su calidad no sostienen una cita. El motivo va con el hueco."""

    SIN_VERSION_ACEPTADA = "sin_version_aceptada"
    """Todo lo que llega está en versiones sin aceptar: se lee, pero no como material confirmado."""

    MAPEO_PROVISIONAL = "mapeo_provisional"
    """Parte de lo citado se asignó al tema sin confirmar (automático o pendiente de revisión)."""

    REPETIDO_EN_OTRA_FUENTE = "repetido_en_otra_fuente"
    """El mismo texto aparece en más de una fuente: se cita una vez y se declara dónde más está."""


@dataclass(frozen=True, slots=True)
class Hole:
    """Un hueco del dossier: qué falta, cuántos casos y, si consta, el motivo literal del filtro."""

    code: HoleCode
    count: int = 0
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PassageFacts:
    """Un tramo de evidencia tal como sale de la base de datos, **antes** de decidir nada.

    Es la entrada del dominio: el repositorio no filtra por vigencia ni por calidad, porque eso son
    reglas y las reglas viven aquí.
    """

    evidence_id: str
    text: str
    normalized: str
    citation_label: str | None
    page: int | None
    section_title: str | None
    ordinal: int
    document_id: str
    document_title: str
    document_type: str
    authority_tier: str | None
    version_id: str
    version_label: str | None
    version_status: str
    quality: str | None
    mappings: tuple[str, ...] = ()
    valid_from: date | None = None
    valid_to: date | None = None


@dataclass(frozen=True, slots=True)
class Passage:
    """Un tramo citable dentro del dossier, con su procedencia y su repetición declarada."""

    evidence_id: str
    text: str
    citation_label: str | None
    page: int | None
    section_title: str | None
    ordinal: int
    quality: str | None
    repeated_in: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Source:
    """Una fuente del tema: un documento en una versión concreta, con sus tramos citables."""

    document_id: str
    document_title: str
    document_type: str
    authority_tier: str | None
    version_id: str
    version_label: str | None
    version_status: str
    quality: str | None
    mappings: tuple[str, ...]
    passages: tuple[Passage, ...]

    @property
    def passages_count(self) -> int:
        return len(self.passages)

    @property
    def provisional(self) -> bool:
        """¿Esta fuente se sostiene **solo** con mapeos sin confirmar?"""
        return bool(self.mappings) and all(
            estado != MappingStatus.ACCEPTED.value for estado in self.mappings
        )


@dataclass(frozen=True, slots=True)
class TopicDossier:
    """El tema tal como el sistema puede sostenerlo hoy: fuentes, citas, huecos y qué se usó."""

    node_id: str
    path: str
    title: str
    depth: int
    generated_at: datetime
    sources: tuple[Source, ...] = ()
    holes: tuple[Hole, ...] = ()
    accepted_sources: int = 0
    provisional_sources: int = 0
    content_hash: str = ""
    version_id: str | None = None
    previous_version_id: str | None = None

    @property
    def passages_total(self) -> int:
        return sum(fuente.passages_count for fuente in self.sources)

    @property
    def sources_total(self) -> int:
        return len(self.sources)

    @property
    def empty(self) -> bool:
        return self.passages_total == 0

    @property
    def provisional(self) -> bool:
        return self.provisional_sources > 0


@dataclass
class _SourceDraft:
    """Borrador de fuente mientras se recorre la lista ordenada de tramos. No sale del módulo."""

    document_id: str
    document_title: str
    document_type: str
    authority_tier: str | None
    version_id: str
    version_label: str | None
    version_status: str
    quality: str | None
    mappings: tuple[str, ...]
    passages: list[Passage]

    @classmethod
    def from_facts(cls, facts: PassageFacts) -> _SourceDraft:
        return cls(
            document_id=facts.document_id,
            document_title=facts.document_title,
            document_type=facts.document_type,
            authority_tier=facts.authority_tier,
            version_id=facts.version_id,
            version_label=facts.version_label,
            version_status=facts.version_status,
            quality=facts.quality,
            mappings=facts.mappings,
            passages=[],
        )


def _clave_fuente(facts: PassageFacts) -> tuple[str, str, str]:
    """Agrupa por obra y versión: el mismo documento en dos versiones son dos fuentes distintas."""
    return (facts.document_title, facts.version_label or "", facts.version_id)


def _clave_tramo(facts: PassageFacts) -> tuple[int, int, str]:
    return (facts.page or 0, facts.ordinal, facts.evidence_id)


def _firma_texto(texto: str) -> str:
    """Firma de comparación: espacios colapsados y sin distinguir mayúsculas."""
    return " ".join(texto.split()).casefold()


def build_dossier(
    *,
    node_id: str,
    path: str,
    title: str,
    depth: int,
    generated_at: datetime,
    facts: tuple[PassageFacts, ...],
    mappings_total: int = 0,
    reference_date: date | None = None,
) -> TopicDossier:
    """Monta el dossier de un tema a partir de los tramos que le llegan.

    El orden de los pasos explica el resultado: primero se decide **qué es citable**, después se
    agrupa por fuente, luego se quita lo repetido (dejando dicho dónde más está) y al final se
    cuentan los huecos con lo que quedó fuera.
    """
    citables: list[PassageFacts] = []
    motivos: dict[str, int] = {}
    for tramo in facts:
        decision = corpus_eligible(
            version_status=tramo.version_status,
            representation_quality=tramo.quality,
            valid_from=tramo.valid_from,
            valid_to=tramo.valid_to,
            reference_date=reference_date,
            version_mode=VersionMode.CURRENT,
        )
        if not decision.eligible:
            motivo = decision.reason or "el corpus no lo considera citable"
            motivos[motivo] = motivos.get(motivo, 0) + 1
            continue
        citables.append(tramo)

    fuentes: dict[tuple[str, str, str], _SourceDraft] = {}
    repetidos: dict[str, list[str]] = {}
    primera_aparicion: dict[str, str] = {}

    for tramo in sorted(citables, key=lambda fila: (_clave_fuente(fila), _clave_tramo(fila))):
        clave = _clave_fuente(tramo)
        borrador = fuentes.get(clave)
        if borrador is None:
            borrador = _SourceDraft.from_facts(tramo)
            fuentes[clave] = borrador
        etiqueta = tramo.citation_label or tramo.document_title
        # Los mapeos que sostienen a la fuente son la **unión** de los de sus tramos: un mismo
        # documento puede estar asignado al tema por su artefacto y, además, por una sección.
        borrador.mappings = tuple(sorted(set(borrador.mappings) | set(tramo.mappings)))
        firma = _firma_texto(tramo.normalized or tramo.text)
        if firma and firma in primera_aparicion:
            repetidos.setdefault(primera_aparicion[firma], []).append(etiqueta)
            continue
        if firma:
            primera_aparicion[firma] = tramo.evidence_id
        borrador.passages.append(
            Passage(
                evidence_id=tramo.evidence_id,
                text=tramo.text,
                citation_label=tramo.citation_label,
                page=tramo.page,
                section_title=tramo.section_title,
                ordinal=tramo.ordinal,
                quality=tramo.quality,
            )
        )

    completas: list[Source] = []
    for borrador in fuentes.values():
        if not borrador.passages:
            # Todo su texto estaba repetido en otra fuente: no aporta nada nuevo y por eso no se
            # enseña como fuente. Se sabe que existe: el hueco de repetición lo cuenta.
            continue
        completas.append(
            Source(
                document_id=borrador.document_id,
                document_title=borrador.document_title,
                document_type=borrador.document_type,
                authority_tier=borrador.authority_tier,
                version_id=borrador.version_id,
                version_label=borrador.version_label,
                version_status=borrador.version_status,
                quality=borrador.quality,
                mappings=borrador.mappings,
                passages=tuple(
                    Passage(
                        evidence_id=pasaje.evidence_id,
                        text=pasaje.text,
                        citation_label=pasaje.citation_label,
                        page=pasaje.page,
                        section_title=pasaje.section_title,
                        ordinal=pasaje.ordinal,
                        quality=pasaje.quality,
                        repeated_in=tuple(sorted(set(repetidos.get(pasaje.evidence_id, ())))),
                    )
                    for pasaje in borrador.passages
                ),
            )
        )

    aceptadas = sum(1 for fuente in completas if not fuente.provisional)
    provisionales = sum(1 for fuente in completas if fuente.provisional)
    huecos = _huecos(
        facts=facts,
        fuentes=completas,
        motivos=motivos,
        repetidos=sum(len(sitios) for sitios in repetidos.values()),
        provisionales=provisionales,
        mappings_total=mappings_total,
    )
    return TopicDossier(
        node_id=node_id,
        path=path,
        title=title,
        depth=depth,
        generated_at=generated_at,
        sources=tuple(completas),
        holes=huecos,
        accepted_sources=aceptadas,
        provisional_sources=provisionales,
        content_hash=dossier_signature(
            sources=tuple(completas),
            holes=huecos,
            accepted_sources=aceptadas,
            provisional_sources=provisionales,
        ),
    )


def _huecos(
    *,
    facts: tuple[PassageFacts, ...],
    fuentes: list[Source],
    motivos: dict[str, int],
    repetidos: int,
    provisionales: int,
    mappings_total: int,
) -> tuple[Hole, ...]:
    """Los huecos, en orden estable y sin ceros decorativos: un hueco que no existe no se enseña.

    La diferencia que importa aquí es entre **no tener material** y **tener material que todavía no
    tiene nada que citar**: son dos situaciones distintas para quien estudia, y decir la primera
    cuando pasa la segunda sería acusar al programa de un hueco que es del material.
    """
    huecos: list[Hole] = []
    if not facts:
        huecos.append(
            Hole(code=HoleCode.SIN_MATERIAL)
            if mappings_total == 0
            else Hole(code=HoleCode.SIN_TEXTO, count=mappings_total)
        )
    for motivo, cuantos in sorted(motivos.items()):
        huecos.append(Hole(code=HoleCode.NO_CITABLE, count=cuantos, reason=motivo))
    if fuentes and all(fuente.version_status != "accepted" for fuente in fuentes):
        huecos.append(Hole(code=HoleCode.SIN_VERSION_ACEPTADA, count=len(fuentes)))
    if provisionales:
        huecos.append(Hole(code=HoleCode.MAPEO_PROVISIONAL, count=provisionales))
    if repetidos:
        huecos.append(Hole(code=HoleCode.REPETIDO_EN_OTRA_FUENTE, count=repetidos))
    return tuple(huecos)


def dossier_signature(
    *,
    sources: tuple[Source, ...],
    holes: tuple[Hole, ...],
    accepted_sources: int,
    provisional_sources: int,
) -> str:
    """Huella del contenido del dossier: dos lecturas con la misma huella son el mismo dossier.

    Se calcula sobre lo que el usuario lee (fuentes, citas, procedencia y huecos) y **no** sobre la
    fecha: volver a mirar el mismo tema no crea una versión nueva. Eso es lo que permite decir «esto
    es lo que sabía antes y esto lo que sé ahora» sin ruido.
    """
    cuerpo = {
        "sources": [
            {
                "document_id": fuente.document_id,
                "version_id": fuente.version_id,
                "version_status": fuente.version_status,
                "mappings": sorted(fuente.mappings),
                "passages": [
                    {
                        "evidence_id": pasaje.evidence_id,
                        "text": pasaje.text,
                        "page": pasaje.page,
                        "ordinal": pasaje.ordinal,
                        "repeated_in": list(pasaje.repeated_in),
                    }
                    for pasaje in fuente.passages
                ],
            }
            for fuente in sources
        ],
        "holes": [
            {"code": hueco.code.value, "count": hueco.count, "reason": hueco.reason}
            for hueco in holes
        ],
        "accepted_sources": accepted_sources,
        "provisional_sources": provisional_sources,
    }
    serializado = json.dumps(cuerpo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


# --- la forma canónica: lo que se guarda y lo que se sirve es lo mismo ---------------------------


def dossier_document(dossier: TopicDossier) -> dict[str, Any]:
    """El dossier como documento: la forma que se guarda al archivarlo y la que se sirve."""
    return {
        "format_version": DOSSIER_FORMAT_VERSION,
        "node_id": dossier.node_id,
        "path": dossier.path,
        "title": dossier.title,
        "depth": dossier.depth,
        "generated_at": dossier.generated_at.isoformat(),
        "content_hash": dossier.content_hash,
        "version_id": dossier.version_id,
        "previous_version_id": dossier.previous_version_id,
        "sources_total": dossier.sources_total,
        "passages_total": dossier.passages_total,
        "accepted_sources": dossier.accepted_sources,
        "provisional_sources": dossier.provisional_sources,
        "provisional": dossier.provisional,
        "empty": dossier.empty,
        "sources": [
            {
                "document_id": fuente.document_id,
                "document_title": fuente.document_title,
                "document_type": fuente.document_type,
                "authority_tier": fuente.authority_tier,
                "version_id": fuente.version_id,
                "version_label": fuente.version_label,
                "version_status": fuente.version_status,
                "quality": fuente.quality,
                "mappings": list(fuente.mappings),
                "provisional": fuente.provisional,
                "passages_total": fuente.passages_count,
                "passages": [
                    {
                        "evidence_id": pasaje.evidence_id,
                        "text": pasaje.text,
                        "citation_label": pasaje.citation_label,
                        "page": pasaje.page,
                        "section_title": pasaje.section_title,
                        "ordinal": pasaje.ordinal,
                        "quality": pasaje.quality,
                        "repeated_in": list(pasaje.repeated_in),
                    }
                    for pasaje in fuente.passages
                ],
            }
            for fuente in dossier.sources
        ],
        "holes": [
            {"code": hueco.code.value, "count": hueco.count, "reason": hueco.reason}
            for hueco in dossier.holes
        ],
    }


def dossier_from_document(datos: Mapping[str, Any]) -> TopicDossier:
    """Reconstruye el dossier desde su documento (lo que hay guardado en una versión anterior)."""
    version_formato = int(datos.get("format_version", DOSSIER_FORMAT_VERSION))
    if version_formato != DOSSIER_FORMAT_VERSION:
        raise ValueError(
            f"el dossier guardado está en el formato {version_formato} y este lector lee el "
            f"{DOSSIER_FORMAT_VERSION}"
        )
    return TopicDossier(
        node_id=str(datos["node_id"]),
        path=str(datos["path"]),
        title=str(datos["title"]),
        depth=int(datos.get("depth", 0)),
        generated_at=_momento(datos["generated_at"]),
        sources=tuple(_fuente(fuente) for fuente in _lista(datos.get("sources"))),
        holes=tuple(
            Hole(
                code=HoleCode(str(hueco["code"])),
                count=int(hueco.get("count", 0)),
                reason=None if hueco.get("reason") is None else str(hueco["reason"]),
            )
            for hueco in _lista(datos.get("holes"))
        ),
        accepted_sources=int(datos.get("accepted_sources", 0)),
        provisional_sources=int(datos.get("provisional_sources", 0)),
        content_hash=str(datos.get("content_hash", "")),
        version_id=None if datos.get("version_id") is None else str(datos["version_id"]),
        previous_version_id=(
            None if datos.get("previous_version_id") is None else str(datos["previous_version_id"])
        ),
    )


def _fuente(datos: Mapping[str, Any]) -> Source:
    return Source(
        document_id=str(datos["document_id"]),
        document_title=str(datos["document_title"]),
        document_type=str(datos["document_type"]),
        authority_tier=_opcional(datos.get("authority_tier")),
        version_id=str(datos["version_id"]),
        version_label=_opcional(datos.get("version_label")),
        version_status=str(datos["version_status"]),
        quality=_opcional(datos.get("quality")),
        mappings=tuple(str(estado) for estado in _lista(datos.get("mappings"))),
        passages=tuple(
            Passage(
                evidence_id=str(pasaje["evidence_id"]),
                text=str(pasaje["text"]),
                citation_label=_opcional(pasaje.get("citation_label")),
                page=None if pasaje.get("page") is None else int(pasaje["page"]),
                section_title=_opcional(pasaje.get("section_title")),
                ordinal=int(pasaje.get("ordinal", 1)),
                quality=_opcional(pasaje.get("quality")),
                repeated_in=tuple(str(sitio) for sitio in _lista(pasaje.get("repeated_in"))),
            )
            for pasaje in _lista(datos.get("passages"))
        ),
    )


def _lista(valor: object) -> Sequence[Any]:
    if isinstance(valor, Sequence) and not isinstance(valor, str | bytes):
        return valor
    return ()


def _opcional(valor: object) -> str | None:
    return None if valor is None else str(valor)


def _momento(valor: object) -> datetime:
    if isinstance(valor, datetime):
        return valor
    return datetime.fromisoformat(str(valor))
