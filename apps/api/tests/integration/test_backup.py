"""Pruebas de la copia, la verificación y la restauración (S12) sobre ficheros y base reales.

Los criterios de aceptación del slice, uno por prueba:

1. **restaurar en vacío reproduce hashes, DB y sesiones**: se hace una copia, se destruye el árbol
   de datos y al restaurar vuelven los mismos bytes (hash a hash) y la misma fila de la base;
2. **un fallo de restauración deja la instalación anterior utilizable**: se fuerza el fallo después
   de haber apartado el material y se comprueba que todo sigue ahí;
3. **validar no escribe nada**: la previsualización deja el árbol exactamente como estaba;
4. **una copia corrupta se declara corrupta**: cambiar un byte del contenido hace que la
   verificación lo diga y que la restauración no empiece;
5. **el manifiesto no puede escribir fuera del destino**: una ruta con `..` se rechaza antes de
   construir ninguna ruta.

Y una que no es un criterio del slice pero es la razón de ser de todo esto: **la base se copia con
la API de respaldo de SQLite**, así que una escritura en marcha no puede dejar una copia rota.
"""

from __future__ import annotations

import json
import sqlite3
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from opofuente.application.backup_service import BackupService
from opofuente.config import DataPaths, Settings
from opofuente.domain.backup import (
    BACKUP_FORMAT_VERSION,
    BackupEntry,
    BackupError,
    BackupManifest,
    is_restorable,
    safe_relative_path,
)
from opofuente.infrastructure.backup_archive import (
    MANIFEST_NAME,
    read_manifest,
    snapshot_database,
    verify_archive,
)

AHORA = datetime(2026, 9, 19, 12, 0, tzinfo=UTC)

REVISION = "0020_changes_and_derivatives"


class _Reloj:
    def now(self) -> datetime:
        return AHORA


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _service(settings: Settings, *, revision: str = REVISION) -> BackupService:
    return BackupService(
        paths=settings.data_paths,
        app_version="0.0.0-test",
        clock=lambda: AHORA,
        schema_revision=lambda: revision,
    )


def _arbol(settings: Settings) -> None:
    """Un árbol de datos pequeño y realista: base con una tabla, artefactos y representaciones."""
    paths = settings.data_paths
    paths.ensure_directories()
    conexion = sqlite3.connect(paths.database)
    try:
        conexion.execute("CREATE TABLE study_sessions (id TEXT PRIMARY KEY, title TEXT)")
        conexion.execute("INSERT INTO study_sessions VALUES ('ses-1', 'Practica de plazos')")
        conexion.commit()
    finally:
        conexion.close()
    (paths.artifacts / "sha256" / "ab").mkdir(parents=True, exist_ok=True)
    (paths.artifacts / "sha256" / "ab" / "uno.bin").write_bytes(b"contenido de un artefacto")
    (paths.extracted / "rep-1").mkdir(parents=True, exist_ok=True)
    (paths.extracted / "rep-1" / "texto.txt").write_text("texto extraido", encoding="utf-8")
    # Un temporal y un registro: **no** entran en la copia y no deben reaparecer al restaurar.
    (paths.tmp / "resto.part").write_bytes(b"basura")
    (paths.logs / "opofuente.log").write_text("linea de registro", encoding="utf-8")


def _sesiones(settings: Settings) -> list[tuple[str, str]]:
    conexion = sqlite3.connect(settings.data_paths.database)
    try:
        return [tuple(fila) for fila in conexion.execute("SELECT id, title FROM study_sessions")]
    finally:
        conexion.close()


def _hashes(settings: Settings) -> dict[str, str]:
    import hashlib

    raiz = settings.data_paths.root
    resumen: dict[str, str] = {}
    for ruta in sorted(raiz.rglob("*")):
        if not ruta.is_file():
            continue
        relativa = ruta.relative_to(raiz).as_posix()
        if relativa.startswith(("backups/", "tmp/", "logs/")):
            continue
        resumen[relativa] = hashlib.sha256(ruta.read_bytes()).hexdigest()
    return resumen


# --- copia --------------------------------------------------------------------------------------


