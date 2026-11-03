"""Pruebas del plan derivado (O4): modo, fase 2, repasos y progreso por bloque.

**Nada de base de datos ni de API aqui**: se prueban las decisiones que no pueden depender de la
pantalla. El repositorio se sustituye por uno falso con los mismos metodos, para comprobar que el
servicio no vuelve a decidir el umbral.
"""

from __future__ import annotations

from datetime import date

from opofuente.application.plan_service import PlanService
from opofuente.domain.study_plan import (
    INTERVALOS_REPASO,
    MINUTOS_REPASO,
    MINUTOS_SIMULACRO,
    MINUTOS_SUPUESTO,
    ModoDeEstudio,
    Plan,
    Semana,
    Tarea,
    TemaDelPlan,
    TipoDeTarea,
    derivar_modo,
    planificar,
)
from opofuente.infrastructure.plan_repository import AvanceDeBloque, PlanGuardado

LUNES = date(2026, 1, 5)


def _tema(codigo: str, bloque: str = "III") -> TemaDelPlan:
    return TemaDelPlan(
        codigo=codigo,
        titulo=f"Tema {codigo}",
        preguntas=10,
        bloque_codigo=bloque,
        bloque_titulo=f"Bloque {bloque}",
    )


# --- el modo se deriva, no se guarda -------------------------------------------------------------


def test_un_tema_por_semana_es_extensivo() -> None:
    assert derivar_modo(4, 4).modo is ModoDeEstudio.EXTENSIVO
    assert derivar_modo(4, 4).temas_por_semana == 1


def test_exactamente_dos_temas_por_semana_es_intensivo_y_cabe() -> None:
    derivacion = derivar_modo(4, 2)

    assert derivacion.modo is ModoDeEstudio.INTENSIVO
    assert derivacion.temas_por_semana == 2
    assert derivacion.planificable


def test_mas_de_dos_temas_por_semana_no_es_planificable_y_lo_dice() -> None:
    derivacion = derivar_modo(5, 2)

    assert derivacion.modo is ModoDeEstudio.INTENSIVO
    assert not derivacion.planificable
    assert derivacion.motivo is not None
    assert "5 temas" in derivacion.motivo


def test_cero_temas_es_planificable_aunque_no_haya_semanas() -> None:
    derivacion = derivar_modo(0, 0)

    assert derivacion.planificable
    assert derivacion.modo is ModoDeEstudio.EXTENSIVO


def test_temas_sin_semanas_de_lectura_no_son_planificables() -> None:
    derivacion = derivar_modo(1, 0)

    assert not derivacion.planificable
    assert derivacion.motivo is not None


# --- el calendario -------------------------------------------------------------------------------


def test_un_examen_pasado_no_inventa_semanas() -> None:
    plan = planificar(
        (_tema("III.1"),),
        hoy=LUNES,
        fecha_examen=LUNES,
        horas_por_semana=10,
    )

    assert plan.semanas == ()
    assert not plan.planificable
    assert plan.fuera == ("III.1",)
    assert plan.fuera_detalle[0].titulo == "Tema III.1"


def test_con_tres_semanas_la_fase_2_se_queda_en_una_y_el_resto_es_lectura() -> None:
    plan = planificar(
        (_tema("III.1"),),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7 * 3),
        horas_por_semana=10,
    )

    assert plan.total_semanas == 3
    assert plan.fase_2_desde == 3
    assert plan.semanas_de_lectura == 2
    assert [semana.fase for semana in plan.semanas] == ["lectura", "lectura", "fase-2"]
    assert plan.planificable
    assert plan.dentro == ("III.1",)


def test_con_cuatro_semanas_se_lee_tres_y_queda_una_de_fase_2() -> None:
    """La fase 2 no puede dejar el plan sin semanas de lectura."""
    plan = planificar(
        (_tema("III.1"), _tema("III.2"), _tema("III.3")),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7 * 4),
        horas_por_semana=20,
    )

    assert plan.total_semanas == 4
    assert plan.semanas_de_lectura == 3
    assert plan.fase_2_desde == 4
    assert [semana.fase for semana in plan.semanas] == ["lectura"] * 3 + ["fase-2"]
    assert plan.dentro == ("III.1", "III.2", "III.3")
    assert plan.planificable


def test_con_una_semana_no_hay_simulacro_pero_los_temas_se_reparten() -> None:
    plan = planificar(
        (_tema("III.1"),),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7),
        horas_por_semana=10,
    )

    assert plan.total_semanas == 1
    assert plan.semanas_de_lectura == 1
    assert plan.fase_2_desde is None
    assert plan.dentro == ("III.1",)
    assert plan.planificable
    semana = plan.semanas[0]
    assert semana.fase == "lectura"
    assert all(tarea.tipo is not TipoDeTarea.SIMULACRO for tarea in semana.tareas)
    assert "simulacro" in " ".join(semana.recortes)
    assert "fase 2" in " ".join(semana.recortes)


