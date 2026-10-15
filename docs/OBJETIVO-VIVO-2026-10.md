# Objetivo vivo (15-oct-2026) · texto autoritativo

**Por qué existe este fichero**: el objetivo del bucle vivía **solo en la sesión del agente orquestador**, y un bloque
lo comprobó: buscó `HttpOnly|SameSite|argon2|bcrypt|consentimiento` en `docs/` de tres árboles y **no encontró nada**.
Es decir: **el encargo de plataforma desplegable no estaba escrito en ningún sitio del repositorio**. Este documento lo
arregla. **Si algo de aquí choca con otro documento, manda el orden de la cabecera**: primero
`AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`, después `SIGUIENTE-TANDA-CIERRE-DEL-OBJETIVO-2026-10.md` (manda en el
orden), después esto, y después el `GOAL-DEEPSEEK-TRABAJO-LARGO-2026-10.md`.

## A · Cierre del objetivo de estudio, en orden de valor para quien estudia

1. **Devolver al estudio las preguntas en cuarentena (clave derivada).** Clave **derivada** cuando coincidan **los apuntes
   (letra con cita verificada)** *y* **una respuesta independiente del modelo sin apuntes**. Se guarda como **`derived`,
   nunca `active`**, y el alumno la ve como **«revisada automáticamente»**. Si no coinciden, la pregunta **sigue fuera** y
   va a la bandeja **agrupada por conjunto**. Un conjunto **vuelve a los tests cuando ≥90 % de sus preguntas tienen clave
   `active` o `derived`**; las que no, siguen fuera. **Las claves oficiales no se tocan jamás.** Informe: preguntas
   devueltas por conjunto y coste.
2. **Que la bandeja se pueda trabajar** (hoy 603 entradas): **fila por conjunto** con acciones en bloque · resolución
   automática de lo que no necesita criterio · **lo oficial aparte y arriba** · meta: **bajar de 603 a menos de 150**
   entradas que de verdad dependan del propietario.
3. **Los dos exámenes oficiales que faltan**: **reextraer las plantillas recortadas** (3.474 versiones; 1,71 M de
   caracteres). Van **antes** que los temas que quedan.
4. **El «0 de 0» del medidor**: un grupo **con apartado propio y sin comprobación guardada** cuenta como **pendiente de
   comprobar**, nunca como cubierto ni como ausente. Volver a medir los 33 y publicar la tabla antes/después.
   **Ningún tema publicado se retira automáticamente**: si alguno baja del 90 %, se queda **con su cifra a la vista**.
5. **Los temas**, en este orden y con ensayo previo a 0 $: **I.3 e I.4** con el medidor nuevo (barato) → **III.4**
   (reclasificar sus preguntas ajenas por ruta auditada y después escribirlo) → **I.6, I.7, I.8** (borradores, reanudar
   desde lo guardado) → **III.6, IV.3, III.2, I.9**. Lo que no pase, **borrador con su cifra**. **No se fuerza ninguno.**
6. **Pendientes pequeños**: **D4** (`reassign_epigraph` auditado; si no existe, se crea con su prueba) · **D11** (lo que
   digan sus puertas) · **D5 copias** (dos verificadas; ver §C) · **`datos\tmp` es un enlace a `E:`**: comprobar que la
   app **avisa claro si `E:` no está conectado** en vez de fallar a medias, y anotarlo en `PARA-EL-PROPIETARIO.md`.
7. **Cierre**: recorrido completo del alumno y del panel con datos reales sobre copia, capturas a 1280 y 390 en
   `artifacts/recorrido/` y un `RECORRIDO.md`; y **PARAR** para que el propietario y Claude revisen las capturas.

## B · Plataforma desplegable (encargo del propietario, 15-oct)

**Regla que manda sobre todo lo demás: el alumno que ya existe (uso local, sin cuenta) tiene que seguir funcionando
igual.** Todo lo nuevo va **detrás de una bandera apagada por defecto** y **sin contratar servicios de pago**.

