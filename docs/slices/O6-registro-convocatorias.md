# O6 · Registro de convocatorias TIC

Estado: **implementado, NO verificado**. Las puertas no han arrancado: el sandbox no construye la
imagen de dependencias (`sandbox_image_failed`), así que aquí no hay ninguna prueba verde que
presumir.

## Qué he construido

- Dominio puro `apps/api/opofuente/domain/convocation_registry.py`:
  - `FuenteOficial` (acto publicado: id, título, editor, identificador, URL canónica, nivel de
    autoridad, derechos, fecha).
  - `ConvocatoriaRegistrada` (código, cuerpo, grupo, administración, sistemas de acceso, plazas
    libres, plazas de promoción interna —nulas si el acto no las publica—, plazo en días hábiles,
    enlace oficial, procedencia y fecha de publicación) con `plazas_totales`.
  - `Procedencia(source_id, quote)`: sin cita literal no hay entrada.
  - `validate_registry`: coherencia de todo el registro (código slug único, textos no vacíos,
    sistemas no repetidos, plazas y plazo positivos, enlace https en `boe.es`, `source_id`
    existente y enlace idéntico al de su fuente).
  - `normalize`, `matches_profile`, `convocatorias_del_perfil` y `vincular_con_perfiles`.
- Carga `apps/api/opofuente/infrastructure/convocation_registry_loader.py`: pydantic con
  `extra="forbid"` (`schema_version: Literal[1]`), ruta por parámetro y valor por defecto
  `apps/api/opofuente/resources/convocation-registry.json`.
- Datos versionados de las tres convocatorias TIC del BOE de diciembre de 2025 (CSI A1, GSI A2 y
  TAI C1 de la AGE) con sus dos fuentes.
- Pruebas: `apps/api/tests/unit/test_convocation_registry.py` y
  `apps/api/tests/integration/test_convocation_registry.py`.

## Cómo fluye la información

1. El JSON versionado se lee una vez (`load_registry`), pydantic comprueba la forma y el dominio la
   coherencia. Cualquier incoherencia aborta la carga completa: nunca se publica un registro a
   medias.
2. `load_profiles` carga los perfiles curados y `vincular_con_perfiles` reparte el registro por
   cuerpo. Hoy solo `tai-age` tiene perfil, así que solo `tai-age-2025` queda vinculada; A1 y A2
   siguen visibles en el registro como cuerpos que la aplicación todavía no prepara.
3. Un cuerpo del registro sin perfil no es error ni se descarta el dato: el registro sirve también
   para detectar convocatorias nuevas.

## Ficheros y migraciones

- `apps/api/opofuente/domain/convocation_registry.py` (nuevo).
- `apps/api/opofuente/infrastructure/convocation_registry_loader.py` (nuevo).
- `apps/api/opofuente/resources/convocation-registry.json` (nuevo, datos BOE).
- `apps/api/tests/unit/test_convocation_registry.py` (nuevo).
- `apps/api/tests/integration/test_convocation_registry.py` (nuevo).
- Sin migración: no hay tabla en este alcance (se descartó la opción B con migración 0049).

## Patrones y decisiones aplicadas

- **Dominio puro sin pydantic** (`domain/system.py` ya lo documenta). El Dispatch pedía esquema
  pydantic en el dominio; se mantiene el esquema en infrastructure y el dominio en dataclasses
  congeladas, igual que `fixture_loader`/`profiles`. Lo que se gana es que el dominio siga sin
  dependencias de serialización y que el JSON tenga una sola puerta de entrada.
- **El registro vive en el paquete, no en `fixtures/`**: la política de escritura del workspace
  bloquea `fixtures/**` (intento rechazado con `Ruta fuera de las fuentes publicas o memoria
  autorizadas`). El coordinador autorizó `apps/api/opofuente/resources/`, que además es el sitio
  correcto: es dato de producto que lee la API, no fixture de pruebas.
- **Registro autocontenido**: las fuentes viven dentro del registro y no en `fixtures/profiles`,
  para no editar el manifiesto de perfiles (fuera de este slice).
- Nombres `RegistroDeConvocatorias` / `ConvocatoriaRegistrada` para no confundirlos con
  `domain.profiles.Convocation`, que es la convocatoria de examen con su programa y su estado.

## Seguridad y privacidad

- Sin credenciales, sin datos personales y sin contenido de terceros: solo metadatos públicos del
  BOE y una cita literal corta de cada acto.
