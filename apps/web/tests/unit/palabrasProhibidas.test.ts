import { describe, expect, it } from 'vitest';

import {
  datosEnElTexto,
  lenguajeInternoEnElTexto,
  revisarPantalla,
} from '../palabrasProhibidas';

/**
 * El detector de palabras prohibidas (revisión de F0, 6 de octubre de 2026).
 *
 * La primera versión buscaba trozos de texto en toda la pantalla y marcaba el propio temario:
 * «versión» sale en 264 enunciados de TAI (control de versiones), «clave» en 163 (clave primaria),
 * «fuente» en 151 (código fuente), «SAS» en 161 (discos SAS) y «Representación» está en el título del
 * tema II.1. Estos casos son los que fijan la diferencia entre **datos que no se pueden ver** y
 * **vocabulario de la interfaz**.
 */
describe('lo que no se puede ver en ninguna parte', () => {
  it('una ruta del propietario o un banco privado saltan en cualquier sitio', () => {
    expect(datosEnElTexto('Fuente: F:\\Oposiciones\\tai\\tema.pdf').length).toBeGreaterThan(0);
    expect(datosEnElTexto('Banco: Rojo -General').map((f) => f.palabra)).toContain('Rojo');
    expect(datosEnElTexto('Celador/a del Servicio de Salud')).not.toHaveLength(0);
  });

  it('un UUID visible salta', () => {
    const encontrados = datosEnElTexto('sesión 0ed21b9a-1c56-4315-819b-928d63b29616');
    expect(encontrados.map((f) => f.palabra)).toContain('uuid visible');
  });

  it('lo que es legítimo dentro del temario no salta', () => {
    // Rutas del sistema que una pregunta de informática nombra sin enseñar nada del propietario.
    expect(datosEnElTexto('La carpeta C:\\Windows\\System32 contiene los ejecutables.')).toHaveLength(
      0,
    );
    // El temario de TAI, tal cual: ni «clave» ni «versión» ni «fuente» ni «representación» son fugas.
    // La comprobación de jerga **no se le aplica**: en la pantalla se pasa solo el texto de la
    // interfaz (menús, botones, avisos), nunca el de las preguntas ni el de los apuntes.
    const temario =
      'Control de versiones: la clave primaria y la clave ajena. El código fuente se compila. ' +
      'Discos SAS y SATA. Representación y comunicación de la información.';
    expect(datosEnElTexto(temario)).toHaveLength(0);
  });

  it('las palabras se buscan completas: «sas» dentro de «casas» no cuenta', () => {
    expect(lenguajeInternoEnElTexto('Las casas y las pesas del mercado')).toHaveLength(0);
    expect(lenguajeInternoEnElTexto('La oposición SAS')).toHaveLength(1);
    // Y «versión» no salta por «versiones» mal contadas… pero «versiones» sí es jerga de interfaz.
    expect(lenguajeInternoEnElTexto('versiones guardadas').map((f) => f.palabra)).toContain(
      'versiones',
    );
  });

  it('la jerga de la interfaz salta fuera del contenido', () => {
    expect(lenguajeInternoEnElTexto('Bandeja')).not.toHaveLength(0);
    expect(lenguajeInternoEnElTexto('Revisión').map((f) => f.palabra)).toContain('revision');
    expect(lenguajeInternoEnElTexto('Ver fuentes del tema')).not.toHaveLength(0);
  });

  it('revisarPantalla separa las dos comprobaciones', () => {
    // En la interfaz: la jerga cuenta. Dentro del contenido: solo los datos.
    expect(revisarPantalla('Bandeja de material', 'Bandeja de material')).not.toHaveLength(0);
    expect(revisarPantalla('Temario', 'El código fuente del programa')).toHaveLength(0);
    expect(revisarPantalla('Temario', 'F:\\Oposiciones\\x.pdf').length).toBeGreaterThan(0);
  });
});
