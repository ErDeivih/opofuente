# Baseline de rendimiento local

Cifras medidas en **este equipo** con el corpus sintético que genera
`apps/api/opofuente/tools/benchmark.py`. No son un banco de pruebas de laboratorio: son un punto de
comparación para que una regresión futura se note. Se ejecutan **a mano**, no en las puertas: un umbral
de tiempo en CI es la forma más rápida de tener una puerta que falla por el portátil y no por el código.

## Cómo se reproduce

```powershell
uv run python -m opofuente.tools.benchmark --documents 300
```

El corpus lo crea el propio comando en un directorio temporal: 300 documentos con cinco fragmentos
cada uno (1 500 fragmentos), su representación, sus derechos y su registro de artefacto, con el fichero
de verdad en el almacén.

## Medición del 19 de septiembre de 2026

**Equipo:** Windows 11, disco local, Python 3.12, SQLite embebido (SQLAlchemy 2), un solo proceso.
**Corpus:** 300 documentos · 1 500 fragmentos · ~2.0 MB de material en el almacén.

| Operación | Tiempo | Detalle |
|---|---|---|
| Copia de seguridad | 4.56 s | 301 ficheros, 295 378 bytes de archivo |
| Restauración completa | 1.82 s | 301 entradas, validación + extracción + intercambio + salud |
| Búsqueda léxica | 0.14 s | 10 fragmentos entregados |
| Rehacer el índice | 0.06 s | 1 500 fragmentos indexados |
| Foto de higiene | 0.05 s | 2 068 798 bytes medidos en todo el almacén |
| **Total** | **6.63 s** | |

Para comparar, la misma medición con 60 documentos: copia 1.32 s, restauración 0.44 s, búsqueda 0.09 s,
rehacer el índice 0.006 s, higiene 0.02 s (total 1.87 s).

## Qué dicen estas cifras, y qué no

**Lo que dicen:**

- la **copia** es lineal con el número de ficheros (301 ficheros → 4.6 s, unos 15 ms por fichero,
  dominado por el hash SHA-256 y la compresión);
- la **restauración** cuesta menos que la copia porque además hace una copia previa (que aquí es
  pequeña) y el intercambio es mover directorios, no copiarlos;
- la **búsqueda léxica** se mantiene por debajo de los 150 ms con 1 500 fragmentos: FTS5 con `bm25` no
  es el cuello de botella a esta escala;
- **rehacer el índice** es baratísimo porque reconstruye desde `evidence_spans` en la misma base.

**Lo que no dicen:**

- **No hay ninguna medición con material real.** El corpus sintético tiene fragmentos de una línea; un
  temario real trae documentos de cientos de páginas, y el coste de una copia depende de los bytes, no
  del número de ficheros: 2 MB de sintético no se parecen a los 500 MB que puede haber en una carpeta
  de apuntes.
- **No hay cifras de la interfaz.** No se ha medido el tiempo de pintado de una tabla con cien filas ni
  el de la pantalla de revisión con muchos grupos: lo que hay es el límite de página (100 filas) y la
  paginación del banco de preguntas (DEBT-011), que acotan el problema sin medirlo.
- **No hay tablas virtualizadas**, y con el límite de página actual tampoco hacen falta: se verá cuando
  el propietario tenga material real y la tabla de preguntas se quede corta.

Lo que corresponde después de estas cifras es volver a medir **con el material del propietario**
(la prueba personal de cuatro semanas) y decidir con esos números si hace falta virtualizar tablas o
trocear la copia.
