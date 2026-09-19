import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { AppShell } from '../../src/app/AppShell';
import { SettingsPage } from '../../src/pages/SettingsPage';
import {
  capabilitiesFixture,
  readinessReady,
  renderWithProviders,
  settingsFixture,
  stubApi,
  type StubbedRoute,
} from './testUtils';

/**
 * Ajustes (07_UI-UX §11) desde el comportamiento real: qué se ve y qué se pide.
 *
 * Lo que se comprueba, y por qué:
 *
 * 1. **el destino de cada proveedor se dice con palabras que no se confunden**: `unknown` nunca se
 *    presenta como «no sale de tu equipo»;
 * 2. **la configuración se lee, no se escribe**: la pantalla lo dice en lugar de ofrecer campos que no
 *    guardarían nada;
 * 3. **retirar material exige confirmación**: el primer clic enseña lo que se va a retirar y cuánto
 *    ocupa; solo el segundo llama al servidor;
 * 4. **la restauración se previsualiza antes**: no se puede restaurar sin ver qué se sustituye, y el
 *    aviso de la copia previa automática está a la vista.
 */

const HIGIENE = {
  usage: [
    {
      area: 'artifacts',
      path_display: 'artifacts',
      size_bytes: 2048,
      file_count: 3,
      readable: true,
      note: 'Material copiado (por contenido)',
    },
    {
      area: 'backups',
      path_display: 'backups',
      size_bytes: 0,
      file_count: 0,
      readable: false,
      note: 'no se ha podido medir (PermissionError)',
    },
  ],
  candidates: [
    {
      action: 'stale_temp',
      reference: 'descarga.part',
      detail: 'fichero temporal de una copia interrumpida: 4.0 KiB',
      size_bytes: 4096,
      display: 'tmp/descarga.part',
    },
    {
      action: 'orphan_artifact',
      reference: 'art-huerfano',
      detail: 'artefacto sin origen ni documento que lo use (sha256/ff/ff/x)',
      size_bytes: 1024,
      display: 'sha256/ff/ff/x',
    },
  ],
  retention_days: 30,
  total_bytes: 2048,
  reclaimable_bytes: 5120,
};

const COPIA = {
  id: '20260919-120000-abc123',
  created_at: '2026-09-19T12:00:00+00:00',
  app_version: '0.0.0-test',
  schema_revision: '0020_changes_and_derivatives',
  scope: ['database', 'artifacts', 'extracted', 'fixtures'],
  size_bytes: 1_048_576,
  file_count: 12,
  note: 'antes de tocar nada',
  restorable: true,
  restorable_reason: 'la copia está en la revisión de esquema actual',
};

const INDICE = { healthy: true, detail: 'el índice está completo (12 fragmentos)', missing_entries: 0 };

function stubAjustes(overrides: Record<string, StubbedRoute> = {}) {
  return stubApi({
    '/api/v1/health/ready': { body: readinessReady },
    '/api/v1/capabilities': { body: capabilitiesFixture },
    '/api/v1/settings': { body: settingsFixture },
    '/api/v1/backups': { body: { backups: [COPIA] } },
    '/api/v1/housekeeping': { body: HIGIENE },
    '/api/v1/search/index': { body: INDICE },
    '/api/v1/diagnostics': {
      body: {
        generated_at: '2026-09-19T12:00:00+00:00',
        version: '0.0.0-test',
        schema_revision: '0020_changes_and_derivatives',
        python_version: '3.12.0',
        platform: 'Windows 11 (python 64 bits)',
        host: '127.0.0.1',
        port: 8765,
        log_level: 'INFO',
        data_dir_display: '…/datos',
        database_file_display: '…/datos/opofuente.sqlite3',
        disk_total_bytes: 500_000_000_000,
        disk_free_bytes: 123_456_789_012,
        counts: { artifacts: 3, jobs: 5, evidence_spans: 12 },
        capabilities: capabilitiesFixture.capabilities,
        degradations: [],
        checks: readinessReady.checks,
        limits: settingsFixture.limits,
        log_tail: ['{"message": "arranque correcto"}'],
        note: 'Diagnóstico sanitizado: no incluye contenido, claves ni rutas completas.',
      },
    },
    '/api/v1/housekeeping/temps': {
      body: {
        action: 'stale_temp',
        removed: 1,
        freed_bytes: 4096,
        skipped: [],
        detail: '1 temporal(es) retirados y 4.0 KiB liberados',
      },
    },
    '/api/v1/search/reindex': {
      body: {
        indexed: 12,
        before: 12,
        after: 12,
        took_seconds: 0.01,
        detail: 'índice rehecho: 12 fragmentos indexados desde el texto de las evidencias',
      },
    },
    ...overrides,
  });
}

function renderAjustes() {
  return renderWithProviders(
    <AppShell>
      <SettingsPage />
    </AppShell>,
    { route: '/ajustes' },
  );
}

