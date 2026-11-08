# Protocolo de autonomía

Cómo trabaja un agente sin esperarte a ti para todo, y sin liarla. Este documento existe porque **si todas las decisiones pasan por David, el sistema no avanza**: con seis proyectos abiertos, esperar su respuesta cada vez deja el trabajo parado semanas.

La solución no es «que decida todo». Es **tres niveles de decisión** y un **motor de tareas** que nunca se queda sin trabajo.

## Los tres niveles

### Nivel 1 — Decide solo y ejecuta

No pregunta. Lo hace, lo prueba, lo sube y lo cuenta.

- Refactorizar código interno sin cambiar comportamiento.
- Arreglar un error del que se puede escribir una prueba.
- Escribir y arreglar pruebas.
- Documentación, comentarios, mensajes de commit, nombres.
- Rendimiento y accesibilidad **dentro** de lo especificado.
- Elegir entre librerías **que ya están** en el proyecto.
- Actualizar dependencias menores con las pruebas en verde.
- Escribir y mantener su `BACKLOG.md`.

### Nivel 2 — Decide solo, pero lo deja escrito y avisa

No bloquea la sesión: lo hace y lo anota en `DECISIONES.md` del proyecto con el motivo. David lo revisa cuando quiere.

- Una pantalla nueva **que ya está en la especificación**.
- Cambios de diseño menores siguiendo el sistema visual ya establecido.
- Una dependencia nueva, pequeña y justificada.
- Cambios de esquema de datos **reversibles** y con migración.
- Cambiar el orden de las tareas de su backlog.

### Nivel 3 — Para y pregunta

Se detiene en seco. Y, mientras espera, **sigue con otra tarea**.

- Cambiar el alcance de la especificación (añadir o quitar pantallas).
- Borrar o mover datos, o cualquier migración destructiva.
- Credenciales, dinero, cuentas, permisos.
- Tocar **otro** proyecto o repositorio.
- Cambiar de rama de trabajo o abrir ramas nuevas.
- Decisiones de producto: qué entra en la versión, qué se recorta.
- Instalar herramientas nuevas en el sistema.

## El motor: el agente se pone tareas

Cada proyecto tiene un `BACKLOG.md`. La regla que quita la dependencia:

1. **Nunca puede quedarse sin al menos 5 tareas listas.**
2. Cada sesión: comprobar estado → elegir la tarea de **más valor** → ejecutar → pasar puertas → commit y push → actualizar backlog.
3. Si al elegir se encuentra con una tarea de **Nivel 3**, la marca `esperando decisión` con la pregunta exacta **y continúa con la siguiente**. Nunca se queda quieto.
4. Si el backlog baja de 5, antes de seguir **genera tareas nuevas** con una de estas tres fuentes:
   - **Investigación de la competencia**: qué hacen las apps del sector, qué les falta, qué se puede copiar con criterio.
   - **Huecos de la especificación**: pantallas prometidas sin implementar, estados sin cubrir (vacío, carga, error, sin permiso), casos límite.
   - **Deuda técnica**: pruebas que faltan, código duplicado, dependencias viejas, accesibilidad.

### El tipo de tarea que David ha pedido: investigar

Una tarea de investigación **siempre** termina en un fichero, no en una opinión:

```
INVESTIGACION.md  →  qué se ha mirado (con enlace o captura),
                     qué hace la competencia,
                     qué nos falta,
                     qué proponemos adoptar y por qué,
                     y una propuesta concreta de tarea Nivel 1 o 2
```

Investigación sin propuesta ejecutable es tiempo perdido. Y **si la propuesta cambia el alcance, es Nivel 3**: se pregunta.

## Cómo se escribe el informe de cada sesión

Al final de cada sesión, el agente deja en `ESTADO-AGENTE.md` del proyecto, con este formato exacto, porque de ahí lo lee el panel:

```
titulo: Garmin Athletics — panel de entrenamiento y editor de gimnasio
estado: en-curso
tarea: implementando la tabla de ejercicios del editor
nivel: 2
siguiente: temporizador de descanso con la pantalla apagada
bloqueado: ¿el frontend nuevo mantiene las 8 pestañas? (nivel 3)
fecha: 2026-11-04
```

Ese bloque es lo que hace que David pueda mirar **un solo panel** y saber qué hace cada proyecto sin abrir seis chats.

## Lo que el agente no hace nunca, ni con autonomía

- Inventar datos o métricas que no ha medido.
- Decir «hecho» sin push.
- Declarar que algo funciona sin haberlo ejecutado.
- Tocar secretos o el `.env`.
- Saltarse una puerta que falla.

## Por qué esto sí quita dependencia y lo anterior no

Lo anterior era: **David decide el alcance, la tarea y el orden**. Eso es un cuello de botella.

