# ADR-010 — La puntuación se calcula con fracciones exactas, y la calificación oficial no se inventa

- **Estado:** aceptada (decisión tomada al abrir S07 para cerrar DEBT-006)
- **Fecha:** 17 de septiembre de 2026
- **Ámbito:** puntuación de sesiones y exámenes (S07, y la base de S08)
- **Asunto:** con qué aritmética se corrige un examen, y qué se puede afirmar sin el baremo oficial

## Contexto

DEBT-006 dejó escrito antes de S07 que había que decidir y probar la representación exacta **antes** de
calcular puntuaciones, con este argumento: la penalización de TAI es un tercio exacto, la fórmula de GC
lleva una división por `N − 1`, y la base guarda esos valores como `float` (`0.3333333333`). Tres
errores en una parte con penalización de un tercio tienen que descontar exactamente un punto; con
aritmética binaria descuentan `0.9999999999` y el cuarto decimal de una nota lo nota.

Y hay una segunda parte del problema, que no es de representación sino de autoridad: la convocatoria de
TAI dice que cada parte se califica de 0 a 50 y que la calificación resulta de **transformar** las
puntuaciones directas con los baremos que fija la Comisión Permanente de Selección. Esos baremos no
están publicados en el anexo, así que la aplicación no puede decir «25 puntos» ni «apto»: solo puede
calcular la puntuación directa y decir que la calificación oficial no está disponible.

## Opciones consideradas

1. **`float` con redondeo a la hora de mostrar.** Descartada: es exactamente lo que DEBT-006 prohíbe.
   Redondear al final no arregla que la resta ya se hizo mal, y con umbrales enteros una décima cambia
   un resultado.
2. **`Decimal` con precisión y modo de redondeo declarados.** Es manejable, pero `Decimal` sigue siendo
   una aproximación con dígitos: `1/3` no se representa, y la penalización de TAI **es** `1/3`. Se
   usaría para sumar cosas que en realidad son fracciones, y volvería el problema del residuo por otro
   camino.
3. **Fracción exacta (`Fraction`) recuperada del decimal almacenado** (elegida).
4. **Guardar la fracción publicada como texto en el fixture** (`"1/3"`) y leerla de ahí. Es tentador,
   pero el dato ya existe con su cita: `exam_rules.wrong_answer_penalty` dice «1/3 del valor de una
   respuesta correcta» con su evidencia. Añadir un campo nuevo al fixture curado duplicaría el mismo
   hecho en dos sitios que pueden divergir, y obligaría a regenerar fixtures verificados por `sha256`
   para un cambio que es de cálculo, no de datos.

## Decisión

**Se calcula con `Fraction` y se guarda como numerador y denominador.** La regla de conversión es
explícita y falla cuando no se cumple:

- el decimal almacenado (`0.3333333333`) es **información** (qué dice la convocatoria), no autoridad de
  cálculo;
- la fracción exacta es la **más simple** que coincide con ese decimal dentro de media unidad de su
  última cifra (tolerancia `1 / 2·10¹⁰`) y con denominador **≤ 100**;
- si el decimal no corresponde a ninguna fracción así, `exact_fraction` **lanza un error** y no se
  calcula nada: una penalización que nadie ha publicado no se aplica en silencio.

Con eso: `exact_fraction(0.3333333333) == Fraction(1, 3)`, `exact_score(0, 3, 1/3) == Fraction(-1)`
exacto, y `attempt_evaluations` guarda `score_numerator = -1`, `score_denominator = 3`.

El decimal existe **solo para enseñarlo**, en un único sitio (`decimal_text`), con redondeo
`ROUND_HALF_UP` a cuatro decimales. El valor exacto viaja aparte, así que redondear al mostrar no
pierde información.

**Y la calificación oficial no se calcula.** `SessionResult` lleva `official_available = False` y su
nota: la puntuación directa es real; el 0-50 y el aprobado necesitan el baremo publicado. Los umbrales
de la convocatoria (`score_max`, `pass_score`) se enseñan **como datos declarados** con su cita, no se
aplican a una puntuación directa: comparar `A − E/3` con el mínimo oficial de 25 sería inventar un
apto. Cuando exista un criterio oficial importado, se aplicará como una capa nueva
(`official_available = True` con su fuente), sin tocar el cálculo directo.

## Consecuencias

- Los `float` de `exam_parts` se quedan como están: son la cita numérica de la convocatoria y siguen
  siendo la referencia para leer qué dice. No se convierten en autoridad de cálculo.
- `attempts` no guarda el acierto ni los puntos: el acierto se deduce de la evaluación, y así no hay
  dos verdades que puedan separarse (03_DATA-MODEL §7 los pone en `attempts`; se aparta de esa
  literalidad a propósito, y el porqué está aquí escrito).
- Recalcular con una clave nueva (S08) añade una fila de `attempt_evaluations` que sustituye a la
  anterior (`supersedes_id`), en vez de sobrescribirla: la puntuación anterior sigue siendo legible, y
  con ella se puede enseñar «tu puntuación cambió de X a Y».
- Una penalización con denominador grande (por ejemplo `0,2857142857` = 2/7 pasa, `0,1234567891` no)
  detendría el cálculo de esa convocatoria hasta que alguien decida cómo representarla. Es una parada
  deliberada: preferimos fallar a puntuar mal.

## Reversión

Si alguna convocatoria publicara una penalización que no es una fracción sencilla, el cambio es local:
ampliar `MAX_DENOMINADOR` (o aceptar un decimal exacto con `Decimal`) en `domain/study.py`, con su
prueba. Nada de lo guardado cambia: numerador y denominador siguen siendo la representación exacta.