describe('ajustes: lo que se ve', () => {
  it('enseña la ruta de datos, el disco y que la configuración se lee, no se escribe', async () => {
    stubAjustes();
    renderAjustes();

    expect(await screen.findByRole('heading', { name: 'Ajustes' })).toBeInTheDocument();
    expect(screen.getByText(settingsFixture.data_dir)).toBeInTheDocument();
    expect(screen.getByText(/no.*escribe configuración, la lee/s)).toBeInTheDocument();
    // El disco sale en una línea con dos cifras. El formato es decimal (KB/MB/GB), así que las cifras
    // son las de la API divididas por 1024: 123 456 789 012 B ≈ 115.0 GB.
    const disco = screen.getByText('Disco');
    expect(disco.nextElementSibling).toHaveTextContent('115.0 GB libres de 465.7 GB');
  });

  it('dice a dónde sale el contenido de cada proveedor, sin confundir «no se sabe» con «no sale»', async () => {
    stubAjustes({
      '/api/v1/settings': {
        body: {
          ...settingsFixture,
          llm: {
            ...settingsFixture.llm,
            provider: 'ollama',
            destination: 'remote',
            destination_reason: 'el endpoint apunta a un servidor fuera de este equipo',
          },
          embeddings: {
            ...settingsFixture.embeddings,
            provider: 'openai_compatible',
            destination: 'unknown',
            destination_reason: 'está configurado pero no declara endpoint: no se sabe el destino',
          },
        },
      },
    });
    renderAjustes();

    expect(await screen.findByText('sale a un tercero')).toBeInTheDocument();
    expect(screen.getByText('no se puede determinar')).toBeInTheDocument();
    expect(screen.queryByText('no sale de tu equipo')).not.toBeInTheDocument();
  });

  it('mide el almacén y declara lo que no ha podido medir', async () => {
    stubAjustes();
    renderAjustes();

    const tabla = await screen.findByRole('table', { name: /Total 2.0 KB/ });
    expect(within(tabla).getByText('Material copiado (por contenido)')).toBeInTheDocument();
    expect(within(tabla).getByText('no se ha podido medir')).toBeInTheDocument();
    expect(screen.getByRole('table', { name: /Total 2.0 KB.*recuperable 5.0 KB/ })).toBeInTheDocument();
  });

  it('retirar exige dos clics: primero enseña lo que se va a retirar', async () => {
    const fetchMock = stubAjustes();
    renderAjustes();

    await screen.findByRole('heading', { name: 'Ajustes' });
     
    console.log('H=' + JSON.stringify(screen.getAllByRole('heading').map((h) => h.textContent)));
     
    console.log('HTML=' + (document.querySelector('[aria-labelledby="ajustes-limpieza"]')?.outerHTML.slice(0, 900) ?? 'NO-SECTION'));
    const retirar = await screen.findByRole('button', {
      name: 'Retirar: Temporales de operaciones interrumpidas',
    }, { timeout: 15_000 });
    await userEvent.click(retirar);

    // El primer clic no llama al servidor: enseña la consecuencia.
    expect(await screen.findByText(/Se van a retirar 1 elemento/)).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some((call) =>
        typeof call[0] === 'string' && call[0].includes('/housekeeping/temps'),
      ),
    ).toBe(false);

    await userEvent.click(screen.getByRole('button', { name: 'Sí, retirar' }));

    await waitFor(() => {
      expect(screen.getByText(/1 temporal\(es\) retirados/)).toBeInTheDocument();
    });
  });

  it('restaurar pide previsualización y avisa de la copia previa automática', async () => {
    const fetchMock = stubAjustes({
      '/api/v1/restore/validate': {
        body: {
          backup: COPIA,
          can_restore: true,
          blockers: [],
          missing_scope: [],
          free_bytes: 500_000_000_000,
          needed_bytes: 2_097_152,
          targets: ['opofuente.sqlite3', 'artifacts', 'extracted'],
          previous_backup_note: 'Antes de restaurar se hará una copia automática de lo que hay ahora.',
        },
      },
    });
    renderAjustes();

    const tabla = await screen.findByRole('table', { name: 'Copias de seguridad' });
    expect(within(tabla).getByText('20260919-120000-abc123')).toBeInTheDocument();
    expect(within(tabla).getByText('antes de tocar nada')).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole('button', { name: 'Previsualizar restauración' }),
    );

    expect(await screen.findByRole('heading', { name: /Restaurar/ })).toBeInTheDocument();
    expect(screen.getByText(/copia automática de lo que hay ahora/)).toBeInTheDocument();
    expect(screen.getByText(/opofuente.sqlite3, artifacts, extracted/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Restaurar esta copia' })).toBeInTheDocument();

    const restaurado = fetchMock.mock.calls.some((call) =>
      typeof call[0] === 'string' ? call[0].includes('/restore/execute') : false,
    );
    expect(restaurado).toBe(false);
  });

  it('el índice se puede rehacer y la pantalla dice qué ha hecho', async () => {
    stubAjustes();
    renderAjustes();

    expect(await screen.findByText(/el índice está completo \(12 fragmentos\)/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Rehacer el índice' }));

    await waitFor(() => {
      expect(screen.getByText(/12 fragmentos indexados desde el texto/)).toBeInTheDocument();
    });
  });

  it('el diagnóstico se puede leer en texto y dice que está saneado', async () => {
    stubAjustes({
      '/api/v1/diagnostics/text': {
        body: 'OpoFuente — diagnóstico sanitizado\nversión: 0.0.0-test\n',
        contentType: 'text/plain',
      },
    });
    renderAjustes();

    await userEvent.click(
      await screen.findByRole('button', { name: 'Preparar el diagnóstico en texto' }),
    );

    const area = await screen.findByLabelText('Diagnóstico sanitizado');
    // Se busca el contenido, no la igualdad exacta: el `Response` de la simulación no conserva el
    // salto final, y lo que importa es que el texto del servidor llegue tal cual.
    const contenido = (area as HTMLTextAreaElement).value;
    expect(contenido).toContain('OpoFuente — diagnóstico sanitizado');
    expect(contenido).toContain('versión: 0.0.0-test');
    expect(screen.getByText(/no lleva contenido, ni claves, ni rutas completas/)).toBeInTheDocument();
  });
});
