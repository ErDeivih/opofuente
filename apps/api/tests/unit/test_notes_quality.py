"""Las comprobaciones de forma de los apuntes, sin red y sin base de datos.

Lo que se comprueba aquí es lo que la revisión del propietario encontró en los tres pilotos: que
el mismo apartado esté escrito dos veces (encabezados repetidos), que se hayan quedado marcas
internas a la vista (`[fact 23]`), que haya tablas sin cabecera o con una columna sin nombre, que
el texto repita párrafos y que un tema se estire muy por encima de los hechos que tiene.

Cada comprobación se prueba por los dos lados: el texto que **no** pasa y el que sí, porque una
comprobación que lo marca todo no sirve para decidir nada.
"""

from __future__ import annotations

from dataclasses import dataclass

from opofuente.domain.notes_quality import (
    CABECERAS_REPETIDAS,
    DENSIDAD,
    ENCABEZADOS_REPETIDOS,
    MARCAS_INTERNAS,
    MAX_PALABRAS_POR_HECHO,
    MINIMO_PALABRAS_PARRAFO,
    NOMBRE_COLUMNA_SIN_TITULO,
    PARRAFOS_REPETIDOS,
    TABLAS_SIN_CABECERA,
    encabezados,
    hechos_distintos,
    limpiar_andamios,
    marcas_internas,
    nombrar_columnas_sin_titulo,
    parecido,
    parrafos,
    quitar_encabezado_repetido,
    revisar_apuntes,
    sin_encabezados_repetidos_en_el_tema,
    tablas_rotas,
    trigramas,
)
from opofuente.domain.topic_notes import FactKind, Hecho


@dataclass(frozen=True)
class _Apartado:
    """Lo mínimo que cumple el protocolo de un apartado: dónde está y qué dice."""

    key: str
    title: str
    anchor: str
    body_markdown: str


def _hecho(texto: str) -> Hecho:
    return Hecho(
        text=texto,
        kind=FactKind.TECNICO,
        epigraph_code="IV.7.2",
        fact_id=texto[:12],
    )


def _codigos(apartados: list[_Apartado], hechos: list[Hecho] | None = None) -> set[str]:
    return {hallazgo.codigo for hallazgo in revisar_apuntes(apartados, hechos or []).hallazgos}


# --- la medida de parecido ------------------------------------------------------------------------


def test_el_parecido_por_trigramas_ordena_lo_igual_y_lo_distinto() -> None:
    assert parecido("El modelo OSI tiene siete capas.", "El modelo OSI tiene siete capas.") == 1.0
    assert parecido("El modelo OSI tiene siete capas.", "La receta de la tortilla") < 0.2
    assert trigramas("ab") == frozenset({"ab"})
    assert trigramas("") == frozenset()


# --- los encabezados repetidos --------------------------------------------------------------------


def test_los_encabezados_casi_iguales_dentro_del_tema_se_cuentan_como_repetidos() -> None:
    """Es el defecto de IV.7: siete apartados seguidos explicando el modelo OSI."""
    apartados = [
        _Apartado(
            key="iv-7-1-1",
            title="Modelo OSI y modelo TCP/IP: capas y protocolos",
            anchor="iv-7-1-1",
            body_markdown="## 1. Las siete capas\n\nEl modelo OSI tiene siete capas.\n",
        ),
        _Apartado(
            key="iv-7-1-2",
            title="OSI y TCP/IP: capas, servicios y protocolos",
            anchor="iv-7-1-2",
            body_markdown="### 1. Las siete capas\n\nOtra vez, de otra manera.\n",
        ),
    ]

    revision = revisar_apuntes(apartados)

    codigos = {hallazgo.codigo for hallazgo in revision.hallazgos}
    assert ENCABEZADOS_REPETIDOS in codigos
    assert not revision.pasa


