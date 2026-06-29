from django.test import TestCase

from infrastructure.box.factories import PieceFactory
from infrastructure.member.factories import (
    MemberAccountFactory, MemberFactory
)
from infrastructure.place.factories import AccountFactory, SpaceFactory
from infrastructure.talk.models import BuiltReply
from infrastructure.users.factories import UserFactory
from infrastructure.xtra.factories import ExtraFactory, FormatFactory
from services.behavior.multiple_select import MultipleSelectBehavior
from test.interface.whatsapp.no_send import WhatsAppResponseNoSend


class MultipleSelectBehaviorTest(TestCase):
    def setUp(self):
        self.space = SpaceFactory()
        account = AccountFactory(space=self.space)
        member = MemberFactory(
            space=self.space, user=UserFactory(phone="5550000000"))
        self.sender = MemberAccountFactory(account=account, member=member)
        json_format = FormatFactory(name="json")
        self.extra = ExtraFactory(
            name="activities", space=self.space, format=json_format,
            flow=None, deleted=False)
        self.dest = PieceFactory(
            deleted=False, written=None, default_extra=None, behavior=None)
        self.response = WhatsAppResponseNoSend(
            sender=self.sender, platform_name="whatsapp")

    def test_sends_flow_and_creates_built_reply(self):
        MultipleSelectBehavior(
            response=self.response,
            flow_id="123456",
            body="Elige actividades",
            extra="activities",
            dest_piece_pk=self.dest.pk,
            options=[
                {"value": "a", "label": "Opción A"},
                {"value": "b", "label": "Opción B"},
            ],
            min=1, max=2,
        )

        self.assertFalse(self.response.errors)
        self.assertEqual(len(self.response.message_list), 1)

        message = self.response.message_list[0]
        self.assertEqual(message["type"], "interactive")

        interactive = message["interactive"]
        self.assertEqual(interactive["type"], "flow")

        params = interactive["action"]["parameters"]
        self.assertEqual(params["flow_id"], "123456")
        self.assertEqual(params["flow_action"], "navigate")
        self.assertEqual(params["flow_message_version"], "3")

        data = params["flow_action_payload"]["data"]
        self.assertEqual(
            data["options"],
            [
                {"id": "a", "title": "Opción A"},
                {"id": "b", "title": "Opción B"},
            ],
        )
        self.assertEqual(data["flow_token"], params["flow_token"])

        built_reply = BuiltReply.objects.get(uuid=params["flow_token"])
        self.assertTrue(built_reply.is_for_write)
        self.assertEqual(built_reply.params["extra"], "activities")
        self.assertEqual(built_reply.params["dest_piece_pk"], self.dest.pk)
        self.assertEqual(built_reply.params["min"], 1)
        self.assertEqual(built_reply.params["max"], 2)

    def test_missing_required_param_adds_error(self):
        MultipleSelectBehavior(
            response=self.response,
            flow_id="123456",
            body="Elige",
            extra="activities",
            # dest_piece_pk missing
            options=[{"value": "a", "label": "A"}],
        )
        self.assertTrue(self.response.errors)
        self.assertEqual(self.response.message_list, [])

    def test_unknown_extra_adds_error(self):
        MultipleSelectBehavior(
            response=self.response,
            flow_id="123456",
            body="Elige",
            extra="does_not_exist",
            dest_piece_pk=self.dest.pk,
            options=[{"value": "a", "label": "A"}],
        )
        self.assertTrue(self.response.errors)
        self.assertEqual(self.response.message_list, [])
