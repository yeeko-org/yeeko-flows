"""Esquemas Pydantic de extracción del bot CACEH (slice del demo).

Cada esquema declara los datos a extraer + los campos de control del loop
(`ia_completed`, `ia_pregunta`) y se registra con @register_schema para que el
behavior genérico `ia_extrae` lo encuentre por nombre. Los nombres de los
campos coinciden 1:1 con las claves de los `Extra` del flujo (ver
flows/variables_v3.md).
"""

from typing import Literal, Optional

from pydantic import BaseModel, field_validator, model_validator

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

# El PDF compara los días por texto exacto y con acento: un «miercoles» pelón
# deja la casilla de la SÉPTIMA vacía y encima cuenta como día de descanso en
# la OCTAVA. Como Literal viaja a Gemini como enum dentro del
# response_json_schema, el catálogo se impone en la generación, no después.
DiaSemana = Literal[
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


@register_schema("jornada", JORNADA_PROMPT)
class Jornada(BaseModel):
    hora_entrada: Optional[str] = None
    hora_salida: Optional[str] = None
    dias_laborables: Optional[list[DiaSemana]] = None
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


_FRASE_PERIODICIDAD = {
    "diaria": "al día",
    "semanal": "a la semana",
    "quincenal": "a la quincena",
    "mensual": "al mes",
}


@register_schema("pago", PAGO_PROMPT)
class Pago(BaseModel):
    monto_pago: Optional[int] = None
    pago_periodicidad: Optional[
        Literal["diaria", "semanal", "quincenal", "mensual"]] = None
    # Derivado determinista para el texto de confirmación ("$550 a la semana").
    # NO lo pide Gemini; lo calculamos de pago_periodicidad tras validar.
    frase_periodicidad: Optional[str] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None

    @model_validator(mode="after")
    def set_frase_periodicidad(self):
        if self.pago_periodicidad:
            self.frase_periodicidad = _FRASE_PERIODICIDAD[
                self.pago_periodicidad]
        return self


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
    "- descanso_minutos: número entero de MINUTOS. Convierte lo que digan "
    "('1 hora' -> 60, 'media hora' -> 30, 'hora y media' -> 90). La ley "
    "exige al menos 30 minutos.\n"
    "- comidas_incluidas: lista entre 'desayuno','comida','cena' (vacía si no "
    "se incluye ninguna).\n"
)


# La OCTAVA de entrada por salida marca las casillas comparando estos tres
# textos exactos; cualquier sinónimo («almuerzo») saldría sin marcar.
Comida = Literal["desayuno", "comida", "cena"]


@register_schema("descanso", DESCANSO_PROMPT)
class Descanso(BaseModel):
    descanso_minutos: Optional[int] = None
    comidas_incluidas: Optional[list[Comida]] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None

    @field_validator("descanso_minutos")
    @classmethod
    def minimo_treinta(cls, v):
        # LFT art. 63: media hora mínima de reposo en jornada continua.
        if v is not None and v < 30:
            raise ValueError(
                "Por ley el descanso debe ser de al menos 30 minutos. "
                "¿Cuánto tiempo de descanso tendrá?")
        return v


