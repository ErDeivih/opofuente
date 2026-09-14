# OpoFuente — plan de implementación por slices

## 1. Reglas

- Ejecutar en orden. Un slice no comienza si sus criterios previos no están verdes.
- Cada slice debe ser demostrable desde UI/API, no solo contener clases.
- Mantener migraciones pequeñas y ascendentes.
- Datos reales solo mediante copia de muestra después de S04.
- LLM, OCR y vectorial son adaptadores opcionales; sus fallos no rompen la biblioteca.
- Cada slice termina con `docs/slices/Sxx.md` y evidencia de ejecución.

Las estimaciones son de alcance relativo, no horas comprometidas.

## S00 — repositorio y puertas

### Entrega

- Crear `F:\EspacioCodigo\opofuente` y `git init`.
- Estructura definida en arquitectura.
- Backend FastAPI y frontend React/TS/Vite mínimos.
- SQLite/Alembic inicial, configuración y health/capabilities.
- Ruff, mypy, pytest, ESLint, TypeScript, Vitest, Playwright y CI.
- Scripts PowerShell documentados para instalar, desarrollar, probar y construir.
- Copiar este paquete a `docs/product-spec/` y convertir `14_NEW-REPO-AGENTS.md` en `AGENTS.md`.

### No incluye

Entidades de negocio, uploads, IA ni UI de producto más allá de shell/estado.

### Aceptación

- Instalación limpia documentada en Windows.
- API y web arrancan; readiness comprueba DB.
- Migración desde DB vacía.
- Todas las puertas ejecutadas con al menos un test real por capa.
- `.env`, `data`, modelos y secretos ignorados.

## S01 — perfiles, convocatoria y programa

### Entrega

- Entidades/repositorios de oposición, convocatoria y programa.
- Fixtures versionados TAI-2025 y GC-2026 desde fuentes oficiales.
- API de perfiles y árbol.
- Selector de oposición y pantalla Programa en lectura.
- Reglas de examen validadas, todavía sin sesiones.

### Aceptación

- TAI tiene exactamente 4 bloques y 33 temas.
- GC tiene 25 temas y partes escritas configuradas.
- Solo una convocatoria activa por oposición.
- Fixture repetido es idempotente.
- Enlaces oficiales y fecha aparecen en UI.

## S02 — artefactos, inventario y lotes

### Entrega

- Almacén SHA-256 e invariantes de ruta.
- Inventario local en lectura.
- Lotes/items/incidencias/jobs persistidos.
- Worker con lease, reanudación y cancelación.
- API y Bandeja: seleccionar carpeta, preview, progreso e informe básico.

### Aceptación

- Originales mantienen hash y fecha.
- Dos archivos idénticos crean un artefacto y dos orígenes.
- Caída/reinicio no duplica.
- Cancelación deja informe coherente.
- Path traversal/junction fuera de raíz se bloquea y registra.

## S03 — extractores seguros

### Entrega

- PDF, DOCX, TXT/MD, HTML, CSV/JSON preview e imágenes preservadas.
- Representaciones versionadas, secciones/páginas y calidad.
- Detección OCR candidate; Tesseract opcional.
- ZIP y URL seguros con sus tests negativos.
- Lector de original/texto con warnings.

### Aceptación

- Fixtures extraídos con estructura esperada.
- HTML activo nunca se ejecuta.
- ZIP traversal/bomb rechazados.
- SSRF bloquea redes no permitidas tras redirección.
- Sin OCR, imagen queda pendiente y la app continúa.

## S04 — clasificación y revisión

### Entrega

- Propuestas por tipo, oposición, tema, autoridad y derechos.
- Motor determinista y puerto de clasificador; LLM puede permanecer disabled/mock.
- Grupos, bulk accept/reject/override y undo.
- Duplicados de texto y clusters de similitud.
- Cobertura provisional/aceptada.

### Aceptación

- Ninguna etiqueta crítica se confirma automáticamente.
- Una aceptación masiva permite excepciones.
- Deshacer restaura mappings/estados y audita.
- Dataset sintético produce métricas reproducibles.

### Puerta humana

Importar copia de 20–50 archivos TAI y medir revisión. Si no ahorra tiempo, no iniciar S05 sin rediseño
aprobado.

## S05 — biblioteca, versiones y colecciones

### Entrega

- Documento lógico/versión/derechos/secciones/evidencias.
- Promoción de artefacto a documento y mappings muchos-a-muchos.
- Biblioteca, filtros, lector, versiones y colecciones.
- Diff básico y `supersedes` confirmado.

### Aceptación

