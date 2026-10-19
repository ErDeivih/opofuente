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

1. **cada hecho va al apartado de lo que afirma**, y cada pregunta a la materia que menciona antes
   (y, a igualdad, la de `prioridad` más baja). Un hecho sobre la cabecera de IPv6 es de IPv6
   **aunque salga de una pregunta sobre UDP**: es lo que impide que el apartado de UDP hable de la
   cabecera de IPv6, de ARP y de ICMP. Y como un hecho puede salir de varias preguntas (y una
   pregunta tener sus hechos en varios apartados), el ancla pregunta→apuntes admite **varios**
   apartados. Se mira primero entre las materias del epígrafe del hecho y, si en el suyo no casa con
   ninguna, en el catálogo entero: hay hechos a los que el modelo puso el epígrafe que no era (9 en
   IV.7), y su contenido manda. Esos se cuentan y se dicen;
2. **el reparto mira primero lo particular**: un hecho que habla de DNS *y* del puerto 53 es un
   hecho de DNS, no de la tabla de puertos. Por eso cada materia tiene su `prioridad` de reparto,
   aparte del orden en que se enseña el índice (y por eso se miran antes los protocolos que la tabla
   de puertos, aunque la tabla se enseñe antes);
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

#: Tope de hechos por apartado del §2.2.3: un apartado que pase de aquí se parte en trozos de la
#: misma materia. No es un tope de comodidad: el texto de un apartado viaja entero en la llamada que
#: lo redacta y en la que lo comprueba, y un apartado de cuatrocientos hechos no cabe en el encargo.
MAX_HECHOS_POR_APARTADO = 150

#: Los códigos de hallazgo de la revisión de un índice. Vocabulario cerrado: el informe los cuenta y
#: la prueba los usa.
APARTADO_MUY_GRANDE = "apartado_muy_grande"
TITULO_REPETIDO = "titulo_repetido"

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
    #: Patrones que **solo deciden si ninguna materia tiene uno propio**. Son las palabras que
    #: aparecen hablando de cualquier cosa del tema (`datagrama`, `IP` suelta): si contaran igual
    #: que las demás, «En la cabecera del datagrama IPv4, el campo Fragment Offset…» acabaría en
    #: UDP —que es de lo que se quejó el propietario— por mencionar «datagrama» antes que «IPv4».
    #: Una materia tiene que tener al menos un patrón propio; los débiles son un segundo intento.
    patrones_debiles: tuple[str, ...] = ()
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

    @property
    def firmas_de_sus_grupos(self) -> frozenset[str]:
        """Las firmas de las preguntas que el índice sitúa **en este apartado**."""
        return frozenset(grupo.signature for grupo in self.grupos)

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
class HallazgoDelIndice:
    """Un defecto del índice, con su cuenta y dónde está, para poder ir a arreglarlo."""

    codigo: str
    cuenta: int
    detalle: str
    donde: tuple[str, ...] = ()

    def line(self) -> str:
        sitios = "" if not self.donde else f" · en {', '.join(self.donde[:5])}"
        if len(self.donde) > 5:
            sitios += f" y {len(self.donde) - 5} más"
        return f"{self.detalle}{sitios}"


