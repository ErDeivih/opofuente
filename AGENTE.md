# Ficha del agente — OpoFuente — temario comun de oposiciones de informatica C1

**Id en el panel**: `opofuente`
**Ruta**: `F:\Proyectos\opofuente`
**Rama de trabajo**: `main`
**Familia de interfaz**: F (documentacion) + A (panel) — ver `F:\Inforepositorios\indice\RECETAS-UI.md`

## Mision

Un temario comun a todas las convocatorias de informatica C1 de Espana, basado en el de TAI y enriquecido con lo que aparece en las demas. Un solo temario, referenciado por cada convocatoria: no se copia por convocatoria.

## Como trabajas

Lee y sigue `F:\EspacioCodigo\_flujo-dsh\PROTOCOLO-AUTONOMIA.md`. En resumen:

- **Nivel 1**: decide solo y ejecuta (refactor, pruebas, docs, rendimiento, accesibilidad).
- **Nivel 2**: decide solo pero lo anotas en `DECISIONES.md` (pantallas ya especificadas, dependencias pequenas, esquema reversible).
- **Nivel 3**: paras y preguntas (alcance, datos, credenciales, dinero, otro proyecto, ramas).
- **Una tarea bloqueada no para la sesion**: la marcas y sigues con la siguiente.

Antes de escribir codigo, lee `ESPECIFICACION.md`. Si no existe o esta vacia, **eso** es la tarea.

## Tu backlog

Vive en `BACKLOG.md`. Nunca puede tener menos de 5 tareas listas. Si baja, generas mas de estas tres fuentes:

1. **Competencia**: que hacen las apps del sector y que nos falta.
2. **Huecos de la especificacion**: pantallas prometidas sin hacer, estados sin cubrir.
3. **Deuda tecnica**: pruebas, duplicacion, dependencias.

## Investigacion inicial encomendada

Como organizan el temario las academias de informatica C1 y los portales de oposiciones, y que se repite en todas las convocatorias.

Se deja en `INVESTIGACION.md`: que se ha mirado, que hace la competencia, que nos falta y **una propuesta concreta de tarea**.

## Primera tarea

Leer el modelo de datos actual y escribir la propuesta de temario unico con convocatorias que lo referencian.

## Al terminar cada sesion

Deja `ESTADO-AGENTE.md` actualizado con este formato exacto. De ahi lo lee el panel:

```
titulo: OpoFuente — temario comun de oposiciones de informatica C1
estado: en-curso
tarea: lo que estabas haciendo
nivel: 1 | 2 | 3
siguiente: lo proximo que haras
bloqueado: la pregunta de nivel 3, si la hay
fecha: AAAA-MM-DD
```

Y recuerda: **sin commit y sin push, no esta terminado.**


## Consultar el catálogo de repositorios (no busques a mano)

Antes de buscar una librería, una herramienta o una referencia, pregunta al catálogo personal de David: más de 500 fichas documentales y ~1.400 repositorios dentro de recopilaciones, con licencia real, límite y recomendación.

```powershell
python F:\Inforepositorios\consultar.py "<lo que necesitas>" -n 5 --json
```

Puedes hacer **varias consultas seguidas** en la misma tarea, una por necesidad (OCR, scraping, PDF, agentes…); cada consulta es independiente y tarda 2-4 s. Devuelve los mejores candidatos con su licencia y la ruta de su ficha; abre solo esas fichas y mira la sección 9 (cuándo no elegirlo) y la 6 (licencia). Si solo quieres repositorios del catálogo, añade `--tipo ficha`. Es evidencia documental: nada se ha clonado, instalado ni ejecutado, así que da **candidatos que merecen revisión, no la garantía de que algo funcione**. Guía: `F:\Inforepositorios\RAG.md`. Para una palabra exacta: `& F:\Inforepositorios\scripts\Buscar-Todo.ps1 -Texto <término>`.
