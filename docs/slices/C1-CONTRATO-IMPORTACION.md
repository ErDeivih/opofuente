# C1 Informática: contrato de importación y puerta de forma

Estado: **implementado y con puerta verde sobre la forma**. NO importado, NO verificado
contra la base real y NO verificado contra fuentes oficiales.

## Qué he construido

1. `apps/api/opofuente/resources/c1-informatica-manifest.json`: manifiesto declarativo
   (`schema_version: 1`, `kind: opofuente.import-contract`) que fija el hueco de catálogo de
   la oposición C1 Informática y el contrato con el que el custodio la importará:
   - 5 bloques × 8 temas comunes (40 temas), 6 partes de estructura por tema, 10–20
     preguntas por tema, patrón de código `^C1-I-(\d{2}|L-[A-Z]{2,4}-\d{2})$`.
   - Temas locales separados de los comunes (`C1-I-L-EST-01`, `C1-I-L-CYL-01`) para que un
     ámbito no contamine el temario común.
   - Dos ámbitos de convocatoria (`estado` → BOE, `cyl` → BOCYL), cada uno con sus fuentes y
     su regla de plazo (20 días hábiles desde el día siguiente a la publicación, festivos
     excluidos, etiqueta `estimado` y `official_overrides_estimate: true`).
   - Cinco fuentes declaradas como huecos (`status: placeholder`, `expected_sha256: null`),
     con ruta esperada relativa a `import_rules.target_data_dir`.
   - Reglas de importación duras: escritura solo en `F:/OpoFuente/datos`, copia previa,
     `integrity_check`, dry-run por defecto, confirmación explícita, nunca borrar,
     idempotencia `upsert_by_code`, aborto ante conflicto de código y informe obligatorio.
   - Contrato de panel: filtros, columnas y regla de plazo estimado.
2. `apps/api/opofuente/tools/_probar-contrato-c1.mjs`: puerta Node sin dependencias que valida
   forma y coherencia interna del manifiesto (esquema estricto por lista de claves, unicidad y
   rango de posiciones, patrón de códigos, referencias cruzadas fuente↔ámbito↔tema local,
   enums de autoridad/derechos, rutas relativas sin `..` ni unidad, booleanos de seguridad y
   coherencia panel↔plazo). 654 comprobaciones.

El manifiesto es **sintético a propósito**: todos los títulos llevan `[SINTÉTICO]` y
`statement` lo declara. No se ha inventado ningún contenido legal, plazo publicado ni cuerpo
convocado, porque no hay fuente oficial disponible en este workspace ni encargo con los 40
temas reales.

## Cómo fluye la información

1. El custodio sustituye cada `[SINTÉTICO]` por el título oficial y rellena
   `expected_relative_path`/`expected_sha256` de cada fuente con el acto descargado.
2. Cambia `synthetic` a `false` y cada fuente obligatoria a `status: verified`.
3. La puerta se vuelve más estricta automáticamente: con `synthetic: false` exige `verified`
   y `sha256` en toda fuente obligatoria.
4. El importador (fuera de este slice) lee el manifiesto, hace copia verificada con
   `integrity_check`, ejecuta en dry-run, compara por `(convocation_id, code)` y solo escribe
   dentro de `target_data_dir` tras confirmación.
5. El panel consume el contrato `panel` para listar convocatorias y estimar plazos; un plazo
   oficial publicado siempre prevalece sobre el estimado.

La puerta nunca abre la base real ni `F:/OpoFuente/datos`: si el directorio no está montado
en el sandbox, cada fuente produce un aviso `external_not_verified` y la puerta no falla por
ello (no se puede confundir «no accesible» con «incorrecto»).

## Ficheros y migraciones

- Nuevo: `apps/api/opofuente/resources/c1-informatica-manifest.json` (dato versionado, sin
  secretos ni contenido de terceros).
- Nuevo: `apps/api/opofuente/tools/_probar-contrato-c1.mjs` (guion público `_probar-*`).
- Nueva puerta registrada: `0de224b1a0c2` («Prueba _probar-contrato-c1»).
- Sin migración de esquema y sin cambios en la base: este slice solo declara el contrato.

Nota de ubicación: la política de escritura de este worker deniega `fixtures/**`, `scripts/**`
y la raíz del repositorio, así que el guion vive en `apps/api/opofuente/tools/` en lugar de la
raíz. El contenido es independiente de la ruta (resuelve la raíz subiendo cuatro niveles).

## Patrones y decisiones aplicadas

- Un único artefacto ejecutable como esquema: el `.mjs` es la fuente de verdad formal; no se
  duplica en un `schema.json` que se desincronice.
- `schema_version: 1` y `kind` explícito, igual que `convocation-registry.json` y el loader de
  convocatorias existente.
- Rutas de fuentes **relativas** a `target_data_dir`, nunca rutas absolutas del host, para que
  el manifiesto no filtre ni dependa de la máquina del custodio.
- Separación estricta temario común / temas locales; los locales solo se enlazan desde su
  ámbito y la puerta exige exactamente una referencia.
- Plazo tratado como estimación: `label: estimado` y `official_overrides_estimate: true` son
  obligatorios, de modo que el panel no pueda presentar un cálculo propio como plazo oficial.
- Enums del dominio reutilizados (`authority_tier`, `rights_status`, grupo `C1`).

## Seguridad y privacidad

