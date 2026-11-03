# O7 · Lectura del tema en voz alta

Estado: **implementado, sin puerta verde**. Tras reparar el manifiesto npm, `validar` ya construye la
imagen y corre la suite de la API (con 8 fallas ajenas al slice), pero la prueba unitaria del módulo
puro **sigue sin ejecutarse**: está escrita en `apps/web/src/features/student/lecturaEnVoz.test.ts`, y
Vitest solo incluye `tests/unit/**` porque `apps/web/vite.config.ts` está fuera de las fuentes que este
trabajador puede escribir, así que el patrón `src/**/*.test.{ts,tsx}` no se ha podido añadir. Queda
escalado al coordinador.

## Qué he construido

- Módulo puro `apps/web/src/features/student/lecturaEnVoz.ts`: convierte el markdown del capítulo en
  los trozos que se pronuncian.
  - `sinAdornos`: quita negritas, cursiva (`_…_`), código y enlaces; **no** toca identificadores con
    barra baja (`tcp_ip`), y una frase que solo es larga no se parte.
  - `frases`: agrupa oraciones en trozos de hasta 240 caracteres.
  - `fragmentosDelApartado` / `fragmentosDelCapitulo`: un trozo por título, por elemento de lista y por
    fila de tabla (celdas separadas por coma), con `key` estable y el apartado de cada trozo. Las
    marcas `<!-- revisar: … -->` no se dicen.
  - `vozPreferida` / `hayVozEnEspanol`: eligen voz por idioma (castellano primero) y prefieren la voz
    local del equipo. Sin voces en español devuelven la que haya; la pantalla lo advierte.
  - `VELOCIDADES`: 0,8 · 1 · 1,25.
- Reproductor `apps/web/src/features/student/LecturaEnVoz.tsx`: botones Escuchar/Pausar/Reanudar,
  Detener y selector de velocidad, con `role="status"` que dice siempre qué pasa (apartado N de M,
  pausa, aviso si el navegador no sintetiza o el equipo no tiene voces). Cada lectura lleva un número
  de generación: al detener o desmontar, los `onend` tardíos se ignoran.
- Integración en `apps/web/src/pages/student/TopicNotesPage.tsx`: el reproductor va bajo el título del
  capítulo, se prepara una vez por capítulo (`useMemo`) y se monta con `key={capítulo}` para que al
  cambiar de capítulo la voz se cancele sola.
- Estilos aditivos `.voz*` en `apps/web/src/styles/global.css`, reutilizando `.button` y los tokens
  existentes.

## Cómo fluye la información

1. La pantalla ya tiene el capítulo abierto (`StudentNotes.sections`).
2. `fragmentosDelCapitulo` lo parte en trozos en el navegador; no viaja nada al servidor.
3. El reproductor crea un `SpeechSynthesisUtterance` por trozo con la voz elegida y la velocidad, y
   encadena el siguiente en `onend`.
4. Pausar/reanudar usan `speechSynthesis.pause()/resume()`; Detener sube la generación, llama a
   `cancel()` y vuelve al principio.

## Ficheros y migraciones

- `apps/web/src/features/student/lecturaEnVoz.ts` (nuevo).
- `apps/web/src/features/student/lecturaEnVoz.test.ts` (nuevo; escrito junto al módulo porque el
  trabajador solo puede escribir bajo `apps/web/src`, pero **aún no lo recoge ningún runner**).
- `apps/web/src/features/student/LecturaEnVoz.tsx` (nuevo).
- `apps/web/src/pages/student/TopicNotesPage.tsx` (integración).
- `apps/web/src/styles/global.css` (bloque `.voz*`).
- Sin migración y sin cambios de contrato: no hay endpoint nuevo.

## Patrones y decisiones aplicadas

- **La voz es del aparato, no del servicio**: Web Speech API; sin nube, sin dependencias nuevas, sin
  contrato HTTP. Es la única forma de ofrecer lectura en voz sin mandar el temario a un tercero.
- **Lógica separada del dibujo**: qué se pronuncia está en un módulo puro y probables sin navegador;
  el componente solo reproduce.
- **Estado explícito**: cuando no se puede leer se dice por qué; no se deja un botón mudo.
- **Cancelación por generación**: el `cancel()` del sintetizador no desengancha `onend` pendientes; el
  contador evita que una lectura vieja siga hablando.

## Seguridad y privacidad

