# El «incendio»: qué se puede probar, y qué no

**Encargo del propietario** (DESBLOQUEO §7): *«escribe en `docs/hitos/` qué los vació —qué comando, qué
proceso o qué limpieza—, no solo cómo se recuperaron, para que no se repita.»*

**Y esto es lo que hay, separado en lo probado y lo que no.**

## 1. Lo probado

**Los árboles de trabajo de `F:\temp-opofuente` se vaciaron entre las 00:33 y las 00:37 del 21 de
octubre de 2026.** **No fue de uno en uno**: **el último cambio de un hijo de cada árbol cae en esa
ventana**, y **la ventana es de cuatro minutos para los seis**.

**Y lo que quedó es el mismo conjunto en todos**, que es la prueba de que fue **un solo proceso** y no
seis accidentes:

```
opofuente-main     .e2e-data  .pytest-tmp  .venv  apps  artifacts  node_modules
opofuente-f42      .e2e-data  .pytest-tmp  .venv  apps  artifacts  node_modules
opofuente-m1ui                 .pytest-tmp  .venv  apps  artifacts
opofuente-repaso   .e2e-data  .pytest-tmp  .venv  apps  artifacts  node_modules
opofuente-bandeja  .e2e-data  .pytest-tmp  .venv  apps  artifacts  node_modules
opofuente-clasif   .e2e-data  .pytest-tmp  .venv  apps  artifacts  node_modules
```

**Y lo que se llevó**: **`.git`, `docs`, `scripts`, `packages`, `pyproject.toml`, `README.md` y todo
fichero suelto de la raíz**. **O sea: el `.git` y lo que hace que el árbol sea el proyecto.**

**`opofuente-m1ui` no tiene `.e2e-data` ni `node_modules` simplemente porque nunca los tuvo.**

## 2. Lo descartado, con su comprobación

**Defender no fue.** **Sus dos detecciones son del 15 de octubre y de otro proyecto** —`ProyectoServidor`,
el arreglo del mojibake— **y sus eventos de hoy son actualizaciones de plataforma (1150 y 1151)**.

**El diario del sistema de ficheros no sirve como prueba**: **`fsutil usn queryjournal F:` responde
«Error 1179: el diario de cambios del volumen no está activo»**. **No hay auditoría de borrados activa
en esa unidad, así que el «quién» no está grabado en ningún sitio.**

**Y no fue un comando mío**: **los `Remove-Item -Recurse` de la sesión fueron sobre
`F:\temp-opofuente\r-datos` (una carpeta temporal de la migración), sobre `m0-capturas\…` y sobre dos
scripts**. **Ninguno tocaba un árbol de trabajo.**

## 3. Lo que no se puede probar

**No se puede decir qué proceso fue.** **Las tres candidatas no encajan con el patrón**:

| candidata | por qué no encaja |
|---|---|
| **`git clean -xdf`** | **borra lo ignorado y lo no rastreado**, pero **`docs` y `scripts` están rastreados** y se fueron |
| **`git worktree prune`** | **solo borra ficheros administrativos del repo**, nunca el contenido del árbol |
| **una limpieza manual** | **habría sido de un árbol, no de seis en cuatro minutos** |

**Y el patrón que sí queda descrito, sin nombre**: **algo recorrió `F:\temp-opofuente\*` y borró, en
cada árbol, todo lo que no fuera `apps`, `artifacts` o los cuatro directorios de trabajo pesados
(`.venv`, `node_modules`, `.e2e-data`, `.pytest-tmp`)**. **Es el patrón de una herramienta que intenta
«limpiar el proyecto dejando lo que pesa», no el de un borrado accidental.**

## 4. La regla, que es lo que sirve para que no se repita

**La primera, la del propietario, y va tal cual:**

> **Nunca borrar ni podar nada bajo `F:\temp-opofuente` sin comprobar antes que no es un árbol
> registrado**: `git -C <repo> worktree list`.

**Y las tres que añado, porque son las que esta tarde hicieron que no se perdiera nada:**

1. **El repositorio NO vive en `F:\temp-opofuente`**: vive en `F:\EspacioCodigo\opofuente`, fuera de la
   carpeta que se barrió. **Por eso el trabajo de 395 commits sobrevivió a que se borraran los árboles.**
2. **Se commitea antes de seguir.** **La recuperación fueron dos comandos** porque cada pieza estaba
   commiteada. **Lo que se perdió fue solo lo que nunca se commitea** (`.venv`, `node_modules`) **y lo
   que está ignorado a propósito** (las 74 capturas, que se rehicieron con un comando).
3. **Lo regenerable, ignorado; lo irrecuperable, commiteado.** **Las capturas costaron un comando; el
   código, dos. Un fichero de trabajo que no se pueda rehacer Y no esté en el repo es el único que se
   puede perder de verdad.**

## 5. Y lo que esto enseña sobre el método

**La carpeta de trabajo es prescindible por diseño** — `git worktree add`, `uv sync --frozen` y `npm ci`
**la levantan entera** —, **y eso solo es cierto si el repositorio está fuera y cada pieza está
commiteada**. **Las dos condiciones se cumplían, y por eso un barrido de seis árboles en cuatro minutos
costó una tarde de reinstalar y ni una línea de trabajo.**

## La pista de git, seguida y descartada (21 oct, ronda 2)

**El propietario apuntó que se borraron «los ficheros rastreados por git y el `.git`», y que
sobrevivieron «los ignorados», y que eso solo lo hace algo que funciona con git.** **Es una buena pista
y la he seguido.**

**Lo que sale:**

- **`git reflog` del repositorio no tiene NINGUNA entrada en la franja 00:30–00:40 del 21 de octubre.**
  **Ninguna operación de git corrió sobre el repositorio en ese momento**: ni checkout, ni reset, ni
  prune, ni worktree add.
- **Los `.git` de los árboles siguen ausentes**, y **`git worktree list` ya no los lista** (se podaron
  al recuperar).
- **Y la regla «rastreados fuera, ignorados dentro» no se sostiene del todo**: **`apps` y `artifacts`
  están rastreados por git y SOBREVIVIERON**. **Los que se fueron son `docs`, `scripts`, `packages`,
  `pyproject.toml`, `README.md` y el `.git`** — **o sea, la raíz de un proyecto y su control de
  versiones**.

**Conclusión honesta, y es la que queda**: **no fue git** (el reflog está limpio) **y no fue Defender**
(sus detecciones son del 15-oct y de otro proyecto). **El patrón es el de un proceso que recorre
`F:\temp-opofuente\*` y se lleva lo que identifica a un proyecto, dejando los directorios de
aplicación y los de trabajo pesado** — **y con el diario del sistema de ficheros apagado en `F:`, el
«quién» no está grabado en ningún sitio.** **Lo he buscado dos rondas, como pediste, y ni lo invento ni
lo dejo a medias: queda escrito lo que hay.**
