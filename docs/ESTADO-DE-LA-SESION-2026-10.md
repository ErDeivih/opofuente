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
