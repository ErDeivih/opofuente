# Fase 3 — De app que funciona a herramienta para estudiar cada día

**Para:** DeepSeek · **De:** Claude, por delegación del propietario · **18 oct 2026** · **Base:** `main = 8a1a14e`
Objetivo largo, para trabajar muchas rondas **sin preguntar**. Sustituye a los objetivos anteriores. Los documentos de método siguen valiendo: `GOAL-DEEPSEEK-TRABAJO-LARGO` §1 (cómo decidir), `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO` (claves y ritmo) y las trampas de `DEBT-022` y `DEBT-029`.

---

## 0. El texto del goal

> Ejecutar `docs/FASE-3-ESTUDIO-DIARIO-SPEC-PLAN-GOAL-2026-10.md` de principio a fin, por hitos y en orden (M0 → M8), sin preguntar: decidir lo reversible y apuntarlo en `DECISIONES-TOMADAS-EN-EL-OBJETIVO.md`; pararse **solo** en los casos del §2.3. El código entra en `main` con 18/18 y con la puerta de codificación. El contenido se genera sobre la base real con copia verificada al empezar cada tanda y lo deciden las puertas de datos. Al cerrar cada hito: actualizar `ESTADO-DEL-OBJETIVO.md` y escribir `docs/hitos/M<n>.md` con las cifras medidas. En M1, M3, M5 y M8 hay que dejar capturas del recorrido con datos reales en `artifacts/recorrido-M<n>/` **y seguir sin esperar a que se revisen**. Presupuesto de API: **30 $** para toda la fase.

Rondas: el máximo que permita el entorno. Si se agotan, la siguiente sesión retoma leyendo `ESTADO-DEL-OBJETIVO.md` y el último `docs/hitos/M<n>.md`.

---

## 1. Para qué es esta fase

La app ya tiene temario, apuntes publicados, tests, simulacros, exámenes oficiales, repaso de fallos y panel. Lo que le falta para que el propietario la abra **cada día** y le rinda el tiempo:

1. **Explicación en cada pregunta.** Hoy, al fallar, ves la correcta, pero no el porqué.
2. **Saber qué tocar hoy**: un plan hasta el examen y una pantalla "Hoy" que lo convierta en tareas.
3. **Memorizar lo que cae**: tarjetas sacadas de los «datos que caen» de los apuntes, con repaso espaciado.
4. **Un supuesto práctico de verdad**, porque la segunda parte del examen es un caso, no preguntas sueltas.
5. **Cerrar el material**: los 33 temas, los exámenes que faltan y las claves en cuarentena.
6. **Dejarlo empaquetado** para una beta cerrada, sin publicar nada.

---

## 2. Reglas (las de siempre, más dos)

### 2.1 Decidir sin preguntar
Ante una duda: la opción **reversible**, más conservadora con los datos, y que **no frene**. Una línea en `DECISIONES-TOMADAS-EN-EL-OBJETIVO.md` (qué, por qué, cómo deshacerlo). Si el propietario debería saberlo, también en `PARA-EL-PROPIETARIO.md`. No esperes respuesta.

### 2.2 Reglas fijas
- Copia **verificada** antes de cualquier escritura masiva en los datos reales. Nada de SQL suelto: solo rutas o métodos auditados.
- Una clave oficial no se cambia nunca.
- Ninguna cifra va a un documento sin medirla.
- Código: rama, prueba que falla antes y pasa después, 18/18, fusión. Una medida pertenece al commit que se midió.
- **Nuevo — puerta de codificación**: al principio de la batería, UTF-8 estricto en todos los ficheros de texto y 0 coincidencias de `Ã[\x80-\xBF]|Â[·ª-¿]|â€`, salvo una lista de excepciones con su motivo. Nada de cmdlets de PowerShell 5.1 sin `-Encoding utf8` sobre ficheros de texto.
- **Nuevo — ningún texto inventado ante el alumno**: ni frecuencias de examen sin calcular, ni datos sin respaldo. Todo lo generado lleva su marca («generada · en revisión») hasta que lo apruebe el propietario.

### 2.3 Solo te detienes si…
1. Hay que borrar datos del propietario (salvo la política de 2 copias).
2. Algo saldría de su ordenador: publicar, desplegar o subir datos a un servicio que no sea la API del modelo.
3. El gasto de API superaría los 30 $.
4. Una migración irreversible sobre datos reales **sin** copia verificada.

---

## 3. Hitos

Cada hito: **spec** (qué), **plan** (cómo, en orden), **hecho cuando** (medible). Entre hitos no se para.

### M0 — Cerrar lo abierto (corto)
- Terminar la cola: F40 → F37 → F39 con su 18/18, y la puerta de codificación del §2.2 en el instrumento.
- El cierre pendiente: recorrido sobre una copia nueva, con la tabla antes/después de los 20 defectos y las capturas en `artifacts/recorrido-M0/`. **No se espera la revisión**: se sigue con M1.
- **Hecho cuando:** las tres ramas están en `main` y existe la tabla de los 20 con su cifra.

