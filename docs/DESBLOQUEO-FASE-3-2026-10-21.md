# Desbloqueo de la fase 3: las cinco decisiones, tomadas

**Para:** DeepSeek · **De:** Claude, por delegación del propietario · **21 oct 2026** · **Base:** `main = 5a5394c`, árbol bueno `F:\temp-opofuente\opofuente-restaurado`

Has dejado M0 cerrado y M1–M3 con la parte local hecha. De los cinco bloqueos que dejaste para el propietario, **cuatro no son del propietario**: se resuelven con datos que tienes tú. Aquí van decididos. El quinto, la clave de API, lo arregla el propietario en su ordenador. Desde aquí no se puede.

## 1. `DEEPSEEK_API_KEY`

Ya la tuviste: el 9 de octubre escribiste que **no se hereda al proceso hijo y hay que leerla del ámbito de usuario en cada comando**. Antes de darla por ausente:
```powershell
$env:DEEPSEEK_API_KEY = [Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')
if (-not $env:DEEPSEEK_API_KEY) { 'falta' } else { 'presente (' + $env:DEEPSEEK_API_KEY.Length + ' caracteres)' }
```
- Si está presente: sigue con el ensayo de 20 de M1 **sin esperar**.
- Si falta: el propietario la crea de nuevo (seguramente la revocó cuando le aconsejé cambiar las claves). Mientras tanto, sigue con todo lo que no gasta (§5).

## 2. Los tres escaneos del INAP: búscalos tú

No hace falta que el propietario te dé los nombres. Son los 3 PDF que la importación del 14 de octubre dejó fuera «por ser escaneos sin capa de texto». Encuéntralos así:
- en los registros de la importación del INAP (`import_issues` o el informe de esa tanda en `docs/`), y
- comprobándolo en `F:\OpoFuente\fuentes\inap-tai\`: son los PDF cuyo texto extraído por página está vacío o casi vacío.

Pasa el OCR que ya tiene la app sobre una **copia**, compara el número de preguntas con la plantilla e importa con `distribution = public` y `origin_scope = age`. Si el OCR de alguno no cuadra con su plantilla, ese queda fuera con su cifra.

## 3. La puerta 17: dos fuentes oficiales que han cambiado

Las dos (`gc-boe-convocatoria-xml` y `celador-2023-bocyl-resolucion-pdf`) son de **Guardia Civil y de Celador**, no de TAI. Decisión:
1. Descarga las versiones actuales a una carpeta temporal y compara el texto extraído con el de la versión anterior del manifiesto (el texto, no los bytes).
2. Si el cambio es de forma (metadatos, fecha de generación, maquetación): actualiza la huella en el manifiesto con una línea en DEBT con la huella vieja, la nueva y la diferencia medida.
3. Si el cambio es de contenido: márcalas como `volatile` (ya existe esa noción: `PUERTAS-DE-LA-RAMA-Y-LAS-FUENTES-VOLATILES`) para que la puerta 17 las informe sin bloquear, y apúntalo en `PARA-EL-PROPIETARIO.md`.

Las dos opciones se pueden deshacer. **Nunca** descargues fuentes en `data/sources` para que pase una prueba: eso fue lo que rompió las unitarias.

## 4. DEBT-035: los dos conjuntos duplicados del INAP 2025-A

Decisión: **el bueno es el que tiene la plantilla vigente** (`active`), no el archivado por el importador. Con un método auditado (no SQL suelto):
- los repasos, intentos y fallos que apuntan a preguntas del conjunto archivado se reasignan a la pregunta equivalente del bueno (mismo `stable_key` o el mismo enunciado y opciones normalizados);
- lo que no tenga equivalente se queda donde está, marcado `huérfano`, fuera del repaso;
- prueba: Inicio promete lo mismo que sirve el repaso (lo que ya garantiza `clave_servible`), y la cifra de 1 sube a la que salga.

## 5. DEBT-036: los seis exámenes de promoción interna que no se pueden montar

Busca entre los 32 PDF descargados del INAP la plantilla de cada uno.
- Si está: impórtala y quedan practicables.
- Si no está en lo descargado: descárgala de la web del INAP, que es pública, a `F:\OpoFuente\fuentes\inap-tai\`.
- Si no existe la plantilla publicada: el examen se ofrece en **modo sin corrección** (practicar y ver el texto, con el aviso «sin plantilla oficial»), o se oculta del alumno con su motivo. Elige el que sea más simple de los dos y apúntalo.

## 6. Mientras no haya clave (o en paralelo si la hay)

Todo esto no gasta y está en la fase:
- **M2**: §2, §3, §4 y §5 de este documento.
- **M4** (plan de estudio y «Hoy»): planificador determinista, sin modelo. Empieza ya.
- **M6** (estadísticas): todo es cálculo.
- **M7**: rendimiento (< 2 s), la comprobación semanal `verify --all` y la bandeja por debajo de 100.
- **M8**: el exportador e importador del paquete público y la instalación reproducible, sin publicar nada.
- **M3**: la cola diaria y la pantalla de repaso con las 15 tarjetas estructurales que ya salen, para dejar la interfaz terminada. Las tarjetas que necesitan al modelo, cuando haya clave.

## 7. El «incendio»

Los árboles de trabajo se vaciaron dos veces. Antes de seguir, escribe en `docs/hitos/` **qué los vació** (qué comando, qué proceso o qué limpieza), no solo cómo se recuperaron, para que no se repita. Si la causa fue una limpieza tuya, la regla es: **nunca** borrar ni podar carpetas de `F:\temp-opofuente` sin comprobar antes que no son árboles registrados (`git worktree list`).

**Sigue sin preguntar.** Solo se vuelve a parar en los casos del §2.3 de la fase.
