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

**Tercera oposición (22 de septiembre de 2026):** decidida y entregada como S12.1 — Celador/a del
SACYL, perfil `celador-sacyl-2022`. No añade modelo, contrato ni interfaz: es un caso más de lo que
ya existía. La decisión está en [ADR-015](../decisions/ADR-015-tercera-oposicion-celador.md) y su
detalle, en `15_OFFICIAL-PROFILES-AND-SOURCE-MANIFEST` §3. Un cuarto perfil vuelve a exigir decisión.

## S12.1 — tercer perfil oficial: Celador/a del SACYL (Salamanca)

### Entrega

- Perfil `celador-sacyl-2022` con el programa del ANEXO II (16 temas, sin bloques) extraído del HTML
  del BOCYL y con dieciséis reglas, cada una con su cita literal.
- Nueve fuentes nuevas en el manifiesto: la orden, la resolución que fija la fecha del ejercicio, el
  cuestionario publicado, la plantilla de respuestas, el cuestionario del llamamiento aplazado y los
  dos avisos legales revisados.
- Extractor `celador_curriculum` en `build_profile_fixtures`, con el corte de anexo propio del BOCYL.

### Aceptación

- Las citas de las dieciséis reglas y de la parte se verifican contra el documento descargado; el
  manifiesto comprueba el `sha256` de las nueve fuentes.
- El cuestionario publicado confirma la estructura del fixture (77 preguntas, 7 de reserva).
- La fecha del ejercicio del fixture coincide con la que publica el BOCYL.
- Ninguna fuente de derechos dudosos se declara reutilizable: las que no publican condiciones quedan
  en `unknown`, con la nota que lo explica.
- TAI sigue siendo la oposición activa después de sembrar.

## S12.2 — segunda convocatoria de Celador: estabilización (Ley 20/2021) — **no empezado**

**Precondición, y no es técnica:** su plazo de solicitudes cerró el 27 de enero de 2023, así que este
programa solo sirve a quien se presentó a ese proceso. Se construye si el propietario dice que es su
caso (o si quiere el temario por otro motivo). Lo que hay hoy: sus catorce temas y sus reglas
verificadas y documentadas en `15_OFFICIAL-PROFILES-AND-SOURCE-MANIFEST` §4, sin sembrar.

### Entrega

- Convocatoria `celador-sacyl-estabilizacion-2022` dentro de la misma oposición `celador-sacyl`, con
  el programa del ANEXO V de la ORDEN SAN/1917/2022 (catorce temas en parte general y parte
  específica) extraído del PDF del BOCYL y con sus reglas citadas.
- Ejercicio declarado como lo publica la orden: 44 preguntas incluidas las de reserva, tres
  alternativas, error penalizado con 1/9, 60 minutos, 0–150 puntos.
- **Selector de convocatoria en la interfaz.** Hoy Programa, Estudio, Repaso y Banco resuelven la
  convocatoria con `active_convocation`, y solo puede haber una convocatoria activa por oposición: una
  segunda convocatoria sembrada sería invisible. O se añade el selector, o esto no se entrega.
- **Decidir el estado de una convocatoria publicada que no es la vigente.** `draft`, `active`,
  `superseded` y `archived` no la describen; usarla como `draft` sería mentir sobre un acto ya
  publicado. Es un cambio de modelo (enumerado, restricción de la base y contrato), con su migración.

### Aceptación

- El fixture dice, en su nota de fecha, que el ejercicio **no se ha convocado** y que el plazo de
  solicitudes cerró el 27 de enero de 2023: no se presenta como un examen disponible.
- Sus cifras de examen son distintas de las de la convocatoria ordinaria y las pruebas lo comprueban,
  para que nadie confunda un perfil con otro.
- La convocatoria ordinaria sigue siendo la vigente de la oposición.

## S12.3 — Anki y Markdown entran como material

### Entrega

- Extractor de barajas de Anki (`.apkg`, `.colpkg`): familia propia reconocida por contenido, lectura
  de la colección (SQLite, zstd desde Anki 2.1.50) y una tarjeta por tramo con los nombres de campo
  de la baraja. La media no se extrae y se avisa (`media_not_extracted`).
- El adorno de Markdown deja de leerse como contenido: encabezados, citas, viñetas y énfasis fuerte
  se quitan antes de leer enunciados, opciones y claves; un encabezado es estructura, no texto suelto.
- Señales nuevas del clasificador con su cita: `.apkg`/`.colpkg` → tarjetas (0,8), `preguntas tipo
  test` y `supuesto práctico` (0,7), `cuestionario` y `anotaciones` (0,5).

### Aceptación

