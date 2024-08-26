from django.test import TestCase
from interface.whatsapp.request import WhatsAppRequest
from services.request.message_model import TextMessage

from test.fixtures.whatsapp_started_data import started_data


class WhatsAppRequestTest(TestCase):
    fixtures = ["test/fixtures/account_fixture.json"]

    def setUp(self):
        self.raw_data = started_data
        self.platform = "whatsapp"

    def test_record_request(self):
        instance = WhatsAppRequest(self.raw_data)
        self.assertFalse(instance.errors)
        self.assertEqual(len(instance.input_accounts), 1)
        self.assertEqual(len(instance.input_accounts[0].members), 1)
        self.assertEqual(len(instance.input_accounts[0].members[0].messages), 1)
        message = instance.input_accounts[0].members[0].messages[0]
        self.assertEqual(type(message), TextMessage)

        self.assertEqual(message.text, "started")  # type: ignore
        self.assertEqual(
            message.message_id, "wamid.HBgNNTIxNTU0OTQ2ODQzOBUC"
            "ABIYFjNFQjAxOEUxRDczOTRERkExMDIzODkA")
        self.assertEqual(message.timestamp, "1702960757")
