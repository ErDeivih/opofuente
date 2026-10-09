# Alinear en orden, y lo que dicen de verdad los cuadernillos (octubre 2026)

Veredicto en una línea: la rama `alinear-en-orden` **pasa las 18 puertas en Windows en una sola pasada
(21:29 minutos)** y está fusionada (`main` = `e4124b4`), pero **no desbloquea los seis exámenes
oficiales de 2025**, y no por un fallo del código: los datos guardados de esos cuatro conjuntos no
siguen el orden ni las reservas que imprimen los cuadernillos. Lo he medido contra los PDF oficiales
del INAP y el resultado está en §3 y §4.

## 1. Las puertas, en verde y en una pasada

Ejecutado con `.\scripts\gates.ps1` en la copia de prueba (rama `alinear-en-orden`, punta `e4124b4`),
con los puertos 8765 y 4173 libres (la puerta 18 no reutiliza servidores):

```
1 ruff format · 2 ruff check · 3 mypy · 4 eslint · 5 typecheck · 6 unitarias (583)
7 integración (491) · 8 contrato · 9 componentes (225) · 10 OpenAPI y tipos · 11 build backend
12 build frontend · 13 migración desde base vacía · 14 esquema con sqlite3 · 15 siembra
16 siembra idempotente · 17 fixtures frente a las fuentes · 18 E2E (54 pasan, 4.5 min)
Todas las puertas ejecutadas en 21:29 minutos.
```

Las 18 con su código de salida (`OK: … (código 0)`), y la E2E dentro del propio guion: ya no hay que
ejecutarla aparte porque la 17 está en verde desde el arreglo de las fuentes volátiles.

## 2. Qué trae la rama, comprobado

- **El lector ya no pierde las preguntas 1 a 9.** El PDF del INAP pone el número solo en una línea
  («1.») y la letra en la de abajo. Medido con el lector de la rama sobre las cuatro plantillas:
  `Plantilla respuestas TAI-L-A_act.pdf` pasa de **93 líneas** (empezando en la 10) a **135**; las de
  promoción interna dan 84 (una línea menos por el texto truncado, §4). La junta solo si la línea es
  **solo** un número y la siguiente **solo** una respuesta, así que un rótulo («Supuesto I») o un
  enunciado no se pegan.
- **La comparación en orden** (`ordered_key_mapping`) empareja la plantilla con las preguntas **en el
  orden del documento** cuando las dos secuencias de números son idénticas, y si no devuelve `None` y
  se sigue comparando por número. Se usa al importar la plantilla, en la ruta de enlace y en el enlace
  automático. Las pruebas nuevas fallan con `main` anterior y pasan con esta rama.

## 3. Por qué los seis exámenes oficiales siguen sin enlazarse

Medido con la API de la rama contra una copia de los datos (puerto 8766) y con el dominio de la rama
sobre la base real (`_oficial\medir_el_encaje_con_la_regla_nueva.py`):

| conjunto | preguntas guardadas | posiciones repetidas | líneas de la plantilla | emparejar en orden | enlace por API |
| --- | --- | --- | --- | --- | --- |
| TAI libre A / B | 135 · 135 | **0** | 135 · 135 | **no encaja** | 409 · 38 discrepancias |
| TAI promoción A / B | 85 · 85 | 0 | 84 · 84 | no encaja | 409 |
| Guardia Civil 2026 A / B | 121 · 120 | 20 | 3 (texto en columna) | no encaja | 409 |

El motivo es concreto: `ordered_key_mapping` exige que la secuencia de números de la plantilla
(1..80, luego 1..5, luego 1..20…) sea **la misma** que la de las posiciones de las preguntas guardadas.
En estos cuatro conjuntos las preguntas están numeradas **1..135 seguidas**, así que la comparación en
orden no se aplica (no hay números repetidos), se cae a la comparación por número —donde el «12» de la
segunda parte compite con el de la primera— y la ruta, con razón, se niega. La comparación en orden sí
sirve para conjuntos como los de Guardia Civil, que sí repiten numeración.

**Conclusión**: para enlazar estos exámenes hay que **reimportarlos con la numeración del cuadernillo**
(que reinicia en cada sección), no tocar el código otra vez.

## 4. Las reservas, contra el cuadernillo oficial

Los cuatro cuadernillos del INAP imprimen la misma estructura, y la plantilla oficial coincide con
ella: `PRIMERA PARTE` + `Preguntas de reserva` + `SUPUESTO I` + `Preguntas de reserva` + `SUPUESTO II` +
`Preguntas de reserva`, cada bloque de reserva numerando desde 1. Medido con
`_oficial\comprobar_las_reservas_contra_el_cuadernillo.py` (lee el PDF página a página, sigue el rótulo
vigente y exige numeración correlativa, para no contar números de dentro de los enunciados):

