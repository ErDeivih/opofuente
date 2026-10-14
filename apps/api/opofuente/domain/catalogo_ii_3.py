"""El catálogo de materias de II.3 (tipos abstractos y estructuras de datos, organizaciones de
ficheros, algoritmos y formatos de información).

II.3 es un tema **técnico** de fundamentos y su banco lo confirma: de sus 171 grupos de preguntas,
**77 no traen epígrafe** y los cuatro epígrafes oficiales —tipos abstractos y estructuras de datos,
organizaciones de ficheros, algoritmos y formatos de información— son un esqueleto de 43, 17, 23 y
11 grupos. Como en IV.7, IV.9, III.3 y IV.1, el índice va **por asunto** dentro de cada epígrafe y
el
enunciado es el que decide.

Diez apartados, en el orden en que se estudia:

- los **tipos abstractos de datos** en uno (II.3.1): qué es un tipo abstracto y cuáles no lo son, la
  pila con su LIFO, la cola con su FIFO, la lista y la lista enlazada, el array, el registro, el
  conjunto no ordenado, la tabla de dispersión con sus colisiones y el acceso directo frente al
  secuencial;
- los **árboles** aparte (II.3.1), que es el bloque más grande del epígrafe: el árbol binario y su
  número máximo de nodos por nivel, los recorridos en preorden, inorden y postorden, la raíz, los
  niveles y el grado, y los árboles de búsqueda equilibrados (AVL), perfectos y llenos;
- los **grafos y las métricas** (II.3.1): vértices y aristas, el grafo conexo sin ciclos, el grafo
  regular, el camino que une dos vértices, los grados y la métrica que mide el nivel de agrupamiento
  de los nodos;
- la **organización de los ficheros** (II.3.2): la organización secuencial, la secuencial indexada y
  la directa, el índice denso y el de agrupamiento, los ficheros dispersos y sus colisiones, el
  enlace al registro siguiente y los métodos de acceso a un archivo;
- los **sistemas de archivos** (II.3.2): FAT 16 y su tamaño máximo, el sistema que se diseñó para
  las memorias SSD como sucesor de HFS+, y qué sistema de ficheros admite un fichero de 6 GB;
- los **algoritmos de ordenación** (II.3.3): la burbuja y el intercambio directo, la selección
  directa, la inserción binaria, el método del pivote, la mezcla directa, los montículos, Shell,
  Radix, Counting, Bucket y Cube sort, con sus complejidades, sus pasadas y su número de
  comparaciones;
- los **algoritmos de búsqueda** (II.3.3): la búsqueda binaria y su número de comparaciones, la
  búsqueda que se vale de una función aritmética, la búsqueda secuencial y la que no cabe en memoria
  y usa ficheros auxiliares;
- los **algoritmos de grafos y de optimización** (II.3.3): Dijkstra, Prim, Kruskal, Bellman-Ford,
  Floyd-Warshall y A*, el árbol recubridor mínimo, el camino más corto y el Minimax;
- el **análisis y la complejidad de los algoritmos** (II.3.3): qué es un algoritmo, qué se llama
  tiempo de ejecución, para qué se analiza la complejidad y qué es un algoritmo de un motor de
  búsqueda;
- los **formatos de fichero y sus extensiones** (II.3.4): el formato abierto de documento y su
  norma, las extensiones y su tipo MIME, JSON, YAML, VRML, el CSV descrito en el RFC 4180, la UDF y
  el fichero gráfico vectorial;
- y la **compresión y la digitalización** (II.3.4): la compresión con y sin pérdida, la codificación
  de Huffman, la digitalización de imágenes y la resolución.

Cinco decisiones de los patrones, dichas donde se leen:

- **las claves de materia del tema anterior no valen aquí.** En III.3 «datos», «estándar» y
  «sentencia» acabaron barriendo grupos de otros temas hacia el apartado equivocado; aquí las
  palabras que salen en todo el tema (`datos`, `estructura`, `fichero`, `algoritmo`, `formato`)
  están en los **débiles** o directamente fuera, y solo deciden cuando ninguna materia ha casado con
  sus patrones propios;
- **la burbuja se pide por sus tres nombres** —`burbuja`, `intercambio directo` y `método del
  intercambio`—, porque el banco usa los tres y son el mismo algoritmo;
- **`O(n)` se pide con la forma en que el banco escribe la complejidad** (`complejidad`, `o(n`,
  `complejidades`), no con una cifra suelta: hay preguntas que dan la complejidad en el enunciado y
  otras que la piden;
- **el CSV y el JSON sí son de este tema** (II.3.4, «Formatos de información y ficheros»), aunque el
  RFC 4180 hable de reglas de comillas y comas: es un formato de fichero y su sitio es este;
- y **lo que es de otro tema no se lava**: el *pharming* y las amenazas al puesto del usuario son de
  **IV.9** y **I.8**, la firma electrónica, el CAdES y el algoritmo de huella de AutoFirma son de
  **I.6** y **IV.5**, SOAP/MTOM y REST son de **IV.3** y **IV.4**, y la taxonomía de Flynn es de
  **II.1**. Van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`).
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Los tipos abstractos de datos: pilas, colas, listas, arrays y tablas de dispersión.
_TIPOS_ABSTRACTOS = (
    r"tipo(s)? abstracto(s)? de datos|\btad\b",
    r"\bpila\b|\blifo\b",
    r"\bcola\b|\bfifo\b",
    r"lista(s)? (enlazada|encadenada|simplemente|doblemente)|\blista\b",
    r"\barray\b|\bvector\b",
    r"\bregistro\b",
    r"\bconjunto\b",
    r"tabla(s)? (hash|de dispersion)|\bdispersion\b|\bcolision(es)?\b|resolucion de colisiones",
    r"acceso (directo|secuencial|aleatorio)",
    r"estructura(s)? de datos",
    r"\bldap\b",
    r"inserciones al final|mismo extremo|mismo nombre y a traves de una posicion",
    r"tipo de datos estructurado|tipo(s)? de datos compuesto|tipo compuesto",
    r"concepto de tipo de datos|que tipo(s)? de datos",
    r"estructura o enfoque",
    r"coleccion no ordenada",
)

#: Los árboles y sus recorridos.
_ARBOLES = (
    r"\barbol(es)?\b",
    r"\bavl\b",
    r"preorden|inorden|postorden|in ?orden|pre ?orden",
    r"\bnodo(s)?\b|\bhoja(s)?\b|\braiz\b",
    r"recorrido(s)? (de|en|del)",
    r"\bbinario de busqueda\b",
    r"subarbol",
)

#: Los grafos.
_GRAFOS = (
    r"\bgrafo(s)?\b|\bvertice(s)?\b|\barista(s)?\b",
    r"conexo sin ciclos|sin ciclos",
    r"arbol recubridor",
    r"camino mas corto|\bcamino\b",
    r"grado de (un|el) (arbol|grafo)|grafo regular|grado 3",
    r"agrupamiento de los nodos|nivel de agrupamiento",
)

#: La organización de los ficheros.
_ORGANIZACION_DE_FICHEROS = (
    r"fichero(s)? (secuencial|indexad|dispers|de acceso|con acceso)",
    r"organizacion (de|del) (los )?fichero",
    r"organizacion secuencial",
    r"indice (de agrupamiento|denso|disperso)|indice denso|indice de agrupamiento",
    r"registro(s)? .*(enlace|siguiente)|enlace al siguiente registro",
    r"metodos? de acceso a un (archivo|fichero)",
    r"tamano de bloque|bloque de \d+",
    r"insertar registros en cualquier posicion",
    r"claves secundarias",
    r"estructura de almacenamiento",
    r"un fichero es un conjunto|en relacion a los ficheros",
)

#: Los sistemas de archivos y sus límites.
_SISTEMAS_DE_ARCHIVOS = (
    r"\bfat ?(16|32)\b|\bntfs\b|\bhfs\b|\bapfs\b|\bext[234]\b|\bexfat\b|\biso ?9660\b",
    r"sistema(s)? de (archivos|ficheros)",
    r"tamano maximo de archivo|podremos almacenar un fichero",
    r"formateado|memorias ssd|sucesor de hfs",
    r"\budf\b",
)

#: Los algoritmos de ordenación y su coste.
_ORDENACION = (
    r"ordenacion|ordenar (un|el|los|una|archivos)",
    r"\bburbuja\b|intercambio directo",
    r"seleccion directa|por seleccion|metodo de seleccion|por el metodo de seleccion",
    r"insercion( binaria)?|por insercion",
    r"\bpivote\b|quicksort|ordenacion rapida",
    r"mezcla directa|mergesort",
    r"monticulos|heapsort",
    r"shell sort|\bshell\b",
    r"radix|\bcounting\b|\bbucket\b|\bbinsort\b|\bcube sort\b",
    r"complejidad(es)?( temporal)?|o\(n",
    r"numero de comparaciones|cuantas pasadas|iteraciones debera|pasadas seria necesario",
    r"tecnicas? de (clasificacion|ordenacion)|clasificacion de datos|cintas auxiliares",
    r"algoritmos? de ordenacion",
)

#: Los algoritmos de búsqueda.
_BUSQUEDA = (
    r"busqueda (binaria|secuencial|dicotomica|hash)",
    r"tecnica de busqueda|algoritmo de busqueda|busca(r)? (un|en|una)",
    r"funcion aritmetica para calcular la posicion",
    r"lista ordenada de partes",
    r"que no caben en memoria|no caben en memoria",
)

#: Los algoritmos de grafos y de optimización.
_ALGORITMOS_DE_GRAFOS = (
    r"\bdijkstra\b|\bprim\b|\bkruskal\b|floyd|bellman|\ba\*",
    r"arbol recubridor minimo|minimax",
    r"algoritmo[s]? (de|para) (la )?(teoria de )?grafos",
    r"teoria de grafos",
)

#: El análisis y la complejidad de los algoritmos.
_ANALISIS = (
    r"complejidad|analizar la complejidad",
    r"tiempo (que tarda|de ejecucion)|tiempo de un algoritmo",
    r"que es un algoritmo|definicion de algoritmo|acerca de los algoritmos|algoritmos es correcta",
    r"algoritmo de un motor de busqueda",
    r"finalidad de analizar",
)

#: Los formatos de fichero y sus extensiones.
_FORMATOS = (
    r"formato(s)? (de archivo|de fichero|abierto|de documentos|de informacion"
    r"|de imagen|de compresion|de datos)",
    r"\bodf\b|opendocument|\booxml\b|\bopenoffice\b|libreoffice",
    r"extension(es)? (de|que|se corresponde|indica)",
    r"\bmime\b|tipo mime",
    r"\bjson\b|\byaml\b|\bvrml\b|\bxml\b",
    r"\bcsv\b|rfc ?4180",
    r"archivo comprimido|\bcomprimido\b|\bzip\b|\brar\b|\b7z\b|\bgzip\b",
    r"formato de (imagen|grafico)|fichero grafico|graficos vectoriales",
    r"\bjpg\b|\bpng\b|\bgif\b|\bsvg\b|\btiff\b|\bbmp\b",
    r"hoja de calculo|documento de texto|documentos abiertos",
)

#: La compresión y la digitalización.
_COMPRESION = (
    r"compresion (con|sin) perdida|tecnica de compresion|metodos? para la compresion",
    r"huffman",
    r"digitalizacion|resolucion de (la )?imagen|bits por pixel|pixeles",
    r"\bjpeg\b|\bmp3\b|\bmp4\b",
)

MATERIAS: tuple[Materia, ...] = (
    # --- II.3.1 Tipos abstractos y Estructuras de datos -----------------------------------------
    Materia(
        key="los-tipos-abstractos-de-datos",
        epigraph_code="II.3.1",
        title="Los tipos abstractos de datos: pilas, colas, listas y tablas de dispersión",
        resumen=(
            "Las estructuras con las que se guarda y se recupera: qué es un tipo abstracto de "
            "datos"
            "y cuáles no lo son, la pila y su LIFO, la cola y su FIFO, la lista y la lista "
            "enlazada, el array, el registro, el conjunto no ordenado, la tabla de dispersión con "
            "sus colisiones y el acceso directo frente al secuencial."
        ),
        patrones=_TIPOS_ABSTRACTOS,
        patrones_debiles=(r"pila", r"estructura"),
        prioridad=30,
    ),
    Materia(
        key="los-arboles-y-sus-recorridos",
        epigraph_code="II.3.1",
        title="Los árboles y sus recorridos",
        resumen=(
            "La estructura jerárquica: el árbol binario y su número máximo de nodos por nivel, los "
            "recorridos en preorden, inorden y postorden, la raíz, los niveles y el grado, y los "
            "árboles de búsqueda equilibrados, perfectos y llenos."
        ),
        patrones=_ARBOLES,
        patrones_debiles=(r"arbol",),
        prioridad=20,
    ),
    Materia(
        key="los-grafos-y-sus-metricas",
        epigraph_code="II.3.1",
        title="Los grafos y sus métricas",
        resumen=(
            "Vértices y aristas: el grafo conexo sin ciclos, el grafo regular de grado tres, el "
            "camino que une dos vértices, las representaciones por conjuntos y la métrica que mide "
            "el nivel de agrupamiento de los nodos."
        ),
        patrones=_GRAFOS,
        patrones_debiles=(r"grafo",),
        prioridad=25,
    ),
    # --- II.3.2 Organizaciones de ficheros ------------------------------------------------------
    Materia(
        key="la-organizacion-de-los-ficheros",
        epigraph_code="II.3.2",
        title="La organización de los ficheros y sus índices",
        resumen=(
            "Cómo se guardan los registros en el soporte: la organización secuencial, la "
            "secuencial"
            "indexada y la directa, el índice denso y el de agrupamiento, los ficheros dispersos y "
            "sus colisiones, el enlace al registro siguiente y los métodos de acceso a un archivo."
        ),
        patrones=_ORGANIZACION_DE_FICHEROS,
        patrones_debiles=(r"registro",),
        prioridad=35,
    ),
    Materia(
        key="los-sistemas-de-archivos",
        epigraph_code="II.3.2",
        title="Los sistemas de archivos y sus límites",
        resumen=(
            "El formato con el que se formatea el soporte: FAT 16 y su tamaño máximo de archivo, "
            "el"
            "sistema diseñado para las memorias SSD como sucesor de HFS+, el sistema de ficheros "
            "que admite un fichero de 6 GB y el estándar UDF de los medios ópticos."
        ),
        patrones=_SISTEMAS_DE_ARCHIVOS,
        patrones_debiles=(r"archivos",),
        prioridad=30,
    ),
    # --- II.3.3 Algoritmos ----------------------------------------------------------------------
    Materia(
        key="los-algoritmos-de-ordenacion",
        epigraph_code="II.3.3",
        title="Los algoritmos de ordenación",
        resumen=(
            "Poner en orden: la burbuja o intercambio directo, la selección directa, la inserción "
            "binaria, el método del pivote, la mezcla directa, los montículos y los algoritmos "
            "Radix, Shell, Counting, Bucket y Cube, con sus complejidades, sus pasadas y su número "
            "de comparaciones."
        ),
        patrones=_ORDENACION,
        patrones_debiles=(r"ordenacion", r"ordenar"),
        prioridad=25,
    ),
    Materia(
        key="los-algoritmos-de-busqueda",
        epigraph_code="II.3.3",
        title="Los algoritmos de búsqueda",
        resumen=(
            "Encontrar un dato: la búsqueda binaria y el número de comparaciones que necesita, la "
            "búsqueda que se vale de una función aritmética para calcular la posición, la búsqueda "
            "secuencial y las clasificaciones que usan ficheros o cintas auxiliares porque el "
            "conjunto no cabe en memoria."
        ),
        patrones=_BUSQUEDA,
        patrones_debiles=(r"busqueda",),
        prioridad=25,
    ),
    Materia(
        key="los-algoritmos-de-grafos-y-de-optimizacion",
        epigraph_code="II.3.3",
        title="Los algoritmos de grafos y de optimización",
        resumen=(
            "Recorrer una red de nodos buscando lo mejor: Dijkstra, Prim, Kruskal, Bellman-Ford, "
            "Floyd-Warshall y A*, el árbol recubridor mínimo de un grafo conexo y ponderado, el "
            "camino más corto y el Minimax."
        ),
        patrones=_ALGORITMOS_DE_GRAFOS,
        patrones_debiles=(r"algoritmo de grafos",),
        prioridad=20,
    ),
    Materia(
        key="el-analisis-y-la-complejidad-de-los-algoritmos",
        epigraph_code="II.3.3",
        title="El análisis y la complejidad de los algoritmos",
        resumen=(
            "Cuánto tarda y cuánto ocupa: qué es un algoritmo y cómo se define, qué se llama "
            "tiempo"
            "de ejecución, para qué se analiza la complejidad y qué es un algoritmo de un motor de "
            "búsqueda."
        ),
        patrones=_ANALISIS,
        patrones_debiles=(r"algoritmo",),
        prioridad=45,
    ),
    # --- II.3.4 Formatos de información y ficheros ----------------------------------------------
    Materia(
        key="los-formatos-de-fichero-y-sus-extensiones",
        epigraph_code="II.3.4",
        title="Los formatos de fichero y sus extensiones",
        resumen=(
            "Con qué extensión y con qué norma: el formato abierto de documento y su estándar, las "
            "extensiones y su tipo MIME, JSON, YAML y VRML, el CSV descrito en el RFC 4180, la UDF "
            "de los medios ópticos y el fichero gráfico vectorial."
        ),
        patrones=_FORMATOS,
        patrones_debiles=(r"extension",),
        prioridad=30,
    ),
    Materia(
        key="la-compresion-y-la-digitalizacion",
        epigraph_code="II.3.4",
        title="La compresión y la digitalización de la información",
        resumen=(
            "Reducir y muestrear: la compresión con pérdida y sin pérdida, la codificación de "
            "Huffman, la digitalización de imágenes con su resolución y sus bits por píxel, y los "
            "formatos que comprimen perdiendo información."
        ),
        patrones=_COMPRESION,
        patrones_debiles=(r"compresion",),
        prioridad=20,
    ),
)

#: El orden del índice: primero las estructuras con las que se guarda el dato —tipos abstractos,
#: árboles y grafos—, después cómo se organiza en el soporte y con qué sistema de archivos, luego
#: los algoritmos —ordenar, buscar, recorrer grafos y analizar el coste— y, al final, los formatos
#: con los que el dato sale del sistema.
ORDEN: tuple[str, ...] = (
    "los-tipos-abstractos-de-datos",
    "los-arboles-y-sus-recorridos",
    "los-grafos-y-sus-metricas",
    "la-organizacion-de-los-ficheros",
    "los-sistemas-de-archivos",
    "los-algoritmos-de-ordenacion",
    "los-algoritmos-de-busqueda",
    "los-algoritmos-de-grafos-y-de-optimizacion",
    "el-analisis-y-la-complejidad-de-los-algoritmos",
    "los-formatos-de-fichero-y-sus-extensiones",
    "la-compresion-y-la-digitalizacion",
)

__all__ = ["MATERIAS", "ORDEN"]
