"""El catálogo de materias de II.1 (informática básica, representación de la información,
arquitectura de ordenadores y componentes internos del puesto).

II.1 es un tema **técnico** y su banco lo confirma: de sus 214 grupos de preguntas, **85 no traen
epígrafe** (el 40 %) y hablan de todo lo que el tema es, mientras que los cinco epígrafes oficiales
del temario —informática básica, representación y comunicación de la información, características y
funciones, arquitectura de ordenadores y componentes internos— son un esqueleto de 6, 41, 1, 51 y 30
grupos. Como en IV.7, IV.5, IV.9, IV.8 y IV.1, el índice va **por asunto** dentro de cada epígrafe,
y
el enunciado es el que decide: sin eso, 85 grupos sin epígrafe se quedarían fuera y el tema no
llegaría nunca al listón.

Catorce apartados, en el orden en que se estudia:

- la **historia de la informática y las generaciones** de ordenadores en uno (II.1.1): el componente
  electrónico de cada generación, la primera computadora electrónica, la ley de Moore y los grandes
  sistemas;
- la **informática básica del puesto**: qué es un interfaz de usuario, qué es un documento y cómo se
  genera un PDF, la ofimática y la diferencia entre un compilador y un intérprete (II.1.1). Son las
  preguntas del tema que no hablan ni de máquinas ni de normas;
- los **sistemas de numeración y las unidades de medida** en uno (II.1.2), que es el bloque más
  grande del banco: binario, octal, hexadecimal y decimal, el complemento a dos, la suma de bits, la
  agrupación de bits y el nibble, y las unidades de capacidad —del bit al saganbyte— con su orden de
  menor a mayor;
- el **álgebra de Boole y las puertas lógicas** aparte (II.1.2): las operaciones básicas, y las
  puertas NAND, NOR, XOR y XNOR con lo que devuelve cada una;
- la **codificación y la teoría de la información** (II.1.2): el código ASCII y sus bits, UTF-8 y su
  normalización, el IEEE 754 y la coma flotante, la codificación de Huffman, la entropía, el bit de
  paridad y la detección de errores;
- los **sistemas de información y el proceso de datos** (II.1.2): los niveles organizativos, las
  partes de un proceso de datos, los datos en bruto y dónde se decide a medio y largo plazo;
- las **características y funciones del sistema informático** (II.1.3), que es el epígrafe de una
  sola pregunta del temario y recoge lo que pregunta por un sistema informático en abstracto —qué lo
  hace «abierto», de qué partes consta— y también las subáreas del área de sistemas;
- las **arquitecturas y los procesadores** (II.1.4): Von Neumann y Harvard, la taxonomía de Flynn y
  sus cuatro categorías, RISC frente a CISC, la segmentación y el solapamiento de instrucciones, el
  superescalar, el multinúcleo y las familias Intel, x86 y ARM;
- la **CPU y sus registros** (II.1.4): la unidad de control y la ALU, el registro de instrucción y
el
  contador de programa, el ciclo de instrucción, la decodificación, el secuenciador, las
  interrupciones —las de hardware y las que produce la propia CPU—, los modos de direccionamiento y
  la potencia medida en FLOPS;
- la **memoria y su jerarquía** (II.1.4): la memoria principal y la caché, la jerarquía y el orden
de
  velocidad, el bus de direcciones y la memoria máxima direccionable, la MMU, el espacio de
  direcciones, el ancho de palabra y el retardo de acceso;
- los **buses y la entrada/salida** (II.1.4): el controlador de E/S y por qué existe, el DMA, el
  programa canal, el multiplexor y el bus del sistema con sus señales de sincronía y control;
- la **placa base y el conjunto de chips** (II.1.5): los puentes norte y sur, los zócalos, PCI
  Express, el factor de forma, los conectores, la pila del reloj y los equipos compactos;
- las **memorias del equipo** (II.1.5): RAM, SRAM, DRAM, ROM, EPROM y EEPROM, la ECC, el refresco de
  la memoria dinámica, la volatilidad, DDR y la memoria persistente;
- y la **BIOS, la UEFI y el arranque** (II.1.5): el programa BIOS y su configuración guardada, el
  firmware, la CMOS, la secuencia de arranque y el diagnóstico de fallos al encender.

Cinco decisiones de los patrones, dichas donde se leen:

- **la palabra que sale en todo el tema no vale como patrón propio.** «memoria», «ordenador»,
  «instrucción», «bits» y «sistema» están en los **débiles** de su materia, que solo deciden cuando
  ninguna otra ha casado. Sin esa regla, el apartado de la memoria y su jerarquía se llevaría media
  asignatura por decir «memoria» en la primera línea —y bloques enteros de la representación de la
  información, que también hablan de bits—;
- **los enunciados que solo dicen «señale la afirmación FALSA» o «indique cuál es verdadera» no se
  sitúan y no se lavan**: no hay en ellos ninguna palabra de la que se pueda decir de qué materia
  hablan, así que van a la bandeja del propietario. Es el precio de no inventar;
- **`\\barm\\b` y `\\bnuc\\b` se aceptan como palabras sueltas** porque en este banco están solas
  —«los procesadores ARM», «los ordenadores NUC»— y no hay otra palabra del tema que se escriba así;
- **la memoria persistente se pide por la frase, no por la marca**: «almacenar los datos de forma
  persistente» es lo único que la distingue de una RAM en el enunciado, y así no se lleva por
  delante
  las preguntas de la BIOS, que también hablan de lo que se guarda;
- y **lo que es de otro tema no se lava**: la virtualización de sistemas operativos, los patrones de
  diseño —el «Bridge» de GoF— y la definición de algoritmo son de II.4, III.4 y II.3, y van a la
  bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`), que es lo que manda el
  índice.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las generaciones de ordenadores y su historia: el bloque propio de II.1.1.
_HISTORIA = (
    r"(primera|segunda|tercera|cuarta|quinta|sexta) generacion",
    r"generacion(es)? (de|del|de los) (los )?ordenador",
    r"componente electronico (fundamental|de la)",
    r"\beniac\b|\bedvac\b|\bunivac\b",
    r"computadora(s)? electronica|primera computadora",
    r"ley de moore|\bmoore\b",
    r"valvulas? de vacio|transistor(es)?\b",
    r"historia de (la )?informatica|evolucion de (la informatica|los ordenadores)",
    r"mainframe|grandes? (sistemas|ordenadores)",
)

#: La informática básica del puesto: el interfaz, los documentos y los programas.
_OFIMATICA = (
    r"interfaz(es)? de usuario",
    r"\bpdf\b",
    r"documento(s)? de texto|procesador(es)? de textos?",
    r"hoja de calculo|\bexcel\b|\bcalc\b",
    r"ofimatic",
    r"compilador(es)?|\binterprete(s)?\b",
    r"lenguaje maquina",
    r"aplicacion(es)? (informatica|de oficina|ofimatica)",
)

#: Los sistemas de numeración, el complemento a dos y las unidades de capacidad.
_NUMERACION = (
    r"complemento a (dos|2|uno|1)",
    r"sistema (binario|octal|hexadecimal|decimal)",
    r"base (binaria|decimal|octal|hexadecimal|\d+)",
    r"numero(s)? (binario|hexadecimal|decimal|octal)",
    r"\bbinario\b|\bbinaria\b|\bhexadecimal\b|\boctal\b|\bdecimal(es)?\b",
    r"suma de \d+",
    r"\b[01]{4,}\b",
    r"agrupacion de \d+ bits|\bnibble\b|\bocteto\b|\bcuarteto\b",
    r"capacidad de almacenamiento|unidad(es)? de (capacidad|almacenamiento|medida|informacion)",
    r"orden(e|ar)? de menor a mayor",
    r"saganbyte|yottabyte|zettabyte|exabyte|petabyte|terabyte|gibibyte|mebibyte|kibibyte",
    r"cuantos bytes|\bbytes? tiene\b",
    r"\bgb\b|\bkb\b|\bmb\b|\btb\b|\bgib\b|\bmib\b",
    r"capacidad de informacion",
)

#: El álgebra de Boole y las puertas lógicas.
_LOGICA = (
    r"algebra de boole|\bboole\b",
    r"puerta(s)? logica",
    r"\bnand\b|\bnor\b|\bxnor\b|\bxor\b",
    r"operacion(es)? (logica|booleana)|operaciones basicas",
    r"tabla de verdad",
)

#: La codificación de caracteres, la coma flotante y la teoría de la información.
_CODIFICACION = (
    r"\bascii\b|\bunicode\b|utf ?8|\butf\b|iso ?8859|latin ?1|\bebcdic\b",
    r"ieee ?754|coma flotante|doble precision|precision simple",
    r"huffman",
    r"entropia|teoria de la informacion",
    r"bit de paridad|paridad (par|impar)",
    r"deteccion de errores|deteccion y correccion",
    r"codificacion (de|estandar|de fuente|de caracteres|de la informacion)",
    r"codigo (ascii|de caracteres|de linea)",
    r"representacion (correcta|de la informacion|de caracteres)",
    r"internet mail consortium",
)

#: Los sistemas de información, sus niveles y el proceso de datos.
_SISTEMAS_DE_INFORMACION = (
    r"sistema(s)? de informacion",
    r"nivel(es)? organizativo",
    r"proceso de datos|procesamiento de datos",
    r"datos en bruto",
    r"toma de decisiones|decisiones a (medio|corto|largo) plazo",
    r"departamento de sistemas|subareas",
    r"partes principales de un proceso",
)

#: Las características y funciones del sistema informático (el epígrafe de una sola pregunta).
_CARACTERISTICAS = (
    r"sistema(s)? informatico",
    r"se considere abierto|considere abierto",
    r"caracteristicas? de un sistema",
    r"funciones? de un sistema",
)

#: Las arquitecturas de computadores y las familias de procesadores.
_ARQUITECTURAS = (
    r"von ?neumann|van neumann|neumman|neumann",
    r"harvard",
    r"\brisc\b|\bcisc\b",
    r"flynn|\bsisd\b|\bsimd\b|\bmisd\b|\bmimd\b",
    r"superescalar",
    r"segmentacion|solapad|pipelining|\bpipeline\b",
    r"multinucleo|dos nucleos|\bnucleos\b",
    r"\barm\b|x86|\bintel\b|\bamd\b|\bxeon\b|core i",
    r"arquitectura(s)? (de|del) (computadores|ordenadores|computacion)",
    r"juego de instrucciones|conjunto de instrucciones",
    r"microprogramacion|microprogramad",
    r"taxonomia de flynn",
)

#: La unidad central de proceso: control, ALU, registros e interrupciones.
_LA_CPU = (
    r"\bcpu\b|unidad central de (proceso|procesamiento)",
    r"\balu\b|unidad aritmetico ?logica",
    r"unidad de control",
    r"registro(s)? (de|del) (la )?(instruccion|instrucciones|proposito|estado|datos|direccion)",
    r"\bregistro (ir|pc|ri|ac|mar|mbr)\b",
    r"contador de programa|program counter",
    r"ciclo de instruccion",
    r"decodific",
    r"secuenciador",
    r"interrupcion",
    r"modo(s)? de direccionamiento",
    r"\bflops\b|megaflops",
    r"potencia de un microprocesador",
    r"\bgpu\b|unidad de procesamiento grafico",
    r"ejecuta directamente las instrucciones|interpretar y ejecutar",
    r"senales? de sincronia",
)

#: La memoria principal y su jerarquía.
_LA_MEMORIA = (
    r"memoria (principal|central|fisica|virtual|cache)",
    r"jerarquia de memoria",
    r"\bcache\b",
    r"bus de direcciones",
    r"direccionable|direccionar",
    r"\bmmu\b|memory management unit",
    r"espacio de direcciones",
    r"capacidad maxima de la memoria|capacidad de una memoria",
    r"ancho de palabra|palabras si tenemos en cuenta",
    r"retardo producido al acceder|tiempo de acceso",
    r"correspondencia (de|directa|asociativa)",
    r"leer pero no modificar",
    r"transferencia de memoria",
    r"cantidad de informacion",
)

#: Los buses y la entrada/salida.
_BUSES = (
    r"controlador(es)? de e s\b|controlador de entrada",
    r"\bdma\b|acceso directo a memoria",
    r"programa canal",
    r"\bbus\b|\bbuses\b",
    r"puente norte|puente sur|northbridge|southbridge",
    r"multiplexor",
    r"entrada ? ?salida|\be s\b|entrada ?/? ?salida",
    r"interfaz(es)? (de|con) (el|los) (periferico|componentes internos)",
    r"ancho de banda para la transferencia",
)

#: La placa base, el conjunto de chips y los conectores internos.
_PLACA_BASE = (
    r"placa base|placa madre|motherboard",
    r"chipset|conjunto de chips",
    r"zocalo|socket",
    r"\bpci\b|\bpci ?express\b|\bpcie\b",
    r"factor de forma|microatx|\batx\b|\bitx\b",
    r"conector(es)? de \d+ pines",
    r"bateria|pila del (pc|sistema|equipo)|reloj del pc",
    r"fuente de alimentacion",
    r"\bnuc\b",
    r"puertos? (usb|serie|paralelo|ps ?2)",
    r"ranura(s)? de (expansion|memoria)",
)

#: Las memorias del equipo: RAM, ROM y sus familias.
_LAS_MEMORIAS = (
    r"\bram\b|\bsram\b|\bdram\b|\brom\b|\beprom\b|\beeprom\b|\bprom\b|\bnvram\b|\bflash\b",
    r"\becc\b",
    r"refresco",
    r"volatil",
    r"\bddr\b",
    r"memoria(s)? (de acceso aleatorio|de solo lectura|dinamica|estatica|de tipo|tipo )",
    r"memorias? (con acceso|de un pc|de tipo|son)",
    r"modulo de memoria|chip de memoria",
    r"de forma persistente",
    r"memoria (ram|rom|flash)",
)

#: La BIOS, la UEFI y el arranque del equipo.
_BIOS = (
    r"\bbios\b|\buefi\b",
    r"firmware",
    r"\bcmos\b",
    r"arranque del (pc|equipo|ordenador)|secuencia de arranque",
    r"\bpost\b|power on self test",
    r"diagnosticar algunos fallos",
    r"configuracion (guardada|de la bios|del equipo)",
)

MATERIAS: tuple[Materia, ...] = (
    # --- II.1.1 Informática básica --------------------------------------------------------------
    Materia(
        key="historia-y-generaciones-de-ordenadores",
        epigraph_code="II.1.1",
        title="La historia de la informática y las generaciones de ordenadores",
        resumen=(
            "De dónde viene la máquina: el componente electrónico que define cada generación —la "
            "válvula de vacío, el transistor, el circuito integrado—, cuál fue la primera "
            "computadora electrónica, la ley empírica que Gordon E. Moore enunció en 1965 y el "
            "papel de los grandes sistemas."
        ),
        patrones=_HISTORIA,
        patrones_debiles=(r"generacion(es)?",),
        prioridad=50,
    ),
    Materia(
        key="informatica-basica-y-ofimatica",
        epigraph_code="II.1.1",
        title="La informática básica: el interfaz, los documentos y los programas",
        resumen=(
            "Lo que se maneja todos los días: qué es y qué no es un interfaz de usuario, cómo se "
            "genera un PDF a partir de un documento de texto, las hojas de cálculo y la ofimática, "
            "y la diferencia entre un compilador y un intérprete."
        ),
        patrones=_OFIMATICA,
        patrones_debiles=(r"informatica basica",),
        prioridad=60,
    ),
    # --- II.1.2 Representación y comunicación de la información ---------------------------------
    Materia(
        key="sistemas-de-numeracion-y-unidades-de-medida",
        epigraph_code="II.1.2",
        title="Los sistemas de numeración y las unidades de medida de la información",
        resumen=(
            "Cómo se escribe un número dentro de la máquina: binario, octal, hexadecimal y decimal "
            "y el paso de uno a otro, el complemento a dos y la suma de bits, la agrupación de "
            "bits"
            "y el nibble, y las unidades de capacidad —del bit al saganbyte— con su orden de menor "
            "a mayor."
        ),
        patrones=_NUMERACION,
        patrones_debiles=(r"bits?", r"bytes?", r"numero(s)?", r"capacidad"),
        prioridad=30,
    ),
    Materia(
        key="algebra-de-boole-y-puertas-logicas",
        epigraph_code="II.1.2",
        title="El álgebra de Boole y las puertas lógicas",
        resumen=(
            "La lógica con la que está hecha la máquina: las operaciones básicas del álgebra de "
            "Boole, la operación XOR y lo que devuelve una puerta NAND, NOR o XNOR de dos entradas."
        ),
        patrones=_LOGICA,
        patrones_debiles=(r"logica",),
        prioridad=25,
    ),
    Materia(
        key="codificacion-y-teoria-de-la-informacion",
        epigraph_code="II.1.2",
        title="La codificación de la información y la teoría de la información",
        resumen=(
            "Cómo se representa un carácter y un número real: el código ASCII y sus bits, UTF-8 y "
            "su normalización, el estándar IEEE 754 y la coma flotante de doble precisión, la "
            "codificación de fuente de Huffman, la entropía, y el bit de paridad con la detección "
            "de errores en la transmisión."
        ),
        patrones=_CODIFICACION,
        patrones_debiles=(r"codificacion", r"informacion"),
        prioridad=20,
    ),
    Materia(
        key="sistemas-de-informacion-y-proceso-de-datos",
        epigraph_code="II.1.2",
        title="Los sistemas de información y el proceso de datos",
        resumen=(
            "El sistema entero, no la máquina: en qué nivel organizativo se asocian los datos en "
            "bruto, cuáles son las partes principales de un proceso de datos, dónde se toman las "
            "decisiones a medio y largo plazo y qué subáreas tiene el área de sistemas de un "
            "departamento informático."
        ),
        patrones=_SISTEMAS_DE_INFORMACION,
        patrones_debiles=(r"sistema(s)?", r"datos"),
        prioridad=40,
    ),
    # --- II.1.3 Características y funciones -----------------------------------------------------
    Materia(
        key="caracteristicas-y-funciones-del-sistema-informatico",
        epigraph_code="II.1.3",
        title="Las características y las funciones del sistema informático",
        resumen=(
            "El sistema informático en abstracto: qué característica hace que se considere "
            "«abierto», de qué partes consta y qué funciones cumple, sin bajar todavía al "
            "componente concreto."
        ),
        patrones=_CARACTERISTICAS,
        patrones_debiles=(r"caracteristicas?", r"funciones?"),
        prioridad=70,
    ),
    # --- II.1.4 Arquitectura de ordenadores -----------------------------------------------------
    Materia(
        key="arquitecturas-y-procesadores",
        epigraph_code="II.1.4",
        title="Las arquitecturas de ordenadores y las familias de procesadores",
        resumen=(
            "Cómo está pensada la máquina por dentro: el modelo de Von Neumann y el de Harvard, "
            "las cuatro categorías de la taxonomía de Flynn, RISC frente a CISC y sus juegos de "
            "instrucciones, la segmentación y la ejecución solapada de instrucciones, el "
            "superescalar, el multinúcleo, la microprogramación y las familias Intel, x86 y ARM."
        ),
        patrones=_ARQUITECTURAS,
        patrones_debiles=(r"arquitectura(s)?", r"procesador(es)?"),
        prioridad=45,
    ),
    Materia(
        key="la-cpu-y-sus-registros",
        epigraph_code="II.1.4",
        title="La unidad central de proceso: control, ALU, registros e interrupciones",
        resumen=(
            "El que ejecuta: la unidad de control y la unidad aritmético-lógica, el registro de "
            "instrucción y el contador de programa, el ciclo de instrucción y la decodificación, "
            "el"
            "secuenciador, las interrupciones —las de hardware y las que produce la propia CPU—, "
            "los modos de direccionamiento y la potencia medida en FLOPS."
        ),
        patrones=_LA_CPU,
        patrones_debiles=(r"instruccion(es)?", r"unidad"),
        prioridad=20,
    ),
    Materia(
        key="la-memoria-y-su-jerarquia",
        epigraph_code="II.1.4",
        title="La memoria principal y su jerarquía",
        resumen=(
            "Dónde están los programas y sus datos: la memoria principal y la caché, la jerarquía "
            "de memoria y el orden de velocidad de acceso, el bus de direcciones y la memoria "
            "máxima direccionable, la unidad de gestión de memoria, el espacio de direcciones, el "
            "ancho de palabra y el retardo de acceso a la RAM."
        ),
        patrones=_LA_MEMORIA,
        patrones_debiles=(r"memoria(s)?",),
        prioridad=25,
    ),
    Materia(
        key="buses-y-entrada-salida",
        epigraph_code="II.1.4",
        title="Los buses y la entrada/salida",
        resumen=(
            "Cómo se hablan la CPU y el resto: por qué existe un controlador de E/S y qué hace, el "
            "acceso directo a memoria, el programa canal, el multiplexor, el bus del sistema con "
            "sus señales de sincronía y control, y qué interfaz ofrece más ancho de banda entre "
            "los"
            "componentes internos."
        ),
        patrones=_BUSES,
        patrones_debiles=(r"periferico(s)?",),
        prioridad=90,
    ),
    # --- II.1.5 Componentes internos de los equipos microinformáticos ---------------------------
    Materia(
        key="la-placa-base-y-el-conjunto-de-chips",
        epigraph_code="II.1.5",
        title="La placa base, el conjunto de chips y los conectores internos",
        resumen=(
            "El soporte de todo: el conjunto de chips con sus puentes norte y sur y qué controla "
            "cada uno, los zócalos del microprocesador, PCI Express y su ancho de banda, el factor "
            "de forma de la placa, los conectores internos, la pila que mantiene el reloj y los "
            "equipos compactos."
        ),
        patrones=_PLACA_BASE,
        patrones_debiles=(r"placa", r"conector(es)?"),
        prioridad=30,
    ),
    Materia(
        key="las-memorias-del-equipo",
        epigraph_code="II.1.5",
        title="Las memorias del equipo: RAM, ROM y sus familias",
        resumen=(
            "Las memorias que se compran: RAM, SRAM y DRAM y su elemento activo, ROM, EPROM y "
            "EEPROM con su característica principal, la memoria con corrección de errores, el "
            "refresco de la memoria dinámica, qué memorias son volátiles, DDR y la memoria "
            "persistente."
        ),
        patrones=_LAS_MEMORIAS,
        patrones_debiles=(r"memoria(s)?", r"almacenar"),
        prioridad=20,
    ),
    Materia(
        key="la-bios-la-uefi-y-el-arranque",
        epigraph_code="II.1.5",
        title="La BIOS, la UEFI y el arranque del equipo",
        resumen=(
            "Lo que pasa al encender: el programa BIOS y la UEFI y su ventaja en la gestión del "
            "almacenamiento, dónde se guardan los datos de configuración, el firmware y por qué se "
            "actualiza, la CMOS, la secuencia de arranque y los fallos que se diagnostican con los "
            "tonos."
        ),
        patrones=_BIOS,
        patrones_debiles=(r"arranque", r"configuracion"),
        prioridad=25,
    ),
)

#: El orden del índice. Primero lo que es la informática y cómo se representa la información,
#: después la máquina por dentro —arquitectura, procesador, memoria y entrada/salida— y, al final,
#: los componentes que se tocan: la placa, las memorias y la BIOS.
ORDEN: tuple[str, ...] = (
    "historia-y-generaciones-de-ordenadores",
    "informatica-basica-y-ofimatica",
    "sistemas-de-numeracion-y-unidades-de-medida",
    "algebra-de-boole-y-puertas-logicas",
    "codificacion-y-teoria-de-la-informacion",
    "sistemas-de-informacion-y-proceso-de-datos",
    "caracteristicas-y-funciones-del-sistema-informatico",
    "arquitecturas-y-procesadores",
    "la-cpu-y-sus-registros",
    "la-memoria-y-su-jerarquia",
    "buses-y-entrada-salida",
    "la-placa-base-y-el-conjunto-de-chips",
    "las-memorias-del-equipo",
    "la-bios-la-uefi-y-el-arranque",
)

__all__ = ["MATERIAS", "ORDEN"]
