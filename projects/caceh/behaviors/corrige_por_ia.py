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
from projects.caceh import derivados
from projects.caceh.behaviors.base import CacehBehaviorBase
from projects.caceh.schemas import CORRECCION_PROMPT, Correccion, Fecha
from projects.caceh.seed.textos import PREGUNTA_FECHA
from services.behavior.extraction import (
    generic_reask_text, repregunta_de_error)
from utilities.gemini_client import GeminiClient

# Campos que Gemini puede reescribir (= campos del esquema Correccion).
# tipo_contrato queda fuera a propósito (task-27, dec. 3); fecha_inicio se
# compone de las tres partes, nunca se escribe directo.
CORREGIBLES = (
    "trab_nombre_completo", "empl_nombre_completo",
    "hora_entrada", "hora_salida", "dias_laborables",
    "lt_calle", "lt_ext", "lt_int", "lt_colonia", "lt_cp", "lt_municipio",
    "lt_estado", "ciudad_firma",
    "monto_pago", "pago_periodicidad", "modo_pago",
    "descanso_minutos", "comidas_incluidas",
    "fecha_dia", "fecha_mes", "fecha_anio",
)
# Solo en entrada por salida; en planta no viajan ni se escriben.
_SOLO_ENTRADA_SALIDA = ("descanso_minutos", "comidas_incluidas")
# Solo si se preguntó la fecha («Ya trabajábamos»); si no, el contrato
# empieza hoy y no hay fecha que corregir.
_FECHA = ("fecha_dia", "fecha_mes", "fecha_anio")
# Contexto de solo lectura: el resumen imprime el diario (la persona
# reacciona a ese número), el tipo decide si aplica el descanso y
# es_retroactivo si aplica la fecha.
CONTEXTO = ("tipo_contrato", "salario_diario", "es_retroactivo")

_HIST = "_hist_correccion"
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
            self._repregunta(generic_reask_text())
            return

        try:
            data = Correccion(**data).model_dump()
        except ValidationError as e:
            # A diferencia de ia_extrae no se persiste nada del dict inválido:
            # aquí pisaríamos un dato bueno con uno malo.
            self._repregunta(
                data.get("ia_pregunta")
                or repregunta_de_error(e, generic_reask_text()))
            return

        cambios = {k: v for k, v in data.items()
                   if k in self._corregibles() and v is not None}
        actividades = data.get("cambiar_actividades") == "si"
        if data.get("ia_completed") != "si":
            self._repregunta(
                data.get("ia_pregunta") or generic_reask_text())
            return
        if not cambios and not actividades:
            # Gemini dijo «listo» sin cambiar nada: volver al resumen igual
            # confundiría más que una repregunta.
            self._repregunta(_PREGUNTA_SIN_CAMBIO)
            return
        if any(k in cambios for k in _FECHA):
            error = self._compone_fecha(cambios)
            if error:
                self._repregunta(error)
                return

        for name, value in cambios.items():
            self._write(name, value)
        self._recalcula_textos()
        self._write("correccion_destino",
                    "actividades" if actividades else "resumen")
        self._write("ia_completed", "si")
        self._clear_historial()

    def _recalcula_textos(self) -> None:
        # El resumen imprime los textos armados (lt_texto): sin esto
        # mostraría la dirección de antes de la corrección. Un None borra,
        # como en las unidades: el descanso o la fecha que ya no aplican
        # dejan de salir en el resumen.
        data = self.member.get_extra_values_data(refrest=True)
        for derivado in derivados.TEXTOS:
            for name, value in derivado(data).items():
                if value is not None:
                    self._write(name, value, required=False)
                    continue
                extra = Extra.objects.filter(
                    name=name, space=self.space, deleted=False).first()
                if extra:
                    self.member.remove_extra(extra)

    def _compone_fecha(self, cambios: dict) -> Optional[str]:
        """Agrega fecha_inicio a `cambios`, o devuelve la repregunta sin
        tocarlo. Las partes no corregidas son las guardadas, como en la
        corrección de la propia unidad: «el año es 2016» conserva día y
        mes."""
        partes = {k: cambios.get(k, self._read(k)) for k in _FECHA}
        try:
            fecha = Fecha(**partes, ia_completed="si")
        except ValidationError as e:
            return repregunta_de_error(e, generic_reask_text())
        if not fecha.fecha_inicio:
            # Sin mes o año guardados (la unidad soltó la fecha) y la
            # corrección no los trae.
            return PREGUNTA_FECHA
        cambios["fecha_inicio"] = fecha.fecha_inicio
        return None

    def _corregibles(self) -> tuple:
        fuera = ()
        if self._read("tipo_contrato") != "entrada_salida":
            fuera += _SOLO_ENTRADA_SALIDA
        if self._read("es_retroactivo") != "si":
            fuera += _FECHA
        return tuple(c for c in CORREGIBLES if c not in fuera)

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
