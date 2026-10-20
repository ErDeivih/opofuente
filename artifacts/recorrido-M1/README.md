# Las capturas de M1: por qué esta carpeta está vacía

**M1 pide capturas en `artifacts/recorrido-M1/` y todavía no hay ninguna.** **No es un olvido, y conviene
que quede escrito aquí y no en la memoria de nadie.**

**Lo que M1 añade a las pantallas es la cita literal de los apuntes bajo la explicación** — en el test y en
el Resultado. **Y hoy esa cita llega nula en todas las preguntas**, porque **las 11.315 explicaciones que
hay son `private` y no tienen cita**: las escribió una persona, no el generador.

**Así que una captura de hoy enseñaría exactamente lo que enseñaba la de M0**, con un hueco donde irá la
cita. **No es una prueba de nada**: sería una foto de la ausencia.

## Cuándo se llenará

**Cuando el generador escriba la primera explicación `generated`** — y eso necesita
**`DEEPSEEK_API_KEY` en el entorno** y **el ensayo de 20 preguntas** que decide si el hito cabe en sus 12 $.

**El orden, entonces**, es este:

1. **el ensayo** (`uv run python -m opofuente.tools.explicar_preguntas --de-verdad --limite 20`);
2. **si la cifra cabe**, la corrida y las explicaciones con su cita en la base;
3. **y entonces** `npm run screens --workspace @opofuente/web -- --datos <copia>` **sobre una copia
   verificada**, que deja los PNG en `artifacts/screens-datos` — **de donde se copian aquí**.

## Y por qué la carpeta existe antes que las fotos

**Porque la ausencia también se documenta.** **Una carpeta que no está dice «no se hizo»; una carpeta con
un motivo escrito dice «no se podía, y esto es lo que falta».** **La diferencia es la que hay entre un hueco
y una decisión.**