| examen | lo que imprime el cuadernillo | lo que hay guardado | preguntas mal marcadas |
| --- | --- | --- | --- |
| TAI libre A | 80 · 5r · 20 · 5r · 20 · 5r | 80 · 5r · 20 · **5r** · **15** · **10r** | **5**: 126-130 son normales (Supuesto II 16-20) y están como reserva |
| TAI libre B | 80 · 5r · 20 · 5r · 20 · 5r | 80 · 5r · **40** · **10r** | **10**: 106-110 son reserva (Supuesto I 1-5) y están como normales; 126-130 son normales (SII 16-20) y están como reserva |
| TAI promoción A | 50 · 5r · 12 · 3r · 12 · 3r | 50 · 5r · **24** · **6r** | **6**: 68-70 son reserva y están normales; 80-82 son normales (SII 10-12) y están como reserva |
| TAI promoción B | igual | igual | **6**: las mismas posiciones |

En total, **27 preguntas mal marcadas** en los cuatro exámenes. Ninguna de las reservas tiene
`reserve_order` declarado, así que la aplicación ordena por posición: la primera reserva que usaría una
sesión es la correcta (81-85 en libre, 51-55 en promoción), de modo que la sustitución por anulación no
se ve afectada; lo que sí pasa es que esas preguntas reales **no entran en el turno ordinario** y, en un
examen completo, se tratan como reserva.

## 5. Un hallazgo más: el orden guardado no es el del papel

Comparando **en orden** la clave activa de cada conjunto con las líneas de su plantilla
(`_oficial\comparar_la_clave_en_orden_con_la_plantilla.py`):

| examen | líneas que coinciden en orden |
| --- | --- |
| TAI libre A | 113 de 135 |
| TAI libre B | 116 de 135 |
| TAI promoción A / B | 22 y 25 de 84 |

Es decir: el orden en el que se guardaron las preguntas **no** es el de la plantilla (las respuestas
del Supuesto II aparecen antes que las reservas, por ejemplo). Eso no prueba por sí solo que la letra
de cada pregunta esté mal —cuando se comprobó pregunta a pregunta **por enunciado** contra el banco
oficial cosechado, coincidían 135 de 135—, pero sí dice que el banco cosechado y lo guardado comparten
el mismo orden, así que esa comprobación no valida el reparto por secciones.

Intenté comprobar el banco directamente contra el cuadernillo
(`_oficial\comprobar_el_banco_oficial_contra_el_cuadernillo.py`) y **no llegué a un resultado fiable**:
mi lectura automática de la numeración del papel se desvía en cuanto hay un número suelto dentro de un
enunciado (la página 4 del cuadernillo los tiene). Queda como trabajo pendiente, y es la razón de más
para rehacer la importación desde el cuadernillo en lugar de seguir parcheando.

## 6. Lo que hay que hacer, en orden

1. **Reimportar los cuatro exámenes de TAI 2025 desde el cuadernillo**: numeración por secciones (como
   la imprime), reservas marcadas como las imprime y `reserve_order` declarado. Con eso la comparación
   en orden funciona, la ruta enlaza las plantillas y las claves se pueden revisar contra el papel.
2. **Volver a meter las plantillas oficiales completas**: la de TAI libre que hay en la biblioteca tiene
   **1.216 caracteres** y se corta en la reserva 3 del Supuesto II (le faltan las dos últimas
   respuestas); entró antes del arreglo del recorte de 1.200 caracteres.
3. **Guardia Civil 2026**: sus conjuntos mezclan conocimientos e idioma con números repetidos y les
   faltan las 6 reservas (101-105 y la de idioma). Es el mismo trabajo de reimportación.
4. Cuando 1 y 2 estén hechos, **enlazar por la ruta nueva** (que ya compara en orden) y activar; las
   claves actuales siguen siendo válidas mientras tanto: están comprobadas contra el fichero oficial.

## 7. Cómo se reproduce

```
cd F:\temp-opofuente\opofuente-arreglos
.\scripts\gates.ps1                       # las 18 puertas, con los puertos libres

$py = ".\.venv\Scripts\python.exe"
$of = "F:\EspacioCodigo\proptech-access-control\docs\opofuente\_oficial"
& $py "$of\comprobar_las_reservas_contra_el_cuadernillo.py"        # §4
& $py "$of\comparar_la_clave_en_orden_con_la_plantilla.py"         # §5
& $py "$of\medir_el_encaje_con_la_regla_nueva.py"                  # §3
& $py "$of\ver_las_marcas_de_reserva_de_los_examenes.py"           # reservas y su orden
```
