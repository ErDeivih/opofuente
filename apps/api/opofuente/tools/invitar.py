"""Crea una invitacion de un solo uso para la beta (M8).

**Que hace**: genera un token, **guarda su hash y no el token**, y **enseña el
enlace una vez y solo una**.

**Y eso ultimo es la decision importante, no un descuido**: **el token no se
guarda en claro en ningun sitio** —**ni en la base ni en un fichero**—,
**porque quien lo leyera podria invitar a quien quisiera**. **La consecuencia
es que si el enlace se pierde, no se puede recuperar: hay que crear otro.**
**El comando lo dice al terminar, para que nadie se entere cuando ya no lo
tiene.**

**Lo demas, en una linea cada cosa**: **caduca a los siete dias** —**una
invitacion que no caduca es una puerta abierta**—, **vale para un correo y no
para otro**, **y se canjea una sola vez**.
"""

from __future__ import annotations

import argparse
import hashlib
import secrets
import sys
import unicodedata
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opofuente.config import get_settings
from opofuente.infrastructure.db_models import AccountInvitationRecord

#: Cuanto dura una invitacion. **Siete dias es lo que tarda alguien en mirar el
#: correo y decidirse**; **mas es regalar una puerta que nadie vigila.**
DIAS = 7

#: La direccion desde la que se canjea. **El comando imprime el enlace entero
#: para que se pueda copiar tal cual.**
BASE = "http://127.0.0.1:5173/invitacion"


def normalizar(correo: str) -> str:
    """El correo en su forma canonica, **igual que el alta normal**."""
    return unicodedata.normalize("NFKC", correo).strip().lower()


def crear(correo: str, *, ahora: datetime | None = None) -> tuple[str, datetime]:
    """Guarda la invitacion y **devuelve el token en claro, que no se guarda**."""
    canonico = normalizar(correo)
    if not canonico:
        raise SystemExit("el correo no puede estar vacio")
    # **`secrets.token_urlsafe` y no `uuid4`**: un uuid tiene una estructura
    # reconocible y no es un secreto; **esto son 32 bytes de azar del sistema**.
    token = secrets.token_urlsafe(32)
    huella = hashlib.sha256(token.encode("utf-8")).hexdigest()
    creada = ahora or datetime.now(UTC)
    caduca = creada + timedelta(days=DIAS)

    motor = create_engine(f"sqlite+pysqlite:///{get_settings().data_paths.database}")
    fabrica = sessionmaker(bind=motor)
    with fabrica() as session:
        session.add(
            AccountInvitationRecord(
                id=str(uuid.uuid4()),
                token_hash=huella,
                email=correo.strip(),
                email_normalized=canonico,
                expires_at=caduca,
                used_at=None,
                created_at=creada,
            )
        )
        session.commit()
    return token, caduca


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--correo", required=True, help="a quien se invita")
    args = parser.parse_args(argv)
    token, caduca = crear(args.correo)
    print(f"invitacion creada para {args.correo}")
    print(f"  caduca: {caduca.isoformat()} ({DIAS} dias)")
    print(f"  enlace: {BASE}?token={token}")
    print()
    # **Y esto no es un adorno**: si no se dice, se pierde y no se nota.
    print("GUARDA EL ENLACE AHORA: no se guarda en ningun sitio y no se puede recuperar.")
    print("Si se pierde, hay que crear otra invitacion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
