"""Pruebas unitarias del emparejamiento fragmento → nodo del programa (S14).

Las que importan son tres: que acierte con lo que dice un título oficial, que **no proponga
nada** cuando
no hay nada que proponer, y que dos ejecuciones den exactamente lo mismo.
"""

from __future__ import annotations

import pytest

from opofuente.domain.topic_matching import (
    MAXIMO_CARACTERES_TROZO,
    UMBRAL_POR_DEFECTO,
    EmparejadorDeTemas,
    NodoPrograma,
    fragmentar,
    normalizar,
    palabras,
    raiz,
)


def _nodos() -> tuple[NodoPrograma, ...]:
    """Cuatro nodos del temario real de TAI: dos del bloque I, uno del III y uno del IV."""
    return (
        NodoPrograma(
            node_id="n-1",
            path="I.1",
            title=(
                "La Constitución Española de 1978. Derechos y deberes fundamentales. "
                "Su garantía y suspensión. La Corona: funciones constitucionales del Rey."
            ),
        ),
        NodoPrograma(
            node_id="n-3",
            path="I.3",
            title=(
                "El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. "
                "Relaciones entre el Gobierno y las Cortes Generales."
            ),
        ),
        NodoPrograma(
            node_id="n-13",
            path="III.3",
            title=(
                "Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. "
                "Procedimientos almacenados. Eventos y disparadores."
            ),
        ),
        NodoPrograma(
            node_id="n-19",
            path="IV.10",
            title=(
                "Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. "
                "Dispositivos de interconexión."
            ),
        ),
    )


def test_normalizar_quita_acentos_y_signos() -> None:
    """El material llega de PDF, de OCR y pegado: «Constitución» y «Constitucion» son la misma
    palabra."""
    assert normalizar("La Constitución Española, de 1978.") == "la constitucion espanola de 1978"
    assert normalizar("Constitución") == normalizar("CONSTITUCION")


def test_la_raiz_junta_singular_plural_y_genero() -> None:
    """Un recorte tosco basta para que «administrativo» y «administrativas» cuenten igual."""
    assert raiz("administrativo") == raiz("administrativa")
    assert raiz("dispositivos") == raiz("dispositivo")
    assert raiz("ley") == "ley"  # no se recorta una palabra corta


def test_las_palabras_sin_valor_no_cuentan() -> None:
    """«tema», «bloque» o «general» están en todos los títulos: no distinguen ninguno."""
    assert "tema" not in palabras("Tema 5 del bloque I")
    assert "generales" not in palabras("Cortes Generales")


def test_un_fragmento_de_la_constitucion_cae_en_su_tema() -> None:
    """El caso que da sentido a todo esto: un párrafo habla de un tema, aunque el documento sea
    de otro."""
    emparejador = EmparejadorDeTemas(_nodos())
    fragmento = (
        "La Constitución garantiza los derechos y deberes fundamentales y regula su garantía y "
        "suspensión. La Corona es inviolable: corresponde al Rey sancionar y promulgar las leyes "
        "según las funciones constitucionales que le atribuye la Constitución Española de 1978."
    )

    coincidencia = emparejador.emparejar(fragmento)

    assert coincidencia is not None
    assert coincidencia.nodo.path == "I.1"


def test_un_fragmento_tecnico_cae_en_su_tema_y_no_en_el_de_al_lado() -> None:
    """Los nodos son de bloques distintos: la prueba no se aprueba eligiendo «el primero»."""
    emparejador = EmparejadorDeTemas(_nodos())

    sql = emparejador.emparejar(
        "El estándar ANSI SQL define las instrucciones de consulta. Un procedimiento almacenado "
        "es un programa que se guarda en el servidor de bases de datos; un disparador se ejecuta "
        "al modificar una tabla."
    )
    redes = emparejador.emparejar(
        "La topología en estrella conecta cada dispositivo a un conmutador central. El método de "
        "acceso al medio determina cómo se reparte el canal entre las estaciones de la red local."
    )

    assert sql is not None and sql.nodo.path == "III.3"
    assert redes is not None and redes.nodo.path == "IV.10"


def test_sin_senales_no_se_propone_nada() -> None:
    """No forzar es la mitad del diseño: una propuesta floja es una decisión que alguien deshace."""
    emparejador = EmparejadorDeTemas(_nodos())

    assert emparejador.emparejar("") is None
    assert emparejador.emparejar("Índice de contenidos. Página 2 de 48.") is None
    assert emparejador.emparejar("lorem ipsum dolor sit amet consectetur") is None


def test_la_porteria_no_se_asigna_a_ningun_tema_por_una_palabra_suelta() -> None:
    """Un pie con «Gobierno de España» no convierte la página en el tema del Gobierno.

    Es la razón de que sólo cuente lo que pasa del umbral: dos palabras sueltas de un título no
    bastan.
    """
    emparejador = EmparejadorDeTemas(_nodos())

    assert emparejador.emparejar("Gobierno de España. Ministerio de Hacienda. Ejemplar 1.") is None


