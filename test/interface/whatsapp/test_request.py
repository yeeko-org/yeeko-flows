"""
Tests para el parseo y estructuración de mensajes entrantes de WhatsApp (`WhatsAppRequest`).

Verifica que al procesar un payload JSON de WhatsApp, la clase `WhatsAppRequest`
construya correctamente la jerarquía de objetos:
  - Un único `input_account` a partir de los metadatos del mensaje.
  - Un único miembro (`member`) dentro de ese account.
  - Un único mensaje (`message`) asociado al miembro.
  - Que el mensaje sea de tipo `TextMessage` con el texto, `message_id` y
    `timestamp` correctos según el payload de prueba.
"""
from django.test import TestCase
from yeeko_abc_message_models import request as y_request
from interface.whatsapp.request import WhatsAppRequest
from test.interface.whatsapp.no_send import WhatsAppRequestNoSend

from test.fixtures.whatsapp_started_data import started_data


class WhatsAppRequestTest(TestCase):
    fixtures = ["test/fixtures/account_fixture.json"]

    def setUp(self):
        self.raw_data = started_data
        self.platform = "whatsapp"

    def test_record_request(self):
        instance = WhatsAppRequestNoSend(self.raw_data)
        # self.assertFalse(instance.errors)
        self.assertEqual(len(instance.input_accounts), 1)
        self.assertEqual(len(instance.input_accounts[0].members), 1)
        self.assertEqual(
            len(instance.input_accounts[0].members[0].messages), 1)
        message = instance.input_accounts[0].members[0].messages[0]
        self.assertEqual(type(message), y_request.TextMessage)

        self.assertEqual(message.text, "started")  # type: ignore
        self.assertEqual(
            message.message_id, "wamid.HBgNNTIxNTU0OTQ2ODQzOBUC"
            "ABIYFjNFQjAxOEUxRDczOTRERkExMDIzODkA")
        self.assertEqual(message.timestamp, 1702960757)
