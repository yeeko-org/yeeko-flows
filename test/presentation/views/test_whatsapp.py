import json
from re import M
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from infrastructure.member.models import Member, MemberAccount
from infrastructure.place.models import Account

from infrastructure.users.models import User


class WebhookWhastAppTest(TestCase):
    fixtures = ["test/fixtures/account_fixture.json"]

    def setUp(self):
        self.client = Client()

    def test_get_subscribe(self):
        verify_token = getattr(settings, "WEBHOOK_TOKEN_WHATSAPP")

        self.assertIsNotNone(
            verify_token, "WEBHOOK_TOKEN_WHATSAPP no debe ser None"
        )
        challenge = "test_challenge"

        url = reverse('webhook_meta_whatsapp')
        url += (
            f"?hub.mode=subscribe&hub.challenge={challenge}&"
            f"hub.verify_token={verify_token}"
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"test_challenge")

    def test_post_started(self):
        data = {
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

        url = reverse('webhook_meta_whatsapp')

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        account = Account.objects.get(pid="112795704944207")

        self.assertTrue(User.objects.filter(
            phone="5215549468438"
        ).exists())
        self.assertTrue(Member.objects.filter(
            user__phone="5215549468438", space=account.space
        ).exists())
        self.assertTrue(MemberAccount.objects.filter(
            member__user__phone="5215549468438", account=account
        ).exists())
