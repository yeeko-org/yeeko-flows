
import json
from unittest.mock import patch
from django.test import TestCase
from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from interface.whatsapp.response import WhatsAppResponse
from infrastructure.service.models import ApiRecord
from services.response.models import SectionsMessage, Section, Button, ReplyMessage


class WhatsAppResponseTest(TestCase):

    # fixtures = ["test/fixtures/account_fixture.json"]

    def setUp(self):
        self.sender_uid = "525549468438"
        self.token = (
            "EAAYaIDXd8t4BO5YrWCpLPYySbxsVt2sW8FlljMO7BT5LxeYJFOdaCVwNjSwga5"
            "vwMM7iP6WRqS8HsQnJn3Ek6ZALocULi03L86rtfDMZCiYBWfNtkrukB35S6iVc"
            "GF5LeGIssILfZBxxXEWMpdWkimS2nd1yDU0OIGKIXazzMdrpWPuGjWOU5zdXr4D9"
            "0zXljGla3Gg4w31mrzKup1UvFs0s4BJPhLKJgZDZD"
        )

        self.account = Account()
        self.account.pid = "103571329211620"
        self.account.token = self.token
        self.message = "Test message"
        self.member = MemberAccount()
        self.member.uid = self.sender_uid
        self.member.account = self.account

    def test_text_to_data(self):
        whatsapp_response = WhatsAppResponse(sender=self.member)
        expected_data = {
            "messaging_product": "whatsapp",
            "to": self.sender_uid,
            "type": "text",
            "text": {"body": self.message},
        }
        self.assertEqual(whatsapp_response.text_to_data(
            self.message), expected_data)

    def test_add_message(self):
        whatsapp_response = WhatsAppResponse(sender=self.member)
        self.assertEqual(whatsapp_response.message_list, [])
        whatsapp_response.message_text(self.message)
        self.assertEqual(len(whatsapp_response.message_list), 1)
        self.assertEqual(
            whatsapp_response.message_list[0][0]["text"]["body"], self.message)

    def test_send_messages(self):
        whatsapp_response = WhatsAppResponse(sender=self.member)
        whatsapp_response.message_text(self.message)
        whatsapp_response.message_multimedia(
            "https://upload.wikimedia.org/wikipedia/en/c/c4/ArcaneJinx.jpeg",
            "image", "Test caption"
        )
        whatsapp_response.message_few_buttons(
            ReplyMessage(
                body="¿Cuál es tu preferencia de contacto?",
                header="https://static.wikia.nocookie.net/eswarhammer40k/images/e/e3/Portada_Codex_Adepta_Sororitas_6%C2%AA_Edici%C3%B3n.jpg",
                footer="Gracias por tu preferencia",
                buttons=[
                    Button(title="Email", payload="PREFER_EMAIL"),
                    Button(title="Email2", payload="PREFER_EMAIL2"),
                    Button(
                        title="WhatsApp", payload="PREFER_WHATSAPP"
                    ),
                ]
            )
        )
        whatsapp_response.message_many_buttons(
            ReplyMessage(
                header="https://pbs.twimg.com/media/FtPjDhKaIAAeRSd.jpg",
                body="¿Cuál es tu preferencia de contacto?",
                footer="Gracias por tu preferencia",
                buttons=[
                    Button(title="Email", payload="PREFER_EMAIL"),
                    Button(title="Email2", payload="PREFER_EMAIL2"),
                    Button(title="Email3", payload="PREFER_EMAIL3"),
                    Button(title="Email4", payload="PREFER_EMAIL4"),
                    Button(
                        title="WhatsApp", payload="PREFER_WHATSAPP"
                    ),
                ]
            )
        )

        first_section = Section(title="sección 1")
        first_section.buttons += [
            Button(payload="laptops", title="Laptops"),
            Button(payload="accesorios", title="Accesorios"),
            Button(payload="smartphones", title="Smartphones"),
        ]

        whatsapp_response.message_sections(
            SectionsMessage(
                header="https://static.wikia.nocookie.net/darkestdungeon_gamepedia/images/5/58/Pdskin1.png",
                body="Elige la categoría que te interesa:",
                button_text="Seleccionar Categoría",
                footer="Gracias por tu preferencia",
                sections=[
                    first_section,
                    Section(
                        title="Sección 2",
                        buttons=[
                            Button(payload="smartphones", title="Smartphones"),
                            Button(payload="laptops", title="Laptops"),
                            Button(payload="accesorios", title="Accesorios"),
                        ]
                    ),
                    Section(
                        title="sección 3",
                        buttons=[
                            Button(payload="smartphones", title="Smartphones"),
                            Button(payload="laptops", title="Laptops"),
                            Button(payload="accesorios", title="Accesorios"),
                        ]
                    )
                ]
            )
        )

        whatsapp_response.send_messages()
        print(whatsapp_response.errors)
