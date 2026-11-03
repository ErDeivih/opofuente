# Espacio en disco: qué puede salir de las oposiciones (OpoFuente)

> **Encargo directo de David (14/10/2026).** Es una tarea pedida, no una idea de otro agente.
>
> **Este documento es solo del material de oposiciones.** `facylf` tiene el suyo
> (`F:\EspacioCodigo\facylf\docs\ESPACIO-EN-DISCO.md`) y no se mezclan: son agentes y almacenes
> distintos.

## Aviso primero: esta zona está VIVA y cambiando

Mientras se escribía este documento, **alguien ya liberó 12,5 GB**: los directorios
`temp-opofuente\f16-datos`, `f18-datos`, `f20-datos`, `backup-f7` y `copia-real-f2` (≈2,5 GB cada uno,
todos copias del mismo `opofuente.sqlite3`) **han desaparecido**, y F: pasó de 5,8 GB libres a
**18,3 GB**. A la 1:05 de la madrugada había escrituras en `temp-opofuente\opofuente-inap`, así que
**hay trabajo en marcha ahora mismo**.

**Antes de mover nada: comprueba qué está en uso** y no pises a quien esté trabajando. Y no des por
buenas las cifras de este documento sin volver a medirlas: cambian por horas.

## Dónde está el material, y qué es cada cosa

| Ruta | GB | Qué es |
|---|---|---|
| **`F:\OpoFuente`** | **63,1** | El material de oposiciones: originales + almacén |
| `F:\OpoFuente\datos` | 38,5 | **Directorio de datos de la aplicación** |
| `F:\OpoFuente\datos\_copias` | **24,2** | **10 copias de la misma base de datos** |
| `F:\OpoFuente\zips` | **14,6** | **25 ficheros** ZIP |
| `F:\OpoFuente\TAI` | 6,3 | Material |
| `F:\OpoFuente\datos\backups` | 4,8 | 2 ficheros |
| `F:\OpoFuente\datos\artifacts` | 3,9 | Almacén por contenido de la app |
| `F:\OpoFuente\datos\opofuente.sqlite3` | 2,6 | **La base de datos viva** |
| `F:\OpoFuente\datos\tmp\snapshot-…` | 2,5 | 1 fichero |
| `F:\OpoFuente\datos-prueba-rama` | 2,4 | 1 fichero |
| `F:\temp-opofuente` | 5,5 | **Área de trabajo** (ver arriba) |
| `F:\EspacioCodigo\opofuente` | 0,7 | El código (repositorio) |

**Casi 30 GB son copias del mismo fichero.** Ese sigue siendo el gran premio, y ya se ha empezado a
cosechar en `temp-opofuente`.

## Hay DOS directorios de datos, y solo uno está vivo

Esto es lo primero que hay que entender, porque confundirlos es la forma más fácil de romper algo:

| Directorio | Base de datos | Última modificación | Veredicto |
|---|---|---|---|
| `F:\EspacioCodigo\opofuente\data` | **0,3 MB** | 14/09/2026 | **Dormido** (es el valor por defecto) |
| `F:\OpoFuente\datos` | **2.599,9 MB** | **13/10/2026 23:41** | **EL VIVO** |

El directorio de datos se elige con **una sola variable**: `OPOFUENTE_DATA_DIR`
(`.env.example` línea 9; por defecto `data`, relativo a la raíz del repositorio).

**Incógnita que hay que resolver antes de tocar nada, y no suponer:** no existe `.env` en
`F:\EspacioCodigo\opofuente` ni en `F:\OpoFuente`, y `OPOFUENTE_DATA_DIR` **no** está definida como
variable de usuario ni de máquina. Y sin embargo la app usa `F:\OpoFuente\datos`. La causa probable
es `project_root()` (`config.py:39-44`), que cae a `Path.cwd()`, y `.env` se lee **del directorio de
trabajo**. Es decir: **depende de desde dónde se lance la app**. Compruébalo (mira cómo se arranca)
antes de mover el directorio de datos, y **deja escrito el resultado** en `docs/OPERACION.md`.

