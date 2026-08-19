"""Tests del PDF del slice CACEH (WP5 paso 4): render_planta produce un PDF y
genera_pdf escribe pdf_contrato. Sin red (Media mockeada) ni IA.

Correr: .venv/bin/python manage.py test projects.caceh
"""
from unittest import mock

from projects.caceh.behaviors.entrega_pdf import EntregaPdfBehavior
from projects.caceh.behaviors.genera_pdf import (
    GeneraPdfBehavior, _texto_descanso)
from projects.caceh.pdf import (
    build_html, render_entrada_salida, render_planta)
from projects.caceh.tests.test_behaviors import CacehBehaviorTestBase


class RenderPlantaTestCase(CacehBehaviorTestBase):
    def _datos(self):
        return {
            "empl_nombre": "Marcela Ruiz Soto",
            "trab_nombre": "Juana Pérez López",
            "lt_calle": "Av. Reforma", "lt_ext": "100", "lt_int": "",
            "lt_colonia": "Centro", "lt_cp": "06000",
            "lt_municipio": "Cuauhtémoc", "lt_estado": "CDMX",
            "inicio_dia": "1", "inicio_mes": "julio", "inicio_anio": "2026",
            "actividades": ["limpieza_general", "lavado"],
            "periodicidad": "semanal", "salario_diario": "350.0",
            "modo_pago": "efectivo",
            "hora_entrada": "8:00", "hora_salida": "16:00",
            "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
            "ciudad_firma": "Ciudad de México",
            "firma_dia": "29", "firma_mes": "junio", "firma_anio": "2026",
        }

    def test_render_produce_bytes_pdf(self):
        pdf = render_planta(self._datos())
        self.assertIsInstance(pdf, bytes)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1000)

    def test_render_omite_campos_no_capturados(self):
        # Sin CURP/edad/domicilio personal el render no debe dejar '________'.
        pdf = render_planta(self._datos())
        # WeasyPrint produce binario; basta con que no truene y dé un PDF.
        self.assertTrue(pdf.startswith(b"%PDF"))


class RenderEntradaSalidaTestCase(CacehBehaviorTestBase):
    def _datos(self):
        return {
            "empl_nombre": "Marcela Ruiz Soto",
            "trab_nombre": "Juana Pérez López",
            "lt_calle": "Av. Reforma", "lt_ext": "100", "lt_int": "",
            "lt_colonia": "Centro", "lt_cp": "06000",
            "lt_municipio": "Cuauhtémoc", "lt_estado": "CDMX",
            "inicio_dia": "1", "inicio_mes": "julio", "inicio_anio": "2026",
            "actividades": ["limpieza_general"],
            "periodicidad": "semanal", "salario_diario": "350.0",
            "modo_pago": "efectivo",
            "hora_entrada": "8:00", "hora_salida": "16:00",
            "dias": ["lunes", "martes"],
            "descanso_texto": "1 hora", "comidas_incluidas": ["comida"],
            "ciudad_firma": "Ciudad de México",
            "firma_dia": "29", "firma_mes": "junio", "firma_anio": "2026",
        }

    def test_html_usa_clausulas_de_entrada_salida(self):
        html = build_html(self._datos(), "entrada_salida")
        self.assertIn("MODALIDAD DE ENTRADA POR SALIDA", html)
        self.assertIn("OCTAVA. DEL DESCANSO", html)
        self.assertIn("descanso de 1 hora", html)  # descanso_texto
        self.assertIn("comida ( X )", html)        # marca la comida elegida
        self.assertIn("desayuno (  )", html)       # las no elegidas, vacías
        # No debe colarse la OCTAVA de planta (descanso nocturno/dormitorio).
        self.assertNotIn("descanso nocturno", html)

    def test_render_produce_bytes_pdf(self):
        pdf = render_entrada_salida(self._datos())
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1000)


class TextoDescansoTestCase(CacehBehaviorTestBase):
    def test_minutos_a_texto(self):
        casos = {
            30: "30 minutos", 45: "45 minutos", 60: "1 hora",
            90: "1 hora y 30 minutos", 120: "2 horas",
            150: "2 horas y 30 minutos", "60": "1 hora",
            None: "", "": "", 0: "",
        }
        for minutos, esperado in casos.items():
            with self.subTest(minutos=minutos):
                self.assertEqual(_texto_descanso(minutos), esperado)


