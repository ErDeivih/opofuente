// Carga de la demo: 50 usuarios concurrentes navegando el temario y el banco de preguntas.
//
// Objetivo: comprobar que la fachada (nginx) y la API aguantan 50 usuarios simultáneos leyendo las
// pantallas que promete la demo. No escribe nada: solo GET, así que no ensucia los datos.
//
// Uso (no hace falta instalar k6; se ejecuta con Docker):
//   docker run --rm -v "${PWD}\load:/load:ro" --add-host=host.docker.internal:host-gateway `
//     -e BASE_URL=http://host.docker.internal:8080 `
//     -e DEMO_USER=demo -e DEMO_PASSWORD=demo `
//     grafana/k6 run /load/k6-50vu.js
//
// Si la demo no tiene autenticación básica, omite DEMO_USER/DEMO_PASSWORD.

import encoding from 'k6/encoding';
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'http://127.0.0.1:8080';
const DURATION = __ENV.DURATION || '60s';
const VUS = Number(__ENV.VUS || 50);

const AUTH = __ENV.DEMO_USER
  ? `Basic ${encoding.b64encode(`${__ENV.DEMO_USER}:${__ENV.DEMO_PASSWORD || ''}`)}`
  : null;

function headers() {
  return AUTH ? { Authorization: AUTH } : {};
}

export const options = {
  scenarios: {
    cincuenta_usuarios: {
      executor: 'constant-vus',
      vus: VUS,
      duration: DURATION,
    },
  },
  thresholds: {
    // Un fallo de red o un 5xx es un fallo: la demo debe servir todas las peticiones.
    http_req_failed: ['rate<0.01'],
    // Lecturas de SQLite detrás de nginx: 1,5 s de p95 es holgado incluso en el plan Free.
    http_req_duration: ['p(95)<1500'],
  },
};

// Una vez por ejecución: descubre el conjunto de preguntas que sirve la base de demo.
export function setup() {
  const respuesta = http.get(`${BASE}/api/v1/question-sets`, { headers: headers() });
  const cuerpo = respuesta.json();
  const conjuntos = Array.isArray(cuerpo) ? cuerpo : (cuerpo.items ?? []);
  return { setId: conjuntos.length > 0 ? conjuntos[0].id : null };
}

export default function (data) {
  // Portada de la demo (estática) y las dos pantallas que pide el encargo.
  const peticiones = [
    http.get(`${BASE}/`, { headers: headers(), tags: { pantalla: 'inicio' } }),
    http.get(`${BASE}/api/v1/curricula`, { headers: headers(), tags: { pantalla: 'temario' } }),
    http.get(`${BASE}/api/v1/question-sets`, {
      headers: headers(),
      tags: { pantalla: 'preguntas' },
    }),
    http.get(`${BASE}/api/v1/health/live`, {
      headers: headers(),
      tags: { pantalla: 'salud' },
    }),
  ];

  if (data?.setId) {
    peticiones.push(
      http.get(`${BASE}/api/v1/question-sets/${data.setId}/questions`, {
        headers: headers(),
        tags: { pantalla: 'preguntas_conjunto' },
      }),
    );
  }

  for (const peticion of peticiones) {
    check(peticion, {
      'responde 200': (respuesta) => respuesta.status === 200,
    });
  }

  // Tiempo de lectura entre iteraciones: 50 usuarios, no 50 martillos.
  sleep(1);
}
