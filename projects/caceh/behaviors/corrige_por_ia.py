"""corrige_por_ia — corrección por IA desde el resumen final (E4).

No reusa ia_extrae: el contexto de aquel viaja por el parámetro `entrada`
(ParamValue, varchar 255) y el estado del contrato no cabe. Aquí el estado
se arma desde self.data filtrado por lista blanca (el dict trae phone,
email, username y los historiales `_hist_*`, que no deben viajar a Gemini)
y se manda junto con lo que la persona escribió. Todo lo demás calca el
contrato de ia_extrae: historial por vueltas, validación Pydantic como
repregunta, escritura de los no-None, `ia_completed`/`ia_pregunta`.
"""
import json
from typing import Optional

from pydantic import ValidationError

from infrastructure.xtra.models import Extra
from projects.caceh.behaviors.base import CacehBehaviorBase
from projects.caceh.schemas import CORRECCION_PROMPT, Correccion
from utilities.gemini_client import GeminiClient

# Campos que Gemini puede reescribir (= campos del esquema Correccion).
# tipo_contrato y fecha_inicio quedan fuera a propósito (task-27, dec. 3).
CORREGIBLES = (
    "trab_nombre_completo", "empl_nombre_completo",
    "hora_entrada", "hora_salida", "dias_laborables",
    "lt_calle", "lt_ext", "lt_int", "lt_colonia", "lt_cp", "lt_municipio",
    "lt_estado", "ciudad_firma",
    "monto_pago", "pago_periodicidad", "modo_pago",
    "descanso_minutos", "comidas_incluidas",
)
# Solo en entrada por salida; en planta no viajan ni se escriben.
_SOLO_ENTRADA_SALIDA = ("descanso_minutos", "comidas_incluidas")
# Contexto de solo lectura: el resumen imprime el diario (la persona
# reacciona a ese número) y el tipo decide si aplica el descanso.
CONTEXTO = ("tipo_contrato", "salario_diario")

_HIST = "_hist_correccion"
_PREGUNTA_FALLBACK = "Perdón, no te entendí bien. ¿Me lo dices de otra forma?"
_PREGUNTA_SIN_CAMBIO = (
    "No alcancé a ver qué cambiar. ¿Me dices qué dato está mal y cómo "
    "debe quedar?")


class CorrigePorIaBehavior(CacehBehaviorBase):
    behavior_name = "corrige_por_ia"

    def __init__(self, response, client: Optional[GeminiClient] = None,
                 **kwargs):
        # El cliente se inyecta en tests; la base llama run() al construirse.
        self.client = client
        super().__init__(response, **kwargs)

    def run(self) -> None:
        client = self.client or GeminiClient()
        historial = self._append_historial(self._read("respuesta_correccion"))
        user_text = (
            "ESTADO ACTUAL:\n" + json.dumps(self._estado(), ensure_ascii=False)
            + "\n\nLO QUE LA PERSONA ESCRIBIÓ:\n" + "\n".join(historial))

        data = client.extract(CORRECCION_PROMPT, user_text, Correccion)
        if data is None:
            self._repregunta(_PREGUNTA_FALLBACK)
            return

        try:
            data = Correccion(**data).model_dump()
        except ValidationError as e:
            # A diferencia de ia_extrae no se persiste nada del dict inválido:
            # aquí pisaríamos un dato bueno con uno malo.
            self._repregunta(data.get("ia_pregunta") or e.errors()[0].get(
                "msg", "Revisa ese dato, por favor."))
            return

        cambios = {k: v for k, v in data.items()
                   if k in self._corregibles() and v is not None}
        actividades = data.get("cambiar_actividades") == "si"
        if data.get("ia_completed") != "si":
            self._repregunta(data.get("ia_pregunta") or _PREGUNTA_FALLBACK)
            return
        if not cambios and not actividades:
            # Gemini dijo «listo» sin cambiar nada: volver al resumen igual
            # confundiría más que una repregunta.
            self._repregunta(_PREGUNTA_SIN_CAMBIO)
            return

        for name, value in cambios.items():
            self._write(name, value)
        self._write("correccion_destino",
                    "actividades" if actividades else "resumen")
        self._write("ia_completed", "si")
        self._clear_historial()

    def _corregibles(self) -> tuple:
        if self._read("tipo_contrato") == "entrada_salida":
            return CORREGIBLES
        return tuple(c for c in CORREGIBLES
                     if c not in _SOLO_ENTRADA_SALIDA)

    def _estado(self) -> dict:
        names = CONTEXTO + self._corregibles()
        return {n: self._read(n) for n in names if self._read(n) is not None}

    def _repregunta(self, pregunta: str) -> None:
        self._write("ia_completed", "no")
        self._write("ia_pregunta", pregunta)

    def _append_historial(self, texto) -> list:
        historial = self._read(_HIST) or []
        if not isinstance(historial, list):
            historial = []
        if texto:
            historial.append(str(texto))
        self._write(_HIST, historial, required=False)
        return historial

    def _clear_historial(self) -> None:
        extra = Extra.objects.filter(
            name=_HIST, space=self.space, deleted=False).first()
        if extra:
            self.member.remove_extra(extra)
