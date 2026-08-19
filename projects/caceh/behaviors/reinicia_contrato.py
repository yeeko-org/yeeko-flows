"""reinicia_contrato — deja al miembro listo para un contrato nuevo (pieza E10).

Hace lo mismo que el `reset` genérico del motor (`services/behavior/reset.py`:
`remove_all_extras()`), pero sin su parte de arranque ni su mensaje: el
genérico dispara `start` él mismo, y en un paso ⚙️ eso rendiría el saludo dos
veces (una por el behavior y otra por el `embedded` de auto-avance). Aquí el
behavior solo borra y el destino del seed manda dónde reaparece la persona,
que es como se cablea todo lo demás del flujo.

Borrar todo es la decisión, no un descuido: una trabajadora de entrada por
salida con varias empleadoras arma un contrato por empleadora y ninguno hereda
datos del anterior.
"""
from projects.caceh.behaviors.base import CacehBehaviorBase


class ReiniciaContratoBehavior(CacehBehaviorBase):
    behavior_name = "reinicia_contrato"

    def run(self) -> None:
        self.member.remove_all_extras()
