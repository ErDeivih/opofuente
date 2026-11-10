# Guía de estudio de la demo

**Página:** <https://erdeivih.github.io/opofuente-demo/#/guia> · **Visible en la pestaña «Guía».**

## Qué hace

1. **Orden recomendado de bloques.** Propone estudiar I → II → III → IV → V: primero la base
   normativa y técnica, después sistemas/redes, datos y seguridad. Para cada bloque muestra su
   cobertura real (`12/12`, `5/5`, `9/9`, `7/7`, `7/7`) y el porcentaje (100 %).
2. **Detección de temas flojos.** Lee el progreso guardado en `localStorage` (solo en el navegador),
   calcula el porcentaje de la última práctica de cada tema y lista los que están por debajo del
   **70 %**. Cada uno enlaza a «Repasar tema» y «Repetir práctica».
3. **Siguiente paso.** Si no hay prácticas hechas, invita a empezar; si no hay temas flojos, propone
   seguir con el temario. Siempre ofrece ir al temario o a todas las prácticas.

## Reglas

- No hay servidor ni cuenta: el cálculo se hace en el navegador con `loadProgress()`.
- Solo cuentan las prácticas hechas; un tema sin práctica no se marca como flojo, se marca como
  pendiente en el mapa.
- El umbral es **70 %** de la última práctica, no del mejor resultado histórico: sirve para detectar
  lo que conviene repasar ahora.
- No se guardan datos personales; el progreso se borra con el botón de la pestaña Prácticas.

## Verificación

La comprobación de Playwright siembra un resultado del 40 % y confirma que la guía muestra el tema y
los enlaces de repaso; también comprueba que la página recomienda el orden de bloques. **46/46**
comprobaciones en la URL pública, a 390 y 1280 px.
