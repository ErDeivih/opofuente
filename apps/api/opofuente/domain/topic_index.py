"""El índice de un tema por materias: los apartados que tendrá, en orden, **antes** de redactar.

El esquema de los pilotos salió de los lotes: un apartado por cada trozo de cuarenta hechos, en el
orden en que se pidieron. De ahí los **19 apartados «Protocolos TCP/IP: …»** de IV.7.2 (cada uno
con su tabla de puertos, distinta de las demás) y los **7 del modelo OSI** de IV.7.1. El contenido
era el mismo; lo que faltaba era la estructura.

Esto es lo contrario: un catálogo de **materias** por epígrafe, en el orden en que se estudia, y un
reparto **determinista** de los hechos y las preguntas que ya están en la base a la materia que les
toca. No llama a nadie: clasifica por las palabras del propio texto, con el vocabulario del tema,
así que el índice se puede calcular, leer y discutir antes de escribir una sola línea (que es lo
que se pidió: ver el esquema antes de redactar).

Siete reglas, y las siete se ven en el resultado:

1. **cada hecho y cada pregunta van a una sola materia**: la que los menciona antes (y, a igualdad,
   la de `prioridad` más baja). Se mira primero entre las materias del epígrafe del hecho y, si en
   el suyo no casa con ninguna, en el catálogo entero: hay hechos a los que el modelo puso el
   epígrafe que no era (9 en IV.7), y su contenido manda. Esos se cuentan y se dicen;
2. **el reparto mira primero lo particular**: un hecho que habla de DNS *y* del puerto 53 es un
   hecho de DNS, no de la tabla de puertos. Por eso cada materia tiene su `prioridad` de reparto,
   aparte del orden en que se enseña el índice;
3. **los hechos repetidos se agrupan y se queda uno por grupo** (`deduplicar`): 998 hechos para 554
   preguntas eran demasiados, sobre todo en el modelo OSI (199 para 125). El que se queda conserva
   **la unión de las preguntas** de todo su grupo, así que ninguna pregunta pierde su anclaje. La
   equivalencia se mide con el parecido de Dice **ponderado por IDF** (lo que distingue un hecho es
   su vocabulario poco frecuente, no «capa» y «modelo») y con una guarda: dos hechos con **siglas o
   cifras distintas** no son el mismo hecho aunque se parezcan en todo lo demás (`LLC` no es `MAC`,
   `TPDU` no es `APDU`, y un hecho del puerto 53 no es uno del 80);
4. **el modelo OSI se reparte en cuatro partes** —qué es OSI y qué es un sistema abierto, las siete
   capas una a una, las unidades de datos y el encapsulado (con LLC y MAC dentro de la capa de
   enlace) y los dispositivos que trabajan en cada capa— por lo que dice cada hecho, no por dónde
   caiga la primera palabra: se mira primero si nombra un dispositivo, después una unidad de datos,
   después una capa concreta y, si no dice nada de eso, es del modelo;
5. **no hay cajones de revisión**: lo que no es de ninguna materia del tema **no se enseña como un
   apartado más**. Se cuenta, se dice con su texto y **para la corrida**: un hecho sin apartado es
   una pregunta mal clasificada, y eso se arregla en la cola de clasificación, no escribiendo
   apuntes alrededor;
6. **la tabla de puertos tiene un solo sitio**: la materia de puertos es la única marcada con
   `tabla_unica`, y su apartado es donde vive esa tabla;
7. **el índice va en el orden oficial**: primero los epígrafes del temario y, dentro de cada uno,
   las materias en el orden en que se estudian. Ese orden está escrito aparte, en una lista de
   claves (`_ORDEN_IV7`), y es distinto del de reparto: si no lo fuera, la tabla de puertos se
   llevaría las preguntas de DNS.
"""

from __future__ import annotations

import math
import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field

from opofuente.domain.rag import normalise
from opofuente.domain.topic_notes import (
    Hecho,
    NoteSection,
    QuestionGroup,
    terminos_significativos,
)

#: Prioridad de reparto por defecto: se mira después de las materias con prioridad propia.
PRIORIDAD_POR_DEFECTO = 100

#: Umbral de equivalencia entre dos hechos: parecido de Dice ponderado por IDF. Se midió sobre los
#: 998 hechos reales de IV.7 antes de elegirlo: con 0,4 desaparecen 261 hechos repetidos (el 26 %) y
#: los cuatro casos de control que no se pueden fusionar (LLC/MAC, TPDU/APDU, FTP/DNS y
#: ASCII/EBCDIC)
#: siguen separados. Bajarlo más empieza a juntar hechos que dicen cosas distintas.
UMBRAL_EQUIVALENCIA = 0.4

#: Una sigla (`LLC`, `MAC`, `TPDU`, `RFC`) o una cifra (`53`, `7498`, `7`) en el texto **original**.
#: Es la guarda de la deduplicación: dos hechos que no comparten estas etiquetas no son el mismo
#: hecho, aunque se digan con las mismas palabras de relleno.
_SIGLA = re.compile(r"\b[A-Z][A-Z0-9]{1,7}\b")
_CIFRA = re.compile(r"\b\d+\b")


@dataclass(frozen=True, slots=True)
class Materia:
    """Un apartado del índice: su materia, en qué epígrafe vive y qué le toca.

    `patrones` son expresiones regulares sobre el texto **normalizado** (sin acentos, sin signos, en
    minúsculas), que es la normalización con la que se compara todo en el proyecto. `resumen` es la
    línea que se le enseña al propietario: qué entra en este apartado.

    Una materia **sin patrones** es el cajón de su epígrafe: recoge lo que no ha casado con ninguna
    otra. Cada epígrafe del catálogo tiene que tener el suyo, y solo uno.
    """

    key: str
    epigraph_code: str
    title: str
    resumen: str
    patrones: tuple[str, ...] = ()
    #: Orden de **reparto** (no el del índice): más bajo, se mira antes. Sirve para que lo
    #: particular gane a lo general (DNS antes que la tabla de puertos) sin cambiar el orden en que
    #: se enseña.
    prioridad: int = PRIORIDAD_POR_DEFECTO
    #: Si es la materia donde vive una tabla que no puede estar en dos sitios (la de puertos).
    tabla_unica: bool = False
    #: La familia a la que pertenece la materia, si sus hermanas comparten vocabulario y hay que
    #: repartir entre ellas por asunto y no por la primera palabra que casa (el modelo OSI). Vacío
    #: es una materia normal: se decide por sus patrones.
    familia: str = ""

    @property
    def es_cajon(self) -> bool:
        """¿Es el cajón del epígrafe (lo que no es de ninguna materia)?"""
        return not self.patrones


@dataclass(frozen=True, slots=True)
class RepartoMateria:
    """Lo que le ha tocado a una materia: sus hechos, los que se han fusionado y sus preguntas.

    `hechos` es lo que se va a redactar (ya deduplicado) y `fusionados` son los hechos que se
    quedaron por el camino al agrupar los equivalentes: se guardan para poder decir **cuántos había
    y cuántos quedan** en cada apartado, que es la cuenta que pidió el propietario. No se pierden:
    su contenido y sus preguntas están en el hecho que se queda.
    """

    materia: Materia
    hechos: tuple[Hecho, ...]
    grupos: tuple[QuestionGroup, ...]
    fusionados: tuple[Hecho, ...] = ()

    @property
    def preguntas(self) -> int:
        return sum(len(grupo.questions) for grupo in self.grupos)

    @property
    def hechos_antes(self) -> int:
        """Los hechos que había en este apartado antes de agrupar los repetidos."""
        return len(self.hechos) + len(self.fusionados)

    @property
    def firmas_de_grupo(self) -> frozenset[str]:
        """Las firmas de las preguntas que anclan los hechos de este apartado."""
        return frozenset(firma for hecho in self.hechos for firma in hecho.source_groups)

    def lineas(self) -> tuple[str, ...]:
        """El apartado del índice: una línea con su cuenta y otra con lo que entra."""
        marcas = " · una sola tabla en todo el tema" if self.materia.tabla_unica else ""
        repetidos = (
            ""
            if not self.fusionados
            else f" (de {self.hechos_antes}; {len(self.fusionados)} repetido(s) agrupado(s))"
        )
        return (
            f"    {self.materia.key} · {self.materia.title} — {len(self.hechos)} hecho(s)"
            f"{repetidos}, {len(self.grupos)} grupo(s) de preguntas "
            f"({self.preguntas} pregunta(s){marcas})",
            f"        {self.materia.resumen}",
        )