- Una carpeta con una baraja y un cuestionario en Markdown entra entera: la baraja **no** se expande
  en miembros, y el cuestionario entra con sus opciones y su clave.
- Un contenedor sin colección, una colección vacía y una comprimida ilegible se declaran; nunca
  devuelven texto inventado.
- Una tarjeta **no** se convierte en pregunta: el modelo no tiene dónde guardar su respuesta
  (DEBT-023), y la baraja se clasifica como tarjetas.
- Todo dato leído tiene su tramo con etiqueta y sus desplazamientos dentro del texto guardado.

## S12.4 — Soltar carpetas enteras

### Entrega

- La bandeja acepta **carpetas**: soltarlas sobre la zona de arrastre (recorridas en el navegador con
  `webkitGetAsEntry`) o elegirlas con el selector de carpetas.
- Cada fichero viaja con su **ruta relativa** y esa ruta se conserva hasta el final: en la entrada del
  lote, en el nombre original (que es lo que ve el clasificador) y en lo que se enseña.
- La basura del sistema operativo no entra, y una carpeta de más de 2.000 ficheros se declara en
  lugar de subirse a medias.

### Aceptación

- Soltar una carpeta con una subcarpeta sube **todos** sus ficheros, no cero, y con su estructura.
- La descarga de un original aplana el nombre: en una cabecera `Content-Disposition` una barra no
  significa nada.
- Las entradas de un ZIP siguen mostrándose como `contenedor/miembro`, como antes.

## S12.5 — Importar las preguntas sin que nadie pulse nada

### Entrega

- Al aceptar una versión de documento, la aplicación mira qué es el material y, si es un examen
  oficial, un banco de preguntas o unos supuestos, **crea el conjunto e importa las preguntas con su
  cita**, sin que el usuario lo pida (ADR-017).
- La respuesta de la aceptación dice qué ha hecho: cuántas preguntas, a qué conjunto o el motivo de no
  importar ninguna («está clasificado como temario», «no está asignado a ninguna oposición», «no está
  clasificado»), y la ficha del documento lo cuenta.
- Un conjunto por **documento**, no por versión: una versión nueva añade lo que trae de nuevo. Un
  conjunto que se creó y quedó vacío se **archiva**.

### Aceptación

- Un banco de preguntas aceptado deja sus preguntas en el banco, con su sección y su fragmento.
- Un temario, unos apuntes o algo sin clasificar **no** crean ningún conjunto, y se dice por qué.
- Sin asignación aceptada al programa no se inventa la oposición: no hay conjunto.
- Aceptar la versión 2 del mismo documento añade solo las preguntas nuevas al conjunto que ya existía.
- Un material que decía traer preguntas y no trae ninguna no deja un conjunto vacío en la lista.

## S12.6 — Catalogar por bloque y tema, y enlazar la clave (en curso)

### Entrega (hecha)

- Al importar preguntas de un documento —sola, al aceptar una versión (S12.5), o a mano desde el
  banco—, cada pregunta **hereda el programa** del documento del que sale: si la versión está asignada
  al «Tema 3», sus preguntas son del tema 3. Es una derivación, no una adivinanza: sin asignación
  **aceptada** no se cataloga nada, y una pregunta que ya tiene tema no se toca (ADR-017).
- El informe lo cuenta: `mapped_to_topics` en el informe de importación y `questions_catalogued` en
  la respuesta de aceptar una versión; la ficha del documento lo dice.
- **DEBT-024, cerrada**: clasificar dejó de ser una petición síncrona con el corpus entero. Se encola
  (202 + trabajo), el trabajador lo ejecuta y la pasada informa de sus tramos —clasificando, guardando,
  aplicando, buscando duplicados— mientras la pantalla los sigue y enseña su avance.

### Aceptación (de lo hecho)

- Las preguntas de un documento asignado quedan con su nodo, y el diagnóstico por temas las ve.
- Una asignación **provisional** no cataloga ni crea conjunto: es una sugerencia, no una decisión.
- Las preguntas que ya traían tema (por ejemplo, de una columna del material) se quedan como estaban.
- Clasificar responde en menos de un segundo y su trabajo dice en qué va, con el corpus del propietario
  (186 sujetos: 0,097 s de respuesta, 48,2 s de trabajo).

### Pendiente

- **enlazar la plantilla de respuestas con su examen**: decidir cómo se reconoce que una plantilla es
  de un examen concreto (por el modelo, por el número de preguntas, por la fecha) y qué se hace
  cuando no cuadra;
- **una pantalla que diga «esto ya está listo para estudiar»** y qué falta, si falta algo, por
  oposición: material por papel, preguntas por tema, claves activas y lo que sigue esperando una
  decisión de una persona.
