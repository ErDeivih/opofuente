# Informe de IV.6 — Comunicaciones, medios de transmisión y redes · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct 19:30–19:58.
Decimotercer tema por valor de la tabla del §4d (313 preguntas con clave utilizable), **sin catálogo**
antes de esta tanda. **PUBLICADO**: pasa las dos puertas del §2.3.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **16**, por asunto dentro de sus siete epígrafes |
| Grupos situados por el enunciado (ensayo) | **299 de 310 = 96,5 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **4 grupos y 5 hechos** (→ bandeja) |

Los 11 grupos que el ensayo no sitúa son de otro tema —los comandos de Unix `vi` y `touch`, el servicio
SMB de Windows, el puerto de SMTP, el software de backup, las funciones del administrador del sistema,
una clave pública— más dos fragmentos sin sujeto que el reparto sitúa por sus hechos; al cerrar
quedaron **4**.

**Un defecto de redacción que el ensayo destapó y se corrigió antes de gastar**: `802 ?11` estaba como
patrón del apartado de organismos y, con el número suelto, **38 de los 310 grupos** acabaron ahí por
citar la norma al principio del enunciado. Los organismos quedaron con los patrones de «quién regula» y
el `802 11` pasó al WiFi y al cableado, que es de quien es: **organismos bajó de 38 a 10 grupos y el
WiFi subió de 45 a 72**. Es exactamente para lo que está el ensayo.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 62 como mínimo y **108** como máximo | **105** (0 fallidas) |
| Coste | 0,42 $ como mínimo y **0,73 $** como máximo | **0,3916 $** |
| Tope decidido (cota de arriba × 4/3) | | **0,97 $** — **no se activó** |

**Es la corrida más barata de la serie**: 105 llamadas a **0,00373 $**, por debajo del mínimo previsto.
Es un tema **técnico** con hechos cortos y muy repetidos (138 de 626 agrupados) y con **el 55 % de la
entrada en caché** (353.664 de 642.841 tokens). Devolvió 491.919 tokens de salida (4.685 por llamada).
**El tope de tiempo no llegó a activarse**: terminó sola con las **310 de 310** comprobaciones hechas.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 310 grupos · **321 preguntas** |
| Hechos | **626 guardados** → **488 en el plan** (138 repetidos agrupados) |
| Apartados | **16** · ninguno pasó del tope de 150 hechos |
| Texto | 16 apartados · 90.970 caracteres · **15.339 palabras** de 25.040 (61,3 %) |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de IV.6 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 15.339 de 25.040 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **288/297 = 97,0 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 288/311 = 92,6 % | — |
| Hechos sin materia en el índice | 0 | 5 (en 4 grupos) | PASA (van a la bandeja) |

`--limpiar-forma` (0 $) tocó **15 apartados** y la forma siguió en PASA. La corrida terminó entera:
**310 de 310** grupos comprobados, 289 cubiertos (269 a la primera y 20 tras añadir material en el
bucle de huecos) y **«sin contestar por los apuntes: 2»**.

**Y es la primera corrida de la serie con párrafos repetidos al 0,0 %**: no hay ni un párrafo que se
repita, y el tope del 5 % no apretó por ningún lado.

## 5. La bandeja del propietario

**25 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 14 |
| `pregunta_ambigua` | 5 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 4 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 2 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**87 conjuntos medibles** (eran 85 al cerrar III.9), **12 en cuarentena · 9 dudosos · 83 sin poder
medir**. El denominador de la cobertura de IV.6 es 297 preguntas, ya sin las de los conjuntos en
cuarentena.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,3916 $** · 105 llamadas (0 fallidas) · 28 minutos · tope no activado |
| Previsión | 0,42–0,73 $ (salió por debajo del mínimo) |
| Gasto acumulado del objetivo | ≈ 13,72 $ antes de IV.6 → **≈ 14,11 $** con IV.6 |