def test_un_tema_con_encabezados_distintos_no_lo_marca() -> None:
    apartados = [
        _Apartado(
            key="iv-7-2-1",
            title="Direccionamiento IPv4 y clases",
            anchor="iv-7-2-1",
            body_markdown="## Clases de direcciones\n\nLa clase A empieza por 1.\n",
        ),
        _Apartado(
            key="iv-7-2-2",
            title="Subredes y máscaras",
            anchor="iv-7-2-2",
            body_markdown="## Máscara de red\n\nLa máscara /24 deja 254 hosts.\n",
        ),
    ]

    assert ENCABEZADOS_REPETIDOS not in _codigos(apartados)


def test_los_encabezados_se_leen_con_su_nivel() -> None:
    assert encabezados("# Uno\n### Tres\nsin almohadilla\n## Dos") == (
        (1, "Uno"),
        (3, "Tres"),
        (2, "Dos"),
    )


def test_el_titulo_del_apartado_repetido_en_su_propio_texto_no_cuenta() -> None:
    """Un apartado bien titulado empieza por su título: eso no es un apartado escrito dos veces."""
    apartados = [
        _Apartado(
            key="iv-7-2-1",
            title="Direccionamiento IPv4 y clases",
            anchor="iv-7-2-1",
            body_markdown="## Direccionamiento IPv4 y clases\n\nLa clase A empieza por 1.\n",
        )
    ]

    assert ENCABEZADOS_REPETIDOS not in _codigos(apartados)


def test_muchos_apartados_con_la_misma_cabecera_es_un_hallazgo() -> None:
    """El defecto de IV.7.2: 19 apartados titulados «Protocolos TCP/IP: …», uno por lote de hechos.

    Son títulos **distintos** (por eso el encabezado repetido no los ve): lo que se repite es la
    cabecera y lo que significa es que el epígrafe se partió en trozos.
    """
    apartados = [
        _Apartado(
            key=f"iv-7-2-{numero}",
            title=f"Protocolos TCP/IP: {cola}",
            anchor=f"iv-7-2-{numero}",
            body_markdown=f"Texto del apartado {numero}.",
        )
        for numero, cola in enumerate(
            ("puertos y servicios", "direccionamiento e ICMP", "IPv4, IPv6 y subredes"), start=1
        )
    ]

    revision = revisar_apuntes(apartados)
    cabeceras = next(
        hallazgo for hallazgo in revision.hallazgos if hallazgo.codigo == CABECERAS_REPETIDAS
    )

    assert cabeceras.cuenta == 3
    assert "protocolos tcp ip" in cabeceras.line()
    # Los tres títulos son distintos: la comprobación de encabezado repetido, sola, no los vería.
    assert ENCABEZADOS_REPETIDOS not in {hallazgo.codigo for hallazgo in revision.hallazgos}


def test_un_encabezado_del_cuerpo_que_repite_el_titulo_de_otro_apartado_se_quita() -> None:
    """La puerta mide los encabezados de **todo** el tema, y el título de un apartado es uno más.

    Medido en I.2: el apartado `cortes-funciones` llevaba dentro un `### Defensor del Pueblo` (el
    epígrafe de las atribuciones que la Constitución da a las Cortes sobre él) y el tema tiene
    además un apartado titulado «El Defensor del Pueblo». Para la puerta son el mismo encabezado dos
    veces, y con razón: son dos apartados con el mismo nombre. Se quita **el encabezado del cuerpo**
    —el texto que lleva debajo se queda— porque el nombre del apartado lo pone el esquema, no el
    redactor.
    """
    textos = (
        "## Composición y funciones\n\nLas Cortes nombran al Defensor del Pueblo.\n"
        "\n### Defensor del Pueblo\n\nSu designación corresponde a las Cortes.\n",
        "## Qué es\n\nEs un alto comisionado de las Cortes Generales.\n",
    )
    titulos = ("Atribuciones de las Cortes Generales", "El Defensor del Pueblo")

    limpios = sin_encabezados_repetidos_en_el_tema(textos, titulos=titulos)

    assert "Defensor del Pueblo" not in [titulo for _nivel, titulo in encabezados(limpios[0])], (
        limpios[0]
    )
    # El texto que llevaba debajo sigue ahí: se quita el encabezado, no el contenido.
    assert "Su designación corresponde a las Cortes." in limpios[0]
    # Y el título del propio apartado no se toca.
    assert "## Composición y funciones" in limpios[0]
    assert limpios[1] == textos[1]


