"""calcula_salario_diario — convierte el pago pactado a salario diario según la
periodicidad y los días trabajados por semana (pieza C8).

Determinista a propósito: el salario diario se imprime en el contrato (cláusula
QUINTA) y se registra como constancia, así que la exactitud es legal; no se
delega a un LLM.
"""
from projects.caceh.behaviors.base import CacehBehaviorBase

# Semanas promedio por mes (52/12 ≈ 4.333) para prorratear el pago mensual.
# TODO confirmar con CACEH: el spec solo fijó diaria/semanal/quincenal.
_SEMANAS_POR_MES = 52 / 12


class CalculaSalarioDiarioBehavior(CacehBehaviorBase):
    behavior_name = "calcula_salario_diario"

    def run(self) -> None:
        monto = self._read("monto_pago")
        periodicidad = self._read("pago_periodicidad")
        dias = self._read("dias_laborables") or []
        dias_sem = len(dias)

        if monto is None or not periodicidad:
            self._error("faltan monto_pago o pago_periodicidad")
            return
        try:
            monto = float(monto)
        except (TypeError, ValueError):
            self._error(f"monto_pago no numérico: {monto!r}")
            return

        # Toda periodicidad mayor a la diaria necesita los días por semana.
        if periodicidad != "diaria" and dias_sem == 0:
            self._error("dias_laborables vacío; no se puede prorratear")
            return

        if periodicidad == "diaria":
            diario = monto
        elif periodicidad == "semanal":
            diario = monto / dias_sem
        elif periodicidad == "quincenal":
            diario = monto / (dias_sem * 2)
        elif periodicidad == "mensual":
            diario = monto / (dias_sem * _SEMANAS_POR_MES)
        else:
            self._error(f"periodicidad inválida: {periodicidad!r}")
            return

        self._write("salario_diario", round(diario, 2))

    def _error(self, message: str) -> None:
        self.response.add_error({
            "behavior": self.behavior_name, "message": message})
