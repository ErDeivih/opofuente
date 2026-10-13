"""La ficha de pregunta, sin base de datos: las reglas que deciden qué se puede arreglar (F20).

Cinco grupos de reglas y **todos los casos salen de la copia de la base real**, medidos el 13 de
octubre de 2026. Eso importa: una regla que solo se prueba con un ejemplo inventado pasa la prueba y
falla con los datos, que es lo que pasó con las once preguntas que el bloque del panel dejó marcadas
como reparables y de las que **una** lo es.

Lo que se fija aquí:

1. **quitar la referencia del examen**: se limpia la que quedó pegada al final, se limpian las dos
   seguidas, y **no** se toca un enunciado que habla de un examen en medio ni un párrafo del BOE que
   empieza por un año;
2. **partir la opción fundida**: se parte «JOB 0d) CALL» y **no** se toca «conforme a lo indicado en
   la opción c)», que es una mención y no una fusión. Es la guarda que impide «reparar» una pregunta
   que está bien;
3. **lo que no se repara se explica**: una opción desbordada, un resto sin principio, dos opciones
que
   solo se diferencian en las mayúsculas y una opción que es el principio de otra tienen cada una su
   motivo, porque son cuatro trabajos distintos para el propietario;
4. **una clave oficial no se cambia**: por el tipo del conjunto (`official_exam`) y por el material
de
   origen (una plantilla enlazada a un documento);
5. **una letra que la pregunta no tiene no se escribe**: la comprobación que evita una respuesta
   correcta que nadie puede elegir.
"""

from __future__ import annotations

import pytest

from opofuente.domain.notes_incidents import PATRON_REFERENCIA_PEGADA
from opofuente.domain.question_file import (
    REGLA_OPCION_FUNDIDA,
    REGLA_REFERENCIA_DEL_EXAMEN,
    letras_de_opcion,
    letras_que_no_existen,
    motivo_de_no_reparar,
    normalizar_letras,
    partir_opcion_fundida,
    protege_cambiar_la_clave,
    quitar_referencia_del_examen,
    reparacion_disponible,
)

# --------------------------------------------------------------- 1. la referencia del examen

#: La forma real de la referencia pegada: el año, el cuerpo y su grupo (medida en la copia).
PEGADA = (
    "En awk, la variable predefinida que indica el separador de campos es: "
    "2013 Cuerpo Auxiliar Extremadura - Gr.C"
)


def test_quita_la_referencia_pegada_al_final_y_deja_el_enunciado_entero() -> None:
    """El caso base: lo que el §2 de los ajustes manda limpiar."""
    assert (
        quitar_referencia_del_examen(PEGADA)
        == "En awk, la variable predefinida que indica el separador de campos es:"
    )


def test_quita_las_dos_referencias_cuando_van_seguidas() -> None:
    """Hay preguntas con dos pegadas: cortar solo la última dejaría la primera dentro.

    El caso está medido: «¿qué carácter distingue las directivas de preprocesador? 2016 Técnicos
    Auxiliares Informática Promoción Interna AGE - Gr. C 2016 Técnicos Auxiliares Informática Acceso
    Libre AGE - Gr.C».
    """
    doble = (
        "En programación C, ¿qué carácter distingue las directivas de preprocesador? "
        "2016 Técnicos Auxiliares Informática Promoción Interna AGE - Gr. C "
        "2016 Técnicos Auxiliares Informática Acceso Libre AGE - Gr.C"
    )
    assert (
        quitar_referencia_del_examen(doble)
        == "En programación C, ¿qué carácter distingue las directivas de preprocesador?"
    )


def test_no_toca_un_enunciado_que_habla_de_un_examen_en_medio() -> None:
    """Un año con cuerpo dentro de la frase no es una referencia pegada: es parte de la pregunta."""
    assert (
        quitar_referencia_del_examen(
            "Según la Ley de 2011 Universidades, el plazo para resolver es de tres meses:"
        )
        is None
    )


def test_no_toca_un_parrafo_del_boe_que_empieza_por_un_ano() -> None:
    """La coincidencia de 7.916 caracteres de la copia: no es una referencia, es un párrafo.

        «Versión 11ª de junio 2025 Comunidad Autónoma (regla 15ª), así como en relación con el
        fomento
    de
        la cultura…». Si la guarda no lo rechazara, limpiar el enunciado se llevaría la pregunta
        entera.
    """
    parrafo = (
        "Los términos de la Administración Electrónica. Versión 11ª de junio "
        "2025 Comunidad Autónoma (regla 15ª), así como en relación con el fomento de la "
        "cultura, de "
        "la investigación y, en su caso, de la enseñanza de la lengua de la Comunidad Autónoma."
    )
    assert PATRON_REFERENCIA_PEGADA.search(parrafo) is not None, "el patrón casa, y aun así no vale"
    assert quitar_referencia_del_examen(parrafo) is None


def test_no_quita_nada_cuando_no_hay_referencia() -> None:
    assert quitar_referencia_del_examen("El modelo TCP/IP tiene cuatro capas.") is None
    assert quitar_referencia_del_examen("   ") is None


