"""E2E del slice planta por el MOTOR REAL (WP7): mete payloads de WhatsApp por
ManagerFlow turno a turno y recorre cada bifurcación del slice, afirmando la
pieza alcanzada y los extras/Contract al cierre.

Gemini es REAL (no mock): valida el slice contra el modelo. Por eso la clase se
salta sin `GEMINI_API_KEY`. La única red mockeada es la de WhatsApp (envío +
subida de media), vía `media_offline`.

Aserciones tolerantes: con IA real no se afirman valores exactos (hora "08:00"),
sino el enrutamiento (`at_piece`) y el estado de cierre que no depende de la IA
(`flujo_completado`, `registro_id`, fila `Contract`).

Correr (con el .env cargado para que settings.GEMINI_API_KEY exista):
    set -a; . config/.env; set +a
    .venv/bin/python manage.py test projects.caceh.tests.test_flow_e2e
"""
from unittest import skipUnless

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from infrastructure.place.models import Space
from infrastructure.xtra.models import Format
from projects.caceh.flow_driver import FlowDriver, media_offline
from projects.caceh.models import Contract

WA_ID = "5215500000001"

# Frases naturales realistas (las interpreta Gemini real).
JORNADA_OK = ("trabajo de lunes a viernes, de 8 de la mañana a 4 de la tarde, "
              "descanso sábado y domingo")
JORNADA_ACLARA = "de lunes a viernes, entrada 8:00 y salida 16:00"
JORNADA_INCOMPLETA = "trabajo de lunes a viernes"   # falta el horario
PAGO_OK = "2500 a la semana"
LUGAR_OK = ("Avenida Reforma 100, colonia Juárez, código postal 06600, "
            "alcaldía Cuauhtémoc, Ciudad de México")
LUGAR_ACLARA = ("calle Avenida Reforma número 100, colonia Juárez, "
                "C.P. 06600, alcaldía Cuauhtémoc, Ciudad de México")
DESCANSO_OK = "una hora de descanso y se le da comida"


@skipUnless(bool(settings.GEMINI_API_KEY),
            "e2e con Gemini real: requiere GEMINI_API_KEY en el entorno")
