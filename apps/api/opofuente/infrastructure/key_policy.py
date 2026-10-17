"""La política de claves, escrita una sola vez.

**Qué decide.** Si una pregunta se puede **corregir**: es decir, si al contestarla hay una letra con
la que decir «bien» o «mal». No es una regla de estilo: una pregunta sin clave se puede enseñar,
pero contestarla no cuenta, y ofrecerla en un test o prometerla en un contador es prometer algo que
la corrección no puede dar.

**Por qué está en un fichero y no en cada sitio que elige preguntas.** El motor elige preguntas en
cuatro sitios —los tests de práctica por conjuntos, la práctica por tema, el examen oficial con sus
simulacros y el repaso de fallos— y además hay contadores que dicen cuántas hay. Hasta F39 cada uno
tenía su versión: el repaso exigía plantilla `active` y los tests de práctica aceptaban también las
claves derivadas. Con eso, Inicio prometía «5 preguntas para repasar hoy» y el repaso contestaba
409: dos pantallas del mismo producto con dos políticas. Ahora la regla es esta, y es la única:

1. **la clave derivada manda** (`0039`, §1 de F29): una letra con dos apoyos independientes —los
   apuntes con su cita verificada y el modelo preguntado sin apuntes— corrige la pregunta tenga o no
   plantilla activa su conjunto, y esté o no en cuarentena;
2. si no hay derivada, el conjunto **no puede estar en cuarentena** (`key_reliability =
   'no_fiable'`) ni la pregunta tener **motivo de fuera** escrito (`0039`): su letra no es de fiar y
   el alumno aprendería la respuesta equivocada;
3. y su **plantilla activa tiene que decir la letra**: una plantilla que no tiene entrada para esa
   pregunta, que la anula o que se contradice no corrige nada.

Lo que no se puede practicar no se puede repasar, y lo que no se puede repasar no se cuenta. Esa es
toda la regla.

**Cómo se usa.** `clave_servible` es la misma condición en SQL, para las consultas que cuentan
(`due_counts`, el contador de «para repasar hoy», y la lista de fallos); el motor, que trabaja con
vistas y no con filas, la aplica con `QuestionRepository.servable_question_ids`. Las dos tienen que
dar lo mismo, y hay una prueba que lo comprueba pregunta a pregunta.

**Por qué las tablas de dentro van con alias.** Una subconsulta correlacionada que vuelve a nombrar
`question_versions` se «autocorrelaciona» con la de fuera y pierde su propio `FROM`: la condición se
convierte en «¿hay *algún* conjunto en cuarentena en toda la base?» y la respuesta deja de depender
de la pregunta. Con un alias propio no hay nada con lo que confundirse.
"""

from __future__ import annotations

from sqlalchemy import ColumnElement, and_, exists, not_, or_, select
from sqlalchemy.orm import InstrumentedAttribute, aliased

from opofuente.domain.key_reliability import KeyReliability
from opofuente.domain.questions import KeyOutcome
from opofuente.infrastructure.db_models import (
    AnswerKeyEntryRecord,
    AnswerKeyVersionRecord,
    DerivedKeyRecord,
    KeyGapRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
)


def clave_servible(
    pregunta: ColumnElement[str] | InstrumentedAttribute[str],
) -> ColumnElement[bool]:
    """¿Se puede corregir esta pregunta? La política de claves, para una consulta.

    `pregunta` es la columna que lleva el identificador de la **versión de pregunta**: casi siempre
    `question_versions.id`, y en el contador de repaso `review_items.question_version_id`. Todo lo
    demás se resuelve con subconsultas correlacionadas, para que la condición se pueda meter en un
    `WHERE` sin arrastrar un `JOIN` que cambie el número de filas.
    """
    version = aliased(QuestionVersionRecord)

    derivada = exists(
        select(DerivedKeyRecord.question_version_id).where(
            DerivedKeyRecord.question_version_id == pregunta
        )
    )
    en_cuarentena = exists(
        select(version.id)
        .join(QuestionSetRecord, QuestionSetRecord.id == version.question_set_id)
        .where(
            version.id == pregunta,
            QuestionSetRecord.key_reliability == KeyReliability.NO_FIABLE.value,
        )
    )
    con_motivo_de_fuera = exists(
        select(KeyGapRecord.question_version_id).where(KeyGapRecord.question_version_id == pregunta)
    )
    con_letra_en_la_plantilla_activa = exists(
        select(AnswerKeyEntryRecord.question_version_id)
        .join(
            AnswerKeyVersionRecord,
            AnswerKeyVersionRecord.id == AnswerKeyEntryRecord.answer_key_version_id,
        )
        .join(version, version.question_set_id == AnswerKeyVersionRecord.question_set_id)
        .where(
            version.id == pregunta,
            AnswerKeyEntryRecord.question_version_id == pregunta,
            AnswerKeyVersionRecord.status == "active",
            AnswerKeyEntryRecord.outcome == KeyOutcome.KEYED.value,
        )
    )
    return or_(
        derivada,
        and_(
            not_(en_cuarentena),
            not_(con_motivo_de_fuera),
            con_letra_en_la_plantilla_activa,
        ),
    )
