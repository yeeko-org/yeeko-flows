from typing import Optional
from infrastructure.box.models import Destination, Piece, Reply
from infrastructure.talk.models import Interaction
from services.processor.behavior import BehaviorProcessor
from services.processor.destination_rules import destination_find
from services.processor.base_mixin import DestinationProcessorMixin
from services.response.abstract import ResponseAbc


class ReplyProcessor(DestinationProcessorMixin):
    reply: Reply
    response: ResponseAbc
    interaction: Optional[Interaction] = None
    destination: Optional[Destination] = None

    def __init__(
        self, reply: Reply, response: ResponseAbc,
        interaction: Interaction | None = None
    ) -> None:
        self.response = response
        self.reply = reply
        self.interaction = interaction

    def process(self):
        if self.interaction:
            self.reply.set_assign(
                self.response.sender.member, self.interaction)

        self.set_extra_default_to_member()

        self.process_destination()

    @property
    def piece(self) -> Piece | None:
        if not hasattr(self, "_piece"):
            self._piece = self.get_piece()
        return self._piece

    def get_piece(self) -> Piece | None:
        if not self.interaction:
            return None

        fragment = self.interaction.fragment
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
        if not self.piece:
            return

        default_extra = self.piece.default_extra
        if not default_extra:
            return

        self.response.sender.member.add_extra_value(
            default_extra, self.reply.title, self.interaction)
