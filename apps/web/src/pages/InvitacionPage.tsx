/**
 * La pantalla de canje de una invitación (M8).
 *
 * **Tres campos y un botón**, que es todo lo que hace falta: **el token viene en la dirección**, y el correo y
 * la contraseña los pone la persona invitada.
 *
 * **Y dos decisiones que se ven en el código:**
 *
 * 1. **el token se lee de la dirección y no se puede editar**: si la persona lo cambia, deja de ser el enlace
 *    que le mandaron, y un campo editable solo sirve para pegar mal;
 * 2. **el motivo de un fallo se enseña tal cual viene del servidor**, sin adornarlo: **el servidor no distingue
 *    «no existe» de «estaba mal» a propósito**, y la pantalla no puede ser más lista que él sin estropearlo.
 */
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { canjearInvitacion } from '../api/invitations';
import { describeError } from '../features/system/labels';

export function InvitacionPage() {
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const [correo, setCorreo] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [estado, setEstado] = useState<'listo' | 'enviando' | 'hecho'>('listo');
  const [error, setError] = useState<string | null>(null);

  if (token === '') {
    return (
      <main className="pagina">
        <h1 className="pagina__titulo">Invitación</h1>
        <p className="bloque__texto">
          Este enlace no trae invitación. Pide uno nuevo a quien te invitó.
        </p>
      </main>
    );
  }

  async function enviar(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setEstado('enviando');
    setError(null);
    try {
      await canjearInvitacion({ token, correo, contrasena });
      setEstado('hecho');
    } catch (fallo) {
      setEstado('listo');
      setError(describeError(fallo));
    }
  }

  if (estado === 'hecho') {
    return (
      <main className="pagina">
        <h1 className="pagina__titulo">Cuenta creada</h1>
        <p className="bloque__texto">Ya puedes entrar con tu correo y tu contraseña.</p>
      </main>
    );
  }

  return (
    <main className="pagina">
      <h1 className="pagina__titulo">Canjea tu invitación</h1>
      <form className="formulario" onSubmit={(evento) => void enviar(evento)}>
        <label className="campo">
          <span className="campo__etiqueta">Tu correo</span>
          <input
            className="campo__control"
            type="email"
            value={correo}
            onChange={(evento) => { setCorreo(evento.target.value); }}
            required
          />
        </label>
        <label className="campo">
          <span className="campo__etiqueta">La contraseña que quieres</span>
          <input
            className="campo__control"
            type="password"
            value={contrasena}
            onChange={(evento) => { setContrasena(evento.target.value); }}
            minLength={12}
            required
          />
        </label>
        {error !== null && (
          <p className="campo__error" role="alert">
            {error}
          </p>
        )}
        <button className="ui-button ui-button--primary" type="submit" disabled={estado === 'enviando'}>
          {estado === 'enviando' ? 'Creando la cuenta…' : 'Crear mi cuenta'}
        </button>
      </form>
    </main>
  );
}

