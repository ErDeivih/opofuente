# Estado de la sesión, para retomar sin preguntar (13-oct-2026)

## 13-oct · lo que ha cambiado hoy (leer esto primero)

**Autoridad nueva: `docs/AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`** (manda sobre el goal si choca):
claves fiables, incidencias bien clasificadas y **el ritmo**: el contenido de apuntes **no** lleva batería de
18 puertas, se decide con las **puertas de datos** del tema.

`main` = **`d67e799`** · gasto **≈10,58 $ de 40** (aviso de los 10 $ cruzado) · base real en **`0036`**.

1. **Claves (f19, en `main`)**: discrepancia apuntes↔clave por conjunto, medida: **528/5.925 = 8,91 %**.
   **10 conjuntos `no_fiable`** (>30 %) · **6 `dudosa`** (15–30 %) · 16 veredictos cambiados con auditoría.
   **1.117 preguntas fuera de tests, simulacros, repasos y del denominador de cobertura**; 984 dudosas
   entran con la marca. Migración `0036` (`key_reliability`) + **puerta permanente** al cerrar cada tema.
   La marca **«clave en revisión» ya se ve** en el test en curso y en los resultados (el campo del alumno es
   **`in_review`**, no `key_in_review`: el vocabulario interno no sale del servidor). **Claves arregladas:
   cero** — el desplazamiento no las explica (probado entero) y las derivadas no se han empezado. El INAP
   2024 A **es el modelo A** y su **numeración no cuadra** (faltan 2 preguntas oficiales, 0 reservas, 7
   posiciones discrepan y **3 anuladas llevan clave**): incidencias del propietario; la oficial **no se toca**.
2. **Incidencias (f18, en `main`)**: pantalla **`/admin/incidencias`** con contador, tres enlaces y cuatro
   estados con nota auditada (migración `0035`). Las 453 reclasificadas: `pregunta_mal_importada` 29 ·
   `clave_no_fiable` 158 · `clave_sospechosa` 200 · **`norma_cambiada` 0** · `hueco_sin_material` 34 ·
   `pregunta_ambigua` 9 → **430 en la bandeja**, 23 falsos positivos fuera y **18 irreparables al temario
   fuera**.
3. **§3 re-medido**: I.6 **71,1 %** · I.4 **88,9 %** · I.8 **82,0 %** — **ninguno cruza el 90 %**, y la
   cuarentena **no regala cobertura: la limpia** (la mayoría de las que salen estaban cubiertas).
4. **La base real estaba en `0034`**: la cuarentena estaba **en el código, no en los datos**. Aplicadas
   `0035` y `0036` y poblados los veredictos por la vía auditada (actor `f19:puerta-de-claves`).
   **Lección: una puerta que solo existe en el código no protege los datos.**
5. **«Dos temas a la vez» NO se puede**: el motor tiene **una marca única de corrida sin el tema dentro**
   (`run_lock.py`): la segunda corrida se niega **antes de llamar al modelo**. Abrirlo por tema es un cambio
   de motor, propuesto y no hecho. **Un tema a la vez.**
6. **En vuelo**: **f20** (ficha de pregunta con «marcar la correcta», árbol `opofuente-preguntas`) y **f21**
   (contenido: I.7 corriendo; índices ensayados de **IV.5 98,4 %**, **III.9 90,2 %**, **I.5 88,2 %**; **III.4
   no se escribe**: solo 237/405 grupos (58,5 %) son de su materia — es un problema de clasificación).
7. **Pendiente con nombre**: la aserción de las capturas del alumno (**escrita y NO ejecutada**: el puerto
   8765 lo tenía el bloque de la ficha); las **claves derivadas** (corrida + marca nuevas); **la fila por
   conjunto** en la bandeja del propietario; la pantalla de **Tests**; `origin_scope` + INAP; D4; D11; y una
   **copia verificada final**.

### Cierre de la tarde del 13-oct · el ritmo nuevo, medido

**Nueve temas publicados** y **cuatro en borrador con su motivo medido**. Lo de esta tarde, sin una sola
batería de 18 puertas (el §4 tenía razón: generar apuntes **no cambia el programa**):

| tema | cobertura (clave utilizable) | coste | previsión |
|---|---|---|---|
| **IV.5** | 367/377 = **97,3 %** | **0,5452 $** | 0,51–0,88 $ |
| **I.5** | 344/377 = **91,2 %** | **0,8966 $** | 0,41–0,71 $ (se cruzó) |
| **III.9** | 328/341 = **96,2 %** | **0,4961 $** | 0,43–0,73 $ |
| **IV.6** | 288/297 = **97,0 %** | **0,3916 $** | — |

