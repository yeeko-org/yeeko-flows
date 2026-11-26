"""Qué pasa con un texto que el flujo no espera (behavior `default_text`).

Antes de sembrarlo, cualquier mensaje escrito fuera de guion producía silencio
absoluto —el bot no contestaba ni «Hola» tras terminar un contrato—. Lo que se
prueba aquí es que el aviso sale y, sobre todo, que **no deja varada** a la
persona: el motor ubica la conversación por la última salida con fragmento, así
que repetir la pieza pendiente es lo que conserva el contexto.

Correr:
    .venv/bin/python manage.py test \
        projects.caceh.tests.test_default_text --noinput
"""
import gc

from django.core.management import call_command
from django.test import TestCase

from infrastructure.box.models import Fragment
from infrastructure.place.models import Space
from infrastructure.xtra.models import Format
from projects.caceh.flow_driver import FlowDriver, gemini_fake, media_offline

WA_ID = "5215500000021"


class DefaultTextTest(TestCase):
    # Space 1 + Account (pid 103571329211620) + Platform whatsapp.
    fixtures = ["test/fixtures/account_fixture.json"]

    @classmethod
    def setUpTestData(cls):
        cls.space = Space.objects.get(pk=1)
        Format.objects.get_or_create(name="json")
        Format.objects.get_or_create(name="int")
        call_command("seed_flow", space=cls.space.pk)

    def setUp(self):
        cm = media_offline()
        cm.__enter__()
        self.addCleanup(cm.__exit__, None, None, None)
        self.d = FlowDriver(WA_ID)

    def tearDown(self):
        gc.collect()

    # La rama de la empleadora se escribe aquí y no se reusa la de
    # test_pdf_delivery porque aquella pasa por los botones de §A que hoy
    # están rojos (task-4) y nunca llega al multiselect.
    @staticmethod
    def _empleadora_hasta_resumen(d: FlowDriver) -> None:
        d.send("hola")
        d.tap("Empleadora")
        d.send("Marcela Ruiz Soto")
        d.send("Juana Pérez López")
        d.tap("De planta")
        d.send("jornada")               # gemini fake: datos canónicos
        d.tap("Sí, así es")
        d.tap("Empieza ahora")
        d.send("2500 a la semana")
        d.tap("Sí, así es")
        d.tap("En efectivo")
        d.send("domicilio")
        d.tap("Sí, es correcta")
        d.submit_form(["limpieza_general", "lavado"])
        assert d.at_piece() == "e_resumen", d.at_piece()

    def test_texto_fuera_de_guion_repite_la_pregunta_pendiente(self):
        d = self.d
        d.send("hola")                   # sin historial: dispara `start`
        self.assertEqual(d.at_piece(), "a_quien_eres")

        d.send("¿esto cuánto cuesta?")
        self.assertIn("No entendí", " ".join(d.bot_texts()))
        # La pieza pendiente se repite, así que sigue siendo el contexto.
        self.assertEqual(d.at_piece(), "a_quien_eres")

        # Y por eso el botón se puede seguir contestando por texto.
        d.tap("Trabajadora")
        self.assertEqual(d.at_piece(), "a_nombre_operador")

    def test_una_captura_de_texto_libre_no_llega_al_default_text(self):
        """Sobre una pieza de captura, `process_written` corre antes: el texto
        se guarda como respuesta (aunque sea «Hola»), que es el comportamiento
        del motor, no algo que introduzca `default_text`."""
        d = self.d
        d.send("hola")
        d.tap("Trabajadora")
        self.assertEqual(d.at_piece(), "a_nombre_operador")

        d.send("Hola")
        self.assertNotIn("No entendí", " ".join(d.bot_texts()))
        self.assertEqual(d.extras().get("operador_nombre"), "Hola")
        self.assertEqual(d.at_piece(), "a_nombre_contraparte")

    def test_texto_sin_context_id_sigue_capturando(self):
        """WhatsApp solo manda `context` si la persona cita el mensaje del bot;
        lo normal es escribir sin citar. La captura debe funcionar igual."""
        d = self.d
        d.send("hola")
        d.tap("Trabajadora")
        self.assertEqual(d.at_piece(), "a_nombre_operador")

        d.send("Juana Pérez López", with_context=False)
        self.assertNotIn("No entendí", " ".join(d.bot_texts()))
        self.assertEqual(d.extras().get("operador_nombre"),
                         "Juana Pérez López")
        self.assertEqual(d.at_piece(), "a_nombre_contraparte")

    def test_texto_tras_la_despedida_reofrece_empezar_otro(self):
        """El caso del correo de Fósforo: terminado un contrato, «Hola» ya no
        cae en el vacío — vuelve la despedida y con ella su botón."""
        d = self.d
        with gemini_fake():
            self._empleadora_hasta_resumen(d)
            d.send("Todo correcto")
            self.assertEqual(d.at_piece(), "e_despedida")

            d.send("Hola")
            self.assertIn("No entendí", " ".join(d.bot_texts()))
            self.assertEqual(d.at_piece(), "e_despedida")

            d.tap("Crear otro contrato")
            self.assertIn("Dignas firma", " ".join(d.bot_texts()))
            self.assertEqual(d.at_piece(), "a_quien_eres")
            self.assertNotIn("tipo_contrato", d.extras())

    @staticmethod
    def _piezas(turn: list[dict]) -> list:
        return [Fragment.objects.get(pk=m["_fragment_id"]).piece.name
                if m.get("_fragment_id") else None for m in turn]

    def test_resumen_dice_la_modalidad_en_palabras(self):
        d = self.d
        with gemini_fake():
            self._empleadora_hasta_resumen(d)
        resumen = d.bot_texts()[-1]
        self.assertEqual(self._piezas(d.last_turn)[-1], "e_resumen")
        self.assertIn("Contrato de planta", resumen)
        self.assertNotIn("Contrato planta", resumen)
        self.assertNotIn("{{", resumen)

    def test_cierre_seguro_social_antes_de_la_despedida(self):
        """La despedida con su botón cierra la pantalla; por eso es lo único
        que un «Hola» posterior repite, sin volver a mandar lo del IMSS."""
        d = self.d
        with gemini_fake():
            self._empleadora_hasta_resumen(d)
            d.send("Todo correcto")
            self.assertEqual(
                [m["type"] for m in d.last_turn],
                ["document", "text", "interactive"])
            self.assertEqual(
                self._piezas(d.last_turn),
                ["e_entrega_pdf", "e_seguro_social", "e_despedida"])
            self.assertEqual(d.bot_buttons(), ["Crear otro contrato"])

            d.send("Hola")
            self.assertNotIn("e_seguro_social", self._piezas(d.last_turn))
            self.assertEqual(self._piezas(d.last_turn)[-1], "e_despedida")
            self.assertEqual(d.last_turn[-1]["type"], "interactive")
            self.assertEqual(d.bot_buttons(), ["Crear otro contrato"])
            self.assertEqual(d.at_piece(), "e_despedida")
