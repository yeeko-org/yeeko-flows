"""Esquemas Pydantic de extracción del bot CACEH (slice del demo).

Cada esquema declara los datos a extraer + los campos de control del loop
(`ia_completed`, `ia_pregunta`) y se registra con @register_schema para que la
unidad de captura `open_question` lo encuentre por nombre. Los nombres de los
campos coinciden 1:1 con las claves de los `Extra` del flujo (ver
flows/variables_v3.md). Un `ValueError` de un validador es la repregunta que
la persona lee, tal cual.
"""

from datetime import date
from typing import ClassVar, Literal, Optional

from pydantic import BaseModel, field_validator, model_validator

from projects.caceh.derivados import (
    frase_periodicidad, hoy_mexico, lista_natural)
from services.behavior.extraction import register_schema


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
            self.frase_periodicidad = frase_periodicidad(
                self.pago_periodicidad)
        return self


DOMICILIO_PROMPT = _PREAMBULO + (
    "Esquema domicilio: dirección del lugar de trabajo en México.\n"
    "- Campos: lt_calle, lt_ext (número exterior), lt_int (interior), "
    "lt_colonia, lt_cp (5 dígitos), lt_municipio (alcaldía o municipio), "
    "lt_estado.\n"
    "- lt_ext acepta lo que la persona diga: un número, manzana y lote "
    "('Mz 3 Lt 12') o, si dice que no tiene número ('sin número', 's/n'), "
    "'S/N'.\n"
    "- Si algo no viene, déjalo en null; no lo inventes.\n"
    "- lt_estado: si no viene, dedúcelo de la alcaldía, el municipio o la "
    "colonia SOLO si estás seguro (p. ej. Iztacalco -> 'Ciudad de "
    "México'); si no estás seguro, déjalo en null.\n"
    "- ia_pregunta: déjalo vacío; la pregunta de lo que falta la arma el "
    "sistema.\n"
    "- ciudad_firma: derivado, NO lo preguntes. Cópialo de lt_municipio "
    "(donde se trabaja se firma); el usuario lo corrige luego en el resumen.\n"
)

# Lo que una repregunta lista, en el orden de la pregunta. El código postal
# entra en la lista cuando falta otra cosa, pero nunca la dispara solo; el
# número y el estado sí, aunque sean lo único que falte.
_DOMICILIO_ETIQUETAS = (
    ("lt_calle", "calle"), ("lt_ext", "número"), ("lt_colonia", "colonia"),
    ("lt_municipio", "municipio o alcaldía"), ("lt_estado", "estado"),
    ("lt_cp", "código postal"))
_DOMICILIO_ESENCIALES = (
    "lt_calle", "lt_ext", "lt_colonia", "lt_municipio", "lt_estado")
REPREGUNTA_DOMICILIO = (
    "Para poder continuar, ayúdame con estos otros datos de la dirección: "
    "{faltan}")


def _cp_valido(v):
    if v and (not v.isdigit() or len(v) != 5):
        raise ValueError("El código postal son 5 dígitos. ¿Me lo repites?")
    return v


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
        # El código postal no se repregunta: uno mal escrito se descarta en
        # lugar de detener la dirección entera.
        try:
            return _cp_valido(v)
        except ValueError:
            return None

    @model_validator(mode="after")
    def completitud_determinista(self):
        # Qué es obligatorio lo decide CACEH, no el modelo: el veredicto de
        # Gemini se reemplaza y la repregunta se arma aquí.
        if all(getattr(self, k) for k in _DOMICILIO_ESENCIALES):
            self.ia_completed = "si"
            self.ia_pregunta = None
            return self
        faltan = [label for key, label in _DOMICILIO_ETIQUETAS
                  if not getattr(self, key)]
        self.ia_completed = "no"
        self.ia_pregunta = REPREGUNTA_DOMICILIO.format(
            faltan=lista_natural(faltan))
        return self


