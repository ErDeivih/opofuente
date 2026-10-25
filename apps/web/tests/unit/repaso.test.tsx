import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { RepasoPage } from '../../src/pages/RepasoPage';
import { renderWithProviders, stubApi } from './testUtils';

/**
 * La pantalla de repaso, con lo que el documento exige (fase «lo que ve el alumno», punto 2).
 *
 * **Lo que se comprueba aquí es de comportamiento, no de aspecto**: que la respuesta **no esté** hasta
 * dar la vuelta, que se pueda dar con el botón —no solo con el espacio, que en el móvil no existe— y
 * que las notas estén deshabilitadas hasta entonces. **Lo que no se puede comprobar aquí es que la
 * pista salga en dos líneas**: eso es una regla de estilo, y se ve en la captura del recorrido.
 */

const TARJETA = {
  id: 'c1',
  front: '¿Qué puerto utiliza HTTPS?',
  // **Un reverso que no aparece en ningún otro sitio de la pantalla**: si fuera «443» lo encontraría
  // también la cita y la prueba pasaría por el motivo equivocado.
  back: 'el puerto seguro',
  citation: null,
  due_at: '2026-10-25T00:00:00',
  interval_days: 1,
  repetitions: 1,
};

describe('la pantalla de repaso', () => {
  it('no enseña la respuesta hasta dar la vuelta, y la da el botón', async () => {
    stubApi({ '/cards/queue': { body: { tarjetas: [TARJETA], total: 1 } } });
    renderWithProviders(<RepasoPage />, { route: '/repaso' });

    expect(await screen.findByText('¿Qué puerto utiliza HTTPS?')).toBeInTheDocument();
    expect(screen.queryByText('el puerto seguro')).not.toBeInTheDocument();

    // Las cuatro notas, deshabilitadas mientras no se ha dado la vuelta.
    for (const etiqueta of [/Otra vez/, /Difícil/, /Bien/, /Fácil/]) {
      expect(screen.getByRole('button', { name: etiqueta })).toBeDisabled();
    }

    await userEvent.click(screen.getByRole('button', { name: 'Ver la respuesta' }));

    await waitFor(() => {
      expect(screen.getByText('el puerto seguro')).toBeInTheDocument();
    });
    for (const etiqueta of [/Otra vez/, /Difícil/, /Bien/, /Fácil/]) {
      expect(screen.getByRole('button', { name: etiqueta })).toBeEnabled();
    }
  });
});