@dataclass(frozen=True, slots=True)
class IndiceDelTema:
    """El índice completo: el tema, sus epígrafes y el reparto de hechos y preguntas."""

    topic_code: str
    topic_title: str
    epigraphs: tuple[tuple[str, str], ...]
    reparto: tuple[RepartoMateria, ...] = ()
    #: Hechos que no son de **ninguna** materia del tema. No se enseña ningún cajón con ellos: se
    #: cuentan y se dicen, porque son preguntas mal clasificadas (van a la cola de clasificación).
    sin_materia: tuple[Hecho, ...] = field(default=())
    #: Hechos que se han ido a una materia del **otro** epígrafe porque es donde se estudian: el
    #: modelo les puso el epígrafe que no era, y eso se mueve sin preguntar.
    fuera_de_su_epigrafe: tuple[Hecho, ...] = field(default=())
    #: Grupos de preguntas que no han casado con ninguna materia.
    grupos_sin_materia: tuple[QuestionGroup, ...] = field(default=())
    #: Hechos que había en el tema antes de agrupar los repetidos.
    hechos_originales: int = 0

    @property
    def hechos(self) -> int:
        return sum(len(apartado.hechos) for apartado in self.reparto)

    @property
    def grupos(self) -> int:
        return sum(len(apartado.grupos) for apartado in self.reparto)

    @property
    def preguntas(self) -> int:
        return sum(apartado.preguntas for apartado in self.reparto)

    @property
    def apartados(self) -> int:
        return len(self.reparto)

    @property
    def materias_de_la_tabla(self) -> tuple[Materia, ...]:
        return tuple(apartado.materia for apartado in self.reparto if apartado.materia.tabla_unica)

    def lines(self) -> tuple[str, ...]:
        """El índice en texto: es lo que se enseña y se discute antes de redactar."""
        lineas = [
            f"Índice por materias de [{self.topic_code}] {self.topic_title}",
            f"    {self.apartados} apartado(s) · {self.hechos} hecho(s) de "
            f"{self.hechos_originales} "
            f"({len(self.fusionados)} repetido(s) agrupado(s)) · {self.preguntas} "
            f"pregunta(s) en {self.grupos} grupo(s) · {len(self.epigraphs)} epígrafe(s) oficiales",
        ]
        actual = ""
        for apartado in self.reparto:
            if apartado.materia.epigraph_code != actual:
                actual = apartado.materia.epigraph_code
                titulo = dict(self.epigraphs).get(actual, "")
                lineas.append(f"  {actual} — {titulo}")
            lineas.extend(apartado.lineas())
        if self.sin_materia:
            lineas.append(
                f"    AVISO: {len(self.sin_materia)} hecho(s) no son de ninguna materia del tema y "
                "NO tienen apartado (no hay cajón): son preguntas mal clasificadas y van a la cola "
                "de clasificación antes de redactar"
            )
            for hecho in self.sin_materia[:10]:
                lineas.append(f"      · {hecho.text[:110]}")
            if len(self.sin_materia) > 10:
                lineas.append(f"      · … y {len(self.sin_materia) - 10} más")
        if self.grupos_sin_materia:
            lineas.append(
                f"    AVISO: {len(self.grupos_sin_materia)} grupo(s) de preguntas "
                f"({sum(len(g.questions) for g in self.grupos_sin_materia)} pregunta(s)) no son de "
                "ninguna materia del tema"
            )
        if self.fuera_de_su_epigrafe:
            lineas.append(
                f"      · {len(self.fuera_de_su_epigrafe)} hecho(s) van a una materia del otro "
                "epígrafe porque es donde se estudian: el epígrafe que traían era el que no era, y "
                "se mueven a su sitio"
            )
        return tuple(lineas)

    @property
    def fusionados(self) -> tuple[Hecho, ...]:
        """Los hechos que se agruparon con otro: los que había de más."""
        return tuple(hecho for apartado in self.reparto for hecho in apartado.fusionados)

    @property
    def grupos_sin_anclaje(self) -> tuple[str, ...]:
        """Las firmas de pregunta cuyo apartado no tiene ningún hecho suyo.

        Es la prueba de que la deduplicación no dejó ninguna pregunta sin anclaje: el hecho que se
        queda conserva la unión de las preguntas, así que este conjunto tiene que estar vacío.
        """
        faltan: list[str] = []
        for apartado in self.reparto:
            ancladas = apartado.firmas_de_grupo
            faltan.extend(
                grupo.signature for grupo in apartado.grupos if grupo.signature not in ancladas
            )
        return tuple(faltan)


# --- la deduplicación -------------------------------------------------------------------------


def etiquetas(texto: str) -> frozenset[str]:
    """Las siglas y las cifras de un hecho: lo que no se puede perder al fusionarlo con otro.

    `LLC` no es `MAC`, `TPDU` no es `APDU`, `7498` no es `9001` y el puerto 53 no es el 80. Las
    cifras se marcan con `#` delante para que no se confundan con una sigla que sea un número
    suelto.
    """
    siglas = {encontrada.lower() for encontrada in _SIGLA.findall(texto)}
    cifras = {f"#{encontrada}" for encontrada in _CIFRA.findall(texto)}
    return frozenset(siglas | cifras)


def _pesos_idf(conjuntos: Sequence[frozenset[str]]) -> dict[str, float]:
    """Cuánto pesa cada término: un término que sale en todos los hechos de la materia pesa poco.

    Es lo que hace que la deduplicación mire lo que **distingue** un hecho («presentación»,
    «sesión», «FTP») y no el relleno que comparten todos («capa», «modelo», «OSI»).
    """
    total = len(conjuntos)
    frecuencia: dict[str, int] = {}
    for terminos in conjuntos:
        for termino in terminos:
            frecuencia[termino] = frecuencia.get(termino, 0) + 1
    return {termino: math.log(1.0 + total / veces) for termino, veces in frecuencia.items()}


def _dice(uno: frozenset[str], otro: frozenset[str], peso: dict[str, float]) -> float:
    """Parecido de Dice ponderado: 1.0 es el mismo vocabulario, 0.0 no comparten nada."""
    if not uno or not otro:
        return 0.0
    comunes = sum(peso[termino] for termino in uno & otro)
    total = sum(peso[termino] for termino in uno) + sum(peso[termino] for termino in otro)
    return 0.0 if not total else 2 * comunes / total


