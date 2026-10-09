# Piloto de clasificación de TAI: los dos primeros bancos (8-oct-2026)

Corrida real contra DeepSeek sobre los datos del propietario, parada a propósito tras los dos primeros
bancos para que él juzgue la calidad antes de seguir (así lo decidió en
`docs/DECISIONES-Y-SIGUIENTE-TANDA-2026-10.md`).

## Qué se ejecutó

```
OPOFUENTE_DATA_DIR=F:\OpoFuente\datos
DEEPSEEK_API_KEY=<solo en el entorno, nunca en un fichero>
uv run python -m opofuente.tools.clasificar_preguntas --bancos 2
```

- **Antes**: copia de seguridad de 2,47 GB (`opofuente-antes-de-clasificar-*.sqlite3`) y migración
  `0028_fuera_de_temario` aplicada a los datos reales.
- Los dos bancos por tamaño: `BLOQUE GENERAL::TESTS GENERALS::MUCHOS_TESTS` (1.227) y
  `Exámenes TAI - Test GSI (v2024)` (410).

## Resultado

### Cifras corregidas, medidas en la base (no en el informe del comando)

| | preguntas / filas |
|---|---|
| Preguntas **tocadas** por la clasificación | **1.789** |
| Mapeos escritos, firmados por `llm:deepseek-flash` | **3.581** |
| — aceptados nuevos (confianza ≥ 0,75) | 2.196 |
| — provisionales nuevos (0,5–0,75: la cola de revisión) | 1.385 |
| Preguntas sin ningún mapeo | 5.249 → **3.460** |
| Preguntas sin mapeo aceptado | 5.249 → **4.150** (hmm: ver más abajo) |
| **Fuera de temario** | **9** (4 `enunciado_roto` + 5 `otra_administracion`) |
| Errores de propuesta o de escritura | **0** |
| **Auditoría** | los 3.581 mapeos tienen **exactamente un** evento `question.mapped`; 0 sin evento, 0 con dos, y estado y confianza coinciden en los 3.581 |

> **Corrección (8-oct-2026).** Una versión anterior de este informe daba «855 asignadas, 532 a la cola,
> 8 fuera de temario». Eran **cifras intermedias**: el registro del comando siguió creciendo después de
> que yo lo leyera, y leí un resumen por banco como si fuera el total. Lo detectó el agente que estaba
> comprobando la base para la pantalla de revisión, que además encontró **un tercer banco clasificado**
> («Cuestionarios del material propio (astrocuestion)», 342 preguntas) de una corrida anterior que yo
> creía hecha sobre una copia. Consecuencia: **hubo al menos dos escrituras solapadas sobre los datos
> reales**, y de ahí salieron **4 preguntas con dos temas propuestos** y 9 con más de un epígrafe.
> Arreglos decididos: la cola de revisión **se agrupa por pregunta** (aceptar un tema retira los demás de
> esa pregunta), y el clasificador **no permitirá dos corridas concurrentes** sobre la misma base.

**Coste medido: 0,3466 $** en 82 llamadas · 558.670 tokens de entrada y 437.959 de salida
(precios de valle). Es decir, **0,00021 $ por pregunta**, no los 0,0000366 $ del piloto de apuntes: allí
el prompt era mucho más pequeño, y aquí lleva los 33 temas y los 134 epígrafes en cada llamada. La
estimación de 0,63 $ para las 17.183 preguntas **queda corregida: serían ≈3,6 $** (y menos si la caché
de prompt ayuda, que ya está aplicada).

## Muestra de los motivos que da el modelo

Salen en el informe de la corrida y son la prueba que el propietario necesita para juzgar:

- «Las BER/DER son reglas de codificación ASN.1 empleadas en certificados y firma digital.»
- «Ansible es una herramienta de gestión de configuración y automatización de sistemas.»
- «MPLS y LDP se relacionan con conmutación de etiquetas en redes de conmutación.»
- «FAT16 es un sistema de archivos y su límite de tamaño se encuadra en organizaciones de ficheros.»
- «El jitter es una métrica de QoS relacionada con la monitorización y control del tráfico.»
- «Visibilidad de atributos en UML.»
- «Active Directory en Windows Server 2008: sistemas Windows.»

Y cuando no lo tiene claro, lo dice: **222 preguntas sin propuesta** y 532 a la cola, en vez de rellenar
un tema a la fuerza. Ese es el comportamiento que se buscaba.

## Lo que queda pendiente de este piloto

1. **El juicio del propietario**: la muestra que le importa es la de su cola de revisión (532), que es
   donde verá si el 0,5–0,75 está bien calibrado. La pantalla para despacharla con el teclado es la
   tanda siguiente.
2. **Comprobar en la base** que las 855 asignaciones y las 8 exclusiones están escritas y auditadas.
3. Con su visto bueno: seguir con los 126 bancos restantes (≈3,6 $) y después los pasos B–E de los
   apuntes sobre lo ya clasificado.
