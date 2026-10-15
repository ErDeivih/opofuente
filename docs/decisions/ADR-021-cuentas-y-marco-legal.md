# ADR-021 — Cuentas propias, derivador de contraseñas y el marco legal del despliegue

- **Fecha**: 15 de octubre de 2026
- **Estado**: aceptada
- **Ámbito**: §8 a §11 del objetivo vivo (`docs/OBJETIVO-VIVO-2026-10.md`)
- **Decide**: el agente codificador, por delegación del propietario (regla de decidir lo reversible y
  apuntarlo). No hay decisión irreversible: las cuatro banderas nacen apagadas.

## Contexto

El objetivo vivo pide que esto sea una plataforma desplegable: cuentas con sesión propia, páginas
legales con consentimiento de verdad, analítica sin identificadores de terceros y el hueco de los
pagos. Y pone por encima de todo una regla: **el alumno que ya existe —uso local, sin cuenta— tiene
que seguir funcionando igual**, con todo lo nuevo detrás de una bandera apagada por defecto y sin
contratar nada.

Antes de esta decisión, la aplicación no tenía **ninguna** forma de autenticación (era una aplicación
de un solo usuario en loopback), no tenía ningún derivador de contraseñas y no tenía ninguna noción
de consentimiento.

## Decisiones

### 1. Dependencia nueva: `argon2-cffi`

**Se añade `argon2-cffi` (argon2id)** como único derivador de contraseñas. No es una elección de
estilo: el proyecto no traía ninguno, y guardar una contraseña con un digest rápido (`hashlib.sha256`)
es exactamente lo que no se puede hacer. Argon2id consume memoria a propósito, ganó la Password
Hashing Competition y es lo que recomienda el NIST en su SP 800-63B.

El coste se deja **configurable** (`OPOFUENTE_PASSWORD_HASH_*`) con los valores por defecto de la
biblioteca: así la suite puede bajarlo —no se está midiendo el tiempo, se está midiendo qué se
guarda— sin que producción deje de derivar en serio.

### 2. La sesión es propia, con cookie `HttpOnly`

**No se contrata ningún proveedor de identidad.** La sesión es de esta aplicación: un testigo de 256
bits que viaja en una cookie `HttpOnly` + `SameSite=Lax` (`Secure` configurable, apagado porque se
sirve por `http://127.0.0.1`) y del que la base guarda **solo su SHA-256**.

`SameSite=Lax` es suficiente aquí porque la web y la API son **mismo sitio** (dos puertos de
`127.0.0.1`), y la defensa de escritura sigue siendo la comprobación de `Origin` que ya existía.
`allow_credentials` del CORS **sigue a la bandera de las cuentas**: con las cuentas apagadas se queda
en `False`, que es como estaba, así que ninguna petición de hoy cambia de comportamiento.

### 3. El dueño del progreso, sin migrar el estudio

El progreso ya se firma con `owner_id` desde la migración `0027`. El dueño de una cuenta es
`acct:<resumen-de-la-dirección>`; el de quien estudia sin cuenta sigue siendo `local`, que es el valor
de siempre. Es una costura, no una migración: **no se toca ni una columna de las tablas del estudio**.

### 4. La bandera del §9, y por qué hay cuatro y no tres

El §B del objetivo nombra tres banderas (`ACCOUNTS`, `ANALYTICS`, `PAYMENTS`). Se añade una cuarta,
`OPOFUENTE_LEGAL_ENABLED`, porque el §9 —páginas legales y consentimiento— es tan nuevo como los
otros tres y sin bandera cambiaría la aplicación por defecto (aparecería un aviso de cookies a quien
hoy no tiene ninguno). Y se ata: **la analítica y los pagos exigen el marco legal encendido**, porque
la primera no puede contar sin consentimiento —y el consentimiento se pide con las rutas del §9— y
los segundos meterían datos personales en un tercero que la política de privacidad tiene que declarar
**antes** de que ocurran. Encender una sin la otra falla al arrancar, con el motivo escrito.

### 5. La puerta de las rutas cierra por defecto

Con las cuentas encendidas, la API exige sesión para **todo** lo que no esté en una lista corta de lo
público (salud, alta, acceso, recuperación, textos legales, contadores y **la zona de estudio
entera**). La alternativa —una lista de lo prohibido— habría que mantenerla a mano y el día que se
añadiera una ruta de administración sin apuntarla allí, la puerta quedaría abierta **en silencio**.

La zona de estudio queda abierta a propósito, con cuentas o sin ellas: es la regla que manda en el
bloque. Con la bandera apagada la puerta ni se ejecuta.

### 6. La recuperación de contraseña sin correo contratado

No se contrata ningún servicio de correo y **no se simula que exista**. El enlace de recuperación se
deja en `datos/recovery/`, dentro del árbol de datos, para que lo lea el titular; `mail_enabled=1`
**falla al arrancar** mientras no haya proveedor, porque encenderlo dejaría a quien no puede entrar
esperando un mensaje que nadie va a mandar. La respuesta de la API es la misma exista o no la
dirección, así que por ahí tampoco se puede averiguar quién tiene cuenta.

El enlace **no se registra en el log y no viaja en ninguna respuesta**: las dos cosas están prohibidas
por las reglas del proyecto.

### 7. La analítica: propia, agregada y con vocabulario cerrado

Se monta una analítica **propia**, no se deja solo el enganche. El §10 permite no montar ninguna, pero
la pregunta «¿qué pantallas se usan de verdad?» se responde con veinte líneas y sin ella se decide a
ojo.

Se monta con un **vocabulario cerrado**: dos tipos de suceso (`page_view`, `action`) y una lista de
etiquetas. El esquema no tiene cuenta, ni sesión, ni dirección, ni navegador, ni texto libre, así que
**no hay nada que anonimizar porque nunca se guarda nada personal**. La comprobación del permiso la
hace el servidor en cada petición: una pantalla que decidiera si mandar el suceso sería una promesa.

### 8. Los pagos: el hueco y la propuesta, sin contratar nada

Solo la bandera apagada, los huecos de plan y la propuesta escrita (Stripe como recomendada, Paddle y
Redsys como alternativas, con qué habría que contratar y qué datos saldrían). **Las comisiones van
marcadas como no verificadas** porque las páginas de precios de los proveedores se sirven con
JavaScript y no se pudieron leer: una cifra que va a un documento y no se ha medido se declara.

## Consecuencias

- **Nada de esto está encendido por defecto.** Con las cuatro banderas a 0 el árbol se comporta como
  `e03b354` para quien estudia sin cuenta, y hay una prueba que lo comprueba.
- **El código entra con 18/18** y su batería; las pruebas que fallan antes y pasan después están en
  `apps/api/tests/integration/test_plataforma_cuentas.py`, `test_plataforma_legal.py` y
  `apps/api/tests/integration/test_temporal_de_datos.py`.
- **Lo que queda fuera y hay que contratar** está en `PARA-EL-PROPIETARIO.md`: correo (para dejar de
  escribir el enlace en un fichero), pasarela de pago y `Secure` de la cookie (para servir por HTTPS).
- **Vuelta atrás**: borrar la migración `0039` se lleva las seis tablas y con ellas las cuentas. El
  progreso firmado como `acct:<…>` no se borra al volver atrás: se queda sin cuenta que lo reclame, y
  eso está dicho en `PARA-EL-PROPIETARIO.md` en vez de borrarlo por sorpresa.