**Cuatro temas publicados por 2,33 $** (media ≈0,58 $/tema). **I.7 quedó en borrador** con dos motivos:
cobertura 291/498 = **58,4 %** y **la corrida la cortó su tope de tiempo** — su coste, 1,1903 $, **cruzó la
previsión** (0,49–0,85 $) porque el tema tiene **133 preguntas sin clave clara**: los temas con claves
dudosas cuestan más y publican menos, y eso ya se ve **antes** de pagar. **Es reanudable sin volver a
pagar** lo escrito. **Frontera de tema publicada**: IV.6 a las 20:02; el siguiente (**III.1**) lanzado a las
20:01. Gasto acumulado **≈14,1 $ de 40**.

**Aprendido midiendo (tercera vez el mismo patrón)**: en la segunda mitad de una corrida **el contador
global de anclas se mueve a saltos** (las comprobaciones se escriben por lotes de 10), así que en una
ventana de quince minutos puede parecer congelado **sin estarlo**; el contador **del nodo del tema** sí lo
pilla. Y `.out.txt` a 0 B durante toda la corrida **no es señal**. Lo que decide es **el contador por
tema**, no el global ni el fichero.

### Cierre de la noche del 13-oct · el estado y un aviso de disco

- **15 de 33 temas publicados** y 4 en borrador con motivo medido. Lo de la tarde: **ocho temas publicados
  por 3,58 $** (media 0,45 $), coberturas del 91 % al 99 %, **sin una sola batería de 18 puertas**. La
  previsión se queda **corta en los normativos densos** (cuestan el doble por llamada) y **larga en los
  técnicos** (es un techo). Cuatro veces una reparación de **0 $** evitó repetir una corrida.
- **La cuarentena entró sola** cuatro veces más al cerrar cada tema: **105 conjuntos medibles y 14 en
  cuarentena** (eran 10 al empezar la tarde). **La bandeja del propietario: 603 incidencias.**
- **Zona del alumno cerrada**: la **pantalla de Tests** ya existe (18/18) y los tres enlaces que le
  apuntaban (`?count=20`, `?tema=X`) funcionan. Queda sin hacer, medido y escrito: «Ver en apuntes» desde
  el test, «Repetir solo las falladas» (el filtro `failed` ya está en el motor), 2 de las 3 pestañas del
  tema y el buscador/marca de leído/modo repaso dentro del tema. **La revisión de apuntes en el panel
  sigue pendiente.**
- **INAP**: **18 exámenes importados**, 4 ya estaban (sin duplicar) y **6 fuera con motivo** —entre ellos
  los tres de 2018, que **son escaneos sin capa de texto y necesitan OCR**—. `origin_scope` en los datos.
- **AVISO DE DISCO**: `F:` llegó a **0 GB libres** al verificar una copia (la extracción necesita 2,7 GB
  más). Se liberaron 6,3 GB borrando los restos de esa extracción y la copia del 10-oct. **`F:` tiene
  ~6 GB y la base pesa 2,72 GB**: hay margen para trabajar, **no para otra copia del árbol entero**
  (pesa 4,08 GB, porque incluye fuentes y PDF; la base sola es 2,72 GB). **Antes de la copia final hay
  que hacer sitio o copiar solo la base.**
- **Sin fusionar todavía**: el bloque del INAP (`f23-inap`), que espera su turno de puertas.

---

# Estado de la sesión, para retomar sin preguntar (12-oct-2026)

Escrito por DeepSeek al **parar el bucle a petición del propietario**. Aquí está lo que hay, lo que está a
medias y lo primero que hay que hacer al volver. Todo lo que va con cifra está **medido**, no heredado.

---

## 1. Punto de partida al volver

```
main = b33a22b        (tandas f14, f15, f16 y f17 dentro; 48 ficheros sucios son del OTRO agente: no tocar)
base real = F:\OpoFuente\datos\opofuente.sqlite3    · revisión 0034
copias verificadas = 20261010-153147-1b6311.zip y 20261010-110733-6e5035.zip  (las dos buenas)
gasto de API = ≈10,58 $ de 40    (el aviso de los 10 $ ya está cruzado y anotado)
F: libre = ≈20 GB
```

**Lo primero, sin excepción:** hay una rama **con trabajo a medias y sin commitear**, ver §4.

---

## 2. Lo que está entregado y funcionando

- **Zona del alumno completa** (bloque B): Inicio, Temario, Tema con apuntes, Test en curso con hoja de
  respuestas, Resultado, Simulacro, Exámenes oficiales, Fallos, Progreso. Verificada a 390 px, 0 fallos de
  accesibilidad, con sus capturas. **Falta solo la pantalla de Tests** (elegir temas y cuántas).
