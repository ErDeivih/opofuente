# Fuentes volátiles: la puerta 17 se comprueba por lo que el documento dice (octubre 2026)

## Qué he construido

Una tercera forma de verificar una fuente oficial, para las que el servidor sirve distintas en cada
descarga: el manifiesto puede marcar una fuente como `volatile` y entonces lo que se compara es el
`sha256` de su **texto visible** (`content_sha256`), no el de sus bytes. Con eso la puerta 17 vuelve a
poder ponerse verde —estaba en rojo por dos páginas de la Guardia Civil que cambian 22 líneas de
3.200 en cada petición, siempre identificadores que el gestor de contenidos inventa al renderizar— y
sin dejar de vigilar lo que importa: si la página deja de decir lo que los perfiles le atribuyen, la
puerta falla. La huella la rellena y la mantiene `--refresh-content`, que antes de escribir verifica
**las 71 citas** de los perfiles y no escribe nada si alguna ha desaparecido.

## Cómo fluye la información

1. `scripts/fetch-sources.ps1` descarga a `data/sources` (caché ignorada por git) y comprueba los
   `sha256` de bytes; para las fuentes `volatile` no compara bytes: imprime `TEXT` y remite a la
   herramienta, porque ese hash no puede coincidir nunca.
2. `build_profile_fixtures` (`load_manifest`) lee del manifiesto `sha256`, `volatile` y
   `content_sha256` y los lleva al `Source` de cada fuente.
3. `verify_sources` decide por fuente: si es volátil compara `content_fingerprint` (texto visible,
   sin comentarios, scripts, estilos ni etiquetas) con `content_sha256`; si no lo es, compara bytes.
   Una volátil **sin** huella no se da por buena: se dice que falta.
4. `verify_quotes` sigue igual para todas: cada cita de cada perfil tiene que aparecer en su fuente.
5. `--refresh-content` vuelve a calcular la huella de las volátiles y reescribe solo ese campo del
   manifiesto, con el formato exacto del fichero (`indent=2`, `ensure_ascii=False`, salto final).

## Patrones aplicados

- **Invariante comprobada, no documentada**: el texto que la puerta vigila es una decisión declarada
  en los datos (`volatile` en el manifiesto), no una excepción escondida en el código.
- **Revisión antes que escritura**: `refresh_content_hashes` verifica las citas primero y solo
  escribe si todas siguen apareciendo (mismo patrón que el constructor de fixtures, que no escribe si
  una cita falla).
- **Una sola fuente de verdad por comprobación**: la verificación por texto vive solo en Python; el
  script de descarga no intenta reimplementarla en PowerShell.

## Especificidades del framework

- `Set-StrictMode -Version Latest` (en `scripts/common.ps1`) convierte en error leer una propiedad
  que no existe: en `fetch-sources.ps1` hay que preguntar por `volatile` con
  `$source.PSObject.Properties['volatile']` antes de usarla.
- El manifiesto no es un fichero cualquiera: su formato (`json.dumps(..., indent=2)` + salto final)
  se conserva al reescribirlo para que el cambio de una huella no parezca la reescritura del fichero.

## Decisiones tomadas

- **Qué entra en la huella**: texto visible, sin comentarios, `<script>`, `<style>` ni `<noscript>`,
  sin etiquetas (ahí viven los identificadores volátiles) y con los espacios colapsados. Se descartó
  hashear el HTML normalizado (habría que decidir qué atributos son ruido, uno a uno) y se descartó
  versionar la copia de la página en `fixtures/` (más peso en el repositorio y duplica un documento
  que no es nuestro).
- **La huella se actualiza con una orden explícita**, no automáticamente al fallar: cambiar lo que la
  fuente dice es una decisión de una persona, y el error explica cómo tomarla.
- **No se toca nada más del manifiesto**: ni el `sha256` de bytes (queda como registro de lo que se
  descargó) ni las notas ni las fechas.
- **La PDF del BOCYL de Celador 2022 vuelve a coincidir** con su `sha256` al volver a descargarla: no
  se marca como volátil. (El repositorio ya documentaba que otro PDF del BOCYL sí es volátil; aquel
  se resolvió no conservándolo como fuente.)

## Qué se rompe si cambias X

- Si quitas `content_sha256` del manifiesto, la puerta vuelve a fallar y ahora **explicando** que falta
  la huella (no pasa en silencio).
- Si haces que `content_fingerprint` conserve las etiquetas, la huella vuelve a ser inestable y la
  puerta se rompe otra vez cada descarga.
- Si `refresh_content_hashes` escribiera sin verificar las citas, se podría «arreglar» la puerta con
  una fuente que ya no dice lo que los perfiles le atribuyen: la comprobación de citas es lo que
  impide que el refresco sea un permiso en blanco.

## Qué criticaría un revisor senior

1. **La huella de una fuente volátil solo se puede comparar con la última registrada**: no hay texto
   anterior guardado, así que el error no puede enseñar un *diff* de lo que cambió. Con las citas
   verificadas y el texto visible que se imprime al refrescar se puede revisar a mano, pero un
   revisor podría pedir más: guardar el texto de las volátiles en `fixtures/` (opción descartada
   aquí) daría un diff real.
2. **`volatile` es una decisión por fuente y a mano**, sin ninguna comprobación de que de verdad haga
   falta: marcar como volátil una fuente estable debilitaría la puerta (dejaría de mirar sus bytes)
   sin que nada lo impidiera. Lo único que lo frena es la revisión del cambio en el manifiesto.
