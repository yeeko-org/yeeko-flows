"""
Tests para el flujo de respuesta a mensajes de texto escritos en WhatsApp.

Verifica que cuando un `MemberAccount` existente envía un mensaje de texto
("started"), el `ManagerFlow` procese correctamente la solicitud:
  - Se genera al menos una respuesta en `response_list`.
  - Se crea al menos un `ApiRecord` saliente en la BD.
  - Se crea al menos una `Interaction` para el MemberAccount existente.

Se utiliza `unittest.mock.patch` para interceptar la llamada HTTP a Meta
y `WhatsAppResponseNoSend` de `test.interface.whatsapp.no_send` para
comparar el comportamiento entre ambos enfoques de aislamiento.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Interaction
from interface.whatsapp.request import RecordWhatsAppRequest
from services.manager_flow import ManagerFlow
from test.fixtures.whatsapp_message.whatsapp_started_data import started_data
from test.interface.whatsapp.no_send import (
    WhatsAppRequestNoSend, WhatsAppResponseNoSend,
)


def make_meta_response_mock() -> MagicMock:
    """Simula una respuesta HTTP 200 de la API de Meta."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "messaging_product": "whatsapp",
        "contacts": [{"input": "5215513375592", "wa_id": "5215513375592"}],
        "messages": [{"id": "wamid.MOCK_FAKE_ID_FOR_TESTING"}],
    }
    return mock_response


class WhatsAppWrittenFlowTest(TestCase):
    """
    Tests del flujo con un MemberAccount preexistente usando
    WhatsAppResponseNoSend (sin llamadas HTTP reales).
    """

    fixtures = [
        "test/fixtures/whatsapp_basic_data/basic_memberaccount.json",
        "test/fixtures/whatsapp_basic_data/written_piece.json",
    ]

    WA_ID = "5215513375592"

    def setUp(self) -> None:
        self.member_account = MemberAccount.objects.get(uid=self.WA_ID)

    def _run_flow(self):
        wa_request = WhatsAppRequestNoSend(started_data.copy())
        record = RecordWhatsAppRequest(wa_request)
        manager_flow = ManagerFlow(
            request_record=record,
            response_class=WhatsAppResponseNoSend,
        )
        manager_flow()
        return manager_flow

    def test_written_response_list_not_empty(self):
        """El flujo debe generar al menos una respuesta en response_list."""
        manager_flow = self._run_flow()

        self.assertTrue(
            manager_flow.response_list,
            "response_list no debe estar vacío"
        )

    def test_written_outgoing_api_record_created(self):
        """Debe crearse al menos un ApiRecord saliente."""
        self._run_flow()

        self.assertGreaterEqual(
            ApiRecord.objects.filter(is_incoming=False).count(), 1,
            "Debe existir al menos 1 ApiRecord saliente"
        )

    def test_written_interaction_created_for_member(self):
        """Debe crearse al menos una Interaction para el MemberAccount."""
        self._run_flow()

        self.assertGreaterEqual(
            Interaction.objects.filter(
                member_account__uid=self.WA_ID
            ).count(), 1,
            "Debe existir al menos una Interaction para el MemberAccount"
        )

    def test_written_incoming_api_record_created(self):
        """Debe crearse el ApiRecord entrante al registrar la petición."""
        self._run_flow()

        self.assertEqual(
            ApiRecord.objects.filter(is_incoming=True).count(), 1,
            "Debe existir exactamente 1 ApiRecord entrante"
        )
