from typing import Optional
from infrastructure.box.models import Piece, Written
from infrastructure.talk.models import Interaction
from infrastructure.xtra.models import Extra
from services.processor.destination_rules import destination_find
from services.processor.base_mixin import DestinationProcessorMixin
from services.request.message_model import TextMessage
from services.response.abstract import ResponseAbc


class WrittenProcessorFull(DestinationProcessorMixin):
    context_piece: Piece
    response: ResponseAbc
    message: str
    written: Written
    extra: Extra
    interaction_in: Optional[Interaction]

    def __init__(
            self, response: ResponseAbc, message: str, context_piece: Piece,
            context_direct: bool = False,
            interaction_in: Optional[Interaction] = None,
    ):
        if not context_piece.written:
            raise Exception("Context piece must have a written")

        self.response = response
        self.message = message
        self.written = context_piece.written
        self.interaction_in = interaction_in

        self.response.set_trigger(self.written, context_direct)

        self.written.set_assign(
            self.response.sender.member, interaction_in)
        _extra = self.written.extra or context_piece.default_extra
        if not _extra:
            raise ValueError("Written must have an extra")
        self.extra = _extra

    def process(self):

        self.response.sender.member.add_extra_value(
            self.extra, self.message, self.interaction_in, "written"
        )

        self.process_destination()

    def get_destination(self) -> None:
        self.destination = destination_find(
            self.written.get_destinations(), self.response.sender.member,
            self.response.platform_name, raise_exception=False)


class WrittenProcessor(WrittenProcessorFull):
    response: ResponseAbc
    message: TextMessage
    written: Written
    extra: Extra

    def __init__(
            self, response: ResponseAbc, message: TextMessage,
            written: Written, default_extra: Optional[Extra] = None
    ):
        self.response = response
        self.message = message
        self.written = written
        self.written.set_assign(
            self.response.sender.member, self.message.interaction)
        _extra = self.written.extra or default_extra
        if not _extra:
            raise ValueError("Written must have an extra")
        self.extra = _extra
