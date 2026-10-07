"""Los exámenes oficiales del INAP son publicables; el resto del banco, no (F2).

Revision ID: 0026_examenes_oficiales_publicos
Revises: 0025_question_set_distribution
Create Date: 2026-10-07

`distribution` nace en `personal` para no cambiar de golpe la visibilidad de nada. Esta migración
hace la parte que sí es una decisión: **los cuatro exámenes oficiales del INAP de TAI 2025** —los
que importó `reimportar_los_examenes_oficiales_de_tai_2025.py`: ingreso libre modelos A y B, y
promoción interna modelos A y B— pasan a `public`, porque su titular los publica (el INAP publica
los cuestionarios y las plantillas de sus procesos). Los 227 bancos privados del propietario se
quedan en `personal`.

Lo que se ve al elegirlos:

- **se eligen por título y tipo, no por identificador**: los identificadores son de esta base y no
  viajan en un fichero de migración. El título es el dato que el importador escribió y el que una
  persona reconoce.
- **se excluyen los archivados**: en la base real hay **ocho** filas con esos cuatro títulos, porque
  el importador se ejecutó dos veces. Cuatro están `archived` y su clave está `superseded` (la
  primera pasada); las otras cuatro están `draft` con la clave `active`. Marcar también las
  archivadas diría que son publicables exámenes que ya no son los vigentes, así que la migración
  deja `public` exactamente los cuatro que hoy se pueden hacer.
- **es idempotente y se puede repetir**: el `WHERE` exige `distribution <> 'public'`, de modo que
  volver a ejecutarla no cambia nada. En una base recién creada (la puerta 13 migra desde cero) no
  hay ninguna fila que cumpla el filtro y la sentencia no hace nada.

**Antes de ejecutarla sobre los datos del propietario hay que hacer copia de seguridad**
(`POST /api/v1/backups` con la API levantada, o una copia coherente del SQLite). `downgrade` vuelve
a dejar en `personal` esos mismos conjuntos: es la inversa exacta de lo que esta migración cambió.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0026_examenes_oficiales_publicos"
down_revision = "0025_question_set_distribution"
branch_labels = None
depends_on = None

#: El filtro que identifica los cuatro exámenes, repetido en la ida y en la vuelta.
_SQL_PUBLICOS = (
    "UPDATE question_sets SET distribution = 'public' "
    "WHERE set_type = 'official_exam' AND status <> 'archived' "
    "AND title IN (:t1, :t2, :t3, :t4) AND distribution <> 'public'"
)

_SQL_PERSONALES = (
    "UPDATE question_sets SET distribution = 'personal' "
    "WHERE set_type = 'official_exam' AND status <> 'archived' "
    "AND title IN (:t1, :t2, :t3, :t4)"
)

#: Los cuatro exámenes oficiales del INAP de TAI 2025, por su título publicado.
TITULOS: tuple[str, ...] = (
    "TAI ingreso libre 2025 · modelo A (examen oficial INAP)",
    "TAI ingreso libre 2025 · modelo B (examen oficial INAP)",
    "TAI promoción interna 2025 · modelo A (examen oficial INAP)",
    "TAI promoción interna 2025 · modelo B (examen oficial INAP)",
)

_PARAMETROS = {"t1": TITULOS[0], "t2": TITULOS[1], "t3": TITULOS[2], "t4": TITULOS[3]}


def upgrade() -> None:
    op.get_bind().execute(sa.text(_SQL_PUBLICOS), _PARAMETROS)


def downgrade() -> None:
    op.get_bind().execute(sa.text(_SQL_PERSONALES), _PARAMETROS)