@dataclass(frozen=True, slots=True)
class RevisionIndice:
    """Lo que se comprueba de un índice **antes** de redactar con él (§2.2.3).

    Tres comprobaciones, y la tercera se cuenta aparte a propósito:

    1. **ningún apartado con más de `MAX_HECHOS_POR_APARTADO` hechos**: se parte y deja de ser un
       hallazgo (`plan_de` lo hace);
    2. **ningún título repetido**: dos apartados con el mismo nombre son el mismo apartado dos
    veces;
    3. **cada hecho en un apartado**: lo que no casa con ninguna materia del catálogo es una
    pregunta
       mal situada, y **no** se recoge en un cajón. Se cuenta aquí y, en la corrida, va a la bandeja
       del propietario con su motivo. No invalida el índice —el defecto es de la pregunta, no del
       árbol—, pero tiene que estar dicho: por eso vive en su propio campo y no entre los hallazgos.
    """

    apartados: int
    hechos: int
    hechos_sin_materia: int
    grupos_sin_materia: int
    preguntas_sin_materia: int
    hallazgos: tuple[HallazgoDelIndice, ...] = ()

    @property
    def pasa(self) -> bool:
        """¿El árbol está bien formado? Lo que no cabe en él se cuenta aparte."""
        return not self.hallazgos

    def lines(self) -> tuple[str, ...]:
        cabecera = (
            f"    revision del indice: {'PASA' if self.pasa else 'NO PASA'} · "
            f"{self.apartados} apartado(s) · {self.hechos} hecho(s) · "
            f"{self.grupos_sin_materia} grupo(s) y {self.hechos_sin_materia} hecho(s) sin materia"
        )
        lineas = [cabecera, *(f"      · {hallazgo.line()}" for hallazgo in self.hallazgos)]
        if self.grupos_sin_materia:
            lineas.append(
                f"      · {self.preguntas_sin_materia} pregunta(s) no las situa ninguna materia "
                "del indice y NO hay cajon para ellas: van a la bandeja del propietario"
            )
        return tuple(lineas)


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
    #: Hechos que **no nombran ninguna materia** del tema y cuya pregunta sí tiene apartado propio:
    #: son exactamente los que la red de seguridad sentaba en el apartado de su pregunta, y hoy
    #: van a la bandeja del propietario con el motivo de su pregunta. Se cuentan porque son la
    #: medida del arreglo y tienen que poder revisarse. **No se sientan en ningún apartado.**
    hechos_de_su_pregunta: int = 0
    #: Grupos cuyo **enunciado** no reconocía ninguna materia y se han colocado por el texto de sus
    #: hechos (la materia que reconocen más de sus hechos). Es lo que resuelve las preguntas cortas
    #: («Una de las siguientes afirmaciones es falsa»), que no dicen de qué hablan pero cuyos hechos
    #: sí. Se cuentan porque es una decisión de reparto y tiene que poder revisarse.
    grupos_por_sus_hechos: int = 0

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
        if self.hechos_de_su_pregunta:
            lineas.append(
                f"    {self.hechos_de_su_pregunta} hecho(s) no nombran ninguna materia del tema y "
                "su pregunta sí tiene apartado propio: la red de seguridad los sentaba ahí y hoy "
                "van a la bandeja con el motivo de su pregunta (no se pierden)"
            )
        if self.grupos_por_sus_hechos:
            lineas.append(
                f"    {self.grupos_por_sus_hechos} grupo(s) de preguntas no dicen de qué hablan "
                "por su enunciado y se han situado por el texto de sus hechos"
            )
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
        """Las firmas de pregunta con **algún hecho sin apartado**.

        Es la prueba del §2.1.1, y es distinta de la que había: antes se pedía «ninguna pregunta sin
        hecho en su apartado», y con el reparto por materia una pregunta puede tener sus hechos en
        **varios** apartados (el de UDP y el de IPv6) sin que ninguno sea «el suyo». Lo que no puede
        pasar es que un hecho del tema se quede sin apartado: eso es un hecho huérfano y se cuenta.
        """
        ancladas = {firma for apartado in self.reparto for firma in apartado.firmas_de_grupo}
        faltan: list[str] = []
        for hecho in self.sin_materia:
            for firma in hecho.source_groups:
                if firma not in ancladas and firma not in faltan:
                    faltan.append(firma)
        return tuple(faltan)

    def apartados_de(self, firma: str) -> tuple[str, ...]:
        """Los apartados donde están los hechos de una pregunta, en orden de lectura.

        El ancla pregunta→apuntes admite **varios** apartados: una pregunta sobre UDP puede tener el
        hecho de UDP en su apartado y el de la cabecera IPv6 en el de IPv6, y los dos son suyos. El
        enlace del alumno abre el primero; la comprobación del paso E recibe la unión.
        """
        return tuple(
            apartado.materia.key for apartado in self.reparto if firma in apartado.firmas_de_grupo
        )

    def materia_de_grupo(self, firma: str) -> str | None:
        """La materia en la que el índice sitúa una pregunta, si la sitúa en alguna.

        Es `None` cuando la pregunta no cabe en ninguna materia del tema (`grupos_sin_materia`): no
        tiene apartado propio, y ninguno de los apartados del tema es el suyo.
        """
        for apartado in self.reparto:
            if firma in apartado.firmas_de_sus_grupos:
                return apartado.materia.key
        return None

    def apartados_propios_de(self, firma: str) -> tuple[str, ...]:
        """Los apartados que son **suyos**: los de sus hechos y, si no tiene ninguno colocado, el de
        la materia en la que el índice la sitúa.

        Existe porque la puerta de cobertura decía **cuántas** respuestas estaban contestadas y no
        **por quién**: un ancla en un apartado que no es el de la pregunta contaba como cobertura
        del tema. Aquí está la lista de las que sí lo son; lo que no aparezca en ella es un apartado
        ajeno, y una comprobación anclada ahí **no cuenta como cobertura** de este tema.

        La segunda mitad importa: una pregunta con epígrafe oficial y sin hechos que nombren nada
        —«Señale la afirmación verdadera»— se sitúa por su propio epígrafe, y su apartado es el
        suyo. Antes se anclaba al **primer** apartado de su epígrafe, que puede no serlo.
        """
        propios = self.apartados_de(firma)
        if propios:
            return propios
        materia = self.materia_de_grupo(firma)
        return () if materia is None else (materia,)


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
    """La materia que menciona el texto **antes** (y, a igualdad, la de la prioridad más baja).

    Es lo que hace que «DHCP es un protocolo … el servidor DNS» sea un hecho de DHCP y no de DNS: un
    hecho habla de su materia primero y de las demás después, para compararlas. Sin esa regla,
    cualquier mención de un distractor se llevaría el hecho.

    Y se hace **en dos pasadas**: primero los patrones propios de cada materia y, solo si ninguno
    casa, los débiles. Es la otra mitad de lo mismo: «datagrama» y una «IP» suelta aparecen hablando
    de media asignatura, así que no pueden ganarle a «IPv4» o a «127.0.0.1», que son de una materia
    concreta y de una sola. Sin las dos pasadas, el apartado de UDP se llevaba la cabecera de IPv4 y
    la dirección de loopback por mencionar «datagrama» antes.

    *(El 17-oct-2026 se probó a juntar los patrones de cada materia en una sola expresión —un
    `re.search` por materia en vez de uno por patrón—: medido sobre la copia con IV.7 e I.4, la
    medida pasó de 1,42 a 1,42 s y de 2,48 a 1,88 s, o sea entre 1,0 y 1,3 veces. El índice se va
    en otras cosas —agrupar y deduplicar los hechos—, así que no se cambia: no se toca el motor de
    los apuntes por un 0 %.)*
    """
    for propios in (True, False):
        mejor: tuple[int, int, Materia] | None = None
        for materia in sorted(candidatas, key=lambda materia: materia.prioridad):
            patrones = materia.patrones if propios else materia.patrones_debiles
            if not patrones:
                continue
            posiciones = [
                casado.start()
                for patron in patrones
                if (casado := re.search(patron, limpio)) is not None
            ]
            if not posiciones:
                continue
            candidato = (min(posiciones), materia.prioridad, materia)
            if mejor is None or candidato[:2] < mejor[:2]:
                mejor = candidato
        if mejor is not None:
            return mejor[2]
    return None


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


