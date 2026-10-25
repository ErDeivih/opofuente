# Lo que ve el alumno — estado para Claude

**`main = c3b4c6a`** (más el commit de este cierre) · árbol limpio · **487 pruebas en verde** ·
`tsc 0` · `eslint 0` · **gasto de API de la tanda: ~0,02 $ de 4 $**.

## Hecho y medido en la base real

| # | punto | estado |
|---|---|---|
| 1 | Tarjetas al alumno | **PARADO por su propio criterio**: el contraste a ciegas da **80 %** (40 de 50) y el documento manda parar por debajo del **90 %**. Hechos: la comprobación de las cuatro condiciones, la columna `draft_reason` (migración **0048**, aplicada) y el contraste. **Nada activado**: 9 tarjetas, 5.274 en borrador. |
| 2 | Pantalla de repaso | **HECHO**: no tenía **ni una regla de CSS**; la respuesta se daba solo con el espacio; no había resumen. Las tres cosas arregladas y **con prueba** (`tests/unit/repaso.test.tsx`). |
| 3 | Fallos vencidos en la cola | **TERMINADO**: la cola mezcla tarjetas y fallos con el **tope de 60 compartido** (medido: **9 + 1, total 10**); `POST /cards/queue/failures/{id}` **corrige sin sesión** y devuelve la explicación con su cita; el repaso los pinta. **Los 4 fallos sin clave se quedan fuera.** |
| 4 | «Hoy», de verdad | **CASI**: cero reglas `.hoy` → escritas; «Continuar», «Repaso: N para hoy», «Repasar fallos (N)» y **las cuatro barras de progreso**. **Falta «Seguir leyendo»**, y **falta el dato**: la lectura no registra posición. |
| 5 | Simulacro en dos partes | **DIAGNOSTICADO**: la base guarda `part_code` en `session_questions` y **la API no lo expone**; por eso el enunciado sale en la primera pregunta. |
| 6-9 | | **sin empezar** |

## Las dos decisiones que necesitan al propietario

1. **El listón de las tarjetas.** El documento fija ≥ 90 %; el modelo da **80 %**. Tres salidas
   escritas: bajar el listón, regenerar las tarjetas, o activar solo las que el contraste acierta.
2. **Las cuatro preguntas falladas sin clave.** Están en la cola con explicación pero sin clave con la
   que corregirse; hoy **no se ofrecen**. ¿Se sacan, o se corrigen sin nota?

## Los tres hallazgos que explican casi todo

- **`apiFetch` sin `/api/v1`**: **69 llamadas en 404**, entre ellas el plan de la portada. Arreglado.
- **Clases en el JSX y ninguna regla en el CSS** en `.repaso` y `.hoy`: por eso lo pegado y lo «sin
  estilo».
- **Datos que ya estaban en el servidor y la pantalla no pedía**: `in_progress`, `due_reviews`,
  `blocks`, `vencen`.
