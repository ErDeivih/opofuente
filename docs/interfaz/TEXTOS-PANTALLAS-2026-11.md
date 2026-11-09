# Textos visibles por pantalla (OpoFuente, 2026-11)

Anexo del [inventario de pantallas](./INVENTARIO-PANTALLAS-2026-11.md). Es el volcado literal del
`innerText` que se ve en cada pantalla, capturado con Playwright el mismo día que las imágenes.
Sirve para juzgar el copy: lo que el revisor externo lea aquí es exactamente lo que aparece en la
pantalla, sin reconstruir ni corregir tildes.

> **Los datos son sintéticos** (los de la suite E2E). Por eso hay textos sin tildes, títulos como
> «Apuntes sinteticos E2E-08 mw8f42ou» y contenidos de relleno: no son defectos de copy de la
> interfaz. Los textos de la interfaz —etiquetas, avisos, botones, estados vacíos— sí son los
> reales.

Generado con `node docs/interfaz/generar-textos.mjs` a partir de `.captura-datos.json` y
`.captura-vacio.json`.

## Índice

- **inicio** — `/`
- **bandeja** — `/bandeja`
- **temario** — `/temario`
- **programa** — `/programa`
- **biblioteca** — `/biblioteca`
- **preguntas** — `/preguntas`
- **estudiar** — `/estudiar`
- **errores** — `/errores`
- **cambios** — `/cambios`
- **revision** — `/revision`
- **buscar** — `/buscar?q=plazo`
- **ajustes** — `/ajustes`
- **no-encontrada** — `/seccion-que-no-existe`
- **temario-tema** — `/temario/ec996939-7d8d-4803-9d73-eff38cf0df23`
- **temario-tema-practicar** — `/temario/ec996939-7d8d-4803-9d73-eff38cf0df23/practicar`
- **temario-tema-convocatoria** — `/temario/a8c67150-b1fd-49d3-b5f9-85ec8f26d1c5?convocatoria=f6b51232-7525-49f8-a19e-fdf74c5fbfad`
- **biblioteca-documento** — `/biblioteca?documento=159de869-bea9-4178-aa42-6b0ebf28888f`
- **biblioteca-documento-versiones** — `/biblioteca?documento=159de869-bea9-4178-aa42-6b0ebf28888f`
- **preguntas-conjunto** — `/preguntas?conjunto=72482c3a-cf15-438f-9435-1b2b61732164&pregunta=0c380199-ac3e-4237-a406-d9066f142548`
- **preguntas-plantillas** — `/preguntas`
- **inicio-cargando** — `/`
- **inicio-error** — `/`
- **preguntas-cargando** — `/preguntas`
- **preguntas-error** — `/preguntas`

## Con datos (directorio sintético `.e2e-data`)

Volcado a 1280 px de ancho. A 390 px el contenido es el mismo salvo el reflujo de la navegación y las tablas (que pasan a bloques); los textos que cambian con el ancho se señalan en el inventario.

### inicio — `/`

- **Captura**: [inicio-1280.png](../capturas/revision-2026-11/inicio-1280.png) (1280×900, 3564 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Inicio»
- **Encabezados**: Inicio · Siguiente tarea · Continuar estudiando · Acciones necesarias · Estado del programa · ¿Listo para estudiar? · Actividad reciente · Últimos lotes · Últimas sesiones · Estado del sistema · Capacidades · Degradaciones declaradas · Almacenamiento
- **Estados**: vacío 0, cargando 0, error 0, avisos 2

Texto visible de `main` (innerText tal cual):

```text
Inicio

La siguiente tarea de hoy: el repaso vencido manda; si no hay nada vencido, se continúa la sesión que quedó a medias.

Siguiente tarea

4 pregunta(s) vencida(s) de repaso 4 de 19 vencidos

Se repasan en una sesión compuesta con lo vencido: la solución no se enseña antes de contestar.

Ir al repaso de errores
Continuar estudiando
Sesión en marcha
práctica · 1 de 2 preguntas
Empezó
2026-11-08T22:43:07.294168
Se retoma en
Estudiar, donde estaba: la sesión vive en el servidor y su cronómetro también.
Acciones necesarias

La aplicación ya ha hecho lo que puede hacer sola. Esto es lo que no puede decidir por ti (ADR-017): cada línea lleva a la pantalla donde se resuelve.

!
18 pendiente(s)
Importaciones con avisos o errores: 18 aviso(s) y error(es) de importación sin resolver: dicen qué fichero no entró y por qué
Ver la bandeja
!
9 pendiente(s)
Clasificaciones esperando tu decisión: 9 decisión(es) sin tomar: mientras no se tomen, ese material no está en ningún tema del programa
Revisar propuestas
!
2 pendiente(s)
Cambios de fuente sin confirmar: 2 cambio(s) propuesto(s) entre versiones: hay que decir si valen o no antes de seguir estudiando con ellos
Ver los cambios
!
1 pendiente(s)
Material sin aceptar: 1 versión(es) de documento sin aceptar: aceptarlas es lo que las convierte en material de estudio y dispara la importación de sus preguntas
Ver la biblioteca
Estado del programa
Oposición activa
Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado tai-age
Convocatoria
tai-age-2025 · publicada el 2025-12-22
Perfiles disponibles
4
¿Listo para estudiar?

!
faltan 2 cosas
Lo que falta está dicho en su paso, con lo que hay que hacer para resolverlo.

✔
Material por papel: listo
4 documento(s) aceptado(s): Temario o programa (3), Apuntes personales (1). Y 3 sin decir todavía a qué parte de este programa pertenece(n), así que la cobertura por temas no los ve
Ver la biblioteca
!
Preguntas por tema: a medias
132 pregunta(s) en 14 conjunto(s); 6 catalogada(s) por tema. Quedan 126 sin tema, y sin tema el diagnóstico por temas no las reparte: se catalogan al aceptar la asignación del documento del que salen
Ver el banco
!
Claves activas: a medias
11 de 14 conjunto(s) con clave activa. 3 sin ella: sin clave activa no se puede corregir ni empezar una sesión sobre ese conjunto
Ver las plantillas

Dominio estimado por tema (07_UI-UX §3, §5): contando lo que has practicado…. Sin intentos no hay dominio, y con pocos es «evidencia insuficiente»: verlo tema a tema en el Programa.

Actividad reciente
Últimos lotes
import: terminado · 3 entrada(s) · 2026-11-08T22:43:37.521753
Ver en la bandeja
inventory: terminado · 6 entrada(s) · 2026-11-08T22:43:37.028473
Ver en la bandeja
import: terminado · 3 entrada(s) · 2026-11-08T22:43:34.304123
Ver en la bandeja
Últimas sesiones
práctica: en marcha · 1 de 2 preguntas
Abrir en Estudiar
simulacro: terminada · 0 de 85 preguntas
Abrir en Estudiar
diagnóstico: terminada · 6 de 6 preguntas
Abrir en Estudiar
Estado del sistema
✔
listo para trabajar
✔
database
sqlite ok (revisión 0023_block_practice, foreign_keys=ON, journal_mode=wal, app_metadata=3)
✔
data_dir
directorio de datos escribible
Capacidades
Capacidades de esta instalación
CAPACIDAD	ESTADO	QUÉ SIGNIFICA
OCR (Tesseract)	
!
configurado sin verificar
	Binario presente, pero la aplicación no lo llama: el OCR no está implementado y una imagen se queda pendiente con su aviso. Declararlo evita creer que un PDF escaneado se está leyendo.
Modelo de lenguaje	
·
desactivado
	Sin proveedor: las respuestas se componen del propio corpus (extractivas) y citan cada afirmación. Un modelo de lenguaje llegaría con la deuda DEBT-014.
Embeddings	
·
desactivado
	Sin proveedor de embeddings decidido: la búsqueda es literal (FTS5) y cada respuesta lo declara como degradación (DEBT-014).
Búsqueda literal (FTS5)	
✔
operativo
	Índice léxico comprobado: tabla externa sobre evidence_spans, ordenada por bm25, con los disparadores que la mantienen al día; se rehace cuando haga falta sin salir de SQLite.
Almacén de originales por SHA-256	
✔
operativo
	Copia inmutable por contenido en <datos>/artifacts/sha256/ab/cd/<hash>. Dos ficheros idénticos comparten un artefacto y conservan dos orígenes.
Cola de trabajos local	
✔
operativo
	Cola persistida en SQLite con lease, trabajada por este proceso; sin Redis ni Celery. Cerrar la pestaña no cancela el trabajo.
Índice vectorial local	
×
no disponible
	Sin proveedor de embeddings no hay vectores que indexar: la búsqueda del corpus es literal (FTS5) sobre el texto extraído (DEBT-014).
Degradaciones declaradas

La aplicación funciona sin estas piezas. Se listan para que no haya funciones ausentes disfrazadas de correctas.

OCR (Tesseract): configurado sin verificar. Binario presente, pero la aplicación no lo llama: el OCR no está implementado y una imagen se queda pendiente con su aviso. Declararlo evita creer que un PDF escaneado se está leyendo.
Modelo de lenguaje: no configurado. Sin proveedor: las respuestas se componen del propio corpus (extractivas) y citan cada afirmación. Un modelo de lenguaje llegaría con la deuda DEBT-014.
Embeddings: no configurado. Sin proveedor de embeddings decidido: la búsqueda es literal (FTS5) y cada respuesta lo declara como degradación (DEBT-014).
Índice vectorial local: no disponible. Sin proveedor de embeddings no hay vectores que indexar: la búsqueda del corpus es literal (FTS5) sobre el texto extraído (DEBT-014).
Almacenamiento
Directorio de datos
F:\Proyectos\opofuente\.e2e-data
Espacio libre
148.0 GB
Proveedor de IA
disabled (sin proveedor)
OCR
disponible
```

### bandeja — `/bandeja`

- **Captura**: [bandeja-1280.png](../capturas/revision-2026-11/bandeja-1280.png) (1280×900, 2237 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Bandeja»
- **Encabezados**: Bandeja · Entrada · Otras formas de entrada · Ficheros o carpetas enteras · Texto pegado · Desde una URL · Lotes recientes
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Bandeja

OpoFuente copia: nunca mueve, renombra ni borra tus originales. Primero inventaría la carpeta en modo lectura y solo después copia lo que confirmes.

Revisar la clasificación del material
Lo importado se clasifica en propuestas: se confirman (o se rechazan) en Revisión.

Entrada
Carpeta a inventariar (ruta absoluta)
Inventariar (solo lectura)

Las tres formas de entrada del MVP están aquí: inventariar una carpeta, copiar ficheros sueltos, pegar texto y traer una URL. Ninguna mueve ni borra nada de su origen.

Otras formas de entrada
Ficheros o carpetas enteras

Suelta una carpeta y entran todos sus ficheros, conservando su ruta («Tema 3/apuntes.pdf»). Un ZIP se copia y se expande al extraer, con límites de tamaño y sin seguir rutas que salgan del paquete. Una baraja de Anki (`.apkg`) se lee como baraja.

Suelta aquí ficheros o carpetas
O elige una carpeta
Texto pegado

Se guarda como material propio con origen «pegado». No sustituye al documento original: es texto, y así se declara.

Texto
Título (opcional)
Guardar el texto
Desde una URL

Solo http y https. El servidor comprueba cada redirección y bloquea direcciones internas; no se eluden controles de acceso ni muros de pago.

Dirección
Descargar y copiar
Lotes recientes
import · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
3 entradas
inventory · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
6 entradas
import · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
3 entradas
inventory · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
6 entradas
import · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
3 entradas
inventory · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
6 entradas
import · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
3 entradas
inventory · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
6 entradas
import · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
3 entradas
inventory · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
6 entradas
import · 2 fichero(s) seleccionados
✔
terminado
2 entradas
import · 1 fichero(s) seleccionados
✔
terminado
3 entradas
import · Apuntes del tema 1
✔
terminado
1 entradas
import · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
3 entradas
inventory · …/opofuente-e2e-HI7Z5Q/material-sintetico
✔
terminado
6 entradas
import · 1 fichero(s) seleccionados
✔
terminado
1 entradas
import · 1 fichero(s) seleccionados
✔
terminado
1 entradas
import · 3 fichero(s) seleccionados
✔
terminado
3 entradas
import · 1 fichero(s) seleccionados
✔
terminado
1 entradas
import · 1 fichero(s) seleccionados
✔
terminado
1 entradas
import · 2 fichero(s) seleccionados
✔
terminado
2 entradas
import · e2e-09-mw8f32g4-v2.txt
✔
terminado
1 entradas
import · e2e-09-mw8f32g4-v1.txt
✔
terminado
1 entradas
```

### temario — `/temario`

- **Captura**: [temario-1280.png](../capturas/revision-2026-11/temario-1280.png) (1280×900, 2555 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Temario»
- **Encabezados**: Temario · Temas · Avance · Por bloque · Qué queda
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Temario

5 bloques · 40 temas

Temas
Buscar un tema

▾
I
Administración y normativa
1
La Constitución Española de 1978
2
La Unión Europea
3
El régimen local
4
Organización municipal
5
El procedimiento administrativo (Ley 39/2015)
6
El régimen jurídico del sector público (Ley 40/2015)
7
El personal al servicio de las administraciones (TREBEP)
8
La función pública local
9
Las haciendas locales y el presupuesto
10
La contratación del sector público (Ley 9/2017)
11
Igualdad y violencia de género
12
Transparencia y protección de datos en la Administración
▾
II
Informática básica y ofimática
13
Arquitectura de ordenadores
14
Sistemas operativos de usuario
15
Ofimática
16
Correo electrónico y colaboración
17
Licencias y software libre
▾
III
Sistemas, redes y comunicaciones
18
Sistemas operativos de servidor
19
Virtualización y contenedores
20
Almacenamiento y copias de seguridad
21
Redes
22
Comunicaciones
23
Servicios de red
24
Monitorización y gestión de incidencias
25
Cloud y centros de datos
26
Soporte al puesto de trabajo
▾
IV
Datos y desarrollo
27
Bases de datos relacionales
28
SQL
29
Gestores de bases de datos
30
Programación
31
Desarrollo web
32
Interoperabilidad e integración
33
Informes y explotación de datos
▾
V
Seguridad y administración electrónica
34
Seguridad de la información
35
El Esquema Nacional de Seguridad (ENS, RD 311/2022)
36
Criptografía y firma electrónica
37
Protección de datos aplicada
38
Ciberseguridad
39
Administración electrónica práctica
40
Accesibilidad y usabilidad
Avance

0 de 40 temas estudiados

Por bloque
I
Administración y normativa
0 de 12
Practicar este bloque
II
Informática básica y ofimática
0 de 5
Practicar este bloque
III
Sistemas, redes y comunicaciones
0 de 9
Practicar este bloque
IV
Datos y desarrollo
0 de 7
Practicar este bloque
V
Seguridad y administración electrónica
0 de 7
Practicar este bloque
Qué queda
I
Administración y normativa
12 de 12 sin estudiar
III
Sistemas, redes y comunicaciones
9 de 9 sin estudiar
IV
Datos y desarrollo
7 de 7 sin estudiar
V
Seguridad y administración electrónica
7 de 7 sin estudiar
II
Informática básica y ofimática
5 de 5 sin estudiar
```

### programa — `/programa`

- **Captura**: [programa-1280.png](../capturas/revision-2026-11/programa-1280.png) (1280×900, 4733 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Programa»
- **Encabezados**: Programa · Temario oficial · Reglas del examen · Ejercicio único
120 min · Reglas transversales · Procedencia oficial
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Programa

Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado · 4 bloques, 33 temas

Temario oficial
▾
I
Organización del Estado y Administración electrónica
bloque
1
La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
tema
2
Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
tema
3
El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
tema
4
El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
tema
5
Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
tema
6
La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
tema
7
La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
tema
8
Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
tema
9
Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
tema
▾
II
Tecnología básica
bloque
1
Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
tema
2
Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
tema
3
Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
tema
4
Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
tema
5
Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
tema
▾
III
Desarrollo de sistemas
bloque
1
Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
tema
2
Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
tema
3
Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
tema
4
Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
tema
5
Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
tema
6
Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
tema
7
Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
tema
8
Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
tema
9
Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
tema
▾
IV
Sistemas y comunicaciones
bloque
1
Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
tema
2
Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
tema
3
Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
tema
4
Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
tema
5
Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
tema
6
Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
tema
7
El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
tema
8
Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
tema
9
Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
tema
10
Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
tema
Reglas del examen

Cada parte y cada regla incluye la cita literal de la convocatoria de la que procede. Esta pantalla solo muestra lo que publica la convocatoria: la puntuación de una sesión se calcula en Estudio, con estas reglas.

Ejercicio único
120 min

Dos partes que se realizan conjuntamente, ambas obligatorias y eliminatorias. El ejercicio único se califica de 0 a 100 puntos.

Pruebas de esta parte
PRUEBA	FORMATO	PREGUNTAS	PUNTUACIÓN	CONDICIÓN
Primera parte: cuestionario de conocimientos	elección única	80 (+5 de reserva)	0–50, mínimo 25	—
Segunda parte: supuesto práctico	elección única	20 (+5 de reserva)	0–50, mínimo 25	—
El proceso de selección estará formado por un ejercicio único que constará de las dos partes que a continuación se indican y que se realizarán conjuntamente, ambas obligatorias y eliminatorias.
Reglas transversales
·
blank_answer_penalty
0

Las respuestas en blanco no penalizan.

Las respuestas en blanco no penalizan.
·
direct_score_minimum_ratio
0.30

Las puntuaciones directas mínimas que fije la Comisión no pueden ser inferiores al 30 % de la puntuación directa máxima obtenible.

Las puntuaciones directas mínimas no podrán ser inferiores al 30 por ciento de la puntuación directa máxima obtenible.
·
official_scaled_score_requires_published_criteria
true

La calificación oficial 0-100 resulta de transformar las puntuaciones directas con los baremos que fije la Comisión Permanente de Selección. Sin ese criterio publicado, la aplicación solo puede mostrar la puntuación directa y debe declarar la calificación oficial como no disponible.

En cada una de las partes del ejercicio la calificación resultará de la transformación de las puntuaciones directas que se deriven de los baremos establecidos por la Comisión Permanente de Selección
·
one_correct_answer
true

Cada pregunta tiene una sola respuesta correcta.

El cuestionario de ambas partes estará compuesto por preguntas con respuestas alternativas, de las cuales sólo una de ellas es correcta.
·
part_pass_score
25

Cada parte se califica de 0 a 50 y requiere un mínimo de 25 para superarse.

Primera parte: se calificará de 0 a 50 puntos, y será necesario obtener una calificación mínima de 25 puntos para superarla.
·
second_part_not_graded_without_selected_case
true

La segunda parte no se corrige si no hay un supuesto válidamente señalado.

No será corregida la segunda parte del ejercicio en el caso de que no tenga señalado el supuesto elegido, que se señalen ambos supuestos o que la marca no sea válida.
·
tie_break_order
1) mayor puntuación directa en la segunda parte; 2) mayor número de respuestas correctas en la segunda parte; 3) mayor número de respuestas correctas en la primera parte; 4) menor número de contestaciones erróneas en la segunda parte; 5) menor número de contestaciones erróneas en la primera parte

