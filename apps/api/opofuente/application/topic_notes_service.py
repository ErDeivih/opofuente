"""Los apuntes de un tema en cuatro pasos (B-E del plan), con reanudación y con cuenta de gasto.

El servicio hace, en este orden:

1. **los hechos** (paso B) de los grupos que todavía no los tienen, en lotes de veinte;
2. **el esquema** (paso C), determinista, desde los epígrafes oficiales y los hechos guardados;
3. **la redacción** (paso D) de los apartados que no tienen texto, cada uno con **todos** sus hechos
   y el material del tema que más se le parece;
4. **la comprobación** (paso E) de cada grupo contra el texto de su epígrafe: la letra y la frase
   copiada, verificada mecánicamente. Lo que falla se queda como hueco, se le añade el hecho que
   falta y el párrafo que lo integra, y se vuelve a comprobar **una** vez; lo que sigue fallando
   queda
   como duda con su motivo.

Cuatro decisiones que se ven en el código:

- **se reanuda, no se reinicia**: cada resultado se guarda en cuanto llega (hechos, apartados y
  comprobaciones), así que volver a ejecutar el mismo comando continúa donde se quedó y no vuelve a
  pagar por lo ya hecho. Es lo que permite una corrida de horas sin miedo a perderla;
- **un lote que falla no tumba la corrida**: la red se cae, el proveedor devuelve 502, y con cientos
  de llamadas eso pasa. Se anota, se sigue y el informe dice cuántos fueron; volver a ejecutar los
  reintenta. Parar todo por un timeout sería tirar lo ya pagado;
- **el texto de los apuntes va aparte por epígrafe en la comprobación**: es el mismo para todas las
  preguntas de ese epígrafe y así el proveedor puede cobrar la parte repetida a precio de caché;
- **lo que no se puede sostener se señala, no se rellena**: sin material, el apartado se escribe
igual
  (el plan lo permite a partir del hecho y de la norma) pero queda marcado para que el propietario
  lo
  mire.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from typing import TypeVar

from opofuente.application.ports import DossierRepository, NotesModel, TopicNotesRepository
from opofuente.application.topic_notes_models import (
    NotesNode,
    SectionReport,
    TopicNotesReport,
)
from opofuente.domain.errors import (
    ExternalServiceError,
    NotFoundError,
    OpoFuenteError,
    UnsupportedError,
)
from opofuente.domain.topic_notes import (
    LOTE_COMPROBACION,
    LOTE_HECHOS,
    SIN_MATERIAL,
    Coverage,
    Hecho,
    HechosBatch,
    NotesCheck,
    NoteSection,
    QuestionGroup,
    RedaccionBatch,
    esquema,
    evaluar,
    hechos_integrados,
    indexar_material,
    seleccionar_material,
)

logger = logging.getLogger("opofuente.application.topic_notes_service")

#: Intentos por llamada al modelo y espera entre ellos. Con cientos de llamadas, un 502 suelto es
#: normal; perder el lote por él obligaría a repetir la corrida entera.
INTENTOS_POR_LLAMADA = 3
ESPERA_ENTRE_INTENTOS = 2.0

T = TypeVar("T")


class TopicNotesService:
    """Escribe y comprueba los apuntes de un tema. No escribe por SQL: todo pasa por el
    repositorio."""

    def __init__(
        self,
        *,
        repository: TopicNotesRepository,
        dossier: DossierRepository,
        model: NotesModel,
        workers: int = 1,
        lote_hechos: int = LOTE_HECHOS,
        lote_comprobacion: int = LOTE_COMPROBACION,
    ) -> None:
        self._repository = repository
        self._dossier = dossier
        self._model = model
        self._workers = max(1, workers)
        self._lote_hechos = max(1, lote_hechos)
        self._lote_comprobacion = max(1, lote_comprobacion)

    # ------------------------------------------------------------------ la corrida

    def run(
        self,
        code: str,
        *,
        now: datetime,
        dry_run: bool = False,
        limite_grupos: int | None = None,
    ) -> TopicNotesReport:
        """Escribe y comprueba los apuntes del tema. `dry_run` llama al modelo y no escribe nada."""
        node_id = self._repository.node_id(code)
        if node_id is None:
            raise NotFoundError("tema del programa", code)
        nodo = self._repository.node(node_id)
        if nodo is None:
            raise UnsupportedError(f"«{code}» no es un tema del programa")
        if not nodo.epigraphs:
            raise UnsupportedError(
                f"el tema «{code}» no tiene epígrafes en el temario: sin epígrafes no hay "
                "apartados que escribir (revisa la siembra del programa)"
            )
        grupos = self._repository.question_groups(node_id)
        if not grupos:
            raise UnsupportedError(
                f"el tema «{code}» no tiene preguntas clasificadas: unos apuntes guiados por "
                "preguntas no tienen de dónde salir (clasifícalas antes)"
            )
        if limite_grupos is not None:
            grupos = grupos[:limite_grupos]
        informe = TopicNotesReport(
            topic_code=nodo.code,
            topic_title=nodo.title,
            node_id=node_id,
            groups=len(grupos),
            questions=sum(len(grupo.questions) for grupo in grupos),
            dry_run=dry_run,
        )

        hechos = self._paso_hechos(nodo, grupos, informe, now=now, dry_run=dry_run)
        secciones = self._paso_esquema(nodo, hechos, informe, now=now, dry_run=dry_run)
        self._paso_redaccion(nodo, secciones, informe, now=now, dry_run=dry_run)
        self._paso_comprobacion(nodo, grupos, informe, now=now, dry_run=dry_run)
        # El informe se cierra leyendo lo que quedó **guardado**: midiéndolo con la lista de
        # apartados anterior a la redacción, los tamaños saldrían a cero y el informe mentiría.
        informe.sections = self._informe_apartados(
            self._repository.sections(node_id) if not dry_run else secciones
        )
        return informe

    # ------------------------------------------------------------------ paso B: los hechos

    def _paso_hechos(
        self,
        nodo: NotesNode,
        grupos: Sequence[QuestionGroup],
        informe: TopicNotesReport,
        *,
        now: datetime,
        dry_run: bool,
    ) -> list[Hecho]:
        """Saca los hechos que faltan y devuelve **todos** los del tema, en orden."""
        guardados = list(self._repository.facts(nodo.node_id))
        cubiertas = {firma for hecho in guardados for firma in hecho.source_groups}
        pendientes = [grupo for grupo in grupos if grupo.signature not in cubiertas]
        lotes = list(_trozos(pendientes, self._lote_hechos))
        trabajos: list[Callable[[], HechosBatch]] = [
            partial(
                self._model.hechos,
                lote,
                topic_code=nodo.code,
                topic_title=nodo.title,
                epigraphs=nodo.epigraphs,
            )
            for lote in lotes
        ]
        resultados = self._en_paralelo(trabajos)
        for _lote, resultado in zip(lotes, resultados, strict=True):
            if resultado is None:
                informe.failed_batches += 1
                continue
            self._contar(
                informe, resultado.input_tokens, resultado.output_tokens, resultado.cache_hit_tokens
            )
            informe.hechos_dudosos += sum(1 for hecho in resultado.hechos if hecho.doubtful)
            informe.add_notes(
                None
                if not resultado.sin_hechos
                else f"el modelo no contestó por {len(resultado.sin_hechos)} pregunta(s): "
                + ", ".join(firma[:8] for firma in resultado.sin_hechos[:5])
            )
            if dry_run:
                guardados.extend(resultado.hechos)
                informe.facts_new += len(resultado.hechos)
                continue
            guardados.extend(self._repository.save_facts(nodo.node_id, resultado.hechos, now=now))
            informe.facts_new += len(guardados)
        if not dry_run:
            guardados = list(self._repository.facts(nodo.node_id))
        informe.facts = len(guardados)
        return guardados

    # ------------------------------------------------------------------ paso C: el esquema

    def _paso_esquema(
        self,
        nodo: NotesNode,
        hechos: Sequence[Hecho],
        informe: TopicNotesReport,
        *,
        now: datetime,
        dry_run: bool,
    ) -> list[NoteSection]:
        """El esquema del tema. Se recalcula entero: es determinista y el texto ya escrito se
        conserva.

        Volver a calcularlo es lo que permite que un hecho nuevo (de una pregunta clasificada
        después) encuentre su sitio sin tocar los apartados que ya estaban: los que existían
        conservan su texto porque su clave no cambia.

        Y si la clave **sí** cambia (han entrado hechos que mueven los trozos de un epígrafe), lo
        guardado se rehace: dejar los apartados viejos junto a los nuevos sería enseñar dos veces el
        mismo contenido y comprobar contra los dos. Rehacerlo cuesta volver a comprobar, y es lo
        correcto: el tema queda con **un solo** texto por subapartado.
        """
        planes = esquema(nodo.epigraphs, hechos)
        informe.sections = self._informe_apartados(planes)
        if dry_run:
            return list(planes)
        guardadas = self._repository.sections(nodo.node_id)
        sobran = {apartado.key for apartado in guardadas} - {plan.key for plan in planes}
        if sobran:
            informe.add_notes(
                f"el esquema se movió: {len(sobran)} apartado(s) que ya no están en el plan se "
                "rehacen, con sus comprobaciones (el texto se vuelve a escribir)"
            )
            self._repository.forget_sections(nodo.node_id)
        return list(self._repository.save_sections(nodo.node_id, planes, now=now))

    # ------------------------------------------------------------------ paso D: la redacción

    def _paso_redaccion(
        self,
        nodo: NotesNode,
        secciones: Sequence[NoteSection],
        informe: TopicNotesReport,
        *,
        now: datetime,
        dry_run: bool,
    ) -> None:
        """Escribe los apartados que no tienen texto. Todos sus hechos van dentro."""
        material = indexar_material(self._dossier.passages_for_node(nodo.node_id))
        sin_escribir = [apartado for apartado in secciones if not apartado.body_markdown.strip()]
        if not sin_escribir:
            return
        selecciones = {
            apartado.key: seleccionar_material(apartado.facts, material)
            for apartado in sin_escribir
        }
        trabajos: list[Callable[[], RedaccionBatch]] = [
            partial(
                self._model.redactar,
                apartado,
                topic_code=nodo.code,
                topic_title=nodo.title,
                material=selecciones[apartado.key],
            )
            for apartado in sin_escribir
        ]
        resultados = self._en_paralelo(trabajos)
        anotaciones: dict[str, tuple[tuple[str, ...], str | None]] = {}
        for apartado, resultado in zip(sin_escribir, resultados, strict=True):
            if resultado is None:
                informe.failed_batches += 1
                continue
            self._contar(
                informe, resultado.input_tokens, resultado.output_tokens, resultado.cache_hit_tokens
            )
            faltan = hechos_integrados(apartado.facts, resultado.markdown)
            motivo = _motivo_de_revision(
                sin_material=not selecciones[apartado.key], faltan=faltan, hechos=apartado.facts
            )
            anotaciones[apartado.key] = (faltan, motivo)
            if not dry_run:
                self._repository.save_section_body(
                    apartado,
                    title=resultado.titulo,
                    body=resultado.markdown,
                    needs_review_reason=motivo,
                    model=self._model.version,
                    now=now,
                )
        informe.sections = self._informe_apartados(
            self._repository.sections(nodo.node_id) if not dry_run else secciones,
            anotaciones,
        )

    # ------------------------------------------------------------------ paso E: la comprobación

    def _paso_comprobacion(
        self,
        nodo: NotesNode,
        grupos: Sequence[QuestionGroup],
        informe: TopicNotesReport,
        *,
        now: datetime,
        dry_run: bool,
    ) -> None:
        """Comprueba cada grupo contra el texto de su epígrafe y vuelve una vez sobre los huecos.

        Los hechos se leen **aquí**, después del esquema, y no se reutiliza la lista del paso B: es
        el
        paso C el que les dice a qué apartado pertenecen, y con la lista anterior (sin apartado)
        todas las preguntas de un epígrafe acabarían apuntando a su primer apartado en vez de al que
        contiene sus hechos. El rastro pregunta → párrafo depende de esa lectura.
        """
        if dry_run:
            return
        secciones = list(self._repository.sections(nodo.node_id))
        por_clave = {apartado.key: apartado for apartado in secciones}
        hechos_por_firma = _hechos_por_firma(self._repository.facts(nodo.node_id))
        epigrafe_por_defecto = nodo.epigraphs[0][0]
        comprobables: list[tuple[QuestionGroup, NoteSection]] = []
        for grupo in grupos:
            apartado = _apartado_de(
                grupo, secciones, por_clave, hechos_por_firma, epigrafe_por_defecto
            )
            if apartado is None or not apartado.body_markdown.strip():
                continue
            comprobables.append((grupo, apartado))
        informe.coverage.groups = len(comprobables)

        previos = {
            resultado.group_signature: resultado
            for resultado in self._repository.checks(nodo.node_id)
        }
        resultados = self._comprobar(
            nodo,
            secciones,
            [pareja for pareja in comprobables if pareja[0].signature not in previos],
            hechos_por_firma,
            informe,
            now=now,
            attempts=1,
        )
        finales = {**previos, **resultados}

        huecos = [
            pareja
            for pareja in comprobables
            if _cobertura(finales.get(pareja[0].signature)) is Coverage.HUECO
        ]
        if huecos:
            finales.update(
                self._segunda_vuelta(nodo, huecos, hechos_por_firma, previos, informe, now=now)
            )

        dudosos_de_la_clave = {
            firma
            for firma, suyos in hechos_por_firma.items()
            if any(hecho.doubtful for hecho in suyos)
        }
        for grupo, _apartado in comprobables:
            resultado = finales.get(grupo.signature)
            if resultado is None:
                continue
            informe.coverage.add(
                resultado.coverage,
                resultado.note,
                attempts=resultado.attempts,
                clave_activa=resultado.key_status.clara,
            )
            if grupo.signature in dudosos_de_la_clave:
                # El paso B señaló la clave: la pregunta se revisa aunque los apuntes la contesten.
                informe.coverage.incidencias_clave_marcada += 1
        informe.sections = self._informe_apartados(secciones, {})

    def _comprobar(
        self,
        nodo: NotesNode,
        secciones: Sequence[NoteSection],
        objetivo: Sequence[tuple[QuestionGroup, NoteSection]],
        hechos_por_firma: dict[str, list[Hecho]],
        informe: TopicNotesReport,
        *,
        now: datetime,
        attempts: int,
    ) -> dict[str, NotesCheck]:
        """Comprueba un conjunto de grupos, agrupados por epígrafe y en lotes, y guarda el
        resultado."""
        por_epigrafe: dict[str, list[tuple[QuestionGroup, NoteSection]]] = {}
        for grupo, apartado in objetivo:
            por_epigrafe.setdefault(apartado.epigraph_code, []).append((grupo, apartado))
        resultados: dict[str, NotesCheck] = {}
        for epigrafe, suyos in por_epigrafe.items():
            apuntes, verificable = _texto_de_epigrafe(secciones, epigrafe)
            for lote in _trozos(suyos, self._lote_comprobacion):
                grupos_lote = [grupo for grupo, _ in lote]
                resultado = self._llamada(
                    partial(self._model.comprobar, grupos_lote, apuntes=apuntes),
                    informe,
                )
                if resultado is None:
                    continue
                self._contar(
                    informe,
                    resultado.input_tokens,
                    resultado.output_tokens,
                    resultado.cache_hit_tokens,
                )
                respuestas = {check.group_signature: check for check in resultado.checks}
                pendientes: list[NotesCheck] = []
                for grupo, apartado in lote:
                    evaluado = evaluar(
                        grupo=grupo,
                        check=respuestas.get(grupo.signature),
                        apuntes=verificable,
                        section=apartado,
                        attempts=attempts,
                        clave_dudosa=any(
                            hecho.doubtful for hecho in hechos_por_firma.get(grupo.signature, ())
                        ),
                    )
                    resultados[grupo.signature] = evaluado
                    pendientes.extend(_expandir(evaluado, grupo))
                self._repository.save_checks(nodo.node_id, pendientes, now=now)
        return resultados

    def _segunda_vuelta(
        self,
        nodo: NotesNode,
        huecos: Sequence[tuple[QuestionGroup, NoteSection]],
        hechos_por_firma: dict[str, list[Hecho]],
        previos: dict[str, NotesCheck],
        informe: TopicNotesReport,
        *,
        now: datetime,
    ) -> dict[str, NotesCheck]:
        """El añadido: el hecho que falta, el párrafo que lo integra y otra comprobación.

        El hecho se busca primero entre los que ya hay (el paso B ya escribió los de esa pregunta):
        lo
        que falta entonces no es el hecho, es que el texto no lo dice. Solo se piden hechos nuevos a
        las preguntas que no tienen ninguno, que son las que el modelo no contestó en el paso B.
        """
        por_apartado: dict[str, list[QuestionGroup]] = {}
        for grupo, apartado in huecos:
            por_apartado.setdefault(apartado.key, []).append(grupo)
        secciones = {apartado.key: apartado for apartado in self._repository.sections(nodo.node_id)}
        resultados: dict[str, NotesCheck] = {}
        for clave, grupos in por_apartado.items():
            seccion = secciones.get(clave)
            if seccion is None:
                continue
            faltantes = [
                hecho for grupo in grupos for hecho in hechos_por_firma.get(grupo.signature, ())
            ]
            sin_hecho = [grupo for grupo in grupos if not hechos_por_firma.get(grupo.signature)]
            if sin_hecho:
                nuevos = self._llamada(
                    partial(
                        self._model.hechos,
                        sin_hecho,
                        topic_code=nodo.code,
                        topic_title=nodo.title,
                        epigraphs=nodo.epigraphs,
                    ),
                    informe,
                )
                if nuevos is not None:
                    self._contar(
                        informe, nuevos.input_tokens, nuevos.output_tokens, nuevos.cache_hit_tokens
                    )
                    guardados = self._repository.save_facts(nodo.node_id, nuevos.hechos, now=now)
                    faltantes.extend(guardados)
                    for hecho in guardados:
                        hechos_por_firma.setdefault(
                            hecho.source_groups[0] if hecho.source_groups else "", []
                        ).append(hecho)
                    self._repository.save_sections(
                        nodo.node_id,
                        [
                            NoteSection(
                                key=seccion.key,
                                epigraph_code=seccion.epigraph_code,
                                title=seccion.title,
                                anchor=seccion.anchor,
                                position=seccion.position,
                                facts=tuple(faltantes),
                            )
                        ],
                        now=now,
                    )
            anadido = self._llamada(
                partial(self._model.anadir, seccion, grupos, faltantes),
                informe,
            )
            if anadido is None:
                continue
            self._contar(
                informe, anadido.input_tokens, anadido.output_tokens, anadido.cache_hit_tokens
            )
            seccion = self._repository.save_section_body(
                seccion,
                title=None,
                body=anadido.markdown,
                needs_review_reason=seccion.needs_review_reason,
                model=self._model.version,
                now=now,
                append=True,
            )
            resultados.update(
                self._comprobar(
                    nodo,
                    [*secciones.values(), seccion],
                    [(grupo, seccion) for grupo in grupos],
                    hechos_por_firma,
                    informe,
                    now=now,
                    attempts=2,
                )
            )
        return resultados

    # ------------------------------------------------------------------ utilidades

    def _en_paralelo(self, trabajos: Sequence[Callable[[], T]]) -> list[T | None]:
        """Las llamadas al modelo, con `workers` a la vez, sin que un fallo pare todo.

        La escritura en la base **no** ocurre aquí: las llamadas devuelven lo que contestó el modelo
        y
        el hilo principal lo aplica. Dos escrituras a la vez sobre la misma base SQLite serían una
        fuente de bloqueos a cambio de nada.
        """
        if not trabajos:
            return []
        if self._workers <= 1 or len(trabajos) == 1:
            return [self._seguro(trabajo) for trabajo in trabajos]
        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            return list(pool.map(self._seguro, trabajos))

    def _seguro(self, trabajo: Callable[[], T]) -> T | None:
        """Una llamada al modelo que no tumba la corrida: se reintenta y, si no, se sigue.

        Se reintenta **solo** lo que puede fallar por la red o por el proveedor
        (`ExternalServiceError`): un error del que ya sabemos que no se arregla repitiendo (un
        código
        que no existe, un nodo que falta) se registra y se sigue sin gastar tres llamadas en él.
        Agotados los intentos, el lote queda sin escribir, se cuenta en el informe y volver a
        ejecutar el comando lo reintenta.
        """
        for intento in range(1, INTENTOS_POR_LLAMADA + 1):
            try:
                return trabajo()
            except ExternalServiceError as error:
                if intento >= INTENTOS_POR_LLAMADA:
                    logger.warning("llamada al modelo fallida tras %s intentos: %s", intento, error)
                    return None
                logger.info("reintento %s/%s: %s", intento, INTENTOS_POR_LLAMADA, error)
                time.sleep(ESPERA_ENTRE_INTENTOS * intento)
            except OpoFuenteError as error:
                logger.warning("llamada al modelo fallida: %s", error)
                return None
        return None

    def _llamada(self, trabajo: Callable[[], T], informe: TopicNotesReport) -> T | None:
        resultado = self._seguro(trabajo)
        if resultado is None:
            informe.failed_batches += 1
        return resultado

    @staticmethod
    def _contar(informe: TopicNotesReport, entrada: int, salida: int, cache: int = 0) -> None:
        informe.ledger.add(input_tokens=entrada, output_tokens=salida, cache_hit_tokens=cache)

    @staticmethod
    def _informe_apartados(
        secciones: Sequence[NoteSection],
        anotaciones: dict[str, tuple[tuple[str, ...], str | None]] | None = None,
    ) -> tuple[SectionReport, ...]:
        notas = anotaciones or {}
        return tuple(
            SectionReport(
                key=apartado.key,
                title=apartado.title,
                epigraph_code=apartado.epigraph_code,
                anchor=apartado.anchor,
                facts=len(apartado.facts),
                body_chars=len(apartado.body_markdown),
                hechos_sin_integrar=notas.get(apartado.key, ((), None))[0],
                needs_review_reason=(
                    notas.get(apartado.key, ((), None))[1] or apartado.needs_review_reason
                ),
            )
            for apartado in secciones
        )


def _trozos[T](elementos: Sequence[T], tamano: int) -> Iterable[Sequence[T]]:
    for inicio in range(0, len(elementos), tamano):
        yield elementos[inicio : inicio + tamano]


def _hechos_por_firma(hechos: Sequence[Hecho]) -> dict[str, list[Hecho]]:
    """Los hechos indexados por el grupo de preguntas del que salieron."""
    indice: dict[str, list[Hecho]] = {}
    for hecho in hechos:
        for firma in hecho.source_groups:
            indice.setdefault(firma, []).append(hecho)
    return indice


def _apartado_de(
    grupo: QuestionGroup,
    secciones: Sequence[NoteSection],
    por_clave: dict[str, NoteSection],
    hechos_por_firma: dict[str, list[Hecho]],
    epigrafe_por_defecto: str,
) -> NoteSection | None:
    """En qué apartado cae un grupo: el de sus hechos y, si no tiene, el primero de su epígrafe."""
    suyos = hechos_por_firma.get(grupo.signature, ())
    for hecho in suyos:
        apartado = por_clave.get(hecho.section_key)
        if apartado is not None:
            return apartado
    epigrafe = grupo.epigraph_code or next(
        (hecho.epigraph_code for hecho in suyos), epigrafe_por_defecto
    )
    return next(
        (apartado for apartado in secciones if apartado.epigraph_code == epigrafe),
        secciones[0] if secciones else None,
    )


def _texto_de_epigrafe(secciones: Sequence[NoteSection], epigrafe: str) -> tuple[str, str]:
    """El texto de un epígrafe para comprobar, en dos formas: la del modelo y la verificable.

    La primera lleva delante el anclaje y el título de cada apartado para que el modelo sepa dónde
    está; la segunda es el mismo texto **sin esos encabezados**, y es contra la que se verifica la
    frase copiada. La diferencia importa: un encabezado lo escribimos nosotros, no es una frase de
    los
    apuntes, y no puede justificar una respuesta. Lo que el modelo lee y lo que se comprueba salen
    de
    la misma lectura, así que no pueden divergir.
    """
    partes = [
        (
            f"## {apartado.anchor} · {apartado.title}\n\n{apartado.body_markdown}",
            apartado.body_markdown,
        )
        for apartado in secciones
        if apartado.epigraph_code == epigrafe and apartado.body_markdown.strip()
    ]
    return ("\n\n".join(parte[0] for parte in partes), "\n\n".join(parte[1] for parte in partes))


def _expandir(resultado: NotesCheck, grupo: QuestionGroup) -> tuple[NotesCheck, ...]:
    """Un resultado por **cada** pregunta del grupo: el rastro tiene que valer para todas.

    Las preguntas repetidas entre bancos comparten grupo y comprobación: si se guardara solo la del
    representante, la mitad del banco no tendría a qué párrafo ir.
    """
    return tuple(
        NotesCheck(
            question_version_id=question_id,
            group_signature=resultado.group_signature,
            section_key=resultado.section_key,
            anchor=resultado.anchor,
            coverage=resultado.coverage,
            note=resultado.note,
            quote=resultado.quote,
            letter=resultado.letter,
            expected=resultado.expected,
            key_status=resultado.key_status,
            attempts=resultado.attempts,
        )
        for question_id in grupo.question_ids
    )


def _cobertura(resultado: NotesCheck | None) -> Coverage | None:
    return None if resultado is None else resultado.coverage


def _motivo_de_revision(
    *, sin_material: bool, faltan: Sequence[str], hechos: Sequence[Hecho]
) -> str | None:
    """Por qué un apartado queda marcado para el propietario (si queda)."""
    if sin_material:
        return SIN_MATERIAL
    if hechos and len(faltan) > len(hechos) / 2:
        return f"{len(faltan)} de {len(hechos)} hechos no aparecen en el texto"
    return None


__all__ = ["TopicNotesService"]
