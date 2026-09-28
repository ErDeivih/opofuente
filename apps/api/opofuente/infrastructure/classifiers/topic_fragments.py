"""Motor de temas por fragmento: coloca cada trozo del texto en su nodo del programa.

Por que existe, y que cambia respecto del motor determinista:

El motor determinista compara el texto **entero** con el titulo de cada nodo y solo propone
cuando
encuentra sus palabras dentro del documento. Medido sobre el material real del propietario, eso
deja
**21 de los 33 temas sin ninguna cobertura**: un temario de 30 paginas no repite el titulo
oficial de
los temas que trata.

Este motor hace lo otro: trocea el documento, coloca **cada trozo** en su nodo (la regla de
dominio
`topic_matching`, medida en 86,7 % de acierto de bloque contra los titulos oficiales) y propone
los
nodos que de verdad pesan en el documento. La confianza es **la parte del documento que habla de
ese
tema**: un documento cuyos trozos son al 80 % del tema IV.3 propone IV.3 con 0,80.

Reglas que respeta, y son las del proyecto:

- propone, no decide: no escribe nada ni toca la base de datos;
- hasta **tres nodos** por documento, como pide `04 §7`;
- por debajo de una parte minima del documento **no propone nada**: un tema que aparece una vez
no es
  un tema del documento;
- eje `topic`, que **no es critico**: la banda alta puede aplicarselo de forma provisional,
visible y
  reversible. Nunca toca autoridad ni derechos.
"""

from __future__ import annotations

from collections.abc import Sequence

from opofuente.domain.classification import (
    Alternative,
    Axis,
    ClassificationSubject,
    ProfileCandidate,
    Proposal,
)
from opofuente.domain.topic_matching import EmparejadorDeTemas, NodoPrograma, fragmentar

ENGINE_NAME = "temas-por-fragmento"
ENGINE_VERSION = "1"

#: `04 §7`: proponer hasta tres nodos con explicacion.
MAX_NODOS = 3

#: Parte minima del documento para proponer un nodo. Por debajo, el tema se menciona, no se trata.
MIN_PARTE = 0.10

#: Longitud del ejemplo que se cita como evidencia: una referencia breve y citable, nunca el
#: documento entero (lo pide `domain/classification.py`).
LARGO_EVIDENCIA = 90


class FragmentTopicClassifier:
    """Propone los temas del programa que de verdad aparecen en el texto, trozo a trozo."""

    name = ENGINE_NAME
    version = ENGINE_VERSION

    def propose(self, subject: ClassificationSubject) -> Sequence[Proposal]:
        """Propuestas de tema del sujeto. Sin texto o sin programa, ninguna."""
        if not subject.text.strip() or not subject.profiles:
            return ()
        trozos = fragmentar(subject.text)
        if not trozos:
            return ()
        propuestas: list[Proposal] = []
        for perfil in subject.profiles:
            propuestas.extend(self._del_perfil(subject, perfil, trozos))
        return tuple(propuestas)

    def _del_perfil(
        self, subject: ClassificationSubject, perfil: ProfileCandidate, trozos: Sequence[str]
    ) -> list[Proposal]:
        """Propuestas de un perfil: los nodos que de verdad pesan en el texto."""
        nodos = [
            NodoPrograma(node_id=nodo.node_id, path=nodo.path, title=nodo.title)
            for nodo in perfil.topics
            if nodo.title.strip()
        ]
        if len(nodos) < 2:
            # Con un solo nodo no hay nada que elegir: proponerlo seria decir que todo el material
            # es de ese tema, y eso no lo dice el texto.
            return []
        emparejador = EmparejadorDeTemas(nodos)
        pesos: dict[str, float] = {}
        ejemplos: dict[str, str] = {}
        for trozo in trozos:
            coincidencia = emparejador.emparejar(trozo)
            if coincidencia is None:
                continue
            ruta = coincidencia.nodo.path
            pesos[ruta] = pesos.get(ruta, 0.0) + coincidencia.puntuacion
            ejemplos.setdefault(ruta, " ".join(trozo.split())[:LARGO_EVIDENCIA])
        total = sum(pesos.values())
        if total <= 0.0:
            return []
        ordenados = sorted(pesos.items(), key=lambda par: (-par[1], par[0]))[:MAX_NODOS]
        return [
            self._propuesta(subject, ruta, peso / total, ordenados, ejemplos, len(trozos))
            for ruta, peso in ordenados
            if peso / total >= MIN_PARTE
        ]

    def _propuesta(
        self,
        subject: ClassificationSubject,
        ruta: str,
        parte: float,
        ordenados: list[tuple[str, float]],
        ejemplos: dict[str, str],
        cuantos: int,
    ) -> Proposal:
        """Una propuesta de tema, con sus alternativas y su evidencia."""
        suma = sum(peso for _, peso in ordenados) or 1.0
        return Proposal(
            id="",
            subject_type=subject.subject_type,
            subject_id=subject.subject_id,
            axis=Axis.TOPIC,
            proposed_value=ruta,
            confidence=round(parte, 4),
            engine_name=self.name,
            engine_version=self.version,
            alternatives=tuple(
                Alternative(value=otra, confidence=round(peso / suma, 4))
                for otra, peso in ordenados
                if otra != ruta
            ),
            evidence=(
                f"{parte:.0%} de {cuantos} fragmentos del documento; "
                f"p. ej. «{ejemplos.get(ruta, '')}»",
            ),
        )