Orden de prelación en caso de empate en la calificación total.

Primero: la mayor puntuación directa obtenida en la segunda parte; segundo: el mayor número de respuestas correctas obtenidas en la segunda parte; tercero: el mayor número de respuestas correctas obtenidas en la primera parte; cuarto: el menor número de contestaciones erróneas realizadas en la segunda parte; quinto: el menor número de contestaciones erróneas realizadas en la primera parte.
·
wrong_answer_penalty
1/3 del valor de una respuesta correcta

Cada contestación errónea descuenta un tercio del valor de una respuesta correcta. Todas las preguntas valen lo mismo.

Todas las preguntas tendrán el mismo valor y cada contestación errónea se penalizará descontando un tercio del valor de una respuesta correcta.
Procedencia oficial

Resolución de 18 de diciembre de 2025, de la Secretaría de Estado de Función Pública, por la que se convocan procesos selectivos para el ingreso libre en el Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado (código 1188)

Publicación
2025-12-22
Fuente
BOE-A-2025-26262 · ANEXO V
Fecha del examen
No consta en la convocatoria

Los datos se extraen de la publicación oficial. OpoFuente no es un organismo oficial y esta pantalla no sustituye a la convocatoria: ante cualquier duda, prevalece el texto publicado.
```

### biblioteca — `/biblioteca`

- **Captura**: [biblioteca-1280.png](../capturas/revision-2026-11/biblioteca-1280.png) (1280×900, 1554 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Biblioteca»
- **Encabezados**: Biblioteca · Filtros · Colecciones · Documentos
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Biblioteca

Tus documentos con sus versiones, sus derechos y su procedencia. Un documento privado no se hace público por promocionarlo, y una versión candidata no es la versión buena hasta que alguien la acepta.

Filtros
Tipo documental
cualquier tipo
Convocatoria
Programa o temario
Norma o reglamento
Documento técnico oficial
Temario privado
Notas personales
Examen oficial
Plantilla de respuestas
Banco de preguntas privado
Caso práctico
Fichas de repaso
Material de la comunidad
Sin clasificar
Ámbito
cualquier ámbito
público
privado tuyo
generado por la aplicación
Derechos
cualquier derecho
solo restringidos (no se pueden compartir)
solo con derechos revisados
Limpiar filtros

Tipo documental y ámbito los filtra el servidor. El de derechos se aplica sobre los documentos ya cargados, porque la API todavía no filtra por derechos: el recuento que se ve es el de esta pantalla, no el de toda la biblioteca.

Colecciones

Una colección agrupa material sin duplicarlo: el mismo documento puede estar en varias. El filtro se aplica en el servidor, así que lo que se ve son los documentos de la colección y no los que han quedado fuera de la página.

Todos los documentos
Coleccion E2E-04 mw8f3g57 
·
0 miembros
Nombre de la colección
Descripción (opcional)
Crear la colección
Documentos

4 de 4 documentos

4 documentos en la biblioteca
TÍTULO	TIPO	VERSIÓN ACTIVA	ÁMBITO Y AUTORIDAD	RECUENTOS	AVISOS	FICHA
Apuntes sinteticos E2E-08 mw8f42ou	Notas personales personal_notes	7ff4f5a2-89eb-4776-a951-92fb7a59b108 
✔
aceptada
	privado tuyo sin autoridad declarada	2 versiones · 0 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
Plazos E2E-09 mw8f32g4	Programa o temario curriculum	88f5b83e-6d6e-4f18-a056-e7d04060ddfb 
✔
aceptada
	privado tuyo sin autoridad declarada	2 versiones · 0 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
Temario E2E preguntas mw8f3r2c	Programa o temario curriculum	81a3f987-b84c-4c55-811d-c09bf32422b2 
✔
aceptada
	privado tuyo sin autoridad declarada	1 versiones · 0 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
Temario sintetico E2E-04 mw8f3g57	Programa o temario curriculum	44b67782-bab1-4546-932c-54dd5055c994 
✔
aceptada
	privado tuyo sin autoridad declarada	2 versiones · 3 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
```

### preguntas — `/preguntas`

- **Captura**: [preguntas-1280.png](../capturas/revision-2026-11/preguntas-1280.png) (1280×900, 903 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Preguntas»
- **Encabezados**: Preguntas · Conjunto · Banco
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Preguntas

El banco de preguntas de una oposición: lo que se importa, lo que se revisa y la plantilla con la que se corrige. Importar no publica nada: una pregunta privada sigue siendo privada.

Conjunto
Conjunto abierto
Practica E2E 1794177785174-455876 · banco privado
Examen E2E 1794177782189-482891 · banco privado
Practica E2E 1794177778314-129160 · banco privado
Practica E2E 1794177775724-465317 · banco privado
Practica E2E 1794177771614-355764 · banco privado
Practica E2E 1794177768627-208028 · banco privado
Importacion E2E 1794177748510-206080 · banco privado
Importacion E2E 1794177747132-551696 · banco privado
Importacion E2E 1794177745877-933138 · banco privado
Importacion E2E 1794177745204-045898 · banco privado
JSON E2E 1794177741138-762711 · banco privado
Clave E2E 1794177725802-594034 · banco privado
Errores E2E mw8f38rv-cola · banco privado
Errores E2E mw8f36ev-cola · banco privado
4 preguntas (0 incompletas · 0 reservas) · 1 plantilla 
·
borrador
 
✔
con clave activa
Crear un conjunto
Banco
Preguntas
Importar
Plantillas
Estado
todos
incompleta
completa
verificada
en conflicto
anulada
sustituida
Origen
todos
OFICIAL
PRIVADA
GENERADA
 solo reservas
1–4 de 4 preguntas del conjunto
Nº	ENUNCIADO	ORIGEN	TIPO	CLAVE	ESTADO
1	El plazo del procedimiento del caso A es de diez dias habiles	
·
PRIVADA
	una respuesta	
✔
clave: b
	
·
completa

2	El plazo del procedimiento del caso B es de veinte dias habiles	
·
PRIVADA
	una respuesta	
✔
clave: b
	
·
completa

3	El plazo del procedimiento del caso C es de treinta dias habiles	
·
PRIVADA
	una respuesta	
✔
clave: b
	
·
completa

4	El plazo del procedimiento del caso D es de cuarenta dias habiles	
·
PRIVADA
	una respuesta	
✔
clave: b
	
·
completa
```

### estudiar — `/estudiar`

- **Captura**: [estudiar-1280.png](../capturas/revision-2026-11/estudiar-1280.png) (1280×900, 1962 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Estudiar»
- **Encabezados**: Estudiar · Sesión en marcha · Pregunta 2 · Sesiones
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Estudiar

Practicar y examinarse con el banco de preguntas. La puntuación la calcula el servidor con la clave activa del conjunto y con la penalización que publica la convocatoria.

Tienes una sesión en marcha (práctica, en marcha): se retoma donde estaba, con lo respondido y el tiempo ya corrido. Lleva 1 de 2 preguntas respondidas y empezó el 2026-11-08T22:43:07.294168.

Preparar otra sesión
La de ahora no se pierde: sigue en el historial, con lo respondido.

Sesión en marcha
Modo
práctica 
!
en marcha
Clave con la que se corrige
Primera parte: cuestionario de conocimientos: plantilla v1
Progreso
1 de 2 respondidas · 1 pendientes
Tiempo
18:26:18 · queda 00:00

Se ha agotado el tiempo de la convocatoria. La aplicación no cierra la sesión sola: se termina cuando tú lo decidas.

Pregunta 2

El plazo del procedimiento del caso B es de veinte dias habiles

A Verdadero
B Falso
Tu respuesta
 A) Verdadero
 B) Falso
Confianza (opcional)
sin declarar
dudando
normal
segura
Responder
Dejarla en blanco
Anterior
Siguiente
Terminar y corregir

Se puede terminar con preguntas pendientes: las que no se contesten salen como no respondidas y no puntúan.

Sesiones
11 sesiones de esta oposición
MODO	ESTADO	PREGUNTAS	EMPEZÓ	ACCIÓN
práctica	en marcha	1 de 2	2026-11-08T22:43:07.294168	Abrir
simulacro	terminada	0 de 85	2026-11-08T22:43:04.838266	Abrir
diagnóstico	terminada	6 de 6	2026-11-08T22:43:01.116316	Abrir
práctica	terminada	3 de 3	2026-11-08T22:42:56.833238	Abrir
práctica	en marcha	1 de 2	2026-11-08T22:42:53.720064	Abrir
práctica	terminada	3 de 3	2026-11-08T22:42:50.812886	Abrir
práctica	en marcha	1 de 1	2026-11-08T22:42:23.279837	Abrir
práctica	terminada	3 de 3	2026-11-08T22:42:07.851047	Abrir
práctica	en marcha	1 de 1	2026-11-08T22:42:01.971544	Abrir
repaso de errores	en marcha	1 de 1	2026-11-08T22:41:58.541535	Abrir
práctica	en marcha	1 de 1	2026-11-08T22:41:57.836158	Abrir
```

### errores — `/errores`

- **Captura**: [errores-1280.png](../capturas/revision-2026-11/errores-1280.png) (1280×900, 1651 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Errores»
- **Encabezados**: Errores · Repaso · Exportar
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Errores

Lo que fallaste y cuándo toca repasarlo. Un fallo entra solo en la cola; la causa, el concepto y la nota los pones tú, y el repaso va subiendo el intervalo hasta un mes.

Repaso

4 de 19 vencidos · 6 fallo(s) acumulado(s)

Hoy
Conceptos
Repasar en una sesión (4)
La sesión se compone con lo vencido y no enseña la solución antes de contestar.

El plazo del procedimiento del caso B es de veinte dias habiles 
·
toca hoy
 primer repaso · 1 fallo(s) · private

un fallo entra en la cola de hoy mismo

A) Verdadero
B) Falso
Repasado y sabido
Repasado y fallado
Aplazar 3 días

