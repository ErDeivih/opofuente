# Las puertas de la rama, y las fuentes que cambian en cada descarga (octubre 2026)

Veredicto en una línea: **la rama `arreglos-traspaso-material` se fusionó con las puertas 1 a 16 en
verde y la 18 (E2E) con 54 de 54**, y la puerta 17, que estaba en rojo por dos páginas oficiales que
cambian de bytes en cada petición, **quedó arreglada** marcando esas fuentes como volátiles y
comparando su texto: con ese arreglo, la ejecución completa de las 18 puertas pasa de una vez
(25:20 minutos). Las tres cosas que Claude arregló están comprobadas contra los datos del
propietario, no solo leídas en el diff.

Rama: `arreglos-traspaso-material`, punta `c6d4dd3`, 14 commits por delante de `main` y `main` cero
por delante: la fusión fue avance rápido. Copia probada: `F:\temp-opofuente\opofuente-arreglos`
(limpia, sin ficheros sin guardar). Después, la puerta 17 se arregló en la rama
`fuentes-por-contenido` (`e804513`) y se fusionó también.

## 1. Las puertas, una a una

Ejecutado con `.\scripts\gates.ps1` en la copia de prueba, con los puertos 8765 y 4173 libres (la
puerta 18 arranca su propia API y su propia vista previa, y **no reutiliza** servidores: si el puerto
está ocupado, la suite tiene que fallar y decirlo, DEBT-021).

| puerta | resultado | medida |
| --- | --- | --- |
| 1. ruff format --check | OK (código 0) | 334 ficheros ya formateados |
| 2. ruff check | OK (código 0) | All checks passed |
| 3. mypy (estricto) | OK (código 0) | 156 ficheros, sin incidencias |
| 4. eslint | OK (código 0) | — |
| 5. typecheck TypeScript | OK (código 0) | — |
| 6. unitarias backend | OK (código 0) | **574 pasan** (incluye `test_question_domain_alignment.py`, 4) |
| 7. integración backend | OK (código 0) | **491 pasan** en 18:44 (incluye `test_answer_key_link.py`, 6) |
| 8. contrato | OK (código 0) | 29 pasan |
| 9. componentes (Vitest) | OK (código 0) | **225 pasan** (18 ficheros) |
| 10. OpenAPI y tipos sincronizados | OK (código 0) | contrato y `openapi.d.ts` sincronizados |
| 11. build backend | OK (código 0) | sdist y wheel |
| 12. build frontend | OK (código 0) | 159 módulos, `dist` construido |
| 13. migración desde base vacía | OK (código 0) | — |
| 14. esquema migrado con sqlite3 | OK (código 0) | revisión `0024_dossier_snapshots`, 3 filas en `app_metadata` |
| 15. siembra desde base vacía | OK (código 0) | 345 entidades nuevas |
| 16. siembra idempotente | OK (código 0) | 346 sin cambios en la segunda pasada |
| **17. fixtures frente a las fuentes** | **FALLO (código 1)** en la primera ejecución · **OK (código 0)** tras el arreglo de §4 | 18 fuentes y 71 citas verificadas |
| 18. E2E (Playwright) | **OK (LASTEXITCODE 0)** | **54 pasan** en 4:42 (y en la ejecución final, dentro del guion) |

Cada «OK» dice ahora el código con el que se decidió, y la comprobación previa confirma que el
intérprete detecta un comando que falla (código 3 visto): el falso «OK» del 1 de octubre ya no puede
repetirse. La 18 incluye la prueba que antes fallaba siempre (`review.spec.ts:186`, modo estricto).

Ejecución final, ya con el arreglo de la 17, en una sola pasada y con los puertos libres:

```
.\scripts\gates.ps1
  … 1 a 16 OK · 17 OK (Fuentes verificadas: 18 · citas: 71) · 18 OK (54 pasan, 4.8 min)
Todas las puertas ejecutadas en 25:20 minutos.
--- FIN DE LAS PUERTAS (codigo 0) ---
```

## 2. Enlazar la plantilla oficial a una clave existente

Ruta nueva: `POST /question-sets/{set_id}/answer-keys/{key_id}/source`, con `null` para desenlazar.
Comprobado con la API de la rama contra una **copia** de los datos del propietario
(`F:\OpoFuente\datos-prueba-rama`, 2,44 GB), en el puerto 8766:

| lo que se intentó | respuesta |
| --- | --- |
| enlazar la plantilla de Guardia Civil a una clave de TAI | **409** · «el documento no tiene ninguna respuesta reconocible» |
| enlazar *su* plantilla (TAI-L-A) a la clave de TAI-L-A | **409** · «la plantilla y la clave no dicen lo mismo en 17 pregunta(s) (números 10, 12, 13…)» |
| desenlazar la clave activa de un examen oficial | **409** · «es la clave activa de un examen oficial: sin la plantilla enlazada no podría estar activa (activa otra antes de desenlazar esta)» |

