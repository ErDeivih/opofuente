# Los apuntes de TAI entran en la biblioteca de la aplicación (30-09-2026)

Medido antes de tocar nada (`medir_los_apuntes_de_tai_en_la_biblioteca.py`): de los **37 apuntes de TAI**
(`F:\OpoFuente\APUNTES`, 33 temas y 4 bloques) había **0** en la biblioteca de la aplicación. La búsqueda y el
dossier por tema no los veían, aunque son el material con el que se estudia.

Se han metido con el camino medido en Guardia Civil, que evita los dos defectos encontrados en el extractor:

1. **texto plano**, no `.md`: un `.md` se extrae por sus encabezados `#` y el tramo guarda **el título** —un apunte
   de 80 KB quedaba en 447 caracteres (0,7 %)—;
2. **bloques de 800 caracteres como mucho**: un fragmento se recorta a 1.200 y un bloque son las líneas seguidas
   sin línea en blanco, así que la cola se perdía (con el arreglo, del 55 % al 98,2 % en Guardia Civil);
3. **por partes**: un apunte de TAI trae entre 557 y 2.768 párrafos y los fragmentos de un documento se cortan en
   **500** (`MAX_BLOCK_SECTIONS`), así que se escribe en partes de 450 párrafos: **102 ficheros** que son documentos
   distintos **mapeados todos al mismo nodo** del tema.

| | antes | ahora |
| --- | --- | --- |
| apuntes de TAI en la biblioteca | **0 de 37** | **37 de 37** (101 documentos, por partes) |
| fragmentos de apunte mapeados a su tema | 0 | **36.930** |
| texto de los apuntes conservado | — | **97,0 %** (11,86 MB de 12,23 MB) |

El nombre del fichero da el nodo (`3.2 Lenguajes de programación…` → `III.2`; `BLOQUE 4 …` → `IV`), que son nodos
de verdad del programa, y las **101 partes** quedaron con su mapeo (comprobado: 101 de 101 con mapeo).

## Lo que queda

- **No es el recorte de párrafos**: `medir_parrafos_largos_en_los_apuntes.py` cuenta **0 párrafos** de más de
  1.200 caracteres en los 102 ficheros de TAI (37.380 párrafos) y en los 25 de Guardia Civil (2.556). El 3 % que
  no se conserva es lo que quitan las **marcas de Markdown** (`#`, `**`, comillas invertidas) al pasar a texto
  plano, que es justo lo que se mide contra el fichero de origen.
- El apunte **4.4** parecía conservar el **71 %** y no es eso: de sus **3 partes** solo entraron **2** (la 1 y la
  3). El propio lote lo dijo —`preserved_unsupported: 1`— y es el **defecto ya medido del sniffing**: se leen los
  primeros 4.096 bytes y, si el corte parte un carácter, el `.txt` se clasifica binario y se conserva sin extraer
  sin decir por qué. De las 102 partes, **101 entraron y 1 se quedó fuera**; el texto de las que entraron se
  conserva al **99,4 %**. Arreglo conocido (`asegurar_que_parece_texto`, el relleno ASCII de 4.096 bytes) y
  pendiente de aplicar a esa parte.
- Los apuntes entran como `personal_notes`: el dossier y la búsqueda ya los tienen, pero **no se han tocado los
  ficheros de `F:\OpoFuente\APUNTES`** (el texto plano vive en `F:\OpoFuente\TAI\internet\apuntes-en-texto`).

## Cómo se reproduce

```
python medir_los_apuntes_de_tai_en_la_biblioteca.py            # 0 de 37 (medición del punto de partida)
python apuntes_de_tai_a_la_biblioteca.py --solo-textos         # 102 partes en internet\apuntes-en-texto
python apuntes_de_tai_a_la_biblioteca.py --ingerir
python apuntes_de_tai_a_la_biblioteca.py --aplicar             # promocionar, aceptar y mapear a su nodo
python mapa_de_material_por_tema.py                            # 33 temas: sin material 0 · sin preguntas 0
```