def test_dos_apartados_con_la_misma_cabecera_no_son_un_hallazgo() -> None:
    """Con dos no se puede hablar de un epígrafe partido: haría falta el tercero."""
    apartados = [
        _Apartado(
            key="iv-7-2-1",
            title="Protocolos TCP/IP: puertos",
            anchor="iv-7-2-1",
            body_markdown="Texto uno.",
        ),
        _Apartado(
            key="iv-7-2-2",
            title="Protocolos TCP/IP: ICMP",
            anchor="iv-7-2-2",
            body_markdown="Texto dos.",
        ),
    ]

    assert CABECERAS_REPETIDAS not in _codigos(apartados)


# --- las marcas internas --------------------------------------------------------------------------


def test_las_marcas_internas_se_cuentan_una_vez_cada_una() -> None:
    """`[fact 26]` es una marca, no dos: la cuenta tiene que poder compararse con la suya."""
    texto = "Un párrafo con la marca [fact 26] dentro y otra fact 7 suelta."

    assert marcas_internas(texto) == ("[fact 26]", "fact 7")
    assert MARCAS_INTERNAS in _codigos(
        [_Apartado(key="iv-7-2-11", title="IP", anchor="iv-7-2-11", body_markdown=texto)]
    )


def test_las_palabras_que_solo_empiezan_por_fact_no_son_marcas() -> None:
    texto = "El factor de forma y la facturación no son marcas internas, y factible tampoco."

    assert marcas_internas(texto) == ()


def test_el_comentario_de_fuentes_a_la_vista_tambien_es_una_marca() -> None:
    assert marcas_internas("<!-- fuentes: BOE -->") == ("<!-- fuentes",)


def test_limpiar_andamios_quita_las_marcas_y_deja_la_frase_legible() -> None:
    """Lo que el redactor copia de su encargo (el número del hecho) no son apuntes.

    El caso es el de IV.7: `[[Hecho 36]]` en medio de un párrafo de encaminamiento.
    """
    texto = (
        "…reenvían tramas basándose en direcciones MAC. [[Hecho 36]] La **ruta por defecto** es la "
        "entrada que se usa para reenviar los paquetes."
    )

    limpio = limpiar_andamios(texto)

    assert marcas_internas(limpio) == ()
    assert "  " not in limpio, "el hueco de la marca no puede quedar como dos espacios"
    assert "MAC. La" in limpio, "la frase sigue leyéndose"
    assert "reenvían tramas basándose en direcciones MAC" in limpio


def test_limpiar_andamios_no_toca_un_texto_limpio() -> None:
    texto = "El modelo OSI tiene siete capas.\n\n| Capa | Función |\n| --- | --- |\n| 1 | Bits |\n"

    assert limpiar_andamios(texto) == texto


def test_el_apartado_que_se_titula_parafraseandose_no_cuenta_como_repetido() -> None:
    """El redactor titula con el mismo texto que se le dio, a veces con una palabra cambiada.

    Es el caso de `dhcp` en IV.7: su cuerpo empieza por «DHCP y configuración automática» y el
    apartado se llama «DHCP y la configuración automática». Eso es titulares, no repetirse; la
    **segunda** vez que aparece sí cuenta.
    """
    apartado = _Apartado(
        key="dhcp",
        title="DHCP y la configuración automática",
        anchor="dhcp",
        body_markdown=(
            "## DHCP y configuración automática\n\nLo que hace DHCP.\n"
            "\n## Formas de asignación\n\nManual y dinámica.\n"
        ),
    )

    revision = revisar_apuntes([apartado])

    assert revision.pasa, [hallazgo.line() for hallazgo in revision.hallazgos]


