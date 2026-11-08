# Doctrina de calidad

Lo que David ha pedido y lo que **todo agente debe aplicar** en cada proyecto. Este documento manda sobre el estilo de cada agente: si algo aquí choca con una costumbre, manda esto.

## 1. Las pruebas: ni imprescindibles ni intocables

David lo ha dicho con claridad: **hacen falta pruebas, pero no una enredadera que impida avanzar**. El problema no son las pruebas: es el tipo de prueba.

### Prueba lo que el usuario ve, no cómo está hecho por dentro

| Bien | Mal |
|---|---|
| «Creo una rutina, la guardo y aparece en la lista» | «`buildRoutineHelper()` llama a `normalize()` 3 veces» |
| «Un usuario sin rol de administrador recibe 403» | «el mock del repositorio fue invocado con este objeto» |
| «La clasificación ordena por puntos y luego por diferencia» | «el componente tiene 4 `div` anidados» |

Una prueba que se rompe al cambiar un nombre de función o un `<div>` no protege al producto: **protege el código de que lo mejoren**.

### Reglas

1. **Una prueba por flujo, no por función.** El flujo es el recorrido real: entrar → hacer la tarea → guardar → ver el resultado.
2. **El camino crítico se prueba de punta a punta.** Los caminos críticos son: autenticación, la tarea principal del producto, guardar, y cualquier cosa que mueva dinero o datos personales.
3. **Nada de pruebas de detalle interno**: funciones privadas, estructura del DOM, textos exactos de la interfaz, número de llamadas a colaboradores internos. Eso es la enredadera.
4. **Una prueba debe poder borrarse.** Si al borrarla el producto sigue funcionando y nadie nota nada, **era ruido**. Se borra.
5. **Un rediseño se lleva sus pruebas.** Si se rehace una pantalla, un flujo o una funcionalidad, **se escriben las pruebas del flujo nuevo y se borran las del viejo en el mismo cambio**. No se dejan zombis «por si acaso».
6. **Nunca se adapta una prueba para que pase.** Si una prueba falla, se arregla el producto o se demuestra que la prueba medía lo que no debía. Adaptarla para que pase sin cambiar el comportamiento es mentir.
7. **Presupuesto**: una suite que tarda más de 5 minutos no se ejecuta y por tanto no protege. Si tarda más, se separa: rápido en cada cambio, lento antes de entregar.
8. **El número de pruebas no es una medalla.** 1.400 pruebas verdes no valen nada si el flujo de compra está roto.

### La puerta de verdad

No es «las pruebas pasan». Es: **el flujo completo se puede ejecutar y no falla, y hay evidencia de haberlo ejecutado**. Una prueba en verde sin haber visto el flujo funcionar es una hipótesis.

### Cómo se usa la disciplina `doublecheck`

Está instalada en DSH y es la forma correcta de aplicar esto sin enredarse:

1. **`grill-requirements`** — antes de escribir código: objetivo, alcance, criterios de aceptación, modos de fallo, prioridades y **no-objetivos**. Se guarda en el repo.
2. **`red-green-tdd`** — una prueba que falla (rojo), el cambio mínimo, verde. Para el comportamiento nuevo, no para cada función.
3. **`delivery-review`** — revisión adversarial antes de decir «hecho»: asumir que el trabajo falla y buscar la objeción más fuerte.
4. **`delivery-proof`** — el informe de entrega con la evidencia.

Aplica a: comportamiento nuevo y flujos. **No** a cambios de estilo, textos o configuración trivial.

## 2. La interfaz: esto es lo que vende

Un producto desplegable tiene que parecer y sentirse profesional. El mínimo, no negociable:

- **Sistema de diseño primero.** Tokens de color, tipografía, espaciado y radios en un solo sitio. Hay skill: `claude-design-system`. Ninguna pantalla se escribe antes.
- **Contraste AA calculado**, no estimado. Texto legible sobre cada fondo.
- **Escala de espaciado** (4/8/12/16/24/32/48) y **escala tipográfica** corta (3 o 4 tamaños). Nada de tamaños inventados por pantalla.
- **Animación con propósito y discreta**: 120–220 ms, para explicar un cambio de estado, nunca para decorar. Respetar `prefers-reduced-motion`.
- **Interacción familiar**: lo que ya sabe usar el cliente (menú arriba o lateral, tarjetas, tablas que se pueden ordenar, formularios con etiquetas visibles). Nada de interacciones originales que haya que aprender.
- **Los cuatro estados de cada pantalla**: vacío, cargando, error y sin permiso. Una pantalla sin estado vacío está a medias.
- **Móvil de verdad**: se usa a 400 px de ancho, sin scroll horizontal.
- **Accesibilidad**: navegable con teclado, foco visible, `label` en los campos, contraste, alt en imágenes.
- **Sin texto de relleno**: ni «bienvenido a nuestra plataforma» ni frases que no aportan.