def materia_nombrada_de(
    texto: str, epigraph_code: str | None, materias: Sequence[Materia]
) -> Materia | None:
    """La materia que el texto **nombra**, o `None` si no nombra ninguna.

    Es `materia_de` con una diferencia que decide todo el reparto: **el cajón no cuenta**. Un cajón
    no tiene patrones —no reconoce nada—, así que «cae en el cajón» quiere decir, literalmente, que
    el texto no ha nombrado ninguna materia. Decir que ahí ha reconocido algo es lo que sentaba
    material de otro tema dentro de un apartado: el estándar ANSI/TIA-942 del CPD de I.3 acabó en el
    cajón `i-3-1-otros` porque el modelo le puso el epígrafe I.3.1 a sus hechos y el cajón recoge
    todo lo de su epígrafe.

    El cajón sigue existiendo para las **preguntas** —una pregunta con epígrafe oficial y sin sujeto
    es de ese epígrafe, y su apartado es el de sus otras cuestiones—, pero para un **hecho** manda
    lo que el hecho dice: si no nombra nada, no es de ninguna materia del tema.
    """
    encontrada = materia_de(texto, epigraph_code, materias)
    return None if encontrada is not None and encontrada.es_cajon else encontrada


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
) -> tuple[dict[str, list[Hecho]], list[Hecho], list[Hecho]]:
    """Los hechos de cada materia, por su clave, y los que no son de ninguna.

    Manda **el texto del hecho**: cada hecho va al apartado de lo que afirma. Un hecho sobre la
    cabecera de IPv6 va a IPv6 aunque venga de una pregunta sobre UDP, y esa es toda la diferencia
    con el reparto anterior —que iba por la pregunta de la que sale—, que metía en el apartado de
    UDP la cabecera de IPv6, la fragmentación, 127.0.0.1, ARP del router e ICMP frente a SMTP.

    **Un hecho que no nombra ninguna materia del tema no se sienta en ningún apartado.** La red de
    seguridad que había —caerlo al apartado de la pregunta de la que sale, para no perderlo— es
    exactamente la puerta por la que el material ajeno se sentó dentro de un tema: sitúa el hecho
    por **de dónde vino la pregunta**, no por lo que el hecho dice, y no hay forma de que eso sea
    suyo. El hecho **no se pierde**: va a `sin_materia` con su texto, se cuenta, se enseña en el
    índice y su pregunta va a la bandeja del propietario con su motivo
    (`SIN_MATERIA_EN_EL_INDICE`). Lo que no hace es sostener un apartado del que no es ni anclar
    respuestas que no contesta.

    Un hecho sin materia de su pregunta se cuenta aparte (`hechos_de_su_pregunta`) porque es la
    medida del arreglo: son los que la red sentaba dentro del tema y hoy van a la bandeja.

    Un hecho cuyas preguntas van a materias distintas va a la materia que **nombra**; sus preguntas
    siguen ancladas donde sus otros hechos las pongan, y el ancla pregunta→apuntes admite varios
    apartados, así que repartir los hechos de una pregunta entre dos apartados no deja a nadie sin
    anclaje.

    Y un hecho cuyas preguntas **no son de este tema** (`grupos_sin_materia`) se va con ellas: si la
    pregunta está mal clasificada y va a la cola, su hecho no puede quedarse aquí a sostener un
    apartado del que ya no es. Es lo que pidió el propietario: «sus datos se van con ellas».
    """
    por_clave: dict[str, list[Hecho]] = {materia.key: [] for materia in materias}
    por_grupo = materia_por_grupo or {}
    ajenas = set(grupos_sin_materia)
    sin_materia: list[Hecho] = []
    por_su_pregunta: list[Hecho] = []
    for hecho in hechos:
        if hecho.source_groups and all(firma in ajenas for firma in hecho.source_groups):
            sin_materia.append(hecho)
            continue
        propia = materia_nombrada_de(hecho.text, hecho.epigraph_code, materias)
        if propia is not None:
            por_clave[propia.key].append(hecho)
            continue
        # No nombra ninguna materia: no se sienta. Se cuenta aparte si su pregunta sí tiene
        # apartado propio, que es el caso que la red de seguridad recogía.
        sin_materia.append(hecho)
        if any(firma in por_grupo for firma in hecho.source_groups):
            por_su_pregunta.append(hecho)
    return por_clave, sin_materia, por_su_pregunta


