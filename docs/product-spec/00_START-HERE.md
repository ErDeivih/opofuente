# OpoFuente — empezar aquí

**Estado del proyecto:** especificado, todavía no implementado  
**Fecha de la especificación:** 14 de septiembre de 2026  
**Producto inicial:** aplicación local de escritorio-web para organizar y estudiar TAI y Guardia Civil  
**Repositorio de destino:** `F:\EspacioCodigo\opofuente` (nuevo repositorio; no implementar dentro de Accesio)

## 1. Qué se va a construir

OpoFuente es una biblioteca personal de oposiciones que transforma material desorganizado en un
sistema de estudio trazable. El usuario deja archivos, carpetas, preguntas, imágenes, texto o enlaces
en una bandeja. La aplicación conserva los originales, extrae el contenido, detecta duplicados,
propone clasificación y permite revisarla en lote.

Después, el usuario puede:

- ver qué partes del programa tiene cubiertas y cuáles no;
- buscar y leer fuentes versionadas;
- hacer preguntas y recibir respuestas con evidencias exactas;
- importar y realizar exámenes oficiales;
- practicar preguntas privadas o generadas, siempre diferenciadas;
- entender por qué falló y programar el repaso;
- saber qué apuntes o preguntas quedan afectados cuando cambia una fuente.

La primera migración será el archivo personal de TAI. Guardia Civil será el segundo perfil y validará
que el motor admite oposiciones con estructuras distintas.

## 2. Qué no es

- No es un chat genérico con PDF.
- No es una academia ni vende un temario oficial.
- No descarga ni redistribuye contenido comercial.
- No garantiza aprobar ni interpreta jurídicamente cambios normativos.
- No prepara entrevistas, personalidad, reconocimiento médico o técnica física.
- No tiene usuarios, pagos, comunidad ni nube en el MVP.
- No genera preguntas masivamente antes de validar las fuentes.

## 3. Decisiones cerradas

| Área | Decisión |
|---|---|
| Despliegue | local-first, un usuario, backend enlazado a `127.0.0.1` |
| Backend | Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic |
| Frontend | React + TypeScript + Vite, React Router, TanStack Query |
| Metadatos | SQLite con claves foráneas y migraciones |
| Búsqueda literal | SQLite FTS5 |
| Vectorial | Qdrant en modo local, índice reconstruible |
| Archivos | almacén por SHA-256, originales inmutables |
| Trabajos | cola persistida en SQLite y un worker local; sin Redis/Celery |
| PDF | PyMuPDF; OCR opcional con Tesseract para páginas sin texto útil |
| DOCX/HTML | `python-docx` y BeautifulSoup/lxml |
| Clasificación | reglas + similitud + proveedor LLM opcional, siempre auditable |
| RAG | filtros de metadatos + FTS5 + vectorial + reranking + citas |
| IA | adaptador OpenAI-compatible y adaptador Ollama; ninguna función básica depende de IA |
| Estudio | motor propio de intentos/errores; exportación Anki en el MVP |
| Obsidian | exportación Markdown, no dependencia interna |
| Telemetría | ninguna por defecto |

Las dependencias exactas se fijarán en el lockfile del primer slice. El agente no puede sustituir el
stack sin una ADR aprobada.

## 4. Orden de lectura obligatorio

1. Este documento.
2. [Producto y alcance](01_PRODUCT-SPEC.md).
3. [Arquitectura](02_ARCHITECTURE.md).
4. [Modelo de dominio y datos](03_DATA-MODEL.md).
5. [Ingestión y clasificación](04_INGESTION-AND-CLASSIFICATION.md).
6. [RAG y evaluación](05_RAG-EVIDENCE-AND-EVALUATION.md).
7. [Preguntas, exámenes y estudio](06_QUESTIONS-EXAMS-AND-STUDY.md).
8. [Interfaz](07_UI-UX.md).
9. [Contrato API](08_API-CONTRACT.md).
10. [Seguridad y derechos](09_SECURITY-PRIVACY-AND-RIGHTS.md).
11. [Plan de pruebas](10_TEST-PLAN.md).
12. [Slices de implementación](11_IMPLEMENTATION-SLICES.md).
13. [Instrucciones para DeepSeek](12_HANDOFF-DEEPSEEK.md).
14. [Decisiones y registro de incógnitas](13_DECISIONS-AND-OPEN-QUESTIONS.md).
15. [Contrato AGENTS del nuevo repositorio](14_NEW-REPO-AGENTS.md).
16. [Perfiles oficiales y manifiesto de fuentes](15_OFFICIAL-PROFILES-AND-SOURCE-MANIFEST.md).
17. [Trazabilidad y definición de terminado](16_TRACEABILITY-AND-DEFINITION-OF-DONE.md).

La investigación previa está en
[`docs/ideas/opposition-study-rag`](../ideas/opposition-study-rag/00_DECISION-2026-09.md). Si existe
una contradicción, este paquete tiene prioridad para la implementación; los hechos oficiales y reglas
de derechos de la investigación siguen siendo aplicables.

## 5. Definición breve de MVP

El MVP se considera terminado cuando una copia de muestra de material TAI puede importarse sin tocar
los originales, revisarse eficientemente, convertirse en biblioteca y preguntas, y utilizarse para
una sesión de estudio. Además debe importar el cuestionario y las dos versiones de plantilla de
Guardia Civil 2026 y demostrar la sustitución versionada.

RAG es parte del MVP, pero llega después de la biblioteca. Una respuesta válida debe abrir el
fragmento que la respalda o declarar que no hay evidencia suficiente.

## 6. Datos que debe aportar el propietario

Antes del slice de ingestión real, crear fuera de los originales una carpeta de muestra con:

- 10 documentos TAI identificables;
- 10 archivos o bloques de preguntas;
- 5 duplicados o revisiones;
- 5 imágenes/PDF escaneados;
- 5 elementos dudosos;
- una convocatoria y un examen oficial TAI;
- cuestionario GC 2026 y las dos plantillas publicadas.

La ausencia de esta muestra no bloquea el scaffold, modelo ni importador sintético. Sí bloquea afirmar
que la clasificación funciona con el archivo real.

## 7. Reglas de trabajo

- Implementar un slice cada vez.
- Ninguna función se considera hecha sin ejecutar sus pruebas y registrar la salida.
- No cambiar el alcance para «mejorar» el producto.
- No silenciar typecheck, lint, tests, migraciones o controles de seguridad.
- No mover ni borrar archivos del usuario, ni durante tests.
- No presentar contenido generado como oficial.
- Toda decisión no especificada se registra como bloqueo o propuesta de ADR; no se improvisa.
