"""Esquemas Pydantic de extracción del bot CACEH (slice del demo).

Cada esquema declara los datos a extraer + los campos de control del loop
(`ia_completed`, `ia_pregunta`) y se registra con @register_schema para que el
behavior genérico `ia_extrae` lo encuentre por nombre. Los nombres de los
campos coinciden 1:1 con las claves de los `Extra` del flujo (ver
flows/variables_v3.md).
"""

from typing import Literal, Optional

from pydantic import BaseModel, field_validator

from services.behavior.ia_extrae import register_schema


_PREAMBULO = (
    "Eres el asistente de CACEH que arma contratos de trabajo del hogar en "
    "México. Recibes lo que la persona escribió con sus palabras (puede venir "
    "en varias líneas, una por cada vez que respondió) y extraes los datos al "
    "esquema. Reglas generales:\n"
    "- Responde SOLO con el JSON del esquema.\n"
    "- Si tienes todos los datos obligatorios, pon ia_completed='si' y deja "
    "ia_pregunta vacío.\n"
    "- Si falta algún dato obligatorio o es ambiguo, pon ia_completed='no' y "
    "escribe en ia_pregunta UNA sola pregunta corta, amable y en español "
    "sencillo para conseguir lo que falta. No inventes datos.\n"
)


JORNADA_PROMPT = _PREAMBULO + (
    "Esquema jornada: días de trabajo y horario.\n"
    "- hora_entrada y hora_salida en formato '8:00' / '16:00'.\n"
    "- dias_laborables: lista de días en minúscula "
    "('lunes','martes',...). Máximo 6 días (la ley exige al menos uno de "
    "descanso); si la persona dice 'toda la semana' o 7 días, pregunta cuál "
    "será el día de descanso.\n"
)


@register_schema("jornada", JORNADA_PROMPT)
class Jornada(BaseModel):
    hora_entrada: Optional[str] = None
    hora_salida: Optional[str] = None
    dias_laborables: Optional[list[str]] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None

    @field_validator("dias_laborables")
    @classmethod
    def max_seis_dias(cls, v):
        if v and len(v) > 6:
            raise ValueError(
                "Por ley debe haber al menos un día de descanso. "
                "¿Qué día descansará?")
        return v


PAGO_PROMPT = _PREAMBULO + (
    "Esquema pago: cuánto se paga y cada cuándo.\n"
    "- monto_pago: número entero en pesos, sin signos ni comas "
    "(ej. '2,500' -> 2500).\n"
    "- pago_periodicidad: una de 'diaria','semanal','quincenal','mensual'.\n"
)


@register_schema("pago", PAGO_PROMPT)
class Pago(BaseModel):
    monto_pago: Optional[int] = None
    pago_periodicidad: Optional[
        Literal["diaria", "semanal", "quincenal", "mensual"]] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None


DOMICILIO_PROMPT = _PREAMBULO + (
    "Esquema domicilio: dirección del lugar de trabajo en México.\n"
    "- Campos: lt_calle, lt_ext (número exterior), lt_int (interior, "
    "OPCIONAL), lt_colonia, lt_cp (5 dígitos), lt_municipio (alcaldía o "
    "municipio), lt_estado.\n"
    "- Todos son obligatorios MENOS lt_int. Si falta el código postal, la "
    "colonia o el municipio, pregúntalo.\n"
    "- ciudad_firma: derivado, NO lo preguntes. Cópialo de lt_municipio "
    "(donde se trabaja se firma); el usuario lo corrige luego en el resumen.\n"
)


@register_schema("domicilio", DOMICILIO_PROMPT)
class Domicilio(BaseModel):
    lt_calle: Optional[str] = None
    lt_ext: Optional[str] = None
    lt_int: Optional[str] = None
    lt_colonia: Optional[str] = None
    lt_cp: Optional[str] = None
    lt_municipio: Optional[str] = None
    lt_estado: Optional[str] = None
    # Derivado por la misma llamada (sustituye al behavior deriva_ciudad_firma).
    # No bloquea ia_completed: si Gemini lo deja vacío, genera_pdf cae a
    # lt_municipio.
    ciudad_firma: Optional[str] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None

    @field_validator("lt_cp")
    @classmethod
    def cp_cinco_digitos(cls, v):
        if v and (not v.isdigit() or len(v) != 5):
            raise ValueError("El código postal son 5 dígitos. ¿Me lo repites?")
        return v


DESCANSO_PROMPT = _PREAMBULO + (
    "Esquema descanso (solo entrada por salida): descanso dentro de la "
    "jornada y alimentos.\n"
    "- descanso_tiempo: texto como '1 hora', '30 minutos'. La ley exige al "
    "menos 30 minutos; si dicen menos, pregunta para confirmar.\n"
    "- comidas_incluidas: lista entre 'desayuno','comida','cena' (vacía si no "
    "se incluye ninguna).\n"
)


@register_schema("descanso", DESCANSO_PROMPT)
class Descanso(BaseModel):
    descanso_tiempo: Optional[str] = None
    comidas_incluidas: Optional[list[str]] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None