def _materia_por_sus_hechos(hechos: Sequence[Hecho], materias: Sequence[Materia]) -> Materia | None:
    """A qué materia va un texto que no reconoce ninguna, según **lo que dicen sus hechos**.

    Hay preguntas que no dicen de qué hablan: «Una de las siguientes afirmaciones es falsa», «Los
    acuerdos adoptados, para ser válidos», «El Decreto de la disolución contendrá». Su enunciado no
    nombra ni un artículo ni una institución, así que ningún patrón las va a coger —y forzar
    patrones
    para cada muletilla de examen sería escribir un diccionario de comodines, no un índice—. Lo que
    sí
    sabe de qué hablan son **sus hechos**: se escribieron a partir de sus opciones y su clave, y un
    hecho sobre el artículo 127 es de la materia donde se estudia el artículo 127.

    La decisión es la **mayoría** de los hechos del grupo, y a igualdad la materia que va antes en
    el
    catálogo: determinista, para que dos corridas den el mismo índice. Si ningún hecho reconoce
    nada,
    esto devuelve `None` y la pregunta va a la bandeja del propietario —que es lo correcto: si ni el
    enunciado ni los hechos dicen de qué va, no es que el índice esté mal, es que la pregunta
    necesita
    que alguien la mire—.

    **El cajón no vota.** Un hecho que «cae en el cajón» no ha nombrado nada, así que no puede
    decidir la materia de su pregunta: si votara, una pregunta sin sujeto se situaría por el
    epígrafe que el modelo le puso a sus hechos, y por ahí se sentó dentro del tema el material del
    CPD de I.3 (sus dos hechos, con el epígrafe I.3.1 puesto por el modelo, votaron al cajón
    `i-3-1-otros`).
    """
    votos: dict[str, int] = {}
    for hecho in hechos:
        hallada = materia_nombrada_de(hecho.text, hecho.epigraph_code, materias)
        if hallada is not None:
            votos[hallada.key] = votos.get(hallada.key, 0) + 1
    if not votos:
        return None
    orden = {materia.key: posicion for posicion, materia in enumerate(materias)}
    ganadora = min(votos.items(), key=lambda par: (-par[1], orden.get(par[0], len(orden))))[0]
    return next((materia for materia in materias if materia.key == ganadora), None)


