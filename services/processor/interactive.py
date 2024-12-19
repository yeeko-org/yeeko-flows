from typing import Optional
from infrastructure.box.models import Destination, Piece, Reply
from services.processor.behavior import BehaviorProcessor
from services.processor.destination_rules import destination_find
from services.processor.base_mixin import DestinationProcessorMixin
from services.request.message_model import InteractiveMessage
from services.response.abstract import ResponseAbc


class InteractiveProcessor(DestinationProcessorMixin):
    message: InteractiveMessage
    response: ResponseAbc
    destination: Optional[Destination] = None
    reply: Optional[Reply]

    def __init__(
        self, message: InteractiveMessage, response: ResponseAbc
    ) -> None:
        self.message = message
        self.response = response
        self.reply = message.built_reply.reply if message.built_reply else None
        self.response.set_trigger(message.built_reply, is_direct=True)

    def process(self):
        if self.process_if_not_built_reply():
            return

        if not self.reply:
            return

        self.reply.set_assign(
            self.response.sender.member, self.message.interaction)

        self.set_extra_default_to_member()

        self.process_destination()

    @property
    def piece(self) -> Piece | None:
        if not hasattr(self, "_piece"):
            self._piece = self.get_piece()
        return self._piece

    def get_piece(self) -> Piece | None:
        if not self.message.built_reply:
            return None

        replay_interaction = self.message.built_reply.interaction
        if not replay_interaction:
            return None

        fragment = replay_interaction.fragment
        if not fragment:
            return None

        return fragment.piece

    def process_if_not_built_reply(self):
        if self.message.built_reply:
            return False

        self.process_behavior()
        return True

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
        if not self.piece:
            return

        default_extra = self.piece.default_extra
        if not default_extra:
            return

        self.response.add_extra_value(
            default_extra, self.message.payload, self.message.interaction)

    def process_behavior(self, behavior_name: Optional[str] = None):
        if not behavior_name:
            behavior_name = self.message.payload

        BehaviorProcessor(behavior=behavior_name,
                          response=self.response).process()