def grupos_equivalentes(
    hechos: Sequence[Hecho], *, umbral: float = UMBRAL_EQUIVALENCIA
) -> tuple[tuple[Hecho, ...], ...]:
    """Los hechos agrupados por lo que dicen, en el orden en que llegan.

    Se agrupa **contra el representante** de cada grupo y no contra cualquiera de sus miembros: si
    se agrupara contra cualquiera, dos hechos que no se parecen acabarían en el mismo grupo por
    cadena (uno habla de FTP y DNS, y por ahí se juntan «FTP es de usuario» con «DNS es de soporte»,
    que son dos hechos distintos). El representante es el hecho **más completo** del grupo —el que
    tiene más términos significativos—, para que al quedarse uno se pierda lo menos posible.
    """
    if not hechos:
        return ()
    conjuntos = [frozenset(terminos_significativos(hecho.text)) for hecho in hechos]
    marcas = [etiquetas(hecho.text) for hecho in hechos]
    peso = _pesos_idf(conjuntos)
    grupos: list[list[int]] = []
    representantes: list[int] = []
    por_termino: dict[str, list[int]] = {}
    for posicion, terminos in enumerate(conjuntos):
        candidatos: dict[int, None] = {}
        for termino in terminos:
            for grupo in por_termino.get(termino, ()):
                candidatos[grupo] = None
        elegido: int | None = None
        mejor = 0.0
        for grupo in candidatos:
            representante = representantes[grupo]
            suyas, ajenas = marcas[posicion], marcas[representante]
            # La guarda: si cada uno tiene una sigla o una cifra que el otro no tiene, no son el
            # mismo hecho. Se exige que uno de los dos conjuntos esté contenido en el otro.
            if not (suyas <= ajenas or ajenas <= suyas):
                continue
            parecido = _dice(terminos, conjuntos[representante], peso)
            if parecido >= umbral and parecido > mejor:
                elegido, mejor = grupo, parecido
        if elegido is None:
            grupos.append([posicion])
            representantes.append(posicion)
            for termino in terminos:
                por_termino.setdefault(termino, []).append(len(grupos) - 1)
            continue
        grupos[elegido].append(posicion)
        # El representante pasa a ser el más completo del grupo: el que se queda tiene que poder
        # sostener lo que decían los demás.
        if len(terminos) > len(conjuntos[representantes[elegido]]):
            representantes[elegido] = posicion
    return tuple(tuple(hechos[miembro] for miembro in grupo) for grupo in grupos)


def deduplicar(
    hechos: Sequence[Hecho], *, umbral: float = UMBRAL_EQUIVALENCIA
) -> tuple[Hecho, ...]:
    """Un hecho por grupo de hechos equivalentes, **con la unión de sus preguntas**.

    Lo que se conserva del grupo, y por qué:

    - **las preguntas de todos** (`source_groups` y `source_questions`): es lo que hace que ninguna
      pregunta se quede sin el hecho que la ancla. Perder la pregunta de un hecho absorbido sería
      dejar una pregunta sin apartado, que es justo lo que no puede pasar;
    - **el texto del más completo**, con su tipo y su nota;
    - `doubtful` se enciende si **cualquiera** del grupo lo estaba: una clave que contradice la
      norma
      no deja de contradecirla porque otro hecho del grupo se dijera mejor.
    """
    salida: list[Hecho] = []
    for grupo in grupos_equivalentes(hechos, umbral=umbral):
        representante = max(grupo, key=lambda hecho: len(terminos_significativos(hecho.text)))
        grupos_origen = sorted({firma for hecho in grupo for firma in hecho.source_groups})
        preguntas = sorted({pregunta for hecho in grupo for pregunta in hecho.source_questions})
        notas = [hecho.note for hecho in grupo if hecho.note]
        salida.append(
            Hecho(
                text=representante.text,
                kind=representante.kind,
                epigraph_code=representante.epigraph_code,
                source_groups=tuple(grupos_origen),
                source_questions=tuple(preguntas),
                doubtful=any(hecho.doubtful for hecho in grupo),
                note=None if not notas else "; ".join(dict.fromkeys(notas)),
                fact_id=representante.fact_id,
                section_key=representante.section_key,
            )
        )
    return tuple(salida)


def _mejor_materia(limpio: str, candidatas: Sequence[Materia]) -> Materia | None:
    """La materia que menciona el texto **antes** (y, a igualdad, la de prioridad más baja).

    Es lo que hace que «DHCP es un protocolo … el servidor DNS» sea un hecho de DHCP y no de DNS: un
    hecho habla de su materia primero y de las demás después, para compararlas. Sin esa regla,
    cualquier mención de un distractor se llevaría el hecho.
    """
    mejor: tuple[int, int, Materia] | None = None
    for materia in sorted(candidatas, key=lambda materia: materia.prioridad):
        if not materia.patrones:
            continue
        posiciones = [
            casado.start()
            for patron in materia.patrones
            if (casado := re.search(patron, limpio)) is not None
        ]
        if not posiciones:
            continue
        candidato = (min(posiciones), materia.prioridad, materia)
        if mejor is None or candidato[:2] < mejor[:2]:
            mejor = candidato
    return None if mejor is None else mejor[2]


def _materia_osi(limpio: str, materias: Sequence[Materia]) -> Materia | None:
    """A qué de las cuatro partes del modelo OSI va un hecho, por lo que el hecho dice.

    Es un reparto **por asunto**, no por posición ni por prioridad, porque las cuatro partes hablan
    de lo mismo y comparten vocabulario: casi todos los hechos del OSI nombran una capa, y muchos
    nombran además la unidad de datos que maneja. Lo que decide es lo primero que el hecho
    **nombra como sujeto**, en este orden:

    1. **el dispositivo** (un `switch`, un `router`, un `hub`): el hecho es de la parte de los
       dispositivos que trabajan en cada capa, aunque diga «conmuta tramas»;
    2. **la unidad de datos** (`PDU`, `trama`, `paquete`, `segmento`, `bit`), el encapsulado y las
       subcapas `LLC` y `MAC`, que van dentro de la capa de enlace;
    3. **la capa concreta** (por su nombre o por su número): es la parte de las siete capas, una a
       una, con su función;
    4. y si no nombra nada de eso, el hecho es del **modelo**: qué es OSI y qué es un sistema
       abierto.

    Solo se llama cuando el reparto normal **ya ha decidido que el texto es de la familia OSI**: si
    se llamara siempre, «la trama se envía al puerto 53» acabaría en las unidades de datos del OSI,
    que es justo lo que no puede pasar.
    """
    de_la_familia = [materia for materia in materias if materia.familia == FAMILIA_OSI]
    if not de_la_familia:
        return None
    for clave, patrones in _REGLAS_OSI:
        if any(re.search(patron, limpio) for patron in patrones):
            elegida = next((materia for materia in de_la_familia if materia.key == clave), None)
            if elegida is not None:
                return elegida
    return None


def materia_de(
    texto: str, epigraph_code: str | None, materias: Sequence[Materia]
) -> Materia | None:
    """A qué materia va un texto, o `None` si no es de ninguna.

    Se busca primero entre las materias **de su epígrafe** (un hecho de IV.7.1 se queda en IV.7.1)
    y, si en el suyo no casa con ninguna, se busca en el catálogo entero: hay hechos a los que el
    modelo puso el epígrafe que no era (9 en IV.7: capas de OSI etiquetadas como IV.7.2), y su
    contenido manda, porque su sitio es donde se estudia. Esos se cuentan aparte y se mueven.

    Dos pasos más, y los dos importan:

    - si la materia que ha ganado es de una **familia** (el modelo OSI), se vuelve a decidir entre
      sus hermanas por asunto (`_materia_osi`): sus cuatro partes comparten vocabulario y decidir
      por la primera palabra que casa sería echarlo a suertes;
    - lo que no casa con nada devuelve `None`, y **no** hay cajón que lo recoja: un hecho sin
      materia es una pregunta mal clasificada, y se dice en vez de esconderse.
    """
    suyas = tuple(materia for materia in materias if materia.epigraph_code == epigraph_code)
    limpio = normalise(texto)
    encontrada = _mejor_materia(limpio, suyas) if suyas else None
    if encontrada is None:
        encontrada = _mejor_materia(limpio, tuple(m for m in materias if not m.es_cajon))
    if encontrada is not None and encontrada.familia:
        return _materia_osi(limpio, materias) or encontrada
    if encontrada is not None:
        return encontrada
    return next((materia for materia in suyas if materia.es_cajon), None)


def _texto_de_grupo(grupo: QuestionGroup) -> str:
    """De un grupo de preguntas se clasifica el **enunciado**: las opciones traen los distractores
    (NTP, DNS, 137) y clasificar por ellos mandaría la pregunta a la materia del distractor."""
    return grupo.representative.stem