def repartir_grupos(
    grupos: Sequence[QuestionGroup],
    materias: Sequence[Materia],
    *,
    hechos_por_grupo: Mapping[str, Sequence[Hecho]] | None = None,
) -> tuple[dict[str, list[QuestionGroup]], list[QuestionGroup], int]:
    """Los grupos de cada materia, por su clave, los que no son de ninguna y cuántos por sus hechos.

    La materia la decide el **enunciado** (es lo que se lee en el índice). Solo cuando el enunciado
    no
    reconoce ninguna se mira lo que dicen los hechos de ese grupo (`_materia_por_sus_hechos`): una
    pregunta corta es de donde vive lo que sus hechos afirman.
    """
    por_clave: dict[str, list[QuestionGroup]] = {materia.key: [] for materia in materias}
    sin_materia: list[QuestionGroup] = []
    por_sus_hechos = 0
    for grupo in grupos:
        epigrafe = grupo.epigraph_code or grupo.representative.epigraph_code
        materia = materia_de(_texto_de_grupo(grupo), epigrafe, materias)
        if materia is None and hechos_por_grupo:
            suyos = hechos_por_grupo.get(grupo.signature, ())
            materia = _materia_por_sus_hechos(suyos, materias) if suyos else None
            if materia is not None:
                por_sus_hechos += 1
        if materia is None:
            sin_materia.append(grupo)
            continue
        por_clave[materia.key].append(grupo)
    return por_clave, sin_materia, por_sus_hechos


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
    por_materia_grupos, grupos_sin_materia, por_sus_hechos = repartir_grupos(
        grupos, materias, hechos_por_grupo=_hechos_por_grupo(hechos)
    )
    materia_por_grupo = {
        grupo.signature: materia.key
        for materia in materias
        for grupo in por_materia_grupos[materia.key]
    }
    por_materia_hechos, sin_materia, por_su_pregunta = repartir_hechos(
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
        hechos_de_su_pregunta=len(por_su_pregunta),
        grupos_por_sus_hechos=por_sus_hechos,
    )


def _hechos_por_grupo(hechos: Sequence[Hecho]) -> dict[str, list[Hecho]]:
    """Los hechos indexados por el grupo de preguntas del que salen.

    Es lo que permite decidir de qué habla una pregunta que no lo dice: sus hechos sí lo dicen. Un
    hecho que sale de varias preguntas aparece en todas, que es lo correcto: sostiene a las tres.
    """
    indice: dict[str, list[Hecho]] = {}
    for hecho in hechos:
        for firma in hecho.source_groups:
            indice.setdefault(firma, []).append(hecho)
    return indice


