# La puerta 18 está en rojo por la pantalla de Revisión, y no por estas ramas (5 de octubre de 2026)

Al pasar las puertas sobre `e5ce278` (el commit que junta el arreglo de las sesiones sin etiqueta y el
de los apuntes por tema): **17 de 18 en verde** y la 18 (E2E, Playwright) en rojo, con **53 de 54**
pruebas pasando.

## La que falla, y por qué

```
x  30 [chromium] tests\e2e\review.spec.ts:397:1
   E2E-03 revisión: accesibilidad sin violaciones automatizables (35.7s)
   Test timeout of 30000ms exceeded.
```

No es una violación de accesibilidad: es un **tiempo agotado**. La prueba tiene 30 s (el límite por
defecto de Playwright) y la pantalla de Revisión tarda ~36 s en quedar lista en el entorno de la E2E.

## Que no es culpa de estas ramas, medido

Se pasó la misma prueba, sola, sobre el commit **anterior** a las dos ramas (`a19d13a`, que es `main`
tal como estaba):

```
ok 1  review.spec.ts:186  revisión en lote  (42.3s)
x  2  review.spec.ts:397  accesibilidad     (36.9s)  →  falla igual
```

Y sobre el commit de las ramas, cuatro veces seguidas: 36,5 s · 37,1 s · 35,7 s · 36,9 s. Es decir,
falla igual **con y sin** los cambios; el cambio que lo decide es la velocidad de la pantalla, no el
código de estas ramas. (En dos pasadas de puertas de por la mañana sí pasó, con el mismo código: está
justo en el límite.)

## Qué lo arregla

Es P2.2 del plan, y ahora bloquea una puerta, así que sube de prioridad: la pantalla de Revisión pinta
**cada propuesta dos veces** («material» y su texto extraído), con 88 propuestas en los datos de prueba,
y la tabla se sale por la derecha. Mientras no se arregle, la puerta 18 no se puede declarar verde sin
tocar su configuración, y eso no se hace.

Lo que **no** se ha hecho, a propósito: subir el límite de tiempo de esa prueba. Eso sería relajar el
juez para que pase, y el problema real (una pantalla que tarda 36 s) seguiría ahí.
