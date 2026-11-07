# INVESTIGACIÓN — cómo organizan el temario las academias de informática C1

**Fecha:** 7 de noviembre de 2026.
**Qué es:** la investigación inicial que pide `AGENTE.md`. No sustituye a la especificación ni
convierte a ninguna academia en autoridad: el producto se apoya en bases y boletines oficiales.
Aquí solo se mira **cómo se organiza y se vende** el temario para detectar qué nos falta.

## Qué se ha mirado

| Fuente | Qué aporta | Acceso |
|---|---|---|
| [MasterD — Temario TAI 2026](https://www.masterd.es/blog/temario-tai) | estructura oficial del TAI, examen y método de estudio | página completa |
| [Oposiciones.red — Simulacro Técnico Auxiliar de Informática (Jaca)](https://oposiciones.red/estudio/simulacro/BOE-A-2025-22895) | un temario local C1 real de **40 temas**, reparto por materia y modelo de producto | página completa |
| [OposicionesInformática — Temario oposiciones TIC](https://oposicionesinformatica.com/temario-oposiciones-tic/) | índice por A1/A2/C1 y convocatorias | página consultada; el texto completo no se sirvió a la herramienta |
| [ADAMS — Orientaciones generales TAI (PDF)](https://www.adams.es/wp-content/uploads/2024/01/OrientacionesGenerales_TAI.pdf) | orientación de una academia clásica | PDF no accesible en la fecha (HTTP 500) |
| [Redopositor — TAI gratis: programa oficial y recursos](https://redopositor.com/blog/es-temario-tai-gratis-donde-encontrar-2026/) | recursos gratuitos y programa | página consultada; el texto completo no se sirvió a la herramienta |

No se ha copiado contenido con derechos: se resume y se enlaza. Las páginas que no se pudieron leer
se citan como consultadas, no como evidencia de su contenido.

## Lo que hacen

**El TAI (Estado) es el esqueleto.** MasterD confirma 33 temas en 4 bloques: Organización del Estado
y Administración electrónica (9), Tecnología básica (5), Desarrollo de sistemas (9) y Sistemas y
comunicaciones (10). El examen son dos partes eliminatorias: test de hasta 80 preguntas y un supuesto
práctico de 20 preguntas elegido entre dos opciones de los bloques III y IV, 120 minutos y un tercio
de penalización por error. La academia insiste en estudiar por bloques, alternar legislación y
técnica, hacer test, analizar errores y practicar supuestos.

**Las C1 locales parecen otro temario, pero se solapan.** Oposiciones.red analiza una plaza de Jaca
con **40 temas**, de los que reconoce la materia de 15: ofimática e informática básica, el municipio,
la Constitución, derechos fundamentales, organización territorial, Estatutos, acto administrativo,
procedimiento (Ley 39/2015), recursos, bienes locales, igualdad y administración electrónica. Es
decir: la parte jurídica local se mezcla con la técnica, y el bloque jurídico cambia de una
convocatoria a otra; la técnica se repite mucho más.

**El producto que se vende no es solo el temario.** Oposiciones.red vende tres cosas que nosotros
debemos mirar de cerca:

1. **Preguntas atadas a la norma y a su versión**, con enlace al artículo del BOE en cada respuesta.
2. **Dos fechas**: cuándo se contrastó con el BOE y de cuándo es el texto consolidado que se estudia.
   Cuando el BOE cambia un artículo, la pregunta vuelve al repaso aunque estuviera dominada.
3. **Simulacros repartidos como el temario real de una convocatoria** (no un test genérico), casos
   prácticos corregidos y un plan de «qué hacer hoy».

MasterD, en cambio, vende preparación guiada, temario actualizado, planificación, simulacros y
profesor. Ninguna de las dos plantea **un único temario versionado que varias convocatorias
referencien**: cada una mantiene su copia por convocatoria y su banco genérico, y el negocio está en
actualizarla.

## Qué nos falta (y qué no)

**Lo que ya tenemos y ellos no plantean igual:** un temario común **versionado**, convocatorias que lo
**referencian** con su cita, particularidades por convocatoria sin copiar el temario, y la ficha del
tema con apuntes, material y preguntas enlazadas. Eso es exactamente el hueco que el producto quiere
cubrir.

**Lo que ellos tienen y nosotros no:**

- aviso de **vigencia normativa** por tema (fecha del texto consolidado, no solo la cita de la base);
- **casos prácticos** como contenido propio, no solo preguntas tipo test;
- **simulacro por bloque** (o por convocatoria) a partir del banco, con reparto de materias;
- preguntas enlazadas al **artículo** concreto de la norma, no solo a la pregunta.

## Propuesta concreta (Nivel 2)

**B-017 — Simulacro por bloque del temario común.**

Hoy la ficha del tema enlaza al banco, pero no hay forma de decir «hazme un test del bloque III con lo
que tengo catalogado». Las dos referencias insisten en practicar por bloques y con el reparto real del
examen; es la pieza de estudio que más valor añade sin tocar el modelo de datos:

- **Qué:** desde `/temario`, un botón por bloque que compone una sesión de estudio con las preguntas
  **aceptadas** mapeadas a los temas de ese bloque (mismo reparto que el banco ya conoce), con las
  reglas de examen de la convocatoria activa o, si no hay, un modo práctica sin nota.
- **Por qué ahora:** usa `curriculum_mappings` (B-003), la composición de sesiones (S07) y el vínculo
  ficha→banco (B-016); no inventa contenido ni requiere fuentes nuevas.
- **Criterio de aceptación:** un bloque con preguntas produce una sesión con todas las preguntas
  aceptadas de sus temas; un bloque sin preguntas lo dice y no crea una sesión vacía; la corrección y
  la penalización son las de la convocatoria activa; ninguna pregunta rechazada o sustituida entra.
- **Riesgo:** si el banco no tiene preguntas de un bloque, el botón no debe parecer roto; se enseña
  «sin preguntas todavía» y se enlaza a la ficha del tema.

**Siguiente propuesta, si B-017 sale bien (B-018, Nivel 2/3):** añadir a cada tema la **fecha del
texto normativo** que estudia y marcar cuándo una pregunta se apoya en una versión anterior. Es lo
que hace Oposiciones.red y lo que más echa de menos hoy; exige decidir de dónde sale esa fecha y quién
la mantiene, así que no se hace de paso.

## Lo que no se propone

- Copiar temarios de academias ni sus bancos: el producto se apoya en el BOE/BOCYL y en las bases.
- Convertir las preguntas en «contenido oficial»: siguen siendo material revisable.
- Perseguir el temario de cada convocatoria local una a una: para eso está el modelo de
  particularidades y la importación de convocatorias, no 40 copias.
