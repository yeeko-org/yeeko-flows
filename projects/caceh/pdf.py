"""Render del contrato a PDF (slice planta).

render_planta(datos) -> bytes: lee el template Jinja2 desde el paquete y lo pasa
por WeasyPrint. Es puro: recibe el dict de datos ya armado (lo construye el
behavior genera_pdf) y devuelve los bytes del PDF; no toca BD ni red.

TODO (pendiente con Nivo): el monto en QUINTA va como dígitos ('$350.00'); el
contrato original pide también el monto en letras ('(trescientos cincuenta /100
M.N)'). Se omitió en el slice para no añadir num2words; afinar antes de
producción.
"""
from pathlib import Path

from jinja2 import Template
from weasyprint import HTML

_TEMPLATES_DIR = Path(__file__).parent / "templates" / "caceh"
_TEMPLATES = {
    "planta": "contrato_planta.html",
    "entrada_salida": "contrato_entrada_salida.html",
}


def build_html(datos: dict, tipo_contrato: str = "planta") -> str:
    """Render del HTML del contrato según la modalidad. Separado de WeasyPrint
    para poder afirmar el contenido en tests sin generar el PDF."""
    name = _TEMPLATES.get(tipo_contrato, _TEMPLATES["planta"])
    tpl = (_TEMPLATES_DIR / name).read_text(encoding="utf-8")
    return Template(tpl).render(**datos)


def render_planta(datos: dict) -> bytes:
    return HTML(string=build_html(datos, "planta")).write_pdf()


def render_entrada_salida(datos: dict) -> bytes:
    return HTML(string=build_html(datos, "entrada_salida")).write_pdf()