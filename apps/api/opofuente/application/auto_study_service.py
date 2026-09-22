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

from dataclasses import dataclass

from opofuente.application.classification_service import ClassificationService
from opofuente.application.library_service import LibraryService
from opofuente.application.ports import Clock
from opofuente.application.profiles_service import ProfilesService
from opofuente.application.question_models import QuestionSetView
from opofuente.application.question_service import QuestionService
from opofuente.domain.classification import DocumentType
from opofuente.domain.errors import NotFoundError
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

#: Título del conjunto que se crea solo. Lleva el título del documento para que se sepa de dónde
#: salió sin abrirlo, y para que dos documentos distintos no compartan conjunto.
SET_TITLE_TEMPLATE = "Preguntas de «{title}»"


@dataclass(frozen=True, slots=True)
class AutoImportOutcome:
    """Qué ha hecho la aplicación sola con una versión aceptada."""

    imported: int = 0
    set_id: str | None = None
    note: str | None = None

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
        return AutoImportOutcome(
            imported=informe.created,
            set_id=conjunto.id,
            note=f"importadas {informe.created} preguntas de este documento",
        )

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
