"""Los modelos del informe de apuntes (pasos B-E) y el nodo del tema como lo ve el redactor.

El informe es lo que se lee **después** de una corrida larga: por tema, cuántos hechos se sacaron,
cuántos apartados se escribieron, cuántas preguntas quedaron cubiertas y por qué no lo quedaron las
demás. Se dice por epígrafe y con los dos motivos separados (lo que falta en los apuntes y lo que
falta en la clave), porque son dos trabajos distintos: el primero se arregla escribiendo, el segundo
revisando la pregunta.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from opofuente.domain.notes_quality import RevisionApuntes
from opofuente.domain.topic_notes import (
    Coverage,
    Motivo,
    TokenLedger,
)

#: Nombres legibles de los motivos, para el informe. El código se guarda; la frase se imprime.
MOTIVO_TEXTO: dict[Motivo, str] = {
    Motivo.SIN_FRASE_EN_LOS_APUNTES: "no hay ninguna frase en los apuntes que la justifique",
    Motivo.LETRA_NO_COINCIDE: "en conflicto: la frase está, pero la clave dice otra opción",
    Motivo.CLAVE_CONTRADICE_LA_NORMA: "la clave contradice la norma o el material",
    Motivo.CLAVE_SIN_DEFINIR: "la pregunta no tiene clave con la que comprobarla",
}


@dataclass(frozen=True, slots=True)
class NotesNode:
    """El tema como lo ve el redactor: su código legible, su título y sus epígrafes oficiales."""

    node_id: str
    code: str
    title: str
    epigraphs: tuple[tuple[str, str], ...]

    @property
    def epigraph_codes(self) -> tuple[str, ...]:
        return tuple(codigo for codigo, _ in self.epigraphs)


@dataclass(slots=True)
class SectionReport:
    """Lo que se escribe de un apartado: sus hechos, su texto y qué hechos no se encontraron."""

    key: str
    title: str
    epigraph_code: str
    anchor: str
    facts: int = 0
    body_chars: int = 0
    hechos_sin_integrar: tuple[str, ...] = ()
    needs_review_reason: str | None = None


@dataclass(slots=True)
class CoverageReport:
    """El recuento de la comprobación, con los dos motivos de duda separados.

    `conflicts` va aparte de `covered` y de las dudas a propósito: es la cuenta que destapó la
    revisión del propietario (96 preguntas de los tres pilotos que se contaban como cubiertas
    diciendo otra letra que su clave). Una pregunta en conflicto **no** está cubierta y va a la cola
    de revisión, con la clave delante.
    """

    groups: int = 0
    covered: int = 0
    covered_primera_vuelta: int = 0
    covered_tras_anadido: int = 0
    covered_con_clave_activa: int = 0
    covered_sin_clave: int = 0
    conflicts: int = 0
    conflicts_con_clave_activa: int = 0
    conflicts_con_clave_borrador: int = 0
    huecos_apuntes: int = 0
    huecos_clave: int = 0
    dudosas_apuntes: int = 0
    dudosas_clave: int = 0
    #: Preguntas que los apuntes **sí** contestan pero cuya clave señaló el paso B como contraria a
    #: la
    #: norma o al material. Son incidencias de la pregunta, no de los apuntes.
    incidencias_clave_marcada: int = 0
    por_motivo: dict[Motivo, int] = field(default_factory=dict)

    @property
    def finales(self) -> int:
        return self.covered + self.dudosas_apuntes + self.dudosas_clave + self.conflicts

    @property
    def en_revision(self) -> int:
        """Las que el propietario tiene que mirar: dudas por los apuntes, dudas por la clave y
        conflictos de letra."""
        return self.dudosas_apuntes + self.dudosas_clave + self.conflicts

    def add(
        self, coverage: Coverage, note: Motivo | None, *, attempts: int, clave_activa: bool
    ) -> None:
        if coverage is Coverage.CUBIERTA:
            self.covered += 1
            if attempts > 1:
                self.covered_tras_anadido += 1
            else:
                self.covered_primera_vuelta += 1
            if clave_activa:
                self.covered_con_clave_activa += 1
            else:
                self.covered_sin_clave += 1
        elif coverage is Coverage.HUECO:
            return
        elif coverage is Coverage.CONFLICTO:
            self.conflicts += 1
            if clave_activa:
                self.conflicts_con_clave_activa += 1
            else:
                self.conflicts_con_clave_borrador += 1
            if note is not None:
                self.por_motivo[note] = self.por_motivo.get(note, 0) + 1
        else:
            if note is not None:
                self.por_motivo[note] = self.por_motivo.get(note, 0) + 1
            if note is not None and note.es_de_los_apuntes:
                self.dudosas_apuntes += 1
            else:
                self.dudosas_clave += 1


@dataclass(slots=True)
class TopicNotesReport:
    """El informe de un tema: lo que se sacó, lo que se escribió, lo que se cubrió y lo que
    costó."""

    topic_code: str
    topic_title: str
    node_id: str
    groups: int = 0
    questions: int = 0
    facts: int = 0
    facts_new: int = 0
    hechos_dudosos: int = 0
    sections: tuple[SectionReport, ...] = ()
    coverage: CoverageReport = field(default_factory=CoverageReport)
    revision: RevisionApuntes | None = None
    ledger: TokenLedger = field(default_factory=TokenLedger)
    failed_batches: int = 0
    dry_run: bool = False
    version_created: bool | None = None
    notes: str = ""

    @property
    def hechos_sin_integrar(self) -> int:
        return sum(len(apartado.hechos_sin_integrar) for apartado in self.sections)

    @property
    def estimated_cost_usd(self) -> float:
        return self.ledger.estimated_cost_usd

    def add_notes(self, texto: str | None) -> None:
        if not texto:
            return
        self.notes = f"{self.notes}\n{texto}".strip() if self.notes else texto

    def lines(self) -> tuple[str, ...]:
        """El informe en texto, que es lo que se imprime y lo que se pega en la revisión."""
        cabecera = (
            f"[{self.topic_code}] {self.topic_title} · {self.groups} grupo(s) de preguntas "
            f"({self.questions} pregunta(s))"
        )
        if self.dry_run:
            cabecera += " · ENSAYO: no se ha escrito nada"
        lineas = [cabecera]
        lineas.append(
            f"    hechos {self.facts} ({self.facts_new} nuevos, {self.hechos_dudosos} con la clave "
            f"señalada) · apartados {len(self.sections)}"
        )
        cobertura = self.coverage
        lineas.append(
            f"    comprobadas {cobertura.finales} de {cobertura.groups} · cubiertas "
            f"{cobertura.covered} ({cobertura.covered_primera_vuelta} a la primera, "
            f"{cobertura.covered_tras_anadido} tras añadir) · en conflicto con la clave "
            f"{cobertura.conflicts} ({cobertura.conflicts_con_clave_activa} con clave activa) · "
            f"sin contestar por los apuntes {cobertura.dudosas_apuntes} · incidencias de clave "
            f"{cobertura.dudosas_clave} (+{cobertura.incidencias_clave_marcada} con la clave "
            "señalada)"
        )
        if cobertura.groups:
            porcentaje = 100.0 * cobertura.covered / cobertura.groups
            lineas.append(
                f"    cobertura {porcentaje:.1f} % · con clave activa "
                f"{cobertura.covered_con_clave_activa} · "
                f"sin clave clara {cobertura.covered_sin_clave} · a revisión "
                f"{cobertura.en_revision}"
            )
        if self.revision is not None:
            lineas.extend(self.revision.lines())
        for motivo, cuantos in sorted(cobertura.por_motivo.items(), key=lambda fila: -fila[1]):
            lineas.append(f"      {cuantos:>5} · {MOTIVO_TEXTO.get(motivo, motivo.value)}")
        if self.hechos_sin_integrar:
            lineas.append(
                f"    hechos que no se encontraron en el texto: {self.hechos_sin_integrar}"
            )
        for apartado in self.sections[:40]:
            aviso = (
                f" · revisar: {apartado.needs_review_reason}"
                if apartado.needs_review_reason
                else ""
            )
            lineas.append(
                f"    · {apartado.key} · {apartado.facts} hecho(s) · "
                f"{apartado.body_chars} caracteres{aviso}"
            )
        if len(self.sections) > 40:
            lineas.append(f"    · … y {len(self.sections) - 40} apartado(s) más")
        if self.failed_batches:
            lineas.append(
                f"    AVISO: {self.failed_batches} lote(s) fallaron y no se escribieron; volver a "
                f"ejecutar el mismo comando los reintenta"
            )
        if self.version_created is not None:
            lineas.append(
                "    versión del tema: "
                + ("guardada (nueva)" if self.version_created else "ya estaba guardada")
            )
        lineas.extend(f"    {linea}" for linea in self.ledger.lines())
        if self.notes:
            lineas.append(f"    {self.notes}")
        return tuple(lineas)


__all__ = [
    "MOTIVO_TEXTO",
    "CoverageReport",
    "NotesNode",
    "SectionReport",
    "TopicNotesReport",
]