La ruta hace lo que dice: comprueba antes de enlazar, se niega con los números cuando no cuadra, y no
deja desenlazar lo que dejaría un examen oficial activo sin plantilla. El enlace queda en la
auditoría (`answer_key.source_linked` / `answer_key.source_unlinked`, con el valor anterior y el
nuevo).

**Lo que hay que saber de la segunda fila**: no es que la clave esté mal. La clave de TAI-L-A está
comprobada **pregunta a pregunta y por enunciado** contra el fichero oficial del INAP (135 de 135
coinciden, ver el informe de claves de octubre). Lo que pasa es que la verificación de la ruta es
**por número**, y esa plantilla reinicia la numeración en cada sección (primera parte 1..80, reservas
1..5, supuesto I 1..20, supuesto II 1..20…), así que alineada por número cae en las preguntas
equivocadas. Con la regla nueva el encaje medido es:

| examen | líneas | emparejadas | ambiguas | preguntas | cubiertas | score | veredicto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TAI libre 2025 A / B | 93 | 93 | 0 | 135 | 71 | 0,526 | se rechaza |
| TAI promoción 2025 A / B | 47 | 47 | 0 | 85 | 41 | 0,482 | se rechaza |
| GC 2026 A / B | 3 | 0 | 0 | 121 / 120 | 0 | 0,000 | se rechaza |

Medido con `_oficial\medir_el_encaje_con_la_regla_nueva.py` (usa el dominio de la rama y la base real;
no toca nada). Consecuencia honesta: **los seis enlaces que hay no se podrían rehacer hoy desde la
interfaz**. Están bien hechos (comprobados contra el fichero oficial y activados por API), pero si una
convocatoria futura trae el mismo formato, la ruta nueva se negará.

Dos caminos, para decidir (no son excluyentes):

1. **Comparar en orden, no por número.** Estas plantillas se leen en el orden del documento y la clave
   se construyó en ese mismo orden: si las líneas de la plantilla coinciden **una a una y en orden**
   con las entradas de la clave, es su plantilla. Mismos guardarraíles (una discrepancia → 409 con el
   número de línea; menos del 95 % confirmado → 409), pero sin depender de la numeración.
2. **Leer bien la plantilla.** El analizador reconoce 93 de las 135 líneas de la plantilla de TAI-L-A
   porque el fichero pone el número y la letra en líneas distintas («1.» y debajo «c»). Eso solo no
   arregla el encaje (seguiría habiendo 135 líneas sobre 85 posiciones distintas), pero hace falta
   para cualquiera de las dos vías.

## 3. Preguntas sin respuesta en la clave activa

Comprobado contra la copia de los datos del propietario. Práctica por tema I.1:

> HTTP 201 · 175 preguntas · «Práctica de un tema: 175 pregunta(s) catalogadas en él (…). **1824 se
> quedaron fuera por no tener plantilla activa. 1 se quedaron fuera porque la plantilla activa no dice
> su respuesta** (sin entrada, anulada o en conflicto). 2 no se practican solas (reservas o tipo no
> soportado).»

Antes esa misma sesión se montaba con 2.002 preguntas, de las que 1.824 no se podían corregir: se
contestaban y no contaban. Ahora solo entran las que la clave activa corrige de verdad, y lo que se
queda fuera se cuenta en la nota. Los exámenes oficiales no cambian de tamaño (se hacen tal cual son y
el resultado ya declara lo que no puntúa), que es lo correcto: un examen no se recorta.

## 4. Puerta 17: por qué no puede ponerse verde hoy

Tres fuentes no coincidían con el `sha256` del manifiesto. Descargadas otra vez, **una a una**:

| fuente | hash del manifiesto | lo que se bajó esta mañana | descarga nueva de ahora | qué pasa |
| --- | --- | --- | --- | --- |
| `celador-2022-bocyl-orden.pdf` | `c1cbedf3…` | `66a9be9a…` | **`c1cbedf3…` = el del manifiesto** | la copia del repositorio estaba mal descargada: **se arregla volviendo a descargar** (ya hecho en la copia de prueba) |
| `gc-2026-oficial.html` | `241f6697…` | `3193f368…` | `a0cc0233…` (y otra vez `3193f368…`) | la página **cambia en cada petición** |
| `gc-nota-legal.html` | `b0b18f35…` | `625de9e5…` | `8ecb96c0…` (y otra vez `625de9e5…`) | la página **cambia en cada petición** |

