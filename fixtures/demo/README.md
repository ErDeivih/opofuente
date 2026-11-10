# Contenido de la demo estática (`fixtures/demo/temas/`)

Cada fichero es **un tema** del temario común, con contenido propio y preguntas. Lo consume
`apps/api/opofuente/tools/build_static_demo.py` y lo publica la demo de GitHub Pages. No se copia
texto de academias, blogs ni apuntes privados: se escribe contenido propio a partir de fuentes
oficiales (BOE, CCN-CERT, IETF, NIST, documentación pública) y se cita la fuente.

## Esquema

```json
{
  "node_path": "I.5",
  "title": "El procedimiento administrativo",
  "source": {
    "label": "Ley 39/2015, de 1 de octubre, del Procedimiento Administrativo Común",
    "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-10565"
  },
  "sections": [
    { "heading": "Ámbito y principios", "body": "Texto con **negritas** y párrafos separados por una línea en blanco." },
    { "heading": "Fases del procedimiento", "table": { "columns": ["Fase", "Qué ocurre"], "rows": [["Iniciación", "..."], ["Instrucción", "..."]] } },
    { "heading": "Ejemplo", "body": "Caso práctico breve y resuelto." }
  ],
  "questions": [
    {
      "stem": "¿Qué ley regula el procedimiento administrativo común?",
      "options": ["La Ley 39/2015", "La Ley 40/2015", "La Ley 7/1985", "La Ley 9/2017"],
      "correct": "a",
      "explanation": "La Ley 39/2015 regula el procedimiento administrativo común de las administraciones públicas."
    }
  ]
}
```

## Reglas de contenido

- **4-6 secciones** por tema; al menos **una tabla** y **un ejemplo** resuelto.
- **10 preguntas** por tema, 4 opciones cada una, una sola correcta, con explicación razonada. Varía
  la letra correcta.
- Español de España, sin jerga de desarrollo, sin afirmaciones sin fuente.
- Si no estás seguro del número exacto de un artículo, **no lo inventes**: describe la materia y cita
  la ley, no el artículo. Prefiere precisión a aparentar detalle.
- Fuente: una URL oficial estable (`boe.es`, `ccn-cert.cni.es`, `ietf.org`, `nist.gov`…).
- No incluyas Guardia Civil, material privado, rutas del disco ni datos de academias.

## Estado de un tema en la demo

- **completo**: tiene al menos 3 secciones y 10 preguntas.
- **con preguntas**: tiene 10 preguntas pero no secciones suficientes (no se usa de momento).
- **en preparación**: no hay fichero; la demo lo dice en el temario y en su ficha en lugar de un
  párrafo vacío.
