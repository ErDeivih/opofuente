import { useEffect, useMemo, useState } from 'react';

import { relojDeSesion, tiempoEnPalabras } from './sessionClock';

/**
 * El reloj visible de un test con tiempo (§3.4).
 *
 * Enseña **lo que queda** y, al lado, **lo que llevas**: en un simulacro de 120 minutos la cifra que
 * decide es la primera, y la segunda es la que dice si vas a poder repasar. En un test sin reloj no
 * pinta nada, porque no hay nada que contar.
 *
 * Lo que **no** hace: no termina el test cuando llega a cero. El reloj informa; quien decide qué pasa
 * al agotarse el tiempo es el servidor, y aquí no se inventa esa regla. Por eso el estado «vencido»
 * se pinta como aviso y no bloquea la pantalla: dejar al alumno sin poder contestar desde el navegador
 * sería una regla de corrección escrita en la pantalla.
 *
 * Va con `aria-live="off"` a propósito: un lector de pantalla que anuncie cada segundo es inservible.
 * La cifra se puede leer cuando se quiera, y el aviso de «queda poco» se dice una vez con su texto.
 *
 * El fichero se llama `TestClock.tsx` —y no `SessionClock.tsx`— porque el módulo de la cuenta se llama
 * `sessionClock.ts`: dos ficheros que solo difieren en la mayúscula son **el mismo fichero en
 * Windows**, y `tsc` lo rechaza. El nombre del componente no cambia.
 */
export function SessionClock({
  startedAt,
  timeLimitMinutes,
  serverNow,
  leidoEnMs,
  detenido = false,
}: {
  readonly startedAt: string | null;
  readonly timeLimitMinutes: number | null;
  readonly serverNow: string | null;
  /** El instante local en el que llegó esta lectura del servidor (el `dataUpdatedAt` de la consulta). */
  readonly leidoEnMs: number;
  readonly detenido?: boolean;
}) {
  // El reloj arranca en el instante en el que se recibió **esta** lectura y solo avanza lo de después:
  // la hora del servidor no se toca, así que un equipo con la hora mal puesta cuenta lo mismo que uno
  // en hora. La pantalla le da una `key` distinta a cada lectura, así que el componente se vuelve a
  // montar cuando llega otra y el arranque no puede quedarse viejo.
  const [ahoraMs, setAhoraMs] = useState(leidoEnMs);

  useEffect(() => {
    if (detenido || startedAt === null || timeLimitMinutes === null) {
      return;
    }
    const temporizador = window.setInterval(() => {
      setAhoraMs(Date.now());
    }, 1000);
    return () => {
      window.clearInterval(temporizador);
    };
  }, [detenido, startedAt, timeLimitMinutes]);

  const reloj = useMemo(
    () =>
      relojDeSesion({
        startedAt,
        timeLimitMinutes,
        serverNow,
        // Lo que ha pasado **desde** la lectura, con el reloj del navegador: es un trozo de tiempo, no
        // una hora, así que no depende de que el equipo esté en hora.
        desdeLaLecturaMs: Math.max(0, ahoraMs - leidoEnMs),
      }),
    [startedAt, timeLimitMinutes, serverNow, leidoEnMs, ahoraMs],
  );

  if (reloj.restanteMs === null || reloj.transcurridoMs === null) {
    return null;
  }

  return (
    <p
      className={`test-reloj${reloj.apurado ? ' test-reloj--apurado' : ''}${
        reloj.vencido ? ' test-reloj--vencido' : ''
      }`}
      aria-live="off"
    >
      <span className="test-reloj__restante">
        Quedan <strong>{tiempoEnPalabras(reloj.restanteMs)}</strong>
      </span>
      <span className="test-reloj__transcurrido">
        Llevas {tiempoEnPalabras(reloj.transcurridoMs)}
      </span>
      {reloj.vencido ? (
        <span className="test-reloj__aviso" role="status">
          Se ha agotado el tiempo: termina el test para ver el resultado.
        </span>
      ) : reloj.apurado ? (
        <span className="test-reloj__aviso" role="status">
          Queda poco tiempo.
        </span>
      ) : null}
    </p>
  );
}
