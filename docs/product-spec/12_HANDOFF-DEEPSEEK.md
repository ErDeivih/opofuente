# Handoff para el agente DeepSeek

## Objetivo

Crear desde cero **OpoFuente** en `F:\EspacioCodigo\opofuente`, una aplicación local para organizar y
estudiar material de TAI y Guardia Civil. No escribir código dentro de `proptech-access-control`:
contiene investigación y especificaciones históricas de otros productos.

## Autoridad documental

Lee completamente, en orden, todos los documentos de `docs/opofuente` del repositorio actual. Copia el
paquete al nuevo repositorio en `docs/product-spec/`. Si contradice investigación anterior, prevalece
este paquete. Si contradice una fuente oficial posterior, bloquea y documenta; no inventes.

## Forma de trabajo

1. Empieza por S00 de `11_IMPLEMENTATION-SLICES.md`.
2. No implementes dos slices a la vez.
3. Antes de cada slice enumera objetivo, dependencias y ficheros previstos.
4. Mantén cambios pequeños y ejecutables.
5. Ejecuta puertas y registra salida real.
6. Entrega `docs/slices/Sxx.md`.
7. Detente al final de cada slice para revisión, salvo autorización expresa.

## Decisiones que no puedes cambiar

- Python 3.12/FastAPI/Pydantic/SQLAlchemy/Alembic.
- React/TypeScript/Vite/TanStack Query.
- SQLite + FTS5 y Qdrant local reconstruible.
- originales SHA-256 inmutables.
- worker persistido local, no Redis/Celery.
- local-first y loopback.
- pregunta/clave/explicación separadas.
- clasificación crítica confirmada.
- RAG con claim/cita/rechazo.
- TAI primero, Guardia Civil segundo.
- sin SaaS, login, pagos, comunidad ni tercera oposición.

Una dependencia auxiliar requiere propuesta previa con justificación, licencia, mantenimiento y
alternativa. Registrar ADR y esperar aceptación si afecta arquitectura.

## Prohibido

- Mover, renombrar o borrar originales.
- Probar contra la carpeta real; usar copia/temporales.
- Simular OCR, descarga, clasificación, verificación o conexión.
- Marcar oficial por texto/nombre solamente.
- Presentar preguntas generadas como oficiales.
- Guardar claves en frontend/logs/repo.
- Escuchar en `0.0.0.0` por defecto.
- Silenciar lint/typecheck/tests o relajar puertas.
- Introducir material privado en fixtures/git.
- Añadir framework de agentes, vector DB remoto o microservicios.

## Bloqueos correctos

Bloquea si necesitas tocar originales, falta una fuente real necesaria, los derechos son dudosos, la
seguridad de URL/ZIP no es suficiente, una fórmula oficial es ambigua o falta una decisión que cambia
modelo/privacidad. Expón evidencia, opciones y recomendación. No uses mocks para afirmar integración
real.

## Datos reales

S00–S03 usan fixtures sintéticos. Antes de S04 solicita una **copia de muestra** y su ubicación.
Ejecuta inventario, presenta plan y solo entonces importa la copia.

## Definition of Done

- objetivo observable;
- migraciones desde cero;
- lint/typecheck/tests/build verdes;
- negativos de seguridad cuando aplican;
- API/UI coherentes;
- sin secretos ni archivos fuera de alcance;
- explicación del slice;
- limitaciones honestas y diff revisado.

## Primer mensaje recomendado

Confirma que has leído el paquete, el directorio nuevo y el alcance de S00. Si ya existe, inspecciónalo
sin borrar ni sobrescribir y reporta conflictos.

