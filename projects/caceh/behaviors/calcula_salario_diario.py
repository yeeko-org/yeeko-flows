"""calcula_salario_diario — convierte el pago pactado a salario diario según la
periodicidad y los días trabajados por semana (pieza C8).

Determinista a propósito: el salario diario se imprime en el contrato (cláusula
QUINTA) y se registra como constancia, así que la exactitud es legal; no se
delega a un LLM.
"""
from projects.caceh.behaviors.base import CacehBehaviorBase
from projects.caceh.derivados import salario_diario


class CalculaSalarioDiarioBehavior(CacehBehaviorBase):
    behavior_name = "calcula_salario_diario"

    def run(self) -> None:
        monto = self._read("monto_pago")
        periodicidad = self._read("pago_periodicidad")
        dias_sem = len(self._read("dias_laborables") or [])

        if monto is None or not periodicidad:
            self._error("faltan monto_pago o pago_periodicidad")
            return
        try:
            float(monto)
        except (TypeError, ValueError):
            self._error(f"monto_pago no numérico: {monto!r}")
            return
        if periodicidad not in ("diaria", "semanal", "quincenal", "mensual"):
            self._error(f"periodicidad inválida: {periodicidad!r}")
            return
        diario = salario_diario(monto, periodicidad, dias_sem)
        if diario is None:
            self._error("dias_laborables vacío; no se puede prorratear")
            return

        self._write("salario_diario", round(diario, 2))

    def _error(self, message: str) -> None:
        self.response.add_error({
            "behavior": self.behavior_name, "message": message})