DESCANSO_PROMPT = _PREAMBULO + (
    "Esquema descanso (solo entrada por salida): descanso dentro de la "
    "jornada y alimentos.\n"
    "- descanso_minutos: número entero de MINUTOS. Convierte lo que digan "
    "('1 hora' -> 60, 'media hora' -> 30, 'hora y media' -> 90). La ley "
    "exige al menos 30 minutos.\n"
    "- comidas_incluidas: lista entre 'desayuno','comida','cena' (vacía si no "
    "se incluye ninguna). Si no dice nada de los alimentos, déjalo en null "
    "y pregunta si se incluye alguno.\n"
)

DESCANSO_MINIMO = (
    "La ley pide que el descanso dure al menos 30 minutos. Por favor, "
    "escribe cuánto tiempo de descanso habrá.")


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
            raise ValueError(DESCANSO_MINIMO)
        return v


FECHA_PROMPT = _PREAMBULO + (
    "Esquema fecha: la fecha en que empezó este trabajo (inicio de la "
    "relación de trabajo).\n"
    "- fecha_dia (opcional), fecha_mes (1 a 12) y fecha_anio (cuatro "
    "dígitos). Acepta cualquier forma: 'mayo de 2015', '05 2015', "
    "'15/03/23' (año de dos dígitos: 23 -> 2023). Las fechas con números "
    "van en orden día/mes/año, como en México; dos números sin día son mes "
    "y año ('05 2015' = mayo de 2015).\n"
    "- Si no da el día, deja fecha_dia en null: con mes y año basta.\n"
    "- Si la fecha es clara, no pidas confirmación.\n"
    "- Si falta el mes o el año, o la fecha es relativa ('hace dos años', "
    "'el año pasado'), pon ia_completed='no' y pregunta el mes y el año.\n"
    "- No juzgues si la fecha ya pasó ni si existe: eso lo revisa el "
    "sistema. Copia los números tal como los entiendas.\n"
    "- fecha_inicio: déjalo vacío; lo arma el sistema.\n"
)

# Las dos únicas repreguntas propias de la fecha.
FECHA_FUTURA = (
    "La fecha que escribiste es posterior al día de hoy. Por favor, escribe "
    "la fecha en que empezó este trabajo.")
FECHA_INEXISTENTE = (
    "No encontré esa fecha en el calendario. Por favor, escríbela de nuevo.")
# Un año de dos dígitos que se cuele (23) sería el año 0023: no es una fecha
# del calendario de nadie que trabaje hoy.
_ANIO_MINIMO = 1900


@register_schema("fecha", FECHA_PROMPT)
class Fecha(BaseModel):
    fecha_dia: Optional[int] = None
    fecha_mes: Optional[int] = None
    fecha_anio: Optional[int] = None
    # 'dd/mm/YYYY', con el día 1 si solo hay mes y año: la forma que
    # genera_pdf y el recap saben leer.
    fecha_inicio: Optional[str] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None

    @field_validator("fecha_anio")
    @classmethod
    def anio_completo(cls, v):
        if v is not None and v < _ANIO_MINIMO:
            raise ValueError(FECHA_INEXISTENTE)
        return v

    @field_validator("fecha_mes")
    @classmethod
    def mes_valido(cls, v):
        if v is not None and not 1 <= v <= 12:
            raise ValueError(FECHA_INEXISTENTE)
        return v

    @model_validator(mode="after")
    def compone(self):
        if not (self.fecha_mes and self.fecha_anio):
            self.fecha_inicio = None
            if self.ia_completed == "si":
                self.ia_completed = "no"
            return self
        try:
            inicio = date(self.fecha_anio, self.fecha_mes,
                          self.fecha_dia or 1)
        except ValueError:
            raise ValueError(FECHA_INEXISTENTE)
        if inicio > hoy_mexico():
            raise ValueError(FECHA_FUTURA)
        self.fecha_inicio = inicio.strftime("%d/%m/%Y")
        return self


