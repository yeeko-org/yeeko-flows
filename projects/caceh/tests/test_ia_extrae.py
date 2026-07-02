"""Tests del behavior genérico ia_extrae con Gemini mockeado, usando los
esquemas del slice CACEH. Un smoke test real queda gated por GEMINI_API_KEY.

Correr: .venv/bin/python manage.py test projects.caceh
"""

from types import SimpleNamespace
from unittest import skipUnless

from django.conf import settings
from django.test import TestCase

from infrastructure.member.factories import MemberFactory
from infrastructure.place.factories import SpaceFactory
from infrastructure.xtra.factories import ClassifyExtraFactory, ExtraFactory
from infrastructure.xtra.models import Format

from services.behavior.ia_extrae import IaExtraeBehavior
from projects.caceh import schemas  # noqa: F401 — puebla el registro


class FakeGemini:
    """Cliente Gemini de prueba: devuelve un dict fijo y captura el texto que
    recibió (para verificar la acumulación de historial)."""

    def __init__(self, result):
        self.result = result
        self.errors = []
        self.last_user_text = None

    def extract(self, system_prompt, user_text, schema):
        self.last_user_text = user_text
        return self.result


class StubResponse:
    """Response mínimo: delega add_extra_value en el member y junta errores,
    sin tocar la maquinaria de notificaciones del ResponseAbc real."""

    def __init__(self, member, space):
        self.sender = SimpleNamespace(
            member=member, account=SimpleNamespace(space=space))
        self.errors = []

    def add_extra_value(
            self, extra, value=None, interaction=None,
            origin="unknown", list_by=None):
        return self.sender.member.add_extra_value(
            extra, value, interaction, origin, list_by)

    def add_error(self, data, e=None):
        self.errors.append(data)


