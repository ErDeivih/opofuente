"""Crea la cuenta del administrador de una instalacion (M8).

**Que hace**: mete una cuenta en `accounts` con su contrasena cifrada en
argon2id, **y no hace nada mas**. **Sin invitaciones todavia** —eso es otro
paso y otro fichero—, **esto es lo que hace falta para entrar la primera vez
en una instalacion recien hecha.**

**De donde sale la contrasena, y es la decision importante**: **del entorno
(`OPOFUENTE_ADMIN_PASSWORD`), no de un argumento**. **Un argumento queda en el
historial del terminal y en la lista de procesos**, **y esa contrasena es la
del administrador de la instalacion**. **El correo si va por argumento**:
**no es un secreto.**

**Y es idempotente**: **si la cuenta ya existe, la actualiza en vez de
fallar**, **para que volver a lanzar el instalador no se rompa en el segundo
intento**. **Dice cual de las dos cosas hizo.**
"""

from __future__ import annotations

import argparse
import os
import sys
import unicodedata
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from opofuente.config import get_settings
from opofuente.infrastructure.db_models import AccountRecord
from opofuente.infrastructure.password_hashing import ALGORITHM, Argon2PasswordHasher

#: La variable de entorno de la que sale la contrasena. **Un secreto no se pasa
#: por argumento.**
VARIABLE = "OPOFUENTE_ADMIN_PASSWORD"

#: La longitud minima. **No es un numero magico: por debajo de esto, argon2
#: protege una contrasena que se adivina igual.**
MINIMO = 12


def normalizar(correo: str) -> str:
    """El correo en su forma canonica, **igual que lo hace el alta normal**."""
    limpio = unicodedata.normalize("NFKC", correo).strip().lower()
    return limpio


def crear(correo: str, contrasena: str) -> tuple[bool, str]:
    """Crea o actualiza la cuenta. **Devuelve si la creo y que hizo.**

    **`owner_id` se pone al del propio correo**: **en una instalacion de una
    persona, el administrador es el dueño**, **y dejar el campo vacio haria que
    sus datos no aparecieran en ningun sitio.**
    """
    if len(contrasena) < MINIMO:
        raise SystemExit(f"la contrasena tiene {len(contrasena)} caracteres y hacen falta {MINIMO}")
    canonico = normalizar(correo)
    if not canonico:
        raise SystemExit("el correo no puede estar vacio")

    motor = create_engine(f"sqlite+pysqlite:///{get_settings().data_paths.database}")
    fabrica = sessionmaker(bind=motor)
    # **El mismo coste que la aplicacion**: un administrador creado con un
    # argon2 mas barato seria una contrasena mas facil de romper que las demas,
    # y nadie lo notaria hasta que importara.
    ajustes = get_settings()
    hasher = Argon2PasswordHasher(
        time_cost=ajustes.password_hash_time_cost,
        memory_cost_kib=ajustes.password_hash_memory_cost_kib,
        parallelism=ajustes.password_hash_parallelism,
    )
    cifrada = hasher.hash(contrasena)
    ahora = datetime.now(UTC)
    with fabrica() as session:
        existente = session.execute(
            select(AccountRecord).where(AccountRecord.email_normalized == canonico)
        ).scalar_one_or_none()
        if existente is not None:
            existente.password_hash = cifrada
            existente.password_algo = ALGORITHM
            existente.password_changed_at = ahora
            existente.updated_at = ahora
            session.commit()
            return (False, "ya existia: se le ha cambiado la contrasena")
        session.add(
            AccountRecord(
                id=str(uuid.uuid4()),
                email=correo.strip(),
                email_normalized=canonico,
                password_hash=cifrada,
                password_algo=ALGORITHM,
                owner_id=canonico,
                created_at=ahora,
                updated_at=ahora,
                password_changed_at=ahora,
            )
        )
        session.commit()
    return (True, "creada")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--correo", required=True, help="el correo del administrador")
    args = parser.parse_args(argv)
    contrasena = os.environ.get(VARIABLE, "")
    if not contrasena:
        print(f"falta {VARIABLE}: la contrasena no se pasa por argumento")
        return 2
    _creada, que = crear(args.correo, contrasena)
    print(f"administrador {args.correo}: {que}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