- No hay credenciales, rutas de usuario ni datos personales en el manifiesto ni en el guion.
- El guion no imprime contenido de fuentes: solo rutas y hashes; no escribe nada.
- `never_delete: true`, `originals_read_only: true`, `backup_before_write: true` e
  `integrity_check_before_write: true` son obligatorios y la puerta falla si desaparecen.
- `target_data_dir` debe ser una ruta absoluta de unidad/UNC y no puede apuntar al workspace
  del producto.
- Toda fuente exige `rights_status` del enum y `authority_tier`; con `synthetic: false` no se
  admite una fuente obligatoria sin `verified` y `sha256`.
- El contenido importado sigue siendo no confiable; este slice no lo ejecuta ni lo interpreta.

## Puertas ejecutadas y resultado

- `0de224b1a0c2` — `_probar-contrato-c1.mjs` sobre el árbol entregado: **verde** (exit 0).
  Resultado: `ok: true`, `checks: 654`, `topics: 40`, `local_topics: 2`, `scopes: 2`,
  `sources: 5`, `checksums_verified: 0`, `external_not_verified: 5`, `errors: []`.
  `manifest_sha256: 1369500713ce5025c63efa1a49a0a9a4abb30a764d7b30fc8e2ac6be4612a8d6`.
  Evidencias nativas de dos ejecuciones verdes encadenadas:
  `3248f3b1b028bca8818c901d8322471eefcce83526afcf168126631649300c49` (árbol previo a este
  documento) y `65f200f4ffec955ca20a42cf30ea191cd45cb7857ecc997b2f432e8e2b4993ce` (árbol con
  este documento, `tree_hash` `0e473e95e9bb67446d7454a6afca0e846666a2dcc6d489328833873b8d0b7acc`).
  La puerta se reejecuta sobre el árbol final del cierre y esa última evidencia verde es la que
  vale para la candidata.
- Puertas preexistentes `5a471fa62eaf`, `648dc9aeae21` y `9df85043f3a0`: **no verdes**, por
  causas de entorno ajenas a este slice (venv sin `argon2-cffi>=25.1.0`; sandbox sin
  `Get-NetTCPConnection` → `sandbox_image_failed`). No se han relajado ni modificado.
- No se ha ejecutado importación real, ni `pytest`, ni build, ni E2E: no hay shell en este
  worker y la base real está fuera del sandbox. No se declara nada de eso como probado.

## Prueba manual

1. Revisar el manifiesto: `synthetic: true`, títulos con `[SINTÉTICO]`, fuentes `placeholder`.
2. Ejecutar la puerta registrada `0de224b1a0c2` con `validar` (proyecto `opofuente`).
3. Romper a propósito una invariante (p. ej. borrar un tema de un bloque o cambiar
   `never_delete` a `false`) y comprobar que la puerta sale con código 1 y mensaje concreto;
   restaurar después.
4. Si hay acceso al host: poner `synthetic: false` sin rellenar fuentes y comprobar que la
   puerta falla exigiendo `verified` + `sha256`.

## Limitaciones conocidas

- **No contiene los 40 temas reales**: son huecos sintéticos. El encargo con la lista validada
  y la sección 0 no está disponible; el coordinador indicó no inventar contenido legal.
- La importación real y la verificación de checksums contra `F:/OpoFuente/datos` quedan
  pendientes para el custodio/CI aislado. `external_not_verified: 5` lo refleja.
- El panel es solo contrato declarativo: no hay endpoint ni UI nuevos en este slice, y el
  cálculo de días hábiles no se ha implementado.
- La observación de los 401 `curriculum_nodes` es una nota del manifiesto
  (`checked_by_this_gate: false`), no una comprobación de esta puerta.
- El guion no está en la raíz por la política de escritura del worker; si el repositorio exige
  `_probar-*.mjs` en raíz, basta moverlo (no cambia su comportamiento).
- Fichero accidental a eliminar antes de commitear: `docs/slices/_tmp-escritura.md` (sonda de
  permisos de escritura; el worker no tiene herramienta de borrado).

## Qué se rompe si cambias X

- Cambiar el patrón de códigos sin actualizar `curriculum.code_pattern` y los códigos: la
  puerta falla y el importador podría duplicar nodos.
- Quitar `never_delete`/`originals_read_only`/`backup_before_write`: la puerta falla; sin ella,
  un importador futuro podría borrar o sobrescribir originales.
- Cambiar `target_data_dir` a una ruta del repositorio: la puerta falla; el riesgo es escribir
  datos reales en el árbol versionado.
- Poner `synthetic: false` sin verificar fuentes: la puerta falla; si se saltara, se
  importarían huecos como si fueran temario oficial.
- Cambiar el `bulletin` de una fuente sin actualizar su ámbito: la puerta detecta el
  desajuste fuente↔ámbito.

## Qué criticaría un revisor senior

- Que el manifiesto no pueda validarse contra la base real ni contra la fuente oficial en este
  entorno: la puerta acredita forma, no verdad documental.
- Que 40 temas y 5 bloques se declaren como decisión del contrato sin la fuente que los fija;
  el riesgo es fosilizar una estructura equivocada cuando llegue el temario oficial.
- Que el panel y el cálculo de plazos sean solo contrato: falta la implementación y sus tests.
- Que el guion viva en `apps/api/opofuente/tools/` y no en la raíz, contra la convención.
- Que el `statement` y los `[SINTÉTICO]` dependan de disciplina humana: nada impide rellenar
  títulos sin fuente y dejar `synthetic: true`. Una comprobación de URL oficial por fuente
  ayudaría.
