# Propuesta: el trozo, no el documento (emparejar fragmentos con el temario)

**Fecha:** 24 de septiembre de 2026
**Rama:** `trozo-a-nodo` (desde `main`), en el árbol aparte `F:\temp-opofuente\opofuente-trozo`
**Naturaleza:** propuesta **fuera de slice**, autorizada por el propietario. **No añade dependencias, no
toca la base de datos, no cambia el contrato y no usa ningún modelo.** Es una regla de dominio y sus
pruebas.
**Origen:** el propietario corrigió el planteamiento del análisis: «un archivo no debe clasificarse como
una cosa sola, sino extraer su info y crear los temas, preguntas, respuestas… clasificando la info que
contiene, no el PDF». Eso es lo que se ha medido y lo que se propone.

## Qué he construido

Un módulo de dominio (`opofuente.domain.topic_matching`) que, dado **un fragmento de texto** y los
**títulos oficiales del programa**, propone el nodo del temario del que habla ese fragmento —o **nada**, si
no llega a un umbral— y devuelve sus alternativas. Además, el troceado de texto en unidades con sentido
que ese emparejamiento necesita.

Las tres decisiones que lo definen:

- **La unidad es el fragmento, no el documento.** Un temario de treinta páginas no pertenece a un tema;
  contiene decenas, y cada uno sí. Es lo que pide `04 §7` («un documento solo cubre parcialmente un tema»)
  y lo que hace posible el mapeo muchos-a-muchos de `03`.
- **Pesa lo que distingue.** Una palabra que aparece en un solo título del programa pesa mucho; una que
  aparece en diez, poco. No hay modelo ni entrenamiento: la referencia son los títulos oficiales.
- **No forzar es parte del diseño.** Si un fragmento no comparte suficiente con ningún título, se devuelve
  `None`. Un fragmento sin asignar es un resultado válido y explícito, no un fallo.

## Cómo fluye la información

```
texto de una representación  →  fragmentar()  →  trozos de 250–1.400 caracteres
                                                      │
                                                      ▼
                              EmparejadorDeTemas(nodos del programa).emparejar(trozo)
                                                      │
                        ┌─────────────────────────────┴─────────────────────────┐
                        ▼                                                       ▼
              Coincidencia(nodo, puntuación, alternativas)              None  ← sin asignar
```

Lo que **falta** para que esto llegue a la pantalla (y no entra aquí): sumar los votos de los trozos de un
documento para saber qué temas toca, y convertir cada coincidencia en una propuesta con la maquinaria de
bandas y revisión que ya existe desde S04. Ese enganche es el siguiente paso.

## Patrones aplicados

- **Puerto y adaptador, en su versión de dominio:** el módulo no sabe de base de datos, ni de HTTP, ni de
  ficheros. Recibe nodos y devuelve una coincidencia. Se prueba sin motor de base de datos, como el resto
  del dominio (`02_ARCHITECTURE §3`).
- **Regla pura y determinista:** sin azar, sin reloj, sin red y sin orden de entrada —el desempate lo fija
  la ruta oficial, no el orden en que llegaron los nodos—, para que dos ejecuciones den lo mismo.
- **Conservador por defecto:** umbral explícito, parámetro con nombre y valor por defecto documentado;
  nada se propone por debajo.

## Especificidades del framework (y del proyecto)

- Sin dependencias nuevas: sólo `re`, `unicodedata`, `dataclasses` y `collections.abc`.
- Tipado estricto (mypy limpio) y `from __future__ import annotations`, como el resto del dominio.
- Los objetos del vocabulario son `frozen=True, slots=True`, como `Proposal` o `ConfidenceBands`.
- Nada de `None` silenciosos: la ausencia de propuesta se devuelve explícitamente y se documenta.

## Decisiones tomadas (y a qué precio)

| Decisión | Por qué | Precio |
|---|---|---|
| Contar palabras distintivas en vez de usar un modelo | Es determinista, explicable, gratis, local y **medido**: los modelos de decisiones probados dan 18,5 % (azar 25 %) y su calibración no es de fiar en español | No entiende sinónimos ni paráfrasis: si el material no usa las palabras del título, no lo ve |
| Normalizar por el peso total del título | Evita que un título largo gane por ser largo | **Diluye** los títulos largos: un fragmento con una sola coincidencia puede quedarse sin asignar (probado y documentado) |
| Recorte tosco de sufijos en vez de lematizar | Un lematizador traería dependencia y diccionario | «administrativo»/«administrativa» sí, pero irregularidades no |
| Trocear por párrafos agrupados | Un tema se reconoce en un párrafo entero, no en una ventana arbitraria | Los párrafos largos se parten por tamaño, y eso **mezcla temas** (ver abajo) |

