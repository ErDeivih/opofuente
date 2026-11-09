# Prueba de carga de la demo (50 usuarios concurrentes)

**Fecha:** 9 de noviembre de 2026 · **Objetivo:** comprobar que la demo aguanta 50 usuarios
simultáneos navegando el temario y el banco de preguntas, sin errores y con latencia razonable.

## El script

[`load/k6-50vu.js`](../load/k6-50vu.js), para **k6** (gratuito y open source). No hace falta
instalarlo: se ejecuta con Docker. Cada usuario virtual (VU) hace en bucle, con 1 s de pausa:

1. `GET /` — portada (estática, servida por nginx).
2. `GET /api/v1/curricula` — el temario.
3. `GET /api/v1/question-sets` — el banco.
4. `GET /api/v1/question-sets/{id}/questions` — las preguntas del conjunto (el id se descubre en `setup`).
5. `GET /api/v1/health/live` — salud.

Solo lecturas: la prueba no ensucia datos. Umbrales: **p95 < 1500 ms** y **< 1 % de peticiones
fallidas**; si no se cumplen, k6 termina con error.

## Cómo se ejecuta

Contra el contenedor local (o contra la URL de Render, cambiando `BASE_URL`):

```powershell
docker run --rm -v "${PWD}\load:/load:ro" --add-host=host.docker.internal:host-gateway `
  -e BASE_URL=http://host.docker.internal:8099 `
  -e DEMO_USER=demo -e DEMO_PASSWORD=demo `
  grafana/k6 run /load/k6-50vu.js
```

Sin autenticación básica, omite `DEMO_USER`/`DEMO_PASSWORD`. Para una pasada más corta,
`-e DURATION=30s`; para más usuarios, `-e VUS=100`.

## Resultado medido (contenedor local, 9/11/2026)

| Métrica | Valor |
|---|---|
| Escenario | 50 VUs constantes, 60 s |
| Peticiones HTTP | **7 565** (123,6 req/s) |
| Checks correctos | **7 564 / 7 564 (100 %)** |
| Peticiones fallidas | **0 (0,00 %)** |
| Latencia media | 149 ms |
| p90 / p95 | 383 ms / **453 ms** |
| Máxima | 830 ms |
| Umbrales | ✅ p95 < 1500 ms · ✅ fallos < 1 % |

Con el contenedor recién arrancado hubo una pasada previa con 3 fallos de 6 469 peticiones
(0,04 %) y un máximo de 30 s: era el **arranque en frío** de la API (importación de dependencias y
migración). Con el servicio ya caliente, la segunda pasada salió limpia.

## Lectura honesta

- Los números son de **este equipo**, con el contenedor en Docker Desktop y sin límite de CPU. El
  plan Free de Render da 0,1 CPU y 512 MB: **será más lento**, sobre todo en frío. Los umbrales del
  script están pensados para que un fallo real se note, no para maquillar el plan gratuito.
- La demo sirve SQLite en modo lectura; no se ha probado carga de escritura (crear sesiones,
  importar material) porque no es el caso de uso de la URL pública.
- Las pantallas pesadas (Revisión, Programa) no entran en la prueba: son árboles grandes que en el
  corpus sintético no representan el uso normal de una demo.

## Reproducir el registro

El resumen de k6 se pega tal cual (el script imprime umbrales y totales). Salida de la pasada buena:
`✓ 'p(95)<1500' p(95)=452.68ms`, `✓ 'rate<0.01' rate=0.00%`, `cincuenta_usuarios ✓ [100 %] 50 VUs`.
