import { useState } from 'react';

import { downloadStudentTopicPdf } from '../../api/studentStudy';
import { describeError } from '../system/labels';

/**
 * «Descargar en PDF» del tema abierto (O7).
 *
 * El PDF lo compone el servidor: es el mismo documento —capítulos, índice y, si el tema está en
 * borrador, su marca— que se lee en pantalla, con la cabecera de la instalación y el pie con la
 * versión y la fecha de generación. Aquí no se maqueta nada: se pide, se entrega al navegador con su
 * nombre y se dice qué ha pasado.
 *
 * Por qué un botón y no un enlace directo a la URL del PDF: la dirección de la API puede necesitar la
 * cookie de sesión (`credentials`), y un `<a href>` no la lleva. Pidiéndolo por el cliente pasa por
 * las mismas reglas que el resto de llamadas —incluido distinguir «la API no está» de «el servidor
 * dijo que no»—.
 *
 * Se descarga **el tema entero**, no el capítulo abierto: es lo que sirve el endpoint, y el aviso lo
 * dice con esas palabras para no prometer otra cosa.
 */
export function DescargarPdf({ codigo }: { codigo: string }) {
  const [estado, setEstado] = useState<'quieto' | 'preparando' | 'hecho' | 'fallo'>('quieto');
  const [aviso, setAviso] = useState('');

  async function descargar(): Promise<void> {
    setEstado('preparando');
    setAviso('');
    try {
      const { blob, filename } = await downloadStudentTopicPdf(codigo);
      const nombre = filename ?? `apuntes-${codigo}.pdf`;
      const url = URL.createObjectURL(blob);
      const enlace = document.createElement('a');
      enlace.href = url;
      enlace.download = nombre;
      document.body.append(enlace);
      enlace.click();
      enlace.remove();
      // La URL se libera en el turno siguiente: si desaparece antes de que el navegador la abra, la
      // descarga se cancela sin decir nada.
      window.setTimeout(() => {
        URL.revokeObjectURL(url);
      }, 0);
      setEstado('hecho');
      setAviso(`Descargando «${nombre}».`);
    } catch (error) {
      setEstado('fallo');
      setAviso(describeError(error));
    }
  }

  return (
    <p className="acciones">
      <button
        className="button"
        type="button"
        disabled={estado === 'preparando'}
        onClick={() => {
          void descargar();
        }}
      >
        {estado === 'preparando' ? 'Preparando el PDF…' : 'Descargar el tema en PDF'}
      </button>{' '}
      <span role="status">
        {aviso === '' ? 'El tema completo, para leerlo sin conexión.' : aviso}
      </span>
    </p>
  );
}
