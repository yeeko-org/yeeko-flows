"""
Tests para la clase abstracta base de procesamiento de peticiones (`RequestAbc`).

Utiliza una implementación mínima concreta (`RequestBase`) para verificar el
comportamiento de la clase base sin depender de ningún adaptador específico:
  - Inicialización (`test_init`): comprueba que `raw_data`, `platform` e
    `input_accounts` se asignen correctamente al construir la instancia.
  - Registro de petición (`test_record_request`): verifica que `record_request()`
    genere un `ApiRecord` persistido en base de datos, con la plataforma y el
    cuerpo correctos, y que `timestamp_server` quede definido.
"""

import json
from django.test import TestCase
from infrastructure.service.models import ApiRecord, Platform

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

        self.platform_name = "test_platform"
        _ = Platform.objects.create(name=self.platform_name)

    def test_init(self):
        instance = RequestBase(self.raw_data, self.platform_name)

        self.assertEqual(instance.raw_data, self.raw_data)
        self.assertEqual(instance.platform_name, self.platform_name)
        self.assertEqual(instance.input_accounts, [])

    def test_record_request(self):
        instance = RequestBase(self.raw_data, self.platform_name)
        self.assertTrue(instance.timestamp_server)
        self.assertTrue(instance.api_record)

        self.assertEqual(instance.api_record.platform.name, self.platform_name)
        self.assertEqual(instance.api_record.body, self.raw_data)

        self.assertTrue(ApiRecord.objects.filter(
            pk=instance.api_record.pk).exists()
        )
