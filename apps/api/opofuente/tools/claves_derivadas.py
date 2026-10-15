"""Las claves derivadas: devolver al estudio las preguntas que hoy estan fuera (§1 del encargo).

    uv run python -m opofuente.tools.claves_derivadas --listar
    uv run python -m opofuente.tools.claves_derivadas --prever
    uv run python -m opofuente.tools.claves_derivadas --derivar --tope-usd 0.50
    uv run python -m opofuente.tools.claves_derivadas --decidir
    uv run python -m opofuente.tools.claves_derivadas --informe

**Que hace.** Un conjunto en cuarentena tiene la clave mal extraida del material y por eso sus
preguntas no entran en tests, simulacros ni repasos. Reextraerla ya se probo y no la
arregla (ninguna rotacion baja del 10 %, medido en F19), asi que lo que queda es
**derivar la letra de cada pregunta** cuando **dos fuentes independientes** dicen lo
mismo: la letra de los apuntes con su cita verificada, y la que el modelo contesta a la
pregunta **sola** (enunciado y opciones, sin apuntes). Si coinciden,
la clave se guarda como `derived` —nunca `active`— y el alumno la ve con la marca «clave revisada
automaticamente». Si no, la pregunta sigue fuera **con su motivo escrito**.

**Los modos, y por que estan separados:**

- **`--listar`** (0 $): los conjuntos en cuarentena, sus numeros y si su clave esta protegida. No
  llama a nadie y no escribe.
- **`--prever`** (0 $): cuantas preguntas se le van a preguntar al modelo, con que texto y **cuanto
  puede costar**, con la tabla de precios del proyecto. Es lo que se mira **antes de pagar**.
- **`--derivar`** (cuesta): la corrida. `--tope-usd` y `--limite` son topes **duros**: al
  alcanzarlos
  la corrida **para** y dice donde se quedo. `--seco` no escribe nada.
- **`--decidir`** (0 $): vuelve a contar cada conjunto y **audita** la decision de volver
  a los tests
  (≥ 90 % de sus preguntas con clave fiable). No cambia el veredicto del conjunto: la pregunta entra
  por **su** clave, y una pregunta con motivo de fuera sigue fuera aunque el conjunto vuelva.
- **`--informe`** (0 $): el antes/despues por conjunto y los motivos de lo que sigue fuera.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime

from opofuente.config import Settings, get_settings
from opofuente.domain.derived_keys import (
    ACTOR,
    UMBRAL_VUELVE_A_LOS_TESTS,
    DecisionDeConjunto,
    Derivacion,
    MotivoDeFuera,
    RecuentoDeFuera,
    RespuestaDelModelo,
    decidir_conjuntos,
    derivar,
    protege_derivar,
    recuento_de_fuera,
)
from opofuente.domain.key_reliability import KeyReliability
from opofuente.domain.topic_classification import (
    PRECIO_ENTRADA_USD_POR_MILLON,
    PRECIO_SALIDA_USD_POR_MILLON,
)
from opofuente.domain.topic_notes import TokenLedger
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.derived_key_repository import (
    ConjuntoEnCuarentena,
    SqlAlchemyDerivedKeyRepository,
)
from opofuente.infrastructure.key_reliability_repository import (
    SqlAlchemyKeyReliabilityRepository,
)
from opofuente.infrastructure.run_lock import CLAVE_APUNTES, ClassificationRunLock
from opofuente.infrastructure.topic_notes_client import (
    BASE_URL_POR_DEFECTO,
    MODELO_POR_DEFECTO,
    DeepSeekNotesModel,
)

#: La variable de la que se lee la clave. Es lo unico que se necesita configurar para escribir.
VARIABLE_DE_LA_CLAVE = "DEEPSEEK_API_KEY"

#: Cuantas preguntas van en cada llamada. El encargo de sistema es corto (no lleva apuntes), asi que
#: el lote reparte ese texto fijo entre mas preguntas; con lotes de uno, el sistema se
#: pagaria entero por pregunta. Es un parametro y no una constante escondida para poder medirlo.
LOTE_POR_DEFECTO = 10

#: El tope por defecto de la corrida, en dolares. El encargo pide tope **siempre**: una corrida sin
#: tope sobre una base que crece es una factura que nadie ha decidido.
TOPE_USD_POR_DEFECTO = 0.50

#: Y el tope de llamadas, por si el precio por llamada sale distinto de lo previsto.
LIMITE_LLAMADAS_POR_DEFECTO = 200

#: Lo que ocupa el mensaje de sistema, en caracteres, para la prevision. Es fijo y se paga una vez
#: por llamada; se cuenta para no dar una previsión que se quede corta por lo que no se ve.
CARACTERES_DEL_SISTEMA = 900

#: La salida de una llamada, por pregunta, en tokens. **Medido, no supuesto**: en la corrida del
#: 15-oct sobre la base real, 74 preguntas costaron 75.510 tokens de salida, o sea ≈1.020 por
#: pregunta. La primera previsión uso 12 (lo que ocupa la letra y su `id` en JSON) y se quedo **14
#: veces corta**: el modelo devuelve mucho mas texto del que se lee. La cifra se queda en lo medido
#: para que la proxima previsión avise de verdad.
TOKENS_DE_SALIDA_POR_PREGUNTA = 1020


def _use_utf8_stdout() -> None:
    """El informe lleva acentos y comillas angulares: en Windows, redirigido, saldria en la
    codificacion local y no se podria comparar entre maquinas."""
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigurar):
        reconfigurar(encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="opofuente.tools.claves_derivadas",
        description=(
            "Deriva la clave de las preguntas de los conjuntos en cuarentena con dos fuentes "
            "independientes, y decide por conjunto si vuelve a los tests."
        ),
    )
    parser.add_argument(
        "--listar",
        action="store_true",
        help="los conjuntos en cuarentena y sus numeros, sin llamar a nadie (0 $)",
    )
    parser.add_argument(
        "--prever",
        action="store_true",
        help=(
            "lo que costaria la corrida **antes de pagarla**: cuantas preguntas se preguntan, con "
            "que texto y con que tope. No llama a nadie (0 $)"
        ),
    )
    parser.add_argument(
        "--derivar",
        action="store_true",
        help="la corrida: pregunta al modelo sin apuntes y guarda las claves derivadas",
    )
    parser.add_argument(
        "--decidir",
        action="store_true",
        help=(
            "vuelve a contar cada conjunto y audita la decision de volver a los tests (>= 90 % de "
            "sus preguntas con clave fiable). No cambia el veredicto ni llama a nadie (0 $)"
        ),
    )
    parser.add_argument(
        "--informe",
        action="store_true",
        help="el antes/despues por conjunto y los motivos de lo que sigue fuera (0 $)",
    )
    parser.add_argument(
        "--seco",
        action="store_true",
        help="hace la corrida entera **sin escribir**: ni clave, ni motivo, ni auditoria",
    )
    parser.add_argument(
        "--tope-usd",
        type=float,
        default=TOPE_USD_POR_DEFECTO,
        help=(
            "tope de gasto de la corrida, en dolares (por defecto "
            f"{TOPE_USD_POR_DEFECTO}). Al alcanzarlo, la corrida para y lo dice"
        ),
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=LIMITE_LLAMADAS_POR_DEFECTO,
        help=f"tope de llamadas al modelo (por defecto {LIMITE_LLAMADAS_POR_DEFECTO})",
    )
    parser.add_argument(
        "--lote",
        type=int,
        default=LOTE_POR_DEFECTO,
        help=f"preguntas por llamada (por defecto {LOTE_POR_DEFECTO})",
    )
    parser.add_argument(
        "--modelo", default=MODELO_POR_DEFECTO, help=f"modelo (por defecto {MODELO_POR_DEFECTO})"
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL_POR_DEFECTO,
        help=f"direccion del modelo (por defecto {BASE_URL_POR_DEFECTO})",
    )
    parser.add_argument(
        "--conjunto",
        action="append",
        default=None,
        metavar="ID",
        help=(
            "limita la corrida a estos conjuntos (repetible). Sin esto, todos los que esten en "
            "cuarentena"
        ),
    )
    return parser.parse_args(argv)


# --- la preparacion: que conjuntos, con que fuentes y con que proteccion -------------------------


class Preparado:
    """Lo que la corrida necesita saber antes de gastar un centimo.

    Se calcula **entero** con consultas de solo lectura: que conjuntos entran, cuales se
    rechazan por su clave oficial, que preguntas tienen la primera fuente (apuntes con
    cita) y cuanto texto se le
    va a mandar al modelo. La corrida y la prevision usan **lo mismo**: una prevision que se calcula
    por un camino distinto del que gasta no previene nada.
    """

    def __init__(
        self, repo: SqlAlchemyDerivedKeyRepository, *, solo: Sequence[str] | None = None
    ) -> None:
        pedidos = set(solo) if solo is not None else None
        conjuntos = [
            conjunto
            for conjunto in repo.sets_in_quarantine()
            if pedidos is None or conjunto.set_id in pedidos
        ]
        enlazados = repo.linked_material([conjunto.set_id for conjunto in conjuntos])
        self.rechazados: list[tuple[ConjuntoEnCuarentena, str]] = []
        self.entran: list[ConjuntoEnCuarentena] = []
        for conjunto in conjuntos:
            motivo = protege_derivar(
                set_type=conjunto.set_type,
                tiene_plantilla_enlazada=(
                    conjunto.tiene_plantilla_enlazada or conjunto.set_id in enlazados
                ),
                origin_scope=conjunto.origin_scope,
            )
            if motivo is None:
                self.entran.append(conjunto)
            else:
                self.rechazados.append((conjunto, motivo))

        self.preguntas: dict[str, tuple[str, ...]] = repo.question_ids_of_sets(
            [conjunto.set_id for conjunto in self.entran]
        )
        todas = tuple(pregunta_id for ids in self.preguntas.values() for pregunta_id in ids)
        self.fuentes = repo.notes_sources(todas)
        self.confirmadas = repo.corroborated(todas)
        self.ya_derivadas = repo.derived_questions([conjunto.set_id for conjunto in self.entran])
        self.ya_fuera = repo.gaps_of([conjunto.set_id for conjunto in self.entran])
        #: Las que de verdad se le preguntan al modelo: las que tienen **letra y cita**.
        #: Una sin cita no puede derivar, y preguntarsela al modelo seria pagar por una
        #: respuesta que no se puede contrastar con nada. Una ya derivada tampoco (no se paga
        #: dos veces por lo mismo), y una **corroborada** tampoco: su letra ya la sostiene la
        #: cita de los apuntes contra la clave activa, asi que preguntarle al modelo no puede
        #: cambiar su clave. Es la regla de no pagar por lo que no cambia nada.
        self.consultables: dict[str, tuple[str, ...]] = {
            conjunto.set_id: tuple(
                pregunta_id
                for pregunta_id in self.preguntas.get(conjunto.set_id, ())
                if pregunta_id in self.fuentes
                and self.fuentes[pregunta_id].sirve
                and pregunta_id not in self.confirmadas
                and pregunta_id not in self.ya_derivadas.get(conjunto.set_id, ())
            )
            for conjunto in self.entran
        }
        self.pedidas = tuple(
            pregunta_id for ids in self.consultables.values() for pregunta_id in ids
        )

    @property
    def total_preguntas(self) -> int:
        return sum(len(ids) for ids in self.preguntas.values())


def _caracteres(repo: SqlAlchemyDerivedKeyRepository, pregunta_ids: Sequence[str]) -> int:
    """Los caracteres que se le van a mandar al modelo: el enunciado y las opciones, medidos."""
    return sum(
        len(pregunta.stem) + sum(len(clave) + len(texto) for clave, texto in pregunta.options)
        for pregunta in repo.questions_for_model(pregunta_ids)
    )


def prever(caracteres: int, preguntas: int, lote: int) -> tuple[float, float, int]:
    """La prevision de dinero y de llamadas, con la tabla de precios del proyecto.

    Los caracteres se convierten en tokens con la regla conservadora del proyecto (≈4 caracteres por
    token) y se le suma **el mensaje de sistema de cada llamada**, que es fijo y se paga entero una
    vez por lote. La salida se estima por arriba (`TOKENS_DE_SALIDA_POR_PREGUNTA`), que es lo que
    midio el paso E con la misma forma de salida.

    Devuelve `(minimo, maximo, llamadas)`. La cota de arriba añade un 10 %: es lo que sube si la
    cache no ayuda en nada, que es el caso de una corrida que no repite el mismo texto dos veces.
    """
    if preguntas <= 0:
        return 0.0, 0.0, 0
    llamadas = -(-preguntas // max(1, lote))
    entrada = caracteres / 4 + CARACTERES_DEL_SISTEMA * llamadas
    salida = TOKENS_DE_SALIDA_POR_PREGUNTA * preguntas
    coste = (
        entrada / 1_000_000 * PRECIO_ENTRADA_USD_POR_MILLON
        + salida / 1_000_000 * PRECIO_SALIDA_USD_POR_MILLON
    )
    return coste, coste * 1.10, llamadas


# --- los modos -----------------------------------------------------------------------------------


def _listar(preparado: Preparado) -> None:
    print(f"Conjuntos en cuarentena: {len(preparado.entran) + len(preparado.rechazados)}")
    for conjunto, motivo in preparado.rechazados:
        print(f"  RECHAZADO  {conjunto.title} ({conjunto.preguntas} preguntas)")
        print(f"             {motivo}")
    for conjunto in preparado.entran:
        ids = preparado.preguntas.get(conjunto.set_id, ())
        con_cita = len(preparado.consultables.get(conjunto.set_id, ()))
        confirmadas = len([q for q in ids if q in preparado.confirmadas])
        derivadas = len(preparado.ya_derivadas.get(conjunto.set_id, ()))
        print(
            f"  {conjunto.title[:50]:52s} {conjunto.preguntas:4d} preguntas · "
            f"{conjunto.set_type}/{conjunto.origin_scope} · con cita {con_cita:3d} · "
            f"corroboradas {confirmadas:3d} · derivadas {derivadas:3d}"
        )


def _prever(
    preparado: Preparado, repo: SqlAlchemyDerivedKeyRepository, args: argparse.Namespace
) -> None:
    caracteres = _caracteres(repo, preparado.pedidas)
    minimo, maximo, llamadas = prever(caracteres, len(preparado.pedidas), args.lote)
    print(
        f"Conjuntos que entran: {len(preparado.entran)} "
        f"(rechazados por clave oficial: {len(preparado.rechazados)})"
    )
    print(f"Preguntas en cuarentena: {preparado.total_preguntas}")
    print(f"Preguntas con letra **y** cita verificada por preguntar: {len(preparado.pedidas)}")
    print(
        "Preguntas que NO se le preguntan al modelo: "
        f"{preparado.total_preguntas - len(preparado.pedidas)} "
        "(sin cita, o ya derivadas)"
    )
    print(f"Texto a enviar: {caracteres} caracteres ≈ {caracteres / 4:.0f} tokens de entrada")
    print(f"Llamadas previstas: {llamadas} (lotes de {args.lote})")
    print(
        f"Coste previsto: {minimo:.4f} $ como minimo y {maximo:.4f} $ como maximo "
        f"(entrada {PRECIO_ENTRADA_USD_POR_MILLON} $/M y salida "
        f"{PRECIO_SALIDA_USD_POR_MILLON} $/M, valle)"
    )
    print(f"Tope de esta corrida: {args.tope_usd:.4f} $ y {args.limite} llamadas")
    if maximo > args.tope_usd:
        print("  AVISO: la cota de arriba pasa del tope. La corrida parara al alcanzarlo.")
    print("Nada de esto ha llamado al modelo.")


def _derivar(
    preparado: Preparado,
    repo: SqlAlchemyDerivedKeyRepository,
    modelo: DeepSeekNotesModel,
    args: argparse.Namespace,
) -> int:
    ledger = TokenLedger()
    ahora = datetime.now(UTC)
    derivadas = 0
    preguntadas = 0
    motivos: list[MotivoDeFuera] = []
    parada: str | None = None
    # Los conjuntos cuya clave es oficial **se rechazan por escrito** antes de gastar nada: el
    # rechazo es una decisión del objetivo («las claves oficiales no se tocan») y tiene que poder
    # leerse después, no vivir en un `if`.
    rechazados = _anotar_rechazos(preparado, repo, seco=args.seco, ahora=ahora)
    if rechazados:
        print(
            f"{rechazados} conjunto(s) rechazado(s) por su clave oficial, con su motivo auditado."
        )
    for conjunto in preparado.entran:
        ids = preparado.preguntas.get(conjunto.set_id, ())
        consultables = preparado.consultables.get(conjunto.set_id, ())
        respuestas: dict[str, RespuestaDelModelo] = {}
        for inicio in range(0, len(consultables), args.lote):
            if parada is not None:
                break
            if ledger.calls >= args.limite:
                parada = f"tope de {args.limite} llamadas"
                break
            if ledger.estimated_cost_usd >= args.tope_usd:
                parada = f"tope de {args.tope_usd:.4f} $"
                break
            lote = consultables[inicio : inicio + args.lote]
            batch = modelo.responder(repo.questions_for_model(lote))
            ledger.add(
                input_tokens=batch.input_tokens,
                output_tokens=batch.output_tokens,
                cache_hit_tokens=batch.cache_hit_tokens,
            )
            preguntadas += len(lote)
            respuestas.update(batch.por_pregunta)
            print(
                f"  {conjunto.title[:40]:42s} lote de {len(lote):2d} · llamada {ledger.calls:3d} · "
                f"acumulado {ledger.estimated_cost_usd:.4f} $",
                flush=True,
            )
        suyas: list[Derivacion] = []
        fuera: dict[str, MotivoDeFuera] = {}
        for pregunta_id in ids:
            if pregunta_id in preparado.ya_derivadas.get(conjunto.set_id, ()):
                continue
            if pregunta_id in preparado.confirmadas:
                # Su letra esta **corroborada** por la cita de los apuntes contra la clave
                # activa: no se le escribe motivo de fuera, porque no lo tiene. Entra cuando
                # el conjunto vuelva (en cuarentena, su plantilla es la sospechosa).
                continue
            resultado = derivar(
                preparado.fuentes.get(pregunta_id),
                respuestas.get(pregunta_id, RespuestaDelModelo(pregunta_id, None)),
            )
            if isinstance(resultado, Derivacion):
                suyas.append(resultado)
            else:
                fuera[pregunta_id] = resultado
                motivos.append(resultado)
        if not args.seco:
            derivadas += repo.save_derivations(
                suyas,
                set_id=conjunto.set_id,
                now=ahora,
                actor=ACTOR,
                model_name=modelo.name,
                model_version=modelo.version,
            )
            repo.save_gaps(fuera, set_id=conjunto.set_id, now=ahora, actor=ACTOR)
        else:
            derivadas += len(suyas)
        aviso = " (SECO: no se ha escrito)" if args.seco else ""
        print(
            f"{conjunto.title[:48]:50s} {len(suyas):3d} derivada(s) · {len(fuera):3d} fuera · "
            f"{ledger.estimated_cost_usd:.4f} ${aviso}",
            flush=True,
        )

    print()
    print("== coste de la corrida ==")
    for linea in ledger.lines():
        print(f"  {linea}")
    if preguntadas:
        print(
            f"  coste por pregunta preguntada: "
            f"{ledger.estimated_cost_usd / preguntadas:.6f} $ "
            f"({preguntadas} pregunta(s) en {ledger.calls} llamada(s))"
        )
    print(f"  {derivadas} clave(s) derivada(s) guardada(s)")
    print()
    print("== lo que sigue fuera, por motivo ==")
    for recuento in recuento_de_fuera(motivos):
        print(f"  {recuento.linea()}")
    if parada is not None:
        print(
            f"\nPARADA: se alcanzo el {parada}. Lo de arriba esta guardado; vuelve a lanzarla para "
            "seguir donde se quedo (lo ya derivado no se vuelve a preguntar)."
        )
        return 2
    return 0


def _anotar_rechazos(
    preparado: Preparado,
    repo: SqlAlchemyDerivedKeyRepository,
    *,
    seco: bool,
    ahora: datetime,
) -> int:
    """Audita el rechazo de los conjuntos cuya clave es oficial. Devuelve cuantos se anotaron."""
    if seco:
        return 0
    return sum(
        1
        for conjunto, motivo in preparado.rechazados
        if repo.record_refusal(conjunto, motivo, now=ahora, actor=ACTOR)
    )


def _decisiones(
    preparado: Preparado,
    repo: SqlAlchemyDerivedKeyRepository,
    *,
    fiabilidad: SqlAlchemyKeyReliabilityRepository | None = None,
    escribir: bool = True,
) -> tuple[DecisionDeConjunto, ...]:
    """La cuenta del 90 % por conjunto, y la decision auditada.

    `derivadas` son las claves derivadas **guardadas** (no las que se acaban de calcular) y
    `corroboradas` las que la cita de los apuntes confirma contra la clave activa. Las dos cosas se
    leen de la base: la decision tiene que poder tomarse sin haber corrido nada en esta sesion.

    **Cuando un conjunto alcanza el liston, vuelve a los tests por la via auditada** (`set_verdict`,
    la misma puerta que puso la cuarentena): a partir de ahi sus preguntas entran con la clave de su
    plantilla, y las que tienen su motivo de fuera escrito **siguen fuera**. Bajo el liston
    no se toca el veredicto: lo que vuelve es lo que tiene clave derivada.
    """
    decisiones = decidir_conjuntos(
        ((conjunto.set_id, conjunto.title, conjunto.preguntas) for conjunto in preparado.entran),
        derivadas=(
            (conjunto.set_id, pregunta_id)
            for conjunto in preparado.entran
            for pregunta_id in preparado.ya_derivadas.get(conjunto.set_id, ())
        ),
        corroboradas=(
            (conjunto.set_id, pregunta_id)
            for conjunto in preparado.entran
            for pregunta_id in preparado.preguntas.get(conjunto.set_id, ())
            if pregunta_id in preparado.confirmadas
        ),
    )
    if escribir:
        ahora = datetime.now(UTC)
        for decision in decisiones:
            repo.record_decision(decision, now=ahora, actor=ACTOR)
            if decision.vuelve_a_los_tests and fiabilidad is not None:
                fiabilidad.set_verdict(
                    decision.set_id,
                    KeyReliability.FIABLE,
                    now=ahora,
                    actor=ACTOR,
                    reason=(
                        f"claves derivadas: {decision.con_clave}/{decision.preguntas} = "
                        f"{100 * decision.proporcion:.1f} % con clave fiable "
                        f"(liston {UMBRAL_VUELVE_A_LOS_TESTS:.0%})"
                    ),
                )
    return decisiones


def _motivo_de(preparado: Preparado, pregunta_id: str) -> MotivoDeFuera | None:
    """El motivo de fuera: lo **escrito** primero y, si no hay nada, lo que se calcula.

    Una pregunta con su motivo guardado lo dice tal cual —es la decision que tomo la
    corrida—; una corroborada o ya derivada no tiene motivo; y una con letra y cita **sin
    contrastar todavia** no es «sin coincidencia» —nadie la ha preguntado—: sale `None` y el
    informe la cuenta aparte como pendiente.
    """
    guardado = preparado.ya_fuera.get(pregunta_id)
    if guardado is not None:
        return guardado
    if pregunta_id in preparado.confirmadas:
        return None
    if any(pregunta_id in ids for ids in preparado.ya_derivadas.values()):
        return None
    fuente = preparado.fuentes.get(pregunta_id)
    if fuente is None or not fuente.letra.strip():
        return MotivoDeFuera.SIN_MATERIAL
    if not fuente.sirve:
        return MotivoDeFuera.SIN_CITA
    return None


def _pendientes(preparado: Preparado) -> int:
    """Con letra y cita, sin decidir todavia: lo que le queda por preguntar a la corrida."""
    return sum(
        1
        for conjunto in preparado.entran
        for pregunta_id in preparado.preguntas.get(conjunto.set_id, ())
        if _motivo_de(preparado, pregunta_id) is None
        and pregunta_id not in preparado.confirmadas
        and pregunta_id not in preparado.ya_derivadas.get(conjunto.set_id, ())
        and (fuente := preparado.fuentes.get(pregunta_id)) is not None
        and fuente.sirve
    )


def _recuento(preparado: Preparado) -> tuple[RecuentoDeFuera, ...]:
    motivos = [
        motivo
        for conjunto in preparado.entran
        for pregunta_id in preparado.preguntas.get(conjunto.set_id, ())
        if (motivo := _motivo_de(preparado, pregunta_id)) is not None
    ]
    return recuento_de_fuera(motivos)


def _informe(preparado: Preparado, repo: SqlAlchemyDerivedKeyRepository) -> None:
    decisiones = _decisiones(preparado, repo, escribir=False)
    print("== la decision, por conjunto ==")
    for decision in decisiones:
        print(f"  {decision.linea()}")
    print()
    print("== lo que sigue fuera, y por que ==")
    for conjunto in preparado.entran:
        motivos = [
            motivo
            for pregunta_id in preparado.preguntas.get(conjunto.set_id, ())
            if (motivo := _motivo_de(preparado, pregunta_id)) is not None
        ]
        if not motivos:
            continue
        print(f"  {conjunto.title[:56]}")
        for recuento in recuento_de_fuera(motivos):
            print(f"     {recuento.linea()}")
    pendientes = _pendientes(preparado)
    if pendientes:
        print(
            f"\n{pendientes} pregunta(s) con letra y cita **sin contrastar todavia**: no estan "
            "fuera, estan pendientes de que la corrida le pregunte al modelo."
        )
    print()
    print(
        f"Liston: {UMBRAL_VUELVE_A_LOS_TESTS:.0%} de las preguntas del conjunto con clave fiable "
        "(derivada, o corroborada por la cita de los apuntes)."
    )


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    args = parse_args(sys.argv[1:] if argv is None else argv)
    _use_utf8_stdout()
    settings: Settings = get_settings()
    engine = build_engine(settings.data_paths.database)
    try:
        session_factory = build_session_factory(engine)
        repo = SqlAlchemyDerivedKeyRepository(session_factory)
        fiabilidad = SqlAlchemyKeyReliabilityRepository(session_factory)
        if not (args.listar or args.prever or args.derivar or args.decidir or args.informe):
            args.listar = True
        if args.derivar:
            return _correr(args, session_factory, repo)
        preparado = Preparado(repo, solo=args.conjunto)
        if args.prever:
            _prever(preparado, repo, args)
        elif args.decidir:
            decisiones = _decisiones(preparado, repo, fiabilidad=fiabilidad)
            for decision in decisiones:
                print(decision.linea())
            print(
                f"\n{len(decisiones)} decision(es) auditada(s). Bajo el liston no se toca el "
                "veredicto del conjunto: lo que vuelve es lo que tiene clave derivada. El "
                "que lo alcanza vuelve a los tests por la via auditada, y sus preguntas con "
                "motivo de fuera escrito siguen fuera."
            )
        elif args.informe:
            _informe(preparado, repo)
        else:
            _listar(preparado)
            print()
            for recuento in _recuento(preparado):
                print(f"  {recuento.linea()}")
            pendientes = _pendientes(preparado)
            if pendientes:
                print(f"  {pendientes} pendiente(s) de preguntar al modelo (con letra y cita)")
        return 0
    finally:
        engine.dispose()


def _correr(
    args: argparse.Namespace,
    session_factory: object,
    repo: SqlAlchemyDerivedKeyRepository,
) -> int:
    """La corrida que escribe: toma el candado, deriva y lo suelta **pase lo que pase**."""
    api_key = os.environ.get(VARIABLE_DE_LA_CLAVE, "").strip()
    if not api_key:
        print(
            f"Falta {VARIABLE_DE_LA_CLAVE}: sin clave del modelo no se puede derivar nada (la "
            "prevision, el listado y el informe si se pueden: no llaman a nadie).",
            file=sys.stderr,
        )
        return 3
    if args.tope_usd <= 0 or args.limite <= 0:
        print(
            "El tope de dinero y el de llamadas tienen que ser mayores que cero: una corrida sin "
            "tope no se lanza.",
            file=sys.stderr,
        )
        return 3
    preparado = Preparado(repo, solo=args.conjunto)
    caracteres = _caracteres(repo, preparado.pedidas)
    minimo, maximo, llamadas = prever(caracteres, len(preparado.pedidas), args.lote)
    print(
        f"Prevision antes de pagar: {len(preparado.pedidas)} preguntas · {llamadas} llamada(s) · "
        f"{minimo:.4f}-{maximo:.4f} $ · tope {args.tope_usd:.4f} $ y {args.limite} llamada(s)"
    )
    if not preparado.pedidas:
        # Nada que derivar, pero los conjuntos que se rechazan por su clave oficial se anotan
        # igual: su rechazo es parte del resultado de la corrida.
        rechazados = _anotar_rechazos(preparado, repo, seco=args.seco, ahora=datetime.now(UTC))
        print(
            "No hay ninguna pregunta con cita verificada por derivar. No se llama a nadie"
            + (f" ({rechazados} rechazo(s) anotado(s))." if rechazados else ".")
        )
        return 0
    modelo = DeepSeekNotesModel(api_key=api_key, model=args.modelo, base_url=args.base_url)
    candado = ClassificationRunLock(
        session_factory,  # type: ignore[arg-type]
        opposition_code="claves derivadas",
        clave=CLAVE_APUNTES,
        que="claves derivadas",
    )
    with candado.hold():
        return _derivar(preparado, repo, modelo, args)


if __name__ == "__main__":
    sys.exit(main())
