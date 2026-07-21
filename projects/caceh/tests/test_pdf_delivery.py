"""Regresión del tramo E5→E7 (genera/registra/entrega el PDF) por el motor,
con Gemini fake (sin red de IA). Nació del bug del demo: S3 sin credenciales
mataba Media.save() y el PDF nunca nacía.

Caso 1 (offline feliz): media_offline como el e2e; sanity del encadenado.
Caso 2 (Meta rechaza la subida): el flujo degrada con error registrado, sin
matar el turno (e_oferta_mejora sí sale, documento no).
Caso 3 (camino real): storage a disco + subida a Meta OK (mock 200); el
documento sale con media_id, fragment_id ligado y MIME application/pdf.

Correr:
    .venv/bin/python manage.py test \
        projects.caceh.tests.test_pdf_delivery --noinput
"""
import gc
import tempfile
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from infrastructure.persistent_media.models import Media
from infrastructure.place.models import Space
from infrastructure.xtra.models import Format
from projects.caceh.flow_driver import FlowDriver, gemini_fake, media_offline

WA_ID = "5215500000009"
_MEDIA_TMP = tempfile.mkdtemp(prefix="caceh-diag-media-")


class _Resp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def _drive_to_resumen(d: FlowDriver) -> None:
    d.send("hola")
    d.send("¡Empecemos!")
    d.send("Trabajadora")
    d.send("Juana Pérez López")
    d.send("Marcela Ruiz Soto")
    d.send("Sí")
    d.send("Una persona")
    d.send("Sí, duermo ahí")
    d.send("jornada")            # gemini fake: contesta datos canónicos
    d.send("Sí, así es")
    d.send("Empieza ahora")
    d.send("2500 a la semana")
    d.send("Sí, así es")
    d.send("En efectivo")
    d.send("domicilio")
    d.send("Sí, es correcta")
    d.submit_form(["limpieza_general", "lavado"])
    assert d.at_piece() == "e_resumen", d.at_piece()


class PdfDeliveryDiagnosis(TestCase):
    fixtures = ["test/fixtures/account_fixture.json"]

    @classmethod
    def setUpTestData(cls):
        cls.space = Space.objects.get(pk=1)
        Format.objects.get_or_create(name="json")
        Format.objects.get_or_create(name="int")
        call_command("seed_flow", space=cls.space.pk)

    def tearDown(self):
        gc.collect()

    def _document_msgs(self, d: FlowDriver) -> list[dict]:
        return [m for m in d.last_turn if m.get("type") == "document"]

    def test_1_offline_feliz(self):
        with media_offline(), gemini_fake():
            d = FlowDriver(WA_ID)
            _drive_to_resumen(d)
            d.send("Todo correcto")
        self.assertEqual(d.at_piece(), "e_oferta_mejora")
        docs = self._document_msgs(d)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["document"]["id"], "FAKEMEDIAID-WP7")
        self.assertTrue(d.extras().get("pdf_contrato"))

    @override_settings(MEDIA_ROOT=_MEDIA_TMP)
    def test_2_meta_rechaza_subida_degrada_sin_matar_turno(self):
        rejected = _Resp(400, {"error": {"code": 100,
                                         "message": "Invalid MIME"}})
        with gemini_fake(), patch(
                "infrastructure.persistent_media.models.requests.post",
                return_value=rejected):
            d = FlowDriver(WA_ID)
            _drive_to_resumen(d)
            d.send("Todo correcto")
        # Sin media_id no hay documento, pero el turno sigue completo.
        self.assertEqual(d.at_piece(), "e_oferta_mejora")
        self.assertEqual(self._document_msgs(d), [])
        self.assertEqual(d.extras().get("flujo_completado"), "completo")

    @override_settings(MEDIA_ROOT=_MEDIA_TMP)
    def test_3_camino_real_disco_y_meta_ok(self):
        ok = _Resp(200, {"id": "MEDIA-REAL-OK"})
        with gemini_fake(), patch(
                "infrastructure.persistent_media.models.requests.post",
                return_value=ok) as mock_post:
            d = FlowDriver(WA_ID)
            _drive_to_resumen(d)
            d.send("Todo correcto")

        self.assertEqual(d.at_piece(), "e_oferta_mejora")
        docs = self._document_msgs(d)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["document"]["id"], "MEDIA-REAL-OK")
        # La Interaction saliente del PDF debe quedar ligada al fragment.
        self.assertIsNotNone(docs[0].get("_fragment_id"))
        # La subida a Meta declara un MIME real.
        sent = mock_post.call_args.kwargs.get(
            "data") or mock_post.call_args.args[1]
        self.assertEqual(sent["type"], "application/pdf")
        media = Media.objects.latest("uploaded_at")
        self.assertEqual(media.media_id, "MEDIA-REAL-OK")
        self.assertEqual(int(d.extras()["pdf_contrato"]), media.pk)