Declarar el resultado es para lo que repases fuera de aquí: el desenlace lo dices tú, no lo mide la aplicación. Último cambio: un fallo entra en la cola de hoy mismo.

El plazo del procedimiento del caso A es de diez dias habiles 
·
toca hoy
 primer repaso · 1 fallo(s) · private

un fallo entra en la cola de hoy mismo

A) Verdadero
B) Falso
Repasado y sabido
Repasado y fallado
Aplazar 3 días

Declarar el resultado es para lo que repases fuera de aquí: el desenlace lo dices tú, no lo mide la aplicación. Último cambio: un fallo entra en la cola de hoy mismo.

El plazo del procedimiento del caso B es de veinte dias habiles 
·
toca hoy
 primer repaso · 1 fallo(s) · private

un fallo entra en la cola de hoy mismo

A) Verdadero
B) Falso
Repasado y sabido
Repasado y fallado
Aplazar 3 días

Declarar el resultado es para lo que repases fuera de aquí: el desenlace lo dices tú, no lo mide la aplicación. Último cambio: un fallo entra en la cola de hoy mismo.

El plazo del procedimiento del caso C es de treinta dias habiles 
·
toca hoy
 primer repaso · 1 fallo(s) · private

un fallo entra en la cola de hoy mismo

A) Verdadero
B) Falso
Repasado y sabido
Repasado y fallado
Aplazar 3 días

Declarar el resultado es para lo que repases fuera de aquí: el desenlace lo dices tú, no lo mide la aplicación. Último cambio: un fallo entra en la cola de hoy mismo.

Exportar

El fichero se escribe en la carpeta de exportaciones del directorio de datos y lleva la procedencia de cada pregunta: conjunto, plantilla, origen, tema y las versiones de los documentos citados.

Título del fichero
 Incluir material con derechos restringidos
Anki CSV
Markdown (Obsidian)
```

### cambios — `/cambios`

- **Captura**: [cambios-1280.png](../capturas/revision-2026-11/cambios-1280.png) (1280×900, 1462 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Cambios»
- **Encabezados**: Cambios · Propuestas y cambios · Qué ha cambiado · Qué depende de lo que ha cambiado · Resúmenes del material
- **Estados**: vacío 0, cargando 0, error 0, avisos 1

Texto visible de `main` (innerText tal cual):

```text
Cambios

Cuando llega una versión nueva de un material, OpoFuente compara las dos y dice qué depende de lo que ha cambiado. Nada se aplica hasta que lo confirmas, y lo que cambió de texto no decide por ti si algo sigue valiendo.

Propuestas y cambios
Apuntes sinteticos E2E-08 mw8f42ou: ebd7e72b-c552-43be-8478-5a77abb7d121 → 7ff4f5a2-89eb-4776-a951-92fb7a59b108
!
propuesto, sin aplicar
2026-11-08 · 1 cambiada(s) · 0 nueva(s) · 0 quitada(s) · 2 sin cambios · 0 derivado(s) afectado(s), 0 por revisar
Temario sintetico E2E-04 mw8f3g57: 44b67782-bab1-4546-932c-54dd5055c994 → 9cecede0-e6d9-4e62-86bb-4d12cc149778
!
propuesto, sin aplicar
2026-11-08 · 1 cambiada(s) · 0 nueva(s) · 0 quitada(s) · 1 sin cambios · 0 derivado(s) afectado(s), 0 por revisar
Plazos E2E-09 mw8f32g4: 5d814639-3ea7-49c3-bd89-797b6b8359a2 → 88f5b83e-6d6e-4f18-a056-e7d04060ddfb
·
confirmado
2026-11-08 · 1 cambiada(s) · 0 nueva(s) · 0 quitada(s) · 1 sin cambios · 1 derivado(s) afectado(s), 1 por revisar
Qué ha cambiado

Apuntes sinteticos E2E-08 mw8f42ou

SECCIÓN	QUÉ LE HA PASADO	ANTES	DESPUÉS
sección 1	
✔
sin cambios
	
Apuntes sinteticos E2E-08 mw8f42ou
	
Apuntes sinteticos E2E-08 mw8f42ou

sección 2	
!
con el texto cambiado
	
El plazo del procedimiento del expedientemw8f42ou es de diez dias habiles.
	
El plazo del procedimiento del registromw8f42ou es de diez dias habiles.

sección 3	
✔
sin cambios
	
La solicitud se presenta en el registro electronico comun.
	
La solicitud se presenta en el registro electronico comun.
Qué depende de lo que ha cambiado

Ningún derivado depende de las secciones que han cambiado: confirmar el cambio no obliga a revisar nada de lo que hay guardado.

OpoFuente describe qué texto cambió y qué depende de él. No decide si una norma sigue vigente, si algo deja de ser válido ni qué hay que hacer con el material: eso lo decide una persona.

Confirmar el cambio
Descartar la propuesta
Confirmar acepta la versión nueva, sustituye la anterior (que se conserva como histórica) y marca los derivados afectados. Descartar no toca nada.
Resúmenes del material

Los resúmenes son extractivos: texto del corpus con su cita, sin modelo. Un resumen depende de las secciones de las que sale, así que un cambio en ellas lo deja pendiente de revisar. Se crean desde el lector de la Biblioteca, en la sección que interesa.

No hay ningún resumen pendiente de revisar. Si un cambio afecta a uno, aparecerá aquí con su motivo.
```

### revision — `/revision`

- **Captura**: [revision-1280.png](../capturas/revision-2026-11/revision-1280.png) (1280×900, 15443 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Revisión»
- **Encabezados**: Revisión · Esto son propuestas, no hechos · Cola de revisión · Clasificación de este material · Propuestas · Cobertura del programa
- **Estados**: vacío 0, cargando 0, error 0, avisos 1

Texto visible de `main` (innerText tal cual):

```text
Revisión

Revisa lo que la aplicación propone sobre tu material: qué eje, qué valor, con qué confianza y con qué evidencia. Decidir aquí es lo que convierte una propuesta en algo aceptado.

Esto son propuestas, no hechos

Nada de esta pantalla se aplicó por su cuenta: cada propuesta espera tu decisión. Lo que aparece como aplicada provisionalmente lo propuso el motor por su banda de confianza, es reversible y lo puedes confirmar, rechazar o deshacer. Las propuestas de autoridad y derechos no se aplican solas nunca, ni con confianza alta: requieren tu confirmación.

Aceptar no convierte el material en oficial: solo lo aprueba para tu corpus (07_UI-UX §12).

Cola de revisión
Buscar propuestas ahora
Una pasada de clasificación no cambia nada por sí sola: solo propone.

9 grupos con 51 propuestas pendientes. Marca los que quieras decidir juntos: el lote se puede completar o dejar fuera filas concretas antes de confirmarlo.

Grupos de revisión
GRUPO	SUJETO	EJE	PROPUESTAS	CONFIANZA	AVISO
 Publicación oficial A	material	Autoridad	10	90 %	
!
requiere tu confirmación

 Solo uso privado private_use_only	material	Derechos	6	60 % – 90 %	
!
requiere tu confirmación

 Temario o programa curriculum	material	Tipo de documento	4	70 %	—
 Bloque 1. La Constitución Española de 1978. 4.1	material	Tema del programa	4	68 %	—
 TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	material	Tema del programa	10	60 %	—
 Normas de actuación del celador en los quirófanos. Normas de higiene. La Esterilización. 10	material	Tema del programa	2	55 %	—
 TÍTULO II. Del Procedimiento. 4.2.2	material	Tema del programa	8	55 %	—
 Apuntes personales personal_notes	material	Tipo de documento	6	40 %	—
 Material de la comunidad community_material	texto extraído	Tipo de documento	1	40 %	—
Clasificación de este material

Apuntes TAI/tema-01.txt (material)

Lo que consta de este material, eje por eje
EJE	VALOR	ORIGEN DE LA ETIQUETA
Tipo de documento	sin clasificar	—
Oposición	sin clasificar	—
Tema del programa	sin clasificar	—
Autoridad	sin clasificar	—
Derechos	sin clasificar	—
Propuestas
51 propuestas esperando tu decisión
MATERIAL	EJE	VALOR PROPUESTO	CONFIANZA	EVIDENCIA	ALTERNATIVAS	ESTADO	DECISIÓN
Apuntes TAI/tema-01.txt (material)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

Apuntes TAI/Tema 3/resumen.txt (material)	Tema del programa	Normas de actuación del celador en los quirófanos. Normas de higiene. La Esterilización. 10	55 % 
!
confianza media
	
título del programa «DERECHO ADMINISTRATIVO»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

Apuntes TAI/tema-01.txt (texto extraído)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

tema-02.txt (texto extraído)	Tema del programa	Normas de actuación del celador en los quirófanos. Normas de higiene. La Esterilización. 10	55 % 
!
confianza media
	
título del programa «DERECHO ADMINISTRATIVO»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

Apuntes del tema 1 (material)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

Apuntes del tema 1 (texto extraído)	Tipo de documento	Apuntes personales personal_notes	40 % 
·
confianza baja
	
origen: texto pegado por el usuario
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

Apuntes del tema 1 (material)	Tipo de documento	Apuntes personales personal_notes	40 % 
·
confianza baja
	
origen: texto pegado por el usuario
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

Apuntes del tema 1 (texto extraído)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

tema-01.pdf (texto extraído)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

tema-01-copia.pdf (material)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-08-mw8f42ou-v2.txt (texto extraído)	Tema del programa	TÍTULO II. Del Procedimiento. 4.2.2	55 % 
!
confianza media
	
título del programa «TÍTULO II. Del Procedimiento.»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.2.2
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-08-mw8f42ou-v2.txt (material)	Tema del programa	TÍTULO II. Del Procedimiento. 4.2.2	55 % 
!
confianza media
	
título del programa «TÍTULO II. Del Procedimiento.»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.2.2
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-08-mw8f42ou-v1.txt (material)	Tema del programa	TÍTULO II. Del Procedimiento. 4.2.2	55 % 
!
confianza media
	
título del programa «TÍTULO II. Del Procedimiento.»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.2.2
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-08-mw8f42ou-v1.txt (texto extraído)	Tema del programa	TÍTULO II. Del Procedimiento. 4.2.2	55 % 
!
confianza media
	
título del programa «TÍTULO II. Del Procedimiento.»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.2.2
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

revision-1-mw8f3vfd-286.txt (texto extraído)	Tema del programa	Bloque 1. La Constitución Española de 1978. 4.1	68 % 
!
confianza media
	
título del programa «Bloque 1. La Constitución Española de 1978.»
	
1.1.10 63 %
I.1 57 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.1
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

revision-1-mw8f3vfd-286.txt (texto extraído)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-1-mw8f3vfd-286.txt (material)	Tema del programa	Bloque 1. La Constitución Española de 1978. 4.1	68 % 
!
confianza media
	
título del programa «Bloque 1. La Constitución Española de 1978.»
	
1.1.10 63 %
I.1 57 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.1
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

revision-3-mw8f3vfd-286.txt (texto extraído)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-3-mw8f3vfd-286.txt (texto extraído)	Derechos 
!
requiere tu confirmación
	Solo uso privado private_use_only	60 % 
!
confianza media
	