def revisar_indice(
    indice: IndiceDelTema,
    planes: Sequence[NoteSection] | None = None,
    *,
    max_hechos_por_apartado: int = MAX_HECHOS_POR_APARTADO,
) -> RevisionIndice:
    """Las comprobaciones del índice del §2.2.3, antes de redactar con él.

    Se miden sobre el **plan de redacción** —lo que se va a escribir, ya partido— y no sobre el
    catálogo: un apartado de trescientos hechos no es un defecto si el plan lo parte en dos, y
    medirlo antes de partir daría por roto un árbol que está bien. Si no se le pasa el plan, lo
    calcula él mismo con el mismo tope, para que medir y redactar no puedan discrepar.

    Las tres cosas que mira están en el documento del objetivo: cada hecho en un apartado, ningún
    apartado por encima del tope y ningún título repetido.
    """
    apartados = (
        tuple(planes)
        if planes is not None
        else plan_de(indice, max_hechos_por_apartado=max_hechos_por_apartado)
    )
    hallazgos: list[HallazgoDelIndice] = []
    grandes = [apartado for apartado in apartados if len(apartado.facts) > max_hechos_por_apartado]
    if grandes:
        hallazgos.append(
            HallazgoDelIndice(
                APARTADO_MUY_GRANDE,
                len(grandes),
                f"{len(grandes)} apartado(s) con más de {max_hechos_por_apartado} hechos sin "
                "partir: no caben en una llamada ni para redactarlos ni para comprobarlos",
                tuple(f"{a.key}: {len(a.facts)}" for a in grandes),
            )
        )
    titulos: dict[str, list[str]] = {}
    for apartado in apartados:
        titulos.setdefault(apartado.title, []).append(apartado.key)
    repetidos = {titulo: claves for titulo, claves in titulos.items() if len(claves) > 1}
    if repetidos:
        hallazgos.append(
            HallazgoDelIndice(
                TITULO_REPETIDO,
                len(repetidos),
                f"{len(repetidos)} título(s) repetido(s) entre apartados del índice",
                tuple(f"«{titulo}» en {', '.join(claves)}" for titulo, claves in repetidos.items()),
            )
        )
    preguntas = sum(len(grupo.questions) for grupo in indice.grupos_sin_materia)
    return RevisionIndice(
        apartados=len(apartados),
        hechos=sum(len(apartado.facts) for apartado in apartados),
        hechos_sin_materia=len(indice.sin_materia),
        grupos_sin_materia=len(indice.grupos_sin_materia),
        preguntas_sin_materia=preguntas,
        hallazgos=tuple(hallazgos),
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
            # «¿Qué protocolo permite reportar al origen, errores en el procesamiento o envío de
            # datagramas IP?»: es ICMP sin nombrarlo, y sin estos patrones el hecho acababa en UDP
            # por decir «datagramas».
            r"reportar.*errores",
            r"informar.*errores",
            r"notificacion de errores",
            r"errores en el (procesamiento|envio)",
            r"mensajes? de (control|error)",
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
            # «IP es un protocolo **no** orientado a conexión» también trae las palabras: TCP solo
            # se queda con las que no llevan el «no» delante.
            r"(?<!no )orientado a conexion",
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
            # «…se observan pequeños cortes intermitentes en el audio. El sistema no retransmite los
            # paquetes perdidos»: el enunciado describe UDP (latencia antes que fiabilidad) sin
            # nombrarlo.
            r"no retransmit",
            r"paquetes perdidos",
            r"baja latencia",
            r"tiempo real",
            r"fiabilidad total",
        ),
        # `datagrama` y «no orientado a conexión» no son de UDP: el primero está en la cabecera de
        # IPv4, en la de IPv6 y en la definición de la propia palabra, y el segundo es también IP
        # («IP es un protocolo no orientado a conexión y de mejor esfuerzo»). Deciden **solo si
        # ninguna materia concreta lo hace**: así la pregunta «Se denomina “datagrama” al paquete de
        # datos en la capa de:» sigue cayendo aquí —es de UDP—, pero los hechos de IP y de la
        # cabecera de IPv4 ya no.
        patrones_debiles=(r"\bdatagramas?\b", r"no orientado a conexion"),
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
            # «El protocolo IP es un protocolo no orientado a conexión y de mejor esfuerzo»: es del
            # protocolo de red, y sin estos dos el hecho se lo llevaba TCP por decir «conexión».
            r"protocolo ip\b",
            r"^ip\b",
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
        ),
        # Una «IP» suelta aparece en media asignatura (ICMP, ARP, UDP…): decide solo si ninguna otra
        # materia tiene un patrón propio en el texto, y así no se lleva los hechos de los demás.
        patrones_debiles=(r"\bip\b",),
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
#:
#: I.6 es un tema **por materias** y no por la estructura de una norma: no hay una sola ley detrás
#: (la LSSI, la propiedad intelectual del software, la Administración electrónica, la Ley 59/2003,
#: el Reglamento europeo eIDAS, la Ley 6/2020, el DNIe y los planes de agenda digital), así que cada
#: bloque normativo tiene su materia y dentro de ella se sigue la estructura de esa ley.
#:
#: I.1 **sí** es normativo y su índice es la estructura de la Constitución: el Título Preliminar,
#: los capítulos del Título I, la garantía y la suspensión (Título I, arts. 53 a 55) y la Corona
#: (Título II); los órganos que la Constitución crea (Cortes, Gobierno, Poder Judicial, Tribunal
#: Constitucional, organización territorial y economía) viven en `I.1.1`, que es el epígrafe de la
#: Constitución entera, porque no tienen epígrafe propio en el temario.
#:
#: Los catálogos de otros temas se importan **aquí abajo** y no arriba: cada uno dice sus materias
#: con la clase `Materia` de este módulo, así que importarlo antes de que esté definida sería un
#: ciclo.
from opofuente.domain.catalogo_i_1 import MATERIAS as MATERIAS_I1  # noqa: E402
from opofuente.domain.catalogo_i_1 import ORDEN as ORDEN_I1  # noqa: E402
from opofuente.domain.catalogo_i_2 import MATERIAS as MATERIAS_I2  # noqa: E402
from opofuente.domain.catalogo_i_2 import ORDEN as ORDEN_I2  # noqa: E402
from opofuente.domain.catalogo_i_3 import MATERIAS as MATERIAS_I3  # noqa: E402
from opofuente.domain.catalogo_i_3 import ORDEN as ORDEN_I3  # noqa: E402
from opofuente.domain.catalogo_i_4 import MATERIAS as MATERIAS_I4  # noqa: E402
from opofuente.domain.catalogo_i_4 import ORDEN as ORDEN_I4  # noqa: E402
from opofuente.domain.catalogo_i_5 import MATERIAS as MATERIAS_I5  # noqa: E402
from opofuente.domain.catalogo_i_5 import ORDEN as ORDEN_I5  # noqa: E402
from opofuente.domain.catalogo_i_6 import MATERIAS as MATERIAS_I6  # noqa: E402
from opofuente.domain.catalogo_i_6 import ORDEN as ORDEN_I6  # noqa: E402
from opofuente.domain.catalogo_i_7 import MATERIAS as MATERIAS_I7  # noqa: E402
from opofuente.domain.catalogo_i_7 import ORDEN as ORDEN_I7  # noqa: E402
from opofuente.domain.catalogo_i_8 import MATERIAS as MATERIAS_I8  # noqa: E402
from opofuente.domain.catalogo_i_8 import ORDEN as ORDEN_I8  # noqa: E402
from opofuente.domain.catalogo_ii_1 import MATERIAS as MATERIAS_II1  # noqa: E402
from opofuente.domain.catalogo_ii_1 import ORDEN as ORDEN_II1  # noqa: E402
from opofuente.domain.catalogo_ii_2 import MATERIAS as MATERIAS_II2  # noqa: E402
from opofuente.domain.catalogo_ii_2 import ORDEN as ORDEN_II2  # noqa: E402
from opofuente.domain.catalogo_ii_3 import MATERIAS as MATERIAS_II3  # noqa: E402
from opofuente.domain.catalogo_ii_3 import ORDEN as ORDEN_II3  # noqa: E402
from opofuente.domain.catalogo_ii_4 import MATERIAS as MATERIAS_II4  # noqa: E402
from opofuente.domain.catalogo_ii_4 import ORDEN as ORDEN_II4  # noqa: E402
from opofuente.domain.catalogo_ii_5 import MATERIAS as MATERIAS_II5  # noqa: E402
from opofuente.domain.catalogo_ii_5 import ORDEN as ORDEN_II5  # noqa: E402
from opofuente.domain.catalogo_iii_1 import MATERIAS as MATERIAS_III1  # noqa: E402
from opofuente.domain.catalogo_iii_1 import ORDEN as ORDEN_III1  # noqa: E402
from opofuente.domain.catalogo_iii_3 import MATERIAS as MATERIAS_III3  # noqa: E402
from opofuente.domain.catalogo_iii_3 import ORDEN as ORDEN_III3  # noqa: E402
from opofuente.domain.catalogo_iii_4 import MATERIAS as MATERIAS_III4  # noqa: E402
from opofuente.domain.catalogo_iii_4 import ORDEN as ORDEN_III4  # noqa: E402
from opofuente.domain.catalogo_iii_5 import MATERIAS as MATERIAS_III5  # noqa: E402
from opofuente.domain.catalogo_iii_5 import ORDEN as ORDEN_III5  # noqa: E402
from opofuente.domain.catalogo_iii_7 import MATERIAS as MATERIAS_III7  # noqa: E402
from opofuente.domain.catalogo_iii_7 import ORDEN as ORDEN_III7  # noqa: E402
from opofuente.domain.catalogo_iii_8 import MATERIAS as MATERIAS_III8  # noqa: E402
from opofuente.domain.catalogo_iii_8 import ORDEN as ORDEN_III8  # noqa: E402
from opofuente.domain.catalogo_iii_9 import MATERIAS as MATERIAS_III9  # noqa: E402
from opofuente.domain.catalogo_iii_9 import ORDEN as ORDEN_III9  # noqa: E402
from opofuente.domain.catalogo_iv_1 import MATERIAS as MATERIAS_IV1  # noqa: E402
from opofuente.domain.catalogo_iv_1 import ORDEN as ORDEN_IV1  # noqa: E402
from opofuente.domain.catalogo_iv_2 import MATERIAS as MATERIAS_IV2  # noqa: E402
from opofuente.domain.catalogo_iv_2 import ORDEN as ORDEN_IV2  # noqa: E402
from opofuente.domain.catalogo_iv_4 import MATERIAS as MATERIAS_IV4  # noqa: E402
from opofuente.domain.catalogo_iv_4 import ORDEN as ORDEN_IV4  # noqa: E402
from opofuente.domain.catalogo_iv_5 import MATERIAS as MATERIAS_IV5  # noqa: E402
from opofuente.domain.catalogo_iv_5 import ORDEN as ORDEN_IV5  # noqa: E402
from opofuente.domain.catalogo_iv_6 import MATERIAS as MATERIAS_IV6  # noqa: E402
from opofuente.domain.catalogo_iv_6 import ORDEN as ORDEN_IV6  # noqa: E402
from opofuente.domain.catalogo_iv_8 import MATERIAS as MATERIAS_IV8  # noqa: E402
from opofuente.domain.catalogo_iv_8 import ORDEN as ORDEN_IV8  # noqa: E402
from opofuente.domain.catalogo_iv_9 import MATERIAS as MATERIAS_IV9  # noqa: E402
from opofuente.domain.catalogo_iv_9 import ORDEN as ORDEN_IV9  # noqa: E402
from opofuente.domain.catalogo_iv_10 import MATERIAS as MATERIAS_IV10  # noqa: E402
from opofuente.domain.catalogo_iv_10 import ORDEN as ORDEN_IV10  # noqa: E402

