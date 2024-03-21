from test.fixtures.whatsapp_started_data import started_data
from services.request.message_model import TextMessage
from interface.whatsapp.request import WhatsAppRequest
from infrastructure.service.models import ApiRecord, Platform
from django.test import TestCase
import json
from interface.whatsapp.response import WhatsAppResponse
from services.manager_flow import ManagerFlow


class WhatsAppManagerFlowTest(TestCase):
    fixtures = ["test/fixtures/account_fixture.json"]

    def setUp(self):
        self.raw_data = started_data

    def test_record_request(self):

        manager_flow = ManagerFlow(
            self.raw_data,
            request_class=WhatsAppRequest,
            response_class=WhatsAppResponse
        )
        manager_flow()

        self.assertTrue(manager_flow.response_list)
