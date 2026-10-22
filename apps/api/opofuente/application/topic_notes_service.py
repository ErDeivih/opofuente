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
import re
import time
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
from functools import partial
from typing import NamedTuple, TypeVar

from opofuente.application.ports import DossierRepository, NotesModel, TopicNotesRepository
from opofuente.application.topic_notes_models import (
    CoverageReport,
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
from opofuente.domain.notes_quality import (
    encabezados,
    escapar_tuberias_en_celdas,
    limpiar_andamios,
    nombrar_columnas_sin_titulo,
    quitar_encabezado_repetido,
    revisar_apuntes,
    sin_encabezados_repetidos,
)
from opofuente.domain.puertos import limpiar_tabla_de_puertos
from opofuente.domain.topic_index import (
    MAX_HECHOS_POR_APARTADO,
    IndiceDelTema,
    catalogo,
    es_la_tabla_de_puertos,
    indice_de,
    plan_de,
    revisar_indice,
)
from opofuente.domain.topic_notes import (
    LOTE_COMPROBACION,
    LOTE_HECHOS,
    SIN_MATERIAL,
    TEXTO_SIN_MATERIA,
    VUELTAS_CON_HUECOS,
    CategoriaIncidencia,
    Coverage,
    Hecho,
    HechosBatch,
    IncidenciaDeApuntes,
    KeyStatus,
    MaterialPassage,
    Motivo,
    NotesCheck,
    NoteSection,
    QuestionGroup,
    RedaccionBatch,
    categoria_de,
    detalle_de_incidencia,
    esquema,
    evaluar,
    hechos_integrados,
    huella_de_texto,
    indexar_material,
    seleccionar_material,
)

logger = logging.getLogger("opofuente.application.topic_notes_service")

#: Intentos por llamada al modelo y espera entre ellos. Con cientos de llamadas, un 502 suelto es
#: normal; perder el lote por él obligaría a repetir la corrida entera.
INTENTOS_POR_LLAMADA = 3
ESPERA_ENTRE_INTENTOS = 2.0

#: Presupuesto de caracteres del texto que se manda a comprobar una pregunta. La unión de sus
#: apartados va siempre; el resto de sus epígrafes, mientras quepa aquí. El número no es de
#: epígrafe entero de un tema normativo no cabe en la ventana del modelo (el primer epígrafe de I.1
#: son ≈300.000 caracteres) y un apartado con sus hermanos pequeños sí, que es el caso de I.6
#: (≈50.000 en su epígrafe más largo).
PRESUPUESTO_CARACTERES_COMPROBACION = 60_000

#: Lo que costó, de media, **una llamada** al modelo. Es lo que convierte una previsión de llamadas
#: en una previsión de dinero, que es la cifra con la que se decide si un tema cabe en el tope de la
#: tanda (1,20 $) o si hay que reducirle el alcance.
#:
#: No es una tarifa inventada: se mide sobre las **cinco** corridas grandes que hay registradas en
#: `docs/ESTADO-DEL-OBJETIVO.md` §1, con los tokens que devolvió cada llamada y la tabla de precios
#: del proyecto (entrada 0,15 $/M y salida 0,60 $/M):
#:
#: - I.1 (355 llamadas, 1,9593 $) → 0,00552 $ por llamada;
#: - IV.7, la corrida del reparto por materia (92 llamadas, 0,5955 $) → 0,00647 $;
#: - I.6, la reescritura con el tope del añadido (74 llamadas, 0,5116 $) → 0,00691 $;
#: - I.2 (194 llamadas, 1,2187 $) → 0,00628 $;
#: - I.4 (169 llamadas, 1,4625 $) → 0,00865 $.
#:
#: La media de las cinco es este número, redondeado hacia arriba.
#:
#: **Y lo que hay que saber al leer la previsión**: la media esconde un recorrido de casi el 60 %
#: (de 0,0055 $ a 0,0087 $ por llamada), y los dos temas **normativos** densos —I.2 e I.4— caen en
#: la parte alta, porque una llamada de estos temas devuelve mucho más texto (I.4: 11.518 tokens
#: de salida por llamada, el doble que la media de las tres antiguas). Por eso la cota de arriba de
#: `--prever` es un **suelo** para un tema así y no un techo: I.4 se previó en 1,03 $ y costó
#: 1,4625 $. Con el tope de 1,20 $ por tema, la decisión se toma sobre la cota de arriba **más un
#: tercio** cuando el tema es normativo y denso.
COSTE_MEDIO_POR_LLAMADA_USD = 0.0068

T = TypeVar("T")


class _TiempoDeLaCorridaAgotadoError(Exception):
    """Se acabó el tiempo de la corrida: no se empieza ninguna llamada más.

    No es un `OpoFuenteError` a propósito. Un error de esos lo traga `_seguro` y la corrida sigue
    con el lote siguiente, que es lo correcto para un fallo de red puntual y lo **contrario** de lo
    que se quiere aquí: si el tope de tiempo se tragara como un fallo, la corrida seguiría gastando
    llamada a llamada hasta el final. Esta excepción sube hasta `run`, que la cuenta y para.
    """


class IndicacionDeLectura(NamedTuple):
    """Lo que dijo quien leyo un apartado, **y a que apartado se refiere** (M7).

    **No es una instruccion general**: viaja atada a un `section_key`, **y solo
    ese apartado se redacta con ella**. Un aviso sobre un parrafo no puede
    cambiar los otros veinte del tema, **y una indicacion sin apartado no se
    admite** — si se admite, se acaba pegando un aviso a un tema entero.
    """

    #: La clave del apartado, la misma que `--olvidar-apartado`.
    section_key: str
    #: El texto del alumno, tal cual.
    text: str


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
        indicacion: IndicacionDeLectura | None = None,
    ) -> None:
        self._repository = repository
        self._dossier = dossier
        self._model = model
        self._workers = max(1, workers)
        self._lote_hechos = max(1, lote_hechos)
        self._lote_comprobacion = max(1, lote_comprobacion)
        #: **La indicacion de este aviso, si viene de uno** (M7): va al apartado
        #: que dice y a ninguno mas.
        self._indicacion = indicacion
        #: Cuándo se agota el tiempo de **esta** corrida (`time.monotonic()`), o `None` sin tope.
        #: Se pone al arrancar `run` y se consulta antes de cada llamada al modelo.
        self._se_acaba_a_las: float | None = None

    def _agotado(self) -> bool:
        """¿Se ha pasado el tope de tiempo de la corrida?

        Se mira **antes** de cada llamada y no dentro: lo que hay que evitar es empezar llamadas
        nuevas, no cortar a mitad la que está en curso (cortarla dejaría un lote pagado y sin
        escribir). Con el tope agotado, la corrida deja de llamar y dice lo que ha dejado a medias;
        lo ya escrito se queda escrito y volver a lanzar el comando sigue desde ahí.
        """
        return self._se_acaba_a_las is not None and time.monotonic() >= self._se_acaba_a_las

    # ------------------------------------------------------------------ la corrida

    def run(
        self,
        code: str,
        *,
        now: datetime,
        dry_run: bool = False,
        limite_grupos: int | None = None,
        maximo_segundos: float | None = None,
    ) -> TopicNotesReport:
        """Escribe y comprueba los apuntes del tema. `dry_run` llama al modelo y no escribe nada.

        `maximo_segundos` es el tope de tiempo de la corrida **entera** (el de cada llamada es del
        cliente, `--tiempo`). Al agotarse, la llamada en curso termina y **no se empieza ninguna
        otra**: lo escrito se queda escrito, el informe dice lo que ha quedado a medias y volver a
        lanzar el comando sigue desde ahí. Sin tope (`None`, el valor por defecto) la corrida hace
        todo su trabajo, como siempre.
        """
        self._se_acaba_a_las = (
            None if maximo_segundos is None else time.monotonic() + max(0.0, maximo_segundos)
        )
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

        # Se declaran antes del `try` para que el tope de tiempo pueda cortar la corrida en
        # cualquier paso: sin esto, cortarla antes de la redacción dejaría el informe sin poder
        # cerrarse (y el informe es lo que dice qué ha quedado a medias).
        hechos: list[Hecho] = []
        secciones: list[NoteSection] = []
        indice: IndiceDelTema | None = None
        try:
            hechos = self._paso_hechos(nodo, grupos, informe, now=now, dry_run=dry_run)
            secciones, indice = self._paso_esquema(nodo, hechos, informe, now=now, dry_run=dry_run)
            self._paso_redaccion(nodo, secciones, informe, now=now, dry_run=dry_run)
            self._paso_comprobacion(nodo, grupos, informe, now=now, dry_run=dry_run, indice=indice)
            # La última vuelta del paso E: lo que sigue sin cubrirse se intenta rellenar **una vez
            # más** (el hueco de verdad, no el que ya se intentó) y lo que quede va a la bandeja del
            # propietario con su categoría. Es el §2.1.4: antes de cerrar un tema, rellenar lo
            # que se pueda y no dejar dudas sin dueño.
            self._paso_huecos(nodo, grupos, informe, now=now, dry_run=dry_run, indice=indice)
        except _TiempoDeLaCorridaAgotadoError:
            # El tope de tiempo: se para de llamar y se dice. No se tira nada de lo escrito: el
            # informe que sigue mide lo que hay en la base y la corrida siguiente sigue desde ahí.
            informe.add_notes(
                f"se agotó el tiempo de la corrida ({maximo_segundos:g} s): no se han hecho las "
                "llamadas que quedaban. Lo escrito está guardado y volver a lanzar el comando "
                "sigue "
                "desde ahí"
            )
        # El final del informe se mide **desde la base**, no desde las listas de la corrida: si el
        # tope de tiempo la cortó a mitad, esas listas no existen y lo que hay que contar es lo que
        # quedó escrito. Con la corrida entera el resultado es el mismo, porque cada paso guarda lo
        # suyo antes de devolverlo.
        hechos = list(self._repository.facts(node_id)) if not dry_run else hechos
        secciones = list(self._repository.sections(node_id)) if not dry_run else secciones
        # La revisión de forma se mide sobre el texto que ha quedado guardado, y con **todos** los
        # hechos del tema: es la comprobación que decide si estos apuntes se pueden dar por buenos
        # (encabezados repetidos, marcas internas, tablas sin cabecera, párrafos repetidos y
        # extensión frente a los hechos que tiene el tema).
        informe.revision = revisar_apuntes(secciones, hechos)
        # El recuento de la cobertura se rehace **desde lo guardado** al terminar: el bucle de
        # huecos
        # vuelve a comprobar grupos y guarda resultados nuevos, y sin esto el informe de la corrida
        # decía menos cobertura de la que el tema acababa teniendo (I.1: 1.947 de 1.995 en el
        # informe,
        # 1.965 de 1.995 en la base).
        self._recontar_cobertura(
            nodo,
            grupos,
            informe,
            hechos,
            secciones,
            indice,
        )
        # El informe se cierra leyendo lo que quedó **guardado**: midiéndolo con la lista de
        # apartados anterior a la redacción, los tamaños saldrían a cero y el informe mentiría.
        informe.sections = self._informe_apartados(secciones)
        return informe

    def medir(self, code: str) -> TopicNotesReport:
        """Mide el tema **guardado**, sin llamar a nadie.

        Es lo que permite decir una cifra sin volver a pagarla: la cobertura sale de las
        comprobaciones guardadas y del **mismo recuento** que hace una corrida
        (`_paso_comprobacion`), y la revisión de forma, del texto que hay hoy en la base. Sin esto,
        la única forma de saber cómo está un tema era volver a ejecutarlo —y volver a pagarlo—, y
        una cifra que va a un documento se mide, no se hereda.

        Dos cosas que hace igual que la corrida y por eso se puede comparar con ella: cuenta la
        puerta **pregunta a pregunta** con los dos denominadores, y marca como no utilizables las
        claves que el paso B señaló (`doubtful`). Lo único que no puede reconstruir es el texto
        contra el que se comprobó cada cita: eso lo dice la huella, y aquí solo se enseña si sigue
        valiendo para el texto de hoy.
        """
        node_id = self._repository.node_id(code)
        if node_id is None:
            raise NotFoundError("tema del programa", code)
        nodo = self._repository.node(node_id)
        if nodo is None:
            raise UnsupportedError(f"«{code}» no es un tema del programa")
        grupos = self._repository.question_groups(node_id)
        hechos = self._repository.facts(node_id)
        informe = TopicNotesReport(
            topic_code=nodo.code,
            topic_title=nodo.title,
            node_id=node_id,
            groups=len(grupos),
            questions=sum(len(grupo.questions) for grupo in grupos),
            facts=len(hechos),
        )
        secciones = list(self._repository.sections(node_id))
        # El índice también se mide: es lo primero que decide si el tema se puede redactar, y sin
        # esto habría que volver a ejecutar el tema entero para saber si el árbol cuadra.
        planes, indice = self._plan_del_tema(nodo, hechos)
        if indice is not None:
            informe.indice = revisar_indice(indice, planes)
            informe.sin_materia = sum(len(grupo.questions) for grupo in indice.grupos_sin_materia)
            informe.sections = self._informe_apartados(planes)
        self._recontar_cobertura(nodo, grupos, informe, hechos, secciones, indice)
        informe.revision = revisar_apuntes(secciones, hechos)
        informe.sections = self._informe_apartados(secciones)
        return informe

    def _recontar_cobertura(
        self,
        nodo: NotesNode,
        grupos: Sequence[QuestionGroup],
        informe: TopicNotesReport,
        hechos: Sequence[Hecho],
        secciones: Sequence[NoteSection],
        indice: IndiceDelTema | None,
    ) -> None:
        """Vuelve a contar la cobertura **desde lo guardado**, sobre un informe recién empezado.

        Es el mismo recuento que hace `_paso_comprobacion` mientras comprueba, pero leído del estado
        final. Hace falta porque el bucle de huecos **vuelve a comprobar** grupos y guarda el
        resultado nuevo sin rehacer aquel recuento: el informe de una corrida acababa diciendo menos
        cobertura de la que el tema tenía de verdad (I.1: el informe dijo 1.947 de 1.995 y el tema
        quedó en 1.965 de 1.995, un 98,5 %). Una cifra que va a un documento se mide, no se hereda —
        ni siquiera de la propia corrida.

        El recuento en sí vive en `_contar_cobertura`, que es el **único** sitio donde se cuenta: la
        corrida y el comando tienen que dar la misma cifra, y con dos bucles separados dejaban de
        darla en cuanto una regla cambiaba en uno solo.
        """
        self._contar_cobertura(nodo, grupos, informe, hechos, secciones, indice)
        # Y la bandeja del propietario, contada **desde la base**: es lo que él va a ver, y lo que
        # el
        # informe enseña tiene que ser eso, no lo que la corrida creía haber escrito.
        for incidencia in self._repository.incidents(nodo.node_id):
            informe.coverage.incidencias += 1
            informe.coverage.por_categoria[incidencia.category] = (
                informe.coverage.por_categoria.get(incidencia.category, 0) + 1
            )

    def _contar_cobertura(
        self,
        nodo: NotesNode,
        grupos: Sequence[QuestionGroup],
        informe: TopicNotesReport,
        hechos: Sequence[Hecho],
        secciones: Sequence[NoteSection],
        indice: IndiceDelTema | None,
    ) -> None:
        """La puerta de cobertura, contada **una vez por pregunta** y **solo con anclas propias**.

        Cuatro reglas, y las tres primeras son el mismo agujero visto desde tres sitios (F25c:
        «nadie comprueba que el sitio donde acaba un hecho o una comprobación sea suyo»):

        1. **una vez por pregunta.** Antes la misma pregunta entraba dos veces —una como hueco, por
           estar en `grupos_sin_materia`, y otra con su comprobación guardada, anclada por el
           respaldo al primer apartado de su epígrafe—, así que el cociente salía por debajo del
           verdadero y podía **bloquear un tema que merecía pasar**. Era el caso de **16 de los 28
           temas con apuntes** cuando se arregló (91 preguntas, entre +0,3 y +8,1 puntos; la primera
           medición, con 19 temas, dio 10 temas y 41 preguntas). Aquí cada grupo se mira **una sola
           vez**;
        2. **con anclas propias.** La comprobación de una pregunta cuenta si su ancla es un apartado
           **suyo** (`IndiceDelTema.apartados_propios_de`): los de sus hechos y, si no tiene ninguno
           colocado, el de la materia en la que el índice la sitúa. Una comprobación anclada en un
           apartado ajeno **no cuenta como cobertura de este tema**: es la puerta que faltaba desde
           I.3, donde las cinco respuestas del estándar del CPD se contaban con una comprobación
           anclada en un apartado que no era el suyo (`i-3-1-otros`);
        3. **lo que no tiene apartado propio cuenta como no cubierto**, y no se cae del denominador:
           si se cayera, la puerta se mediría sobre un conjunto del que se han ido justo las que
           peor están;
        4. **lo que tiene apartado propio y no tiene comprobación guardada es PENDIENTE DE
           COMPROBAR**: cuenta en el denominador y no en el numerador, y se cuenta aparte
           (`CoverageReport.pendientes`). Es el §4 de
           `SIGUIENTE-TANDA-CIERRE-DEL-OBJETIVO-2026-10`, y es la regla que faltaba: antes este
           grupo se caía de la puerta por los dos lados (`continue`), así que un tema con
           apartados y sin comprobaciones medía **«0 de 0»** —denominador vacío— y el trabajo que
           le quedaba por hacer desaparecía de la cifra. Un grupo así **no** se da por cubierto
           (sería mentira) ni se cae del denominador (sería peor: esconde trabajo por hacer).
        """
        informe.coverage = CoverageReport()
        informe.coverage.preguntas = informe.questions
        anclas = self._anclas_propias(nodo, grupos, secciones, indice)
        con_texto = {
            firma: apartados
            for firma, apartados in anclas.items()
            if any(apartado.body_markdown.strip() for apartado in apartados)
        }
        informe.coverage.groups = len(con_texto)
        hechos_por_firma = _hechos_por_firma(hechos)
        dudosos_de_la_clave = {
            firma
            for firma, suyos in hechos_por_firma.items()
            if any(hecho.doubtful for hecho in suyos)
        }
        sin_materia = {grupo.signature for grupo in _grupos_sin_materia(indice)}
        por_firma = {
            resultado.group_signature: resultado
            for resultado in self._repository.checks(nodo.node_id)
        }
        vigentes = 0
        for grupo in grupos:
            firma = grupo.signature
            apartados = con_texto.get(firma, ())
            resultado = por_firma.get(firma)
            if apartados and resultado is not None:
                if resultado.text_sha256 == _huella_de(secciones, apartados):
                    vigentes += 1
                informe.coverage.add(
                    resultado.coverage,
                    resultado.note,
                    attempts=resultado.attempts,
                    clave_activa=resultado.key_status.clara,
                    preguntas=len(grupo.questions),
                    clave_utilizable=firma not in dudosos_de_la_clave,
                    tiene_clave=resultado.key_status is not KeyStatus.NINGUNA,
                )
                if firma in dudosos_de_la_clave:
                    informe.coverage.incidencias_clave_marcada += 1
                continue
            if apartados:
                # Tiene apartado propio y **no** hay comprobación guardada: es el quinto desenlace,
                # «pendiente de comprobar». Ni cubierta —no hay nada que lo demuestre— ni ausente
                # —hay apartado escrito para ella y trabajo hecho—: entra en el denominador y no en
                # el numerador, y se cuenta aparte. Antes se caía de la puerta por los dos lados y
                # un tema con apartados y sin comprobaciones medía «0 de 0».
                informe.coverage.add_pendiente(
                    preguntas=len(grupo.questions),
                    clave_utilizable=firma not in dudosos_de_la_clave,
                    tiene_clave=grupo.key_status is not KeyStatus.NINGUNA,
                )
                continue
            if resultado is None and firma not in sin_materia:
                # Su apartado propio está vacío y nunca se comprobó: no hay nada que contar.
                continue
            # Sin apartado propio: no está cubierta, se cuenta **una sola vez** y con su resultado
            # guardado a la vista no cuenta como cobertura.
            informe.coverage.add(
                Coverage.HUECO,
                None,
                attempts=1,
                clave_activa=grupo.key_status.clara,
                preguntas=len(grupo.questions),
                clave_utilizable=firma not in dudosos_de_la_clave,
                tiene_clave=grupo.key_status is not KeyStatus.NINGUNA,
            )
        informe.coverage.comprobaciones_vigentes = vigentes

    def _anclas_propias(
        self,
        nodo: NotesNode,
        grupos: Sequence[QuestionGroup],
        secciones: Sequence[NoteSection],
        indice: IndiceDelTema | None,
    ) -> dict[str, tuple[NoteSection, ...]]:
        """Los apartados **suyos** de cada pregunta, en orden de lectura.

        Con catálogo manda **el índice** (`apartados_propios_de`), no la clave guardada en cada
        hecho: el reparto de hoy es el que dice dónde va cada hecho, y así la medida del comando y
        la de una corrida dicen lo mismo aunque la base se escribiera con el reparto de antes.

        Sin catálogo (temas con el esquema por epígrafes) se mantiene la lectura de siempre: los
        apartados donde cayeron sus hechos y, si no cayó ninguno, el primero de su epígrafe.
        """
        por_clave = {apartado.key: apartado for apartado in secciones}
        if indice is None:
            hechos_por_firma = _hechos_por_firma(self._repository.facts(nodo.node_id))
            epigrafe_por_defecto = nodo.epigraphs[0][0] if nodo.epigraphs else ""
            return {
                grupo.signature: _apartados_de(
                    grupo, secciones, por_clave, hechos_por_firma, epigrafe_por_defecto
                )
                for grupo in grupos
            }
        por_materia = _secciones_por_materia(secciones)
        return {
            grupo.signature: tuple(
                apartado
                for materia in indice.apartados_propios_de(grupo.signature)
                for apartado in por_materia.get(materia, ())
            )
            for grupo in grupos
        }

    def _comprobables(
        self,
        nodo: NotesNode,
        grupos: Sequence[QuestionGroup],
        secciones: Sequence[NoteSection],
        indice: IndiceDelTema | None = None,
    ) -> list[tuple[QuestionGroup, tuple[NoteSection, ...]]]:
        """Los grupos que se pueden comprobar: los que tienen algún apartado **suyo** con texto.

        Es la misma lista que arma `_paso_comprobacion`, y tiene que serlo: si aquí se contaran
        otras preguntas, la medida del comando y la del informe de una corrida no cuadrarían. Y
        «suyo» es lo que cambia: antes bastaba con que `_apartados_de` encontrara un apartado —y lo
        encontraba siempre, porque sin hechos caía al primero de su epígrafe—, así que se comprobaba
        una pregunta contra el texto de un apartado que no era el suyo.
        """
        anclas = self._anclas_propias(nodo, grupos, secciones, indice)
        comprobables: list[tuple[QuestionGroup, tuple[NoteSection, ...]]] = []
        for grupo in grupos:
            apartados = anclas.get(grupo.signature, ())
            if not apartados or not any(a.body_markdown.strip() for a in apartados):
                continue
            comprobables.append((grupo, apartados))
        return comprobables

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
            antes = len(guardados)
            guardados.extend(self._repository.save_facts(nodo.node_id, resultado.hechos, now=now))
            # Lo que ha traído esta corrida, **no** el total acumulado: `guardados` crece lote a
            # lote
            # y sumar su longitud cada vez daba una cifra que no era la de los hechos nuevos (la
            # corrida de I.1 del 10-oct dijo «3.511 nuevos» cuando el tema ya tenía 3.509 y solo dos
            # preguntas necesitaban hechos). Una cifra que va a un informe se cuenta, no se acumula.
            informe.facts_new += len(guardados) - antes
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
    ) -> tuple[list[NoteSection], IndiceDelTema | None]:
        """El esquema del tema. Se recalcula entero: es determinista y el texto ya escrito se
        conserva.

        Si el tema tiene **catálogo de materias**, el esquema es su **índice aprobado** (paso C del
        plan, revisado por el propietario): un apartado por materia, en el orden en que se
        estudia, y
        los hechos repetidos agrupados en uno solo con la unión de sus preguntas. Si no lo tiene, se
        cae al esquema por epígrafes en trozos de cuarenta, que es lo que había.

        **Lo que no se puede situar no para la corrida**: una pregunta que no casa con ninguna
        materia ni por su enunciado ni por el texto de sus hechos no se mete en un cajón de «otros»
        (eso sería taparla) y tampoco tumba el tema entero. Se cuenta en el informe y va a la
        bandeja del propietario con su motivo, en `_paso_huecos`. Antes esto salía con
        `UnsupportedError` y el tema no se podía redactar **por diez preguntas de dos mil**; el
        propietario se enteraba de que había un problema, pero no de cuáles eran esas diez.

        Volver a calcularlo es lo que permite que un hecho nuevo (de una pregunta clasificada
        después) encuentre su sitio sin tocar los apartados que ya estaban: los que existían
        conservan su texto porque su clave no cambia.

        Y si la clave **sí** cambia (han entrado hechos que mueven los trozos de un epígrafe), lo
        guardado se rehace: dejar los apartados viejos junto a los nuevos sería enseñar dos veces el
        mismo contenido y comprobar contra los dos. Rehacerlo cuesta volver a comprobar, y es lo
        correcto: el tema queda con **un solo** texto por subapartado.
        """
        planes, indice = self._plan_del_tema(nodo, hechos)
        if indice is not None:
            informe.indice = revisar_indice(indice, planes)
        informe.sections = self._informe_apartados(planes)
        if dry_run:
            return list(planes), indice
        guardadas = self._repository.sections(nodo.node_id)
        sobran = {apartado.key for apartado in guardadas} - {plan.key for plan in planes}
        # Y no basta con que la clave siga: si a un apartado le han **salido** hechos, su texto se
        # escribió con otros y dejarlo sería enseñar lo que ya no le toca. Es lo que pasó al
        # repartir
        # por materia (§2.1.1): la clave `udp` no cambió, pero el apartado de UDP hablaba de la
        # cabecera de IPv6, de ARP y de ICMP, y su texto tenía que rehacerse.
        mudos = _apartados_que_pierden_hechos(guardadas, planes)
        if sobran or mudos:
            informe.add_notes(
                f"el esquema se movió: {len(sobran)} apartado(s) que ya no están en el plan y "
                f"{len(mudos)} que han perdido hechos se rehacen, con sus comprobaciones (el texto "
                "se vuelve a escribir). Han perdido hechos: " + ", ".join(sorted(mudos)[:8])
            )
            self._repository.forget_sections(nodo.node_id)
        return list(self._repository.save_sections(nodo.node_id, planes, now=now)), indice

    def _plan_del_tema(
        self, nodo: NotesNode, hechos: Sequence[Hecho]
    ) -> tuple[tuple[NoteSection, ...], IndiceDelTema | None]:
        """El plan de redacción: el índice aprobado si el tema lo tiene, y si no el de epígrafes.

        El índice se parte por el tope de hechos del §2.2.3 (`MAX_HECHOS_POR_APARTADO`): un apartado
        de cuatrocientos hechos no cabe en una llamada —ni la que lo redacta ni la que lo comprueba—
        y se corta en trozos **de la misma materia**, que es lo único que se puede partir sin volver
        a repetir el tema.
        """
        if catalogo(nodo.code) is None:
            return esquema(nodo.epigraphs, hechos), None
        indice = indice_de(
            topic_code=nodo.code,
            topic_title=nodo.title,
            epigraphs=nodo.epigraphs,
            hechos=hechos,
            grupos=self._repository.question_groups(nodo.node_id),
        )
        return plan_de(indice, max_hechos_por_apartado=MAX_HECHOS_POR_APARTADO), indice

    def prever(self, code: str) -> tuple[str, ...]:
        """Qué le haría una corrida al tema, **sin llamar a nadie**: el plan y lo que se rehace.

        Existe para no pagar dos veces por lo mismo sin enterarse. El plan de una corrida se calcula
        **una vez** y no cambia mientras se escribe (se planifica, se escribe con ese plan), pero
        entre dos corridas sí puede cambiar —una pregunta nueva, un hecho que llega, el índice
        redefinido— y entonces el texto de los apartados que se mueven **se tira y se vuelve a
        escribir**: es lo correcto (un texto escrito con unos hechos no vale para otros) y cuesta
        dinero. Verlo antes de lanzar la corrida es lo que permite decidir si toca pagarlo ahora.
        """
        node_id = self._repository.node_id(code)
        if node_id is None:
            raise NotFoundError("tema del programa", code)
        nodo = self._repository.node(node_id)
        if nodo is None:
            raise UnsupportedError(f"«{code}» no es un tema del programa")
        hechos = self._repository.facts(node_id)
        planes, indice = self._plan_del_tema(nodo, hechos)
        guardadas = self._repository.sections(node_id)
        con_texto = {apartado.key for apartado in guardadas if apartado.body_markdown.strip()}
        fuera = sorted({apartado.key for apartado in guardadas} - {plan.key for plan in planes})
        reciclados = sorted(_apartados_que_pierden_hechos(guardadas, planes))
        vacios = [plan.key for plan in planes if plan.key not in con_texto]
        lineas = [
            f"[{code}] lo que haría una corrida, medido sin llamar a nadie:",
            f"    el plan tiene {len(planes)} apartado(s); hay {len(guardadas)} escrito(s)",
        ]
        if fuera:
            lineas.append(
                f"    {len(fuera)} apartado(s) escritos que ya no están en el plan se tiran: "
                + ", ".join(fuera[:8])
            )
        if reciclados:
            lineas.append(
                f"    {len(reciclados)} apartado(s) se vuelven a redactar y a comprobar (≈"
                f"{len(reciclados)} llamada(s) de redacción): " + ", ".join(reciclados[:8])
            )
        if vacios:
            lineas.append(
                f"    {len(vacios)} apartado(s) sin texto: se redactan (≈{len(vacios)} "
                "llamada(s)): " + ", ".join(vacios[:8])
            )
        if not fuera and not reciclados and not vacios:
            lineas.append(
                "    no se rehace nada: los apartados escritos siguen siendo los del plan"
            )
        conservados = sorted(con_texto - set(reciclados) - set(fuera))
        if conservados:
            lineas.append(f"    {len(conservados)} apartado(s) se conservan tal cual")
        lineas.extend(
            self._prevision_de_llamadas(
                nodo,
                hechos,
                planes,
                reciclados=reciclados,
                vacios=vacios,
                indice=indice,
            )
        )
        if indice is not None:
            lineas.extend(revisar_indice(indice, planes).lines())
        return tuple(lineas)

    def _prevision_de_llamadas(
        self,
        nodo: NotesNode,
        hechos: Sequence[Hecho],
        planes: Sequence[NoteSection],
        *,
        reciclados: Sequence[str],
        vacios: Sequence[str],
        indice: IndiceDelTema | None,
    ) -> tuple[str, ...]:
        """Cuántas llamadas y cuánto dinero costaría la corrida, **sin llamar a nadie**.

        Decir qué apartados se conservan y cuáles se rehacen no basta para decidir si un tema cabe
        en el tope de la tanda: falta el número que se paga. Se calcula de lo que ya está en la
        base, que por eso es determinista:

        - **hechos** (paso B): los grupos que no tienen ningún hecho guardado, en lotes de
          `lote_hechos`;
        - **redacción** (paso D): una llamada por apartado sin texto, más una por apartado que se
          recicla porque ha perdido hechos (su texto se escribió con otros);
        - **comprobación** (paso E): los grupos que se pueden comprobar —los situados en el índice,
          que son los que tendrán un apartado con texto—, en lotes de `lote_comprobacion`.

        Y lo que **no** se puede saber antes de escribir: el **bucle de huecos**. Depende de lo que
        conteste el modelo al comprobar, así que se da como cota superior (un añadido por apartado
        y otra pasada de comprobación). Las dos cifras van dichas y no se funden en una: una cota no
        es un resultado.

        Y un caso que se dice en vez de taparse: un tema **sin hechos** no tiene plan. El índice se
        reparte con el texto de los hechos, así que sin ellos no hay nada que repartir y el plan
        sale vacío —medido: I.2 recién estrenado daba «0 apartado(s)»—. La redacción no se puede
        prever hasta que el paso B escriba los hechos, pero la cota de abajo sí: el catálogo, porque
        cada materia del catálogo es al menos un apartado. Se dice cuál de las dos cosas se usa,
        que es lo que impide confundir una previsión con un cero.
        """
        grupos = self._repository.question_groups(nodo.node_id)
        firmas_con_hechos = {firma for hecho in hechos for firma in hecho.source_groups}
        pendientes = sum(1 for grupo in grupos if grupo.signature not in firmas_con_hechos)
        llamadas_hechos = -(-pendientes // self._lote_hechos)
        a_redactar = len(set(vacios) | set(reciclados))
        aviso_plan_vacio = ""
        if not planes and pendientes:
            # Sin hechos no hay plan y la redacción no se puede prever. La cota de abajo es el
            # catálogo: se redacta al menos un apartado por materia (y más si alguna no cabe en su
            # llamada y se parte).
            materias = catalogo(nodo.code) or ()
            a_redactar = len(materias)
            aviso_plan_vacio = (
                f"        (el plan está vacío porque el tema todavía no tiene hechos: la redacción "
                f"no se puede prever hasta que el paso B los escriba. La cota de abajo es el "
                f"catálogo, {len(materias)} materia(s), que es al menos un apartado cada una)"
            )
        sin_materia = len(indice.grupos_sin_materia) if indice is not None else 0
        comprobables = max(0, len(grupos) - sin_materia)
        llamadas_comprobacion = -(-comprobables // self._lote_comprobacion)
        minimo = llamadas_hechos + a_redactar + llamadas_comprobacion
        # El bucle de huecos solo llama por los apartados que tienen huecos, y como mucho son todos.
        apartados_previstos = len(planes) or a_redactar
        maximo = minimo + apartados_previstos + llamadas_comprobacion
        lineas = [
            "    prevision de llamadas (sin llamar a nadie):",
            f"        hechos: {llamadas_hechos} llamada(s) para {pendientes} grupo(s) sin hechos "
            f"(lotes de {self._lote_hechos})",
            f"        redaccion: {a_redactar} llamada(s) para los apartados sin texto "
            f"({len(vacios)} vacio(s) y {len(reciclados)} reciclado(s))",
        ]
        if aviso_plan_vacio:
            lineas.append(aviso_plan_vacio)
        lineas.extend(
            (
                f"        comprobacion: {llamadas_comprobacion} llamada(s) para {comprobables} "
                f"grupo(s) (lotes de {self._lote_comprobacion})",
                f"        bucle de huecos: hasta {apartados_previstos} anadido(s) y "
                f"{llamadas_comprobacion} recomprobacion(es), que dependen de lo que conteste el "
                "modelo",
                f"        total: {minimo} llamada(s) como minimo y {maximo} como maximo",
                f"        coste estimado: {minimo * COSTE_MEDIO_POR_LLAMADA_USD:.2f} $ como minimo "
                f"y {maximo * COSTE_MEDIO_POR_LLAMADA_USD:.2f} $ como maximo "
                f"({COSTE_MEDIO_POR_LLAMADA_USD:.4f} $ por llamada, la media medida)",
            )
        )
        return tuple(lineas)

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
        """Escribe los apartados que no tienen texto. Todos sus hechos van dentro.

        Los trozos de una **misma materia** se escriben **en orden**, y cada uno recibe los
        encabezados que ya han puesto los anteriores. Es lo que evita que las dos mitades de una
        materia partida escriban el mismo índice: en I.1, las Cortes Generales (286 hechos) se
        parten
        en dos llamadas porque no caben en una, y las dos escribieron «2. Composición de las
        Cámaras» y «3. Estatuto de los parlamentarios» —dos apartados con el mismo nombre dentro del
        tema—. Las materias distintas siguen escribiéndose a la vez: lo que se serializa es lo que
        de
        verdad depende de lo anterior.
        """
        material = indexar_material(self._dossier.passages_for_node(nodo.node_id))
        sin_escribir = [apartado for apartado in secciones if not apartado.body_markdown.strip()]
        if not sin_escribir:
            return
        selecciones = {
            apartado.key: seleccionar_material(apartado.facts, material)
            for apartado in sin_escribir
        }
        tablas = {
            apartado.key: es_la_tabla_de_puertos(nodo.code, apartado.key)
            for apartado in sin_escribir
        }
        # Los trozos de la misma materia, en orden de lectura; el trabajo de cada grupo devuelve sus
        # resultados y **no escribe**: la escritura la hace el hilo principal, como las demás.
        grupos: dict[str, list[NoteSection]] = {}
        for apartado in sin_escribir:
            grupos.setdefault(_materia_de(apartado.key), []).append(apartado)
        trabajos: list[Callable[[], list[tuple[NoteSection, RedaccionBatch]] | None]] = [
            partial(self._redactar_trozos, nodo, trozos, selecciones, tablas)
            for trozos in grupos.values()
        ]
        resultados = self._en_paralelo(trabajos)
        anotaciones: dict[str, tuple[tuple[str, ...], str | None]] = {}
        for resultado in resultados:
            if resultado is None:
                informe.failed_batches += 1
                continue
            for apartado, redactado in resultado:
                self._contar(
                    informe,
                    redactado.input_tokens,
                    redactado.output_tokens,
                    redactado.cache_hit_tokens,
                )
                faltan = hechos_integrados(apartado.facts, redactado.markdown)
                motivo = _motivo_de_revision(
                    sin_material=not selecciones[apartado.key],
                    faltan=faltan,
                    hechos=apartado.facts,
                )
                anotaciones[apartado.key] = (faltan, motivo)
                if not dry_run:
                    # El redactor numera los hechos que recibe y a veces cita ese número dentro del
                    # texto: es andamio, no apuntes, y se quita antes de guardar
                    # (`limpiar_andamios`). Y si el apartado es la tabla de puertos, se parte por
                    # familias y se le quitan las notas que solo dicen lo que un puerto no es
                    # (`limpiar_tabla_de_puertos`).
                    cuerpo = _enderezar(
                        nodo.code, apartado.key, limpiar_andamios(redactado.markdown), informe
                    )
                    self._repository.save_section_body(
                        apartado,
                        title=redactado.titulo,
                        body=cuerpo,
                        needs_review_reason=motivo,
                        model=self._model.version,
                        now=now,
                    )
        informe.sections = self._informe_apartados(
            self._repository.sections(nodo.node_id) if not dry_run else secciones,
            anotaciones,
        )

    def _redactar_trozos(
        self,
        nodo: NotesNode,
        trozos: Sequence[NoteSection],
        selecciones: dict[str, tuple[MaterialPassage, ...]],
        tablas: dict[str, bool],
    ) -> list[tuple[NoteSection, RedaccionBatch]] | None:
        """Redacta en orden los trozos de una materia, diciéndole a cada uno lo que ya está puesto.

        Devuelve los resultados (no escribe) o `None` si alguna llamada se agota: entonces el grupo
        entero queda sin escribir y la corrida siguiente lo reintenta. Cortar por el trozo que falla
        dejaría la materia a medias sin decirlo.
        """
        escritos: list[tuple[NoteSection, RedaccionBatch]] = []
        usados: list[str] = []
        for apartado in trozos:
            resultado = self._modelo_o_nada(
                partial(
                    self._model.redactar,
                    replace(apartado, encabezados_ya_usados=tuple(usados)),
                    topic_code=nodo.code,
                    topic_title=nodo.title,
                    material=selecciones[apartado.key],
                    es_tabla_de_puertos=tablas[apartado.key],
                    indicacion=self._indicacion_de(apartado.key),
                )
            )
            if resultado is None:
                return None
            escritos.append((apartado, resultado))
            usados.extend(titulo for _, titulo in encabezados(resultado.markdown))
        return escritos

    def _indicacion_de(self, section_key: str) -> str | None:
        """El aviso del alumno, **solo si este es el apartado del que habla**."""
        if self._indicacion is None or self._indicacion.section_key != section_key:
            return None
        return self._indicacion.text

    def _modelo_o_nada(self, trabajo: Callable[[], T]) -> T | None:
        """Una llamada al modelo sin contar el fallo: lo cuenta quien la agrupa."""
        return self._seguro(trabajo)

    # ------------------------------------------------------------------ paso E: la comprobación

    def _paso_comprobacion(
        self,
        nodo: NotesNode,
        grupos: Sequence[QuestionGroup],
        informe: TopicNotesReport,
        *,
        now: datetime,
        dry_run: bool,
        indice: IndiceDelTema | None = None,
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
        hechos = self._repository.facts(nodo.node_id)
        hechos_por_firma = _hechos_por_firma(hechos)
        comprobables = self._comprobables(nodo, grupos, secciones, indice)
        informe.coverage.groups = len(comprobables)
        # Las preguntas que el índice **no puede situar** no tienen apartado propio, así que no son
        # «comprobables», y sin contarlas la puerta de cobertura se mediría sobre un conjunto del
        # que se han caído justo las que peor están. Se cuentan como no cubiertas —tienen clave
        # utilizable y los apuntes no las contestan porque no hay dónde—; su incidencia va a la
        # bandeja en `_paso_huecos`. El recuento lo hace `_contar_cobertura`, que es el único sitio
        # donde se cuenta: aquí solo se dice cuántas son.
        informe.sin_materia = sum(len(grupo.questions) for grupo in _grupos_sin_materia(indice))
        dudosos_de_la_clave = {
            firma
            for firma, suyos in hechos_por_firma.items()
            if any(hecho.doubtful for hecho in suyos)
        }

        previos = {
            resultado.group_signature: resultado
            for resultado in self._repository.checks(nodo.node_id)
        }
        # Una comprobación guardada vale **para el texto contra el que se verificó**, y para ningún
        # otro. Antes se reutilizaba por la firma del grupo, así que un apartado reescrito seguía
        # con la cita vieja —una frase que ya no está en los apuntes— y la bandeja del propietario
        # la enseñaba como prueba de un conflicto (pasó con I.6: su texto se rehízo después de
        # comprobarlo y las 45 claves sospechosas quedaron con frases que nadie encuentra).
        # Las filas escritas antes de que existiera la huella no la tienen: se vuelven a comprobar,
        # que es lo correcto cuando no se sabe a qué texto corresponden.
        a_recomprobar = {
            grupo.signature
            for grupo, apartados in comprobables
            if (previo := previos.get(grupo.signature)) is None
            or previo.text_sha256 != _huella_de(secciones, apartados)
        }
        resultados = self._comprobar(
            nodo,
            secciones,
            [pareja for pareja in comprobables if pareja[0].signature in a_recomprobar],
            hechos_por_firma,
            informe,
            now=now,
            attempts=1,
        )
        finales = {
            **{firma: previo for firma, previo in previos.items() if firma not in a_recomprobar},
            **resultados,
        }

        huecos = [
            pareja
            for pareja in comprobables
            if _cobertura(finales.get(pareja[0].signature)) is Coverage.HUECO
        ]
        if huecos:
            finales.update(
                self._segunda_vuelta(nodo, huecos, hechos_por_firma, previos, informe, now=now)
            )

        for grupo, _apartados in comprobables:
            resultado = finales.get(grupo.signature)
            if resultado is None:
                continue
            if grupo.signature in dudosos_de_la_clave:
                # El paso B señaló la clave: la pregunta se revisa aunque los apuntes la contesten.
                informe.coverage.incidencias_clave_marcada += 1
        informe.coverage.preguntas = informe.questions
        # La puerta, contada en el sitio único: una vez por pregunta y solo con anclas propias.
        self._contar_cobertura(nodo, grupos, informe, hechos, secciones, indice)
        informe.sections = self._informe_apartados(secciones, {})

    def _comprobar(
        self,
        nodo: NotesNode,
        secciones: Sequence[NoteSection],
        objetivo: Sequence[tuple[QuestionGroup, tuple[NoteSection, ...]]],
        hechos_por_firma: dict[str, list[Hecho]],
        informe: TopicNotesReport,
        *,
        now: datetime,
        attempts: int,
    ) -> dict[str, NotesCheck]:
        """Comprueba un conjunto de grupos, agrupados por el texto que les toca, y guarda el
        resultado.

        El texto que recibe cada pregunta es la **unión de los apartados donde están sus hechos**
        (§2.1.1): con el reparto por materia, una pregunta sobre UDP puede tener un hecho en UDP y
        otro en IPv6, y los dos tienen que poder justificar su respuesta.

        Antes se mandaba el **epígrafe entero** de esos apartados, «que es lo que abarataba la
        llamada» (la parte repetida se cobra a precio de caché). Se dejó de hacer por dos razones
        medidas, no por gusto: el encargo de I.1 —nueve apartados de hasta 150 hechos en su primer
        epígrafe— no cabe en la ventana del modelo (≈80.000 tokens frente a 64.000), y mandar texto
        que no es de la pregunta invita a citar una frase de un apartado que no es el suyo. Lo que
        se
        manda es exactamente lo que dice el §2.1.1, y el ahorro de caché se recupera porque las
        preguntas de un mismo apartado siguen viajando juntas en el mismo lote.
        """
        por_apartados: dict[
            frozenset[str], list[tuple[QuestionGroup, tuple[NoteSection, ...]]]
        ] = {}
        for grupo, apartados in objetivo:
            clave = frozenset(apartado.key for apartado in apartados)
            por_apartados.setdefault(clave, []).append((grupo, apartados))
        resultados: dict[str, NotesCheck] = {}
        for claves, suyos in por_apartados.items():
            apuntes, verificable = _texto_de_apartados(secciones, claves)
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
                # La huella del texto que el modelo acaba de leer: viaja con cada comprobación y es
                # lo que permite saber, en la corrida siguiente, si esta comprobación sigue valiendo
                # o si el apartado se ha reescrito y hay que volver a comprobarlo.
                huella = huella_de_texto(verificable)
                for grupo, apartados in lote:
                    evaluado = evaluar(
                        grupo=grupo,
                        check=respuestas.get(grupo.signature),
                        apuntes=verificable,
                        # El ancla es el **primero** de sus apartados: el enlace del alumno abre
                        # ahí, y los demás se abren desde el mismo índice del tema.
                        section=apartados[0],
                        attempts=attempts,
                        clave_dudosa=any(
                            hecho.doubtful for hecho in hechos_por_firma.get(grupo.signature, ())
                        ),
                    )
                    evaluado = replace(evaluado, text_sha256=huella)
                    resultados[grupo.signature] = evaluado
                    pendientes.extend(_expandir(evaluado, grupo))
                self._repository.save_checks(nodo.node_id, pendientes, now=now)
        return resultados

    def _segunda_vuelta(
        self,
        nodo: NotesNode,
        huecos: Sequence[tuple[QuestionGroup, tuple[NoteSection, ...]]],
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
        for grupo, apartados in huecos:
            # El añadido se escribe en el **primer** apartado de sus hechos: es donde el alumno va a
            # leer el añadido, y los demás siguen enlazados por el índice.
            por_apartado.setdefault(apartados[0].key, []).append(grupo)
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
                body=_enderezar(
                    nodo.code,
                    seccion.key,
                    quitar_encabezado_repetido(
                        seccion.body_markdown, limpiar_andamios(anadido.markdown)
                    ),
                    informe,
                ),
                needs_review_reason=seccion.needs_review_reason,
                model=self._model.version,
                now=now,
                append=True,
            )
            resultados.update(
                self._comprobar(
                    nodo,
                    [*secciones.values(), seccion],
                    [(grupo, (seccion,)) for grupo in grupos],
                    hechos_por_firma,
                    informe,
                    now=now,
                    attempts=2,
                )
            )
        return resultados

    # ------------------------------------------------------------------ el bucle de huecos

    def _paso_huecos(
        self,
        nodo: NotesNode,
        grupos: Sequence[QuestionGroup],
        informe: TopicNotesReport,
        *,
        now: datetime,
        dry_run: bool,
        indice: IndiceDelTema | None = None,
    ) -> None:
        """La última vuelta del paso E: rellenar los huecos y **categorizar el resto**.

        Es el §2.1.4 del objetivo, y son dos trabajos:

        1. **rellenar**: las preguntas que quedaron sin frase en los apuntes son, por definición, un
           hueco de material (el modelo dijo «NO ESTÁ» después de dos vueltas). Se les da una vuelta
           más de añadido —con sus hechos, que el paso B ya escribió— y se vuelve a comprobar. Es la
           tercera y última: más vueltas sobre el mismo hueco no lo rellenan, lo tapan.
        2. **categorizar**: lo que siga sin cubrirse va a la bandeja del propietario con la
           categoría que dice **quién lo arregla** (hueco de material, clave sospechosa, pregunta
           ambigua o
           norma cambiada), el motivo del motor y la frase verificada cuando la hay. Un conflicto de
           letra **siempre** trae su frase: es lo que el propietario necesita para decidir si el que
           está mal es la clave o los apuntes.

        El bucle de huecos se hace sobre las comprobaciones **guardadas**, no sobre las de esta
        corrida: así reanudar el comando tras un corte no pierde lo que ya estaba comprobado.

        Y va también a la bandeja lo que **el índice no puede situar**: una pregunta que no casa con
        ninguna materia ni por su enunciado ni por el texto de sus hechos no tiene apartado donde
        contestarse, así que su incidencia es lo único que se le puede dar al propietario. No se
        mete
        en un cajón de «otros»: se le dice cuál es y por qué.
        """
        if dry_run:
            return
        secciones = {apartado.key: apartado for apartado in self._repository.sections(nodo.node_id)}
        por_firma = {grupo.signature: grupo for grupo in grupos}
        hechos_por_firma = _hechos_por_firma(self._repository.facts(nodo.node_id))
        guardadas = {
            resultado.group_signature: resultado
            for resultado in self._repository.checks(nodo.node_id)
        }
        finales = {firma: resultado for firma, resultado in guardadas.items() if firma in por_firma}

        huecos = {
            firma: resultado
            for firma, resultado in finales.items()
            if resultado.coverage is Coverage.DUDOSA
            and resultado.note is Motivo.SIN_FRASE_EN_LOS_APUNTES
        }
        if huecos:
            self._rellenar_huecos(
                nodo, huecos, por_firma, secciones, hechos_por_firma, informe, now=now
            )
            finales = {
                resultado.group_signature: resultado
                for resultado in self._repository.checks(nodo.node_id)
                if resultado.group_signature in por_firma
            }

        incidencias = tuple(
            IncidenciaDeApuntes(
                question_version_id=resultado.question_version_id,
                group_signature=resultado.group_signature,
                category=categoria,
                reason=resultado.note or Motivo.SIN_FRASE_EN_LOS_APUNTES,
                detail=detalle_de_incidencia(resultado, por_firma.get(resultado.group_signature)),
                section_key=resultado.section_key,
                anchor=resultado.anchor,
                phrase=resultado.quote,
            )
            for resultado in finales.values()
            if (categoria := categoria_de(resultado.coverage, resultado.note)) is not None
        )
        # Y lo que el índice no puede situar, con su motivo propio: no es un hueco de los apuntes
        # (no hay apartado donde escribirlo) ni una clave sospechosa.
        incidencias = (
            *incidencias,
            *_incidencias_sin_materia(
                _grupos_sin_materia(indice), _hechos_sin_materia_por_grupo(indice)
            ),
        )
        informe.coverage.incidencias = len(incidencias)
        for incidencia in incidencias:
            informe.coverage.por_categoria[incidencia.category] = (
                informe.coverage.por_categoria.get(incidencia.category, 0) + 1
            )
        # Las incidencias se escriben siempre, aunque la lista venga vacía: la bandeja tiene que
        # reflejar el tema de hoy, y una incidencia resuelta deja de estar.
        self._repository.save_incidents(nodo.node_id, incidencias, now=now)

    def _rellenar_huecos(
        self,
        nodo: NotesNode,
        huecos: dict[str, NotesCheck],
        por_firma: dict[str, QuestionGroup],
        secciones: dict[str, NoteSection],
        hechos_por_firma: dict[str, list[Hecho]],
        informe: TopicNotesReport,
        *,
        now: datetime,
    ) -> None:
        """Una vuelta más de añadido para los huecos de material, y otra comprobación.

        Se agrupa por apartado porque el añadido se escribe **una vez por apartado**: escribir un
        párrafo por pregunta sería repetir la misma explicación diez veces.
        """
        por_apartado: dict[str, list[QuestionGroup]] = {}
        for resultado in huecos.values():
            grupo = por_firma.get(resultado.group_signature)
            if grupo is None:
                continue
            clave = resultado.section_key or next(iter(secciones), "")
            por_apartado.setdefault(clave, []).append(grupo)
        for clave, grupos in por_apartado.items():
            seccion = secciones.get(clave)
            if seccion is None:
                continue
            faltantes = [
                hecho for grupo in grupos for hecho in hechos_por_firma.get(grupo.signature, ())
            ]
            anadido = self._llamada(
                partial(self._model.anadir, seccion, grupos, faltantes), informe
            )
            if anadido is None:
                continue
            self._contar(
                informe, anadido.input_tokens, anadido.output_tokens, anadido.cache_hit_tokens
            )
            informe.coverage.huecos_rellenados += 1
            seccion = self._repository.save_section_body(
                seccion,
                title=None,
                body=_enderezar(
                    nodo.code,
                    seccion.key,
                    quitar_encabezado_repetido(
                        seccion.body_markdown, limpiar_andamios(anadido.markdown)
                    ),
                    informe,
                ),
                needs_review_reason=seccion.needs_review_reason,
                model=self._model.version,
                now=now,
                append=True,
            )
            secciones[clave] = seccion
            self._comprobar(
                nodo,
                list(self._repository.sections(nodo.node_id)),
                [(grupo, (seccion,)) for grupo in grupos],
                hechos_por_firma,
                informe,
                now=now,
                attempts=VUELTAS_CON_HUECOS,
            )

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
            # El tope de tiempo de la corrida se mira **antes** de cada intento: cuando se agota, la
            # excepción sube sin que la trague el `except` de abajo, que es para los fallos de red.
            if self._agotado():
                raise _TiempoDeLaCorridaAgotadoError
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


def _materia_de(clave: str) -> str:
    """La materia de un apartado, sin el número del trozo: `cortes-generales-2` →
    `cortes-generales`.

    Es cómo se sabe qué apartados son trozos de la misma materia y tienen que escribirse en orden:
    el
    plan los numera así (`plan_de`) cuando una materia no cabe en una llamada.
    """
    return re.sub(r"-\d+$", "", clave)


def _secciones_por_materia(
    secciones: Sequence[NoteSection],
) -> dict[str, tuple[NoteSection, ...]]:
    """Los apartados guardados de cada materia, con sus trozos y en orden de lectura.

    Una materia que no cabe en una llamada se parte en trozos numerados (`udp-1`, `udp-2`): el
    índice la nombra por su clave (`udp`) y en la base hay dos apartados. Sin esta traducción, la
    pregunta de una materia partida se quedaría sin apartado propio —y contaría como no cubierta—
    por un detalle de cómo se guarda el texto, no por dónde está su material.

    Cada apartado se indexa por su clave **y** por la de su materia, y las dos hacen falta: hay
    claves de materia que **acaban en cifras** (`ley-59-2003`), así que quitarle a la clave de un
    apartado el sufijo de trozo no siempre devuelve la clave de su materia. Así la pregunta
    encuentra su apartado tanto si la materia va entera como si va partida.
    """
    por_materia: dict[str, list[NoteSection]] = {}
    for apartado in secciones:
        por_materia.setdefault(apartado.key, []).append(apartado)
        por_materia.setdefault(_materia_de(apartado.key), []).append(apartado)
    return {
        materia: tuple(sorted(suyos, key=lambda apartado: apartado.position))
        for materia, suyos in por_materia.items()
    }


def _grupos_sin_materia(indice: IndiceDelTema | None) -> tuple[QuestionGroup, ...]:
    """Las preguntas que el índice **no puede situar**: ni por su enunciado ni por sus hechos."""
    return () if indice is None else indice.grupos_sin_materia


def _hechos_sin_materia_por_grupo(
    indice: IndiceDelTema | None,
) -> dict[str, tuple[Hecho, ...]]:
    """Los hechos que **no se han sentado** en ningún apartado, por la pregunta de la que salen.

    Es la mitad del arreglo de `repartir_hechos` que el propietario tiene que poder ver: el hecho
    no se sienta en un apartado ajeno, pero **tampoco se pierde**, y su sitio es la bandeja con el
    mismo motivo que su pregunta. Un hecho puede salir de varias preguntas y se enseña en todas.
    """
    por_firma: dict[str, list[Hecho]] = {}
    for hecho in () if indice is None else indice.sin_materia:
        for firma in hecho.source_groups:
            por_firma.setdefault(firma, []).append(hecho)
    return {firma: tuple(suyos) for firma, suyos in por_firma.items()}


def _incidencias_sin_materia(
    grupos: Sequence[QuestionGroup],
    hechos_por_grupo: Mapping[str, tuple[Hecho, ...]] | None = None,
) -> tuple[IncidenciaDeApuntes, ...]:
    """Las incidencias de las preguntas que no caben en ninguna materia del tema.

    Una fila **por pregunta** y no por grupo: la bandeja del propietario tiene una fila por pregunta
    (es su clave natural) y una pregunta repetida en dos bancos tiene que poder despacharse dos
    veces. El detalle lleva el enunciado y el motivo, que es lo que él necesita para decidir: sin
    apartado no hay frase de los apuntes que enseñar, y sin frase no se puede inventar una.

    Y lleva sus **hechos sin apartado**: son los que la red de seguridad sentaba dentro del tema
    antes de este arreglo, y el propietario tiene que verlos con su texto para decidir si la
    pregunta está mal clasificada o si falta un apartado en el tema.
    """
    sin_apartado = hechos_por_grupo or {}
    return tuple(
        IncidenciaDeApuntes(
            question_version_id=pregunta.question_version_id,
            group_signature=grupo.signature,
            category=CategoriaIncidencia.PREGUNTA_AMBIGUA,
            reason=Motivo.SIN_MATERIA_EN_EL_INDICE,
            detail=(
                f"{TEXTO_SIN_MATERIA}\n"
                f"pregunta: {grupo.representative.stem.strip()[:300]}\n"
                f"clave: {', '.join(grupo.correct_keys) or 'sin clave'} "
                f"({grupo.key_status.value})"
                + "".join(
                    f"\nhecho sin apartado: {hecho.text.strip()[:300]}"
                    for hecho in sin_apartado.get(grupo.signature, ())
                )
            ),
        )
        for grupo in grupos
        for pregunta in grupo.questions
    )


def _apartados_que_pierden_hechos(
    guardadas: Sequence[NoteSection], planes: Sequence[NoteSection]
) -> frozenset[str]:
    """Las claves de los apartados a los que les han **salido** hechos desde que se escribieron.

    Es la condición para rehacer su texto y no solo repartir sus hechos: un texto escrito con unos
    hechos y leído con otros es un texto que explica lo que ya no le toca. Añadir hechos **no**
    cuenta
    aquí: eso lo arregla el añadido del paso E y la marca `hechos nuevos sin integrar`, sin volver a
    pagar la redacción del tema entero (es el caso de las preguntas que se clasifican después).
    """
    del_plan = {plan.key: {hecho.fact_id for hecho in plan.facts} for plan in planes}
    return frozenset(
        apartado.key
        for apartado in guardadas
        if {hecho.fact_id for hecho in apartado.facts} - del_plan.get(apartado.key, set())
    )


def _es_la_tabla_del_catalogo(topic_code: str, clave: str) -> bool:
    """¿Este apartado es la tabla única del tema? Lo dice el catálogo, no el título del apartado.

    Es la marca `tabla_unica` del índice: un tema puede tener apartados con tablas, pero solo uno es
    «la tabla de puertos» y solo ese lleva las instrucciones de familias.
    """
    materias = catalogo(topic_code)
    return any(materia.key == clave and materia.tabla_unica for materia in (materias or ()))


def _enderezar(topic_code: str, clave: str, cuerpo: str, informe: TopicNotesReport) -> str:
    """La última mano al texto de un apartado antes de guardarlo.

    Hace cuatro cosas, y las cuatro son reparaciones de forma que mide `revisar_apuntes`:

    - un encabezado que repite otro del mismo apartado es un apartado dentro de otro: se quita el
      encabezado y se queda su texto (`sin_encabezados_repetidos`);
    - una tabla cuya cabecera deja una columna sin nombre no se puede leer: se le pone el nombre que
      le falta (`nombrar_columnas_sin_titulo`), que es lo que I.1 tenía en cuatro tablas;
    - una tubería dentro de un `código` en una celda de tabla parte la fila en una celda de más y la
      tabla deja de leerse: se escapa (`escapar_tuberias_en_celdas`), que es lo que le pasó a II.4
      con la tabla de operadores del shell, cuyo operador `` | `` es él mismo una tubería;
    - y, si el apartado es la tabla de puertos, se parte por familias y se le quitan las notas que
      solo dicen lo que un puerto **no** es (`limpiar_tabla_de_puertos`).

    Se cuenta lo que se ha hecho (`notas_de_puertos_retiradas` y `confusiones_de_puertos`) porque un
    arreglo que no se puede medir no se puede revisar.
    """
    cuerpo = nombrar_columnas_sin_titulo(
        escapar_tuberias_en_celdas(sin_encabezados_repetidos(cuerpo))
    )
    if not es_la_tabla_de_puertos(topic_code, clave):
        return cuerpo
    limpieza = limpiar_tabla_de_puertos(cuerpo)
    informe.notas_de_puertos_retiradas += limpieza.notas_retiradas
    informe.confusiones_de_puertos = len(limpieza.confusiones)
    return limpieza.texto


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


def _apartados_de(
    grupo: QuestionGroup,
    secciones: Sequence[NoteSection],
    por_clave: dict[str, NoteSection],
    hechos_por_firma: dict[str, list[Hecho]],
    epigrafe_por_defecto: str,
) -> tuple[NoteSection, ...]:
    """En qué apartados caen los hechos de un grupo, en orden de lectura.

    **Varios**, y esa es la diferencia con el reparto por pregunta: como cada hecho va al apartado
    de lo que afirma (§2.1.1), los hechos de una misma pregunta pueden estar repartidos —el de UDP
    en su apartado y el de la cabecera de IPv6 en el de IPv6—, y su ancla son todos. El enlace del
    alumno abre el primero; la comprobación recibe la unión de todos.

    Si no tiene ningún hecho con apartado, cae al primero de su epígrafe, que es lo que había.
    """
    suyos = hechos_por_firma.get(grupo.signature, ())
    vistos: list[NoteSection] = []
    for hecho in suyos:
        apartado = por_clave.get(hecho.section_key)
        if apartado is not None and apartado not in vistos:
            vistos.append(apartado)
    if vistos:
        return tuple(sorted(vistos, key=lambda apartado: apartado.position))
    epigrafe = grupo.epigraph_code or next(
        (hecho.epigraph_code for hecho in suyos), epigrafe_por_defecto
    )
    por_defecto = next(
        (apartado for apartado in secciones if apartado.epigraph_code == epigrafe),
        secciones[0] if secciones else None,
    )
    return () if por_defecto is None else (por_defecto,)


def _huella_de(secciones: Sequence[NoteSection], apartados: Sequence[NoteSection]) -> str:
    """La huella del texto con el que se comprueba un grupo: la unión de los apartados de sus
    hechos.

    Es la **misma lectura** que hace `_comprobar` (`_texto_de_apartados`), y tiene que serlo: si
    aquí se calculara sobre otro texto, la huella no diría nada sobre lo que se verificó, y una
    comprobación se daría por buena —o se repetiría— por un motivo falso.
    """
    return huella_de_texto(
        _texto_de_apartados(secciones, {apartado.key for apartado in apartados})[1]
    )


def _texto_de_apartados(
    secciones: Sequence[NoteSection],
    claves: Collection[str],
    *,
    presupuesto: int = PRESUPUESTO_CARACTERES_COMPROBACION,
) -> tuple[str, str]:
    """El texto de unos apartados para comprobar, en dos formas: la del modelo y la verificable.

    La primera lleva delante el anclaje y el título de cada apartado para que el modelo sepa dónde
    está; la segunda es el mismo texto **sin esos encabezados**, y es contra la que se verifica la
    frase copiada. La diferencia importa: un encabezado lo escribimos nosotros, no es una frase de
    los apuntes, y no puede justificar una respuesta. Lo que el modelo lee y lo que se comprueba
    salen de la misma lectura, así que no pueden divergir.

    El texto es la **unión de los apartados de la pregunta** (§2.1.1) y, mientras quepa en el
    presupuesto, **el resto de sus epígrafes**. Las dos partes importan y por eso están juntas:

    - la unión es lo que pide el objetivo, y es lo que hace que el encargo quepa en la ventana del
      modelo: el primer epígrafe de I.1 son nueve apartados de hasta 150 hechos (≈300.000
      caracteres) y no entra en modo alguno;
    - el resto del epígrafe es lo que **abarataba** la llamada (la parte repetida se cobra a precio
      de caché) y lo que permite justificar una respuesta con una frase de un apartado hermano: el
      hecho va al apartado de lo que afirma, y una pregunta puede estar contestada en el apartado de
      al lado sin dejar de ser su epígrafe. Medido en I.6, quitarlo se llevó la cobertura del 63,6 %
      a menos de la mitad.

    El corte es por tamaño y por orden de lectura, así que es determinista: el mismo tema da el
    texto y la misma huella.
    """
    propios = [a for a in secciones if a.key in claves and a.body_markdown.strip()]
    epigrafes = {apartado.epigraph_code for apartado in propios}
    elegidos = {apartado.key: apartado for apartado in propios}
    total = sum(len(apartado.body_markdown) for apartado in propios)
    for apartado in secciones:
        if apartado.key in elegidos or apartado.epigraph_code not in epigrafes:
            continue
        if not apartado.body_markdown.strip():
            continue
        largura = len(apartado.body_markdown)
        if total + largura > presupuesto:
            continue
        elegidos[apartado.key] = apartado
        total += largura
    ordenados = sorted(elegidos.values(), key=lambda apartado: apartado.position)
    partes = [
        (
            f"## {apartado.anchor} · {apartado.title}\n\n{apartado.body_markdown}",
            apartado.body_markdown,
        )
        for apartado in ordenados
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
            text_sha256=resultado.text_sha256,
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
