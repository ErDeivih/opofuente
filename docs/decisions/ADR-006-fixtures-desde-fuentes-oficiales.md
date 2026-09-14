# ADR-006 — Fixtures de perfil desde fuentes oficiales y condiciones de uso

- **Estado:** aceptada y ratificada por el propietario el 14/09/2026, **exclusivamente para el
  alcance actual**: aplicación local, personal y repositorio privado. DEBT-003 sigue abierta como
  barrera previa a cualquier publicación, distribución, despliegue en nube o acceso de terceros.
- **Fecha:** 14 de septiembre de 2026
- **Ámbito:** procedencia de datos y derechos de S01
- **Asunto:** cómo se construyen los perfiles TAI 2025 y Guardia Civil 2026, qué se versiona y con
  qué condiciones de uso

## Contexto

`15_OFFICIAL-PROFILES-AND-SOURCE-MANIFEST.md` exige que los perfiles se siembren desde fuentes
oficiales verificadas, registrando «URL canónica, fecha, derechos y hash», y `11_IMPLEMENTATION-SLICES`
(S01) pide «fixtures versionados TAI-2025 y GC-2026 desde fuentes oficiales». `09_SECURITY-PRIVACY-
AND-RIGHTS.md` §8 obliga a conservar atribución, URL, fecha y licencia, y a no publicar ni compartir
material restringido.

Al descargar las fuentes se comprobó que **las condiciones de uso de las dos fuentes no son las
mismas**:

| Fuente | Condiciones verificadas |
|---|---|
| BOE (Agencia Estatal Boletín Oficial del Estado) | Reutilización **autorizada** con condiciones: citar la fuente con enlace a <https://www.boe.es>, no alterar el sentido de la información, no indicar ni insinuar carácter oficial, conservar la fecha de actualización, y citar «Basado en datos de la Agencia Estatal Boletín Oficial del Estado» en obras derivadas. |
| Portal de la Guardia Civil (temario oficial) | «La licencia de uso de cualquier contenido de este Portal otorgada al usuario se limita a la descarga por parte del usuario de dicho contenido y al **uso privado** del mismo (…). Por ello, el uso, reproducción, distribución, comunicación pública o cualquier otra actividad similar o análoga al margen de lo anterior queda totalmente prohibida salvo que medie autorización expresa de la Dirección General de la Guardia Civil.» |

Ambas citas, sus URL y sus hashes están en `fixtures/profiles/manifest.json` y en
`data/sources/` (copia local, ignorada por git).

## Decisión

1. **Manifiesto con verificación de hash.** `fixtures/profiles/manifest.json` registra, por fuente:
   identificador, título, organismo, URL canónica, URL consultada, formato, fecha de publicación,
   fecha de consulta, `sha256`, ruta local, nivel de autoridad, estado de derechos, nota de derechos
   y URL del documento de condiciones. La herramienta de construcción **verifica el `sha256`** antes
   de leer cada fuente y falla si no coincide.
2. **Fixtures derivados, no copiados.** Se versionan dos ficheros por perfil: el **perfil curado**
   (identidad, convocatoria, plazas y reglas de examen, cada valor con una cita literal de la fuente)
   y el **programa generado** (bloques, temas y epígrafes extraídos del documento oficial). La
   herramienta comprueba que **cada cita existe literalmente** en la fuente antes de escribir nada:
   una cifra sin cita no puede entrar en el fixture.
3. **Los documentos originales no se versionan.** Se descargan a `data/sources/` (ignorado por git)
   con `scripts/fetch-sources.ps1`, que vuelve a comprobar los hashes del manifiesto.
4. **Atribución visible en la aplicación.** Toda pantalla que muestre el programa o las reglas
   muestra también la fuente, su URL, su fecha de publicación y su condición de uso. La interfaz
   distingue «oficial (procedencia confirmada)» de «publicación oficial de OpoFuente» —que no
   existe— y avisa de que OpoFuente no es un organismo oficial.
5. **Uso privado.** El producto es local, de un solo usuario, sin nube, sin comunidad y sin
   redistribución (`01_PRODUCT-SPEC` §10, `09` §8). Ese es exactamente el uso que la licencia del
   portal de la Guardia Civil permite. Por eso el fixture del temario **solo puede existir mientras
   el repositorio y la aplicación sigan siendo privados**; la obligación de retirarlo o de pedir
   autorización expresa antes de publicar o distribuir queda registrada como DEBT-003.

## Alternativa descartada (y cuándo habría que volver a ella)

No incluir el temario de Guardia Civil en el repositorio y exigir su importación manual, como prevé
`10_TEST-PLAN` §2 para fuentes sin copia permitida. Se descarta porque el producto existe para
estudiar ese programa (J2), la licencia sí cubre el uso privado, y hacerlo a mano convertiría una
tarea mecánica y verificable en trabajo del usuario. El propietario **ratificó esta alternativa** el
14/09/2026 para el alcance actual: si en algún momento hay que publicar el repositorio, distribuir la
aplicación o dar acceso a terceros, se aplica la importación manual del PDF del usuario (o se pide
autorización expresa), tal como exige DEBT-003.

## Comprobaciones de derechos hechas por el propietario (14/09/2026)

- **BOE:** su aviso legal permite la reutilización comercial **y** no comercial con atribución y las
  demás condiciones; la implementación las respeta (cita, enlace, sin carácter oficial).
- **Guardia Civil:** el temario puede utilizarse privadamente, pero su aviso legal prohíbe
  reproducirlo o distribuirlo sin autorización. De ahí el alcance ratificado.
- **Temario de 2024 aplicado a la convocatoria de 2026:** la página oficial del procedimiento
  mantiene los 25 temas y declara que el temario permanece entre convocatorias salvo modificación
  publicada con antelación (nueve meses). Queda justificado su uso para 2026.

## Consecuencias

- Cualquier cambio de una fuente oficial (nueva versión del temario, corrección de erratas) se
  detecta: el hash deja de coincidir y la puerta de fixtures falla.
- El repositorio contiene texto oficial del temario de GC. Es un dato del que depende DEBT-003, que
  sigue abierta como barrera previa a publicar o distribuir.
- Las cifras del examen y del programa son auditables: cada una apunta a su cita y su documento.

## Reversión

Borrar `fixtures/profiles/*curriculum.json` del temario de GC y sustituir la siembra por la
importación manual del PDF del usuario. El resto del paquete (manifiesto, reglas del BOE, modelo,
API y pantalla) no cambia.
