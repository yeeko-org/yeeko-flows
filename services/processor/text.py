import re
from typing import Optional

from infrastructure.box.models import Piece, Written
from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Interaction
from infrastructure.xtra.models import Extra
from services.processor.behavior import BehaviorProcessor
from services.processor.base_mixin import Processor
from services.processor.written import WrittenProcessor
from services.request.message_model import TextMessage
from services.response import ResponseAbc


class TextMessageProcessor(Processor):
    sender: MemberAccount
    api_request: ApiRecord
    request_message_id: str
    message: TextMessage
    response: ResponseAbc
    written: Optional[Written] = None
    default_extra: Optional[Extra] = None
    last_interaction_out: Optional[Interaction] = None

    def __init__(
            self, manager_flow, message: TextMessage, response: ResponseAbc
    ) -> None:
        self.manager_flow = manager_flow
        self.message = message
        self.sender = response.sender

        self.response = response
        self.set_written_context()

    def set_written_context(self):
        context_piece = None
        self.context_direct = False
        if self.message.context_id:
            context_piece = Piece.objects.filter(
                fragments__interaction__mid=self.message.context_id).first()
            self.context_direct = True
        else:
            context_interaction = Interaction.objects.filter(
                member_account=self.sender, is_incoming=False)\
                .order_by("created").last()
            self.last_interaction_out = context_interaction

            if context_interaction and context_interaction.fragment:
                context_piece = context_interaction.fragment.piece

        self.written = getattr(context_piece, "written", None)
        self.default_extra = getattr(context_piece, "default_extra", None)

    def process(self):

        if self.command_handler():
            return

        if self.context_direct and self.process_written():
            return

        if self.intent_to_contact_administrator():
            return

        if not self.last_interaction_out:
            self.call_behavior("start")
            return

        valid_time_interval = self.message.valid_time_interval(
            raise_exception=False)

        if valid_time_interval and self.process_written():
            return

        self.call_behavior("default_text")

    def command_handler(self):
        if self.message.text.startswith("/"):
            self.call_behavior(self.message.text[1:])
            return True

    def intent_to_contact_administrator(self) -> bool:
        if not bool(re.search(r"admin", self.message.text, re.IGNORECASE)):
            return False

        self.call_behavior("admin_contact")
        return True

    def call_behavior(self, behavior):
        BehaviorProcessor(behavior, self.response).process()

    def process_written(self):
        if not self.written:
            return

        WrittenProcessor(
            response=self.response, message=self.message,
            written=self.written, default_extra=self.default_extra
        ).process()
        return True