### M1 — Una explicación en cada pregunta
**Spec.** Tras corregir una pregunta, el alumno ve de 2 a 5 frases: por qué la correcta lo es y por qué no la trampa más tentadora, con «Ver en apuntes» al párrafo. La explicación se apoya en el apartado de los apuntes que ya contiene la respuesta (`question_note_anchors`) y, en los temas normativos, en el artículo.
**Plan.**
1. Tabla o uso de `question_explanations` con `origin = 'generated'`, `status` (`generada`, `aprobada`, `rechazada`), la cita y el ancla.
2. Generador por lotes (≈ 20 preguntas por llamada) que recibe la pregunta, la clave servible y el apartado anclado. Prohibido explicar sin ancla: esas preguntas van a la bandeja como `sin_material`.
3. Comprobaciones mecánicas: la cita existe literalmente en los apuntes; la letra que justifica la explicación coincide con la clave; 0 frases sobre exámenes o frecuencias; de 2 a 5 frases.
4. Orden: los exámenes oficiales del INAP primero; después los temas por número de preguntas.
5. Pantalla: la explicación en el test (corrección al momento) y en el Resultado. En el panel, revisión en bloque con teclas (A aprobar, E editar, R regenerar).
6. Las 11.315 explicaciones privadas que ya existen solo se usan como **material** para el generador cuando sean de un conjunto fiable, nunca se copian.

**Hecho cuando:** el 100 % de las preguntas oficiales servibles y ≥ 90 % del resto de servibles tienen explicación que pasa las comprobaciones; capturas en `recorrido-M1`. Coste previsto: medido en el ensayo; tope del hito, 12 $.

### M2 — Cerrar el material
**Spec.** Que el alumno no se tope con huecos.
**Plan.**
1. **Temas:** III.6, IV.3, III.2, I.9 y el borrador I.6, con el método de siempre (ensayo a 0 $, catálogo con `ruff` y `mypy`, puertas de datos). Lo que no pase queda en borrador con su cifra.
2. **Exámenes:** OCR de los 3 escaneos del INAP con el OCR que ya tiene la app, y la ingesta de los dos exámenes que la reextracción dijo que la necesitaban. `distribution = public`, `origin_scope = age`.
3. **Claves en cuarentena:** volver a pasar las claves derivadas sobre los apuntes ya publicados (habrá más coincidencias que cuando se hizo). Informe por conjunto: cuántas vuelven al estudio.
4. **D4/D5:** la política de dos copias, una copia nueva verificada al empezar.

**Hecho cuando:** 33/33 temas publicados, o en borrador con su cifra; los exámenes nuevos practicables; la tabla de claves recuperadas por conjunto. Tope del hito, 8 $.

### M3 — Tarjetas y repaso espaciado
**Spec.** Lo que hay que memorizar (cifras, plazos, mayorías, puertos, artículos, siglas) en tarjetas cortas, con un repaso diario que mezcla tarjetas y fallos.
**Plan.**
1. Tarjetas sacadas de `topic_facts` y de las tablas «datos que caen». Anverso: la pregunta («¿Puerto de SMTPS?»); reverso: la respuesta y el enlace al párrafo. Se generan sin modelo cuando el hecho ya es una pareja dato–valor; con el modelo solo cuando hay que reformularlo (con su marca).
2. Programación del repaso con **FSRS**. Usa la biblioteca de código abierto si su licencia lo permite: verifícala y apúntalo; si no, SM-2 escrito en el dominio. Cuatro respuestas: Otra vez, Difícil, Bien, Fácil.
3. **Una sola cola diaria**: tarjetas vencidas, fallos vencidos y un tope diario configurable (60 por defecto). Pantalla de repaso con teclado (espacio para dar la vuelta, 1 a 4 para responder).
4. Un fallo en un test crea o adelanta la tarjeta de su hecho.

**Hecho cuando:** hay tarjetas en los 33 temas (o en todos los publicados); la cola funciona entera con teclado; capturas en `recorrido-M3`.

### M4 — Plan de estudio y pantalla «Hoy»
**Spec.** El propietario indica la fecha del examen (por defecto, la de la convocatoria si está en la base; si no, a 6 meses) y las horas por semana. La app reparte los 33 temas según su peso (preguntas por tema), lo flojo que va en cada uno y el tiempo que queda. «Hoy» sustituye a Inicio como pantalla principal.
**Plan.**
1. Modelo `study_plan` (fecha, horas por semana, días de descanso) y un planificador **determinista** (sin modelo), con pruebas de propiedades: cubre todos los temas antes del examen, repite los flojos y deja las dos últimas semanas para simulacros.
2. «Hoy»: 3–5 tareas concretas, cada una con su botón («Lee IV.7, capítulo 2 · 25 min», «Test de 20 de IV.7», «Repaso: 38 tarjetas», «Simulacro corto»). Se tachan solas al hacerlas.
3. «Vas bien / vas retrasado» con la cifra: temas leídos y practicados respecto al plan.
4. Replanificar sola si pasan días sin estudiar, sin culpar.

**Hecho cuando:** con la fecha puesta, «Hoy» muestra tareas reales que llevan a la pantalla correcta; el plan sale idéntico con los mismos datos.

