# Dataset sintético etiquetado de clasificación (S04)

Conjunto de casos **inventados** para medir la calidad de la clasificación, con su etiqueta humana por
eje. Es la pieza que hace posible el criterio de aceptación de S04 («dataset sintético produce
métricas reproducibles») y la primera medición de §7 del plan de pruebas.

- Fichero: `dataset.json` (léelo entero: cada caso lleva su `note` explicando por qué está ahí).
- Motor medido: `DeterministicClassifier` (`opofuente.infrastructure.classifiers.deterministic`).
- Cálculo: `opofuente.domain.classification_metrics` (dominio puro, sin base de datos ni red).
- Informe: `uv run python -m opofuente.tools.classification_metrics`.
- Números fijados en pruebas: `apps/api/tests/unit/test_classification_metrics.py`.

## De dónde sale el texto

De ningún sitio: está escrito para este fichero. No hay ni un párrafo copiado de un temario, de una
convocatoria, de un libro ni del material del usuario, y no hay ninguna ruta del disco de nadie. Los
nombres propios son deliberadamente falsos (`demo-tai-2026`, «Técnico Auxiliar de Muestra»,
«Comunidad Autónoma de Ejemplo»). La única cadena con forma de URL real
(`https://www.boe.es/documento-sintetico?id=DEMO-2026-1`) es un identificador **inventado** que existe
para probar una regla del motor: los dominios de publicación oficial son una señal de autoridad. No
se descarga nada.

Los perfiles (`profiles`) van dentro del propio dataset en vez de reutilizar
`fixtures/profiles/`: así la medición no depende de que el temario oficial cambie y los títulos de
los nodos se leen junto al caso que los pone a prueba.

## Qué es cada caso

15 casos, 75 ranuras (caso × eje). Cuatro intenciones declaradas en el campo `intent`:

| Intención | Cuántos | Para qué |
|---|---|---|
| `facil` | 8 | Señales claras y cita literal; mide el techo del motor y si sabe abstenerse en el resto de ejes. |
| `ambiguo` | 3 | Dos lecturas defendibles en el mismo eje; mide cómo se rompen los empates. |
| `sin_senales` | 2 | No hay nada que clasificar; mide que la abstención no se confunda con un acierto. |
| `donde_falla` | 2 | El motor se equivoca y se sabe por qué; mide el suelo y deja el fallo por escrito. |

| Caso | Intención | Qué pone a prueba |
|---|---|---|
| `facil-bases-convocatoria` | facil | Tres señales de tipo documental y procedencia oficial: convocatoria en el BOE, autoridad A. |
| `facil-plantilla-respuestas` | facil | Empate a 0,7 entre «plantilla de respuestas» y «examen oficial» en el eje documental. |
| `facil-pegado-apuntes-propios` | facil | Un pegado del usuario es material propio (`personal_notes`), no material de tercero. |
| `facil-guia-tecnica-reutilizacion` | facil | Acierto en un eje crítico (derechos) que **no** se aplica solo por ser crítico. |
| `facil-derechos-uso-privado` | facil | Un aviso de derechos no dice qué tipo documental es: abstención correcta en el resto. |
| `facil-guia-autonomica` | facil | Autoridad B (otra administración) frente a A (organismo convocante). |
| `facil-temario-oposicion-muestra` | facil | Código y nombre completo del cuerpo en el texto: oposición con confianza alta. |
| `facil-tema-vial` | facil | El segundo perfil del usuario: tema y cuerpo reconocidos sin el código del proceso (confianza 0,4). |
| `ambiguo-anexo-oficial-copiado` | ambiguo | Es el anexo oficial, pero la copia la hizo una academia. El motor empata y decide por orden alfabético. |
| `ambiguo-apuntes-para-el-foro` | ambiguo | **Fallo conocido**: «apuntes de» + «foro» dan `community_material` con 0,8 donde el humano dice `private_syllabus`. |
| `ambiguo-dos-temas` | ambiguo | **Fallo conocido**: dos títulos del programa coinciden igual (0,8) y gana el de ruta alfabéticamente menor. |
| `donde-falla-tema-sin-tipo` | donde_falla | **Fallo conocido**: el tema se reconoce, el tipo documental se queda sin ninguna señal. |
| `donde-falla-cita-de-resolucion` | donde_falla | **Fallo conocido**: una cita a una resolución se lee como si el documento fuera de esa autoridad. |
| `sin-senales-nota-cotidiana` | sin_senales | Nota cotidiana: cero propuestas en los cinco ejes (y la etiqueta humana también es nula). |
| `sin-senales-escaneo-sin-texto` | sin_senales | Escaneo sin texto (ni OCR): con cero texto, abstenerse es lo único honesto. |

