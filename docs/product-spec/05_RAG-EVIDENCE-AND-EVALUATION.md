# OpoFuente — RAG, evidencias y evaluación

## 1. Principio

RAG no es la fuente de verdad. Recupera candidatos y ayuda a redactar. La autoridad reside en versiones
aceptadas y evidencias identificables. Una respuesta bien escrita sin respaldo debe aparecer como
insuficiente.

## 2. Corpus elegible

Por defecto solo se recuperan:

- documentos `accepted`;
- representaciones `good` o `usable_with_warnings`;
- evidencias asignadas a la convocatoria/oposición activa o compartidas explícitamente;
- versiones vigentes para la fecha seleccionada;
- material privado del usuario actual;
- idiomas admitidos.

Se excluyen `candidate`, `poor`, `superseded`, `rejected` y generado como fuente primaria. El usuario
puede consultar una versión histórica de manera explícita.

## 3. Fragmentación

### Jurídica

Unidad principal: artículo/disposición, conservando jerarquía y título. Artículos largos se dividen por
apartados con solapamiento lógico; nunca separar una excepción de su inciso sin incluir contexto.

### Técnica

Encabezados, subsecciones, listas y tablas. Tamaño objetivo orientativo 300–800 tokens, subordinado a
la estructura. Guardar ruta de encabezados y versión del producto/estándar.

### Apuntes

Por secciones/epígrafes. Mantener marcas de página y autoridad privada. Las notas del usuario pueden
ser evidencia personal, nunca oficial.

### Preguntas

No indexar clave/explicación junto al enunciado en modos de examen para evitar fuga. Índices separados:
`question_prompt` y `question_solution`.

## 4. Indexación

- FTS5 sobre texto normalizado, títulos, identificadores y ruta de sección.
- Embedding de `title path + text`, sin añadir respuestas generadas.
- Qdrant payload con IDs y filtros, no copia de metadatos autoritativos.
- `corpus_revision` aumenta tras cambios que afecten búsqueda.
- Índices reconstruibles desde SQLite y representaciones.

Modelo local inicial para evaluar: familia multilingual E5 de tamaño compatible con el equipo. El
nombre exacto se fija mediante ADR tras benchmark español; no descargar modelos al iniciar sin aviso.

## 5. Recuperación híbrida

1. validar consulta y filtros;
2. detectar oposición, convocatoria y fecha activa;
3. buscar FTS5 y vectorial en paralelo;
4. normalizar scores y fusionar por Reciprocal Rank Fusion;
5. ampliar contexto padre/hijo cuando una unidad requiere título o excepción;
6. rerank opcional;
7. diversificar evitando diez fragmentos equivalentes;
8. construir paquete de evidencia con límite de tokens;
9. guardar todos los hits y los finalmente usados.

FTS sigue funcionando si embeddings están desactivados. El endpoint devuelve también resultados sin
generar una respuesta.

## 6. Contrato de respuesta

El modelo recibe:

- pregunta;
- perfil/convocatoria/fecha;
- instrucciones de no usar conocimiento externo como hecho;
- fragmentos numerados con metadatos;
- esquema JSON requerido.

Salida validada:

```json
{
  "status": "supported | partial | insufficient",
  "short_answer": "...",
  "explanation": "...",
  "claims": [
    {
      "text": "...",
      "evidence_ids": ["uuid"],
      "support": "direct | inferred"
    }
  ],
  "uncertainties": ["..."],
  "suggested_followups": ["..."]
}
```

Validación posterior:

- todos los IDs existen y fueron entregados al modelo;
- cada afirmación factual importante tiene evidencia;
- un verificador independiente comprueba entailment/contradicción cuando está configurado;
- si falla el esquema o las citas, no mostrar como `supported`;
- la UI permite abrir sección, página y original.

No se muestra una bibliografía global como sustituto de citas por afirmación.

## 7. Respuestas legales y técnicas

- Mostrar versión y fecha de la norma.
- Avisar que los textos consolidados del BOE son informativos.
- Si una pregunta exige interpretación no explícita, marcar inferencia.
- En conflictos, describirlos; no elegir silenciosamente.
- En técnica, no mezclar versiones de estándares/productos sin indicarlo.
- La explicación didáctica puede usar ejemplos generados, etiquetados como ejemplos.

## 8. Generación de preguntas

No forma parte de los primeros slices. Cuando se habilite:

1. seleccionar epígrafe y evidencias aceptadas;
2. generar candidato con una única mejor respuesta;
3. generar distractores ligados a errores plausibles;
4. producir justificación por opción y citas;
5. ejecutar verificador distinto del generador;
6. buscar duplicados;
7. colocar en cuarentena;
8. revisión humana o promoción conforme a política validada.

Nunca etiquetar `official`. Si cambia una evidencia, la dependencia la marca `needs_review`.

## 9. Conjunto patrón

Crear y versionar:

- 50 consultas TAI: factual, comparativa, negativa y multifuente;
- 30 consultas GC sobre temas legales y técnico-científicos;
- 20 consultas que deben resultar `insufficient`;
- 20 casos de versión antigua/vigente;
- 30 preguntas oficiales con explicación manual y evidencia;
- casos de OCR malo y fuente conflictiva.

Cada caso define fuentes permitidas, evidencias relevantes, respuesta mínima y afirmaciones prohibidas.

## 10. Métricas

### Recuperación

- Recall@5/10;
- MRR y nDCG@10;
- cobertura de evidencias necesarias;
- porcentaje de resultados obsoletos filtrados;
- latencia p50/p95 en equipo local de referencia.

### Respuesta

- exactitud por caso;
- fidelidad/entailment de claims;
- precisión y completitud de citas;
- tasa de rechazo correcto;
- sobre-rechazo;
- contradicciones;
- utilidad humana 1–5.

### Preguntas generadas

- una única respuesta defendible;
- en programa;
- distractores incorrectos;
- citas suficientes;
- duplicidad;
- minutos de revisión por pregunta aceptada.

## 11. Puertas de calidad

El RAG no pasa a uso normal si:

- Recall@10 de evidencias patrón es menor de 0,90;
- alguna respuesta `supported` contiene una afirmación central sin evidencia;
- versiones obsoletas aparecen cuando se pidió vigente;
- la cita no abre el fragmento correcto;
- el sistema responde cuando el patrón exige rechazo en más del 5 % de casos críticos.

Los umbrales pueden revisarse mediante ADR con datos; no se reducen para poner verde una entrega.

## 12. Benchmark de referencia

Ejecutar las mismas preguntas con el mismo corpus en NotebookLM y en OpoFuente. Registrar tiempo de
preparación, calidad, citación y rechazo. No comparar estilos subjetivos solamente. OpoFuente debe
ganar en inspección de evidencia, versiones y cobertura, aunque no siempre redacte mejor.

## 13. Privacidad y costes

Antes de una llamada externa, mostrar proveedor y política configurada. En modo privado estricto usar
solo local o desactivar generación. Cachear por hash de consulta, filtros, corpus, modelo y plantilla;
no reutilizar respuestas después de un cambio de corpus.

