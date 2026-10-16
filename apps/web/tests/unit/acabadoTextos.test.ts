/**
 * Los textos nuevos del acabado, pasados por el **detector de palabras prohibidas**.
 *
 * El encargo lo pide con una razón concreta: el detector vive en `tests/palabrasProhibidas.ts` y la zona
 * del alumno no puede enseñar según qué cosas. Un cambio de estilo toca textos, así que hay que pasarlos
 * por él **antes** de cerrar.
 *
 * Y se hace aquí, frase a frase, y no sobre una captura entera, porque la captura trae además la
 * interfaz de antes —en el informe de las 24 capturas de `main` salen `Celador`, `bandeja`, `revision`…
 * en Inicio— y eso no es de este cambio. Lo que se mide aquí es lo que **añade** el acabado.
 */

import { describe, expect, it } from 'vitest';

import { datosEnElTexto, lenguajeInternoEnElTexto } from '../palabrasProhibidas';

/**
 * Las frases que el acabado pone **delante del alumno**, copiadas tal cual de las pantallas.
 *
 * Si alguna cambia en la pantalla, esta lista tiene que cambiar con ella: es la única manera de que la
 * comprobación siga midiendo lo que se lee.
 */
const TEXTOS_DEL_ACABADO: readonly string[] = [
  'Puntuación directa: 12,50 sobre 50 (estimada)',
  '¿Por qué estimada?',
  'Tu hoja de respuestas',
  'Cada casilla dice lo que pasó: la verde es la que era correcta, y la que lleva el color del fallo es la que marcaste y no lo era. Pulsa un número para bajar a esa pregunta.',
  'Ver en apuntes',
  'Ir a la pregunta 12',
  'Cargando el temario…',
  'Cargando el progreso…',
  'Cargando los apuntes…',
  // Y los de la lectura por capítulos (F35, §3.1): esto es lo que se añade a la pantalla de los
  // apuntes, que es la que más texto nuevo pone delante del alumno.
  'Apartados',
  'Esto se pregunta',
  'Esto está mal',
  'Capítulos del tema',
  'Anterior: IV.7.1',
  'Siguiente: IV.7.2',
  'Tabla: Capa, Unidad',
];

describe('los textos nuevos del acabado', () => {
  it('no traen ninguna palabra prohibida de las que no se pueden ver nunca', () => {
    for (const texto of TEXTOS_DEL_ACABADO) {
      expect(datosEnElTexto(texto), `datos en «${texto}»`).toEqual([]);
    }
  });

  it('tampoco añaden jerga interna a la interfaz', () => {
    for (const texto of TEXTOS_DEL_ACABADO) {
      expect(lenguajeInternoEnElTexto(texto), `jerga en «${texto}»`).toEqual([]);
    }
  });

  it('el detector sigue leyendo «Rojo» como el banco: por eso el texto no dice ese color', () => {
    // Es la razón de que la frase de la hoja diga «el color del fallo» en vez del nombre del color: el
    // detector lee «Rojo» (el banco privado) sin distinguir mayúsculas, así que escribirlo en la
    // pantalla del alumno habría metido un aviso nuevo en el informe de capturas. Queda anotado para
    // que el propietario decida si el detector debería distinguir la mayúscula en ese caso.
    expect(datosEnElTexto('la correcta va en rojo').map((hallado) => hallado.palabra)).toEqual([
      'Rojo',
    ]);
  });
});
