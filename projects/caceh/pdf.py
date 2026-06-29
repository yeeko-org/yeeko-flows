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

_TEMPLATE_PATH = (
    Path(__file__).parent / "templates" / "caceh" / "contrato_planta.html"
)


def render_planta(datos: dict) -> bytes:
    html = Template(_TEMPLATE_PATH.read_text(encoding="utf-8")).render(**datos)
    return HTML(string=html).write_pdf()