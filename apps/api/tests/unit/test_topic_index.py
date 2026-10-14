"""El índice por materias de un tema (el esquema antes de redactar), sin red y sin base de datos.

Lo que se comprueba es lo que tiene que sostener el índice para que sirva de algo:

- **todo hecho cae en un apartado** (nada se pierde por el camino) y un hecho **va al apartado de lo
  que afirma**, no al de la pregunta de la que sale: el apartado de UDP no habla de la cabecera de
  IPv6, ni de ARP, ni de ICMP;
- una pregunta puede tener sus hechos en **varios** apartados: el ancla pregunta→apuntes los admite
  todos;
- **los hechos repetidos se agrupan**: se queda uno por grupo, con la unión de las preguntas de todo
  el grupo, y dos hechos con siglas o cifras distintas **no** se agrupan aunque se parezcan;
- el reparto es **determinista**: los mismos hechos dan el mismo índice;
- **la tabla de puertos tiene un solo sitio** y está marcado;
- un hecho que habla de dos materias va a la que menciona **antes** (DNS y el puerto 53 es DNS), y
  una palabra que aparece en media asignatura (`datagrama`, una `IP` suelta) no le gana a una que es
  de una materia y de una sola;
- un hecho que no es de ninguna materia del tema **no cae en ningún cajón**: se cuenta y se dice, y
  se va con sus preguntas a la cola de clasificación;
- el modelo OSI se reparte en sus cuatro partes por lo que dice cada hecho;
- el orden del índice es el del temario, no el de reparto.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from opofuente.domain.notes_quality import CABECERAS_REPETIDAS, revisar_apuntes
from opofuente.domain.topic_index import (
    APARTADO_MUY_GRANDE,
    Materia,
    catalogo,
    deduplicar,
    etiquetas,
    grupos_equivalentes,
    indice_de,
    materia_de,
    plan_de,
    repartir_grupos,
    repartir_hechos,
    revisar_indice,
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


def _hecho(
    texto: str,
    *,
    epigrafe: str = "IV.7.2",
    grupos: tuple[str, ...] = (),
    fact_id: str = "",
) -> Hecho:
    return Hecho(
        text=texto,
        kind=FactKind.TECNICO,
        epigraph_code=epigrafe,
        source_groups=grupos,
        source_questions=(),
        fact_id=fact_id or texto[:12],
    )


def _grupo(identificador: str, enunciado: str, *, epigrafe: str | None = "IV.7.2") -> QuestionGroup:
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


def test_el_catalogo_de_iv7_cubre_sus_dos_epigrafes_y_no_tiene_cajones() -> None:
    """Los dos cajones de revisión **no se quedan** en el tema: lo que no es de aquí se va."""
    materias = _materias()
    validar_catalogo("IV.7", materias)

    assert {materia.epigraph_code for materia in materias} == {"IV.7.1", "IV.7.2"}
    assert [materia.key for materia in materias if materia.es_cajon] == []


def test_el_modelo_osi_esta_partido_en_sus_cuatro_partes() -> None:
    """Qué es OSI, las siete capas, las unidades de datos y los dispositivos: cuatro apartados."""
    materias = _materias()
    osi = [materia.key for materia in materias if materia.familia == "osi"]

    assert osi == ["osi-que-es", "osi-capas", "osi-unidades", "osi-dispositivos"]
    assert not any(materia.key == "osi-modelo" for materia in materias)


def test_el_acceso_remoto_y_el_directorio_son_dos_apartados() -> None:
    """El apartado 20 se parte: Telnet/SSH/RDP por un lado y LDAP/SNMP por otro."""
    claves = [materia.key for materia in _materias()]

    assert "acceso-remoto" in claves
    assert "directorio-y-gestion" in claves
    assert "gestion" not in claves


def test_los_protocolos_que_no_son_tcp_ip_no_van_a_otros_protocolos() -> None:
    """IPX/SPX y NetBEUI no son de la familia TCP/IP: se nombran al comparar familias."""
    materias = _materias()
    otros = next(materia for materia in materias if materia.key == "otros-protocolos")
    arquitectura = next(materia for materia in materias if materia.key == "tcpip-arquitectura")

    assert not any("ipx" in patron for patron in otros.patrones)
    assert not any("netbeui" in patron for patron in otros.patrones)
    assert any("ipx" in patron for patron in arquitectura.patrones)


def test_la_tabla_de_puertos_tiene_un_solo_sitio_y_esta_marcado() -> None:
    con_tabla = [materia for materia in _materias() if materia.tabla_unica]

    assert len(con_tabla) == 1, "una tabla que sale dos veces es justo lo que hay que impedir"
    assert con_tabla[0].key == "puertos"


def test_un_catalogo_con_dos_cajones_en_el_mismo_epigrafe_se_rechaza() -> None:
    dos_cajones = (
        Materia(key="uno", epigraph_code="IV.7.1", title="Uno", resumen=""),
        Materia(key="dos", epigraph_code="IV.7.1", title="Dos", resumen=""),
    )
    with pytest.raises(ValueError, match="cajones"):
        validar_catalogo("IV.7", dos_cajones)


def test_un_catalogo_sin_cajon_es_valido() -> None:
    """Sin cajón no hay dónde esconder lo que no casa: se cuenta y se dice (el caso de IV.7)."""
    sin_cajon = (
        Materia(
            key="uno", epigraph_code="IV.7.1", title="Uno", resumen="", patrones=(r"\balgo\b",)
        ),
    )
    validar_catalogo("IV.7", sin_cajon)


def test_un_catalogo_con_la_misma_clave_dos_veces_se_rechaza() -> None:
    repetido = (
        Materia(key="uno", epigraph_code="IV.7.1", title="Uno", resumen=""),
        Materia(key="uno", epigraph_code="IV.7.1", title="Otra vez", resumen=""),
    )
    with pytest.raises(ValueError, match="repetidas"):
        validar_catalogo("IV.7", repetido)


def test_un_tema_sin_catalogo_no_tiene_indice() -> None:
    """I.9 todavía no tiene catálogo: sin catálogo no hay índice, y eso se dice, no se inventa.

    El tema del ejemplo es uno de los que siguen sin catálogo: cuando se le escriba el suyo, esta
    prueba tiene que cambiar de tema y **no** de expectativa —lo que comprueba es que un tema sin
    catálogo no tiene índice, no cuál es ese tema—. IV.2 e I.2 fueron el ejemplo antes de que se les
    definiera el suyo, que es exactamente lo que le pasará a este.
    """
    assert catalogo("I.9") is None
    with pytest.raises(KeyError):
        indice_de(topic_code="I.9", topic_title="La Constitución", epigraphs=EPIGRAFES)


# --- el catálogo de I.1 (la estructura de la norma) -----------------------------------------------


def test_el_catalogo_de_i_1_sigue_la_estructura_de_la_constitucion() -> None:
    """I.1 es normativo: sus apartados son la norma (Título Preliminar, Título I, garantía, Corona).

    Los órganos que la Constitución crea (Cortes, Gobierno, Poder Judicial, Tribunal Constitucional,
    organización territorial y economía) no tienen epígrafe propio en el temario: van a `I.1.1`, que
    es el epígrafe de la Constitución entera. Es la decisión que ya estaba tomada y que este
    aplica.
    """
    materias = catalogo("I.1")
    assert materias is not None
    validar_catalogo("I.1", materias)

    assert {materia.epigraph_code for materia in materias} == {
        "I.1.1",
        "I.1.2",
        "I.1.3",
        "I.1.4",
    }
    assert len(materias) == 15
    # Los órganos viven en I.1.1, que es el epígrafe de la Constitución entera.
    de_la_constitucion = {materia.key for materia in materias if materia.epigraph_code == "I.1.1"}
    assert de_la_constitucion == {
        "constitucion-caracteres",
        "titulo-preliminar",
        "cortes-generales",
        "gobierno-y-administracion",
        "relaciones-gobierno-cortes",
        "poder-judicial",
        "economia-y-hacienda",
        "organizacion-territorial",
    }
    # La Corona es su propio epígrafe, y la garantía y la suspensión el suyo.
    assert [m.key for m in materias if m.epigraph_code == "I.1.4"] == ["corona"]
    assert [m.key for m in materias if m.epigraph_code == "I.1.3"] == [
        "garantias-y-defensor",
        "suspension-de-derechos",
    ]
    # Y ninguno se recoge en un cajón de «otros»: lo que no case se dice, no se esconde.
    assert [materia.key for materia in materias if materia.es_cajon] == []


def test_las_autonomicas_se_llaman_de_las_dos_maneras_y_las_dos_cuentan() -> None:
    """`Autónomas` y `autonómicas` son la misma cosa, y el patrón tiene que aceptar las dos.

    La normalización del proyecto quita los acentos, así que un patrón escrito solo con
    «autonómicas» deja sin materia a todas las preguntas que digan «Comunidades Autónomas» —que es
    como lo escribe media oposición, y como lo escribía el banco real—.
    """
    materias = catalogo("I.1")
    assert materias is not None

    por_las_autonomicas = materia_de(
        "¿Cuántas Comunidades Autónomas son históricas en España?", None, materias
    )
    por_lo_autonomico = materia_de(
        "El Estado se organiza territorialmente en municipios y entes autonómicos.", None, materias
    )

    assert por_las_autonomicas is not None
    assert por_las_autonomicas.key == "organizacion-territorial"
    assert por_lo_autonomico is not None
    assert por_lo_autonomico.key == "organizacion-territorial"


# --- las preguntas que no dicen de qué hablan -----------------------------------------------------


def test_una_pregunta_que_no_dice_de_que_habla_va_a_la_materia_de_sus_hechos() -> None:
    """«Una de las siguientes afirmaciones es falsa» no dice de qué va; sus hechos sí.

    Es la mitad del arreglo de I.1: 209 de sus grupos son enunciados cortos sin artículo ni
    institución, y forzar un patrón por cada muletilla de examen sería escribir un diccionario de
    comodines. Lo que sabe de qué hablan son sus hechos, así que manda la mayoría de ellos.
    """
    grupo = _grupo("q1", "Una de las siguientes afirmaciones es falsa:")
    hechos = [
        _hecho("DNS utiliza el puerto 53 para las consultas.", grupos=(grupo.signature,)),
        _hecho(
            "El registro MX de DNS identifica el servidor de correo.", grupos=(grupo.signature,)
        ),
        _hecho("SSH usa el puerto 22.", grupos=(grupo.signature,)),
    ]

    reparto, sin_materia, por_sus_hechos = repartir_grupos(
        [grupo],
        _materias(),
        hechos_por_grupo={grupo.signature: hechos},
    )

    assert sin_materia == []
    assert por_sus_hechos == 1
    assert [g.signature for g in reparto["dns"]] == [grupo.signature]


def test_un_grupo_sin_enunciado_ni_hechos_que_reconozcan_nada_se_queda_sin_materia() -> None:
    """Si ni el enunciado ni los hechos dicen de qué va, no se inventa: va a la bandeja.

    Lo que **no** puede pasar es que acabe en un cajón de «otros»: la pregunta necesita que el
    propietario la mire, y eso se le dice.
    """
    grupo = _grupo("q1", "Señale la respuesta correcta:")
    hechos = [_hecho("El plazo de resolución es de tres meses.", grupos=(grupo.signature,))]

    reparto, sin_materia, por_sus_hechos = repartir_grupos(
        [grupo],
        _materias(),
        hechos_por_grupo={grupo.signature: hechos},
    )

    assert sin_materia == [grupo]
    assert por_sus_hechos == 0
    assert all(not suyos for suyos in reparto.values())


# --- las comprobaciones del índice (§2.2.3) -------------------------------------------------------


def test_el_indice_mide_un_apartado_de_mas_de_ciento_cincuenta_hechos() -> None:
    """Un apartado de trescientos hechos no cabe en una llamada: el plan lo parte y deja de serlo.

    La comprobación se mide sobre el **plan** y no sobre el catálogo, así que lo que denuncia es un
    apartado que no se ha partido; con el plan que usa la corrida, pasa.
    """
    hechos = [
        _hecho(f"DNS utiliza el puerto {53 + indice} para las consultas.", grupos=("f",))
        for indice in range(200)
    ]
    indice = indice_de(
        topic_code="IV.7",
        topic_title="Modelo TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=hechos,
        grupos=[_grupo("q1", "¿Qué protocolo resuelve los nombres de dominio?")],
        umbral_equivalencia=1.1,
    )
    sin_partir = plan_de(indice, max_hechos_por_apartado=0)
    partido = plan_de(indice, max_hechos_por_apartado=150)

    revision_sin_partir = revisar_indice(indice, sin_partir)
    revision_partido = revisar_indice(indice, partido)

    assert [hallazgo.codigo for hallazgo in revision_sin_partir.hallazgos] == [APARTADO_MUY_GRANDE]
    assert not revision_sin_partir.pasa
    assert revision_partido.pasa
    assert len(partido) == 2, "200 hechos con tope 150 son dos apartados de la misma materia"


def test_el_indice_cuenta_las_preguntas_que_no_puede_situar() -> None:
    """Lo que no cabe en el árbol no invalida el árbol, pero se cuenta: va a la bandeja."""
    grupo = _grupo("q1", "Señale la respuesta correcta:")
    indice = indice_de(
        topic_code="IV.7",
        topic_title="Modelo TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=[],
        grupos=[grupo],
    )

    revision = revisar_indice(indice, ())

    assert revision.pasa, "el árbol está bien; el defecto es de la pregunta"
    assert revision.grupos_sin_materia == 1
    assert revision.preguntas_sin_materia == 1
    assert "bandeja del propietario" in "\n".join(revision.lines())


# --- la deduplicación de los hechos repetidos -----------------------------------------------------


def test_dos_hechos_iguales_con_otras_palabras_son_uno() -> None:
    """El defecto del modelo OSI: la misma capa explicada cinco veces con otras palabras."""
    hechos = [
        _hecho(
            "La capa de presentación del modelo OSI se ocupa de la representación, el formato y la "
            "sintaxis de los datos: codificación estándar, compresión y cifrado.",
            epigrafe="IV.7.1",
        ),
        _hecho(
            "La capa de presentación del modelo OSI se ocupa de la representación de los datos: "
            "codificación y conversión de formatos, compresión y cifrado.",
            epigrafe="IV.7.1",
        ),
    ]

    quedan = deduplicar(hechos)

    assert len(quedan) == 1
    assert "presentación" in quedan[0].text


def test_el_hecho_que_se_queda_conserva_las_preguntas_de_todo_el_grupo() -> None:
    """Lo que hace que ninguna pregunta se quede sin anclaje: la unión de sus preguntas."""
    hechos = [
        _hecho(
            "La capa de presentación se ocupa de la representación, el formato y la sintaxis de "
            "los datos: codificación, compresión y cifrado.",
            grupos=("firma-uno",),
            epigrafe="IV.7.1",
        ),
        _hecho(
            "La capa de presentación se ocupa de la representación de los datos: codificación y "
            "conversión de formatos, compresión y cifrado.",
            grupos=("firma-dos",),
            epigrafe="IV.7.1",
        ),
    ]

    quedan = deduplicar(hechos)

    assert len(quedan) == 1
    assert set(quedan[0].source_groups) == {"firma-uno", "firma-dos"}


def test_dos_hechos_con_siglas_distintas_no_se_agrupan() -> None:
    """`LLC` no es `MAC` y `TPDU` no es `APDU`: la guarda de las etiquetas."""
    llc = _hecho(
        "La subcapa LLC se encarga del control del enlace lógico y de la construcción de tramas.",
        epigrafe="IV.7.1",
    )
    mac = _hecho(
        "La subcapa MAC se encarga del control de acceso al medio físico, no del enlace lógico.",
        epigrafe="IV.7.1",
    )
    tpdu = _hecho(
        "La unidad de datos intercambiada en la capa de transporte es la TPDU.",
        epigrafe="IV.7.1",
    )
    apdu = _hecho(
        "La unidad de datos de la capa de aplicación del modelo OSI es la APDU.",
        epigrafe="IV.7.1",
    )

    assert etiquetas(llc.text) == frozenset({"llc"})
    assert etiquetas(mac.text) == frozenset({"mac"})
    assert len(grupos_equivalentes([llc, mac])) == 2
    assert len(grupos_equivalentes([tpdu, apdu])) == 2


def test_dos_hechos_con_cifras_distintas_no_se_agrupan() -> None:
    """Un hecho del puerto 53 no es uno del 80, aunque se digan con las mismas palabras."""
    cincuenta_y_tres = _hecho("El servidor DNS escucha en el puerto 53 de la red local.")
    ochenta = _hecho("El servidor HTTP escucha en el puerto 80 de la red local.")

    assert "#53" in etiquetas(cincuenta_y_tres.text)
    assert "#80" in etiquetas(ochenta.text)
    assert len(grupos_equivalentes([cincuenta_y_tres, ochenta])) == 2


def test_la_deduplicacion_no_quita_ninguna_pregunta_de_su_apartado() -> None:
    """La prueba que pidió el propietario: ninguna pregunta pierde su apartado al deduplicar."""
    grupos = [
        _grupo("q1", "¿Qué hace la capa de presentación del modelo OSI?"),
        _grupo("q2", "¿De qué se encarga la capa de presentación?"),
    ]
    hechos = [
        _hecho(
            "La capa de presentación se ocupa de la representación, el formato y la sintaxis de "
            "los datos: codificación, compresión y cifrado.",
            grupos=(grupos[0].signature,),
            epigrafe="IV.7.1",
        ),
        _hecho(
            "La capa de presentación se ocupa de la representación de los datos: codificación y "
            "conversión de formatos, compresión y cifrado.",
            grupos=(grupos[1].signature,),
            epigrafe="IV.7.1",
        ),
    ]

    sin_dedup = indice_de(
        topic_code="IV.7",
        topic_title="TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=hechos,
        grupos=grupos,
        umbral_equivalencia=2.0,
    )
    con_dedup = indice_de(
        topic_code="IV.7",
        topic_title="TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=hechos,
        grupos=grupos,
    )

    assert con_dedup.hechos < sin_dedup.hechos, "los repetidos se tienen que agrupar"
    assert con_dedup.grupos_sin_anclaje == ()
    for apartado in con_dedup.reparto:
        firmas = {grupo.signature for grupo in apartado.grupos}
        ancladas = apartado.firmas_de_grupo
        assert firmas <= ancladas, f"una pregunta de «{apartado.materia.key}» se quedó sin hecho"


def test_el_indice_dice_cuantos_hechos_habia_y_cuantos_quedan() -> None:
    hechos = [
        _hecho(
            "El orden de las capas del modelo OSI, de abajo arriba, es: física, enlace de datos, "
            "red, transporte, sesión, presentación y aplicación.",
            epigrafe="IV.7.1",
        ),
        _hecho(
            "Las siete capas del modelo OSI, de abajo hacia arriba, son: física, enlace de datos, "
            "red, transporte, sesión, presentación y aplicación.",
            epigrafe="IV.7.1",
        ),
    ]

    indice = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos)

    assert indice.hechos_originales == 2
    assert indice.hechos == 1
    assert len(indice.fusionados) == 1
    assert any("de 2" in linea and "1 repetido" in linea for linea in indice.lines())


# --- el reparto por materia y no por pregunta ------------------------------------------------


def _indice_con_udp() -> tuple[object, QuestionGroup]:
    """El caso del propietario: una pregunta sobre UDP cuyos hechos hablan de otras materias.

    Es el defecto que se arregla: el reparto iba por **la pregunta de la que sale el hecho**, así
    que el apartado de UDP acabó hablando de la cabecera de IPv6, de ARP y de ICMP —los
    distractores de esa pregunta— en vez de lo que afirma cada hecho.
    """
    grupo = _grupo(
        "q-udp", "¿Cuál de las siguientes afirmaciones es correcta respecto del protocolo UDP?"
    )
    firma = grupo.signature
    hechos = [
        _hecho(
            "UDP es un protocolo no orientado a conexión que no garantiza la entrega ni el orden.",
            grupos=(firma,),
        ),
        _hecho("La cabecera básica de IPv6 tiene longitud fija de 40 bytes.", grupos=(firma,)),
        _hecho(
            "ARP se usa para obtener la dirección MAC del router, no la del sistema final.",
            grupos=(firma,),
        ),
        _hecho(
            "ICMP permite reportar al origen errores en el procesamiento o envío de datagramas IP.",
            grupos=(firma,),
        ),
    ]
    indice = indice_de(
        topic_code="IV.7",
        topic_title="TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=hechos,
        grupos=[grupo],
    )
    return indice, grupo


def test_un_hecho_va_al_apartado_de_su_materia_y_no_al_de_su_pregunta() -> None:
    """La prueba del propietario: el apartado de UDP **no** habla de IPv6, de ARP ni de ICMP."""
    indice, _grupo_udp = _indice_con_udp()
    por_clave = {apartado.materia.key: apartado for apartado in indice.reparto}  # type: ignore[attr-defined]

    udp = [hecho.text for hecho in por_clave["udp"].hechos]
    assert len(udp) == 1
    assert "UDP es un protocolo no orientado a conexión" in udp[0]
    for ajeno in ("IPv6", "ARP", "ICMP"):
        assert not any(ajeno in texto for texto in udp), (
            f"el apartado de UDP sigue hablando de {ajeno}: el hecho va donde se afirma, no donde "
            "se pregunta"
        )
    assert [hecho.text for hecho in por_clave["ipv6"].hechos] == [
        "La cabecera básica de IPv6 tiene longitud fija de 40 bytes."
    ]
    assert [hecho.text for hecho in por_clave["arp"].hechos] == [
        "ARP se usa para obtener la dirección MAC del router, no la del sistema final."
    ]
    assert [hecho.text for hecho in por_clave["icmp"].hechos] == [
        "ICMP permite reportar al origen errores en el procesamiento o envío de datagramas IP."
    ]


def test_una_pregunta_puede_anclarse_en_varios_apartados() -> None:
    """El ancla pregunta→apuntes admite varios: sus hechos están repartidos por materia."""
    indice, grupo = _indice_con_udp()

    apartados = indice.apartados_de(grupo.signature)  # type: ignore[attr-defined]

    assert set(apartados) == {"udp", "ipv6", "arp", "icmp"}, (
        "el ancla de una pregunta reúne los apartados donde están sus hechos, no solo uno"
    )
    assert apartados.index("ipv6") < apartados.index("icmp"), "y van en orden de lectura"


def test_ninguna_pregunta_se_queda_con_un_hecho_sin_apartado() -> None:
    """La prueba del §2.1.1, tal como quedó: «ninguna pregunta con algún hecho sin apartado»."""
    indice, grupo = _indice_con_udp()

    assert indice.grupos_sin_anclaje == ()  # type: ignore[attr-defined]
    # Y un hecho de otro bloque, sin apartado, sí se cuenta: es un hecho huérfano.
    ajeno = _grupo("q-ajeno", "El acoplamiento de control se da entre módulos.")
    suelto = _hecho(
        "El acoplamiento de control se da cuando los parámetros que se pasan son de control.",
        grupos=(ajeno.signature,),
    )
    indice_suelto = indice_de(
        topic_code="IV.7",
        topic_title="TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=[*indice.reparto[0].hechos, suelto],  # type: ignore[attr-defined]
        grupos=[grupo, ajeno],
    )

    assert indice_suelto.grupos_sin_anclaje == (ajeno.signature,)


def test_una_palabra_que_esta_en_media_asignatura_no_le_gana_a_la_de_una_materia() -> None:
    """`datagrama` y una `IP` suelta son débiles: la cabecera de IPv4 no es un hecho de UDP."""
    materias = _materias()

    cabecera = materia_de(
        "En la cabecera del datagrama IPv4, el campo Posición del Fragmento tiene 13 bits.",
        "IV.7.2",
        materias,
    )
    localhost = materia_de(
        "Un datagrama dirigido a una dirección 127.x.x.x se devuelve al remitente: 127.0.0.1 es "
        "localhost.",
        "IV.7.2",
        materias,
    )
    # Y el débil sigue sirviendo cuando no hay nada propio: la pregunta del término «datagrama».
    termino = materia_de(
        "Se denomina datagrama al paquete de datos en la capa de:", "IV.7.2", materias
    )
    # Y lo que sí es de IP, y no de ninguna materia concreta, cae en IPv4.
    protocolo_ip = materia_de(
        "El protocolo IP es un protocolo no orientado a conexión y de mejor esfuerzo.",
        "IV.7.2",
        materias,
    )

    assert cabecera is not None and cabecera.key == "direccionamiento-ipv4"
    assert localhost is not None and localhost.key == "direcciones-especiales"
    assert termino is not None and termino.key == "udp"
    assert protocolo_ip is not None and protocolo_ip.key == "direccionamiento-ipv4"


# --- el reparto -----------------------------------------------------------------------------------


def test_un_hecho_va_a_la_materia_que_menciona_antes() -> None:
    """«DHCP es un protocolo … el servidor DNS» es un hecho de DHCP, no de DNS."""
    materias = _materias()

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

    assert dhcp is not None and dhcp.key == "dhcp"
    assert dns is not None and dns.key == "dns"


def test_un_hecho_que_habla_de_un_protocolo_y_de_su_puerto_es_del_protocolo() -> None:
    correo = materia_de(
        "POP3 utiliza el puerto 110 sin cifrado y el 995 con SSL/TLS.",
        "IV.7.2",
        _materias(),
    )

    assert correo is not None and correo.key == "correo"


def test_el_reparto_del_modelo_osi_es_por_asunto_y_no_por_la_primera_palabra() -> None:
    """Cada hecho del OSI va a su parte: la unidad, el dispositivo, la capa o el modelo."""
    materias = _materias()

    ejemplos = {
        "osi-unidades": "En el modelo OSI, la PDU de la capa de enlace de datos es la trama.",
        "osi-dispositivos": (
            "Los switches o conmutadores conmutan tramas en la capa 2 del modelo OSI, no en la 3."
        ),
        "osi-capas": "La capa de sesión (capa 5 del modelo OSI) controla el diálogo entre pares.",
        "osi-que-es": (
            "Para ISO, un sistema abierto es el que cumple las normas OSI al comunicarse."
        ),
    }

    for clave, texto in ejemplos.items():
        materia = materia_de(texto, "IV.7.1", materias)
        assert materia is not None and materia.key == clave, f"«{texto[:40]}» no es de {clave}"


def test_un_hecho_de_otro_bloque_no_cae_en_ningun_apartado_y_se_dice() -> None:
    """Sin cajones: un hecho de otro bloque se cuenta, se enseña y para la corrida."""
    hechos = [
        _hecho("La máscara /24 deja 254 direcciones utilizables."),
        _hecho("El acoplamiento de control se da cuando los parámetros son de control."),
    ]
    indice = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos)

    assert [hecho.text for hecho in indice.sin_materia] == [
        "El acoplamiento de control se da cuando los parámetros son de control."
    ]
    assert indice.hechos == 1
    assert any("NO tienen apartado" in linea for linea in indice.lines())
    assert not any("Otros contenidos" in linea for linea in indice.lines())


def test_un_hecho_cuyas_preguntas_no_son_del_tema_se_va_con_ellas() -> None:
    """«Sus datos se van con ellas»: el hecho de una pregunta mal clasificada no se queda."""
    grupo = _grupo("q1", "El acoplamiento de control se da entre módulos.")
    hecho = _hecho(
        "El acoplamiento de control se da cuando los parámetros que se pasan son de control.",
        grupos=(grupo.signature,),
    )
    indice = indice_de(
        topic_code="IV.7",
        topic_title="TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=[hecho],
        grupos=[grupo],
    )

    assert indice.hechos == 0
    assert [suyo.text for suyo in indice.sin_materia] == [hecho.text]
    assert len(indice.grupos_sin_materia) == 1


def test_un_hecho_con_el_epigrafe_que_no_era_va_a_la_materia_donde_se_estudia() -> None:
    """El modelo etiquetó una capa de OSI como IV.7.2: su sitio es el modelo OSI, y se dice."""
    indice = indice_de(
        topic_code="IV.7",
        topic_title="TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=[
            _hecho(
                "La capa de presentación se encarga del cifrado y del formato.",
                epigrafe="IV.7.2",
            )
        ],
    )

    por_materia = {apartado.materia.key: apartado for apartado in indice.reparto}
    assert len(por_materia["osi-capas"].hechos) == 1
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


def test_el_reparto_no_depende_de_la_deduplicacion() -> None:
    """Dos hechos equivalentes se reparten por su texto: agruparlos no mueve a nadie de sitio."""
    hechos = [
        _hecho("El puerto 53 corresponde a DNS."),
        _hecho("El servidor DNS escucha en el puerto 53."),
    ]

    sin_dedup = indice_de(
        topic_code="IV.7",
        topic_title="TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=hechos,
        umbral_equivalencia=2.0,
    )
    con_dedup = indice_de(
        topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos
    )

    def claves(indice: object) -> dict[str, int]:
        return {
            apartado.materia.key: len(apartado.hechos)
            for apartado in indice.reparto  # type: ignore[attr-defined]
            if apartado.hechos
        }

    assert set(claves(sin_dedup)) == set(claves(con_dedup))


# --- las preguntas y el orden ---------------------------------------------------------------------


def test_las_preguntas_se_reparten_por_su_enunciado_y_no_por_sus_opciones() -> None:
    """Las opciones traen los distractores: clasificar por ellas manda la pregunta a otro sitio."""
    grupo = _grupo("q1", "¿Qué protocolo resuelve los nombres de dominio?")

    reparto, sin_materia, por_sus_hechos = repartir_grupos([grupo], _materias())

    assert len(reparto["dns"]) == 1
    assert all(not reparto[clave] for clave in reparto if clave != "dns")
    assert sin_materia == []
    assert por_sus_hechos == 0, "este grupo se sitúa por su enunciado, no por sus hechos"


def test_el_indice_va_en_el_orden_del_temario_y_cuenta_sus_preguntas() -> None:
    hechos = [
        _hecho("SSH usa el puerto 22 y va cifrado."),
        _hecho("DNS utiliza el puerto 53 para las consultas."),
        _hecho("El puerto 829 corresponde a CMP."),
    ]
    reparto, _sin_materia, _por_su_pregunta = repartir_hechos(hechos, _materias())

    assert reparto["acceso-remoto"], "SSH es de la materia de acceso remoto"
    assert reparto["dns"], "el hecho habla de DNS"
    assert reparto["puertos"], "un número de puerto sin protocolo del tema es de la tabla"

    indice = indice_de(
        topic_code="IV.7",
        topic_title="TCP/IP",
        epigraphs=EPIGRAFES,
        hechos=[*hechos, _hecho("La sincronización de tiempo se hace con NTP.")],
        grupos=[_grupo("q1", "¿Qué protocolo resuelve los nombres de dominio?")],
    )

    claves = [apartado.materia.key for apartado in indice.reparto]
    assert claves.index("direccionamiento-ipv4") < claves.index("subredes") < claves.index("dns")
    # La tabla de puertos se enseña antes que DNS (es el orden del temario) y, aun así, el hecho de
    # DNS está en DNS: el orden del índice y el del reparto son dos decisiones distintas.
    assert claves.index("puertos") < claves.index("dns")
    assert claves.index("acceso-remoto") < claves.index("directorio-y-gestion")
    assert len(next(a for a in indice.reparto if a.materia.key == "dns").hechos) == 1
    assert indice.preguntas == 1
    assert any("grupo(s) de preguntas" in linea for linea in indice.lines())


def test_el_plan_de_redaccion_es_un_apartado_por_materia_y_solo_las_que_tienen_hechos() -> None:
    """Lo que se redacta sale del índice aprobado: ni trozos de cuarenta ni apartados vacíos."""
    hechos = [
        _hecho("El puerto 53 corresponde a DNS."),
        _hecho("El puerto 80 corresponde a HTTP."),
    ]
    indice = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos)

    plan = plan_de(indice)

    assert [seccion.key for seccion in plan] == ["puertos"]
    assert [seccion.position for seccion in plan] == [1]
    assert len(plan[0].facts) == 2


def test_el_plan_parte_una_materia_muy_grande_en_trozos_numerados_de_la_misma_materia() -> None:
    hechos = [
        _hecho(f"El puerto {numero} está registrado en la IANA.") for numero in range(1024, 1030)
    ]
    indice = indice_de(topic_code="IV.7", topic_title="TCP/IP", epigraphs=EPIGRAFES, hechos=hechos)

    plan = plan_de(indice, max_hechos_por_apartado=3)

    assert [seccion.key for seccion in plan] == ["puertos-1", "puertos-2"]
    assert all(seccion.epigraph_code == "IV.7.2" for seccion in plan)
    assert sum(len(seccion.facts) for seccion in plan) == len(hechos)


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


# --- el sitio donde acaba un hecho tiene que ser suyo (F25b y F25c) -------------------------------

#: Los tres epígrafes oficiales de I.3, tal como los declara su convocatoria.
EPIGRAFES_I_3 = (
    ("I.3.1", "El Gobierno: composición, nombramiento y cese."),
    ("I.3.2", "Las funciones del Gobierno."),
    ("I.3.3", "Relaciones entre el Gobierno y las Cortes Generales."),
)


def test_un_hecho_sin_materia_no_se_sienta_en_el_apartado_de_su_pregunta() -> None:
    """La red de seguridad de `repartir_hechos` deja de sentar hechos en apartados ajenos.

    Un hecho que **no nombra ninguna materia** del tema se caía al apartado de la pregunta de la que
    salía «para no perderlo». Eso sitúa el hecho por **de dónde vino la pregunta**, no por lo que el
    hecho dice, y es la puerta por la que el material de otro tema se sentó dentro de un tema. Hoy
    no se sienta en ninguno: va a `sin_materia` (no se pierde), se cuenta y su pregunta va a la
    bandeja.
    """
    grupo = _grupo("q1", "¿Qué protocolo resuelve los nombres de dominio?")
    ajeno = _hecho(
        "El acoplamiento de control se da cuando los parámetros que se pasan son de control.",
        grupos=(grupo.signature,),
    )

    reparto, sin_materia, de_su_pregunta = repartir_hechos(
        [ajeno], _materias(), materia_por_grupo={grupo.signature: "dns"}
    )

    assert all(not suyos for suyos in reparto.values()), (
        "no se sienta en ningún apartado, ni siquiera en el de su pregunta"
    )
    assert [hecho.text for hecho in sin_materia] == [ajeno.text]
    assert [hecho.text for hecho in de_su_pregunta] == [ajeno.text], (
        "y se cuenta: es la medida del arreglo"
    )


def test_el_material_del_cpd_de_i_3_no_se_sienta_en_ningun_apartado_y_va_a_la_bandeja() -> None:
    """El caso medido del CPD en I.3, como prueba de regresión de este arreglo.

    El grupo del estándar **ANSI/TIA-942-B** de la zona de un CPD no trae epígrafe y ningún patrón
    de I.3 lo sitúa; sus dos hechos llevan el epígrafe I.3.1 que les puso el modelo, y por eso el
    cajón `i-3-1-otros` —que recoge todo lo de su epígrafe— los recogía, y con esas anclas el grupo
    quedaba sentado ahí con sus **5 respuestas contadas como cubiertas**. Medido entonces (`F25b`):
    1 apartado de 15, 2 hechos de 300, 730 caracteres y 5 preguntas de 181.

    Hoy ni el cajón reconoce nada ni hay red que los recoja: el grupo no cabe en ninguna materia del
    tema (va a la bandeja con su motivo) y sus hechos no se sientan en ningún apartado.
    """
    grupo = _grupo(
        "cpd",
        "Según el estándar ANSI/TIA 942-B, la zona de un Centro de Procesamiento de Datos donde se "
        "ubican elementos finales, como un servidor o un mainframe, se denomina:",
        epigrafe=None,
    )
    hechos = [
        _hecho(
            "Según el estándar ANSI/TIA-942, la zona del Centro de Procesamiento de Datos donde se "
            "ubican los elementos finales, como servidores o mainframes, se denomina MDA.",
            epigrafe="I.3.1",
            grupos=(grupo.signature,),
        ),
        _hecho(
            "En el mismo estándar, el MDA (Main Distribution Area) alberga la distribución "
            "principal (router, backbone de red, conmutador principal).",
            epigrafe="I.3.1",
            grupos=(grupo.signature,),
        ),
    ]

    indice = indice_de(
        topic_code="I.3",
        topic_title="El Gobierno",
        epigraphs=EPIGRAFES_I_3,
        hechos=hechos,
        grupos=[grupo],
    )

    assert [suyo.signature for suyo in indice.grupos_sin_materia] == [grupo.signature], (
        "el grupo no cabe en ninguna materia y va a la bandeja del propietario con su motivo"
    )
    assert indice.hechos == 0, "y sus hechos no sostienen ningún apartado del tema"
    assert [hecho.text for hecho in indice.sin_materia] == [hecho.text for hecho in hechos]
    assert indice.apartados_de(grupo.signature) == ()
    assert indice.apartados_propios_de(grupo.signature) == (), (
        "no tiene apartado propio: ninguno de los del tema es el suyo"
    )


def test_un_hecho_sin_materia_no_se_sienta_en_el_cajon_de_su_epigrafe() -> None:
    """El cajón de un epígrafe **no reconoce** nada: recoge, y aquí no recoge hechos.

    El cajón existe para las preguntas con epígrafe oficial y sin sujeto —su sitio es el de las
    otras cuestiones de ese epígrafe—, pero un hecho no se sitúa por el epígrafe que le puso el
    modelo: si no nombra nada, el cajón tampoco es suyo. Es lo que sentó el material del CPD en I.3.
    """
    grupo = _grupo("q1", "Señale la afirmación verdadera", epigrafe="I.3.1")
    hecho = _hecho(
        "El MDA alberga la distribución principal del centro de procesamiento de datos.",
        epigrafe="I.3.1",
        grupos=(grupo.signature,),
    )

    indice = indice_de(
        topic_code="I.3",
        topic_title="El Gobierno",
        epigraphs=EPIGRAFES_I_3,
        hechos=[hecho],
        grupos=[grupo],
    )

    assert indice.materia_de_grupo(grupo.signature) == "i-3-1-otros", (
        "la pregunta sí es de ese epígrafe: su apartado es el de sus otras cuestiones"
    )
    assert all(
        hecho.text not in [suyo.text for suyo in apartado.hechos] for apartado in indice.reparto
    ), "el hecho no se sienta en el cajón por el epígrafe que le puso el modelo"
    assert indice.apartados_propios_de(grupo.signature) == ("i-3-1-otros",), (
        "y el apartado propio de la pregunta es el de su materia, no el primero del epígrafe"
    )
