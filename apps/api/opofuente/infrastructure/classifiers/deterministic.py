"""Motor determinista de clasificación: reglas explícitas, reproducibles y explicables.

No hay modelo estadístico ni llamada a ningún servicio: cada propuesta sale de **señales que se
pueden citar** (una palabra del nombre del fichero, un encabezado del texto, la procedencia del
material) y la confianza es una función documentada de cuántas señales han coincidido. Dos
ejecuciones sobre el mismo material dan exactamente el mismo resultado, y cualquiera puede leer por
qué se propuso lo que se propuso.

Reglas de honestidad, que son las que mandan aquí:

- **sin señales, no hay propuesta**: un eje sin evidencia no genera una propuesta de relleno. Eso es
  «sin clasificar», y así se cuenta en las métricas (§7 del plan de pruebas), no un `unknown`
  inventado;
- **autoridad y derechos son ejes críticos** (`CRITICAL_AXES`): este motor los propone, pero no
  aplican solos;
- **el texto se mira acotado** y nunca se guarda: de él solo salen citas breves como evidencia.

Cómo se calcula la confianza (documentado porque es una decisión, no un detalle):

- cada señal tiene un peso entre 0,4 y 0,7;
- la confianza de un eje es `min(0,9, suma de pesos de las señales que coinciden)`, redondeada a dos
  decimales;
- si dos valores empatan en el eje documental, gana el orden declarado en `DocumentType` (estable);
- en el eje temático, la confianza es `0,3 + 0,5 · (palabras del título presentes / palabras del
  título)` y se exige al menos la mitad de las palabras del título para proponer algo.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from opofuente.domain.classification import (
    Alternative,
    AuthorityTier,
    Axis,
    ClassificationSubject,
    DocumentType,
    ProfileCandidate,
    Proposal,
    RightsStatus,
    SubjectType,
    TopicCandidate,
)

ENGINE_NAME = "determinista"
ENGINE_VERSION = "1"

#: Extracto máximo que se mira del texto. No es un límite de memoria del motor, es una decisión de
#: alcance: un tipo documental o un tema se reconocen en el principio y en los encabezados.
MAX_EXCERPT_CHARS = 20_000

#: Palabras vacías que no cuentan como señal en los títulos del programa.
_STOPWORDS = frozenset(
    {
        "de",
        "del",
        "la",
        "las",
        "el",
        "los",
        "y",
        "o",
        "en",
        "con",
        "sin",
        "para",
        "por",
        "que",
        "sobre",
        "al",
        "a",
        "su",
        "sus",
        "un",
        "una",
        "unos",
        "unas",
    }
)

#: Señales del tipo documental. Cada patrón se busca sobre el nombre del fichero y sobre el texto
#: normalizado; la etiqueta es lo que se cita como evidencia de la propuesta.
_CUES_DOCUMENT_TYPE: tuple[tuple[DocumentType, str, float, str], ...] = (
    (DocumentType.OFFICIAL_EXAM, r"\bexamen oficial\b", 0.7, "«examen oficial»"),
    (DocumentType.ANSWER_KEY, r"\bplantilla de respuestas\b", 0.7, "«plantilla de respuestas»"),
    (DocumentType.ANSWER_KEY, r"\brespuesta correcta\b", 0.5, "«respuesta correcta»"),
    (DocumentType.ANSWER_KEY, r"\bclave de respuestas\b", 0.6, "«clave de respuestas»"),
    (DocumentType.CONVOCATION, r"\bconvocatoria\b", 0.6, "«convocatoria»"),
    (DocumentType.CONVOCATION, r"\bbases de la convocatoria\b", 0.7, "«bases de la convocatoria»"),
    (DocumentType.CURRICULUM, r"\btemario oficial\b", 0.7, "«temario oficial»"),
    (DocumentType.CURRICULUM, r"\bprograma oficial\b", 0.7, "«programa oficial»"),
    (DocumentType.CURRICULUM, r"\banexo v\b", 0.5, "«anexo V»"),
    (DocumentType.LAW_OR_REGULATION, r"\breal decreto\b", 0.7, "«real decreto»"),
    (DocumentType.LAW_OR_REGULATION, r"\bley organica\b", 0.6, "«ley orgánica»"),
    (DocumentType.LAW_OR_REGULATION, r"\breglamento\b", 0.5, "«reglamento»"),
    (DocumentType.PRIVATE_SYLLABUS, r"\btemario particular\b", 0.7, "«temario particular»"),
    (DocumentType.PRIVATE_SYLLABUS, r"\bacademia\b", 0.4, "«academia»"),
    (DocumentType.PRIVATE_QUESTION_BANK, r"\bbanco de preguntas\b", 0.7, "«banco de preguntas»"),
    (DocumentType.PRIVATE_QUESTION_BANK, r"\btest de repaso\b", 0.5, "«test de repaso»"),
    (DocumentType.FLASHCARDS, r"\btarjetas de repaso\b", 0.7, "«tarjetas de repaso»"),
    (DocumentType.FLASHCARDS, r"\bflashcards\b", 0.7, "«flashcards»"),
    (DocumentType.PRACTICAL_CASE, r"\bcaso practico\b", 0.7, "«caso práctico»"),
    (DocumentType.COMMUNITY_MATERIAL, r"\bapuntes de\b", 0.4, "«apuntes de»"),
    (DocumentType.COMMUNITY_MATERIAL, r"\bforo\b", 0.4, "«foro»"),
    (DocumentType.PERSONAL_NOTES, r"\bmis apuntes\b", 0.7, "«mis apuntes»"),
    (DocumentType.PERSONAL_NOTES, r"\bresumen personal\b", 0.7, "«resumen personal»"),
    (DocumentType.PERSONAL_NOTES, r"\besquema propio\b", 0.6, "«esquema propio»"),
    (DocumentType.OFFICIAL_TECHNICAL, r"\bguia tecnica\b", 0.6, "«guía técnica»"),
    (DocumentType.OFFICIAL_TECHNICAL, r"\bmanual de\b", 0.5, "«manual de»"),
    (
        DocumentType.OFFICIAL_TECHNICAL,
        r"\bespecificacion tecnica\b",
        0.6,
        "«especificación técnica»",
    ),
)

#: Señales de autoridad. Ninguna coincide -> **no hay propuesta** en ese eje.
_CUES_AUTHORITY: tuple[tuple[AuthorityTier, str, float, str], ...] = (
    (AuthorityTier.A, r"\bboletin oficial del estado\b", 0.8, "«Boletín Oficial del Estado»"),
    (AuthorityTier.A, r"\bministerio de\b", 0.6, "«Ministerio de»"),
    (AuthorityTier.A, r"\bdireccion general de\b", 0.6, "«Dirección General de»"),
    (AuthorityTier.A, r"\bresolucion de \d", 0.5, "«Resolución de …»"),
    (AuthorityTier.B, r"\bcomunidad autonoma\b", 0.5, "«comunidad autónoma»"),
    (AuthorityTier.B, r"\bayuntamiento\b", 0.4, "«ayuntamiento»"),
    (AuthorityTier.B, r"\bdiputacion\b", 0.4, "«diputación»"),
    (AuthorityTier.C, r"\beditorial\b", 0.5, "«editorial»"),
    (AuthorityTier.C, r"\bisbn\b", 0.5, "«ISBN»"),
    (AuthorityTier.C, r"\bautor(?:a)?:\b", 0.4, "«autor:»"),
    (AuthorityTier.D, r"\bforo\b", 0.4, "«foro»"),
    (AuthorityTier.D, r"\bcomunidad de opositores\b", 0.5, "«comunidad de opositores»"),
    (AuthorityTier.D, r"\banonimo\b", 0.4, "«anónimo»"),
)

#: Dominios que son publicación oficial por sí mismos: la procedencia también es una señal.
_OFFICIAL_HOSTS = (".gob.es", ".boe.es", ".europa.eu", ".gob.es/")

#: Señales de derechos. Ninguna coincide -> **no hay propuesta** en ese eje.
_CUES_RIGHTS: tuple[tuple[RightsStatus, str, float, str], ...] = (
    (
        RightsStatus.REUSE_WITH_CONDITIONS,
        r"\breutilizacion (?:autorizada|permitida)\b",
        0.7,
        "«reutilización autorizada»",
    ),
    (
        RightsStatus.REUSE_WITH_CONDITIONS,
        r"\bcondiciones de reutilizacion\b",
        0.6,
        "«condiciones de reutilización»",
    ),
    (
        RightsStatus.PRIVATE_USE_ONLY,
        r"\buso privado\b",
        0.6,
        "«uso privado»",
    ),
    (
        RightsStatus.PRIVATE_USE_ONLY,
        r"\bprohibida su reproduccion\b",
        0.7,
        "«prohibida su reproducción»",
    ),
    (
        RightsStatus.PRIVATE_USE_ONLY,
        r"\btodos los derechos reservados\b",
        0.7,
        "«todos los derechos reservados»",
    ),
    (RightsStatus.RIGHTS_DOCUMENT, r"\baviso legal\b", 0.6, "«aviso legal»"),
    (RightsStatus.RIGHTS_DOCUMENT, r"\bcondiciones de uso\b", 0.6, "«condiciones de uso»"),
)

#: Peso a partir del cual una señal se considera fuerte (una publicación oficial, una plantilla de
#: respuestas, un temario oficial). Por debajo son señales débiles y no bastan para decidir solas.
_STRONG_WEIGHT = 0.6

#: Techo de la confianza cuando **solo** coinciden señales débiles: por debajo del umbral de
#: la banda alta a propósito: «apuntes de» + «foro» no pueden autoaplicar una etiqueta equivocada
#: sobre material con derechos; se quedan en la cola de revisión.
_WEAK_ONLY_CEILING = 0.6

#: Un pegado lo escribió el usuario: es una señal floja de apuntes propios, nunca una certeza.
_PASTE_CUE = (DocumentType.PERSONAL_NOTES, 0.4, "origen: texto pegado por el usuario")


def _normalise(texto: str) -> str:
    """Minúsculas y sin tildes: las reglas se leen igual con `Ó` que con `o`."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(
        caracter for caracter in descompuesto if not unicodedata.combining(caracter)
    )
    return sin_tildes.lower()


