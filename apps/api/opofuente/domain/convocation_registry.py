"""Registro de convocatorias TIC publicadas por boletines oficiales.

Este módulo **no** es la convocatoria de examen que usa el motor (`domain.profiles`): es el
rastreador de lo que sale en el BOE y en los boletines autonómicos o provinciales. Una entrada del
registro dice qué cuerpo convoca, con qué plazas, en qué plazo y dónde está el acto oficial; el
vínculo con un perfil se resuelve por el nombre del cuerpo, nunca por suposición.

Capa de dominio: sin FastAPI, sin SQLAlchemy y sin acceso a disco. La validación de forma la hace
pydantic en `infrastructure.convocation_registry_loader`; aquí quedan las reglas de coherencia que
no dependen del formato del fichero.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from urllib.parse import urlsplit

from opofuente.domain.classification import AuthorityTier, RightsStatus
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.profiles import Profile

#: Dominio oficial que se acepta como enlace de una convocatoria estatal.
BOE_HOST = "boe.es"

_CODE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class Grupo(StrEnum):
    """Grupo de clasificación del cuerpo convocado (art. 76 TREBEP)."""

    A1 = "A1"
    A2 = "A2"
    C1 = "C1"


class SistemaAcceso(StrEnum):
    """Sistema selectivo. Un mismo acto puede convocar turno libre y promoción interna."""

    OPOSICION = "oposicion"
    CONCURSO_OPOSICION = "concurso_oposicion"


@dataclass(frozen=True, slots=True)
class Procedencia:
    """Procedencia obligatoria de una entrada: qué fuente y qué cita literal la respaldan."""

    source_id: str
    quote: str


@dataclass(frozen=True, slots=True)
class FuenteOficial:
    """Acto publicado en un boletín oficial del que sale una o varias entradas del registro."""

    id: str
    title: str
    publisher: str
    identifier: str
    canonical_url: str
    authority_tier: AuthorityTier
    rights_status: RightsStatus
    published_at: date | None = None


@dataclass(frozen=True, slots=True)
class ConvocatoriaRegistrada:
    """Una convocatoria tal como la publica el boletín, sin interpretar más de lo que dice.

    `plazas_promocion_interna` es nulo cuando el acto no publica esa cifra: no se rellena con cero
    ni se deduce del total.
    """

    code: str
    cuerpo: str
    grupo: Grupo
    administracion: str
    sistemas: tuple[SistemaAcceso, ...]
    plazas_libres: int
    plazo_dias_habiles: int
    enlace_oficial: str
    procedencia: Procedencia
    plazas_promocion_interna: int | None = None
    published_at: date | None = None

    @property
    def plazas_totales(self) -> int:
        return self.plazas_libres + (self.plazas_promocion_interna or 0)


@dataclass(frozen=True, slots=True)
class RegistroDeConvocatorias:
    """Fuentes y convocatorias ya validadas, tal como las consume la aplicación."""

    fuentes: tuple[FuenteOficial, ...]
    convocatorias: tuple[ConvocatoriaRegistrada, ...]


def normalize(text: str) -> str:
    """Normaliza un nombre de cuerpo para compararlo (sin acentos, mayúsculas ni puntuación)."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_accents.lower()).strip()


def _is_official_url(url: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == BOE_HOST or host.endswith(f".{BOE_HOST}"))


