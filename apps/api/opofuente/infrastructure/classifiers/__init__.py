"""Motores de clasificación disponibles (S04).

Hoy hay uno: el determinista. El puerto `ClassifierPort` permite añadir un clasificador LLM opcional
más adelante (S09) sin tocar el servicio; hasta entonces, la capacidad `llm` sigue declarada
`disabled` y **no** existe ningún adaptador que llame a un modelo.
"""

from __future__ import annotations

from opofuente.infrastructure.classifiers.deterministic import (
    ENGINE_NAME,
    ENGINE_VERSION,
    DeterministicClassifier,
)

__all__ = ["ENGINE_NAME", "ENGINE_VERSION", "DeterministicClassifier"]