class FlowE2ETest(TestCase):
    # Space 1 + Account (pid 103571329211620) + Platform whatsapp.
    fixtures = ["test/fixtures/account_fixture.json"]

    @classmethod
    def setUpTestData(cls):
        cls.space = Space.objects.get(pk=1)
        # Format que el seed asigna a extras json/int (no vienen por migración).
        Format.objects.get_or_create(name="json")
        Format.objects.get_or_create(name="int")
        call_command("seed_flow", space=cls.space.pk)

    def setUp(self):
        # Sin red de WhatsApp en todo el test (genera_pdf/entrega_pdf suben media).
        cm = media_offline()
        cm.__enter__()
        self.addCleanup(cm.__exit__, None, None, None)
        self.d = FlowDriver(WA_ID)

    # ------------------------------------------------------------ prefijos
    def _saludo_a_quien_eres(self):
        d = self.d
        d.send("hola")
        self.assertEqual(d.at_piece(), "a_saludo")
        d.tap("¡Empecemos!")
        self.assertEqual(d.at_piece(), "a_quien_eres")

    def _nombres(self, rol):
        d = self.d
        d.tap(rol)                       # "Trabajadora" | "Empleadora"
        self.assertEqual(d.at_piece(), "a_nombre_operador")
        d.send("Juana Pérez López")
        self.assertEqual(d.at_piece(), "a_nombre_contraparte")
        d.send("Marcela Ruiz Soto")      # dispara asigna_partes + bifurca

    def _ia_capture(self, text, confirm_piece, repregunta_piece, aclara):
        """Manda una captura que dispara ia_extrae con loop de repregunta. Con
        Gemini real el modelo puede pedir un dato aunque la frase parezca
        completa; se aclara hasta 2 veces antes de exigir la confirmación."""
        d = self.d
        d.send(text)
        for _ in range(2):
            if d.at_piece() == confirm_piece:
                return
            if d.at_piece() == repregunta_piece:
                d.send(aclara)
        self.assertEqual(d.at_piece(), confirm_piece)

    def _jornada_pago_lugar_hasta_resumen(self):
        """Desde b_jornada_abierta hasta e_resumen (3 llamadas a Gemini real)."""
        d = self.d
        self.assertEqual(d.at_piece(), "b_jornada_abierta")
        self._ia_capture(JORNADA_OK, "b_confirma_jornada",
                         "b_repregunta_jornada", JORNADA_ACLARA)
        d.tap("Sí, así es")
        self.assertEqual(d.at_piece(), "c_relacion_previa")
        d.tap("Empieza ahora")
        self.assertEqual(d.at_piece(), "c_pago_abierta")
        d.send(PAGO_OK)
        self.assertEqual(d.at_piece(), "c_confirma_pago")
        d.tap("Sí, así es")
        d.tap("En efectivo")             # calcula_salario_diario -> lugar
        self.assertEqual(d.at_piece(), "c_lugar_abierta")
        self._ia_capture(LUGAR_OK, "c_confirma_lugar",
                         "c_repregunta_lugar", LUGAR_ACLARA)
        d.tap("Sí, es correcta")         # confirma lugar -> lista actividades
        self.assertEqual(d.at_piece(), "d_actividades")
        # D1: FormWa multiselect. El submit del Flow escribe {{actividades}} y
        # avanza (dest_piece_pk) a d_deriva_categoria -> ... -> e_resumen.
        d.submit_form(["limpieza_general", "lavado"])
        self.assertEqual(d.at_piece(), "e_resumen")  # D2 + tabulador off

    # --------------------------------------------------------------- casos
    def test_p1_trabajadora_planta_hasta_pdf(self):
        d = self.d
        self._saludo_a_quien_eres()
        self._nombres("Trabajadora")
        self.assertEqual(d.at_piece(), "a_mayor_edad")
        d.tap("Sí")
        self.assertEqual(d.at_piece(), "a_num_empleadoras")
        d.tap("Una persona")
        self.assertEqual(d.at_piece(), "a_duerme")
        d.tap("Sí, duermo ahí")          # tipo_contrato=planta
        self._jornada_pago_lugar_hasta_resumen()

        d.tap("Todo correcto")           # genera_pdf + registra + entrega
        self.assertEqual(d.at_piece(), "e_oferta_mejora")

        extras = d.extras()
        self.assertEqual(extras.get("flujo_completado"), "completo")
        self.assertTrue(extras.get("registro_id"))
        self.assertTrue(extras.get("pdf_contrato"))
        self.assertEqual(Contract.objects.count(), 1)
        self.assertTrue(Contract.objects.first().folio)

        d.tap("Así está bien")
        self.assertEqual(d.at_piece(), "e_despedida")

    def test_p2_empleadora_planta_hasta_pdf(self):
        d = self.d
        self._saludo_a_quien_eres()
        self._nombres("Empleadora")
        # La empleadora salta mayoría/empleadoras/duerme: declara el tipo.
        self.assertEqual(d.at_piece(), "a_tipo_empleadora")
        d.tap("De planta")               # tipo_contrato=planta
        self._jornada_pago_lugar_hasta_resumen()

        d.tap("Todo correcto")
        self.assertEqual(d.at_piece(), "e_oferta_mejora")
        self.assertEqual(d.extras().get("flujo_completado"), "completo")
        self.assertEqual(Contract.objects.count(), 1)

    def test_p3_menor_de_edad_termina(self):
        d = self.d
        self._saludo_a_quien_eres()
        self._nombres("Trabajadora")
        self.assertEqual(d.at_piece(), "a_mayor_edad")
        d.tap("No")
        self.assertEqual(d.at_piece(), "a_menor")
        self.assertNotEqual(d.extras().get("flujo_completado"), "completo")
        self.assertEqual(Contract.objects.count(), 0)

    def test_p4_varias_empleadoras_entrada_salida(self):
        """Varias empleadoras -> entrada_salida -> §B con descanso (B6/B7)."""
        d = self.d
        self._saludo_a_quien_eres()
        self._nombres("Trabajadora")
        d.tap("Sí")
        self.assertEqual(d.at_piece(), "a_num_empleadoras")
        d.tap("Varias")                  # A10 link auto-avanza a §B
        self.assertEqual(d.at_piece(), "b_jornada_abierta")
        self.assertEqual(d.extras().get("tipo_contrato"), "entrada_salida")
        # entrada_salida añade descanso: jornada cierra en b_descanso_abierta.
        self._ia_capture(JORNADA_OK, "b_descanso_abierta",
                         "b_repregunta_jornada", JORNADA_ACLARA)
        d.send(DESCANSO_OK)              # B7 ia_extrae descanso -> confirma
        self.assertEqual(d.at_piece(), "b_confirma_jornada")
        self.assertTrue(d.extras().get("descanso_tiempo"))

    def test_p5_no_duerme_entrada_salida(self):
        d = self.d
        self._saludo_a_quien_eres()
        self._nombres("Trabajadora")
        d.tap("Sí")
        d.tap("Una persona")
        self.assertEqual(d.at_piece(), "a_duerme")
        d.tap("No duermo ahí")
        self.assertEqual(d.at_piece(), "b_jornada_abierta")
        self.assertEqual(d.extras().get("tipo_contrato"), "entrada_salida")

    def test_p6_empleadora_entrada_salida(self):
        d = self.d
        self._saludo_a_quien_eres()
        self._nombres("Empleadora")
        self.assertEqual(d.at_piece(), "a_tipo_empleadora")
        d.tap("Entrada por salida")
        self.assertEqual(d.at_piece(), "b_jornada_abierta")
        self.assertEqual(d.extras().get("tipo_contrato"), "entrada_salida")

    def test_p8_relacion_previa_retroactiva(self):
        """Ya trabajábamos -> captura fecha; una no parseable reedita y una
        fecha pasada válida sigue a pago (la consume la cláusula SEGUNDA)."""
        d = self.d
        self._saludo_a_quien_eres()
        self._nombres("Trabajadora")
        d.tap("Sí")
        d.tap("Una persona")
        d.tap("Sí, duermo ahí")
        self.assertEqual(d.at_piece(), "b_jornada_abierta")
        self._ia_capture(JORNADA_OK, "b_confirma_jornada",
                         "b_repregunta_jornada", JORNADA_ACLARA)
        d.tap("Sí, así es")
        self.assertEqual(d.at_piece(), "c_relacion_previa")
        d.tap("Ya trabajábamos")
        self.assertEqual(d.at_piece(), "c_fecha_inicio")
        self.assertEqual(d.extras().get("es_retroactivo"), "si")
        d.send("el año pasado")          # no parseable -> reedita
        self.assertEqual(d.at_piece(), "c_repregunta_fecha")
        d.send("15/03/2023")             # válida -> normaliza y sigue a pago
        self.assertEqual(d.at_piece(), "c_pago_abierta")
        self.assertEqual(d.extras().get("fecha_inicio"), "15/03/2023")

    def test_p7_loop_repregunta_jornada(self):
        d = self.d
        self._saludo_a_quien_eres()
        self._nombres("Trabajadora")
        d.tap("Sí")
        d.tap("Una persona")
        d.tap("Sí, duermo ahí")
        self.assertEqual(d.at_piece(), "b_jornada_abierta")
        # Frase sin horario: Gemini real debe pedir el dato que falta.
        d.send(JORNADA_INCOMPLETA)
        self.assertEqual(d.at_piece(), "b_repregunta_jornada")
        # Completa el horario: cierra y avanza a confirmar.
        d.send("de 8 de la mañana a 4 de la tarde")
        self.assertEqual(d.at_piece(), "b_confirma_jornada")
