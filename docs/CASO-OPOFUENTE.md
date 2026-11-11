# Caso OpoFuente — temario completo y demo verificable

**URL pública:** <https://erdeivih.github.io/opofuente-demo/> · **Fecha:** 10/11/2026

## 1. Resumen ejecutivo

OpoFuente es una aplicación local-first para preparar oposiciones de informática C1. Este caso
documenta la parte que ya se puede enseñar: un **temario común de 40 temas, 400 preguntas base, 50 de
casos prácticos y 40 prácticas**, publicado como demo estática, sin cuentas ni backend, con progreso en el navegador.

| Métrica | Valor |
|---|---|
| Temas con apuntes completos | **40/40 (100 %)** |
| Preguntas razonadas | **400** (10 por tema) |
| Casos prácticos | **5** casos · **50** preguntas |
| Supuestos resueltos | **19** · **380** preguntas |
| Preguntas totales | **450** (400 de temario + 50 de casos) |
| Prácticas | **40** (una por tema) |
| Bloques | **5** (I-IV al 100 %; V 7/7) |
| Convocatorias C1 | **12** (10 draft, 2 archivadas) |
| Comprobaciones Playwright | **120/120** en la URL pública |
| Enlaces de convocatoria | **12/12** (HTTP 200) |
| Pruebas | **517** unitarias backend · **225** web |
| Capturas | 390 y 1280 px en `docs/capturas/demo-pages/` |

## 2. Problema y propuesta

Preparar un temario de 40 temas exige estudiar, practicar y medir sin perder el hilo. Muchas
plataformas encierran el contenido y el progreso; esta demo demuestra lo contrario: **contenido
propio, navegable y verificable**, con el estado de cobertura a la vista y el progreso guardado solo
en el navegador.

La propuesta no es «una web bonita»: es un **producto mínimo completo** con temario, mapa de
cobertura, prácticas, examen, estadísticas, guía de estudio y mecanismos de calidad y seguridad.

## 3. Cobertura real

| Bloque | Temas | Apuntes | Cobertura |
|---|---|---|---|
| I · Administración y normativa | 12 | 12 | 100 % |
| II · Informática básica y ofimática | 5 | 5 | 100 % |
| III · Sistemas, redes y comunicaciones | 9 | 9 | 100 % |
| IV · Datos y desarrollo | 7 | 7 | 100 % |
| V · Seguridad y administración electrónica | 7 | 7 | 100 % |
| **Total** | **40** | **40** | **100 %** |

Cada tema incluye 6-7 apartados, tabla, ejemplo resuelto, fuente oficial, 10 preguntas, «lo que hay
que memorizar», errores típicos, fecha de revisión y norma citada. Los 400 puntos de memorización y
las opciones de test están equilibrados: 100 respuestas correctas por cada letra a/b/c/d.

## 4. Qué puede hacer una persona

- **Temario** con búsqueda y filtros; cada ficha muestra cobertura, fuente, revisión, memorizar,
  errores típicos, práctica y reporte de erratas.
- **Mapa de cobertura** con los 40 temas y dos sellos: apuntes y práctica.
- **Prácticas** de 10 preguntas con corrección al elegir, explicación, fuente y reanudación.
- **Casos prácticos**: 5 escenarios de 10 preguntas sobre los temas más delgados (II.15, II.16,
  II.17, III.18 y III.22), con su propio runner y registro en el historial.
- **Temas largos**: I.1, III.21, IV.27, V.34 y V.35 con 2.488-3.064 palabras, 70 test cases, tablas
  y 3 SVG propios; página autosuficiente y fuentes citadas por apartado/página.
- **Supuestos resueltos**: 17 casos (7 oficiales del INAP y 10 propios), 340 preguntas con resolución, justificación y modo examen de 20 preguntas.
- **Guía de estudio** con orden de bloques y temas flojos (<70 % en la última práctica).
- **Examen por bloque** y **examen completo** que mezcla los cinco bloques, con tiempo total,
  penalización por fallo, nota y revisión de fallos. El perfil TAI usa 120 min y −1/3; las C1 locales
  se marcan como estimación porque sus bases draft no publican reglas.
- **Estadísticas** separadas de prácticas e **historial unificado** de intentos con tipo, bloque,
  fecha, aciertos, tiempo y nota.
- **Seguridad**: CSP por `<meta>`, `referrer: no-referrer`, `connect-src 'none'` y etiqueta
  «Simulación» en el examen. Sin servidor no hay cabeceras HTTP completas; se documenta el límite.

## 5. Arquitectura de la demo