def validate_registry(
    convocatorias: Sequence[ConvocatoriaRegistrada],
    fuentes: Iterable[FuenteOficial],
) -> None:
    """Comprueba que el registro es coherente antes de publicarlo.

    Un registro mal formado no es un registro incompleto: es un dato que se puede enseñar como si
    fuera oficial. Por eso cualquier incoherencia aborta la carga entera.
    """
    if not convocatorias:
        raise InvariantViolationError("el registro de convocatorias está vacío")

    lista_de_fuentes = tuple(fuentes)
    sources = {fuente.id: fuente for fuente in lista_de_fuentes}
    if len(sources) != len(lista_de_fuentes):
        raise InvariantViolationError("el registro repite el id de una fuente")

    codes: set[str] = set()
    for entrada in convocatorias:
        if not _CODE_PATTERN.match(entrada.code):
            raise InvariantViolationError(
                f"{entrada.code}: el código del registro no es un slug en minúsculas"
            )
        if entrada.code in codes:
            raise InvariantViolationError(f"{entrada.code}: convocatoria repetida en el registro")
        codes.add(entrada.code)

        if not entrada.cuerpo.strip():
            raise InvariantViolationError(f"{entrada.code}: la convocatoria no dice el cuerpo")
        if not entrada.administracion.strip():
            raise InvariantViolationError(f"{entrada.code}: la convocatoria no dice administración")
        if not entrada.sistemas:
            raise InvariantViolationError(f"{entrada.code}: la convocatoria no declara sistema")
        if len(set(entrada.sistemas)) != len(entrada.sistemas):
            raise InvariantViolationError(f"{entrada.code}: sistemas de acceso repetidos")

        if entrada.plazas_libres < 0:
            raise InvariantViolationError(f"{entrada.code}: plazas libres negativas")
        if entrada.plazas_promocion_interna is not None and entrada.plazas_promocion_interna < 0:
            raise InvariantViolationError(f"{entrada.code}: plazas de promoción interna negativas")
        if entrada.plazas_totales <= 0:
            raise InvariantViolationError(f"{entrada.code}: la convocatoria no convoca plazas")
        if entrada.plazo_dias_habiles <= 0:
            raise InvariantViolationError(
                f"{entrada.code}: el plazo de solicitudes no puede ser cero"
            )

        if not _is_official_url(entrada.enlace_oficial):
            raise InvariantViolationError(
                f"{entrada.code}: el enlace {entrada.enlace_oficial} no es oficial (https, boe.es)"
            )

        procedencia = entrada.procedencia
        if not procedencia.source_id.strip():
            raise InvariantViolationError(f"{entrada.code}: la convocatoria no dice su fuente")
        if not procedencia.quote.strip():
            raise InvariantViolationError(f"{entrada.code}: la convocatoria no cita su fuente")
        fuente = sources.get(procedencia.source_id)
        if fuente is None:
            raise InvariantViolationError(
                f"{entrada.code}: la fuente {procedencia.source_id} no está en el registro"
            )
        if fuente.canonical_url != entrada.enlace_oficial:
            raise InvariantViolationError(
                f"{entrada.code}: el enlace no coincide con el de la fuente {procedencia.source_id}"
            )


def matches_profile(entrada: ConvocatoriaRegistrada, profile: Profile) -> bool:
    """¿El cuerpo convocado es el de este perfil?

    La comparación es por contención del nombre normalizado en cualquiera de los dos sentidos: el
    perfil curado escribe el nombre completo del cuerpo y el registro también, pero uno de los dos
    puede añadir el turno («… (ingreso libre)») o el código interno.
    """
    cuerpo = normalize(entrada.cuerpo)
    nombre = normalize(profile.opposition.name)
    if not cuerpo or not nombre:
        return False
    return cuerpo in nombre or nombre in cuerpo


def convocatorias_del_perfil(
    profile: Profile, convocatorias: Sequence[ConvocatoriaRegistrada]
) -> tuple[ConvocatoriaRegistrada, ...]:
    """Convocatorias del registro que corresponden al cuerpo del perfil, de la más reciente atrás."""
    encontradas = [entrada for entrada in convocatorias if matches_profile(entrada, profile)]
    encontradas.sort(key=lambda entrada: (entrada.published_at or date.min, entrada.code))
    return tuple(reversed(encontradas))


def vincular_con_perfiles(
    convocatorias: Sequence[ConvocatoriaRegistrada], profiles: Sequence[Profile]
) -> tuple[tuple[str, tuple[ConvocatoriaRegistrada, ...]], ...]:
    """Reparte el registro entre los perfiles cargados.

    Un cuerpo del registro sin perfil no es un error: el registro también sirve para descubrir
    cuerpos que la aplicación todavía no prepara. Por eso solo se devuelven los perfiles con
    alguna convocatoria vinculada.
    """
    vinculadas: list[tuple[str, tuple[ConvocatoriaRegistrada, ...]]] = []
    for profile in profiles:
        del_perfil = convocatorias_del_perfil(profile, convocatorias)
        if del_perfil:
            vinculadas.append((profile.opposition.code, del_perfil))
    return tuple(vinculadas)