## Lo que se puede hacer, por orden de seguridad

### 1 · Copias históricas de la base de datos — 24,2 GB en 10 ficheros

`F:\OpoFuente\datos\_copias`: ficheros tipo
`opofuente-antes-de-clasificar-20261008131256.sqlite3`, `opofuente-antes-del-resto-…`,
`opofuente-antes-epigrafes-tai-…`. **Nombres de agente**: son salvaguardas antes de una operación
arriesgada.

- Quédate con **las 2 más recientes** y mueve el resto a `E:\OpoFuente\copias-historicas`.
- **No borrar a lo bruto**: si una migración salió mal, la copia anterior es la única salida.
- Lo mismo con `datos\backups` (4,8 GB, 2 ficheros) y `datos\tmp\snapshot-…` (2,5 GB, 1 fichero).

### 2 · `zips` — 14,6 GB en **25 ficheros**

Copiar y pegar de minutos. Son archivos estáticos y **nada del proyecto los lee**: no hay ninguna
referencia a `OpoFuente\zips` en el código (comprobado). Es el movimiento más fácil y más rentable.

### 3 · El directorio de datos, por configuración y no moviendo ficheros

La app admite ruta absoluta en `OPOFUENTE_DATA_DIR`. Antes que mover 38 GB, **se puede apuntar a E:**
con una línea en el `.env` correcto (el que lea el lanzamiento real: ver la incógnita de arriba).
Con la app **parada**, mover el directorio y cambiar la línea. Sin enlaces, sin copias intermedias.

### 4 · `F:\temp-opofuente` (5,5 GB, y bajando)

Es un **área de trabajo**, no basura: contiene `f3…f23-scratch` (una por sesión), varias copias de
trabajo de la app (`opofuente-main`, `opofuente-inap`, `opofuente-claves`, `opofuente-contenido`,
`opofuente-alumno2`, `opofuente-clasif`, `opofuente-preguntas`, `opofuente-arreglos`, `opofuente-f2`,
`opofuente-alumno`) y utilidades (`tessdata`, `uv-cache`, `playwright-transform-cache`,
`node-compile-cache`, `__pycache__`).

Lo único claramente desechable son las **cachés** (`uv-cache`, `playwright-transform-cache`,
`node-compile-cache`, `__pycache__`) y los `tmp*` del 19/09. **Lo demás es trabajo**: decídelo con
David, no por tu cuenta. Ojo al nombre: dice «temp» y **no** es temporal.

## Qué NO hacer

- **Nunca mover, renombrar ni borrar los originales** (regla dura del proyecto: solo lectura). Si
  algún día se mueven, ten en cuenta que **la base de datos guarda la ruta real de cada artefacto**:
  esas rutas quedarían obsoletas y habría que decidirlo a conciencia, no como efecto lateral.
- **No borrar `_copias` sin conservar las recientes.**
- **No usar datos reales** para las puertas de pruebas (regla del propio `AGENTS.md`).
- **No relajar ni desactivar comprobaciones** para que algo pase.
- **No hacer commit** sin que David lo pida.

## Verificación

Con la app parada y el directorio movido o reapuntado:

```powershell
.\scripts\migrate.ps1     # la base se abre donde toque
.\scripts\seed.ps1        # los perfiles siguen ahí
```

Y las puertas completas antes de dar nada por terminado: `.\scripts\gates.ps1`.

## Deja constancia

1. Apunta en **`docs/OPERACION.md`** dónde queda cada cosa y, sobre todo, **cómo se lanza la app**
   (la incógnita de `OPOFUENTE_DATA_DIR` de arriba): eso es lo que necesita saber el siguiente.
2. Actualiza la tabla de este documento con lo que hayas movido, cuándo y a dónde.
3. Si mueves el directorio de datos, **anótalo también en `F:\OpoFuente`** (un `LEEME.md` en la raíz
   del material): quien mire la carpeta desde fuera tiene que enterarse sin leer este repositorio.
