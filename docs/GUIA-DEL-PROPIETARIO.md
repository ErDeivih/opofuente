# OpoFuente — guía de una página

**Todo lo de aquí está ejecutado y medido el 22 de octubre de 2026.** **Lo que no está, se dice al final.**

## 1. Instalar

```powershell
$env:OPOFUENTE_ADMIN_PASSWORD = 'una contraseña larga'
.\scripts\instalar.ps1 -Datos F:\OpoFuente\datos -Paquete .\paquete.json -Correo tu@correo
```

**Qué hace**: comprueba `uv` y `pnpm`, crea la carpeta, migra la base, revisa el paquete (y no lo importa
si lleva datos de una persona), lo importa, crea tu cuenta de administrador y te dice cómo arrancar.

**Medido**: **código 0, base de 23,8 MB, 1.455 preguntas y 1 cuenta.** **Sin `-Paquete` también funciona**:
deja el esquema y sin contenido.

**La contraseña va en el entorno, no en el comando**: **un argumento queda en el historial del terminal**.

## 2. Sacar el paquete de contenido

```powershell
cd apps\api
uv run python -m opofuente.tools.paquete_publico exportar --salida ..\..\paquete.json
uv run python -m opofuente.tools.paquete_publico revisar --paquete ..\..\paquete.json
```

**`revisar` es obligatorio antes de repartirlo**: **devuelve 1 si el paquete lleva una tabla de una persona
o una explicación privada.**

**Medido**: **13 tablas, 31.901 filas, 19,5 MB · `revisar` en verde · exportar, importar y volver a exportar
da exactamente lo mismo.**

## 3. Copia y restauración

```powershell
# copiar (no se copia el fichero: se pide una copia limpia a SQLite)
uv run python -c "import sqlite3;c=sqlite3.connect(r'F:\OpoFuente\datos\opofuente.sqlite3',timeout=30);c.execute('vacuum into \"F:\OpoFuente\copia.sqlite3\"');c.close()"

# restaurar: se para la aplicación, se sustituye el fichero y se arranca
```

**`VACUUM INTO` y no un copiar y pegar**: **con WAL, copiar el fichero a mano puede dejarse la mitad de las
últimas escrituras.**

**Medido**: **copia de 22,8 MB · restaurada en otra carpeta · 1.455 preguntas, 1 cuenta, `integrity_check`
= `ok`.**

## 4. Arrancar

```powershell
$env:OPOFUENTE_DATA_DIR = 'F:\OpoFuente\datos'
cd apps\api; uv run uvicorn opofuente.main:app --port 8000
cd apps\web; pnpm dev
```

**La API arranca y sirve, comprobado sobre esta instalación**: `GET /api/v1/stats` responde 200 con la
nota a `null` y las listas vacías, **que es lo correcto en una instalación sin actividad**.

**El instalador no arranca nada a propósito** — **si lo dejara corriendo, cerrar la ventana lo mataría y no
sabrías si está instalado.**

**La web no la he verificado sobre una instalación.**

## 5. Apagar

**Cerrar las dos ventanas.** **No hay servicio de Windows ni nada que se quede residente.**

## Lo que todavía no hay

- **invitar a nadie**: **la beta es por invitación, pero el enlace de invitación no está construido**;
- **capturas de M8**: **necesitan la aplicación arrancada y la web verificada**, **y la web es la mitad que
  falta**.
