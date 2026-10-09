# Los apuntes, puestos al día con el banco de la aplicación (30-09-2026)

Los apuntes por tema se escribieron el 29-09. Desde entonces el banco de la aplicación pasó de **2.399 a 5.359
preguntas** (las de los paquetes nuevos y las 1.600 de la Constitución), y el banco por tema dejó de ser
`F:\OpoFuente\BANCO\<tema>.md` para ser el volcado de la aplicación en
`F:\OpoFuente\BANCO\por-tema-de-la-app\`. Los apuntes seguían anunciando el banco viejo y sus cifras.

## Lo que se ha hecho, medido

| | antes | después |
| --- | --- | --- |
| apuntes que anunciaban el banco viejo | 33 | **0** |
| frases con cifras del banco viejo (ya falsas) | 32 | **0**, sustituidas por las de la aplicación |
| frases que solo citaban la ruta del banco viejo | 114 | **0**, reapuntadas al banco de la aplicación |
| líneas de «Para practicar» repetidas | 32 apuntes con dos | **0** |
| definiciones de glosario dentro de los apuntes | 0 | **305** (repartidas por bloque) |
| preguntas que anuncian los apuntes | 2.399 (del banco viejo) | **2.101 del tema** (las de la aplicación) |

El apunte del tema I.1 (la Constitución) es el que más cambia: anunciaba 543 preguntas del banco viejo y ahora
anuncia **1.584 preguntas de la aplicación, todas con su respuesta y 1.581 con su cita**, y apunta al fichero
`BANCO\por-tema-de-la-app\TAI\I.1.md`.

Los apuntes anteriores están guardados en `APUNTES-anteriores\2026-09-30-1232\`.

## Los glosarios: al bloque, no al tema, y por qué

Los 21 cuestionarios HTML por tema (comandos de Linux, puertos, diagramas UML, amenazas, HTTP, MPLS…) venían con
sus definiciones en un objeto de JavaScript. Ya se convirtieron a texto; ahora sus **305 definiciones** están
dentro de los apuntes… pero **en el apunte del bloque**, no en el del tema.

El motivo está medido: con el umbral flojo (0,15) los glosarios cortos se colocaban mal —`Comandos_Git` acababa
en el tema de Internet y `Linux_Comandos` en el de estructuras de datos—, y con el umbral de siempre (0,25) y
limitado a su bloque (que sí consta, lo dice la carpeta del HTML original) **ninguno llega**. Así que van al
apunte del bloque, con una nota que dice que están pendientes de repartir: un glosario en el tema equivocado es
peor que un glosario en el bloque correcto.

## Qué **no** se ha tocado

El **cuerpo** de cada apunte: el texto de cada tema, su resumen y sus fragmentos con procedencia ya estaban
limpios y ordenados (12.066 fragmentos en los 33 temas, entre 4 y 400 por tema), y volver a generarlos habría
cambiado también lo que ya estaba bien. Esta pasada **añade y corrige lo desfasado**, y dice cuánto.

## Lo que queda a la vista para el próximo paso

- **Los temas están al tope**: 26 de los 33 temas tienen 400 fragmentos (el máximo por tema, que es lo que hace
  legible el apunte). Con el temario de 2026 —los textos legales, ya en la biblioteca— lo que procede no es
  añadir más, sino **sustituir** lo peor de cada tema por lo mejor del temario nuevo, y eso pide una medida de
  calidad por fragmento que todavía no existe.
- Los glosarios están **repartidos por bloque**; bajarlos a su tema es un trabajo con nombre y número (21
  ficheros, 305 definiciones).
- Los apuntes anuncian las preguntas de su tema, pero **no las muestran**: las preguntas están en el banco y en
  `BANCO\por-tema-de-la-app\`. Si se quieren dentro del apunte, el banco ya las tiene ordenadas y con su
  respuesta, así que es una decisión de formato, no de datos.

## Cómo se reproduce

```powershell
python estado_de_los_apuntes.py --guardar antes      # el estado de partida
python actualizar_los_apuntes.py                     # informe de lo que cambiaría
python actualizar_los_apuntes.py --aplicar           # lo cambia (guarda los anteriores)
python estado_de_los_apuntes.py --comparar antes     # qué ha cambiado
python ver_frases_del_banco_viejo.py                 # las frases que hablaban del banco viejo
```
