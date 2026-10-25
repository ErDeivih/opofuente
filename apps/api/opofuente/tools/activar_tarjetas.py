"""Pasa a `active` las tarjetas generadas que cumplen, con su comprobación por programa.

**Qué resuelve** (fase «lo que ve el alumno», punto 1): **5.274 tarjetas generadas siguen en
`draft` y el alumno solo ve 9**. **No se activan a ciegas**: se comprueban cuatro cosas, **las
cuatro por programa**, y las que no pasan **se quedan en `draft` con su motivo escrito**.

**Las cuatro comprobaciones**:

1. **la respuesta aparece literalmente en el hecho**, normalizando mayúsculas, acentos y espacios —
   una tarjeta cuyo reverso no está en el hecho es una afirmación sin fuente;
2. **la respuesta tiene 25 palabras o menos** — una tarjeta con un párrafo no se repasa, se lee;
3. **la pregunta no contiene la respuesta** — si la contiene, no pregunta nada;
4. **no hay otra tarjeta del mismo tema con la misma pregunta** (frente normalizado) — dos
   iguales son la misma tarjeta repetida, y repasar dos veces lo mismo no es repasar.

**El tope de nuevas al día** existe para que el primer día no salgan cinco mil: **se activan
como mucho `--limite` por ejecución** (20 por defecto, o `OPOFUENTE_TARJETAS_NUEVAS_AL_DIA`),
y **el resto siguen en `draft`, listas para la siguiente**. **No se pierde ninguna.**

**Uso**:

```
uv run python -m opofuente.tools.activar_tarjetas              # cuenta, sin escribir
uv run python -m opofuente.tools.activar_tarjetas --aplicar    # escribe
uv run python -m opofuente.tools.activar_tarjetas --limite 0 --aplicar   # sin tope
```
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sqlite3
import unicodedata
from collections.abc import Sequence

import httpx

from opofuente.config import get_settings

#: El tope de tarjetas nuevas que se activan en una ejecución: **el drip diario**.
_TOPE_POR_DEFECTO = 20

#: Las palabras que puede tener el reverso como mucho.
_MAXIMO_DE_PALABRAS = 25


def _normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y con los espacios colapsados: compara lo que se lee, no el byte."""
    sin_tildes = unicodedata.normalize("NFD", texto)
    plano = "".join(caracter for caracter in sin_tildes if unicodedata.category(caracter) != "Mn")
    return re.sub(r"\s+", " ", plano.lower()).strip()


def _motivo(*, frente: str, reverso: str, hecho: str, repetida: bool) -> str | None:
    """El motivo por el que la tarjeta **no** pasa, o `None` si pasa.

    **Se devuelve el primero que falla**: es lo que el panel tiene que enseñar, y una lista de
    cuatro motivos en una columna de texto no se lee.
    """
    if repetida:
        return "hay otra tarjeta con la misma pregunta en el tema"
    if len(reverso.split()) > _MAXIMO_DE_PALABRAS:
        return f"la respuesta tiene más de {_MAXIMO_DE_PALABRAS} palabras"
    if _normalizar(reverso) not in _normalizar(hecho):
        return "la respuesta no aparece en el hecho"
    if _normalizar(reverso) in _normalizar(frente):
        return "la pregunta contiene la respuesta"
    return None


def _candidatas(conexion: sqlite3.Connection) -> list[tuple[str, str, str, str, str]]:
    """Las generadas en borrador con su hecho: `(id, frente, reverso, hecho, tema)`."""
    return list(
        conexion.execute(
            """
            select c.id, c.front, c.back, tf.text, tf.curriculum_node_id
            from cards as c
            join topic_facts as tf on tf.id = c.topic_fact_id
            where c.status = 'draft' and c.origin = 'generated'
            order by c.created_at, c.id
            """
        )
    )


def activar(*, aplicar: bool, limite: int) -> int:
    conexion = sqlite3.connect(str(get_settings().data_paths.database), timeout=60)
    try:
        filas = _candidatas(conexion)
        print(f"  tarjetas generadas en borrador: {len(filas)}")

        # **Los frentes ya activos, por tema**: con eso se decide «hay otra igual en el tema».
        repetidas: set[tuple[str, str]] = set()
        for tema, frente in conexion.execute(
            "select tf.curriculum_node_id, c.front from cards as c "
            "join topic_facts as tf on tf.id = c.topic_fact_id "
            "where c.status = 'active'"
        ):
            repetidas.add((str(tema), _normalizar(str(frente))))

        validas: list[str] = []
        motivos: list[tuple[str, str]] = []
        for identificador, frente, reverso, hecho, tema in filas:
            clave = (str(tema), _normalizar(str(frente)))
            motivo = _motivo(
                frente=str(frente),
                reverso=str(reverso),
                hecho=str(hecho),
                repetida=clave in repetidas,
            )
            if motivo is None:
                validas.append(str(identificador))
                repetidas.add(clave)
            else:
                motivos.append((str(identificador), motivo))

        print(f"  cumplen las cuatro: {len(validas)}")
        print(f"  se quedan en borrador con su motivo: {len(motivos)}")
        if not aplicar:
            print("  (sin --aplicar no se escribe nada)")
            return 0

        activadas = validas if limite <= 0 else validas[:limite]
        for identificador in activadas:
            conexion.execute(
                "update cards set status = 'active', draft_reason = null, "
                "updated_at = datetime('now') where id = ?",
                (identificador,),
            )
        for identificador, motivo in motivos:
            conexion.execute(
                "update cards set draft_reason = ? where id = ?",
                (motivo, identificador),
            )
        conexion.commit()
        print(f"  activadas ahora: {len(activadas)}")
        if len(validas) > len(activadas):
            print(f"  cumplen y esperan a otra tanda: {len(validas) - len(activadas)}")
        return 0
    finally:
        conexion.close()


