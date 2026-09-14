# OpoFuente — preguntas, exámenes y sistema de estudio

## 1. Principios

- Estudiar comienza por recuperar, no por leer resúmenes infinitos.
- Pregunta, clave, explicación y evidencia tienen procedencia separada.
- Oficial, privado y generado siempre son visibles.
- El perfil de convocatoria configura el examen.
- Corregir una clave no reescribe el pasado.

## 2. Perfil TAI de referencia

Fuente: [BOE-A-2025-26262](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26262).

```yaml
code: tai-age-2025
opposition: tai-age
curriculum:
  blocks: 4
  topics: 33
exam:
  total_minutes: 120
  parts:
    - code: general
      questions: 80
      reserves: 5
      scope: all_blocks
      score_min: 0
      score_max: 50
      pass_score: 25
      wrong_penalty_fraction: 0.3333333333
    - code: practical
      questions: 20
      reserves: 5
      scope: [block_iii, block_iv]
      score_min: 0
      score_max: 50
      pass_score: 25
      wrong_penalty_fraction: 0.3333333333
rules:
  blank_penalty: 0
  official_scaled_score_requires_published_correction_criteria: true
```

El YAML es ilustrativo; la configuración se guarda validada en base de datos y se siembra desde un
fixture versionado.

La app calcula la puntuación directa `A - E/3`. No puede transformar por sí sola esa puntuación en la
calificación oficial 0–50: la convocatoria establece que la Comisión fija los baremos y la puntuación
directa mínima. Hasta importar ese criterio oficial, debe mostrar «calificación oficial no disponible».

## 3. Perfil Guardia Civil 2026