def _significativas(titulo: str) -> list[str]:
    """Palabras del título que cuentan para comparar con el texto (sin vacías ni cortas)."""
    limpias = re.findall(r"[a-z0-9]+", _normalise(titulo))
    return [palabra for palabra in limpias if len(palabra) >= 4 and palabra not in _STOPWORDS]


@dataclass(frozen=True, slots=True)
class _Match:
    value: str
    score: float
    evidence: tuple[str, ...]


def _score_cues(
    texto_normalizado: str,
    nombre_normalizado: str,
    cues: Iterable[tuple[str, str, float, str]],
    *,
    cap: float = 0.9,
) -> list[_Match]:
    """Suma los pesos de las señales que coinciden, agrupadas por valor."""
    acumulado: dict[str, float] = {}
    evidencias: dict[str, list[str]] = {}
    fuertes: set[str] = set()
    for value, patron, peso, etiqueta in cues:
        if re.search(patron, texto_normalizado) or re.search(patron, nombre_normalizado):
            if etiqueta in evidencias.get(value, []):
                continue
            acumulado[value] = acumulado.get(value, 0.0) + peso
            evidencias.setdefault(value, []).append(etiqueta)
            if peso >= _STRONG_WEIGHT:
                fuertes.add(value)
    return [
        _Match(
            value=value,
            score=round(_techo(score, cap=cap, fuerte=value in fuertes), 2),
            evidence=tuple(evidencias[value]),
        )
        for value, score in acumulado.items()
    ]