def _nombre_prompt(quien: str) -> str:
    return _PREAMBULO + (
        f"Esquema nombre: el nombre completo de {quien}.\n"
        "- Separa el nombre de pila (puede ser compuesto: 'María José') del "
        "apellido paterno y el materno. Respeta mayúsculas y acentos tal "
        "como los escriba.\n"
        "- Si solo escribe un apellido, deja el otro en null; no lo "
        "inventes.\n"
        "- ia_pregunta: déjalo vacío; la pregunta la arma el sistema.\n"
    )


def _completitud_nombre(modelo, prefijo: str, repregunta: str):
    """Pide los dos apellidos cuando falta alguno. La unidad insiste una
    sola vez (max_reasks=1) y, por `never_drop`, acepta lo que haya a la
    segunda: hay personas con un solo apellido."""
    pila = getattr(modelo, f"{prefijo}_nombre_pila")
    paterno = getattr(modelo, f"{prefijo}_apellido_paterno")
    materno = getattr(modelo, f"{prefijo}_apellido_materno")
    if pila and paterno and materno:
        modelo.ia_completed = "si"
        modelo.ia_pregunta = None
    elif pila:
        modelo.ia_completed = "no"
        modelo.ia_pregunta = repregunta
    else:
        modelo.ia_completed = "no"
        modelo.ia_pregunta = None
    return modelo


APELLIDOS_OPERADOR = "Por favor, escribe también tus dos apellidos."
# {{etiqueta_contraparte}} lo rinde el motor al mandar el mensaje.
APELLIDOS_CONTRAPARTE = (
    "Por favor, escribe también los dos apellidos de la persona "
    "{{etiqueta_contraparte}}.")


@register_schema("nombre_operador",
                 _nombre_prompt("la persona que escribe"))
class NombreOperador(BaseModel):
    never_drop: ClassVar[bool] = True
    operador_nombre_pila: Optional[str] = None
    operador_apellido_paterno: Optional[str] = None
    operador_apellido_materno: Optional[str] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None

    @model_validator(mode="after")
    def completitud(self):
        return _completitud_nombre(self, "operador", APELLIDOS_OPERADOR)


@register_schema("nombre_contraparte",
                 _nombre_prompt("la otra persona del contrato"))
class NombreContraparte(BaseModel):
    never_drop: ClassVar[bool] = True
    contraparte_nombre_pila: Optional[str] = None
    contraparte_apellido_paterno: Optional[str] = None
    contraparte_apellido_materno: Optional[str] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None

    @model_validator(mode="after")
    def completitud(self):
        return _completitud_nombre(
            self, "contraparte", APELLIDOS_CONTRAPARTE)


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
    "- Fecha en que empezó el trabajo: fecha_dia (opcional), fecha_mes (1 a "
    "12) y fecha_anio (cuatro dígitos; 23 -> 2023), solo si es_retroactivo "
    "es 'si'. Pon solo las partes que la persona cambia. Las fechas con "
    "números van en orden día/mes/año, como en México. No juzgues si la "
    "fecha ya pasó ni si existe: eso lo revisa el sistema.\n"
    "- tipo_contrato NO se corrige aquí, ni la fecha de inicio si "
    "es_retroactivo no es 'si': si es lo único que pide, pon "
    "ia_completed='no' y explica en ia_pregunta que eso se cambia con "
    "«Crear otro contrato» al final, y pregunta si hay algo más que "
    "corregir.\n"
)


@register_schema("correccion", CORRECCION_PROMPT)
class Correccion(BaseModel):
    """Todos los corregibles del resumen (E4), opcionales: None = «no cambia»
    y el behavior lo salta. Los Literal/validadores son los mismos de los
    esquemas de origen para que una corrección no pueda meter un valor que la
    captura original hubiera rechazado. La fecha se valida aparte, con el
    esquema Fecha, porque una parte corregida solo se juzga junto con las
    guardadas."""
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
    fecha_dia: Optional[int] = None
    fecha_mes: Optional[int] = None
    fecha_anio: Optional[int] = None
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
        # Aquí sí se repregunta: es una corrección pedida por la persona.
        return _cp_valido(v)

    @field_validator("descanso_minutos")
    @classmethod
    def minimo_treinta(cls, v):
        return Descanso.minimo_treinta(v)
