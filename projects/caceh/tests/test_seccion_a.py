"""Copy de §A por el motor, con Gemini fake (los nombres pasan por la unidad
de captura): la explicación de CACEH desde el saludo y la pregunta A8 con el
nombre de la contraparte.

Correr:
    .venv/bin/python manage.py test \
        projects.caceh.tests.test_seccion_a --noinput
"""
import gc

from django.core.management import call_command
from django.test import TestCase

from infrastructure.box.models import Fragment
from infrastructure.place.models import Space
from infrastructure.xtra.models import Format
from projects.caceh.flow_driver import FlowDriver, gemini_fake
from projects.caceh.tests.seed_titles import title_of

WA_ID = "5215500000031"


class SeccionATest(TestCase):
    # Space 1 + Account (pid 103571329211620) + Platform whatsapp.
    fixtures = ["test/fixtures/account_fixture.json"]

    @classmethod
    def setUpTestData(cls):
        cls.space = Space.objects.get(pk=1)
        Format.objects.get_or_create(name="json")
        Format.objects.get_or_create(name="int")
        call_command("seed_flow", space=cls.space.pk)

    def setUp(self):
        cm = gemini_fake()
        cm.__enter__()
        self.addCleanup(cm.__exit__, None, None, None)
        self.d = FlowDriver(WA_ID)

    def tearDown(self):
        gc.collect()

    @staticmethod
    def _piezas(turn: list[dict]) -> list:
        return [Fragment.objects.get(pk=m["_fragment_id"]).piece.name
                if m.get("_fragment_id") else None for m in turn]

    def test_que_es_caceh_explica_y_repite_la_pregunta_de_rol(self):
        d = self.d
        d.send("hola")
        d.press(title_of("a_saludo", "a_acerca"))
        self.assertEqual(self._piezas(d.last_turn),
                         ["a_acerca", "a_quien_eres"])
        self.assertIn("CACEH es una organización", d.bot_texts()[0])
        self.assertEqual(d.at_piece(), "a_quien_eres")

    def test_a8_lleva_el_nombre_de_la_contraparte(self):
        d = self.d
        d.send("hola")
        d.tap(title_of("a_quien_eres", operador="trabajadora"))
        d.send("Juana Pérez López")
        d.send("Marcela Ruiz Soto")
        d.tap(title_of("a_mayor_edad", mayor_edad="si"))
        self.assertEqual(d.at_piece(), "a_num_empleadoras")
        pregunta = d.bot_texts()[-1]
        self.assertIn("Marcela Ruiz Soto", pregunta)
        self.assertNotIn("{{", pregunta)

    def _trabajadora_hasta_a8(self, wa_id: str) -> FlowDriver:
        d = FlowDriver(wa_id)
        d.send("hola")
        d.tap(title_of("a_quien_eres", operador="trabajadora"))
        d.send("Juana Pérez López")
        d.send("Marcela Ruiz Soto")
        d.tap(title_of("a_mayor_edad", mayor_edad="si"))
        return d

    def test_linea_de_modalidad_solo_para_la_trabajadora(self):
        es = "de entrada por salida"
        una_casa = title_of("a_num_empleadoras", "a_duerme")
        casos = [
            ("planta",
             [una_casa, title_of("a_duerme", tipo_contrato="planta")],
             ["a_modalidad_planta", "b_jornada_abierta"], "de planta"),
            ("una casa",
             [una_casa, title_of("a_duerme", tipo_contrato="entrada_salida")],
             ["a_modalidad_es", "b_jornada_abierta"], es),
            ("varias casas",
             [title_of("a_num_empleadoras", "a_modalidad_es_varias")],
             ["a_modalidad_es_varias", "a_link_es", "b_jornada_abierta"], es),
        ]
        for i, (caso, botones, piezas, modalidad) in enumerate(casos):
            with self.subTest(trabajadora=caso):
                d = self._trabajadora_hasta_a8(f"52155000001{i:02d}")
                for boton in botones:
                    d.tap(boton)
                self.assertEqual(self._piezas(d.last_turn), piezas)
                self.assertEqual(d.extras().get("modalidad_texto"),
                                 modalidad)

        for i, (clave, modalidad) in enumerate(
                [("planta", "de planta"), ("entrada_salida", es)]):
            with self.subTest(empleadora=clave):
                d = FlowDriver(f"52155000002{i:02d}")
                d.send("hola")
                d.tap(title_of("a_quien_eres", operador="empleadora"))
                d.send("Marcela Ruiz Soto")
                d.send("Juana Pérez López")
                d.tap(title_of("a_tipo_empleadora", tipo_contrato=clave))
                self.assertEqual(self._piezas(d.last_turn),
                                 ["b_jornada_abierta"])
                self.assertEqual(d.extras().get("modalidad_texto"),
                                 modalidad)
