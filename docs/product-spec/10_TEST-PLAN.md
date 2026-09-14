# OpoFuente — plan de pruebas y aceptación

## 1. Pirámide

- Unitarias: dominio, puntuación, estados, rutas, normalización, deduplicación.
- Integración: SQLite/FTS, almacén, parsers, Qdrant, worker, migraciones.
- Contrato: OpenAPI/backend/frontend.
- Componentes: UI con estados y accesibilidad.
- E2E: flujos críticos en copia temporal.
- Evaluación IA: datasets versionados, separada de tests deterministas.

No llamar proveedores pagados en la suite normal. Tests externos se etiquetan y requieren credenciales
explícitas.

## 2. Fixtures

`fixtures/synthetic` contiene documentos creados para pruebas, no materiales comerciales. Incluir:

- PDF nativo multipágina;
- PDF escaneado pequeño;
- DOCX con títulos/tabla;
- CSV de preguntas válido y filas defectuosas;
- HTML con scripts/prompt injection;
- ZIP seguro y ZIP con traversal/bomb simulada;
- dos archivos idénticos con nombres distintos;
- dos revisiones casi iguales;
- cuestionarios sintéticos modelo A/B;
- claves v1/v2 con una respuesta corregida.

Fuentes oficiales usadas en tests deben tener URL, fecha, derechos y copia permitida; si no, tests de
descarga usan metadatos/mock y el usuario importa manualmente.

## 3. Unitarias esenciales

### Seguridad/archivos

- ruta fuera de raíz, junction/symlink, `..`, nombre reservado Windows;
- hash por streaming y fallo parcial;
- ZIP traversal, tamaño, ratio y profundidad;
- SSRF IPv4/IPv6/redirección/rebinding defensivo;
- sanitización de logs y errores.

### Dominio

- transiciones válidas/inválidas de documento, propuesta, trabajo y clave;
- autoridad no promovida automáticamente;
- artefacto compartido no eliminado;
- ciclos `supersedes` rechazados;
- claim respaldado solo por evidencia elegible.

### Puntuación

- TAI: puntuación directa con aciertos/fallos/blancos y reservas/anuladas; ausencia explícita de
  calificación oficial sin baremo publicado;
- GC: fórmula `A-E/(N-1)`, Y/T, límites y redondeo documentado;
- GC ortografía/gramática: 5 vs 6 errores;
- umbrales de conocimientos/inglés/aptitudes;
- clave v2 genera evaluación nueva.

### Preguntas

- parseo de opciones, numeración y reservas;
- opciones reordenadas modelo A/B;
- negaciones no eliminadas en normalización;
- duplicados no fusionan claves conflictivas;
- solución nunca aparece en payload activo.

## 4. Integración

- migrar DB vacía a última y rollback donde soporte;
- `foreign_keys=ON` y restricciones;
- worker reanuda lease expirado;
- idempotencia tras caída entre copia y commit;
- reconstrucción FTS/Qdrant;
- filtro por convocatoria/vigencia/autoridad;
- cancelación entre páginas;
- importación completa con informe cuadrado;
- backup, borrado del entorno temporal, restauración y hashes.

Todas usan directorio temporal resuelto y verificado. Nunca apuntar tests a la carpeta real.

## 5. E2E críticos

### E2E-01 Primera ejecución

Arranque, perfiles sembrados, capacidades, oposición activa y estado vacío útil.

### E2E-02 Inventario/importación

Seleccionar fixture, ver preview, importar, seguir job, revisar informe; hashes del origen iguales.

### E2E-03 Revisión en lote

Aceptar grupo, excluir fila, corregir tema, deshacer y comprobar cobertura.

### E2E-04 Documento compartido

Asignar una fuente a TAI y GC; comprobar un único artefacto y dos mappings.

### E2E-05 Preguntas

Importar CSV parcialmente inválido, corregir mapeo, practicar aceptadas y ver rechazadas.

### E2E-06 Examen TAI

Crear sesión, responder/fallar/dejar blanco, finalizar y verificar puntuación/partes.

### E2E-07 Clave GC corregida

Importar set y v1, completar; importar v2, confirmar sustitución, ver resultado anterior/nuevo.

### E2E-08 RAG

Pregunta respaldada muestra citas abribles; pregunta negativa devuelve insuficiente; obsoleta no entra.

### E2E-09 Cambio

Versionar artículo, confirmar diff y comprobar derivados `needs_review`.

### E2E-10 Reinicio

Cerrar durante job, reiniciar y reanudar sin duplicar.

## 6. UI

- Vitest/Testing Library para estados y interacciones.
- axe para violaciones automatizables.
- Playwright Chromium como navegador principal.
- snapshots visuales solo en componentes estables; preferir aserciones semánticas.
- anchos 1440, 1024 y 390.
- teclado en bandeja, pregunta, diálogo y lector de evidencia.

## 7. Evaluación de clasificación

Manifiesto humano con muestra real copiada. Por eje:

- precisión/recall/F1;
- matriz de confusión;
- calibración de confianza;
- precisión de auto-aplicadas;
- porcentaje sin clasificar;
- minutos por 100 elementos;
- correcciones por lote.

Puerta inicial: cero promociones críticas erróneas automáticas y duplicados exactos 100 %. Los umbrales
temáticos se establecen tras baseline y se registran en ADR.

## 8. Evaluación RAG

Según [05_RAG-EVIDENCE-AND-EVALUATION.md](05_RAG-EVIDENCE-AND-EVALUATION.md). Dataset separado de
prompts de desarrollo. Guardar versión de corpus/modelo/configuración. Una mejora no se acepta si sube
fluidez pero baja citas, rechazo o fidelidad.

## 9. Rendimiento

Escenarios de referencia:

- inventario 10.000 archivos sin copiar;
- importar 1 GB mixto con progreso;
- tabla 100.000 preguntas paginada/virtualizada;
- FTS sobre 100.000 fragmentos;
- recuperación híbrida sobre corpus objetivo;
- reinicio con 1.000 jobs históricos.

Definir equipo de referencia y baseline en slice de rendimiento; no inventar SLA antes de medir.
La UI no debe congelarse durante escenarios.

## 10. Puertas por slice

Todo slice ejecuta, en este orden:

1. formato/lint;
2. typecheck;
3. unitarias afectadas;
4. integración afectada;
5. build backend/frontend;
6. E2E requerido;
7. migración desde cero;
8. revisión de diff y explicación del slice.

Un fallo devuelve código no cero y bloquea. Prohibido ignores, skips, relajar configuración o adaptar
un test para ocultar un defecto.

## 11. Evidencia de entrega

Cada slice produce `docs/slices/Sxx.md`:

- qué se construyó;
- flujo de información;
- decisiones/patrones;
- migraciones;
- comandos ejecutados y resultado;
- pruebas manuales;
- limitaciones;
- crítica senior;
- siguiente slice desbloqueado.
