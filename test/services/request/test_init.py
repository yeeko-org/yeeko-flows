
import json
from django.test import TestCase
from infrastructure.service.models import ApiRequest, Platform

from services.request import RequestAbc


class RequestBase(RequestAbc):
    def sort_data(self):
        pass

    def data_to_class(self):
        pass


class RequestAbcTest(TestCase):  # replace with your actual class name
    def setUp(self):
        self.raw_data = {
            "entry": [
                {
                    "id": "112795704944207",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "contacts": [
                                    {
                                        "wa_id": "5215549468438",
                                        "profile": {
                                            "name": "Ricardo Sanginés"
                                        }
                                    }
                                ],
                                "messages": [
                                    {
                                        "id": "wamid.HBgNNTIxNTU0OTQ2ODQzOBUC"
                                              "ABIYFjNFQjAxOEUxRDczOTRERkExMD"
                                              "IzODkA",
                                        "from": "5215549468438",
                                        "text": {
                                            "body": "started"
                                        },
                                        "type": "text",
                                        "timestamp": "1702960757"
                                    }
                                ],
                                "metadata": {
                                    "phone_number_id": "103571329211620",
                                    "display_phone_number": "15550578839"
                                },
                                "messaging_product": "whatsapp"
                            }
                        }
                    ]
                }
            ],
            "object": "whatsapp_business_account"
        }

        self.platform = "test_platform"
        _ = Platform.objects.create(name=self.platform)
        self.set_messages = False

    def test_init(self):
        instance = RequestBase(
            self.raw_data, self.platform, self.set_messages)

        self.assertEqual(instance.raw_data, self.raw_data)
        self.assertEqual(instance.platform, self.platform)
        self.assertEqual(instance.data, {})
        self.assertEqual(instance.input_accounts, [])
        self.assertEqual(instance.errors, [])

    def test_record_request(self):
        instance = RequestBase(
            self.raw_data, self.platform, self.set_messages)
        instance.record_request()
        self.assertTrue(instance.timestamp_server)
        self.assertTrue(instance.api_request)

        self.assertEqual(instance.api_request.platform.name, self.platform)
        self.assertEqual(instance.api_request.body, self.raw_data)

        self.assertTrue(ApiRequest.objects.filter(
            pk=instance.api_request.pk).exists()
        )
