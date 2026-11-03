# Informe de diagnóstico — candidata de OpoFuente

**Task:** `task_afe170bc38ef` · **Dispatch:** `ctx_77e71905a7d0` · **Run:** `run_8eed83a73d15`
**Evidencia recogida:** 30/10/2026, sobre el workspace `C:\Users\David\orca\workspaces\opofuente\equipo-ia`.
**Alcance:** diagnóstico y preparación. **No** se ha implementado producto, **no** se ha ejecutado E2E completo,
**no** se ha tocado la base real, **no** se ha hecho commit, push ni despliegue.

---

## 1. Estado del árbol

| Dato | Valor |
|---|---|
| Rama | `ErDeivih/equipo-ia` |
| HEAD | `6483111dfd7e7939aabb260cd28abd98b146f5c2` |
| `tree_hash` | `78c9c8811c088ecf210cb274cfadadd5f4e5f9dca65112e0718291bf827ab98d` |
| `status_porcelain` | vacío |
| `diff_stat` / `cached_diff_stat` | vacíos |
| Tras los gates | `subject_changed_after_gates: false` |

El árbol estaba limpio antes de empezar y sigue limpio salvo este informe. No hay WIP ajeno
mezclado. `docs/hitos/SIGUIENTE-PASO.md` documenta `main = c3b4c6a` «más el commit de este cierre»;
el HEAD de este worktree es `6483111`, distinto. Con las herramientas disponibles (`git_estado`,
sin shell) **no se puede verificar la relación exacta entre `6483111` y `main`**; por tanto no se
afirma que este árbol sea la rama integrada ni que sea la candidata publicada.

---

## 2. Puertas ejecutadas

### 2.1 Unitarias de la API — ROJA por entorno

- **Gate:** `648dc9aeae21` · `uv run --frozen pytest apps/api/tests/unit -q`
- **Resultado:** `ok: false`, **exit code 4**, **18,84 s**.
- **Señal:** `ModuleNotFoundError: No module named 'argon2'`
- **Dónde falla:** al cargar `apps/api/tests/conftest.py` → `opofuente.main` →
  `opofuente.infrastructure.password_hashing` → `from argon2 import PasswordHasher`.
- **Evidencia:** `F:\EspacioCodigo\flujo\estado\orca-evidencias\0aa245de42c9971e6dd8dff46a420ddef59781caa228088137c505fb4b189738.json`
  (y una segunda idéntica, `74dfb035…`).
- **Diagnóstico:** `pyproject.toml` **sí declara** `argon2-cffi>=25.1.0` (línea 9). El fallo es del
  **entorno del sandbox**, que no tiene instalada la dependencia declarada; **no es un fallo del
  código del producto**. Aun así, la puerta **no está verde** y no se puede declarar verde por
  inferencia.

### 2.2 `gates.ps1` · 18 puertas — NO EJECUTADA

- **Gate:** `9df85043f3a0` · `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/gates.ps1`
- **Motivo:** dura ~54 minutos, incluye E2E y el encargo prohíbe la suite E2E completa. Además
  heredaría el mismo fallo de entorno de `argon2`. **No hay medición 18/18 sobre este árbol.**

### 2.3 Typecheck y lint del frontend — NO EJECUTADOS

- Los scripts existen en la raíz: `typecheck:web` (`npm run typecheck --workspace @opofuente/web`)
  y `lint:web`.
- **No hay puerta registrada** para ellos en `contexto_proyecto` (solo están `648dc9aeae21` y
  `9df85043f3a0`), y el shell no está disponible para esta sesión. `apps/web/package.json` queda
  fuera de las fuentes públicas autorizadas, así que tampoco se puede leer su script exacto.
- **No se afirma `tsc 0` ni `eslint 0`**: las cifras de la documentación (`487 pruebas`, `tsc 0`,
  `eslint 0`) son históricas y no se han re-medido aquí.

### 2.4 E2E / puerta 18 — NO EJECUTADA, rojo conocido

No se ha ejecutado. La documentación previa registra un fallo **preexistente** de la puerta 18:
timeout en `tests/e2e/review.spec.ts:397` y E2E-03 de accesibilidad (~36 s). Se cita como
antecedente documental, **no como medición de hoy**.

### 2.5 Migración desde cero — NO EJECUTADA

No hay puerta de migración registrada y no se ha ejecutado ninguna. El esquema que citan los
documentos es `0048`; no se ha verificado contra una base nueva en esta sesión.

---

## 3. Estado real del producto frente a lo documentado

Hay una **discrepancia documental importante**: `docs/hitos/SIGUIENTE-PASO.md` está desactualizado.
Dice que el punto 5 solo está «diagnosticado» y que 6-9 están «sin empezar», pero el código y
`docs/hitos/LO-QUE-VE-EL-ALUMNO.md` muestran otra cosa.

