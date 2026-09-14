import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <>
      <header className="page__header">
        <h1>Página no encontrada</h1>
      </header>
      <section className="card">
        <p>La dirección solicitada no corresponde a ninguna sección de OpoFuente.</p>
        <p>
          <Link to="/">Volver a Inicio</Link>
        </p>
      </section>
    </>
  );
}
