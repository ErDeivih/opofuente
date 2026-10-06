# F0 hecho, y por dónde sigue el rediseño (6 de octubre de 2026)

Estado: **F0 entregado** (rama `f0-capturas-y-privacidad`, commit `7f5b889`, sobre `main = e5ce278`).
Las fases **F1 a F9** del `REDISENO-ALUMNO-TAI-Y-PANEL-ADMIN-2026-10` **no** están hechas: este
documento dice qué falta, en qué orden y con qué dudas, para que las continúe la siguiente sesión.

## F0 — Ver la interfaz y saber por dónde sangra (hecho)

- **`npm run screens`** (nuevo): recorre las **11 rutas** a **1280×800** y **390×844**, guarda el PNG en
  `artifacts/screens/` y escribe `artifacts/screens/report.md` con, por pantalla: lo que tarda, los
  errores de consola, las violaciones de axe y las palabras prohibidas.
- **`apps/web/tests/palabrasProhibidas.ts`**: la lista de lo que no puede ver un alumno en un solo
  sitio —rutas de fichero (`:\`, `F:\`, `.pdf`…), otras oposiciones (Celador, Guardia Civil, SAS,
  BOCYL), bancos privados (Rojo, GSI, Preparatic), jerga interna (revisión, bandeja, fuente, tramo,
  mapeo, representación, conjunto, clave, versión, evidencia, artefacto) y UUID visibles—, con el
  buscador que devuelve **dónde** aparece cada una.
- No entra en las puertas: `npm run e2e` sigue mirando `tests/e2e`, y esto vive en `tests/screens` con
  su propia configuración. En F0 las palabras **informan**; en F9 bloquearán.

### Lo que dice el informe hoy (datos de prueba, 22 capturas)

**Las 22 pantallas** enseñan palabras prohibidas. No es un detalle de estilo: hoy la aplicación es una
herramienta interna de gestión de material, no una web de estudio.

| lo que sale | dónde |
| --- | --- |
| `F:\`, `:\`, `.pdf` | Inicio, Ajustes, Bandeja, Biblioteca, Buscar, Revisión |
| Celador, Guardia Civil, SAS | **todas** |
| revisión, bandeja, fuente | **todas** |
| conjunto, clave, versión, evidencia, artefacto, mapeo, representación | Programa, Estudiar, Preguntas, Errores, Ajustes, Buscar, Revisión |
| UUID visibles | Biblioteca, Cambios |

Otras dos cosas que salen del informe:

- **un error de consola en las 22**: `frame-ancestors` en una `<meta>`, que el navegador ignora por
  definición. Va en cabecera HTTP o no va. Es cosmético pero ensucia todas las pantallas.
- **Revisión tarda 30-35 s** en quedar lista para interactuar (su carga inicial es 1,5 s): es lo que
  tiene en rojo la puerta 18. Está medido y con PNG en el informe.

## Lo que falta, en el orden del documento

| fase | qué es | por qué importa |
| --- | --- | --- |
| **F1** | Dos zonas: router, layout del alumno (7 entradas) y layout de admin, con redirecciones de las rutas viejas | es el esqueleto: sin esto no hay «fuera la paja» |
| **F2** | API `/api/v1/student/*` (overview, syllabus, topics, progress), orden numérico de temas y solo TAI | lo que el alumno ve no puede llevar evidencia, conjunto ni rutas |
| **F3** | Inicio, Temario, Tema (sin apuntes), Progreso | las pantallas que más se usan |
| **F4** | Tests: configurador, pantalla con teclado y mapa, resultado | «de Inicio a contestando: menos de 4 clics» |
| **F5** | Simulacros por `exam_parts`, exámenes oficiales y Fallos | lo que de verdad se parece a una academia |
| **F6** | Admin Preguntas (editar, marcar la correcta, asignar tema, reportes) | tu panel: corregir preguntas sin tocar SQL |
| **F7** | Admin Apuntes (`topic_notes` con versiones y publicar) | tu panel: escribir y arreglar apuntes |
| **F8** | Admin Temario (crear, renombrar, reordenar, archivar) | ampliar temas según entra material nuevo |
| **F9** | Palabras prohibidas **bloqueantes** en las puertas | la garantía de que lo de arriba no se rompe |

Antes de F4 hay dos cosas pendientes del plan anterior que siguen vivas: **la segunda mitad de P0.4**
(el dossier de un bloque sigue devolviendo 58,8 MB y 19 s: hace falta resumen y fragmentos paginados —
lo necesita la columna «Material del tema» de F7) y **la puerta 18 en rojo** por la lentitud de
Revisión, que al pasar a `/admin/revision` sigue teniendo que ser rápida o, si no, llevar su propio
límite **justificado** (nunca subirlo sin más).

## Dudas que dejo indicadas (para Claude, no para decidir yo)

1. **Quién filtra TAI.** El documento propone fijar la oposición por configuración
   (`OPOFUENTE_STUDENT_OPPOSITION=tai-age`) y una API de alumno aparte. La alternativa es que el
   filtro viva en la API de alumno sin variable (siempre TAI). Me inclino por la variable: el día que
   entre otra oposición, el trabajo ya está hecho.
2. **Acceso a `/admin`.** El documento deja `OPOFUENTE_ADMIN=1` por defecto en local. Si algún día la
   aplicación se abre a otras personas, ese interruptor no es una frontera de seguridad: harán falta
   cuentas. Conviene que el panel lo diga en algún sitio, para no confundir «oculto» con «privado».
3. **Las 227 preguntas de bancos privados.** Sin resolver los derechos, la zona del alumno no puede
   servirlas. Propuesta del documento: campo `distribution` (`personal` | `public`) en los conjuntos.
   Decisión tuya.
4. **Los apuntes que ya existen** (los que construye el dossier desde el material) **no** son los
   `topic_notes`: son la materia prima. En F7 hay que decidir si un tema puede tener apuntes escritos a
   mano **y** material citado (yo diría que sí: el material es la columna derecha del editor).
5. **Estructura visual.** No he tocado ni un estilo todavía. Los tokens y los componentes
   reutilizables (`src/ui/`: Button, Card, ProgressBar, Tabs, Accordion, OptionButton, QuestionGrid,
   StatTile, EmptyState, Modal) son la primera tarea de F3, y ahí sí conviene que mires el resultado:
   las capturas de `npm run screens` son la forma de enseñártelo sin que abras un editor.

## Cómo se comprueba lo de F0

```powershell
npm run build --workspace @opofuente/web   # la vista previa sirve el paquete construido
npm run screens --workspace @opofuente/web # 22 capturas + artifacts/screens/report.md
```

Ya está ejecutado: **22 de 22 capturas** y el informe, en `artifacts/screens/` (ignorado por git: se
genera, no se guarda).