### M5 — El supuesto práctico real
**Spec.** La segunda parte del examen es un **supuesto**: un enunciado de caso con 20 preguntas (más 5 de reserva) sobre él, del bloque III o del IV. Hoy el simulacro la monta con preguntas sueltas del bloque.
**Plan.**
1. Modelo `practical_case`: enunciado (texto y, si lo hay, tablas o esquema), bloque y preguntas asociadas.
2. **Supuestos oficiales primero:** extraer de los exámenes INAP los supuestos de III y de IV con su enunciado y sus preguntas.
3. **Supuestos generados** a partir de los apuntes, para tener variedad: el modelo escribe el caso y 25 preguntas con su clave y su explicación, cada una anclada a un párrafo de los apuntes. Pasan las mismas comprobaciones que M1, más una: un segundo modelo responde las 25 sin conocer la clave y la coincidencia tiene que ser ≥ 90 %. Si no llega, el supuesto se descarta. Marcados «supuesto generado».
4. El simulacro usa un supuesto real del bloque elegido (oficial si hay alguno sin hacer; si no, generado) y el examen oficial muestra su supuesto como en el papel: enunciado a la izquierda y preguntas a la derecha.

**Hecho cuando:** al menos todos los supuestos oficiales disponibles y 6 generados por bloque (III y IV) aprobados por las comprobaciones; capturas en `recorrido-M5`. Tope del hito, 6 $.

### M6 — Estadísticas que dicen qué hacer
**Spec.** Progreso que responde a «¿qué estudio ahora?».
**Plan.** Nota estimada por parte, con su intervalo, a partir de los últimos simulacros y tests ponderados por el peso de cada tema. Los 5 epígrafes más flojos con su botón de práctica. Tiempo medio por pregunta frente al del examen (120 min / 100). Evolución semanal. Todo calculado; nada de frases sin cifra.
**Hecho cuando:** Progreso enseña la nota estimada con su intervalo y los 5 epígrafes con un botón que funciona.

### M7 — Calidad continua
**Plan.**
1. El bucle de «Esto está mal»: el aviso del alumno → regenerar solo ese párrafo con la indicación → volver a comprobar las preguntas ancladas → propuesta en la bandeja.
2. Comprobación semanal automática de los temas publicados (`opofuente notes verify --all`) que avise si alguno baja del listón.
3. Bandeja del propietario por debajo de 100 decisiones reales, con todo lo automatizable propuesto en bloque.
4. Rendimiento: cualquier pantalla del alumno por debajo de 2 s y el simulacro por debajo de 5 s, con una prueba que lo vigile.

**Hecho cuando:** las cuatro cosas medidas en `docs/hitos/M7.md`.

### M8 — Empaquetado para una beta cerrada (sin publicar)
**Spec.** Dejar listo, con las banderas apagadas, lo que hace falta para que 5–10 personas puedan usarla el día que el propietario decida (decisiones ya tomadas: cuentas por invitación, gratis, nada contratado).
**Plan.**
1. **Paquete de contenido público**: un exportador que saca solo lo `distribution = public` más los apuntes, las explicaciones y las tarjetas generadas (que son propias), con ids estables; y un importador idempotente. Prueba: exportar, importar y volver a exportar da lo mismo, y dentro del paquete no hay ninguna palabra prohibida ni ningún dato privado.
2. **Instalación reproducible**: un `docker compose` (API, web y volumen de datos) o un instalador para Windows, lo que sea más simple para el propietario (decídelo y apúntalo). Arranca con el paquete público, crea el administrador e invita por enlace. **No se despliega en ningún sitio.**
3. Copia y restauración probadas sobre la instalación.
4. Guía de una página para el propietario: cómo arrancarla, invitar, hacer copia y apagarla.

**Hecho cuando:** en una carpeta limpia, desde el paquete público, se instala, se entra con una invitación, se hace un test y se restaura una copia. Capturas en `recorrido-M8`.

---

## 4. Orden, ritmo y presupuesto

- Orden: **M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8**. Puedes llevar contenido (M1, M2 y M5 generan con el modelo) en paralelo con código de otro hito, como hasta ahora, sin pisar puertos ni carpetas de pruebas.
- Presupuesto total: **30 $** (M1 12, M2 8, M5 6, resto 4). Aviso en `ESTADO` cada 5 $.
- Revisión de capturas: Claude revisará `recorrido-M1`, `M3`, `M5` y `M8` cuando el propietario se las pase. Tú no esperas: sigues.

## 5. Cuándo está terminada la fase

- [ ] M0–M8 con su `docs/hitos/M<n>.md` y sus cifras.
- [ ] Explicación en todas las preguntas oficiales servibles y en ≥ 90 % del resto.
- [ ] 33 temas publicados o con su motivo; exámenes nuevos practicables.
- [ ] Tarjetas y cola diaria; plan y «Hoy»; supuestos reales en el simulacro; estadísticas útiles.
- [ ] Bandeja por debajo de 100; pantallas por debajo de 2 s.
- [ ] Paquete público e instalación reproducible probados, sin publicar nada.
- [ ] Gasto ≤ 30 $; base real intacta salvo las escrituras auditadas.