- **Panel (bloque C), empezado y con dos pantallas en `main`**:
  - `/admin/avisos` — **la bandeja del alumno** (lo que él marca con «Esto está mal»): se ve, se despacha
    con nota y se audita. Migraciones `0033`/`0034`.
  - `/admin/no-son-preguntas` — los enunciados rotos con su motivo: **769 `enunciado_roto` + 325
    `otra_administracion`**, contados en la base.
- **Apuntes (bloque A): 5 temas publicados y 3 en borrador con motivo medido.**

| Tema | Cobertura (clave utilizable) | Estado |
|---|---|---|
| IV.7 · I.1 · I.2 · **IV.2** · **II.4** | 95,8 % · 98,5 % · 95,2 % · **99,9 %** · **95,9 %** | **publicados** |
| I.6 | 72,5 % (techo medido 84,1 %) | borrador |
| I.4 | 88,9 % (le faltan 7 preguntas) | borrador |
| I.8 | **82,0 % (suelo: la corrida se paró a 389/442 grupos)** | borrador, **reanudable** |

- **Datos (bloque D), hecho**: base migrada a `0034` (**el botón «Esto está mal» ya guarda**, verificado en
  la tabla); **12,2 GB liberados** con las cinco copias comprobadas (todas buenas, ninguna cortada);
  **32 exámenes del INAP descargados y verificados** con manifiesto en `F:\OpoFuente\fuentes\inap-tai\`.

---

## 3. El precio real de un tema (lo que gobierna lo que queda)

**0,70 $ un tema técnico · 1,21 $ uno normativo y denso.** El 70 % de los tokens de entrada vienen de
**caché**. Con ese precio, **los 25 temas que faltan caben en los ≈29,4 $ que quedan**: no hay que subir el
presupuesto. (Las tres estimaciones anteriores de esta sesión fueron demasiado agoreras; esta está medida.)

Herramientas que hay que usar **en este orden** y que ya existen: `--esquema`/ensayo del reparto (0 $),
`--prever` (0 $, dice llamadas **y euros**), la corrida con `--tiempo-maximo`, `--limpiar-forma` (0 $,
repara títulos y tuberías), `--publicar` (0 $, mide lo guardado). **Nunca repetir una corrida por un
defecto de forma**: la limpieza es gratis y ya ha publicado un tema así (II.4).

---

## 4. LO QUE ESTÁ A MEDIAS (esto es lo primero al volver)

**Rama `f18-panel-incidencias`, creada desde `8d831af`, con ~15 ficheros SIN COMMITEAR.** El bloque es
**la bandeja del motor**: las incidencias que el propio sistema detecta al escribir los apuntes y que hoy
solo se ven abriendo la API. El agente fue parado a mitad.

Lo que ya está hecho en el árbol (sin commitear): migración **`0035_incidencias_despachables.py`**,
`api/notes_incident_schemas.py`, cambios en `api/__init__.py`, `api/deps.py`, `main.py`,
`infrastructure/db_models.py` y el contrato `packages/contracts/openapi.json`. **Falta la pantalla**, sus
pruebas, las capturas y las puertas.

**Decisión ya tomada y razonada por el agente** (reversible, §1.2): `notes_incidents` **no tiene estados**,
así que `0035` añade `status`, `resolution_note` y `reviewed_at` **con el mismo vocabulario que la bandeja
de avisos** (`open`/`in_progress`/`reviewed`/`dismissed`), con CHECK e índice y **sin tocar el motor**: su
escritor ignora las columnas nuevas, así que la decisión del propietario **sobrevive a una corrida que
vuelva a señalar lo mismo**. Limitación que él mismo anotó: si el motor resuelve la incidencia, la fila se
borra y con ella la nota (el evento de auditoría la conserva).

**Cifras medidas de esa bandeja** (leídas de la base real, `mode=ro`):

```
total 453 · norma_cambiada 291 · clave_sospechosa 110 · hueco_sin_material 40 · pregunta_ambigua 12
por motivo: clave_contradice_la_norma 291 · letra_no_coincide 110 · sin_frase_en_los_apuntes 40 ·
            clave_sin_definir 8 · sin_materia_en_el_indice 4
