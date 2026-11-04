# Especificación — OpoFuente, temario de C1

Estado: **borrador para revisar**. Alcance recortado a propósito.

## Objetivo

Una sola cosa: **el temario de C1**, consultable y con el avance de estudio. Todo lo demás queda fuera de esta tanda.

En el repositorio, C1 es **TAI** (Técnico Auxiliar de Informática). Hay una rama `f3-epigrafes-tai` con **134 epígrafes derivados del título oficial**: esa es la base del índice.

## Familia y recetas

Familias **F (documentación)** para la consulta del temario y **A (panel)** para la administración.

Esto no es una web de marketing ni un chat: es documentación navegable con estado de avance.

## Pantallas de esta tanda

### 1. Índice del temario
- [ ] Árbol de temas y epígrafes, en el orden oficial
- [ ] Búsqueda que **perdona tildes** (`buscar` encuentra `Búsqueda`)
- [ ] Marca visible de lo estudiado
- [ ] Estado vacío: «sin tema seleccionado»

### 2. Ficha de tema
- [ ] El texto del epígrafe
- [ ] Los apuntes del tema, si existen
- [ ] Las preguntas asociadas al tema
- [ ] Navegación anterior / siguiente dentro del temario
- [ ] Marcar como estudiado, con la fecha

### 3. Avance
- [ ] Porcentaje por bloque y total
- [ ] Qué queda, ordenado por lo que falta
- [ ] Última vez que se estudió cada tema

## Estados obligatorios

- [ ] Vacío · [ ] Cargando · [ ] Error · [ ] Sin permiso

## Decisiones que hay que tomar antes de implementar

| Decisión | Por qué importa | Estado |
|---|---|---|
| ¿Qué es un «tema»: epígrafe oficial, bloque o capítulo? | define el índice entero | **pendiente** |
| ¿Cuántos niveles tiene el árbol? | decide la navegación | **pendiente** |
| ¿El avance es por epígrafe o por tema? | decide el porcentaje | **pendiente** |
| ¿Qué se hace con el material de otras oposiciones del banco? | hay `GUARDIA-CIVIL`, `celador` y más en `E:\OpoFuente-datos` | **pendiente** |
| ¿Se usa `main` como rama de trabajo? | hay **85 ramas**; abrir más es perder el hilo | **recomendado: sí** |

## Fuera de alcance (a propósito, y esto es importante que quede escrito)

- **Batería de preguntas y simulacros**: no en esta tanda.
- **Ciclo de estudio del alumno** (resultado, repaso, fallos, progreso): no.
- **Panel de administración completo**: solo lo mínimo para cargar el temario.
- **Cualquier otra oposición que no sea C1/TAI.**

Si un agente propone meter alguno de estos, se rechaza: ya existen en otras ramas y volverán cuando el temario esté cerrado.

## Riesgos

- **85 ramas locales.** La de trabajo es `main` (`6483111`). Las demás son historia. No se abren ramas nuevas por tarea.
- El banco de datos vive en E: con junction desde `F:\OpoFuente`. **No mover ni copiar el banco** mientras haya un servidor usándolo.
- `DEBT.md` (100 KB) tiene deuda acumulada: leerla antes de tocar el modelo de datos.

## Puertas antes de dar una pantalla por buena

1. Pruebas en verde (`python -m pytest -q`).
2. `ai-design-check` o la lista de diez.
3. Ojos frescos con este fichero y una captura.
