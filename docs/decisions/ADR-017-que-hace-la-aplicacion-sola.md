# ADR-017 — Qué hace la aplicación sola y qué sigue pidiendo una persona

**Estado:** aceptada (22 de septiembre de 2026)
**Contexto de la decisión:** el propietario pidió que «el estudiante solo tenga que dar sus documentos
y archivos y que la app sola sea capaz de hacer todo y dejarlo listo para el estudio».

## Contexto

La aplicación ya hacía sola la mayor parte del camino: copia el material, lo extrae, lo clasifica con
un motor determinista y **aplica solo** las propuestas de la banda alta (menos las críticas). Lo que
seguía pidiendo manos era lo de después:

| Paso | Quién lo hacía |
|---|---|
| Soltar la carpeta, copiar, extraer, clasificar | la aplicación |
| Decidir si el material entra en la biblioteca como obra | una persona (promocionar) |
| Decidir que una versión concreta es la buena | una persona (aceptar; ADR-009) |
| Importar las preguntas de ese material | una persona, documento a documento |
| Catalogar cada pregunta por bloque y tema | nadie: no estaba construido |
| Enlazar la plantilla de respuestas con su examen | una persona, a mano |
| Saber si el material ya está listo para estudiar | nadie: había que mirar cinco pantallas |

## Decisión

**1. Se automatiza todo lo que va **después** de aceptar una versión.**

En cuanto una versión queda aceptada, la aplicación mira qué es el material (clasificación vigente),
y si es un examen oficial, un banco de preguntas privado o unos supuestos, **crea el conjunto e
importa las preguntas con su cita**, sin que nadie pulse nada. El resultado viaja en la propia
respuesta de la aceptación (cuántas preguntas, a qué conjunto, o el motivo de no haber importado
ninguna) y la ficha del documento lo cuenta.

**2. No se automatizan tres actos, y no por comodidad: por las decisiones que ya están tomadas.**

- **Aceptar una versión** (ADR-009: activar es aprobar). Es el acto que hace que el material cuente:
  sostiene cobertura, se puede citar como vigente y alimenta el estudio. Automatizarlo sería declarar
  buena una versión que nadie ha leído.
- **Otorgar autoridad o derechos** (04 §8 y ADR-006). La aplicación no decide que un material es
  oficial ni que se puede reutilizar; esos dos ejes **nunca** se autoaplican, y eso no cambia.
- **Promocionar material a la biblioteca** (crear la obra lógica). Promocionar es decir «esto es un
  documento que voy a seguir», y de ahí cuelgan las versiones, los derechos y las citas.

Lo que sí se hace con esos tres es **hacerlos fáciles**: la aplicación dice qué material está
esperando una decisión y por qué, y todo lo demás ocurre alrededor sin intervención.

**3. La importación automática no inventa de qué oposición son las preguntas.**

El conjunto se crea para la oposición y la convocatoria de la **asignación aceptada** de la versión.
Sin asignación al programa, no hay conjunto: se dice y se para. Un banco de preguntas que no está
asignado a nada es material sin destino, y adivinar el destino sería peor que no importar.

**4. Un conjunto por documento, no por versión; y un conjunto vacío se archiva.**

Si llega una versión nueva del mismo banco de preguntas, las nuevas se añaden al conjunto que ya
existe (lo que ya estaba se reconoce por su huella). Si el material decía traer preguntas y no se
reconoció ninguna, el conjunto se **archiva**: no se queda un conjunto vacío ensuciando la lista, y
tampoco se borra.

**5. Todo lo automático se cuenta.**

Cada efecto de una decisión automática viaja con su motivo: cuántas preguntas entraron, o por qué no
entró ninguna («está clasificado como temario», «no está asignado a ninguna oposición», «no se sabe
si trae preguntas»). Una automatización que no dice lo que ha hecho es indistinguible de una que no
ha hecho nada.

## Consecuencias

- El flujo del propietario queda en: **soltar la carpeta** → la aplicación copia, extrae y clasifica
  sola → él acepta las versiones que quiere usar (decisiones cortas y visibles) → **las preguntas ya
  están en el banco, con su cita**.
- El banco puede tener conjuntos que el usuario no creó. Se reconocen por su título («Preguntas de
  …»), llevan su `source_document_version_id` y se pueden archivar como cualquier otro.
- Queda pendiente, y se decidirá en S12.6: **catalogar cada pregunta por bloque y tema** (los mapeos
  existen para documentos y artefactos, no para preguntas) y **enlazar la plantilla con su examen**.
  Esta decisión no los autoriza por sí sola: cada uno tiene su propio riesgo (una pregunta mal
  catalogada envenena el diagnóstico por temas).
- Automatizar la importación **no** automatiza la corrección: las claves siguen siendo lo que son, y
  un conjunto importado sin clave activa no corrige nada (la pantalla lo dice).

## Reversión

La importación automática se apaga quitando la llamada en la ruta que acepta la versión. Lo ya
importado no se toca: los conjuntos siguen ahí, con su procedencia, y se archivan o se dejan como
estén. No hay migración ni cambio de esquema: lo que se ha añadido son tres campos **opcionales** en
la respuesta de la aceptación.