_CATALOGOS: dict[str, tuple[Materia, ...]] = {
    "IV.7": _en_orden_de_estudio(_MATERIAS_IV7, _ORDEN_IV7),
    "IV.1": _en_orden_de_estudio(MATERIAS_IV1, ORDEN_IV1),
    "IV.2": _en_orden_de_estudio(MATERIAS_IV2, ORDEN_IV2),
    "II.4": _en_orden_de_estudio(MATERIAS_II4, ORDEN_II4),
    "I.6": _en_orden_de_estudio(MATERIAS_I6, ORDEN_I6),
    "I.7": _en_orden_de_estudio(MATERIAS_I7, ORDEN_I7),
    "I.1": _en_orden_de_estudio(MATERIAS_I1, ORDEN_I1),
    "III.9": _en_orden_de_estudio(MATERIAS_III9, ORDEN_III9),
    "III.1": _en_orden_de_estudio(MATERIAS_III1, ORDEN_III1),
    "III.5": _en_orden_de_estudio(MATERIAS_III5, ORDEN_III5),
    "III.7": _en_orden_de_estudio(MATERIAS_III7, ORDEN_III7),
    "I.2": _en_orden_de_estudio(MATERIAS_I2, ORDEN_I2),
    "I.4": _en_orden_de_estudio(MATERIAS_I4, ORDEN_I4),
    "I.5": _en_orden_de_estudio(MATERIAS_I5, ORDEN_I5),
    "I.8": _en_orden_de_estudio(MATERIAS_I8, ORDEN_I8),
    "IV.5": _en_orden_de_estudio(MATERIAS_IV5, ORDEN_IV5),
    "IV.6": _en_orden_de_estudio(MATERIAS_IV6, ORDEN_IV6),
    "IV.8": _en_orden_de_estudio(MATERIAS_IV8, ORDEN_IV8),
    "IV.9": _en_orden_de_estudio(MATERIAS_IV9, ORDEN_IV9),
    "I.3": _en_orden_de_estudio(MATERIAS_I3, ORDEN_I3),
    "II.1": _en_orden_de_estudio(MATERIAS_II1, ORDEN_II1),
    "II.3": _en_orden_de_estudio(MATERIAS_II3, ORDEN_II3),
    "III.3": _en_orden_de_estudio(MATERIAS_III3, ORDEN_III3),
    "IV.10": _en_orden_de_estudio(MATERIAS_IV10, ORDEN_IV10),
    "II.2": _en_orden_de_estudio(MATERIAS_II2, ORDEN_II2),
    "II.5": _en_orden_de_estudio(MATERIAS_II5, ORDEN_II5),
    "III.8": _en_orden_de_estudio(MATERIAS_III8, ORDEN_III8),
    "IV.4": _en_orden_de_estudio(MATERIAS_IV4, ORDEN_IV4),
    "III.4": _en_orden_de_estudio(MATERIAS_III4, ORDEN_III4),
}