def test_la_fase_2_ocupa_las_cuatro_ultimas_semanas_y_cierra_con_un_simulacro() -> None:
    plan = planificar(
        tuple(_tema(f"III.{indice}") for indice in range(1, 5)),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7 * 8),
        horas_por_semana=20,
    )

    assert plan.total_semanas == 8
    assert plan.semanas_de_lectura == 4
    assert plan.fase_2_desde == 5
    assert [semana.fase for semana in plan.semanas[:4]] == ["lectura"] * 4
    assert [semana.fase for semana in plan.semanas[4:]] == ["fase-2"] * 4

    fase_2 = plan.semanas[4:]
    assert all(
        [tarea.tipo for tarea in semana.tareas].count(TipoDeTarea.SUPUESTO) == 1
        for semana in fase_2
    )
    simulacros = [
        tarea for semana in fase_2 for tarea in semana.tareas if tarea.tipo is TipoDeTarea.SIMULACRO
    ]
    assert len(simulacros) == 1
    assert plan.semanas[-1].tareas[-1].tipo is TipoDeTarea.SIMULACRO


def test_un_tema_que_no_cabe_se_nombra_fuera_del_plan() -> None:
    plan = planificar(
        tuple(_tema(f"III.{indice}") for indice in range(1, 8)),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7 * 5),
        horas_por_semana=10,
    )

    # Con cinco semanas quedan tres de lectura: dos temas por semana son seis.
    assert plan.semanas_de_lectura == 3
    assert plan.temas_por_semana == 2
    assert len(plan.dentro) == 6
    assert plan.fuera == ("III.7",)
    assert plan.fuera_detalle[0].titulo == "Tema III.7"
    assert not plan.planificable
    assert plan.motivo is not None and "III.7" not in plan.motivo


def test_los_repasos_caen_a_una_tres_y_siete_semanas() -> None:
    plan = planificar(
        (_tema("III.1"),),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7 * 8),
        horas_por_semana=40,
    )

    destinos = {
        semana.numero
        for semana in plan.semanas
        for tarea in semana.tareas
        if tarea.tipo is TipoDeTarea.REPASO and tarea.codigo == "III.1"
    }
    # La fase 2 empieza en la quinta, asi que los repasos de +1, +3 y +7 se recortan a +1 y +3.
    assert destinos == {2, 4}
    assert INTERVALOS_REPASO == (1, 3, 7)


def test_los_repasos_no_pasan_a_la_fase_2_y_se_avisa() -> None:
    plan = planificar(
        (_tema("III.1"),),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7 * 8),
        horas_por_semana=40,
    )

    assert plan.semanas_de_lectura == 4
    assert plan.fase_2_desde == 5
    # Ni repasos ni lecturas nuevas dentro de la fase 2: alli solo hay supuestos y simulacro.
    for semana in plan.semanas[4:]:
        assert all(
            tarea.tipo in (TipoDeTarea.SUPUESTO, TipoDeTarea.SIMULACRO) for tarea in semana.tareas
        )

    # El +7 del tema leido en la primera semana cae en la fase 2: no se inventa una cita
    # alli, pero la semana de lectura lo dice en vez de callarlo.
    recortes = " ".join(plan.semanas[0].recortes)
    assert "fase 2" in recortes
    assert "III.1" in recortes
    assert "+7" in recortes


def test_un_repaso_que_no_cabe_se_recorta_y_se_dice() -> None:
    plan = planificar(
        (_tema("III.1"), _tema("III.2")),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7 * 8),
        horas_por_semana=3,
    )

    semana = plan.semanas[1]
    assert all(tarea.tipo is not TipoDeTarea.REPASO for tarea in semana.tareas)
    assert any(str(MINUTOS_REPASO) in recorte for recorte in semana.recortes)
    assert semana.minutos <= 3 * 60


def test_el_modo_intensivo_avisa_si_dos_temas_pasan_de_las_horas() -> None:
    """Dos temas y su test son 320 min: con 5 h declaradas el plan lo dice, no borra un tema."""
    plan = planificar(
        tuple(_tema(f"III.{indice}") for indice in range(1, 8)),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7 * 6),
        horas_por_semana=5,
    )

    assert plan.modo is ModoDeEstudio.INTENSIVO
    assert plan.semanas_de_lectura == 3
    assert plan.temas_por_semana == 2
    semana = plan.semanas[0]
    # 150 + 150 de lectura y 20 del test: 320 min frente a los 300 declarados.
    assert semana.minutos == 320
    assert sum(1 for tarea in semana.tareas if tarea.tipo is TipoDeTarea.LEER) == 2
    aviso = " ".join(semana.recortes)
    assert "320" in aviso
    assert "300" in aviso
    assert "sobran 20 min" in aviso
    assert "amplia las horas" in aviso


