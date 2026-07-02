"""valida_fecha_pasada — valida la fecha de inicio retroactiva (pieza C3).

Determinista a propósito: la fecha de inicio entra en la cláusula SEGUNDA del
contrato y fija la antigüedad de la relación, así que su validez es legal y no
se delega a un LLM. Acepta día/mes/año o solo mes/año (asume el día 1), exige
que sea una fecha pasada y la normaliza a 'd/m/Y' para que genera_pdf la consuma.

Patrón de control igual al de los bloques IA: escribe {{fecha_valida}} ('si'/
'no') para que la bifurcación C3b decida, y {{fecha_error}} con el mensaje de
reedición cuando rechaza. No usa add_error: una fecha mal escrita es un reintento
normal del usuario, no un fallo del flujo.
"""
from datetime import date, datetime

from projects.caceh.behaviors.base import CacehBehaviorBase

# Formatos completos (día/mes/año) y de solo mes/año (caen al día 1 vía
# strptime, que rellena los componentes ausentes con su valor mínimo).
_FORMATOS_COMPLETOS = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d")
_FORMATOS_MES_ANIO = ("%m/%Y", "%m-%Y")


class ValidaFechaPasadaBehavior(CacehBehaviorBase):
    behavior_name = "valida_fecha_pasada"

    def run(self) -> None:
        raw = (self._read("fecha_inicio") or "").strip()
        parsed = self._parse(raw)
        if parsed is None:
            self._reject(
                "No entendí la fecha. 🗓️ Escríbela como día/mes/año, por "
                "ejemplo 15/03/2023 (o solo mes/año, 03/2023).")
            return
        if parsed > date.today():
            self._reject(
                "Esa fecha todavía no llega. 🗓️ Dime la fecha en que "
                "empezaron a trabajar, por ejemplo 15/03/2023.")
            return

        # Normaliza a 'd/m/Y' (el formato que genera_pdf sabe parsear) y limpia
        # un posible mensaje de error de un intento anterior.
        self._write("fecha_inicio", parsed.strftime("%d/%m/%Y"))
        self._write("fecha_valida", "si")
        self._write("fecha_error", "")

    def _parse(self, raw: str):
        for fmt in _FORMATOS_COMPLETOS + _FORMATOS_MES_ANIO:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None

    def _reject(self, message: str) -> None:
        self._write("fecha_valida", "no")
        self._write("fecha_error", message)