def repartir_hechos(
    hechos: Sequence[Hecho],
    materias: Sequence[Materia],
    *,
    materia_por_grupo: Mapping[str, str] | None = None,
    grupos_sin_materia: Collection[str] = (),
) -> tuple[dict[str, list[Hecho]], list[Hecho]]:
    """Los hechos de cada materia, por su clave, y los que no son de ninguna.

    Manda **la pregunta de la que sale el hecho**, no su texto: un hecho es una frase escrita para
    contestar unas preguntas concretas, así que su sitio es el de esas preguntas. Si se repartiera
    por su texto, el enunciado y el hecho podrían acabar en apartados distintos y la pregunta se
    quedaría sin el hecho que la ancla en su propio apartado (116 preguntas en IV.7 antes de esto).

    El texto decide en dos casos, y solo en dos: un hecho **sin** pregunta de origen (lo escribió el
    modelo para un lote que no identificó) y un hecho cuyas preguntas van a materias distintas
    (porque el propio hecho habla de dos cosas).

    Y un hecho cuyas preguntas **no son de este tema** (`grupos_sin_materia`) se va con ellas: si la
    pregunta está mal clasificada y va a la cola, su hecho no puede quedarse aquí a sostener un
    apartado del que ya no es. Es lo que pidió el propietario: «sus datos se van con ellas».

    Después hay una **segunda pasada, de sobrantes**: un hecho que va con sus preguntas pero cuyo
    texto es de otra materia del tema se mueve a la suya, **siempre que su pregunta siga teniendo
    algún hecho donde está**. Es lo que deja el apartado de acceso remoto con los hechos de Telnet,
    SSH y RDP aunque salieran de la misma pregunta que los de SNMP: el hecho de Telnet se va a su
    sitio y la pregunta no se queda sin nada, que es la condición que hace segura la mudanza.
    """
    por_clave: dict[str, list[Hecho]] = {materia.key: [] for materia in materias}
    por_grupo = materia_por_grupo or {}
    ajenas = set(grupos_sin_materia)
    sin_materia: list[Hecho] = []
    de_su_texto: dict[str, str] = {}
    for hecho in hechos:
        if hecho.source_groups and all(firma in ajenas for firma in hecho.source_groups):
            sin_materia.append(hecho)
            continue
        destinos = {por_grupo[firma] for firma in hecho.source_groups if firma in por_grupo}
        clave = next(iter(destinos)) if len(destinos) == 1 else None
        if clave is None:
            materia = materia_de(hecho.text, hecho.epigraph_code, materias)
            if materia is None:
                sin_materia.append(hecho)
                continue
            clave = materia.key
        else:
            propia = materia_de(hecho.text, hecho.epigraph_code, materias)
            if propia is not None and propia.key != clave:
                de_su_texto[hecho.fact_id] = propia.key
        por_clave[clave].append(hecho)

    if de_su_texto:
        cuenta: dict[str, int] = {}
        for hecho in hechos:
            for firma in hecho.source_groups:
                clave = por_grupo.get(firma)
                if clave is not None:
                    cuenta[firma] = cuenta.get(firma, 0) + 1
        for hecho in hechos:
            destino = de_su_texto.get(hecho.fact_id)
            if destino is None:
                continue
            suyo = next(
                (por_grupo[firma] for firma in hecho.source_groups if firma in por_grupo), None
            )
            if suyo is None:
                continue
            # Solo se muda si la pregunta sigue anclada en su apartado sin este hecho.
            if all(
                cuenta.get(firma, 0) > 1
                for firma in hecho.source_groups
                if por_grupo.get(firma) == suyo
            ):
                por_clave[suyo].remove(hecho)
                por_clave[destino].append(hecho)
                for firma in hecho.source_groups:
                    if por_grupo.get(firma) == suyo:
                        cuenta[firma] -= 1
    return por_clave, sin_materia


def repartir_grupos(
    grupos: Sequence[QuestionGroup], materias: Sequence[Materia]
) -> tuple[dict[str, list[QuestionGroup]], list[QuestionGroup]]:
    """Los grupos de preguntas de cada materia, por su clave, y los que no son de ninguna."""
    por_clave: dict[str, list[QuestionGroup]] = {materia.key: [] for materia in materias}
    sin_materia: list[QuestionGroup] = []
    for grupo in grupos:
        epigrafe = grupo.epigraph_code or grupo.representative.epigraph_code
        materia = materia_de(_texto_de_grupo(grupo), epigrafe, materias)
        if materia is None:
            sin_materia.append(grupo)
            continue
        por_clave[materia.key].append(grupo)
    return por_clave, sin_materia


def validar_catalogo(topic_code: str, materias: Sequence[Materia]) -> None:
    """Un catálogo mal formado se dice antes de repartir nada, no se descubre en el resultado.

    Dos invariantes: no hay claves de materia repetidas, y **como mucho** hay un cajón por epígrafe
    (si lo hay, no puede tener patrones: dejaría de recoger lo que no casa con nada). Un catálogo
    **sin** cajón es válido y es el de IV.7: no hay apartado de revisión, y lo que no case con
    ninguna materia se cuenta y se dice.
    """
    por_epigrafe: dict[str, list[Materia]] = {}
    for materia in materias:
        por_epigrafe.setdefault(materia.epigraph_code, []).append(materia)
    claves = [materia.key for materia in materias]
    if len(set(claves)) != len(claves):
        raise ValueError(f"el catálogo de {topic_code} tiene claves de materia repetidas")
    for epigrafe, suyas in por_epigrafe.items():
        cajones = [materia for materia in suyas if materia.es_cajon]
        if len(cajones) > 1:
            raise ValueError(
                f"el epígrafe {epigrafe} de {topic_code} tiene {len(cajones)} cajones y no puede "
                "tener más de uno"
            )


def indice_de(
    *,
    topic_code: str,
    topic_title: str,
    epigraphs: Sequence[tuple[str, str]],
    hechos: Sequence[Hecho] = (),
    grupos: Sequence[QuestionGroup] = (),
    umbral_equivalencia: float = UMBRAL_EQUIVALENCIA,
) -> IndiceDelTema:
    """El índice del tema con el catálogo de sus epígrafes. Falla si el tema no tiene catálogo.

    Un catálogo de materias es una decisión de contenido: inventarlo a medias para un tema que no se
    ha definido sería escribir apuntes a ciegas. Los temas sin catálogo se dicen, no se inventan.

    El orden de los pasos importa: **primero se reparte** (cada hecho y cada grupo a su materia, con
    el texto tal como está) y **después se agrupan los repetidos dentro de cada materia**. Al revés,
    la deduplicación decidiría a qué apartado va cada pregunta —dos hechos equivalentes pueden
    repartirse por su texto— y una pregunta podría cambiar de apartado por haber juntado dos hechos.
    Así, el reparto es el mismo con deduplicación y sin ella, y lo único que cambia es cuántos
    hechos
    hay que redactar.
    """
    materias = catalogo(topic_code)
    if materias is None:
        raise KeyError(topic_code)
    validar_catalogo(topic_code, materias)
    conocidos = {codigo for codigo, _ in epigraphs}
    for materia in materias:
        if materia.epigraph_code not in conocidos:
            raise ValueError(
                f"la materia «{materia.key}» apunta al epígrafe {materia.epigraph_code}, que no "
                f"está en el temario de {topic_code}"
            )
    por_materia_grupos, grupos_sin_materia = repartir_grupos(grupos, materias)
    materia_por_grupo = {
        grupo.signature: materia.key
        for materia in materias
        for grupo in por_materia_grupos[materia.key]
    }
    por_materia_hechos, sin_materia = repartir_hechos(
        hechos,
        materias,
        materia_por_grupo=materia_por_grupo,
        grupos_sin_materia={grupo.signature for grupo in grupos_sin_materia},
    )
    reparto: list[RepartoMateria] = []
    for materia in materias:
        originales = tuple(por_materia_hechos[materia.key])
        quedan = deduplicar(originales, umbral=umbral_equivalencia)
        # Lo que se agrupa se guarda aparte, para poder decir cuántos había y cuántos quedan.
        conservados = {hecho.fact_id for hecho in quedan}
        reparto.append(
            RepartoMateria(
                materia=materia,
                hechos=quedan,
                grupos=tuple(por_materia_grupos[materia.key]),
                fusionados=tuple(hecho for hecho in originales if hecho.fact_id not in conservados),
            )
        )
    definitivo = tuple(reparto)
    return IndiceDelTema(
        topic_code=topic_code,
        topic_title=topic_title,
        epigraphs=tuple(epigraphs),
        reparto=definitivo,
        sin_materia=tuple(sin_materia),
        fuera_de_su_epigrafe=tuple(
            hecho
            for apartado in definitivo
            for hecho in apartado.hechos
            if hecho.epigraph_code != apartado.materia.epigraph_code
        ),
        grupos_sin_materia=tuple(grupos_sin_materia),
        hechos_originales=len(hechos),
    )


