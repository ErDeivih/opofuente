# ADR-007 — Nodos de programa con material asignado: bloquear la retirada, no borrarla

- **Estado:** aceptada (decisión del codificador, autorizada por el propietario al aprobar el alcance
  de S04: «S04 crea `curriculum_mappings` y cierra DEBT-005 dentro de S04»)
- **Fecha:** 16 de septiembre de 2026
- **Ámbito:** integridad del programa (S01) frente a la clasificación y la cobertura (S04)
- **Asunto:** qué ocurre cuando un nodo del programa desaparece del fixture oficial y tiene material
  asignado

## Contexto

`SqlAlchemyProfileRepository._sync_curriculum` borra los nodos que ya no aparecen en el fixture
versionado. Hoy es seguro porque **nada los referencia**. A partir de S04, `curriculum_mappings`
asigna material (artefactos y representaciones) a nodos del programa, y la cobertura se calcula a
partir de esos mapeos (`03_DATA-MODEL` §5). Un fixture nuevo que reorganice el temario —o una errata
del organismo que cambie la numeración— haría que la siembra borrara nodos **con documentos dentro**,
y con `ON DELETE CASCADE` se llevaría por delante las asignaciones sin avisar: el usuario vería
desaparecer su clasificación y su cobertura sin haber hecho nada.

El temario cambia de verdad: la convocatoria publica correcciones y el temario permanece entre
convocatorias «salvo modificación publicada con antelación» (ADR-006). Es decir, el caso no es
hipotético.

## Decisión

**1. La retirada de un nodo con material asignado se bloquea y se informa; nunca se ejecuta en
silencio.** Al sincronizar un fixture, la siembra:

- calcula los nodos que ya no están en el fixture (`stale`);
- separa los que tienen **alguna** fila en `curriculum_mappings` de los que no;
- borra solo los que no tienen ninguna referencia;
- **conserva** los que sí la tienen, con su ruta, su título y su posición tal como estaban, y los
  informa como **conflicto** en el resultado de la siembra (`EntityOutcome.blocked`), con el nodo y
  el motivo. La siembra termina correctamente: el resto de cambios del fixture sí se aplica.

**2. La integridad es real, no una convención del código.** `curriculum_mappings.curriculum_node_id`
se declara `FOREIGN KEY ... ON DELETE RESTRICT` y SQLite las aplica (`PRAGMA foreign_keys=ON` en cada
conexión, ya vigente desde S02). Aunque alguien borre el nodo por otra vía —SQL directo, un script
futuro, un `DELETE` mal escrito— la base **rechaza** la operación con `IntegrityError`. La guarda del
código existe para dar un mensaje útil y dejar el estado consistente, no para ser la única defensa.

**3. Qué puede hacer el usuario con un nodo bloqueado.** Nada se pierde: el nodo sigue ahí y sus
mapeos también. Retirarlo de verdad requiere una acción explícita y consciente (reasignar el material
a otros nodos y después retirar el nodo), que **no** forma parte de S04 y queda como puerta abierta
documentada en `docs/slices/S04.md`. S04 no decide por el usuario a qué nodo mover su material: eso es
exactamente lo que la aplicación no debe inventar.

## Alternativas descartadas

- **Borrado en cascada (lo que había).** Destruye clasificación y cobertura sin avisar. Descartada:
  contradice «no fabricar certeza» y la invariante 10 del modelo (borrar un lote no borra un artefacto
  compartido mientras queden referencias) en su misma lógica.
- **Versionar el nodo** (nodo antiguo y nodo nuevo conviviendo con `supersedes`). Es la solución
  correcta a largo plazo cuando el temario se reorganice de verdad, pero exige decidir identidad de
  nodo, vigencia por convocatoria y qué versión manda en la cobertura. Es una decisión de modelo mayor
  que este slice no necesita y que además tocaría la cobertura de S05; se descarta **por ahora**, no
  por imposible.
- **Reasignación automática** al nodo más parecido por título o ruta. Descartada: afirmaría una
  equivalencia que el usuario no ha confirmado. Como mucho, S04 puede *proponer* el mapeo nuevo, y esa
  propuesta pasa por la cola de revisión como cualquier otra.

## Consecuencias

- Un fixture que reorganice el temario deja de ser una operación destructiva: como mucho, deja nodos
  «colgando» que la siembra declara y que el usuario puede resolver cuando quiera.
- La siembra ya no es «idempotente respecto al fixture» en ese caso concreto: el informe dirá que hay
  nodos que no se han podido retirar. Es información honesta, no un fallo (`seed_profiles --check`
  sigue midiendo lo que mide: entidades creadas o actualizadas).
- La cobertura se calcula sobre mapeos que nunca apuntan a un nodo inexistente: la restricción lo
  hace imposible a nivel de base, no solo a nivel de consulta.

## Reversión

Volver a `CASCADE` exigiría una migración que reconstruya la tabla `curriculum_mappings` (SQLite no
altera claves foráneas en sitio), y volver a permitir el borrado silencioso de nodos con material. El
`downgrade` de la migración 0012 hace lo contrario: retira la tabla entera, así que revertir el slice
deja el esquema como estaba en S03.
