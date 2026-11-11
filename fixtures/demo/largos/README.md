# Temas largos — encargo de redacción

Cada fichero `<tema>.json` es un **fragmento** para ampliar la ficha del tema en la demo. El Lead lo
integrará en `fixtures/demo/temas/<tema>.json` como `longSections`. No toques los JSON del temario.

## Esquema

```json
{
  "tema": "I.1",
  "title": "La Constitución Española de 1978",
  "sections": [
    {"heading": "1. Introducción y contexto", "body": "Texto de 150-300 palabras..."},
    {"heading": "2. ...", "body": "..."},
    {"heading": "Tabla ...", "table": {"columns": ["...","..."], "rows": [["...","..."]]}}
  ],
  "testCases": [
    {"question": "...", "options": ["a) ...","b) ...","c) ...","d) ..."], "answer": "a", "explanation": "..."}
  ],
  "sources": [
    {"file": "fichero exacto", "page": "p. 12 o apartado", "use": "qué dato se ha usado"}
  ]
}
```

## Reglas

- **1.500-3.000 palabras** de redacción propia en `sections` (sin contar tablas/test). Nada de copiar
  párrafos literales: sintetiza, explica y ordena.
- **8-12 apartados** numerados: introducción/contexto, desarrollo completo, tablas comparativas,
  ejemplos prácticos, casos tipo test, resumen "lo que hay que memorizar", fuentes citadas.
- **10-15 `testCases`** con 4 opciones, respuesta razonada y letra correcta variada.
- Cita **fichero + página o apartado** en `sources` y al final de las secciones que lo usen. Para DOCX
  sin paginación fija, cita «DOCX, apartado X»; para PDF usa `PÁGINA N` del texto extraído.
- Español de España, sin inventar normas ni cifras que no estén en las fuentes. Si un dato no está,
  no lo pongas.
- Usa solo las fuentes indicadas en la tarea y `data/fuentes/<tema>.txt`.