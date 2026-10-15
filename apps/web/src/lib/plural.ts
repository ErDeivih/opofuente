/**
 * Un número con su palabra **en su forma**: «1 aviso», «3 avisos».
 *
 * Existe por un defecto real que se vio en la pantalla: la fila de un examen decía «1 claves
 * sospechosas». No es cosmético —el propietario lee esa línea en cada fila— y tampoco se arregla con
 * una regla que añada una «s»: en español el plural no es eso («pregunta que no se puede juzgar» →
 * «preguntas que no se pueden juzgar»).
 *
 * Por eso el singular y el plural se escriben **los dos**, aquí o donde se use, y nunca se derivan
 * el uno del otro.
 */
export function conNumero(cantidad: number, singular: string, plural: string): string {
  return `${String(cantidad)} ${cantidad === 1 ? singular : plural}`;
}