- Toda entrada exige procedencia con cita; el enlace debe ser https del dominio `boe.es` y coincidir
  con la URL canónica de su fuente (además de `authority_tier = A` y
  `rights_status = reuse_with_conditions` en las dos fuentes cargadas).
- Ninguna escritura fuera del workspace ni sobre los originales; no se toca la carpeta de datos del
  usuario.

## Puertas ejecutadas y resultado

- `validar` puerta `648dc9aeae21` (unitarias de la API): **roja por entorno**, dos veces, sin
  colectar un solo test:
  `sandbox_image_failed: source_manifest_invalid: npm ci rechaza el protocolo workspace: de los
  package.json publicos; corrige coherentemente dependencia local y package-lock.json con el gestor
  registrado`. La imagen no se construye, así que ningún paso de pytest se ha ejecutado.
- `validar` puerta `9df85043f3a0` (`scripts/gates.ps1`): `capacidad ocupada:
  orca-docker-readiness`, no ejecutada.
- No existe guion público `_probar-*.mjs`, así que no hay puerta de integración que registrar.
- No se ha hecho commit, push ni despliegue.
- Decisión del coordinador sobre esta evidencia: el rojo de `648dc9aeae21` es **previo al árbol**
  (manifiesto/imagen del sandbox) y la contención de `9df85043f3a0` es capacidad
  (`orca-docker-readiness`), no fallo de pruebas; ninguna de las dos se cuenta como rojo del
  producto, pero tampoco autorizan a declarar verde. La reparación de `apps/web/package.json` y
  `package-lock.json` es de otra tarea: no está en este slice y no se ha tocado.

## Prueba manual

Cuando el entorno compile la imagen:

```powershell
uv run --frozen pytest apps/api/tests/unit/test_convocation_registry.py apps/api/tests/integration/test_convocation_registry.py -q
```

Y, con la API levantada, comprobar que `load_registry()` devuelve tres convocatorias y que
`vincular_con_perfiles` solo asocia `tai-age-2025` al perfil TAI.

## Limitaciones conocidas

- Para GSI (A2) y TAI (C1) las cifras están en una tabla del BOE y no forman una cadena contigua:
  la cita guardada es la frase que introduce los cuadros («Las plazas convocadas para los procesos
  selectivos especificados se ajustan a lo dispuesto en los siguientes cuadros:»). Las cifras son
  correctas y de la misma fuente, pero la cita no las contiene literalmente; un validador más
  estricto exigiría transcribir la tabla o citar por filas.
- No hay tabla, repositorio ni endpoint: el registro se lee del paquete. La persistencia y la
  exposición HTTP quedan para el alcance B que el coordinador decidió posponer.
- `plazo_dias_habiles` es el plazo de solicitudes del acto; no distingue turnos ni fechas de examen.
- La vinculación es por nombre de cuerpo normalizado; si dos cuerpos distintos comparten subcadena
  podrían cruzarse (hoy no ocurre con las tres entradas y el perfil TAI).

## Qué se rompe si cambias X

- Cambiar el `source_id` de una entrada sin actualizar las fuentes rompe la carga entera
  (a propósito).
- Añadir un campo al JSON sin añadirlo al esquema pydantic hace fallar la carga (`extra="forbid"`).
- Cambiar el nombre del cuerpo en el perfil o en el registro deshace el vínculo y la convocatoria
  deja de aparecer asociada al perfil.
- Mover el JSON fuera de `apps/api/opofuente/resources/` obliga a cambiar `default_registry_path` y
  a revisar el empaquetado del wheel.

## Qué criticaría un revisor senior

- Que la cita de A2/C1 no contiene las cifras y confía en el lector; conviene un `quote` por fila o
  un campo `quote_table` con la tabla transcrita.
- Que el registro se versiona a mano y nada comprueba contra el BOE en vivo: una convocatoria nueva
  no aparece hasta que alguien la añade.
- Que `load_registry` valida todo o nada: una entrada mala deja sin servicio a las buenas; quizá se
  prefiera cuarentena por entrada, con la entrada mala señalada.
- Que el alcance se quedó en lectura de fichero: sin persistencia no hay histórico ni detección de
  cambios entre convocatorias.
- Que no hay prueba ejecutada: todo lo anterior está justificado por lectura de código, no por
  evidencia del harness.