| # | Punto | Estado comprobado | Evidencia |
|---|---|---|---|
| 1 | Tarjetas al alumno | **Parado por criterio propio**: contraste a ciegas 80 % (< 90 % exigido). 9 tarjetas activas, 5.274 en borrador. No re-medido hoy. | `SIGUIENTE-PASO.md`; `tools/activar_tarjetas.py`; `db_models.py` (`draft_reason`) |
| 2 | Pantalla de repaso | **Hecho** (documentado). | `LO-QUE-VE-EL-ALUMNO.md` |
| 3 | Fallos vencidos en la cola | **Terminado** (documentado): tope compartido de 60, corrección sin sesión, 4 fallos sin clave fuera. | `LO-QUE-VE-EL-ALUMNO.md` |
| 4 | «Hoy», de verdad | **Parcial**: están «Continuar», «Repaso: N», «Repasar fallos (N)» y las barras de progreso. **Falta el enlace «Seguir leyendo»**. El dato ya se registra: `lib/ultimoApartado.ts` y `TopicNotesPage.tsx` guardan tema/capítulo/apartado en `localStorage`, pero `leerUltimoApartado()` **no se usa en ninguna pantalla** y `HoyPage.tsx` no lo importa. | `apps/web/src/lib/ultimoApartado.ts`; `TopicNotesPage.tsx:84-103`; `HoyPage.tsx`; `grep` sin uso fuera de la librería |
| 5 | Simulacro en dos partes | **Hecho**: `part_code` viaja en `SessionQuestionView` (`study_models.py:92`), en los tipos del alumno (`studentTests.ts:79,125,176`), la hoja separa partes (`AnswerSheet.tsx`) y el resultado pinta la tabla por parte (`ResultPage.tsx`). | Código citado |
| 6 | Contraste de las 450 claves | **Aplicado**: 4 preguntas fuera de su supuesto, sin reserva interna, sin cuarentena. | `LO-QUE-VE-EL-ALUMNO.md:352-406` |
| 7 | Guardián de capturas | **Hecho**: `apps/web/tests/screens/siembra.ts`, frases extraídas de fixtures y `CapturaSembrada`. | `LO-QUE-VE-EL-ALUMNO.md:410-452` |
| 8-9 | Recorrido/capturas y cierre 18/18 | **Sin evidencia en los documentos leídos** y sin medición actual. No se pueden dar por hechos. | — |

**Conclusión:** el pendiente funcional más claro del punto 4 es pequeño (pintar «Seguir leyendo» con
`leerUltimoApartado()`), pero **no se ha implementado en este encargo**.

---

## 4. Bloqueos antes de llamar «desplegable» a la candidata

1. **Entorno del sandbox:** falta `argon2` (dependencia declarada). Sin arreglar esto no hay puerta
   unitaria verde ni batería 18/18 posible.
2. **Puerta 18 en rojo conocida:** timeout de `review.spec.ts:397`; no se ha re-medido, pero no consta
   arreglada.
3. **DEBT-003 (derechos):** el temario de la Guardia Civil está versionado en los fixtures y su
   licencia es de uso privado. `docs/DEBT.md:177-181` prohíbe publicar, alojar o distribuir la
   aplicación con ese temario hasta retirarlo o contar con autorización expresa. **Es una condición
   previa de producto/legal, no un bug de código.**
4. **Invariante loopback:** la aplicación escucha solo en `127.0.0.1` por diseño, no tiene login y la
   cookie va sin `Secure`. Publicar en una interfaz accesible exige cambiar el modelo de seguridad
   (auth, HTTPS, cookie segura, CORS/Origin), no solo abrir el host. `docs/OPERACION.md:17-22` y
   `docs/DEBT.md:79-116` lo respaldan.
5. **Cifras de frontend sin re-medir:** no hay puerta registrada de `typecheck`/`lint`, así que
   `tsc 0` y `eslint 0` no se pueden afirmar sobre este árbol.

---

## 5. Recomendación y siguiente paso

1. **Desbloquear el sandbox**: sincronizar el entorno con las dependencias declaradas
   (`uv sync --frozen` o equivalente del arnés) y repetir `648dc9aeae21`. Después, ejecutar
   `9df85043f3a0` en una ventana que permita los 54 minutos (o una variante sin E2E, si existe como
   puerta registrada).
2. **Registrar puertas de frontend** (`npm run typecheck:web` y `npm run lint:web`) para poder
   re-medir `tsc`/`eslint` sobre el árbol exacto.
3. **Cerrar el punto 4**: añadir en `HoyPage.tsx` el enlace «Seguir leyendo» usando
   `leerUltimoApartado()` y `enlaceDeUltimoApartado()`, con prueba de componente. Es la única pieza
   funcional que el código ya casi tiene.
4. **Actualizar `SIGUIENTE-PASO.md`**: refleja un estado anterior (punto 5 diagnosticado, 6-9 sin
   empezar) que ya no coincide con el árbol.
5. **No declarar la candidata desplegable** hasta resolver DEBT-003, el modelo loopback/auth y tener
   las puertas verdes sobre el árbol exacto. El despliegue a producción sigue siendo decisión de
   David y no se ha tocado.

---

## 6. Prueba manual

No se ha arrancado la aplicación ni se ha usado la base del propietario. No hay prueba manual que
declarar; sería inventarla.

## 7. Limitaciones conocidas de este informe

- Sin shell: no se pudo instalar la dependencia que falta ni ejecutar `npm`, `uv` o `git log`.
- `apps/web/package.json`, `scripts/` y `apps/web/tests/` no son legibles por la política de fuentes;
  los scripts se citan por el `package.json` de la raíz y los tests del frontend no se han podido
  inspeccionar.
- Las cifras de producto (9 tarjetas, 5.274 borradores, 4 preguntas fuera, etc.) se citan de la
  documentación; solo el código y el estado git se han verificado directamente.
- El gate unitario se ejecutó una vez y falló en la recolección; no se repitió para no duplicar
  trabajo pesado.