8. **Cuentas y sesiones**: registro, acceso, recuperación, cierre de sesión y protección de rutas. Sesión propia (cookie
   `HttpOnly` + `SameSite`), **contraseñas con hash**, rutas auditadas, **sin revelar si un correo ya existe** y con
   **límite de intentos**.
9. **Páginas legales y control de datos**: aviso legal, privacidad y política de cookies, con **consentimiento real**
   (antes de aceptar **no se pone ninguna cookie no esencial**; rechazar es **tan fácil como aceptar**) y un apartado
   **escrito y verificable** de **qué datos se recogen, para qué y cuánto tiempo**.
10. **Analíticas**: **no se activan sin permiso** y **sin identificadores de terceros**. No montar ninguna es una
    respuesta válida: entonces se dice y se deja el punto de enganche.
11. **Pagos**: **solo el hueco y la bandera, apagada**. Documentar **qué pasarela** y por qué, **qué habría que
    contratar** y **qué datos personales pasarían a un tercero** (eso entra en privacidad). **No contratar nada.**
12. **Acabado de interfaz**: transiciones y estados de carga, jerarquía visual y coherencia entre pantallas. Se puede
    usar el catálogo `F:\Inforepositorios` (`scripts\Buscar-Repos.ps1`) **solo** con repos cuyo **«límite» no choque**
    (nada que exija WebGPU/WebGL, nada sin licencia verificada, nada que dependa de servicios de pago), y **se anotan
    las decisiones y las descartadas con su motivo**.

**Banderas**: `OPOFUENTE_ACCOUNTS_ENABLED=0`, `OPOFUENTE_ANALYTICS_ENABLED=0`, `OPOFUENTE_PAYMENTS_ENABLED=0`.
Con las tres a 0, el árbol se comporta **exactamente** como antes para el alumno sin cuenta, y **esa es la primera
prueba que hay que pasar**.

## C · D5: las copias, con la causa del tamaño ya medida (15-oct)

```
20261013-204211-1a9a69.zip  4,39 GB  18.021 entradas  artifacts · database · extracted · manifest.json
20261014-101138-3c75b9.zip  0,81 GB       2 entradas  database · manifest.json
```

**El tamaño lo decide el alcance, no la base**: 0,8 GB es **solo base** (el estándar del proyecto, y el que manda la
regla de D5); 4,4 GB es **base + almacén de artefactos + texto extraído**, y es **la única que restaura el almacén de
contenido**. Quedan **dos verificadas**: la ancha del 13-oct 20:42 y la más reciente del 14-oct 10:11. **Lo que no vale
es que el tamaño dependa de quién la lanzó**, que es lo que pasaba.

## D · Reglas que no se negocian

- Decidir lo reversible y **apuntarlo en `DECISIONES-TOMADAS-EN-EL-OBJETIVO.md`** sin preguntar; pararse solo en los
  cuatro casos del §1.3 del goal.
- **El código entra en `main` con 18/18.** Si una batería se reparte en tramos, **se dice con sus intentos y su causa**.
- **El contenido de apuntes no lleva batería**: se genera sobre la base real con **copia verificada al empezar la tanda**
  y lo deciden **las puertas de datos**.
- **Un catálogo nuevo es código**: antes de commitear, `ruff check .` y `mypy`.
- **Copia verificada antes de escrituras masivas**; **nada de SQL suelto** (solo rutas auditadas); **una clave oficial no
  se cambia jamás**.
- **Ninguna cifra entra en un documento sin estar medida.**
- Al cerrar cada bloque, **actualizar** `ESTADO-DEL-OBJETIVO.md`, `DECISIONES-TOMADAS-EN-EL-OBJETIVO.md` y
  `PARA-EL-PROPIETARIO.md`.
- **Antes de contratar o activar cualquier servicio externo, parar y avisar al propietario.**
