import { useState } from 'react';

import { Button } from '../ui/Button';
import { Card, EmptyState, StatTile } from '../ui/Card';
import { Accordion, Modal, Tabs } from '../ui/Disclosure';
import { OptionButton, type OptionState } from '../ui/OptionButton';
import { ProgressBar, QuestionGrid, type CellState } from '../ui/Progress';

/**
 * La página de los componentes (F3 del rediseño, 6 de octubre de 2026).
 *
 * Existe para **ver** cada pieza en todos sus estados antes de construir las pantallas de test con
 * ellas, que es lo que pidió Claude: se abre en `/admin/ui` y sale en `npm run screens`, así que las
 * capturas se revisan sin tocar el código.
 *
 * Los textos son de temario de TAI de verdad (control de versiones, clave primaria) a propósito: es la
 * mejor forma de ver si el panel de opciones aguanta un enunciado largo.
 */
export function AdminUiPage() {
  const [pestana, setPestana] = useState('apuntes');
  const [opcion, setOpcion] = useState('b');
  const [abierta, setAbierta] = useState(false);
  const casillas: CellState[] = [
    'answered',
    'answered',
    'doubtful',
    'blank',
    'answered',
    'blank',
    'answered',
    'answered',
    'doubtful',
    'blank',
    'answered',
    'answered',
  ];

  const estados: readonly { estado: OptionState; texto: string }[] = [
    { estado: 'idle', texto: 'Sin tocar' },
    { estado: 'chosen', texto: 'Elegida' },
    { estado: 'correct', texto: 'Correcta' },
    { estado: 'wrong', texto: 'Fallada' },
    { estado: 'disabled', texto: 'Sin poder elegir' },
  ];

  return (
    <div style={{ display: 'grid', gap: 'var(--s5)', maxWidth: 900 }}>
      <h1 style={{ fontSize: 'var(--fs-h1)', margin: 0 }}>Componentes</h1>
      <p className="hint">
        Todas las piezas de la zona del alumno, en todos sus estados. Lo que se ve aquí es lo que usan
        el temario, los tests y el progreso.
      </p>

      <Card title="Botones">
        <div style={{ display: 'flex', gap: 'var(--s3)', flexWrap: 'wrap' }}>
          <Button variant="primary">Empezar test</Button>
          <Button variant="secondary">Ver apuntes</Button>
          <Button variant="ghost">Saltar</Button>
          <Button variant="primary" disabled>
            Empezar test
          </Button>
        </div>
      </Card>

      <Card title="Cifras y progreso">
        <div style={{ display: 'flex', gap: 'var(--s7)', flexWrap: 'wrap' }}>
          <StatTile label="preguntas vistas" value="1.240" />
          <StatTile label="aciertos" value="78 %" hint="Bloque IV · Sistemas" />
          <StatTile label="fallos por repasar" value="23" />
        </div>
        <div style={{ display: 'grid', gap: 'var(--s4)', marginTop: 'var(--s5)' }}>
          <ProgressBar percent={0} label="Bloque I · Organización del Estado" />
          <ProgressBar percent={42} label="Bloque II · Tecnología básica" />
          <ProgressBar percent={78} label="Bloque III · Desarrollo de sistemas" />
          <ProgressBar percent={100} label="Bloque IV · Sistemas y comunicaciones" />
        </div>
      </Card>

      <Card title="Enunciado y opciones">
        <p className="ui-stem">
          En el control de versiones, ¿qué permite identificar de forma única cada fila de una tabla?
        </p>
        <div style={{ display: 'grid', gap: 'var(--s2)', marginTop: 'var(--s4)' }}>
          <OptionButton
            optionKey="A"
            text="La clave ajena"
            state={opcion === 'a' ? 'chosen' : 'idle'}
            onChoose={() => setOpcion('a')}
          />
          <OptionButton
            optionKey="B"
            text="La clave primaria"
            state={opcion === 'b' ? 'chosen' : 'idle'}
            onChoose={() => setOpcion('b')}
          />
          <OptionButton
            optionKey="C"
            text="El índice agrupado del fichero de datos"
            state={opcion === 'c' ? 'chosen' : 'idle'}
            onChoose={() => setOpcion('c')}
          />
          <OptionButton optionKey="D" text="El código fuente compilado" state="disabled" />
        </div>
        <div style={{ display: 'grid', gap: 'var(--s2)', marginTop: 'var(--s5)' }}>
          {estados.map((fila) => (
            <OptionButton
              key={fila.estado}
              optionKey="A"
              text={`Estado: ${fila.texto}`}
              state={fila.estado}
            />
          ))}
        </div>
      </Card>

      <Card title="Mapa de preguntas">
        <QuestionGrid cells={casillas} current={4} />
        <p className="hint" style={{ marginTop: 'var(--s3)' }}>
          Rellena: contestada · discontinua: dudosa · contorno grueso: la que toca ahora.
        </p>
      </Card>

      <Card title="Pestañas y acordeón">
        <Tabs
          tabs={[
            { id: 'apuntes', label: 'Apuntes' },
            { id: 'preguntas', label: 'Preguntas' },
            { id: 'progreso', label: 'Mi progreso' },
          ]}
          active={pestana}
          onChange={setPestana}
        >
          <p className="ui-reading" style={{ marginTop: 'var(--s4)' }}>
            Contenido de la pestaña «{pestana}». Las pestañas se cambian también con las flechas.
          </p>
        </Tabs>
        <div style={{ marginTop: 'var(--s5)' }}>
          <Accordion
            items={[
              {
                id: 'i',
                title: 'Bloque I · Organización del Estado y Administración electrónica',
                children: <p>6 temas</p>,
              },
              {
                id: 'ii',
                title: 'Bloque II · Tecnología básica',
                children: <p>7 temas</p>,
              },
              {
                id: 'iv',
                title: 'Bloque IV · Sistemas y comunicaciones',
                children: <p>10 temas</p>,
              },
            ]}
            open={['ii']}
          />
        </div>
        <div style={{ marginTop: 'var(--s5)' }}>
          <Button variant="secondary" onClick={() => setAbierta(true)}>
            Abrir una ventana
          </Button>
          <Modal open={abierta} title="¿Terminar el test?" onClose={() => setAbierta(false)}>
            <p>Te quedan 3 preguntas sin contestar.</p>
            <div style={{ display: 'flex', gap: 'var(--s3)', marginTop: 'var(--s4)' }}>
              <Button variant="primary" onClick={() => setAbierta(false)}>
                Terminar y corregir
              </Button>
              <Button variant="secondary" onClick={() => setAbierta(false)}>
                Seguir
              </Button>
            </div>
          </Modal>
        </div>
      </Card>

      <Card title="Cuando no hay nada">
        <EmptyState
          message="Aún no has hecho ningún test."
          action={
            <Button variant="primary" onClick={() => undefined}>
              Empezar test rápido
            </Button>
          }
        />
      </Card>
    </div>
  );
}
