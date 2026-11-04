# Especificación — OpoFuente, todas las oposiciones

Estado: **borrador para revisar**. Alcance redefinido el 2026-11-04.

## Objetivo

Una plataforma de **temario para todas las oposiciones** de David, no solo una. **TAI (C1) es la semilla**: su estructura, sus 134 epígrafes y su forma de organizar el temario son el modelo que se generaliza a las demás.

Debe poder alojar **C1 y C2** y admitir más temas y más oposiciones sin rehacer nada.

## El cambio de alcance respecto al borrador anterior

Antes: «solo C1». Ahora: **un modelo de datos que aguante todas**, con TAI como primera oposición cargada.

Eso cambia lo que hay que decidir primero. Ya no es «qué es un tema» en una oposición, sino:

| Decisión | Por qué manda ahora | Estado |
|---|---|---|
| ¿La oposición es una entidad de primer nivel, o un atributo? | decide el modelo entero | **pendiente** |
| ¿Un tema puede pertenecer a varias oposiciones a la vez? | hay temarios compartidos entre C1 y C2 | **pendiente** |
| ¿El temario es por convocatoria, por año o estable? | cambia si hay versiones del mismo tema | **pendiente** |
| ¿Cuántos niveles: oposición → bloque → tema → epígrafe? | define la navegación y el avance | **pendiente** |
| ¿El avance es por oposición, por tema o por epígrafe? | decide el porcentaje | **pendiente** |

**Lo que ya está, y sirve de molde**: 134 epígrafes de TAI derivados del título oficial (rama `f3-epigrafes-tai`).

## Familia y recetas

Familias **F (documentación)** para consultar el temario y **A (panel)** para administrarlo. Documentación navegable con estado de avance, no una web de marketing ni un chat.

## Pantallas de esta tanda

### 1. Selector de oposición
- [ ] Lista de oposiciones con su temario cargado
- [ ] Estado vacío: «todavía no hay oposiciones»
- [ ] Cargando y error

### 2. Índice del temario de una oposición
- [ ] Árbol bloque → tema → epígrafe, en el orden oficial
- [ ] Búsqueda que **perdona tildes**
- [ ] Marca visible de lo estudiado
- [ ] Navegación de vuelta al selector

### 3. Ficha de tema
- [ ] Texto del epígrafe
- [ ] Apuntes del tema, si existen
- [ ] Preguntas asociadas
- [ ] Navegación anterior / siguiente
- [ ] Marcar como estudiado, con fecha

### 4. Avance
- [ ] Por bloque y por oposición
- [ ] Qué queda, ordenado por lo que falta

## Estados obligatorios

- [ ] Vacío · [ ] Cargando · [ ] Error · [ ] Sin permiso

## Fuera de alcance de esta tanda

- **Batería de preguntas y simulacros**: no todavía.
- **Ciclo de estudio del alumno** (resultado, repaso, fallos): no.
- **Panel de administración completo**: solo lo mínimo para cargar un temario.

Meter contenido multi-oposición **no** es meter todo el producto: primero el modelo y el temario, después el resto.

## Riesgos

- **85 ramas locales.** La de trabajo es `main` (`6483111`), que está activa en el worktree `F:\temp-opofuente\opofuente-restaurado`. No abrir ramas por tarea.
- El banco de datos (53,7 GB) vive en `E:\OpoFuente-datos` con junction desde `F:\OpoFuente`. **Y no es solo informática**: tiene `GUARDIA-CIVIL`, `celador` y `apuntes-tai-copia`, que ahora sí son material relevante porque el producto pasa a ser multi-oposición.
- `DEBT.md` (100 KB): leerla antes de tocar el modelo de datos.

## Puertas antes de dar una pantalla por buena

1. `python -m pytest -q` en verde.
2. `ai-design-check` o la lista de diez de las recetas.
3. Ojos frescos: subagente sin historial con este fichero y una captura.
