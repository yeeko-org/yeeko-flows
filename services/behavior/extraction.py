"""What the AI-extraction behaviors share: the schema registry a project
fills, the derivations it hooks in, the generic re-ask and the extras
helpers. `ia_extrae` and `open_question` both build on it.
"""
from typing import Any, Callable, Optional, Type

from pydantic import BaseModel, ValidationError

from infrastructure.tool.models import Parameter
from infrastructure.xtra.models import Extra
from services.response.abstract import ResponseAbc


# Registro nombre_de_esquema -> (clase Pydantic, system prompt). Lo pueblan los
# proyectos (p. ej. projects/caceh/schemas.py) con @register_schema,
# autodescubierto en su AppConfig.ready(). El motor no importa los proyectos:
# el contenido de dominio se "enchufa" al cargar.
SCHEMA_REGISTRY: dict[str, tuple[Type[BaseModel], str]] = {}

# Fields every schema carries to steer the extraction loop; they are never
# stored by `open_question`.
CONTROL_FIELDS = ("ia_completed", "ia_pregunta")

# The seed value of the `reask` slot of `open_question`. At run time the
# text is read from that Parameter row (the DB owns it); this constant is
# only its initial value and the fallback before the row exists.
PREGUNTA_GENERICA = (
    "Disculpa, no te entendí bien. Por favor, ayúdame a escribir una nueva "
    "respuesta.")

Derivation = Callable[[ResponseAbc, dict], Optional[dict]]
DERIVATIONS: dict[str, list[Derivation]] = {}


def register_schema(name: str, system_prompt: str):
    """Decorador para registrar un esquema de extracción bajo `name`."""
    def deco(cls: Type[BaseModel]) -> Type[BaseModel]:
        SCHEMA_REGISTRY[name] = (cls, system_prompt)
        return cls
    return deco


def register_derivation(schema_name: str):
    """Hooks `fn(response, extras) -> {extra_name: value} | None` to a
    schema: it runs after every value of that schema is stored, first
    capture or correction, with the member's extras already updated. Each
    returned pair is written; a None value removes the extra."""
    def deco(fn: Derivation) -> Derivation:
        DERIVATIONS.setdefault(schema_name, []).append(fn)
        return fn
    return deco


def validation_message(e: ValidationError) -> Optional[str]:
    """The text a project validator wrote for the person, if any.

    Solo un `value_error` lo redactamos nosotros (un ValueError de un
    validador del proyecto); se toma de `ctx` porque `msg` le antepone
    «Value error, ». Cualquier otro tipo trae el mensaje de Pydantic en
    inglés, que nunca debe llegar a la persona.
    """
    for err in e.errors():
        if err.get("type") == "value_error":
            own = str(err.get("ctx", {}).get("error", "")).strip()
            if own:
                return own
    return None


def repregunta_de_error(e: ValidationError,
                        generic: str = PREGUNTA_GENERICA) -> str:
    """Texto que la persona recibe cuando la validación Pydantic falla."""
    return validation_message(e) or generic


def generic_reask_text() -> str:
    """The generic re-ask, from the one place it is edited: the default of
    the `reask` slot of `open_question`."""
    param = Parameter.objects.filter(
        behavior_id="open_question", name="reask", deleted=False).first()
    return (param.default_value if param else None) or PREGUNTA_GENERICA


class ExtrasMixin:
    """Reads and writes the member's extras by name within its space."""
    response: ResponseAbc
    extra_origin: str = "unknown"
    behavior_name: str = ""

    def _extra(self, name: str) -> Optional[Extra]:
        return Extra.objects.filter(
            name=name, space=self.response.sender.account.space,
            deleted=False).first()

    def _write(self, name: str, value: Any, required: bool = True) -> None:
        extra = self._extra(name)
        if not extra:
            if required:
                self.response.add_error({
                    "behavior": self.behavior_name, "extra": name,
                    "message": "extra no encontrado"})
            return
        self.response.add_extra_value(extra, value, origin=self.extra_origin)

    def _remove(self, name: str) -> None:
        extra = self._extra(name)
        if extra:
            self.response.sender.member.remove_extra(extra)

    @staticmethod
    def _hist_name(schema: str) -> str:
        return f"_hist_{schema}"
