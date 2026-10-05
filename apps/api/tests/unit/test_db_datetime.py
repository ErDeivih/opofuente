"""Las fechas se guardan en UTC y se leen **con zona** (5 de octubre de 2026).

SQLite no guarda la zona horaria: se escribía un `datetime` con zona y se leía sin ella, así que la
API servía «2026-10-05T10:43:52.793645» y el navegador lo interpretaba como hora local de Madrid. El
cronómetro de una práctica empezaba en `2:00:03` y un examen oficial de 120 minutos nacía con el
tiempo agotado. Esto fija las dos mitades del arreglo: al leer, la fecha lleva UTC; al escribir, se
guarda en UTC (y sin zona en el fichero, para no cambiar el formato de lo que ya hay).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import Integer, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from opofuente.infrastructure.db_models import UtcDateTime


class _Base(DeclarativeBase):
    pass


class _Marca(_Base):
    __tablename__ = "marca_de_prueba"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    momento: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


def _motor(tmp_path):
    motor = create_engine(f"sqlite:///{tmp_path / 'fechas.sqlite3'}")
    _Base.metadata.create_all(motor)
    return motor


def test_una_fecha_guardada_se_lee_con_utc(tmp_path) -> None:
    motor = _motor(tmp_path)
    escrita = datetime(2026, 10, 5, 10, 43, 52, 793645, tzinfo=UTC)
    with Session(motor) as sesion:
        sesion.add(_Marca(id=1, momento=escrita))
        sesion.commit()
        leida = sesion.execute(select(_Marca.momento).where(_Marca.id == 1)).scalar_one()
    motor.dispose()

    assert leida.tzinfo is not None, "sin zona, el navegador la toma por hora local"
    assert leida == escrita
    assert leida.utcoffset() == timedelta(0)


def test_una_fecha_de_otra_zona_se_guarda_en_utc(tmp_path) -> None:
    motor = _motor(tmp_path)
    madrid = timezone(timedelta(hours=2))
    en_madrid = datetime(2026, 10, 5, 12, 43, 52, tzinfo=madrid)
    with Session(motor) as sesion:
        sesion.add(_Marca(id=1, momento=en_madrid))
        sesion.commit()
        leida = sesion.execute(select(_Marca.momento).where(_Marca.id == 1)).scalar_one()
        # Lo que hay en el fichero sigue siendo el mismo formato de siempre: sin zona, en UTC.
        crudo = sesion.execute(text("select momento from marca_de_prueba")).scalar_one()
    motor.dispose()

    assert leida == en_madrid, "el instante es el mismo"
    assert leida.hour == 10 and leida.tzinfo is UTC
    assert "+" not in crudo and not crudo.endswith("Z")


def test_una_fecha_heredada_sin_zona_se_lee_como_utc(tmp_path) -> None:
    """Toda la base que ya existe tiene las fechas sin zona, y están en UTC: se leen como UTC."""
    motor = _motor(tmp_path)
    with Session(motor) as sesion:
        sesion.execute(
            text(
                "insert into marca_de_prueba (id, momento) values (1, '2026-10-05 10:43:52.793645')"
            )
        )
        sesion.commit()
        leida = sesion.execute(select(_Marca.momento).where(_Marca.id == 1)).scalar_one()
    motor.dispose()

    assert leida == datetime(2026, 10, 5, 10, 43, 52, 793645, tzinfo=UTC)
