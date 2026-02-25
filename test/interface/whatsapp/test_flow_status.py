"""
Tests de integración para el flujo completo de procesamiento de mensajes de WhatsApp.

Verifica que al ejecutar `ManagerFlow` con un mensaje entrante de WhatsApp se
produzcan correctamente los siguientes efectos en la base de datos:
  - Se crea el `MemberAccount` correspondiente al remitente si no existía.
  - Se registra un `ApiRecord` de salida (respuesta enviada al usuario).
  - Se crea una `Interaction` asociada al `MemberAccount` del remitente.
  - El registro de entrada (`ApiRecord` entrante) queda vinculado a la interacción.

Se utiliza una subclase de `WhatsAppResponse` (`WhatsAppResponseNoSend`) que
simula el envío del mensaje sin realizar llamadas reales a la API de WhatsApp.
"""
from typing import Optional
from django.test import TestCase

from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Interaction
from interface.whatsapp.request import RecordWhatsAppRequest, WhatsAppRequest
from interface.whatsapp.response import WhatsAppResponse
from services.manager_flow import ManagerFlow
from test.fixtures.whatsapp_messages_data import flow_data
from utilities.models_count import models_count


class WhatsAppResponseNoSend(WhatsAppResponse):

    def send_message(
        self, message_data: dict, api_request: Optional[ApiRecord] = None
    ) -> ApiRecord:

        response_body = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "525513375592", "wa_id": "5215513375592"}],
            "messages": [
                {"id": "wamid.HBgNNTIxNTUxMzM3NTU5MhUCABEYEkQzNEE4MDI4RkU2NzQ4NzdBMQA="}
            ]
        }

        return ApiRecord.objects.create(
            platform=self.sender.account.platform,
            body=message_data,
            interaction_type_id="default",
            is_incoming=False,
            response_status=200,
            response_body=response_body,
        )


class WhatsAppFlowStatusTest(TestCase):
    fixtures = ["test/fixtures/basic_flow.json"]

    def test_flow_commit(self):
        print(models_count())
        self.assertFalse(
            MemberAccount.objects.filter(uid="5215513375592").exists())
        self.assertFalse(
            ApiRecord.objects.all().exists())
        self.assertFalse(
            Interaction.objects.filter(
                member_account__uid="5215513375592").exists())

        wa_request = WhatsAppRequest(flow_data[0])
        record = RecordWhatsAppRequest(wa_request)
        manager_flow = ManagerFlow(
            request_record=record,
            response_class=WhatsAppResponseNoSend
        )
        manager_flow()

        self.assertTrue(MemberAccount.objects.filter(
            uid="5215513375592").exists())

        self.assertEqual(
            ApiRecord.objects.filter(is_incoming=False,).count(), 1
        )

        self.assertEqual(
            Interaction.objects.filter(
                member_account__uid="5215513375592").count(), 2)

        interaction = Interaction.objects.filter(
            member_account__uid="5215513375592").first()

        self.assertEqual(
            ApiRecord.objects.filter(is_incoming=True,).count(), 1
        )
        self.assertEqual(interaction.api_record_in.all().count(), 1)

        print(models_count())