def _techo(score: float, *, cap: float, fuerte: bool) -> float:
    """Confianza final: sin ninguna señal fuerte, no se pasa del techo de las señales débiles."""
    limite = cap if fuerte else min(cap, _WEAK_ONLY_CEILING)
    return min(limite, score)


class DeterministicClassifier:
    """Motor de reglas explícitas: implementa `ClassifierPort` sin base de datos ni red."""

    name = ENGINE_NAME
    version = ENGINE_VERSION

    def propose(self, subject: ClassificationSubject) -> Sequence[Proposal]:
        """Propone lo que las señales sostienen y nada más: sin señales, sin propuesta."""
        texto = subject.text[:MAX_EXCERPT_CHARS]
        texto_normalizado = _normalise(texto)
        nombre_normalizado = _normalise(subject.original_name or "")
        propuestas: list[Proposal] = []

        for eje, coincidencias in (
            (
                Axis.DOCUMENT_TYPE,
                self._document_type(subject, texto_normalizado, nombre_normalizado),
            ),
            (Axis.OPPOSITION, self._opposition(subject, texto_normalizado, nombre_normalizado)),
            (Axis.TOPIC, self._topic(subject, texto_normalizado, nombre_normalizado)),
            (Axis.AUTHORITY, self._authority(subject, texto_normalizado, nombre_normalizado)),
            (Axis.RIGHTS, self._rights(texto_normalizado, nombre_normalizado)),
        ):
            if not coincidencias:
                continue
            principal, *resto = coincidencias
            propuestas.append(
                Proposal(
                    id="",
                    subject_type=subject.subject_type,
                    subject_id=subject.subject_id,
                    axis=eje,
                    proposed_value=principal.value,
                    confidence=principal.score,
                    engine_name=self.name,
                    engine_version=self.version,
                    alternatives=tuple(
                        Alternative(value=otra.value, confidence=otra.score) for otra in resto[:2]
                    ),
                    evidence=principal.evidence,
                )
            )
        return tuple(propuestas)

    def _document_type(
        self, subject: ClassificationSubject, texto: str, nombre: str
    ) -> list[_Match]:
        coincidencias = _score_cues(texto, nombre, _CUES_DOCUMENT_TYPE)
        if subject.origin_type == "paste":
            tipo, peso, etiqueta = _PASTE_CUE
            if not any(match.value == tipo.value for match in coincidencias):
                coincidencias.append(_Match(value=tipo.value, score=peso, evidence=(etiqueta,)))
        return sorted(coincidencias, key=lambda match: (-match.score, match.value))

    def _opposition(self, subject: ClassificationSubject, texto: str, nombre: str) -> list[_Match]:
        coincidencias: list[_Match] = []
        for perfil in subject.profiles:
            codigo = _normalise(perfil.opposition_code)

            evidencias: list[str] = []
            score = 0.0
            if re.search(rf"\b{re.escape(codigo)}\b", texto) or re.search(
                rf"\b{re.escape(codigo)}\b", nombre
            ):
                score += 0.6
                evidencias.append(f"código «{perfil.opposition_code}»")
            palabras = _significativas(perfil.opposition_name)
            if palabras and all(
                re.search(rf"\b{re.escape(palabra)}", texto) for palabra in palabras
            ):
                score += 0.4
                evidencias.append(f"nombre «{perfil.opposition_name}»")
            if score:
                coincidencias.append(
                    _Match(
                        value=perfil.opposition_code,
                        score=round(min(0.9, score), 2),
                        evidence=tuple(evidencias),
                    )
                )
        return sorted(coincidencias, key=lambda match: (-match.score, match.value))

    def _topic(self, subject: ClassificationSubject, texto: str, nombre: str) -> list[_Match]:
        coincidencias: list[_Match] = []
        for perfil in subject.profiles:
            for nodo in perfil.topics:
                coincidencia = _topic_match(nodo, texto, nombre)
                if coincidencia is not None:
                    coincidencias.append(coincidencia)
        # Ante la misma confianza gana el nodo más profundo: un apunte de un tema concreto no
        # «cubre» el bloque entero, y la cobertura se calcula con esto.
        profundidades = {
            nodo.path: nodo.depth for perfil in subject.profiles for nodo in perfil.topics
        }
        return sorted(
            coincidencias,
            key=lambda match: (-match.score, -profundidades.get(match.value, 0), match.value),
        )

    def _authority(self, subject: ClassificationSubject, texto: str, nombre: str) -> list[_Match]:
        coincidencias = _score_cues(texto, nombre, _CUES_AUTHORITY)
        procedencia = _normalise(subject.origin_display or "")
        if procedencia and any(host in procedencia for host in _OFFICIAL_HOSTS):
            coincidencias.append(
                _Match(value=AuthorityTier.A.value, score=0.8, evidence=("procedencia oficial",))
            )
        agrupado: dict[str, _Match] = {}
        for coincidencia in coincidencias:
            actual = agrupado.get(coincidencia.value)
            if actual is None or coincidencia.score > actual.score:
                agrupado[coincidencia.value] = coincidencia
        return sorted(agrupado.values(), key=lambda match: (-match.score, match.value))

    def _rights(self, texto: str, nombre: str) -> list[_Match]:
        return sorted(
            _score_cues(texto, nombre, _CUES_RIGHTS), key=lambda match: (-match.score, match.value)
        )


