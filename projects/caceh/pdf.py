"""Render del contrato a PDF (slice planta).

render_planta(datos) -> bytes: lee el template Jinja2 desde el paquete y lo pasa
por WeasyPrint. Es puro: recibe el dict de datos ya armado (lo construye el
behavior genera_pdf) y devuelve los bytes del PDF; no toca BD ni red.
"""
from decimal import Decimal, InvalidOperation
from pathlib import Path

from jinja2 import Template
from num2words import num2words
from weasyprint import HTML

_TEMPLATES_DIR = Path(__file__).parent / "templates" / "caceh"
_TEMPLATES = {
    "planta": "contrato_planta.html",
    "entrada_salida": "contrato_entrada_salida.html",
}


def _apocope(palabras: str) -> str:
    """'uno' final se apocopa ante sustantivo: veintiuno -> veintiún,
    ciento uno -> ciento un (acento solo cuando queda dentro de palabra)."""
    if palabras.endswith("veintiuno"):
        return palabras[:-len("veintiuno")] + "veintiún"
    if palabras.endswith("uno"):
        return palabras[:-len("uno")] + "un"
    return palabras


def monto_en_letras(valor) -> str:
    """Monto en palabras para la QUINTA, en el formato del contrato original:
    'trescientos cincuenta pesos 00/100 M.N'. Cadena vacía si no hay monto
    usable: lo no capturado se omite, nunca se imprime una línea en blanco."""
    try:
        monto = Decimal(str(valor).replace("$", "").replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return ""
    if monto <= 0:
        return ""
    pesos, centavos = divmod(int(monto.scaleb(2).to_integral_value()), 100)
    letras = _apocope(num2words(pesos, lang="es"))
    unidad = "peso" if pesos == 1 else "pesos"
    return f"{letras} {unidad} {centavos:02d}/100 M.N"


def build_html(datos: dict, tipo_contrato: str = "planta") -> str:
    """Render del HTML del contrato según la modalidad. Separado de WeasyPrint
    para poder afirmar el contenido en tests sin generar el PDF."""
    name = _TEMPLATES.get(tipo_contrato, _TEMPLATES["planta"])
    tpl = (_TEMPLATES_DIR / name).read_text(encoding="utf-8")
    # El monto en letras se deriva aquí y no en genera_pdf para que valga
    # igual en cualquier ruta de render (incluidas las pruebas del HTML).
    datos = {**datos,
             "salario_letras": monto_en_letras(datos.get("salario_diario"))}
    return Template(tpl).render(**datos)


def render_planta(datos: dict) -> bytes:
    return HTML(string=build_html(datos, "planta")).write_pdf()


def render_entrada_salida(datos: dict) -> bytes:
    return HTML(string=build_html(datos, "entrada_salida")).write_pdf()