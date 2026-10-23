"""Los cuestionarios y las plantillas del INAP, tal como el importador los entiende (D10).

**Qué problema resuelve.** Los PDF del INAP son documentos de examen, no ficheros de preguntas: el
texto sale del PDF con el número de la pregunta en una línea, las opciones con su letra en otra, los
rótulos de sección sueltos y la cabecera de página repetida en las catorce páginas. El importador
(`parse_questions`) lee un formato de líneas —`1. enunciado`, `a) opción`—, así que entre los dos
hace falta **una conversión determinista** y eso es lo único que hay aquí.

**Las cinco reglas de la conversión, y por qué cada una:**

1. **La numeración oficial se respeta.** Una pregunta de la primera parte se guarda en la posición
   80 porque el documento la numera 80, y las reservas y los supuestos prácticos vuelven a numerar
   desde 1 porque así los numera el INAP. Esto no es un capricho: es lo que hace que la plantilla
   (que también reinicia la numeración en cada sección) encaje **en orden** con el conjunto
   (`ordered_key_mapping`) y que una sesión de examen se monte con la primera parte delante y los
   supuestos detrás (`all_questions` ordena por el documento cuando hay posiciones repetidas). El
   error que no se puede repetir es el contrario: renumerar para que «cuadre» y, con ello, correr
   todas las claves una posición.
2. **La clave no se interpreta.** La plantilla se manda **tal cual viene**, con sus `ANULADA` y sus
   `MODIFICADA` y sin tocar ninguna letra; lo único que se quita son la cabecera del documento y los
   rótulos de sección, que no son respuestas. Si la plantilla no encaja con el cuestionario, el
   importador **lo dice** (`unmatched_positions`, `keys_in_conflict`) en vez de recolocar nada.
3. **Las reservas van marcadas.** El PDF las separa con un rótulo («Preguntas de reserva»), no en la
   línea de cada pregunta, así que la marca se pone donde el importador la entiende: `(R)` al
   principio del enunciado (`_RESERVE` del parser), que además la quita del texto.
4. **Los rótulos de sección van como encabezado.** `## PRIMERA PARTE` es un encabezado de Markdown
   y el parser lo lee como **estructura** («un encabezado de Markdown es estructura, no texto
   suelto»), en lugar de informarlo como texto fuera de pregunta. Lo que estructura el material no
   se convierte en incidencia.
5. **Cabeceras y pies repetidos se quitan, y se dice cuáles.** La cabecera («2024 - TAI-L, MODELO
   A») y el pie («Página 3 de 14») aparecen en cada página y, si se dejaran, se pegarían al final de
   la opción `d)` de la pregunta anterior. Se quitan por patrón y cada línea quitada va al informe.

**Lo que esta conversión NO hace, y no es un olvido:**

- no arregla una numeración no consecutiva: la **declara** (`desviaciones`). Una pregunta cuya
  numeración salta se leería como continuación de la anterior, y eso hay que verlo, no taparlo;
- no rellena opciones que no están ni inventa la letra de una clave que el documento no trae;
- no hace OCR: un cuestionario sin capa de texto (los tres de 2018) se **rechaza** diciéndolo,
  porque transcribir un escaneo a mano no es convertir un PDF.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from opofuente.domain.questions import numbering_match
from opofuente.infrastructure.ocr import TesseractOcr

#: Hasta qué número puede llegar una pregunta de estos exámenes. El cuestionario más largo numera
#: 80 por sección, así que un número por encima de este tope no es una pregunta: es una línea de
#: texto que empieza por una cifra («802.1w.» es una opción, no la pregunta 802).
TOPE_DE_NUMERO = 200

#: Las cabeceras y los pies que el PDF repite en cada página. Quitarlos es obligatorio: si se
#: quedaran, se pegarían al final de la última opción de la página anterior y ensuciarían el
#: enunciado de la pregunta siguiente.
_CABECERA = re.compile(
    r"^\s*\d{4}\s*[-\u2013\u2014]\s*TAI\s*[-\u2013\u2014]?\s*[LP]I?\b.*$"
    r"|^\s*P[áa]gina\s+\d+\s+de\s+\d+\s*$"
    r"|^\s*CONTIN[ÚU]A\s+EN\s+LA\s+P[ÁA]GINA\s+SIGUIENTE\s*$",
    re.IGNORECASE,
)

#: Los rótulos de sección del cuestionario, con lo que dicen de las preguntas que vienen detrás.
#: `Preguntas de reserva` marca las siguientes como reservas; `PRIMERA PARTE` y `SUPUESTO I/II`
#: abren una parte ordinaria. El rótulo se conserva en el informe (es la estructura del examen) y en
#: el texto va como encabezado de Markdown.
_PARTE = re.compile(r"^\s*(PRIMERA|SEGUNDA)\s+PARTE\s*$", re.IGNORECASE)
_RESERVA = re.compile(r"^\s*Preguntas?\s+de\s+reserva\s*$|^\s*Reserva\s*$", re.IGNORECASE)
_SUPUESTO = re.compile(r"^\s*SUPUESTO\s+(I|II|III|IV|[12])\s*$", re.IGNORECASE)

#: El rótulo que se pone a una pregunta que aparece antes de cualquier rótulo del documento. Los
#: cuestionarios de 2019 empiezan directamente por la pregunta 1, sin decir «PRIMERA PARTE».
SIN_ROTULO = "SIN RÓTULO"

#: La etiqueta de una opción: `a)`, `B.`, `(c)`. En estos cuestionarios siempre es una letra con
#: paréntesis o punto, y el texto puede venir en la misma línea o en la siguiente.
_ETIQUETA_DE_OPCION = re.compile(r"^\s*\(?\s*([a-dA-D])\s*[.)\u2013-]\s*(.*)$")


@dataclass(frozen=True, slots=True)
class OpcionDelCuestionario:
    """Una opción con su letra y su texto, tal como los trae el documento."""

    letra: str
    texto: str
    linea: int


@dataclass(frozen=True, slots=True)
class PreguntaDelCuestionario:
    """Una pregunta del cuestionario, con su número oficial y sus opciones."""

    numero: int
    enunciado: str
    opciones: tuple[OpcionDelCuestionario, ...]
    linea: int
    seccion: str
    es_reserva: bool

    @property
    def letras(self) -> tuple[str, ...]:
        return tuple(opcion.letra for opcion in self.opciones)


@dataclass(frozen=True, slots=True)
class Seccion:
    """Un tramo del cuestionario: su rótulo y sus preguntas, en el orden del documento."""

    rotulo: str
    es_reserva: bool
    preguntas: tuple[PreguntaDelCuestionario, ...] = ()


@dataclass(slots=True)
class _EnCurso:
    """La pregunta que se está leyendo: es estado de la conversión, no un dato del documento."""

    numero: int
    linea: int
    enunciado: str
    opciones: list[OpcionDelCuestionario]


@dataclass(frozen=True, slots=True)
class Desviacion:
    """Algo del documento que no encaja con lo que se esperaba, **dicho** en vez de arreglado.

    Tres clases, y las tres son distintas para quien lee el informe: `numero_saltado` (la
    numeración no es consecutiva dentro de su sección), `linea_descartada` (una línea que no es ni
    pregunta, ni opción, ni rótulo) y `sin_capa_de_texto` (el PDF es un escaneo).
    """

    linea: int
    clase: str
    detalle: str


@dataclass(frozen=True, slots=True)
class Cuestionario:
    """Un cuestionario convertido: sus secciones, sus preguntas y lo que se descartó."""

    fuente: str
    secciones: tuple[Seccion, ...] = ()
    descartes: tuple[Desviacion, ...] = ()
    cabeceras_quitadas: tuple[Desviacion, ...] = ()
    modelo: str | None = None

    @property
    def preguntas(self) -> tuple[PreguntaDelCuestionario, ...]:
        return tuple(pregunta for seccion in self.secciones for pregunta in seccion.preguntas)

    @property
    def ordinarias(self) -> int:
        return sum(1 for pregunta in self.preguntas if not pregunta.es_reserva)

    @property
    def reservas(self) -> int:
        return sum(1 for pregunta in self.preguntas if pregunta.es_reserva)


def lineas_del_pdf(path: Path, *, ocr: TesseractOcr | None = None) -> tuple[tuple[int, str], ...]:
    """Las líneas del PDF con su número (1-based), sin las cabeceras ni los pies repetidos.

    Se lee página a página y **en orden de página**: el orden importa porque el documento es la
    fuente del orden de las preguntas. La numeración de línea es la del documento entero, para que
    una incidencia pueda señalar una línea concreta.

    **Si el PDF no trae capa de texto y se pasa un OCR, se lee con OCR** (fase 3, §2.5): los tres
    cuestionarios de 2018 del INAP son escaneos, **y hasta ahora este módulo los rechazaba**.
    **El OCR no es el camino normal**: solo se usa cuando la capa de texto viene vacía, **porque un
    PDF con texto se lee exacto y sin depender de ningún binario**.
    """
    documento = pymupdf.open(path)
    try:
        lineas: list[tuple[int, str]] = []
        numero = 0
        for pagina in range(documento.page_count):
            for cruda in documento[pagina].get_text().splitlines():
                numero += 1
                if _CABECERA.match(cruda):
                    continue
                lineas.append((numero, cruda))
        if ocr is not None and not any(texto.strip() for _, texto in lineas):
            return _lineas_del_ocr(path, ocr, paginas=documento.page_count)
        return tuple(lineas)
    finally:
        documento.close()


def _lineas_del_ocr(path: Path, ocr: TesseractOcr, *, paginas: int) -> tuple[tuple[int, str], ...]:
    """Las líneas de un PDF escaneado, **leídas con OCR**.

    **El orden de página se conserva**: el adaptador devuelve el texto en el orden en que lee las
    páginas, **y de ese orden sale el orden de las preguntas del examen**.
    """
    leido = ocr.text_of_pdf(path, max_pages=max(1, paginas))
    lineas: list[tuple[int, str]] = []
    numero = 0
    for cruda in leido.text.splitlines():
        numero += 1
        if _CABECERA.match(cruda):
            continue
        lineas.append((numero, cruda))
    return tuple(lineas)


def _rotulo(linea: str) -> tuple[str, bool] | None:
    """El rótulo de sección de una línea, con su nombre y si abre una sección de reservas.

    El nombre es el del documento, normalizado en mayúsculas: `SUPUESTO I` y `SUPUESTO II` son dos
    secciones distintas y el informe tiene que poder decirlas por su nombre.
    """
    parte = _PARTE.match(linea)
    if parte is not None:
        return f"{parte.group(1).upper()} PARTE", False
    if _RESERVA.match(linea):
        return "Preguntas de reserva", True
    supuesto = _SUPUESTO.match(linea)
    if supuesto is not None:
        return f"SUPUESTO {supuesto.group(1).upper()}", False
    return None


def extraer_cuestionario(path: Path, *, ocr: TesseractOcr | None = None) -> Cuestionario:
    """Convierte un cuestionario del INAP en secciones con sus preguntas.

    El algoritmo es de una pasada y **se apoya dos veces en el propio documento** para no confundir
    una línea de texto con una pregunta: la numeración de cada sección es consecutiva (desde 1) y
    las opciones van en orden `a`, `b`, `c`, `d`. Lo que no cumple ninguna de las dos cosas se lee
    como continuación de lo que había (una opción partida en dos líneas, un enunciado largo) y, si
    no encaja ahí tampoco, se declara. Nunca se reordena ni se renumera nada.
    """
    lineas = lineas_del_pdf(path, ocr=ocr)
    if not lineas or sum(len(texto.strip()) for _n, texto in lineas) == 0:
        return Cuestionario(
            fuente=path.name,
            descartes=(
                Desviacion(
                    linea=0,
                    clase="sin_capa_de_texto",
                    detalle=(
                        "el PDF no tiene capa de texto: es un escaneo y necesita OCR antes de "
                        "poder importarse"
                    ),
                ),
            ),
        )

    cabeceras = tuple(
        Desviacion(linea=n, clase="cabecera_quitada", detalle=texto.strip())
        for n, texto in _lineas_quitadas(path)
    )

    secciones: list[Seccion] = []
    descartes: list[Desviacion] = []
    rotulo_actual: str | None = None
    es_reserva_actual = False
    preguntas_de_la_seccion: list[PreguntaDelCuestionario] = []

    numero_esperado = 1
    abierta: _EnCurso | None = None

    def cerrar_seccion() -> None:
        nonlocal preguntas_de_la_seccion, rotulo_actual, es_reserva_actual
        # Una sección sin rótulo y sin preguntas es el hueco que deja la portada (las instrucciones
        # del cuestionario empiezan numeradas y no son preguntas): no se declara como sección,
        # porque lo que había dentro ya está en los descartes como portada.
        if rotulo_actual is not None and (preguntas_de_la_seccion or rotulo_actual != SIN_ROTULO):
            secciones.append(
                Seccion(
                    rotulo=rotulo_actual,
                    es_reserva=es_reserva_actual,
                    preguntas=tuple(preguntas_de_la_seccion),
                )
            )
        preguntas_de_la_seccion = []

    def clase_de_lo_suelto() -> str:
        """Qué es un texto que no forma parte de ninguna pregunta, según dónde aparezca."""
        if not secciones and not preguntas_de_la_seccion:
            return "portada"
        if rotulo_actual is not None and rotulo_actual.startswith("SUPUESTO"):
            return "escenario_de_supuesto"
        return "fuera_de_pregunta"

    def cerrar_pregunta() -> None:
        nonlocal abierta
        if abierta is None:
            return
        enunciado = abierta.enunciado.strip()
        if not enunciado:
            descartes.append(
                Desviacion(
                    linea=abierta.linea,
                    clase=clase_de_lo_suelto(),
                    detalle=f"bloque sin enunciado: {abierta.enunciado[:60]}",
                )
            )
        elif len(abierta.opciones) < 2:
            descartes.append(
                Desviacion(
                    linea=abierta.linea,
                    clase=clase_de_lo_suelto(),
                    detalle=(
                        f"«{enunciado[:60]}» tiene {len(abierta.opciones)} opción(es): no es una "
                        "pregunta de este cuestionario"
                    ),
                )
            )
        else:
            preguntas_de_la_seccion.append(
                PreguntaDelCuestionario(
                    numero=abierta.numero,
                    enunciado=enunciado,
                    opciones=tuple(abierta.opciones),
                    linea=abierta.linea,
                    seccion=rotulo_actual or "",
                    es_reserva=es_reserva_actual,
                )
            )
        abierta = None

    for numero_linea, cruda in lineas:
        texto = cruda.strip()
        if not texto:
            continue

        etiqueta_rotulo = _rotulo(texto)
        if etiqueta_rotulo is not None:
            cerrar_pregunta()
            cerrar_seccion()
            rotulo_actual, es_reserva_actual = etiqueta_rotulo
            numero_esperado = 1
            continue

        etiqueta = _ETIQUETA_DE_OPCION.match(texto)
        if etiqueta is not None and abierta is not None:
            letra = etiqueta.group(1).lower()
            esperada = chr(ord("a") + len(abierta.opciones))
            # Una opción solo se abre si es **la que toca**: así una línea del enunciado que empiece
            # por «b)» (una referencia a otra opción) no parte la pregunta en dos.
            if letra == esperada:
                abierta.opciones.append(
                    OpcionDelCuestionario(
                        letra=letra, texto=etiqueta.group(2).strip(), linea=numero_linea
                    )
                )
                continue

        numero = numbering_match(texto)
        if numero is not None:
            candidato = int(numero.group(1))
            if candidato <= TOPE_DE_NUMERO and candidato == numero_esperado:
                cerrar_pregunta()
                if rotulo_actual is None:
                    # Una pregunta antes de cualquier rótulo: el cuestionario no lo declara (los de
                    # 2019 empiezan directamente) y se abre una sección sin nombre.
                    rotulo_actual = SIN_ROTULO
                    es_reserva_actual = False
                numero_esperado = candidato + 1
                abierta = _EnCurso(
                    numero=candidato,
                    linea=numero_linea,
                    enunciado=texto[numero.end() :].strip(),
                    opciones=[],
                )
                continue
            if candidato <= TOPE_DE_NUMERO:
                descartes.append(
                    Desviacion(
                        linea=numero_linea,
                        clase="numero_saltado",
                        detalle=(
                            f"la línea empieza por «{candidato}» y la numeración de la sección va "
                            f"por {numero_esperado}: se lee como continuación"
                        ),
                    )
                )

        if abierta is None:
            descartes.append(
                Desviacion(
                    linea=numero_linea,
                    clase=clase_de_lo_suelto(),
                    detalle=f"texto suelto: {texto[:70]}",
                )
            )
            continue
        if abierta.opciones:
            ultima = abierta.opciones[-1]
            abierta.opciones[-1] = OpcionDelCuestionario(
                letra=ultima.letra, texto=f"{ultima.texto} {texto}".strip(), linea=ultima.linea
            )
        else:
            abierta.enunciado = f"{abierta.enunciado} {texto}".strip()

    cerrar_pregunta()
    cerrar_seccion()
    return Cuestionario(
        fuente=path.name,
        secciones=tuple(secciones),
        descartes=tuple(descartes),
        cabeceras_quitadas=cabeceras,
        modelo=_modelo_del_documento(tuple(texto for _n, texto in lineas)),
    )


def _lineas_quitadas(path: Path) -> tuple[tuple[int, str], ...]:
    """Las líneas que `lineas_del_pdf` quita por ser cabecera o pie repetido."""
    documento = pymupdf.open(path)
    try:
        quitadas: list[tuple[int, str]] = []
        numero = 0
        for pagina in range(documento.page_count):
            for cruda in documento[pagina].get_text().splitlines():
                numero += 1
                if _CABECERA.match(cruda):
                    quitadas.append((numero, cruda))
        return tuple(quitadas)
    finally:
        documento.close()


def _modelo_del_documento(lineas: tuple[str, ...]) -> str | None:
    """El modelo que declara la cabecera del cuestionario (por ejemplo «MODELO A»), si lo dice."""
    for linea in lineas[:40]:
        encontrado = re.search(r"modelo\s*[:\-]?\s*([A-D])\b", linea, re.IGNORECASE)
        if encontrado is not None and len(linea.strip()) <= 60:
            return encontrado.group(1).upper()
    return None


def texto_de_importacion(cuestionario: Cuestionario) -> str:
    """El texto que se manda al importador: rótulos como encabezado, reservas marcadas con `(R)`."""
    trozos: list[str] = []
    for seccion in cuestionario.secciones:
        if not seccion.preguntas:
            continue
        trozos.append(f"## {seccion.rotulo}")
        for pregunta in seccion.preguntas:
            marca = "(R) " if pregunta.es_reserva else ""
            trozos.append(f"{pregunta.numero}. {marca}{pregunta.enunciado}")
            for opcion in pregunta.opciones:
                trozos.append(f"{opcion.letra}) {opcion.texto}")
    return "\n".join(trozos) + "\n"


def texto_de_plantilla(path: Path) -> str:
    """La plantilla **tal como viene**, sin la cabecera del documento ni los rótulos de sección.

    Ni una letra se toca: `ANULADA`, `MODIFICADA` y los números repetidos de cada sección se quedan
    como están, porque son parte de lo que la plantilla dice y el importador sabe leerlos. Lo que se
    quita es lo que no es una respuesta —el título del documento y los rótulos—, y se quita porque
    el parser de plantillas no tiene dónde ponerlo y lo declararía como línea ilegible en cada
    sección, que es ruido en el informe de una importación que sí ha ido bien.
    """
    partes: list[str] = []
    empezado = False
    for _numero, cruda in lineas_del_pdf(path):
        texto = cruda.strip()
        if not texto:
            continue
        if not empezado:
            if re.match(r"^\s*\d{1,3}\s*[.)\u2013-]", texto) is not None or re.match(
                r"^\s*\d{1,3}\s*$", texto
            ):
                empezado = True
            else:
                continue
        if _rotulo(texto) is not None:
            continue
        partes.append(texto)
    return "\n".join(partes) + "\n"


@dataclass(frozen=True, slots=True)
class SeccionDePlantilla:
    """Un tramo de la plantilla: su rótulo, sus líneas numeradas y lo que no tenía número.

    `sueltas` son las líneas que no traen número (la cabecera del documento, si se cuela): se
    guardan **aparte** para que no cuenten como respuestas —una cabecera no es una clave— y para que
    se vea que estaban.
    """

    rotulo: str
    es_reserva: bool
    lineas: tuple[tuple[int, str], ...] = ()
    sueltas: tuple[str, ...] = ()


def secciones_de_plantilla(path: Path) -> tuple[SeccionDePlantilla, ...]:
    """La plantilla por secciones, para poder **comparar** sus recuentos con los del cuestionario.

    Es la comprobación que evita el error de la numeración: si el cuestionario tiene 80 preguntas en
    la primera parte y la plantilla 80 líneas, encajan; si no, hay que decirlo antes de importar.
    """
    secciones: list[SeccionDePlantilla] = []
    rotulo = SIN_ROTULO
    es_reserva = False
    lineas: list[tuple[int, str]] = []
    sueltas: list[str] = []
    pendiente: int | None = None

    def cerrar() -> None:
        nonlocal lineas, sueltas
        if lineas or sueltas:
            secciones.append(
                SeccionDePlantilla(
                    rotulo=rotulo,
                    es_reserva=es_reserva,
                    lineas=tuple(lineas),
                    sueltas=tuple(sueltas),
                )
            )
        lineas = []
        sueltas = []

    for _numero, cruda in lineas_del_pdf(path):
        texto = cruda.strip()
        if not texto:
            continue
        etiqueta = _rotulo(texto)
        if etiqueta is not None:
            if pendiente is not None:
                lineas.append((pendiente, ""))
                pendiente = None
            cerrar()
            rotulo, es_reserva = etiqueta
            continue
        solo_numero = re.match(r"^\s*(\d{1,3})\s*[.)\u2013-]*\s*$", texto)
        if solo_numero is not None:
            if pendiente is not None:
                lineas.append((pendiente, ""))
            pendiente = int(solo_numero.group(1))
            continue
        junto = re.match(r"^\s*(\d{1,3})\s*[.)\u2013-]+\s*(\S.*)$", texto)
        if junto is not None:
            if pendiente is not None:
                lineas.append((pendiente, ""))
                pendiente = None
            lineas.append((int(junto.group(1)), junto.group(2).strip()))
            continue
        if pendiente is not None:
            lineas.append((pendiente, texto))
            pendiente = None
        else:
            # Sin número y sin pregunta detrás: la cabecera del documento. Se declara aparte.
            sueltas.append(texto)
    if pendiente is not None:
        lineas.append((pendiente, ""))
    cerrar()
    return tuple(secciones)


__all__ = [
    "TOPE_DE_NUMERO",
    "Cuestionario",
    "Desviacion",
    "OpcionDelCuestionario",
    "PreguntaDelCuestionario",
    "Seccion",
    "SeccionDePlantilla",
    "extraer_cuestionario",
    "lineas_del_pdf",
    "secciones_de_plantilla",
    "texto_de_importacion",
    "texto_de_plantilla",
]
