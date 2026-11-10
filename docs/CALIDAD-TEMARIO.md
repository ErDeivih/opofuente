# Calidad del temario — revisión y refuerzo

**Fecha:** 10/11/2026 · **Cobertura:** 40/40 temas · **Demo:** <https://erdeivih.github.io/opofuente-demo/>

## Auditoría inicial

Los 40 temas ya tenían **6-7 apartados**, al menos **una tabla**, un **ejemplo resuelto**, fuente y 10
preguntas. No había temas «vacíos», pero cinco eran los más delgados por contenido (≈3.000-3.300
caracteres): **II.15 Ofimática**, **II.16 Correo**, **II.17 Licencias**, **III.18 Servidores** y
**III.22 Comunicaciones**.

También se detectó un problema de test: 19 temas tenían **todas las respuestas correctas en la letra
«a»** (global: 256 a / 83 b / 38 c / 23 d). Un test así se puede aprobar sin leer las opciones.

## Refuerzo de los 5 temas

A cada uno se le añadió una sección nueva con tabla:

| Tema | Sección añadida | Qué refuerza |
|---|---|---|
| II.15 Ofimática | Seguridad y colaboración en documentos | Macros, metadatos, control de cambios, PDF accesible |
| II.16 Correo | Autenticación del correo y diagnóstico | SPF, DKIM, DMARC, rebotes y colas |
| II.17 Licencias | Software libre en la Administración | Reutilización, EUPL, dependencias, LICENSE |
| III.18 Servidores | Monitorización, copias y continuidad | RTO/RPO, copias externas, preproducción |
| III.22 Comunicaciones | Planificación de una red inalámbrica | Bandas, canales, SSID, WPA3, firmware |

Los cinco pasan de 6 a **7 apartados** y de 1 a **2 tablas**, manteniendo su ejemplo y sus 10
preguntas. Los demás temas ya superaban ese umbral.

## Ficha de tema

Cada ficha incorpora ahora dos bloques nuevos, además de apuntes, tabla, ejemplo, fuente y práctica:

- **Lo que hay que memorizar**: 3-5 puntos concretos (cifras, plazos, clasificaciones, normas).
- **Errores típicos**: 2-4 confusiones de test («confundir X con Y», «olvidar Z»).

Los 40 temas tienen ambos bloques: **200 puntos de memorización** (5 por tema) y **~150 errores
típicos**. Se validan en el build (3-5 y 2-4) y en las pruebas.

## Letra correcta equilibrada

Se reordenaron las opciones de las 400 preguntas manteniendo su contenido: ahora hay **100 preguntas
con correcta a, 100 con b, 100 con c y 100 con d**, y cada tema usa al menos tres letras distintas.
No se cambió ni una explicación ni una respuesta, solo el orden de las opciones.

## Verificación

- **53/53** comprobaciones con Playwright en la URL pública, incluidas las tarjetas de memorizar y
  errores típicos en la ficha.
- 40/40 temas, 400 preguntas, 12/12 enlaces de convocatoria.
- 517 pruebas unitarias de backend y 225 de web; typecheck, eslint, ruff, mypy y build en verde.

## Límites

- El contenido es propio y cita fuente oficial; no sustituye a una revisión jurídica de cada norma.
- El refuerzo se ha centrado en los cinco temas más delgados; los demás ya cumplían el mínimo.
- La letra correcta se equilibró mecánicamente; conviene revisar de vez en cuando que las opciones
  siguen teniendo sentido en el nuevo orden.
