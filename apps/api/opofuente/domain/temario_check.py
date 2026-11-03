"""El chequeo del temario guardado, tema a tema, sin modelo y sin red (O3).

Existe porque un tema puede tener buena cobertura de preguntas y no ser el tema que el enunciado
oficial pide: los pilotos se escribieron **por lotes de preguntas**, y eso deja epígrafes sin
apartado y desaparece la estructura fija del temario. Este módulo mide las cuatro cosas que el
`REFERENCIA-OPOSICIONESINFORMATICA` exige y que se pueden medir sin juicio de contenido:

1. **epígrafes**: cada epígrafe del enunciado oficial del tema tiene al menos un apartado con texto;
2. **estructura**: están las seis partes (índice, desarrollo, normativa vigente, resumen, mapa
   conceptual y preguntas de autoevaluación);
3. **preguntas**: entre 10 y 20 preguntas tipo test, cada una con **clave**, **explicación** y
   **evidencia** declaradas en campos separados;
4. **normas**: las normas citadas llevan fecha de consolidación. La **vigencia** y la **derogación**
   no se evalúan: sin catálogo autorizado del BOE no hay forma de saberlo, y no se inventa. Quedan
   `no evaluable` con su motivo.

El resultado es **informativo y no bloqueante**: no cambia las dos puertas que ya deciden (forma y
cobertura por preguntas) ni las vuelve retroactivas. Un tema en `parcial` se enseña y se arregla,
pero no se impide publicarlo por este chequeo.

La detección es determinista y deliberadamente estrecha: las partes se buscan en los **títulos** de
los apartados y las normas por su forma oficial (`Ley 39/2015`, `Real Decreto 3/2010`…). Una fecha
de consolidación solo cuenta si la línea la declara (`texto consolidado a…`, `última
actualización…`): la fecha de promulgación de la propia norma no es la de consolidación.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from opofuente.domain.rag import normalise

#: El motivo, siempre el mismo, de que la vigencia no se pueda evaluar. Se imprime tal cual.
MOTIVO_SIN_CATALOGO_BOE = "sin catálogo autorizado del BOE"

#: Cuántas preguntas de autoevaluación exige el enunciado del temario: ni menos de diez ni más de
#: veinte. Se comprueba **cuando la parte de preguntas existe**: si falta, ya la lista `partes`.
MIN_PREGUNTAS = 10
MAX_PREGUNTAS = 20


#: El estado del tema. `no evaluable` no es un suspenso: es que faltan datos para medirlo.
class Estado(StrEnum):
    OK = "ok"
    PARCIAL = "parcial"
    AUSENTE = "ausente"
    NO_EVALUABLE = "no evaluable"


class ApartadoDeTemario(Protocol):
    """Lo que el chequeo necesita de un apartado guardado: dónde está, qué epígrafe cubre y qué
    dice."""

    @property
    def key(self) -> str: ...

    @property
    def title(self) -> str: ...

    @property
    def epigraph_code(self) -> str: ...

    @property
    def body_markdown(self) -> str: ...


#: Las seis partes de la estructura fija, en el orden en que se leen. `desarrollo` no busca palabra:
#: es el texto que no pertenece a ninguna de las otras cinco partes.
PARTES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("indice", "índice", ("indice",)),
    ("desarrollo", "desarrollo", ()),
    ("normativa", "normativa vigente", ("normativa", "legislacion")),
    ("resumen", "resumen", ("resumen",)),
    ("mapa_conceptual", "mapa conceptual", ("mapa conceptual", "mapa")),
    (
        "preguntas",
        "preguntas de autoevaluación",
        ("pregunta", "test", "cuestionario", "autoevaluacion"),
    ),
)

#: Las partes que se reconocen por el título del apartado. `desarrollo` va aparte porque es el
#: contenido que queda cuando se descuentan las demás.
_PALABRAS_DE_PARTE: dict[str, tuple[str, ...]] = {
    clave: palabras for clave, _, palabras in PARTES if palabras
}

#: Una norma por su forma oficial y con número. Se deja fuera lo que no tiene número (la
#: Constitución, por ejemplo): sin número no hay referencia que comprobar contra un catálogo.
_NORMA = re.compile(
    r"\b(?:Ley(?:\s+Org[áa]nica)?"
    r"|Real\s+Decreto(?:\s+Legislativo)?"
    r"|Reglamento(?:\s*\(UE\))?"
    r"|Directiva(?:\s*\(UE\))?"
    r"|Decisi[óo]n(?:\s*\(UE\))?)"
    r"\s+\d{1,4}/\d{4}\b",
    re.IGNORECASE,
)

#: Un mes en español, para reconocer una fecha escrita.
_MESES = (
    "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre"
    "|diciembre"
)

#: Una fecha escrita: `2 de abril de 2024` o `2024-04-02`.
_FECHA = re.compile(
    rf"\b\d{{1,2}}\s+de\s+(?:{_MESES})\s+de\s+\d{{4}}\b|\b\d{{4}}-\d{{2}}-\d{{2}}\b",
    re.IGNORECASE,
)

#: Lo que declara que la fecha de al lado es la de **consolidación**, no la de promulgación.
_MARCA_DE_CONSOLIDACION = (
    "consolidad",
    "texto consolidado",
    "ultima actualizacion",
    "ultima modificacion",
    "vigente a",
    "vigente desde",
)


@dataclass(frozen=True, slots=True)
class EpigrafeOficial:
    """Un epígrafe del enunciado oficial y los apartados que lo cubren."""

    code: str
    title: str
    apartados: tuple[str, ...] = ()

    @property
    def cubierto(self) -> bool:
        return bool(self.apartados)


@dataclass(frozen=True, slots=True)
class ParteExigida:
    """Una de las seis partes de la estructura, con los apartados donde se ha encontrado."""

    clave: str
    nombre: str
    donde: tuple[str, ...] = ()

    @property
    def presente(self) -> bool:
        return bool(self.donde)


@dataclass(frozen=True, slots=True)
class CitaNormativa:
    """Una norma citada en un apartado, con su fecha de consolidación si la declara."""

    referencia: str
    ubicacion: str
    fecha_consolidacion: str | None = None


@dataclass(frozen=True, slots=True)
class PreguntaAutoevaluacion:
    """Una pregunta del apartado de autoevaluación, con los tres campos que debe declarar.

    Los campos son **separados** por exigencia del enunciado: la clave no se esconde dentro de la
    explicación y la evidencia no se repite como explicación. El chequeo no juzga si la explicación
    es buena, solo que existe y que no se confunde con la evidencia.
    """

    numero: int
    ubicacion: str
    tiene_clave: bool = False
    tiene_explicacion: bool = False
    tiene_evidencia: bool = False

    @property
    def completa(self) -> bool:
        return self.tiene_clave and self.tiene_explicacion and self.tiene_evidencia


@dataclass(frozen=True, slots=True)
class RevisionTemario:
    """Lo que mide el chequeo sobre un tema guardado. No decide: informa."""

    code: str
    title: str
    epigrafes: tuple[EpigrafeOficial, ...]
    partes: tuple[ParteExigida, ...]
    citas: tuple[CitaNormativa, ...]
    apartados: int = 0
    con_texto: int = 0
    preguntas: tuple[PreguntaAutoevaluacion, ...] = ()

    @property
    def epigrafes_cubiertos(self) -> tuple[str, ...]:
        return tuple(epigrafe.code for epigrafe in self.epigrafes if epigrafe.cubierto)

    @property
    def epigrafes_sin_apartado(self) -> tuple[str, ...]:
        return tuple(epigrafe.code for epigrafe in self.epigrafes if not epigrafe.cubierto)

    @property
    def partes_ausentes(self) -> tuple[str, ...]:
        return tuple(parte.clave for parte in self.partes if not parte.presente)

    @property
    def citas_sin_fecha(self) -> tuple[CitaNormativa, ...]:
        return tuple(cita for cita in self.citas if cita.fecha_consolidacion is None)

    @property
    def hay_parte_de_preguntas(self) -> bool:
        return any(parte.clave == "preguntas" and parte.presente for parte in self.partes)

    @property
    def preguntas_completas(self) -> tuple[PreguntaAutoevaluacion, ...]:
        return tuple(pregunta for pregunta in self.preguntas if pregunta.completa)

    @property
    def preguntas_incompletas(self) -> tuple[PreguntaAutoevaluacion, ...]:
        return tuple(pregunta for pregunta in self.preguntas if not pregunta.completa)

    @property
    def preguntas_fuera_de_rango(self) -> bool:
        return self.hay_parte_de_preguntas and not (
            MIN_PREGUNTAS <= len(self.preguntas) <= MAX_PREGUNTAS
        )

    @property
    def estado_vigencia(self) -> Estado:
        """La vigencia **no** se puede evaluar: no hay catálogo autorizado del BOE."""
        return Estado.NO_EVALUABLE

    @property
    def motivo_vigencia(self) -> str:
        return MOTIVO_SIN_CATALOGO_BOE

    @property
    def estado(self) -> Estado:
        if not self.epigrafes:
            return Estado.NO_EVALUABLE
        if not self.apartados or not self.con_texto:
            return Estado.AUSENTE
        if self.epigrafes_sin_apartado or self.partes_ausentes:
            return Estado.PARCIAL
        if self.preguntas_fuera_de_rango or self.preguntas_incompletas:
            return Estado.PARCIAL
        if not self.citas or self.citas_sin_fecha:
            return Estado.PARCIAL
        return Estado.OK

    @property
    def motivo(self) -> str | None:
        """Por qué no está `ok`, en una frase. `None` cuando el tema está `ok`."""
        if self.estado is Estado.OK:
            return None
        if not self.epigrafes:
            return "el tema no declara epígrafes oficiales"
        if not self.apartados:
            return "no hay apartados guardados"
        if not self.con_texto:
            return "ningún apartado tiene texto"
        if self.epigrafes_sin_apartado:
            return "epígrafes sin apartado: " + ", ".join(self.epigrafes_sin_apartado)
        if self.partes_ausentes:
            return "faltan partes de la estructura: " + ", ".join(self.partes_ausentes)
        if self.preguntas_fuera_de_rango:
            return (
                f"preguntas de autoevaluación fuera de {MIN_PREGUNTAS}-{MAX_PREGUNTAS}: "
                f"{len(self.preguntas)}"
            )
        if self.preguntas_incompletas:
            return "preguntas sin clave, explicación o evidencia separadas: " + ", ".join(
                str(pregunta.numero) for pregunta in self.preguntas_incompletas
            )
        if not self.citas:
            return "no se ha encontrado ninguna norma citada"
        return f"normas sin fecha de consolidación: {len(self.citas_sin_fecha)}"

    @property
    def pasa(self) -> bool:
        """Informativo: el chequeo **no** es una puerta que bloquee la publicación."""
        return self.estado is Estado.OK

    def lines(self) -> tuple[str, ...]:
        """El resumen corto que se imprime en stdout, sin volcar el tema."""
        con_apartado = ", ".join(self.epigrafes_cubiertos) or "—"
        sin_apartado = ", ".join(self.epigrafes_sin_apartado) or "—"
        partes = ", ".join(parte.clave for parte in self.partes if not parte.presente) or "—"
        return (
            f"[{self.code}] {self.title} · temario: {self.estado.value}",
            f"    epígrafes: {len(self.epigrafes_cubiertos)} de {len(self.epigrafes)} con "
            f"apartado · con apartado: {con_apartado} · sin apartado: {sin_apartado}",
            f"    partes: {len(self.partes) - len(self.partes_ausentes)} de {len(self.partes)}"
            f" · faltan: {partes}",
            f"    preguntas: {len(self.preguntas)} (exigidas {MIN_PREGUNTAS}-{MAX_PREGUNTAS}) · "
            f"completas: {len(self.preguntas_completas)} · incompletas: "
            f"{len(self.preguntas_incompletas)}",
            f"    normas citadas: {len(self.citas)} · con fecha de consolidación: "
            f"{len(self.citas) - len(self.citas_sin_fecha)} · sin fecha: "
            f"{len(self.citas_sin_fecha)}",
            f"    vigencia: {self.estado_vigencia.value} ({self.motivo_vigencia})",
            *((f"    motivo: {self.motivo}",) if self.motivo else ()),
        )

    def detalle(self) -> tuple[str, ...]:
        """El detalle por tema para el informe de `docs/slices`, en markdown."""
        lineas = [
            f"### {self.code} · {self.title}",
            "",
            f"- **Estado:** `{self.estado.value}`" + (f" — {self.motivo}" if self.motivo else ""),
            f"- **Apartados:** {self.apartados} guardados, {self.con_texto} con texto",
            f"- **Vigencia:** `{self.estado_vigencia.value}` ({self.motivo_vigencia})",
            "",
            "| Epígrafe | Título | Apartados |",
            "| --- | --- | --- |",
        ]
        for epigrafe in self.epigrafes:
            donde = ", ".join(epigrafe.apartados) if epigrafe.apartados else "—"
            lineas.append(f"| {epigrafe.code} | {epigrafe.title} | {donde} |")
        lineas.extend(("", "| Parte | Presente | Dónde |", "| --- | --- | --- |"))
        for parte in self.partes:
            donde = ", ".join(parte.donde) if parte.donde else "—"
            lineas.append(f"| {parte.nombre} | {'sí' if parte.presente else 'no'} | {donde} |")
        if self.hay_parte_de_preguntas:
            lineas.extend(
                (
                    "",
                    f"Preguntas: {len(self.preguntas)} (exigidas {MIN_PREGUNTAS}-{MAX_PREGUNTAS}); "
                    f"{len(self.preguntas_completas)} completas.",
                    "",
                    "| Pregunta | Apartado | Clave | Explicación | Evidencia |",
                    "| --- | --- | --- | --- | --- |",
                )
            )
            for pregunta in self.preguntas:
                lineas.append(
                    f"| {pregunta.numero} | {pregunta.ubicacion} | "
                    f"{'sí' if pregunta.tiene_clave else 'no'} | "
                    f"{'sí' if pregunta.tiene_explicacion else 'no'} | "
                    f"{'sí' if pregunta.tiene_evidencia else 'no'} |"
                )
        lineas.extend(
            (
                "",
                "| Norma citada | Apartado | Fecha de consolidación |",
                "| --- | --- | --- |",
            )
        )
        if not self.citas:
            lineas.append("| — | — | — |")
        for cita in self.citas:
            fecha = cita.fecha_consolidacion or "**sin fecha**"
            lineas.append(f"| {cita.referencia} | {cita.ubicacion} | {fecha} |")
        lineas.append("")
        return tuple(lineas)


def _titulo_normalizado(titulo: str) -> str:
    return normalise(titulo)


def _parte_del_titulo(titulo: str) -> str | None:
    """La clave de la parte auxiliar que anuncia el título, o `None` si es desarrollo."""
    normalizado = _titulo_normalizado(titulo)
    for clave, palabras in _PALABRAS_DE_PARTE.items():
        if any(palabra in normalizado for palabra in palabras):
            return clave
    return None


#: El arranque de una pregunta numerada (`1.`, `2)`). Las opciones (`a)`) no empiezan por número.
_NUMERO_PREGUNTA = re.compile(r"^\s*(\d{1,3})[.)]\s+\S")

#: Un campo declarado al principio de su línea. Se busca sobre la línea **normalizada**, así que
#: `**Explicación:**` y `- Clave:` cuentan igual. El campo tiene que empezar la línea: una palabra
#: suelta dentro de una frase no convierte la frase en campo.
_CAMPO = re.compile(r"^(respuesta correcta|clave|explicacion|evidencia)\s*(.*)$")

#: Una clave de test: una letra de la `a` a la `d`, sola o con su texto detrás.
_CLAVE = re.compile(r"^(?:opcion\s+)?([a-d])(?:\s|$)")


def _campo_de_linea(linea: str) -> tuple[str, str] | None:
    """El campo que declara la línea y su contenido, o `None` si no declara ninguno."""
    casada = _CAMPO.match(normalise(linea))
    if casada is None:
        return None
    return casada.group(1), casada.group(2).strip()


def _preguntas_de(apartado: ApartadoDeTemario) -> tuple[PreguntaAutoevaluacion, ...]:
    """Las preguntas numeradas de un apartado, con qué campos declara cada una.

    Una pregunta empieza en una línea numerada y termina en la siguiente. Los campos se buscan al
    principio de línea; si el contenido queda en las líneas siguientes (una explicación partida), se
    toma la primera línea no vacía que no declare otro campo.
    """
    bloques: list[tuple[int, list[str]]] = []
    for linea in apartado.body_markdown.splitlines():
        casada = _NUMERO_PREGUNTA.match(linea)
        if casada is not None:
            bloques.append((int(casada.group(1)), [linea]))
        elif bloques:
            bloques[-1][1].append(linea)

    preguntas: list[PreguntaAutoevaluacion] = []
    for numero, lineas in bloques:
        campos: dict[str, str] = {}
        for indice, linea in enumerate(lineas):
            campo = _campo_de_linea(linea)
            if campo is None:
                continue
            nombre, contenido = campo
            if not contenido:
                contenido = next(
                    (
                        siguiente.strip()
                        for siguiente in lineas[indice + 1 :]
                        if siguiente.strip() and _campo_de_linea(siguiente) is None
                    ),
                    "",
                )
            campos.setdefault(nombre, contenido)
        clave = campos.get("respuesta correcta") or campos.get("clave", "")
        explicacion = campos.get("explicacion", "")
        evidencia = campos.get("evidencia", "")
        preguntas.append(
            PreguntaAutoevaluacion(
                numero=numero,
                ubicacion=apartado.key,
                tiene_clave=bool(_CLAVE.match(normalise(clave))),
                tiene_explicacion=bool(explicacion),
                tiene_evidencia=bool(evidencia) and normalise(evidencia) != normalise(explicacion),
            )
        )
    return tuple(preguntas)


def _citas_de(apartado: ApartadoDeTemario) -> tuple[CitaNormativa, ...]:
    """Las normas citadas en un apartado, con la fecha de consolidación que declare su línea."""
    citas: list[CitaNormativa] = []
    for linea in apartado.body_markdown.splitlines():
        normalizada = normalise(linea)
        declara_consolidacion = any(marca in normalizada for marca in _MARCA_DE_CONSOLIDACION)
        fecha = _FECHA.search(linea) if declara_consolidacion else None
        for casada in _NORMA.finditer(linea):
            citas.append(
                CitaNormativa(
                    referencia=" ".join(casada.group(0).split()),
                    ubicacion=apartado.key,
                    fecha_consolidacion=fecha.group(0) if fecha else None,
                )
            )
    return tuple(citas)


def revisar_temario(
    *,
    code: str,
    title: str,
    epigraphs: tuple[tuple[str, str], ...] | list[tuple[str, str]],
    apartados: tuple[ApartadoDeTemario, ...] | list[ApartadoDeTemario],
) -> RevisionTemario:
    """Mide un tema guardado contra su enunciado oficial. Puro: no escribe ni llama a nadie."""
    con_texto = [apartado for apartado in apartados if apartado.body_markdown.strip()]
    por_epigrafe: dict[str, list[str]] = {}
    for apartado in con_texto:
        por_epigrafe.setdefault(apartado.epigraph_code, []).append(apartado.key)

    epigrafes = tuple(
        EpigrafeOficial(
            code=codigo,
            title=titulo,
            apartados=tuple(por_epigrafe.get(codigo, ())),
        )
        for codigo, titulo in epigraphs
    )

    partes: list[ParteExigida] = []
    for clave, nombre, palabras in PARTES:
        if clave == "desarrollo":
            donde = tuple(
                apartado.key for apartado in con_texto if _parte_del_titulo(apartado.title) is None
            )
        else:
            donde = tuple(
                apartado.key for apartado in con_texto if _parte_del_titulo(apartado.title) == clave
            )
        partes.append(ParteExigida(clave=clave, nombre=nombre, donde=donde))

    preguntas = tuple(
        pregunta
        for apartado in con_texto
        if _parte_del_titulo(apartado.title) == "preguntas"
        for pregunta in _preguntas_de(apartado)
    )

    citas: list[CitaNormativa] = []
    vistas: set[tuple[str, str]] = set()
    for apartado in con_texto:
        for cita in _citas_de(apartado):
            clave_cita = (cita.referencia.casefold(), cita.ubicacion)
            if clave_cita in vistas:
                continue
            vistas.add(clave_cita)
            citas.append(cita)

    return RevisionTemario(
        code=code,
        title=title,
        epigrafes=epigrafes,
        partes=tuple(partes),
        citas=tuple(citas),
        apartados=len(apartados),
        con_texto=len(con_texto),
        preguntas=preguntas,
    )
