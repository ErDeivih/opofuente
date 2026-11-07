"""Estado de las fuentes oficiales de los perfiles frente a su manifiesto (DEBT-028).

La puerta 17 no puede exigir que las fuentes descargadas sigan siendo idénticas: el BOE y el BOCYL
cambian en origen y un ``sha256`` de septiembre no se puede reproducir en noviembre. Pero tampoco
debe fallar siempre. Este comprobador separa los dos casos:

- **falta la fuente** (código 1): no se puede saber nada; hay que ejecutar
  ``scripts/fetch-sources.ps1``. Es el único caso que bloquea.
- **la fuente cambió** (código 2): está, pero no es la del manifiesto. Se avisa con el detalle y la
  puerta 17 omite la verificación de los fixtures de perfiles con ese motivo escrito; el resto de la
  puerta (temario común y convocatorias C1) sigue siendo bloqueante.
- **todo coincide** (código 0): la puerta puede ejecutar ``build_profile_fixtures --check``
  completo.

Uso:
    uv run python -m opofuente.tools.check_profile_sources
    uv run python -m opofuente.tools.check_profile_sources --json
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from opofuente.config import project_root
from opofuente.tools.build_profile_fixtures import Source, load_manifest

SourceState = Literal["ok", "missing", "drifted"]


@dataclass(frozen=True, slots=True)
class SourceStatus:
    id: str
    local_path: str
    state: SourceState
    expected_sha256: str
    actual_sha256: str | None = None


def evaluate_sources(sources: Iterable[Source]) -> tuple[tuple[SourceStatus, ...], int]:
    """Devuelve el estado de cada fuente y el código de salida de la comprobación."""
    estados: list[SourceStatus] = []
    for source in sources:
        ruta: Path = source.local_path
        if not ruta.is_file():
            estados.append(
                SourceStatus(
                    id=source.id,
                    local_path=str(ruta),
                    state="missing",
                    expected_sha256=source.sha256,
                )
            )
            continue
        digest = hashlib.sha256(ruta.read_bytes()).hexdigest()
        estados.append(
            SourceStatus(
                id=source.id,
                local_path=str(ruta),
                state="ok" if digest == source.sha256 else "drifted",
                expected_sha256=source.sha256,
                actual_sha256=digest,
            )
        )

    if any(estado.state == "missing" for estado in estados):
        return tuple(estados), 1
    if any(estado.state == "drifted" for estado in estados):
        return tuple(estados), 2
    return tuple(estados), 0


def _resumen(estados: tuple[SourceStatus, ...]) -> str:
    faltan = [estado for estado in estados if estado.state == "missing"]
    desviadas = [estado for estado in estados if estado.state == "drifted"]
    if faltan:
        nombres = ", ".join(estado.local_path for estado in faltan)
        return (
            "faltan fuentes oficiales de los perfiles: "
            f"{nombres}. Ejecuta scripts/fetch-sources.ps1"
        )
    if desviadas:
        nombres = ", ".join(
            f"{estado.id} ({estado.expected_sha256[:12]}… != {(estado.actual_sha256 or '?')[:12]}…)"
            for estado in desviadas
        )
        return (
            f"{len(desviadas)} fuente(s) de perfiles desviadas respecto al manifiesto: {nombres}. "
            "No se puede verificar build_profile_fixtures contra ellas; la puerta 17 omite esa "
            "verificación con este motivo (DEBT-028) y sigue con el temario común y las C1."
        )
    return f"{len(estados)} fuentes de perfiles coinciden con el manifiesto."


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = project_root()
    fuentes = load_manifest(root)
    estados, codigo = evaluate_sources(fuentes)

    if "--json" in args:
        print(
            json.dumps(
                {
                    "exit_code": codigo,
                    "summary": _resumen(estados),
                    "sources": [
                        {
                            "id": estado.id,
                            "state": estado.state,
                            "path": estado.local_path,
                            "expected_sha256": estado.expected_sha256,
                            "actual_sha256": estado.actual_sha256,
                        }
                        for estado in estados
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for estado in estados:
            if estado.state == "missing":
                print(f"  FALTA   {estado.id}: {estado.local_path}")
            elif estado.state == "drifted":
                print(
                    f"  DESVIADA {estado.id}: {estado.expected_sha256[:12]}… != "
                    f"{estado.actual_sha256[:12] if estado.actual_sha256 else '?'}…"
                )
            else:
                print(f"  ok      {estado.id}")
        print(_resumen(estados))

    if codigo == 1:
        print(
            "Bloqueante: sin las fuentes no se puede verificar ningún fixture de perfil.",
            file=sys.stderr,
        )
    elif codigo == 2:
        print(
            "No bloqueante: la puerta 17 omite la verificación de perfiles con este motivo "
            "(DEBT-028); temario común y convocatorias C1 sí se comprueban.",
            file=sys.stderr,
        )
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
