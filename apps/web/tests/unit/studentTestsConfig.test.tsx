/**
 * La pantalla de Tests (F22): la que deja **elegir y empezar**.
 *
 * Lo que se comprueba, y por qué cada cosa:
 *
 * 1. **la dirección manda**: `?tema=IV.7` (el botón «Test» del Temario) y `?count=20` (el atajo «Test
 *    rápido de 20» de Inicio) llegan con la elección hecha. Un enlace que lleva a un formulario en
 *    blanco es peor que no tener el enlace;
 * 2. **no se inventa tamaños**: `?count=37` no es un tamaño ofrecido, así que se empieza por el de por
 *    defecto en lugar de montar en silencio un test de otra cosa;
 * 3. **lo que no se puede preguntar no se puede marcar**: un tema sin preguntas sale desactivado y lo
 *    dice, y el bloque que las tiene marca y desmarca los suyos;
 * 4. **el reloj se lee del plan, no se calcula aquí**: los minutos son los del servidor, y sin el
 *    reloj del test se enseña el tiempo del examen (120), que **no** es cero;
 * 5. **lo que se manda al servidor es lo que se ha elegido**, con la forma del contrato del motor;
 * 6. **la interfaz no enseña la cocina**: el texto que no es contenido no lleva vocabulario interno.
 */

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { TestsPage } from '../../src/pages/student/TestsPage';
import { lenguajeInternoEnElTexto } from '../palabrasProhibidas';
import {
  syllabusFixture,
  testPlanFixture,
  testPlanSinTiempoFixture,
} from './studentFixtures';
import { renderWithProviders, stubApi, type StubbedRoute } from './testUtils';

/** La pantalla con su plan y su temario simulados, por la dirección que se quiera. */
function montar({
  ruta = '/tests',
  plan = testPlanFixture,
  extra = {},
}: {
  ruta?: string;
  plan?: typeof testPlanFixture;
  extra?: Record<string, StubbedRoute>;
} = {}) {
  const fetchMock = stubApi({
    '/api/v1/student/tests/plan': { body: plan },
    '/api/v1/student/syllabus': { body: syllabusFixture },
    'POST /api/v1/student/tests': {
      status: 201,
      body: { ...syllabusFixture, id: 'ses-nuevo' },
    },
    ...extra,
  });
  renderWithProviders(<TestsPage />, { route: ruta });
  return fetchMock;
}

/**
 * La casilla de un tema, por su código.
 *
 * El límite de palabra no es decorativo: `IV.1` está dentro de `IV.10`, así que sin él la consulta
 * encontraría dos casillas —y la trampa es la misma que la del buscador del Temario—.
 */
function nombreDeTema(codigo: string): RegExp {
  return new RegExp(`^${codigo.replace('.', '\\.')}\\b`);
}

function casillaDeTema(codigo: string): HTMLElement {
  return screen.getByRole('checkbox', { name: nombreDeTema(codigo) });
}

/** La dirección de una llamada, con el mismo trato que le da el simulador. */
function urlDe(url: RequestInfo | URL): string {
  if (typeof url === 'string') {
    return url;
  }
  return url instanceof URL ? url.href : url.url;
}

/** El cuerpo con el que se ha pedido el test, del fetch simulado. */
function cuerpoDelTest(fetchMock: ReturnType<typeof stubApi>): Record<string, unknown> {
  const llamada = fetchMock.mock.calls.find(
    ([url, init]) =>
      urlDe(url).includes('/api/v1/student/tests') &&
      (init?.method ?? 'GET').toUpperCase() === 'POST',
  );
  const cuerpo = llamada?.[1]?.body;
  if (typeof cuerpo !== 'string') {
    throw new Error('la llamada no llevaba cuerpo de texto');
  }
  return JSON.parse(cuerpo) as Record<string, unknown>;
}

