import re
from typing import Optional

from infrastructure.box.models import Piece, Reply
from infrastructure.talk.models import BuiltReply, Interaction
from services.processor.behavior import BehaviorProcessor
from services.processor.context_mixin import ContextMixing
from services.processor.interactive import ReplyProcessor
from services.processor.written import WrittenProcessorFull
from services.request.message_model import TextMessage
from services.response import ResponseAbc
from utilities.standard_str import standard


class TextProcessor(ContextMixing):

    text: str
    response: ResponseAbc
    interaction_in: Optional[Interaction] = None

    def __init__(
            self, text: str, response: ResponseAbc,
            interaction_in: Optional[Interaction] = None,
            context_piece: Optional[Piece] = None,
            context_id: Optional[str] = None,
            do_written: bool = True
    ) -> None:
        self.text = text
        self.response = response

        self.interaction_in = interaction_in
        self.context_piece = context_piece
        self.do_written = do_written
        self.calculate_context_piece(self.response.sender, context_id)

    def process(self, call_default_text=True):

        if self.command_handler():
            return

        if self.context_direct and self.process_written():
            return

        if self.intent_to_contact_administrator():
            return

        if not self.last_interaction_out:
            self.call_behavior("start")
            return

        if self.check_buttons_text():
            return

        if call_default_text:
            self.call_behavior("default_text", parameters={"text": self.text})

    def command_handler(self):
        if self.text.startswith("/"):
            self.call_behavior(self.text[1:])
            return True

    def intent_to_contact_administrator(self) -> bool:
        if not bool(re.search(r"admin", self.text, re.IGNORECASE)):
            return False

        self.call_behavior("admin_contact")
        return True

    def call_behavior(self, behavior, parameters=None):
        BehaviorProcessor(
            behavior, self.response, parameters=parameters,
            context_direct=self.context_direct,
            interaction_in=self.interaction_in).process()

    def process_written(self):
        if not self.do_written:
            return False
        if not self.context_piece:
            return False
        try:
            written_processor = WrittenProcessorFull(
                response=self.response, message=self.text,
                context_piece=self.context_piece,
                interaction_in=self.interaction_in
            )
        except Exception as e:
            return False

        written_processor.process()
        return True

    def check_buttons_text(self):
        # estandarizar texto, buscar normalizador de texto
        if not self.context_piece:
            return False

        replays = Reply.objects.filter(
            fragment__piece=self.context_piece)

        reply_by_text = None

        for replay in replays:
            if not replay.title:
                continue
            if standard(replay.title) == standard(self.text):
                reply_by_text = replay
                break

        if not reply_by_text:
            return False

        interaction_origin = Interaction.objects.filter(
            fragment__piece=self.context_piece,
            # TODO configurar el related_name después de merge con notifications
            builtreply__reply=reply_by_text,
            member_account=self.response.sender
        ).first()

        built_reply = BuiltReply.objects.filter(
            interaction=interaction_origin,
            reply=reply_by_text
        ).first()
        if built_reply:
            self.response.set_trigger(
                built_reply, interaction_in=self.interaction_in)

        reply_processor = ReplyProcessor(
            reply=reply_by_text, response=self.response,
            interaction_origin=self.last_interaction_out
        )
        reply_processor.process()
        return True


class TextMessageProcessor(TextProcessor):

    message: TextMessage

    def __init__(
            self, message: TextMessage, response: ResponseAbc
    ) -> None:
        super().__init__(
            text=message.text, response=response,
            context_id=message.context_id, interaction_in=message.interaction
        )

    def process(self):
        super().process(call_default_text=False)

        valid_time_interval = self.message.valid_time_interval(
            raise_exception=False)

        if valid_time_interval and self.process_written():
            return

        self.call_behavior("default_text")
