"""OCR local con Tesseract (04_INGESTION §5): texto de una imagen o de una página escaneada.

Decisiones, y por qué:

- **nunca se mezcla con el texto nativo**: el resultado es una representación de tipo `ocr`, con su
  extractor y su versión. Un PDF con capa de texto no pasa por aquí;
- **se llama al binario por ruta absoluta, sin `shell`**, con tiempo máximo: un Tesseract colgado no
  puede dejar un lote a medias. La ruta y los idiomas los decide la configuración, no el código;
- **el idioma se declara**: se OCRiza con los idiomas configurados (por defecto `spa`) y el
  resultado dice cuáles se usaron. Un OCR en inglés sobre texto español produce basura plausible,
  que es lo peor que se puede guardar sin decirlo;
- **la sonda es una prueba de verdad**: `probe()` ejecuta `tesseract --version` y `--list-langs`; la
  capacidad de la aplicación no se declara operativa por tener una ruta escrita en la configuración
  (16_TRACEABILITY §4: prohibido el botón falso);
- **las páginas se renderizan a 300 ppp** con PyMuPDF antes de OCRizar: a menos resolución, las
  letras pequeñas de un escaneo se pierden, y se midió que a 300 ppp el texto se lee correctamente.
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from opofuente.config import Settings

logger = logging.getLogger(__name__)

#: Resolución de renderizado antes de OCRizar. Es una decisión medida: a 300 ppp el texto de un
#: escaneo oficial se lee correctamente y el coste por página sigue siendo de segundos.
DEFAULT_DPI = 300

#: Tiempo máximo por página. Un escaneo grande tarda segundos; un minuto es margen de sobra y evita
#: que un Tesseract atascado bloquee el lote.
DEFAULT_TIMEOUT_SECONDS = 60

#: Ejecuta un comando y devuelve el resultado. Se inyecta en las pruebas para no depender del
#: binario instalado.
Runner = Callable[[Sequence[str], float], "CompletedRun"]


@dataclass(frozen=True, slots=True)
class CompletedRun:
    """Lo que devuelve una ejecución del binario, reducido a lo que se usa."""

    returncode: int
    stdout: str
    stderr: str = ""


@dataclass(frozen=True, slots=True)
class OcrProbe:
    """Resultado de comprobar el binario de verdad."""

    available: bool
    detail: str
    version: str | None = None
    languages: tuple[str, ...] = ()


#: Lo que separa el texto de dos páginas. Es una decisión con consecuencia: el extractor cuenta con
#: **este** separador para saber dónde empieza cada página, y de ahí salen los números de página con
#: los que se citan los tramos. Un separador distinto descuadraría todas las citas.
PAGE_SEPARATOR = "\n\n"


@dataclass(frozen=True, slots=True)
class PdfOcrText:
    """Lo reconocido en un PDF, **página a página**, y el recuento del documento.

    Se devuelve por páginas y no como una sola cadena porque la página es lo que necesitan las
    citas: partir el texto por líneas en blanco daba secciones inventadas (una tabla con filas
    separadas producía dieciocho «páginas» en un documento de dos).
    """

    pages: tuple[str, ...]
    page_count: int

    @property
    def read_pages(self) -> int:
        return len(self.pages)

    @property
    def text(self) -> str:
        return PAGE_SEPARATOR.join(self.pages)

    @property
    def page_spans(self) -> tuple[tuple[int, int], ...]:
        """Tramo `(inicio, fin)` de cada página dentro de `text`, en orden."""
        tramos: list[tuple[int, int]] = []
        inicio = 0
        for pagina in self.pages:
            tramos.append((inicio, inicio + len(pagina)))
            inicio += len(pagina) + len(PAGE_SEPARATOR)
        return tuple(tramos)


def _run(command: Sequence[str], timeout: float) -> CompletedRun:
    try:
        completado = subprocess.run(  # noqa: S603 - comando construido con rutas de configuración
            list(command),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise OcrFailedError(f"Tesseract tardó más de {timeout:.0f} s y se detuvo") from error
    except OSError as error:
        raise OcrFailedError(f"No se pudo ejecutar Tesseract: {type(error).__name__}") from error
    return CompletedRun(
        returncode=completado.returncode,
        stdout=completado.stdout or "",
        stderr=completado.stderr or "",
    )


class OcrFailedError(RuntimeError):
    """El OCR no se pudo hacer: se dice, no se devuelve texto vacío como si no hubiera nada."""


class TesseractOcr:
    """Adaptador de Tesseract. Su única dependencia externa es el binario configurado."""

    def __init__(
        self,
        *,
        binary: Path,
        languages: str = "spa",
        tessdata: Path | None = None,
        dpi: int = DEFAULT_DPI,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        runner: Runner | None = None,
    ) -> None:
        self._binary = binary
        self._languages = languages
        self._tessdata = tessdata
        self._dpi = dpi
        self._timeout = timeout_seconds
        self._run = runner or _run
        self._probe: OcrProbe | None = None

    @property
    def binary(self) -> Path:
        return self._binary

    @property
    def languages(self) -> str:
        return self._languages

    @property
    def dpi(self) -> int:
        return self._dpi

    @property
    def tessdata(self) -> Path | None:
        """Directorio de modelos en uso, si se pasa alguno. Se dice: no es un detalle interno."""
        return self._tessdata

    def _base_command(self) -> list[str]:
        comando = [str(self._binary)]
        if self._tessdata is not None:
            comando += ["--tessdata-dir", str(self._tessdata)]
        return comando

    def probe(self, *, refresh: bool = False) -> OcrProbe:
        """Comprueba el binario de verdad y **memoriza** el resultado.

        Comprueba dos cosas, no una: que el binario responde (con su versión) y **que tiene el
        idioma configurado**. Un Tesseract sin `spa` instalado respondería igual a `--version` y
        luego no podría leer español: es el caso de este equipo antes de instalar el modelo.
        """
        if self._probe is not None and not refresh:
            return self._probe

        if not self._binary.is_file():
            self._probe = OcrProbe(
                available=False,
                detail=f"La ruta configurada no existe en este equipo: {self._binary.name}",
            )
            return self._probe

        try:
            version = self._run([str(self._binary), "--version"], 15.0)
        except OcrFailedError as error:
            self._probe = OcrProbe(available=False, detail=str(error))
            return self._probe
        if version.returncode != 0:
            self._probe = OcrProbe(
                available=False, detail=f"Tesseract respondió con código {version.returncode}"
            )
            return self._probe
        linea_version = next(
            (linea for linea in version.stdout.splitlines() if linea.strip()), ""
        ).strip()

        try:
            idiomas_crudos = self._run([*self._base_command(), "--list-langs"], 20.0)
        except OcrFailedError as error:
            self._probe = OcrProbe(available=False, detail=str(error), version=linea_version)
            return self._probe
        idiomas = tuple(
            linea.strip()
            for linea in idiomas_crudos.stdout.splitlines()
            if linea.strip() and " " not in linea.strip() and not linea.lower().startswith("list")
        )
        pedidos = tuple(idioma for idioma in self._languages.split("+") if idioma)
        faltan = [idioma for idioma in pedidos if idioma not in idiomas]
        if faltan:
            self._probe = OcrProbe(
                available=False,
                version=linea_version,
                languages=idiomas,
                detail=(
                    f"Tesseract {linea_version} está instalado, pero no tiene el idioma "
                    f"{' y '.join(faltan)}: solo puede leer {' y '.join(idiomas) or 'ninguno'}. "
                    "Un OCR en inglés sobre texto español produce texto plausible y equivocado."
                ),
            )
            return self._probe

        self._probe = OcrProbe(
            available=True,
            version=linea_version,
            languages=idiomas,
            detail=f"Tesseract {linea_version}, idiomas {'+'.join(pedidos)}",
        )
        return self._probe

    def text_of_image(self, path: Path) -> str:
        """Texto de una imagen. Lanza `OcrFailedError` si el OCR no se pudo hacer."""
        return self._ocr_fichero(path)

    def text_of_pdf(self, path: Path, *, max_pages: int, psm: int | None = None) -> PdfOcrText:
        """Texto de las páginas de un PDF escaneado, una entrada por página.

        Cada página se renderiza a 300 ppp y se OCRiza por separado: así una página ilegible no
        arrastra a las demás y el resultado se puede trocear por página, que es lo que necesitan las
        citas. El recuento total del documento se conserva aunque solo se lean las primeras páginas:
        sin él no se puede decir que falten.
        """
        import pymupdf  # import local: el OCR es opcional y no debe cargar PyMuPDF si no se usa

        try:
            documento = pymupdf.open(path)
        except (pymupdf.FileDataError, RuntimeError, ValueError) as error:
            raise OcrFailedError(
                f"No se pudo abrir el PDF para OCR: {type(error).__name__}"
            ) from error

        try:
            total = documento.page_count
            leer = min(total, max_pages)
            paginas: list[str] = []
            for numero in range(leer):
                pagina = documento.load_page(numero)
                with tempfile.TemporaryDirectory(prefix="opofuente-ocr-") as carpeta:
                    png = Path(carpeta) / f"pagina-{numero + 1}.png"
                    pagina.get_pixmap(dpi=self._dpi).save(png)
                    paginas.append(self._ocr_fichero(png, psm=psm).strip())
            return PdfOcrText(pages=tuple(paginas), page_count=total)
        finally:
            documento.close()

    def _ocr_fichero(self, path: Path, *, psm: int | None = None) -> str:
        sonda = self.probe()
        if not sonda.available:
            raise OcrFailedError(sonda.detail)
        comando = [*self._base_command(), str(path), "stdout", "-l", self._languages]
        # **El modo de segmentación importa y mucho en un examen escaneado**: con el
        # automático, Tesseract pone el número de la pregunta en una línea y su
        # enunciado en la siguiente, **y el parser no los une**. Con `6` —un bloque
        # de texto uniforme— el número y el enunciado salen en la misma línea.
        if psm is not None:
            comando += ["--psm", str(psm)]
        resultado = self._run(comando, self._timeout)
        if resultado.returncode != 0:
            motivo = resultado.stderr.strip()[:120]
            raise OcrFailedError(f"Tesseract terminó con código {resultado.returncode}: {motivo}")
        return resultado.stdout

    def describe(self) -> str:
        """Frase para la interfaz: qué OCR se usó, con qué idiomas y a qué resolución."""
        sonda = self.probe()
        idiomas = self._languages.replace("+", " y ")
        version = f" {sonda.version}" if sonda.version else ""
        modelos = f" Modelos de idioma en {self._tessdata}." if self._tessdata else ""
        return (
            f"Texto leído por OCR (Tesseract{version}, idioma {idiomas}, {self._dpi} ppp)."
            f"{modelos} El reconocimiento puede contener errores: la imagen se conserva."
        )


def default_tessdata() -> Path | None:
    """Dónde se buscan los modelos de idioma si no se configura un directorio.

    El instalador de Tesseract para Windows deja su `tessdata` **dentro de `Program Files`**, que no
    es escribible sin ser administrador: el modelo de español —que no viene de serie— no se puede
    dejar ahí, así que el sitio natural es el perfil del usuario. Se devuelve la ruta **solo si
    existe**: si no, no se le pasa nada al binario y manda el `tessdata` que tenga configurado, que
    es lo que hay que hacer cuando no hay nada que aportar (no se inventa una ruta).
    """
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        return None
    ruta = Path(base) / "OpoFuente" / "tessdata"
    return ruta if ruta.is_dir() else None


def tesseract_from_settings(settings: Settings) -> TesseractOcr | None:
    """El único sitio donde la configuración se convierte en un adaptador de OCR.

    Devuelve `None` si no hay ruta configurada: el OCR es opcional y la aplicación funciona sin él.
    Se construye **una sola instancia** por proceso (main.py) para que la sonda se ejecute una vez y
    el informe de capacidades y el extractor hablen del mismo binario.
    """
    if settings.tesseract_path is None:
        return None
    return TesseractOcr(
        binary=settings.tesseract_path,
        languages=settings.tesseract_languages,
        tessdata=settings.tesseract_tessdata or default_tessdata(),
    )