Esto es: **David decide el alcance y los límites; el agente decide el cómo, el cuándo y el orden, y se busca su propio trabajo.** David revisa, no dirige.

Y el mecanismo concreto que lo hace posible: **una tarea bloqueada no para la sesión**. Si hay cinco tareas listas, siempre hay algo que hacer.

## Obligaciones permanentes de cada agente

Estas tres no son opcionales y no dependen de que David las recuerde.

### 1. Usar las skills y plugins instalados

Antes de improvisar, mira si ya hay una skill que lo hace. Las instaladas y para qué sirven están en
`SKILLS-INSTALADAS.md`. Las que más importan:

- **Arquitectura y UI/UX**: `claude-design-system` para el sistema de diseño, `claude-design` para
  revisar pantallas en artboards, `claude-dashboard` para paneles con datos.
- **Tipografía, color y animación**: se deciden en el sistema de diseño, no pantalla a pantalla.
- **Pruebas y buen software**: cada rebanada termina con pruebas en verde; no se declara terminado
  sin haberlas ejecutado.
- **Datos**: `data_profile`, `data_clean` y `data_verify` antes de fiarse de una ingesta.

Un plugin no sustituye al criterio: si la skill no encaja, se usa el criterio propio y se dice.

### 2. Revisar el catálogo de repositorios

En `F:\Inforepositorios` hay 468 fichas de repositorios y 1.424 repositorios dentro de
recopilaciones, con licencia, límite y recomendación. **Cada cierto tiempo, y siempre que necesites
una pieza nueva**, busca ahí antes de inventarla:

```powershell
& F:\Inforepositorios\scripts\Buscar-Todo.ps1 -Texto <lo que necesitas>
& F:\Inforepositorios\scripts\Buscar-Repos.ps1 -Categoria <area>
```

Se propone lo que sirve **con su ficha, su licencia y su límite**. No se adopta por intuición ni por
estrellas.

### 3. Dejar el estado legible

`ESTADO-AGENTE.md` con el formato exacto, `BACKLOG.md` con al menos 5 tareas, y **commit y push**.
Sin eso, el panel de proyectos no puede vigilar y David no puede coordinar.

### 0. Leer la doctrina antes de construir

`DOCTRINA-CALIDAD.md` dice **cómo se pruea, cómo se diseña y qué se considera terminado** en
todos los proyectos. Es de lectura obligatoria al empezar cada sesión. En resumen:

- Las pruebas cubren **flujos**, no detalles internos. **Se pueden borrar y rehacer** si el flujo
  cambia: un rediseño se lleva sus pruebas y trae las nuevas en el mismo cambio. Una prueba que se
  rompe al renombrar una función no protege el producto, protege el código de que lo mejoren.
- Hay disciplina instalada para esto: `grill-requirements` → `red-green-tdd` → `delivery-review` →
  `delivery-proof`.
- La interfaz se construye sobre un **sistema de diseño**, con contraste AA calculado, escala de
  espaciado y tipografía, animación de 120–220 ms con propósito y los cuatro estados por pantalla.
- La autorización se comprueba **en el servidor**; hay matriz de permisos escrita.
- Antes de desplegar: checklist OWASP, dependencias revisadas, **restauración de backup probada**,
  plan de vuelta atrás y normativa local.
- Lo que David diga en el chat de coordinación **se escribe en los documentos del proyecto**. Un
  hallazgo que no está escrito no existe para el que construye.
## POLÍTICA DE GITHUB (2026-11-04) — obligatoria

David ha agotado la cuota gratuita de GitHub y **todas las ejecuciones de GitHub Actions fallan**.

- **PROHIBIDO usar GitHub Actions.** Nada de workflows, nada de CI en la nube. Las pruebas, el
  lint y el build se ejecutan **en local**, en la máquina de David.
- **El push no es continuo.** Se sube **cuando David lo pida**, o como mucho **una vez al final de
  una sesión de trabajo real**. Con 15 proyectos y commits cada pocos minutos, la cuota se agota.
- **Commit local sí, push selectivo.** Se puede comitear en local todo lo que haga falta; lo que se
  raciona es el envío a GitHub.
- Antes de hacer push, comprobar que es necesario: ¿hay trabajo real que merezca respaldo? Si es un
  cambio de una línea de documentación, se puede esperar.
- Si un push falla por cuota o por red, **no se reintenta en bucle**: se anota y se sigue.
- Nada de crear repositorios nuevos sin que David lo pida.
### La interfaz no habla de cómo está hecha

Antes de dar una pantalla por buena, recorrer cada texto y preguntar: **«¿esto le sirve al cliente para decidir o actuar?»**. Si no, se borra. Nada de «el token dura 30 días», explicaciones de cómo se calcula algo, pies de página describiendo el producto ni métricas de relleno. Está desarrollado en `DOCTRINA-CALIDAD.md` §8 y §9.