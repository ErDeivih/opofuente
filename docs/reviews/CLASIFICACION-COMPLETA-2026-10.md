# La clasificación de las preguntas de TAI, terminada (8-oct-2026)

Segundo paso de la tanda que fijó el propietario en `docs/DECISIONES-Y-SIGUIENTE-TANDA-2026-10.md`.
Corrida real contra DeepSeek sobre sus datos, con el temario leído de la base (33 temas y 134 epígrafes).

## Lo que se ejecutó

```
OPOFUENTE_DATA_DIR=F:\OpoFuente\datos      # la clave, solo en el entorno; jamás en un fichero
uv run python -m opofuente.tools.clasificar_preguntas
```

- En un **árbol limpio** (`f6-clasificacion-resto`, sobre el `main` con la maquinaria ya verificada) y
  **no** en el árbol donde otra pieza tenía a medio editar la cadena de escritura.
- **Copia de seguridad previa** de 2,47 GB.
- **Una sola corrida** (el clasificador no permite dos a la vez en el código fusionado).

## Resultado

| | preguntas |
|---|---|
| **Asignadas** (confianza ≥ 0,75) | **1.138** |
| **A la cola de revisión del propietario** (0,5–0,75) | **736** |
| **Fuera de temario** | **1.076** (754 enunciado roto + 324 otra administración) |
| Sin propuesta (el modelo no lo tenía claro) | 507 |
| **Errores de escritura** | **0** (3 errores de propuesta: respuestas ilegibles, no se escribió nada) |
| Confianza media | **0,875** |

**Coste medido: 1,1058 $** (250 llamadas, 1.832.737 tokens de entrada y 1.384.792 de salida, precios de
valle). Con la corrida anterior, **clasificar todo ha costado 1,45 $**.

## Comprobado en la base, no en el informe del comando

| | antes | después |
|---|---|---|
| Preguntas sin ningún mapeo | 3.460 | **1.586** |
| Exclusiones | 9 | **1.078** |

Y cuadra sin resto: 3.460 − (1.138 asignadas + 736 a la cola) = **1.586**, que es justo lo que devuelve
la consulta. Las 1.078 exclusiones y las 507 sin propuesta no generan mapeo, y por eso están entre las
1.586.

## Lo que la máquina demuestra que sabe hacer

- **Distingue por contenido, que era el criterio del propietario.** De los bancos de otras
  administraciones (`Principado de Asturias - IAAP`, `Región de Murcia CARM`, `AGE 2006`…) se queda con
  la informática y marca fuera de temario las leyes y la organización ajenas:
  > «Pregunta sobre la organización de la función informática según la legislación autonómica de Castilla
  > y León, propia de otra administración.»
  > «Funciones públicas de Corporaciones Locales, régimen local ajeno al temario TAI.»
- **Razona y nombra la alternativa que descarta**:
  > «El firmware es software de bajo nivel ligado al hardware; encaja en componentes internos de equipos
  > microinformáticos, aunque también podría relacionarse con administración del software de base (IV.1).»
- **Detecta material que no son preguntas.** Los 754 «enunciado roto» no son falsos positivos: son
  fragmentos de reglamento importados como si fueran preguntas, y **miré seis a mano para confirmarlo**:
  > «Los Estados miembros garantizarán que el incumplimiento del presente Reglamento… se sancione con
  > multas administrativas…» · «La Comisión podrá, mediante actos de ejecución, establecer:» · «Sin
  > perjuicio de lo dispuesto en el artículo 5 bis, apartado 18, la información facilitada… incluirá, como
  > mínimo:»

  Terminan en dos puntos, no preguntan nada y no tienen opciones. Es un **hallazgo sobre el material de
  origen** (bancos «Doc adicional» y «baquedano»), no un fallo de la clasificación: ahora está etiquetado
  en vez de mezclado.

## Lo que queda, y decide el propietario

1. **736 propuestas** para despachar con el teclado en `/admin/clasificacion` (la pantalla está
   verificada con 18 puertas y espera a que Claude guarde su trabajo para entrar en `main`).
2. **1.078 exclusiones** con su enunciado y su motivo, para confirmar o corregir.
3. **507 sin propuesta**: segunda pasada con umbral más bajo, o revisión a mano.
4. Después, los **tres temas piloto de apuntes** (IV.7, I.6 e I.1), que es para lo que se hizo todo esto.