#: El contraste: **cincuenta tarjetas al azar**, contestadas por el modelo **con el hecho delante**.
_MUESTRA_DE_CONTRASTE = 50

#: Por debajo de esta coincidencia **se para y se apunta**: la tanda no vale.
_MINIMO_DE_COINCIDENCIA = 90

_SISTEMA_CONTRASTE = (
    "Te doy un hecho de unos apuntes y una pregunta sacada de él. Contesta **solo con la "
    "respuesta**, en tres palabras o menos, sin explicar nada. Si el hecho no la contiene, "
    'contesta "no consta". Devuelve JSON: {"respuestas": ["...", "..."]} en el mismo orden.'
)


def _pedir_respuestas(clave: str, lote: Sequence[tuple[str, str]]) -> list[str]:
    """Una llamada al modelo con el hecho y la pregunta de cada tarjeta del lote."""
    preguntas = [
        {"n": indice, "hecho": hecho, "pregunta": frente}
        for indice, (frente, hecho) in enumerate(lote, start=1)
    ]
    respuesta = httpx.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {clave}"},
        json={
            "model": "deepseek-chat",
            "temperature": 0,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SISTEMA_CONTRASTE},
                {"role": "user", "content": json.dumps(preguntas, ensure_ascii=False)},
            ],
        },
        timeout=180.0,
    )
    respuesta.raise_for_status()
    contenido = respuesta.json()["choices"][0]["message"]["content"]
    return [str(item) for item in json.loads(contenido).get("respuestas", [])]


def contraste(clave: str, *, muestra: int = _MUESTRA_DE_CONTRASTE) -> int:
    """**Cincuenta tarjetas al azar, contestadas a ciegas con el hecho delante.**

    **Por qué existe**: una tarjeta activa se le sirve al alumno como verdad. **Que su reverso esté
    literalmente en el hecho no basta** si el hecho no contesta a la pregunta: eso solo lo dice
    alguien que la conteste sin ver la respuesta. **Por debajo del 90 % se para y se apunta.**
    """
    conexion = sqlite3.connect(str(get_settings().data_paths.database), timeout=60)
    try:
        filas = _candidatas(conexion)
        validas = [
            (str(frente), str(reverso), str(hecho))
            for _, frente, reverso, hecho, _ in filas
            if _motivo(frente=str(frente), reverso=str(reverso), hecho=str(hecho), repetida=False)
            is None
        ]
        if not validas:
            print("  no hay tarjetas que contrastar")
            return 0
        # **Semilla fija a propósito**: la muestra tiene que poder repetirse para comparar dos
        # ejecuciones. No es un sorteo criptográfico.
        random.Random(20261025).shuffle(validas)  # noqa: S311 - muestra reproducible
        elegidas = validas[:muestra]
        aciertos = 0
        for inicio in range(0, len(elegidas), 10):
            lote = elegidas[inicio : inicio + 10]
            respuestas = _pedir_respuestas(clave, [(frente, hecho) for frente, _, hecho in lote])
            for (frente, reverso, _), respuesta in zip(lote, respuestas, strict=False):
                esperada = _normalizar(reverso)
                dada = _normalizar(respuesta)
                if esperada and (esperada in dada or dada in esperada):
                    aciertos += 1
                else:
                    print(
                        f"    no coincide: «{frente}» -> esperaba «{reverso}», dijo «{respuesta}»"
                    )
        porcentaje = 100 * aciertos / len(elegidas)
        print(f"  coinciden {aciertos} de {len(elegidas)} ({porcentaje:.0f} %)")
        if porcentaje < _MINIMO_DE_COINCIDENCIA:
            print("  POR DEBAJO DEL 90 %: se para y no se activa nada")
            return 1
        print("  por encima del 90 %: se puede activar")
        return 0
    finally:
        conexion.close()


def informe() -> int:
    """Cuántas quedan activas **por tema**, y cuántas en borrador con cada motivo."""
    conexion = sqlite3.connect(str(get_settings().data_paths.database), timeout=60)
    try:
        print("  activas por tema:")
        for tema, cuantas in conexion.execute(
            "select tf.curriculum_node_id, count(*) from cards as c "
            "join topic_facts as tf on tf.id = c.topic_fact_id "
            "where c.status = 'active' group by tf.curriculum_node_id "
            "order by count(*) desc"
        ):
            print(f"    {str(tema)[:8]}: {cuantas}")
        print("  motivos para seguir en borrador:")
        for motivo, cuantas in conexion.execute(
            "select coalesce(draft_reason, '(sin comprobar)'), count(*) from cards "
            "where status = 'draft' group by 1 order by count(*) desc"
        ):
            print(f"    {motivo}: {cuantas}")
        return 0
    finally:
        conexion.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="escribe de verdad")
    parser.add_argument(
        "--limite",
        type=int,
        default=int(os.environ.get("OPOFUENTE_TARJETAS_NUEVAS_AL_DIA", _TOPE_POR_DEFECTO)),
        help="cuántas se activan como mucho en esta ejecución (0 = todas)",
    )
    parser.add_argument("--informe", action="store_true", help="cuenta lo que hay, por tema")
    parser.add_argument(
        "--contraste",
        type=int,
        default=0,
        help="contrasta esa muestra con el modelo antes de activar",
    )
    args = parser.parse_args(argv)
    if args.informe:
        return informe()
    if args.contraste:
        clave = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not clave:
            print("  sin DEEPSEEK_API_KEY no hay contraste: se para sin gastar")
            return 2
        return contraste(clave, muestra=args.contraste)
    return activar(aplicar=args.aplicar, limite=args.limite)


if __name__ == "__main__":
    raise SystemExit(main())
