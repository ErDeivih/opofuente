"""Lectura y escritura de las claves derivadas (§1 del encargo). Cuatro cosas y ninguna mas.

1. **Que conjuntos hay que arreglar**: los que estan en cuarentena (`no_fiable`) y **no** estan
   protegidos. De cada uno viaja su tipo, su procedencia y si su plantilla viene de un documento,
   que es lo que decide el rechazo.
2. **Las dos fuentes**: la letra de los apuntes con su **cita verificada** (el ancla) y el enunciado
   con sus opciones para preguntarle al modelo sin apuntes.
3. **Escribir la clave derivada y su motivo de fuera**, cada uno por su ruta **auditada**: la clave
   con su evento (una por clave, que es lo que el alumno va a estudiar) y el motivo agrupado por
   conjunto (una pregunta sin clave no es un cambio de datos del propietario, es un informe).
4. **La decision de cada conjunto** (`vuelve_a_los_tests` o no) con su cifra, tambien auditada.

Nada de esto escribe en `answer_key_versions`: una clave derivada **no** es la clave del conjunto y
no la sustituye. La tabla donde vive tiene un `CHECK` que solo admite `derived`, asi que guardarla
como `active` no es que este prohibido: es que no cabe.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.derived_keys import (
    ACCION_CLAVE_DERIVADA,
    ACCION_DECISION,
    ACCION_HUECOS,
    ACCION_RECHAZO,
    DecisionDeConjunto,
    Derivacion,
    FuenteDeLosApuntes,
    MotivoDeFuera,
    RecuentoDeFuera,
    recuento_de_fuera,
)
from opofuente.domain.key_reliability import KeyReliability, letras_de_clave, normalizar_letra
from opofuente.domain.topic_classification import ClassifiableQuestion
from opofuente.infrastructure.db_models import (
    AnswerKeyVersionRecord,
    AuditEventRecord,
    DerivedKeyRecord,
    KeyGapRecord,
    OptionVersionRecord,
    QuestionNoteAnchorRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
)

#: La version de la plantilla del encargo con la que se pide la respuesta independiente. Va guardada
#: con cada clave derivada: si el encargo cambia, las claves derivadas con el anterior se reconocen.
PROMPT_VERSION = "clave-derivada-1"


@dataclass(frozen=True, slots=True)
class ConjuntoEnCuarentena:
    """Un conjunto que hay que arreglar, con lo justo para decidir si se puede."""

    set_id: str
    title: str
    set_type: str
    origin_scope: str
    source_document_version_id: str | None
    preguntas: int

    @property
    def tiene_plantilla_enlazada(self) -> bool:
        return self.source_document_version_id is not None


class SqlAlchemyDerivedKeyRepository:
    """Las claves derivadas: quien las lee, quien las escribe y quien las audita."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ lectura

    def sets_in_quarantine(self) -> tuple[ConjuntoEnCuarentena, ...]:
        """Los conjuntos `no_fiable`, con su numero de preguntas.

        El total de preguntas es **el total del conjunto**, no el de sus anclas: el liston del 90 %
        se mide sobre lo que el alumno se juega, y una pregunta sin ancla tambien se juega.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    QuestionSetRecord.id,
                    QuestionSetRecord.title,
                    QuestionSetRecord.set_type,
                    QuestionSetRecord.origin_scope,
                    QuestionSetRecord.source_document_version_id,
                    select(func.count(QuestionVersionRecord.id))
                    .where(QuestionVersionRecord.question_set_id == QuestionSetRecord.id)
                    .scalar_subquery(),
                )
                .where(QuestionSetRecord.key_reliability == KeyReliability.NO_FIABLE.value)
                .order_by(QuestionSetRecord.title)
            ).all()
        return tuple(
            ConjuntoEnCuarentena(
                set_id=str(fila[0]),
                title=str(fila[1]),
                set_type=str(fila[2]),
                origin_scope=str(fila[3]),
                source_document_version_id=fila[4],
                preguntas=int(fila[5]),
            )
            for fila in filas
        )

    def linked_material(self, set_ids: Sequence[str]) -> frozenset[str]:
        """Los conjuntos cuya **plantilla** viene de un documento (el segundo camino de «oficial»).

        Se mira la plantilla y no solo el conjunto: una clave enlazada a un documento salio de un
        papel aunque el conjunto este marcado como banco privado, y ese es justo el caso que la
        proteccion de la clave oficial existe para cubrir.
        """
        if not set_ids:
            return frozenset()
        with self._session_factory() as session:
            filas = session.execute(
                select(AnswerKeyVersionRecord.question_set_id)
                .where(AnswerKeyVersionRecord.question_set_id.in_(list(set_ids)))
                .where(AnswerKeyVersionRecord.source_document_version_id.is_not(None))
                .distinct()
            ).all()
        return frozenset(str(fila[0]) for fila in filas)

    def question_ids_of_sets(self, set_ids: Sequence[str]) -> dict[str, tuple[str, ...]]:
        """Las preguntas de cada conjunto, para poder contarlas y para pedirlas al modelo.

        Se piden **todas** las preguntas del conjunto (no solo las que tienen ancla): el liston del
        90 % se mide sobre lo que el alumno se juega, y una pregunta sin ancla tambien se juega.
        """
        if not set_ids:
            return {}
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionVersionRecord.question_set_id, QuestionVersionRecord.id)
                .where(QuestionVersionRecord.question_set_id.in_(list(set_ids)))
                .order_by(QuestionVersionRecord.question_set_id, QuestionVersionRecord.position)
            ).all()
        por_conjunto: dict[str, list[str]] = {}
        for set_id, pregunta_id in filas:
            por_conjunto.setdefault(str(set_id), []).append(str(pregunta_id))
        return {set_id: tuple(ids) for set_id, ids in por_conjunto.items()}

    def notes_sources(self, question_ids: Sequence[str]) -> dict[str, FuenteDeLosApuntes]:
        """La primera fuente de cada pregunta: la letra que dan los apuntes y **su cita**.

        Se devuelven **tambien las anclas sin cita** y no solo las que la tienen: la diferencia
        entre «los apuntes no han mirado esta pregunta» (`sin_material`) y «la miraron y no
        sostienen la letra» (`sin_cita`) es el motivo que va al informe y a la bandeja, y sin las
        anclas sin cita las dos cosas se verian igual.

        Una pregunta puede tener ancla en mas de un tema. Se elige **una**, y el orden se dice aqui
        en vez de depender del que devuelva la base: primero las que tienen cita, despues las
        comprobadas contra la clave **activa** (es la que puede corroborar la clave del conjunto) y,
        entre iguales, la comprobada mas recientemente.
        """
        if not question_ids:
            return {}
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    QuestionNoteAnchorRecord.question_version_id,
                    QuestionNoteAnchorRecord.id,
                    QuestionNoteAnchorRecord.answer_letter,
                    QuestionNoteAnchorRecord.quoted_sentence,
                    QuestionNoteAnchorRecord.key_status,
                )
                .where(QuestionNoteAnchorRecord.question_version_id.in_(list(question_ids)))
                .order_by(
                    QuestionNoteAnchorRecord.question_version_id,
                    QuestionNoteAnchorRecord.quoted_sentence.is_(None),
                    (QuestionNoteAnchorRecord.key_status != "active"),
                    QuestionNoteAnchorRecord.checked_at.desc(),
                )
            ).all()
        fuentes: dict[str, FuenteDeLosApuntes] = {}
        for pregunta_id, ancla_id, letra, cita, key_status in filas:
            fuentes.setdefault(
                str(pregunta_id),
                FuenteDeLosApuntes(
                    question_version_id=str(pregunta_id),
                    anchor_id=str(ancla_id),
                    letra=str(letra or ""),
                    cita=str(cita or ""),
                    key_status=str(key_status),
                ),
            )
        return fuentes

    def has_any_anchor(self, question_ids: Sequence[str]) -> frozenset[str]:
        """Las preguntas con **algun** ancla, tenga cita o no. Separa «sin material» de «sin cita».

        Una pregunta sin ninguna ancla es una pregunta que los apuntes **no han mirado** (su tema no
        esta escrito, o el reparto no la situo): no hay material. Una con ancla y sin cita es una
        pregunta que los apuntes miraron y **no sostenian**: hay material, falta la cita.
        """
        if not question_ids:
            return frozenset()
        with self._session_factory() as session:
            filas = session.execute(
                select(QuestionNoteAnchorRecord.question_version_id)
                .where(QuestionNoteAnchorRecord.question_version_id.in_(list(question_ids)))
                .distinct()
            ).all()
        return frozenset(str(fila[0]) for fila in filas)

    def corroborated(self, question_ids: Sequence[str]) -> frozenset[str]:
        """Las preguntas cuya letra de los apuntes **confirma la clave activa** del conjunto.

        Es el otro lado del liston: la letra de los apuntes, con su cita verificada, **coincide**
        con la de la plantilla activa. Esa clave tiene un apoyo independiente del material del
        que salio, y por eso cuenta como `active` en la cuenta del 90 %. Solo valen las anclas
        comprobadas contra la clave **activa** (`key_status = 'active'`): una comprobada contra un
        borrador no dice nada de la clave que corrige hoy.
        """
        if not question_ids:
            return frozenset()
        confirmadas: set[str] = set()
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    QuestionNoteAnchorRecord.question_version_id,
                    QuestionNoteAnchorRecord.answer_letter,
                    QuestionNoteAnchorRecord.expected_letters,
                )
                .where(QuestionNoteAnchorRecord.question_version_id.in_(list(question_ids)))
                .where(QuestionNoteAnchorRecord.key_status == "active")
                .where(QuestionNoteAnchorRecord.quoted_sentence.is_not(None))
                .where(QuestionNoteAnchorRecord.quoted_sentence != "")
            ).all()
        for pregunta_id, letra, esperadas in filas:
            propia = normalizar_letra(letra)
            if propia and propia in {normalizar_letra(x) for x in letras_de_clave(esperadas)}:
                confirmadas.add(str(pregunta_id))
        return frozenset(confirmadas)

    def gaps_of(self, set_ids: Sequence[str]) -> dict[str, MotivoDeFuera]:
        """El motivo de fuera **ya escrito**, por pregunta, de los conjuntos que se pidan.

        Es la decision que tomo la corrida, y por eso manda sobre cualquier recuento que se pueda
        volver a calcular: el informe tiene que decir lo que hay, no lo que se deduciria.
        """
        if not set_ids:
            return {}
        with self._session_factory() as session:
            filas = session.execute(
                select(KeyGapRecord.question_version_id, KeyGapRecord.reason).where(
                    KeyGapRecord.question_set_id.in_(list(set_ids))
                )
            ).all()
        return {str(pregunta_id): MotivoDeFuera(str(motivo)) for pregunta_id, motivo in filas}

    def derived_questions(self, set_ids: Sequence[str]) -> dict[str, tuple[str, ...]]:
        """Las preguntas que **ya** tienen clave derivada, por conjunto.

        Lo leen la prevision (para no preguntar dos veces por lo mismo), la cuenta del 90 % y el
        informe. Se leen de la base y no de lo que se acaba de calcular: la decision de un conjunto
        tiene que poder tomarse en otra sesion, sin haber corrido nada delante.
        """
        if not set_ids:
            return {}
        with self._session_factory() as session:
            filas = session.execute(
                select(DerivedKeyRecord.question_set_id, DerivedKeyRecord.question_version_id)
                .where(DerivedKeyRecord.question_set_id.in_(list(set_ids)))
                .order_by(DerivedKeyRecord.question_set_id, DerivedKeyRecord.question_version_id)
            ).all()
        por_conjunto: dict[str, list[str]] = {}
        for set_id, pregunta_id in filas:
            por_conjunto.setdefault(str(set_id), []).append(str(pregunta_id))
        return {set_id: tuple(ids) for set_id, ids in por_conjunto.items()}

    def questions_for_model(self, question_ids: Sequence[str]) -> tuple[ClassifiableQuestion, ...]:
        """El enunciado y las opciones de cada pregunta: lo unico que ve el modelo sin apuntes."""
        if not question_ids:
            return ()
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    QuestionVersionRecord.id,
                    QuestionVersionRecord.stem,
                    OptionVersionRecord.stable_key,
                    OptionVersionRecord.text,
                )
                .join(
                    OptionVersionRecord,
                    OptionVersionRecord.question_version_id == QuestionVersionRecord.id,
                )
                .where(QuestionVersionRecord.id.in_(list(question_ids)))
                .order_by(QuestionVersionRecord.id, OptionVersionRecord.position)
            ).all()
        acumulado: dict[str, list[tuple[str, str]]] = {}
        enunciados: dict[str, str] = {}
        for pregunta_id, enunciado, clave, texto in filas:
            enunciados[str(pregunta_id)] = str(enunciado)
            acumulado.setdefault(str(pregunta_id), []).append((str(clave), str(texto)))
        return tuple(
            ClassifiableQuestion(
                question_version_id=pregunta_id,
                stem=enunciados[pregunta_id],
                options=tuple(opciones),
            )
            for pregunta_id, opciones in acumulado.items()
        )

    # ------------------------------------------------------------------ escritura

    def save_derivations(
        self,
        derivaciones: Sequence[Derivacion],
        *,
        set_id: str,
        now: datetime,
        actor: str,
        model_name: str,
        model_version: str,
    ) -> int:
        """Guarda las claves derivadas de un conjunto, **cada una con su evento de auditoria**.

        Idempotente por pregunta: si la clave derivada ya esta con la misma letra, no se toca (ni se
        reescribe la fecha ni se llena la auditoria de ruido). Y si la pregunta tenia un motivo de
        fuera, se le quita: las dos cosas no pueden ser verdad a la vez.
        """
        if not derivaciones:
            return 0
        escritas = 0
        with self._session_factory() as session:
            for derivacion in derivaciones:
                letra = derivacion.letra
                anterior = session.get(DerivedKeyRecord, derivacion.question_version_id)
                if anterior is not None and str(anterior.correct_option_keys_json) == _json(
                    [letra]
                ):
                    continue
                session.merge(
                    DerivedKeyRecord(
                        question_version_id=derivacion.question_version_id,
                        question_set_id=set_id,
                        correct_option_keys_json=_json([letra]),
                        key_state="derived",
                        notes_letter=derivacion.apuntes.letra,
                        notes_quote=derivacion.apuntes.cita,
                        notes_anchor_id=derivacion.apuntes.anchor_id,
                        notes_key_status=derivacion.apuntes.key_status,
                        model_letter=derivacion.modelo.letra or "",
                        model_name=model_name,
                        model_version=model_version,
                        prompt_version=PROMPT_VERSION,
                        actor=actor,
                        created_at=now,
                    )
                )
                hueco = session.get(KeyGapRecord, derivacion.question_version_id)
                if hueco is not None:
                    session.delete(hueco)
                session.add(
                    AuditEventRecord(
                        id=str(uuid.uuid4()),
                        actor=actor,
                        action=ACCION_CLAVE_DERIVADA,
                        object_type="question_version",
                        object_id=derivacion.question_version_id,
                        before_json=json.dumps({"key_state": "ninguna"}, ensure_ascii=False),
                        after_json=json.dumps(
                            {
                                "key_state": "derived",
                                "letra": letra,
                                "set_id": set_id,
                                "notes_letter": derivacion.apuntes.letra,
                                "notes_quote": derivacion.apuntes.cita,
                                "model_letter": derivacion.modelo.letra,
                                "prompt_version": PROMPT_VERSION,
                            },
                            ensure_ascii=False,
                        ),
                        correlation_id=None,
                        created_at=now,
                    )
                )
                escritas += 1
            session.commit()
        return escritas

    def save_gaps(
        self,
        motivos: Mapping[str, MotivoDeFuera],
        *,
        set_id: str,
        now: datetime,
        actor: str,
    ) -> int:
        """Guarda **por que** cada pregunta de un conjunto procesado sigue fuera.

        Una fila por pregunta y **un solo evento por conjunto**, con el recuento por motivo: la
        bandeja del propietario se lee por conjunto (asi lo pide el §2), y mil eventos de «esta
        pregunta sigue fuera» taparian los que si son cambios de datos (las claves derivadas).

        Se **reescribe** el motivo de las preguntas del conjunto que la corrida ha mirado: si una
        pregunta ya no esta fuera, su fila se va. Lo que no se toca es lo que no se ha mirado.
        """
        with self._session_factory() as session:
            previos = {
                str(fila[0]): str(fila[1])
                for fila in session.execute(
                    select(KeyGapRecord.question_version_id, KeyGapRecord.reason).where(
                        KeyGapRecord.question_set_id == set_id
                    )
                ).all()
            }
            escritos = 0
            for pregunta_id, motivo in motivos.items():
                if previos.get(pregunta_id) == motivo.value:
                    continue
                session.merge(
                    KeyGapRecord(
                        question_version_id=pregunta_id,
                        question_set_id=set_id,
                        reason=motivo.value,
                        actor=actor,
                        created_at=now,
                    )
                )
                escritos += 1
            for pregunta_id in previos:
                if pregunta_id not in motivos:
                    fila = session.get(KeyGapRecord, pregunta_id)
                    if fila is not None:
                        session.delete(fila)
                        escritos += 1
            if not motivos and not previos:
                session.commit()
                return 0
            recuentos = recuento_de_fuera(list(motivos.values()))
            session.add(
                AuditEventRecord(
                    id=str(uuid.uuid4()),
                    actor=actor,
                    action=ACCION_HUECOS,
                    object_type="question_set",
                    object_id=set_id,
                    before_json=json.dumps({"fuera": len(previos)}, ensure_ascii=False),
                    after_json=json.dumps(
                        {
                            "key_state": "ninguna",
                            "fuera": len(motivos),
                            "motivos": {r.motivo.value: r.preguntas for r in recuentos},
                        },
                        ensure_ascii=False,
                    ),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()
            return escritos

    def record_refusal(
        self,
        conjunto: ConjuntoEnCuarentena,
        motivo: str,
        *,
        now: datetime,
        actor: str,
    ) -> bool:
        """Deja escrito que un conjunto oficial **se ha rechazado**, con su motivo.

        Se audita aunque no se escriba ninguna clave: si manana alguien se pregunta por que esas
        preguntas siguen fuera, la respuesta tiene que estar en la auditoria y no en un `if` del
        codigo. Devuelve `False` si ese mismo motivo ya estaba escrito para ese conjunto —un rechazo
        repetido no es un hecho nuevo— y `True` si es la primera vez.
        """
        with self._session_factory() as session:
            previo = session.execute(
                select(AuditEventRecord.after_json)
                .where(AuditEventRecord.action == ACCION_RECHAZO)
                .where(AuditEventRecord.object_id == conjunto.set_id)
                .order_by(AuditEventRecord.created_at.desc())
                .limit(1)
            ).first()
            if previo is not None:
                try:
                    escrito = json.loads(str(previo[0]))
                except ValueError:
                    escrito = {}
                if isinstance(escrito, dict) and escrito.get("motivo") == motivo:
                    return False
            session.add(
                AuditEventRecord(
                    id=str(uuid.uuid4()),
                    actor=actor,
                    action=ACCION_RECHAZO,
                    object_type="question_set",
                    object_id=conjunto.set_id,
                    before_json=json.dumps(
                        {"clave": "extraida", "preguntas": conjunto.preguntas}, ensure_ascii=False
                    ),
                    after_json=json.dumps(
                        {
                            "clave": "extraida",
                            "derivada": False,
                            "title": conjunto.title,
                            "motivo": motivo,
                        },
                        ensure_ascii=False,
                    ),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()
            return True

    def record_decision(
        self,
        decision: DecisionDeConjunto,
        *,
        now: datetime,
        actor: str,
        fuera: Sequence[RecuentoDeFuera] = (),
    ) -> None:
        """Deja escrita la decision del conjunto: vuelve a los tests o no, con su cifra.

        **No cambia el veredicto del conjunto.** Lo que decide si una pregunta entra es su clave: la
        derivada propia, o la del conjunto cuando no esta en cuarentena. Cambiar `key_reliability` a
        `fiable` para «devolver» el conjunto meteria en los tests, por la puerta de atras, las
        preguntas cuyo motivo de fuera sigue escrito —que es justo lo que el encargo prohibe—.
        """
        with self._session_factory() as session:
            session.add(
                AuditEventRecord(
                    id=str(uuid.uuid4()),
                    actor=actor,
                    action=ACCION_DECISION,
                    object_type="question_set",
                    object_id=decision.set_id,
                    before_json=json.dumps({"vuelve_a_los_tests": False}, ensure_ascii=False),
                    after_json=json.dumps(
                        {
                            "vuelve_a_los_tests": decision.vuelve_a_los_tests,
                            "title": decision.set_title,
                            "preguntas": decision.preguntas,
                            "con_clave": decision.con_clave,
                            "derivadas": decision.derivadas,
                            "corroboradas": decision.corroboradas,
                            "proporcion": round(decision.proporcion, 4),
                            "fuera": {r.motivo.value: r.preguntas for r in fuera},
                            "motivo": decision.motivo(),
                        },
                        ensure_ascii=False,
                    ),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()


def _json(letras: Sequence[str]) -> str:
    return json.dumps(list(letras), ensure_ascii=False)


__all__ = ["PROMPT_VERSION", "ConjuntoEnCuarentena", "SqlAlchemyDerivedKeyRepository"]