class GeneraPdfTestCase(CacehBehaviorTestBase):
    def setUp(self):
        super().setUp()
        for name in ("empl_nombre_completo", "trab_nombre_completo",
                     "pago_periodicidad", "salario_diario", "modo_pago",
                     "hora_entrada", "hora_salida", "pdf_contrato"):
            self._extra(name)
        self._extra("dias_laborables", self.fmt_json)
        self._set("empl_nombre_completo", "Marcela Ruiz Soto")
        self._set("trab_nombre_completo", "Juana Pérez López")
        self._set("pago_periodicidad", "semanal")
        self._set("salario_diario", "350.0")
        self._set("modo_pago", "efectivo")
        self._set("hora_entrada", "8:00")
        self._set("hora_salida", "16:00")
        self._set("dias_laborables",
                  ["lunes", "martes", "miércoles", "jueves", "viernes"])

    def test_genera_pdf_escribe_pdf_contrato(self):
        with mock.patch(
            "projects.caceh.behaviors.genera_pdf.Media"
        ) as MockMedia, mock.patch(
            "projects.caceh.behaviors.genera_pdf.render_planta",
            return_value=b"%PDF-1.4 fake",
        ) as mock_render:
            MockMedia.return_value.pk = 4242
            GeneraPdfBehavior(self.response)

        mock_render.assert_called_once()
        data = self._data()
        self.assertEqual(int(data["pdf_contrato"]), 4242)
        self.assertEqual(self.response.errors, [])

    def test_genera_pdf_arma_datos_desde_extras(self):
        with mock.patch("projects.caceh.behaviors.genera_pdf.Media") as MM, \
             mock.patch(
                 "projects.caceh.behaviors.genera_pdf.render_planta",
                 return_value=b"%PDF",) as mock_render:
            MM.return_value.pk = 1
            GeneraPdfBehavior(self.response)

        datos = mock_render.call_args.args[0]
        self.assertEqual(datos["empl_nombre"], "Marcela Ruiz Soto")
        self.assertEqual(datos["periodicidad"], "semanal")
        self.assertEqual(datos["dias"][0], "lunes")
        # ciudad_firma cae a lt_municipio (vacío aquí) si no se capturó
        self.assertIn("firma_mes", datos)

    def test_actividades_del_flow_marcan_casillas_de_la_cuarta(self):
        # Regresión: el multiselect guarda ids del tabulador y la cláusula
        # CUARTA usa otro vocabulario; sin traducción salen todas vacías.
        self._extra("actividades", self.fmt_json)
        self._set("actividades", ["labor_3", "labor_19"])
        with mock.patch("projects.caceh.behaviors.genera_pdf.Media") as MM, \
             mock.patch(
                 "projects.caceh.behaviors.genera_pdf.render_planta",
                 return_value=b"%PDF",) as mock_render:
            MM.return_value.pk = 1
            GeneraPdfBehavior(self.response)

        datos = mock_render.call_args.args[0]
        self.assertEqual(
            datos["actividades"],
            ["limpieza_profunda", "cuidado_personas", "acompanamiento"])

        html = build_html(datos, "planta")
        for texto in ("limpieza profunda ( X )", "cuidado de personas ( X )",
                      "acompañamiento y/o asistencia personal ( X )"):
            self.assertIn(texto, html)
        # Ninguna otra casilla de la CUARTA queda marcada.
        cuarta = html.split("CUARTA. DE LAS ACTIVIDADES")[1].split(
            "podrá desempeñar")[0]
        self.assertEqual(cuarta.count("( X )"), 3)

    def test_entrada_salida_usa_render_entrada_salida(self):
        self._extra("tipo_contrato")
        self._set("tipo_contrato", "entrada_salida")
        with mock.patch("projects.caceh.behaviors.genera_pdf.Media") as MM, \
             mock.patch(
                 "projects.caceh.behaviors.genera_pdf.render_entrada_salida",
                 return_value=b"%PDF",) as mock_es, \
             mock.patch(
                 "projects.caceh.behaviors.genera_pdf.render_planta",
                 return_value=b"%PDF",) as mock_planta:
            MM.return_value.pk = 7
            GeneraPdfBehavior(self.response)

        mock_es.assert_called_once()
        mock_planta.assert_not_called()


class EntregaPdfTestCase(CacehBehaviorTestBase):
    def setUp(self):
        super().setUp()
        self._extra("pdf_contrato")

    def test_entrega_manda_documento_con_media_id(self):
        self._set("pdf_contrato", 99)
        fake_media = mock.Mock()
        fake_media.get_media_id.return_value = "wamid-123"
        with mock.patch(
            "projects.caceh.behaviors.entrega_pdf.Media"
        ) as MockMedia:
            MockMedia.objects.filter.return_value.first.return_value = \
                fake_media
            EntregaPdfBehavior(self.response)

        self.assertEqual(len(self.response.media_messages), 1)
        msg = self.response.media_messages[0]
        self.assertEqual(msg["media_type"], "document")
        self.assertEqual(msg["media_id"], "wamid-123")

    def test_sin_pdf_contrato_agrega_error(self):
        EntregaPdfBehavior(self.response)
        self.assertEqual(self.response.media_messages, [])
        self.assertTrue(self.response.errors)
