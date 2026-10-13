"""Lectura de la discrepancia apuntes -> clave y escritura del veredicto de cada conjunto (§1).

Dos cosas y ninguna mas:

1. **Leer** lo que hace falta para medir: una fila por ancla con su conjunto, su letra y su clave.
  La
   cuenta la hace el dominio (`medir_conjuntos`), que se prueba sin base de datos.
2. **Escribir** el veredicto y sus dos numeros en `question_sets`, **diciendo que ha cambiado** en
   `audit_events`. Un conjunto no pasa de `fiable` a `no_fiable` en silencio: eso deja preguntas
   fuera de los tests del alumno, y eso tiene que poder leerse despues.

La puerta es **idempotente**: aplicar la misma medida dos veces no escribe nada la segunda. Se puede
llamar al final de cada tema sin miedo a llenar la auditoria de ruido.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.key_reliability import (
    AnclaMedible,
    Desplazamiento,
    KeyReliability,
    MedidaDeConjunto,
    letras_de_clave,
    medir_conjuntos,
    probar_desplazamientos,
)
from opofuente.infrastructure.db_models import (
    AnswerKeyEntryRecord,
    AnswerKeyVersionRecord,
    AuditEventRecord,
    QuestionNoteAnchorRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
)

#: La accion que se escribe en la auditoria cuando el veredicto de un conjunto cambia.
ACCION = "question_set.key_reliability_changed"


class SqlAlchemyKeyReliabilityRepository:
    """Mide la discrepancia por conjunto y guarda el veredicto."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ lectura

    def anchors(self) -> tuple[AnclaMedible, ...]:
        """Todas las anclas con su conjunto, su letra y su clave.

        Sin filtro por tema a proposito: la discrepancia se mide **por conjunto de origen**, y un
        mismo conjunto puede tener preguntas repartidas entre varios temas. Medirla tema a tema
        partiria el denominador y no se veria el problema (un conjunto de 18 preguntas repartido en
        cinco temas deja de decidir nada).
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    QuestionVersionRecord.question_set_id,
                    QuestionSetRecord.title,
                    QuestionNoteAnchorRecord.question_version_id,
                    QuestionNoteAnchorRecord.answer_letter,
                    QuestionNoteAnchorRecord.expected_letters,
                )
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == QuestionNoteAnchorRecord.question_version_id,
                )
                .join(
                    QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id
                )
            ).all()
        return tuple(
            AnclaMedible(
                set_id=str(fila[0]),
                set_title=str(fila[1] or ""),
                question_version_id=str(fila[2]),
                answer_letter=fila[3],
                expected_letters=fila[4],
            )
            for fila in filas
        )

    def measures(self) -> tuple[MedidaDeConjunto, ...]:
        """La discrepancia por conjunto de origen, medida ahora."""
        return medir_conjuntos(self.anchors())

    def shifts(self) -> tuple[tuple[MedidaDeConjunto, tuple[Desplazamiento, ...]], ...]:
        """La prueba del desplazamiento de **cada** conjunto que no es fiable.

        Devuelve la medida de hoy y las alternativas —la clave una o dos preguntas más allá, y las
        opciones giradas— de los conjuntos `dudosa` o `no_fiable`. Es la comprobación barata del §1:
        si alguna alternativa baja del 10 %, la clave no está mal —está corrida— y volver a
        extraerla del material la arregla.
        """
        with self._session_factory() as session:
            anclas = session.execute(
                select(
                    QuestionVersionRecord.question_set_id,
                    QuestionVersionRecord.position,
                    QuestionNoteAnchorRecord.question_version_id,
                    QuestionNoteAnchorRecord.answer_letter,
                    QuestionNoteAnchorRecord.expected_letters,
                ).join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == QuestionNoteAnchorRecord.question_version_id,
                )
            ).all()
            claves = session.execute(
                select(
                    AnswerKeyVersionRecord.question_set_id,
                    QuestionVersionRecord.position,
                    AnswerKeyEntryRecord.correct_option_keys_json,
                )
                .join(
                    AnswerKeyEntryRecord,
                    AnswerKeyEntryRecord.answer_key_version_id == AnswerKeyVersionRecord.id,
                )
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == AnswerKeyEntryRecord.question_version_id,
                )
                .where(AnswerKeyVersionRecord.status == "active")
            ).all()

        letras_por_conjunto: dict[str, dict[int, str]] = {}
        for set_id, posicion, crudo in claves:
            propias = letras_de_clave(crudo)
            if propias:
                letras_por_conjunto.setdefault(str(set_id), {})[int(posicion)] = propias[0]

        por_conjunto: dict[str, dict[str, tuple[int, AnclaMedible]]] = {}
        for set_id, posicion, pregunta_id, letra, esperadas in anclas:
            ancla = AnclaMedible(
                set_id=str(set_id),
                set_title="",
                question_version_id=str(pregunta_id),
                answer_letter=letra,
                expected_letters=esperadas,
            )
            if not ancla.medible:
                continue
            por_conjunto.setdefault(str(set_id), {})[str(pregunta_id)] = (int(posicion), ancla)

        salida: list[tuple[MedidaDeConjunto, tuple[Desplazamiento, ...]]] = []
        for medida in self.measures():
            suyas = por_conjunto.get(medida.set_id, {})
            if not suyas or medida.veredicto is KeyReliability.FIABLE:
                continue
            pares = [(posicion, ancla.answer_letter or "") for posicion, ancla in suyas.values()]
            salida.append(
                (
                    medida,
                    probar_desplazamientos(
                        pares,
                        letras_por_conjunto.get(medida.set_id, {}),
                        actual=medida,
                    ),
                )
            )
        return tuple(salida)

    def stored(self) -> dict[str, tuple[str, int, int]]:
        """Lo que hay guardado: `set_id -> (veredicto, comprobadas, discrepantes)`."""
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    QuestionSetRecord.id,
                    QuestionSetRecord.key_reliability,
                    QuestionSetRecord.key_checked_count,
                    QuestionSetRecord.key_discrepant_count,
                )
            ).all()
        return {str(fila[0]): (str(fila[1]), int(fila[2]), int(fila[3])) for fila in filas}

    # ------------------------------------------------------------------ escritura

    def apply(
        self,
        medidas: Sequence[MedidaDeConjunto],
        *,
        now: datetime,
        actor: str,
    ) -> tuple[MedidaDeConjunto, ...]:
        """Guarda la medida de cada conjunto y devuelve **los que han cambiado de veredicto**.

        Un conjunto deja de estar medido si ya no tiene anclas: en ese caso su medida desaparece de
                la lista y **no se toca**. Borrar el veredicto de un conjunto porque hoy no se le
          puede medir
        dejaria entrar en los tests, sin avisar, preguntas que ayer estaban en cuarentena.
        """
        cambiados: list[MedidaDeConjunto] = []
        with self._session_factory() as session:
            for medida in medidas:
                fila = session.get(QuestionSetRecord, medida.set_id)
                if fila is None:
                    continue
                anterior = str(fila.key_reliability)
                nuevo = medida.veredicto.value
                # Idempotencia de verdad: si el veredicto y los dos numeros son los mismos, no se
                # toca la fila. Medir cada tema vuelve a pasar por conjuntos que no han cambiado, y
                # escribirles `updated_at` los convertiria en «modificados hoy» sin motivo.
                if (
                    anterior == nuevo
                    and int(fila.key_checked_count) == medida.comprobadas
                    and int(fila.key_discrepant_count) == medida.discrepantes
                ):
                    continue
                fila.key_checked_count = medida.comprobadas
                fila.key_discrepant_count = medida.discrepantes
                fila.key_measured_at = now
                if anterior == nuevo:
                    continue
                fila.key_reliability = nuevo
                fila.updated_at = now
                cambiados.append(medida)
                session.add(
                    AuditEventRecord(
                        id=str(uuid.uuid4()),
                        actor=actor,
                        action=ACCION,
                        object_type="question_set",
                        object_id=medida.set_id,
                        before_json=json.dumps({"key_reliability": anterior}, ensure_ascii=False),
                        after_json=json.dumps(
                            {
                                "key_reliability": nuevo,
                                "key_checked_count": medida.comprobadas,
                                "key_discrepant_count": medida.discrepantes,
                                "title": medida.set_title,
                            },
                            ensure_ascii=False,
                        ),
                        correlation_id=None,
                        created_at=now,
                    )
                )
            session.commit()
        return tuple(cambiados)

    def set_verdict(
        self,
        set_id: str,
        verdict: KeyReliability,
        *,
        now: datetime,
        actor: str,
        reason: str,
    ) -> bool:
        """Fija el veredicto de un conjunto a mano (por ejemplo, al reparar su clave).

        Existe para que **el arreglo de una clave** tenga una via auditada: sin esto, devolver un
        conjunto a `fiable` despues de arreglarlo habria que hacerlo con SQL suelto, que es justo lo
        que el contrato prohibe. Devuelve `False` si el conjunto no existe o si ya estaba asi.
        """
        with self._session_factory() as session:
            fila = session.get(QuestionSetRecord, set_id)
            if fila is None:
                return False
            anterior = str(fila.key_reliability)
            if anterior == verdict.value:
                return False
            fila.key_reliability = verdict.value
            fila.updated_at = now
            session.add(
                AuditEventRecord(
                    id=str(uuid.uuid4()),
                    actor=actor,
                    action=ACCION,
                    object_type="question_set",
                    object_id=set_id,
                    before_json=json.dumps({"key_reliability": anterior}, ensure_ascii=False),
                    after_json=json.dumps(
                        {"key_reliability": verdict.value, "reason": reason}, ensure_ascii=False
                    ),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()
            return True


__all__ = ["ACCION", "SqlAlchemyKeyReliabilityRepository"]
