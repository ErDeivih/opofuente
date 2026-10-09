# P0.5 + P0.6 — Sesiones limpias y un solo aviso si la API no responde (5 de octubre de 2026)

Bloque 2 del plan `PLAN-PARA-DEEPSEEK-2026-10.md`. Rama `sesiones-y-aviso-api` (`a19d13a`), sacada de
`main` (`e510f97`).

## Lo que se veía

- **Cinco sesiones de prueba** en Estudiar —cuatro de examen oficial de 85 y una práctica de 176—
  creadas durante las comprobaciones, y el «Continuar estudiando» del Inicio apuntando a una de ellas.
- La lista **no decía de qué era cada sesión**: cinco filas iguales («examen oficial · sin empezar ·
  0 de 85»), porque el contexto solo viajaba como identificador del conjunto, y lo que se enseñaba era
  la etiqueta de la clave (que llega a listar **21 plantillas** en un párrafo).
- El nombre accesible del botón decía «Abrir la sesión **empezada** el …» también en las que no habían
  empezado, y las fechas salían **en bruto** («2026-10-01T13:41:58.984423»).
- Con la **API parada**, cada tarjeta de cada pantalla decía «Failed to fetch» en inglés con su botón
  de reintentar: ocho avisos iguales y ninguno decía qué hacer.

## Lo que se ha hecho

1. **La sesión guarda de qué es** (`SessionConfiguration.context_label`, congelado al crearla): el
   título de sus conjuntos, el tema de una práctica por tema («I.7 · Protección de datos»), «Repaso de
   tus fallos» o «Diagnóstico por temas». Se ve en la lista y en el nombre accesible del botón.
2. **`DELETE /study-sessions/{id}`**: descarta una sesión. Si **no tiene respuestas** se borra; si
   tiene alguna, se marca **abandonada** y el historial se conserva (nunca se borra historial con
   respuestas). Las dos cosas quedan auditadas (`study_session.discarded` / `study_session.abandoned`).
3. **La tabla de sesiones** dice de qué es cada una, con su modo, su progreso y la fecha legible, y
   tiene su botón **Descartar** con confirmación (el aviso dice si se borra o si se abandona).
4. **Un solo aviso cuando la API no responde** (P0.6): un fallo de red se reconoce en el cliente HTTP
   (`ApiUnavailableError`), TanStack Query lo anota en un almacén de módulo, y la aplicación enseña
   **un** aviso arriba —«La aplicación no responde. Arráncala con `scripts\api.ps1`…»— con un botón de
   reintentar que relee todo. Las tarjetas de cada pantalla dejan de contar su propia versión.
5. **Fechas legibles** en un solo sitio (`lib/fechas.ts`, `es-ES`, hora local de quien estudia).

## Cómo se comprueba

- `apps/api/tests/integration/test_study_api.py`:
  - `test_descartar_una_sesion_sin_respuestas_la_borra`: la sesión desaparece y el listado queda a 0;
  - `test_descartar_una_sesion_con_respuestas_la_abandona_sin_borrar_nada`: queda `abandoned` con su
    respuesta dentro; una sesión que no existe responde 404;
  - `test_la_sesion_dice_de_que_es`: la etiqueta de contexto viaja al crear y al listar.
- `apps/web/tests/unit/apiCaida.test.tsx`: con `fetch` que falla se enseña **un** aviso con cómo
  arrancar la aplicación y el contenido de la pantalla sigue ahí; con la API levantada, ninguno.
- `apps/web/tests/unit/fechas.test.ts`: fechas legibles, sin zona se toma por UTC y una ilegible se
  enseña tal cual en vez de inventarse una.
- Puertas: `.\scripts\gates.ps1` **18/18** antes de fusionar (medida en la copia limpia, sobre este
  commit).
- A mano, contra los datos del propietario:
  - se descartaron las **5 sesiones de prueba** (4 sin empezar → **borradas**; 1 en marcha con 1
    respuesta → **abandonada**, historial conservado) y se dejaron las **2 terminadas**, que son
    historia de verdad. Copia de seguridad previa:
    `opofuente-antes-de-descartar-sesiones-de-prueba-194319571337.sqlite3`;
  - una sesión de examen oficial nueva del TAI libre 2025 A dice de qué es
    («TAI ingreso libre 2025 · modelo A (examen oficial INAP)»), sus fechas llevan zona
    (`2026-10-05T17:45:03.939794Z`), su tiempo límite son 120 minutos y se descarta con la ruta nueva
    (`action: deleted`), dejando la base como estaba.

## Lo que queda del plan

Siguiente bloque, según el orden actualizado por Claude: **P0.4, los apuntes por tema (el «dossier»)**,
que es lo más lento de la aplicación en el camino de estudiar —medido por él: **99 s** la primera vez
para el tema II.1, **21 s** después, 1,16 MB de datos y otros 21 s para guardar una versión—, y después
la pantalla de estudio (P1.1/P1.2).
