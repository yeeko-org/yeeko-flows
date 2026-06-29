"""Base común de los behaviors deterministas de CACEH.

Patrón Template Method: la base resuelve el contexto (extras del miembro y el
space) y expone helpers `_read`/`_write`; cada behavior implementa `run()`.
Evita repetir el patrón de localizar el Extra por nombre y escribir con
add_extra_value (el mismo que usa ia_extrae). El motor localiza estas clases
por el `app_label` de la Collection del Behavior (ver
services/processor/behavior.py) y las busca por su alias snake_case en
projects/caceh/behaviors/__init__.py.
"""
from infrastructure.xtra.models import Extra
from services.response.abstract import ResponseAbc


class CacehBehaviorBase:
    # Identidad del behavior (para errores); lo fija cada subclase.
    behavior_name = "caceh_base"
    # Provenance de los extras escritos: ORIGIN_CHOICES no tiene nombres de
    # función; "assigned" ("Asignado") es la categoría para un dato derivado
    # por una función (y cabe en el varchar(20) de ExtraValue.origin).
    extra_origin = "assigned"

    def __init__(self, response: ResponseAbc, **kwargs):
        self.response = response
        self.member = response.sender.member
        self.account = response.sender.account
        self.space = response.sender.account.space
        # refrest=True: relee de BD para no arrastrar una caché previa del
        # mismo request (un behavior anterior pudo escribir un extra que
        # necesitamos). Estos behaviors corren pocas veces; el costo es nulo.
        self.data = self.member.get_extra_values_data(refrest=True)
        self.params = kwargs
        self.run()

    def run(self) -> None:
        raise NotImplementedError

    def _read(self, name: str, default=None):
        return self.data.get(name, default)

    def _write(self, name: str, value, required: bool = True) -> None:
        extra = Extra.objects.filter(
            name=name, space=self.space, deleted=False).first()
        if not extra:
            if required:
                self.response.add_error({
                    "behavior": self.behavior_name, "extra": name,
                    "message": "extra no encontrado"})
            return
        self.response.add_extra_value(
            extra, value, origin=self.extra_origin)