Fuentes: [convocatoria](https://www.boe.es/buscar/doc.php?id=BOE-A-2026-9982) y
[página oficial](https://web.guardiacivil.es/es/tramites/ingresos/Procedimiento-de-ingreso-directo-en-la-Escala-de-Cabos-y-Guardias-de-la-Guardia-Civil/).

```yaml
code: gc-cabos-guardias-2026
opposition: gc-cabos-guardias
curriculum:
  topics: 25
written_exam:
  theoretical_practical_minutes: 140
  parts:
    - code: spelling
      format: multi_mark_error
      ordinary_items: 20
      structure: 5_sentences_x_4_marked_expressions
      reserve_items: 4
      fail_if_errors_gte: 6
    - code: grammar
      format: multi_mark_error
      ordinary_items: 20
      reserve_items: 4
      fail_if_errors_gte: 6
    - code: general_knowledge
      format: single_choice
      questions: 100
      reserves: 5
      options: 4
      score_max: 100
      pass_score: 50
    - code: english
      format: single_choice
      questions: 20
      reserves: 1
      options: 4
      score_max: 20
      pass_score: 8
  psychotechnical:
    aptitude_questions: 80
    aptitude_minutes: 55
    options: 4
    score_max: 30
    pass_score: 12
    personality_scoring_supported: false
```

Para preguntas con cuatro alternativas, implementar la fórmula oficial parametrizada:

```text
raw = A - E / (N - 1)
score = Y * raw / T
```

`A` aciertos, `E` errores, `N` alternativas, `T` preguntas ordinarias computables y `Y` puntuación
máxima. Reservas sustituyen anuladas en orden antes del cálculo. Verificar contra ejemplos manuales.

Fase de concurso, pruebas físicas, entrevista y reconocimiento pueden registrarse como información,
pero no se calculan/preparan en el MVP.

## 4. Banco de preguntas

Filtros:

- oposición/convocatoria;
- parte, bloque, tema y epígrafe;
- oficial/privada/generada;
- verificada, conflictiva, anulada o sustituida;
- fuente y versión;
- acertada/fallada/no vista;
- dificultad observada;
- colección y etiquetas.

Vista de edición muestra original a un lado y campos estructurados al otro. Cambios a una pregunta
oficial crean anotación/corrección local, nunca alteran el texto importado.

## 5. Modos de sesión

### Práctica

Sin límite opcional, feedback inmediato, filtros libres y posibilidad de consultar evidencia después
de responder.

### Repaso de errores

Selecciona vencidos y errores recurrentes. No muestra la respuesta antes del intento. Después solicita
causa y confianza cuando sea útil.

### Examen oficial histórico

Mismo cuestionario, modelo y clave versionada. Cronómetro y corrección conforme a esa publicación.

### Simulacro

Muestra el perfil exacto y origen de cada pregunta. No se denomina oficial. Evita preguntas vistas
recientemente si hay banco suficiente.

### Diagnóstico

Muestra pequeña estratificada; produce estimación por tema con intervalo/incertidumbre, no porcentaje
falso de dominio basado en dos preguntas.

## 6. Ciclo de respuesta

1. presentar enunciado y opciones, sin solución indexada;
2. registrar respuesta, tiempo y confianza opcional;
3. congelar intento;
4. evaluar con clave activa de la sesión;
5. mostrar resultado, origen y versión de clave;
6. explicar cada opción con evidencia disponible;
7. permitir «creo que es ambigua/incorrecta»;
8. clasificar causa del fallo;
9. crear/actualizar repaso.

No generar una explicación en directo si puede retrasar o alterar la corrección. Mostrar primero clave
y evidencias ya verificadas; la explicación IA opcional queda etiquetada.

## 7. Reservas, anulaciones y claves nuevas

- `is_reserve` y orden de reserva son datos.
- al anular ordinaria, sustituir por primera reserva no usada según perfil;
- guardar composición efectiva del cálculo;
- nueva plantilla crea `AnswerKeyVersion`;
- recalcular genera `AttemptEvaluation` nueva;
- UI muestra «tu puntuación cambió de X a Y por plantilla oficial v2».

## 8. Errores y repaso

Después de un fallo, proponer epígrafes basados en mapeo de la pregunta, no en una nueva clasificación
sin revisar. El usuario puede elegir causa y redactar regla recordatoria propia.

Scheduler MVP determinista:

- fallo: hoy/mañana;
- respuesta correcta con baja confianza: 2 días;
- correcto tras fallo: 4 días;
- correcto seguro repetido: 8, 16, 30 días;
- nuevo fallo reduce intervalo.

Guardar historial. FSRS se evaluará cuando existan suficientes revisiones; no copiar parcialmente su
algoritmo. Exportación Anki CSV incluye pregunta, opciones, respuesta, explicación, citas, oposición y
tema.

## 9. Cobertura frente a dominio

### Cobertura documental

Porcentaje ponderado de epígrafes con al menos una evidencia aceptada, vigente y de confianza adecuada.

### Cobertura de preguntas

Número y diversidad de preguntas verificadas por epígrafe. No usar cantidad bruta si son duplicadas.

### Dominio

Estimación basada en intentos recientes, dificultad y repetición. Con pocos datos mostrar «evidencia
insuficiente», no 100 %.

## 10. Explicaciones

Orden:

1. resultado y clave;
2. respuesta breve;
3. por qué la correcta;
4. por qué cada distractor;
5. evidencia/versiones;
6. concepto a repasar;
7. nota personal.

Si no hay evidencia para un distractor, decirlo. No inventar racionalización.

## 11. Aceptación

- Puntuación directa TAI verificada con blancos, fallos y reservas; calificación oficial solo con el
  criterio de corrección versionado.
- Puntuación GC verificada con fórmula, anulaciones y umbrales.
- Ortografía/gramática representan múltiples marcas y regla de seis errores.
- Una clave GC v2 recalcula sin sobrescribir v1.
- Pregunta oficial siempre enlaza al artefacto/página.
- Modo examen no filtra solución a búsqueda, HTML o API antes de responder.
- Repasos conservan historial y son deterministas.
