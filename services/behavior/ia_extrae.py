from typing import Optional, Type

from pydantic import BaseModel, ValidationError

from infrastructure.xtra.models import Extra
from services.behavior.extraction import (  # noqa: F401 — re-exported
    ExtrasMixin, PREGUNTA_GENERICA, SCHEMA_REGISTRY, generic_reask_text,
    register_schema, repregunta_de_error)
from services.response.abstract import ResponseAbc
from utilities.gemini_client import GeminiClient
from utilities.replacer_from_data import replace_parameter


class IaExtraeBehavior(ExtrasMixin):
    """Behavior genérico de extracción por IA.

    Recibe (esquema, entrada) por ParamValue. Acumula las respuestas del
    usuario en un extra de historial transitorio (`_hist_<esquema>`), las manda
    a Gemini pidiendo salida que cumpla el esquema, valida con Pydantic y
    escribe cada campo en su extra homónimo. `ia_completed` gobierna el loop de
    repregunta del flujo; al completar, limpia el historial.

    Es un paso de cómputo dentro de una pieza: no procesa destinos. El avance
    del flujo (hacia la bifurcación que lee `ia_completed`) lo arma el seed.
    """
    behavior_name = "ia_extrae"
    extra_origin = "ia_extrae"

    def __init__(
            self, response: ResponseAbc, esquema: Optional[str] = None,
            entrada: str = "", client: Optional[GeminiClient] = None,
            **kwargs
    ):
        self.response = response
        self.member = response.sender.member
        self.space = response.sender.account.space

        if not esquema or esquema not in SCHEMA_REGISTRY:
            response.add_error({
                "behavior": "ia_extrae", "esquema": esquema,
                "message": "esquema no registrado"})
            return

        schema_cls, system_prompt = SCHEMA_REGISTRY[esquema]
        # El cliente se inyecta en tests (Gemini mockeado); en runtime se crea
        # aquí para no instanciarlo cuando el esquema es inválido.
        self.client = client or GeminiClient()

        # refrest=True: estado fresco de BD (la respuesta recién guardada por el
        # procesador de texto y el historial de vueltas previas). El cache de
        # member es por instancia y puede venir poblado/stale desde un paso
        # anterior de la misma request.
        data = self.member.get_extra_values_data(refrest=True)
        entrada_text = replace_parameter(data, entrada)
        historial = self._append_historial(esquema, entrada_text)

        data = self.client.extract(
            system_prompt, "\n".join(historial), schema_cls)
        if data is None:
            self._write("ia_completed", "no")
            self._write("ia_pregunta", generic_reask_text())
            return

        data = self._validate(schema_cls, data)
        self._persist(data)

        if data.get("ia_completed") == "si":
            self._clear_historial(esquema)

    def _validate(self, schema_cls: Type[BaseModel], data: dict) -> dict:
        """Corre los validadores Pydantic; si fallan, lo trata como
        repregunta (ia_completed='no' + una pregunta derivada del error)."""
        try:
            return schema_cls(**data).model_dump()
        except ValidationError as e:
            data["ia_completed"] = "no"
            if not data.get("ia_pregunta"):
                data["ia_pregunta"] = repregunta_de_error(
                    e, generic_reask_text())
            return data

    def _persist(self, data: dict):
        for name, value in data.items():
            if value is None:
                continue  # no sobreescribir el extra con "None"
            self._write(name, value)

    # --- historial transitorio por esquema -------------------------------

    def _append_historial(self, esquema: str, entrada_text: str) -> list:
        data = self.member.get_extra_values_data()
        historial = data.get(self._hist_name(esquema)) or []
        if not isinstance(historial, list):
            historial = []
        if entrada_text:
            historial.append(entrada_text)
        # best-effort: si el extra de historial no está sembrado, igual
        # extraemos con lo que haya en memoria (single-shot).
        self._write(self._hist_name(esquema), historial, required=False)
        return historial

    def _clear_historial(self, esquema: str):
        extra = Extra.objects.filter(
            name=self._hist_name(esquema), space=self.space,
            deleted=False).first()
        if extra:
            self.member.remove_extra(extra)