«uso privado»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-2-mw8f3vfd-286.txt (material)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-1-mw8f3vfd-286.txt (texto extraído)	Derechos 
!
requiere tu confirmación
	Solo uso privado private_use_only	90 % 
!
confianza media
	
«uso privado»
«prohibida su reproducción»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-1-mw8f3vfd-286.txt (material)	Derechos 
!
requiere tu confirmación
	Solo uso privado private_use_only	90 % 
!
confianza media
	
«uso privado»
«prohibida su reproducción»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-3-mw8f3vfd-286.txt (material)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-2-mw8f3vfd-286.txt (texto extraído)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-3-mw8f3vfd-286.txt (texto extraído)	Tipo de documento	Material de la comunidad community_material	40 % 
·
confianza baja
	
«apuntes de»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-2-mw8f3vfd-286.txt (texto extraído)	Derechos 
!
requiere tu confirmación
	Solo uso privado private_use_only	60 % 
!
confianza media
	
«uso privado»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-2-mw8f3vfd-286.txt (material)	Derechos 
!
requiere tu confirmación
	Solo uso privado private_use_only	60 % 
!
confianza media
	
«uso privado»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-1-mw8f3vfd-286.txt (material)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

revision-3-mw8f3vfd-286.txt (material)	Derechos 
!
requiere tu confirmación
	Solo uso privado private_use_only	60 % 
!
confianza media
	
«uso privado»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

temario-mw8f3r2c.txt (material)	Tema del programa	Bloque 1. La Constitución Española de 1978. 4.1	68 % 
!
confianza media
	
título del programa «Bloque 1. La Constitución Española de 1978.»
	
4.2.2 55 %
25 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.1
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

temario-mw8f3r2c.txt (texto extraído)	Tema del programa	Bloque 1. La Constitución Española de 1978. 4.1	68 % 
!
confianza media
	
título del programa «Bloque 1. La Constitución Española de 1978.»
	
4.2.2 55 %
25 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.1
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-04-mw8f3g57-tema-v2.pdf (texto extraído)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-04-mw8f3g57-tema-v2.pdf (texto extraído)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-04-mw8f3g57-tema-v2.pdf (material)	Tipo de documento	Temario o programa curriculum	70 % 
!
confianza media
	
«temario oficial»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-04-mw8f3g57-tema-v2.pdf (material)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-04-mw8f3g57-tema-v2.pdf (material)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-04-mw8f3g57-tema-v2.pdf (texto extraído)	Tipo de documento	Temario o programa curriculum	70 % 
!
confianza media
	
«temario oficial»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-04-mw8f3g57-tema-copia.pdf (texto extraído)	Tipo de documento	Temario o programa curriculum	70 % 
!
confianza media
	
«temario oficial»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-04-mw8f3g57-tema.pdf (material)	Tipo de documento	Temario o programa curriculum	70 % 
!
confianza media
	
«temario oficial»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-04-mw8f3g57-tema-copia.pdf (texto extraído)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-04-mw8f3g57-tema-copia.pdf (texto extraído)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-04-mw8f3g57-tema.pdf (material)	Autoridad 
!
requiere tu confirmación
	Publicación oficial A	90 % 
!
confianza media
	
«Boletín Oficial del Estado»
«Resolución de …»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-04-mw8f3g57-tema.pdf (material)	Tema del programa	TÍTULO IV. De las disposiciones del procedimiento administrativo común. 10.1.5	60 % 
!
confianza media
	
título del programa «TÍTULO IV. De las disposiciones del procedimiento administrativo común.»
	
10.1 59 %
4.2.2 55 %
	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 10.1.5
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-09-mw8f32g4-v2.txt (material)	Tema del programa	TÍTULO II. Del Procedimiento. 4.2.2	55 % 
!
confianza media
	
título del programa «TÍTULO II. Del Procedimiento.»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.2.2
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-09-mw8f32g4-v2.txt (texto extraído)	Tipo de documento	Apuntes personales personal_notes	40 % 
·
confianza baja
	
origen: texto pegado por el usuario
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-09-mw8f32g4-v2.txt (texto extraído)	Tema del programa	TÍTULO II. Del Procedimiento. 4.2.2	55 % 
!
confianza media
	
título del programa «TÍTULO II. Del Procedimiento.»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.2.2
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-09-mw8f32g4-v2.txt (material)	Tipo de documento	Apuntes personales personal_notes	40 % 
·
confianza baja
	
origen: texto pegado por el usuario
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-09-mw8f32g4-v1.txt (texto extraído)	Tipo de documento	Apuntes personales personal_notes	40 % 
·
confianza baja
	
origen: texto pegado por el usuario
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-09-mw8f32g4-v1.txt (texto extraído)	Tema del programa	TÍTULO II. Del Procedimiento. 4.2.2	55 % 
!
confianza media
	
título del programa «TÍTULO II. Del Procedimiento.»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.2.2
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido

e2e-09-mw8f32g4-v1.txt (material)	Tipo de documento	Apuntes personales personal_notes	40 % 
·
confianza baja
	
origen: texto pegado por el usuario
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar

e2e-09-mw8f32g4-v1.txt (material)	Tema del programa	TÍTULO II. Del Procedimiento. 4.2.2	55 % 
!
confianza media
	
título del programa «TÍTULO II. Del Procedimiento.»
	—	
!
pendiente de tu decisión
	
Aceptar
Rechazar
Corregir el tema
Sin corrección: se propone 4.2.2
I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
I.2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
I.3 · El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
I.4 · El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
I.5 · Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
I.6 · La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
I.7 · La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
I.8 · Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
I.9 · Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
II.1 · Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
II.2 · Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
II.3 · Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
II.4 · Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
II.5 · Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
III.1 · Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
III.2 · Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
III.3 · Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
III.4 · Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
III.5 · Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
III.6 · Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
III.7 · Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
III.8 · Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
III.9 · Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
IV.1 · Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
IV.2 · Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
IV.3 · Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
IV.4 · Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
IV.5 · Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
IV.6 · Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
IV.7 · El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
IV.8 · Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
IV.9 · Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
IV.10 · Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
Aceptar corregido
Cobertura del programa

Se cuenta lo que cubre cada nodo con su subárbol. La cobertura provisional es lo aplicado por el motor sin confirmar; la aceptada es lo que has confirmado tú sobre texto utilizable. Nunca se suman.

▾
I
Organización del Estado y Administración electrónica
bloque
1
La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
tema
2
Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
tema
3
El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
tema
4
El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
tema
5
Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
tema
6
La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
tema
7
La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
tema
8
Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
tema
9
Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
tema
▾
II
Tecnología básica
bloque
1
Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
tema
2
Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
tema
3
Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
tema
4
Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
tema
5
Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
tema
▾
III
Desarrollo de sistemas
bloque
1
Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
tema
2
Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
tema
3
Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
tema
4
Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
tema
5
Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
tema
6
Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
tema
7
Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
tema
8
Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
tema
9
Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
tema
▾
IV
Sistemas y comunicaciones
bloque
1
Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
tema
2
Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
tema
3
Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
tema
4
Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
tema
5
Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
tema
6
Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
tema
7
El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
tema
8
Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
tema
9
Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
tema
10
Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
tema

Elige un bloque o un tema para ver su cobertura.
```

### buscar — `/buscar?q=plazo`

- **Captura**: [buscar-1280.png](../capturas/revision-2026-11/buscar-1280.png) (1280×900, 1418 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Buscar y preguntar»
- **Encabezados**: Buscar y preguntar · Búsqueda · Resultados · Lo que esta búsqueda no puede hacer · Fuera del corpus
- **Estados**: vacío 0, cargando 0, error 0, avisos 1

Texto visible de `main` (innerText tal cual):

```text
Buscar y preguntar

La búsqueda va sobre el material publicado y vigente. Preguntar añade una respuesta con sus citas: cada afirmación dice de qué fragmento sale y, si el corpus no la sostiene, lo dice.

Búsqueda
Qué buscas
Versiones
solo lo vigente
incluir también el histórico
Buscar
Respuesta
breve
explicada
comparando fuentes
Preguntar
 Incluir mi material privado
Preguntar guarda la consulta y su recuperación: la respuesta queda auditable.
Resultados

4 fragmentos · solo versiones vigentes · recuperación lexical · corpus 18-2026-11-08 22:42:44.669074-4

Lo que esta búsqueda no puede hacer
sin proveedor de embeddings: la búsqueda ha sido solo léxica (FTS5)
Fuera del corpus
«Plazos E2E-09 mw8f32g4»: la versión está en estado «superseded»
«Apuntes sinteticos E2E-08 mw8f42ou»: la versión está en estado «superseded»

Plazos E2E-09 mw8f32g4 
✔
accepted
 coincide en: plazo

sección 1 · Plazos E2E-09 mw8f32g4 · accepted
Tema de plazos mw8f32g4
Abrir en la Biblioteca

Plazos E2E-09 mw8f32g4 
✔
accepted
 coincide en: plazo

sección 2 · Plazos E2E-09 mw8f32g4 · accepted
El plazo del procedimiento es de veinte dias habiles.
Abrir en la Biblioteca

Apuntes sinteticos E2E-08 mw8f42ou 
✔
accepted
 coincide en: plazo

sección 2 · Apuntes sinteticos E2E-08 mw8f42ou · accepted
El plazo del procedimiento del registromw8f42ou es de diez dias habiles.
Abrir en la Biblioteca

Temario E2E preguntas mw8f3r2c 
✔
accepted
 coincide en: plazo

sección 3 · Temario E2E preguntas mw8f3r2c · accepted
2. El plazo de alegaciones del procedimiento es de:
a) Diez dias habiles
b) Veinte dias habiles
c) Un mes
Abrir en la Biblioteca
```

### ajustes — `/ajustes`

- **Captura**: [ajustes-1280.png](../capturas/revision-2026-11/ajustes-1280.png) (1280×900, 3333 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Ajustes»
- **Encabezados**: Ajustes · Datos y disco · Uso del almacén · Capacidades instaladas · Privacidad: a dónde sale tu contenido · Copia y restauración · Índice de búsqueda · Exportación · Diagnóstico y registros saneados · Límites en vigor
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Ajustes

Todo lo que la aplicación hace con tus datos, dicho sin adornos: dónde los guarda, qué capacidades hay de verdad, a dónde sale el contenido si configuras un proveedor, y cómo se copia y se restaura.

Datos y disco
Versión
0.0.0 · esquema 0023_block_practice
Ruta de datos
F:\Proyectos\opofuente\.e2e-data
Base de datos
F:\Proyectos\opofuente\.e2e-data\opofuente.sqlite3
Disco
148.0 GB libres de 208.3 GB
Servidor
127.0.0.1:8765 · registro WARNING

Los ajustes se editan en .env y en las variables de entorno: esta pantalla no escribe configuración, la lee y la explica.

Uso del almacén
Total 182.3 KB · recuperable 0 B
ÁREA	FICHEROS	TAMAÑO
Material copiado (por contenido)	16	5.2 KB
Texto extraído y representaciones	30	9.0 KB
Copias de seguridad	1	167.0 KB
Exportaciones generadas	1	1.1 KB
Registros	1	0 B

Aquí no se borra nada solo: cada bloque de abajo enseña lo que se puede retirar y su motivo, y hay que confirmarlo.

Capacidades instaladas
Capacidades de esta instalación
CAPACIDAD	ESTADO	QUÉ SIGNIFICA
OCR (Tesseract)	
!
configurado sin verificar
	Binario presente, pero la aplicación no lo llama: el OCR no está implementado y una imagen se queda pendiente con su aviso. Declararlo evita creer que un PDF escaneado se está leyendo.
Modelo de lenguaje	
·
desactivado
	Sin proveedor: las respuestas se componen del propio corpus (extractivas) y citan cada afirmación. Un modelo de lenguaje llegaría con la deuda DEBT-014.
Embeddings	
·
desactivado
	Sin proveedor de embeddings decidido: la búsqueda es literal (FTS5) y cada respuesta lo declara como degradación (DEBT-014).
Búsqueda literal (FTS5)	
✔
operativo
	Índice léxico comprobado: tabla externa sobre evidence_spans, ordenada por bm25, con los disparadores que la mantienen al día; se rehace cuando haga falta sin salir de SQLite.
Almacén de originales por SHA-256	
✔
operativo
	Copia inmutable por contenido en <datos>/artifacts/sha256/ab/cd/<hash>. Dos ficheros idénticos comparten un artefacto y conservan dos orígenes.
Cola de trabajos local	
✔
operativo
	Cola persistida en SQLite con lease, trabajada por este proceso; sin Redis ni Celery. Cerrar la pestaña no cancela el trabajo.
Índice vectorial local	
×
no disponible
	Sin proveedor de embeddings no hay vectores que indexar: la búsqueda del corpus es literal (FTS5) sobre el texto extraído (DEBT-014).
Privacidad: a dónde sale tu contenido

Se calcula sobre la dirección real de cada proveedor, no sobre su nombre. «No se puede determinar» cuenta como que sí sale: es la respuesta conservadora.

Modelo de lenguaje
✔
sin proveedor
 el modelo de lenguaje no está configurado: no se envía nada
Embeddings
✔
sin proveedor
 el proveedor de embeddings no está configurado: no se envía nada
Clave del proveedor
no hay clave configurada
Copia y restauración
Nota de la copia (opcional)
Hacer una copia ahora
Copias de seguridad
COPIA	FECHA	TAMAÑO	SE PUEDE RESTAURAR	ACCIONES
20261108-224245-fd6cd3

copia de E2E-10

	2026-11-08 22:42:45	167.0 KB	
✔
sí
 la copia está en la revisión de esquema actual (0023_block_practice)	Verificar Previsualizar restauración
Índice de búsqueda

✔
completo
 el índice está completo (18 fragmentos)

Rehacer el índice

El índice es derivado: el texto de las evidencias es la verdad. Rehacerlo no puede perder nada y sirve para reparar un índice que se haya quedado atrás.

Exportación

Las exportaciones (Markdown/Obsidian y Anki CSV) se hacen desde Errores, junto a la cola de repaso, porque es ahí donde se elige qué se lleva.

Diagnóstico y registros saneados
Preparar el diagnóstico en texto

El diagnóstico no lleva contenido, ni claves, ni rutas completas: las rutas van abreviadas y el registro pasa por el saneado de secretos. Es lo que se puede pegar en una incidencia.

Última generación: 2026-11-09 16:09:34 · 0 línea(s) de registro

artifacts: 16
artifact_origins: 20
document_versions: 7
representations: 15
jobs: 42
jobs_pending: 0
evidence_spans: 18
questions: 132
study_sessions: 11
rag_queries: 2
learning_errors: 2
change_sets: 3
Límites en vigor
Tamaño por fichero
512.0 MB
Entradas por lote
50000
Descarga por URL
64.0 MB · 5 redirección(es)
Texto pegado
4.0 MB
ZIP
2000 entradas · 1.0 GB · ratio 200 · profundidad 1
PDF
2000 páginas
Worker
sondeo cada 1 s · lease 60 s
```

