"""La tabla de puertos: partida por familias y sin las notas que solo dicen lo que un puerto no es.

Es el arreglo §2.1.2 del objetivo, tal como lo pidió el propietario leyendo IV.7: en la tabla
sobraban «6000 X11 — No es DynamoDB» y «3000 Grafana — No es MySQL» —distractores de una pregunta,
no confusiones de estudio— y la tabla era una sola lista de 47 filas. Lo que se comprueba aquí es
que la tabla se parte por familias, que las notas de distractor se van, que las que explican el
puerto se quedan, y que las confusiones de verdad acaban en su bloque aparte.
"""

from __future__ import annotations

from dataclasses import dataclass

from opofuente.domain.notes_quality import (
    FAMILIAS_DE_PUERTOS,
    NOTAS_DE_PUERTOS,
    revisar_apuntes,
)
from opofuente.domain.puertos import (
    FAMILIAS,
    es_confusion_real,
    familia_de_un_titulo,
    familias_de_la_tabla,
    limpiar_tabla_de_puertos,
    notas_sin_sentido,
    puertos_repetidos,
    tablas_de_puertos,
)

#: La tabla tal como la escribió el modelo en IV.7: una sola tabla y notas con distractores.
TABLA_DE_IV7 = """La siguiente tabla recoge los puertos que conviene tener identificados:

| Puerto / transporte | Servicio | Notas |
|---|---|---|
| 25/TCP | SMTP tradicional | El 465 y el 587 funcionan como alternativas |
| 80/TCP | HTTP | No es Telnet |
| 110/TCP | POP3 sin cifrar | — |
| 465/TCP | SMTPS, SMTP sobre SSL/TLS | Alternativa al 25; no es FTPS (ese es el 990) |
| 587/TCP | SMTP submission (MSA) | Envío de mensajes por el cliente, con STARTTLS |
| 995/TCP | POP3S, POP3 sobre TLS/SSL | No es IMAP4 |
| 3306/TCP | MySQL y MariaDB | — |
| 546/UDP | Cliente DHCPv6 | El servidor DHCPv6 escucha en el 547, no en el 546 |
| 547/UDP | Servidor DHCPv6 | — |
| 6000/TCP | Servidor X11 | No es DynamoDB |
| 27017/TCP | MongoDB | — |

Y con eso se repasa.
"""


@dataclass(frozen=True)
class _Apartado:
    key: str
    title: str
    anchor: str
    body_markdown: str


def test_una_tabla_de_puertos_se_parte_por_familias() -> None:
    """La tabla deja de ser una lista larga: una tabla por familia, cada una con su encabezado."""
    limpieza = limpiar_tabla_de_puertos(TABLA_DE_IV7)

    tablas = tablas_de_puertos(limpieza.texto)
    familias = familias_de_la_tabla(limpieza.texto)

    assert len(tablas) >= 3, "una tabla de 45 filas no se memoriza: tiene que ir por familias"
    assert "" not in familias, "cada tabla tiene que decir de qué familia es"
    assert set(familias) <= {familia.key for familia in FAMILIAS}
    # Y ninguna fila se pierde ni se duplica al partirla.
    de_partida = tablas_de_puertos(TABLA_DE_IV7)[0].filas
    assert sum(len(tabla.filas) for tabla in tablas) == len(de_partida)
    assert puertos_repetidos(limpieza.texto) == ()


def test_cada_fila_cae_en_su_familia() -> None:
    """El reparto por familias es el del temario: correo con correo, bases de datos con bases."""
    limpieza = limpiar_tabla_de_puertos(TABLA_DE_IV7)

    por_familia = {
        familia_de_un_titulo(tabla.titulo): {fila.puerto for fila in tabla.filas}
        for tabla in tablas_de_puertos(limpieza.texto)
    }

    assert por_familia["servicios-de-red"] >= {80, 546, 547}
    assert por_familia["correo"] >= {25, 110, 465, 587, 995}
    assert por_familia["bases-de-datos"] >= {3306, 27017}
    assert por_familia["escritorio-remoto"] >= {6000}


