"""Tests de los behaviors deterministas del slice CACEH (WP5): asigna_partes y
calcula_salario_diario. Sin red ni IA.

Correr: .venv/bin/python manage.py test projects.caceh
"""

from types import SimpleNamespace

from django.test import TestCase

from infrastructure.member.factories import MemberFactory
from infrastructure.place.factories import AccountFactory, SpaceFactory
from infrastructure.xtra.factories import ClassifyExtraFactory, ExtraFactory
from infrastructure.xtra.models import Format

from projects.caceh.behaviors.asigna_partes import AsignaPartesBehavior
from projects.caceh.behaviors.calcula_salario_diario import (
    CalculaSalarioDiarioBehavior,
)
from projects.caceh.behaviors.registra_contrato import RegistraContratoBehavior
from projects.caceh.behaviors.valida_fecha_pasada import (
    ValidaFechaPasadaBehavior,
)
from projects.caceh.models import Contract


class StubResponse:
    """Response mínimo: delega add_extra_value en el member y junta errores,
    sin tocar la maquinaria de notificaciones del ResponseAbc real."""

    def __init__(self, member, space, account=None):
        self.sender = SimpleNamespace(
            member=member,
            account=account or SimpleNamespace(space=space))
        self.errors = []
        self.media_messages = []

    def message_multimedia(self, **kwargs):
        self.media_messages.append(kwargs)

    def add_extra_value(
            self, extra, value=None, interaction=None,
            origin="unknown", list_by=None):
        return self.sender.member.add_extra_value(
            extra, value, interaction, origin, list_by)

    def add_error(self, data, e=None):
        self.errors.append(data)


class CacehBehaviorTestBase(TestCase):
    def setUp(self):
        self.space = SpaceFactory()
        self.member = MemberFactory(space=self.space)
        self.response = StubResponse(self.member, self.space)
        self.classify = ClassifyExtraFactory()
        self.fmt_json, _ = Format.objects.get_or_create(name="json")
        self.fmt_int, _ = Format.objects.get_or_create(name="int")
        self.extras = {}

    def _extra(self, name, fmt=None):
        extra = ExtraFactory(
            name=name, space=self.space, classify=self.classify,
            format=fmt, flow=None, deleted=False)
        self.extras[name] = extra
        return extra

    def _set(self, name, value, fmt=None):
        extra = self.extras.get(name) or self._extra(name, fmt)
        self.member.add_extra_value(extra, value, None, "test", None)

    def _data(self):
        return self.member.get_extra_values_data(refrest=True)


class AsignaPartesTestCase(CacehBehaviorTestBase):
    def setUp(self):
        super().setUp()
        for name in ("operador", "operador_nombre", "contraparte_nombre",
                     "trab_nombre_completo", "empl_nombre_completo",
                     "telefono_operador"):
            self._extra(name)
        self.member.user.phone = "5215551234567"
        self.member.user.save()

    def test_operador_trabajadora_reparte_y_fija_telefono(self):
        self._set("operador", "trabajadora")
        self._set("operador_nombre", "Juana Pérez López")
        self._set("contraparte_nombre", "Marcela Ruiz Soto")

        AsignaPartesBehavior(self.response)

        data = self._data()
        self.assertEqual(data["trab_nombre_completo"], "Juana Pérez López")
        self.assertEqual(data["empl_nombre_completo"], "Marcela Ruiz Soto")
        self.assertEqual(data["telefono_operador"], "5215551234567")
        self.assertEqual(self.response.errors, [])

    def test_operador_empleadora_invierte_los_nombres(self):
        self._set("operador", "empleadora")
        self._set("operador_nombre", "Marcela Ruiz Soto")
        self._set("contraparte_nombre", "Juana Pérez López")

        AsignaPartesBehavior(self.response)

        data = self._data()
        self.assertEqual(data["trab_nombre_completo"], "Juana Pérez López")
        self.assertEqual(data["empl_nombre_completo"], "Marcela Ruiz Soto")

    def test_operador_invalido_agrega_error_y_no_escribe(self):
        self._set("operador", "")
        self._set("operador_nombre", "Quien Sea")
        self._set("contraparte_nombre", "Otra Persona")

        AsignaPartesBehavior(self.response)

        data = self._data()
        self.assertIsNone(data.get("trab_nombre_completo"))
        self.assertTrue(
            any(e.get("message", "").startswith("operador inválido")
                for e in self.response.errors))


