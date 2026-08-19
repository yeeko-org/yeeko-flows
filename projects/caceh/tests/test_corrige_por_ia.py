"""Tests de corrige_por_ia (E4, task-27) con Gemini falso: qué viaja al
modelo (lista blanca), qué se escribe y cómo se enruta.

Correr: .venv/bin/python manage.py test projects.caceh
"""
import json

from projects.caceh.behaviors.calcula_salario_diario import (
    CalculaSalarioDiarioBehavior,
)
from projects.caceh.behaviors.corrige_por_ia import (
    CORREGIBLES, CorrigePorIaBehavior,
)
from projects.caceh.tests.test_behaviors import CacehBehaviorTestBase
from projects.caceh.tests.test_ia_extrae import FakeGemini

_NADA = {"ia_completed": "si", "ia_pregunta": None,
         "cambiar_actividades": "no"}


class CorrigePorIaTestCase(CacehBehaviorTestBase):
    def setUp(self):
        super().setUp()
        # Mismos formatos que seed/extras.py: sin ellos el int/json vuelve str.
        fmt = {"monto_pago": self.fmt_int, "descanso_minutos": self.fmt_int,
               "dias_laborables": self.fmt_json,
               "comidas_incluidas": self.fmt_json}
        for name in CORREGIBLES:
            self._extra(name, fmt.get(name))
        for name in ("tipo_contrato", "salario_diario", "ia_completed",
                     "ia_pregunta", "respuesta_correccion",
                     "correccion_destino"):
            self._extra(name)
        self._extra("_hist_correccion", self.fmt_json)
        self.member.user.phone = "5215551234567"
        self.member.user.save()
        self._set("tipo_contrato", "planta")
        self._set("trab_nombre_completo", "Juana Pérez López")
        self._set("empl_nombre_completo", "Marcela Ruiz Soto")
        self._set("monto_pago", 2500)
        self._set("pago_periodicidad", "semanal")
        self._set("dias_laborables", ["lunes", "martes", "miércoles",
                                      "jueves", "viernes"])
        self._set("salario_diario", "500.0")

    def _run(self, result, texto="algo está mal"):
        self._set("respuesta_correccion", texto)
        client = FakeGemini(result)
        CorrigePorIaBehavior(self.response, client=client)
        return client

    def test_nombre_corrige_y_vuelve_al_resumen(self):
        client = self._run(
            {**_NADA, "empl_nombre_completo": "Marcela Ruiz Sánchez"},
            "la empleadora es Marcela Ruiz Sánchez, no Soto")
        data = self._data()
        self.assertEqual(data["empl_nombre_completo"], "Marcela Ruiz Sánchez")
        self.assertEqual(data["trab_nombre_completo"], "Juana Pérez López")
        self.assertEqual(data["ia_completed"], "si")
        self.assertEqual(data["correccion_destino"], "resumen")
        self.assertIsNone(data.get("_hist_correccion"))
        self.assertEqual(self.response.errors, [])
        # Lista blanca: el estado viaja, los datos del usuario no.
        estado = json.loads(
            client.last_user_text.split("ESTADO ACTUAL:\n")[1]
            .split("\n\nLO QUE")[0])
        self.assertEqual(estado["empl_nombre_completo"], "Marcela Ruiz Soto")
        self.assertEqual(estado["salario_diario"], "500.0")
        self.assertNotIn("phone", estado)
        self.assertNotIn("username", estado)
        self.assertNotIn("_hist_correccion", estado)
        self.assertNotIn("descanso_minutos", estado)   # planta
        self.assertIn("la empleadora es Marcela", client.last_user_text)

    def test_salario_solo_monto_conserva_periodicidad_y_recalcula(self):
        self._run({**_NADA, "monto_pago": 3000}, "el pago son 3000")
        data = self._data()
        self.assertEqual(data["monto_pago"], 3000)
        self.assertEqual(data["pago_periodicidad"], "semanal")
        # e_recalcula: el mismo behavior de C8 sobre los extras corregidos.
        CalculaSalarioDiarioBehavior(self.response)
        self.assertEqual(self._data()["salario_diario"], "600.0")

    def test_texto_confuso_repregunta_y_conserva_historial(self):
        self._run({**_NADA, "ia_completed": "no",
                   "ia_pregunta": "¿Qué dato está mal?"}, "yo no dije eso")
        data = self._data()
        self.assertEqual(data["ia_completed"], "no")
        self.assertEqual(data["ia_pregunta"], "¿Qué dato está mal?")
        self.assertEqual(data["_hist_correccion"], ["yo no dije eso"])
        self.assertNotIn("correccion_destino", data)
        # Segunda vuelta: Gemini recibe las dos respuestas acumuladas.
        client = self._run(
            {**_NADA, "trab_nombre_completo": "Juana Pérez García"},
            "el apellido de Juana es García")
        self.assertIn("yo no dije eso", client.last_user_text)
        self.assertIn("García", client.last_user_text)
        self.assertEqual(self._data()["trab_nombre_completo"],
                         "Juana Pérez García")

    def test_completo_sin_cambios_se_vuelve_repregunta(self):
        self._run(_NADA, "está bien")
        self.assertEqual(self._data()["ia_completed"], "no")
        self.assertTrue(self._data()["ia_pregunta"])

    def test_actividades_enruta_al_flow(self):
        self._run({**_NADA, "cambiar_actividades": "si"},
                  "las actividades")
        data = self._data()
        self.assertEqual(data["ia_completed"], "si")
        self.assertEqual(data["correccion_destino"], "actividades")

    def test_valor_invalido_no_se_escribe(self):
        # A diferencia de ia_extrae, un dict que no valida no pisa nada.
        self._run({**_NADA, "lt_cp": "123", "lt_calle": "Otra calle"},
                  "el cp es 123 y la calle Otra calle")
        data = self._data()
        self.assertEqual(data["ia_completed"], "no")
        self.assertIn("5 dígitos", data["ia_pregunta"])
        self.assertNotIn("lt_calle", data)
        self.assertNotIn("lt_cp", data)
