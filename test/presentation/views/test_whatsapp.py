"""
Tests de integración para el webhook de WhatsApp Business (`webhook_meta_whatsapp`).

Cubre los dos flujos HTTP que expone el endpoint:
  - GET (suscripción): verifica que el webhook responda correctamente al
    challenge de Meta, validando el token de verificación configurado en
    `settings.WEBHOOK_TOKEN_WHATSAPP` y devolviendo el challenge en el cuerpo.
    También verifica que un token inválido retorne HTTP 403.
  - POST (mensaje entrante): verifica que al recibir un payload válido de
    WhatsApp se creen en la base de datos el `ApiRecord` entrante, el
    `ApiRecord` saliente, la `Interaction` vinculada, y el `User`/`Member`/
    `MemberAccount` correspondientes al remitente. La llamada HTTP real a Meta
    se intercepta con `unittest.mock.patch` para evitar dependencias de red.
  - POST con JSON inválido: verifica que la vista siempre retorne HTTP 200
    aunque el body no sea JSON válido (la excepción es silenciada por diseño).
"""
import json
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from infrastructure.member.models import Member, MemberAccount
from infrastructure.place.models import Account
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Interaction
from infrastructure.users.models import User


def make_meta_response_mock(wa_id: str = "5215549468438") -> MagicMock:
    """
    Retorna un MagicMock que simula una respuesta HTTP 200 de la API de Meta,
    incluyendo el body con `messages[0].id` necesario para que `save_interaction`
    pueda extraer el `mid` y crear la `Interaction`.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "messaging_product": "whatsapp",
        "contacts": [{"input": wa_id, "wa_id": wa_id}],
        "messages": [{"id": "wamid.MOCK_FAKE_ID_FOR_TESTING"}],
    }
    return mock_response


class WebhookWhastAppGetTest(TestCase):
    """Tests del método GET (verificación de suscripción de webhook)."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("webhook_meta_whatsapp")

    def test_get_subscribe_valid_token(self):
        """Con token correcto devuelve HTTP 200 y el challenge en el body."""
        verify_token = getattr(settings, "WEBHOOK_TOKEN_WHATSAPP")
        self.assertIsNotNone(
            verify_token, "WEBHOOK_TOKEN_WHATSAPP no debe ser None"
        )
        challenge = "test_challenge_abc123"
        url = (
            self.url
            + f"?hub.mode=subscribe&hub.challenge={challenge}"
            + f"&hub.verify_token={verify_token}"
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, challenge.encode())

    def test_get_invalid_token_returns_403(self):
        """Con token incorrecto debe retornar HTTP 403."""
        url = (
            self.url
            + "?hub.mode=subscribe&hub.challenge=abc"
            + "&hub.verify_token=WRONG_TOKEN"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_missing_params_returns_403(self):
        """Sin parámetros debe retornar HTTP 403."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


class WebhookWhatsAppPostTest(TestCase):
    """Tests del método POST (mensajes entrantes desde Meta)."""

    fixtures = ["test/fixtures/account_fixture.json"]

    # Datos del usuario simulado en el payload
    WA_ID = "5215549468438"
    PHONE_NUMBER_ID = "103571329211620"

    def setUp(self):
        self.client = Client()
        self.url = reverse("webhook_meta_whatsapp")
        self.valid_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "112795704944207",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "phone_number_id": self.PHONE_NUMBER_ID,
                                    "display_phone_number": "15550578839",
                                },
                                "contacts": [
                                    {
                                        "wa_id": self.WA_ID,
                                        "profile": {"name": "Ricardo Sanginés"},
                                    }
                                ],
                                "messages": [
                                    {
                                        "id": (
                                            "wamid.HBgNNTIxNTU0OTQ2ODQzOBUC"
                                            "ABIYFjNFQjAxOEUxRDczOTRERkExMD"
                                            "IzODkA"
                                        ),
                                        "from": self.WA_ID,
                                        "type": "text",
                                        "timestamp": "1702960757",
                                        "text": {"body": "started"},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

    def _post_payload(self, payload: dict):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    # ------------------------------------------------------------------
    # Test principal: flujo completo end-to-end
    # ------------------------------------------------------------------

    @patch("interface.whatsapp.response.requests.post")
    def test_post_started_creates_member_and_records(self, mock_post):
        """
        Al recibir un mensaje válido de WhatsApp se deben crear en BD:
          - ApiRecord entrante (is_incoming=True)
          - User, Member y MemberAccount del remitente
          - ApiRecord saliente (is_incoming=False) con la respuesta de Meta
          - Interaction vinculada al ApiRecord entrante
        La API de Meta recibe 2 llamadas: mark-as-read y envío de mensaje.
        """
        mock_post.return_value = make_meta_response_mock(self.WA_ID)

        response = self._post_payload(self.valid_payload)

        # La vista siempre retorna 200
        self.assertEqual(response.status_code, 200)

        # --- ApiRecord entrante ---
        self.assertEqual(
            ApiRecord.objects.filter(is_incoming=True).count(), 1,
            "Debe existir exactamente 1 ApiRecord entrante"
        )

        # --- Entidades del usuario ---
        self.assertTrue(
            User.objects.filter(phone=self.WA_ID).exists(),
            "Debe crearse el User"
        )
        account = Account.objects.get(pid=self.PHONE_NUMBER_ID)
        self.assertTrue(
            Member.objects.filter(
                user__phone=self.WA_ID, space=account.space
            ).exists(),
            "Debe crearse el Member"
        )
        self.assertTrue(
            MemberAccount.objects.filter(
                member__user__phone=self.WA_ID, account=account
            ).exists(),
            "Debe crearse el MemberAccount"
        )

        # --- ApiRecord saliente ---
        self.assertGreaterEqual(
            ApiRecord.objects.filter(is_incoming=False).count(), 1,
            "Debe existir al menos 1 ApiRecord saliente (respuesta a Meta)"
        )

        # --- Interaction ---
        self.assertGreaterEqual(
            Interaction.objects.filter(
                member_account__uid=self.WA_ID
            ).count(), 1,
            "Debe existir al menos 1 Interaction para el remitente"
        )

        # --- Llamadas HTTP a Meta (mark-as-read + mensaje) ---
        self.assertEqual(mock_post.call_count, 2,
                         "Deben realizarse 2 llamadas a Meta: mark-as-read y envío de mensaje")
        # La llamada de envío de mensaje usa el phone_number_id
        send_call_args = mock_post.call_args_list[-1]
        called_url = send_call_args[0][0] if send_call_args[0] else send_call_args[1].get(
            "url", "")
        self.assertIn(
            self.PHONE_NUMBER_ID, called_url,
            "La URL de la llamada a Meta debe incluir el phone_number_id"
        )

    @patch("interface.whatsapp.response.requests.post")
    def test_post_links_interaction_to_incoming_record(self, mock_post):
        """
        La Interaction creada debe estar vinculada al ApiRecord entrante
        a través de `api_record_in`.
        """
        mock_post.return_value = make_meta_response_mock(self.WA_ID)

        self._post_payload(self.valid_payload)

        api_record_in = ApiRecord.objects.get(is_incoming=True)
        interaction = Interaction.objects.filter(
            member_account__uid=self.WA_ID
        ).first()

        self.assertIsNotNone(
            interaction, "Debe existir al menos una Interaction")
        self.assertIn(
            api_record_in, interaction.api_record_in.all(),
            "El ApiRecord entrante debe estar vinculado a la Interaction"
        )

    # ------------------------------------------------------------------
    # Tests de casos límite en POST
    # ------------------------------------------------------------------

    def test_post_invalid_json_returns_200(self):
        """
        La vista silencia excepciones por diseño; un body no-JSON debe
        retornar HTTP 200 sin crear ningún registro en BD.
        """
        response = self.client.post(
            self.url,
            data="this is not json {{",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ApiRecord.objects.count(), 0)

    @patch("interface.whatsapp.response.requests.post")
    def test_post_unknown_account_pid_returns_200(self, mock_post):
        """
        Si el phone_number_id no corresponde a ninguna Account en BD,
        la vista retorna 200 y registra el error en el ApiRecord entrante.
        """
        mock_post.return_value = make_meta_response_mock()
        payload = json.loads(json.dumps(self.valid_payload))
        payload["entry"][0]["changes"][0]["value"]["metadata"][
            "phone_number_id"
        ] = "NONEXISTENT_PID_999"

        response = self._post_payload(payload)

        self.assertEqual(response.status_code, 200)
        # El ApiRecord entrante se crea de todas formas
        self.assertEqual(ApiRecord.objects.filter(is_incoming=True).count(), 1)
        # Pero no se crean entidades de usuario ni respuestas
        self.assertFalse(MemberAccount.objects.exists())
        self.assertFalse(ApiRecord.objects.filter(is_incoming=False).exists())
