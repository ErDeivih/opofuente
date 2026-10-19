"""Comprueba que la composición con la misma semilla elige **las mismas preguntas**.

Es la comprobación que hace falta después de tocar `_candidatas`: el reparto depende del orden en el
que se recorren las preguntas, así que si el orden se hubiera vuelto inestable (un `set` de Python,
por ejemplo), la misma semilla montaría sesiones distintas y nadie se enteraría hasta que un alumno
viera que su simulacro no se reproduce.

Uso:
    python artifacts/simulacro/reproducibilidad.py <data_dir>
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from opofuente.application.student_models import StudentMockExamRequest  # noqa: F401
from opofuente.application.study_service import CompositionSpec, PartSpec
from opofuente.config import Settings
from opofuente.domain.profiles import NodeType
from opofuente.domain.study import SessionMode
from opofuente.main import create_app

SEMILLA = 20261016


def elegidas(
    app, partes: tuple[PartSpec, ...], semilla: int | None, oposicion_id: str
) -> list[str]:
    study = app.state.study_service
    resultado = study.compose(
        CompositionSpec(
            parts=partes,
            mode=SessionMode.MOCK_EXAM,
            exam_like=True,
            public_only=True,
            seed=semilla,
            label="Sonda de reproducibilidad",
        ),
        opposition_id=oposicion_id,
    )
    # Las preguntas congeladas de la sesión, en su orden: es lo que se compara.
    return [
        pregunta.question_version_id
        for pregunta in study._study.session_questions(resultado.session.id)
    ]


def main() -> int:
    data_dir = Path(sys.argv[1])
    os.environ.pop("OPOFUENTE_DATA_DIR", None)
    app = create_app(Settings(data_dir=data_dir, worker_enabled=False, _env_file=None))

    student = app.state.student_service
    perfil = app.state.profiles_service
    # La zona del alumno no enseña identificadores, así que la oposición se lee del perfil: es la
    # misma que sirve el alumno (una sola en esta instalación) y aquí se comprueba que no está
    # vacía.
    oposiciones = perfil.list_oppositions()
    if not oposiciones:
        raise SystemExit("no hay ninguna oposición sembrada")
    # La que sirve la zona del alumno, que es sobre la que se mide (se elige por su código legible:
    # el alumno no enseña identificadores y aquí no hace falta ninguno).
    codigo = student.opposition_view().code
    elegida = next((una for una in oposiciones if una.code == codigo), None)
    if elegida is None:
        raise SystemExit(f"no hay ninguna oposición con el código «{codigo}»")
    oposicion_id = elegida.id
    detalle = perfil.get_opposition(oposicion_id)
    if detalle is None or not detalle.convocations:
        raise SystemExit("la oposición no tiene convocatoria: no hay nada que componer")
    curriculum = perfil.get_curriculum(detalle.convocations[0].id)
    if curriculum is None:
        raise SystemExit("la convocatoria no tiene programa: no hay nada que componer")
    temas = [
        tema.id
        for bloque in curriculum.nodes
        if bloque.node_type is NodeType.BLOCK
        for tema in bloque.children
    ]
    supuesto_iv = [
        tema.id
        for bloque in curriculum.nodes
        if bloque.node_type is NodeType.BLOCK and bloque.path.upper() == "IV"
        for tema in bloque.children
    ]
    if not temas or not supuesto_iv:
        raise SystemExit("el programa no tiene los bloques que necesita la sonda")

    partes = (
        PartSpec(code="primera_parte", node_ids=tuple(temas), count=80, reserve=5),
        PartSpec(
            code="segunda_parte",
            node_ids=tuple(supuesto_iv),
            count=20,
            reserve=5,
            alternative_group="supuesto",
        ),
    )
    primera = elegidas(app, partes, SEMILLA, oposicion_id)
    segunda = elegidas(app, partes, SEMILLA, oposicion_id)
    print(f"preguntas: {len(primera)} · {len(segunda)}")
    print("mismas con la misma semilla:", primera == segunda)
    if primera != segunda:
        distintas = [
            (indice, a, b)
            for indice, (a, b) in enumerate(zip(primera, segunda, strict=True))
            if a != b
        ]
        print("primeras diferencias:", distintas[:5])
    # Y sin semilla, el orden es el del programa: también tiene que ser estable.
    tercera = elegidas(app, partes, None, oposicion_id)
    cuarta = elegidas(app, partes, None, oposicion_id)
    print("mismas sin semilla:", tercera == cuarta)
    return 0 if primera == segunda and tercera == cuarta else 1


if __name__ == "__main__":
    raise SystemExit(main())
