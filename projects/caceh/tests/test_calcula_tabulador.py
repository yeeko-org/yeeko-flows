"""Tests de calcula_tabulador (D5): regla max, margen $100 y degradación
sin imagen. Sin red: no hay PNGs en assets/tablas, así que la rama "bajo"
registra el faltante de imagen en vez de subir un Media a WhatsApp.

Correr: .venv/bin/python manage.py test projects.caceh
"""
from infrastructure.place.factories import AccountFactory

from projects.caceh.behaviors.calcula_tabulador import (
    CalculaTabuladorBehavior,
)
from projects.caceh import tabulador
from projects.caceh.tests.test_behaviors import (
    CacehBehaviorTestBase, StubResponse,
)


class CalculaTabuladorTestCase(CacehBehaviorTestBase):
    def setUp(self):
        super().setUp()
        self.account = AccountFactory(space=self.space)
        self.response = StubResponse(
            self.member, self.space, account=self.account)
        self._extra("actividades", self.fmt_json)
        for name in ("salario_diario", "salario_sugerido", "salario_bajo"):
            self._extra(name)

    def test_max_de_los_items_y_salario_bajo(self):
        self._set("actividades", ["labor_1", "labor_19"])  # 342.47 y 904
        self._set("salario_diario", "500.0")

        CalculaTabuladorBehavior(self.response)

        data = self._data()
        self.assertEqual(data["salario_sugerido"], "904")
        self.assertEqual(data["salario_bajo"], "si")
        # Sin PNG en assets/tablas: degrada con error, sin romper el turno.
        self.assertTrue(any(
            e.get("imagen") == "tabulador_904" for e in self.response.errors))
        self.assertEqual(self.response.media_messages, [])

    def test_dentro_del_margen_no_avisa(self):
        # 350 = 450 - 100 exactos: el margen es inclusivo (no avisa).
        self._set("actividades", ["labor_2"])
        self._set("salario_diario", "350.0")

        CalculaTabuladorBehavior(self.response)

        data = self._data()
        self.assertEqual(data["salario_sugerido"], "450")
        self.assertEqual(data["salario_bajo"], "no")
        self.assertEqual(self.response.errors, [])

    def test_salario_arriba_del_sugerido_silencio(self):
        self._set("actividades", ["labor_10"])  # 800
        self._set("salario_diario", "900.0")

        CalculaTabuladorBehavior(self.response)

        self.assertEqual(self._data()["salario_bajo"], "no")

    def test_sin_actividades_sin_referencia(self):
        self._set("actividades", [])
        self._set("salario_diario", "300.0")

        CalculaTabuladorBehavior(self.response)

        data = self._data()
        self.assertEqual(data["salario_bajo"], "no")
        self.assertIsNone(data.get("salario_sugerido"))

    def test_sin_salario_diario_error_y_no_avisa(self):
        self._set("actividades", ["labor_19"])

        CalculaTabuladorBehavior(self.response)

        data = self._data()
        self.assertEqual(data["salario_bajo"], "no")
        self.assertTrue(any(
            "salario_diario" in e.get("message", "")
            for e in self.response.errors))

    def test_titulos_respetan_limite_checkbox(self):
        # Meta corta el CheckboxGroup en 20 opciones: la lista está justo
        # en el límite, agregar una labor obliga a fusionar otra.
        self.assertLessEqual(len(tabulador.opciones()), 20)
        for opcion in tabulador.opciones():
            self.assertLessEqual(len(opcion["title"]), 30, opcion["id"])
            self.assertLessEqual(len(opcion["description"]), 300)