def test_el_apartado_que_repite_su_titulo_dentro_si_mismo_si_cuenta() -> None:
    apartado = _Apartado(
        key="dhcp",
        title="DHCP y la configuración automática",
        anchor="dhcp",
        body_markdown=(
            "## DHCP y la configuración automática\n\nLo que hace DHCP.\n"
            "\n## DHCP y la configuración automática\n\nOtra vez.\n"
        ),
    )

    revision = revisar_apuntes([apartado])

    assert ENCABEZADOS_REPETIDOS in {hallazgo.codigo for hallazgo in revision.hallazgos}


# --- las tablas -----------------------------------------------------------------------------------


def test_una_tabla_sin_linea_de_separacion_no_tiene_cabecera() -> None:
    texto = "| Clase | Primer octeto | Uso |\n| A | 1-126 | Grandes |\n"

    rotas = tablas_rotas("iv-7-2-18", texto)

    assert len(rotas) == 1
    assert "sin fila de cabecera" in rotas[0].motivo
    assert TABLAS_SIN_CABECERA in _codigos(
        [_Apartado(key="iv-7-2-18", title="TCP/IP", anchor="iv-7-2-18", body_markdown=texto)]
    )


def test_una_columna_sin_nombre_en_la_cabecera_se_detecta() -> None:
    """Es el caso de I.1: treinta tablas con la primera columna sin titular."""
    texto = "| | Artículo | Contenido |\n|---|---|---|\n| 1 | 14 | Igualdad |\n"

    rotas = tablas_rotas("i-1-1-1", texto)

    assert any("columna(s) sin nombre" in rota.motivo for rota in rotas)


def test_una_fila_con_mas_celdas_que_la_cabecera_es_una_columna_sin_nombre() -> None:
    """`| 137 | NetBIOS Name Service | NTP |` con una cabecera de dos columnas."""
    texto = (
        "| Puerto | Servicio |\n"
        "|---|---|\n"
        "| 137 | NetBIOS Name Service | NTP |\n"
        "| 139 | NetBIOS Session Service | NTP |\n"
    )

    rotas = tablas_rotas("iv-7-2-1", texto)

    assert len(rotas) == 2, "las dos filas enseñan una columna que nadie ha titulado"
    assert all("3 celda(s) y una cabecera de 2 columna(s)" in rota.motivo for rota in rotas)
    assert [rota.fila for rota in rotas] == [3, 4]


def test_una_columna_de_tabla_sin_titulo_se_nombra_y_deja_de_estar_rota() -> None:
    """La tabla de comparación se escribe con la primera columna sin titular, y así no se lee.

    Es el defecto que tenía I.1 en cuatro apartados: `| | Ordinario (art. 167) | Agravado (art. 168)
    |` con los conceptos debajo. La reparación toca **la cabecera** y solo la celda vacía: una
    columna que sí tiene nombre se queda como está, y los datos no se tocan.
    """
    con_hueco = (
        "| | Ordinario (art. 167) | Agravado (art. 168) |\n"
        "|---|---|---|\n"
        "| Supuestos | Cualquier reforma | Revisión total |\n"
    )
    entera = "| Concepto | Puerto | Servicio |\n|---|---|---|\n| Correo | 25 | SMTP |\n"
    assert tablas_rotas("constitucion-caracteres-1", con_hueco), "de entrada está rota"

    reparada = nombrar_columnas_sin_titulo(con_hueco)

    assert not tablas_rotas("constitucion-caracteres-1", reparada)
    assert NOMBRE_COLUMNA_SIN_TITULO in reparada
    assert "| Supuestos | Cualquier reforma | Revisión total |" in reparada, "los datos no se tocan"
    assert nombrar_columnas_sin_titulo(entera) == entera, "una tabla que está bien no se toca"
    assert nombrar_columnas_sin_titulo("Sin tablas por aquí.") == "Sin tablas por aquí."


def test_una_tabla_bien_hecha_no_se_marca() -> None:
    texto = "| Puerto | Servicio |\n|---|---|\n| 53 | DNS |\n"

    assert tablas_rotas("iv-7-2-1", texto) == ()