def catalogo(topic_code: str) -> tuple[Materia, ...] | None:
    """El catálogo de materias de un tema, o `None` si todavía no está definido."""
    return _CATALOGOS.get(topic_code)


def es_la_tabla_de_puertos(topic_code: str, clave: str) -> bool:
    """¿Este apartado es la tabla única del tema? Lo dice el catálogo, no el título del apartado.

    Es la marca `tabla_unica` del índice: un tema puede tener apartados con tablas, pero solo uno es
    «la tabla de puertos» y solo ese lleva las instrucciones de familias y la limpieza de sus notas.
    """
    materias = catalogo(topic_code)
    return any(materia.key == clave and materia.tabla_unica for materia in (materias or ()))


__all__ = [
    "APARTADO_MUY_GRANDE",
    "MAX_HECHOS_POR_APARTADO",
    "PRIORIDAD_POR_DEFECTO",
    "TITULO_REPETIDO",
    "UMBRAL_EQUIVALENCIA",
    "HallazgoDelIndice",
    "IndiceDelTema",
    "Materia",
    "RepartoMateria",
    "RevisionIndice",
    "catalogo",
    "deduplicar",
    "etiquetas",
    "grupos_equivalentes",
    "indice_de",
    "materia_de",
    "materia_nombrada_de",
    "plan_de",
    "repartir_grupos",
    "repartir_hechos",
    "revisar_indice",
    "validar_catalogo",
]
