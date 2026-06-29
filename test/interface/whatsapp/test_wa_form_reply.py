import gc

from django.test import TestCase

from infrastructure.box.factories import PieceFactory
from infrastructure.box.models import Fragment
from infrastructure.member.factories import (
    MemberAccountFactory, MemberFactory
)
from infrastructure.place.factories import AccountFactory, SpaceFactory
from infrastructure.place.models import Space
from infrastructure.talk.models import BuiltReply, ExtraValue
from infrastructure.users.factories import UserFactory
from infrastructure.xtra.factories import ExtraFactory, FormatFactory
from interface.whatsapp.response import WhatsAppResponse
from services.manager_flow import ManagerFlow
from services.processor.wa_form_reply import WaFormReplyProcessor
from services.request.message_model import WaFormReplyMessage

from test.fixtures.whatsapp_wa_form_reply_data import wa_form_reply_data
from test.interface.whatsapp.no_send import (
    WhatsAppRequestNoSend, WhatsAppResponseNoSend
)


class WaFormReplyParseTest(TestCase):
    fixtures = ["test/fixtures/account_fixture.json"]

    def test_parses_nfm_reply(self):
        raw = wa_form_reply_data("token-abc", ["act_01", "act_07"])
        request = WhatsAppRequestNoSend(raw)

        self.assertFalse(request.api_record.errors)
        message = request.input_accounts[0].members[0].messages[0]

        self.assertIsInstance(message, WaFormReplyMessage)
        self.assertEqual(message.flow_token, "token-abc")
        self.assertEqual(message.selected, ["act_01", "act_07"])


class WaFormReplyCompletionTest(TestCase):
    fixtures = ["test/fixtures/account_fixture.json"]

    def setUp(self):
        self.space = Space.objects.get(pk=1)
        json_format = FormatFactory(name="json")
        self.extra = ExtraFactory(
            name="activities", space=self.space, format=json_format,
            flow=None, deleted=False)
        self.dest = PieceFactory(
            deleted=False, written=None, default_extra=None, behavior=None)
        Fragment.objects.create(
            piece=self.dest, fragment_type="message", body="¡Listo!",
            order=1, deleted=False)
        self.built_reply = BuiltReply.objects.create(
            is_for_write=True,
            params={
                "behavior": "multiple_select",
                "extra": "activities",
                "dest_piece_pk": self.dest.pk,
                "min": 1,
                "max": 5,
            },
        )

    def tearDown(self):
        # ApiRecord.__del__ saves on GC; force it inside this test's
        # transaction so it can't poison a sibling test's connection.
        gc.collect()

    def test_writes_selection_and_advances(self):
        raw = wa_form_reply_data(
            str(self.built_reply.uuid), ["act_01", "act_07"])
        manager = ManagerFlow(
            raw,
            request_class=WhatsAppRequestNoSend,
            response_class=WhatsAppResponseNoSend,
        )
        manager()

        extra_value = ExtraValue.objects.get(extra=self.extra)
        self.assertEqual(extra_value.get_value(), ["act_01", "act_07"])

        texts = [
            message
            for response in manager.response_list
            for message in response.message_list
            if message.get("type") == "text"
        ]
        self.assertTrue(
            any(t["text"]["body"] == "¡Listo!" for t in texts)
        )


class WaFormReplyValidationTest(TestCase):
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
        self.built_reply = BuiltReply.objects.create(
            is_for_write=True,
            params={
                "extra": "activities",
                "dest_piece_pk": self.dest.pk,
                "min": 2,
                "max": 3,
            },
        )

    def _process(self, selected):
        # api_record_in stays None so errors land on response.errors.
        response = WhatsAppResponseNoSend(
            sender=self.sender, platform_name="whatsapp")
        message = WaFormReplyMessage(
            message_id="wamid.X", timestamp=0,
            flow_token=str(self.built_reply.uuid), selected=selected)
        WaFormReplyProcessor(message, response).process()
        return response

    def test_out_of_range_logs_error_but_still_writes(self):
        response = self._process(["a"])  # below min=2

        self.assertTrue(response.errors)
        extra_value = ExtraValue.objects.get(extra=self.extra)
        self.assertEqual(extra_value.get_value(), ["a"])

    def test_within_range_no_error(self):
        response = self._process(["a", "b"])

        self.assertFalse(response.errors)
        extra_value = ExtraValue.objects.get(extra=self.extra)
        self.assertEqual(extra_value.get_value(), ["a", "b"])

    def test_unknown_flow_token_adds_error(self):
        response = WhatsAppResponseNoSend(
            sender=self.sender, platform_name="whatsapp")
        message = WaFormReplyMessage(
            message_id="wamid.X", timestamp=0,
            flow_token="00000000-0000-0000-0000-000000000000", selected=["a"])
        WaFormReplyProcessor(message, response).process()

        self.assertTrue(response.errors)
