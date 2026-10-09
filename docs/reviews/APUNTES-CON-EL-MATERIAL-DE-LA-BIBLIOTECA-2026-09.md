# Los apuntes, con el material de la biblioteca dentro (30-09-2026)

Los apuntes se armaron el 29-09 recorriendo la bandeja. La biblioteca de la aplicación, desde entonces, tiene
material nuevo (el **ENS**, la documentación de **SQL**, el **EBEP** consolidado, las notas de **.NET**) y tiene
además **asignaciones aceptadas** documento → tema. La pregunta era cuánto de eso está en los apuntes.

## Lo que se midió primero

`medir_apuntes_contra_asignaciones.py`: de los **12.066 fragmentos** que hay en los apuntes, solo **867 (el 7 %)**
vienen de documentos que la aplicación **asigna** a ese tema. En 31 de los 33 temas, menos del 25 %; en varios
(2.2, 3.3, 3.7, 3.8, 4.2, 4.5, 4.9), **el 0 %**.

Eso no quiere decir que los apuntes estén mal —sus fragmentos se eligieron por parecido con el título del tema, y
esa regla está medida—, pero sí que **el material nuevo no estaba dentro**: los cinco temas que se acaban de
rellenar (I.4, II.2, III.3, III.5 y IV.5) no tenían ni un fragmento de su material asignado.

## Lo que se ha hecho

Se ha añadido a esos cinco apuntes un apartado **`## Material del tema en la biblioteca de la aplicación`** con
los mejores fragmentos de **cada documento asignado** al tema, en el mismo formato que el resto del apunte
(`**[n]** texto` y la fuente debajo en `<sub>`), continuando la numeración:

| tema | fragmentos que tenía | añadidos | documentos de los que salen | ahora |
| --- | --- | --- | --- | --- |
| I.4 (EBEP) | 80 | **24** | 2 | 104 |
| II.2 (periféricos) | 80 | **14** | 2 | 94 |
| III.3 (SQL) | 80 | **68** | 6 | 148 |
| III.5 (Java EE/.NET) | 80 | **82** | 9 | 162 |
| IV.5 (seguridad y ENS) | 80 | **73** | 7 | 153 |

**261 fragmentos** en total, repartidos de forma que **ninguna fuente se quede fuera** (hasta 12 por documento).
Al final del apartado queda la **lista completa** de documentos que la aplicación asigna a ese tema, con cuántos
fragmentos tiene cada uno, para saber dónde está todo lo demás.

Y la cabecera de cada apunte, que decía «80 fragmentos en el apunte (de 102 encontrados)», ahora dice de dónde
sale cada cosa: «**153 fragmentos** en el apunte · 80 del material propio (de 102 encontrados) · **73 de la
biblioteca de la aplicación**».

## Tres decisiones que se tomaron midiendo, no por gusto

1. **No se copia todo.** Los temas tienen 277 a 777 fragmentos en la biblioteca. Copiarlos todos convertiría un
   apunte de 80 fragmentos en uno de 700: los apuntes son **selecciones** (80 fragmentos, el mejor de cada
   fuente), no volcados. Se copian hasta 12 por documento y 150 por apunte.
2. **Se quita el ruido de las fuentes traídas de internet.** El primer fragmento de cada página de PostgreSQL
   era su **menú** (`Home`, `About`, `Download`…) y los tres primeros de cada fichero eran la **cabecera** que
   escribió el descargador (título, dirección, fecha). Se vio en el apunte del tema III.3 (fragmentos 69 a 71) y
   se filtran: fuera las líneas de menú de las quince primeras y fuera los fragmentos que solo son cabecera o
   tienen menos de 80 caracteres.
3. **Los apuntes anteriores se guardan** en `APUNTES-anteriores\2026-09-30-1342\`.

## Qué queda

- **28 de los 33 apuntes siguen sin el material de la biblioteca dentro** (el mismo apartado, con sus documentos
  asignados). Para los que ya están en 80 fragmentos, el apartado sería la **lista de documentos** y una
  selección corta, no un volcado.
- Lo que de verdad sigue faltando no es esto, sino **preguntas**: hay tres temas sin ninguna (II.2, III.2, IV.5)
  y el banco está muy concentrado en I.1 (1.586 de 5.224).
- Los apuntes siguen **sin incluir las preguntas** (solo dicen cuántas hay y dónde): las preguntas están en el
  banco y en `BANCO\por-tema-de-la-app\`.

## Cómo se reproduce

```powershell
python medir_apuntes_contra_asignaciones.py                        # ¿cuánto del apunte viene del material asignado?
python anadir_material_de_la_biblioteca_a_los_apuntes.py --temas III.3 IV.5 I.4 II.2 III.5   # informe
python anadir_material_de_la_biblioteca_a_los_apuntes.py --temas III.3 IV.5 I.4 II.2 III.5 --aplicar
python contar_marcadores_de_los_apuntes.py                         # cabecera, marcadores y fuentes de cada apunte
```