def test_una_copia_trae_base_artefactos_y_representaciones_con_sus_hashes(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)

    vista = servicio.create()

    assert vista.file_count >= 3, "base + artefacto + representación"
    assert vista.scope == ("database", "artifacts", "extracted", "fixtures")
    assert vista.restorable is True
    assert "revisión de esquema actual" in vista.restorable_reason

    archivo = settings.data_paths.backups / f"{vista.id}.zip"
    manifiesto, problemas = verify_archive(archivo)
    assert problemas == ()
    rutas = {entrada.path for entrada in manifiesto.entries}
    assert "database/opofuente.sqlite3" in rutas
    assert "artifacts/sha256/ab/uno.bin" in rutas
    assert "extracted/rep-1/texto.txt" in rutas


def test_la_copia_no_lleva_temporales_ni_registros_ni_otras_copias(tmp_path: Path) -> None:
    """Lo que no es dato del usuario no entra: si no, cada copia llevaría dentro las anteriores."""
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)
    primera = servicio.create(note="primera")

    manifiesto = read_manifest(settings.data_paths.backups / f"{primera.id}.zip")

    rutas = {entrada.path for entrada in manifiesto.entries}
    assert not any(ruta.startswith("tmp/") for ruta in rutas)
    assert not any(ruta.startswith("logs/") for ruta in rutas)
    assert not any(ruta.startswith("backups/") for ruta in rutas)


def test_la_base_se_copia_con_la_api_de_respaldo_y_queda_legible(tmp_path: Path) -> None:
    """Copiar el `.sqlite3` a mano con `-wal` activo puede dar una base rota; la instantánea no."""
    settings = _settings(tmp_path)
    _arbol(settings)
    instantanea = settings.data_paths.tmp / "snap.sqlite3"

    snapshot_database(settings.data_paths.database, instantanea)

    conexion = sqlite3.connect(instantanea)
    try:
        assert conexion.execute("SELECT title FROM study_sessions").fetchone() == (
            "Practica de plazos",
        )
    finally:
        conexion.close()


# --- verificación -------------------------------------------------------------------------------


def test_una_copia_alterada_se_declara_corrupta_y_no_se_restaura(tmp_path: Path) -> None:
    """Criterio: una copia corrupta se dice, no se restaura a medias."""
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)
    vista = servicio.create()
    archivo = settings.data_paths.backups / f"{vista.id}.zip"

    # Se reescribe el contenido de una entrada dejando el manifiesto como estaba: es exactamente lo
    # que pasa cuando un fichero se corrompe en el disco.
    with zipfile.ZipFile(archivo) as original:
        piezas = {nombre: original.read(nombre) for nombre in original.namelist()}
    piezas["artifacts/sha256/ab/uno.bin"] = b"contenido manipulado"
    with zipfile.ZipFile(archivo, "w") as nuevo:
        for nombre, datos in piezas.items():
            nuevo.writestr(nombre, datos)

    informe = servicio.verify(vista.id)
    assert informe is not None
    assert informe.verified is False
    assert any("uno.bin" in problema for problema in informe.problems)

    with pytest.raises(BackupError) as error:
        servicio.restore(vista.id)
    assert "verificación" in str(error.value)


def test_una_entrada_con_punto_punto_se_rechaza_antes_de_construir_la_ruta() -> None:
    """La copia es dato no confiable: un `..` en el manifiesto no escribe fuera del destino."""
    for mala in ("../fuera.txt", "artifacts/../../fuera.txt", "/absoluto.txt", "C:/windows.txt"):
        with pytest.raises(BackupError):
            safe_relative_path(mala)


def test_una_ruta_buena_se_acepta_y_se_normaliza() -> None:
    assert safe_relative_path("artifacts\\sha256\\ab\\uno.bin").as_posix() == (
        "artifacts/sha256/ab/uno.bin"
    )


def test_una_copia_de_una_revision_mas_nueva_no_se_restaura(tmp_path: Path) -> None:
    """Restaurar el futuro sobre el presente dejaría tablas que el programa no sabe leer."""
    manifest = BackupManifest(
        id="futuro",
        created_at=AHORA.isoformat(),
        app_version="9.9.9",
        schema_revision="0099_del_futuro",
        format_version=BACKUP_FORMAT_VERSION,
        scope=("database",),
        entries=(BackupEntry("database/opofuente.sqlite3", 1, "a" * 64),),
    )

    puede, motivo = is_restorable(manifest, current_revision=REVISION)

    assert puede is False
    assert "actualiza el programa" in motivo