# --------------------------------------------------------------- 2. la opción fundida


def test_parte_la_opcion_que_se_trago_a_la_siguiente() -> None:
    """El caso medido del examen de JCL: «JOB 0d) CALL» son dos opciones."""
    assert partir_opcion_fundida(["EXEC", "DD", "JOB 0d) CALL"]) == ("EXEC", "DD", "JOB", "CALL")


def test_no_parte_una_opcion_que_nombra_a_otra() -> None:
    """«… indicado en la opción c)» es una mención, no una fusión: la pregunta está bien.

    Es la mitad del hallazgo de esta tanda: siete de las once señales del motor son menciones
    legítimas, y «repararlas» habría partido por la mitad una opción correcta.
    """
    opciones = [
        "Podrá ser ejercitada mediante la remisión a la mesa del Congreso de una "
        "proposición de ley.",
        "Todas las otras respuestas son verdaderas.",
        "En el caso indicado en la opción b) la Asamblea podrá delegar ante el Congreso un "
        "máximo de "
        "cinco miembros para su defensa.",
        "Podrá ser ejercida a través del Gobierno, al que se solicitará una proposición de Ley.",
    ]
    assert partir_opcion_fundida(opciones) is None
    assert (
        partir_opcion_fundida(
            [
                "en presencia de la persona física o de un representante autorizado, o",
                "a distancia, utilizando medios de identificación electrónica, o",
                "por medio de un certificado de una firma electrónica cualificada expedido de "
                "conformidad con la letra a) o b), o",
                "utilizando otros métodos reconocidos a escala nacional.",
            ]
        )
        is None
    )


def test_no_parte_un_resto_al_que_le_falta_el_principio() -> None:
    """«y c)» es un resto: partir por ahí dejaría dos trozos de nada."""
    assert partir_opcion_fundida(["no están sujetos al mismo tipo de protección", "y c)"]) is None


def test_parte_solo_una_opcion_aunque_haya_dos_candidatas() -> None:
    """Partir dos a la vez es demasiado para una regla: si hay dos, hace falta el original."""
    opciones = ["uno 0a) dos", "tres 0b) cuatro"]
    assert partir_opcion_fundida(opciones) == ("uno", "dos", "tres 0b) cuatro")


# --------------------------------------------------------------- 3. lo que no se repara, explicado


def test_la_reparacion_ofrece_las_dos_reglas_cuando_hacen_falta_las_dos() -> None:
    """La pregunta del JCL tiene la referencia pegada **y** la opción fundida: una sola versión."""
    reparacion = reparacion_disponible(
        stem=(
            "¿Cuál NO es una sentencia del lenguaje JCL (Job Control Language)? "
            "2013 Cuerpo de Gestión de Sistemas e Informática de la AGE - Gr.B"
        ),
        opciones=["EXEC", "DD", "JOB 0d) CALL"],
        tipo="single_choice",
    )
    assert reparacion is not None
    assert reparacion.reglas == (REGLA_REFERENCIA_DEL_EXAMEN, REGLA_OPCION_FUNDIDA)
    assert reparacion.stem == "¿Cuál NO es una sentencia del lenguaje JCL (Job Control Language)?"
    assert reparacion.opciones == ("EXEC", "DD", "JOB", "CALL")
    assert "referencia del examen" in reparacion.detalle


def test_una_opcion_que_se_trago_el_documento_no_se_repara_y_se_dice_por_que() -> None:
    """El caso de «Doc Adicional»: la opción C lleva dentro cuatro disposiciones del BOE."""
    opciones = [
        "Los sitios web que reciban financiación pública para su diseño o mantenimiento.",
        "Los sitios web vinculados a la prestación de servicios públicos.",
        "Los sitios web de los centros privados educativos sostenidos con fondos públicos. "
        + "Disposición adicional segunda. Las letras a) o b) de la disposición final. " * 200,
        "L.: M-1/1958 - ISSN: 0212-033X",
    ]
    assert (
        reparacion_disponible(stem="Una pregunta.", opciones=opciones, tipo="single_choice") is None
    )
    motivo = motivo_de_no_reparar(stem="Una pregunta.", opciones=opciones, tipo="single_choice")
    assert motivo is not None
    assert "se llevó el resto del documento" in motivo


def test_una_mencion_a_otra_opcion_se_explica_como_mencion_y_no_como_reparacion() -> None:
    """La pregunta está bien: lo que falla es la regla mecánica, y eso hay que decirlo."""
    opciones = [
        "En dos periodos ordinarios de sesiones, conforme a lo indicado en la opción c).",
        "En un solo periodo ordinario de sesiones, de septiembre a junio.",
        "En dos periodos ordinarios, el primero de septiembre a diciembre.",
        "En dos periodos ordinarios, el primero de septiembre a enero.",
    ]
    motivo = motivo_de_no_reparar(
        stem="Las Cámaras se reunirán anualmente:", opciones=opciones, tipo="single_choice"
    )
    assert motivo is not None
    assert "nombra a otra opción" in motivo


