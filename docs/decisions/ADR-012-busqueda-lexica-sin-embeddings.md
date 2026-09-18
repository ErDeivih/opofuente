# ADR-012 — La búsqueda del corpus es léxica (FTS5) hasta que exista un proveedor de embeddings

- **Estado:** aceptada (decisión del codificador al abrir S09); **pendiente de ratificación del propietario**
- **Fecha:** 18 de septiembre de 2026
- **Ámbito:** recuperación e índice (S09), y lo que herede S10+
- **Asunto:** con qué se recupera el corpus y qué se declara mientras no haya vectores

## Contexto

`02_ARCHITECTURE` y `05_RAG` §4 piden un índice léxico **y** uno vectorial (Qdrant local con payload de
identificadores), y §10 fija métricas de recuperación (Recall@10 ≥ 0,90) que solo se pueden medir con el
conjunto patrón de §9. A la vez, §4 dice dos cosas que atan las manos:

- el modelo de embeddings **se fija por ADR tras un benchmark en español**; y
- **no se descarga ningún modelo al iniciar sin avisar**.

Al abrir S09 no hay benchmark, no hay modelo decidido y no hay proveedor de embeddings configurado
(`Settings.embedding_provider = "disabled"`). Y el patrón de evaluación de §9 —50 consultas TAI, 30 GC,
20 que deben rechazarse— no existe: es material con datos reales, y fabricarlo ahora sería inventar la
vara con la que se mide el producto.

## Opciones consideradas

1. **Elegir un modelo de embeddings y descargarlo** (familia multilingual E5 u otra). Descartada: §4
   prohíbe descargar al iniciar sin aviso y el nombre debe fijarse por ADR **con un benchmark** que
   nadie ha hecho. Decidirlo aquí sería cambiar el orden que el propio proyecto exige.
2. **Simular la búsqueda vectorial** (devolver ceros, o reordenar por parecido de cadenas y llamarlo
   «híbrida»). Descartada: es la trampa que `16_TRACEABILITY §4` prohíbe. Una fusión falsa no mejora
   el recall y envenena las métricas: nadie sabría después si el 0,90 de Recall@10 se midió contra
   vectores reales o contra ruido.
3. **Retrasar S09 hasta tener vectores.** Descartada: el producto se queda sin buscar nada, y §5 dice
   expresamente que **FTS sigue funcionando si los embeddings están desactivados** y que el endpoint
   devuelve resultados sin generar respuesta.
4. **Construir la recuperación léxica completa (FTS5), el puerto vectorial y la degradación
   declarada** (elegida).

## Decisión

**El corpus se recupera con FTS5 sobre el texto normalizado de las evidencias** (`evidence_fts`, tabla
de contenido externo sobre `evidence_spans`, `bm25` como orden y prefijos por término), y el índice
vectorial queda como un **puerto** (`VectorSearch`, en `application/ports.py`) cuya implementación
activa declara no estar disponible, con su motivo.

Reglas concretas:

1. la respuesta de búsqueda y de RAG **dice** que la recuperación fue solo léxica
   (`degradations`), en lugar de devolver menos resultados en silencio;
2. `POST /search` y `POST /rag/queries` aceptan `strategy: lexical|hybrid`: pedir `hybrid` sin proveedor
   no falla ni miente, se degrada a léxico y se declara;
3. el índice es **reconstruible desde SQLite** (§4): el texto vive en `evidence_spans`, la tabla FTS es
   derivada y se rehace sin salir de la base;
4. `/capabilities` declara el estado real: `fts5` operativo (comprobado ejecutando FTS5 en este equipo
   **y** que el índice existe en esta base), `vector_index` no disponible con el motivo y sin prometer
   un slice, y `embeddings` no configurado;
5. la evaluación de §9-§11 se hará cuando existan modelo y patrón; **no** se declaran métricas de
   recuperación que nadie haya medido.

## Datos que la sostienen

- El SQLite de este equipo soporta FTS5 3.49.1 (comprobado en `SqliteCapabilityProvider` en cada
  arranque): tabla de contenido externo, `snippet`, `bm25` y disparadores de sincronización funcionan
  (`apps/api/tests/integration/test_migrations_0018.py`).
- La búsqueda real sobre material ingerido devuelve el fragmento con su cita, excluye lo no publicado
  con su motivo y no responde sin evidencia: `apps/web/tests/e2e/search.spec.ts` (E2E-08) lo recorre
  entero con un `.txt` sintético promocionado a documento.
- Una versión sustituida **no** entra (se informa de por qué) y la que la sustituye sí: mismo guion,
  punto 7.

## Consecuencias

- Se puede buscar y preguntar hoy, con citas que abren el documento, sin descargar nada y sin red.
- **El recall es el del léxico**: una pregunta con vocabulario distinto al del material («cómo se
  computa el plazo» frente a «el plazo se cuenta») puede no encontrar el fragmento. Está declarado en
  la propia pantalla y queda como limitación conocida de S09.
- La deuda **DEBT-014** registra lo que falta: proveedor de embeddings decidido por ADR con benchmark
  en español, índice vectorial local y proveedor de lenguaje. Mientras no se cierre, ni el estilo de
  respuesta ni el rerank pueden depender de un modelo.
- La fusión por RRF (`.reciprocal_rank_fusion`) y la diversificación ya existen y están probadas, así
  que añadir el vectorial es escribir un adaptador y encender una rama, sin tocar el contrato.

## Reversión

Enchufar un proveedor: implementar `VectorSearch` (adaptador con su modelo y dimensión), registrarlo en
`SearchService` y pasar `strategy: hybrid`. El contrato ya admite `hybrid`, `strategies` y las
degradaciones; nada de lo guardado cambia, porque las consultas y los hits guardan la estrategia con la
que se recuperaron. Apagar el proveedor devuelve el sistema a esta decisión sin migración.