describe('la pantalla de Tests', () => {
  it('lee el tema de la dirección y lo deja marcado (el botón «Test» del Temario)', async () => {
    montar({ ruta: '/tests?tema=IV.7' });

    await screen.findByRole('heading', { level: 1, name: 'Tests' });
    await waitFor(() => {
      expect(casillaDeTema('IV.7')).toBeChecked();
    });
    expect(casillaDeTema('IV.1')).not.toBeChecked();
    // Y el resumen lo dice: un tema, y las preguntas que ese tema tiene de verdad.
    expect(screen.getByRole('status')).toHaveTextContent('Test de 25 preguntas de 1 tema');
  });

  it('lee el tamaño de la dirección (el «Test rápido de 20» de Inicio)', async () => {
    montar({ ruta: '/tests?count=20' });

    const veinte = await screen.findByRole('radio', { name: /20 preguntas/ });
    expect(veinte).toBeChecked();
    expect(screen.getByRole('radio', { name: /25 preguntas/ })).not.toBeChecked();
  });

  it('un tamaño que no se ofrece no se inventa: se empieza por el de por defecto', async () => {
    montar({ ruta: '/tests?count=37' });

    const veinticinco = await screen.findByRole('radio', { name: /25 preguntas/ });
    expect(veinticinco).toBeChecked();
    expect(screen.queryByRole('radio', { name: /37 preguntas/ })).toBeNull();
  });

  it('un tema sin preguntas sale desactivado y lo dice; el bloque marca los que sí las tienen', async () => {
    const usuario = userEvent.setup();
    montar();

    const sinPreguntas = await screen.findByRole('checkbox', { name: nombreDeTema('IV.10') });
    expect(sinPreguntas).toBeDisabled();
    expect(screen.getByText('Sin preguntas todavía')).toBeInTheDocument();

    // La casilla del bloque IV marca IV.1 y IV.7 (que tienen 30 cada uno) y deja IV.10 fuera. Se
    // busca dentro del bloque, porque los dos bloques del temario simulado tienen dos temas con
    // preguntas y la etiqueta es la misma.
    const bloque = document.querySelector('[data-bloque="IV"]');
    expect(bloque).not.toBeNull();
    await usuario.click(
      within(bloque as HTMLElement).getByRole('checkbox', { name: /Todo el bloque \(2 temas\)/ }),
    );

    expect(casillaDeTema('IV.1')).toBeChecked();
    expect(casillaDeTema('IV.7')).toBeChecked();
    expect(casillaDeTema('IV.10')).not.toBeChecked();
    expect(screen.getByRole('status')).toHaveTextContent('Test de 25 preguntas de 2 temas');
  });

  it('dice lo que dura el reloj del servidor y lo que pasa si no se pone', async () => {
    const usuario = userEvent.setup();
    montar({ ruta: '/tests?tema=IV.1' });

    // Sin el reloj del test, el tiempo no es cero: es el del examen, y se dice.
    expect(await screen.findByText(/Sin el reloj del test manda el tiempo del examen: 120 minutos/)).toBeInTheDocument();
    // La regla del reloj la escribe el servidor y la pantalla la pinta tal cual.
    expect(screen.getByText(testPlanFixture.timed_note)).toBeInTheDocument();

    await usuario.click(screen.getByRole('checkbox', { name: /Poner el reloj del test/ }));

    // Con el reloj puesto se enseña lo que duraría el tamaño elegido, y ya no el tiempo del examen.
    expect(screen.getByText('50 minutos para 25 preguntas.')).toBeInTheDocument();
    expect(screen.queryByText(/manda el tiempo del examen/)).toBeNull();
  });

  it('si la convocatoria no publica tiempo, lo dice en vez de suponer que no hay', async () => {
    montar({ plan: testPlanSinTiempoFixture, ruta: '/tests?tema=IV.1' });

    expect(
      await screen.findByText(
        'Sin el reloj del test, el examen tampoco publica un tiempo para este material.',
      ),
    ).toBeInTheDocument();
  });

  it('avisa antes de empezar si hay menos preguntas que las pedidas', async () => {
    montar({ ruta: '/tests?tema=I.6&count=100' });

    // I.6 tiene 12 preguntas en el temario simulado: el motor montaría un test de 12, y se dice
    // **antes** de pulsar, no al ver un test más corto de lo pedido. Se busca el texto y no el
    // `role="status"`, que también lo lleva el aviso de «cargando».
    expect(
      await screen.findByText(/solo hay 12 disponibles, así que tendrá 12/),
    ).toBeInTheDocument();
  });

  it('pide el test con lo que se ha elegido y entra a hacerlo', async () => {
    const usuario = userEvent.setup();
    const fetchMock = montar({ ruta: '/tests?tema=IV.1&count=20' });

    // El botón solo existe cuando el plan y el temario han llegado: esperar por él es esperar a que
    // la pantalla esté cargada de verdad.
    await screen.findByRole('button', { name: 'Empezar el test' });
    await usuario.click(screen.getByRole('radio', { name: /Las que he fallado/ }));
    await usuario.click(screen.getByRole('radio', { name: /Al terminar/ }));
    await usuario.click(screen.getByRole('checkbox', { name: /Poner el reloj del test/ }));
    await usuario.click(screen.getByRole('button', { name: 'Empezar el test' }));

    await waitFor(() => {
      expect(cuerpoDelTest(fetchMock)).toEqual({
        nodes: ['IV.1'],
        count: 20,
        filter: 'failed',
        feedback: 'at_end',
        timed: true,
      });
    });
  });

  it('no deja empezar sin temas: lo dice en el resumen y el botón está apagado', async () => {
    montar();

    const boton = await screen.findByRole('button', { name: 'Empezar el test' });
    expect(boton).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent(
      'Elige al menos un tema para poder empezar.',
    );
  });

  it('la interfaz no enseña la cocina: ni un término de dentro', async () => {
    montar({ ruta: '/tests?tema=IV.1' });

    await screen.findByRole('heading', { level: 1, name: 'Tests' });

    // El mismo criterio que la puerta de capturas: el texto de la **interfaz** es el del documento
    // menos lo que va dentro de un contenedor `data-contenido` (títulos de tema, enunciados).
    const copia = document.body.cloneNode(true) as HTMLElement;
    for (const nodo of Array.from(copia.querySelectorAll('[data-contenido]'))) {
      nodo.remove();
    }
    const interfaz = copia.textContent ?? '';

    expect(lenguajeInternoEnElTexto(interfaz)).toEqual([]);
  });

  it('cada tema dice lo que ya se ha contestado en él', async () => {
    montar();

    const fila = await screen.findByRole('checkbox', { name: nombreDeTema('IV.1') });
    const caja = fila.closest('li');
    expect(caja).not.toBeNull();
    expect(within(caja as HTMLElement).getByText('12 contestadas · 75 % de acierto')).toBeInTheDocument();

    const sinEmpezar = screen.getByRole('checkbox', { name: nombreDeTema('IV.7') }).closest('li');
    expect(within(sinEmpezar as HTMLElement).getByText('Sin contestar todavía')).toBeInTheDocument();
  });
});