def test_un_titulo_largo_diluye_y_el_fragmento_se_queda_sin_asignar() -> None:
    """Límite conocido y aceptado: una sola palabra de un título largo no basta para proponer.

    El tema I.1 es el título más largo del programa, así que un fragmento que sólo comparta «Corona»
    se queda por debajo del umbral. El error cae del lado conservador —no se propone nada— y por eso
    se deja así: forzar la propuesta crearía una decisión que alguien tendría que deshacer.
    """
    emparejador = EmparejadorDeTemas(_nodos())

    assert emparejador.emparejar("La Corona es inviolable.") is None


def test_el_mismo_fragmento_da_siempre_lo_mismo() -> None:
    """Dos ejecuciones y dos emparejadores distintos dan la misma propuesta y la misma
    puntuación."""
    fragmento = (
        "Las redes locales se clasifican por su tipología y por el método de acceso al medio, y "
        "los dispositivos de interconexión reparten el tráfico entre segmentos."
    )

    primera = EmparejadorDeTemas(_nodos()).emparejar(fragmento)
    segunda = EmparejadorDeTemas(list(reversed(_nodos()))).emparejar(fragmento)

    assert primera is not None and segunda is not None
    assert primera == segunda


def test_el_desempate_lo_fija_la_ruta_y_no_el_orden_de_entrada() -> None:
    """Con dos nodos idénticos en contenido, gana el de ruta menor: nunca el que llegó antes."""
    repetido = (
        NodoPrograma(node_id="b", path="IV.10", title="Redes locales y dispositivos de enlace"),
        NodoPrograma(node_id="a", path="II.3", title="Redes locales y dispositivos de enlace"),
    )

    coincidencia = EmparejadorDeTemas(repetido).emparejar("Las redes locales y sus dispositivos")

    assert coincidencia is not None
    assert coincidencia.nodo.path == "II.3"


def test_las_alternativas_van_por_detras_de_la_elegida() -> None:
    """La revisión necesita ver qué había al lado, no sólo qué se eligió."""
    emparejador = EmparejadorDeTemas(_nodos())
    fragmento = (
        "Las Cortes Generales representan al pueblo español. El Gobierno dirige la política "
        "interior y exterior y responde ante el Congreso de los Diputados."
    )

    coincidencia = emparejador.emparejar(fragmento)

    assert coincidencia is not None
    assert all(valor <= coincidencia.puntuacion for _, valor in coincidencia.alternativas)
    assert coincidencia.puntuacion > 0


def test_el_umbral_se_puede_subir_y_es_el_mismo_por_defecto() -> None:
    """El umbral es una decisión, no una constante escondida: se puede exigir más."""
    emparejador = EmparejadorDeTemas(_nodos())
    fragmento = "El procedimiento almacenado y el disparador son objetos de la base de datos."

    assert emparejador.emparejar(fragmento, umbral=UMBRAL_POR_DEFECTO) is not None
    assert emparejador.emparejar(fragmento, umbral=0.99) is None

    with pytest.raises(ValueError):
        emparejador.emparejar(fragmento, umbral=1.5)


def test_sin_nodos_no_hay_emparejador() -> None:
    """Un programa vacío es un error de quien llama, no un emparejador que nunca encuentra nada."""
    with pytest.raises(ValueError):
        EmparejadorDeTemas([])


def test_fragmentar_descarta_un_bloque_corto_y_no_pierde_una_cola_larga() -> None:
    """Las dos reglas del troceado: la migaja suelta se cae, la cola de un párrafo largo no.

    «Página 12» solo no es un trozo (no hay nada que clasificar). Pero el resto de un párrafo
    partido
    **sí** se conserva aunque quede corto: es contenido, no una migaja.
    """
    assert fragmentar("Página 12") == ()
    assert fragmentar("") == ()

    largo = "Frase de relleno suficientemente larga para contar como contenido real. " * 40
    trozos = fragmentar(largo)

    assert len(trozos) > 1
    assert all(len(trozo) <= MAXIMO_CARACTERES_TROZO for trozo in trozos)
    # Ninguna letra se ha quedado fuera: lo que se pierde son sólo los espacios de unión.
    assert sum(len(trozo) for trozo in trozos) >= len(largo.strip()) - 2 * len(trozos)


def test_fragmentar_agrupa_parrafos_cortos_en_uno_solo() -> None:
    """Dos párrafos cortos de un mismo tema son un trozo, no dos: el tema se lee en el conjunto."""
    corto = "Un párrafo breve sobre el tema. " * 12

    trozos = fragmentar(f"{corto}\n\n{corto}")

    assert len(trozos) == 1
    assert trozos[0].count("\n\n") == 1
    assert len(trozos[0]) <= MAXIMO_CARACTERES_TROZO


def test_fragmentar_rechaza_limites_absurdos() -> None:
    """Unos límites que no dejan trocear son un error, no un troceado vacío."""
    with pytest.raises(ValueError):
        fragmentar("texto", minimo=0)
    with pytest.raises(ValueError):
        fragmentar("texto", minimo=500, maximo=100)
