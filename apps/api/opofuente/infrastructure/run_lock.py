"""La marca de corrida del clasificador (F5): una sola corrida por base y por vez.

Esto existe por un fallo medido, no por prudencia. El 8 de octubre de 2026 se lanzaron dos corridas
del clasificador sobre los datos reales del propietario y **se pisaron**: cada una calculó su lista
de preguntas pendientes antes de que la otra escribiera, así que las dos propusieron temas a las
mismas preguntas y quedaron cuatro preguntas con dos temas propuestos distintos (dos de ellas con un
tema aceptado y otro provisional) y nueve con más de un epígrafe. La auditoría lo deja ver —hay tres
epígrafes aceptados cuyo tema ya existía, que son las filas «ya estaba» de un informe intermedio— y
el propietario, al despachar su cola, habría visto la misma pregunta dos veces.

La marca vive en `app_metadata` (la tabla que ya existe para esto) con una clave propia:

- **al arrancar**, si la clave está y es reciente, la corrida **se niega** y dice desde cuándo corre
  la otra y con qué oposición, en lugar de escribir encima;
- **al terminar**, se retira, tanto si la corrida acaba bien como si falla: la marca se suelta en un
  `finally`, que es la única forma de que un error no deje la clasificación bloqueada para siempre;
- si el proceso muere de golpe (un `kill`, un corte de luz), la marca se queda. Para que eso no
  bloquee el comando para siempre, una marca más vieja que `HORAS_ANTES_DE_DARLA_POR_MUERTA` se da
  por muerta y se toma, **diciéndolo**. Borrarla a mano también vale, y el mensaje dice dónde está.

La marca guarda un **testigo** aleatorio y solo se suelta con él: si una corrida se quedó colgada y
otra tomó el relevo, la vieja no puede retirar la marca de la nueva al despertar.
"""

from __future__ import annotations

import json
import logging
import socket
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.errors import ClassificationAlreadyRunningError
from opofuente.infrastructure.db_models import AppMetadataRecord

logger = logging.getLogger("opofuente.infrastructure.run_lock")

#: La clave en `app_metadata`. Se enseña en el mensaje de error para que se pueda retirar a mano.
CLAVE = "clasificacion_en_curso"

#: La marca de los apuntes: la misma protección, otra clave. Existe por el mismo tipo de accidente:
#: el 10 de octubre de 2026 se lanzaron dos corridas de `apuntes` a la vez sobre I.6 y hubo que
#: matar la segunda a los tres minutos, antes de que escribiera. Escribir apuntes es lo más caro
#: del proyecto (cientos de llamadas al modelo), así que la segunda corrida se niega en vez de
#: repartirse el trabajo a medias con la primera.
CLAVE_APUNTES = "apuntes_en_curso"

#: A partir de aquí, una marca se da por muerta y se toma. Doce horas es más que la corrida más
#: larga que se ha medido (128 bancos, ≈3,6 $) por un margen amplio, y menos que «para siempre».
HORAS_ANTES_DE_DARLA_POR_MUERTA = 12


def _now() -> datetime:
    return datetime.now(UTC)


