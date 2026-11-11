# Supuestos oficiales resueltos

**Fecha:** 11/11/2026 · **Pestaña:** <https://erdeivih.github.io/opofuente-demo/#/supuestos>

## Qué se ha construido

Cinco supuestos oficiales del **Cuerpo de Técnicos Auxiliares de Informática (TAI)** del INAP, cada uno
con **20 preguntas** y **100 preguntas en total**, resolución paso a paso, justificación de cada respuesta y referencia a la
plantilla oficial. Todos se pueden resolver en modo examen: sin corrección hasta el final.

| Supuesto | Año | Bloque | Dificultad | Estado | Plantilla |
|---|---|---|---|---|---|
| Becas para personas opositoras (TAI-L 2024-A-S1) | 2024 | IV | media | Resuelto | Oficial (20/20) |
| Becas para personas opositoras (TAI-L 2024-B-S1) | 2024 | IV | media | Resuelto | Oficial (20/20) |
| Red OEOF y segmentación (TAI-L 2024-A-S2) | 2024 | III | alta | Resuelto | Oficial (20/20; q15 anulada) |
| Representación electrónica con Cl@ve PIN (TAI-L 2023-S1) | 2023 | IV | media | Resuelto | Oficial (20/20; q15 anulada) |
| Segmentación de red y servicios (TAI-L 2023-S2) | 2023 | III | media | Resuelto | Oficial (20/20) |

**Fuentes oficiales:**

- Cuestionario TAI-L 2024 modelo A: [sede.inap.gob.es](https://sede.inap.gob.es/documents/59312/2364268/Cuestionario_TAI_LI_2024_A_M8L91VL1CL_154AB89SD658.pdf/43a5d8c6-3f74-dbca-8452-c00408125ff8), pp. 8-10 (S1) y 11-14 (S2).
- Plantilla definitiva 2024 A: [sede.inap.gob.es](https://sede.inap.gob.es/documents/59312/2364268/Plantilla+Cuestionario_TAI_LI_2024_A_definitiva.pdf/927bb295-6199-2a83-20e1-8cf970aa177e).
- Cuestionario TAI-L 2024 modelo B: [sede.inap.gob.es](https://sede.inap.gob.es/documents/59312/2364268/Cuestionario_TAI_LI_2024_B_DNFGFEK45R_154AB89SD658.pdf/f20d579c-5036-0013-4a90-ba7e24fc9bf9), pp. 8-10 (S1).
- Plantilla definitiva 2024 B: [sede.inap.gob.es](https://sede.inap.gob.es/documents/59312/2364268/Plantilla+Cuestionario_TAI_LI_2024_B_definitiva.pdf/e70c5182-f819-860d-3b9c-2a67b4547146).
- Cuestionario TAI-L 2023 (OEP 2022): [sede.inap.gob.es](https://sede.inap.gob.es/documents/59312/2194858/Cuestionario+TAI-L_2023.pdf/505d8c94-69a3-2971-b013-76c83e442ba1), pp. 8-10 (S1) y 11-14 (S2).
- Plantilla definitiva 2023: [sede.inap.gob.es](https://sede.inap.gob.es/documents/59312/2194858/PlantillaRespuestas+DEFINITIVA+TAI-L_oep2022.pdf/54977d89-8c20-cb49-d715-23cb72681c35).

## Contenido de cada supuesto

- **Enunciado** reescrito con palabras propias y datos completos del caso.
- **Resolución en 5 pasos**: qué se pide, qué datos importan, qué norma/técnica se aplica y cómo se
  descartan las opciones.
- **20 preguntas** con cuatro opciones, letra correcta de la plantilla y justificación razonada.
- **Temas que toca**, enlazados a la ficha del temario.
- **Fuente y páginas** del PDF oficial.
- **Dificultad y tiempo estimado** (28-30 minutos).

Las preguntas anuladas de 2023-S1 y 2024-A-S2 se conservan marcadas como **ANULADA** y se explican; el
cálculo de la nota excluye las anuladas.

## Búsqueda de exámenes y límites

- Se han descargado los cuadernillos y plantillas oficiales de **2023 y 2024** (modelos A y B) desde la sede del
  INAP. La página del INAP también enlaza exámenes de 2008/2010; no se han usado porque el formato y
  el temario son anteriores.
- La cabecera del PDF de 2023 dice «2022 - TAI-L» y la plantilla «OEP 2022»: el ejercicio se
  identifica por la convocatoria de 2022 y se celebra en 2023. En la ficha se muestra **2023** y se
  aclara la convocatoria; no se oculta la discrepancia.
- No se han encontrado en la sede del INAP cuadernillos de supuestos de 2019/2022 descargables con
  texto en el momento de la búsqueda; si aparecen, se añadirán con el mismo esquema.
- El material de academia local (`Apuntes TAI`/`BLOQUE 4`: **9 ficheros de supuestos localizados**; el README de la carpeta habla de 12) se usa solo como
  **referencia de formato**. No se publica su texto; los supuestos publicados son oficiales o propios.

## Próximos pasos

1. Añadir más supuestos oficiales de 2019/2022 cuando estén localizables y con plantilla.
2. Crear **supuestos propios** de los bloques III/IV (redes, sistemas, BD, seguridad, desarrollo) con
   el mismo esquema, sin copiar academia.
3. Ampliar filtros por dificultad y guardar el resultado en el historial de intentos (ya se guarda
   como tipo «Supuesto»).

## Verificación

- **78/78** comprobaciones Playwright en la URL pública, incluidas la pestaña Supuestos, el filtro por
  año, el enunciado/resolución y una resolución completa de 20 preguntas.
- Build y test validan **3 supuestos × 20 preguntas** y las opciones sin prefijo duplicado.