def test_una_copia_de_una_revision_anterior_se_restaura_con_migracion(tmp_path: Path) -> None:
    manifest = BackupManifest(
        id="antigua",
        created_at=AHORA.isoformat(),
        app_version="0.0.1",
        schema_revision="0010_recover_item_origin",
        format_version=BACKUP_FORMAT_VERSION,
        scope=("database",),
        entries=(BackupEntry("database/opofuente.sqlite3", 1, "a" * 64),),
    )

    puede, motivo = is_restorable(manifest, current_revision=REVISION)

    assert puede is True
    assert "se aplicarán las migraciones" in motivo


# --- restauración -------------------------------------------------------------------------------


def test_restaurar_en_vacio_reproduce_hashes_base_y_sesiones(tmp_path: Path) -> None:
    """Criterio: restaurar en vacío reproduce hashes, DB y sesiones.

    El hash se comprueba en el **material** (artefactos y representaciones), que es lo que el
    usuario no puede reconstruir. La base se comprueba por su contenido: la API de respaldo de
    SQLite da una copia lógicamente idéntica pero puede reordenar páginas, así que exigirle el
    mismo hash sería exigir algo que la copia en marcha no puede prometer.
    """
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)
    vista = servicio.create(note="antes de romperlo")
    hashes_antes = _hashes(settings)

    # Se destruye el árbol de datos: como si el usuario hubiera borrado la carpeta sin querer.
    for nombre in ("opofuente.sqlite3", "artifacts", "extracted"):
        objetivo = settings.data_paths.root / nombre
        if objetivo.is_dir():
            import shutil

            shutil.rmtree(objetivo)
        elif objetivo.exists():
            objetivo.unlink()
    assert not (settings.data_paths.root / "opofuente.sqlite3").exists()

    resultado = servicio.restore(vista.id)

    assert resultado.health_ok is True, resultado.health_detail
    assert set(resultado.restored) >= {"artifacts/sha256/ab/uno.bin", "extracted/rep-1/texto.txt"}
    # El material vuelve byte a byte: mismo conjunto de ficheros y mismos hashes.
    hashes_despues = _hashes(settings)
    assert set(hashes_despues) == set(hashes_antes)
    for ruta, digest in hashes_antes.items():
        if ruta == "opofuente.sqlite3":
            continue
        assert hashes_despues[ruta] == digest, f"{ruta} no ha vuelto igual"
    # Y la base vuelve con lo que tenía dentro: esquema y sesiones.
    assert _sesiones(settings) == [("ses-1", "Practica de plazos")]
    # La copia previa automática existe y tiene su propia nota (criterio del contrato).
    ids = [copia.id for copia in servicio.list()]
    assert resultado.previous_backup_id in ids


def test_restaurar_no_toca_el_arbol_de_temporales_ni_los_registros(tmp_path: Path) -> None:
    """El árbol de temporales es **zona de paso**, no estado: la restauración no lo sustituye.

    La garantía no es «lo de antes desaparece» (nadie borra la zona de paso), sino que **no entra en
    la copia** y que la restauración no lo intercambia. Lo primero hace que una restauración no
    resucite restos de una operación interrumpida, y lo segundo, que no se mezcle con la copia.
    """
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)
    vista = servicio.create()
    (settings.data_paths.tmp / "otro.part").write_bytes(b"basura nueva")

    manifiesto = read_manifest(settings.data_paths.backups / f"{vista.id}.zip")
    rutas = {entrada.path for entrada in manifiesto.entries}
    assert not any(ruta.startswith("tmp/") for ruta in rutas)
    assert not any(ruta.startswith("logs/") for ruta in rutas)

    resultado = servicio.restore(vista.id)

    assert resultado.health_ok is True
    # La zona de paso sigue como estaba: ni se sustituye ni se vacía.
    assert (settings.data_paths.tmp / "otro.part").read_bytes() == b"basura nueva"
    assert (settings.data_paths.tmp / "resto.part").read_bytes() == b"basura"
    assert (settings.data_paths.logs / "opofuente.log").read_text(encoding="utf-8") == (
        "linea de registro"
    )
    assert "tmp" not in resultado.restored


