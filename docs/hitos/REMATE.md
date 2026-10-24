# El remate de la fase 3, punto por punto

**De:** DeepSeek · **Para:** Claude, por delegación del propietario · **24 oct 2026**
**Documento que manda:** `docs/FASE-3-REMATE-2026-10-24.md`

**Base de partida:** `main = 20d24fe` (el documento del remate commiteado).

Aquí se apunta **lo que se decide y por qué**, para que la decisión se pueda revisar o deshacer sin
reconstruirla. **Un punto solo se da por hecho cuando se cumple en la base real y en la app que
arranca `scripts\api.ps1`**, no en una siembra de pruebas.

---

## Punto 1 · Las 5.939 explicaciones privadas, archivadas

### Lo que pasó, medido

```
copia antes de M1:  11.315 privadas + 1.609 generadas
base real después:   5.376 privadas + 9.007 generadas
```

**`--sustituir-lo-privado` reemplazó 5.939 privadas en la misma fila.** Comprobado fila a fila: **el
`id` no cambió** — la generada ocupó la fila de la privada — y **el texto original solo quedaba en la
copia**.

### La decisión: se archivan, no se borran

**Estado nuevo `archived` + el único por pregunta pasa a parcial.** **La privada y la generada son
la misma fila hoy**, así que archivar **no puede ser un `update`**: hay que insertar una fila nueva,
y para eso hacen falta dos cosas que la 0047 añade:

1. **el `CHECK` de estados tiene que admitir `archived`** — hoy solo admite `draft`, `reviewed` y
   `rejected`, así que el original **no se habría podido guardar**;
2. **el único `uq_explanation_question` tiene que dejar de cubrir las archivadas** — si no, la
   segunda fila de la misma pregunta choca.

**Sigue habiendo una sola explicación viva por pregunta**: el índice pasa a cubrir
`option_stable_key IS NULL AND status <> 'archived'`. **Y lo que se sirve no cambia**: `explanations_of`
filtra las archivadas.

### Lo que se hizo

- **`0047_explicaciones_archivadas`**: reconstruye la tabla **a mano**, con el `CREATE TABLE` entero.
  **No con `batch_alter_table`**: el modo por lotes refleja la tabla con SQLAlchemy, y **SQLAlchemy
  no refleja los `CHECK` de SQLite**, así que habría borrado `ck_explanation_origin`,
  `ck_explanation_text` y `ck_explanation_generated` **sin que nadie lo notara al día siguiente**.
- **`tools/recuperar_explicaciones_privadas.py`**: copia las privadas de la copia a la base real con
  `status = 'archived'`, con comprobación de referencia **fila a fila**, `--aplicar` obligatorio para
  escribir, e **idempotente** (relanzarlo no duplica).
- **La instantánea verificada**: `base-real-20261024-222022-antes-de-recuperar-privadas.sqlite3`,
  2.641,7 MB, `integrity_check ok`.

### La cifra, contada en la base real

```
revision            0047_explicaciones_archivadas
explicaciones       20.322
  generadas          9.007
  privadas          11.315   <- las 11.315 de antes de M1, todas
estado
  draft             14.383
  archivadas         5.939   (todas privadas)
vivas por pregunta       0   (ninguna pregunta con dos vivas)
preguntas que el alumno ve con explicación   14.383   (las mismas que antes)
```

**Y relanzar el importador da `candidatas: 0`.** **La decisión se puede deshacer**: bajar la 0047
borra las archivadas y vuelve la tabla anterior (dicho en el `downgrade`).

### Dónde se apuntó

- **`DEBT.md`**: la entrada de la sustitución, cerrada con su cifra.
- **`PARA-EL-PROPIETARIO.md`**: qué se recuperó y cómo se deshace.
