# OpoFuente — decisiones e incógnitas

## Decisiones ratificadas

| ID | Decisión | Motivo |
|---|---|---|
| D001 | Repositorio independiente | dominio/ciclo distintos de Accesio |
| D002 | Local-first, un usuario | utilidad personal y privacidad |
| D003 | Biblioteca antes de RAG | ordenar y verificar es el problema actual |
| D004 | Originales inmutables por hash | seguridad y reversibilidad |
| D005 | Fuente global, mapping por oposición | evitar duplicar leyes sin mezclar niveles |
| D006 | Clasificación híbrida y auditable | la IA no otorga autoridad |
| D007 | Pregunta/clave/explicación separadas | modelos, correcciones y conflictos |
| D008 | Python + React | ecosistema documental e interacción rica |
| D009 | SQLite/FTS5 + Qdrant local | local, híbrido y reconstruible |
| D010 | Worker SQLite | suficiente para un usuario, sin Redis |
| D011 | IA desacoplada | privacidad, coste y no vendor lock-in |
| D012 | Perfiles TAI-2025 y GC-2026 versionados | no convertir convocatorias en constantes |
| D013 | No cubrir psicofísico GC | seguridad, alcance y profesionales |
| D014 | Exportar a Obsidian/Anki | portabilidad y herramientas maduras |
| D015 | Un solo temario común versionado; las convocatorias lo **referencian** (O1/O2) | evitar 40 temas copiados por convocatoria y dos verdades del mismo temario |
| D016 | Re-atribuir al común preguntas y fallos con equivalencias **aceptadas**, informe por fila e inverso (O3) | lo dudoso se queda donde estaba y se revisa; nada se mueve a ciegas |
| D017 | Las convocatorias C1 se importan como tarea propia, con ref `primary` y estado de confianza (O4) | un listado sin bases no puede parecer una convocatoria confirmada |

## Incógnitas con default no bloqueante

### Q001 Nombre

Default: OpoFuente provisional. No registrar marca/dominio antes de validar.

### Q002 Embeddings

Default: interfaz y disabled primero; benchmark multilingual E5 en S09. ADR por recall español,
memoria y latencia.

### Q003 LLM

Default: ninguno. En S09 configurar OpenAI-compatible u Ollama según elección del propietario.

### Q004 OCR

Default: Tesseract opcional. Si falta, marcar y continuar; no instalar silenciosamente.

### Q005 Umbrales de clasificación

Default: nunca autoaceptar críticos; resto provisional. Calibrar con muestra S04.

### Q006 Repaso

Default: intervalos deterministas de SPEC-06. Evaluar FSRS con datos suficientes.

### Q007 Borrado físico

Default: archivar/excluir. Diseñar garbage collection tras backup fiable.

### Q008 Distribución

Default: scripts Windows. Instalador/Electron después de cuatro semanas de uso.

### Q009 Fechas de examen

Default: opcionales y con fuente; no inferir.

### Q010 Profundidad del programa

Default: estructura oficial. Subepígrafes explicativos son propuestas salvo publicación expresa.

## Requieren decisión futura nueva

Nube/multiusuario, precio, corpus compartido, tercera oposición, móvil/Electron, crawling periódico,
oral, recomendaciones médicas/físicas, fine-tuning, comunidad y borrado definitivo automatizado.

## Resolución

Crear `docs/decisions/ADR-NNN-titulo.md` con contexto, opciones, datos, decisión, consecuencias y
reversión. La ausencia de decisión no autoriza escoger lo más cómodo si afecta seguridad o privacidad.

