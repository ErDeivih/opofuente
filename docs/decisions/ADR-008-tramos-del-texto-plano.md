# ADR-008 — Tramos del texto plano: un bloque por línea en blanco, sin adivinar jerarquía

- **Estado:** aceptada (decisión del codificador al abrir S06, para cerrar DEBT-009)
- **Fecha:** 17 de septiembre de 2026
- **Ámbito:** extracción (S03) y su efecto en las citas y el banco de preguntas (S05/S06)
- **Asunto:** qué secciones produce un texto plano (`.txt` y texto pegado) para que se pueda citar

## Contexto

`PlainTextExtractor` solo calculaba secciones para Markdown: un `.txt` devolvía `sections=()`, y el
texto **pegado** entra por ese mismo camino. Sin secciones, al promocionar no se crean
`document_sections` y, en consecuencia:

| Qué falta | Dónde se nota |
|---|---|
| Cero `evidence_spans` | la ficha se queda sin citas y «copiar cita» no tiene qué citar |
| `diff_versions` sin nada que comparar | `GET /documents/{id}/diff` responde vacío aunque el texto cambie |
| Estructura vacía | la pestaña «Estructura» no lista nada |

El hueco no es teórico: es el material más probable de quien estudia —sus propios apuntes, pegados o
en `.txt`—, y S06 necesita **citar documento y sección** para que una pregunta sea oficial. Estaba
registrado como DEBT-009 y bloqueaba el banco de preguntas. (El `.md`, el PDF, el DOCX y el HTML sí
producían secciones; el problema era solo el texto sin sintaxis.)

## Opciones consideradas

1. **Dejarlo como estaba** y que S06 exigiera PDF/DOCX/Markdown para citar. Descartada: deja fuera el
   material que el usuario escribe, y el banco de preguntas nace cojo justo donde más se usa.
2. **Reconocer encabezados por heurística** (`Tema 1`, `1.1`, `ARTÍCULO 5`, líneas en mayúsculas) y
   tratarlos como `title`/`heading`. Descartada: es adivinar jerarquía. Una línea «Tema 1. Plazos» y
   otra «El plazo es de diez días» se parecen demasiado como para que un patrón decida cuál manda, y
   el proyecto prohíbe afirmar estructura que nadie ha comprobado (`document_section_type` ya lo dice
   para el vocabulario del documento).
3. **Una sola sección con todo el texto.** Descartada como única opción: permite citar «el documento
   entero», que no dice nada útil al lado de una pregunta, y hace que el diff de dos versiones sea
   «todo cambió».
4. **Un tramo por bloque separado por una línea en blanco** (elegida).

## Decisión

**Un texto plano produce un tramo (`paragraph`) por cada bloque separado por una línea en blanco, con
sus offsets exactos sobre el texto normalizado que se guarda.** Reglas concretas:

- **A nada se le llama «título»**: `title` queda vacío. En el vocabulario del documento esos tramos se
  traducen a `technical`, que significa exactamente «texto del que no sabemos más».
- Un fichero **sin** líneas en blanco produce **un** tramo con todo el texto; uno vacío o solo con
  espacios no produce ninguno y la representación queda `empty`, como antes.
- Los tramos se acotan a **500** (`MAX_BLOCK_SECTIONS`). A partir de ahí se deja de partir; el texto
  completo sigue en la representación, sin recortar. Un fichero con miles de bloques no puede llenar
  la base de secciones.
- Se calculan sobre el texto **normalizado** y se ajustan con `clamp_sections`, igual que en el resto
  de extractores: un offset tiene que apuntar al texto que se guarda, o la cita diría otra cosa.
- Markdown no cambia: sus encabezados `#` siguen siendo `title`/`heading` por la extensión (y sin el
  nombre original no se adivinan, que es lo que ya hacía).

## Datos que la sostienen

- Extracción real de un `.txt` de tres bloques:
  `Tema 1. La Constitucion espanola.\nEl plazo es de diez dias habiles.\n\nTema 2. …\n\n\nSuelto al final.\n`
  → tres tramos `paragraph`, tres posiciones, y los recortes por offsets devuelven exactamente cada
  bloque (`tests/unit/test_extractors.py::test_un_texto_plano_deja_un_tramo_por_bloque_con_sus_offsets`).
- El diff de dos versiones de texto **pegado** ya informa de lo que cambió: un bloque cambiado y otro
  añadido, en `tests/integration/test_library_api.py::test_el_diff_compara_dos_versiones_del_mismo_documento`.
- Ni un texto vacío ni un fichero de 1.200 bloques rompen nada: el primero no inventa tramos y el
  segundo se acota, con el texto completo intacto.

## Consecuencias

- Unos apuntes pegados ya se pueden citar por bloque, y su ficha muestra estructura y evidencias.
- **No** hay jerarquía: la biblioteca no dirá «Tema 3» sino «sección 3». Es una limitación honesta: para
  tener títulos, el material tiene que venir con sintaxis (Markdown) o con estructura (PDF/DOCX/HTML).
- El diff de dos apuntes empareja por posición (`sección N`), así que insertar un bloque en medio hace
  que los siguientes cuenten como cambiados. Está documentado en `docs/slices/S05.md` y es el precio de
  no inventar títulos.
- Los tramos pasan a existir para material ya ingerido **a partir de ahora**: lo extraído antes se
  queda sin secciones hasta que se vuelva a extraer (no hay reproceso automático, y forzarlo no está
  en este slice).

## Reversión

Volver al comportamiento anterior es una línea: dejar `_block_sections` fuera del extractor de texto
plano y devolver `sections=()`. Lo que **no** se revierte solo son las secciones ya guardadas: las
promociones hechas con esta decisión conservan sus tramos, sus evidencias y sus citas.
