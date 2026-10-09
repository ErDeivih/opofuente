# Los dos temas que no tenían material, y ahora sí (30-09-2026)

El mapa de material por tema (`mapa_de_material_por_tema.py`) puso en números lo que ya se veía venir: de los 33
temas del programa, **dos no tenían ni un fragmento asignado** en la aplicación —quien quisiera estudiar esos
temas no encontraba nada— y otros tres tenían 2, 8 y 12.

| tema | título | fragmentos antes | ahora |
| --- | --- | --- | --- |
| **III.3** | Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados | **0** | **1.208** |
| **IV.5** | Conceptos de seguridad de los sistemas de información. Seguridad física y lógica. El ENS | **0** | **2.562** |
| I.4 | El texto refundido del Estatuto Básico del Empleo Público | 8 | **303** |
| II.2 | Periféricos: conectividad y administración. Elementos de impresión | 2 | **437** |
| III.5 | Arquitectura Java EE/Jakarta EE y plataforma .NET | 12 | **764** |

**Ningún tema del programa se queda por debajo de 50 fragmentos** (antes: 5 temas), y **ninguno sin material**
(antes: 2). El estado del dossier de II.2, por ejemplo: 2 fuentes y **436 pasajes**, sin huecos de material.

## De dónde sale el material, y por qué de ahí

Las dos fuentes que faltaban, con su procedencia escrita en
`F:\OpoFuente\TAI\internet\fuentes-de-temas-flacos\PROCEDENCIA.md`:

- **IV.5** · el **Esquema Nacional de Seguridad**: Real Decreto 311/2022, en el **texto consolidado del BOE**
  (`boe.es/buscar/act.php?id=BOE-A-2022-7191`). Es la norma que ese tema estudia, y es oficial.
- **III.3** · el **lenguaje SQL** y los **procedimientos almacenados**, en la **documentación oficial de
  PostgreSQL**: el índice del lenguaje SQL, `SELECT`, `CREATE TABLE`, `CREATE FUNCTION`, PL/pgSQL y
  transacciones.

Antes de escribirlas se comprobó que las direcciones responden (`probar_fuentes_de_los_temas_flacos.py`): el BOE
da 200 con 233.482 caracteres de texto y PostgreSQL, 200. De cada una se guarda el **texto visible** sin scripts
ni etiquetas, en `.txt`, con su dirección y su fecha en la cabecera.

## Dos fallos de mi propia herramienta, los dos medidos

1. **Sin párrafos no hay cita.** Al quitar todas las líneas vacías, cada fuente quedaba en **un solo párrafo** y
   la aplicación, que parte un `.txt` por líneas en blanco y recorta cada fragmento a 1.200 caracteres, la
   guardaba como **3 fragmentos**: la norma entera del ENS reducida a sus primeros 3.600 caracteres. Arreglado:
   los párrafos se conservan y, además, las líneas se **agrupan en párrafos de 900 caracteres como mucho**, que es
   lo que cabe en un fragmento citable. La misma página de PostgreSQL pasó de 3 a **351 fragmentos**.
2. **No vale mapear la primera versión ni una sola parte.** Después de arreglar los párrafos, el tema seguía con
   18 fragmentos: las versiones buenas **existían pero sin mapear**, porque el script cogía la primera versión de
   cada título (la mala) y solo una parte. Arreglado: se asigna la versión **más reciente con texto** y **todas
   las partes** (el ENS son 6 ficheros). **42 mapeos** creados con `POST /document-versions/{id}/mappings`, que es
   la ruta que la aplicación tiene para asignar material a un nodo.

Los ficheros malos se quedan en la biblioteca (la aplicación no tiene ruta para borrar documentos) y están
dichos aquí: 3 fragmentos por fuente, sin mapear, y no cuentan como material de ningún tema.

## Los otros tres: el material ya estaba, solo le faltaba estar asignado

Para I.4, II.2 y III.5 lo primero no era traer nada de internet, sino mirar si el material ya estaba en la
biblioteca **sin asignar**. La búsqueda de la aplicación no vale para eso (la ganan los programas y los exámenes,
que nombran el tema sin explicarlo), así que se midió de otra forma: contar en el **texto** de cada documento
cuántas veces aparecen los términos del tema (`buscar_en_la_biblioteca_por_terminos.py`).

Y estaba:

