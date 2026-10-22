"""Canjea una invitacion y crea la cuenta (M8).

**Que hace, y en que orden**: **busca la invitacion por el hash del token**,
**comprueba que no ha caducado**, **que no se ha usado**, **y que el correo es
el suyo**; **y solo entonces crea la cuenta y marca la invitacion**.

**Y el orden importa**: **las tres comprobaciones van antes de escribir nada**.
**Una invitacion caducada que creara la cuenta y luego fallara al marcarse
dejaria a alguien dentro con un enlace que deberia haber dejado de valer.**

**El correo se comprueba aunque el token sea un secreto**: **un enlace reenviado
a otra persona no puede crear una cuenta con otra direccion**, **y eso es lo
que hace que «invitar a alguien» signifique invitar a ese alguien.**
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import unicodedata
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.config import get_settings
from opofuente.infrastructure.db_models import (
    AccountInvitationRecord,
    AccountRecord,
)
from opofuente.infrastructure.password_hashing import ALGORITHM, Argon2PasswordHasher

#: La variable de la que sale la contrasena. **Un secreto no se pasa por argumento.**
VARIABLE = "OPOFUENTE_ADMIN_PASSWORD"
MINIMO = 12


def _normalizar(correo: str) -> str:
    return unicodedata.normalize("NFKC", correo).strip().lower()


def _fabrica() -> sessionmaker[Session]:
    motor = create_engine(f"sqlite+pysqlite:///{get_settings().data_paths.database}")
    return sessionmaker(bind=motor)


def canjear(token: str, correo: str, contrasena: str) -> tuple[bool, str]:
    """Canjea o dice por que no. **No escribe nada si algo no cuadra.**"""
    if len(contrasena) < MINIMO:
        return (False, f"la contrasena tiene {len(contrasena)} y hacen falta {MINIMO}")
    canonico = _normalizar(correo)
    huella = hashlib.sha256(token.encode("utf-8")).hexdigest()
    ahora = datetime.now(UTC)

    ajustes = get_settings()
    hasher = Argon2PasswordHasher(
        time_cost=ajustes.password_hash_time_cost,
        memory_cost_kib=ajustes.password_hash_memory_cost_kib,
        parallelism=ajustes.password_hash_parallelism,
    )
    fabrica = _fabrica()
    with fabrica() as session:
        invitacion = session.execute(
            select(AccountInvitationRecord).where(AccountInvitationRecord.token_hash == huella)
        ).scalar_one_or_none()
        # **Las tres comprobaciones, y el mismo mensaje para las tres si el token
        # no existe**: decir «existe pero caduco» a quien no tiene el enlace le
        # confirma que el enlace existe.
        if invitacion is None:
            return (False, "la invitacion no existe o ya se uso")
        if invitacion.used_at is not None:
            return (False, "la invitacion ya se uso")
        if invitacion.expires_at.replace(tzinfo=UTC) < ahora:
            return (False, "la invitacion ha caducado")
        if invitacion.email_normalized != canonico:
            return (False, "la invitacion es para otra direccion")

        ya_existe = session.execute(
            select(AccountRecord).where(AccountRecord.email_normalized == canonico)
        ).scalar_one_or_none()
        if ya_existe is not None:
            return (False, "ya hay una cuenta con ese correo")

        session.add(
            AccountRecord(
                id=str(uuid.uuid4()),
                email=invitacion.email,
                email_normalized=canonico,
                password_hash=hasher.hash(contrasena),
                password_algo=ALGORITHM,
                owner_id=canonico,
                created_at=ahora,
                updated_at=ahora,
                password_changed_at=ahora,
            )
        )
        invitacion.used_at = ahora
        session.commit()
    return (True, "cuenta creada y invitacion marcada")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token", required=True, help="el token del enlace")
    parser.add_argument("--correo", required=True, help="la direccion invitada")
    args = parser.parse_args(argv)
    contrasena = os.environ.get(VARIABLE, "")
    if not contrasena:
        print(f"falta {VARIABLE}: la contrasena no se pasa por argumento")
        return 2
    bien, que = canjear(args.token, args.correo, contrasena)
    print(f"{'canjeada' if bien else 'NO canjeada'}: {que}")
    return 0 if bien else 1


if __name__ == "__main__":
    sys.exit(main())
