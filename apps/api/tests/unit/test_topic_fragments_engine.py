"""Pruebas del motor de temas por fragmento (S14).

Lo que hay que defender: que propone el tema del que de verdad habla el texto, que no propone nada
cuando no hay nada que proponer, y que respeta los topes del proyecto (tres nodos, eje no critico).
"""

from __future__ import annotations

from opofuente.domain.classification import (
    Axis,
    ClassificationSubject,
    ProfileCandidate,
    SubjectType,
    TopicCandidate,
)
from opofuente.infrastructure.classifiers.topic_fragments import (
    MAX_NODOS,
    FragmentTopicClassifier,
)

TITULO_CONSTITUCION = (
    "La Constitucion Espanola de 1978. Derechos y deberes fundamentales. Su garantia y "
    "suspension. La Corona: funciones constitucionales del Rey."
)
TITULO_SQL = (
    "Lenguajes de interrogacion de bases de datos. Estandar ANSI SQL. Procedimientos "
    "almacenados. Eventos y disparadores."
)
TITULO_REDES = (
    "Redes locales. Tipologia. Tecnicas de transmision. Metodos de acceso. Dispositivos de "
    "interconexion."
)


def _perfil(topics: tuple[TopicCandidate, ...] | None = None) -> ProfileCandidate:
    return ProfileCandidate(
        opposition_code="tai-age",
        opposition_name="TAI",
        convocation_code="tai-age-2025",
        topics=topics
        or (
            TopicCandidate(node_id="n-1", path="I.1", depth=1, title=TITULO_CONSTITUCION),
            TopicCandidate(node_id="n-13", path="III.3", depth=1, title=TITULO_SQL),
            TopicCandidate(node_id="n-19", path="IV.10", depth=1, title=TITULO_REDES),
        ),
    )


def _sujeto(texto: str, topics: tuple[TopicCandidate, ...] | None = None) -> ClassificationSubject:
    return ClassificationSubject(
        subject_type=SubjectType.REPRESENTATION,
        subject_id="rep-1",
        text=texto,
        profiles=(_perfil(topics),),
    )


SQL = (
    "El estandar ANSI SQL define las instrucciones de consulta y de modificacion de datos. Un "
    "procedimiento almacenado es un programa que se guarda y se ejecuta en el servidor de bases de "
    "datos; un disparador se ejecuta automaticamente al insertar o borrar filas de una tabla.\n\n"
    "Los eventos de la base de datos permiten programar tareas. La normalizacion de tablas y los "
    "lenguajes de interrogacion son la base de este tema.\n\n"
    "Un procedimiento almacenado puede recibir parametros y devolver un resultado al cliente que lo "
    "invoca; los disparadores no reciben parametros y trabajan sobre la fila que ha cambiado."
)

REDES = (
    "La topologia en estrella conecta cada dispositivo a un conmutador central y es la mas habitual "
    "en las redes locales actuales. El metodo de acceso al medio reparte el canal entre estaciones.\n\n"
    "Los dispositivos de interconexion, conmutadores y encaminadores, unen segmentos de la red local "
    "y deciden por donde sale cada trama.\n\n"
    "Las tecnicas de transmision y la tipologia de la red condicionan el cableado y la velocidad "
    "disponible en cada puesto de trabajo."
)


def test_un_texto_de_sql_propone_su_tema() -> None:
    """El documento habla de un tema sin repetir su titulo entero, y el motor lo encuentra."""
    propuestas = FragmentTopicClassifier().propose(_sujeto(SQL))

    assert propuestas, "deberia proponer al menos un tema"
    assert propuestas[0].proposed_value == "III.3"
    assert propuestas[0].axis is Axis.TOPIC
    assert 0.0 < propuestas[0].confidence <= 1.0


def test_un_texto_de_redes_propone_el_suyo_y_no_el_de_al_lado() -> None:
    """Con tres nodos distintos, la prueba no se aprueba eligiendo siempre el primero."""
    propuestas = FragmentTopicClassifier().propose(_sujeto(REDES))

    assert propuestas
    assert propuestas[0].proposed_value == "IV.10"


def test_sin_texto_no_hay_propuestas() -> None:
    """Sin texto no se propone nada: no es un fallo, es la respuesta correcta."""
    motor = FragmentTopicClassifier()

    assert motor.propose(_sujeto("")) == ()
    assert motor.propose(_sujeto("   ")) == ()


def test_sin_programa_no_hay_propuestas() -> None:
    """Sin nodos del programa no hay nada con lo que comparar."""
    sujeto = ClassificationSubject(subject_type=SubjectType.ARTIFACT, subject_id="art-1", text=SQL)

    assert FragmentTopicClassifier().propose(sujeto) == ()


def test_un_solo_nodo_no_se_propone() -> None:
    """Con un unico nodo, proponerlo seria decir que todo el material es de ese tema."""
    solo = (TopicCandidate(node_id="n", path="I.1", depth=1, title=TITULO_CONSTITUCION),)

    assert FragmentTopicClassifier().propose(_sujeto(SQL, solo)) == ()


def test_nunca_pasa_de_tres_nodos() -> None:
    """Hasta tres nodos por documento: lo pide el proyecto, no el motor."""
    temas = (
        TopicCandidate(node_id="a", path="I.1", depth=1, title="Redes locales. Metodos de acceso."),
        TopicCandidate(node_id="b", path="I.2", depth=1, title="Redes locales. Dispositivos."),
        TopicCandidate(node_id="c", path="I.3", depth=1, title="Tipologia de redes locales."),
        TopicCandidate(node_id="d", path="I.4", depth=1, title="Metodos de acceso al medio."),
        TopicCandidate(node_id="e", path="I.5", depth=1, title="Conmutadores de red local."),
    )
    propuestas = FragmentTopicClassifier().propose(_sujeto(REDES, temas))

    assert len(propuestas) <= MAX_NODOS
    assert all(p.axis is Axis.TOPIC for p in propuestas)
    assert all(p.engine_name == FragmentTopicClassifier.name for p in propuestas)
    assert all(p.evidence for p in propuestas), "una propuesta sin evidencia no se puede revisar"


def test_la_confianza_es_la_parte_del_documento() -> None:
    """La confianza significa algo: la parte del documento que habla de ese tema.

    Si solo un nodo casa con algun fragmento no hay alternativas, y eso tambien es correcto: no
    habia nada mas con lo que comparar. Por eso la prueba no exige que existan.
    """
    propuestas = FragmentTopicClassifier().propose(_sujeto(SQL))

    assert propuestas
    principal = propuestas[0]
    assert 0.0 < principal.confidence <= 1.0
    assert sum(a.confidence for a in principal.alternatives) + principal.confidence <= 1.0 + 1e-9
    if principal.alternatives:
        assert principal.confidence >= max(a.confidence for a in principal.alternatives)
