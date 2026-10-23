"""Las tarjetas de repaso que salen de un hecho, con el modelo (M3 de la fase 3).

**Que hace.** Lee los hechos que aun no tienen tarjeta, los manda por tandas al modelo y **se
queda solo
con las que se pueden comprobar**: la respuesta tiene que estar **literalmente** en el texto
del hecho.
Una tarjeta cuya respuesta no esta en el hecho no se guarda: **repasar con ella es estudiar
algo que el
material no dice**.

**Por que la comprobacion es literal y no «parecida».** El modelo tiende a completar con lo que
sabe,
y lo que sabe no es lo que el temario dice. **Si la respuesta no aparece en el hecho, se
descarta y se
dice por que** —no se reescribe a mano, que seria taparlo—.

**Por defecto no llama a nadie y no escribe nada**: dice cuantas tarjetas saldrian y cuanto
costaria.
Con `--de-verdad` llama al modelo; con `--guardar` las escribe.

**La clave se lee de `DEEPSEEK_API_KEY`** y no se escribe en ningun fichero.

Uso:
    uv run python -m opofuente.tools.tarjetas --limite 40
    uv run python -m opofuente.tools.tarjetas --limite 40 --de-verdad --guardar

Codigos de salida: 0 bien · 2 sin clave.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from opofuente.config import get_settings

#: Cuantos hechos van en cada llamada. **Doce** porque cada uno pide dos frases y con mas la
#: respuesta se corta: el mismo problema que se midio en los supuestos.
POR_TANDA = 12

#: El tope de salida, dicho. Sin el, el servidor aplica el suyo y **el JSON llega truncado**.
MAX_TOKENS = 4000

SISTEMA = (
    "Eres un profesor que prepara tarjetas de repaso. Para cada HECHO que se te da, escribe una "
    "tarjeta con una pregunta corta (front) y su respuesta (back). Reglas: la respuesta tiene que "
    "estar EN EL TEXTO del hecho, copiada tal cual, sin inventar ni completar con lo que sepas; "
    "la pregunta no puede contener la respuesta; y si el hecho no da para una respuesta corta y "
    "comprobable (una cifra, un plazo, un articulo, un nombre, una sigla), devuelve back vacio. "
    'Devuelve JSON: {"tarjetas": [{"id": "...", "front": "...", "back": "..."}]}'
)


@dataclass(frozen=True, slots=True)
class Hecho:
    """Un hecho del temario, con su identificador y su texto."""

    id: str
    texto: str


@dataclass(frozen=True, slots=True)
class Tarjeta:
    """Una tarjeta propuesta, ya comprobada."""

    hecho_id: str
    front: str
    back: str


def _hechos(limite: int, por_tema: int = 60) -> tuple[Hecho, ...]:
    """Los hechos que aun no tienen tarjeta, **sin los dudosos**.

    **Un hecho dudoso no se convierte en tarjeta**: se repasa con lo que el temario afirma, y
    un hecho
    marcado como dudoso es justo el que hay que mirar antes de memorizarlo.
    """
    base = sqlite3.connect(get_settings().data_paths.database)
    try:
        filas = base.execute(
            # **Con un tope por tema**: repartir las tarjetas importa mas que acumularlas, y sin
            # este tope la corrida llenaba un tema entero (doscientas noventa tarjetas en uno)
            # antes de pasar al siguiente. **Cincuenta por tema es lo que pide el hito**; se piden
            # sesenta para que el descarte no deje ningun tema corto.
            "select id, text from ("
            "  select f.id, f.text, row_number() over ("
            "    partition by f.curriculum_node_id order by f.id) as orden "
            "  from topic_facts f "
            "  where coalesce(f.doubtful, 0) = 0 "
            "  and length(trim(f.text)) > 0 "
            "  and not exists (select 1 from cards c where c.topic_fact_id = f.id)"
            ") where orden <= ? order by id limit ?",
            (por_tema, limite),
        ).fetchall()
    finally:
        base.close()
    return tuple(Hecho(id=str(f[0]), texto=str(f[1])) for f in filas)


def _normaliza(texto: str) -> str:
    """El texto en una forma comparable: sin acentos de mas, sin espacios de mas, en minusculas."""
    recortado = re.sub(r"\s+", " ", texto).strip().lower()
    return recortado


def comprobar(hecho: str, respuesta: str) -> str | None:
    """El motivo por el que una tarjeta no vale, o `None` si vale.

    **La respuesta tiene que estar literalmente en el hecho**, comparando en la forma normalizada
    (espacios y mayusculas no cuentan, el texto si). **Una respuesta vacia tampoco vale**: es
    el modelo
    diciendo que ese hecho no da para tarjeta, y eso se respeta.
    """
    if not respuesta.strip():
        return "el hecho no da para una respuesta corta y comprobable"
    if _normaliza(respuesta) not in _normaliza(hecho):
        return f"la respuesta no esta literalmente en el hecho: «{respuesta[:60]}»"
    return None


def _prompt(lote: Sequence[Hecho]) -> str:
    lineas = [f"[{hecho.id}] {hecho.texto}" for hecho in lote]
    return "HECHOS:\n" + "\n".join(lineas)


def pedir(clave: str, lote: Sequence[Hecho], *, modelo: str) -> list[dict[str, object]]:
    """Una llamada al modelo. Devuelve lo que diga, **sin juzgarlo**."""
    respuesta = httpx.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {clave}"},
        json={
            "model": modelo,
            "temperature": 0,
            "max_tokens": MAX_TOKENS,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SISTEMA},
                {"role": "user", "content": _prompt(lote)},
            ],
        },
        timeout=180.0,
    )
    respuesta.raise_for_status()
    sobre = respuesta.json()
    contenido = sobre["choices"][0]["message"]["content"]
    return list(json.loads(contenido).get("tarjetas", []))


def _guardar(tarjetas: Sequence[Tarjeta], *, modelo: str) -> int:
    """Escribe las tarjetas aceptadas. **El anverso es unico**, asi que pasarla dos veces no
    duplica."""
    base = sqlite3.connect(get_settings().data_paths.database)
    ahora = datetime.now(UTC).isoformat()
    guardadas = 0
    try:
        for tarjeta in tarjetas:
            try:
                base.execute(
                    "insert into cards (id, topic_fact_id, front, back, citation, origin, status, "
                    "ease, interval_days, repetitions, due_at, created_at, updated_at) "
                    "values (?, ?, ?, ?, ?, 'generated', 'draft', 2.5, 0, 0, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        tarjeta.hecho_id,
                        tarjeta.front,
                        tarjeta.back,
                        f"hecho de {tarjeta.hecho_id[:8]} · {modelo}",
                        ahora,
                        ahora,
                        ahora,
                    ),
                )
                guardadas += 1
            except sqlite3.IntegrityError:
                # **Una tarjeta repetida no es un fallo**: el anverso es unico y el
                # hecho ya la tenia.
                continue
        base.commit()
    finally:
        base.close()
    return guardadas


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limite", type=int, default=40, help="cuantos hechos mirar")
    parser.add_argument(
        "--por-tema", type=int, default=60, help="cuantas tarjetas como mucho por tema"
    )
    parser.add_argument(
        "--de-verdad", action="store_true", help="llama al modelo (gasta); sin esto no gasta nada"
    )
    parser.add_argument(
        "--guardar", action="store_true", help="escribe las aceptadas (con --de-verdad)"
    )
    args = parser.parse_args(argv)

    hechos = _hechos(args.limite, args.por_tema)
    print(f"hechos sin tarjeta: {len(hechos)}")
    if not hechos:
        return 0

    if not args.de_verdad:
        tandas = (len(hechos) + POR_TANDA - 1) // POR_TANDA
        print(f"tandas previstas: {tandas} (de {POR_TANDA})")
        print("sin --de-verdad no se llama a nadie y no se escribe nada")
        return 0

    clave = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not clave:
        print("sin DEEPSEEK_API_KEY no hay tarjetas: se para sin gastar")
        return 2

    ajustes = get_settings()
    modelo = ajustes.llm_model or "deepseek-chat"
    aceptadas: list[Tarjeta] = []
    rechazadas: list[tuple[str, str]] = []
    for inicio in range(0, len(hechos), POR_TANDA):
        tanda = hechos[inicio : inicio + POR_TANDA]
        por_id = {hecho.id: hecho for hecho in tanda}
        try:
            propuestas = pedir(clave, tanda, modelo=modelo)
        except (httpx.HTTPError, ValueError, KeyError) as error:
            print(f"  tanda {inicio // POR_TANDA + 1}: la llamada fallo: {type(error).__name__}")
            continue
        for propuesta in propuestas:
            ident = str(propuesta.get("id", "")).strip()
            hecho = por_id.get(ident)
            if hecho is None:
                continue
            front = str(propuesta.get("front", "")).strip()
            back = str(propuesta.get("back", "")).strip()
            motivo = comprobar(hecho.texto, back)
            if motivo is not None:
                rechazadas.append((ident, motivo))
                continue
            if not front:
                rechazadas.append((ident, "la pregunta esta vacia"))
                continue
            aceptadas.append(Tarjeta(hecho_id=ident, front=front, back=back))

    print(f"aceptadas: {len(aceptadas)}")
    print(f"rechazadas: {len(rechazadas)}")
    for ident, motivo in rechazadas[:5]:
        print(f"  {ident[:8]}: {motivo}")
    if args.guardar:
        print(f"guardadas: {_guardar(aceptadas, modelo=modelo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
