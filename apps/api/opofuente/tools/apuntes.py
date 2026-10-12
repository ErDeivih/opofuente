"""Los apuntes de un tema, guiados por sus preguntas (pasos B-E del plan, los tres pilotos).

Es el comando del piloto: coge las preguntas **ya clasificadas** de un tema, escribe con el modelo
los
hechos que hay que saber, monta el esquema con los epígrafes oficiales, redacta cada apartado con
todos
sus hechos y el material del tema, y comprueba **pregunta a pregunta** que los apuntes la contestan.
Al final guarda el tema como versión (el mecanismo de versiones del dossier, que ya existía).

Uso:
    # ver lo que hay en un tema, sin llamar a nadie
    uv run python -m opofuente.tools.apuntes --tema IV.7 --listar
    # el indice por materias del tema, sin llamar a nadie (el esquema, antes de redactar)
    uv run python -m opofuente.tools.apuntes --tema IV.7 --esquema
    # cómo está el tema **guardado**, sin llamar a nadie: cobertura y forma, medidas
    uv run python -m opofuente.tools.apuntes --tema IV.7 --medir
    # escribir los apuntes del tema (llama al modelo)
    $env:DEEPSEEK_API_KEY = "…"
    uv run python -m opofuente.tools.apuntes --tema IV.7
    # escribir, pero no dar el tema por bueno si no pasa las comprobaciones de forma
    uv run python -m opofuente.tools.apuntes --tema IV.7 --exigir-calidad
    # los tres pilotos, de una vez
    uv run python -m opofuente.tools.apuntes --tema IV.7 --tema I.6 --tema I.1

La clave se lee de `DEEPSEEK_API_KEY`. **No** se escribe en ningún fichero del repositorio, ni en un
log, ni en este comando: si no está, el comando lo dice y para. Una corrida sin clave gastaría horas
de trabajo para nada.

Códigos de salida: 0 bien · 1 fallo al escribir los apuntes · 2 falta la clave · 3 el tema no pasa
las comprobaciones de forma (con `--exigir-calidad`, no se archiva la versión).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from typing import NoReturn

from opofuente.application.dossier_service import DossierService
from opofuente.application.topic_notes_models import TopicNotesReport
from opofuente.application.topic_notes_service import TopicNotesService
from opofuente.config import Settings, get_settings
from opofuente.domain.errors import OpoFuenteError
from opofuente.domain.notes_quality import (
    escapar_tuberias_en_celdas,
    limpiar_andamios,
    marcas_internas,
    nombrar_columnas_sin_titulo,
    revisar_apuntes,
    sin_encabezados_repetidos,
    sin_encabezados_repetidos_en_el_tema,
    titulos_que_cambian,
)
from opofuente.domain.puertos import limpiar_tabla_de_puertos
from opofuente.domain.topic_index import (
    MAX_HECHOS_POR_APARTADO,
    catalogo,
    es_la_tabla_de_puertos,
    indice_de,
    plan_de,
    revisar_indice,
)
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.dossier_repository import SqlAlchemyDossierRepository
from opofuente.infrastructure.run_lock import CLAVE_APUNTES, ClassificationRunLock
from opofuente.infrastructure.topic_notes_client import (
    BASE_URL_POR_DEFECTO,
    MODELO_POR_DEFECTO,
    DeepSeekNotesModel,
)
from opofuente.infrastructure.topic_notes_repository import SqlAlchemyTopicNotesRepository

#: La variable de la que se lee la clave. Es lo único que se necesita configurar para escribir.
VARIABLE_DE_LA_CLAVE = "DEEPSEEK_API_KEY"

#: Los tres temas del piloto que fijó el propietario (`DECISIONES-Y-SIGUIENTE-TANDA` §6).
PILOTOS = ("IV.7", "I.6", "I.1")


class _ModeloQueNoSeUsa:
    """El motor de `--medir`: mide lo guardado y **no** llama a nadie.

    Existe para que medir un tema no pueda costar dinero ni por accidente: si algún camino de la
    medida acabara pidiendo algo al modelo, esto lo dice en vez de gastar. Es la misma garantía que
    el `--listar` y el `--esquema`, pero con el tipo del puerto para que el servicio esté completo.
    """

    name = "sin-modelo"

    @property
    def version(self) -> str:
        return "sin-modelo"

    @staticmethod
    def _no() -> NoReturn:
        raise RuntimeError("`--medir` no llama al modelo: la medida se hace sobre lo guardado")

    def hechos(self, *_args: object, **_kwargs: object) -> NoReturn:
        self._no()

    def redactar(self, *_args: object, **_kwargs: object) -> NoReturn:
        self._no()

    def comprobar(self, *_args: object, **_kwargs: object) -> NoReturn:
        self._no()

    def anadir(self, *_args: object, **_kwargs: object) -> NoReturn:
        self._no()


def _use_utf8_stdout() -> None:
    """El informe lleva acentos y comillas angulares: en Windows, redirigido, saldría en la
    codificación local y no se podría comparar entre máquinas."""
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Las opciones del comando, con los valores por defecto en su ayuda."""
    parser = argparse.ArgumentParser(
        prog="opofuente.tools.apuntes",
        description="Escribe los apuntes de un tema a partir de sus preguntas y los comprueba.",
    )
    parser.add_argument(
        "--tema",
        action="append",
        default=None,
        metavar="CODIGO",
        help=f"tema del programa, repetible (por defecto, los pilotos: {', '.join(PILOTOS)})",
    )
    parser.add_argument(
        "--medir",
        action="store_true",
        help=(
            "mide el tema **guardado** sin llamar a nadie: la cobertura de sus comprobaciones "
            "(con los dos denominadores de la puerta) y las comprobaciones de forma. Es el número "
            "que va al informe, medido y no heredado"
        ),
    )
    parser.add_argument(
        "--limpiar-forma",
        dest="limpiar_forma",
        action="store_true",
        help=(
            "vuelve a pasar las reparaciones de forma al texto **ya escrito**: nombra las columnas "
            "de tabla que se quedaron sin título y quita los encabezados que repiten otro del "
            "mismo apartado. No llama al modelo y no archiva versión"
        ),
    )
    parser.add_argument(
        "--prever",
        action="store_true",
        help=(
            "dice lo que le haría una corrida al tema **sin llamar a nadie**: qué apartados se "
            "conservan, cuáles se vuelven a redactar (y cuántas llamadas son) y cuáles se tiran. Es"
            ""
            "lo que evita pagar dos veces por lo mismo sin enterarse"
        ),
    )
    parser.add_argument(
        "--publicar",
        action="store_true",
        help=(
            "mide las dos puertas sobre lo **ya guardado** y, si las pasa, archiva la versión del "
            "tema (y si no, la retira con su motivo). No llama al modelo: publicar no puede costar "
            "una corrida"
        ),
    )
    parser.add_argument(
        "--listar",
        action="store_true",
        help="enseña lo que hay en el tema (preguntas, hechos y apartados) sin llamar al modelo",
    )
    parser.add_argument(
        "--esquema",
        action="store_true",
        help=(
            "enseña el índice por materias del tema (el esquema antes de redactar): qué apartados "
            "tendrá y qué hechos van en cada uno, sin llamar al modelo"
        ),
    )
    parser.add_argument(
        "--exigir-calidad",
        dest="exigir_calidad",
        action="store_true",
        help=(
            "no da el tema por bueno si no pasa las comprobaciones de forma (encabezados "
            "repetidos, marcas internas, tablas sin cabecera, párrafos repetidos y extensión): no "
            "archiva la versión y sale con código 3"
        ),
    )
    parser.add_argument(
        "--limpiar-andamios",
        dest="limpiar_andamios",
        action="store_true",
        help=(
            "quita del texto ya escrito las marcas internas que el redactor copió de su encargo "
            "(`[Hecho 3]` y compañía) y no llama a nadie: es una limpieza, no una redacción. No se "
            "archiva versión"
        ),
    )
    parser.add_argument(
        "--limpiar-puertos",
        dest="limpiar_puertos",
        action="store_true",
        help=(
            "vuelve a pasar la limpieza de la tabla de puertos al texto **ya escrito** (la parte "
            "por familias, le quita las notas de distractor y recoge las confusiones de verdad) y "
            "enseña la revisión de forma del tema. No llama al modelo y no archiva versión"
        ),
    )
    parser.add_argument(
        "--olvidar-apartado",
        dest="olvidar_apartado",
        action="append",
        default=None,
        metavar="CLAVE",
        help=(
            "borra el texto de un apartado para que la próxima corrida lo vuelva a redactar (y "
            "vuelva a comprobar sus preguntas): es la corrección de un apartado que no pasa la "
            "revisión de forma, sin rehacer el tema entero. Repetible: con la opción varias veces"
            "se "
            "olvidan varios apartados de una vez, que es como se rehace un tema que no pasa la "
            "puerta de extensión. No llama al modelo"
        ),
    )
    parser.add_argument(
        "--dry-run",
        "--seco",
        dest="dry_run",
        action="store_true",
        help="llama al modelo y dice lo que haría, pero no escribe nada",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        metavar="N",
        help="como mucho N grupos de preguntas (para probar sin gastar en el tema entero)",
    )
    parser.add_argument(
        "--sin-version",
        dest="version",
        action="store_false",
        help="no guarda el tema como versión al terminar",
    )
    parser.add_argument(
        "--modelo", default=MODELO_POR_DEFECTO, help=f"modelo (por defecto {MODELO_POR_DEFECTO})"
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL_POR_DEFECTO,
        help=f"endpoint del modelo (por defecto {BASE_URL_POR_DEFECTO})",
    )
    parser.add_argument(
        "--paralelo",
        type=int,
        default=4,
        metavar="N",
        help="llamadas al modelo a la vez (por defecto 4; 1 es secuencial)",
    )
    parser.add_argument(
        "--tiempo",
        type=float,
        default=300.0,
        metavar="SEGUNDOS",
        help="tiempo máximo por llamada (por defecto 300)",
    )
    parser.add_argument(
        "--tiempo-maximo",
        dest="tiempo_maximo",
        type=float,
        default=0.0,
        metavar="SEGUNDOS",
        help=(
            "tope de tiempo de la corrida **entera**, sumando todas las llamadas (0 = sin tope, el "
            "valor por defecto). Al agotarse no se empieza ninguna llamada más: lo escrito se "
            "queda "
            "escrito y volver a lanzar el comando sigue desde ahí"
        ),
    )
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8_stdout()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    settings: Settings = get_settings()
    settings.data_paths.ensure_directories()
    temas: list[str] = list(args.tema) if args.tema else list(PILOTOS)

    engine = build_engine(settings.data_paths.database)
    try:
        session_factory = build_session_factory(engine)
        notas = SqlAlchemyTopicNotesRepository(session_factory)
        dossier_service = DossierService(
            repository=SqlAlchemyDossierRepository(session_factory),
            clock=SystemClock(),
            notes=notas,
        )
        if args.listar:
            # Sin clave y sin modelo: ver lo que hay no cuesta nada y es lo primero que se mira.
            for tema in temas:
                print("\n".join(_listar(notas, tema)))
            return 0
        if args.prever:
            # Lo que costaría una corrida, antes de pagarla: tampoco llama a nadie ni necesita
            # clave.
            servicio = TopicNotesService(
                repository=notas,
                dossier=SqlAlchemyDossierRepository(session_factory),
                model=_ModeloQueNoSeUsa(),
                workers=1,
            )
            for tema in temas:
                print("\n".join(servicio.prever(tema)))
                print()
            return 0
        if args.publicar:
            # Publicar es archivar la versión del tema si las dos puertas pasan, y no cuesta
            # llamadas:
            # la medida sale de lo guardado. Antes, la única forma de publicar era volver a pagar
            # una
            # corrida entera por un tema cuyo texto ya estaba escrito y medido.
            servicio = TopicNotesService(
                repository=notas,
                dossier=SqlAlchemyDossierRepository(session_factory),
                model=_ModeloQueNoSeUsa(),
                workers=1,
            )
            for tema in temas:
                informe = servicio.medir(tema)
                _decidir_y_archivar(
                    informe,
                    dossier_service=dossier_service,
                    exigir_calidad=True,
                    version=True,
                    dry_run=False,
                )
                print("\n".join(informe.lines()))
                print()
            return 0
        if args.medir:
            # La medida del tema guardado: tampoco llama a nadie ni necesita clave. Una cifra que va
            # a un documento se mide, no se hereda, y medirla no puede costar dinero.
            servicio = TopicNotesService(
                repository=notas,
                dossier=SqlAlchemyDossierRepository(session_factory),
                model=_ModeloQueNoSeUsa(),
                workers=1,
            )
            for tema in temas:
                print("\n".join(servicio.medir(tema).lines()))
                print()
            return 0
        if args.esquema:
            # El esquema antes de redactar: tampoco llama a nadie ni necesita clave.
            for tema in temas:
                print("\n".join(_esquema(notas, tema)))
                print()
            return 0
        if args.limpiar_andamios:
            # Limpieza del texto ya escrito: no llama a nadie y no archiva versión.
            for tema in temas:
                print("\n".join(_limpiar_andamios(notas, tema)))
                print()
            return 0
        if args.limpiar_puertos:
            # La tabla de puertos del texto ya escrito: tampoco llama a nadie.
            for tema in temas:
                print("\n".join(_limpiar_puertos(notas, tema)))
                print()
            return 0
        if args.limpiar_forma:
            # Las reparaciones de forma del texto ya escrito: tampoco llama a nadie.
            for tema in temas:
                print("\n".join(_limpiar_forma(notas, tema)))
                print()
            return 0
        if args.olvidar_apartado:
            # Deja apartados sin texto para que la próxima corrida los rehaga.
            for tema in temas:
                for clave in args.olvidar_apartado:
                    print("\n".join(_olvidar_apartado(notas, tema, clave)))
                print()
            return 0

        api_key = os.environ.get(VARIABLE_DE_LA_CLAVE, "")
        if not api_key.strip():
            print(
                f"Falta la variable de entorno {VARIABLE_DE_LA_CLAVE}: sin clave no se escriben "
                "apuntes. Se lee del entorno y no se guarda en ningún sitio.",
                file=sys.stderr,
            )
            return 2

        servicio = TopicNotesService(
            repository=notas,
            dossier=SqlAlchemyDossierRepository(session_factory),
            model=DeepSeekNotesModel(
                api_key=api_key,
                model=args.modelo,
                base_url=args.base_url,
                timeout_seconds=args.tiempo,
            ),
            workers=max(1, args.paralelo),
        )
        reloj = SystemClock()
        if args.dry_run:
            print("ENSAYO: se llama al modelo y NO se escribe nada.\n")
        total = 0.0
        sin_calidad: list[str] = []
        sin_cobertura: list[str] = []
        # La marca de corrida: escribir apuntes es lo más caro del proyecto y el 10 de octubre de
        # 2026 se lanzaron dos corridas a la vez sobre I.6. La segunda no escribe: se niega y dice
        # desde cuándo corre la primera. Es la misma marca que usa el clasificador, con su clave.
        marca = ClassificationRunLock(
            session_factory,
            opposition_code=", ".join(temas),
            clave=CLAVE_APUNTES,
            que="corrida de apuntes",
        )
        with marca.hold():
            for tema in temas:
                informe = servicio.run(
                    tema,
                    now=reloj.now(),
                    dry_run=args.dry_run,
                    limite_grupos=args.limite,
                    # El tope de la corrida entera: sin él, una corrida atascada gasta tiempo y
                    # dinero sin que nadie la pare. 0 (el valor por defecto) es «sin tope».
                    maximo_segundos=args.tiempo_maximo if args.tiempo_maximo > 0 else None,
                )
                pasa_forma, pasa_cobertura = _decidir_y_archivar(
                    informe,
                    dossier_service=dossier_service,
                    exigir_calidad=args.exigir_calidad,
                    version=args.version,
                    dry_run=args.dry_run,
                )
                if not pasa_forma:
                    sin_calidad.append(informe.topic_code)
                if not pasa_cobertura:
                    sin_cobertura.append(informe.topic_code)
                print("\n".join(informe.lines()))
                print()
                total += informe.estimated_cost_usd
        if len(temas) > 1:
            print(f"Coste estimado de los {len(temas)} temas: {total:.4f} $ (precios de valle).")
        if sin_calidad:
            print(
                "NO pasan las comprobaciones de forma: "
                + ", ".join(sin_calidad)
                + (
                    ". No se ha archivado la versión: un tema con encabezados repetidos, marcas "
                    "internas, tablas sin cabecera, párrafos repetidos o extensión de sobra no se "
                    "da por bueno."
                    if args.exigir_calidad
                    else ". Se archiva igual porque no se pidió --exigir-calidad."
                ),
                file=sys.stderr,
            )
        if sin_cobertura:
            print(
                "NO pasan la puerta de cobertura "
                "(90 % de las preguntas con clave utilizable): "
                + ", ".join(sin_cobertura)
                + (
                    ". No se ha archivado la versión y, si había una, se ha retirado: el tema "
                    "queda en borrador con su motivo."
                    if args.exigir_calidad
                    else ". Se archiva igual porque no se pidió --exigir-calidad."
                ),
                file=sys.stderr,
            )
        if args.exigir_calidad and (sin_calidad or sin_cobertura):
            return 3
        return 0
    except OpoFuenteError as error:
        print(f"No se han podido escribir los apuntes: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


def _esquema(notas: SqlAlchemyTopicNotesRepository, code: str) -> tuple[str, ...]:
    """El índice por materias del tema: el esquema antes de redactar, sin llamar a nadie.

    Es el paso C del plan tal como lo pidió el propietario: ver el árbol de apartados antes de que
    se escriba nada. Los hechos y las preguntas salen de la base; el reparto, del catálogo del tema.
    """
    node_id = notas.node_id(code)
    if node_id is None:
        return (f"[{code}] no existe ese tema en el programa",)
    nodo = notas.node(node_id)
    if nodo is None:
        return (f"[{code}] no es un tema del programa",)
    if catalogo(code) is None:
        return (
            f"[{code}] todavía no tiene catálogo de materias: el índice de este tema está sin "
            "definir (se define antes de redactar, no se inventa)",
        )
    try:
        indice = indice_de(
            topic_code=code,
            topic_title=nodo.title,
            epigraphs=nodo.epigraphs,
            hechos=notas.facts(node_id),
            grupos=notas.question_groups(node_id),
        )
    except (KeyError, ValueError) as error:
        return (f"[{code}] el catálogo de materias no cuadra con el temario: {error}",)
    # El índice y **su revisión**, que es lo que decide si se puede redactar con él: sin esto, la
    # única forma de saber si el árbol cuadra era lanzar la corrida y esperar a que se quejara. Se
    # mide sobre el plan (con los apartados ya partidos), que es lo que se va a escribir.
    return (
        *indice.lines(),
        *revisar_indice(
            indice, plan_de(indice, max_hechos_por_apartado=MAX_HECHOS_POR_APARTADO)
        ).lines(),
    )


def _limpiar_andamios(notas: SqlAlchemyTopicNotesRepository, code: str) -> tuple[str, ...]:
    """Quita las marcas internas del texto **ya escrito** del tema. No llama a nadie.

    Es la misma limpieza que se aplica al guardar un apartado nuevo (`limpiar_andamios`), para el
    texto que se escribió antes de que existiera: el redactor copia a veces el número del hecho que
    se le da (`[[Hecho 36]]`) y eso es andamio, no apuntes. Se dice cuántas marcas había y cuántas
    quedan; si no había ninguna, no se toca nada (ni la fecha del apartado).
    """
    node_id = notas.node_id(code)
    if node_id is None:
        return (f"[{code}] no existe ese tema en el programa",)
    lineas = [f"[{code}] limpieza de marcas internas"]
    total = 0
    tocados = 0
    for apartado in notas.sections(node_id):
        marcas = marcas_internas(apartado.body_markdown)
        limpio = limpiar_andamios(apartado.body_markdown)
        # Se toca lo que de verdad cambia, no solo lo que tiene marcas: la limpieza también retira
        # los corchetes que quedaron alrededor de una marca ya quitada (`[]`), y eso no es marca.
        if limpio == apartado.body_markdown:
            continue
        notas.save_section_body(
            apartado,
            title=None,
            body=limpio,
            needs_review_reason=apartado.needs_review_reason,
            model=None,
            now=SystemClock().now(),
        )
        total += len(marcas)
        tocados += 1
        lineas.append(f"    {apartado.key}: {len(marcas)} marca(s) quitada(s)")
    lineas.append(f"    {total} marca(s) en {tocados} apartado(s)")
    return tuple(lineas)


def _decidir_y_archivar(
    informe: TopicNotesReport,
    *,
    dossier_service: DossierService,
    exigir_calidad: bool,
    version: bool,
    dry_run: bool,
) -> tuple[bool, bool]:
    """Las dos puertas de un tema (§2.3) y lo que se hace con su versión. Devuelve si las pasa.

    Son **dos**: las cinco comprobaciones de forma y la cobertura. Antes solo se miraba la primera,
    y
    por eso un tema podía quedar publicado con el 85 % de las preguntas sin contestar. Lo que pasa
    las dos se archiva (la marca «Versión generada · en revisión» de la zona del alumno) y lo que
    no,
    **no se queda publicado**: si tenía una versión archivada de una corrida anterior, se retira con
    su motivo. Es reversible: en cuanto pase, se archiva otra vez.

    Está en una función y no dentro del bucle porque la usan los dos caminos que deciden: la corrida
    que escribe con el modelo y `--publicar`, que mide lo ya guardado y archiva sin llamar a nadie.
    Dos copias de esta decisión acabarían diciendo cosas distintas.
    """
    pasa_forma = informe.revision is None or informe.revision.pasa
    pasa_cobertura = informe.coverage.pasa_cobertura
    pasa = pasa_forma and pasa_cobertura
    if version and not dry_run and (pasa or not exigir_calidad):
        archivado = dossier_service.archive(informe.node_id)
        if archivado is not None:
            informe.version_created = archivado[1]
    elif version and not dry_run and not pasa:
        informe.version_retired = dossier_service.retire(
            informe.node_id,
            reason=(
                f"la corrida de {informe.topic_code} no pasa la puerta "
                f"({'forma' if not pasa_forma else 'cobertura'}): el tema queda en borrador"
            ),
        )
    return pasa_forma, pasa_cobertura


def _limpiar_forma(notas: SqlAlchemyTopicNotesRepository, code: str) -> tuple[str, ...]:
    """Vuelve a pasar las reparaciones de forma al texto **ya escrito** del tema. No llama a nadie.

    Son las mismas que se aplican al guardar un apartado (`_enderezar`), más la que solo tiene
    sentido
    sobre el tema entero:

    1. **encabezados repetidos en el tema**: se quitan de cada apartado los que ya han salido en
    otro
       anterior (la puerta los cuenta en todo el tema, así que la reparación también);
    2. **encabezados repetidos dentro del mismo apartado** (`sin_encabezados_repetidos`);
    3. **columnas de tabla sin titular**: se les pone nombre (`nombrar_columnas_sin_titulo`);
    4. **tuberías dentro de un `código` en una celda de tabla**: se escapan
       (`escapar_tuberias_en_celdas`), porque sin el escape la fila se parte en una celda de más y
       la tabla deja de leerse. Es lo que le pasaba a II.4 con la tabla de operadores del shell,
       cuyo operador `` | `` es, él mismo, una tubería.

    Existe por el texto escrito antes de que existieran: I.1 tenía cuatro tablas de comparación con
    la
    primera columna sin titular y dos encabezados repetidos entre los dos trozos de una misma
    materia.
    Dice cuántos apartados ha tocado y vuelve a medir la forma con la misma revisión que decide.
    """
    node_id = notas.node_id(code)
    if node_id is None:
        return (f"[{code}] no existe ese tema en el programa",)
    apartados = list(notas.sections(node_id))
    sin_repetidos = sin_encabezados_repetidos_en_el_tema(
        [apartado.body_markdown for apartado in apartados],
        titulos=[apartado.title for apartado in apartados],
    )
    titulos = dict(titulos_que_cambian(apartados, _titulos_del_indice(notas, node_id, code)))
    lineas = [f"[{code}] limpieza de forma"]
    tocados = 0
    for apartado, primero in zip(apartados, sin_repetidos, strict=True):
        antes = apartado.body_markdown
        nuevo_titulo = titulos.get(apartado.key)
        if not antes.strip():
            continue
        cuerpo = nombrar_columnas_sin_titulo(
            escapar_tuberias_en_celdas(sin_encabezados_repetidos(primero))
        )
        if cuerpo == antes and nuevo_titulo is None:
            continue
        notas.save_section_body(
            apartado,
            title=nuevo_titulo,
            body=cuerpo,
            needs_review_reason=apartado.needs_review_reason,
            model=None,
            now=SystemClock().now(),
        )
        tocados += 1
        if nuevo_titulo is None:
            lineas.append(f"    {apartado.key}: {len(antes)} → {len(cuerpo)} caracteres")
        else:
            lineas.append(f"    {apartado.key}: título «{apartado.title}» → «{nuevo_titulo}»")
    lineas.append(f"    {tocados} apartado(s) tocado(s)")
    lineas.extend(
        f"    {linea}"
        for linea in revisar_apuntes(notas.sections(node_id), notas.facts(node_id)).lines()
    )
    return tuple(lineas)


def _titulos_del_indice(
    notas: SqlAlchemyTopicNotesRepository, node_id: str, code: str
) -> dict[str, str]:
    """El título que le toca a cada apartado según **su índice**, sin llamar a nadie.

    Sale del mismo camino que usa la corrida para planificar (`indice_de` y `plan_de`), así que el
    título que pone la limpieza de forma es exactamente el que pondría volver a escribir el tema. Si
    el tema todavía no tiene catálogo, no hay nada que decir y se devuelve vacío.
    """
    if catalogo(code) is None:
        return {}
    nodo = notas.node(node_id)
    if nodo is None:
        return {}
    indice = indice_de(
        topic_code=code,
        topic_title=nodo.title,
        epigraphs=nodo.epigraphs,
        hechos=notas.facts(node_id),
        grupos=notas.question_groups(node_id),
    )
    planes = plan_de(indice, max_hechos_por_apartado=MAX_HECHOS_POR_APARTADO)
    return {plan.key: plan.title for plan in planes}


def _limpiar_puertos(notas: SqlAlchemyTopicNotesRepository, code: str) -> tuple[str, ...]:
    """Vuelve a pasar la limpieza de la tabla de puertos al texto ya escrito. No llama a nadie.

    Es la misma limpieza que se aplica al guardar (`limpiar_tabla_de_puertos`), para el texto que
    se escribió antes de que existiera: parte la tabla por familias, le quita las notas que solo
    dicen lo que un puerto **no** es y recoge las confusiones de verdad en su bloque. Se dice
    cuántas notas se han retirado y se enseña la revisión de forma del tema, que es la puerta que
    esto arregla.
    """
    node_id = notas.node_id(code)
    if node_id is None:
        return (f"[{code}] no existe ese tema en el programa",)
    lineas = [f"[{code}] limpieza de la tabla de puertos"]
    for apartado in notas.sections(node_id):
        if not es_la_tabla_de_puertos(code, apartado.key):
            continue
        limpieza = limpiar_tabla_de_puertos(apartado.body_markdown)
        if limpieza.texto == apartado.body_markdown:
            lineas.append("    no había nada que limpiar")
            continue
        notas.save_section_body(
            apartado,
            title=None,
            body=limpieza.texto,
            needs_review_reason=apartado.needs_review_reason,
            model=None,
            now=SystemClock().now(),
        )
        lineas.append(
            f"    {apartado.key}: {limpieza.notas_retiradas} nota(s) de distractor retirada(s) · "
            f"{len(limpieza.confusiones)} confusión(es) que caen"
        )
    lineas.extend(
        f"    {linea}"
        for linea in revisar_apuntes(notas.sections(node_id), notas.facts(node_id)).lines()
    )
    return tuple(lineas)


def _olvidar_apartado(
    notas: SqlAlchemyTopicNotesRepository, code: str, clave: str
) -> tuple[str, ...]:
    """Deja un apartado sin texto para que la próxima corrida lo redacte otra vez.

    Es la corrección de **un** apartado que no pasa la revisión de forma (una tabla rota, un
    encabezado repetido), sin rehacer el tema entero ni volver a pagar por los demás. No se borran
    sus hechos ni sus comprobaciones: la corrida siguiente escribe su texto y las vuelve a
    comprobar.
    """
    node_id = notas.node_id(code)
    if node_id is None:
        return (f"[{code}] no existe ese tema en el programa",)
    for apartado in notas.sections(node_id):
        if apartado.key != clave:
            continue
        notas.save_section_body(
            apartado,
            title=None,
            body="",
            needs_review_reason=None,
            model=None,
            now=SystemClock().now(),
        )
        return (
            f"[{code}] {clave}: texto borrado ({len(apartado.body_markdown)} caracteres). La "
            "próxima corrida lo redacta otra vez y vuelve a comprobar sus preguntas.",
        )
    return (f"[{code}] no hay ningún apartado con la clave {clave}",)


def _listar(notas: SqlAlchemyTopicNotesRepository, code: str) -> tuple[str, ...]:
    """Lo que hay en un tema hoy: sus preguntas, sus hechos y sus apartados."""
    node_id = notas.node_id(code)
    if node_id is None:
        return (f"[{code}] no existe ese tema en el programa",)
    nodo = notas.node(node_id)
    grupos = notas.question_groups(node_id)
    hechos = notas.facts(node_id)
    apartados = notas.sections(node_id)
    comprobadas = notas.checks(node_id)
    lineas = [
        f"[{code}] {'' if nodo is None else nodo.title}",
        f"    {len(nodo.epigraphs) if nodo else 0} epígrafe(s) · "
        f"{len(grupos)} grupo(s) de preguntas "
        f"({sum(len(grupo.questions) for grupo in grupos)} preguntas)",
        f"    hechos guardados: {len(hechos)} · apartados: {len(apartados)} · "
        f"comprobaciones: {len(comprobadas)}",
    ]
    for apartado in apartados:
        lineas.append(
            f"      · {apartado.key} · {apartado.title[:60]} · "
            f"{len(apartado.facts)} hecho(s) · {len(apartado.body_markdown)} caracteres"
        )
    return tuple(lineas)


def _resumen(informes: Sequence[TopicNotesReport]) -> tuple[str, ...]:
    """La última línea del comando cuando se escriben varios temas."""
    return tuple(
        f"[{informe.topic_code}] {informe.coverage.covered} cubiertas de "
        f"{informe.coverage.groups} · {informe.estimated_cost_usd:.4f} $"
        for informe in informes
    )


if __name__ == "__main__":
    raise SystemExit(main())
