# Informe de IV.4 — Administración de redes de área local, usuarios, dispositivos y tráfico · 14-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0037_origin_scope`). Corrida del 14-oct, lanzada y
**esperada dentro del turno**. Cuarto tema de la tanda f25 y **vigésimo quinto** por valor de la tabla
vuelta a medir hoy (**150** claves utilizables). **PUBLICADO**: pasa las dos puertas con
**141/145 = 97,2 %** de cobertura sobre clave utilizable.

## 1. El índice, antes de gastar (0 $), y el hallazgo que vale para todos los catálogos

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **15** |
| Grupos situados por el enunciado (ensayo, tras los arreglos) | **147 de 151 = 97,4 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **143/147 = 97,3 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **4 grupos y 9 hechos**, los cuatro de otro tema |

### El hallazgo: **la barra es un espacio, y por eso `/etc/passwd` no podía casar nunca**

El primer ensayo dejó **22 grupos sin materia** y el techo en **85,7 %**, por debajo del listón. Al
mirarlos uno a uno aparece una causa que **no es de este tema sino de todos los catálogos**:

**El normalizador del texto convierte la barra en espacio**, como ya hacía con el guion, el punto y la
coma. Así que un patrón escrito `/etc/passwd` **no puede casar jamás**: el texto que ve el motor es
« etc passwd ». Los patrones de ficheros hay que escribirlos **con el espacio del separador**:

| Se escribió | No casa nunca | Hay que escribir |
|---|---|---|
| `/etc/passwd` | ✗ | `etc ?passwd` |
| `/etc/shadow` | ✗ | `etc ?shadow` |
| `/etc/gshadow` | ✗ | `etc ?gshadow` |
| `login\.defs` | ✗ | `login ?defs` |

**Esto solo explica tres de los grupos sin situar**, pero es una regla general: **el separador nunca
llega al patrón**, y un patrón con `/` es un patrón muerto que además **no da ningún error** —el
catálogo se carga, el índice dice PASA y el grupo se cae a la bandeja sin que nadie se entere—.

Los otros tres grupos que se recuperaron venían de **patrones demasiado literales**, y también es una
lección: el enunciado dice «estadísticas **y** conexiones» donde yo escribí «conexiones y estadísticas»,
y «propiedad de **una** organización» donde escribí «propiedad de **la** organización».

**Arreglado a 0 $, el techo pasó de 85,7 % a 97,3 %**: **dieciséis puntos de cobertura por no haber
pagado la corrida antes de ensayar**. Es el mejor ejemplo de la serie de lo que vale el ensayo previo.

### Y una decisión de apartado, dicha

Las preguntas de **usuarios conectados, sesión en una máquina remota, procesos en un equipo remoto y
fecha del último reinicio** son **administración del sistema**, no de la red: no caben en «la red en
Linux» ni en «la red en Windows», así que se les da **un apartado propio** («Los comandos de
administración del sistema») en vez de forzarlas dentro de otro. Es el mismo criterio que con la
orientación a objetos en II.5 y con el cortafuegos aquí.

## 2. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 151 grupos · **153 preguntas** |
| Hechos | **308 guardados** → **261 en el plan** (47 repetidos agrupados) · **17 con la clave señalada** |
| Apartados | **15** |
| Texto | 8.879 palabras de 12.320 (72,1 %) · párrafos repetidos **0,0 %** |

## 3. Las puertas (§2.3)

| Puerta | Umbral | Cifra de IV.4 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 8.879 de 12.320 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **141/145 = 97,2 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 141/151 = 93,4 % | — |
| Hechos sin materia en el índice | 0 | 4 grupos y 9 hechos con su motivo | — |

La corrida **terminó entera**: **151 de 151 grupos comprobados**, 145 cubiertos (137 a la primera y
**8** tras añadir), **0 en conflicto con la clave** y **0 «sin contestar por los apuntes»**.

## 4. Lo que NO se coló, comprobado

Los **4 grupos** que el índice no sitúa son de otro tema y **se quedaron sin ancla**, en la bandeja del
propietario con su motivo —comprobado grupo por grupo con `donde_cayeron.py` (0 $), que es la
verificación que en I.3 faltó—:

| La pregunta | De qué tema es |
|---|---|
| El ataque que inunda un objetivo con múltiples dispositivos hasta comprometer la disponibilidad | **IV.9** (seguridad) |
| Las funciones de la capa de transporte | **IV.7** (el modelo de referencia) |
| Los sistemas de almacenamiento SAN y NAS | **IV.2** (administración del almacenamiento) |
| Las entidades locales de ámbito inferior al municipio (Ley 7/1985) | **otro bloque** (derecho administrativo) |

## 5. La bandeja del propietario

**10 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice el material) | 6 |
| `pregunta_ambigua` (sin clave con la que comprobar) | 4 |

## 6. Lo que costó, y la previsión

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 38 como mínimo y **68** como máximo | **70** (0 fallidas) — **por encima del máximo** |
| Coste | 0,26 $ como mínimo y **0,46 $** como máximo | **0,1522 $** — por debajo del mínimo |
| Precio por llamada | — | **0,002174 $** |
| Consumo | — | 307.708 tokens de entrada (136.448 en caché, 44,3 %) · 176.773 de salida |

**Es la primera vez en la serie que la cota de llamadas se queda corta por arriba** (70 frente a 68) y
la cuarta seguida que el coste sale por debajo del mínimo. Las dos cosas a la vez dicen lo mismo: **la
cota de `--prever` no predice bien el reparto, pero su extremo de dinero es un techo** — porque el
bucle de huecos añade llamadas cortas y baratas—. El aviso queda: **la cota de llamadas puede
superarse, la de dinero no**.

## 7. La puerta de datos del §1, al cerrar (0 $)

**124 conjuntos medibles · 21 en cuarentena · 9 dudosos · 81 sin poder medir.** Dos conjuntos más en
cuarentena que al cerrar II.5 (19 → 21).

## 8. Lo que queda fuera, con el porqué

- los **4 grupos** de otro tema del §4, en la bandeja con su motivo y **sin ancla**;
- **I.8 (81,2 %), I.6 (71,4 %) e I.7 (57,1 %)**: los tres borradores que siguen, con su cifra y su causa
  medida (**0 grupos sin comprobar** en los tres: el hueco es material);
- **III.4**: sigue sin escribir; su banco es de otra materia en un 40 %, ya medido.

## 9. Lo que este tema deja medido

- **Un patrón con `/` es un patrón muerto y no avisa**: el normalizador convierte la barra en espacio y
  el grupo se cae a la bandeja sin error. Vale para todos los catálogos y hay que mirarlo **antes** de
  correr. Es la comprobación que convierte dieciséis puntos de techo en una línea de ensayo.
- **El ensayo previo se pagó solo otra vez**: sin él, IV.4 habría corrido con un techo de 85,7 % —por
  debajo del listón— y habría acabado en borrador con su cifra. Con él, publicó al 97,2 %.
- **La cota de llamadas de `--prever` se puede superar; la de dinero, no.**
