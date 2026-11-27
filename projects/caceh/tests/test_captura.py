"""Las capturas de CACEH como unidades de `open_question`, por el motor con
Gemini fake guionizable: los textos de validación, la dirección con su estado,
la fecha con día 1, el recálculo al corregir, el recorrido de planta con su
hueco en el PDF y los nombres que nunca se sueltan.

Correr:
    .venv/bin/python manage.py test \
        projects.caceh.tests.test_captura --noinput
"""
import gc
import re
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from infrastructure.box.models import Piece
from infrastructure.place.models import Space
from infrastructure.talk.models import Interaction
from infrastructure.xtra.models import Format
from projects.caceh import schemas
from projects.caceh.derivados import texto_fecha
from projects.caceh.flow_driver import FlowDriver, gemini_fake, media_offline
from projects.caceh.pdf import (
    HUECO_CORTO, HUECO_MEDIO, build_html, render_planta)
from projects.caceh.seed.textos import NO_ENTENDI_DATO
from projects.caceh.tests.seed_titles import title_of
from services.behavior.open_question import FIRST_RECAP_HINT

LUNES_A_VIERNES = ["lunes", "martes", "miércoles", "jueves", "viernes"]


def fecha(mes=5, anio=2015, dia=None, done="si", pregunta=None):
    return {"fecha_dia": dia, "fecha_mes": mes, "fecha_anio": anio,
            "fecha_inicio": None, "ia_completed": done,
            "ia_pregunta": pregunta}


def domicilio(**campos):
    base = {"lt_calle": "Calle 5", "lt_ext": "12", "lt_int": None,
            "lt_colonia": "Centro", "lt_cp": None, "lt_municipio": "Toluca",
            "lt_estado": "Estado de México", "ciudad_firma": "Toluca",
            "ia_completed": "si", "ia_pregunta": None}
    return {**base, **campos}


def nombre(prefijo, pila=None, paterno=None, materno=None):
    return {f"{prefijo}_nombre_pila": pila,
            f"{prefijo}_apellido_paterno": paterno,
            f"{prefijo}_apellido_materno": materno,
            "ia_completed": "si", "ia_pregunta": None}