# --- los párrafos repetidos -----------------------------------------------------------------------


def _parrafo(marca: str) -> str:
    return (
        f"El modelo OSI tiene siete capas y cada una tiene su función dentro de la comunicación "
        f"entre sistemas abiertos, y esto se explica en el apartado {marca} de los apuntes."
    )


def test_un_parrafo_repetido_se_cuenta_y_supera_el_tope() -> None:
    apartados = [
        _Apartado(
            key="iv-7-1-1",
            title="El modelo OSI",
            anchor="iv-7-1-1",
            body_markdown="\n\n".join(
                _parrafo(nombre) for nombre in ("uno", "dos", "tres", "cuatro")
            ),
        )
    ]

    revision = revisar_apuntes(apartados)

    assert revision.parrafos == 4
    assert revision.parrafos_repetidos == 3
    assert revision.porcentaje_repetidos > 0.05
    assert PARRAFOS_REPETIDOS in {hallazgo.codigo for hallazgo in revision.hallazgos}


def test_parrafos_distintos_no_se_marcan() -> None:
    apartados = [
        _Apartado(
            key="iv-7-2-3",
            title="IPv6",
            anchor="iv-7-2-3",
            body_markdown=(
                "La dirección multicast link-local all routers es FF02::2 y se usa para hablar "
                "con todos los encaminadores del enlace.\n\n"
                "El prefijo fc00::/7 identifica las direcciones locales únicas y no se enruta "
                "fuera de la organización que las usa.\n\n"
                "La cabecera básica de IPv6 mide cuarenta octetos y no lleva suma de "
                "verificación, a diferencia de la de IPv4.\n"
            ),
        )
    ]

    assert PARRAFOS_REPETIDOS not in _codigos(apartados)


def test_los_parrafos_cortos_no_cuentan_para_la_repeticion() -> None:
    """«Sí.» y «Ver arriba.» se parecen a cualquier cosa y no dicen nada de la redacción."""
    assert MINIMO_PALABRAS_PARRAFO > 2
    cortos = "\n\n".join(["Sí.", "Sí.", "Sí.", "Sí."])

    assert parrafos(cortos) == ("Sí.", "Sí.", "Sí.", "Sí.")
    assert PARRAFOS_REPETIDOS not in _codigos(
        [_Apartado(key="x", title="X", anchor="x", body_markdown=cortos)]
    )


# --- la densidad ----------------------------------------------------------------------------------


def test_un_tema_que_se_estira_mucho_mas_que_sus_hechos_no_pasa() -> None:
    hechos = [
        _hecho(f"Hecho número {numero} del tema, con su contenido propio.") for numero in range(3)
    ]
    largo = " ".join(f"palabra{numero}" for numero in range(MAX_PALABRAS_POR_HECHO * 3 + 1))

    revision = revisar_apuntes(
        [_Apartado(key="i-1-1", title="La Constitución", anchor="i-1-1", body_markdown=largo)],
        hechos,
    )

    densidad = next(hallazgo for hallazgo in revision.hallazgos if hallazgo.codigo == DENSIDAD)
    assert revision.limite_palabras == MAX_PALABRAS_POR_HECHO * 3
    assert densidad.cuenta == revision.palabras - revision.limite_palabras


def test_un_tema_dentro_del_tope_de_densidad_no_se_marca() -> None:
    hechos = [
        _hecho(f"Hecho número {numero} del tema, con su contenido propio.") for numero in range(10)
    ]
    texto = " ".join(f"palabra{numero}" for numero in range(MAX_PALABRAS_POR_HECHO * 10))

    assert DENSIDAD not in _codigos(
        [_Apartado(key="i-1-1", title="La Constitución", anchor="i-1-1", body_markdown=texto)],
        hechos,
    )


def test_sin_hechos_no_hay_tope_de_densidad_que_aplicar() -> None:
    """Un tema sin hechos guardados no se puede juzgar por densidad: se calla, no se inventa."""
    apartado = _Apartado(key="x", title="X", anchor="x", body_markdown=" ".join(["palabra"] * 500))

    assert DENSIDAD not in _codigos([apartado], [])
    assert hechos_distintos([]) == 0


