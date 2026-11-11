# Lector de temas: feedback aplicado

**Fecha:** 11/11/2026 · **Demo:** <https://erdeivih.github.io/opofuente-demo/>

## OP-U1 — Índice fijo

Cada tema tiene una barra **«Índice ▾ · epígrafe actual»** pegada arriba. Un toque abre la lista de
epígrafes; otro toque salta al elegido. El epígrafe actual se actualiza con el scroll y el elemento
activo queda resaltado. En móvil la barra no desborda y se puede cerrar tocando de nuevo.

## OP-U2/OP-I3 — Sin duplicados

En los temas largos, el **resumen** y las **fuentes** salen una sola vez, dentro del desarrollo de 10
apartados (`Resumen para memorizar` y `Fuentes citadas`). Se ocultan las tarjetas separadas «Lo que
hay que memorizar» y «Revisión y fuente» cuando ya existen esas secciones. Los temas cortos conservan
sus tarjetas porque no tienen desarrollo largo. Resultado: **1 resumen y 1 fuentes visibles por tema**.
«Errores típicos» se mantiene como bloque independiente porque no duplica el resumen.

## OP-I1 — Jerarquía y lectura

- **H2:** 22 px, peso 700, margen superior de 32 px.
- **H3:** 18 px, peso 700.
- **Cuerpo y listas:** 16 px con interlineado **1,6**.
- **Medida:** párrafos y listas limitados a **68 caracteres**.
- **Móvil:** sin scroll horizontal a 390 px; tablas y SVG se adaptan.

La comprobación de Playwright mide los estilos computados y el `scrollWidth` real a 390 px.

## OP-U3/OP-F1 — Continuar leyendo

La posición se guarda por tema y epígrafe en `localStorage` (`opofuente-demo-reading-v1`). Al volver
a abrir el tema aparece **«Continuar en {epígrafe}»** con el botón **«Continuar leyendo»**, que salta
al punto guardado. La barra de índice y el resumen siguen funcionando después del salto.

## OP-F2 — Simulacro TAI

Nueva pestaña **Simulacro** con el formato del ejercicio:

- **80 preguntas** de cuestionario (parte 1) + **20** de supuesto de los bloques III/IV (parte 2).
- **120 minutos** de cuenta atrás.
- **−1/3** por error; en blanco no resta.
- **Mínimo 25/50 en cada parte** para considerarse apto.
- Sin corrección hasta el final; nota por parte y revisión.

Los 80+20 se generan del banco de prácticas; el simulacro es una simulación de la demo, no un examen
oficial.

## OP-F3 — Vigencia

Todos los temas muestran en la cabecera **«Vigente a 11/2026»**, junto a los sellos de apuntes,
práctica y formato.

## Botón de test

En los temas largos, la cabecera tiene **«Test del tema»**. Un toque desplaza al bloque de test (15 preguntas) sin pasar por el índice. El índice y el test están, por tanto, a un toque cada uno.

## Capturas

| Pantalla | Captura 390 px |
|---|---|
| Índice desplegado | [indice-tema-390](capturas/demo-pages/indice-tema-390.png) |
| Test del tema | [test-tema-390](capturas/demo-pages/test-tema-390.png) |
| Simulacro (reglas) | [simulacro-390](capturas/demo-pages/simulacro-390.png) |
| Simulacro (resultado) | [simulacro-resultado-390](capturas/demo-pages/simulacro-resultado-390.png) |
| Tema V.35 | [tema-v-35-390](capturas/demo-pages/tema-v-35-390.png) |

## Verificación

**94/94** comprobaciones Playwright en la URL pública: índice, un solo resumen/fuentes, H2/cuerpo,
sin scroll horizontal, continuar leyendo, simulacro 80+20 con nota y vigencia. 12/12 enlaces de
convocatoria (200).