def plan_de(
    indice: IndiceDelTema,
    *,
    max_hechos_por_apartado: int = 0,
) -> tuple[NoteSection, ...]:
    """El plan de redacción del índice: un apartado por materia, en el orden en que se estudia.

    Es lo que convierte el índice aprobado en lo que se redacta. Tres decisiones:

    - **un apartado por materia**, con sus hechos ya agrupados: es el índice que el propietario
      aprobó, no los trozos de cuarenta hechos que salían de los lotes;
    - **las materias sin hechos no generan apartado**: un apartado vacío es un hueco, y los huecos
      los declara el índice, no el texto;
    - `max_hechos_por_apartado` (0 = sin tope) parte una materia muy grande en trozos numerados
      **de la misma materia**, que es lo único que se puede partir sin volver a repetir el tema.
      Los trozos comparten las tres primeras palabras del título a propósito: son el mismo apartado
      y se leen seguidos.
    """
    apartados: list[NoteSection] = []
    posicion = 1
    for reparto in indice.reparto:
        if not reparto.hechos:
            continue
        if max_hechos_por_apartado <= 0 or len(reparto.hechos) <= max_hechos_por_apartado:
            trozos = [reparto.hechos]
        else:
            trozos = [
                reparto.hechos[inicio : inicio + max_hechos_por_apartado]
                for inicio in range(0, len(reparto.hechos), max_hechos_por_apartado)
            ]
        for numero, trozo in enumerate(trozos, start=1):
            sufijo = "" if len(trozos) == 1 else f" ({numero}/{len(trozos)})"
            clave = reparto.materia.key if len(trozos) == 1 else f"{reparto.materia.key}-{numero}"
            apartados.append(
                NoteSection(
                    key=clave,
                    epigraph_code=reparto.materia.epigraph_code,
                    title=f"{reparto.materia.title}{sufijo}",
                    anchor=clave,
                    position=posicion,
                    facts=tuple(trozo),
                )
            )
            posicion += 1
    return tuple(apartados)


# --- el catálogo de IV.7 --------------------------------------------------------------------------

#: La clave de la familia del modelo OSI. Sus cuatro materias comparten los patrones que dicen «esto
#: es del modelo OSI» y se reparten después por asunto (`_REGLAS_OSI`): si cada una tuviera patrones
#: propios, la que ganara sería la de siempre (la primera por prioridad) y las otras tres quedarían
#: vacías.
FAMILIA_OSI = "osi"

#: Lo que dice que un texto es del modelo OSI: la sigla, la norma de la que sale, el sistema abierto
#: y las palabras que solo aparecen hablando de sus capas.
_PATRONES_OSI: tuple[str, ...] = (
    r"\bosi\b",
    r"\biso\b",
    r"sistema abierto",
    r"interoperabilidad",
    r"\bsubcapa",
    r"\bllc\b",
    r"\bpdu\b",
    r"\bencapsul",
    r"capa (1|2|3|4|5|6|7|fisica|enlace|de enlace|red|transporte|sesion|presentacion|aplicacion)",
    r"nivel (1|2|3|4|5|6|7|fisico|de enlace|red|transporte|sesion|presentacion|aplicacion)",
    r"\bpresentacion\b",
    r"\bsesion\b",
    r"\bcapas?\b",
    r"\bnivel(es)?\b",
    # Los dispositivos que trabajan en cada capa: su apartado es parte del modelo (d), así que sus
    # palabras también dicen «esto es del OSI» (el `hub` que se define «en la interconexión»).
    r"\bhubs?\b",
    r"\bswitches?\b",
    r"\bconmutador",
    r"\brepetidor",
    r"\bbridge\b|\bpuente",
    r"\bpasarela",
    # El vocabulario del nivel de aplicación del modelo (`ASE`, contexto de aplicación), que es
    # donde se estudia.
    r"\bases\b",
    r"contexto de aplicacion",
)

#: Las cuatro partes del modelo OSI, en el orden en que se miran. Las tres primeras tienen su
#: vocabulario; lo que no casa con ninguna es del **modelo** (qué es OSI y qué es un sistema
#: abierto), que es la materia `osi-que-es` y no una regla más: así no hay un quinto destino que
#: nadie haya aprobado.
#:
#: El orden es el de la pregunta que decide: ¿nombra un dispositivo? ¿nombra una unidad de datos o
#: una subcapa? ¿nombra una capa concreta? Un `switch` que «conmuta tramas» es un hecho de
#: dispositivos, no de unidades, y por eso los dispositivos se miran antes.
_REGLAS_OSI: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "osi-dispositivos",
        (
            r"\bswitches?\b",
            r"\bconmutador",
            r"\brouters?\b",
            r"\bencaminador",
            r"\bhubs?\b",
            r"\bconcentrador",
            r"\brepetidor",
            r"\bbridge\b|\bpuente",
            r"\bgateway\b|\bpasarela",
            r"\bmodems?\b",
            r"punto de acceso",
            r"tarjeta de red",
            r"\bnic\b",
            r"dispositivos? (de|que|utilizados)",
        ),
    ),
    (
        "osi-unidades",
        (
            r"\bpdu\b",
            r"unidad(es)? de datos",
            r"\bencapsul",
            r"\bsubcapas?\b|\bsubniveles?\b",
            r"\bllc\b",
            r"\bmac\b",
            r"\btramas?\b|\bframes?\b",
            r"\bsegmentos?\b",
            r"\bpaquetes?\b|\bdatagramas?\b",
            r"\bbytes?\b",
            r"\btdpu\b|\bapdu\b|\bbpdu\b",
        ),
    ),
    (
        "osi-que-es",
        (
            r"sistema abierto",
            r"iso 7498",
            r"modelo de referencia",
            r"\binteroperabilidad\b",
            r"\bmodular\b",
            r"independencia entre capas",
            r"no debe afectar",
            r"transparente para el resto",
            r"dividir la red en capas",
            r"sistemas cerrados",
            r"estandar de comunicaciones",
            r"open systems? interconnection",
        ),
    ),
    (
        "osi-capas",
        (
            r"\bnivel(es)?\b",
            r"capa (1|2|3|4|5|6|7|fisica|enlace|de enlace|red|transporte|sesion|presentacion|"
            r"aplicacion)",
            r"nivel (1|2|3|4|5|6|7|fisico|de enlace|red|transporte|sesion|presentacion|aplicacion)",
            r"\bpresentacion\b",
            r"\bsesion\b",
            r"\baplicacion\b",
            r"\btransporte\b",
            r"\benlace\b",
            r"capa fisica|\bfisica\b",
            r"\bcapas?\b",
        ),
    ),
)