## Reglas de etiquetado (por qué las etiquetas son como son)

- Una etiqueta `null` significa «aquí no hay nada que decir»: el motor debe abstenerse. Por eso el
  porcentaje «sin clasificar» se informa separado en abstenciones correctas y material sin cubrir;
  mezclados, el número no dice nada.
- La **autoridad** describe quién publica el material, no lo que el material cita: por eso
  `donde-falla-cita-de-resolucion` lleva `authority: null` aunque su texto mencione una resolución.
- Los ejes **oposición** y **tema** solo se pueden acertar si el material nombra el proceso o el
  título del programa; el dataset no da por supuesto que el motor adivine.
- La etiqueta es lo que debería quedar tras una revisión humana cuidadosa, **no** lo que propone el
  motor. Si un caso y el motor coinciden, es porque el motor acierta, no porque la etiqueta se copiara
  de su salida.

## Los fallos conocidos, y por qué son información y no un fracaso

El motor determinista mide señales léxicas: no entiende de intención. Los cinco fallos del dataset
actual son (números exactos en el informe y en las pruebas):

1. `ambiguo-apuntes-para-el-foro · document_type`: la señal «foro» (peso 0,4) se suma a «apuntes de»
   (0,4) y da 0,8 para `community_material`, por encima de «academia» (0,4, `private_syllabus`). Con
   0,8 el motor **aplicaría solo** la propuesta, que es el caso peligroso: no es un eje crítico, así
   que la banda alta sí decide. Es el hallazgo más útil de todo el dataset.
2. `ambiguo-dos-temas · topic`: dos títulos del programa coinciden al 100 % y el empate se rompe por
   la ruta (`IV.2` antes que `IV.5`), no por cuál pesa más en el texto. El motor no tiene forma de
   saber cuál es el tema principal, y lo dice: la alternativa queda guardada en la propuesta.
3. `ambiguo-dos-temas · document_type`: el nombre `resumen-sistemas-ejemplo.pdf` empieza por
   «resumen-» y para una persona es un resumen propio, pero la regla exige la cadena literal «resumen
   personal» (o «esquema propio»). El motor no reconoce prefijos del nombre del fichero.
4. `donde-falla-tema-sin-tipo · document_type`: «Tema 1. La Constitución Española…» no contiene
   ninguna de las cadenas del vocabulario documental (`convocatoria`, `temario oficial`, `programa
   oficial`…). Aquí la abstención es la conducta correcta del motor —no inventa—, y a la vez es un
   fallo real: el material se queda sin cubrir y cuenta como corrección necesaria.
5. `donde-falla-cita-de-resolucion · authority`: `resolución de <dígito>` (peso 0,5) propone
   autoridad A sobre un resumen personal que solo cita la resolución. Es un falso positivo en un eje
   crítico; la banda lo deja en la cola de revisión, nunca autoaplicado.

Los tres primeros son errores de precisión (se propone algo equivocado), el cuarto es un error de
recall (no se propone lo que hacía falta) y el quinto es una confusión de procedencia. Ninguno se
arregla subiendo un umbral a ojo: son la razón por la que existe este dataset.

## Cómo se mantiene

- Si cambia el motor, las pruebas de `test_classification_metrics.py` fallan. Se mira si la calidad
  mejoró o empeoró, se actualiza el número **con** la explicación y se anota en `docs/slices/S04.md`
  si el cambio de motor lo provoca.
- Si se añade un caso, se añade con su `note`, con las cinco etiquetas y con una intención válida; la
  carga del dataset rechaza un campo mal escrito, una etiqueta fuera del vocabulario del eje o una
  etiqueta que falte. Un caso nuevo «sin señales» que en realidad tenga señales sería una medida
  falsa, y eso es peor que no medir.
- Este dataset **no** es la muestra real: es una referencia reproducible para desarrollo. La puerta de
  calidad con material real (muestra copiada a mano) sigue pendiente de la muestra del usuario, igual
  que la calibración de las bandas (Q005).