class CalculaSalarioDiarioTestCase(CacehBehaviorTestBase):
    def setUp(self):
        super().setUp()
        self._extra("monto_pago", self.fmt_int)
        self._extra("pago_periodicidad")
        self._extra("dias_laborables", self.fmt_json)
        self._extra("salario_diario")
        self.cinco_dias = ["lunes", "martes", "miércoles", "jueves", "viernes"]

    def _run(self, monto=None, periodicidad=None, dias=None):
        if monto is not None:
            self._set("monto_pago", monto)
        if periodicidad is not None:
            self._set("pago_periodicidad", periodicidad)
        if dias is not None:
            self._set("dias_laborables", dias)
        CalculaSalarioDiarioBehavior(self.response)
        return self._data()

    def test_diaria_es_el_mismo_monto(self):
        data = self._run(monto=350, periodicidad="diaria", dias=self.cinco_dias)
        self.assertEqual(float(data["salario_diario"]), 350.0)
        self.assertEqual(self.response.errors, [])

    def test_semanal_divide_entre_dias_por_semana(self):
        data = self._run(
            monto=1750, periodicidad="semanal", dias=self.cinco_dias)
        self.assertEqual(float(data["salario_diario"]), 350.0)

    def test_quincenal_divide_entre_el_doble_de_dias(self):
        data = self._run(
            monto=3500, periodicidad="quincenal", dias=self.cinco_dias)
        self.assertEqual(float(data["salario_diario"]), 350.0)

    def test_mensual_prorratea_con_semanas_por_mes(self):
        data = self._run(
            monto=7000, periodicidad="mensual", dias=self.cinco_dias)
        # 7000 / (5 * 52/12) ≈ 323.08
        self.assertAlmostEqual(float(data["salario_diario"]), 323.08, places=1)

    def test_no_diaria_sin_dias_agrega_error(self):
        data = self._run(monto=1750, periodicidad="semanal", dias=[])
        self.assertIsNone(data.get("salario_diario"))
        self.assertTrue(
            any("prorratear" in e.get("message", "")
                for e in self.response.errors))

    def test_falta_monto_agrega_error(self):
        data = self._run(periodicidad="diaria", dias=self.cinco_dias)
        self.assertIsNone(data.get("salario_diario"))
        self.assertTrue(self.response.errors)


class RegistraContratoTestCase(CacehBehaviorTestBase):
    def setUp(self):
        super().setUp()
        # account real para el FK del Contract; comparte el space del miembro
        # para que los _write encuentren los Extra.
        self.account = AccountFactory(space=self.space)
        self.response = StubResponse(
            self.member, self.space, account=self.account)
        for name in ("tipo_contrato", "trab_nombre_completo",
                     "empl_nombre_completo", "registro_id",
                     "flujo_completado"):
            self._extra(name)
        self._set("tipo_contrato", "planta")
        self._set("trab_nombre_completo", "Juana Pérez López")
        self._set("empl_nombre_completo", "Marcela Ruiz Soto")

    def test_crea_contrato_con_snapshot_y_cierra_flujo(self):
        RegistraContratoBehavior(self.response)

        contract = Contract.objects.get()
        self.assertEqual(contract.member, self.member)
        self.assertEqual(contract.account, self.account)
        self.assertEqual(contract.tipo_contrato, "planta")
        self.assertEqual(contract.trab_nombre, "Juana Pérez López")
        self.assertEqual(contract.empl_nombre, "Marcela Ruiz Soto")
        # el snapshot incluye los extras capturados (la constancia)
        self.assertEqual(contract.data["tipo_contrato"], "planta")
        self.assertEqual(self.response.errors, [])

    def test_folio_formato_canonico(self):
        RegistraContratoBehavior(self.response)

        contract = Contract.objects.get()
        fecha = contract.created_at.strftime("%Y%m%d")
        self.assertEqual(
            contract.folio, f"CACEH-{fecha}-{contract.pk:05d}")

    def test_escribe_registro_id_y_flujo_completado(self):
        RegistraContratoBehavior(self.response)

        contract = Contract.objects.get()
        data = self._data()
        self.assertEqual(data["registro_id"], contract.folio)
        self.assertEqual(data["flujo_completado"], "completo")

    def test_falta_dato_obligatorio_no_crea_contrato(self):
        self._set("tipo_contrato", "")
        RegistraContratoBehavior(self.response)

        self.assertFalse(Contract.objects.exists())
        self.assertTrue(self.response.errors)


class ValidaFechaPasadaTestCase(CacehBehaviorTestBase):
    def setUp(self):
        super().setUp()
        for name in ("fecha_inicio", "fecha_valida", "fecha_error"):
            self._extra(name)

    def _run(self, fecha):
        self._set("fecha_inicio", fecha)
        ValidaFechaPasadaBehavior(self.response)
        return self._data()

    def test_fecha_pasada_completa_valida_y_normaliza(self):
        data = self._run("15/03/2023")
        self.assertEqual(data["fecha_valida"], "si")
        self.assertEqual(data["fecha_inicio"], "15/03/2023")
        self.assertEqual(self.response.errors, [])

    def test_solo_mes_y_anio_asume_dia_uno(self):
        data = self._run("03/2023")
        self.assertEqual(data["fecha_valida"], "si")
        self.assertEqual(data["fecha_inicio"], "01/03/2023")

    def test_formato_iso_se_normaliza(self):
        data = self._run("2023-03-15")
        self.assertEqual(data["fecha_valida"], "si")
        self.assertEqual(data["fecha_inicio"], "15/03/2023")

    def test_fecha_futura_se_rechaza(self):
        data = self._run("01/01/2999")
        self.assertEqual(data["fecha_valida"], "no")
        self.assertTrue(data["fecha_error"])

    def test_texto_no_parseable_se_rechaza(self):
        data = self._run("el año pasado")
        self.assertEqual(data["fecha_valida"], "no")
        self.assertTrue(data["fecha_error"])