### no-encontrada — `/seccion-que-no-existe`

- **Captura**: [no-encontrada-1280.png](../capturas/revision-2026-11/no-encontrada-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Página no encontrada»
- **Encabezados**: Página no encontrada
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Página no encontrada

La dirección solicitada no corresponde a ninguna sección de OpoFuente.

Volver a Inicio
```

### temario-tema — `/temario/ec996939-7d8d-4803-9d73-eff38cf0df23`

- **Captura**: [temario-tema-1280.png](../capturas/revision-2026-11/temario-tema-1280.png) (1280×900, 1357 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.»
- **Encabezados**: La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey. · Apuntes · Material del tema · Preguntas · En qué convocatorias aparece
- **Estados**: vacío 1, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Temario
› Organización del Estado y Administración electrónica
La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.

I.1 · Resolución de 18 de diciembre de 2025, de la Secretaría de Estado de Función Pública, por la que se convocan procesos selectivos para el ingreso libre en el Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado (código 1188)

Apuntes

Este tema aún no tiene apuntes

Cuando haya texto para este tema aparecerá aquí.

Material del tema
Temario sintetico E2E-04 mw8f3g57
Documento
Marcar como estudiado
Preguntas

2 preguntas en el banco

Una respuesta

La Constitucion se aprobo en

Ver en el banco

Una respuesta

El DNI electronico sirve para

Ver en el banco

En qué convocatorias aparece

Este tema pertenece al programa publicado de una convocatoria.

Publicación
22 de diciembre de 2025
Fuente
BOE-A-2025-26262 · ANEXO V
Siguiente
2 · Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
```

### temario-tema-practicar — `/temario/ec996939-7d8d-4803-9d73-eff38cf0df23/practicar`

- **Captura**: [temario-tema-practicar-1280.png](../capturas/revision-2026-11/temario-tema-practicar-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Práctica libre del bloque»
- **Encabezados**: Práctica libre del bloque · Preguntas del bloque
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Temario
›
La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
Práctica libre del bloque

I.1 · La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.

Preguntas del bloque

Preguntas aceptadas del banco catalogadas en los temas de este bloque. Puedes abrirlas en su ficha o empezar una práctica del bloque: sin reservas ni tiempo y con la corrección de la convocatoria.

Cuántas preguntas
10
20
50
Todas
Reservas
Ninguna
1
2
Tiempo máximo
Sin tiempo
15 minutos
30 minutos
60 minutos
Empezar la práctica del bloque

2 preguntas

Una respuesta

La Constitucion se aprobo en

Repasar en el banco

Una respuesta

El DNI electronico sirve para

Repasar en el banco

Volver al temario
```

### temario-tema-convocatoria — `/temario/a8c67150-b1fd-49d3-b5f9-85ec8f26d1c5?convocatoria=f6b51232-7525-49f8-a19e-fdf74c5fbfad`

- **Captura**: [temario-tema-convocatoria-1280.png](../capturas/revision-2026-11/temario-tema-convocatoria-1280.png) (1280×900, 1309 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «La Constitución Española de 1978»
- **Encabezados**: La Constitución Española de 1978 · Apuntes · Preguntas · En qué convocatorias aparece · En esta convocatoria
- **Estados**: vacío 1, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Temario
› Administración y normativa
La Constitución Española de 1978

I.1 · Temario común de informática C1 · 13 convocatorias

Apuntes
estructura, derechos y deberes, principios rectores, organización del Estado, las Cortes, el Gobierno, el Poder Judicial, el Tribunal Constitucional y las CCAA.
Marcar como estudiado
Preguntas

Este tema aún no tiene preguntas

Cuando el banco tenga preguntas de este tema aparecerán aquí.

En qué convocatorias aparece
Técnico Especialista en Informática (C1) - resto provincias
Temario que se estudia

BOP CyL; estado en la fuente: VIGILAR (recurrente)

Bases oficiales
·
Convocatoria elegida

Técnico Especialista en Informática (C1) - SALAMANCA
Temario que se estudia

BOP CyL; estado en la fuente: CERRADO (baremo provisional 15/01/2026)

Bases oficiales
·
Ver particularidades

Resolución de 18 de diciembre de 2025, de la Secretaría de Estado de Función Pública, por la que se convocan procesos selectivos para el ingreso libre en el Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado (código 1188)
Temario que se estudia

ANEXO V, apartado 3

Bases oficiales
·
Ver particularidades

10 convocatorias por confirmar
En esta convocatoria

Sin particularidades: el tema se estudia tal y como está en el temario común.

Siguiente
2 · La Unión Europea
```

### biblioteca-documento — `/biblioteca?documento=159de869-bea9-4178-aa42-6b0ebf28888f`

- **Captura**: [biblioteca-documento-1280.png](../capturas/revision-2026-11/biblioteca-documento-1280.png) (1280×900, 2964 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Biblioteca»
- **Encabezados**: Biblioteca · Filtros · Colecciones · Documentos · Apuntes sinteticos E2E-08 mw8f42ou · Derechos restringidos: no se puede compartir · Ficha del documento · Secciones · sección 1 · Índice de evidencia citable de la versión · Colecciones del documento abierto
- **Estados**: vacío 0, cargando 0, error 0, avisos 1

Texto visible de `main` (innerText tal cual):

```text
Biblioteca

Tus documentos con sus versiones, sus derechos y su procedencia. Un documento privado no se hace público por promocionarlo, y una versión candidata no es la versión buena hasta que alguien la acepta.

Filtros
Tipo documental
cualquier tipo
Convocatoria
Programa o temario
Norma o reglamento
Documento técnico oficial
Temario privado
Notas personales
Examen oficial
Plantilla de respuestas
Banco de preguntas privado
Caso práctico
Fichas de repaso
Material de la comunidad
Sin clasificar
Ámbito
cualquier ámbito
público
privado tuyo
generado por la aplicación
Derechos
cualquier derecho
solo restringidos (no se pueden compartir)
solo con derechos revisados
Limpiar filtros

Tipo documental y ámbito los filtra el servidor. El de derechos se aplica sobre los documentos ya cargados, porque la API todavía no filtra por derechos: el recuento que se ve es el de esta pantalla, no el de toda la biblioteca.

Colecciones

Una colección agrupa material sin duplicarlo: el mismo documento puede estar en varias. El filtro se aplica en el servidor, así que lo que se ve son los documentos de la colección y no los que han quedado fuera de la página.

Todos los documentos
Coleccion E2E-04 mw8f3g57 
·
0 miembros
Nombre de la colección
Descripción (opcional)
Crear la colección
Documentos

4 de 4 documentos

4 documentos en la biblioteca
TÍTULO	TIPO	VERSIÓN ACTIVA	ÁMBITO Y AUTORIDAD	RECUENTOS	AVISOS	FICHA
Apuntes sinteticos E2E-08 mw8f42ou	Notas personales personal_notes	7ff4f5a2-89eb-4776-a951-92fb7a59b108 
✔
aceptada
	privado tuyo sin autoridad declarada	2 versiones · 0 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha abierta ahora
Plazos E2E-09 mw8f32g4	Programa o temario curriculum	88f5b83e-6d6e-4f18-a056-e7d04060ddfb 
✔
aceptada
	privado tuyo sin autoridad declarada	2 versiones · 0 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
Temario E2E preguntas mw8f3r2c	Programa o temario curriculum	81a3f987-b84c-4c55-811d-c09bf32422b2 
✔
aceptada
	privado tuyo sin autoridad declarada	1 versiones · 0 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
Temario sintetico E2E-04 mw8f3g57	Programa o temario curriculum	44b67782-bab1-4546-932c-54dd5055c994 
✔
aceptada
	privado tuyo sin autoridad declarada	2 versiones · 3 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
Apuntes sinteticos E2E-08 mw8f42ou

Notas personales · personal_notes

Volver a la lista

Versión activa
7ff4f5a2-89eb-4776-a951-92fb7a59b108 
✔
aceptada
Autoridad
sin autoridad declarada
Ámbito
privado tuyo no público
Vigencia
sin fecha de vigencia declarada
Procedencia
artefacto 7795d65d-f74f-4efd-a46f-e71adcb5649f
Derechos
no constan: se tratan como desconocidos y restringidos
Derechos restringidos: no se puede compartir

Esta versión no trae ningún registro de derechos. Los derechos desconocidos se tratan como restringidos: no se puede compartir ni publicar el documento, y lo que se cite de él conserva su atribución y su procedencia.

Ficha del documento
Lector
Estructura
Asignaciones
Versiones y diff
Metadatos

Se lee el texto extraído de la versión «7ff4f5a2-89eb-4776-a951-92fb7a59b108» y, al lado, la página del original de la que sale. El original no se modifica ni se muestra aquí. Esta versión no tiene URL oficial registrada.

Secciones
sección 1
sin página
sección 2
sin página
sección 3
sin página
sección 1

sin página del original · sin URL oficial: la página del original no se puede abrir · abrir el fichero original que se copió

Crear un resumen de esta sección
Extractivo: junta el texto de los fragmentos con su cita, sin modelo. El resumen dependerá de esta sección y quedará pendiente de revisar si cambia (S11).

Apuntes sinteticos E2E-08 mw8f42ou

sección 1 · calidad good · índice: pending

Copiar cita
Índice de evidencia citable de la versión
sección 1 
Copiar cita
sección 2 
Copiar cita
sección 3 
Copiar cita
Colecciones del documento abierto
Añadir a una colección
elige una colección
Coleccion E2E-04 mw8f3g57
Añadir a la colección

Se añade la versión activa del documento. Añadir dos veces lo mismo no duplica el miembro, y el documento puede estar en varias colecciones a la vez.
```

### biblioteca-documento-versiones — `/biblioteca?documento=159de869-bea9-4178-aa42-6b0ebf28888f`

- **Captura**: [biblioteca-documento-versiones-1280.png](../capturas/revision-2026-11/biblioteca-documento-versiones-1280.png) (1280×900, 3219 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Biblioteca»
- **Encabezados**: Biblioteca · Filtros · Colecciones · Documentos · Apuntes sinteticos E2E-08 mw8f42ou · Derechos restringidos: no se puede compartir · Ficha del documento · Comparar dos versiones (diff) · Colecciones del documento abierto
- **Estados**: vacío 0, cargando 0, error 0, avisos 1

Texto visible de `main` (innerText tal cual):

```text
Biblioteca

Tus documentos con sus versiones, sus derechos y su procedencia. Un documento privado no se hace público por promocionarlo, y una versión candidata no es la versión buena hasta que alguien la acepta.

Filtros
Tipo documental
cualquier tipo
Convocatoria
Programa o temario
Norma o reglamento
Documento técnico oficial
Temario privado
Notas personales
Examen oficial
Plantilla de respuestas
Banco de preguntas privado
Caso práctico
Fichas de repaso
Material de la comunidad
Sin clasificar
Ámbito
cualquier ámbito
público
privado tuyo
generado por la aplicación
Derechos
cualquier derecho
solo restringidos (no se pueden compartir)
solo con derechos revisados
Limpiar filtros

Tipo documental y ámbito los filtra el servidor. El de derechos se aplica sobre los documentos ya cargados, porque la API todavía no filtra por derechos: el recuento que se ve es el de esta pantalla, no el de toda la biblioteca.

Colecciones

Una colección agrupa material sin duplicarlo: el mismo documento puede estar en varias. El filtro se aplica en el servidor, así que lo que se ve son los documentos de la colección y no los que han quedado fuera de la página.

Todos los documentos
Coleccion E2E-04 mw8f3g57 
·
0 miembros
Nombre de la colección
Descripción (opcional)
Crear la colección
Documentos

4 de 4 documentos

4 documentos en la biblioteca
TÍTULO	TIPO	VERSIÓN ACTIVA	ÁMBITO Y AUTORIDAD	RECUENTOS	AVISOS	FICHA
Apuntes sinteticos E2E-08 mw8f42ou	Notas personales personal_notes	7ff4f5a2-89eb-4776-a951-92fb7a59b108 
✔
aceptada
	privado tuyo sin autoridad declarada	2 versiones · 0 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha abierta ahora
Plazos E2E-09 mw8f32g4	Programa o temario curriculum	88f5b83e-6d6e-4f18-a056-e7d04060ddfb 
✔
aceptada
	privado tuyo sin autoridad declarada	2 versiones · 0 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
Temario E2E preguntas mw8f3r2c	Programa o temario curriculum	81a3f987-b84c-4c55-811d-c09bf32422b2 
✔
aceptada
	privado tuyo sin autoridad declarada	1 versiones · 0 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
Temario sintetico E2E-04 mw8f3g57	Programa o temario curriculum	44b67782-bab1-4546-932c-54dd5055c994 
✔
aceptada
	privado tuyo sin autoridad declarada	2 versiones · 3 mapeos de programa	

×
derechos restringidos
 no constan derechos: se tratan como desconocidos y restringidos.

	Abrir la ficha
Apuntes sinteticos E2E-08 mw8f42ou

Notas personales · personal_notes

Volver a la lista

Versión activa
7ff4f5a2-89eb-4776-a951-92fb7a59b108 
✔
aceptada
Autoridad
sin autoridad declarada
Ámbito
privado tuyo no público
Vigencia
sin fecha de vigencia declarada
Procedencia
artefacto 7795d65d-f74f-4efd-a46f-e71adcb5649f
Derechos
no constan: se tratan como desconocidos y restringidos
Derechos restringidos: no se puede compartir

Esta versión no trae ningún registro de derechos. Los derechos desconocidos se tratan como restringidos: no se puede compartir ni publicar el documento, y lo que se cite de él conserva su atribución y su procedencia.

Ficha del documento
Lector
Estructura
Asignaciones
Versiones y diff
Metadatos
2 versiones del documento (la antigua no se borra)
VERSIÓN	ESTADO	FECHAS	CONTENIDO	SUSTITUYE A	ACCIONES
ebd7e72b-c552-43be-8478-5a77abb7d121	
·
sustituida
	publicada: no consta
recuperada: no consta
vigente desde: no consta	3 secciones · 3 evidencias
hash: e1a7cb7fc85843748af2493848e399faf2b5e163401beff1cc5a52b806fe391e

×
derechos restringidos: no se puede compartir
	a ninguna	sin acciones: el estado no lo admite
7ff4f5a2-89eb-4776-a951-92fb7a59b108 
✔
versión activa y aceptada
	
✔
aceptada
	publicada: no consta
recuperada: no consta
vigente desde: no consta	3 secciones · 3 evidencias
hash: fa2a60dc2732e5e4a55ba3019fe1cb100ba78e5eb30b33a1c2d502d7eb831e30

×
derechos restringidos: no se puede compartir
	ebd7e72b-c552-43be-8478-5a77abb7d121	Marcar sustitución…
Comparar dos versiones (diff)
Versión anterior
ebd7e72b-c552-43be-8478-5a77abb7d121 · sustituida
7ff4f5a2-89eb-4776-a951-92fb7a59b108 · aceptada
Versión nueva
ebd7e72b-c552-43be-8478-5a77abb7d121 · sustituida
7ff4f5a2-89eb-4776-a951-92fb7a59b108 · aceptada

Nuevas: 0 · quitadas: 0 · con el texto cambiado: 1 · sin cambios: 2 (sobre 3 secciones comparadas, de la más antigua a la más nueva). Comparar no fusiona nada: no se ha modificado ninguna versión.

Comparación de «ebd7e72b-c552-43be-8478-5a77abb7d121» con «7ff4f5a2-89eb-4776-a951-92fb7a59b108», sección a sección
SECCIÓN	QUÉ PASÓ	ANTES	DESPUÉS
sección 1	
✔
sin cambios
	Apuntes sinteticos E2E-08 mw8f42ou	Apuntes sinteticos E2E-08 mw8f42ou
sección 2	
!
texto cambiado
	El plazo del procedimiento del expedientemw8f42ou es de diez dias habiles.	El plazo del procedimiento del registromw8f42ou es de diez dias habiles.
sección 3	
✔
sin cambios
	La solicitud se presenta en el registro electronico comun.	La solicitud se presenta en el registro electronico comun.
Colecciones del documento abierto
Añadir a una colección
elige una colección
Coleccion E2E-04 mw8f3g57
Añadir a la colección

Se añade la versión activa del documento. Añadir dos veces lo mismo no duplica el miembro, y el documento puede estar en varias colecciones a la vez.
```

### preguntas-conjunto — `/preguntas?conjunto=72482c3a-cf15-438f-9435-1b2b61732164&pregunta=0c380199-ac3e-4237-a406-d9066f142548`

- **Captura**: [preguntas-conjunto-1280.png](../capturas/revision-2026-11/preguntas-conjunto-1280.png) (1280×900, 6496 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Preguntas»
- **Encabezados**: Preguntas · Conjunto · Banco · Pregunta 1 · Composición · Corrección local · Reportar una incidencia
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Preguntas

El banco de preguntas de una oposición: lo que se importa, lo que se revisa y la plantilla con la que se corrige. Importar no publica nada: una pregunta privada sigue siendo privada.

Conjunto
Conjunto abierto
Practica E2E 1794177785174-455876 · banco privado
Examen E2E 1794177782189-482891 · banco privado
Practica E2E 1794177778314-129160 · banco privado
Practica E2E 1794177775724-465317 · banco privado
Practica E2E 1794177771614-355764 · banco privado
Practica E2E 1794177768627-208028 · banco privado
Importacion E2E 1794177748510-206080 · banco privado
Importacion E2E 1794177747132-551696 · banco privado
Importacion E2E 1794177745877-933138 · banco privado
Importacion E2E 1794177745204-045898 · banco privado
JSON E2E 1794177741138-762711 · banco privado
Clave E2E 1794177725802-594034 · banco privado
Errores E2E mw8f38rv-cola · banco privado
Errores E2E mw8f36ev-cola · banco privado
85 preguntas (0 incompletas · 5 reservas) · 1 plantilla 
·
borrador
 
✔
con clave activa
Crear un conjunto
Banco
Preguntas
Importar
Plantillas
Estado
todos
incompleta
completa
verificada
en conflicto
anulada
sustituida
Origen
todos
OFICIAL
PRIVADA
GENERADA
 solo reservas
1–85 de 85 preguntas del conjunto
Nº	ENUNCIADO	ORIGEN	TIPO	CLAVE	ESTADO
1	El supuesto 1 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

2	El supuesto 2 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

3	El supuesto 3 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

4	El supuesto 4 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

5	El supuesto 5 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

6	El supuesto 6 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

7	El supuesto 7 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

8	El supuesto 8 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

9	El supuesto 9 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

10	El supuesto 10 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

11	El supuesto 11 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

12	El supuesto 12 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

13	El supuesto 13 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

14	El supuesto 14 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

15	El supuesto 15 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

16	El supuesto 16 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

17	El supuesto 17 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

18	El supuesto 18 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

19	El supuesto 19 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

20	El supuesto 20 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

21	El supuesto 21 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

22	El supuesto 22 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

23	El supuesto 23 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

24	El supuesto 24 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

25	El supuesto 25 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

26	El supuesto 26 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

27	El supuesto 27 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

28	El supuesto 28 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

29	El supuesto 29 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

30	El supuesto 30 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

31	El supuesto 31 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

32	El supuesto 32 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

33	El supuesto 33 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

34	El supuesto 34 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

35	El supuesto 35 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

36	El supuesto 36 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

37	El supuesto 37 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

38	El supuesto 38 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

39	El supuesto 39 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

40	El supuesto 40 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

41	El supuesto 41 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

42	El supuesto 42 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

43	El supuesto 43 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

44	El supuesto 44 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

45	El supuesto 45 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

46	El supuesto 46 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

47	El supuesto 47 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

48	El supuesto 48 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

49	El supuesto 49 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

50	El supuesto 50 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

51	El supuesto 51 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

52	El supuesto 52 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

53	El supuesto 53 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

54	El supuesto 54 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

55	El supuesto 55 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

56	El supuesto 56 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

57	El supuesto 57 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

58	El supuesto 58 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

59	El supuesto 59 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

60	El supuesto 60 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

61	El supuesto 61 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

62	El supuesto 62 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

63	El supuesto 63 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

64	El supuesto 64 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

65	El supuesto 65 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

66	El supuesto 66 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

67	El supuesto 67 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

68	El supuesto 68 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

69	El supuesto 69 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

70	El supuesto 70 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

71	El supuesto 71 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

72	El supuesto 72 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

73	El supuesto 73 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

74	El supuesto 74 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

75	El supuesto 75 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

76	El supuesto 76 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

77	El supuesto 77 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

78	El supuesto 78 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

79	El supuesto 79 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

80	El supuesto 80 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

81 
·
reserva
	El supuesto 81 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

82 
·
reserva
	El supuesto 82 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

83 
·
reserva
	El supuesto 83 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

84 
·
reserva
	El supuesto 84 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa

85 
·
reserva
	El supuesto 85 se resuelve así:	
·
PRIVADA
	una respuesta	
✔
clave: a
	
·
completa
Pregunta 1

·
PRIVADA
·
completa
✔
con clave: a
una respuesta

Campos estructurados

El supuesto 1 se resuelve así:

A Opcion A 
✔
correcta
B Opcion B
Original

Así llegó el enunciado, antes de cualquier edición: no se reescribe nunca.

El supuesto 1 se resuelve así:

Esta pregunta no tiene documento de origen adjunto, así que no hay cita que abrir. La cita se crea al importar la pregunta desde un documento, desde la pestaña «Importar» de esta pantalla; no se rellena con una cita inventada.

Composición

Aquí se cambia cómo se presenta la pregunta (tipo, orden y si es reserva). El enunciado y las opciones de una pregunta oficial no se reescriben: se corrigen con corrección local.

Tipo de pregunta
una respuesta
marcar errores
verdadero o falso
referencia libre
Posición
 es reserva
Orden de reserva
Guardar composición
Corrección local

Cambiar una transcripción oficial crea una versión nueva con su motivo y deja la anterior como sustituida: el original sigue ahí y se puede comparar.

Motivo (obligatorio)
Enunciado corregido (opcional)
Opciones corregidas (una por línea, opcional)

Se guarda solo lo que cambies: con el enunciado en blanco y las opciones tal como están, la versión nueva conserva el texto y añade únicamente el motivo. El original no se toca en ningún caso.

Guardar corrección

El motivo es obligatorio: sin él no se puede corregir una transcripción oficial.

Reportar una incidencia
Qué pasa
ambigua
clave equivocada
errata
desactualizada
otra cosa
Detalle
Reportar
```

### preguntas-plantillas — `/preguntas`

- **Captura**: [preguntas-plantillas-1280.png](../capturas/revision-2026-11/preguntas-plantillas-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Preguntas»
- **Encabezados**: Preguntas · Conjunto · Banco · Sesiones ya corregidas
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Preguntas

El banco de preguntas de una oposición: lo que se importa, lo que se revisa y la plantilla con la que se corrige. Importar no publica nada: una pregunta privada sigue siendo privada.

Conjunto
Conjunto abierto
Practica E2E 1794177785174-455876 · banco privado
Examen E2E 1794177782189-482891 · banco privado
Practica E2E 1794177778314-129160 · banco privado
Practica E2E 1794177775724-465317 · banco privado
Practica E2E 1794177771614-355764 · banco privado
Practica E2E 1794177768627-208028 · banco privado
Importacion E2E 1794177748510-206080 · banco privado
Importacion E2E 1794177747132-551696 · banco privado
Importacion E2E 1794177745877-933138 · banco privado
Importacion E2E 1794177745204-045898 · banco privado
JSON E2E 1794177741138-762711 · banco privado
Clave E2E 1794177725802-594034 · banco privado
Errores E2E mw8f38rv-cola · banco privado
Errores E2E mw8f36ev-cola · banco privado
4 preguntas (0 incompletas · 0 reservas) · 1 plantilla 
·
borrador
 
✔
con clave activa
Crear un conjunto
Banco
Preguntas
Importar
Plantillas
1 plantillas del conjunto
VERSIÓN	ESTADO	DESENLACES	APROBADA	SUSTITUYE A	ACCIONES
v1	
✔
activa
	4 preguntas con desenlace	2026-11-08T22:43:05.872587	a ninguna	
Sesiones ya corregidas

✔
0 sesiones desactualizadas
 no hay sesiones terminadas de este conjunto: no hay nada que comparar
```

### inicio-cargando — `/`

- **Captura**: [inicio-cargando-1280.png](../capturas/revision-2026-11/inicio-cargando-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Inicio»
- **Encabezados**: Inicio · Siguiente tarea · Continuar estudiando · Acciones necesarias · Estado del programa · Actividad reciente · Estado del sistema · Capacidades · Almacenamiento
- **Estados**: vacío 0, cargando 8, error 0, avisos 1

Texto visible de `main` (innerText tal cual):

```text
Inicio

La siguiente tarea de hoy: el repaso vencido manda; si no hay nada vencido, se continúa la sesión que quedó a medias.

Siguiente tarea

Mirando lo que toca hoy…

Continuar estudiando

Cargando las sesiones…

Acciones necesarias

Mirando qué espera tu decisión…

Estado del programa

Cargando perfiles…

Actividad reciente

Mirando lo último que ha pasado…

Estado del sistema

Comprobando la base de datos…

Capacidades

Consultando capacidades…

Almacenamiento

Consultando la configuración…
```

### inicio-error — `/`

- **Captura**: [inicio-error-1280.png](../capturas/revision-2026-11/inicio-error-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Inicio»
- **Encabezados**: Inicio · Siguiente tarea · Continuar estudiando · Acciones necesarias · Estado del programa · Actividad reciente · Estado del sistema · Capacidades · Almacenamiento
- **Estados**: vacío 3, cargando 0, error 5, avisos 1

Texto visible de `main` (innerText tal cual):

```text
Inicio

La siguiente tarea de hoy: el repaso vencido manda; si no hay nada vencido, se continúa la sesión que quedó a medias.

Siguiente tarea

No se pudo leer la cola de repaso

La API no responde o la base de datos no está migrada.

Continuar estudiando

No se pudieron cargar las sesiones

La API no responde o la base de datos no está migrada.

Acciones necesarias

No se pudo leer lo que espera tu decisión

Fallo forzado para la captura

Reintentar
Estado del programa

No se pudieron cargar los perfiles

La API no responde o la base de datos no está migrada.

Comprueba el estado del sistema, más abajo.

Actividad reciente

No se pudo leer la actividad reciente

Fallo forzado para la captura

Reintentar
Estado del sistema

No se pudo comprobar el estado

Fallo forzado para la captura

Reintentar
Capacidades

No se pudieron consultar las capacidades

Fallo forzado para la captura

Reintentar
Almacenamiento

No se pudo leer la configuración

Fallo forzado para la captura

Reintentar
```

### preguntas-cargando — `/preguntas`

- **Captura**: [preguntas-cargando-1280.png](../capturas/revision-2026-11/preguntas-cargando-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Preguntas»
- **Encabezados**: Preguntas · Conjunto · Banco
- **Estados**: vacío 0, cargando 1, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Preguntas

El banco de preguntas de una oposición: lo que se importa, lo que se revisa y la plantilla con la que se corrige. Importar no publica nada: una pregunta privada sigue siendo privada.

Cargando los conjuntos…

Conjunto
Crear un conjunto
Banco
Preguntas
Importar
Plantillas

Elige o crea un conjunto para trabajar con sus preguntas.
```

### preguntas-error — `/preguntas`

- **Captura**: [preguntas-error-1280.png](../capturas/revision-2026-11/preguntas-error-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Preguntas»
- **Encabezados**: Preguntas · Conjunto · Banco
- **Estados**: vacío 0, cargando 0, error 1, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Preguntas

El banco de preguntas de una oposición: lo que se importa, lo que se revisa y la plantilla con la que se corrige. Importar no publica nada: una pregunta privada sigue siendo privada.

No se pudieron cargar los conjuntos

El servidor no responde o la oposición no está disponible.

Reintentar
Conjunto
Crear un conjunto
Banco
Preguntas
Importar
Plantillas

Elige o crea un conjunto para trabajar con sus preguntas.
```


## Estados vacíos (directorio temporal recién migrado y sembrado)

Directorio de datos sin material, sin preguntas, sin sesiones, sin propuestas y sin cambios. Solo la siembra de perfiles (oposiciones, convocatorias y temario común) está puesta.

### inicio — `/`

- **Captura**: [inicio-vacio-1280.png](../capturas/revision-2026-11/inicio-vacio-1280.png) (1280×900, 2692 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Inicio»
- **Encabezados**: Inicio · Siguiente tarea · Continuar estudiando · Acciones necesarias · Estado del programa · ¿Listo para estudiar? · Actividad reciente · Estado del sistema · Capacidades · Degradaciones declaradas · Almacenamiento
- **Estados**: vacío 1, cargando 0, error 0, avisos 2

Texto visible de `main` (innerText tal cual):

```text
Inicio

La siguiente tarea de hoy: el repaso vencido manda; si no hay nada vencido, se continúa la sesión que quedó a medias.

Siguiente tarea

Nada vencido y ninguna sesión a medias. Lo siguiente es practicar: una sesión de práctica sobre el banco que tengas, o un examen oficial si el material está completo.

Continuar estudiando

Sin sesiones de estudio

No hay ninguna sesión previa que continuar. Se empieza desde la sección Estudiar, con el banco de preguntas de la oposición.

Hace falta un conjunto de preguntas con su clave activa: sin clave no hay corrección.

Acciones necesarias

Nada esperando tu decisión: no hay incidencias de importación abiertas, ninguna propuesta sin decidir, ningún cambio de fuente sin confirmar y ningún material sin aceptar.

Estado del programa
Oposición activa
Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado tai-age
Convocatoria
tai-age-2025 · publicada el 2025-12-22
Perfiles disponibles
4
¿Listo para estudiar?

!
faltan 3 cosas
Lo que falta está dicho en su paso, con lo que hay que hacer para resolverlo.

·
Material por papel: todavía nada
Todavía no hay ningún documento aceptado en este programa: suelta tus carpetas y la aplicación las analizará.
Ir a la bandeja
·
Preguntas por tema: todavía nada
Todavía no hay preguntas importadas: entran solas al aceptar un documento con preguntas, o a mano desde el banco.
Ir al banco
·
Claves activas: todavía nada
Sin conjuntos de preguntas no hay clave que activar.
Ir al banco

Dominio estimado por tema (07_UI-UX §3, §5): contando lo que has practicado…. Sin intentos no hay dominio, y con pocos es «evidencia insuficiente»: verlo tema a tema en el Programa.

Actividad reciente

Todavía no hay actividad: ni lotes en la bandeja ni sesiones de estudio. Lo primero es soltar tus carpetas en la bandeja; lo segundo, preparar una sesión en Estudiar.

Estado del sistema
✔
listo para trabajar
✔
database
sqlite ok (revisión 0023_block_practice, foreign_keys=ON, journal_mode=wal, app_metadata=3)
✔
data_dir
directorio de datos escribible
Capacidades
Capacidades de esta instalación
CAPACIDAD	ESTADO	QUÉ SIGNIFICA
OCR (Tesseract)	
!
configurado sin verificar
	Binario presente, pero la aplicación no lo llama: el OCR no está implementado y una imagen se queda pendiente con su aviso. Declararlo evita creer que un PDF escaneado se está leyendo.
Modelo de lenguaje	
·
desactivado
	Sin proveedor: las respuestas se componen del propio corpus (extractivas) y citan cada afirmación. Un modelo de lenguaje llegaría con la deuda DEBT-014.
Embeddings	
·
desactivado
	Sin proveedor de embeddings decidido: la búsqueda es literal (FTS5) y cada respuesta lo declara como degradación (DEBT-014).
Búsqueda literal (FTS5)	
✔
operativo
	Índice léxico comprobado: tabla externa sobre evidence_spans, ordenada por bm25, con los disparadores que la mantienen al día; se rehace cuando haga falta sin salir de SQLite.
Almacén de originales por SHA-256	
✔
operativo
	Copia inmutable por contenido en <datos>/artifacts/sha256/ab/cd/<hash>. Dos ficheros idénticos comparten un artefacto y conservan dos orígenes.
Cola de trabajos local	
✔
operativo
	Cola persistida en SQLite con lease, trabajada por este proceso; sin Redis ni Celery. Cerrar la pestaña no cancela el trabajo.
Índice vectorial local	
×
no disponible
	Sin proveedor de embeddings no hay vectores que indexar: la búsqueda del corpus es literal (FTS5) sobre el texto extraído (DEBT-014).
Degradaciones declaradas

La aplicación funciona sin estas piezas. Se listan para que no haya funciones ausentes disfrazadas de correctas.

OCR (Tesseract): configurado sin verificar. Binario presente, pero la aplicación no lo llama: el OCR no está implementado y una imagen se queda pendiente con su aviso. Declararlo evita creer que un PDF escaneado se está leyendo.
Modelo de lenguaje: no configurado. Sin proveedor: las respuestas se componen del propio corpus (extractivas) y citan cada afirmación. Un modelo de lenguaje llegaría con la deuda DEBT-014.
Embeddings: no configurado. Sin proveedor de embeddings decidido: la búsqueda es literal (FTS5) y cada respuesta lo declara como degradación (DEBT-014).
Índice vectorial local: no disponible. Sin proveedor de embeddings no hay vectores que indexar: la búsqueda del corpus es literal (FTS5) sobre el texto extraído (DEBT-014).
Almacenamiento
Directorio de datos
C:\Users\David\AppData\Local\Temp\opofuente-capturas-vacio
Espacio libre
62.5 GB
Proveedor de IA
disabled (sin proveedor)
OCR
disponible
```

### bandeja — `/bandeja`

- **Captura**: [bandeja-vacio-1280.png](../capturas/revision-2026-11/bandeja-vacio-1280.png) (1280×900, 1467 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Bandeja»
- **Encabezados**: Bandeja · Entrada · Otras formas de entrada · Ficheros o carpetas enteras · Texto pegado · Desde una URL · Lotes recientes
- **Estados**: vacío 1, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Bandeja

OpoFuente copia: nunca mueve, renombra ni borra tus originales. Primero inventaría la carpeta en modo lectura y solo después copia lo que confirmes.

Revisar la clasificación del material
Lo importado se clasifica en propuestas: se confirman (o se rechazan) en Revisión.

Entrada
Carpeta a inventariar (ruta absoluta)
Inventariar (solo lectura)

Las tres formas de entrada del MVP están aquí: inventariar una carpeta, copiar ficheros sueltos, pegar texto y traer una URL. Ninguna mueve ni borra nada de su origen.

Otras formas de entrada
Ficheros o carpetas enteras

Suelta una carpeta y entran todos sus ficheros, conservando su ruta («Tema 3/apuntes.pdf»). Un ZIP se copia y se expande al extraer, con límites de tamaño y sin seguir rutas que salgan del paquete. Una baraja de Anki (`.apkg`) se lee como baraja.

Suelta aquí ficheros o carpetas
O elige una carpeta
Texto pegado

Se guarda como material propio con origen «pegado». No sustituye al documento original: es texto, y así se declara.

Texto
Título (opcional)
Guardar el texto
Desde una URL

Solo http y https. El servidor comprueba cada redirección y bloquea direcciones internas; no se eluden controles de acceso ni muros de pago.

Dirección
Descargar y copiar
Lotes recientes

Todavía no hay lotes

Cuando inventaríes una carpeta aparecerá aquí, con su informe.
```

### temario — `/temario`

- **Captura**: [temario-vacio-1280.png](../capturas/revision-2026-11/temario-vacio-1280.png) (1280×900, 2555 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Temario»
- **Encabezados**: Temario · Temas · Avance · Por bloque · Qué queda
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Temario

5 bloques · 40 temas

Temas
Buscar un tema

▾
I
Administración y normativa
1
La Constitución Española de 1978
2
La Unión Europea
3
El régimen local
4
Organización municipal
5
El procedimiento administrativo (Ley 39/2015)
6
El régimen jurídico del sector público (Ley 40/2015)
7
El personal al servicio de las administraciones (TREBEP)
8
La función pública local
9
Las haciendas locales y el presupuesto
10
La contratación del sector público (Ley 9/2017)
11
Igualdad y violencia de género
12
Transparencia y protección de datos en la Administración
▾
II
Informática básica y ofimática
13
Arquitectura de ordenadores
14
Sistemas operativos de usuario
15
Ofimática
16
Correo electrónico y colaboración
17
Licencias y software libre
▾
III
Sistemas, redes y comunicaciones
18
Sistemas operativos de servidor
19
Virtualización y contenedores
20
Almacenamiento y copias de seguridad
21
Redes
22
Comunicaciones
23
Servicios de red
24
Monitorización y gestión de incidencias
25
Cloud y centros de datos
26
Soporte al puesto de trabajo
▾
IV
Datos y desarrollo
27
Bases de datos relacionales
28
SQL
29
Gestores de bases de datos
30
Programación
31
Desarrollo web
32
Interoperabilidad e integración
33
Informes y explotación de datos
▾
V
Seguridad y administración electrónica
34
Seguridad de la información
35
El Esquema Nacional de Seguridad (ENS, RD 311/2022)
36
Criptografía y firma electrónica
37
Protección de datos aplicada
38
Ciberseguridad
39
Administración electrónica práctica
40
Accesibilidad y usabilidad
Avance

0 de 40 temas estudiados

Por bloque
I
Administración y normativa
0 de 12
Practicar este bloque
II
Informática básica y ofimática
0 de 5
Practicar este bloque
III
Sistemas, redes y comunicaciones
0 de 9
Practicar este bloque
IV
Datos y desarrollo
0 de 7
Practicar este bloque
V
Seguridad y administración electrónica
0 de 7
Practicar este bloque
Qué queda
I
Administración y normativa
12 de 12 sin estudiar
III
Sistemas, redes y comunicaciones
9 de 9 sin estudiar
IV
Datos y desarrollo
7 de 7 sin estudiar
V
Seguridad y administración electrónica
7 de 7 sin estudiar
II
Informática básica y ofimática
5 de 5 sin estudiar
```

### biblioteca — `/biblioteca`

- **Captura**: [biblioteca-vacio-1280.png](../capturas/revision-2026-11/biblioteca-vacio-1280.png) (1280×900, 915 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Biblioteca»
- **Encabezados**: Biblioteca · Filtros · Colecciones · Documentos
- **Estados**: vacío 1, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Biblioteca

Tus documentos con sus versiones, sus derechos y su procedencia. Un documento privado no se hace público por promocionarlo, y una versión candidata no es la versión buena hasta que alguien la acepta.

Filtros
Tipo documental
cualquier tipo
Convocatoria
Programa o temario
Norma o reglamento
Documento técnico oficial
Temario privado
Notas personales
Examen oficial
Plantilla de respuestas
Banco de preguntas privado
Caso práctico
Fichas de repaso
Material de la comunidad
Sin clasificar
Ámbito
cualquier ámbito
público
privado tuyo
generado por la aplicación
Derechos
cualquier derecho
solo restringidos (no se pueden compartir)
solo con derechos revisados
Limpiar filtros

Tipo documental y ámbito los filtra el servidor. El de derechos se aplica sobre los documentos ya cargados, porque la API todavía no filtra por derechos: el recuento que se ve es el de esta pantalla, no el de toda la biblioteca.

Colecciones

Una colección agrupa material sin duplicarlo: el mismo documento puede estar en varias. El filtro se aplica en el servidor, así que lo que se ve son los documentos de la colección y no los que han quedado fuera de la página.

Todavía no hay colecciones. Crea una para agrupar material.

Nombre de la colección
Descripción (opcional)
Crear la colección
Documentos

Todavía no hay ningún documento

Un documento nace al promocionar material ya copiado: la biblioteca no crea obras.

Copia el material en la Bandeja y promociónalo: aparecerá aquí con su versión.
```

### preguntas — `/preguntas`

- **Captura**: [preguntas-vacio-1280.png](../capturas/revision-2026-11/preguntas-vacio-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Preguntas»
- **Encabezados**: Preguntas · Conjunto · Banco
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Preguntas

El banco de preguntas de una oposición: lo que se importa, lo que se revisa y la plantilla con la que se corrige. Importar no publica nada: una pregunta privada sigue siendo privada.

Conjunto

Todavía no hay ningún conjunto de preguntas. Se crea aquí debajo: un examen oficial, un banco privado, práctica o un lote generado.

Crear un conjunto
Banco
Preguntas
Importar
Plantillas

Elige o crea un conjunto para trabajar con sus preguntas.
```

### estudiar — `/estudiar`

- **Captura**: [estudiar-vacio-1280.png](../capturas/revision-2026-11/estudiar-vacio-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Estudiar»
- **Encabezados**: Estudiar · Preparar la sesión
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Estudiar

Practicar y examinarse con el banco de preguntas. La puntuación la calcula el servidor con la clave activa del conjunto y con la penalización que publica la convocatoria.

Preparar la sesión

El modo decide cómo se corrige: en práctica se puede corregir al responder; un examen oficial corrige al terminar, con el tamaño, las reservas y el tiempo de la convocatoria; un simulacro monta ese mismo perfil pero no se llama oficial y prefiere las preguntas que no has visto hace poco.

Modo
práctica
examen oficial
simulacro
Parte del examen
Primera parte: cuestionario de conocimientos
Segunda parte: supuesto práctico
Partes que todavía no se pueden practicar
Conjunto de preguntas
Elige un conjunto…
Cuántas preguntas
Corrección
corrección al responder
corrección al terminar
 barajar el orden
Empezar
¿No sabes por dónde empezar? Haz un diagnóstico
```

### errores — `/errores`

- **Captura**: [errores-vacio-1280.png](../capturas/revision-2026-11/errores-vacio-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Errores»
- **Encabezados**: Errores · Repaso · Exportar
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Errores

Lo que fallaste y cuándo toca repasarlo. Un fallo entra solo en la cola; la causa, el concepto y la nota los pones tú, y el repaso va subiendo el intervalo hasta un mes.

Repaso

sin repasos: se crean al fallar una pregunta · 0 fallo(s) acumulado(s)

No hay ningún repaso todavía: se crean solos al fallar una pregunta en una sesión.

Hoy
Conceptos

No hay nada vencido. La cola se llena sola cuando fallas una pregunta en una sesión; si quieres repasar antes de que toque, puedes declarar el resultado de un repaso hecho fuera.

Exportar

El fichero se escribe en la carpeta de exportaciones del directorio de datos y lleva la procedencia de cada pregunta: conjunto, plantilla, origen, tema y las versiones de los documentos citados.

Título del fichero
 Incluir material con derechos restringidos
Anki CSV
Markdown (Obsidian)
```

### cambios — `/cambios`

- **Captura**: [cambios-vacio-1280.png](../capturas/revision-2026-11/cambios-vacio-1280.png) (1280×900, 900 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Cambios»
- **Encabezados**: Cambios · Sin cambios · Resúmenes del material
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Cambios

Cuando llega una versión nueva de un material, OpoFuente compara las dos y dice qué depende de lo que ha cambiado. Nada se aplica hasta que lo confirmas, y lo que cambió de texto no decide por ti si algo sigue valiendo.

Sin cambios

No hay ninguna versión nueva pendiente de revisar. Un cambio aparece cuando promocionas una segunda versión de un documento que ya tenía una aceptada: entonces se compara y se dice qué derivados dependen de lo que cambió.

Resúmenes del material

Los resúmenes son extractivos: texto del corpus con su cita, sin modelo. Un resumen depende de las secciones de las que sale, así que un cambio en ellas lo deja pendiente de revisar. Se crean desde el lector de la Biblioteca, en la sección que interesa.

No hay ningún resumen pendiente de revisar. Si un cambio afecta a uno, aparecerá aquí con su motivo.
```

### revision — `/revision`

- **Captura**: [revision-vacio-1280.png](../capturas/revision-2026-11/revision-vacio-1280.png) (1280×900, 3508 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Revisión»
- **Encabezados**: Revisión · Esto son propuestas, no hechos · Cola de revisión · Propuestas · Cobertura del programa
- **Estados**: vacío 0, cargando 0, error 0, avisos 1

Texto visible de `main` (innerText tal cual):

```text
Revisión

Revisa lo que la aplicación propone sobre tu material: qué eje, qué valor, con qué confianza y con qué evidencia. Decidir aquí es lo que convierte una propuesta en algo aceptado.

Esto son propuestas, no hechos

Nada de esta pantalla se aplicó por su cuenta: cada propuesta espera tu decisión. Lo que aparece como aplicada provisionalmente lo propuso el motor por su banda de confianza, es reversible y lo puedes confirmar, rechazar o deshacer. Las propuestas de autoridad y derechos no se aplican solas nunca, ni con confianza alta: requieren tu confirmación.

Aceptar no convierte el material en oficial: solo lo aprueba para tu corpus (07_UI-UX §12).

Cola de revisión
Buscar propuestas ahora
Una pasada de clasificación no cambia nada por sí sola: solo propone.

No hay propuestas pendientes que agrupar. Cuando el motor proponga algo lo verás aquí, agrupado por eje y valor, con su tamaño y su confianza.

Propuestas

No hay ninguna propuesta esperando tu decisión. Las que ya decidiste están en el historial de esta sesión y las descartadas no vuelven a aparecer.

Cobertura del programa

Se cuenta lo que cubre cada nodo con su subárbol. La cobertura provisional es lo aplicado por el motor sin confirmar; la aceptada es lo que has confirmado tú sobre texto utilizable. Nunca se suman.

▾
I
Organización del Estado y Administración electrónica
bloque
1
La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey.
tema
2
Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo.
tema
3
El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales.
tema
4
El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.
tema
5
Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.
tema
6
La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España.
tema
7
La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales.
tema
8
Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad.
tema
9
Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica.
tema
▾
II
Tecnología básica
bloque
1
Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos.
tema
2
Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización.
tema
3
Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros.
tema
4
Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles.
tema
5
Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes.
tema
▾
III
Desarrollo de sistemas
bloque
1
Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización.
tema
2
Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa.
tema
3
Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores.
tema
4
Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML).
tema
5
Arquitectura Java EE/Jakarta EE y plataforma.NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de interfaces.
tema
6
Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados.
tema
7
Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script.
tema
8
Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas.
tema
9
Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software.
tema
▾
IV
Sistemas y comunicaciones
bloque
1
Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo.
tema
2
Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario.
tema
3
Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios.
tema
4
Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico.
tema
5
Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario.
tema
6
Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas.
tema
7
El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP.
tema
8
Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS.
tema
9
Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario.
tema
10
Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión.
tema

Elige un bloque o un tema para ver su cobertura.
```

### ajustes — `/ajustes`

- **Captura**: [ajustes-vacio-1280.png](../capturas/revision-2026-11/ajustes-vacio-1280.png) (1280×900, 3192 px de alto)
- **Título de la pestaña**: OpoFuente
- **H1**: «Ajustes»
- **Encabezados**: Ajustes · Datos y disco · Uso del almacén · Capacidades instaladas · Privacidad: a dónde sale tu contenido · Copia y restauración · Índice de búsqueda · Exportación · Diagnóstico y registros saneados · Límites en vigor
- **Estados**: vacío 0, cargando 0, error 0, avisos 0

Texto visible de `main` (innerText tal cual):

```text
Ajustes

Todo lo que la aplicación hace con tus datos, dicho sin adornos: dónde los guarda, qué capacidades hay de verdad, a dónde sale el contenido si configuras un proveedor, y cómo se copia y se restaura.

Datos y disco
Versión
0.0.0 · esquema 0023_block_practice
Ruta de datos
C:\Users\David\AppData\Local\Temp\opofuente-capturas-vacio
Base de datos
C:\Users\David\AppData\Local\Temp\opofuente-capturas-vacio\opofuente.sqlite3
Disco
63.1 GB libres de 464.8 GB
Servidor
127.0.0.1:8765 · registro WARNING

Los ajustes se editan en .env y en las variables de entorno: esta pantalla no escribe configuración, la lee y la explica.

Uso del almacén
Total 0 B · recuperable 0 B
ÁREA	FICHEROS	TAMAÑO
Material copiado (por contenido)	0	0 B
Texto extraído y representaciones	0	0 B
Copias de seguridad	0	0 B
Exportaciones generadas	0	0 B
Registros	1	0 B

Aquí no se borra nada solo: cada bloque de abajo enseña lo que se puede retirar y su motivo, y hay que confirmarlo.

Capacidades instaladas
Capacidades de esta instalación
CAPACIDAD	ESTADO	QUÉ SIGNIFICA
OCR (Tesseract)	
!
configurado sin verificar
	Binario presente, pero la aplicación no lo llama: el OCR no está implementado y una imagen se queda pendiente con su aviso. Declararlo evita creer que un PDF escaneado se está leyendo.
Modelo de lenguaje	
·
desactivado
	Sin proveedor: las respuestas se componen del propio corpus (extractivas) y citan cada afirmación. Un modelo de lenguaje llegaría con la deuda DEBT-014.
Embeddings	
·
desactivado
	Sin proveedor de embeddings decidido: la búsqueda es literal (FTS5) y cada respuesta lo declara como degradación (DEBT-014).
Búsqueda literal (FTS5)	
✔
operativo
	Índice léxico comprobado: tabla externa sobre evidence_spans, ordenada por bm25, con los disparadores que la mantienen al día; se rehace cuando haga falta sin salir de SQLite.
Almacén de originales por SHA-256	
✔
operativo
	Copia inmutable por contenido en <datos>/artifacts/sha256/ab/cd/<hash>. Dos ficheros idénticos comparten un artefacto y conservan dos orígenes.
Cola de trabajos local	
✔
operativo
	Cola persistida en SQLite con lease, trabajada por este proceso; sin Redis ni Celery. Cerrar la pestaña no cancela el trabajo.
Índice vectorial local	
×
no disponible
	Sin proveedor de embeddings no hay vectores que indexar: la búsqueda del corpus es literal (FTS5) sobre el texto extraído (DEBT-014).
Privacidad: a dónde sale tu contenido

Se calcula sobre la dirección real de cada proveedor, no sobre su nombre. «No se puede determinar» cuenta como que sí sale: es la respuesta conservadora.

Modelo de lenguaje
✔
sin proveedor
 el modelo de lenguaje no está configurado: no se envía nada
Embeddings
✔
sin proveedor
 el proveedor de embeddings no está configurado: no se envía nada
Clave del proveedor
no hay clave configurada
Copia y restauración
Nota de la copia (opcional)
Hacer una copia ahora

Todavía no hay copias. Una copia incluye la base de datos, el material copiado y el texto extraído, con el hash de cada fichero.

Índice de búsqueda

✔
completo
 el índice está completo (0 fragmentos)

Rehacer el índice

El índice es derivado: el texto de las evidencias es la verdad. Rehacerlo no puede perder nada y sirve para reparar un índice que se haya quedado atrás.

Exportación

Las exportaciones (Markdown/Obsidian y Anki CSV) se hacen desde Errores, junto a la cola de repaso, porque es ahí donde se elige qué se lleva.

Diagnóstico y registros saneados
Preparar el diagnóstico en texto

El diagnóstico no lleva contenido, ni claves, ni rutas completas: las rutas van abreviadas y el registro pasa por el saneado de secretos. Es lo que se puede pegar en una incidencia.

Última generación: 2026-11-09 16:11:43 · 0 línea(s) de registro

artifacts: 0
artifact_origins: 0
document_versions: 0
representations: 0
jobs: 0
jobs_pending: 0
evidence_spans: 0
questions: 0
study_sessions: 0
rag_queries: 0
learning_errors: 0
change_sets: 0
Límites en vigor
Tamaño por fichero
512.0 MB
Entradas por lote
50000
Descarga por URL
64.0 MB · 5 redirección(es)
Texto pegado
4.0 MB
ZIP
2000 entradas · 1.0 GB · ratio 200 · profundidad 1
PDF
2000 páginas
Worker
sondeo cada 1 s · lease 60 s
```

