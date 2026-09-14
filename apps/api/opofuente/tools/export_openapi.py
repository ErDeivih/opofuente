"""Exporta el esquema OpenAPI del backend.

OpenAPI es la fuente de verdad del contrato (02_ARCHITECTURE §2). Este comando escribe
`packages/contracts/openapi.json`; los tipos TypeScript se derivan de ese fichero con
`npm run contracts:generate`. Con `--check` no escribe: falla si el fichero no coincide.

Uso:
    uv run python -m opofuente.tools.export_openapi [ruta] [--check]
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

from opofuente.config import Settings, project_root
from opofuente.main import create_app

DEFAULT_TARGET = ("packages", "contracts", "openapi.json")


def render_schema() -> str:
    """Esquema OpenAPI serializado de forma determinista."""
    app = create_app(Settings())
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check_only = "--check" in args
    positional = [argument for argument in args if not argument.startswith("--")]
    target = Path(positional[0]) if positional else project_root().joinpath(*DEFAULT_TARGET)

    rendered = render_schema()

    if check_only:
        if not target.is_file():
            print(f"Falta el contrato generado: {target.name}", file=sys.stderr)
            return 1
        if target.read_text(encoding="utf-8") != rendered:
            print(
                f"El contrato en {target.name} no coincide con la API. "
                "Ejecuta: uv run python -m opofuente.tools.export_openapi",
                file=sys.stderr,
            )
            return 1
        print(f"Contrato sincronizado: {target.name}")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n": el contrato es un artefacto y debe ser byte a byte igual en Windows y en
    # Linux, para que `contracts:check` y el diff de git no dependan de la plataforma.
    target.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"OpenAPI escrito en {target.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
