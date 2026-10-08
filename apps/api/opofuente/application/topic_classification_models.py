"""Modelos del clasificador de preguntas (F4): lo que se lee, lo que se decide y lo que se informa.

Son modelos de **lectura y de informe**, no entidades: el clasificador no tiene tabla propia. Lo que
escribe lo escribe por el camino auditado del banco de preguntas, y lo que deja aquí es el informe
que el propietario lee para decidir si sigue con el resto del banco.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from opofuente.domain.topic_classification import (
    PRECIO_ENTRADA_USD_POR_MILLON,
    PRECIO_SALIDA_USD_POR_MILLON,
)

#: Cuántas notas se guardan por banco y cuántas se imprimen. Lo que no cabe se cuenta: un informe de
#: miles de preguntas no puede llevar miles de líneas, pero tampoco puede esconder que las hubo.
NOTAS_POR_BANCO = 100
NOTAS_IMPRESAS = 10


@dataclass(frozen=True, slots=True)
class BankToClassify:
    """Un banco por clasificar: el conjunto de preguntas y cuántas le faltan por tener tema.

    El «banco» es el **conjunto** (`question_sets`), que es como está agrupado el material por su
    origen: un examen de Zaragoza, un mazo de la comunidad, un documento del BOE. Clasificar por
    bancos y de mayor a menor es lo que permite parar tras los dos primeros y mirar la calidad.
    """

    set_id: str
    title: str
    pending: int


@dataclass(slots=True)
class BankReport:
    """Lo que ha pasado en un banco: cuántas preguntas y en qué han quedado."""

    set_id: str
    title: str
    pending: int
    batches: int = 0
    processed: int = 0
    #: Asignadas con confianza alta (`accepted`): entran y cuentan.
    assigned: int = 0
    #: Guardadas como propuesta (`provisional`): cola de revisión, no cuentan.
    proposed: int = 0
    #: Declaradas fuera del temario, con su motivo.
    out_of_syllabus: int = 0
    #: Sin escribir nada (confianza por debajo del mínimo o el modelo se abstuvo).
    nothing: int = 0
    #: Filas con las que **no** se pudo hacer nada: código que no está en el temario, etc.
    errors: int = 0
    #: Filas que sí se intentaron escribir y el servicio rechazó.
    write_errors: int = 0
    #: Ya estaban asignadas de una pasada anterior (el lote es idempotente).
    existing: int = 0
    #: Las primeras notas del banco (qué se dudó y por qué). Las demás se cuentan, no se guardan.
    notes: list[str] = field(default_factory=list)
    #: Notas que no se han guardado por no engordar el informe de una corrida de miles de preguntas.
    omitted_notes: int = 0

    def add_note(self, texto: str) -> None:
        """Guarda una nota si cabe; si no, la cuenta.

        Una corrida real clasifica miles de preguntas y cada duda produce una nota: guardarlas
        todas haría que el informe pesara más que el trabajo. Se conservan las primeras —que es
        donde se ve el patrón— y se dice cuántas quedaron fuera, en lugar de callarlo.
        """
        if len(self.notes) < NOTAS_POR_BANCO:
            self.notes.append(texto)
        else:
            self.omitted_notes += 1

    @property
    def extra_notes(self) -> int:
        """Las notas que no se imprimen: las de más allá de las diez primeras y las no guardadas."""
        return max(len(self.notes) - NOTAS_IMPRESAS, 0) + self.omitted_notes


@dataclass(frozen=True, slots=True)
class ClassificationReport:
    """El informe de la corrida: por banco, con totales y con lo que costó."""

    opposition_code: str
    dry_run: bool
    banks: tuple[BankReport, ...]
    input_tokens: int = 0
    output_tokens: int = 0

    def _total(self, attr: str) -> int:
        return sum(int(getattr(banco, attr)) for banco in self.banks)

    @property
    def pending(self) -> int:
        return self._total("pending")

    @property
    def processed(self) -> int:
        return self._total("processed")

    @property
    def assigned(self) -> int:
        return self._total("assigned")

    @property
    def proposed(self) -> int:
        return self._total("proposed")

    @property
    def out_of_syllabus(self) -> int:
        return self._total("out_of_syllabus")

    @property
    def nothing(self) -> int:
        return self._total("nothing")

    @property
    def errors(self) -> int:
        return self._total("errors") + self._total("write_errors")

    @property
    def existing(self) -> int:
        return self._total("existing")

    @property
    def batches(self) -> int:
        return self._total("batches")

    @property
    def estimated_cost_usd(self) -> float:
        """Lo que costaría la corrida con los precios de valle y los tokens que se gastaron.

        Es una **estimación**, no una factura: la cifra buena la da el proveedor. Se calcula con los
        tokens que devolvió cada llamada, así que sirve para decidir si seguir o parar.
        """
        return (
            self.input_tokens / 1_000_000 * PRECIO_ENTRADA_USD_POR_MILLON
            + self.output_tokens / 1_000_000 * PRECIO_SALIDA_USD_POR_MILLON
        )

    def lines(self) -> tuple[str, ...]:
        """El informe en texto, que es lo que se imprime y lo que se pega en la revisión."""
        cabecera = (
            f"Clasificación de «{self.opposition_code}» · {len(self.banks)} banco(s) · "
            f"{self.processed} pregunta(s) de {self.pending} pendiente(s)"
        )
        if self.dry_run:
            cabecera += " · ENSAYO: no se ha escrito nada"
        lineas = [cabecera, ""]
        for banco in self.banks:
            lineas.append(f"[{banco.pending:>5} pendientes] {banco.title}")
            lineas.append(f"    procesadas {banco.processed} en {banco.batches} lote(s)")
            lineas.append(
                f"    asignadas {banco.assigned} · a la cola de revisión {banco.proposed} · "
                f"fuera de temario {banco.out_of_syllabus} · sin propuesta {banco.nothing}"
            )
            if banco.existing or banco.errors:
                lineas.append(
                    f"    ya estaban {banco.existing} · errores de propuesta {banco.errors} · "
                    f"errores de escritura {banco.write_errors}"
                )
            lineas.extend(f"    · {nota}" for nota in banco.notes[:NOTAS_IMPRESAS])
            if banco.extra_notes:
                lineas.append(f"    · … y {banco.extra_notes} nota(s) más")
        lineas.extend(
            [
                "",
                f"Total: asignadas {self.assigned}, a la cola {self.proposed}, fuera de temario "
                f"{self.out_of_syllabus}, sin propuesta {self.nothing}, errores {self.errors}, "
                f"ya estaban {self.existing}",
                f"Llamadas: {self.batches} · tokens: {self.input_tokens} entrada / "
                f"{self.output_tokens} salida · coste estimado "
                f"{self.estimated_cost_usd:.4f} $ (precios de valle)",
            ]
        )
        return tuple(lineas)


__all__ = ["BankReport", "BankToClassify", "ClassificationReport"]
