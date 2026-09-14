# OpoFuente — trazabilidad y definición de terminado

## 1. Matriz de requisitos

| Requisito | Slice principal | Evidencia mínima |
|---|---|---|
| RF-01 Perfiles | S01/S08 | árboles 33/25, fixtures y fuentes verificadas |
| RF-02 Ingestión reversible | S02/S03 | E2E-02 y hashes origen antes/después |
| RF-03 Clasificación auditable | S04 | propuestas, bulk, undo y métricas de muestra |
| RF-04 Biblioteca versionada | S05/S11 | fuente compartida, versiones y diff |
| RF-05 Preguntas estructuradas | S06/S08 | sets, opciones, claves v1/v2 y conflictos |
| RF-06 Estudio fiel | S07/S08 | casos matemáticos y E2E TAI/GC |
| RF-07 Respuesta verificable | S09 | dataset RAG, citas abribles y rechazo |
| RF-08 Errores/repaso | S10 | historial y cola determinista |
| RF-09 Cambios | S11 | invalidación selectiva reproducible |
| RF-10 Portabilidad | S10/S12 | exportaciones y restauración verificada |

## 2. Flujos que debe poder demostrar el MVP

### Demo A — del caos al programa TAI

1. seleccionar copia de carpeta;
2. inventariar sin cambiarla;
3. importar y ver progreso;
4. detectar duplicados;
5. revisar tipos/temas en lote;
6. abrir Programa y ver fuentes/preguntas;
7. practicar preguntas importadas;
8. revisar un error y programarlo.

### Demo B — evidencia

1. abrir tema TAI;
2. preguntar algo respaldado;
3. ver respuesta por claims;
4. abrir página/artículo exacto;
5. preguntar algo fuera del corpus;
6. recibir `insufficient`, no invención.

### Demo C — Guardia Civil versionada

1. abrir los 25 temas;
2. importar cuestionario/modelos;
3. importar plantilla v1;
4. realizar preguntas y obtener resultado;
5. importar plantilla v2 correctora;
6. confirmar sustitución;
7. ver puntuación anterior/nueva y causa.

### Demo D — cambio normativo

1. tener resumen/pregunta dependiente de versión 1;
2. importar versión 2 con sección modificada;
3. confirmar diff;
4. observar solo derivados afectados en `needs_review`;
5. la versión 1 sigue accesible históricamente.

### Demo E — recuperación

1. crear backup;
2. validarlo;
3. restaurar en directorio temporal vacío;
4. comparar hashes, perfiles, preguntas, sesión y notas.

## 3. Definition of Done del MVP

### Producto

- Los cinco flujos anteriores se completan desde UI sin SQL/terminal.
- El usuario puede estudiar TAI con una muestra real durante cuatro semanas.
- No hay funcionalidad P0/P1 representada por un botón falso.
- Estados degradados explican OCR/LLM/vector deshabilitado.

### Datos

- Migraciones desde cero y actualización desde cada release interna.
- Invariantes del modelo probadas.
- Originales inmutables y referencias íntegras.
- Informe de lote cuadra.
- Backup/restore probado.

### Calidad

- Puertas completas verdes.
- E2E críticos verdes.
- Dataset de clasificación real documentado sin incluir datos en git.
- Dataset RAG cumple puertas.
- Puntuaciones contrastadas con cálculos manuales y fuentes.
- Sin vulnerabilidades altas conocidas sin decisión explícita.

### Seguridad

- Loopback, CORS/Origin y CSP.
- Tests ZIP/path/SSRF/prompt injection.
- Solución no fugada.
- Logs/diagnóstico sanitizados.
- Secretos y `data` fuera de git.
- Ningún original modificado en pruebas reales.

### Documentación

- README de instalación/operación Windows.
- Arquitectura y ADR actuales.
- OpenAPI y tipos sincronizados.
- Explicación de todos los slices.
- Limitaciones y capacidades reales visibles.

## 4. No cuenta como terminado

- Código escrito pero no ejecutado.
- Test unitario con integración simulada presentado como integración.
- Pantalla conectada a datos hardcoded.
- Clasificación «oficial» sin procedencia.
- RAG con documento relacionado pero claim sin respaldo.
- Puntuación TAI 0–50 inventada sin criterio de transformación publicado.
- OCR marcado como correcto sin motor/revisión.
- Backup creado sin prueba de restauración.
- Importación probada contra originales.
- Función escondida tras TODO sin estado degradado explícito.

## 5. Handoff final

El agente entrega:

- ruta y commit del repositorio;
- slices completados y pendientes;
- comandos exactos de instalación/arranque/pruebas;
- resultados de puertas;
- ubicación de datos y backup;
- capacidades configuradas;
- riesgos/limitaciones;
- guía para importar la muestra TAI;
- decisión de si puede comenzar la prueba de cuatro semanas.

