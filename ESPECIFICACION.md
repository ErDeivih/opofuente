# Especificación — OpoFuente, oposiciones de informática C1

Estado: **borrador para revisar**. Alcance corregido el 2026-11-04.

## Qué es y qué no es

**Es**: una plataforma de temario para **oposiciones de informática de España de cualquier administración** — ayuntamientos, diputaciones, comunidades, sanidad, Estado. Grupo **C1** (y su escalón C2 si comparte temario).

**No es**: celador, Guardia Civil ni ninguna oposición que no sea de informática. Ese material existe en el banco pero **no entra en el producto**.

## El problema real que resuelve

Las distintas oposiciones C1 de informática **no comparten temario entre sí**. Cada convocatoria publica el suyo. La solución no es copiar uno: es hacer **un temario general basado en el de TAI**, y enriquecerlo con lo que aparece en las demás convocatorias.

Eso ya está empezado, y bien, en:

```
F:\aprendizaje\empleo-informatica\
```

| Fichero | Qué es |
|---|---|
| `minicerebro\temario-c1.md` (9,1 KB) | **el temario único**: construido desde bases reales de 2026 y del TAI del Estado, con bloques y temas numerados |
| `fuentes\oposicionesinformatica\c1.txt` (y a1, a2, c2) | convocatorias de informática de toda España con su enlace |
| `fuentes\sacyl\C1 Tecnico Especialista en Informatica\` | **convocatorias y plantillas de examen reales** de Ávila, León, Palencia, Salamanca, Soria, Valladolid y Zamora |
| `fuentes\sacil\...`, `cyl_*.md`, `jcyl_*.html` | bases de Castilla y León, A1/A2/C1 |
| `minicerebro\convocatorias.csv`, `oposiciones-web.md`, `bolsas.md` | inventario de convocatorias y bolsas |
| `alertas\` | vigía de nuevas oposiciones de informática |

Datos que ese temario ya deja escritos y que el producto debe respetar:

- Las C1 que publican temario tienen **unos 40 temas**.
- Hay materias que **se repiten en todas**: régimen local, redes, sistemas operativos y servidores, copias de seguridad y continuidad.
- **Formato típico del examen**: test de **50 preguntas** (a veces 40–90), con penalización de **1/3 o 1/4** por error, **más un supuesto práctico**. Hay que sacar **5 sobre 10** en cada parte.

## El modelo de datos: es lo primero que hay que decidir

| Decisión | Por qué manda | Estado |
|---|---|---|
| ¿Una **convocatoria** (ayuntamiento, año) es entidad propia, o solo una etiqueta sobre el tema? | decide si el temario es único o hay N versiones | **pendiente** |
| ¿Un tema puede pertenecer a **varias convocatorias** a la vez? | el temario único se solapa con todos | **pendiente** |
| ¿El temario general es **una** entidad y las convocatorias lo *referencian*, o cada convocatoria tiene su copia? | es la decisión que evita duplicar 40 temas por convocatoria | **pendiente** |
| ¿Niveles: bloque → tema → epígrafe, o hay uno más? | define la navegación y el avance | **pendiente** |
| ¿El avance es por tema, por bloque o por convocatoria? | decide el porcentaje | **pendiente** |

Recomendación: **un temario general único, y cada convocatoria lo referencia** con sus particularidades (temas añadidos, suprimidos, ponderación). Copiar el temario por convocatoria es el camino a 40 temas × 50 convocatorias.

## Familia y recetas

Familias **F (documentación)** para consultar el temario y **A (panel)** para administrarlo. Documentación navegable con estado de avance; no es una web de marketing ni un chat.

## Pantallas de esta tanda

### 1. Índice del temario general
- [ ] Árbol bloque → tema, en el orden oficial
- [ ] Búsqueda que **perdona tildes**
- [ ] Marca visible de lo estudiado

### 2. Ficha de tema
- [ ] Texto del tema
- [ ] Apuntes, si existen
- [ ] **En qué convocatorias aparece** (esto es lo que hace útil el temario único)
- [ ] Navegación anterior / siguiente
- [ ] Marcar como estudiado, con fecha

### 3. Avance
- [ ] Por bloque y total
- [ ] Qué queda, ordenado por lo que falta

### 4. Convocatorias (solo lectura)
- [ ] Lista con administración, año y grupo
- [ ] Ficha con sus bases y sus particularidades de temario

## Estados obligatorios

- [ ] Vacío · [ ] Cargando · [ ] Error · [ ] Sin permiso

## Fuera de alcance de esta tanda

- **Test y simulacros con penalización**: no todavía, aunque el formato ya está documentado.
- **Supuesto práctico**: no.
- **Ciclo del alumno** (resultado, repaso, fallos): no.
- **Cualquier oposición que no sea de informática**.
- **El banco de 53,7 GB**: no es la fuente de este producto. La fuente es `F:\aprendizaje\empleo-informatica\`.

## Riesgos

- **85 ramas locales.** La de trabajo es `main` (`6483111`), activa en el worktree `F:\temp-opofuente\opofuente-restaurado`. No abrir ramas por tarea.
- `DEBT.md` (100 KB): leerla antes de tocar el modelo de datos.
- **No confundir fuentes**: el banco `E:\OpoFuente-datos` tiene material de otras oposiciones (celador, Guardia Civil) que **no** entra aquí.

## Puertas antes de dar una pantalla por buena

1. `python -m pytest -q` en verde.
2. `ai-design-check` o la lista de diez de las recetas.
3. Ojos frescos: subagente sin historial con este fichero y una captura.
