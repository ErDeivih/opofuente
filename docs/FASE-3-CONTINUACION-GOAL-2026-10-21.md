# Fase 3, continuación: de M1 a M8 sin parar

**Para:** DeepSeek · **De:** Claude, por delegación del propietario · **21 oct 2026** · **Base:** `main = 53e105f`
Se lee junto con `FASE-3-ESTUDIO-DIARIO-SPEC-PLAN-GOAL-2026-10.md` (la especificación) y `DESBLOQUEO-FASE-3-2026-10-21.md` (las decisiones). Si algo choca, manda este documento.

## 0. Goal

> Terminar la fase 3 (M1 → M8) siguiendo `docs/FASE-3-CONTINUACION-GOAL-2026-10-21.md`, sin preguntar y sin pararse entre hitos: decidir lo reversible y apuntarlo en `docs/hitos/`. Pararse solo en los casos del §2.3 de la fase. Leer `DEEPSEEK_API_KEY` del ámbito de usuario en cada comando. El código entra en `main` con 18/18 (una batería por integración) y con la puerta de codificación. El contenido se genera sobre la base real, con copia verificada al empezar cada tanda, y lo deciden las puertas de datos. Al cerrar cada hito: `docs/hitos/M<n>.md` con cifras medidas y capturas con datos reales en `artifacts/recorrido-M<n>/` en M1, M3, M5 y M8, sin esperar revisión. Presupuesto de API de toda la fase: 30 $ (llevas 0,03 $).

**Rondas:** el máximo. Al final de cada sesión, deja escrito en `docs/hitos/SIGUIENTE-PASO.md` el paso exacto con el que se retoma (comando, rama y commit), para que una sesión nueva arranque sin releer conversaciones.

**Sobre el estado «Blocked»:** el objetivo no se bloquea por falta de decisiones del propietario. Si un paso necesita algo que no tienes, apúntalo en `PARA-EL-PROPIETARIO.md` y **pasa al siguiente punto de la lista**. Solo se declara bloqueado si **todos** los puntos pendientes de los §1 a §3 necesitan algo del propietario.

---

## 1. M1 — Explicaciones: subir del 65 % a la primera y hacer la corrida

El ensayo dio 13 de 20 a la primera, y las 7 que cayeron caen por **parafrasear la cita**. No lo arregles pidiendo «copia literal», que el modelo no siempre cumple. Hazlo **por construcción**:

1. Parte el apartado anclado en **frases numeradas** (`[1] …`, `[2] …`) y pásaselas así al modelo.
2. El modelo devuelve el **número** de la frase (o los números, hasta 2) que justifican la respuesta, no el texto.
3. El programa compone la cita con esas frases. La cita es literal siempre, porque sale del propio apartado.
4. Las comprobaciones que quedan son: que el número existe; que la frase contiene el dato que decide (alguna palabra clave de la opción correcta); que la letra coincide con la clave; de 2 a 5 frases, y nada de frecuencias de examen.

Vuelve a ensayar 20 con esto. Si pasan ≥ 18, lanza la corrida completa (≈ 11.147 preguntas, ≈ 5 $ medidos), primero los exámenes oficiales y después los temas por número de preguntas. La segunda pasada es solo para las que caigan. Después: la acción «regenerar» de la bandeja, y las capturas de `recorrido-M1`.

## 2. M2 — Material (lo de `DESBLOQUEO` §2 a §5)

Los tres escaneos con OCR, las dos fuentes de Guardia Civil y Celador, DEBT-035 y DEBT-036, con las decisiones ya escritas. Y con clave: las 16 claves de la cuarentena (≈ 0,01 $) y los temas que faltan (III.6, IV.3, III.2, I.9 y el borrador I.6), con el método de siempre.

## 3. M3 a M8

Con la especificación de la fase, en este orden: **M3** (tarjetas: las estructurales ya salen; con clave, las que hay que reformular, y la cola diaria con su pantalla) → **M4** (plan y «Hoy») → **M5** (supuestos: oficiales primero; los generados, con un segundo modelo que los responde a ciegas, ≥ 90 % de coincidencia) → **M6** (estadísticas) → **M7** (calidad continua y rendimiento) → **M8** (paquete público e instalación reproducible, sin publicar).

Paralelo permitido: mientras corre contenido de M1, M2 o M5 (que gasta y tarda), escribe el código de M4, M6, M7 o M8 en otra rama.

## 4. El incendio

Has dejado bien escrito lo que se puede probar. Hay una pista que conviene seguir: se borraron **los ficheros rastreados por git y el `.git` de cada árbol**, y sobrevivieron **los ignorados** (`.venv`, `node_modules`, `.e2e-data`, `artifacts`…). Así no borra un antivirus ni un limpiador de temporales: así borra **una operación que conoce git**. Mira:
- `git reflog` y `logs/` del repositorio y de cada árbol, en la franja 00:30–00:40 del 21 de octubre;
- `git worktree list` y si alguno de esos árboles se «quitó» y se volvió a añadir;
- las tareas programadas de Windows y los procesos de los agentes (incluidos tus subagentes) que estuvieran vivos a esa hora.

Si sale la causa, regla en el documento del incendio. Si no sale en 2 rondas, se deja como está y se sigue.

## 5. Cuándo se termina

La lista de comprobación del §5 de la fase, completa: M0–M8 con su `docs/hitos/M<n>.md`, explicaciones, 33 temas o su motivo, tarjetas y cola, plan y «Hoy», supuestos, estadísticas, bandeja por debajo de 100, pantallas por debajo de 2 s, paquete e instalación probados sin publicar, y gasto ≤ 30 $.
