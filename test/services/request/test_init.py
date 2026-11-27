import gc

from django.test import TestCase
from infrastructure.service.models import ApiRecord, Platform

from services.request import RequestAbc


class RequestBase(RequestAbc):
    def sort_data(self):
        pass

    def data_to_class(self):
        pass


class RequestAbcTest(TestCase):
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

    def tearDown(self):
        # ApiRecord.__del__ saves on GC; collect while this test's
        # transaction is still open.
        gc.collect()

    def test_init(self):
        instance = RequestBase(
            self.raw_data, self.platform, self.set_messages)

        self.assertEqual(instance.raw_data, self.raw_data)
        self.assertEqual(instance.platform_name, self.platform)
        self.assertEqual(instance.input_accounts, [])
        # set_messages=False must defer recording to the caller.
        self.assertFalse(hasattr(instance, "api_record"))
        self.assertFalse(ApiRecord.objects.exists())

    def test_record_request(self):
        instance = RequestBase(
            self.raw_data, self.platform, self.set_messages)
        instance.record_request()
        self.assertTrue(instance.timestamp_server)
        self.assertTrue(instance.api_record)

        self.assertEqual(instance.api_record.platform.name, self.platform)
        self.assertEqual(instance.api_record.body, self.raw_data)
        self.assertTrue(instance.api_record.is_incoming)

        self.assertTrue(ApiRecord.objects.filter(
            pk=instance.api_record.pk).exists()
        )