- React 19 + TypeScript + Vite; una sola página con rutas por hash.
- Datos generados desde `fixtures/` a `apps/web/demo/data.json`; sin peticiones de red en ejecución.
- Progreso, intentos, erratas y reanudación en `localStorage`.
- Build estático publicado en GitHub Pages; el repositorio de la demo solo contiene el build.
- Verificación con Playwright: 69 comprobaciones a 390/1280 px, capturas y enlaces de convocatoria.

## 6. Evidencia visual

| Pantalla | Captura 390 px |
|---|---|
| Portada y cobertura | [portada-390](capturas/demo-pages/portada-390.png) |
| Mapa de los 40 temas | [cobertura-390](capturas/demo-pages/cobertura-390.png) |
| Ficha de tema | [tema-completo-390](capturas/demo-pages/tema-completo-390.png) |
| Práctica | [practica-390](capturas/demo-pages/practica-390.png) |
| Corrección | [correccion-1280](capturas/demo-pages/correccion-1280.png) |
| Examen por bloque | [examen-390](capturas/demo-pages/examen-390.png) |
| Examen completo | [examen-completo-390](capturas/demo-pages/examen-completo-390.png) |
| Resultado y fallos | [examen-resultado-390](capturas/demo-pages/examen-resultado-390.png) |
| Estadísticas e historial | [estadisticas-390](capturas/demo-pages/estadisticas-390.png) |
| Guía de estudio | [guia-390](capturas/demo-pages/guia-390.png) |
| Supuestos | [supuestos-390](capturas/demo-pages/supuestos-390.png) |
| Tema largo V.39 | [tema-v-39-390](capturas/demo-pages/tema-v-39-390.png) |
| Tema largo III.21 | [tema-iii-21-390](capturas/demo-pages/tema-iii-21-390.png) |
| Tema largo II.14 | [tema-ii-14-390](capturas/demo-pages/tema-ii-14-390.png) |
| Tema largo III.22 | [tema-iii-22-390](capturas/demo-pages/tema-iii-22-390.png) |
| Tema largo IV.28 | [tema-iv-28-390](capturas/demo-pages/tema-iv-28-390.png) |
| Tema largo II.13 | [tema-ii-13-390](capturas/demo-pages/tema-ii-13-390.png) |
| Índice del tema | [indice-tema-390](capturas/demo-pages/indice-tema-390.png) |
| Simulacro | [simulacro-390](capturas/demo-pages/simulacro-390.png) |
| Resultado simulacro | [simulacro-resultado-390](capturas/demo-pages/simulacro-resultado-390.png) |
| Tema V.35 | [tema-v-35-390](capturas/demo-pages/tema-v-35-390.png) |
| Resultado de supuesto | [supuesto-resultado-390](capturas/demo-pages/supuesto-resultado-390.png) |
| Caso práctico | [caso-practico-390](capturas/demo-pages/caso-practico-390.png) |

Capturas completas en [docs/capturas/demo-pages/](capturas/demo-pages/).

## 7. Calidad y límites

- **Derechos:** el material de academia o de terceros no se publica (decisión D-034); el temario TAI
  recuperado es privado. Los apuntes son de redacción propia y citan fuente oficial.
- **Normas:** las reglas de examen de las C1 locales están pendientes de bases oficiales; se muestran
  como estimación, no como dato verificado.
- **Demo estática:** sin cuentas, sin backend, sin sincronización entre dispositivos. El progreso se
  pierde si se borra el almacenamiento del navegador.
- **Verificación:** las cifras de cobertura salen del build (`data.json`) y las comprobaciones se
  ejecutan contra la URL pública, no solo en local.

## 8. Qué demuestra para el portfolio

1. **Producto completo**: no un mockup; 40 temas con contenido real y 400 preguntas.
2. **Criterio editorial**: cobertura calculada, fuentes oficiales, derechos y límites explícitos.
3. **Calidad medible**: 63 comprobaciones, capturas 390/1280, 517 + 225 pruebas y build.
4. **Diseño de interacción**: prácticas, examen con tiempo/penalización, estadísticas e historial.
5. **Seguridad y transparencia**: CSP, referrer, etiqueta de simulación y reporte de erratas.

## 9. Cómo revisarlo en 2 minutos

1. Abre <https://erdeivih.github.io/opofuente-demo/>.
2. Entra en **Cobertura** y comprueba 40/40 y los sellos.
3. Abre un tema, revisa «Lo que hay que memorizar» y prueba una práctica.
4. Lanza el **Examen completo**, mira tiempo/penalización y termina para ver la nota.
5. Ve a **Estadísticas** y revisa el historial con fecha, tipo, bloque, aciertos y tiempo.