- Una fuente compartida se guarda una vez y se asigna a TAI/GC.
- La versión antigua no se pierde.
- Fuente pobre/candidata no cuenta como cobertura aceptada.
- Derechos desconocidos permanecen restringidos.
- Citas abren página/sección correcta.

## S06 — importador y banco de preguntas

### Entrega

- Set/pregunta/opciones/claves/explicaciones.
- Parser desde texto/documento y asistente CSV/JSON.
- Reservas, modelos y anulaciones.
- Duplicados y opciones reordenadas.
- UI Preguntas, editor, conflictos y original.

### Aceptación

- Filas inválidas no abortan el lote.
- Sin plantilla, examen oficial queda sin clave.
- Respuesta privada no se convierte en oficial.
- Negaciones se conservan.
- Claves conflictivas no se fusionan.

## S07 — sesiones y puntuación TAI

### Entrega

- Sesión/pregunta/intento/evaluación.
- Práctica y examen TAI.
- Cronómetro, guardado, navegación, finalización y revisión.
- Puntuación directa de servidor, reservas y soporte de criterio oficial versionado cuando exista.
- Prevención de fuga de solución.

### Aceptación

- Casos matemáticos de puntuación directa TAI revisados manualmente.
- Sin baremo importado, la UI no inventa calificación oficial 0–50 ni estado apto.
- Recargar conserva intento.
- API/HTML no contienen solución antes de corregir.
- Resultado separa partes, fallos, blancos y reservas.

## S08 — Guardia Civil y claves versionadas

### Entrega

- Modos GC de ortografía, gramática, conocimientos, inglés y aptitudes.
- Fórmula y umbrales GC 2026.
- Modelos A/B y claves v1/v2.
- Recalculo con evaluación versionada.

### Aceptación

- Regla de seis errores exacta.
- Fórmula `A-E/(N-1)` verificada.
- Reservas/anulaciones correctas.
- UI explica cambio de resultado por clave nueva.
- Personalidad/físicas no se presentan como evaluadas.

## S09 — búsqueda y RAG verificable

### Entrega

- FTS5, Qdrant local y reconstrucción.
- Embeddings disabled/local/external.
- Búsqueda híbrida y filtros.
- Query/retrieval/answer/claims/citations.
- LLM OpenAI-compatible/Ollama/disabled.
- Vista Preguntar y evidencia.

### Aceptación

- FTS funciona sin vector/LLM.
- No se mezclan modelos vectoriales.
- Obsoletas excluidas por defecto.
- Pregunta negativa retorna insuficiente.
- Claims solo citan spans entregados.
- Dataset patrón cumple puertas RAG.

## S10 — errores, repaso y exportación

### Entrega

- Error/repaso e intervalos deterministas.
- Cola Hoy, conceptos, causas y notas.
- Exportación Anki CSV y Markdown/Obsidian.
- Inicio recomienda siguiente tarea.

### Aceptación

- Fallo crea repaso; historial no se sobrescribe.
- Exportaciones contienen procedencia/versiones.
- Material restringido requiere aviso.
- Dominio muestra insuficiencia con pocos datos.

## S11 — cambios e invalidación

### Entrega

- ChangeSet y dependencias.
- Diff por sección y derivados afectados.
- `needs_review`, resolución y UI Cambios.
- Simulación de cambio normativo.

### Aceptación

- Solo derivados dependientes se invalidan.
- Relación de versión exige confirmación.
- Reindexación/caché respetan corpus revision.
- No se interpreta automáticamente efecto jurídico.

## S12 — backup, endurecimiento y release local

### Entrega

- Backup/validate/restore atómico.
- Logs sanitizados, diagnóstico, límites y CSP.
- Baseline de rendimiento y tablas virtualizadas.
- Accesibilidad/E2E completa.
- Scripts de build/release local y manual de operación.

### Aceptación

- Restore en vacío reproduce hashes, DB y sesiones.
- Fallo de restore deja instalación anterior utilizable.
- Ningún secreto/contenido privado en logs.
- Suite y auditoría de dependencias verdes.
- Puede comenzar prueba personal de cuatro semanas.

## S13 — generación de preguntas, condicional

Solo si S09 supera evaluación y la prueba personal confirma necesidad.

Entrega candidatos desde evidencias, verificador independiente, deduplicación, cuarentena, explicación
por opción e invalidación. No continuar si revisar una pregunta cuesta casi lo mismo que escribirla o
si la ambigüedad supera el umbral acordado.

## 2. Release MVP

El MVP personal termina en S12. S13 es experimental. Comercialización, nube y tercera oposición
requieren una decisión nueva.
