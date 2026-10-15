"""La bandeja agrupada por conjunto, sin base de datos (F31, §2 del cierre del objetivo).

Lo que se prueba aquí es **la cifra** y **el permiso**, que son las dos cosas que no se pueden
comprobar mirando la pantalla:

- qué cuenta como «una cosa que el propietario tiene que atender» (`entradas_de_decision`),
  que es la medida de éxito del §2.4. Si contara una incidencia por fila, la bandeja parecería
  igual de grande después de agruparla, y agrupar no habría servido de nada;
- qué conjunto admite una acción en bloque. **Un examen oficial no admite ninguna**, y esa decisión
  no se reescribe aquí: la dice `protege_cambiar_la_clave`, la misma que se lee al intentar cambiar
  la clave desde la ficha de la pregunta. La prueba la ata a esa verdad y no a una lista paralela.

Y el estado que deja la resolución automática (`estado_resuelto`), con sus tres casos y el que
**no** se toca, que es el que sigue esperando al propietario.
"""

from __future__ import annotations

from opofuente.domain.notes_incidents import IncidentStatus, estado_resuelto
from opofuente.domain.topic_notes import CategoriaIncidencia
from opofuente.domain.tray import (
    ACCIONES,
    TrayAction,
    TraySection,
    TraySet,
    acciones_permitidas,
    agrupar,
    rechazo_de_accion,
)


def _conjunto(
    set_id: str,
    *,
    title: str,
    set_type: str = "private_bank",
    plantilla: bool = False,
    pendientes: dict[str, int] | None = None,
    propuestas: int = 0,
) -> TraySet:
    return TraySet(
        set_id=set_id,
        title=title,
        set_type=set_type,
        origin_scope="desconocida",
        key_reliability="fiable",
        tiene_plantilla_enlazada=plantilla,
        pendientes={} if pendientes is None else pendientes,
        propuestas=propuestas,
    )


# --------------------------------------------------------------------------------- la cifra


def test_un_conjunto_no_oficial_cuenta_una_vez_aunque_tenga_cincuenta_incidencias() -> None:
    """Agrupar es lo que baja la cifra: 50 sospechosas de un banco son **una** cosa que atender.

    Es el caso del §2.1 del cierre del objetivo —«TEST VARIOS: 50 claves sospechosas»—, y sin esta
    regla la medida de éxito no se movería: la bandeja tendría las mismas entradas que antes.
    """
    fila = _conjunto(
        "s1", title="TEST VARIOS", pendientes={"clave_sospechosa": 50, "hueco_sin_material": 3}
    )

    assert fila.total_pendiente == 53
    assert fila.entradas_de_decision == 1
    assert fila.resumen() == "50 claves sospechosas · 3 huecos sin material"


def test_lo_oficial_cuenta_una_por_incidencia_porque_no_se_decide_en_bloque() -> None:
    """Un examen oficial no tiene atajo: su clave la decide el propietario, incidencia a incidencia.

    Contarlo como una fila escondería justo lo que más pesa, que es lo que el §3 del cierre del
    objetivo pide enseñar aparte y arriba.
    """
    oficial = _conjunto(
        "s2",
        title="TAI ingreso libre 2025 · modelo A (examen oficial INAP)",
        set_type="official_exam",
        pendientes={"pregunta_ambigua": 3},
    )

    assert oficial.seccion is TraySection.OFICIAL
    assert oficial.entradas_de_decision == 3


def test_una_plantilla_enlazada_tambien_es_oficial_aunque_el_tipo_diga_banco_privado() -> None:
    """El segundo camino a «oficial»: la plantilla salió de un documento.

    Es el caso de la Guardia Civil 2026 y el de un examen importado antes de que su tipo se
    arreglara. Si la bandeja solo mirara `set_type`, ofrecería el botón de aceptar derivadas
    sobre una plantilla publicada.
    """
    fila = _conjunto(
        "s3", title="Plantilla de un papel", plantilla=True, pendientes={"clave_sospechosa": 4}
    )

    assert fila.es_oficial is True
    assert fila.acciones == ()
    assert fila.entradas_de_decision == 4