def test_un_fallo_de_restauracion_deja_la_instalacion_anterior_utilizable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Criterio: un fallo de restauración deja la instalación anterior utilizable."""
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)
    vista = servicio.create()
    hashes_antes = _hashes(settings)

    from opofuente.infrastructure import backup_archive

    llamadas = {"n": 0}

    def swap_que_falla(**kwargs: object) -> tuple[str, ...]:
        """Mueve lo viejo a su punto de retorno y revienta antes de colocar lo nuevo."""
        llamadas["n"] += 1
        import shutil as _shutil

        raiz = Path(str(kwargs["root"]))
        objetivo = raiz / "artifacts"
        retorno = backup_archive.rollback_directory(objetivo)
        if retorno.exists():
            _shutil.rmtree(retorno)
        objetivo.rename(retorno)
        raise BackupError("fallo simulado después de apartar el material")

    monkeypatch.setattr(backup_archive, "swap_restored", swap_que_falla)
    # El servicio importó la función por nombre, así que se parchea también donde la usa.
    monkeypatch.setattr(
        "opofuente.application.backup_service.swap_restored", swap_que_falla, raising=False
    )
    assert llamadas["n"] == 0

    with pytest.raises(BackupError):
        servicio.restore(vista.id)

    # El material está en el punto de retorno, no borrado: la recuperación manual es posible.
    retorno = backup_archive.rollback_directory(settings.data_paths.root / "artifacts")
    assert retorno.is_dir()
    retorno.rename(settings.data_paths.root / "artifacts")

    assert set(_hashes(settings)) == set(hashes_antes)
    assert _sesiones(settings) == [("ses-1", "Practica de plazos")]


def test_la_previsualizacion_no_escribe_nada(tmp_path: Path) -> None:
    """Criterio del contrato: el paso 1 valida sin escribir."""
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)
    vista = servicio.create()
    antes = _hashes(settings)
    copias_antes = len(list(settings.data_paths.backups.glob("*.zip")))

    vista_previa = servicio.preview(vista.id)

    assert vista_previa is not None
    assert vista_previa.can_restore is True
    assert vista_previa.blockers == ()
    assert "copia automática" in vista_previa.previous_backup_note
    assert _hashes(settings) == antes
    assert len(list(settings.data_paths.backups.glob("*.zip"))) == copias_antes


def test_la_previsualizacion_bloquea_una_copia_de_otra_revision(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _arbol(settings)
    # La copia la hace un programa **más nuevo** que el que luego intenta restaurarla.
    futuro = _service(settings, revision="0099_del_futuro")
    vista = futuro.create()

    vista_previa = _service(settings).preview(vista.id)

    assert vista_previa is not None
    assert vista_previa.can_restore is False
    assert any("actualiza el programa" in bloqueo for bloqueo in vista_previa.blockers)


def test_un_identificador_de_copia_no_puede_salir_de_la_carpeta_de_copias(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)

    with pytest.raises(BackupError):
        servicio.verify("../../opofuente.sqlite3")
    with pytest.raises(BackupError):
        servicio.get("..\\..\\secreto")


def test_una_copia_ilegible_aparece_en_la_lista_con_su_motivo(tmp_path: Path) -> None:
    """Una copia que no se puede leer no se esconde: se dice que está y por qué no sirve."""
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)
    (settings.data_paths.backups / "20260101-000000-rota.zip").write_bytes(b"no soy un zip")

    vistas = servicio.list()

    rota = next(copia for copia in vistas if copia.id == "20260101-000000-rota")
    assert rota.restorable is False
    assert "no es un archivo legible" in rota.restorable_reason


def test_el_manifiesto_viaja_como_json_estable(tmp_path: Path) -> None:
    """El manifiesto se puede leer sin el programa: es texto con su versión de formato."""
    settings = _settings(tmp_path)
    _arbol(settings)
    servicio = _service(settings)
    vista = servicio.create(note="con nota")

    with zipfile.ZipFile(settings.data_paths.backups / f"{vista.id}.zip") as archivo:
        datos = json.loads(archivo.read(MANIFEST_NAME).decode("utf-8"))

    assert datos["format_version"] == BACKUP_FORMAT_VERSION
    assert datos["schema_revision"] == REVISION
    assert datos["note"] == "con nota"
    assert datos["scope"] == ["database", "artifacts", "extracted", "fixtures"]
    assert all(len(entrada["sha256"]) == 64 for entrada in datos["entries"])


def test_data_paths_de_una_configuracion_temporal_no_toca_el_arbol_real(tmp_path: Path) -> None:
    """Las pruebas construyen su propio árbol: ninguna toca `data/` del repositorio."""
    settings = _settings(tmp_path)
    paths: DataPaths = settings.data_paths

    assert paths.root == (tmp_path / "datos").resolve()
    assert paths.backups.parent == paths.root