def test_las_notas_que_solo_dicen_lo_que_un_puerto_no_es_se_van() -> None:
    """La prueba del propietario: «6000 X11 — No es DynamoDB» no puede quedar en la tabla."""
    antes = notas_sin_sentido(TABLA_DE_IV7)
    limpieza = limpiar_tabla_de_puertos(TABLA_DE_IV7)

    assert len(antes) >= 3, "el texto de partida tiene los distractores que hay que quitar"
    assert limpieza.notas_retiradas >= 3
    assert notas_sin_sentido(limpieza.texto) == ()
    assert "No es DynamoDB" not in limpieza.texto
    assert "No es MySQL" not in limpieza.texto
    assert "No es IMAP4" not in limpieza.texto
    assert "No es Telnet" not in limpieza.texto
    # Y se dice qué se ha ido, con su puerto delante: un arreglo que no se cuenta no se revisa.
    assert any("6000" in descartada for descartada in limpieza.descartadas)
    assert any("995" in descartada for descartada in limpieza.descartadas)


def test_una_nota_que_explica_el_puerto_se_queda() -> None:
    """Lo que la nota tiene que hacer: explicar el puerto. Eso no se toca."""
    limpieza = limpiar_tabla_de_puertos(TABLA_DE_IV7)

    filas = {
        fila.puerto: fila for tabla in tablas_de_puertos(limpieza.texto) for fila in tabla.filas
    }

    assert "SSL/TLS" in filas[465].nota or "Alternativa al 25" in filas[465].nota
    assert "547" in filas[546].nota, "el contraste cliente/servidor explica el puerto: se queda"
    assert filas[3306].servicio == "MySQL y MariaDB"


def test_una_confusion_de_verdad_va_a_su_bloque_aparte() -> None:
    """El par que se confunde de verdad —546 y 547, 465 y 587— no se pierde: va a su lista."""
    limpieza = limpiar_tabla_de_puertos(TABLA_DE_IV7)

    assert "Confusiones que caen" in limpieza.texto
    assert any("546" in confusion and "547" in confusion for confusion in limpieza.confusiones)
    assert any("465" in confusion for confusion in limpieza.confusiones)


def test_una_confusion_que_no_lo_es_no_se_declara() -> None:
    """MySQL frente a Oracle no es una confusión de estudio: es un distractor, y no se lista."""
    assert not es_confusion_real(3306, 1521, "MySQL y MariaDB", "Oracle Database")
    assert not es_confusion_real(6000, 8000, "Servidor X11", "DynamoDB, versión local de AWS")
    assert not es_confusion_real(5900, 5938, "VNC, primera pantalla", "TeamViewer")
    # Y las cuatro que sí: mismo servicio con y sin cifrar, cliente y servidor, control y datos y
    # números parecidos del mismo servicio.
    assert es_confusion_real(110, 995, "POP3 sin cifrar", "POP3S, POP3 sobre TLS/SSL")
    assert es_confusion_real(25, 465, "SMTP tradicional", "SMTPS, SMTP sobre SSL/TLS")
    assert es_confusion_real(546, 547, "Cliente DHCPv6", "Servidor DHCPv6")
    assert es_confusion_real(20, 21, "FTP, canal de datos", "FTP, canal de control")


def test_la_puerta_de_forma_exige_la_tabla_partida_y_sin_notas_de_distractor() -> None:
    """La comprobación automática: sin arreglar, no pasa; arreglada, pasa."""
    sin_arreglar = revisar_apuntes([_Apartado("puertos", "Puertos", "puertos", TABLA_DE_IV7)])
    codigos = {hallazgo.codigo for hallazgo in sin_arreglar.hallazgos}

    assert NOTAS_DE_PUERTOS in codigos, (
        "una nota de distractor en la tabla no puede pasar la puerta"
    )
    assert FAMILIAS_DE_PUERTOS in codigos, "una tabla sin partir no puede pasar la puerta"

    limpieza = limpiar_tabla_de_puertos(TABLA_DE_IV7)
    arreglado = revisar_apuntes([_Apartado("puertos", "Puertos", "puertos", limpieza.texto)])

    assert NOTAS_DE_PUERTOS not in {hallazgo.codigo for hallazgo in arreglado.hallazgos}
    assert FAMILIAS_DE_PUERTOS not in {hallazgo.codigo for hallazgo in arreglado.hallazgos}


def test_un_texto_sin_tabla_de_puertos_no_se_toca() -> None:
    """La limpieza es de la tabla de puertos y de nada más: el resto de los apuntes no se toca."""
    texto = "Una tabla cualquiera:\n\n| Concepto | Qué es |\n|---|---|\n| OSI | un modelo |\n"

    limpieza = limpiar_tabla_de_puertos(texto)

    assert limpieza.texto == texto
    assert limpieza.tablas == 0
    assert revisar_apuntes([_Apartado("x", "X", "x", texto)]).pasa
