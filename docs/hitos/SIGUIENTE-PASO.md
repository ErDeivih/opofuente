
# El remate de la fase 3, terminado — para que Claude lo revise

**Estado: los nueve puntos, hechos y medidos.** `main = 998f20a`, árbol limpio, **18/18 en una sola
corrida** (54:12 minutos, cero fallos).

## Los nueve puntos, con su cifra

| # | qué era | cómo está |
|---|---|---|
| 1 | **5.939 privadas borradas por M1** | **archivadas**, no borradas: 20.322 explicaciones, 11.315 privadas, 0 preguntas con dos vivas |
| 2 | **el repaso no estaba en el menú** | `/repaso` en el menú, y **9 tarjetas reales** servidas por `scripts\api.ps1` |
| 3 | **la portada y `/inicio`** | «Hoy» es la portada, `/inicio` redirige, `StudentHomePage` **borrada** con su prueba |
| 4 | **el simulacro sin supuesto** | **el supuesto real**: 25 preguntas, 5 de reserva, **450 claves recuperadas** y el enunciado servido en la sesión |
| 5 | **el reloj en una práctica de 3** | **solo en simulacros, exámenes y tests con «con tiempo»**: medido, `null` y `10` |
| 6 | **títulos internos colados** | **cero en la base real**, y un guardián en la puerta 17 |
| 7 | **las 423 «sin material» y el OCR** | las 423 **fuera de tests y repasos** (bandeja: 12 decisiones); **el OCR intentado y descartado con su cifra: 59 de 300** |
| 8 | **el recorrido viejo** | **85 de 85 pantallas**, 80 PNG en `artifacts/recorrido-final-2/`, sobre copia verificada y **paquete de `main`** |
| 9 | **18/18** | **una corrida, cero fallos** |

## Lo que el recorrido destapó y no se veía

**El cliente de la API tenía la base por defecto sin `/api/v1`**, así que **69 llamadas acababan en
404** —entre ellas el plan de la portada—. **Estaba roto siempre y solo salió al mirar la aplicación de
verdad**, con la base del propietario. **Arreglado en `apiFetch`**, el único sitio por el que pasan
todas.

## Lo que queda abierto, dicho

- **`first-run` y la portada**: resuelto en la fase anterior (la prueba describe `HoyPage`).
- **La «nota por parte» del simulacro** no se ha destacado en la pantalla del resultado: el dato está,
  la pantalla no lo resalta.
- **La cola del día sirve tarjetas, no fallos vencidos**: `cola_del_dia` ya sabe entrelazar y
  `review_items` ya existe, pero la API no los une. **Es un cambio de contrato**, no un adorno.
- **Los cuestionarios de 2018 quedan fuera**: 59 de 300 con el intento acotado.

## Lo que necesita una decisión del propietario

**Nada bloqueante.** Lo de `docs/PARA-EL-PROPIETARIO.md` sigue en pie: las 423 salen de tests **y
vuelven solas** si un tema nuevo cubre su materia.

## La lección, para quien siga

**Cada puerta destapa la siguiente.** Este remate ha necesitado **cinco correcciones** que ninguna
revisión mía vio, y **una de ellas era un comentario que prometía lo que el código no hacía**. **La
batería de las 18 no es una lista de trámites: es una cadena, y hasta recorrerla entera no se sabe
dónde está el eslabón flojo.**
