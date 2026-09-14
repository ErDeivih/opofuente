# OpoFuente — especificación de producto

## 1. Visión

Permitir que una persona prepare una oposición desde su propio material y fuentes oficiales sin perder
tiempo ordenando archivos ni confiar ciegamente en una IA. OpoFuente convierte documentos y preguntas
en un mapa verificable de qué estudiar, practicar y repasar.

## 2. Usuario inicial

David, usuario único local, con conocimientos informáticos y una colección TAI desorganizada. Puede
revisar propuestas técnicas, pero la aplicación debe ser utilizable sin editar bases de datos, YAML o
prompts. Guardia Civil se configura como segunda oposición, no necesariamente para el mismo calendario
de estudio.

## 3. Trabajos del usuario

### J1. Ordenar sin trabajo previo

«Quiero señalar mi carpeta y que la aplicación me diga qué contiene, qué está repetido y dónde encaja,
sin modificar mis originales».

### J2. Saber si el material basta

«Quiero ver los temas y epígrafes oficiales, qué fuente cubre cada uno, qué preguntas tengo y qué me
falta».

### J3. Encontrar una respuesta fiable

«Quiero preguntar algo y abrir exactamente la ley, página o sección que respalda la respuesta».

### J4. Convertir preguntas dispersas en práctica

«Quiero pegar o importar preguntas, separar opciones/soluciones y practicar por tema o como examen».

### J5. Aprender de los fallos

«Quiero saber qué concepto confundí y que vuelva a aparecer cuando convenga».

### J6. Evitar estudiar contenido obsoleto

«Quiero saber si una fuente cambió y qué preguntas, notas o tarjetas debo revisar».

## 4. Navegación del MVP

1. **Inicio** — tarea recomendada, oposición activa, pendientes y cambios.
2. **Bandeja** — lotes, archivos, propuestas, problemas y revisión en lote.
3. **Programa** — árbol oficial con cobertura, preguntas y dominio.
4. **Biblioteca** — documentos lógicos, versiones, colecciones y lector.
5. **Preguntas** — banco filtrable, conflictos, edición y procedencia.
6. **Estudiar** — práctica, examen, corrección y repaso.
7. **Errores** — conceptos débiles y cola de recuperación.
8. **Cambios** — versiones sustituidas y derivados afectados.
9. **Ajustes** — almacenamiento, OCR, modelos, privacidad y exportación.

## 5. Historias prioritarias

### P0 — sin ellas no hay producto

- Como usuario, puedo crear/activar los perfiles TAI y Guardia Civil.
- Puedo inventariar una carpeta en modo lectura antes de copiar nada.
- Puedo importar un lote y obtener un informe exhaustivo.
- El sistema detecta duplicados exactos por contenido.
- Puedo revisar, corregir y deshacer clasificaciones.
- Puedo navegar el programa y ver cobertura.
- Puedo importar preguntas con opciones y respuestas separadas.
- Puedo realizar una sesión y conservar el intento.
- Puedo abrir el original y su texto extraído.
- Una plantilla nueva puede sustituir a otra sin borrar historial.

### P1 — MVP completo

- Detectar casi duplicados y revisiones.
- Clasificación temática asistida y revisión en lote.
- Búsqueda FTS y semántica.
- Preguntas al corpus con citas y rechazo.
- Importación de examen oficial TAI y GC.
- Cuaderno de errores y cola de repaso.
- Exportación Markdown y Anki CSV.
- Diff de versiones e invalidación de derivados.

### P2 — posterior a validación

- Generación verificada de preguntas.
- Monitor periódico de BOE/INAP/Guardia Civil.
- OCR avanzado de tablas y diseños complejos.
- Modelos locales optimizados.
- Estadística de dificultad con suficientes intentos.

## 6. Requisitos funcionales

### RF-01 Perfiles de oposición

Cada oposición contiene convocatorias versionadas, programa, partes del examen, reglas de puntuación,
fuentes oficiales y estado de activación. Una futura convocatoria crea una versión nueva.

### RF-02 Ingestión reversible

Todo lote tiene inventario previo, progreso, cancelación segura, reanudación, incidencias e informe.
El sistema copia; nunca reorganiza el origen.

### RF-03 Clasificación auditable

Cada propuesta conserva etiqueta, confianza, alternativas, evidencia, clasificador y decisión humana.
El usuario puede aceptar por lote y revertir.

### RF-04 Biblioteca versionada

El mismo documento lógico admite versiones. Los fragmentos y derivados conocen la versión exacta. Un
documento puede mapearse a múltiples epígrafes.

### RF-05 Preguntas estructuradas

Enunciado, opciones, clave, explicación, origen y evidencias no se almacenan en un único campo opaco.
Se soportan anulaciones, reservas, modelos y claves sustituidas.

### RF-06 Estudio fiel al perfil

La sesión aplica número de preguntas, tiempo, penalización y umbrales de la convocatoria seleccionada.
Los modos de práctica pueden relajarlos, pero deben etiquetarse.

### RF-07 Respuesta verificable

El usuario elige oposición/convocatoria y, opcionalmente, fuentes. La respuesta muestra afirmaciones y
citas. Si no basta la evidencia, no completa por conocimiento general sin avisar.

### RF-08 Errores y repaso

Un fallo se relaciona con conceptos/epígrafes y causa elegida. La cola prioriza errores recurrentes y
recuerdo activo. El usuario puede posponer o archivar.

### RF-09 Cambios

Una nueva versión genera diff, identifica fragmentos afectados y marca derivados `needs_review`. Nada
se corrige silenciosamente.

### RF-10 Portabilidad

El usuario puede exportar metadatos, Markdown, preguntas e intentos. El backup incluye SQLite,
artefactos y configuración, con restauración probada.

## 7. Requisitos no funcionales

- Funciona en Windows 11 sin Docker obligatorio.
- Arranca con un comando de desarrollo y un comando de producción local.
- Biblioteca de 10.000 archivos y 100.000 preguntas sin bloquear la UI; objetivo, no promesa inicial.
- Operaciones largas se ejecutan como trabajos persistidos.
- La UI sigue respondiendo y muestra progreso/cancelación.
- Todas las fechas internas en UTC; presentación en zona local.
- Identificadores UUIDv7 o UUID estándar generado por servidor; usar una sola estrategia.
- UTF-8 y búsqueda correcta en español con tildes; conservar original y forma normalizada.
- Accesibilidad básica WCAG 2.2 AA: teclado, foco, etiquetas, contraste y no depender solo del color.
- Sin llamadas externas ocultas.

## 8. Métricas del producto

- tiempo de revisar 100 elementos;
- porcentaje clasificado correctamente por etiqueta crítica;
- duplicados exactos encontrados;
- porcentaje del programa con fuente aceptada;
- preguntas con evidencia suficiente;
- respuestas RAG correctas/fieles/citadas;
- minutos de estudio frente a minutos de mantenimiento;
- fallos repetidos por concepto;
- sesiones semanales y tiempo ahorrado.

## 9. Criterios de abandono

- La revisión de la bandeja consume tanto como ordenar manualmente.
- El sistema no puede separar con fiabilidad preguntas, claves y explicaciones.
- Las citas no superan la referencia de NotebookLM en el conjunto patrón.
- Mantener versiones consume más tiempo que ahorra.
- Después de cuatro semanas el usuario estudia fuera de la app.

## 10. Fuera de alcance

SaaS, cuentas, pagos, comunidad, colaboración, contenido compartido, app móvil nativa, descarga masiva
de academias, promesas de aprobado, predicción de examen, corrección oral y preparación psicofísica.