class IaExtraeTestCase(TestCase):
    def setUp(self):
        self.space = SpaceFactory()
        self.member = MemberFactory(space=self.space)
        self.response = StubResponse(self.member, self.space)
        self.classify = ClassifyExtraFactory()
        self.fmt_json, _ = Format.objects.get_or_create(name="json")
        self.fmt_int, _ = Format.objects.get_or_create(name="int")
        # extras del esquema jornada (+ control + historial)
        self._extra("hora_entrada")
        self._extra("hora_salida")
        self._extra("dias_laborables", self.fmt_json)
        self._extra("ia_completed")
        self._extra("ia_pregunta")
        self._extra("_hist_jornada", self.fmt_json)

    def _extra(self, name, fmt=None):
        return ExtraFactory(
            name=name, space=self.space, classify=self.classify,
            format=fmt, flow=None, deleted=False)

    def _data(self):
        return self.member.get_extra_values_data(refrest=True)

    def _run(self, result, entrada="de lunes a viernes de 8 a 4"):
        behavior = IaExtraeBehavior(
            self.response, esquema="jornada", entrada=entrada,
            client=FakeGemini(result))
        return behavior

    def test_extraccion_completa_escribe_extras_y_limpia_historial(self):
        self._run({
            "hora_entrada": "8:00", "hora_salida": "16:00",
            "dias_laborables": ["lunes", "martes", "miércoles", "jueves",
                                "viernes"],
            "ia_completed": "si", "ia_pregunta": None})
        data = self._data()
        self.assertEqual(data["hora_entrada"], "8:00")
        self.assertEqual(data["hora_salida"], "16:00")
        self.assertEqual(data["dias_laborables"][0], "lunes")
        self.assertEqual(data["ia_completed"], "si")
        # historial limpiado al completar
        self.assertIsNone(data.get("_hist_jornada"))
        self.assertEqual(self.response.errors, [])

    def test_incompleto_repregunta_y_no_escribe_none(self):
        self._run({
            "hora_entrada": "8:00", "hora_salida": None,
            "dias_laborables": ["lunes"], "ia_completed": "no",
            "ia_pregunta": "¿A qué hora termina la jornada?"})
        data = self._data()
        self.assertEqual(data["ia_completed"], "no")
        self.assertEqual(data["ia_pregunta"], "¿A qué hora termina la jornada?")
        # hora_salida era None: no se sobreescribe con "None"
        self.assertIsNone(data.get("hora_salida"))
        # historial conservado para la siguiente vuelta
        self.assertEqual(data.get("_hist_jornada"), ["de lunes a viernes de 8 a 4"])

    def test_extra_recien_escrito_visible_sin_refrest(self):
        # Regresión: el render de la repregunta lee get_extra_values_data() SIN
        # refrest. El extra que el behavior acaba de escribir debe verse en el
        # cache; si no, el cuerpo del mensaje "{{ia_pregunta}}" sale vacío y
        # Meta lo rechaza con 400 (bot mudo). Materializamos el cache antes de
        # escribir, como hace el request real, para forzar el caso.
        self.member.get_extra_values_data()
        self._run({
            "hora_entrada": None, "hora_salida": None,
            "dias_laborables": ["lunes"], "ia_completed": "no",
            "ia_pregunta": "¿A qué hora entraría y a qué hora saldría?"})
        data = self.member.get_extra_values_data()  # SIN refrest: lee cache
        self.assertEqual(
            data.get("ia_pregunta"),
            "¿A qué hora entraría y a qué hora saldría?")

    def test_validacion_pydantic_mas_de_seis_dias_se_vuelve_repregunta(self):
        self._run({
            "hora_entrada": "8:00", "hora_salida": "16:00",
            "dias_laborables": ["lunes", "martes", "miércoles", "jueves",
                                "viernes", "sábado", "domingo"],
            "ia_completed": "si", "ia_pregunta": None})
        data = self._data()
        self.assertEqual(data["ia_completed"], "no")
        self.assertIn("descanso", data["ia_pregunta"].lower())

    def test_gemini_falla_degrada_a_repregunta_suave(self):
        self._run(None)
        data = self._data()
        self.assertEqual(data["ia_completed"], "no")
        self.assertIn("forma", data["ia_pregunta"].lower())

    def test_pago_deriva_frase_periodicidad(self):
        # El esquema Pago calcula frase_periodicidad de pago_periodicidad (texto
        # de confirmación "$550 al día"); Gemini no la manda.
        from projects.caceh.schemas import Pago
        casos = {"diaria": "al día", "semanal": "a la semana",
                 "quincenal": "a la quincena", "mensual": "al mes"}
        for periodicidad, frase in casos.items():
            p = Pago(monto_pago=550, pago_periodicidad=periodicidad,
                     ia_completed="si").model_dump()
            self.assertEqual(p["frase_periodicidad"], frase)
        # sin periodicidad no inventa frase
        p = Pago(ia_completed="no").model_dump()
        self.assertIsNone(p["frase_periodicidad"])

    def test_historial_acumula_entre_vueltas(self):
        incompleto = {
            "hora_entrada": None, "hora_salida": None,
            "dias_laborables": None, "ia_completed": "no",
            "ia_pregunta": "¿Qué días trabajas?"}
        self._run(incompleto, entrada="trabajo de día")
        b2 = self._run(incompleto, entrada="de lunes a viernes")
        # la 2.ª llamada a Gemini recibió ambas respuestas acumuladas
        self.assertIn("trabajo de día", b2.client.last_user_text)
        self.assertIn("de lunes a viernes", b2.client.last_user_text)

    def test_esquema_no_registrado_agrega_error(self):
        IaExtraeBehavior(
            self.response, esquema="inexistente", entrada="x",
            client=FakeGemini({}))
        self.assertTrue(
            any(e.get("esquema") == "inexistente"
                for e in self.response.errors))


@skipUnless(
    settings.GEMINI_API_KEY,
    "smoke test real: requiere GEMINI_API_KEY en el entorno")
class GeminiSmokeTestCase(TestCase):
    def test_extrae_jornada_real(self):
        from utilities.gemini_client import GeminiClient
        from projects.caceh.schemas import Jornada, JORNADA_PROMPT

        client = GeminiClient()
        data = client.extract(
            JORNADA_PROMPT,
            "trabajo de lunes a viernes de 9 de la mañana a 5 de la tarde",
            Jornada)
        self.assertIsNotNone(data, f"errores: {client.errors}")
        self.assertIn(data["ia_completed"], ("si", "no"))
