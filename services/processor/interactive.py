from typing import Optional
from infrastructure.box.models import Destination, Piece, Reply
from infrastructure.talk.models import Interaction
from services.processor.behavior import BehaviorProcessor
from services.processor.context_mixin import ContextMixing
from services.processor.destination_rules import destination_find
from services.processor.base_mixin import DestinationProcessorMixin
from services.request.message_model import InteractiveMessage
from services.response.abstract import ResponseAbc


class ReplyProcessor(DestinationProcessorMixin):
    reply: Reply | None
    response: ResponseAbc
    interaction_origin: Optional[Interaction] = None
    destination: Optional[Destination] = None

    def __init__(
        self, reply: Reply | None, response: ResponseAbc,
        interaction_origin: Interaction | None = None,
        piece: Piece | None = None
    ) -> None:
        self.response = response
        self.reply = reply
        self.interaction_origin = interaction_origin

        if piece:
            self._piece = piece

    def process(self):
        if not self.reply:
            return

        if self.interaction_origin:
            self.reply.set_assign(
                self.response.sender.member, self.interaction_origin)

        self.set_extra_default_to_member()

        self.process_destination()

    @property
    def piece(self) -> Piece | None:
        if not hasattr(self, "_piece"):
            self._piece = self.get_piece()
        return self._piece

    def get_piece(self) -> Piece | None:
        if not self.interaction_origin:
            return None

        fragment = self.interaction_origin.fragment
        if not fragment:
            return None

        return fragment.piece

    def get_destination(self) -> None:
        if not self.reply:
            return

        self.destination = destination_find(
            self.reply.get_destinations(),
            self.response.sender.member,
            self.response.platform_name,
            raise_exception=False)

        if self.destination:
            return

        if not self.piece:
            return

        self.destination = destination_find(
            self.piece.get_destinations(),
            self.response.sender.member,
            self.response.platform_name,
            raise_exception=False)

    def set_extra_default_to_member(self):
        if not (self.piece and self.reply):
            return

        default_extra = self.piece.default_extra
        if not default_extra:
            return

        self.response.add_extra_value(
            default_extra, self.reply.title, self.interaction_origin)



class InteractiveProcessor(ReplyProcessor, ContextMixing):
    message: InteractiveMessage

    def __init__(
        self, message: InteractiveMessage, response: ResponseAbc
    ) -> None:
        super().__init__(
            reply=message.built_reply.reply if message.built_reply else None,
            response=response, interaction_origin=message.interaction
        )
        if message.built_reply:
            self.response.set_trigger(
                message.built_reply, is_direct=True,
                interaction_in=message.interaction)

    def process(self):
        if self.process_if_not_built_reply():
            return

        super().process()

    def get_piece(self) -> Piece | None:
        if not self.message.built_reply:
            return None

        self.interaction_origin = self.message.built_reply.interaction
        super().get_piece()

    def process_if_not_built_reply(self):
        if self.message.built_reply:
            return False

        BehaviorProcessor(
            behavior=self.message.payload, response=self.response,
            interaction_in=self.message.interaction
        ).process()
        return True