CORRECCION_PROMPT = (
    "Eres el asistente de CACEH que arma contratos de trabajo del hogar en "
    "México. La persona ya vio el resumen de su contrato y escribió con sus "
    "palabras qué está mal (puede venir en varias líneas, una por cada vez "
    "que respondió). Recibes el ESTADO ACTUAL en JSON y su texto; devuelve "
    "SOLO el JSON del esquema con los campos que cambian.\n"
    "Reglas:\n"
    "- Deja en null todo campo que la persona NO pidió cambiar. Nunca "
    "repitas el valor actual ni inventes datos.\n"
    "- Si identificaste al menos un cambio claro, pon ia_completed='si' y "
    "deja ia_pregunta vacío.\n"
    "- Si no entiendes qué quiere cambiar, o dice qué está mal pero no cómo "
    "debe quedar, pon ia_completed='no' y escribe en ia_pregunta UNA sola "
    "pregunta corta, amable y en español sencillo.\n"
    "- Salario: lo pactado es monto_pago (entero en pesos, sin comas) más "
    "pago_periodicidad ('diaria','semanal','quincenal','mensual'). Si la "
    "persona da solo un monto sin periodo, cambia solo monto_pago y deja "
    "pago_periodicidad en null: se conserva la guardada, no preguntes. "
    "salario_diario es solo contexto, no se corrige; se recalcula.\n"
    "- modo_pago: 'efectivo' o 'transferencia'.\n"
    "- hora_entrada y hora_salida en formato '8:00' / '16:00'. "
    "dias_laborables: lista completa de días en minúscula y con acento "
    "('lunes','miércoles','sábado'); máximo 6.\n"
    "- Domicilio: lt_calle, lt_ext, lt_int, lt_colonia, lt_cp (5 dígitos), "
    "lt_municipio (alcaldía o municipio), lt_estado. ciudad_firma es donde "
    "se firma: si cambia lt_municipio, pon ciudad_firma igual al nuevo "
    "municipio, salvo que la persona diga otra ciudad de firma.\n"
    "- descanso_minutos (entero, mínimo 30) y comidas_incluidas "
    "('desayuno','comida','cena') solo existen en tipo_contrato "
    "'entrada_salida'.\n"
    "- Si la persona quiere cambiar las actividades o tareas del trabajo, "
    "pon cambiar_actividades='si' (no las escribas tú: se le vuelve a "
    "mandar la lista) e ia_completed='si'.\n"
    "- tipo_contrato y la fecha de inicio NO se corrigen aquí: si es lo "
    "único que pide, pon ia_completed='no' y explica en ia_pregunta que eso "
    "se cambia con «Hacer otro contrato» al final, y pregunta si hay algo "
    "más que corregir.\n"
)


@register_schema("correccion", CORRECCION_PROMPT)
class Correccion(BaseModel):
    """Todos los corregibles del resumen (E4), opcionales: None = «no cambia»
    y el behavior lo salta. Los Literal/validadores son los mismos de los
    esquemas de origen para que una corrección no pueda meter un valor que la
    captura original hubiera rechazado."""
    trab_nombre_completo: Optional[str] = None
    empl_nombre_completo: Optional[str] = None
    hora_entrada: Optional[str] = None
    hora_salida: Optional[str] = None
    dias_laborables: Optional[list[DiaSemana]] = None
    lt_calle: Optional[str] = None
    lt_ext: Optional[str] = None
    lt_int: Optional[str] = None
    lt_colonia: Optional[str] = None
    lt_cp: Optional[str] = None
    lt_municipio: Optional[str] = None
    lt_estado: Optional[str] = None
    ciudad_firma: Optional[str] = None
    monto_pago: Optional[int] = None
    pago_periodicidad: Optional[
        Literal["diaria", "semanal", "quincenal", "mensual"]] = None
    modo_pago: Optional[Literal["efectivo", "transferencia"]] = None
    descanso_minutos: Optional[int] = None
    comidas_incluidas: Optional[list[Comida]] = None
    # Las actividades no se corrigen por texto: «si» reabre el Flow (D1).
    cambiar_actividades: Literal["si", "no"] = "no"
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None

    # Mismos validadores que los esquemas de origen (misma repregunta).
    @field_validator("dias_laborables")
    @classmethod
    def max_seis_dias(cls, v):
        return Jornada.max_seis_dias(v)

    @field_validator("lt_cp")
    @classmethod
    def cp_cinco_digitos(cls, v):
        return Domicilio.cp_cinco_digitos(v)

    @field_validator("descanso_minutos")
    @classmethod
    def minimo_treinta(cls, v):
        return Descanso.minimo_treinta(v)
