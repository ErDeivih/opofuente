# Paso A de los apuntes: lo que hay que decidir antes de gastar (7 de octubre de 2026)

Medido sobre los datos reales, en solo lectura, con un piloto de **70 preguntas y 5 llamadas** que costó
**0,0036 $**. El informe completo del guion está en `INFORME-PASO-A.md` (fuera del repositorio, en la
carpeta de trabajo); aquí queda lo que cambia el plan y lo que hay que decidir.

## 1. El precio, verificado hoy

`deepseek-flash`, en USD por millón de tokens, según la tabla oficial consultada el 7-oct-2026: entrada
**0,15** (0,30 en punta), entrada con **acierto de caché 0,003**, salida **0,60** (1,20 en punta). El
modelo `deepseek-v4-pro` cuesta 4,4 veces más. Punta = 01:00–04:00 y 06:00–10:00 UTC de lunes a viernes;
el trabajo se hizo a las 13:13 UTC, en valle.

Medido en el piloto: **0,0000366 $ por pregunta** con lotes de 20, y la caché de prompt funciona (11.776
de 15.321 tokens de entrada a precio de acierto en la segunda pasada).

## 2. Lo que cuesta el paso A entero

| escenario | preguntas | llamadas | coste (valle) |
| --- | --- | --- | --- |
| tema de las que no tienen (agrupando repetidas) | 6.065 grupos | 304 | **0,222 $** |
| tema de las que no tienen (sin agrupar) | 7.677 | 384 | 0,281 $ |
| epígrafe de las que ya tienen tema | 9.506 | 476 | 0,348 $ |
| **paso A completo (tema + epígrafe)** | 17.183 | **860** | **0,629 $** |
| peor caso, sin caché de prompt | 17.183 | 860 | 1,372 $ |

**El paso A no es el gasto del plan de apuntes: es la decisión.** Los pasos que de verdad cuestan son
redactar (1.000–2.000 llamadas) y comprobar pregunta a pregunta (670 por vuelta).

## 3. Los datos, medidos (y no exactamente como decía el plan)

| dato | plan | medido |
| --- | --- | --- |
| preguntas de TAI | 16.743 | **17.183** |
| enunciados distintos | 13.327 | **13.329** |
| con tema | 9.342 | 9.506 |
| **sin tema** | 7.401 (44 %) | **7.677 (44,7 %)** |
| **con epígrafe** | — | **0** |
| por tema | 59–1.865 | 74 (IV.4) – 2.006 (I.1) |
| bloque II | 80–86 por tema | 83–104 por tema (475 en total) |

Las 440 de diferencia son exactamente las de la reimportación de los exámenes oficiales del 2-oct-2026
(`REIMPORTACION-DE-LOS-EXAMENES-2025-2026-10.md`), que entraron **con** tema. Cuadra.

## 4. Hallazgo 1: el epígrafe no existe para TAI

`curriculum_nodes` tiene **125 nodos de tipo epígrafe y los 125 son de Guardia Civil**
(`gc-cabos-guardias-2026`; comprobado contra la base y contra el fixture). **Celador tiene cero y TAI
tiene cero.** La convocatoria de TAI
tiene 4 bloques y 33 temas, y **cero epígrafes**; los mapeos de pregunta no guardan `epigraph_index`. El
paso A.3 del plan **no se puede ejecutar tal cual**: hay que crear los epígrafes. Ya están derivados del
título oficial (que los separa por puntos): **134 epígrafes** para los 33 temas.

> **Corrección (7-oct-2026, ronda 43).** Este apartado decía que los 125 epígrafes eran «de Celador».
> Era falso: lo copié del informe del trabajo de apuntes sin comprobarlo contra la base, y el agente que
> está creando los 134 lo cazó. Los 125 son de Guardia Civil. La conclusión del apartado no cambia —TAI
> no tiene ninguno y hay que crearlos—, pero queda dicho de dónde salió el error: **una cifra que va a un
> documento se comprueba contra los datos, no se hereda del informe de otro.**

## 5. Hallazgo 2: cerca de un cuarto del banco no es del programa

El 28 % de la muestra el modelo la mandó fuera de temario. Revisado: **8 de cada 11 son banco ajeno** —
exámenes de Pontevedra, Zaragoza, Barcelona, Murcia, Asturias… importados al banco de TAI—, 2 son
enunciados rotos (un trozo de norma copiado sin pregunta) y **1 es fallo del modelo**. Es un hallazgo
sobre los datos: del orden de **2.100 preguntas** que no son materia del programa vigente de TAI.

## 6. La calidad del método, revisada a mano

Se revisaron **las 40** asignaciones del piloto: **35 defendibles (87,5 %)**, 3 dudosas y **2 mal**. La
inestabilidad entre pasadas es del **7 %** (la misma pregunta cayendo en dos temas distintos). Dos
conclusiones: sirve para clasificar, pero **no se publica sin revisión**; y conviene **agrupar por firma
(enunciado + opciones)** antes de llamar, que ahorra un 21 % de llamadas y quita la única inconsistencia
grave vista.

## 7. Lo que hay que decidir (del propietario)

1. **Las ≈2.100 ajenas al programa**: ¿se marcan «fuera de temario» —lo que el plan contempla, y se puede
   hacer **en bloque por conjunto de origen**, sin clasificarlas una a una— o se les fuerza un tema?
2. **Cómo se guarda el resultado**: **no hay ninguna ruta HTTP que asigne tema a una pregunta**. Existe el
   método auditado por dentro (`QuestionRepository.map_question_to_node`, que deja `audit_events` con
   acción `question.mapped`), pero no está expuesto; y la vez que se escribió directo en la base —los 440
   mapeos del 2-oct— **quedó sin auditoría** (12.047 de 12.487 mapeos la tienen). El plan ya propone
   `POST /questions/{id}/topics`, y esa ruta la necesita también el panel de administración, así que la
   recomendación es implementarla en vez de tirar por un guion.

## 8. Orden recomendado, cuando se apruebe

1. **Gratis**: agrupar por firma (7.677 → 6.065) y separar por conjunto de origen las ajenas al programa.
2. **Clasificar por conjuntos, no por bloques**: el bloque de una pregunta sin tema **se desconoce**, así
   que «el bloque II primero» no es ejecutable. **12 conjuntos concentran 4.784 de las 7.677 (62 %)**;
   clasificar de mayor a menor da los cuatro bloques desde el primer lote y permite cortar cuando se
   quiera.
3. **Freno de revisión** tras los dos primeros conjuntos (≈2.100 preguntas, ≈105 llamadas, **≈0,08 $**)
   para comprobar la calidad sobre datos reales antes de seguir.
4. Los tres temas piloto (IV.7, I.6 e I.1) no se pueden preparar antes de clasificar: hasta que no se
   sepa qué preguntas sin tema acaban en cada uno, no hay nada que redactar.