Antes de dar una pantalla por buena: `dsh-design-qa` (fidelidad al diseño) y ojos frescos.

## 3. Datos y peticiones

- **Paginación siempre** que la lista pueda crecer. Nunca «traigo todo y filtro en el cliente».
- **Índices** en las columnas por las que se filtra y se ordena. Una pantalla que tarda 3 segundos es una pantalla rota.
- **Sin N+1**: si pintar 20 filas lanza 40 consultas, está mal.
- **Contrato documentado** de cada endpoint (qué devuelve, qué errores tiene).
- **Consultas optimizadas medidas**, no supuestas: se mide el tiempo de la consulta real.

## 4. Seguridad y roles

- **La autorización se comprueba en el servidor**, siempre. Ocultar un botón no es un permiso.
- **Matriz de permisos escrita**: quién puede hacer qué por rol y por ámbito (personal / equipo / club).
- **Secretos fuera del repositorio**, y comprobado antes de cada commit.
- **Validar toda entrada** en el servidor.
- **Sesiones**: caducidad, cierre, y sin datos sensibles en el cliente.
- **Registro de auditoría** de las acciones que importan: quién cambió qué y cuándo.

## 5. Antes de desplegar (cuando llegue el momento)

1. **Auditoría de seguridad** con checklist OWASP: inyección, autenticación rota, exposición de datos, control de acceso, configuración, dependencias vulnerables, registro y monitorización.
2. **Dependencias revisadas** (`npm audit`, `pip-audit`).
3. **Backups y restauración probada** — un backup que no se ha restaurado nunca no es un backup.
4. **Plan de vuelta atrás**: si el despliegue falla, cómo se vuelve.
5. **HTTPS, cabeceras de seguridad, límite de peticiones.**
6. **Normativa local**, cuando se despliegue de verdad: protección de datos (RGPD/LOPDGDD), aviso legal, consentimiento de cookies, accesibilidad (WCAG 2.1 AA / UNE-EN 301549), y las condiciones del sector.
7. **Monitorización y registro** para enterarse de que algo se rompe antes que el cliente.

## 6. Prohibido, en cualquier proyecto

- Declarar «hecho» sin commit, sin push y sin haber ejecutado.
- Decir que algo funciona sin haberlo visto funcionar.
- Adaptar una prueba para que pase sin cambiar el comportamiento.
- Copiar contenido ajeno sin licencia.
- Dejar una suite roja y seguir construyendo encima.
- Inventar cifras que no se han medido.

## 7. Lo que David diga, va al documento

Cuando David explique algo en el chat de coordinación, **no se queda en el chat**: se escribe en el `ESPECIFICACION.md`, en el `AGENTE.md` o aquí. Los agentes leen documentos, no conversaciones. Un hallazgo que no está escrito no existe para el que construye.
## 8. LA INTERFAZ NO HABLA DE CÓMO ESTÁ HECHA (regla de David, 2026-11-05)

David lo ha dicho claro y vale para **todos los proyectos**: las apps están llenas de textos que al cliente no le interesan y que son cosas de desarrollador.

### Prohibido en la interfaz

- **Detalles técnicos**: «el token dura 30 días», «sesión caducada por el servidor», «caché vacía», nombres de endpoints, IDs internos.
- **Explicaciones de cómo se calcula algo**: «zonas según lo ocurrido en las últimas temporadas», «calculado con la media de…», «este porcentaje se obtiene de…». El cálculo se hace bien **y se calla**.
- **Pie de página con la descripción del producto**: «academia de datos, estadística, machine learning…». Si el producto es bueno, se entiende solo.
- **Métricas de relleno**: «% de conceptos vistos», «has visitado 12 páginas». Solo se enseña lo que el usuario necesita para decidir o actuar.
- **Avisos internos de administración** (versión, entorno, estado del sincronizador).
- **Textos de relleno** que no aportan nada: párrafos introductorios, «bienvenido a…», «descubre…».

### Qué sí va

- Lo que el usuario necesita **para decidir o actuar**: qué es esto, qué cuesta, dónde, cuándo, qué hago ahora.
- **Explicaciones de las medidas que ve**, cuando le ayudan a entender un dato: «carga aguda: lo que has entrenado esta semana», «20 % más barato por kilo».
- Etiquetas cortas y nombres claros.

### Cómo se comprueba

Antes de dar una pantalla por buena: recorrerla y preguntar de cada texto **«¿esto le sirve al cliente para decidir o actuar?»**. Si la respuesta es no, se borra. Y no se sustituye por otro texto: se borra.

## 9. Nombres de marca y de personas

- **No usar el nombre de otra empresa como nombre de la app.** «Garmin» es una marca registrada: si el producto se llama Garmin Athletics, hay que renombrarlo. Cualquier app inspirada en otra se llama distinto.
- **Menores de edad**: si la federación tiene consentimiento de tratamiento, **el nombre se publica** (en FACYLF así es). Las **fotos** quedan sin publicar de momento.