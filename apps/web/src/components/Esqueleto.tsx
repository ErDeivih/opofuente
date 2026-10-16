import { useEffect, useState } from 'react';

/**
 * El esqueleto de una lista que tarda (§2.5 del cierre del objetivo).
 *
 * La regla del encargo, tal cual: **esqueletos en las listas que tardan más de 300 ms** (Temario,
 * Progreso y Tema), **sin animaciones de entrada decorativas** y respetando `prefers-reduced-motion`.
 *
 * Y la mitad que se olvida: una respuesta que llega **antes** de esos 300 ms no puede hacer parpadear
 * nada. Un esqueleto que aparece y desaparece en 40 ms es peor que no ponerlo, así que el retardo es
 * parte del componente y no una decisión de cada pantalla.
 *
 * Accesibilidad: el esqueleto es `role="status"` y lleva **nombre** («Cargando el temario…»). Un
 * dibujo de barras grises no se anuncia si no dice qué está esperando, y el texto de carga de siempre
 * —que sigue existiendo los primeros 300 ms— es el que da el aviso inmediato.
 */

/** Cuánto se espera antes de enseñar el esqueleto. El número está en el encargo, no aquí. */
const RETARDO_DEL_ESQUELETO_MS = 300;

export interface EsqueletoDeListaProps {
  /** Lo que se está esperando, en palabras: `el temario`, `el progreso`, `los apuntes`. */
  nombre: string;
  /** El identificador de la prueba, para poder exigir que el esqueleto está de verdad. */
  identificador: string;
  /** Cuántas filas se dibujan. No es el número de filas que van a llegar: es una silueta. */
  filas?: number;
}

/** El texto de carga de los primeros 300 ms, compartido por las tres pantallas. */
function cargaDelEsqueleto(nombre: string): string {
  return `Cargando ${nombre}…`;
}

export function EsqueletoDeLista({ nombre, identificador, filas = 4 }: EsqueletoDeListaProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const espera = window.setTimeout(() => setVisible(true), RETARDO_DEL_ESQUELETO_MS);
    return () => {
      window.clearTimeout(espera);
    };
  }, []);

  if (!visible) {
    // Los primeros 300 ms: el estado de carga de siempre. Es el que se anuncia en cuanto se pide.
    return (
      <p className="loading" role="status">
        {cargaDelEsqueleto(nombre)}
      </p>
    );
  }

  return (
    <div className="esqueleto" role="status" aria-label={cargaDelEsqueleto(nombre)} data-testid={identificador}>
      {Array.from({ length: filas }, (_valor, indice) => (
        <div className="esqueleto__fila" key={indice}>
          <span className="esqueleto__barra esqueleto__barra--titulo" />
          <span className="esqueleto__barra esqueleto__barra--dato" />
        </div>
      ))}
    </div>
  );
}
