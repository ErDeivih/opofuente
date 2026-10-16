"""La vuelta atrás de las migraciones, **derivada del guion de alembic** y ejecutada de verdad.

El método del proyecto es explícito: «escrito no es hecho; ejecutado es hecho». Varios slices
declaraban que su `downgrade` estaba probado y no había ninguna prueba que lo ejecutara (solo 0011 y
0012 lo hacían), así que esta prueba recorre la cadena entera hacia abajo, un escalón cada vez, y
comprueba en cada uno tres cosas:

1. la revisión marcada es la que se pidió;
2. las tablas que esa migración creó **ya no están** (una migración que solo ensancha una
   restricción añade columnas o `CHECK`, no tablas, y por eso su escalón va vacío);
3. volver a subir a la cabeza las recrea: bajar no deja el esquema en un estado del que no se pueda
   salir.

**La escalera se deriva, no se enumera.** Antes había aquí una lista escrita a mano y **rompió cinco
fusiones en un día** (15-oct-2026): el panel (`0038_revision_de_apuntes`), el medidor
(`0037_origin_scope`), la bandeja (`0039_bandeja_por_conjunto`, dos veces: al re-apuntarla a
`0039_claves_derivadas` y otra vez al entrar `0040`) y la plataforma desplegable
(`0040_cuentas_y_consentimiento`). El síntoma era siempre el mismo y no parecía de quien lo sufría:
la puerta 7 caía en el **primer** escalón diciendo que esperaba otra revisión, porque la lista se
había quedado corta al añadir una migración.

Ahora los escalones salen de dos sitios que **no se pueden olvidar**:

- la **cadena**: `ScriptDirectory.walk_revisions()` recorre `down_revision` desde la cabeza hasta la
  raíz, así que una migración nueva entra sola, en su sitio y con su padre;
- las **tablas** que se lleva cada bajada: se leen del propio guion de la migración
  (`op.create_table(...)`), resolviendo el nombre aunque venga de una constante del módulo.

Lo único que sigue escrito a mano es lo que **no** se puede deducir de un guion: nada. Si alguien
escribe un `create_table` con un nombre calculado (una f-string, una variable que no sea una
constante de texto), esta prueba **falla y lo dice**: es mejor que comprobar en silencio menos de lo
que cree.

No comprueba la forma de cada tabla recreada (eso lo hacen las pruebas de cada migración): comprueba
que la bajada existe, se ejecuta y devuelve el esquema a su sitio.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from alembic.script import Script, ScriptDirectory
from sqlalchemy import text

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations, script_head

#: La raíz de la cadena: la migración más antigua, la que ya no baja a ninguna parte.
BASE = "0001_app_metadata"

#: Un escalón: de qué revisión se baja, a cuál, y qué tablas desaparecen al hacerlo.
Escalon = tuple[str, str, tuple[str, ...]]


def _tablas_creadas(script: Script) -> tuple[str, ...]:
    """Las tablas que la migración crea, leídas de su `op.create_table(...)`.

    El nombre puede ser un literal o una constante de texto del propio módulo
    (`0028_fuera_de_temario` usa `TABLA = "question_curriculum_exclusions"`). Si no se puede
    resolver, esto **falla**: una comprobación que se salta en silencio lo que no entiende es peor
    que no tenerla.
    """
    arbol = ast.parse(Path(script.path).read_text(encoding="utf-8"))
    constantes = {
        nodo.targets[0].id: nodo.value.value
        for nodo in arbol.body
        if isinstance(nodo, ast.Assign)
        and len(nodo.targets) == 1
        and isinstance(nodo.targets[0], ast.Name)
        and isinstance(nodo.value, ast.Constant)
        and isinstance(nodo.value.value, str)
    }
    nombres: list[str] = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        if not isinstance(nodo.func, ast.Attribute) or nodo.func.attr != "create_table":
            continue
        if not nodo.args:
            continue
        primero = nodo.args[0]
        if isinstance(primero, ast.Constant) and isinstance(primero.value, str):
            nombres.append(primero.value)
        elif isinstance(primero, ast.Name) and primero.id in constantes:
            nombres.append(constantes[primero.id])
        else:
            raise AssertionError(
                f"{Path(script.path).name}: `op.create_table` con un nombre que no se puede leer "
                f"({ast.unparse(primero)}). Deja el nombre como texto (o como constante de "
                "texto del módulo): la escalera de esta prueba se deriva del guion y no puede "
                "adivinar."
            )
    return tuple(nombres)


def _escalones(settings: Settings) -> tuple[Escalon, ...]:
    """La escalera entera, **derivada**: de la cabeza a la raíz, un escalón por migración.

    Cada escalón es `(desde, hasta, tablas_que_se_van)`. Ni la cadena ni las tablas están
    escritas a mano: la primera la da alembic y las segundas, el guion de cada migración.
    """
    guion = ScriptDirectory.from_config(alembic_config(settings))
    escalones: list[Escalon] = []
    for script in guion.walk_revisions():
        padre = script.down_revision
        if padre is None:
            break
        # Una revisión de fusión tendría dos padres y esta cadena no las tiene: si aparece una, se
        # dice en lugar de comparar con el texto de una tupla.
        assert isinstance(padre, str), (
            f"{script.revision} declara varios padres ({padre!r}): la escalera no sabe bajar por "
            "una "
            "fusión y hay que decidir cómo se recorre"
        )
        escalones.append((str(script.revision), padre, _tablas_creadas(script)))
    return tuple(escalones)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _bajar_a(settings: Settings, revision: str) -> None:
    """Baja de revisión de verdad: `run_migrations` solo sube."""
    command.downgrade(alembic_config(settings), revision)


def _tablas(settings: Settings) -> set[str]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return {
                str(fila[0])
                for fila in conexion.execute(
                    text("SELECT name FROM sqlite_master WHERE type = 'table'")
                )
            }
    finally:
        engine.dispose()


def _revision(settings: Settings) -> str:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return str(conexion.execute(text("SELECT version_num FROM alembic_version")).scalar())
    finally:
        engine.dispose()


def test_la_escalera_es_la_cadena_de_alembic_sin_saltos(tmp_path: Path) -> None:
    """La escalera llega de la cabeza a la raíz y **cada escalón baja un paso**.

    Esto es lo que impide que vuelva a colarse una lista escrita a mano: una lista se queda corta
    al añadir una migración, y aquí un hueco se ve enseguida —el padre de `desde` tiene que ser
    `hasta`—.
    """
    settings = _settings(tmp_path)
    escalera = _escalones(settings)

    assert escalera, "la cadena de migraciones está vacía"
    assert escalera[0][0] == script_head(settings), "la escalera no empieza en la cabeza"
    assert escalera[-1][1] == BASE, f"la escalera no llega a la raíz ({BASE})"

    guion = ScriptDirectory.from_config(alembic_config(settings))
    for desde, hasta, _ in escalera:
        revision = guion.get_revision(desde)
        assert revision is not None, f"{desde} no está en el guion de alembic"
        assert revision.down_revision == hasta, (
            f"{desde} baja a {revision.down_revision!r}, y la escalera dice {hasta}"
        )


def test_la_cadena_entera_se_puede_recorrer_hacia_atras(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")
    assert _revision(settings) == script_head(settings)

    for desde, hasta, tablas_que_se_van in _escalones(settings):
        assert _revision(settings) == desde, f"se esperaba estar en {desde}"
        _bajar_a(settings, hasta)
        assert _revision(settings) == hasta, f"no se bajó de {desde} a {hasta}"
        presentes = _tablas(settings)
        for tabla in tablas_que_se_van:
            assert tabla not in presentes, f"{tabla} sigue ahí tras bajar de {desde}"


def test_volver_a_subir_recrea_lo_que_la_bajada_retiro(tmp_path: Path) -> None:
    """Bajar no deja el esquema inservible: subir otra vez lo devuelve a la cabeza."""
    settings = _settings(tmp_path)
    run_migrations(settings, revision="head")

    escalones = _escalones(settings)
    _bajar_a(settings, BASE)
    assert _revision(settings) == BASE
    retiradas = {tabla for _, _, tablas in escalones for tabla in tablas}
    presentes = _tablas(settings)
    for tabla in sorted(retiradas):
        assert tabla not in presentes, f"{tabla} debería haber desaparecido al bajar a {BASE}"

    run_migrations(settings, revision="head")

    assert _revision(settings) == script_head(settings)
    presentes = _tablas(settings)
    for tabla in sorted(retiradas):
        assert tabla in presentes, f"{tabla} no se ha recreado al volver a subir"


@pytest.mark.parametrize(
    ("revision", "tabla"),
    [
        ("0013_documents_versions_and_rights", "rights_statuses"),
        ("0014_questions_and_keys", "answer_key_entries"),
        ("0016_study_sessions", "attempt_evaluations"),
        ("0018_search_and_rag", "retrieval_hits"),
        ("0019_errors_and_reviews", "review_items"),
        ("0020_changes_and_derivatives", "derived_artifacts"),
    ],
)
def test_cada_migracion_deja_su_tabla_al_llegar_a_ella(
    tmp_path: Path, revision: str, tabla: str
) -> None:
    """Cada escalón se puede alcanzar **desde cero**: la cadena no depende de haber subido antes."""
    settings = _settings(tmp_path)

    run_migrations(settings, revision=revision)

    assert _revision(settings) == revision
    assert tabla in _tablas(settings)
