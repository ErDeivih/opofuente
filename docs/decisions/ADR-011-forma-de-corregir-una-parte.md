# ADR-011 — La forma de corregir una parte la fija su convocatoria

- **Estado:** aceptada (decisión del codificador al abrir S08)
- **Fecha:** 17 de septiembre de 2026
- **Ámbito:** puntuación de partes y pruebas (S08, y lo que herede S09+)
- **Asunto:** cómo decide la aplicación con qué fórmula se corrige cada parte del examen

## Contexto

Las dos convocatorias sembradas publican cosas distintas, y S07 solo sabía corregir una de ellas:

| Convocatoria | Qué publica de una parte | Qué se puede calcular |
|---|---|---|
| TAI 2025 | la penalización («un tercio del valor de una respuesta correcta») y que la calificación resulta de unos baremos que fija la Comisión | la puntuación directa `A − E·p`; la calificación oficial 0-50 **no** |
| Guardia Civil 2026 | la fórmula completa `Px = (Y/T)·(A − E/(N−1))` con `Y`, `T` y `N` para cada prueba | la nota de la prueba, y su umbral (`50`, `8`, `12`) |
| Guardia Civil 2026 (ortografía y gramática) | que se evalúan como apto o no apto, con seis o más errores | el veredicto, **no** una puntuación |

La pregunta es de dónde sale esa distinción: ¿de una lista escrita en el código, de un campo nuevo en
los fixtures, o de lo que el perfil ya dice?

## Opciones consideradas

1. **Una lista en el código** (`si la convocatoria es GC, usa la fórmula`). Descartada: ata el cálculo
   al nombre de una convocatoria y obliga a tocar código cada vez que llegue un perfil nuevo.
2. **Un campo nuevo en el fixture curado** (`scoring: scaled|direct|pass_fail`). Es explícito, pero
   duplica un hecho que el perfil ya declara: si la parte trae `options_per_question`, `score_max` y
   `ordinary_items`, su fórmula está publicada; si solo trae `wrong_penalty_fraction`, no. Además
   obligaría a regenerar fixtures verificados por `sha256` para un cambio que es de cálculo.
3. **Deducirlo de los campos publicados de la parte** (elegida).

## Decisión

`StudyService._regla` construye la regla de cada parte con esta prioridad, y ninguna rama inventa nada:

1. **`fail_if_errors_gte`** declarado → `pass_fail`: la parte se evalúa como apto o no apto por número
   de errores, sin puntuación. El veredicto es `errores < umbral` (cinco errores pasan, seis no).
2. **`options_per_question`, `score_max` y `ordinary_items`** declarados → `scaled`: la nota de la
   prueba es la que publica la convocatoria, `(Y/T)·(A − E/(N−1))`, y su umbral se aplica.
3. **`wrong_penalty_fraction`** declarado → `direct`: se calcula `A − E·p` y la calificación oficial
   queda declarada como no disponible (ADR-010).
4. Nada de lo anterior → **no se corrige** y la sesión no se crea: 409 con el motivo.

Dos consecuencias que se aplican a propósito:

- **una práctica parcial de una parte escalada no se escala**: `T` es el número de preguntas del
  cuestionario, así que con cuatro preguntas se muestra la puntuación directa con la penalización
  `1/(N−1)` y se dice por qué. La nota sobre cien solo aparece con el cuestionario completo;
- **el total suma solo las partes numéricas**, y el proceso **no** se declara superado: superar la
  oposición depende de la fase de concurso y del número de plazas, que no están en los perfiles.

## Consecuencias

- Los fixtures no cambian: la deducción usa datos que ya estaban publicados y citados.
- Si una convocatoria futura publicara la fórmula sin el número de alternativas, caería en
  `direct` (o no se corregiría) en lugar de escalar mal. Es la limitación conocida de esta decisión y
  está anotada en `docs/slices/S08.md`: antes de añadir más perfiles conviene decidir si merece un
  campo explícito.
- La forma con la que se corrigió cada parte viaja en el resultado (`kind`) y se enseña, así que una
  puntuación siempre se puede explicar.

## Reversión

Si se decide que el perfil declare la forma de corrección, el cambio es local: un campo `scoring` en
los fixtures curados y su lectura en `_regla`, con la deducción como respaldo. Nada de lo guardado
cambia, porque lo que se guarda son los números y la forma con la que se calculó.
