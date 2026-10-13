# Informe de I.7 — La protección de datos personales y su régimen jurídico · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct 15:27–17:01.
Es el **quinto tema por valor** de la tabla del §4d (528 preguntas con clave utilizable) y **no tenía
catálogo**: el índice se escribió y se ensayó **antes** de pagar nada.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **19**, estructurados por las normas del tema (RGPD, LOPDGDD, LOPD 15/1999 y RD 1720/2007, más los derechos digitales del título X) |
| Grupos situados por el enunciado (ensayo, solo lectura) | **339 de 364 = 93,1 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos sin materia al cerrar | **3** (de 364) y **6 hechos** → bandeja del propietario |

Los 25 grupos que el ensayo **no** sitúa están clasificados uno a uno en
`f21-scratch/sin-materia-I.7.txt` (con sus opciones):

- **~14 son de otro tema** —cartografía del IGN y del Sistema Cartográfico Nacional, ciberseguridad y
  CSIRT, TLS 1.3 frente a TLS 1.2, un controlador DMA, personal funcionario interino (EBEP), la Ley
  Reguladora de las Haciendas Locales, el Estatuto de autonomía de las Illes Balears, la Ley 39/2015 y
  las bases de subvenciones—: van a la bandeja del propietario, que es lo que manda el índice;
- el resto son **fragmentos de norma sin sujeto** («…tendrá como mínimo las siguientes funciones» —las
  funciones del delegado de protección de datos—, «Asimismo, le corresponde…» —las del presidente de
  la Agencia—, «Cada Estado miembro establecerá por ley…» —el artículo 54 del RGPD—), y el reparto los
  sitúa **por el texto de sus hechos**, que es el camino que el motor tiene para eso. Al cerrar
  quedaron **3** sin materia.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 72 como mínimo y **125** como máximo | **144** (0 fallidas) |
| Coste | 0,49 $ como mínimo y **0,85 $** como máximo | **1,1903 $** |
| Tope decidido (cota de arriba × 4/3) | | **1,13 $** — **se cruzó en 0,06 $ (5,3 %)** |

**El tope se cruzó y se dice por qué**: la cota de llamadas se quedó corta por 19 (144 frente a 125), y
el bucle de huecos —que hace añadidos y recomprobaciones que la previsión no puede saber— es el que las
añadió. El precio por llamada salió a **0,00826 $**, por encima del 0,0068 $ de la tabla: es el tercer
tema **normativo y denso** de la serie (tras I.4 con 0,00865 $ y I.8 con 0,00853 $), y se comporta como
la regla supone. La corrida devolvió **1.531.556 tokens de salida** en 144 llamadas (10.636 por llamada)
y trajo 1,25 M de los 1,81 M de entrada en caché.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas del tema | 364 grupos · **564 preguntas** |
| Hechos | **738 guardados** → **610 en el plan** (128 repetidos agrupados por la deduplicación) |
| Apartados | **19** · ninguno pasó del tope de 150 hechos, así que **no hubo que partir ninguno** |
| Texto | 19 apartados · 163.059 caracteres · **25.768 palabras** |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de I.7 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **1,6 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 25.768 de 29.520 (**87,3 %**) | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **291/498 = 58,4 %** | **NO PASA** |
| Preguntas cubiertas (todas las claves) | — | 291/531 = 54,8 % | — |
| Hechos sin materia en el índice | 0 | 6 (en 3 grupos) | PASA (van a la bandeja) |

**Forma: PASA** y `--limpiar-forma` (0 $) tocó **15 apartados** —la limpieza de títulos y de tuberías—
sin que la forma dejara de pasar.

## 5. Por qué queda en borrador, con dos motivos medidos

1. **La cobertura es el 58,4 %** de las 498 preguntas con clave utilizable (listón 90 %). **No se toca
   el listón.**
2. **La corrida no terminó**: su propio informe dice «se agotó el tiempo de la corrida (5400 s): no se
   han hecho las llamadas que quedaban. Lo escrito está guardado y volver a lanzar el comando sigue
   desde ahí». Se comprobó con **257 de los 364 grupos** y el bucle de huecos —el que rellena los
   huecos añadiendo material y volviendo a comprobar— **apenas arrancó**: solo 3 grupos se cubrieron
   «tras añadir».

Así que el 58,4 % es un **suelo**, no el techo. Lo que costaría terminarlo, medido y sin pagarlo:
**38–94 llamadas · 0,26–0,64 $** (`--prever` sobre lo guardado). No se ha hecho en esta tanda porque
IV.5, III.9 e I.5 —los tres temas siguientes— tienen catálogo ya ensayado y un banco que encaja mejor;
queda **propuesto y con su precio**, y no se vuelve a pagar por lo escrito.

**Y una cosa que queda a medias y se dice**: la bandeja del propietario de I.7 está **vacía**
(`notes_incidents` no tiene ni una fila del tema) porque las incidencias las escribe el final del bucle
de huecos, que es justo lo que el tope de tiempo cortó. Los 196 huecos y los 59 dudosos están en las
anclas con su motivo, pero **el propietario no los ve en la bandeja** hasta que se retome la corrida.

## 6. Las incidencias, por motivo (de las anclas de la corrida)

| Motivo | Cuenta |
|---|---|
| La clave contradice la norma o el material | 23 |
| No hay ninguna frase en los apuntes que la justifique (hueco) | 11 |
| En conflicto: la frase está, pero la clave dice otra opción | 4 |
| La pregunta no tiene clave con la que comprobarla | 1 |

Y el estado de las 564 anclas del tema: **303 cubiertas · 196 huecos · 59 dudosas · 6 en conflicto**.

## 7. La puerta de datos del §1, otra vez al cerrar (0 $)

Se recalcula al terminar el tema, como manda el documento. Sobre la base real: **65 conjuntos
medibles** (eran 60: las anclas nuevas de I.7 dan medida a conjuntos que no llegaban al mínimo de 15),
**10 en cuarentena · 7 dudosos · 85 sin poder medir**. Y **3 cambios de veredicto**, cada uno con su
evento de auditoría:

| conjunto | antes | ahora |
|---|---|---|
| Material Adicional (respuestas marcadas) | fiable | **dudosa** |
| Normativa (respuestas marcadas) | fiable | **dudosa** |
| Doc adicional (respuestas marcadas) | dudosa | **fiable** |

Es la puerta funcionando en su sitio: un conjunto que nadie había medido y que al cruzar el 15 %
**entra marcado solo**, sin que nadie se acuerde de mirarlo.

## 8. Coste y gasto

| | |
|---|---|
| Coste medido | **1,1903 $** · 144 llamadas (0 fallidas) · 90 minutos · **parada por su tope de tiempo** |
| Previsión | 0,49–0,85 $ (se cruzó el máximo) |
| Gasto acumulado del objetivo | ≈ **10,58 $** antes de esta tanda → **≈ 11,77 $** con I.7 (aviso de los 10 $ ya cruzado en F19) |
