"""El índice por materias de un tema (el esquema antes de redactar), sin red y sin base de datos.

Lo que se comprueba es lo que tiene que sostener el índice para que sirva de algo:

- **todo hecho cae en un apartado y en uno solo** (nada se pierde por el camino);
- el reparto es **determinista**: los mismos hechos dan el mismo índice;
- **la tabla de puertos tiene un solo sitio** y está marcado;
- un hecho que habla de dos materias va a la que menciona **antes** (DNS y el puerto 53 es DNS);
- un hecho que no es de ninguna materia del tema cae en el cajón, y se dice cuántos;
- el orden del índice es el del temario, no el de reparto.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from opofuente.domain.notes_quality import CABECERAS_REPETIDAS, revisar_apuntes
from opofuente.domain.topic_index import (
    Materia,
    catalogo,
    indice_de,
    materia_de,
    repartir_grupos,
    repartir_hechos,
    validar_catalogo,
)
from opofuente.domain.topic_notes import (
    FactKind,
    Hecho,
    KeyStatus,
    QuestionForNotes,
    QuestionGroup,
    agrupar,
)

EPIGRAFES = (
    ("IV.7.1", "El modelo TCP/IP y el modelo de referencia OSI de ISO."),
    ("IV.7.2", "Protocolos TCP/IP."),
)


@dataclass(frozen=True)
class _Apartado:
    """Un apartado como lo ve la revisión de forma (para comprobar el índice con ella)."""

    key: str
    title: str
    anchor: str
    body_markdown: str


def _materias() -> tuple[Materia, ...]:
    materias = catalogo("IV.7")
    assert materias is not None
    return materias


def _hecho(texto: str, *, epigrafe: str = "IV.7.2") -> Hecho:
    return Hecho(
        text=texto,
        kind=FactKind.TECNICO,
        epigraph_code=epigrafe,
        source_groups=(),
        source_questions=(),
        fact_id=texto[:12],
    )


def _grupo(identificador: str, enunciado: str, *, epigrafe: str = "IV.7.2") -> QuestionGroup:
    return agrupar(
        [
            QuestionForNotes(
                question_version_id=identificador,
                set_id="conjunto-1",
                stem=enunciado,
                options=(("a", "uno"), ("b", "dos")),
                correct_keys=("a",),
                key_status=KeyStatus.DRAFT,
                epigraph_code=epigrafe,
                mapping_status="accepted",
            )
        ]
    )[0]


# --- el catálogo ----------------------------------------------------------------------------------


def test_el_catalogo_de_iv7_cubre_sus_dos_epigrafes_y_tiene_un_cajon_por_epigrafe() -> None:
    materias = catalogo("IV.7")
    assert materias is not None
    validar_catalogo("IV.7", materias)

    assert {materia.epigraph_code for materia in materias} == {"IV.7.1", "IV.7.2"}
    for epigrafe in ("IV.7.1", "IV.7.2"):
        cajones = [m for m in materias if m.epigraph_code == epigrafe and m.es_cajon]
        assert len(cajones) == 1, f"{epigrafe} tiene que tener un cajón y solo uno"


def test_la_tabla_de_puertos_tiene_un_solo_sitio_y_esta_marcado() -> None:
    materias = catalogo("IV.7")
    assert materias is not None

    con_tabla = [materia for materia in materias if materia.tabla_unica]

    assert len(con_tabla) == 1, "una tabla que sale dos veces es justo lo que hay que impedir"
    assert con_tabla[0].key == "puertos"


def test_un_catalogo_sin_cajon_se_rechaza_antes_de_repartir() -> None:
    sin_cajon = (
        Materia(
            key="uno", epigraph_code="IV.7.1", title="Uno", resumen="", patrones=(r"\balgo\b",)
        ),
    )
    with pytest.raises(ValueError, match="cajones"):
        validar_catalogo("IV.7", sin_cajon)


def test_un_catalogo_con_la_misma_clave_dos_veces_se_rechaza() -> None:
    repetido = (
        Materia(key="uno", epigraph_code="IV.7.1", title="Uno", resumen=""),
        Materia(key="uno", epigraph_code="IV.7.1", title="Otra vez", resumen=""),
    )
    with pytest.raises(ValueError, match="repetidas"):
        validar_catalogo("IV.7", repetido)


def test_un_tema_sin_catalogo_no_tiene_indice() -> None:
    assert catalogo("I.1") is None
    with pytest.raises(KeyError):
        indice_de(topic_code="I.1", topic_title="La Constitución", epigraphs=EPIGRAFES)


# --- el reparto -----------------------------------------------------------------------------------


def test_un_hecho_va_a_la_materia_que_menciona_antes() -> None:
    """«DHCP es un protocolo … el servidor DNS» es un hecho de DHCP, no de DNS."""
    materias = catalogo("IV.7")
    assert materias is not None

    dhcp = materia_de(
        "DHCP es un protocolo de aplicación que reparte la configuración, entre ella el DNS.",
        "IV.7.2",
        materias,
    )
    dns = materia_de(
        "El DNS es una base de datos distribuida de nombres, no un protocolo de configuración.",
        "IV.7.2",
        materias,
    )

    assert dhcp.key == "dhcp"
    assert dns.key == "dns"


def test_un_hecho_que_habla_de_un_protocolo_y_de_su_puerto_es_del_protocolo() -> None:
    materias = catalogo("IV.7")
    assert materias is not None

    correo = materia_de(
        "POP3 utiliza el puerto 110 sin cifrado y el 995 con SSL/TLS.",
        "IV.7.2",
        materias,
    )
    assert correo.key == "correo"


def test_cada_hecho_cae_en_un_solo_apartado_y_ninguno_se_pierde() -> None:
    hechos = [
        _hecho("La dirección IPv6 ::1/128 es la de loopback."),
        _hecho("La máscara /27 divide la red en bloques de 32 direcciones."),
        _hecho("ARP obtiene la dirección MAC a partir de la dirección IP."),
        _hecho("POP3 utiliza el puerto 110.", epigrafe="IV.7.2"),
        _hecho("El modelo OSI tiene siete capas.", epigrafe="IV.7.1"),
        _hecho("La integridad referencial exige que la clave ajena exista en la primaria."),
    ]
    indice = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos)

    repartidos = [hecho for apartado in indice.reparto for hecho in apartado.hechos]
    assert len(repartidos) == len(hechos)
    assert {id(hecho) for hecho in repartidos} == {id(hecho) for hecho in hechos}
    assert indice.hechos == len(hechos)


def test_el_reparto_es_el_mismo_si_se_vuelve_a_calcular() -> None:
    hechos = [
        _hecho("ICMP avisa con un mensaje de tiempo excedido cuando el TTL llega a cero."),
        _hecho("El puerto 53 corresponde a DNS."),
        _hecho("UDP no garantiza el orden de los mensajes."),
    ]
    uno = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos)
    otro = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos)

    assert uno.lines() == otro.lines()


def test_un_hecho_de_otro_bloque_cae_en_el_cajon_y_se_cuenta() -> None:
    hechos = [
        _hecho("La máscara /24 deja 254 direcciones utilizables."),
        _hecho("El acoplamiento de control se da cuando los parámetros son de control."),
    ]
    indice = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos)

    assert [hecho.text for hecho in indice.sin_materia] == [
        "El acoplamiento de control se da cuando los parámetros son de control."
    ]
    assert any("Otros contenidos" in linea for linea in indice.lines())


def test_un_hecho_con_el_epigrafe_que_no_era_va_a_la_materia_donde_se_estudia() -> None:
    """El modelo etiquetó una capa de OSI como IV.7.2: su sitio es el modelo OSI, y se dice."""
    hechos = [
        _hecho("La capa de presentación se encarga del cifrado y del formato.", epigrafe="IV.7.2")
    ]
    indice = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos)

    por_materia = {apartado.materia.key: apartado for apartado in indice.reparto}
    assert len(por_materia["osi-modelo"].hechos) == 1
    assert len(indice.fuera_de_su_epigrafe) == 1
    assert any("otro epígrafe" in linea for linea in indice.lines())


def test_un_hecho_de_un_epigrafe_que_no_esta_en_el_catalogo_se_dice() -> None:
    with pytest.raises(ValueError, match="no está en el temario"):
        indice_de(
            topic_code="IV.7",
            topic_title="TCP/IP",
            epigraphs=(("IV.7.1", "Uno"),),
            hechos=(),
        )


# --- las preguntas y el orden ---------------------------------------------------------------------


def test_las_preguntas_se_reparten_por_su_enunciado_y_no_por_sus_opciones() -> None:
    """Las opciones traen los distractores: clasificar por ellas manda la pregunta a otro sitio."""
    grupo = _grupo("q1", "¿Qué protocolo resuelve los nombres de dominio?")

    reparto = repartir_grupos([grupo], _materias())

    assert len(reparto["dns"]) == 1
    assert all(not reparto[clave] for clave in reparto if clave != "dns")


def test_el_indice_va_en_el_orden_del_temario_y_cuenta_sus_preguntas() -> None:
    hechos = [
        _hecho("SSH usa el puerto 22 y va cifrado."),
        _hecho("DNS utiliza el puerto 53 para las consultas."),
        _hecho("El puerto 829 corresponde a CMP."),
    ]
    reparto = repartir_hechos(hechos, _materias())

    assert reparto["gestion"], "SSH es de la materia de acceso remoto"
    assert reparto["dns"], "el hecho habla de DNS"
    assert reparto["puertos"], "un número de puerto sin protocolo del tema es de la tabla"

    indice = indice_de(
        topic_code="IV.7",
        topic_title="TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=hechos,
        grupos=[_grupo("q1", "¿Qué protocolo resuelve los nombres de dominio?")],
    )

    claves = [apartado.materia.key for apartado in indice.reparto]
    assert claves.index("direccionamiento-ipv4") < claves.index("subredes") < claves.index("dns")
    # La tabla de puertos se enseña antes que DNS (es el orden del temario) y, aun así, el hecho de
    # DNS está en DNS: el orden del índice y el del reparto son dos decisiones distintas.
    assert claves.index("puertos") < claves.index("dns")
    assert len(next(a for a in indice.reparto if a.materia.key == "dns").hechos) == 1
    assert indice.preguntas == 1
    assert any("grupo(s) de preguntas" in linea for linea in indice.lines())


def test_el_indice_no_repite_la_cabecera_de_sus_apartados() -> None:
    """Un índice por materias no puede caer en el defecto que va a arreglar: 19 títulos iguales."""
    indice = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=())

    titulos = [apartado.materia.title for apartado in indice.reparto]
    assert len(set(titulos)) == len(titulos)

    revision = revisar_apuntes(
        [
            _Apartado(
                key=apartado.materia.key,
                title=apartado.materia.title,
                anchor=apartado.materia.key,
                body_markdown="",
            )
            for apartado in indice.reparto
        ]
    )
    assert CABECERAS_REPETIDAS not in {hallazgo.codigo for hallazgo in revision.hallazgos}
