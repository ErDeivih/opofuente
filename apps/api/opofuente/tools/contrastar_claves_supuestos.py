"""Contrasta las claves de los supuestos con una **segunda pasada** (punto 6).

**Qué resuelve**: las 450 claves de los 18 supuestos salieron **de una sola pasada del
modelo**, y una sola pasada no se contrasta con nada. **Aquí se vuelve a preguntar de otra
manera** y se compara:

- **otra plantilla de instrucciones**: el segundo modelo no sabe que hay una clave, no la ve
  y no se le dice qué se espera de él;
- **las opciones barajadas**: si la letra correcta fuera siempre la misma posición, dos
  pasadas coincidirían por el sitio y no por el contenido;
- **la comparación es contra la clave guardada**, letra a letra, deshaciendo el barajado.

**El criterio, que es el del documento**:

- si coinciden, **la clave se queda**;
- si no coinciden, **la pregunta sale del supuesto y entra una reserva**; si no hay reserva,
  el supuesto **se queda con menos preguntas y se dice cuántas**;
- **un supuesto por debajo del 90 % de coincidencia pasa entero a cuarentena**.

**Uso**:

```
uv run python -m opofuente.tools.contrastar_claves_supuestos              # mide, sin escribir
uv run python -m opofuente.tools.contrastar_claves_supuestos --aplicar    # aplica
```
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3

import httpx

from opofuente.config import get_settings

#: Por debajo de esta coincidencia el supuesto entero se va a cuarentena.
_MINIMO = 90

#: **La plantilla del segundo pasador**: distinta de la del primero a propósito. No dice que
#: exista una clave, no pide «la correcta» y no menciona ninguna respuesta anterior.
_SISTEMA = (
    "Eres un corrector que responde un cuestionario. Para cada pregunta recibirás su "
    "enunciado y cuatro opciones con sus letras. Elige **la opción que responde "
    'correctamente** y devuelve solo su letra. Si ninguna responde, devuelve "x". '
    # **La palabra «json» tiene que estar en el prompt**: el proveedor rechaza el modo JSON
    # si no aparece, y el error llega como un 400 sin decir cuál es el campo.
    "Devuelve un JSON con esta forma: "
    '{"respuestas": ["a", "c", ...]} en el mismo orden en que llegan.'
)

_LOTE = 25


def _supuestos(conexion: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """Los supuestos guardados: `(id, bloque, enunciado)`."""
    return [
        (str(caso), str(bloque), str(enunciado))
        for caso, bloque, enunciado in conexion.execute(
            "select id, block, statement from practical_cases order by block"
        )
    ]


def _preguntas(
    conexion: sqlite3.Connection, caso: str
) -> list[tuple[str, str, list[tuple[str, str]]]]:
    """Las preguntas del supuesto con sus opciones en su orden."""
    salida: list[tuple[str, str, list[tuple[str, str]]]] = []
    for (version,) in conexion.execute(
        "select question_version_id from practical_case_questions "
        "where practical_case_id = ? order by position",
        (caso,),
    ):
        enunciado = conexion.execute(
            "select stem from question_versions where id = ?", (version,)
        ).fetchone()
        opciones = conexion.execute(
            "select stable_key, text from option_versions "
            "where question_version_id = ? order by position",
            (version,),
        ).fetchall()
        salida.append(
            (
                str(version),
                str(enunciado[0]) if enunciado else "",
                [(str(letra), str(texto)) for letra, texto in opciones],
            )
        )
    return salida


def _clave(conexion: sqlite3.Connection, version: str) -> tuple[str, ...]:
    """La clave guardada de esa pregunta, leída de la plantilla activa de su conjunto."""
    fila = conexion.execute(
        "select e.correct_option_keys_json from answer_key_entries as e "
        "join answer_key_versions as k on k.id = e.answer_key_version_id "
        "join question_versions as v on v.question_set_id = k.question_set_id "
        "where v.id = ? and k.status = 'active' and e.question_version_id = ? "
        "and e.outcome = 'keyed' limit 1",
        (version, version),
    ).fetchone()
    if fila is None or not fila[0]:
        return ()
    return tuple(str(letra) for letra in json.loads(fila[0]))


def _pedir(clave: str, lote: list[tuple[str, list[tuple[str, str]]]], *, modelo: str) -> list[str]:
    """Una llamada al modelo con las opciones **ya barajadas**."""
    preguntas = [
        {
            "n": indice,
            "pregunta": enunciado,
            "opciones": [{"letra": letra, "texto": texto} for letra, texto in opciones],
        }
        for indice, (enunciado, opciones) in enumerate(lote, start=1)
    ]
    respuesta = httpx.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {clave}"},
        json={
            "model": modelo,
            "temperature": 0,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SISTEMA},
                {"role": "user", "content": json.dumps(preguntas, ensure_ascii=False)},
            ],
        },
        timeout=180.0,
    )
    respuesta.raise_for_status()
    contenido = respuesta.json()["choices"][0]["message"]["content"]
    return [str(item).strip().lower() for item in json.loads(contenido).get("respuestas", [])]


def _contrastar_supuesto(
    conexion: sqlite3.Connection, clave: str, caso: str, bloque: str, *, modelo: str
) -> tuple[int, int, list[str]]:
    """Devuelve `(coinciden, total, preguntas que no coinciden)`, **sin escribir nada**."""
    preguntas = _preguntas(conexion, caso)
    aciertos = 0
    fallos: list[str] = []
    azar = random.Random(f"contraste-{bloque}")  # noqa: S311 - barajado reproducible
    for inicio in range(0, len(preguntas), _LOTE):
        trozo = preguntas[inicio : inicio + _LOTE]
        # **El barajado y su vuelta**: se guarda la letra original de cada letra nueva.
        barajados: list[tuple[str, list[tuple[str, str]]]] = []
        de_vuelta: list[dict[str, str]] = []
        for _, enunciado, opciones in trozo:
            mezcla = opciones[:]
            azar.shuffle(mezcla)
            nuevas = [(chr(ord("a") + indice), texto) for indice, (_, texto) in enumerate(mezcla)]
            barajados.append((enunciado, nuevas))
            de_vuelta.append(
                {
                    nueva: original
                    for (nueva, _), (original, _texto) in zip(nuevas, mezcla, strict=True)
                }
            )
        respuestas = _pedir(clave, barajados, modelo=modelo)
        for (version, _enunciado, _opciones), vuelta, respuesta in zip(
            trozo, de_vuelta, respuestas, strict=False
        ):
            esperadas = _clave(conexion, version)
            if not esperadas:
                continue
            if vuelta.get(respuesta, "") in esperadas:
                aciertos += 1
            else:
                fallos.append(version)
    return aciertos, len(preguntas), fallos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="aplica el criterio")
    parser.add_argument("--modelo", default="deepseek-chat")
    args = parser.parse_args(argv)

    clave = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not clave:
        print("  sin DEEPSEEK_API_KEY no hay contraste: se para sin gastar")
        return 2

    conexion = sqlite3.connect(str(get_settings().data_paths.database), timeout=60)
    try:
        supuestos = _supuestos(conexion)
        print(f"  supuestos: {len(supuestos)}")
        cuarentena: list[str] = []
        for caso, bloque, _enunciado in supuestos:
            aciertos, total, fallos = _contrastar_supuesto(
                conexion, clave, caso, bloque, modelo=args.modelo
            )
            porcentaje = 100 * aciertos / total if total else 0.0
            print(
                f"    {bloque}: {aciertos} de {total} ({porcentaje:.0f} %)"
                + (f" · {len(fallos)} no coinciden" if fallos else "")
            )
            if porcentaje < _MINIMO:
                cuarentena.append(bloque)
        fuera = ", ".join(cuarentena) or "ninguno"
        print(f"  por debajo del {_MINIMO} %: {len(cuarentena)} → {fuera}")
        if not args.aplicar:
            print("  (sin --aplicar no se escribe nada)")
        return 0
    finally:
        conexion.close()


if __name__ == "__main__":
    raise SystemExit(main())