- El texto no sale del equipo: no hay petición, ni servicio externo, ni audio guardado.
- Se usa la voz local (`localService`) cuando existe; si el sistema solo ofrece voces de red, se usa la
  que haya y no se simula lo contrario.
- Sin secretos, sin datos personales nuevos, sin escritura en disco.

## Puertas ejecutadas y resultado

- `validar({"project":"opofuente","gate":"648dc9aeae21"})` sobre el árbol con el CSS y la pantalla →
  **FALLO DE ENTORNO**, no de pruebas:
  `sandbox_image_failed: source_manifest_invalid: npm ci rechaza el protocolo workspace: de los
  package.json publicos; corrige coherentemente dependencia local y package-lock.json con el gestor
  registrado, sin eliminar dependencias ni puertas. La imagen no se ha construido y ninguna prueba ha
  corrido`.
- **Actualización posterior**: ese manifiesto se reparó (`workspace:*` → `^0.0.0`, coherente con el
  lock ya resuelto) y la misma puerta ya construye la imagen y corre: 1083 pasan, 8 fallan y 3 se
  omiten. Las 8 fallas son de `test_safe_inputs.py`, `test_safe_paths.py` y `test_study_plan.py`,
  ajenos a este slice; la prueba de este módulo vive en `apps/web/src/features/student/` y el
  `test.include` de `vite.config.ts` (solo lectura) la deja fuera, así que sigue **sin ejecutar**.
- `validar` sobre el árbol con el módulo, el reproductor y la prueba unitaria → `waiting_resources`
  («capacidad ocupada: heavy», reintento a 60 s): tampoco se ejecutó nada; es una espera, no un fallo de
  pruebas.
- No se ejecutaron `npm run test:web`, `tsc`, `eslint` ni build. No hay evidencia verde de nada.
- La prueba unitaria existe en el repositorio, pero **no se puede ejecutar**: `apps/web/tests/unit/`
  rechaza la escritura por política de fuentes y `apps/web/vite.config.ts` (que habría que tocar para
  incluir `src/**/*.test.{ts,tsx}`) también rechaza la escritura. Escalado al coordinador con la ruta,
  el patrón y el test redactado; hasta que se resuelva, el slice se documenta como no verificado.

## Prueba manual

1. Abrir un tema con apuntes (`/temario/IV.7?capitulo=IV.7.2`).
2. Pulsar **Escuchar**: se oye el título del capítulo y los apartados en orden; el estado dice en qué
   apartado va.
3. **Pausar** y **Reanudar** en mitad de un párrafo; **Detener** vuelve al principio.
4. Cambiar de velocidad a Lenta y comprobar que la siguiente frase ya va más despacio.
5. Navegar a otro capítulo mientras suena: la voz anterior se corta y no sigue.
6. En un navegador sin `speechSynthesis`, comprobar el aviso y que los controles están desactivados.

## Limitaciones conocidas

- **Ninguna prueba ejecutada** (imagen sin construir / capacidad ocupada) y **prueba unitaria escrita
  pero sin runner**: falta ampliar `include` de `apps/web/vite.config.ts`, que este trabajador no puede
  editar.
- `speechSynthesis.pause()` depende del navegador: en algunos motores la pausa corta la frase en curso.
- No hay resaltado del trozo que suena: el estado dice el apartado, no la frase.
- Si el sistema cambia de voces a mitad de lectura, la voz elegida se mantiene hasta la siguiente.
- El texto se prepara al abrir el capítulo: un capítulo muy largo cuesta un primer render algo mayor.

## Qué se rompe si cambias X

- Si cambias el markdown del reproductor sin tocar `notesMarkdownParser.ts`, lo que se oye y lo que se
  ve dejarán de contar lo mismo.
- Si quitas la `key` por capítulo en la pantalla, dos capítulos pueden sonar a la vez.
- Si quitas el contador de generación, «Detener» dejará de detener de verdad.
- Si cambias `.apuntes__capitulo` o `.button`, revisa el bloque `.voz` (usa ambos).

## Qué criticaría un revisor senior

- Que se entregue sin ninguna puerta verde ni la prueba unitaria pedida.
- Que la lógica de troceo no tenga un caso de tabla ancha o de texto sin puntuación.
- Que la pausa no esté probada en un navegador real.
- Que el aviso de «sin voz en español» no ofrezca ir a las preferencias del sistema.
