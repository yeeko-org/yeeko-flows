"""asigna_partes — reparte los nombres capturados según el rol del operador y
fija su teléfono desde el canal de WhatsApp, sin preguntar (pieza A5).

El teléfono del operador no es un dato capturado: viene del canal y
get_extra_values_data lo expone como `phone` (de User.phone). Por eso este
behavior es determinista y no puede delegarse a ia_extrae.
"""
from projects.caceh.behaviors.base import CacehBehaviorBase


class AsignaPartesBehavior(CacehBehaviorBase):
    behavior_name = "asigna_partes"

    def run(self) -> None:
        operador = self._read("operador")
        operador_nombre = self._read("operador_nombre")
        contraparte_nombre = self._read("contraparte_nombre")

        if operador == "trabajadora":
            trab, empl = operador_nombre, contraparte_nombre
        elif operador == "empleadora":
            trab, empl = contraparte_nombre, operador_nombre
        else:
            self.response.add_error({
                "behavior": self.behavior_name, "operador": operador,
                "message": "operador inválido o ausente"})
            return

        self._write("trab_nombre_completo", trab)
        self._write("empl_nombre_completo", empl)

        telefono = self._read("phone")
        if telefono:
            self._write("telefono_operador", telefono)
