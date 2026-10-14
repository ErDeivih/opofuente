"""Importa los exámenes del INAP como exámenes practicables, por la ruta auditada (D10).

**Qué entra y qué no.** El manifiesto de `F:\\OpoFuente\\fuentes\\inap-tai` tiene **16
cuestionarios** con su plantilla. Este comando no inventa ninguno: convierte el PDF con
`opofuente.infrastructure.inap` (que respeta la numeración oficial y marca las reservas), comprueba
que la plantilla oficial **encaja** con el cuestionario y escribe por los **mismos métodos que usan
las rutas de la API** (`QuestionService.create_set`, `import_from_text`, `import_key_from_text`,
`set_distribution`, `set_origin_scope`), con su evento de auditoría. Un examen cuyo PDF no tiene
capa de texto (los tres de 2018) **no se importa**: se declara con su motivo en vez de
transcribirlo a mano.

**Ensayo por defecto.** Sin `--aplicar` no escribe nada: dice, examen a examen, qué preguntas saca
del documento, si la plantilla encaja y qué hay ya en la base. Con `--aplicar` importa lo que falta.

**Idempotente por título y tipo.** Un examen que ya está importado y cuya clave coincide con la
plantilla oficial **no se vuelve a importar**: se dice que ya estaba. Es la decisión que evita el
error del importador anterior, que se ejecutó dos veces y dejó ocho filas para cuatro exámenes.

**Una sola verdad, dicha.** Cuando el mismo examen ya vive en la base **como banco privado** (los
«examen completo, con su plantilla» de 2019, 2022 y 2024, y el `TAI_ejer_1_A_libre_AGE_2024` con la
numeración desplazada), este comando **no toca** el banco privado: importa el examen oficial, que es
la verdad practicable, y **dice** el solapamiento con sus cifras para que el propietario decida qué
hacer con la copia vieja.

Uso:
    # ver qué haría (no escribe nada)
    uv run python -m opofuente.tools.importar_inap
    # importar de verdad
    uv run python -m opofuente.tools.importar_inap --aplicar

Códigos de salida: 0 bien · 1 fallo.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from opofuente.application.question_models import QuestionSetView
from opofuente.application.question_service import QuestionService
from opofuente.application.read_models import OppositionSummary
from opofuente.config import Settings, get_settings
from opofuente.domain.questions import (
    Origin,
    OriginScope,
    SetType,
    ordered_key_mapping,
    parse_answer_key,
    parse_questions,
)
from opofuente.domain.topic_notes import firma_de_grupo
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository
from opofuente.infrastructure.inap import (
    Cuestionario,
    extraer_cuestionario,
    secciones_de_plantilla,
    texto_de_importacion,
    texto_de_plantilla,
)
from opofuente.infrastructure.profile_repository import SqlAlchemyProfileRepository
from opofuente.infrastructure.question_repository import SqlAlchemyQuestionRepository
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente.tools.inap_biblioteca import ApiInalcanzableError, enlazar_plantilla

#: Dónde están los PDF descargados y verificados (con su manifiesto y sus sha256).
FUENTES_POR_DEFECTO = Path(r"F:\OpoFuente\fuentes\inap-tai")


@dataclass(frozen=True, slots=True)
class Examen:
    """Un examen del INAP: su documento, su plantilla y cómo se titula en la base."""

    titulo: str
    cuestionario: str
    plantilla: str
    #: `definitiva` o `provisional`: la provisional se importa igual (es la única que hay), pero
    #: **se dice** cuál es, porque una definitiva puede cambiarla.
    plantilla_tipo: str
    modelo: str | None = None
    held_at: date | None = None
    notas: tuple[str, ...] = ()


#: Los 16 cuestionarios del manifiesto, en el orden del INAP. Los tres de 2018 se declaran aquí para
#: que su ausencia sea una decisión con motivo y no un olvido: no tienen capa de texto y el proyecto
#: no tiene OCR instalado (`OPOFUENTE_TESSERACT_PATH` sin binario).
EXAMENES: tuple[Examen, ...] = (
    Examen(
        titulo="TAI ingreso libre 2018 · primer ejercicio (examen oficial INAP)",
        cuestionario="TAI-2018-libre-cuestionario-1.pdf",
        plantilla="TAI-2018-libre-plantilla-definitiva-1.pdf",
        plantilla_tipo="definitiva",
        notas=("el cuestionario es un escaneo sin capa de texto",),
    ),
    Examen(
        titulo="TAI ingreso libre 2018 · segundo ejercicio (examen oficial INAP)",
        cuestionario="TAI-2018-libre-cuestionario-2.pdf",
        plantilla="TAI-2018-libre-plantilla-definitiva-2.pdf",
        plantilla_tipo="definitiva",
        notas=("el cuestionario es un escaneo sin capa de texto",),
    ),
    Examen(
        titulo="TAI promoción interna 2018 · ejercicio único (examen oficial INAP)",
        cuestionario="TAI-2018-pi-cuestionario-unico.pdf",
        plantilla="TAI-2018-pi-plantilla-definitiva-unico.pdf",
        plantilla_tipo="definitiva",
        notas=("el cuestionario es un escaneo sin capa de texto",),
    ),
    Examen(
        titulo="TAI ingreso libre 2019 · ejercicio único (examen oficial INAP)",
        cuestionario="TAI-2019-libre-cuestionario-unico.pdf",
        plantilla="TAI-2019-libre-plantilla-definitiva-unico.pdf",
        plantilla_tipo="definitiva",
    ),
    Examen(
        titulo="TAI promoción interna 2019 · ejercicio único (examen oficial INAP)",
        cuestionario="TAI-2019-pi-cuestionario-unico.pdf",
        plantilla="TAI-2019-pi-plantilla-definitiva-unico.pdf",
        plantilla_tipo="definitiva",
    ),
    Examen(
        titulo="TAI ingreso libre 2022 · ejercicio único (examen oficial INAP)",
        cuestionario="TAI-2022-libre-cuestionario-unico.pdf",
        plantilla="TAI-2022-libre-plantilla-definitiva-unico.pdf",
        plantilla_tipo="definitiva",
    ),
    Examen(
        titulo="TAI promoción interna 2022 · ejercicio único (examen oficial INAP)",
        cuestionario="TAI-2022-pi-cuestionario-unico.pdf",
        plantilla="TAI-2022-pi-plantilla-definitiva-unico.pdf",
        plantilla_tipo="definitiva",
    ),
    Examen(
        titulo="TAI ingreso libre 2024 · modelo A (examen oficial INAP)",
        cuestionario="TAI-2024-libre-cuestionario-unico-A.pdf",
        plantilla="TAI-2024-libre-plantilla-definitiva-unico-A.pdf",
        plantilla_tipo="definitiva",
        modelo="A",
    ),
    Examen(
        titulo="TAI ingreso libre 2024 · modelo B (examen oficial INAP)",
        cuestionario="TAI-2024-libre-cuestionario-unico-B.pdf",
        plantilla="TAI-2024-libre-plantilla-definitiva-unico-B.pdf",
        plantilla_tipo="definitiva",
        modelo="B",
    ),
    Examen(
        titulo="TAI promoción interna 2024 · modelo A (examen oficial INAP)",
        cuestionario="TAI-2024-pi-cuestionario-unico-A.pdf",
        plantilla="TAI-2024-pi-plantilla-definitiva-unico-A.pdf",
        plantilla_tipo="definitiva",
        modelo="A",
    ),
    Examen(
        titulo="TAI promoción interna 2024 · modelo B (examen oficial INAP)",
        cuestionario="TAI-2024-pi-cuestionario-unico-B.pdf",
        plantilla="TAI-2024-pi-plantilla-definitiva-unico-B.pdf",
        plantilla_tipo="definitiva",
        modelo="B",
    ),
    Examen(
        titulo="TAI ingreso libre 2025 · modelo A (examen oficial INAP)",
        cuestionario="TAI-2025-libre-cuestionario-unico-A.pdf",
        plantilla="TAI-2025-libre-plantilla-provisional-unico-A.pdf",
        plantilla_tipo="provisional",
        modelo="A",
    ),
    Examen(
        titulo="TAI ingreso libre 2025 · modelo B (examen oficial INAP)",
        cuestionario="TAI-2025-libre-cuestionario-unico-B.pdf",
        plantilla="TAI-2025-libre-plantilla-provisional-unico-B.pdf",
        plantilla_tipo="provisional",
        modelo="B",
    ),
    Examen(
        titulo="TAI ingreso libre 2025 · extraordinario (examen oficial INAP)",
        cuestionario="TAI-2025-libre-cuestionario-extraordinario.pdf",
        plantilla="TAI-2025-libre-plantilla-provisional-extraordinario.pdf",
        plantilla_tipo="provisional",
    ),
    Examen(
        titulo="TAI promoción interna 2025 · modelo A (examen oficial INAP)",
        cuestionario="TAI-2025-pi-cuestionario-unico-A.pdf",
        plantilla="TAI-2025-pi-plantilla-definitiva-unico-A.pdf",
        plantilla_tipo="definitiva",
        modelo="A",
    ),
    Examen(
        titulo="TAI promoción interna 2025 · modelo B (examen oficial INAP)",
        cuestionario="TAI-2025-pi-cuestionario-unico-B.pdf",
        plantilla="TAI-2025-pi-plantilla-definitiva-unico-B.pdf",
        plantilla_tipo="definitiva",
        modelo="B",
    ),
)


@dataclass(slots=True)
class Lectura:
    """Lo que dice el documento de un examen, ya convertido y comprobado contra su plantilla."""

    examen: Examen
    cuestionario: Cuestionario | None = None
    preguntas: int = 0
    ordinarias: int = 0
    reservas: int = 0
    secciones: tuple[int, ...] = ()
    claves: int = 0
    encaje_en_orden: bool = False
    #: Posiciones de la clave que no encuentran pregunta (por número): el choque, con sus números.
    sin_pareja: tuple[int, ...] = ()
    posiciones_repetidas: bool = False
    motivo: str | None = None


def _leer(examen: Examen, fuentes: Path) -> Lectura:
    """Convierte el cuestionario y comprueba que la plantilla encaja, sin tocar ninguna base."""
    cuestionario = extraer_cuestionario(fuentes / examen.cuestionario)
    if not cuestionario.preguntas:
        motivo = (
            cuestionario.descartes[0].detalle
            if cuestionario.descartes
            else "el cuestionario no tiene preguntas"
        )
        return Lectura(examen=examen, motivo=motivo)

    texto = texto_de_importacion(cuestionario)
    parseado = parse_questions(texto)
    lineas, _incidencias = parse_answer_key(texto_de_plantilla(fuentes / examen.plantilla))
    posiciones = [pregunta.number or 0 for pregunta in parseado.questions]
    repetidas = len(posiciones) != len(set(posiciones))
    en_orden = ordered_key_mapping(
        lineas,
        tuple((f"q{indice}", posicion) for indice, posicion in enumerate(posiciones)),
    )
    # Por número: lo que pasaría si la numeración **no** se reiniciara en cada sección. Una posición
    # con más de una pregunta queda ambigua, y ese es el choque que el importador declara.
    por_posicion: dict[int, int] = {}
    for posicion in posiciones:
        por_posicion[posicion] = por_posicion.get(posicion, 0) + 1
    sin_pareja = tuple(
        sorted({linea.position for linea in lineas if por_posicion.get(linea.position, 0) != 1})
    )
    secciones = tuple(
        len(seccion.lineas)
        for seccion in secciones_de_plantilla(fuentes / examen.plantilla)
        if seccion.lineas
    )
    return Lectura(
        examen=examen,
        cuestionario=cuestionario,
        preguntas=len(parseado.questions),
        ordinarias=sum(1 for pregunta in parseado.questions if not pregunta.is_reserve),
        reservas=sum(1 for pregunta in parseado.questions if pregunta.is_reserve),
        secciones=secciones,
        claves=len(lineas),
        encaje_en_orden=en_orden is not None and len(lineas) == len(parseado.questions),
        sin_pareja=sin_pareja,
        posiciones_repetidas=repetidas,
    )


def _firmas_de(texto_preguntas: Sequence[tuple[str, tuple[tuple[str, str], ...]]]) -> set[str]:
    return {firma_de_grupo(stem, opciones) for stem, opciones in texto_preguntas}


def _firmas_del_banco(servicio: QuestionService, oposicion: str) -> dict[str, set[str]]:
    """Las firmas de las preguntas de cada conjunto del banco, en una pasada."""
    firmas: dict[str, set[str]] = {}
    for vista in _conjuntos_del_examen(servicio, oposicion):
        paginas = servicio.questions(set_id=vista.id, limit=200, include_key=False)
        if not paginas.questions:
            continue
        firmas[vista.id] = _firmas_de(
            [
                (
                    pregunta.stem,
                    tuple((opcion.stable_key, opcion.text) for opcion in pregunta.options),
                )
                for pregunta in paginas.questions
            ]
        )
    return firmas


@dataclass(slots=True)
class YaEnLaBase:
    """Un conjunto que ya está en la base y se parece a este examen."""

    set_id: str
    title: str
    set_type: str
    status: str
    distribution: str
    origin_scope: str
    questions: int
    reserve_count: int
    #: Qué fracción del documento del examen está dentro de ese conjunto.
    cobertura: float
    es_el_mismo_documento: bool


#: A partir de qué fracción del documento se dice «este conjunto **es** el mismo examen». Medido el
#: 13 de octubre de 2026 sobre la base real: las cuatro copias que de verdad son el mismo examen
#: cubren el **98,5 %, 100 %, 99,3 % y 97,8 %** del documento, y lo que más se le acerca sin serlo
#: —el mismo examen del año entre ingreso libre y promoción interna, que comparten parte del
#: temario— se queda en el **58,8 %**. El listón en el 90 % los separa sin tocar ninguno.
MISMO_DOCUMENTO = 0.90

#: A partir de qué fracción se **declara** una copia parcial (no es el mismo examen, pero comparte
#: preguntas y conviene saberlo): el `TAI_ejer_1_A_libre_AGE_2024` cubre el 57,8 % del documento.
COPIA_PARCIAL = 0.20


def _conjuntos_del_examen(servicio: QuestionService, oposicion: str) -> tuple[QuestionSetView, ...]:
    return servicio.sets(opposition_id=oposicion, limit=500).sets


def _parecidos(
    servicio: QuestionService,
    oposicion: str,
    examen: Examen,
    firmas_del_documento: set[str],
    *,
    firmas_por_conjunto: Mapping[str, set[str]] | None = None,
) -> list[YaEnLaBase]:
    """Los conjuntos que ya existen con el mismo título o con el mismo contenido.

    Dos caminos, y los dos hacen falta:

    - **el título**: es como este comando deja sus conjuntos, y repetir el título es duplicar;
    - **el contenido**: varios exámenes del INAP ya viven en la base como **banco privado** («TAI
      ingreso libre 2019 (examen completo, con su plantilla)», `TAI_ejer_1_A_libre_AGE_2024`). Se
      comparan las **firmas** (enunciado y opciones normalizados) y se dice el solapamiento con su
      cifra, que es lo que permite contar «esto ya está, con otro nombre y con otra numeración».

    `firmas_por_conjunto` se calcula **una vez** para todos los exámenes: recorrer los 231 conjuntos
    del banco por cada examen convertiría una comprobación en una espera.
    """
    encontrados: list[YaEnLaBase] = []
    for vista in _conjuntos_del_examen(servicio, oposicion):
        mismo_titulo = str(vista.title).strip() == examen.titulo
        firmas = None if mismo_titulo else (firmas_por_conjunto or {}).get(vista.id)
        cobertura = (
            0.0
            if not firmas
            else len(firmas & firmas_del_documento) / max(1, len(firmas_del_documento))
        )
        if mismo_titulo or cobertura >= COPIA_PARCIAL:
            encontrados.append(
                YaEnLaBase(
                    set_id=vista.id,
                    title=str(vista.title),
                    set_type=str(vista.set_type),
                    status=str(vista.status),
                    distribution=str(vista.distribution),
                    origin_scope=str(vista.origin_scope),
                    questions=int(vista.question_count),
                    reserve_count=int(vista.reserve_count),
                    cobertura=cobertura,
                    es_el_mismo_documento=cobertura >= MISMO_DOCUMENTO,
                )
            )
    return encontrados


@dataclass(slots=True)
class Resultado:
    examen: Examen
    estado: str
    detalle: str
    set_id: str | None = None
    creadas: int = 0
    claves: int = 0
    conflictos: int = 0
    sin_pareja: tuple[int, ...] = ()
    #: Si su clave quedó **activa** (el examen se puede hacer) o sigue en borrador.
    clave_activa: bool = False
    avisos: list[str] = field(default_factory=list)


def _importar_uno(
    servicio: QuestionService,
    *,
    oposicion: str,
    convocatoria: str | None,
    examen: Examen,
    fuentes: Path,
    lectura: Lectura,
) -> Resultado:
    """Crea el conjunto, mete sus preguntas con la numeración oficial y aplica la plantilla."""
    if lectura.cuestionario is None or not lectura.preguntas:
        return Resultado(examen=examen, estado="fuera", detalle=lectura.motivo or "sin preguntas")
    if not lectura.encaje_en_orden:
        # Sin encaje no se importa: meter las preguntas y dejar la plantilla sin aplicar daría un
        # examen que se ofrece y no se puede corregir. Se dice con los números del choque.
        return Resultado(
            examen=examen,
            estado="choque",
            detalle=(
                f"la plantilla no encaja en orden con el cuestionario "
                f"({lectura.claves} líneas de clave, {lectura.preguntas} preguntas; "
                f"posiciones sin pareja {list(lectura.sin_pareja)[:8]})"
            ),
        )

    creado = servicio.create_set(
        examen.titulo,
        opposition_id=oposicion,
        set_type=SetType.OFFICIAL_EXAM.value,
        convocation_version_id=convocatoria,
        model_code=examen.modelo,
        held_at=examen.held_at,
        origin_scope=OriginScope.AGE.value,
        actor=ACTOR,
    )
    informe = servicio.import_from_text(
        creado.id,
        texto_de_importacion(lectura.cuestionario),
        origin_type=Origin.OFFICIAL,
        actor=ACTOR,
    )
    # La clave, **tal cual viene en la plantilla**: ni una letra se toca aquí.
    clave = servicio.import_key_from_text(
        creado.id, texto_de_plantilla(fuentes / examen.plantilla), actor=ACTOR
    )
    servicio.set_distribution(creado.id, "public", actor=ACTOR)
    avisos: list[str] = []
    if lectura.examen.plantilla_tipo != "definitiva":
        avisos.append(
            "la plantilla es **provisional**: cuando aparezca la definitiva habrá que "
            "reimportar la clave"
        )
    if clave.unmatched:
        # Preguntas del conjunto que la plantilla no cubre: se dice, no se rellena.
        avisos.append(
            f"la plantilla no cubre {len(clave.unmatched)} posición(es): "
            f"{list(clave.unmatched)[:10]}"
        )
    if informe.parts_detected:
        avisos.append(f"rótulos de parte vistos: {', '.join(informe.parts_detected)}")
    return Resultado(
        examen=examen,
        estado="importado",
        detalle=f"{informe.created} preguntas creadas, {informe.existing} ya estaban",
        set_id=creado.id,
        creadas=int(informe.created),
        claves=int(informe.key_entries),
        conflictos=len(informe.conflicts),
        sin_pareja=tuple(clave.unmatched),
        avisos=avisos,
    )


#: Quién firma los cambios en la auditoría: el comando de esta tanda, ni una persona ni el modelo.
ACTOR = "f23:inap"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Importa los exámenes del INAP (D10).")
    parser.add_argument("--fuentes", type=Path, default=FUENTES_POR_DEFECTO)
    parser.add_argument(
        "--aplicar", action="store_true", help="escribe de verdad (sin esto, solo dice qué haría)"
    )
    parser.add_argument(
        "--api",
        default=None,
        help=(
            "dirección de la API levantada (por ejemplo http://127.0.0.1:8799). Con ella se da la "
            "segunda mitad: subir la plantilla a la biblioteca, enlazarla a la clave y activarla, "
            "que es lo que deja el examen practicable"
        ),
    )
    parser.add_argument(
        "--solo",
        action="append",
        default=None,
        help="importa solo los exámenes cuyo cuestionario contenga este texto (repetible)",
    )
    return parser.parse_args(list(argv))


def _use_utf8_stdout() -> None:
    for flujo in (sys.stdout, sys.stderr):
        reconfigure = getattr(flujo, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8_stdout()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.fuentes.is_dir():
        print(f"no encuentro los PDF en {args.fuentes}", file=sys.stderr)
        return 1

    settings: Settings = get_settings()
    settings.data_paths.ensure_directories()
    engine = build_engine(settings.data_paths.database)
    elegidos = [
        examen
        for examen in EXAMENES
        if not args.solo or any(filtro in examen.cuestionario for filtro in args.solo)
    ]
    try:
        session_factory = build_session_factory(engine)
        servicio = QuestionService(
            questions=SqlAlchemyQuestionRepository(session_factory),
            clock=SystemClock(),
            documents=SqlAlchemyDocumentRepository(
                session_factory, RepresentationStore(settings.data_paths)
            ),
        )
        oposicion = _oposicion_tai(settings, session_factory)
        if oposicion is None:
            print("no encuentro la oposición de TAI en la base", file=sys.stderr)
            return 1
        convocatoria = oposicion.convocation_id
        # Las firmas de **todos** los conjuntos del banco, una sola vez: comparar cada examen contra
        # los 231 conjuntos, uno a uno, convertiría una comprobación en una espera de minutos.
        firmas_por_conjunto = _firmas_del_banco(servicio, oposicion.id)
        print(f"banco: {len(firmas_por_conjunto)} conjuntos con preguntas en esta oposición")

        resultados: list[Resultado] = []
        for examen in elegidos:
            lectura = _leer(examen, args.fuentes)
            print("=" * 100)
            print(examen.titulo)
            print(f"  documento : {examen.cuestionario}")
            if lectura.cuestionario is None or not lectura.preguntas:
                print(f"  FUERA     : {lectura.motivo}")
                resultados.append(
                    Resultado(examen=examen, estado="fuera", detalle=lectura.motivo or "")
                )
                continue
            print(
                f"  extraído  : {lectura.preguntas} preguntas "
                f"({lectura.ordinarias} ordinarias, {lectura.reservas} reservas), "
                f"secciones {list(lectura.secciones)}"
            )
            print(
                f"  plantilla : {lectura.claves} líneas ({examen.plantilla_tipo}) — "
                f"encaje en orden: {'sí' if lectura.encaje_en_orden else 'NO'}"
            )
            preguntas_del_documento = parse_questions(
                texto_de_importacion(lectura.cuestionario)
            ).questions
            firmas = _firmas_de(
                [
                    (
                        pregunta.stem,
                        tuple((opcion.stable_key, opcion.text) for opcion in pregunta.options),
                    )
                    for pregunta in preguntas_del_documento
                ]
            )
            parecidos = _parecidos(
                servicio, oposicion.id, examen, firmas, firmas_por_conjunto=firmas_por_conjunto
            )
            for parecido in parecidos:
                if parecido.es_el_mismo_documento:
                    marca = "MISMO DOCUMENTO"
                elif str(parecido.title).strip() == examen.titulo:
                    marca = "mismo título"
                else:
                    marca = "copia parcial"
                print(
                    f"  ya en base: {parecido.set_id} [{parecido.status}, {parecido.distribution}, "
                    f"{parecido.origin_scope}] {parecido.questions} preguntas "
                    f"({parecido.reserve_count} reservas) · {marca} "
                    f"({round(parecido.cobertura * 100)} % del documento): {parecido.title}"
                )
            if not args.aplicar:
                print("  (ensayo: no se escribe nada)")
                resultados.append(Resultado(examen=examen, estado="ensayo", detalle=""))
                continue
            ya = [p for p in parecidos if str(p.title).strip() == examen.titulo]
            if ya:
                # Idempotencia: el mismo examen, ya importado. No se duplica.
                print(f"  YA ESTÁ   : {ya[0].set_id} — no se vuelve a importar")
                resultados.append(
                    Resultado(
                        examen=examen,
                        estado="ya_estaba",
                        detalle=ya[0].title,
                        set_id=ya[0].set_id,
                    )
                )
                continue
            resultado = _importar_uno(
                servicio,
                oposicion=oposicion.id,
                convocatoria=convocatoria,
                examen=examen,
                fuentes=args.fuentes,
                lectura=lectura,
            )
            print(f"  {resultado.estado.upper():9s} : {resultado.detalle}")
            for aviso in resultado.avisos:
                print(f"              · {aviso}")
            resultados.append(resultado)

        if args.api is not None:
            _dejar_practicables(
                args.api,
                servicio=servicio,
                oposicion=oposicion.id,
                fuentes=args.fuentes,
                resultados=resultados,
                elegidos=elegidos,
            )

        print("=" * 100)
        print("RESUMEN")
        for resultado in resultados:
            print(
                f"  {resultado.estado:12s} "
                f"{'clave activa' if resultado.clave_activa else 'clave SIN activar':18s} "
                f"{resultado.examen.titulo}"
            )
        return 0
    finally:
        engine.dispose()


def _dejar_practicables(
    api: str,
    *,
    servicio: QuestionService,
    oposicion: str,
    fuentes: Path,
    resultados: list[Resultado],
    elegidos: Sequence[Examen],
) -> None:
    """La segunda mitad: la plantilla entra en la biblioteca y la clave queda activa.

    Sin esto, un examen oficial **se ve y no se puede hacer**: su clave se queda en borrador porque
    la invariante no deja activarla sin la plantilla oficial enlazada. Se hace por las rutas de la
    API porque la extracción la ejecuta su worker.
    """
    por_titulo = {
        str(vista.title).strip(): vista
        for vista in servicio.sets(opposition_id=oposicion, limit=500).sets
    }
    for resultado in resultados:
        if resultado.examen not in elegidos or resultado.estado not in {"importado", "ya_estaba"}:
            continue
        vista = por_titulo.get(resultado.examen.titulo)
        if vista is None:
            continue
        claves = servicio.keys(vista.id)
        if any(str(clave.status) == "active" for clave in claves):
            resultado.clave_activa = True
            print(f"  CLAVE     : ya estaba activa ({vista.title})")
            continue
        print(f"  BIBLIOTECA: subo la plantilla de {resultado.examen.titulo}")
        try:
            enlace = enlazar_plantilla(
                api,
                plantilla=fuentes / resultado.examen.plantilla,
                titulo_documento=(
                    "Plantilla de respuestas · "
                    f"{resultado.examen.titulo.replace(' (examen oficial INAP)', '')} (INAP)"
                ),
                set_id=vista.id,
                etiqueta_de_version=resultado.examen.plantilla_tipo,
            )
        except (RuntimeError, ApiInalcanzableError) as error:
            resultado.avisos.append(f"no se pudo dejar practicable: {error}")
            print(f"              · no se pudo dejar practicable: {error}")
            continue
        resultado.clave_activa = enlace.activa
        print(f"              · {enlace.detalle}")


def _oposicion_tai(settings: Settings, session_factory: object) -> OppositionSummary | None:
    """La oposición que sirve la zona del alumno, por el **código configurado** y no a mano.

    El mismo camino que usa el motor para saber qué cuerpo sirve (`OPOFUENTE_STUDENT_OPPOSITION`):
    escribir el identificador aquí sería tener dos verdades sobre qué oposición es «la de TAI».
    """
    perfiles = SqlAlchemyProfileRepository(session_factory)  # type: ignore[arg-type]
    for oposicion in perfiles.list_oppositions():
        if oposicion.code == settings.student_opposition:
            return oposicion
    return None


__all__ = ["ACTOR", "EXAMENES", "Examen", "main", "parse_args"]


if __name__ == "__main__":
    raise SystemExit(main())
