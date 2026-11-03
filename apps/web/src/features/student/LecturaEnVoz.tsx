import { useCallback, useEffect, useRef, useState } from 'react';

import {
  VELOCIDADES,
  hayVozEnEspanol,
  vozPreferida,
  type FragmentoEnVoz,
} from './lecturaEnVoz';

/**
 * Los controles para **oír** el capítulo que se está leyendo (O7).
 *
 * La voz la pone el aparato: `window.speechSynthesis` con las voces que el sistema tenga instaladas.
 * No hay petición al servidor, no se manda el texto a ningún servicio y no se guarda audio: el tema
 * se lee **en el propio ordenador**, que es lo que permite ofrecerlo sin depender de la red ni de un
 * tercero. Esa es también la razón de que el aviso sea explícito cuando el equipo no puede: se dice lo
 * que falta, en vez de enseñar un botón que no hace nada.
 *
 * La pantalla monta este componente con una `key` por capítulo: al cambiar de capítulo se desmonta,
 * cancela la voz y vuelve a empezar. Así no hay que reiniciar nada a mano ni quedan dos lecturas
 * sonando a la vez.
 *
 * La lógica de qué se pronuncia vive en `lecturaEnVoz.ts`; aquí solo está el reproductor.
 */

export interface LecturaEnVozProps {
  /** Los trozos ya preparados del capítulo abierto. */
  fragmentos: readonly FragmentoEnVoz[];
  /** Cuántos apartados tiene el capítulo, para decir «apartado 3 de 12». */
  totalApartados: number;
}

type EstadoDeLectura = 'parado' | 'leyendo' | 'pausado';

/** `true` si este navegador puede sintetizar voz; se comprueba una vez. */
function haySintesis(): boolean {
  return (
    typeof window !== 'undefined' &&
    'speechSynthesis' in window &&
    typeof window.SpeechSynthesisUtterance === 'function'
  );
}

/**
 * El reproductor del capítulo: escuchar, pausar, reanudar y detener, a tres velocidades.
 *
 * Para que la pausa y el «detener» sean fiables se numera cada lectura (`generacion`): al detener o al
 * cambiar de capítulo la generación sube, y los `onend` que lleguen tarde de la lectura anterior se
 * ignoran en vez de seguir hablando por su cuenta. Un `cancel()` suelto no basta: las llamadas
 * pendientes del sintetizador no se pueden desenganchar de otra manera.
 */
export function LecturaEnVoz({ fragmentos, totalApartados }: LecturaEnVozProps) {
  const [soportado] = useState(haySintesis);
  const [voces, setVoces] = useState<SpeechSynthesisVoice[]>([]);
  const [estado, setEstado] = useState<EstadoDeLectura>('parado');
  const [indice, setIndice] = useState(0);
  const [velocidad, setVelocidad] = useState(1);
  const [aviso, setAviso] = useState('');

  const generacion = useRef(0);
  const velocidadEnCurso = useRef(velocidad);
  velocidadEnCurso.current = velocidad;

  useEffect(() => {
    if (!soportado) {
      return;
    }
    const sintesis = window.speechSynthesis;
    const cargar = (): void => {
      setVoces(sintesis.getVoices());
    };
    cargar();
    sintesis.addEventListener('voiceschanged', cargar);
    return () => {
      sintesis.removeEventListener('voiceschanged', cargar);
    };
  }, [soportado]);

  useEffect(() => {
    const sintesis = soportado ? window.speechSynthesis : null;
    return () => {
      if (sintesis !== null) {
        generacion.current += 1;
        sintesis.cancel();
      }
    };
  }, [soportado]);

  const detener = useCallback(() => {
    generacion.current += 1;
    if (soportado) {
      window.speechSynthesis.cancel();
    }
    setEstado('parado');
    setIndice(0);
  }, [soportado]);

  const hablarDesde = useCallback(
    (desde: number) => {
      if (!soportado) {
        return;
      }
      const sintesis = window.speechSynthesis;
      generacion.current += 1;
      const lectura = generacion.current;
      sintesis.cancel();
      const voz = vozPreferida(voces);
      setAviso(
        voz === null || hayVozEnEspanol(voces)
          ? ''
          : 'No hay una voz en español en este equipo; se lee con la voz del sistema.',
      );
      setEstado('leyendo');

      const decir = (posicion: number): void => {
        if (generacion.current !== lectura) {
          return;
        }
        const fragmento = fragmentos[posicion];
        if (fragmento === undefined) {
          setEstado('parado');
          setIndice(0);
          return;
        }
        setIndice(posicion);
        const dicho = new SpeechSynthesisUtterance(fragmento.text);
        dicho.lang = voz?.lang ?? 'es-ES';
        if (voz !== null) {
          dicho.voice = voz;
        }
        dicho.rate = velocidadEnCurso.current;
        dicho.onend = () => {
          decir(posicion + 1);
        };
        dicho.onerror = () => {
          if (generacion.current !== lectura) {
            return;
          }
          setEstado('parado');
          setAviso('La lectura en voz alta se ha interrumpido.');
        };
        sintesis.speak(dicho);
      };

      decir(desde);
    },
    [fragmentos, soportado, voces],
  );

  const alternar = (): void => {
    if (fragmentos.length === 0) {
      return;
    }
    if (estado === 'leyendo') {
      window.speechSynthesis.pause();
      setEstado('pausado');
      return;
    }
    if (estado === 'pausado') {
      window.speechSynthesis.resume();
      setEstado('leyendo');
      return;
    }
    hablarDesde(indice);
  };

  const puedeLeer = soportado && fragmentos.length > 0 && voces.length > 0;

  const fragmento = fragmentos[indice] ?? null;
  const apartado = fragmento?.sectionNumber ?? 0;

  let mensaje: string;
  if (!soportado) {
    mensaje = 'Este navegador no puede leer en voz alta; el tema sigue disponible para leerlo en pantalla.';
  } else if (voces.length === 0) {
    mensaje = 'Este equipo no tiene ninguna voz instalada para leer en voz alta.';
  } else if (estado === 'leyendo' && fragmento !== null) {
    mensaje = `Leyendo el apartado ${String(apartado)} de ${String(totalApartados)}: ${fragmento.sectionTitle}`;
  } else if (estado === 'pausado' && fragmento !== null) {
    mensaje = `En pausa en el apartado ${String(apartado)} de ${String(totalApartados)}: ${fragmento.sectionTitle}`;
  } else if (aviso !== '') {
    mensaje = aviso;
  } else {
    mensaje = 'Se lee en este equipo, sin enviar el tema a ningún servicio.';
  }

  return (
    <div className="voz" role="group" aria-label="Lectura en voz alta del capítulo">
      <button
        type="button"
        className="button voz__boton"
        onClick={alternar}
        disabled={!puedeLeer}
        aria-pressed={estado === 'leyendo'}
      >
        {estado === 'leyendo' ? 'Pausar' : estado === 'pausado' ? 'Reanudar' : 'Escuchar'}
      </button>
      <button type="button" className="button" onClick={detener} disabled={estado === 'parado'}>
        Detener
      </button>
      <label className="voz__velocidad">
        Velocidad
        <select
          value={velocidad}
          onChange={(evento) => {
            setVelocidad(Number(evento.target.value));
          }}
          disabled={!puedeLeer}
        >
          {VELOCIDADES.map((opcion) => (
            <option key={opcion.valor} value={opcion.valor} title={opcion.descripcion}>
              {opcion.etiqueta}
            </option>
          ))}
        </select>
      </label>
      <p className="voz__estado" role="status" aria-live="polite">
        {mensaje}
      </p>
    </div>
  );
}
