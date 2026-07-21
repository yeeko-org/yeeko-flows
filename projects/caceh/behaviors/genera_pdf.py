"""genera_pdf — arma el PDF del contrato planta y lo deja como Media (pieza E5).

Construye el dict de datos desde los extras del miembro, lo renderiza con
render_planta y crea un Media (que al guardarse se auto-sube a WhatsApp). Escribe
{{pdf_contrato}} con el pk del Media para que entrega_pdf lo recupere.
"""
from datetime import date, datetime

from django.core.files.base import ContentFile

from infrastructure.persistent_media.models import Media
from projects.caceh.behaviors.base import CacehBehaviorBase
from projects.caceh.pdf import render_entrada_salida, render_planta

_MESES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

_DIAS_SEMANA = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
]


def _dias_descanso(dias_laborables: list) -> str:
    """Días de la semana no laborables, como texto ('sábado y domingo').
    Vacío si no hay días capturados (la plantilla imprime la línea en
    blanco para llenar a mano)."""
    if not dias_laborables:
        return ""
    libres = [d for d in _DIAS_SEMANA if d not in dias_laborables]
    if not libres:
        return ""
    if len(libres) == 1:
        return libres[0]
    return ", ".join(libres[:-1]) + " y " + libres[-1]


def _fecha_partes(valor) -> tuple[str, str, str]:
    """(día, mes en palabra, año) de un date o texto 'd/m/Y'. Si no se puede
    parsear, cae a hoy (el inicio retroactivo está fuera del slice)."""
    d = None
    if isinstance(valor, date):
        d = valor
    elif isinstance(valor, str) and valor.strip():
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                d = datetime.strptime(valor.strip(), fmt).date()
                break
            except ValueError:
                continue
    d = d or date.today()
    return str(d.day), _MESES[d.month], str(d.year)


class GeneraPdfBehavior(CacehBehaviorBase):
    behavior_name = "genera_pdf"

    def run(self) -> None:
        datos = self._build_datos()
        if self._read("tipo_contrato") == "entrada_salida":
            pdf = render_entrada_salida(datos)
        else:
            pdf = render_planta(datos)

        media = Media(
            account=self.account,
            file=ContentFile(pdf, name="contrato.pdf"),
            media_type="document",
        )
        media.save()

        self._write("pdf_contrato", media.pk)

    def _build_datos(self) -> dict:
        hoy_dia, hoy_mes, hoy_anio = _fecha_partes(date.today())
        if self._read("es_retroactivo") == "si":
            ini_dia, ini_mes, ini_anio = _fecha_partes(
                self._read("fecha_inicio"))
        else:
            ini_dia, ini_mes, ini_anio = hoy_dia, hoy_mes, hoy_anio

        return {
            "empl_nombre": self._read("empl_nombre_completo", ""),
            "trab_nombre": self._read("trab_nombre_completo", ""),
            # Domicilio del lugar de trabajo = domicilio de la empleadora
            # (declaración II.B y TERCERA).
            "lt_calle": self._read("lt_calle", ""),
            "lt_ext": self._read("lt_ext", ""),
            "lt_int": self._read("lt_int", ""),
            "lt_colonia": self._read("lt_colonia", ""),
            "lt_cp": self._read("lt_cp", ""),
            "lt_municipio": self._read("lt_municipio", ""),
            "lt_estado": self._read("lt_estado", ""),
            "inicio_dia": ini_dia,
            "inicio_mes": ini_mes,
            "inicio_anio": ini_anio,
            "actividades": self._read("actividades") or [],
            "actividad_otra": self._read("actividad_otra", ""),
            "periodicidad": self._read("pago_periodicidad", ""),
            "salario_diario": self._read("salario_diario", ""),
            "modo_pago": self._read("modo_pago", ""),
            "hora_entrada": self._read("hora_entrada", ""),
            "hora_salida": self._read("hora_salida", ""),
            "dias": self._read("dias_laborables") or [],
            # OCTAVA de planta (versión 2026): días de descanso convenidos,
            # derivados como complemento de los laborables (el flujo no
            # pregunta horarios de descanso en planta).
            "dias_descanso": _dias_descanso(
                self._read("dias_laborables") or []),
            # Descanso: solo lo captura entrada por salida (OCTAVA); en planta
            # estos quedan vacíos.
            "descanso_tiempo": self._read("descanso_tiempo", ""),
            "comidas_incluidas": self._read("comidas_incluidas") or [],
            "ciudad_firma": self._read(
                "ciudad_firma", self._read("lt_municipio", "")),
            "firma_dia": hoy_dia,
            "firma_mes": hoy_mes,
            "firma_anio": hoy_anio,
        }
