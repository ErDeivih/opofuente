// Comprueba que las 12 convocatorias de la demo abren de verdad (HTTP 2xx/3xx).
//
// Uso:
//   node docs/interfaz/verificar-convocatorias.mjs http://localhost:8098
//   BASE_URL=https://<usuario>.github.io/opofuente-demo/ node docs/interfaz/verificar-convocatorias.mjs

const BASE = (process.env.BASE_URL ?? process.argv[2] ?? '').replace(/\/+$/, '');
if (BASE === '') {
  console.error('Falta BASE_URL o el primer argumento.');
  process.exit(2);
}

const data = await (await fetch(`${BASE}/data.json`)).json();
let fallos = 0;
for (const item of data.convocatorias.items) {
  let estado = 'sin URL';
  if (item.url !== '') {
    try {
      const respuesta = await fetch(item.url, {
        redirect: 'follow',
        signal: AbortSignal.timeout(20_000),
        headers: { 'user-agent': 'Mozilla/5.0 (compatible; OpoFuente-demo-check)' },
      });
      estado = String(respuesta.status);
      if (!respuesta.ok) {
        fallos += 1;
      }
    } catch (error) {
      estado = `ERROR ${String(error)}`;
      fallos += 1;
    }
  } else {
    fallos += 1;
  }
  console.log(`${estado}\t${item.title}`);
}

console.log(`\n${data.convocatorias.items.length - fallos}/${data.convocatorias.items.length} enlaces abren`);
process.exit(fallos === 0 ? 0 : 1);