def test_la_ultima_semana_avisa_si_el_simulacro_pasa_de_las_horas() -> None:
    """Supuesto y simulacro conservan su duracion real aunque no quepan: se avisa, no se acortan."""
    plan = planificar(
        (),
        hoy=LUNES,
        fecha_examen=LUNES.fromordinal(LUNES.toordinal() + 7 * 8),
        horas_por_semana=2,
    )

    ultima = plan.semanas[-1]
    assert ultima.fase == "fase-2"
    assert [tarea.tipo for tarea in ultima.tareas] == [
        TipoDeTarea.SUPUESTO,
        TipoDeTarea.SIMULACRO,
    ]
    assert ultima.minutos == MINUTOS_SUPUESTO + MINUTOS_SIMULACRO == 210
    aviso = " ".join(ultima.recortes)
    assert "210" in aviso
    assert "120" in aviso
    assert "sobran 90 min" in aviso


# --- el progreso por bloque ----------------------------------------------------------------------


class _RepositorioFalso:
    def __init__(self) -> None:
        self._guardado = PlanGuardado(
            exam_date=LUNES.fromordinal(LUNES.toordinal() + 7 * 8),
            hours_per_week=20,
            rest_days=frozenset({6}),
        )
        self._temas = (
            TemaDelPlan("III.1", "Tema III.1", 10, bloque_codigo="III", bloque_titulo="Bloque III"),
            TemaDelPlan("III.2", "Tema III.2", 10, bloque_codigo="III", bloque_titulo="Bloque III"),
            TemaDelPlan("IV.1", "Tema IV.1", 10, bloque_codigo="IV", bloque_titulo="Bloque IV"),
            TemaDelPlan("IV.2", "Tema IV.2", 10, bloque_codigo="IV", bloque_titulo="Bloque IV"),
        )

    def guardado(self) -> PlanGuardado:
        return self._guardado

    def plan(self, *, hoy: date | None = None) -> Plan:
        """Un plan fijo de dos semanas: aisla el progreso del calendario real."""
        tareas_semana_1 = tuple(
            Tarea(
                tipo=TipoDeTarea.LEER,
                codigo=codigo,
                titulo=f"Lee {codigo}",
                minutos=150,
                bloque_codigo=codigo.split(".")[0],
                bloque_titulo=f"Bloque {codigo.split('.')[0]}",
            )
            for codigo in ("III.1", "III.2")
        )
        tareas_semana_2 = tuple(
            Tarea(
                tipo=TipoDeTarea.LEER,
                codigo=codigo,
                titulo=f"Lee {codigo}",
                minutos=150,
                bloque_codigo=codigo.split(".")[0],
                bloque_titulo=f"Bloque {codigo.split('.')[0]}",
            )
            for codigo in ("IV.1", "IV.2")
        )
        return Plan(
            semanas=(
                Semana(numero=1, empieza=LUNES, tareas=tareas_semana_1),
                Semana(
                    numero=2,
                    empieza=LUNES.fromordinal(LUNES.toordinal() + 7),
                    tareas=tareas_semana_2,
                ),
            ),
            fuera=(),
            dentro=("III.1", "III.2", "IV.1", "IV.2"),
        )

    def temas(self) -> tuple[TemaDelPlan, ...]:
        return self._temas

    def leido_y_practicado(self) -> tuple[int, int]:
        return 2, 1

    def avance_por_bloque(self) -> tuple[AvanceDeBloque, ...]:
        return (
            AvanceDeBloque("III", "Bloque III", leidos=1, practicados=1, total=2),
            AvanceDeBloque("IV", "Bloque IV", leidos=1, practicados=0, total=2),
        )


def test_el_progreso_desglosa_por_bloque_con_el_mismo_umbral() -> None:
    servicio = PlanService(_RepositorioFalso())  # type: ignore[arg-type]
    # Segunda semana de lectura: solo la primera ha terminado, asi que deberian estar
    # leidos sus dos temas; la semana en curso no cuenta todavia.
    progreso = servicio.progreso(hoy=LUNES.fromordinal(LUNES.toordinal() + 7))

    assert progreso is not None
    assert progreso.esperados == 2
    por_bloque = {bloque.codigo: bloque for bloque in progreso.bloques}
    assert por_bloque["III"].esperados == 2
    assert por_bloque["III"].total == 2
    assert por_bloque["III"].leidos == 1
    assert not por_bloque["III"].vas_bien
    assert por_bloque["IV"].esperados == 0
    assert por_bloque["IV"].frase


def test_la_semana_en_curso_no_cuenta_como_esperada() -> None:
    """El lunes no se puede deber lo que el plan pide para esa misma semana."""
    servicio = PlanService(_RepositorioFalso())  # type: ignore[arg-type]

    primero = servicio.progreso(hoy=LUNES)
    mitad = servicio.progreso(hoy=LUNES.fromordinal(LUNES.toordinal() + 8))

    assert primero is not None and primero.esperados == 0
    assert primero.vas_bien
    assert mitad is not None and mitad.esperados == 2


def test_hoy_lleva_el_modo_y_lo_que_no_cabe() -> None:
    servicio = PlanService(_RepositorioFalso())  # type: ignore[arg-type]
    hoy = servicio.hoy(hoy=LUNES)

    assert hoy.modo is ModoDeEstudio.EXTENSIVO
    assert hoy.planificable
    assert hoy.motivo is None
    assert hoy.semana is not None
