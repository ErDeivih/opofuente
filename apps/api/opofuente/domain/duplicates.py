"""Detección determinista de duplicados de **texto** (S04): reglas puras, sin base de datos ni red.

Reglas y por qué son así:

- **Los duplicados exactos de bytes no se buscan aquí.** Dos ficheros idénticos ya son un artefacto
  con dos orígenes (`artifact_origins`), y eso lo garantiza el almacén por hash desde S02.
- **Mismo texto normalizado** (`same_text`): el hash del texto normalizado coincide. No se borra
  ninguno, porque la paginación y la cita pueden cambiar de un fichero a otro.
- **Casi duplicados** (`near_duplicate`): similitud de Jaccard sobre fragmentos de palabras
  (shingles) por encima de un umbral. Solo se **propone** un cluster: no se fusiona nada.
- Todo es reproducible: mismo material, mismos clusters, en el mismo orden. Y hay un tope de
  comparaciones (`MAX_COMPARISONS`) porque este paso no puede crecer sin límite en una biblioteca
  grande: cuando se alcanza, la detección para y lo dice el informe en lugar de mentir.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

#: Umbral de similitud para considerar dos textos casi duplicados.
NEAR_DUPLICATE_THRESHOLD = 0.8

#: Palabras por fragmento al comparar. Cinco palabras bastan para no confundir frases sueltas.
SHINGLE_SIZE = 5

#: Tope de comparaciones por pareja en una pasada. Un orden de magnitud por encima de una biblioteca
#: personal razonable; si se supera, la detección avisa en lugar de quedarse colgada.
MAX_COMPARISONS = 200_000

#: Con menos palabras que esto no se comparan: todo se parecería a todo.
MIN_WORDS_FOR_SIMILARITY = 30


@dataclass(frozen=True, slots=True)
class TextDocument:
    """Texto de un sujeto, ya listo para comparar."""

    subject_type: str
    subject_id: str
    label: str | None
    text: str


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    """Grupo detectado: la firma que lo identifica, su relación y sus miembros con su similitud."""

    kind: str
    relation: str
    signature: str
    members: tuple[tuple[str, str, str | None, float], ...]
    comparisons_exhausted: bool = False


def normalise_for_comparison(text: str) -> str:
    """Normaliza para comparar: minúsculas, sin tildes, sin puntuación y con espacios simples.

    Es una normalización **solo para comparar**: el texto que se guarda y se cita no se toca.
    """
    descompuesto = unicodedata.normalize("NFKD", text)
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    limpio = re.sub(r"[^0-9a-záéíóúüñ ]+", " ", sin_tildes.lower())
    return " ".join(limpio.split())


def text_signature(text: str) -> str:
    """Huella estable del texto normalizado: dos textos iguales dan la misma firma."""
    return hashlib.sha256(normalise_for_comparison(text).encode("utf-8")).hexdigest()


def shingles(text: str, *, size: int = SHINGLE_SIZE) -> frozenset[str]:
    """Fragmentos de `size` palabras consecutivas, como conjunto."""
    palabras = normalise_for_comparison(text).split()
    if len(palabras) < size:
        return frozenset()
    return frozenset(" ".join(palabras[i : i + size]) for i in range(len(palabras) - size + 1))


def jaccard(izquierda: frozenset[str], derecha: frozenset[str]) -> float:
    """Similitud de Jaccard entre dos conjuntos de fragmentos (0 si alguno está vacío)."""
    if not izquierda or not derecha:
        return 0.0
    union = izquierda | derecha
    if not union:
        return 0.0
    return len(izquierda & derecha) / len(union)


def find_duplicates(
    documents: Sequence[TextDocument],
    *,
    threshold: float = NEAR_DUPLICATE_THRESHOLD,
    max_comparisons: int = MAX_COMPARISONS,
) -> tuple[DuplicateGroup, ...]:
    """Grupos de mismo texto y de casi duplicados, en orden determinista."""
    grupos: list[DuplicateGroup] = []
    por_firma: dict[str, list[TextDocument]] = defaultdict(list)
    for documento in documents:
        if not normalise_for_comparison(documento.text):
            continue
        por_firma[text_signature(documento.text)].append(documento)

    ya_en_grupo: set[tuple[str, str]] = set()
    for firma in sorted(por_firma):
        miembros = sorted(por_firma[firma], key=lambda doc: (doc.subject_type, doc.subject_id))
        if len(miembros) < 2:
            continue
        for miembro in miembros:
            ya_en_grupo.add((miembro.subject_type, miembro.subject_id))
        grupos.append(
            DuplicateGroup(
                kind="same_text",
                relation="similar",
                signature=firma,
                members=tuple(
                    (doc.subject_type, doc.subject_id, doc.label, 1.0) for doc in miembros
                ),
            )
        )

    candidatos = [
        documento
        for documento in documents
        if (documento.subject_type, documento.subject_id) not in ya_en_grupo
        and len(normalise_for_comparison(documento.text).split()) >= MIN_WORDS_FOR_SIMILARITY
    ]
    candidatos.sort(key=lambda doc: (doc.subject_type, doc.subject_id))
    fragmentos = {_clave(doc): shingles(doc.text) for doc in candidatos}

    comparaciones = 0
    agotado = False
    pares: list[tuple[TextDocument, TextDocument, float]] = []
    for indice, izquierda in enumerate(candidatos):
        for derecha in candidatos[indice + 1 :]:
            if comparaciones >= max_comparisons:
                agotado = True
                break
            comparaciones += 1
            similitud = jaccard(fragmentos[_clave(izquierda)], fragmentos[_clave(derecha)])
            if similitud >= threshold:
                pares.append((izquierda, derecha, similitud))
        if agotado:
            break

    for izquierda, derecha, similitud in pares:
        firma = hashlib.sha256(
            "|".join(sorted([_clave(izquierda), _clave(derecha)])).encode("utf-8")
        ).hexdigest()
        grupos.append(
            DuplicateGroup(
                kind="near_duplicate",
                relation="similar",
                signature=firma,
                members=(
                    (izquierda.subject_type, izquierda.subject_id, izquierda.label, similitud),
                    (derecha.subject_type, derecha.subject_id, derecha.label, similitud),
                ),
                comparisons_exhausted=agotado,
            )
        )
    return _merge_components(grupos)


def _clave(documento: TextDocument) -> str:
    return f"{documento.subject_type}:{documento.subject_id}"


def groups_by_kind(groups: Iterable[DuplicateGroup]) -> dict[str, int]:
    """Cuántos grupos de cada tipo: lo que se informa en la pasada de duplicados."""
    conteo: dict[str, int] = defaultdict(int)
    for grupo in groups:
        conteo[grupo.kind] += 1
    return dict(conteo)


def _merge_components(grupos: Sequence[DuplicateGroup]) -> tuple[DuplicateGroup, ...]:
    """Une los grupos de casi duplicados que comparten algún miembro.

    Comparar por pares deja cadenas: si A se parece a B y B a C, salían dos clusters para el mismo
    material. Aquí se unen por componentes conexas, así que un grupo de textos parecidos es **un**
    cluster, con una firma determinista (el hash de sus miembros ordenados) que no depende del orden
    en que se hayan comparado.
    """
    mismo_texto = [grupo for grupo in grupos if grupo.kind != "near_duplicate"]
    casi = [grupo for grupo in grupos if grupo.kind == "near_duplicate"]
    if not casi:
        return tuple(mismo_texto)

    padre: dict[str, str] = {}

    def _raiz(clave: str) -> str:
        padre.setdefault(clave, clave)
        while padre[clave] != clave:
            padre[clave] = padre[padre[clave]]
            clave = padre[clave]
        return clave

    miembros: dict[str, tuple[str, str, str | None, float]] = {}
    for grupo in casi:
        for miembro in grupo.members:
            clave = f"{miembro[0]}:{miembro[1]}"
            miembros[clave] = miembro
            _raiz(clave)
        claves = [f"{miembro[0]}:{miembro[1]}" for miembro in grupo.members]
        for otra in claves[1:]:
            padre[_raiz(otra)] = _raiz(claves[0])

    componentes: dict[str, list[str]] = {}
    for clave in sorted(miembros):
        componentes.setdefault(_raiz(clave), []).append(clave)

    agotado = any(grupo.comparisons_exhausted for grupo in casi)
    unidos: list[DuplicateGroup] = []
    for claves in componentes.values():
        if len(claves) < 2:
            continue
        firma = hashlib.sha256("|".join(claves).encode("utf-8")).hexdigest()
        unidos.append(
            DuplicateGroup(
                kind="near_duplicate",
                relation="similar",
                signature=firma,
                members=tuple(miembros[clave] for clave in claves),
                comparisons_exhausted=agotado,
            )
        )
    return tuple(mismo_texto + unidos)
