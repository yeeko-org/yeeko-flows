"""Textos y cifras derivados de los datos del contrato, sin IA.

Los recaps, el resumen y el PDF imprimen frases armadas de varios extras. Se
calculan aquí, de forma determinista, para que salgan iguales tras la captura
y tras una corrección que solo cambió una parte (siempre se reemplaza una
parte, nunca el registro entero).

Cada unidad de captura engancha los suyos con `register_derivation`: corren
después de guardar, en la primera captura y en cada corrección, con los
extras ya actualizados. Un valor None borra el extra.
"""
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from projects.caceh import tabulador
from services.behavior.extraction import register_derivation

# «Hoy» es el del país de la persona: el servidor corre en UTC y de noche
# una fecha de hoy saldría «posterior al día de hoy».
ZONA_MEXICO = ZoneInfo("America/Mexico_City")

FRASE_PERIODICIDAD = {
    "diaria": "al día",
    "semanal": "a la semana",
    "quincenal": "a la quincena",
    "mensual": "al mes",
}

MESES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

DIAS_SEMANA = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
]

# Semanas promedio por mes (52/12 ≈ 4.333) para prorratear el pago mensual.
# TODO confirmar con CACEH: el spec solo fijó diaria/semanal/quincenal.
SEMANAS_POR_MES = 52 / 12


def hoy_mexico() -> date:
    return datetime.now(ZONA_MEXICO).date()


