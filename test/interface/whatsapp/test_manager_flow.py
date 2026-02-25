"""
Tests para el flujo principal de gestión de mensajes de WhatsApp (`ManagerFlow`).

Verifica que al instanciar y ejecutar `ManagerFlow` con un payload de tipo
"started" (primer mensaje de un usuario nuevo):
  - Se genera al menos una respuesta en `response_list`.
  - Se crea el `ApiRecord` entrante en la BD.
  - Se crea al menos un `ApiRecord` saliente en la BD.
  - Se crea al menos una `Interaction` vinculada al `ApiRecord` entrante.

La llamada HTTP a Meta se intercepta con `unittest.mock.patch` para evitar
dependencias de red durante los tests.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Interaction
from interface.whatsapp.request import RecordWhatsAppRequest, WhatsAppRequest
from interface.whatsapp.response import WhatsAppResponse
from services.manager_flow import ManagerFlow
from test.fixtures.whatsapp_started_data import started_data


def make_meta_response_mock() -> MagicMock:
    """Simula una respuesta HTTP 200 de la API de Meta."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "messaging_product": "whatsapp",
        "contacts": [{"input": "5215549468438", "wa_id": "5215549468438"}],
        "messages": [{"id": "wamid.MOCK_FAKE_ID_FOR_TESTING"}],
    }
    return mock_response


class WhatsAppManagerFlowTest(TestCase):
    fixtures = ["test/fixtures/basic_flow.json"]

    def setUp(self):
        self.raw_data = started_data

    def _run_flow(self):
        wa_request = WhatsAppRequest(self.raw_data)
        record = RecordWhatsAppRequest(wa_request)
        manager_flow = ManagerFlow(
            request_record=record,
            response_class=WhatsAppResponse,
        )
        manager_flow()
        return manager_flow, record

    @patch("interface.whatsapp.response.requests.post")
    def test_response_list_not_empty(self, mock_post):
        """El pipeline debe generar al menos una respuesta."""
        mock_post.return_value = make_meta_response_mock()

        manager_flow, _ = self._run_flow()

        self.assertTrue(
            manager_flow.response_list,
            "response_list no debe estar vacío después de ejecutar el flujo"
        )

    @patch("interface.whatsapp.response.requests.post")
    def test_incoming_api_record_created(self, mock_post):
        """Debe crearse el ApiRecord entrante al registrar la petición."""
        mock_post.return_value = make_meta_response_mock()

        self._run_flow()

        self.assertEqual(
            ApiRecord.objects.filter(is_incoming=True).count(), 1,
            "Debe existir exactamente 1 ApiRecord entrante"
        )

    @patch("interface.whatsapp.response.requests.post")
    def test_outgoing_api_record_created(self, mock_post):
        """Debe crearse al menos un ApiRecord saliente (la respuesta enviada)."""
        mock_post.return_value = make_meta_response_mock()

        self._run_flow()

        self.assertGreaterEqual(
            ApiRecord.objects.filter(is_incoming=False).count(), 1,
            "Debe existir al menos 1 ApiRecord saliente"
        )

    @patch("interface.whatsapp.response.requests.post")
    def test_interaction_created_and_linked(self, mock_post):
        """Debe crearse una Interaction vinculada al ApiRecord entrante."""
        mock_post.return_value = make_meta_response_mock()

        self._run_flow()

        api_record_in = ApiRecord.objects.get(is_incoming=True)
        interaction = Interaction.objects.first()

        self.assertIsNotNone(
            interaction, "Debe existir al menos una Interaction")
        self.assertIn(
            api_record_in, interaction.api_record_in.all(),
            "El ApiRecord entrante debe estar vinculado a la Interaction"
        )

    @patch("interface.whatsapp.response.requests.post")
    def test_meta_api_called_once(self, mock_post):
        """La API de Meta debe ser llamada dos veces: una para mark-as-read y otra para el mensaje."""
        mock_post.return_value = make_meta_response_mock()

        self._run_flow()

        # 1 mark-as-read + 1 mensaje de respuesta
        self.assertEqual(mock_post.call_count, 2,
                         "Deben realizarse exactamente 2 llamadas a la API de Meta: "
                         "mark-as-read y envío de mensaje")
        # La última llamada debe ser el mensaje (no el read status)
        last_call_kwargs = mock_post.call_args_list[-1].kwargs
        self.assertNotIn("status", last_call_kwargs.get("json", {}))
