import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AcceptedClassificationPanel } from '../../src/features/review/AcceptedClassificationPanel';

/**
 * Pruebas del panel que hace **visible** la clasificación vigente de un material (corrector de S04).
 *
 * El defecto que cierran: aceptar una propuesta de tipo documental, oposición, autoridad o derechos
 * cambiaba un estado y no se veía en ninguna parte. Aquí se fija lo que el usuario tiene que poder ver:
 * los cinco ejes, la diferencia entre lo que aceptó y lo que el motor aplicó por su cuenta, y los ejes
 * que **no** constan, que se dicen en lugar de desaparecer.
 */

const RESPUESTA = {
  subject_type: 'artifact',
  subject_id: 'art-1',
  subject_label: 'mis-apuntes.txt',
  pending_review: true,
  values: [
    {
      axis: 'document_type',
      value: 'personal_notes',
      value_label: 'Apuntes personales',
      status: 'accepted',
      confidence: 0.4,
      is_critical: false,
      decided_at: '2026-09-16T10:00:00Z',
    },
    {
      axis: 'topic',
      value: 'bloque-4/tema-1',
      value_label: 'Protección de datos personales',
      status: 'auto_applied_provisional',
      confidence: 0.8,
      is_critical: false,
      decided_at: '2026-09-16T10:00:00Z',
    },
  ],
};

function renderPanel(respuesta: unknown = RESPUESTA) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve(respuesta),
      } as unknown as Response),
    ),
  );
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AcceptedClassificationPanel
        subjectType="artifact"
        subjectId="art-1"
        subjectLabel="mis-apuntes.txt"
      />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('clasificación vigente de un material', () => {
  it('lista los cinco ejes en orden y dice cuáles están sin clasificar', async () => {
    renderPanel();

    const tabla = await screen.findByRole('table', {
      name: /Lo que consta de este material/i,
    });
    const ejes = within(tabla)
      .getAllByRole('rowheader')
      .map((celda) => celda.textContent ?? '');

    expect(ejes).toEqual([
      'Tipo de documento',
      'Oposición',
      'Tema del programa',
      'Autoridad',
      'Derechos',
    ]);
    // Los tres ejes sin valor no desaparecen: se dicen.
    expect(within(tabla).getAllByText('sin clasificar')).toHaveLength(3);
    expect(within(tabla).getByText('Apuntes personales')).toBeInTheDocument();
    expect(within(tabla).getByText('Protección de datos personales')).toBeInTheDocument();
  });

  it('distingue lo que aceptó el usuario de lo que aplicó el motor por su cuenta', async () => {
    renderPanel();

    const tabla = await screen.findByRole('table', {
      name: /Lo que consta de este material/i,
    });
    const filaAceptada = within(tabla).getByRole('row', { name: /Tipo de documento/ });
    const filaProvisional = within(tabla).getByRole('row', { name: /Tema del programa/ });

    expect(within(filaAceptada).getByText(/aceptad/i)).toBeInTheDocument();
    expect(within(filaProvisional).getByText(/provisional/i)).toBeInTheDocument();
    expect(
      screen.getByText(/aplicadas provisionalmente: son revisables/i),
    ).toBeInTheDocument();
  });

  it('avisa cuando no hay nada decidido en lugar de mentir con un valor', async () => {
    renderPanel({
      subject_type: 'artifact',
      subject_id: 'art-2',
      subject_label: 'otro.txt',
      pending_review: false,
      values: [],
    });

    const tabla = await screen.findByRole('table', {
      name: /Lo que consta de este material/i,
    });
    expect(within(tabla).getAllByText('sin clasificar')).toHaveLength(5);
    expect(
      screen.queryByText(/aplicadas provisionalmente: son revisables/i),
    ).not.toBeInTheDocument();
  });
});