| tema | documento | apariciones |
| --- | --- | --- |
| I.4 | `rdl-5-2015-ebep.txt` (el texto refundido del EBEP) | 96 (personal laboral 61, funcionario de carrera 9…) |
| I.4 | `PreparaTIC_30_024 - Tema.pdf` (el tema del EBEP de Preparatic) | 62 (ebep 27, trebep 25) |
| II.2 | `Tema 9.docx` (impresoras y periféricos) | 103 (impresora 74, periférico 9) |
| III.5 | `DotNETFrameworkNotesForProfessionals.pdf` | 289 (.net 263) |
| III.5 | `SpringFrameworkNotesForProfessionals.pdf` | 243 (spring 225) |
| III.5 | `HibernateNotesForProfessionals.pdf` | 190 (hibernate 157, jpa 12) |

**16 mapeos** creados con `POST /document-versions/{id}/mappings` (nacen aceptados y auditados, con cobertura
**parcial**: un documento trata el tema, no es el tema entero). Entre ellos hay **4 temas de Preparatic**
(`PreparaTIC_30_024` del EBEP y `PreparaTIC_29_066` de .NET), que es justo lo que pedía el objetivo: el material
de Preparatic **mapeado a los temas de TAI**.

Y un error mío cazado por una medida: la primera versión del script buscaba la pista «en cualquier parte del
título», así que `Tema 9.docx` (periféricos) arrastraba también `Esquema BIII - Tema 9.docx`, que es el tema 9
del **bloque III** (repositorios) y no tiene nada que ver. Se vio porque ese documento **no aparecía** en la
medida de términos ni con el mínimo más bajo; ahora la pista tiene que estar al **principio** del título.

## Cómo queda

- Biblioteca: **3.228 documentos y 3.240 versiones aceptadas** (antes 3.204 y 3.216).
- Los temas sin material: **ninguno**. Los que siguen con poco: I.4 (8), II.2 (2), III.5 (12).
- El mapa completo por tema, con fragmentos, documentos y preguntas, en
  `F:\OpoFuente\CATALOGO\mapa-material-por-tema.json`.

## Lo que sigue faltando, con nombre y número

- **Tres temas sin ninguna pregunta**: **II.2** (periféricos), **III.2** (lenguajes de programación) e **IV.5**
  (seguridad de los sistemas de información). El banco tiene 5.224 preguntas, pero de esos tres temas, cero.
- **1.201 preguntas sin tema** en el banco, y el banco muy concentrado (I.1 con 1.586 preguntas).
- **15 ficheros temporales de Word** (`~WRL*.tmp`) se colaron en la biblioteca al descomprimir los paquetes, y
  suman unos **6.900 fragmentos**: son versiones anteriores de documentos de bloque con un nombre que no dice
  nada, y alguna **sale en las búsquedas**. La aplicación no tiene ruta para borrar documentos; lo que sí existe
  es `POST /document-versions/{id}/supersedes` (una versión sustituye a otra). Antes de usarlo hay que emparejar
  cada temporal con el documento del que es versión anterior —por el texto, no por el nombre— y eso está medido:
  son 15, y el que más fragmentos tiene (1.744) es el mayor de todos. Queda como trabajo con nombre y número
  (`ver_temporales_en_la_biblioteca.py`).
- Los **apuntes** por tema siguen saliendo del recorrido de la bandeja (`apuntes_limpios.py`), no de las
  asignaciones de la aplicación: lo que se ha arreglado aquí se ve en el **dossier** de cada tema en la
  aplicación, y llevar el material nuevo (el ENS, la documentación de SQL, el EBEP) a los apuntes es el
  siguiente paso natural, con su medida antes y después.

## Cómo se reproduce

```powershell
python mapa_de_material_por_tema.py --escribir          # el mapa: qué tiene cada tema
python probar_fuentes_de_los_temas_flacos.py            # ¿responden las fuentes?
python traer_fuentes_de_los_temas_flacos.py --aplicar   # traerlas, guardarlas e ingerirlas
python asignar_fuentes_a_su_tema.py --aplicar           # asignarlas a su tema
python ver_documentos_de_una_fuente.py "III.3-PostgreSQL"   # qué versiones hay y cuál está mapeada
python mapa_de_material_por_tema.py                     # el mapa otra vez, para ver el cambio
```