def lista_natural(items: list) -> str:
    """['a', 'b', 'c'] -> 'a, b y c'."""
    items = [str(i) for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " y " + items[-1]


def frase_periodicidad(periodicidad: Optional[str]) -> Optional[str]:
    return FRASE_PERIODICIDAD.get(periodicidad or "")


def texto_monto(monto) -> Optional[str]:
    """2500 -> '2,500'; los centavos solo si los hay (2500.5 -> '2,500.50')."""
    try:
        valor = float(str(monto).replace(",", ""))
    except (TypeError, ValueError):
        return None
    if valor.is_integer():
        return f"{int(valor):,}"
    return f"{valor:,.2f}"


def texto_hora(hora: Optional[str]) -> Optional[str]:
    """'8:00' -> '8am', '16:00' -> '4pm', '13:30' -> '1:30pm'.

    El formato de la hora en el recap de la jornada sigue sin aprobarse; por
    eso vive solo aquí: cambiarlo es cambiar esta función."""
    if not hora:
        return None
    try:
        t = datetime.strptime(str(hora).strip(), "%H:%M")
    except ValueError:
        return str(hora)
    sufijo = "am" if t.hour < 12 else "pm"
    hora12 = t.hour % 12 or 12
    if t.minute:
        return f"{hora12}:{t.minute:02d}{sufijo}"
    return f"{hora12}{sufijo}"


def texto_jornada(dias, entrada, salida) -> Optional[str]:
    """'lunes, martes y miércoles, de 8am a 4pm'."""
    if not dias or not entrada or not salida:
        return None
    orden = [d for d in DIAS_SEMANA if d in dias]
    return (f"{lista_natural(orden)}, de {texto_hora(entrada)} a "
            f"{texto_hora(salida)}")


def texto_minutos(minutos) -> str:
    """30 -> '30 minutos', 60 -> '1 hora', 90 -> '1 hora y 30 minutos'."""
    try:
        minutos = int(minutos)
    except (TypeError, ValueError):
        return ""
    if minutos <= 0:
        return ""
    horas, resto = divmod(minutos, 60)
    partes = []
    if horas:
        partes.append("1 hora" if horas == 1 else f"{horas} horas")
    if resto:
        partes.append("1 minuto" if resto == 1 else f"{resto} minutos")
    return " y ".join(partes)


def texto_descanso(minutos, comidas) -> Optional[str]:
    """'1 hora, con comida' / '30 minutos, sin alimentos'."""
    tiempo = texto_minutos(minutos)
    if not tiempo:
        return None
    comidas = [c for c in (comidas or []) if c]
    if not comidas:
        return f"{tiempo}, sin alimentos"
    return f"{tiempo}, con {lista_natural(comidas)}"


def texto_domicilio(data: dict) -> Optional[str]:
    """La dirección solo con lo que hay: un opcional ausente no deja hueco
    ni etiqueta suelta («C.P.» sin número)."""
    calle = str(data.get("lt_calle") or "").strip()
    if not calle:
        return None
    primera = calle
    if data.get("lt_ext"):
        primera += f" {data['lt_ext']}"
    if data.get("lt_int"):
        primera += f" int. {data['lt_int']}"
    partes = [primera]
    if data.get("lt_colonia"):
        partes.append(f"col. {data['lt_colonia']}")
    if data.get("lt_cp"):
        partes.append(f"C.P. {data['lt_cp']}")
    for key in ("lt_municipio", "lt_estado"):
        if data.get(key):
            partes.append(str(data[key]))
    return ", ".join(partes)


def parse_fecha(valor) -> Optional[date]:
    if isinstance(valor, date):
        return valor
    try:
        return datetime.strptime(str(valor or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def texto_fecha(valor) -> Optional[str]:
    """'01/05/2015' -> '1 de mayo de 2015' (la forma del recap; el PDF
    dice «del 2015», como lo trae la plantilla)."""
    d = parse_fecha(valor)
    if d is None:
        return None
    return f"{d.day} de {MESES[d.month]} de {d.year}"


def nombre_completo(*partes) -> Optional[str]:
    texto = " ".join(str(p).strip() for p in partes if p and str(p).strip())
    return texto or None


def salario_diario(monto, periodicidad, dias_sem: int) -> Optional[float]:
    """El pago pactado convertido a pago por día, o None si faltan datos:
    toda periodicidad mayor a la diaria necesita los días por semana."""
    try:
        monto = float(monto)
    except (TypeError, ValueError):
        return None
    if periodicidad == "diaria":
        return monto
    if not dias_sem:
        return None
    divisor = {"semanal": dias_sem, "quincenal": dias_sem * 2,
               "mensual": dias_sem * SEMANAS_POR_MES}.get(periodicidad)
    return monto / divisor if divisor else None


def veredicto_tabulador(actividades, diario) -> tuple[float, Optional[bool]]:
    """(salario sugerido, ¿queda bajo?). Sin diario, (sugerido, None)."""
    salarios = [tabulador.SALARIOS[a] for a in (actividades or [])
                if a in tabulador.SALARIOS]
    sugerido = max(salarios) if salarios else tabulador.SALARIO_MINIMO
    try:
        diario = float(diario)
    except (TypeError, ValueError):
        return sugerido, None
    umbral = max(sugerido - tabulador.MARGEN_MXN, tabulador.SALARIO_MINIMO)
    return sugerido, diario < umbral


# --------------------------------------------------- derivados por unidad
def _salario(extras: dict) -> dict:
    """Salario diario y, si ya se eligieron actividades, el veredicto del
    tabulador en silencio: tras una corrección se regresa a lo pendiente,
    no al aviso de D7, que quedaría sin sus botones."""
    dias = extras.get("dias_laborables") or []
    diario = salario_diario(
        extras.get("monto_pago"), extras.get("pago_periodicidad"),
        len(dias))
    out = {"salario_diario": round(diario, 2) if diario is not None
           else None}
    if extras.get("actividades"):
        sugerido, bajo = veredicto_tabulador(
            extras["actividades"], out["salario_diario"])
        out["salario_sugerido"] = f"{sugerido:g}"
        out["salario_bajo"] = "si" if bajo else "no"
    return out


def textos_jornada(extras: dict) -> dict:
    return {"jornada_texto": texto_jornada(
        extras.get("dias_laborables"), extras.get("hora_entrada"),
        extras.get("hora_salida"))}


def textos_pago(extras: dict) -> dict:
    return {
        "frase_periodicidad": frase_periodicidad(
            extras.get("pago_periodicidad")),
        "monto_texto": texto_monto(extras.get("monto_pago")),
    }


def textos_descanso(extras: dict) -> dict:
    # Solo aplica en entrada por salida: un descanso capturado antes de
    # cambiar a planta (un botón viejo de §A) no debe llegar al resumen.
    if extras.get("tipo_contrato") != "entrada_salida":
        return {"descanso_texto": None}
    return {"descanso_texto": texto_descanso(
        extras.get("descanso_minutos"), extras.get("comidas_incluidas"))}


def textos_domicilio(extras: dict) -> dict:
    return {"lt_texto": texto_domicilio(extras)}


def textos_fecha(extras: dict) -> dict:
    # Solo en un contrato retroactivo, igual que la SEGUNDA del PDF.
    if extras.get("es_retroactivo") != "si":
        return {"fecha_inicio_texto": None}
    return {"fecha_inicio_texto": texto_fecha(extras.get("fecha_inicio"))}


# Lo que corrige_por_ia (E4) recalcula tras escribir: los mismos textos que
# imprimen los recaps y el resumen.
TEXTOS = (textos_jornada, textos_pago, textos_descanso, textos_domicilio,
          textos_fecha)


@register_derivation("jornada")
def deriva_jornada(response, extras: dict) -> dict:
    return {**textos_jornada(extras), **_salario(extras)}


@register_derivation("pago")
def deriva_pago(response, extras: dict) -> dict:
    return {**textos_pago(extras), **_salario(extras)}


@register_derivation("descanso")
def deriva_descanso(response, extras: dict) -> dict:
    return textos_descanso(extras)


@register_derivation("domicilio")
def deriva_domicilio(response, extras: dict) -> dict:
    return textos_domicilio(extras)


@register_derivation("fecha")
def deriva_fecha(response, extras: dict) -> dict:
    return textos_fecha(extras)


@register_derivation("nombre_operador")
def deriva_nombre_operador(response, extras: dict) -> dict:
    return {"operador_nombre": nombre_completo(
        extras.get("operador_nombre_pila"),
        extras.get("operador_apellido_paterno"),
        extras.get("operador_apellido_materno"))}


@register_derivation("nombre_contraparte")
def deriva_nombre_contraparte(response, extras: dict) -> dict:
    return {"contraparte_nombre": nombre_completo(
        extras.get("contraparte_nombre_pila"),
        extras.get("contraparte_apellido_paterno"),
        extras.get("contraparte_apellido_materno"))}
