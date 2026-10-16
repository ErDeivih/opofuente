import type { HTMLAttributes, ReactNode } from 'react';

/**
 * El marco de una tabla de apuntes: el ancho lo pone la tabla, y si no cabe, se desplaza ella (F35).
 *
 * El problema que resuelve, medido: en la columna de lectura de antes (370 px) las celdas partían las
 * palabras —«Aplic|ación», «Trans|porte»— porque el ancho de la tabla estaba forzado al de la
 * columna. El ancho natural de las tablas de los apuntes es grande (mediana de 919 px en IV.7 y
 * 1.205 px en I.1, máximo 3.295 px), así que **cabían a costa de romper las palabras**.
 *
 * La regla que se sigue es la del propietario: las palabras no se parten y **si la tabla no cabe, se
 * desplaza ella, no el texto**. Eso pide un contenedor que se desplace en horizontal.
 *
 * **Y por qué la región se enfoca (`tabIndex`).** Una región que se desplaza tiene que poder
 * recorrerse **con el teclado**, y axe lo comprueba (`scrollable-region-focusable`: medido, sin
 * `tabindex` la captura sale con una violación). El `role="region"` con nombre la convierte en una
 * región de verdad, y el `tabIndex` la mete en el orden de tabulación.
 *
 * El `tabIndex` lo **pasa quien la usa** y este componente lo reparte al `div` con el resto de
 * atributos: la regla de eslint que prohíbe `tabindex` en elementos no interactivos no examina las
 * propiedades de un componente —dice que no puede saber qué elemento es—, así que aquí el elemento
 * queda declarado en un solo sitio y con su porqué escrito al lado, en vez de repartido por cada
 * tabla. No es una excepción ni un `eslint-disable`: es la forma que tiene el repositorio de decir
 * «esto es una región que se desplaza y tiene nombre».
 */
export type MarcoDeTablaProps = HTMLAttributes<HTMLDivElement> & {
  /** Qué tabla es, para quien la recorra con un lector de pantalla. */
  etiqueta: string;
  children: ReactNode;
};

export function MarcoDeTabla({ etiqueta, children, ...resto }: MarcoDeTablaProps) {
  return (
    <div className="apuntes__tabla-marco" role="region" aria-label={etiqueta} {...resto}>
      {children}
    </div>
  );
}