class ClassificationRunLock:
    """La marca de corrida sobre `app_metadata`: se toma, se suelta y no deja pasar a la segunda.

    `clave` y `que` son lo único que cambia entre la clasificación y los apuntes: la mecánica —tomar
    la marca, negarse si hay otra viva, darla por muerta a las doce horas, soltarla en el `finally`
    con el testigo propio— es la misma y vive en un solo sitio a propósito. Dos copias de esto
    acabarían comportándose distinto.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        opposition_code: str,
        clave: str = CLAVE,
        que: str = "clasificación",
        hours_before_stale: float = HORAS_ANTES_DE_DARLA_POR_MUERTA,
    ) -> None:
        self._session_factory = session_factory
        self._opposition_code = opposition_code
        self._clave = clave
        self._que = que
        self._hours_before_stale = hours_before_stale
        #: El testigo de **esta** corrida: solo ella puede retirar su propia marca.
        self._token: str | None = None

    @contextmanager
    def hold(self) -> Iterator[None]:
        """Toma la marca, deja correr el bloque y la suelta pase lo que pase.

        El `finally` no es un detalle: sin él, un fallo al llamar al modelo dejaría la base
        marcada y el propietario no podría volver a clasificar sin tocar la base a mano.
        """
        self.acquire()
        try:
            yield
        finally:
            self.release()

    def acquire(self) -> None:
        """Toma la marca. Si ya hay una corrida en curso y viva, no deja pasar."""
        ahora = _now()
        testigo = str(uuid.uuid4())
        with self._session_factory() as session:
            existente = session.get(AppMetadataRecord, self._clave)
            if existente is not None:
                en_curso = self._read(existente)
                if not self._is_stale(existente.updated_at, ahora):
                    raise ClassificationAlreadyRunningError(
                        started_at=en_curso.get("iniciada", str(existente.updated_at)),
                        opposition_code=en_curso.get("oposicion", "desconocida"),
                        que=self._que,
                        hint=(
                            f"Si esa corrida ya no existe (se murió el proceso), borra la clave "
                            f"«{self._clave}» de la tabla app_metadata o espera "
                            f"{self._hours_before_stale:g} h: a partir de ahí se da por muerta."
                        ),
                    )
                # Marca muerta: se toma el relevo, diciéndolo. Un proceso que murió de golpe no
                # puede desbloquear el comando para siempre.
                logger.warning(
                    "marca de %s sin retirar desde %s: se da por muerta y se toma",
                    self._que,
                    en_curso.get("iniciada", existente.updated_at),
                )
            session.merge(
                AppMetadataRecord(
                    key=self._clave,
                    value=json.dumps(
                        {
                            "testigo": testigo,
                            "iniciada": ahora.isoformat(timespec="seconds"),
                            "oposicion": self._opposition_code,
                            "equipo": socket.gethostname(),
                        },
                        ensure_ascii=False,
                    ),
                    updated_at=ahora,
                )
            )
            try:
                session.commit()
            except IntegrityError as error:
                # Dos procesos a la vez: los dos vieron la clave libre y los dos intentaron
                # escribir. Quien pierde el `INSERT` es el que se niega, que es justo lo que se
                # quiere; reintentar sería volver a pisarse.
                session.rollback()
                raise ClassificationAlreadyRunningError(
                    started_at="ahora mismo (otra corrida acaba de arrancar)",
                    opposition_code=self._opposition_code,
                    que=self._que,
                    hint=(
                        "Dos procesos a la vez sobre la misma base: espera a que termine el otro."
                    ),
                ) from error
        self._token = testigo

    def release(self) -> None:
        """Retira la marca **si es la de esta corrida**. Sin testigo propio, no toca nada."""
        if self._token is None:
            return
        with self._session_factory() as session:
            existente = session.get(AppMetadataRecord, self._clave)
            if existente is None or self._read(existente).get("testigo") != self._token:
                return
            session.execute(delete(AppMetadataRecord).where(AppMetadataRecord.key == self._clave))
            session.commit()
        self._token = None

    @staticmethod
    def _read(fila: AppMetadataRecord) -> dict[str, str]:
        """Lo que guarda la marca, ya leído. Sin poder leerla, se devuelve vacío y se dice
        «desconocida» donde haga falta."""
        try:
            datos = json.loads(fila.value)
        except ValueError:
            return {}
        if not isinstance(datos, dict):
            return {}
        return {str(clave): str(valor) for clave, valor in datos.items()}

    def _is_stale(self, updated_at: datetime, ahora: datetime) -> bool:
        """¿La marca es tan vieja que su corrida ya no puede estar viva?"""
        cuando = updated_at if updated_at.tzinfo is not None else updated_at.replace(tzinfo=UTC)
        return (ahora - cuando).total_seconds() > self._hours_before_stale * 3600


def current_run(
    session_factory: sessionmaker[Session], *, clave: str = CLAVE
) -> dict[str, str] | None:
    """La corrida en curso, si la hay: lo lee `--listar` para poder decirla sin tomar la marca."""
    with session_factory() as session:
        fila = session.scalar(select(AppMetadataRecord).where(AppMetadataRecord.key == clave))
        if fila is None:
            return None
        return ClassificationRunLock._read(fila) | {"marca": str(fila.updated_at)}


__all__ = [
    "CLAVE",
    "CLAVE_APUNTES",
    "HORAS_ANTES_DE_DARLA_POR_MUERTA",
    "ClassificationRunLock",
    "current_run",
]
