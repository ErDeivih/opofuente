"""La revisión de los apuntes por el propietario: qué decide y **por qué** (F24, §4.3 del objetivo).

Es lo que faltaba del punto (4) del objetivo: el propietario tiene que poder **ver** qué temas están
publicados y cuáles en borrador, **leer** un borrador dentro del panel y **decidirlo** (aprobarlo o
rechazarlo con su nota). Tres cosas y las tres viven aquí, que es dominio puro y se puede probar sin
base de datos:

1. **la decisión** (`ReviewDecision`) y lo que se guarda con ella: la nota es opcional al aprobar y
   **obligatoria** al rechazar —un rechazo sin motivo deja el borrador igual de parado y encima sin
   saber por qué—;
2. **las razones por las que un tema no está publicado**, que son lo que el propietario lee: cada
   una con **su cifra** y con las palabras del motor, no con las de la trastienda. Las cifras **no
   se recalculan aquí**: llegan medidas desde las comprobaciones que el motor ya dejó guardadas
   (`CifrasDelTema`), y aquí solo se convierten en frases;
3. **qué impide publicar hoy**, que no es lo mismo que «por qué está en borrador»: un tema puede
   cumplir las dos puertas del §2.3 y seguir sin publicar porque nadie archivó su versión. Ese
   caso —el de I.4 medido el 14 de octubre de 2026, 90,2 %— se dice con esas palabras, porque es
   exactamente lo que el propietario necesita saber antes de pulsar «Aprobar».

**Lo que este módulo NO decide**: el listón del §2.3 (`COBERTURA_MINIMA`, que no se toca) ni si un
tema se publica. Publicar es **archivar la versión**, y eso lo sigue decidiendo el par de puertas de
siempre: aprobar un tema que no las pasa lo deja aprobado y **sin publicar**, con su motivo delante.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from opofuente.domain.errors import InvalidReviewError
from opofuente.domain.notes_reports import normalise_note
from opofuente.domain.numeros import porcentaje
from opofuente.domain.plural import con_numero
from opofuente.domain.topic_notes import COBERTURA_MINIMA, CategoriaIncidencia

#: El umbral del §2.3, en palabras, tal como se lee en la frase del motivo.
UMBRAL_TEXTO = f"{100 * COBERTURA_MINIMA:.0f} %"

#: Nombres de las categorías de la bandeja del motor, para las frases del motivo. Es el vocabulario
#: del §2 de los ajustes: son **los nombres de lo que el motor registró**, no frases nuestras.
NOMBRE_DE_CATEGORIA: dict[CategoriaIncidencia, str] = {
    CategoriaIncidencia.HUECO_SIN_MATERIAL: "huecos sin material",
    CategoriaIncidencia.CLAVE_SOSPECHOSA: "respuestas correctas que no cuadran",
    CategoriaIncidencia.PREGUNTA_AMBIGUA: "preguntas que no se pueden juzgar",
    CategoriaIncidencia.NORMA_CAMBIADA: "normas cambiadas",
    CategoriaIncidencia.PREGUNTA_MAL_IMPORTADA: "preguntas mal importadas",
    CategoriaIncidencia.CLAVE_NO_FIABLE: "claves en cuarentena",
}


class ReviewDecision(StrEnum):
    """Qué ha decidido el propietario sobre los apuntes de un tema.

    Son dos y no tres a propósito: «aprobado» y «rechazado» son las dos salidas del botón del panel,
    y **no hay un estado «pendiente» que guardar** porque no escribir nada ya significa eso. Un tema
    sin fila es un tema que nadie ha mirado; con fila, alguien dijo algo de él y lo firmó.
    """

    APPROVED = "approved"
    REJECTED = "rejected"


class MotivoDelBorrador(StrEnum):
    """El código de cada razón que se le da al propietario. El texto se compone al lado.

    Van del caso más general al más concreto y **en el orden en el que se leen**: primero qué le
    pasa al tema (sin apartados, publicado, a las puertas, sin llegar al listón, con la forma rota)
    y después el desglose de a quién le toca cada parte (los apuntes, la respuesta correcta, la
    norma).
    """

    SIN_APARTADOS = "sin_apartados"
    PUBLICADO = "publicado"
    RECHAZADO = "rechazado"
    A_LAS_PUERTAS = "a_las_puertas"
    COBERTURA = "cobertura"
    FORMA = "forma"
    HUECOS = "huecos"
    CONFLICTOS = "conflictos"
    CLAVES_EN_REVISION = "claves_en_revision"
    SIN_MATERIA = "sin_materia"
    INCIDENCIAS = "incidencias"
    SIN_DECISION = "sin_decision"
    #: La tabla del panel **no mide** los borradores (cuesta alrededor de un segundo por tema y la
    #: pantalla tiene que abrirse sin esperar): esta razón dice dónde está la cifra que falta.
    SIN_MEDIDA = "sin_medida"


@dataclass(frozen=True, slots=True)
class Razon:
    """Una razón con su cifra, ya escrita, para que la pantalla no componga frases de cifras.

    `figura` es la cifra **tal como se enseña** («489/542 = 90,2 %»), y va aparte del texto porque
    la pantalla la pinta con su propio peso: el propietario tiene que poder leer el número sin leer
    la frase. Componer la frase en el servidor es lo mismo que hace el resumen de preparación
    (`StudyReadinessStepSchema`): dos sitios que escriben la misma frase acaban diciendo cosas
    distintas.
    """

    code: MotivoDelBorrador
    text: str
    figure: str | None = None


@dataclass(frozen=True, slots=True)
class CifrasDelTema:
    """Lo que hace falta para explicar un tema, **medido** donde ya está.

    Nada de esto se recalcula en este módulo: la cobertura y la forma salen de las comprobaciones
    que el motor dejó guardadas (`apuntes --medir`, 0 $ y sin modelo), el número de incidencias de
    la bandeja sale de su tabla y la decisión, de la fila de la revisión. `form_failures` son las
    líneas de lo que no pasa, tal como las escribe la revisión de forma.
    """

    has_sections: bool
    published: bool
    #: Si la cobertura y la forma se han **medido** en esta lectura. Sin medir no se enseña ninguna
    #: cifra de puerta: un cero sin medir se leería como «cero preguntas cubiertas», que es mentira.
    measured: bool = False
    #: La puerta de cobertura: el número que decide, con su denominador de clave utilizable.
    covered: int = 0
    with_key: int = 0
    #: El segundo denominador, el de todas las que tienen clave. Se enseña, no decide.
    covered_all_keys: int = 0
    with_key_all_keys: int = 0
    #: La puerta de forma.
    form_passes: bool = True
    form_failures: tuple[str, ...] = ()
    #: Por qué no están cubiertas las que no lo están.
    sin_frase: int = 0
    conflictos: int = 0
    claves_marcadas: int = 0
    sin_materia: int = 0
    #: La bandeja del motor: cuántas esperan todavía una decisión, por categoría.
    incidencias_abiertas: int = 0
    incidencias_por_categoria: tuple[tuple[CategoriaIncidencia, int], ...] = ()
    #: Lo que decidió el propietario, si lo ha mirado.
    decision: ReviewDecision | None = None
    decision_note: str | None = None

    @property
    def cobertura(self) -> float:
        """Cubiertas sobre las que tienen clave utilizable. Es el número de la puerta."""
        if not self.with_key:
            return 0.0
        return self.covered / self.with_key

    @property
    def cobertura_texto(self) -> str:
        """La cifra de la puerta, tal como se enseña. Vacía si no se ha medido.

        En español y con **un** decimal (§2.2): aquí la décima **hace falta**, porque el listón es
        el 90 % y una cobertura de 89,7 % no es lo mismo que una de 90,2 %. El docstring de `Razon`
        escribe esta cifra con coma desde antes de este arreglo: el que estaba mal era el código.
        """
        if not self.measured:
            return ""
        return f"{self.covered}/{self.with_key} = {porcentaje(self.cobertura)}"

    @property
    def cobertura_todas_las_claves_texto(self) -> str:
        if not self.with_key_all_keys:
            return f"{self.covered_all_keys}/{self.with_key_all_keys}"
        return (
            f"{self.covered_all_keys}/{self.with_key_all_keys} = "
            f"{porcentaje(self.covered_all_keys / self.with_key_all_keys)}"
        )

    @property
    def pasa_cobertura(self) -> bool:
        return self.cobertura >= COBERTURA_MINIMA

    @property
    def pasa_las_puertas(self) -> bool:
        """Las dos puertas del §2.3 juntas, que es lo que decide si aprobar publica."""
        return self.pasa_cobertura and self.form_passes

    @property
    def le_faltan(self) -> int:
        """Cuántas preguntas cubiertas le faltan para llegar al listón. Cero si ya llega.

        La cuenta se hace con **enteros** (el listón en milésimas) y no con `math.ceil(0.9 * n)`:
        `0,9` no es exacto en binario, así que `0.9 * 10` da 9,000000000000002 y el techo diría 10
        donde el listón pide 9. Una cifra que se le enseña al propietario no puede fallar por un
        decimal.
        """
        if not self.with_key:
            return 0
        milesimas = round(COBERTURA_MINIMA * 1000)
        necesarias = -(-(milesimas * self.with_key) // 1000)
        return max(0, necesarias - self.covered)


def normalise_decision_note(decision: ReviewDecision, note: str | None) -> str | None:
    """La nota de la decisión: una línea, recortada, y obligatoria al rechazar.

    Reutiliza la regla de la nota del aviso (`normalise_note`): el propietario ya tiene un solo
    sitio donde se le recorta la nota a una línea, y estrenar otra forma sería tener dos.

    Rechazar sin motivo es un **error de entrada** (`InvalidReviewError`, que la API traduce a 422
    con su campo) y no una excepción cualquiera: un `ValueError` suelto acabaría en un 500 por algo
    que ha escrito una persona, que es justo lo que el contrato de errores de esta aplicación evita.
    """
    limpia = normalise_note(note)
    if decision is ReviewDecision.REJECTED and limpia is None:
        raise InvalidReviewError("un tema que se rechaza necesita su motivo")
    return limpia


@dataclass(frozen=True, slots=True)
class TopicReview:
    """La decisión guardada sobre un tema: qué se decidió, con qué nota, cuándo y quién."""

    node_id: str
    decision: ReviewDecision
    note: str | None
    actor: str
    reviewed_at: datetime


def razones_del_tema(cifras: CifrasDelTema) -> tuple[Razon, ...]:
    """Las razones, en orden de lectura, con su cifra. La primera es el titular.

    Se cuentan **todas** las que aplican y no solo una: un tema en borrador suele tener más de un
    motivo (I.8 tenía dos, y II.4 tiene cobertura que pasa y 30 claves marcadas que no cuentan), y
    enseñar solo el primero haría que el segundo se descubriera abriendo la bandeja.
    """
    razones: list[Razon] = []
    #: La cifra de la puerta, o nada: un tema publicado que la tabla no ha medido **no** lleva cifra
    #: (un «0/0» se leería como «cero preguntas cubiertas»).
    cobertura = cifras.cobertura_texto or None

    if not cifras.has_sections:
        razones.append(
            Razon(
                MotivoDelBorrador.SIN_APARTADOS,
                "Este tema todavía no tiene apuntes escritos: no hay nada que revisar.",
            )
        )
    elif cifras.published:
        razones.append(
            Razon(
                MotivoDelBorrador.PUBLICADO,
                "Está publicado: su versión se archivó al pasar las dos puertas.",
                cobertura,
            )
        )

    if cifras.decision is ReviewDecision.REJECTED:
        detalle = f": «{cifras.decision_note}»" if cifras.decision_note else ""
        razones.append(
            Razon(
                MotivoDelBorrador.RECHAZADO,
                f"Lo revisaste y lo rechazaste{detalle}. Mientras siga rechazado no se publica.",
            )
        )
    elif (
        cifras.has_sections
        and not cifras.published
        and cifras.pasa_las_puertas
        and cifras.decision is not ReviewDecision.APPROVED
    ):
        razones.append(
            Razon(
                MotivoDelBorrador.A_LAS_PUERTAS,
                "Cumple las dos puertas y **no está publicado**: no es que le falte nada, es que "
                "nadie ha archivado su versión. Aprobarlo la publica.",
                cobertura,
            )
        )

    if not cifras.pasa_cobertura and cifras.with_key:
        razones.append(
            Razon(
                MotivoDelBorrador.COBERTURA,
                f"Contesta al {porcentaje(cifras.cobertura)} de las preguntas que se pueden "
                f"corregir y el listón es el {UMBRAL_TEXTO}: le faltan {cifras.le_faltan} "
                "preguntas cubiertas.",
                cobertura,
            )
        )
    elif cifras.measured and not cifras.pasa_cobertura:
        # Sin ninguna pregunta comprobable no hay nada que medir, y la puerta **no pasa**: no es que
        # el texto esté mal, es que no hay con qué demostrarlo. Decirlo así evita el «0 de 0» y el
        # «no se ha publicado» sin motivo.
        razones.append(
            Razon(
                MotivoDelBorrador.COBERTURA,
                "No se ha podido medir la cobertura: no hay ninguna pregunta con respuesta "
                "correcta utilizable con la que comprobarlo, y sin eso la puerta no pasa.",
            )
        )

    if not cifras.form_passes:
        fallos = "; ".join(cifras.form_failures) if cifras.form_failures else "sin detalle"
        razones.append(
            Razon(
                MotivoDelBorrador.FORMA,
                f"La forma del texto no pasa: {fallos}",
            )
        )

    if cifras.sin_frase:
        razones.append(
            Razon(
                MotivoDelBorrador.HUECOS,
                con_numero(
                    cifras.sin_frase,
                    "pregunta no tiene ninguna frase en los apuntes que la justifique: es material "
                    "que falta, y se rellena escribiendo.",
                    "preguntas no tienen ninguna frase en los apuntes que las justifique: es "
                    "material que falta, y se rellena escribiendo.",
                ),
                con_numero(cifras.sin_frase, "pregunta", "preguntas"),
            )
        )

    if cifras.conflictos:
        razones.append(
            Razon(
                MotivoDelBorrador.CONFLICTOS,
                con_numero(
                    cifras.conflictos,
                    "la contestan los apuntes con otra letra que su respuesta correcta: hay que "
                    "decidir cuál de las dos está mal.",
                    "las contestan los apuntes con otra letra que su respuesta correcta: hay que "
                    "decidir cuál de las dos está mal.",
                ),
                con_numero(cifras.conflictos, "pregunta", "preguntas"),
            )
        )

    if cifras.claves_marcadas:
        razones.append(
            Razon(
                MotivoDelBorrador.CLAVES_EN_REVISION,
                con_numero(
                    cifras.claves_marcadas,
                    "respuesta correcta está marcada como contraria a la norma o al material: no "
                    "cuenta en el listón (no hay respuesta con la que acertar) y su sitio es la "
                    "bandeja de incidencias.",
                    "respuestas correctas están marcadas como contrarias a la norma o al "
                    "material: no cuentan en el listón (no hay respuesta con la que acertar) y su "
                    "sitio es la bandeja de incidencias.",
                ),
                con_numero(cifras.claves_marcadas, "pregunta", "preguntas"),
            )
        )

    if cifras.sin_materia:
        razones.append(
            Razon(
                MotivoDelBorrador.SIN_MATERIA,
                con_numero(
                    cifras.sin_materia,
                    "pregunta no cabe en ninguna materia del índice: está en la bandeja sin "
                    "apartado donde contestarla.",
                    "preguntas no caben en ninguna materia del índice: están en la bandeja sin "
                    "apartado donde contestarlas.",
                ),
                con_numero(cifras.sin_materia, "pregunta", "preguntas"),
            )
        )

    if cifras.incidencias_abiertas:
        incidencias_texto = con_numero(
            cifras.incidencias_abiertas,
            "incidencia del motor sin despachar",
            "incidencias del motor sin despachar",
        )
        desglose = ", ".join(
            f"{cuantas} {NOMBRE_DE_CATEGORIA[cual]}"
            for cual, cuantas in sorted(cifras.incidencias_por_categoria, key=lambda fila: -fila[1])
        )
        razones.append(
            Razon(
                MotivoDelBorrador.INCIDENCIAS,
                f"{incidencias_texto}" + (f" ({desglose})" if desglose else "") + ".",
                con_numero(cifras.incidencias_abiertas, "incidencia", "incidencias"),
            )
        )

    if cifras.has_sections and not cifras.published and cifras.decision is None:
        razones.append(
            Razon(
                MotivoDelBorrador.SIN_DECISION,
                "Nadie ha revisado este tema todavía: no hay ninguna decisión escrita sobre él.",
            )
        )

    # La última, y a propósito: no es un motivo del tema, es **dónde está la cifra que falta**. La
    # tabla del panel no mide los borradores (medirlos cuesta alrededor de un segundo por tema y la
    # tabla tiene que abrirse sin esperar); la ficha sí los mide, y es donde se decide.
    if cifras.has_sections and not cifras.published and not cifras.measured:
        razones.append(
            Razon(
                MotivoDelBorrador.SIN_MEDIDA,
                "La cobertura y la forma de este tema se miden al abrir su ficha: esta tabla no "
                "las mide porque cada medida cuesta alrededor de un segundo y hay que poder "
                "abrirla sin esperar. Abre el tema para ver las dos cifras antes de decidir.",
            )
        )

    return tuple(razones)


__all__ = [
    "NOMBRE_DE_CATEGORIA",
    "UMBRAL_TEXTO",
    "CifrasDelTema",
    "MotivoDelBorrador",
    "Razon",
    "ReviewDecision",
    "TopicReview",
    "normalise_decision_note",
    "razones_del_tema",
]
