"""Lo que la aplicación hace **sola** cuando una versión de documento se acepta.

Decisión de S12.5 (ADR-017): el propietario pidió que él solo deje su material y que la aplicación
lo deje listo para estudiar. Eso choca con dos actos que una decisión anterior reserva a una persona
—**aceptar una versión** (ADR-009: activar es aprobar) y **otorgar autoridad o derechos** (04 §8)—,
así que aquí se automatiza todo lo que va **después** de ese acto y no se automatiza el acto.

Lo que hace, en orden, y sin preguntar nada:

1. mira la **clasificación vigente** del material (lo aceptado o lo aplicado provisionalmente por el
   motor determinista) y se queda con el tipo documental;
2. si el tipo no es de los que traen preguntas —examen oficial, banco privado o supuestos—, no hace
   nada y lo dice con su motivo;
3. busca la **oposición** por el programa al que está asignada la versión: sin asignación no hay
   conjunto que crear, y tampoco se adivina;
4. crea el conjunto (o reutiliza el que ya salió de esa misma versión) y **importa las preguntas con
   su cita**, que es lo que ya sabía hacer el importador de S06;
5. si el material no traía ninguna pregunta reconocible, deja el conjunto archivado y lo dice: un
   conjunto vacío es basura en la lista del banco.

Lo que **no** hace: aceptar la versión, promover el material a la biblioteca, ni tocar autoridad o
derechos. Esas siguen siendo decisiones de una persona, y la aplicación lo dice en lugar de
suponerlas.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from opofuente.application.classification_service import ClassificationService
from opofuente.application.library_service import LibraryService
from opofuente.application.ports import Clock
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.question_models import QuestionSetView
from opofuente.application.question_service import QuestionService
from opofuente.domain.classification import DocumentType
from opofuente.domain.errors import NotFoundError
from opofuente.domain.questions import (
    ParsedKeyLine,
    key_alignment,
    parse_answer_key,
    parse_key_model,
)
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository

#: Tipos documentales que **traen preguntas**. Un temario, unos apuntes o una ley no: de ahí no se
#: importa nada, porque no hay nada que importar.
QUESTION_DOCUMENT_TYPES: frozenset[str] = frozenset(
    {
        DocumentType.OFFICIAL_EXAM.value,
        DocumentType.PRIVATE_QUESTION_BANK.value,
        DocumentType.PRACTICAL_CASE.value,
    }
)

#: Tipos documentales que **son** una plantilla de respuestas: no traen preguntas, traen la clave de
#: un examen que ya está en el banco. Lo que se hace con ellas es **enlazarlas** (S12.6).
KEY_DOCUMENT_TYPES: frozenset[str] = frozenset({DocumentType.ANSWER_KEY.value})

#: Proporción mínima de líneas de la plantilla que tienen que caer en una pregunta del examen para
#: dar el enlace por bueno. Casi todas: una plantilla de verdad cubre el examen entero, así que si
#: hay líneas que no encuentran pregunta, lo que no encaja es el examen.
KEY_ALIGNMENT_MINIMUM = 0.95

#: Conjuntos con los que se puede enlazar una plantilla: un examen oficial, que es lo que tiene
#: plantilla. Un banco privado se corrige con la clave que trae su propio material.
KEY_SET_TYPES: frozenset[str] = frozenset({"official_exam"})

#: Título del conjunto que se crea solo. Lleva el título del documento para que se sepa de dónde
#: salió sin abrirlo, y para que dos documentos distintos no compartan conjunto.
SET_TITLE_TEMPLATE = "Preguntas de «{title}»"


@dataclass(frozen=True, slots=True)
class AutoImportOutcome:
    """Qué ha hecho la aplicación sola con una versión aceptada."""

    imported: int = 0
    set_id: str | None = None
    note: str | None = None
    #: Preguntas catalogadas por bloque y tema al heredar el programa del documento (S12.6).
    catalogued: int = 0

    @property
    def did_something(self) -> bool:
        return self.imported > 0


class AutoStudyService:
    """Importa solo lo que el material trae y la clasificación ya dice qué es."""

    def __init__(
        self,
        *,
        questions: QuestionService,
        classifications: ClassificationService,
        library: LibraryService,
        profiles: ProfilesService,
        documents: SqlAlchemyDocumentRepository,
        clock: Clock,
    ) -> None:
        self._questions = questions
        self._classifications = classifications
        self._library = library
        self._profiles = profiles
        self._documents = documents
        self._clock = clock

    def after_version_accepted(self, version_id: str) -> AutoImportOutcome:
        """Lo que se hace solo cuando una versión queda aceptada; no lanza si no puede ayudar."""
        detalle = self._documents.version_detail(version_id)
        if detalle is None:
            return AutoImportOutcome(note="no se encontró la versión aceptada")

        tipo = self._document_type(detalle.version.artifact_id)
        if tipo is None:
            return AutoImportOutcome(
                note="el material no está clasificado: no se sabe si trae preguntas"
            )
        if tipo in KEY_DOCUMENT_TYPES:
            # Una plantilla no trae preguntas: trae las respuestas de un examen que ya está en el
            # banco. Enlazarla es todo lo que se puede hacer sin equivocarse (S12.6).
            return self._link_answer_key(version_id=version_id)
        if tipo not in QUESTION_DOCUMENT_TYPES:
            return AutoImportOutcome(note=f"el material está clasificado como «{tipo}»")

        oposicion = self._opposition_of(version_id)
        if oposicion is None:
            return AutoImportOutcome(
                note="la versión no está asignada a ninguna oposición: no hay conjunto que crear"
            )
        opposition_id, convocation_id = oposicion

        existente = self._existing_set(
            version_id=version_id, document_id=detalle.document_id, opposition_id=opposition_id
        )
        if existente is not None:
            informe = self._questions.import_from_document(existente.id, version_id)
            catalogadas = self.catalogue_questions(set_id=existente.id, version_id=version_id)
            return AutoImportOutcome(
                imported=informe.created,
                set_id=existente.id,
                note=(
                    "las preguntas ya estaban importadas"
                    if informe.created == 0
                    else "se añadieron las preguntas que traía la versión nueva"
                ),
            )

        conjunto = self._questions.create_set(
            SET_TITLE_TEMPLATE.format(title=detalle.document_title),
            opposition_id=opposition_id,
            set_type=(
                "official_exam" if tipo == DocumentType.OFFICIAL_EXAM.value else "private_bank"
            ),
            convocation_version_id=convocation_id,
            source_document_version_id=version_id,
            actor="auto",
        )
        informe = self._questions.import_from_document(conjunto.id, version_id)
        if informe.created == 0:
            # Un conjunto vacío no se queda en la lista: se archiva y se dice por qué.
            self._questions.archive_set(
                conjunto.id, reason="el material no traía preguntas reconocibles"
            )
            return AutoImportOutcome(note="el material no traía preguntas reconocibles")
        catalogadas = self.catalogue_questions(set_id=conjunto.id, version_id=version_id)
        return AutoImportOutcome(
            imported=informe.created,
            set_id=conjunto.id,
            note=f"importadas {informe.created} preguntas de este documento",
            catalogued=catalogadas,
        )

    # ------------------------------------------------------------------ plantilla de respuestas

    def _link_answer_key(self, *, version_id: str) -> AutoImportOutcome:
        """Enlaza una plantilla de respuestas con **el** examen al que pertenece, o dice por qué no.

        La regla es conservadora a propósito (S12.6): enlazar la plantilla de un modelo con el
        examen de otro corrige el examen entero con las respuestas equivocadas, y eso no se nota
        hasta que el propietario estudia con ello. Por eso solo se enlaza si **no hay duda**:

        1. el examen tiene que ser de la misma oposición, y la versión tiene que estar asignada a su
           programa (sin asignación no se sabe de quién es la plantilla);
        2. si la plantilla declara el modelo —«Modelo A»—, el examen tiene que ser de ese modelo;
        3. la plantilla tiene que **encajar**: casi todas sus líneas (95 %) caen en una pregunta del
           examen;
        4. tiene que encajar con **un solo** examen. Con dos candidatos no se elige por nadie: se
           dice y se para.

        Lo que **no** hace: activar la plantilla. Activar es aprobar (ADR-009) y eso lo decide una
        persona; aquí se deja enlazada, en borrador, y se dice qué falta.
        """
        oposicion = self._opposition_of(version_id)
        if oposicion is None:
            return AutoImportOutcome(
                note=(
                    "la plantilla no está asignada a ninguna oposición: no se sabe de qué examen es"
                )
            )
        opposition_id, _convocation_id = oposicion

        texto = self._texto(version_id)
        if texto is None:
            return AutoImportOutcome(note="la plantilla no tiene texto extraído que se pueda leer")
        lineas, _incidencias = parse_answer_key(texto)
        if not lineas:
            return AutoImportOutcome(
                note="la plantilla no tiene ninguna respuesta reconocible: no se enlaza nada"
            )

        modelo = parse_key_model(texto)
        candidatos = [
            conjunto
            for conjunto in self._questions.sets(opposition_id=opposition_id, limit=200).sets
            if conjunto.set_type in KEY_SET_TYPES
            and (modelo is None or conjunto.model_code == modelo)
        ]
        if not candidatos:
            del_modelo = f" del modelo {modelo}" if modelo is not None else ""
            return AutoImportOutcome(
                note=(
                    "no hay ningún examen oficial"
                    f"{del_modelo} de esta oposición con el que enlazar la plantilla"
                )
            )

        puntuaciones = [
            (self._alineacion(conjunto.id, lineas), conjunto) for conjunto in candidatos
        ]
        buenos = [
            (alineacion, conjunto)
            for alineacion, conjunto in puntuaciones
            if alineacion >= KEY_ALIGNMENT_MINIMUM
        ]
        if not buenos:
            mejor = max(puntuaciones, key=lambda par: par[0])
            return AutoImportOutcome(
                note=(
                    "la plantilla no encaja con ningún examen de esta oposición: la que más se "
                    f"parece es «{mejor[1].title}» y solo coincide en el "
                    f"{round(mejor[0] * 100)} % de sus líneas"
                )
            )
        if len(buenos) > 1:
            titulos = ", ".join(f"«{conjunto.title}»" for _alineacion, conjunto in buenos[:3])
            return AutoImportOutcome(
                note=(
                    f"la plantilla encaja con {len(buenos)} exámenes ({titulos}): "
                    "no se elige por ti, dime cuál es y se enlaza"
                )
            )

        _alineacion, examen = buenos[0]
        informe = self._questions.import_key_from_text(
            examen.id,
            texto,
            source_document_version_id=version_id,
            actor="auto",
        )
        if informe.key_id is None:
            return AutoImportOutcome(
                note="la plantilla encaja con el examen, pero no se pudo guardar ninguna respuesta"
            )
        return AutoImportOutcome(
            set_id=examen.id,
            note=(
                f"plantilla enlazada con el examen «{examen.title}»: {informe.entries} respuestas "
                "(queda en borrador; actívala en Preguntas para corregir con ella)"
            ),
        )

    def _texto(self, version_id: str) -> str | None:
        """Texto extraído de la versión, o `None` si no hay nada que leer."""
        vista = self._library.version_text(version_id)
        if vista is None or not vista.text.strip():
            return None
        return vista.text

    def _alineacion(self, set_id: str, lineas: Sequence[ParsedKeyLine]) -> float:
        """Cómo encaja la plantilla con el conjunto por **número de pregunta** (`key_alignment`).

        Una línea solo cuenta si su número es el de una sola pregunta, y la plantilla tiene que
        cubrir el conjunto, no solo caer en él. Antes se miraba solo si cada línea encontraba alguna
        pregunta, y solo entre las 200 primeras: una plantilla de 93 líneas daba «100 %» con un
        conjunto de 135 preguntas que reiniciaba la numeración en cada sección.
        """
        _destinos, en_orden = self._questions.key_line_targets(set_id, lineas)
        if en_orden:
            # Encaja uno a uno en el orden del examen (numeración reiniciada por secciones).
            return 1.0
        return key_alignment(lineas, self._questions.question_ids_by_position(set_id)).score

    def catalogue_questions(self, *, set_id: str, version_id: str) -> int:
        """Cataloga por bloque y tema las preguntas que aún no tienen tema (S12.6).

        El tema no se adivina: se **hereda** de la asignación aceptada del documento del que salen
        las preguntas. Si el documento está asignado al «Tema 3» del programa, sus preguntas son del
        tema 3; si no está asignado a nada, no se cataloga ninguna y no se inventa un tema.

        Solo se tocan las preguntas **sin** tema: una que ya lo tiene (puesto a mano o traído de una
        columna del material) se respeta, porque pisarla sería cambiar una decisión en silencio.
        """
        nodos = [
            mapeo.node_id
            for mapeo in self._library.mappings_of(version_id)
            if mapeo.status == "accepted"
        ]
        if not nodos:
            return 0
        catalogadas = 0
        for pregunta_id in self._questions.questions_without_topic(set_id, limit=500):
            for node_id in nodos:
                if self._questions.map_question_to_node(pregunta_id, node_id=node_id) is not None:
                    catalogadas += 1
        return catalogadas

    def _document_type(self, artifact_id: str) -> str | None:
        """Tipo documental vigente del material: lo aceptado manda sobre lo aplicado provisional."""
        vigente = self._classifications.accepted_classification(
            subject_type="artifact", subject_id=artifact_id
        )
        for valor in vigente.values:
            if valor.axis == "document_type":
                return valor.value
        # El motor clasifica también la representación (el texto); si el artefacto no tiene nada,
        # se mira por ahí antes de darse por vencido.
        return None

    def _opposition_of(self, version_id: str) -> tuple[str, str | None] | None:
        """Oposición y convocatoria de la versión, por el programa al que está asignada.

        Se usa la asignación **aceptada**: una propuesta sin aceptar es una sugerencia, y crear un
        conjunto a partir de una sugerencia sería inventar de qué oposición son las preguntas.
        """
        for mapeo in self._library.mappings_of(version_id):
            if mapeo.status != "accepted":
                continue
            try:
                nodo = self._profiles.get_node(mapeo.node_id)
            except NotFoundError:
                # Una asignación que apunta a un nodo que ya no está no puede tumbar la importación
                # automática: se salta y se sigue con las demás.
                continue
            for oposicion in self._profiles.list_oppositions():
                if oposicion.code == nodo.opposition_code:
                    return oposicion.id, nodo.convocation_id
        return None

    def _existing_set(
        self, *, version_id: str, document_id: str, opposition_id: str
    ) -> QuestionSetView | None:
        """Conjunto que ya salió de este mismo documento: uno por documento, no uno por versión.

        La clave es el **documento**, no la versión: cuando llega una versión nueva del mismo banco
        de preguntas (una revisión, una errata corregida), sus preguntas nuevas se añaden al
        conjunto que ya existe en vez de crear otro. Lo que ya estaba se reconoce por su huella
        y no se duplica.
        """
        pagina = self._questions.sets(opposition_id=opposition_id, limit=200)
        for conjunto in pagina.sets:
            if conjunto.source_document_version_id is None:
                continue
            if conjunto.source_document_version_id == version_id:
                return conjunto
            origen = self._documents.version_detail(conjunto.source_document_version_id)
            if origen is not None and origen.document_id == document_id:
                return conjunto
        return None
