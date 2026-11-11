# Revisión final de la demo — 10/11/2026

**URL:** <https://erdeivih.github.io/opofuente-demo/> · **Verificación:** **94/94** comprobaciones con
Playwright contra la URL pública, a 1280 y **390 px**. Sin errores de página.

## Qué se ha revisado

| Comprobación | Resultado |
|---|---|
| Tres pestañas visibles y pulsables | **Temario, Cobertura y Prácticas**, con 44 px de alto |
| Portada | Cobertura, resumen por bloque, «Continuar donde lo dejé», 3 prácticas y un solo aviso |
| Buscador | `III.20` deja exactamente 1 tema a 390 px |
| Filtros | «Con apuntes» y «Con práctica» devuelven los temas esperados |
| Mapa de cobertura | 40 filas y sellos de apuntes/práctica coincidentes, también a 390 px |
| Temas de la tanda | III.19 y III.20 con apuntes completos, tabla, fuente y 10 preguntas |
| Ficha de tema | Migas «Temario › III.19», sellos y enlace a convocatorias |
| Práctica | Corrección al elegir, sin «Comprobar», reanudable y con enlace al BOE |
| Enlaces | 12/12 convocatorias abren (HTTP 200) y su texto es «Bases de {título}» |
| Sin errores | Ningún error de página en la consola del navegador |

## Capturas a 390 px

| Pantalla | Captura |
|---|---|
| Portada | [portada-390](capturas/demo-pages/portada-390.png) |
| Temario | [temario-390](capturas/demo-pages/temario-390.png) |
| Cobertura / mapa | [cobertura-390](capturas/demo-pages/cobertura-390.png) |
| Prácticas (lista completa) | [practicas-390](capturas/demo-pages/practicas-390.png) |
| Buscador con `III.20` | [buscador-390](capturas/demo-pages/buscador-390.png) |
| Tema III.19 | [tema-iii-19-390](capturas/demo-pages/tema-iii-19-390.png) |
| Tema III.20 | [tema-iii-20-390](capturas/demo-pages/tema-iii-20-390.png) |
| Tema III.26 | [tema-iii-26-390](capturas/demo-pages/tema-iii-26-390.png) |
| Tema IV.30 | [tema-iv-30-390](capturas/demo-pages/tema-iv-30-390.png) |
| Guía de estudio | [guia-390](capturas/demo-pages/guia-390.png) |
| Examen | [examen-390](capturas/demo-pages/examen-390.png) |
| Examen completo | [examen-completo-390](capturas/demo-pages/examen-completo-390.png) |
| Resultado del examen | [examen-resultado-390](capturas/demo-pages/examen-resultado-390.png) |
| Supuestos | [supuestos-390](capturas/demo-pages/supuestos-390.png) |
| Tema largo V.39 | [tema-v-39-390](capturas/demo-pages/tema-v-39-390.png) |
| Tema largo II.13 | [tema-ii-13-390](capturas/demo-pages/tema-ii-13-390.png) |
| Tema largo III.21 | [tema-iii-21-390](capturas/demo-pages/tema-iii-21-390.png) |
| Índice del tema | [indice-tema-390](capturas/demo-pages/indice-tema-390.png) |
| Simulacro | [simulacro-390](capturas/demo-pages/simulacro-390.png) |
| Resultado simulacro | [simulacro-resultado-390](capturas/demo-pages/simulacro-resultado-390.png) |
| Resultado de supuesto | [supuesto-resultado-390](capturas/demo-pages/supuesto-resultado-390.png) |
| Estadísticas | [estadisticas-390](capturas/demo-pages/estadisticas-390.png) |
| Estadísticas vacías | [estadisticas-vacia-390](capturas/demo-pages/estadisticas-vacia-390.png) |
| Tema V.40 | [tema-v-40-390](capturas/demo-pages/tema-v-40-390.png) |
| Tema completo (I.1) | [tema-completo-390](capturas/demo-pages/tema-completo-390.png) |
| Tema pendiente (III.23) | [tema-pendiente-390](capturas/demo-pages/tema-pendiente-390.png) |
| Práctica | [practica-390](capturas/demo-pages/practica-390.png) |
| Ficha de pregunta | [pregunta-390](capturas/demo-pages/pregunta-390.png) |

## Estado final

- **40/40** apuntes completos; **0 pendientes**; **0 solo resumen**; **40 prácticas**; **400 preguntas**.
- Cobertura por bloque: **I 12/12 · II 5/5 · III 9/9 · IV 7/7 · V 7/7**.
- **12/12** enlaces de convocatoria abren (HTTP 200).
- **Examen por bloque** con tiempo/penalización, **historial unificado** e **histórico de intentos**
  verificados; fecha de revisión visible en la ficha.
- **CSP y referrer** presentes; **errata descargada como JSON**; etiqueta **Simulación** en el examen.
- **Corrección al elegir** sin «Comprobar», **estados vacíos con acción** y **resultado con revisión primero**.
- **Lector**: índice fijo, resumen/fuentes únicos, tipografía 22/16 px, continuar por epígrafe y vigencia.
- **Simulacro TAI** 80+20 con 120 min, −1/3 y mínimo 25/50 por parte.
- **Temas largos** I.1/III.21/IV.27/V.34/V.35 con SVG, test cases y fuentes; 94/94 comprobaciones.
- Pruebas: 517 unitarias de backend, 225 de web, typecheck, eslint, ruff, mypy y build.

## Temario completo

No quedan temas pendientes: los 40 están redactados con apuntes propios, tabla, ejemplo, fuente y 10 preguntas, y cada uno tiene su fila y sellos en el mapa.
