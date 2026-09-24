"""Pruebas del OCR: la sonda, la lectura y los comandos que se construyen.

Dos niveles, y la diferencia importa (no son lo mismo):

- **con un runner inyectado** (lo que corre siempre en la puerta): se comprueba la decisión de si
  hay OCR, el comando exacto que se ejecuta, el reparto por páginas y los avisos. Determinista y
  sin depender de que este equipo tenga Tesseract instalado;
- **con el binario de verdad**: se comprueba que Tesseract **lee**. Se busca el Tesseract del equipo
  (PATH o su ruta típica de Windows) y **se salta** si no lo hay o si no tiene el modelo de español.
  Un salto no es una verificación: en un equipo sin Tesseract, la prueba de que el OCR funciona
  es la medida a mano de `docs/reviews/OCR-escaneos-2026-09.md`.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pymupdf
import pytest

from opofuente.config import Settings
from opofuente.infrastructure.ocr import (
    PAGE_SEPARATOR,
    CompletedRun,
    OcrFailedError,
    PdfOcrText,
    TesseractOcr,
    default_tessdata,
    tesseract_from_settings,
)
from opofuente_testing.synthetic_documents import build_scanned_pdf, build_scanned_pdf_with_text

VERSION_REAL = "tesseract v5.4.0.20240606\n leptonica-1.82.0\n"
CABECERA_IDIOMAS = 'List of available languages in "tessdata" (3):\n'


class GuionOCR:
    """Runner de mentira con guion: anota lo que se le pide y responde lo que dice el guion.

    El OCR de verdad es un proceso externo; lo que se comprueba aquí no es que Tesseract lea, sino
    **que la aplicación pide lo correcto y hace lo correcto con lo que le devuelven**.
    """

    def __init__(
        self,
        *,
        texto: str = "texto reconocido por el doble",
        por_pagina: tuple[str, ...] = (),
        version: str = VERSION_REAL,
        idiomas: tuple[str, ...] = ("eng", "osd", "spa"),
        codigo_version: int = 0,
        codigo_ocr: int = 0,
        error_ocr: str = "",
    ) -> None:
        self.texto = texto
        self.por_pagina = por_pagina
        self.version = version
        self.idiomas = idiomas
        self.codigo_version = codigo_version
        self.codigo_ocr = codigo_ocr
        self.error_ocr = error_ocr
        self.peticiones: list[list[str]] = []
        self._ocr_llamadas = 0

    def __call__(self, command: Sequence[str], timeout: float) -> CompletedRun:
        self.peticiones.append(list(command))
        if "--version" in command:
            return CompletedRun(returncode=self.codigo_version, stdout=self.version)
        if "--list-langs" in command:
            listado = CABECERA_IDIOMAS.replace("(3)", f"({len(self.idiomas)})")
            return CompletedRun(returncode=0, stdout=listado + "\n".join(self.idiomas) + "\n")
        if self.codigo_ocr != 0:
            return CompletedRun(
                returncode=self.codigo_ocr, stdout="", stderr=f"Error: {self.error_ocr}"
            )
        pagina = self._ocr_llamadas
        self._ocr_llamadas += 1
        if self.por_pagina:
            return CompletedRun(returncode=0, stdout=self.por_pagina[pagina])
        return CompletedRun(returncode=0, stdout=self.texto)

    @property
    def lecturas(self) -> list[list[str]]:
        """Solo los comandos que OCRizan algo (los de la sonda quedan fuera)."""
        return [
            peticion
            for peticion in self.peticiones
            if "--version" not in peticion and "--list-langs" not in peticion
        ]


def _binario_falso(tmp_path: Path) -> Path:
    """Un fichero que existe: la sonda comprueba la ruta antes de ejecutar nada."""
    binario = tmp_path / "tesseract-falso.exe"
    binario.write_bytes(b"esto no es un binario, es una ruta que existe")
    return binario


def _adaptador(tmp_path: Path, doble: GuionOCR, *, languages: str = "spa") -> TesseractOcr:
    return TesseractOcr(binary=_binario_falso(tmp_path), languages=languages, runner=doble)


# --- La sonda: no se declara OCR por tener una ruta escrita -----------------------------------


def test_la_sonda_no_ejecuta_nada_si_la_ruta_no_existe(tmp_path: Path) -> None:
    doble = GuionOCR()
    adaptador = TesseractOcr(binary=tmp_path / "no-existe.exe", runner=doble)

    sonda = adaptador.probe()

    assert sonda.available is False
    assert "no-existe.exe" in sonda.detail
    assert doble.peticiones == [], "sin binario no se ejecuta nada: ni para preguntar la versión"


def test_la_sonda_dice_la_version_y_los_idiomas_cuando_el_binario_responde(tmp_path: Path) -> None:
    doble = GuionOCR()

    sonda = _adaptador(tmp_path, doble).probe()

    assert sonda.available is True
    assert sonda.version == "tesseract v5.4.0.20240606"
    assert sonda.languages == ("eng", "osd", "spa")
    assert "spa" in sonda.detail
    assert [peticion[-1] for peticion in doble.peticiones] == ["--version", "--list-langs"]


def test_la_sonda_falla_si_falta_el_idioma_pedido(tmp_path: Path) -> None:
    """Un Tesseract sin español responde a `--version` y luego no sabe leer español."""
    sonda = _adaptador(tmp_path, GuionOCR(idiomas=("eng", "osd"))).probe()

    assert sonda.available is False
    assert "spa" in sonda.detail
    assert sonda.version == "tesseract v5.4.0.20240606", "la versión se conserva en el motivo"


def test_la_sonda_falla_si_el_binario_responde_con_error(tmp_path: Path) -> None:
    sonda = _adaptador(tmp_path, GuionOCR(codigo_version=1)).probe()

    assert sonda.available is False
    assert "código 1" in sonda.detail


def test_la_sonda_memoriza_el_resultado_y_se_puede_refrescar(tmp_path: Path) -> None:
    """El informe de capacidades y el extractor preguntan: el binario no se ejecuta dos veces."""
    doble = GuionOCR()
    adaptador = _adaptador(tmp_path, doble)

    adaptador.probe()
    adaptador.probe()
    assert len(doble.peticiones) == 2, "una vez la versión y otra los idiomas"

    adaptador.probe(refresh=True)
    assert len(doble.peticiones) == 4, "refrescar vuelve a preguntar de verdad"


# --- La lectura: el comando y el resultado -----------------------------------------------------


def test_el_ocr_de_una_imagen_usa_los_idiomas_configurados_y_pasa_el_tessdata(
    tmp_path: Path,
) -> None:
    doble = GuionOCR(texto="Tema 4. Medidas cautelares")
    adaptador = TesseractOcr(
        binary=_binario_falso(tmp_path),
        languages="spa+eng",
        tessdata=tmp_path / "tessdata",
        runner=doble,
    )

    texto = adaptador.text_of_image(tmp_path / "escaneo.png")

    assert texto == "Tema 4. Medidas cautelares"
    peticion = doble.lecturas[-1]
    assert peticion[1:3] == ["--tessdata-dir", str(tmp_path / "tessdata")]
    assert peticion[-3:] == ["stdout", "-l", "spa+eng"]
    assert peticion[3].endswith("escaneo.png")


def test_el_ocr_no_se_ejecuta_si_la_sonda_no_pasa(tmp_path: Path) -> None:
    doble = GuionOCR(idiomas=("eng",))
    adaptador = _adaptador(tmp_path, doble)

    with pytest.raises(OcrFailedError) as fallo:
        adaptador.text_of_image(tmp_path / "escaneo.png")

    assert "spa" in str(fallo.value)
    assert doble.lecturas == [], "sin idioma no se OCRiza nada"


def test_el_ocr_declara_el_fallo_con_su_codigo_en_lugar_de_devolver_texto_vacio(
    tmp_path: Path,
) -> None:
    adaptador = _adaptador(tmp_path, GuionOCR(codigo_ocr=1, error_ocr="Image too large"))

    with pytest.raises(OcrFailedError) as fallo:
        adaptador.text_of_image(tmp_path / "escaneo.png")

    assert "código 1" in str(fallo.value)
    assert "Image too large" in str(fallo.value)


def test_el_ocr_de_un_pdf_ocr_iza_pagina_a_pagina_y_cuenta_las_que_hay(tmp_path: Path) -> None:
    archivo = build_scanned_pdf(tmp_path / "escaneado.pdf", pages=3)
    doble = GuionOCR(por_pagina=("uno", "dos", "tres"))
    adaptador = _adaptador(tmp_path, doble)

    reconocido = adaptador.text_of_pdf(archivo, max_pages=2)

    assert reconocido.pages == ("uno", "dos")
    assert reconocido.read_pages == 2
    assert reconocido.page_count == 3, "el total del documento se conserva aunque no se lea entero"
    assert len(doble.lecturas) == 2, "una llamada por página: una ilegible no arrastra al resto"


def test_los_tramos_de_pagina_cuadran_con_el_texto_unido() -> None:
    reconocido = PdfOcrText(pages=("primera", "segunda", ""), page_count=3)

    assert reconocido.text == f"primera{PAGE_SEPARATOR}segunda{PAGE_SEPARATOR}"
    tramos = reconocido.page_spans
    assert tramos[0] == (0, len("primera"))
    assert reconocido.text[tramos[1][0] : tramos[1][1]] == "segunda"


def test_describe_dice_la_version_el_idioma_y_la_resolucion(tmp_path: Path) -> None:
    frase = _adaptador(tmp_path, GuionOCR()).describe()

    assert "tesseract v5.4.0.20240606" in frase
    assert "spa" in frase
    assert "300 ppp" in frase


# --- La configuración: un solo sitio construye el adaptador -------------------------------------


def test_sin_ruta_configurada_no_hay_adaptador() -> None:
    assert tesseract_from_settings(Settings(tesseract_path=None, _env_file=None)) is None


def test_la_configuracion_se_convierte_en_un_adaptador_con_lo_que_declara(tmp_path: Path) -> None:
    adaptador = tesseract_from_settings(
        Settings(
            tesseract_path=tmp_path / "tesseract.exe",
            tesseract_languages="spa+eng",
            tesseract_tessdata=tmp_path / "tessdata",
            _env_file=None,
        )
    )

    assert adaptador is not None
    assert adaptador.binary == tmp_path / "tesseract.exe"
    assert adaptador.languages == "spa+eng"
    assert adaptador.dpi == 300


# --- Con el binario de verdad: que Tesseract lee ------------------------------------------------

#: Dónde instala Tesseract para Windows su propio instalador. Se mira también el `PATH`, porque en
#: Linux y macOS es lo normal.
RUTA_TIPICA_WINDOWS = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


def _tesseract_del_equipo() -> TesseractOcr | None:
    """El Tesseract de **este** equipo, si lo hay. No se pide por configuración de la aplicación.

    Se busca a propósito al margen de `OPOFUENTE_*`: esas variables las neutraliza el `conftest`
    (la suite no depende de la máquina, y eso no se toca) y colar una puerta trasera solo para esta
    prueba sería peor que buscarlo. Los modelos se resuelven como en la aplicación
    (`default_tessdata`): el `tessdata` del perfil del usuario si está, si no el del binario.
    """
    import shutil

    encontrado = shutil.which("tesseract")
    binario = Path(encontrado) if encontrado else RUTA_TIPICA_WINDOWS
    if not binario.is_file():
        return None
    return TesseractOcr(
        binary=binario,
        languages="spa",
        tessdata=default_tessdata(),
    )


@pytest.fixture(scope="module")
def ocr_real() -> TesseractOcr:
    """El adaptador real de este equipo, o un salto con su motivo (nunca una prueba fingida)."""
    adaptador = _tesseract_del_equipo()
    if adaptador is None:
        pytest.skip(
            "no hay un Tesseract instalado en este equipo (ni en el PATH ni en su ruta típica)"
        )
    sonda = adaptador.probe()
    if not sonda.available:
        pytest.skip(f"el Tesseract de este equipo no sirve para leer español: {sonda.detail}")
    return adaptador


def test_el_ocr_real_lee_una_imagen_sintetica_con_texto(
    ocr_real: TesseractOcr, tmp_path: Path
) -> None:
    documento = pymupdf.open()
    pagina = documento.new_page()
    pagina.insert_text((72, 90), "Medidas cautelares", fontsize=22)
    imagen = tmp_path / "rotulo.png"
    pagina.get_pixmap(dpi=200).save(imagen)
    documento.close()

    texto = ocr_real.text_of_image(imagen)

    assert "cautelares" in texto.lower()


def test_el_ocr_real_lee_un_pdf_escaneado_sin_capa_de_texto(
    ocr_real: TesseractOcr, tmp_path: Path
) -> None:
    archivo = build_scanned_pdf_with_text(
        tmp_path / "escaneado.pdf",
        pages=2,
        lines=("Medidas cautelares", "Silencio administrativo"),
    )

    reconocido = ocr_real.text_of_pdf(archivo, max_pages=2)

    assert reconocido.read_pages == 2
    assert "cautelares" in reconocido.pages[0].lower()
    assert "administrativo" in reconocido.pages[1].lower()
