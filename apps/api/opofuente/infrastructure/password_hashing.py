"""El derivador de contraseñas: argon2id, con los parámetros a la vista (S28, §8).

**Por qué argon2id y no un SHA con sal.** Un digest rápido está hecho para ser rápido, y eso es
exactamente lo que no se quiere delante de una contraseña: con una tarjeta gráfica se prueban miles
demillones por segundo. Argon2id está hecho para lo contrario —consume memoria a propósito— y es el
ganador del concurso de referencia de la propia Password Hashing Competition y la recomendación que
hace el NIST en su SP 800-63B. La aplicación no traía ningún derivador (solo `hashlib`), así que se
añade `argon2-cffi`, que es una dependencia de una sola cosa, mantenida y con envoltorio tipado.

**Lo que no hace.** No inventa la política de contraseñas —eso es `domain/accounts.py`— ni decide
cuándo hay que volver a escribir un resumen: lo dice `needs_rehash`, y quien lo pregunta es el
servicio al acertar la contraseña, que es el único momento en el que la contraseña en claro está a
mano y se puede aprovechar para reescribir el resumen con los parámetros de hoy.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

#: El nombre del algoritmo tal como se guarda en `accounts.password_algo`.
ALGORITHM = "argon2id"


class Argon2PasswordHasher:
    """Escribe y comprueba resúmenes argon2id.

    La comprobación **no lanza**: devuelve `False`. Un resumen ilegible (una fila tocada a mano, una
    versión futura) es un «no coincide», no una excepción que tumbe la petición: quien está al otro
    lado solo tiene que saber que esa contraseña no vale.
    """

    def __init__(self, *, time_cost: int, memory_cost_kib: int, parallelism: int) -> None:
        self._hasher = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost_kib,
            parallelism=parallelism,
            hash_len=32,
            salt_len=16,
        )

    @property
    def algorithm(self) -> str:
        return ALGORITHM

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, stored_hash: str) -> bool:
        try:
            return self._hasher.verify(stored_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def needs_rehash(self, stored_hash: str) -> bool:
        """¿Este resumen se escribió con parámetros más flojos que los de hoy?"""
        try:
            return self._hasher.check_needs_rehash(stored_hash)
        except InvalidHashError:
            # Un resumen que no se puede leer no se puede mejorar: se deja como está y no se fuerza
            # un cambio de contraseña por un formato ilegible, que sería culpa de la aplicación.
            return False


__all__ = ["ALGORITHM", "Argon2PasswordHasher"]