La prueba de que esas dos son volátiles: **dos descargas seguidas, en el mismo minuto, difieren entre
sí** en 22 de unas 3.200 líneas (y en 9-27 bytes de tamaño), y lo que cambia son identificadores que el
gestor de contenidos inventa al renderizar (`id="grid_container"`, `data-cssid="sgrowcolumn_n167974"`).
Con eso, ningún `sha256` de bytes puede ser estable: actualizar el manifiesto con el de hoy **volvería a
fallar en la próxima descarga**. Y no es un problema usada por los perfiles: regenerando los programas
con las fuentes de ahora salen **idénticos** a los que hay en `fixtures/profiles` y **las 71 citas de
los perfiles siguen apareciendo en su fuente** (medido con
`_oficial\comprobar_las_fuentes_oficiales_que_cambiaron.py`, que salta la comprobación de hash **solo
en memoria**).

Elegida la primera opción (verificar por contenido), esto es lo que se hizo en la rama
`fuentes-por-contenido` (`e804513`, un commit, fusionado después):

1. El manifiesto puede marcar una fuente como `"volatile": true` y guardar su huella de contenido
   (`content_sha256`): el `sha256` del **texto visible** de la página (sin comentarios, `<script>`,
   `<style>` ni etiquetas, que es donde viven los identificadores volátiles), con los espacios
   colapsados. Se marcaron las dos páginas de la Guardia Civil.
2. `verify_sources` compara bytes en todas las fuentes **menos** en las volátiles, que se comparan por
   esa huella. Una volátil **sin** huella no se da por buena: la puerta falla diciendo que falta.
3. `--refresh-content` recalcula la huella y reescribe solo ese campo del manifiesto; antes **verifica
   las 71 citas** de los perfiles y no escribe nada si alguna ha desaparecido, para que «refrescar» no
   sea un permiso en blanco.
4. `scripts/fetch-sources.ps1` deja de dar error en esas dos fuentes: imprime `TEXT` y remite a la
   comprobación por contenido, que vive en un solo sitio (el Python).
5. La PDF del BOCYL de Celador 2022 **no** se marca: al volver a descargarla coincide con su `sha256`
   del manifiesto (dos descargas independientes dieron `c1cbedf3…`), así que la copia que había era la
   anómala. El repositorio ya documentaba que otro PDF del BOCYL sí es volátil, y aquel se resolvió no
   conservándolo como fuente.

Con eso, la puerta 17 pasa (`Fuentes verificadas: 18 · citas verificadas: 71 · fixtures
sincronizados`) y la ejecución completa de las 18 puertas termina en verde en una sola pasada.

## 5. Cómo se reproduce

```
# las puertas (con los puertos 8765 y 4173 libres: la 18 no reutiliza servidores)
cd F:\temp-opofuente\opofuente-arreglos
.\scripts\gates.ps1

# la puerta 17, fuente a fuente
.\scripts\fetch-sources.ps1 -VerifyOnly
uv run python -m opofuente.tools.build_profile_fixtures --check

# la huella de contenido de las fuentes volátiles (verifica las citas antes de escribir)
uv run python -m opofuente.tools.build_profile_fixtures --refresh-content

# ¿las fuentes que cambiaron cambian algún dato de los perfiles?
.\.venv\Scripts\python.exe ...\_oficial\comprobar_las_fuentes_oficiales_que_cambiaron.py

# ¿qué dice la regla nueva de encaje sobre los seis exámenes oficiales?
.\.venv\Scripts\python.exe ...\_oficial\medir_el_encaje_con_la_regla_nueva.py

# las tres cosas arregladas, contra una copia de los datos del propietario (puerto 8766)
$env:OPOFUENTE_DATA_DIR='F:\OpoFuente\datos-prueba-rama'; $env:OPOFUENTE_PORT='8766'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\api.ps1
python ...\_oficial\probar_la_rama_con_los_datos_del_propietario.py
```

## 6. Lo que queda

1. **Rehacer las claves a medias** de los 20 conjuntos flojos (7.876 preguntas sin corregir hoy), que
   es lo que de verdad falta para poder practicar: la clave del conjunto de 1.547 preguntas cubre 200.
2. **Guardia Civil 2026**: añadir las 6 reservas que faltan (101-105 y la de idioma), renumerar el
   bloque de idioma y activar.
3. **Enlazar plantillas de exámenes que reinician numeración** (§2), si se quiere que la ruta nueva
   sirva también para esta convocatoria.
4. **5.249 preguntas sin tema** y **3.067 documentos sin asignar** al programa de TAI.