class CapturaTest(TestCase):
    # Space 1 + Account (pid 103571329211620) + Platform whatsapp.
    fixtures = ["test/fixtures/account_fixture.json"]

    @classmethod
    def setUpTestData(cls):
        cls.space = Space.objects.get(pk=1)
        Format.objects.get_or_create(name="json")
        Format.objects.get_or_create(name="int")
        call_command("seed_flow", space=cls.space.pk)

    def setUp(self):
        for cm in (media_offline(), gemini_fake()):
            fake = cm.__enter__()
            self.addCleanup(cm.__exit__, None, None, None)
        self.gemini = fake

    def tearDown(self):
        gc.collect()

    # ------------------------------------------------------------ helpers
    def _answer(self, d: FlowDriver, text: str, *scripted) -> list[str]:
        self.gemini.script.extend(scripted)
        d.send(text, with_context=False)
        return d.bot_texts()

    def _trabajadora_hasta_jornada(self, wa_id: str,
                                   planta: bool = True) -> FlowDriver:
        d = FlowDriver(wa_id)
        d.send("hola")
        d.tap(title_of("a_quien_eres", operador="trabajadora"))
        d.send("Juana Pérez López")
        d.send("Marcela Ruiz Soto")
        d.tap(title_of("a_mayor_edad", mayor_edad="si"))
        d.tap(title_of("a_num_empleadoras", "a_duerme"))
        d.tap(title_of("a_duerme", tipo_contrato="planta" if planta
                       else "entrada_salida"))
        self.assertEqual(d.at_piece(), "b_jornada_abierta")
        return d

    def _hasta_modo_pago(self, d: FlowDriver) -> None:
        d.send("de lunes a viernes de 8 a 4")
        d.tap(title_of("c_relacion_previa", "c_pago_abierta"))
        d.send("2500 a la semana")
        self.assertEqual(d.at_piece(), "c_modo_pago")

    # -------------------------------------------------------------- tests
    def test_10_textos_de_validacion_llegan_tal_cual(self):
        d = self._trabajadora_hasta_jornada("5215500000101", planta=False)
        d.send("de lunes a viernes de 8 a 4")
        self.assertEqual(d.at_piece(), "b_descanso_abierta")
        texts = self._answer(d, "15 minutos y comida", {
            "descanso_minutos": 15, "comidas_incluidas": ["comida"],
            "ia_completed": "si", "ia_pregunta": None})
        self.assertEqual(texts, [schemas.DESCANSO_MINIMO])
        d.send("una hora y se le da comida")
        d.tap(title_of("c_relacion_previa", "c_fecha_inicio"))

        texts = self._answer(d, "mayo de 2999", fecha(anio=2999))
        self.assertEqual(texts, [schemas.FECHA_FUTURA])
        texts = self._answer(d, "13/2015", fecha(mes=13))
        self.assertEqual(texts, [schemas.FECHA_INEXISTENTE])
        d.send("mayo de 2015")
        self.assertEqual(d.extras().get("fecha_inicio"), "01/05/2015")

        d.press("Corregir", piece="c_fecha_inicio")
        texts = self._answer(d, "mayo del 15", fecha(anio=15))
        self.assertEqual(texts, [schemas.FECHA_INEXISTENTE])
        texts = self._answer(d, "no, mayo de 2999", fecha(anio=2999))
        self.assertEqual(texts, [schemas.FECHA_FUTURA])
        self.assertEqual(d.at_slot(), "reask")
        self.assertEqual(d.extras().get("fecha_inicio"), "01/05/2015")

    def test_11_domicilio_lo_que_falta_y_el_estado_en_la_repregunta(self):
        reask = schemas.REPREGUNTA_DOMICILIO
        casos = [
            ({"lt_colonia": None},
             reask.format(faltan="colonia y código postal")),
            ({"lt_ext": None, "lt_cp": "50000"}, reask.format(faltan="número")),
            ({"lt_estado": None, "lt_cp": "50000"},
             reask.format(faltan="estado")),
        ]
        for faltante, pregunta in casos:
            with self.subTest(faltante=faltante):
                dom = schemas.Domicilio(**domicilio(**faltante))
                self.assertEqual(dom.ia_completed, "no")
                self.assertEqual(dom.ia_pregunta, pregunta)
        for completo in ({"lt_ext": "S/N"}, {"lt_cp": None}):
            with self.subTest(completo=completo):
                dom = schemas.Domicilio(**domicilio(**completo))
                self.assertEqual(dom.ia_completed, "si")

        d = self._trabajadora_hasta_jornada("5215500000111")
        self._hasta_modo_pago(d)
        d.tap(title_of("c_modo_pago", modo_pago="efectivo"))
        texts = self._answer(d, "Calle 5 número 12, Centro, Toluca",
                             domicilio(lt_estado=None))
        self.assertEqual(texts, [reask.format(faltan="estado y código postal")])
        self.assertEqual(d.at_slot(), "reask")
        texts = self._answer(d, "Estado de México", domicilio())
        self.assertEqual(texts[0], (
            "La dirección del lugar de trabajo quedó así: Calle 5 12, col. "
            "Centro, Toluca, Estado de México."))
        self.assertEqual(d.at_piece(), "d_actividades")
        self.assertFalse(Piece.objects.filter(
            name__in=("c_estado", "c_checa_estado")).exists())

    def test_12_dia_uno_recalculo_y_pdf_sin_cp(self):
        d = self._trabajadora_hasta_jornada("5215500000121")
        d.send("de lunes a viernes de 8 a 4")
        d.tap(title_of("c_relacion_previa", "c_fecha_inicio"))
        texts = self._answer(d, "mayo de 2015", fecha(mes=5, anio=2015))
        self.assertEqual(d.extras().get("fecha_inicio"), "01/05/2015")
        self.assertEqual(
            texts[0], "La fecha en que empezó este trabajo quedó así: "
            "1 de mayo de 2015.")
        self.assertEqual(texto_fecha("01/05/2015"), "1 de mayo de 2015")

        d.send("2500 a la semana")
        self.assertEqual(d.extras().get("salario_diario"), "500.0")
        d.press("Corregir", piece="b_jornada_abierta")
        texts = self._answer(d, "también los sábados", {
            "dias_laborables": LUNES_A_VIERNES + ["sábado"],
            "hora_entrada": None, "hora_salida": None,
            "ia_completed": "si", "ia_pregunta": None})
        self.assertEqual(texts, [
            "La jornada laboral quedó así: lunes, martes, miércoles, jueves, "
            "viernes y sábado, de 8am a 4pm.", "¿Y cómo se le paga?"])
        self.assertEqual(d.extras().get("salario_diario"), "416.67")
        self.assertEqual(d.at_piece(), "c_modo_pago")

        datos = {"lt_calle": "Calle 5", "lt_ext": "12",
                 "lt_colonia": "Centro", "lt_municipio": "Toluca"}
        for tipo in ("planta", "entrada_salida"):
            with self.subTest(tipo=tipo):
                self.assertNotIn("C.P.", build_html(datos, tipo))
                self.assertIn("C.P. 50000",
                              build_html({**datos, "lt_cp": "50000"}, tipo))

    def test_13_planta_completo_con_hueco_en_el_pdf(self):
        d = self._trabajadora_hasta_jornada("5215500000131")
        d.send("de lunes a viernes de 8 a 4")
        recap = d.bot_texts()[0]
        self.assertEqual(recap, (
            "La jornada laboral quedó así: lunes, martes, miércoles, jueves "
            "y viernes, de 8am a 4pm.\n\n" + FIRST_RECAP_HINT))
        self.assertIn("Corregir", d.bot_buttons())

        d.tap(title_of("c_relacion_previa", "c_fecha_inicio"))
        sin_fecha = fecha(mes=None, anio=None, done="no",
                          pregunta="¿En qué mes y año empezó?")
        for _ in range(2):
            self.assertEqual(self._answer(d, "hace mucho", sin_fecha),
                             ["¿En qué mes y año empezó?"])
        texts = self._answer(d, "no me acuerdo", sin_fecha)
        self.assertEqual(texts[0], NO_ENTENDI_DATO)
        self.assertEqual(d.at_piece(), "c_pago_abierta")
        self.assertNotIn("fecha_inicio", d.extras())

        texts = self._answer(d, "1000 a la semana", {
            "monto_pago": 1000, "pago_periodicidad": "semanal",
            "ia_completed": "si", "ia_pregunta": None})
        self.assertEqual(texts, ["El pago quedó así: $1,000 a la semana.",
                                 "¿Y cómo se le paga?"])
        d.tap(title_of("c_modo_pago", modo_pago="efectivo"))
        texts = self._answer(d, "Av. Reforma 100, col. Juárez")
        self.assertEqual(texts[0], (
            "La dirección del lugar de trabajo quedó así: Av. Reforma 100, "
            "col. Juárez, C.P. 06600, Cuauhtémoc, Ciudad de México."))
        self.assertEqual(d.at_piece(), "d_actividades")

        d.submit_form(["labor_1", "labor_2"])
        self.assertEqual(d.at_piece(), "d_sugerencia")
        d.press(title_of("d_sugerencia", "d_contacto"))
        texts = d.bot_texts()
        self.assertIn("alguien de CACEH te va a escribir", texts[0])
        self.assertTrue(texts[1].startswith("Esto es lo que tengo."))
        self.assertEqual(d.at_piece(), "e_resumen")

        rendered: list[dict] = []

        def _spy(datos):
            rendered.append(datos)
            return render_planta(datos)

        with patch("projects.caceh.behaviors.genera_pdf.render_planta",
                   side_effect=_spy):
            d.tap(title_of("e_resumen", "e_genera_pdf"))
        self.assertEqual(d.at_piece(), "e_despedida")
        html = build_html(rendered[0], "planta")
        segunda = html.split("SEGUNDA. DE LA DURACIÓN")[1].split(
            "TERCERA")[0]
        # Día, mes y año, cada uno con el largo de lo que se escribe ahí.
        self.assertEqual(re.findall(r"_{3,}", segunda),
                         [HUECO_CORTO, HUECO_MEDIO, HUECO_MEDIO])
        declaraciones = html.split("Declara «LA PERSONA EMPLEADORA»")[1]
        self.assertNotIn("___", declaraciones.split("C)</strong>")[0])
        self.assertIn("$200.00", html)

    def test_14_nombres_insisten_una_vez_y_nunca_se_sueltan(self):
        d = FlowDriver("5215500000141")
        d.send("hola")
        d.tap(title_of("a_quien_eres", operador="trabajadora"))
        texts = self._answer(d, "Juana Pérez",
                             nombre("operador", "Juana", "Pérez"))
        self.assertEqual(texts, [schemas.APELLIDOS_OPERADOR])
        texts = self._answer(d, "solo tengo uno",
                             nombre("operador", "Juana", "Pérez"))
        self.assertEqual(d.extras().get("operador_nombre"), "Juana Pérez")
        self.assertEqual(texts, [
            "Gracias, Juana. Ahora escríbeme el nombre completo de la persona "
            "empleadora."])

        texts = self._answer(d, "Marcela", nombre("contraparte", "Marcela"))
        self.assertEqual(texts, [
            "Por favor, escribe también los dos apellidos de la persona "
            "empleadora."])
        for _ in range(3):
            self._answer(d, "no sé", nombre("contraparte"))
            self.assertEqual(d.at_piece(), "a_nombre_contraparte")
            self.assertEqual(d.at_slot(), "reask")
        self._answer(d, "Marcela Ruiz",
                     nombre("contraparte", "Marcela", "Ruiz"))
        self.assertEqual(d.extras().get("contraparte_nombre"),
                         "Marcela Ruiz")
        self.assertEqual(d.at_piece(), "a_mayor_edad")