def _topic_match(nodo: TopicCandidate, texto: str, nombre: str) -> _Match | None:
    """Propone un nodo del programa si al menos la mitad de las palabras de su título aparecen.

    Las palabras se buscan **enteras**, no como prefijo: si «derecho» diera por bueno «derechos», un
    bloque genérico empataría con el tema concreto que el material sí menciona.
    """
    palabras = _significativas(nodo.title)
    if not palabras:
        return None
    presentes = [
        palabra
        for palabra in palabras
        if re.search(rf"\b{re.escape(palabra)}\b", texto)
        or re.search(rf"\b{re.escape(palabra)}\b", nombre)
    ]
    proporcion = len(presentes) / len(palabras)
    if proporcion < 0.5:
        return None
    return _Match(
        value=nodo.path,
        score=round(min(0.9, 0.3 + 0.5 * proporcion), 2),
        evidence=(f"título del programa «{nodo.title}»",),
    )


def build_subject_id(subject_type: SubjectType, subject_id: str) -> str:
    """Identificador estable de un sujeto, útil para logs y para la clave de grupo."""
    return f"{subject_type.value}:{subject_id}"


def profiles_from_rows(
    rows: Iterable[tuple[str, str, Sequence[tuple[str, str, str, int]]]],
) -> tuple[ProfileCandidate, ...]:
    """Construye los perfiles candidatos desde filas, sin acoplarse al ORM."""
    return tuple(
        ProfileCandidate(
            opposition_code=codigo,
            opposition_name=nombre,
            convocation_code="",
            topics=tuple(
                TopicCandidate(node_id=nodo_id, path=path, title=title, depth=depth)
                for nodo_id, path, title, depth in nodos
            ),
        )
        for codigo, nombre, nodos in rows
    )
