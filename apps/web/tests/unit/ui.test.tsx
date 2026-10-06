import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Button } from '../../src/ui/Button';
import { EmptyState } from '../../src/ui/Card';
import { Accordion } from '../../src/ui/Disclosure';
import { OptionButton } from '../../src/ui/OptionButton';
import { ProgressBar, QuestionGrid } from '../../src/ui/Progress';

/**
 * Los componentes base de la zona del alumno (F3 del rediseño).
 *
 * Se comprueba lo que no se ve en una captura: que el color no sea la única señal, que el progreso se
 * anuncie como tal y que el mapa y el acordeón digan en voz alta qué pasa. Es lo que hace que la
 * pantalla sirva también con lector de pantalla o sin distinguir el verde del rojo.
 */
describe('los componentes base', () => {
  it('una opción corregida se lee, no solo se colorea', () => {
    render(<OptionButton optionKey="B" text="La clave primaria" state="correct" />);
    expect(screen.getByText(/Correcta/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /La clave primaria/ })).toBeDisabled();
  });

  it('la opción fallada dice que es la tuya y no se puede volver a pulsar', () => {
    const alElegir = vi.fn();
    render(
      <OptionButton optionKey="C" text="El índice agrupado" state="wrong" onChoose={alElegir} />,
    );
    expect(screen.getByText(/Tu respuesta/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /El índice agrupado/ })).toBeDisabled();
    expect(alElegir).not.toHaveBeenCalled();
  });

  it('una opción sin corregir se puede elegir', async () => {
    const alElegir = vi.fn();
    render(<OptionButton optionKey="A" text="La clave ajena" state="idle" onChoose={alElegir} />);
    await userEvent.click(screen.getByRole('button', { name: /La clave ajena/ }));
    expect(alElegir).toHaveBeenCalledOnce();
  });

  it('el progreso se anuncia como barra con su valor', () => {
    render(<ProgressBar percent={42} label="Bloque II · Tecnología básica" />);
    const barra = screen.getByRole('progressbar', { name: 'Bloque II · Tecnología básica' });
    expect(barra).toHaveAttribute('aria-valuenow', '42');
  });

  it('el mapa de preguntas dice el estado de cada casilla y avisa de la que toca', async () => {
    const alIr = vi.fn();
    render(
      <QuestionGrid
        cells={['answered', 'doubtful', 'blank', 'answered']}
        current={3}
        onGo={alIr}
      />,
    );
    expect(screen.getByRole('button', { name: 'Pregunta 2: dudosa' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pregunta 3: en blanco' })).toHaveAttribute(
      'aria-current',
      'true',
    );
    await userEvent.click(screen.getByRole('button', { name: 'Pregunta 4: respondida' }));
    expect(alIr).toHaveBeenCalledWith(4);
  });

  it('el acordeón dice si está abierto o cerrado', async () => {
    render(
      <Accordion
        items={[{ id: 'iv', title: 'Bloque IV · Sistemas y comunicaciones', children: <p>10 temas</p> }]}
      />,
    );
    const boton = screen.getByRole('button', { name: /Bloque IV/ });
    expect(boton).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(boton);
    expect(boton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('10 temas')).toBeVisible();
  });

  it('el estado vacío siempre trae su salida', () => {
    render(
      <EmptyState
        message="Aún no has hecho ningún test."
        action={<Button variant="primary">Empezar test rápido</Button>}
      />,
    );
    expect(screen.getByText('Aún no has hecho ningún test.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Empezar test rápido' })).toBeInTheDocument();
  });
});
