import re
from typing import Optional

from infrastructure.box.models import Piece, Written
from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Interaction
from infrastructure.xtra.models import Extra
from services.processor.behavior_processor import BehaviorProcessor
from services.processor.processor_base import Processor
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
                fragments__interaction__id=self.message.context_id).first()
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

        if self.message.text.startswith("/"):
            behavior_processor = BehaviorProcessor(
                self.message.text[1:], self.response)
            behavior_processor.process()
            return

        self.intension()

    def intension(self):
        self.message.valid_time_interval()

        if self.context_direct and self.written:
            self.process_written()
            return

        intent_to_contact_administrator = self.intent_to_contact_administrator()

        if self.written:  # indirect intension
            # intencion indirecta, se requiere mas analisis por written
            # evaluacion de tiempo
            # evaluacion de intencion de contacto con administrador
            self.process_written()
            return

        if intent_to_contact_administrator:
            self.process_intent_to_contact_administrator()
            return

        if not self.last_interaction_out:
            self.started()
            return

        self.process_default()

    def intent_to_contact_administrator(self) -> bool:
        return bool(re.search(r"admin", self.message.text, re.IGNORECASE))

    def process_intent_to_contact_administrator(self):
        pass

    def process_default(self):
        print("++++++++++++++++++++++process_default++++++++++++++++++++++")
        pass

    def process_written(self):
        if not self.written:
            return

        written_processor = WrittenProcessor(
            response=self.response, message=self.message,
            written=self.written, default_extra=self.default_extra
        )
        written_processor.process()

    def started(self):
        behavior_processor = BehaviorProcessor("start", self.response)
        behavior_processor.process()
