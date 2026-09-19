# Manual de operación — OpoFuente

Esta guía es para **usar y mantener** la aplicación, no para desarrollarla. Todo lo que dice aquí se
puede comprobar desde la propia interfaz o desde los comandos del repositorio, y lo que no está
comprobado se dice.

---

## 1. Arrancar y parar

```powershell
# Instalación limpia (una vez)
git clone <url> F:\EspacioCodigo\opofuente
cd F:\EspacioCodigo\opofuente
./scripts/install.ps1

# Arrancar todo (API en 127.0.0.1:8765 y web en 127.0.0.1:5173)
./scripts/dev.ps1
```

La aplicación es **local y de un solo usuario**: escucha solo en loopback y no tiene login. No la
publiques en ninguna red: el host no loopback falla al arrancar a propósito.

Para parar: `Ctrl+C` en la ventana donde corre `dev.ps1`. Los trabajos de la bandeja viven en la base
de datos, así que un corte no pierde nada: al volver a arrancar, lo que quedó a medias se recupera.

## 2. El día a día

| Quiero | Dónde |
|---|---|
| Meter material | **Bandeja** → inventariar una carpeta (en lectura) o importar una copia |
| Pegar texto o traer una URL | **Bandeja** → pestaña correspondiente |
| Revisar lo que el programa ha propuesto | **Revisión** (se entra desde la bandeja) |
| Leer un documento y copiar una cita | **Biblioteca** → abrir el documento → Lector |
| Practicar o hacer un examen | **Estudiar** |
| Repasar lo fallado | **Errores** |
| Buscar o preguntar al corpus | Buscador de la cabecera |
| Ver cambios de material y qué depende de ellos | **Cambios** |
| Copias, almacén, proveedores y diagnóstico | **Ajustes** |

**Nada de esto mueve, renombra ni borra tus originales.** La importación copia por contenido (SHA-256),
así que dos ficheros idénticos son un solo artefacto con dos orígenes, y el original se queda donde
estaba. La única operación que retira algo es la de **Ajustes → Qué se puede retirar**, y solo retira
material que ya no sostiene ninguna cita ni cobertura, con confirmación explícita.

## 3. Copia de seguridad

**Ajustes → Copia y restauración → Hacer una copia ahora.** Una copia contiene:

- la base de datos (instantánea coherente, tomada con la API de respaldo de SQLite);
- el material copiado (`artifacts/`);
- el texto extraído y las representaciones (`extracted/`);
- los perfiles oficiales sembrados (`fixtures/`);
- un **manifiesto** con la revisión de esquema, la fecha y el hash de cada fichero.

Lo que **no** entra: las copias anteriores (no se copia una copia dentro de otra), los temporales, los
registros y el índice vectorial (que está vacío porque no hay proveedor de embeddings).

**Verificar** una copia comprueba hash y tamaño de **cada** entrada y devuelve la lista de problemas.
Sin verificar no se restaura: la restauración comprueba la copia entera antes de tocar nada.

### Restaurar

1. **Previsualizar**: dice qué se va a sustituir, cuánto ocupa, si hay espacio y si la copia es de una
   revisión más nueva que el programa (en ese caso **no** se puede restaurar: actualiza primero).
2. **Restaurar esta copia**: hace una **copia previa automática** de lo que hay, extrae a un
   directorio temporal, intercambia y comprueba la base restaurada.

Si algo falla a mitad, la restauración **se deshace**: el material anterior se queda en
`<área>.restore-old` dentro del árbol de datos y el servicio dice dónde. Recuperación manual:

```powershell
# Con la aplicación parada, dentro del directorio de datos:
Move-Item artifacts.restore-old artifacts -Force
Move-Item opofuente.sqlite3.restore-old opofuente.sqlite3 -Force
```

Cuando una restauración termina bien, esos puntos de retorno se retiran solos.

## 4. Diagnóstico

**Ajustes → Diagnóstico y registros saneados → Preparar el diagnóstico en texto.** El texto está
sanitizado: no lleva contenido, ni claves, ni rutas completas (van abreviadas), y las líneas del
registro pasan por el mismo saneado que los logs. Es lo que se pega en una incidencia.

Para verlo por API:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/v1/diagnostics | ConvertTo-Json -Depth 5
(Invoke-WebRequest http://127.0.0.1:8765/api/v1/diagnostics/text).Content
```

Los registros viven en `<datos>\logs\opofuente.log`, en JSON, rotados por tamaño. **Nunca** contienen
el texto importado, las preguntas privadas, los prompts completos, las respuestas personales, las
rutas absolutas ni las claves: el formateador solo copia una lista blanca de campos.

## 5. Si algo va mal

| Síntoma | Qué mirar |
|---|---|
| «No está listo» en la cabecera | Ajustes → capacidades, o `GET /api/v1/health/ready`: cada comprobación dice qué falla |
| Una imagen no tiene texto | Es lo esperado: el OCR **no** está implementado. La entrada queda `ocr_pending` con su aviso |
| La búsqueda no encuentra algo que debería | Comprueba el estado del corpus (una versión `candidate` o `superseded` no se recupera por defecto) y, si el índice se quedó atrás, **Ajustes → Rehacer el índice** |
| El disco se llena | Ajustes → Uso del almacén y Qué se puede retirar |
| Una copia no se puede restaurar | Verifícala: el motivo se dice. Si es de una revisión más nueva, actualiza el programa |
| Corrupción de la base | Para el proceso (no dejar que siga escribiendo), copia `opofuente.sqlite3` y el manifiesto a mano, y restaura desde la última copia verificada |

## 6. Qué **no** hace la aplicación (y lo dice)

- **OCR**: no está implementado. Una imagen o un PDF escaneado quedan pendientes con su aviso.
- **Modelo de lenguaje e índice vectorial**: no hay proveedor. La búsqueda es léxica y la respuesta se
  compone del propio corpus, citando cada afirmación.
- **Calificación oficial 0–50 y apto/suspenso**: sin baremo oficial importado no se inventan; se da la
  puntuación directa por partes.
- **Simulacro y examen diagnóstico**: no existen; pedirlos responde 409 con el motivo.
- **Borrado de material**: el producto archiva y excluye; no borra. La retirada de la sección de higiene
  solo toca lo que ya no sostiene nada.
- **Múltiples usuarios y acceso remoto**: fuera de alcance a propósito.

## 7. Release local

```powershell
./scripts/build.ps1      # construye backend (sdist+wheel) y frontend (dist/)
./scripts/release.ps1    # empaqueta una release local en dist/release/
```

La release local incluye los artefactos construidos y un `RELEASE.md` con la versión, la revisión de
esquema y la lista de comprobaciones ejecutadas. No se publica nada a ningún sitio: el repositorio es
privado mientras el temario de Guardia Civil siga dentro (DEBT-003).
