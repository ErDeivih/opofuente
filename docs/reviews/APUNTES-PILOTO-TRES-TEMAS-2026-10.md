# Los apuntes de los tres temas piloto (IV.7, I.6, I.1) — 8-oct-2026

En `main` = `7196b63` (rama `f7-apuntes-piloto`: `5813389` backend + `7196b63` web y contratos),
**18/18 puertas** en 27:17. Guiados por las preguntas ya clasificadas, con comprobación pregunta a
pregunta.

## Cobertura, medida en la base

| tema | preguntas | cubiertas | dudosas | sin contestar | apartados | caracteres |
|---|---|---|---|---|---|---|
| IV.7 | 554 | 478 (86,3 %) | 76 | 10 | 26 | 213.611 |
| I.6 | 317 | 242 (76,3 %) | 75 | 38 | 11 | 158.688 |
| I.1 | 2.041 | 1.986 (97,3 %) | 55 | 12 | 90 | 943.148 |
| **total** | **2.912** | **2.706 (92,9 %)** | 206 | **60 (2,1 %)** | 127 | 1.315.447 |

Las 206 dudosas: 131 con la clave contradiciendo la norma o el material, 48 sin frase que las justifique,
12 con la frase pero la clave diciendo otra opción y 15 sin clave con la que comprobarlas.
**Solo 500 de las 2.912 preguntas tienen clave activa**; en el resto no hay letra que decida y el
resultado lo decide la cita verificada.

## Coste real

| tema | llamadas | entrada | de caché | salida | coste |
|---|---|---|---|---|---|
| IV.7 | 100 | 2.690.658 | 2.486.780 | 578.493 | 0,7507 $ |
| I.6 | 52 | 728.280 | 458.496 | 677.726 | 0,5159 $ |
| I.1 | 374 | 23.599.894 | 22.335.360 | 2.519.284 | 5,0516 $ |
| **total** | **526** | **27.018.832** | **25.280.636 (93,6 %)** | **3.775.503** | **6,3182 $** |

**0,00217 $ por pregunta**, más barato que clasificar (0,0036 $) porque el texto de los apuntes va en el
mensaje de sistema y nueve de cada diez tokens de entrada son caché. A eso hay que sumar **~1,5–2 $ de dos
corridas parciales tiradas** por dos fallos del propio agente (no medibles: murieron antes de imprimir);
los hechos ya pagados se conservaron.

## Las 60 sin contestar: casi ninguna es una pregunta

- **54 no son preguntas**: trozos de norma importados como si lo fueran, sin «¿» y sin terminar en «?»
  (p. ej. «La Comisión podrá, mediante actos de ejecución, establecer:» con opciones que son fragmentos
  del reglamento). **Es el mismo material que los 754 «enunciado roto» que encontró la clasificación en
  otros bancos**: dos instrumentos independientes han topado con la misma basura, así que el hallazgo
  queda confirmado.
- **6 son preguntas de verdad** y falta un dato o una decisión sobre la clave: el número de direcciones
  para hosts de una subred, el puerto de ASMP (587), la clase de la IP 199.8.45.3, SFTP frente a FTPS y el
  proyecto europeo «TORK».

Conclusión: **lo que falta no es más texto en los apuntes**; son enunciados que arreglar y claves que
decidir.

## Advertencia que hay que leer antes de firmar nada

**La comprobación prueba cobertura, no verdad.** El propio agente encontró un error en los apuntes de
IV.7: la tabla de puertos pone **LDAPS 989-990** donde es **636** (989-990 es FTPS). El paso F —la
revisión del propietario— sigue siendo necesario, y por eso los apuntes se marcan con la etiqueta
«revisar» donde no hay material que los sostenga.

## Cómo se guardan y dónde se leen

- Se guardan **dentro de la versión del tema** (el dossier incluye los apuntes en el payload y en la
  huella de contenido), usando el mecanismo de versiones que ya existía. Leer una versión antigua devuelve
  los apuntes **como estaban** (hay prueba).
- El rastro de qué preguntas cubre cada apartado vive en `question_note_anchors` y viaja al contrato.
- Se leen en **Programa → el tema**: bloque «Apuntes redactados del tema», con la cabecera de lo
  comprobado («26 apartados · 478 de 554 preguntas cubiertas · 76 para revisar»), la etiqueta «revisar» y
  cada apartado con su epígrafe, su recuento y su texto con tablas de verdad.

## Lo que queda fuera, y decide el propietario

1. **Los 33 temas restantes** (parada acordada).
2. **La pantalla de lectura del alumno** (capítulos por epígrafe, índice, buscador, salto al párrafo):
   `GET /student/topics/{codigo}/notes` sigue sin contrato propio.
3. **El panel `/admin/apuntes`** y la **cola de incidencias**: el motivo de cada duda está en
   `question_note_anchors.note`, pero `question_issue_reports` no tiene columna `origin` (pide migración).
4. **El tamaño de I.1**: 943.148 caracteres (~170.000 palabras) en un tema, porque la regla del plan es
   «todos los hechos dentro» con 3.509 hechos. No es un fallo, pero es una decisión: pantalla por
   capítulos, o tope de detalle por apartado.

## Trampa de entorno nueva (la quinta)

`DEEPSEEK_API_KEY` **no se hereda** al proceso hijo en DSH: de las 14 variables de usuario es la única que
no pasa. Hay que leerla del ámbito de usuario **en cada comando**:

```powershell
$env:DEEPSEEK_API_KEY=[Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')
```

La clave sigue viviendo solo en el entorno, nunca en un fichero, un log ni el repositorio; si falta, el
comando para con código 2 y lo dice.
