"""Si la clave de un conjunto se puede fiar: `key_reliability` (F19, §1 del objetivo).

Revision ID: 0036_claves_no_fiables
Revises: 0034_avisos_en_curso_y_nota (o 0035, si ya está en el árbol: ver abajo)
Create Date: 2026-10-13

**El problema, medido.** Comparando la letra que dan los apuntes con la clave de cada pregunta y
agrupando por conjunto de origen (`question_note_anchors`, 5.925 preguntas con letra y clave), la
media global es del 8,9 % —los apuntes se equivocan a veces, y eso es normal—, pero **10 conjuntos
pasan del 30 %**, y en un conjunto de 18 preguntas eso no es que los apuntes se equivoquen: es que
**la clave está mal**. Y el propietario ya está practicando con ellos.

**Lo que añade.** Una columna de vocabulario cerrado en `question_sets` —el conjunto es la unidad
del fallo: la clave se extrajo del material de un conjunto entero, no de una pregunta suelta— y
**los dos números de la medida**, para que el veredicto se pueda auditar sin volver a medirlo:

- `key_reliability` — `fiable` · `dudosa` · `no_fiable`. Por defecto `fiable`: **ninguna fila cambia
  de significado al migrar**, y un conjunto que nadie ha medido no queda en cuarentena por no
  saberse.
- `key_checked_count` — preguntas con letra y clave que se compararon.
- `key_discrepant_count` — cuántas de esas no coincidían.
- `key_measured_at` — cuándo se midió, para saber si la cifra es de hoy.

Los dos contadores van con `CHECK >= 0` y con `discrepant <= checked`: un numerador mayor que su
denominador es una cifra imposible, y mejor que la base la rechace a que un informe la enseñe.

**Vuelta atrás.** Quita las cuatro columnas y sus tres restricciones. No hace falta convertir nada
antes —al revés que en `0034`— porque bajar solo **pierde la medida**: el esquema vuelve al de
`0034` y las claves siguen exactamente donde estaban. Lo que se pierde es saber cuáles estaban en
cuarentena, y por eso el `downgrade` lo dice.

**Dos cabezas al fusionar.** Este bloque trabajó en su propio árbol (`f19-claves-fiables`) mientras
otro bloque tenía la `0035` en el suyo, y ninguno de los dos podía saber cuál entraba antes en
`main`. Para no dejar la cadena con dos cabezas —que rompen `upgrade head`—, la revisión previa se
resuelve **al importar**: si `0035_incidencias_despachables` ya está en el directorio de versiones,
esta migración va detrás de ella; si no, va detrás de `0034`. Es determinista para un árbol dado y
se comprueba en la prueba de esta migración.
"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision = "0036_claves_no_fiables"
branch_labels = None
depends_on = None

#: Las dos fronteras del §1: por encima del 30 %, cuarentena; entre el 15 % y el 30 %, marcada.
_VEREDICTOS = "key_reliability IN ('fiable', 'dudosa', 'no_fiable')"
_CONTADORES_NO_NEGATIVOS = "key_checked_count >= 0 AND key_discrepant_count >= 0"
_DISCREPANTES_CABEN = "key_discrepant_count <= key_checked_count"


def _revision_previa() -> str:
    """`0035` si el otro bloque ya la dejó en el árbol, y si no `0034`.

    Los dos bloques se crearon desde el mismo `main` y no se pueden fusionar entre ellos; el
    propietario fusiona. Sin esto, la fusión dejaría **dos cabezas** y `upgrade head` fallaría con
    «Multiple head revisions are present», que es un fallo que no se ve hasta que alguien intenta
    migrar de verdad.
    """
    versiones = Path(__file__).resolve().parent
    if (versiones / "0035_incidencias_despachables.py").exists():
        return "0035_incidencias_despachables"
    return "0034_avisos_en_curso_y_nota"


down_revision = _revision_previa()


def upgrade() -> None:
    with op.batch_alter_table("question_sets") as batch:
        batch.add_column(
            sa.Column(
                "key_reliability",
                sa.String(16),
                nullable=False,
                server_default=sa.text("'fiable'"),
            )
        )
        batch.add_column(
            sa.Column(
                "key_checked_count",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )
        batch.add_column(
            sa.Column(
                "key_discrepant_count",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )
        # `DateTime` con hora: la medida se repite muchas veces el mismo día, y dos medidas del
        # mismo día tienen que poder ordenarse.
        batch.add_column(sa.Column("key_measured_at", sa.DateTime(), nullable=True))
        batch.create_check_constraint("ck_question_set_key_reliability", _VEREDICTOS)
        batch.create_check_constraint("ck_question_set_key_counts", _CONTADORES_NO_NEGATIVOS)
        batch.create_check_constraint("ck_question_set_key_discrepant", _DISCREPANTES_CABEN)
        # El motor de tests pregunta «¿de qué conjuntos no me fío?» en cada composición: sin índice
        # eso es un recorrido de la tabla entera.
        batch.create_index("ix_question_sets_key_reliability", ["key_reliability"])


def downgrade() -> None:
    # Bajar **pierde la medida y el veredicto**, no las claves: las preguntas, sus plantillas y sus
    # entradas siguen donde estaban. Lo que se pierde es saber cuáles estaban en cuarentena, y por
    # eso se dice aquí: si se vuelve a subir, todos los conjuntos vuelven a `fiable` hasta que la
    # puerta de datos los mida otra vez.
    with op.batch_alter_table("question_sets") as batch:
        batch.drop_index("ix_question_sets_key_reliability")
        batch.drop_constraint("ck_question_set_key_discrepant", type_="check")
        batch.drop_constraint("ck_question_set_key_counts", type_="check")
        batch.drop_constraint("ck_question_set_key_reliability", type_="check")
        batch.drop_column("key_measured_at")
        batch.drop_column("key_discrepant_count")
        batch.drop_column("key_checked_count")
        batch.drop_column("key_reliability")
