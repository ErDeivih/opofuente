/**
 * El canje de una invitación, del lado de la pantalla (M8).
 *
 * **Lo que viaja es el token del enlace, el correo y la contraseña que se quiere poner**, y **lo que vuelve es
 * si se creó la cuenta o el motivo por el que no.**
 *
 * **El motivo se enseña tal cual**: lo escribe el servidor y **no distingue «no existe» de «estaba mal»** a
 * propósito —confirmar que un enlace existe a quien no lo tiene es regalar media invitación—, **así que la
 * pantalla no lo reinterpreta**.
 */
import { apiFetch } from './client';

export interface CanjeResultado {
  creada: boolean;
  motivo: string;
}

export async function canjearInvitacion(cuerpo: {
  token: string;
  correo: string;
  contrasena: string;
}): Promise<CanjeResultado> {
  return apiFetch<CanjeResultado>('/invitations/accept', {
    method: 'POST',
    body: JSON.stringify(cuerpo),
  });
}
