/**
 * Las estadísticas del alumno, del lado de la pantalla (M6).
 *
 * **Lo que viaja es lo que se enseña**: la frase de la nota ya viene compuesta del servidor y el texto
 * de la comparación del tiempo también. **La pantalla no vuelve a componer frases con cifras** —dos
 * sitios que las escriben acaban diciendo cosas distintas— **y tampoco decide si hay margen**: si el
 * intervalo viene a `null`, no lo hay, y eso no es un cero.
 */
import { apiFetch } from './client';

export interface TemaFlojo {
  codigo: string;
  titulo: string;
  intentos: number;
  acierto: number;
  frase: string;
}

export interface SemanaDeAcierto {
  empieza: string;
  intentos: number;
  acierto: number;
}

export interface Nota {
  nota: number;
  minimo: number | null;
  maximo: number | null;
  intentos: number;
  frase: string;
}

export interface Stats {
  nota: Nota | null;
  flojos: TemaFlojo[];
  semanas: SemanaDeAcierto[];
  segundos_por_pregunta: number | null;
  comparacion_del_tiempo: string | null;
}

export async function fetchStats(): Promise<Stats> {
  return apiFetch<Stats>('/stats');
}
