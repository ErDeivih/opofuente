"""La bandeja agrupada por conjunto: dos estados que resuelve una regla, no una persona (F31).

Revision ID: 0039_bandeja_por_conjunto
Revises: 0039_claves_derivadas
Create Date: 2026-10-15

**Va detrás de `0039_claves_derivadas`, y ese orden es el correcto aunque las dos se llamen 0039.**
Las dos ramas nacieron del mismo `main` y las dos colgaron de `0038_revision_de_apuntes`: dos
migraciones con el mismo padre son **dos cabezas**, y alembic se niega a subir. Al fusionar, la del
§1 entró primero, y esta **se re-apunta a ella**. El identificador de revisión es la cadena entera
(`0039_bandeja_por_conjunto` ≠ `0039_claves_derivadas`), así que los dos números conviven; lo que no
puede convivir es el padre repetido.

Y no es un detalle de fontanería: la bandeja **lee** `question_derived_keys` para proponer en bloque
lo que el §1 ha derivado, así que esta migración va detrás de la suya por la misma razón por la que
el aviso va detrás de la comprobación.

La bandeja nació (`0031`) como un resto que la corrida de apuntes contaba al terminar, y `0035` la
hizo **despachable**: cuatro estados —los mismos que la bandeja del alumno— y la nota de lo que se
había hecho. Estaba bien para el trabajo que tenía entonces: **una persona mira una incidencia y
decide**. El §2 del cierre del objetivo pide otra cosa, y la medición del 15 de octubre de 2026 lo
confirma: **868 incidencias abiertas en 150 conjuntos**, de las cuales dos tercios no son
defectos de una pregunta sino de la clave de su conjunto.

Eso deja dos clases de fila que el vocabulario viejo **no puede escribir**:

1. **`propuesta_lista`**: la regla del §1 ya resolvió la incidencia —la letra que dicen los apuntes
   con cita y una respuesta independiente del modelo coinciden— y solo falta que el propietario la
   apruebe **en bloque**. No es `open` (no hay nada que averiguar) ni `reviewed` (nadie la ha
   aprobado): si se guardara como `open`, la fila se contaría entre las que esperan criterio y la
   cifra de la medida de éxito mentiría; si se guardara como `reviewed`, el comando de resolución
   estaría firmando una decisión que no es suya.
2. **`no_son_preguntas`**: una pregunta mal importada, decidida por las reglas **mecánicas** del
   §2 —sin modelo y sin red—: le faltan opciones, o dos quedaron fundidas. Sale de la bandeja a «No
   son preguntas» y ahí se queda, mirándose.

Sobre `reviewed_at`: la columna dice **cuándo dejó de esperar** una incidencia, y `no_son_preguntas`
deja de esperar cuando la escribe la regla. Por eso el dominio la cuenta entre las cerradas. El
**quién** no vive aquí, vive en `audit_events`, que es donde esta aplicación guarda lo que el dato
pierde.

La vuelta atrás **no borra ninguna fila**: recoloca los dos estados nuevos en los que ya
existían
(`propuesta_lista` vuelve a `open`, que es lo que era antes de que existiera la propuesta;
`no_son_preguntas` vuelve a `dismissed`, que es la salida que significa «no se toca nada más»). Sin
eso, la recreación de la tabla fallaría a mitad con las filas dentro.
"""

from __future__ import annotations

from alembic import op

revision = "0039_bandeja_por_conjunto"
down_revision = "0039_claves_derivadas"
branch_labels = None
depends_on = None

#: El vocabulario del estado, con los dos que añade la resolución automática (F31).
_ESTADOS_NUEVOS = (
    "status IN ('open', 'in_progress', 'reviewed', 'dismissed', 'propuesta_lista', "
    "'no_son_preguntas')"
)

#: El de `0035`, que es al que se vuelve.
_ESTADOS_VIEJOS = "status IN ('open', 'in_progress', 'reviewed', 'dismissed')"


def upgrade() -> None:
    with op.batch_alter_table("notes_incidents") as batch:
        batch.drop_constraint("ck_notes_incident_status", type_="check")
        batch.create_check_constraint("ck_notes_incident_status", _ESTADOS_NUEVOS)
    # El índice que pide la bandeja agrupada: «las propuestas de este conjunto» y «lo que espera de
    # este conjunto» son las dos consultas que hace la pantalla al desplegar una fila.
    op.create_index(
        "ix_notes_incidents_status_set",
        "notes_incidents",
        ["status", "question_version_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_notes_incidents_status_set", table_name="notes_incidents")
    # Los dos estados nuevos vuelven a uno viejo antes de recrear el `CHECK`: una propuesta sin
    # aprobar es lo que era —algo pendiente— y lo que se fue a «No son preguntas» es algo que ya no
    # se toca.
    op.execute("UPDATE notes_incidents SET status = 'open' WHERE status = 'propuesta_lista'")
    op.execute("UPDATE notes_incidents SET status = 'dismissed' WHERE status = 'no_son_preguntas'")
    with op.batch_alter_table("notes_incidents") as batch:
        batch.drop_constraint("ck_notes_incident_status", type_="check")
        batch.create_check_constraint("ck_notes_incident_status", _ESTADOS_VIEJOS)
