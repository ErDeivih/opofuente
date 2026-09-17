"""Pruebas unitarias de la detección de duplicados de texto (S04).

Lo que se fija aquí es la **forma** de la detección, que es donde estaban los defectos: los
duplicados exactos de bytes no llegan aquí (son un artefacto con varios orígenes), el mismo texto
con otra maquetación se agrupa, y los casi duplicados se unen por componentes conexas y no con un
cluster por pareja.
"""

from __future__ import annotations

from opofuente.domain.duplicates import (
    MIN_WORDS_FOR_SIMILARITY,
    TextDocument,
    find_duplicates,
    jaccard,
    normalise_for_comparison,
    shingles,
    text_signature,
)

#: Texto largo con muchas palabras **distintas**: así una variante en el final apenas cambia el
#: conjunto de fragmentos y la similitud se mantiene alta, que es el caso real (dos revisiones del
#: mismo apunte). Un texto repetitivo daría un conjunto de fragmentos diminuto y engañoso.
LARGO = " ".join(f"palabra{i}" for i in range(200))


def _documento(nombre: str, texto: str) -> TextDocument:
    return TextDocument(
        subject_type="artifact", subject_id=nombre, label=f"{nombre}.txt", text=texto
    )


def test_el_mismo_texto_con_otra_maquetacion_es_un_duplicado() -> None:
    """Bytes distintos, contenido igual: es el caso que el almacén por hash **no** detecta."""
    documentos = (
        _documento("a", "Resumen del tema de legislacion con dos ejemplos resueltos."),
        _documento("b", "Resumen  del  tema  de  legislacion  con  dos  ejemplos  resueltos."),
    )

    grupos = find_duplicates(documentos)

    assert len(grupos) == 1
    assert grupos[0].kind == "same_text"
    assert len(grupos[0].members) == 2
    assert {miembro[1] for miembro in grupos[0].members} == {"a", "b"}


def test_tres_textos_parecidos_son_un_solo_cluster_y_no_tres() -> None:
    """Regresión: la comparación por pares dejaba una cadena de clusters para el mismo material."""
    largo = LARGO
    documentos = (
        _documento("a", largo + "Primera variante del final del documento."),
        _documento("b", largo + "Segunda variante del final del documento."),
        _documento("c", largo + "Tercera variante del final del documento."),
    )

    grupos = find_duplicates(documentos)

    casi = [grupo for grupo in grupos if grupo.kind == "near_duplicate"]
    assert len(casi) == 1, f"los tres textos deberían ser un cluster: {len(casi)}"
    assert len(casi[0].members) == 3
    assert {miembro[1] for miembro in casi[0].members} == {"a", "b", "c"}


def test_la_firma_del_cluster_no_depende_del_orden_de_comparacion() -> None:
    """Mismo material, misma firma: el orden de los documentos no puede cambiarla."""
    largo = LARGO
    a = _documento("a", largo + "Primera variante del final.")
    b = _documento("b", largo + "Segunda variante del final.")

    primera = find_duplicates((a, b))
    segunda = find_duplicates((b, a))

    assert [grupo.signature for grupo in primera] == [grupo.signature for grupo in segunda]


def test_un_texto_sin_senales_no_se_compara_con_nada() -> None:
    """Un texto muy corto no entra: cualquier cosa se parecería a cualquier cosa."""
    corto = _documento("corto", "Dos palabras.")
    largo = _documento("largo", LARGO * 3)

    assert find_duplicates((corto, largo)) == ()
    assert len(normalise_for_comparison(corto.text).split()) < MIN_WORDS_FOR_SIMILARITY


def test_la_normalizacion_solo_sirve_para_comparar() -> None:
    """Sirve para comparar: minúsculas, sin tildes y con espacios simples, sin tocar el original."""
    assert normalise_for_comparison("SESIÓN   de TAI: 1/2") == "sesion de tai 1 2"
    assert text_signature("Hola  mundo") == text_signature("hola mundo")
    # La puntuación no cuenta para comparar: dos textos que solo difieren en el punto son el mismo.
    assert text_signature("Hola mundo") == text_signature("Hola mundo.")


def test_la_similitud_de_fragmentos_es_la_esperada() -> None:
    """Jaccard sobre fragmentos de palabras: 1 si son iguales y 0 si no comparten nada."""
    texto = LARGO
    assert jaccard(shingles(texto), shingles(texto)) == 1.0
    assert jaccard(shingles(texto), shingles("otra cosa completamente distinta " * 20)) == 0.0
    assert jaccard(frozenset(), shingles(texto)) == 0.0