#: IV.7, por epígrafes y **en el orden en que se estudia** (el que se enseña). El orden del reparto
#: es otro y va en `prioridad`: un hecho que habla de POP3 y del puerto 110 es un hecho de correo,
#: no de la tabla de puertos, así que los protocolos se reparten antes que la tabla de puertos.
_MATERIAS_IV7: tuple[Materia, ...] = (
    # --- IV.7.1: el modelo de referencia y la arquitectura
    Materia(
        key="tcpip-arquitectura",
        epigraph_code="IV.7.1",
        title="La arquitectura TCP/IP: capas, protocolos y familias",
        resumen=(
            "Qué es TCP/IP como familia de protocolos, sus cuatro capas (acceso a la red, "
            "internet, transporte y aplicación), qué protocolos van en cada una, los protocolos de "
            "usuario y de soporte, la correspondencia capa a capa con el modelo OSI y las familias "
            "que **no** son TCP/IP (IPX/SPX y NetBEUI), que se nombran solo al compararlas."
        ),
        patrones=(
            r"tcp ip",
            r"\barquitectura\b",
            r"capa de internet",
            r"acceso a la red",
            r"protocolos? de (usuario|soporte)",
            r"\benrutable\b",
            r"familia de protocolos|familias de protocolos",
            r"\bcuatro capas\b",
            r"\bconectividad extremo a extremo\b",
            # Las familias que no son TCP/IP: van aquí porque aquí es donde se comparan familias,
            # que es lo único que se dice de ellas.
            r"\bipx\b|\bspx\b",
            r"netbeui|netbios",
        ),
        prioridad=10,
    ),
    Materia(
        key="osi-que-es",
        epigraph_code="IV.7.1",
        title="El modelo OSI y el sistema abierto",
        resumen=(
            "Qué es el modelo de referencia OSI (ISO 7498), qué es un sistema abierto según ISO, "
            "para qué sirve dividir la comunicación en capas (sistema modular e independencia "
            "entre capas), la comunicación vertical y horizontal (virtual) y la interoperabilidad."
        ),
        patrones=_PATRONES_OSI,
        prioridad=21,
        familia=FAMILIA_OSI,
    ),
    Materia(
        key="osi-capas",
        epigraph_code="IV.7.1",
        title="Las siete capas del modelo OSI, una a una",
        resumen=(
            "El nombre, el número y la función de cada una de las siete capas: física, enlace de "
            "datos, red, transporte, sesión, presentación y aplicación. Incluye el orden de las "
            "capas y qué hace cada nivel."
        ),
        patrones=_PATRONES_OSI,
        prioridad=22,
        familia=FAMILIA_OSI,
    ),
    Materia(
        key="osi-unidades",
        epigraph_code="IV.7.1",
        title="Unidades de datos y encapsulado: la subcapa LLC y la MAC",
        resumen=(
            "La unidad de datos (PDU) de cada capa —bit, trama, paquete, segmento— y el "
            "encapsulado. Las dos subcapas de la capa de enlace de datos: LLC (Logical Link "
            "Control) y MAC (Media Access Control)."
        ),
        patrones=_PATRONES_OSI,
        prioridad=23,
        familia=FAMILIA_OSI,
    ),
    Materia(
        key="osi-dispositivos",
        epigraph_code="IV.7.1",
        title="Qué dispositivos trabajan en cada capa",
        resumen=(
            "En qué capa del modelo OSI opera cada dispositivo de interconexión: el repetidor y el "
            "concentrador (hub) en la capa física, el conmutador (switch) y el puente (bridge) en "
            "la de enlace, el encaminador (router) en la de red y la pasarela (gateway) en las "
            "superiores."
        ),
        patrones=_PATRONES_OSI,
        prioridad=24,
        familia=FAMILIA_OSI,
    ),
    Materia(
        key="conceptos-del-modelo",
        epigraph_code="IV.7.1",
        title="Servicio, protocolo, interfaz y comunicación entre capas",
        resumen=(
            "El vocabulario del modelo: qué es un servicio y una primitiva, qué es un protocolo, "
            "la interfaz entre capas adyacentes, la comunicación vertical y horizontal (virtual), "
            "la multiplexación y las técnicas de nivel de enlace (piggybacking)."
        ),
        patrones=(
            r"\bservicios?\b",
            r"\bprotocolos?\b",
            r"\binterfaz(es)?\b",
            r"\bprimitivas?\b",
            r"\bpiggyback",
            r"\bmultiplexa",
            r"modos? de transmision",
            r"\bduplex\b",
            r"\bcheckpoints?\b",
            r"\bpuntos de (verificacion|sincronizacion)\b",
            # «¿Cómo se llaman los puntos insertados en la corriente de datos para permitir la
            # recuperación tras una interrupción?»: son los puntos de comprobación de la capa de
            # sesión, y el enunciado no usa ninguna de las dos palabras.
            r"puntos insertados en la corriente",
            r"recuperacion tras una interrupcion",
            r"\bmodular\b",
        ),
        prioridad=90,
    ),
    # --- IV.7.2: los protocolos
    Materia(
        key="ipv6",
        epigraph_code="IV.7.2",
        title="IPv6: direcciones, cabecera y convivencia con IPv4",
        resumen=(
            "El direccionamiento de 128 bits y su notación, los tipos de dirección (global "
            "unicast, link-local, ULA fc00::/7, multicast, loopback ::1, no especificada), la "
            "cabecera fija de 40 bytes y sus campos (flow label, traffic class, hop limit), los "
            "jumbogramas, la MTU mínima de 1280 y los mecanismos de transición."
        ),
        patrones=(
            r"\bipv6\b",
            # El enunciado de una pregunta llega con erratas de OCR («1Pv6»): sin esto, la pregunta
            # del campo Clase de Tráfico caía en el cajón de revisión.
            r"\bpv6\b",
            r"\bff0[0-9]",
            r"\bfc00\b|\bfd00\b",
            r"\bula\b",
            r"jumbograma",
            r"flow label|etiqueta de flujo",
            r"hop limit",
            r"neighbor (solicitation|advertisement)",
            r"solicited node",
            r"cabeceras? de extension",
            r"eui 64",
            r"traffic class",
        ),
        prioridad=10,
    ),
    Materia(
        key="arp",
        epigraph_code="IV.7.2",
        title="ARP y RARP: la dirección física",
        resumen=(
            "Cómo se pasa de una dirección IP a la dirección MAC dentro de la red local (ARP), la "
            "resolución inversa (RARP) y las direcciones físicas y de difusión."
        ),
        patrones=(r"\barp\b", r"\brarp\b", r"direccion fisica", r"direcciones? mac"),
        prioridad=11,
    ),
    Materia(
        key="icmp",
        epigraph_code="IV.7.2",
        title="ICMP: los mensajes de control y error",
        resumen=(
            "Qué es ICMP (y ICMPv6), en qué capa vive, sus mensajes de error (destino "
            "inalcanzable, tiempo excedido, redirección) y su relación con el TTL y con las "
            "herramientas de diagnóstico."
        ),
        patrones=(
            r"\bicmp",
            r"time exceeded",
            r"destino inalcanzable",
            r"destination unreachable",
        ),
        prioridad=12,
    ),
    Materia(
        key="dns",
        epigraph_code="IV.7.2",
        title="DNS: nombres de dominio",
        resumen=(
            "La base de datos distribuida y jerárquica de nombres, los tipos de registro (A, AAAA, "
            "NS, MX, CNAME, SOA, PTR, TXT), el 53/UDP y 53/TCP, la resolución directa e inversa y "
            "las consultas."
        ),
        patrones=(
            r"\bdns\b",
            r"nombres? de dominio",
            r"registros? (a|aaaa|ns|mx|cname|soa|ptr|txt|srv)\b",
            r"\bnslookup\b",
            r"resolucion (de nombres|inversa|directa)",
            r"transferencias? de zona",
        ),
        prioridad=13,
    ),
    Materia(
        key="dhcp",
        epigraph_code="IV.7.2",
        title="DHCP y la configuración automática",
        resumen=(
            "La asignación dinámica de direcciones (DHCP, sus puertos 67-68/UDP, BOOTP), la "
            "configuración manual frente a la automática y lo que pasa cuando no hay servidor."
        ),
        patrones=(
            r"\bdhcp\b",
            r"\bbootp\b",
            r"asignacion (dinamica|automatica) de direcciones",
            r"direccionamiento (estatico|dinamico)",
            r"\bconcesion\b",
        ),
        prioridad=14,
    ),
    Materia(
        key="web",
        epigraph_code="IV.7.2",
        title="HTTP y HTTPS",
        resumen=(
            "El protocolo de transferencia de hipertexto, sus métodos y códigos, el 80/TCP y el "
            "443/TCP con TLS, y HTTP/2 y HTTP/3 como versiones."
        ),
        patrones=(r"\bhttp", r"\bhipertexto\b", r"\bweb\b"),
        prioridad=15,
    ),
    Materia(
        key="correo",
        epigraph_code="IV.7.2",
        title="Correo electrónico: SMTP, POP3, IMAP y sus versiones seguras",
        resumen=(
            "El envío (SMTP en el 25 y submission en el 587), la recogida (POP3 en el 110 y 995, "
            "IMAP4 en el 143 y 993), el formato de los mensajes y los protocolos con cifrado."
        ),
        patrones=(
            r"\bsmtp\b",
            r"\bpop3\b|\bpop2\b",
            r"\bimap",
            r"\bcorreo\b",
            r"\bqmtp\b",
            r"\bsubmission\b",
        ),
        prioridad=16,
    ),
    Materia(
        key="ficheros",
        epigraph_code="IV.7.2",
        title="Transferencia de ficheros: FTP, FTPS, SFTP y TFTP",
        resumen=(
            "FTP y sus dos conexiones (20 y 21/TCP), TFTP sobre 69/UDP, SFTP sobre SSH (22/TCP) y "
            "FTPS: en qué se diferencian y cuál va cifrado."
        ),
        patrones=(
            r"\bftp\b",
            r"\bftps\b",
            r"\bsftp\b",
            r"\btftp\b",
            r"transferencia de ficheros",
            r"\bscp\b",
        ),
        prioridad=17,
    ),
    Materia(
        key="acceso-remoto",
        epigraph_code="IV.7.2",
        title="Acceso remoto: Telnet, SSH y RDP",
        resumen=(
            "Cómo se entra a un equipo o a un servicio a distancia: Telnet en el 23/TCP (sin "
            "cifrado), SSH en el 22/TCP (con cifrado, autenticación y túneles) y RDP en el "
            "3389/TCP, con lo que aporta cada uno frente a los otros."
        ),
        patrones=(r"\btelnet\b", r"\bssh\b", r"\brdp\b", r"acceso remoto", r"escritorio remoto"),
        prioridad=18,
    ),
    Materia(
        key="directorio-y-gestion",
        epigraph_code="IV.7.2",
        title="Directorio y gestión: LDAP y SNMP",
        resumen=(
            "El acceso a servicios de directorio (LDAP y el 389/TCP, sobre el modelo X.500) y la "
            "gestión y monitorización de la red con SNMP: sus versiones (v1, v2c, v3 con "
            "seguridad), la MIB, las PDU y los puertos 161 y 162."
        ),
        patrones=(
            r"\bsnmp",
            r"\bmib\b",
            r"gestion de red",
            r"\bmonitorizacion\b",
            r"\bldap\b",
            r"\bx 500\b|\bx500\b",
            r"gestion osi",
            r"servicios? de directorio",
        ),
        prioridad=18,
    ),
    Materia(
        key="subredes",
        epigraph_code="IV.7.2",
        title="Subredes, máscaras y CIDR",
        resumen=(
            "La máscara de subred y el prefijo (/24, /27, /29…), el cálculo de la dirección de red "
            "(AND bit a bit), la de difusión, el rango de direcciones utilizables, CIDR, VLSM y el "
            "reparto en subredes del mismo tamaño."
        ),
        patrones=(
            r"subred",
            r"subnet",
            r"\bmascaras?\b",
            r"\bprefijo",
            r"\bcidr\b",
            r"\bvlsm\b",
            r"direccion de red",
            r"direccion de difusion",
            r"\bbroadcast\b",
            r"direcciones? (utiles|validas)",
            r"hosts? (utilizables|disponibles|validas)",
            r"and bit a bit",
            r"bits? (de hosts?|para hosts?)",
            r"bloques de \d+",
            r"\bhosts?\b",
            # «¿A qué red pertenece el equipo 10.31.93.25/29?»: el enunciado trae la dirección con
            # su prefijo, y la normalización quita los puntos y la barra, así que se busca la forma
            # normalizada (`10 31 93 25 29`).
            r"a que red pertenece",
            r"\b\d{1,3}( \d{1,3}){3} \d{1,2}\b",
            # «Se va a abrir un nuevo Centro de Salud… ha dado el siguiente direccionamiento»: el
            # enunciado no dice «subred», dice «direccionamiento» y pide repartirlo.
            r"direccionamiento",
            r"tipo de direccion",
        ),
        prioridad=20,
    ),
    Materia(
        key="direcciones-especiales",
        epigraph_code="IV.7.2",
        title="Direcciones privadas, reservadas y NAT",
        resumen=(
            "Los rangos privados de la RFC 1918, las direcciones reservadas (loopback 127.0.0.0/8, "
            "0.0.0.0, APIPA 169.254.0.0/16, multicast 224.0.0.0/4, clase E), el direccionamiento "
            "público y privado y la traducción de direcciones (NAT)."
        ),
        patrones=(
            r"\bprivad",
            r"rfc 1918",
            r"\bloopback\b",
            r"\bapipa\b",
            r"169 254",
            r"multidifusion|\bmulticast\b",
            r"clase [de]\b",
            r"\bnat\b",
            r"\bpublica",
            r"reservad",
            r"127 0 0",
            r"no asignable",
            # «¿Cuál de estas direcciones es de Internet?»: se pregunta por una dirección pública
            # frente a las privadas, y el enunciado no usa la palabra «pública».
            r"es de internet|direcciones? de internet",
        ),
        prioridad=21,
    ),
    Materia(
        key="tcp",
        epigraph_code="IV.7.2",
        title="TCP: conexión, fiabilidad y cabecera",
        resumen=(
            "El protocolo orientado a conexión: el saludo de tres vías (SYN, SYN-ACK, ACK), los "
            "acuses y las retransmisiones, el control de flujo y de congestión, la cabecera (20 a "
            "60 bytes) y sus campos (puertos, número de secuencia, flags, ventana)."
        ),
        patrones=(
            r"\btcp\b",
            r"orientado a conexion",
            r"\bsyn\b",
            r"\backs?\b",
            r"ventana (de |de congestion|congestion)",
            r"retransmis",
            r"control de flujo",
            r"control de congestion",
            # La sonda que comprueba que la conexión sigue viva: es de TCP aunque el enunciado no
            # diga «TCP».
            r"keep ?alive",
        ),
        prioridad=25,
    ),
    Materia(
        key="udp",
        epigraph_code="IV.7.2",
        title="UDP: datagramas sin conexión",
        resumen=(
            "El protocolo no orientado a conexión: qué no garantiza (entrega, orden, duplicados), "
            "su cabecera de 8 bytes y para qué se usa frente a TCP."
        ),
        patrones=(
            r"\budp\b",
            r"no orientado a conexion",
            r"\bdatagramas?\b",
            # «…se observan pequeños cortes intermitentes en el audio. El sistema no retransmite los
            # paquetes perdidos»: el enunciado describe UDP (latencia antes que fiabilidad) sin
            # nombrarlo.
            r"no retransmit",
            r"paquetes perdidos",
            r"baja latencia",
            r"tiempo real",
            r"fiabilidad total",
        ),
        prioridad=26,
    ),
    Materia(
        key="encaminamiento",
        epigraph_code="IV.7.2",
        title="Encaminamiento: rutas, protocolos y puerta de enlace",
        resumen=(
            "El encaminamiento de paquetes y la tabla de rutas, la puerta de enlace por defecto, "
            "los protocolos de encaminamiento (RIP, OSPF, BGP) y su clasificación, el TTL y el "
            "número de saltos, y la alta disponibilidad de la puerta de enlace (VRRP, HSRP)."
        ),
        patrones=(
            r"encaminamiento|enrutamiento|\brouting\b",
            r"\brutas?\b",
            r"\brouters?\b",
            r"\bospf",
            # «RIPng» es RIP: sin quitar el límite de palabra, la pregunta de RIPng se quedaba sin
            # materia y caía en el cajón de revisión.
            r"\brip",
            # «RlPng»: el OCR del banco cambia la `I` por una `l` minúscula, y sin esto la pregunta
            # de RIPng se quedaba sin apartado.
            r"\brlpng\b|\brlp\b",
            r"\bbgp",
            r"\bttl\b",
            r"\bsaltos?\b",
            r"puerta de enlace",
            r"\bvrrp\b|\bhsrp\b",
            r"\bgateway\b",
            r"tabla de (rutas|encaminamiento)",
        ),
        prioridad=30,
    ),
    Materia(
        key="herramientas",
        epigraph_code="IV.7.2",
        title="Herramientas de diagnóstico y configuración",
        resumen=(
            "Con qué se mira la red desde el equipo: ping, traceroute/tracert, netstat, ipconfig e "
            "ifconfig, arp, y los ficheros de configuración de red del sistema operativo."
        ),
        patrones=(
            r"\bping\b",
            r"trace(route|rt)",
            r"\bnetstat\b",
            r"\bipconfig\b|\bifconfig\b",
            r"herramientas? de (diagnostico|red)",
            r"etc (fstab|hosts|netplan|sysconfig|resolv)",
            r"path mtu|camino mtu",
            r"depuracion de windows",
        ),
        # Se reparte **antes** que subredes: un hecho que habla de `ipconfig` o de `/etc/hosts`
        # es un hecho de herramientas, aunque mencione la máscara o los hosts de la red.
        prioridad=19,
    ),
    Materia(
        key="puertos",
        epigraph_code="IV.7.2",
        title="Puertos bien conocidos (una sola tabla)",
        resumen=(
            "Qué es un puerto, los rangos de la IANA (bien conocidos, registrados y dinámicos), "
            "los pares puerto-servicio que se confunden y **la tabla de puertos del tema, aquí y "
            "solo aquí**: el resto de apartados la enlazan."
        ),
        patrones=(r"\bpuertos?\b", r"well known", r"\biana\b", r"\bsockets?\b"),
        prioridad=40,
        tabla_unica=True,
    ),
    Materia(
        key="direccionamiento-ipv4",
        epigraph_code="IV.7.2",
        title="Direccionamiento IPv4: clases, cabecera y fragmentación",
        resumen=(
            "La dirección IPv4 y sus clases (A, B, C, D y E), la notación decimal y binaria, la "
            "cabecera IPv4 (IHL, ToS, identificación, offset, checksum, protocolo) y la "
            "fragmentación, la MTU y el MSS."
        ),
        patrones=(
            r"\bipv4\b",
            r"direcciones? ip\b",
            r"primer octeto",
            r"\boctetos?\b",
            r"cabecera ip",
            r"\bihl\b",
            r"\btos\b",
            r"total length",
            r"suma de verificacion",
            r"\bchecksum\b",
            r"campo (tos|ihl|identificacion|offset|desplazamiento)",
            r"fragmentacion|fragmentos?",
            # «Respecto al campo Fragment offset»: el enunciado nombra el campo en inglés y sin la
            # palabra «fragmentación», y sin este patrón la pregunta se quedaba sin materia.
            r"fragment offset",
            r"\bmtu\b|\bmss\b",
            # «¿A qué clase pertenece la red 172.17.8.0/21?»: el enunciado nombra la clase y no la
            # dirección, así que sin este patrón la pregunta se quedaba sin materia.
            r"\bclase\b",
            r"bits? mas significativos",
            # «172 en binario es 10101100…»: la conversión de una dirección a binario es de la
            # dirección, no del cálculo de subredes.
            r"en binario",
            r"\bip\b",
        ),
        prioridad=50,
    ),
    Materia(
        key="otros-protocolos",
        epigraph_code="IV.7.2",
        title="Otros protocolos",
        resumen=(
            "Los protocolos TCP/IP que aparecen en las preguntas del tema y no son de las materias "
            "anteriores: NTP (hora), IPP (impresión), RSVP (reservas), Kerberos y RADIUS "
            "(autenticación), CoAP (dispositivos limitados) y los que se confunden con ellos. "
            "IPX/SPX y NetBEUI **no son de la familia TCP/IP**: se nombran en el apartado de la "
            "arquitectura TCP/IP, y solo al comparar familias de protocolos."
        ),
        patrones=(
            r"\bntp\b",
            r"\bipp\b",
            r"\brsvp\b",
            r"\bkerberos\b",
            r"\bradius\b",
            r"\bcoap\b",
            r"protocolo de tiempo|sincronizacion de tiempo",
            r"\bwhois\b",
            r"\bx11\b",
            r"\bsdp\b",
            r"\bsap\b",
            r"\bcmip\b",
            r"\blpd\b",
            r"\bgopher\b",
            r"\bsntp\b",
        ),
        prioridad=45,
    ),
)