por tema: I.2 99 · II.4 84 · I.6 63 · I.1 61 · IV.7 55 · I.4 55 · IV.2 36
```

`section_key` está **vacío en las 453**, pero **el ancla casa en 449/453** con la de `topic_note_sections`:
el enlace al apartado exacto se hace por el ancla, como en la bandeja de avisos.

**Al volver, en este orden:** (1) entrar en `opofuente-clasif`, comprobar la rama y **commitear lo que hay**
(o descartarlo diciendo por qué) para no perder el reconocimiento; (2) terminar la pantalla con sus pruebas
que fallan antes; (3) capturas con **la copia** de la base (`F:\temp-opofuente\f18-datos`, 2,7 GB, se puede
borrar), **nunca la real**; (4) puertas 18/18 con registro en `gates-f18-panel-incidencias.txt`; (5) fusionar.

---

## 5. Lo que queda, por orden de valor

1. **Los 25 temas de apuntes** (bloque A). El 7.º por valor es **I.7 (550 con clave utilizable)** y **no
   tiene catálogo**: lo primero es escribirlo y ensayarlo (0 $). Después, la tabla de valor §4d.
2. **I.8 se puede reanudar** sin volver a pagar por lo escrito (faltan 53 grupos por comprobar + el bucle).
3. **La pantalla de Tests** del alumno (elegir temas y cuántas): su entrada ya existe y dice qué hará.
4. **El resto del panel**: la ficha de pregunta, la revisión de apuntes, el temario del panel.
5. **D10 · los exámenes del INAP**: están descargados, pero **`origin_scope` NO existe en el código**
   (columna + migración + esquemas + relleno + uso en el simulacro) y hay que construirlo antes de
   importar. Avisos: los 4 exámenes de TAI 2025 **ya se importaron** en su día (migración `0026`, 8 filas
   para 4 exámenes) y **3 cuestionarios de 2018 necesitan OCR** (Tesseract no está instalado).
6. **D4** · los 30 hechos con `epigraph_code` mal guardado: `topic_facts.reassign_epigraph`, actor
   `f10:epigrafes`.
7. **D11** · la entrega antigua `s14-promover-sin-guardar`: una pasada por las puertas; si 18/18, fusionar;
   si no, a `DEBT.md` y no volver.
8. **Copia verificada nueva** en la revisión actual (`0034`): las dos que se conservan son anteriores, y
   eso se dijo al propietario. Hacerla cuando ningún bloque esté escribiendo la base.

**Dos discrepancias anotadas y sin tocar** (son decisión del propietario): el §2.3 pide **≤3 %** de
párrafos casi repetidos y el código aplica **≤5 %** (lo medido no aprieta: 0,2–0,3 %); y la puerta
**«hechos fuera de su materia (≤3 %)» sigue sin implementar**.

---

## 6. Reglas y trampas que no hay que volver a aprender

- **Cinco trampas de las puertas**: nada de tuberías para `gates.ps1`; el registro con
  `Start-Process -RedirectStandardOutput`, **nunca** con `>`; `data\sources` en todo árbol nuevo; el puerto
  8765 libre para la E2E; **`DEEPSEEK_API_KEY` no se hereda al proceso hijo** (leerla del ámbito de usuario
  en cada comando).
- **El avance se mide con el contador que el motor escribe**, no con un proceso ni con un fichero:
  - en la **primera** mitad de una corrida de apuntes, `topic_note_sections` (apartados) y `topic_facts`;
  - en la **segunda**, **`question_note_anchors`** (anclas). Mirar los apartados ahí hace creer que está
    parada cuando está comprobando;
  - **`corrida-<tema>.out.txt` está a 0 B toda la corrida** (el comando no vacía la salida hasta el final):
    **no es una señal**. El lanzador `uv` marca 0 s de CPU **siempre**: tampoco lo es.
- **Una cifra que va a un documento se mide, no se hereda.** De ahí salieron tres errores en esta sesión y
  sus remedios: la cola agrupada por pregunta, la guarda de corrida (`apuntes_en_curso`) y las cifras
  contadas en la base (333 incidencias, 769+325 enunciados rotos, 453 incidencias del motor).
- **Arreglar el código o la pantalla, no la prueba.** Y nada de reintentar hasta el verde: si una prueba
  falla a veces, se demuestra **ajena e inestable** con evidencia (pasando en aislamiento, su fichero
  entero y la corrida siguiente) y se anota; fue el caso de `test_changes.py` en f16.
- **Un fallo de puerta se cuenta siempre, con su causa**, aunque se arregle después.
- Copia **verificada** antes de cualquier escritura masiva; escribir en los datos **solo por rutas
  auditadas**; **un bloque a la vez**; **18/18 para fusionar**.
- **No commitear en `main` mientras un bloque tenga su rama abierta**: obliga a fusionar con merge en vez
  de avance rápido (pasó al documentar la sesión). Y en `opofuente-main` hay **48 ficheros sin commitear
  del otro agente**: no se tocan ni se commitean.