## Qué se ha medido, y una corrección

Sobre el material real del propietario (16 documentos con el bloque declarado en su propio nombre) y los
**33 títulos oficiales**:

| Medida | Resultado |
|---|---|
| **Bloque correcto** (voto de los trozos del documento) | **13/15 = 86,7 %** (con el otro filtro, 14/16 = 87,5 %) |
| **Tema exacto** | **6/12 = 50 %** |
| Trozos que se colocan solos | ~61 % |
| Trozos sin asignar | ~39 % |

Para comparar, la misma tarea pedida al documento entero: **18,5 %** con el modelo Laya (el azar es 25 %),
y el motor de reglas que hay hoy propone tema en 5 de esos ficheros y acierta 3.

**Corrección de un número mío:** antes había anunciado 93,8 % / 61,5 %. Eso se midió con un guion cuyo
troceado **recortaba** los párrafos largos (perdía texto). Al arreglarlo —partir en vez de recortar— el
número baja al de la tabla. Se ha aislado la causa: **no son las palabras vacías** (idéntico resultado con
las dos listas), **es el troceado**. El troceado que pierde texto puntúa mejor porque produce menos trozos
y más homogéneos. La conclusión práctica es la del apartado siguiente.

## Qué se rompe si cambias X

- **Si bajas el umbral**, empiezas a proponer temas por una palabra suelta: sube la cobertura y sube el
  ruido, y cada propuesta mala es una decisión que alguien tiene que deshacer.
- **Si quitas el desempate por ruta**, dos nodos iguales se resuelven por el orden de entrada y el
  resultado deja de ser reproducible entre máquinas.
- **Si dejas de normalizar por el peso del título**, los títulos largos ganan siempre y el emparejamiento
  se vuelve un «cuál es el título más largo», no un «de qué habla esto».
- **Si vuelves a recortar párrafos largos**, recuperas puntuación y pierdes texto del temario. Perder texto
  no es una decisión de formato.
- **Si el troceado lo hace una ventana fija de caracteres**, el resultado empeora: es justo lo que se ha
  medido.

## Qué criticaría un revisor senior

1. **«El troceado es lo más flojo de todo esto.»** Cierto, y es la siguiente pieza: el modo bueno de
   trocear no es una ventana de caracteres, es **la estructura del documento** —los encabezados y las
   secciones que la aplicación ya extrae y guarda en `document_sections`—. Con secciones reales, un trozo
   es un epígrafe, no un corte a mitad de párrafo. Es lo primero que probaría ahora.
2. **«Esto no es un slice y no hay contrato con lista de ficheros.»** Cierto: es una propuesta con dos
   ficheros nuevos, sin dependencias ni esquema, hecha a petición del propietario. Si se acepta, el sitio
   natural es un slice propio que incluya el enganche con propuestas y bandas.
3. **«Falta el enganche.»** Cierto y a propósito: aquí está la regla y sus pruebas, no la integración. Sin
   el enganche no hay nada que el usuario vea todavía.

## Puertas ejecutadas

| Puerta | Comando | Resultado |
|---|---|---|
| Unitarias | `python -m pytest apps/api/tests/unit/test_topic_matching.py` | **16 passed** |
| Lint | `ruff check <los dos ficheros>` | **All checks passed!** |
| Formato | `ruff format --check <los dos ficheros>` | **2 files already formatted** |
| Tipos | `mypy apps/api/opofuente/domain/topic_matching.py` | **Success: no issues found** |

**No ejecutadas:** la suite completa, la integración, el contrato OpenAPI y el E2E. No hay cambios en
rutas ni en el esquema, así que no deberían verse afectadas, pero **no se declaran ejecutadas**.

## Ficheros

- `apps/api/opofuente/domain/topic_matching.py` (nuevo): la regla y el troceado.
- `apps/api/tests/unit/test_topic_matching.py` (nuevo): 16 pruebas, con los dos límites conocidos escritos
  como pruebas para que no se descubran por sorpresa.
