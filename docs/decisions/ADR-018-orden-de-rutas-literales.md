# ADR-018 — Las rutas literales se declaran antes que las parametrizadas

**Estado:** propuesto (pendiente de ratificación del propietario)
**Fecha:** 23 de septiembre de 2026
**Contexto de la decisión:** DEBT-027 §5, al ir a servir las columnas de preguntas y próximo repaso
del Programa.

## Contexto

FastAPI resuelve por **orden de declaración**: la primera ruta cuyo patrón encaje con la petición es
la que la atiende, y las siguientes no se miran. Eso convierte el orden de las líneas de un fichero de
rutas en comportamiento observable, sin que nada lo advierta.

El 23 de septiembre de 2026 se encontró el fallo que lo demuestra. En `api/routes/reviews.py` estaba:

```python
@router.get("/reviews/{review_id}")        # declarada antes
@router.get("/reviews/mastery")            # declarada después: nunca se alcanza
```

`GET /api/v1/reviews/mastery` encajaba con la primera (con `review_id="mastery"`) y devolvía el 404 de
«no existe repaso con ese identificador». **La columna de dominio del Programa no se había servido
nunca**: el cliente pedía el dato, recibía un 404 y la pantalla pintaba la fila sin dominio, que es
justo lo que se ve cuando no hay datos. Nada lo delató:

- las pruebas unitarias de la interfaz **simulan `fetch`**, así que la URL nunca se compara con la API;
- las pruebas de la API probaban el servicio (`service.mastery(...)`), no la ruta;
- la E2E del Programa no miraba la columna de dominio, y un 404 en una consulta opcional no rompe la
  pantalla.

Lo encontró una prueba escrita para otra cosa: la que comprueba el estado de estudio por nodo pedía
`/api/v1/reviews/mastery` por HTTP en lugar de llamar al servicio.

## Decisión

**Toda ruta literal se declara antes que cualquier ruta parametrizada con la que pueda encajar**, en el
mismo router. Si dos rutas pueden encajar con la misma petición, la literal va primero.

Se añade una **prueba de contrato que recorre el orden real de las rutas** y falla si alguna literal
queda tapada por otra con parámetros declarada antes. La prueba se comprueba a sí misma con el caso
real que la motivó (`/reviews/{review_id}` antes de `/reviews/mastery`), para que no sea una prueba que
no puede fallar.

## Consecuencias

- El orden de declaración deja de ser un detalle de estilo: hay una prueba que lo vigila y una regla
  escrita aquí, con el caso que la motivó.
- La ruta `/reviews/mastery` conserva su nombre (está registrada en ADR-013 y el cliente la usa); lo
  que cambia es **dónde** se declara, no qué se sirve.
- Si algún día se renombra una ruta parametrizada de forma que su patrón deje de poder encajar con una
  literal, la prueba seguirá pasando sin cambios: solo mira lo que de verdad puede colisionar.

## Alternativas descartadas

1. **Confiar en el orden sin prueba.** Es lo que había, y costó una columna entera sin servir durante
   varios slices. Un comentario en el fichero no lo habría impedido.
2. **Prefijos distintos** (`/reviews-mastery` o `/program-mastery`). Evita la colisión a base de
   romper la jerarquía de la URL y obliga a cambiar el contrato y el cliente por un problema de orden.
3. **Convertir `review_id` en `UUID` para que `mastery` no encaje.** FastAPI genera el patrón de la
   ruta con el conversor de cadena y valida el tipo **después** de encajar, así que la petición
   llegaría igualmente a esa ruta y contestaría un 422 en lugar de un 404: el mismo problema con otro
   número de estado.