def test_un_resto_sin_principio_se_explica_como_resto() -> None:
    motivo = motivo_de_no_reparar(
        stem="Los archivos de dispositivos en UNIX:",
        opciones=[
            "no están sujetos al mismo tipo de protección de acceso que los archivos ordinarios.",
            "están vacíos y asocian los dispositivos con sus drivers.",
            "sus nombres se pasan a los programas como los de los archivos ordinarios.",
            "y c)",
        ],
        tipo="single_choice",
    )
    assert motivo is not None
    assert "le falta el principio" in motivo


def test_dos_opciones_que_solo_cambian_en_las_mayusculas_no_son_un_resto() -> None:
    """En una pregunta de `LC_COLLATE` esa diferencia **es** el contenido."""
    motivo = motivo_de_no_reparar(
        stem="En LINUX, tenemos la definición de variable LC_COLLATE=C. ¿Qué devuelve el comando?",
        opciones=["AaBbCc", "aAbBcC", "ABC", "AbBcC"],
        tipo="single_choice",
    )
    assert motivo is not None
    assert "mayúsculas" in motivo


def test_una_opcion_que_es_el_principio_de_otra_se_arregla_con_la_clave_no_con_el_texto() -> None:
    motivo = motivo_de_no_reparar(
        stem=(
            "En caso de reforma del Estatuto de Autonomía, la Junta de Andalucía deberá "
            "someterla a referéndum:"
        ),
        opciones=[
            "En un plazo máximo de 6 meses",
            "En un plazo máximo de 6 meses tras ser la reforma ratificada por el Congreso "
            "mediante ley orgánica",
            "En un plazo máximo de 6 meses tras ser la reforma ratificada por las Cortes Generales",
        ],
        tipo="single_choice",
    )
    assert motivo is not None
    assert "marcando la respuesta correcta" in motivo


def test_una_pregunta_sin_problemas_no_tiene_reparacion_ni_motivo() -> None:
    """Sin señal del motor no hay nada que explicar, y la pantalla no inventa un motivo."""
    assert (
        reparacion_disponible(
            stem="El modelo TCP/IP tiene cuatro capas.", opciones=["Sí", "No"], tipo="true_false"
        )
        is None
    )
    assert (
        motivo_de_no_reparar(
            stem="El modelo TCP/IP tiene cuatro capas.", opciones=["Sí", "No"], tipo="true_false"
        )
        is None
    )


def test_una_pregunta_a_la_que_le_faltan_opciones_no_se_puede_inventar_las_que_no_estan() -> None:
    motivo = motivo_de_no_reparar(
        stem="Se inadmitirán a trámite, mediante resolución motivada, las solicitudes:",
        opciones=["Solo una opción con texto"],
        tipo="single_choice",
    )
    assert motivo is not None
    assert "le faltan opciones" in motivo


# --------------------------------------------------------------- 4. la clave oficial


def test_una_clave_de_examen_oficial_no_se_cambia_y_se_dice_por_que() -> None:
    motivo = protege_cambiar_la_clave(set_type="official_exam", tiene_plantilla_enlazada=True)
    assert motivo is not None
    assert "examen oficial" in motivo


def test_una_plantilla_que_viene_de_un_documento_protege_aunque_el_conjunto_no_sea_oficial() -> (
    None
):
    """El otro camino a «oficial»: la plantilla salió de un papel."""
    motivo = protege_cambiar_la_clave(set_type="private_bank", tiene_plantilla_enlazada=True)
    assert motivo is not None
    assert "material de origen" in motivo


def test_un_banco_privado_sin_plantilla_enlazada_se_puede_corregir() -> None:
    assert protege_cambiar_la_clave(set_type="private_bank", tiene_plantilla_enlazada=False) is None


# --------------------------------------------------------------- 5. las letras


def test_las_letras_de_una_pregunta_son_las_de_sus_opciones() -> None:
    assert letras_de_opcion(["uno", "dos", "tres", "cuatro"]) == ("a", "b", "c", "d")


def test_las_letras_se_normalizan_antes_de_compararse() -> None:
    """`["C"]` y `["c"]` son la misma respuesta: si no, la comparación falla por una mayúscula."""
    assert normalizar_letras(["C"]) == ("c",)
    assert normalizar_letras(["B", "a", "b"]) == ("a", "b")
    assert normalizar_letras([]) == ()


def test_una_letra_que_la_pregunta_no_tiene_se_detecta_antes_de_escribir() -> None:
    assert letras_que_no_existen(pedidas=["d"], disponibles=["a", "b", "c"]) == ("d",)
    assert letras_que_no_existen(pedidas=["C"], disponibles=["a", "b", "c"]) == ()
    assert letras_que_no_existen(pedidas=["a", "h"], disponibles=["a", "b"]) == ("h",)


def test_una_reparacion_que_no_cambia_nada_no_es_una_reparacion() -> None:
    """El contrato del dominio: sin texto nuevo no se escribe una versión."""
    from opofuente.domain.question_file import Reparacion

    with pytest.raises(ValueError):
        Reparacion(reglas=(REGLA_REFERENCIA_DEL_EXAMEN,), detalle="nada")
    with pytest.raises(ValueError):
        Reparacion(reglas=(), detalle="nada", stem="algo")
