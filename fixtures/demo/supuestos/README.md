# Supuestos oficiales — esquema

Cada fichero `<slug>.json` es un supuesto completo de 20 preguntas para la pestaña «Supuestos».

```json
{
  "slug": "tai-2024-a-s1",
  "year": 2024,
  "conv": "TAI-L 2024 · modelo A",
  "block": "IV",
  "title": "Becas para personas opositoras",
  "difficulty": "media",
  "official": true,
  "estimatedMinutes": 30,
  "statement": "Enunciado propio y completo del caso...",
  "steps": ["Paso 1...", "Paso 2..."],
  "topics": ["IV.31", "IV.27"],
  "source": {
    "label": "INAP — Cuestionario TAI-L 2024 modelo A",
    "url": "https://...",
    "pages": "pp. 8-10"
  },
  "questions": [
    {
      "stem": "Pregunta...",
      "options": ["a) ...", "b) ...", "c) ...", "d) ..."],
      "correct": "c",
      "justification": "Por qué es correcta y por qué fallan las otras."
    }
  ]
}
```

Reglas:
- **20 preguntas** exactas (si la plantilla oficial anula una, `correct: "ANULADA"` y se explica).
- Reestructura el enunciado y las preguntas con palabras propias; no copies párrafos literales largos. Conserva los datos técnicos y las opciones.
- `correct` = letra de la **plantilla oficial**; `justification` breve y razonada.
- `topics` = códigos del temario común (I.1…V.40) que toca.
- `source` con URL de la sede del INAP y páginas.
- `difficulty`: baja/media/alta.