# F1 — Las dos zonas: lo que se ha revisado antes de fusionar (7 de octubre de 2026)

Rama `f1-zonas` en la copia limpia (`opofuente-arreglos`), sobre `main = 3ebe0dd`. Pendiente: el
resultado de las puertas (se anota al final cuando terminen).

## Qué hace

- **Dos marcos, elegidos por la dirección**: `/admin/…` monta `AdminShell` (menú lateral, indicadores del
  sistema y el aviso «Modo administración · sin contraseña: solo en este ordenador»); cualquier otra
  dirección monta `AppShell`, el marco del alumno. Con rutas envolventes, una pantalla nueva **no puede
  quedarse sin marco ni coger el de la otra zona**.
- **Mapa del alumno (7)**: Inicio `/`, Temario `/temario`, Tests `/tests`, Simulacros `/simulacros`,
  Exámenes `/examenes`, Fallos `/fallos`, Progreso `/progreso`. Las seis sin pantalla todavía se pintan
  con `ComingSoonPage`, que saca el título y la frase **del propio mapa de navegación** (no copiados a
  mano, así no pueden divergir cuando F3 las construya).
- **Mapa de administración (11)**: Importaciones, Biblioteca, Revisión, Cambios, Errores, Preguntas,
  Programa, Estudiar, Buscar, Ajustes y Componentes, con las páginas que ya existían **sin tocarlas por
  dentro**.
- **Ninguna dirección vieja da 404**: las diez se redirigen a su sección nueva, y el redirect **conserva
  la consulta y el ancla** (`OldAddress`), que es lo que hace que `/biblioteca?documento=…` siga abriendo
  esa ficha y `/buscar?q=…` siga trayendo la búsqueda hecha.

## Lo que he comprobado yo, antes de las puertas

1. **La zona del alumno no enseña la cocina.** Pasado el buscador con la lista de vocabulario interno
   (bandeja, revisión, fuente, tramo, mapeo, conjunto, clave, evidencia, artefacto, corpus, dossier,
   ingesta) sobre `ComingSoonPage.tsx`, `AppShell.tsx` y `HomePage.tsx`: **sin coincidencias**; las dos
   únicas apariciones son **comentarios** que explican lo que se ha retirado («ni caja de *Buscar en el
   corpus*», «eso se fue con el panel»).
2. **El acoplamiento de la suite era pequeño**, como decía el plan: de las 54 pruebas E2E, solo
   `first-run.spec.ts` pulsa el menú por rótulo; el resto entra por URL, así que las redirecciones las
   mantienen funcionando.

## Lo que queda por verificar (no se da por bueno hasta verlo)

- El registro de `.\scripts\gates.ps1` **completo y en 18/18**, pasado por mí sobre el commit de la rama.
- Que la E2E pasa contando con las direcciones viejas: la prueba nueva de que `/bandeja` acaba en
  `/admin/importar` es la que demuestra que las redirecciones existen de verdad y no solo en el mapa.
- Que en el móvil la barra del alumno y la del panel no se pisan (queda para las capturas de
  `npm run screens`).

## Nota de operación: no metas `gates.ps1` en una tubería de PowerShell

Costó una corrida entera de puertas el 7 de octubre de 2026, y el fallo **parecía de la aplicación**:
`Excepción en '11. build backend' … FALLO (código -1)`.

No lo era. Lanzar el guion como `.\scripts\gates.ps1 2>&1 | Tee-Object …` convierte la línea de progreso
que `uv` escribe en **stderr** en un `ErrorRecord` terminante, porque `scripts/common.ps1` pone
`$ErrorActionPreference = 'Stop'`. La puerta lo reporta como excepción con código −1 aunque `uv build`
esté bien. Reproducido con un guion mínimo: sin tubería, `OK (código 0)`; con `2>&1 | Tee-Object`,
`FALLO (código −1)`; con redirección **del sistema operativo** (`cmd /c "… > registro 2>&1"`), `OK`.

Conclusión: para guardar el registro, usa la redirección de `Start-Process`/`cmd` y **no** una tubería de
PowerShell. Un fallo en la puerta 11 con código −1 y ninguna traza de compilación es esto, no el build.