def test_la_cifra_no_cuenta_lo_propuesto_ni_lo_que_no_espera() -> None:
    """Lo propuesto se aprueba en bloque y lo resuelto por regla ya no espera: ninguna de las dos
    cosas es criterio del propietario."""
    fila = _conjunto("s4", title="Banco con propuestas", propuestas=12)

    assert fila.total_pendiente == 0
    assert fila.entradas_de_decision == 0


def test_la_vista_parte_en_dos_secciones_y_pone_lo_oficial_arriba() -> None:
    """Lo oficial va primero y, dentro de cada sección, lo que más espera."""
    vista = agrupar(
        [
            _conjunto("a", title="Banco pequeño", pendientes={"clave_sospechosa": 2}),
            _conjunto("b", title="Banco grande", pendientes={"clave_sospechosa": 40}),
            _conjunto(
                "c",
                title="INAP modelo B",
                set_type="official_exam",
                pendientes={"clave_sospechosa": 1},
            ),
        ]
    )

    assert [fila.set_id for fila in vista.oficial] == ["c"]
    assert [fila.set_id for fila in vista.resto] == ["b", "a"]
    assert vista.entradas_de_decision == 1 + 1 + 1
    assert vista.total_pendiente == 43


# ------------------------------------------------------------------------------- el permiso


def test_aceptar_derivadas_sobre_un_examen_oficial_se_rechaza_con_el_motivo_de_la_clave() -> None:
    """**Una clave oficial no se cambia jamás**, y la bandeja lo rechaza por el mismo motivo.

    La prueba ata el rechazo al dominio de la clave (`protege_cambiar_la_clave`) y no a un texto
    suelto: si mañana la aplicación aprende otra forma de ser oficial, la bandeja la hereda sola.
    """
    motivo = rechazo_de_accion(
        TrayAction.ACEPTAR_DERIVADAS, set_type="official_exam", tiene_plantilla_enlazada=False
    )

    assert motivo is not None
    assert "examen oficial" in motivo
    assert "no se cambia" in motivo


def test_aceptar_derivadas_sobre_un_banco_privado_se_permite() -> None:
    """El reverso: sin protección, la acción se admite y con ella las otras dos."""
    assert (
        rechazo_de_accion(
            TrayAction.ACEPTAR_DERIVADAS, set_type="private_bank", tiene_plantilla_enlazada=False
        )
        is None
    )
    assert acciones_permitidas(set_type="private_bank", tiene_plantilla_enlazada=False) == ACCIONES


def test_dejar_fuera_un_conjunto_oficial_tambien_se_rechaza_y_dice_por_que() -> None:
    """Las otras dos acciones no escriben la clave, pero un examen oficial tampoco se saca del
    temario en bloque: el motivo viaja con la aclaración para que no parezca un error."""
    motivo = rechazo_de_accion(
        TrayAction.DEJAR_FUERA, set_type="official_exam", tiene_plantilla_enlazada=False
    )

    assert motivo is not None
    assert "no se decide en bloque" in motivo


# ------------------------------------------------------------------- la resolución automática


def test_una_pregunta_mal_importada_se_va_a_no_son_preguntas_sin_pasar_por_el_propietario() -> None:
    assert (
        estado_resuelto(categoria=CategoriaIncidencia.PREGUNTA_MAL_IMPORTADA, tiene_propuesta=False)
        is IncidentStatus.NO_SON_PREGUNTAS
    )


def test_un_falso_positivo_queda_descartado_y_no_se_borra_de_la_bandeja() -> None:
    """`dismissed` y no una fila borrada: el motor vuelve a comprobar los temas, y un falso positivo
    ya descartado **no puede volver a entrar**."""
    assert estado_resuelto(categoria=None, tiene_propuesta=False) is IncidentStatus.DISMISSED


def test_una_incidencia_con_propuesta_espera_la_aprobacion_en_bloque() -> None:
    assert (
        estado_resuelto(categoria=CategoriaIncidencia.CLAVE_SOSPECHOSA, tiene_propuesta=True)
        is IncidentStatus.PROPUESTA_LISTA
    )


def test_lo_que_necesita_criterio_se_queda_abierto() -> None:
    """El caso que cuenta la medida de éxito: sin regla que lo cierre, sigue esperando."""
    assert (
        estado_resuelto(categoria=CategoriaIncidencia.HUECO_SIN_MATERIAL, tiene_propuesta=False)
        is None
    )