#: El orden en que se **enseña** el índice de IV.7: el del temario, que es el del propietario. Las
#: materias se declaran agrupadas por epígrafe para poder leerlas; este es el orden del índice, y es
#: una decisión aparte del orden de reparto (`prioridad`), que mira primero lo particular.
_ORDEN_IV7 = (
    "tcpip-arquitectura",
    "osi-que-es",
    "osi-capas",
    "osi-unidades",
    "osi-dispositivos",
    "conceptos-del-modelo",
    "direccionamiento-ipv4",
    "subredes",
    "direcciones-especiales",
    "ipv6",
    "arp",
    "icmp",
    "encaminamiento",
    "tcp",
    "udp",
    "puertos",
    "dns",
    "dhcp",
    "web",
    "correo",
    "ficheros",
    "acceso-remoto",
    "directorio-y-gestion",
    "herramientas",
    "otros-protocolos",
)


def _en_orden_de_estudio(materias: Sequence[Materia], orden: Sequence[str]) -> tuple[Materia, ...]:
    """Las materias en el orden del índice. Falla si el orden no cubre el catálogo entero.

    Un orden escrito a mano se desincroniza en cuanto alguien añade una materia: mejor que falle al
    cargar que quedarse una materia fuera del índice sin que nadie lo vea.
    """
    por_clave = {materia.key: materia for materia in materias}
    if set(orden) != set(por_clave):
        faltan = sorted(set(por_clave) - set(orden))
        sobran = sorted(set(orden) - set(por_clave))
        raise ValueError(
            f"el orden del índice no cuadra con el catálogo (faltan {faltan}, sobran {sobran})"
        )
    return tuple(por_clave[clave] for clave in orden)


#: Los catálogos definidos. Un tema sin catálogo no tiene índice: se dice, no se inventa.
_CATALOGOS: dict[str, tuple[Materia, ...]] = {
    "IV.7": _en_orden_de_estudio(_MATERIAS_IV7, _ORDEN_IV7),
}


def catalogo(topic_code: str) -> tuple[Materia, ...] | None:
    """El catálogo de materias de un tema, o `None` si todavía no está definido."""
    return _CATALOGOS.get(topic_code)


__all__ = [
    "PRIORIDAD_POR_DEFECTO",
    "UMBRAL_EQUIVALENCIA",
    "IndiceDelTema",
    "Materia",
    "RepartoMateria",
    "catalogo",
    "deduplicar",
    "etiquetas",
    "grupos_equivalentes",
    "indice_de",
    "materia_de",
    "plan_de",
    "repartir_grupos",
    "repartir_hechos",
    "validar_catalogo",
]