def test_dos_hechos_con_las_mismas_palabras_son_uno() -> None:
    iguales = [
        _hecho("El modelo OSI tiene siete capas."),
        _hecho("el modelo osi tiene siete capas"),
    ]

    assert hechos_distintos(iguales) == 1


# --- el tema entero -------------------------------------------------------------------------------


def test_un_tema_limpio_pasa_y_lo_dice() -> None:
    apartados = [
        _Apartado(
            key="iv-7-2-1",
            title="Direccionamiento IPv4 y clases",
            anchor="iv-7-2-1",
            body_markdown=(
                "## Clases de direcciones\n\n"
                "El primer octeto decide la clase: la A empieza por 1 y la B por 128.\n\n"
                "| Clase | Primer octeto |\n|---|---|\n| A | 1-126 |\n| B | 128-191 |\n"
            ),
        )
    ]
    hechos = [_hecho("El primer octeto decide la clase de una dirección IPv4.")]

    revision = revisar_apuntes(apartados, hechos)

    assert revision.pasa
    assert revision.hallazgos == ()
    assert "PASA" in revision.lines()[0]
    assert revision.apartados == 1
    assert revision.hechos == 1


def test_el_informe_de_la_revision_dice_lo_que_no_pasa_y_donde() -> None:
    apartados = [
        _Apartado(
            key="iv-7-2-11",
            title="IP",
            anchor="iv-7-2-11",
            body_markdown="Un párrafo con la marca [fact 23] dentro del texto de los apuntes.",
        )
    ]

    lineas = revisar_apuntes(apartados).lines()

    assert "NO PASA" in lineas[0]
    assert any(MARCAS_INTERNAS[:8] in linea or "[fact 23]" in linea for linea in lineas[1:])


def test_al_anadido_se_le_quita_el_encabezado_que_el_apartado_ya_tiene() -> None:
    """El defecto que se vio en IV.7: el añadido titulaba con un encabezado que ya estaba.

    La plantilla del añadido le pide empezar con `### ` y un título corto, y el redactor titula con
    el nombre de un subapartado que ya existe. El tema acababa con «Cabecera IPv6» dos veces y la
    revisión de encabezados repetidos lo decía, con razón. Se quita **el encabezado**, no su texto.
    """
    ya_escrito = (
        "## 5. La cabecera IPv6\n\nLa cabecera básica tiene 40 bytes.\n\n"
        "### Cabecera IPv6\n\nEl campo Hop Limit sustituye al TTL."
    )
    anadido = "### Cabecera IPv6\n\nEl campo Traffic Class ocupa 8 bits y sustituye al ToS de IPv4."

    limpio = quitar_encabezado_repetido(ya_escrito, anadido)

    assert not limpio.startswith("###")
    assert "Traffic Class ocupa 8 bits" in limpio
    revision = revisar_apuntes(
        [_Apartado("iv7-ipv6", "IPv6", "iv7-ipv6", ya_escrito + "\n\n" + limpio)]
    )
    assert ENCABEZADOS_REPETIDOS not in {hallazgo.codigo for hallazgo in revision.hallazgos}


def test_un_anadido_con_un_encabezado_nuevo_se_queda_como_esta() -> None:
    """Si el título del añadido no estaba, es un subapartado nuevo y se queda."""
    ya_escrito = "## 5. La cabecera IPv6\n\nLa cabecera básica tiene 40 bytes."
    anadido = "### Fragmentación y MTU\n\nIPv6 no fragmenta en los routers."

    assert quitar_encabezado_repetido(ya_escrito, anadido) == anadido


def test_sin_texto_previo_no_se_toca_nada() -> None:
    """Un añadido sobre un apartado vacío no tiene nada con lo que chocar."""
    anadido = "### Cabecera IPv6\n\nEl campo Hop Limit sustituye al TTL."

    assert quitar_encabezado_repetido("", anadido) == anadido
